from __future__ import annotations

import os
from typing import List, Dict, Any


def load_taz_ids(taz_file: str) -> List[str]:
	try:
		taz_ids: List[str] = []
		with open(taz_file, 'r', encoding='utf-8') as f:
			for line in f:
				if 'id=' in line and 'taz' in line:
					parts = line.split('id="')
					if len(parts) > 1:
						taz_id = parts[1].split('"')[0]
						taz_ids.append(taz_id)
		return taz_ids
	except Exception as e:
		raise Exception(f"TAZ ID加载失败: {str(e)}")


def validate_taz_file(taz_file: str) -> Dict[str, Any]:
	try:
		result: Dict[str, Any] = {
			"file_path": taz_file,
			"is_valid": True,
			"issues": [],
			"taz_count": 0,
		}
		if not os.path.exists(taz_file):
			result["is_valid"] = False
			result["issues"].append("文件不存在")
			return result
		with open(taz_file, 'r', encoding='utf-8') as f:
			content = f.read()
		if '<tazs>' not in content or '</tazs>' not in content:
			result["is_valid"] = False
			result["issues"].append("缺少tazs标签")
		taz_count = content.count('<taz')
		result["taz_count"] = taz_count
		if taz_count == 0:
			result["is_valid"] = False
			result["issues"].append("没有找到TAZ定义")
		return result
	except Exception as e:
		return {
			"file_path": taz_file,
			"is_valid": False,
			"issues": [f"验证过程出错: {str(e)}"],
			"taz_count": 0,
		}

