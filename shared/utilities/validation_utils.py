from __future__ import annotations

import os
from datetime import datetime


def validate_time_format(time_str: str) -> bool:
	try:
		datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
		return True
	except ValueError:
		return False


def validate_file_path(file_path: str) -> bool:
	try:
		return os.path.exists(file_path) and os.path.isfile(file_path)
	except Exception:
		return False

