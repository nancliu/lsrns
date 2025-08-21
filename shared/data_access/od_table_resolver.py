from __future__ import annotations

from datetime import datetime
from typing import Dict


def get_table_names_from_date(date: datetime) -> Dict[str, str]:
	"""根据日期推断各业务表名。
	可按实际规则扩展；当前规则保留与历史一致的示例。
	"""
	if date.year == 2024:
		return {
			"od_table": "dwd_od_g4202",
			"gantry_table": "dwd_flow_gantry",
			"onramp_table": "dwd_flow_onramp",
			"offramp_table": "dwd_flow_offramp",
		}
	return {
		"od_table": "dwd_od_weekly",
		"gantry_table": "dwd_flow_gantry_weekly",
		"onramp_table": "dwd_flow_onramp_weekly",
		"offramp_table": "dwd_flow_offramp_weekly",
	}

