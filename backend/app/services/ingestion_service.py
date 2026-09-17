"""Service module for validating, normalizing, and importing CSV telemetry into SQLite."""
import io
import csv
from datetime import datetime, timezone
from typing import List, Dict, Set, Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.campus import Building, ResourceMeter, ConsumptionReading
from app.schemas.ingestion import IngestionSummary

# Canonical configuration
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
VALID_RESOURCES = {"electricity", "water", "waste"}
RESOURCE_UNITS = {
    "electricity": "kWh",
    "water": "L",
    "waste": "kg",
}
REQUIRED_COLUMNS = ["timestamp", "building", "resource_type", "value"]


def generate_csv_template() -> str:
    """Generates the canonical CSV template string with instructions and example rows."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(REQUIRED_COLUMNS)
    writer.writerow(["2026-09-01 10:00:00", "Central Library", "electricity", "82.4"])
    writer.writerow(["2026-09-01 11:00:00", "Central Library", "electricity", "85.1"])
    writer.writerow(["2026-09-01 12:00:00", "Central Library", "electricity", "91.7"])
    writer.writerow(["2026-09-01 10:00:00", "Evergreen Residence Hall", "water", "420.0"])
    writer.writerow(["2026-09-01 11:00:00", "Evergreen Residence Hall", "water", "438.0"])
    writer.writerow(["2026-09-01 00:00:00", "Campus Student Center", "waste", "320.0"])
    writer.writerow(["2026-09-02 00:00:00", "Campus Student Center", "waste", "340.0"])
    return output.getvalue()


def parse_flexible_timestamp(raw: str) -> Optional[datetime]:
    """Parses timestamps in common ISO and campus formats into a timezone-naive UTC datetime."""
    s = raw.strip()
    # Try ISO format
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass

    # Common standard patterns
    patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    return None


class IngestionService:
    """Handles parsing, validation, duplicate prevention, and atomic ingestion of telemetry data."""

    @staticmethod
    async def validate_file_metadata(file: UploadFile) -> bytes:
        """Validates file extension, emptiness, and size limit."""
        filename = file.filename or ""
        if not filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for '{filename}'. Only CSV files (.csv) are accepted.",
            )

        content = await file.read()
        if not content or len(content.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded CSV file is empty.",
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
            )

        return content

    @classmethod
    async def process_csv_upload(cls, db: Session, file: UploadFile) -> IngestionSummary:
        """Processes a multipart CSV upload: validates headers, rows, and commits new readings."""
        filename = file.filename or "uploaded_data.csv"
        content_bytes = await cls.validate_file_metadata(file)

        # Decode content safely (handle BOM if present)
        try:
            text_content = content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text_content = content_bytes.decode("latin-1")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unable to decode CSV file encoding: {str(e)}",
                )

        csv_file = io.StringIO(text_content)
        reader = csv.reader(csv_file)

        # Read and clean headers
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded CSV file contains no header row.",
            )

        headers = [h.strip().lower() for h in raw_headers if h is not None]
        missing_headers = [req for req in REQUIRED_COLUMNS if req not in headers]
        if missing_headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required CSV column(s): {', '.join(missing_headers)}. Required schema: {', '.join(REQUIRED_COLUMNS)}.",
            )

        col_map = {col_name: idx for idx, col_name in enumerate(headers)}

        # Load existing Buildings and Meters into memory for O(1) resolution
        buildings = db.query(Building).all()
        building_lookup: Dict[str, Building] = {
            b.name.strip().lower(): b for b in buildings
        }

        meters = db.query(ResourceMeter).all()
        meter_lookup: Dict[Tuple[int, str], ResourceMeter] = {
            (m.building_id, m.resource_type.strip().lower()): m for m in meters
        }

        # Parsing statistics
        total_rows = 0
        valid_rows = 0
        invalid_rows = 0
        duplicate_rows = 0
        errors: List[str] = []
        warnings: List[str] = []

        staged_readings: List[ConsumptionReading] = []
        # In-batch duplicate tracker: set of (meter_id, timestamp)
        seen_in_batch: Set[Tuple[int, datetime]] = set()

        # Gather distinct candidate meters and timestamps for batch DB duplicate lookup
        parsed_row_data = []

        row_num = 1  # 1-based, header was row 1
        for row in reader:
            row_num += 1
            if not row or all(c.strip() == "" for c in row):
                continue  # Skip blank lines

            # Skip comment rows if any
            if row[0].strip().startswith("#"):
                continue

            total_rows += 1

            # 1. Column count check
            if len(row) < len(REQUIRED_COLUMNS):
                invalid_rows += 1
                errors.append(f"Row {row_num}: Incomplete row with fewer columns than required.")
                continue

            raw_ts = row[col_map["timestamp"]].strip() if col_map["timestamp"] < len(row) else ""
            raw_bldg = row[col_map["building"]].strip() if col_map["building"] < len(row) else ""
            raw_res = row[col_map["resource_type"]].strip().lower() if col_map["resource_type"] < len(row) else ""
            raw_val = row[col_map["value"]].strip() if col_map["value"] < len(row) else ""

            # 2. Required non-empty check
            if not raw_ts or not raw_bldg or not raw_res or not raw_val:
                invalid_rows += 1
                errors.append(f"Row {row_num}: Missing required field values.")
                continue

            # 3. Parse timestamp
            parsed_ts = parse_flexible_timestamp(raw_ts)
            if parsed_ts is None:
                invalid_rows += 1
                errors.append(f"Row {row_num}: Invalid timestamp '{raw_ts}'. Format must be YYYY-MM-DD HH:MM:SS or YYYY-MM-DD.")
                continue

            # 4. Validate Building existence
            building = building_lookup.get(raw_bldg.lower())
            if not building:
                invalid_rows += 1
                errors.append(f"Row {row_num}: Unknown building \"{raw_bldg}\". Existing campus buildings: {', '.join([b.name for b in buildings])}.")
                continue

            # 5. Validate Resource Type
            if raw_res not in VALID_RESOURCES:
                invalid_rows += 1
                errors.append(f"Row {row_num}: Invalid resource_type \"{raw_res}\". Allowed resources: electricity, water, waste.")
                continue

            # 6. Validate Numeric Value
            try:
                numeric_val = float(raw_val)
            except ValueError:
                invalid_rows += 1
                errors.append(f"Row {row_num}: Value must be numeric (got \"{raw_val}\").")
                continue

            # 7. Validate Non-negative Value
            if numeric_val < 0.0:
                invalid_rows += 1
                errors.append(f"Row {row_num}: Value cannot be negative (got {numeric_val}).")
                continue

            # 8. Resolve or auto-create Meter
            meter_key = (building.id, raw_res)
            meter = meter_lookup.get(meter_key)
            if not meter:
                # Ensure meter exists for building
                unit = RESOURCE_UNITS.get(raw_res, "units")
                meter = ResourceMeter(building_id=building.id, resource_type=raw_res, unit=unit)
                db.add(meter)
                db.flush()
                meter_lookup[meter_key] = meter

            parsed_row_data.append({
                "row_num": row_num,
                "building_name": building.name,
                "resource_type": raw_res,
                "meter_id": meter.id,
                "timestamp": parsed_ts,
                "value": numeric_val,
            })

        # Check DB duplicates in batch for candidates
        if parsed_row_data:
            candidate_meters = {r["meter_id"] for r in parsed_row_data}
            min_ts = min(r["timestamp"] for r in parsed_row_data)
            max_ts = max(r["timestamp"] for r in parsed_row_data)

            existing_db_pairs: Set[Tuple[int, datetime]] = set()
            existing_records = (
                db.query(ConsumptionReading.meter_id, ConsumptionReading.timestamp)
                .filter(
                    ConsumptionReading.meter_id.in_(candidate_meters),
                    ConsumptionReading.timestamp >= min_ts,
                    ConsumptionReading.timestamp <= max_ts,
                )
                .all()
            )
            for m_id, ts in existing_records:
                existing_db_pairs.add((m_id, ts))

            # Process candidates for staging
            for item in parsed_row_data:
                m_id = item["meter_id"]
                ts = item["timestamp"]
                pair = (m_id, ts)

                # Check DB or in-batch duplicate
                if pair in existing_db_pairs or pair in seen_in_batch:
                    duplicate_rows += 1
                    warnings.append(
                        f"Row {item['row_num']}: Duplicate record for {item['building_name']} "
                        f"({item['resource_type']}) at {ts}. Skipped."
                    )
                    continue

                seen_in_batch.add(pair)
                valid_rows += 1
                staged_readings.append(
                    ConsumptionReading(
                        meter_id=m_id,
                        timestamp=ts,
                        value=round(item["value"], 2),
                        is_anomaly=False,
                    )
                )

        # Atomic commit of valid rows
        imported_rows = len(staged_readings)
        if imported_rows > 0:
            try:
                db.add_all(staged_readings)
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database transaction error during telemetry import: {str(e)}",
                )

        # Message summary
        if imported_rows > 0 and invalid_rows == 0 and duplicate_rows == 0:
            msg = f"Successfully imported all {imported_rows} telemetry records."
        elif imported_rows > 0:
            msg = f"Imported {imported_rows} new records with {duplicate_rows} duplicate(s) and {invalid_rows} rejected row(s)."
        elif duplicate_rows > 0 and invalid_rows == 0:
            msg = f"No new records imported: all {duplicate_rows} valid row(s) already exist in database."
        else:
            msg = f"Import completed: 0 rows imported, {invalid_rows} row(s) rejected."

        return IngestionSummary(
            filename=filename,
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            imported_rows=imported_rows,
            duplicate_rows=duplicate_rows,
            errors=errors,
            warnings=warnings,
            message=msg,
        )
