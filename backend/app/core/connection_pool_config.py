"""
Centralised SQLAlchemy connection-pool settings.
database.py reads from here so all tuning lives in one place.
"""

POOL_SIZE: int = 10
MAX_OVERFLOW: int = 20
POOL_TIMEOUT: int = 30
POOL_RECYCLE: int = 3600
POOL_PRE_PING: bool = True
