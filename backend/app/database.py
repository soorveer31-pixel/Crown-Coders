"""Convenience proxy re-exporting core database utilities from app.core.database."""
from app.core.database import Base, engine, get_db, SessionLocal, init_db

__all__ = ["Base", "engine", "get_db", "SessionLocal", "init_db"]
