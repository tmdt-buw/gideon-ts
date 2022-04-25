"""
    Connector Dependencies
"""
from src.db.sqlalchemy.database import SessionLocal
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_connector():
    pool = TimescaleDBConnectorPool()
    try:
        yield pool
    finally:
        pool.disconnect()
