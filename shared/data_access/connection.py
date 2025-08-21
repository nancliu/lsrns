from __future__ import annotations

import psycopg2
from .db_config import get_db_config


def open_db_connection():
	cfg = get_db_config()
	return psycopg2.connect(
		host=cfg["host"], port=cfg["port"], dbname=cfg["database"],
		user=cfg["user"], password=cfg["password"]
	)

