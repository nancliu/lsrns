from __future__ import annotations

from datetime import datetime
from typing import Optional, List


def parse_datetime(time_str: str) -> datetime:
	"""解析时间字符串为 datetime
	支持多种常见格式及 ISO8601。
	"""
	if isinstance(time_str, datetime):
		return time_str
	formats = [
		"%Y/%m/%d %H:%M:%S",
		"%Y-%m-%d %H:%M:%S",
		"%Y/%m/%d %H:%M",
		"%Y-%m-%d %H:%M",
		"%Y/%m/%d",
		"%Y-%m-%d",
	]
	for fmt in formats:
		try:
			return datetime.strptime(time_str, fmt)
		except Exception:
			continue
	# ISO 回退
	try:
		return datetime.fromisoformat(str(time_str).replace('Z', '').replace('/', '-'))
	except Exception:
		pass
	raise ValueError(f"无法解析时间格式: {time_str}")


def calculate_duration(start_time: datetime, end_time: datetime) -> int:
	"""计算两个时间点之间的持续时间（秒）"""
	if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
		raise ValueError("参数必须是datetime对象")
	
	delta = end_time - start_time
	return int(delta.total_seconds())


def split_time_range(start_time: datetime, end_time: datetime, 
                    interval_hours: int = 1) -> List[tuple[datetime, datetime]]:
	"""将时间范围分割为多个小时间隔
	
	Args:
		start_time: 开始时间
		end_time: 结束时间
		interval_hours: 间隔小时数，默认1小时
	
	Returns:
		时间间隔列表，每个元素为(start, end)的元组
	"""
	if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
		raise ValueError("参数必须是datetime对象")
	
	if start_time >= end_time:
		raise ValueError("开始时间必须早于结束时间")
	
	intervals = []
	current_start = start_time
	
	while current_start < end_time:
		current_end = min(
			current_start.replace(hour=current_start.hour + interval_hours),
			end_time
		)
		intervals.append((current_start, current_end))
		current_start = current_end
	
	return intervals
