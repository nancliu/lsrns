from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
import logging
import pandas as pd
import psycopg2

from .db_config import get_db_config


logger = logging.getLogger(__name__)


class GantryDataLoader:
	"""门架数据访问：从数据库加载门架观测数据。"""
	def __init__(self):
		self._conn = None

	def _connect(self):
		if self._conn is None:
			cfg = get_db_config()
			self._conn = psycopg2.connect(
				host=cfg["host"], port=cfg["port"], dbname=cfg["database"],
				user=cfg["user"], password=cfg["password"]
			)
		return self._conn

	def check_data_availability(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
		"""检查指定时间范围内的门架数据可用性"""
		try:
			conn = self._connect()
			with conn.cursor() as cur:
				# 检查数据目录表
				query = """
					SELECT 
						table_name,
						data_date,
						record_count,
						data_status
					FROM dwd.dwd_data_catalog 
					WHERE table_name = 'dwd_flow_gantry_weekly'
					  AND data_date >= %s::DATE AND data_date <= %s::DATE
					ORDER BY data_date
				"""
				cur.execute(query, (start_time.date(), end_time.date()))
				catalog_data = cur.fetchall()
				
				# 检查实际数据
				data_query = """
					SELECT 
						COUNT(*) as total_records,
						COUNT(DISTINCT start_gantryid) as unique_gantries,
						MIN(start_time) as earliest_time,
						MAX(start_time) as latest_time,
						SUM(total) as total_flow,
						AVG(avg_speed) as avg_speed
					FROM dwd.dwd_flow_gantry_weekly 
					WHERE start_time >= %s AND start_time < %s
					  AND total > 0  -- 过滤无效数据
				"""
				cur.execute(data_query, (start_time, end_time))
				data_stats = cur.fetchone()
				
				# 检查数据覆盖情况
				coverage_query = """
					SELECT 
						DATE(start_time) as date,
						COUNT(*) as daily_records,
						COUNT(DISTINCT start_gantryid) as daily_gantries,
						SUM(total) as daily_flow
					FROM dwd.dwd_flow_gantry_weekly 
					WHERE start_time >= %s AND start_time < %s
					  AND total > 0
					GROUP BY DATE(start_time)
					ORDER BY date
				"""
				cur.execute(coverage_query, (start_time, end_time))
				daily_coverage = cur.fetchall()
				
				return {
					"available": len(catalog_data) > 0 and data_stats[0] > 0,
					"catalog_entries": len(catalog_data),
					"total_records": data_stats[0] if data_stats else 0,
					"unique_gantries": data_stats[1] if data_stats else 0,
					"total_flow": data_stats[4] if data_stats else 0,
					"avg_speed": float(data_stats[5]) if data_stats and data_stats[5] else None,
					"time_range": {
						"earliest": data_stats[2].isoformat() if data_stats and data_stats[2] else None,
						"latest": data_stats[3].isoformat() if data_stats and data_stats[3] else None
					},
					"daily_coverage": [
						{
							"date": row[0].isoformat(),
							"records": row[1],
							"gantries": row[2],
							"flow": row[3]
						} for row in daily_coverage
					],
					"catalog_details": [
						{
							"date": row[1].isoformat(),
							"record_count": row[2],
							"status": row[3]
						} for row in catalog_data
					]
				}
		except Exception as e:
			logger.error(f"数据可用性检查失败: {e}")
			return {
				"available": False,
				"error": str(e)
			}

	def close(self):
		try:
			if self._conn:
				self._conn.close()
		except Exception:
			pass
		finally:
			self._conn = None

	def load_gantry_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
		"""按时间范围加载门架数据。
		返回 DataFrame，若失败返回空表。
		
		根据 docs/data_in_db/DWD_四表结构说明.md 中的表结构实现
		"""
		try:
			conn = self._connect()
			with conn.cursor() as cur:
				# 使用正确的表名和字段结构，基于 dwd_flow_gantry_weekly 表
				query = """
					SELECT 
						start_gantryid as gantry_id,
						end_gantryid,
						gantry_name,
						start_time,
						-- 流量相关字段
						total as flow,
						k1, k2, k3, k4,           -- 客车流量
						h1, h2, h3, h4, h5, h6,   -- 货车流量
						t1, t2, t3, t4, t5, t6,   -- 特种车流量
						total_k, total_h, total_t, -- 分类总流量
						-- 性能指标
						avg_speed as speed,
						avg_duration,
						distance
					FROM dwd.dwd_flow_gantry_weekly 
					WHERE start_time >= %s AND start_time < %s
					  AND total > 0  -- 过滤无效流量数据
					  AND start_gantryid IS NOT NULL  -- 确保门架ID有效
					ORDER BY start_gantryid, start_time
				"""
				cur.execute(query, (start_time, end_time))
				rows = cur.fetchall()
				cols = [desc[0] for desc in cur.description]
				df = pd.DataFrame(rows, columns=cols)
				
				if df.empty:
					logger.warning(
						f"在时间范围 {start_time} - {end_time} 内未找到门架数据"
					)
					logger.info("请检查: 1) 时间范围覆盖 2) 数据库连接 3) dwd_flow_gantry_weekly 是否有数据")
				else:
					logger.info(f"成功加载门架数据: {len(df)} 条记录")
					try:
						logger.info(f"门架数量: {df['gantry_id'].nunique()}")
						logger.info(f"时间范围: {df['start_time'].min()} - {df['start_time'].max()}")
						logger.info(
							f"总流量: {df['flow'].sum()} 客车: {df.get('total_k', pd.Series(dtype=float)).sum()} "
							f"货车: {df.get('total_h', pd.Series(dtype=float)).sum()} 特种: {df.get('total_t', pd.Series(dtype=float)).sum()}"
						)
					except Exception:
						pass
				
				return df
		except Exception as e:
			logger.error(f"门架数据加载失败: {e} ({type(e).__name__})")
			return pd.DataFrame()
		finally:
			try:
				if self._conn:
					self._conn.commit()
			except Exception:
				pass

	def load_gantry_data_for_analysis(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
		"""按时间范围加载用于分析的门架数据。
		当前实现直接复用 load_gantry_data，保持简单并将标准化留给处理器。
		"""
		return self.load_gantry_data(start_time, end_time)

