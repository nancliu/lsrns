from __future__ import annotations

import psycopg2
import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from .db_config import get_db_config

logger = logging.getLogger(__name__)

# Global SQLAlchemy engine instance (initialized on first use)
_engine = None


def open_db_connection():
	"""
	Legacy database connection function using psycopg2 directly.

	Maintained for backward compatibility with existing code.

	Returns:
		psycopg2 connection object
	"""
	cfg = get_db_config()
	return psycopg2.connect(
		host=cfg["host"], port=cfg["port"], dbname=cfg["database"],
		user=cfg["user"], password=cfg["password"]
	)


def get_engine(
	pool_size: int = 10,
	max_overflow: int = 5,
	pool_timeout: int = 30
):
	"""
	Get or create SQLAlchemy engine with connection pooling.

	Uses QueuePool for efficient connection management. Thread-safe
	singleton pattern ensures single engine instance per process.

	Args:
		pool_size: Number of connections to maintain (default: 10)
		max_overflow: Max additional connections beyond pool_size (default: 5)
		pool_timeout: Seconds to wait for connection from pool (default: 30)

	Returns:
		SQLAlchemy engine instance with connection pooling

	Example:
		engine = get_engine()
		with engine.connect() as conn:
			result = conn.execute(text("SELECT * FROM edges"))
	"""
	global _engine

	if _engine is None:
		cfg = get_db_config()

		# Build PostgreSQL connection URL
		db_url = (
			f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
			f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
		)

		logger.info(
			"Initializing SQLAlchemy engine with connection pooling",
			extra={
				"pool_size": pool_size,
				"max_overflow": max_overflow,
				"pool_timeout": pool_timeout
			}
		)

		_engine = create_engine(
			db_url,
			poolclass=QueuePool,
			pool_size=pool_size,
			max_overflow=max_overflow,
			pool_timeout=pool_timeout,
			pool_pre_ping=True,  # Verify connections before using
			echo=False  # Set True for SQL logging during development
		)

	return _engine


def get_pooled_connection():
	"""
	Get database connection from connection pool.

	Uses SQLAlchemy engine pooling for efficient connection management.

	Returns:
		SQLAlchemy connection object (use with context manager)

	Example:
		with get_pooled_connection() as conn:
			result = conn.execute(text("SELECT * FROM edges"))
	"""
	engine = get_engine()
	return engine.connect()

