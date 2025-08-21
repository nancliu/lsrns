"""
E1 数据处理模块
负责从 XML 文件解析 E1 检测器数据、标准化列并进行按门架与时间聚合。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import logging
import pandas as pd


logger = logging.getLogger(__name__)


class E1DataProcessor:
    """E1 数据处理器。

    职责：
    - 解析 E1 XML 文件至 DataFrame
    - 标准化列名与数据类型
    - 依据门架 ID 与分钟粒度进行聚合（多车道合并）
    """

    def load_e1_data(self, e1_dir: Path, simulation_start: Optional[datetime] = None) -> pd.DataFrame:
        """加载E1数据的简化接口（用于机理分析）
        
        Args:
            e1_dir: 包含 E1 XML 文件的目录
            simulation_start: 仿真起始时间（可选，用于机理分析时可能不需要）
            
        Returns:
            聚合并标准化后的 E1 DataFrame
        """
        try:
            # 如果没有提供simulation_start，尝试从案例元数据获取
            if simulation_start is None:
                # 从e1_dir的父目录结构推断仿真目录
                if "simulations" in e1_dir.parts:
                    sim_index = e1_dir.parts.index("simulations")
                    simulation_dir = Path(*e1_dir.parts[:sim_index + 2])  # 包含simulations和仿真ID
                    simulation_start = self._get_simulation_start_time_from_case(simulation_dir)
                else:
                    simulation_start = datetime.now()
            
            return self.load_from_directory(e1_dir, simulation_start)
            
        except Exception as e:
            logger.error(f"加载E1数据失败: {e}")
            return pd.DataFrame()

    def load_from_directory(self, e1_dir: Path, simulation_start: datetime) -> pd.DataFrame:
        """从目录加载并聚合 E1 数据。

        Args:
            e1_dir: 包含 E1 XML 文件的目录
            simulation_start: 仿真起始绝对时间（用于将 XML 中的相对秒转换为绝对时间）

        Returns:
            聚合并标准化后的 E1 DataFrame（列至少包括 gantry_id, start_time, time_key, flow, speed, occupancy）
        """
        try:
            if not e1_dir.exists() or not e1_dir.is_dir():
                logger.warning(f"E1 目录不存在或不可用: {e1_dir}")
                return pd.DataFrame()

            xml_files = list(e1_dir.rglob("*.xml"))
            if not xml_files:
                logger.warning(f"E1 目录下未发现 XML 文件: {e1_dir}")
                return pd.DataFrame()

            frames: List[pd.DataFrame] = []
            for xml_file in xml_files:
                try:
                    df = self._parse_single_xml(xml_file, simulation_start)
                    if not df.empty:
                        frames.append(df)
                except Exception as ex:
                    logger.warning(f"解析 E1 XML 失败 {xml_file.name}: {ex}")

            if not frames:
                return pd.DataFrame()

            raw_df = pd.concat(frames, ignore_index=True)
            std_df = self.standardize_columns(raw_df)
            return self.aggregate_minutely(std_df)

        except Exception as e:
            logger.error(f"加载 E1 目录失败: {e}")
            return pd.DataFrame()

    def standardize_columns(self, e1_df: pd.DataFrame) -> pd.DataFrame:
        """标准化 E1 列名与数据类型，并生成分钟级时间键。"""
        try:
            if e1_df.empty:
                return pd.DataFrame()

            df = e1_df.copy()
            try:
                df.columns = [str(c).strip().lower() for c in df.columns]
            except Exception:
                pass

            # 必需列检查（宽松处理）
            required = ["gantry_id", "start_time", "flow"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                logger.warning(f"E1 数据缺少必要列: {missing}")

            # 类型转换
            if "start_time" in df.columns:
                df["start_time"] = pd.to_datetime(df["start_time"])  # 绝对时间
            for col in ("flow", "speed", "occupancy", "nvehcontrib"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # 生成分钟级时间键
            if "start_time" in df.columns:
                df["time_key"] = df["start_time"].dt.floor("1min")

            # 过滤无效
            subset_cols = [c for c in ["gantry_id", "start_time", "flow"] if c in df.columns]
            if subset_cols:
                df = df.dropna(subset=subset_cols)

            return df
        except Exception as e:
            logger.error(f"E1 数据标准化失败: {e}")
            return pd.DataFrame()

    def aggregate_minutely(self, e1_df: pd.DataFrame) -> pd.DataFrame:
        """将多车道 E1 数据按分钟、门架聚合。

        - flow: 求和
        - speed: 以 nVehContrib 加权平均（若无则退化为均值）
        - occupancy: 平均
        - 输出同时包含 start_time（取 time_key）和 time_key
        """
        try:
            if e1_df.empty:
                return pd.DataFrame()

            needed = ["gantry_id", "time_key"]
            for n in needed:
                if n not in e1_df.columns:
                    logger.warning(f"E1 数据缺少对齐关键列: {n}")
                    return pd.DataFrame()

            df = e1_df.copy()

            # 构造权重
            if "nvehcontrib" not in df.columns:
                df["nvehcontrib"] = 1.0

            group_cols = ["gantry_id", "time_key"]
            agg_df = (
                df.groupby(group_cols).apply(
                    lambda g: pd.Series({
                        "flow": g["flow"].sum(skipna=True) if "flow" in g else 0.0,
                        "speed": (g["speed"].mul(g["nvehcontrib"]).sum(skipna=True) / g["nvehcontrib"].sum(skipna=True))
                                  if ("speed" in g and g["nvehcontrib"].sum(skipna=True) > 0) else (g["speed"].mean(skipna=True) if "speed" in g else 0.0),
                        "occupancy": g["occupancy"].mean(skipna=True) if "occupancy" in g else 0.0,
                        "nvehcontrib": g["nvehcontrib"].sum(skipna=True),
                    })
                ).reset_index()
            )

            # 输出 start_time（用于与对齐结果中的 e1_time 对应）
            agg_df["start_time"] = agg_df["time_key"]

            # 列顺序整理
            cols = [c for c in ["gantry_id", "start_time", "time_key", "flow", "speed", "occupancy", "nvehcontrib"] if c in agg_df.columns]
            return agg_df[cols]
        except Exception as e:
            logger.error(f"E1 数据聚合失败: {e}")
            return pd.DataFrame()

    def _parse_single_xml(self, e1_file: Path, simulation_start: datetime) -> pd.DataFrame:
        """解析单个 E1 XML 文件为 DataFrame。

        列：detector_id, gantry_id, start_time, end_time, begin, end, flow, speed, occupancy, nVehContrib
        """
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(e1_file)
            root = tree.getroot()

            rows: List[Dict[str, Any]] = []
            for interval in root.findall(".//interval"):
                detector_id = interval.get("id")
                begin_sec = float(interval.get("begin", 0))
                end_sec = float(interval.get("end", 0))
                # 修复：SUMO E1检测器的流量字段是"entered"，不是"flow"
                flow = float(interval.get("entered", 0))  # 从entered字段获取流量
                speed = float(interval.get("speed", 0))
                occupancy = float(interval.get("occupancy", 0))
                n_veh = int(interval.get("nVehContrib", 0))

                # 绝对时间
                start_time = simulation_start + timedelta(seconds=begin_sec)
                end_time = simulation_start + timedelta(seconds=end_sec)

                # 门架 ID：去掉最后 _车道 后缀
                if detector_id and "_" in detector_id:
                    gantry_id = detector_id.rsplit("_", 1)[0]
                else:
                    gantry_id = detector_id

                rows.append({
                    "detector_id": detector_id,
                    "gantry_id": gantry_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "begin": begin_sec,
                    "end": end_sec,
                    "flow": flow,
                    "speed": speed,
                    "occupancy": occupancy,
                    "nVehContrib": n_veh,
                })

            return pd.DataFrame(rows)
        except Exception as e:
            logger.error(f"解析 E1 XML 失败 {e1_file}: {e}")
            return pd.DataFrame()
    
    def _get_simulation_start_time_from_case(self, simulation_dir: Path) -> datetime:
        """从案例元数据获取仿真开始时间"""
        try:
            # 查找案例元数据文件
            case_dir = simulation_dir.parent.parent
            metadata_file = case_dir / "metadata.json"
            
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 从案例元数据获取时间范围
                time_range = metadata.get("time_range", {})
                start_time_str = time_range.get("start")
                
                if start_time_str:
                    from shared.utilities.time_utils import parse_datetime
                    return parse_datetime(start_time_str)
            
            # 如果无法获取，返回当前时间
            logger.warning("无法从案例元数据获取仿真开始时间，使用当前时间")
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"无法从案例元数据获取仿真开始时间: {e}")
            return datetime.now()


