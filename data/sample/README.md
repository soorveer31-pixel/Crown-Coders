# Demonstration Sample Telemetry Data

This directory contains safe, synthetic demonstration telemetry data for testing the **Campus Resource Autopilot** data ingestion pipeline.

## Files

- `sample_consumption.csv`: A canonical sample CSV with hourly electricity, water, and daily waste telemetry across registered campus facilities.

## Canonical CSV Schema

| Column | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `timestamp` | String / ISO-8601 | UTC or campus timestamp of reading | `2026-09-01 10:00:00` |
| `building` | String | Case-insensitive registered facility name | `Science & Engineering Complex` |
| `resource_type` | String | Resource identifier: `electricity`, `water`, `waste` | `electricity` |
| `value` | Float | Non-negative consumption measurement | `198.6` |

> [!NOTE]
> This file contains synthetic benchmark values only and does not contain private, confidential, or sensitive campus operational credentials.
