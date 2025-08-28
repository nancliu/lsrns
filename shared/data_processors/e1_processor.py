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
            聚合并标准化后的 E1 DataFrame（列至少包括 gantry_id, start_time, time_key, volume, speed, occupancy）
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
            required = ["gantry_id", "start_time", "volume"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                logger.warning(f"E1 数据缺少必要列: {missing}")

            # 类型转换
            if "start_time" in df.columns:
                df["start_time"] = pd.to_datetime(df["start_time"])  # 绝对时间
            for col in ("volume", "speed", "occupancy", "nvehcontrib", "nvehentered", "harmonicmeanspeed", "vehiclelength", "begin", "end"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # 生成分钟级时间键
            if "start_time" in df.columns:
                df["time_key"] = df["start_time"].dt.floor("1min")

            # 过滤无效
            subset_cols = [c for c in ["gantry_id", "start_time", "volume"] if c in df.columns]
            if subset_cols:
                df = df.dropna(subset=subset_cols)

            return df
        except Exception as e:
            logger.error(f"E1 数据标准化失败: {e}")
            return pd.DataFrame()

    def aggregate_minutely(self, e1_df: pd.DataFrame) -> pd.DataFrame:
        """将多车道 E1 数据按分钟、门架聚合。

        - volume: 求和（车辆数）
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
            # 检查flow字段是否存在
            has_flow = "flow" in df.columns
            logger.info(f"E1数据聚合: flow字段存在 = {has_flow}, 可用列 = {list(df.columns)}")
            
            agg_dict = {
                "volume": "sum",
                "speed": lambda x: (x * df.loc[x.index, "nvehcontrib"]).sum() / df.loc[x.index, "nvehcontrib"].sum() if "nvehcontrib" in df.columns and df.loc[x.index, "nvehcontrib"].sum() > 0 else x.mean(),
                "occupancy": "mean",
                "nvehcontrib": "sum",
                "nvehentered": "sum",
                "harmonicmeanspeed": "mean",
                "vehiclelength": "mean",
                "begin": "min",
                "end": "max"
            }
            
            # 如果存在flow字段，添加到聚合中
            if has_flow:
                agg_dict["flow"] = "sum"  # flow字段按时间区间求和
                logger.info("已添加flow字段到聚合字典")
            else:
                logger.warning("E1数据中缺少flow字段，将使用volume字段作为替代")
                # 如果没有flow字段，将volume作为flow的替代
                agg_dict["flow"] = "sum"  # 使用volume作为flow
            
            # 使用兼容的聚合方式，避免pandas版本问题
            agg_df = df.groupby(group_cols).agg(agg_dict).reset_index()

            # 输出 start_time（用于与对齐结果中的 e1_time 对应）
            agg_df["start_time"] = agg_df["time_key"]

            # 列顺序整理 - 确保flow字段包含在内
            base_cols = ["gantry_id", "start_time", "time_key"]
            data_cols = ["flow", "volume", "speed", "occupancy", "nvehcontrib", "nvehentered", "harmonicmeanspeed", "vehiclelength", "begin", "end"]
            
            # 按优先级选择列
            cols = base_cols + [c for c in data_cols if c in agg_df.columns]
            
            # 如果没有flow字段但有volume字段，将volume复制为flow
            if "flow" not in cols and "volume" in cols:
                agg_df["flow"] = agg_df["volume"]
                cols.append("flow")
                logger.info("已将volume字段复制为flow字段")
            
            logger.info(f"最终输出列: {cols}")
            return agg_df[cols]
        except Exception as e:
            logger.error(f"E1 数据聚合失败: {e}")
            return pd.DataFrame()

    def _parse_single_xml(self, e1_file: Path, simulation_start: datetime) -> pd.DataFrame:
        """解析单个 E1 XML 文件为 DataFrame。
        
        按照实际的SUMO E1检测器输出格式进行解析：
        - 根标签：<detector>
        - 数据标签：<interval> 直接包含所有属性
        - 关键字段：id, begin, end, nVehContrib, flow, occupancy, speed, harmonicMeanSpeed, length, nVehEntered
        
        输出列：detector_id, gantry_id, start_time, end_time, begin, end, flow, volume, speed, occupancy, nVehContrib, nVehEntered
        """
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(e1_file)
            root = tree.getroot()

            # 检查根标签
            if root.tag != "detector":
                logger.warning(f"XML文件 {e1_file} 根标签不是detector: {root.tag}")
                return pd.DataFrame()

            rows: List[Dict[str, Any]] = []
            
            # 解析每个interval标签
            for interval in root.findall("interval"):
                # 获取检测器ID
                detector_id = interval.get("id")
                if not detector_id:
                    logger.warning(f"interval标签缺少id属性: {e1_file}")
                    continue
                    
                # 获取时间区间
                begin_sec = float(interval.get("begin", 0))
                end_sec = float(interval.get("end", 0))
                
                # 获取核心字段 - 直接使用XML属性值，不需要复杂检查
                flow = float(interval.get("flow", 0))                    # 交通流量（辆/小时）
                n_veh_contrib = int(interval.get("nVehContrib", 0))     # 贡献车辆数
                occupancy = float(interval.get("occupancy", 0))         # 占有率
                speed = float(interval.get("speed", 0))                 # 平均速度
                harmonic_mean_speed = float(interval.get("harmonicMeanSpeed", 0))  # 调和平均速度
                vehicle_length = float(interval.get("length", 0))       # 车辆长度
                n_veh_entered = int(interval.get("nVehEntered", 0))    # 进入车辆数
                
                # volume字段（保持向后兼容）
                volume = n_veh_entered
                
                # 转换为绝对时间
                start_time = simulation_start + timedelta(seconds=begin_sec)
                end_time = simulation_start + timedelta(seconds=end_sec)

                # 门架 ID：去掉最后 _车道 后缀
                if detector_id and "_" in detector_id:
                    gantry_id = detector_id.rsplit("_", 1)[0]
                else:
                    gantry_id = detector_id

                # 构建数据行
                row = {
                    "detector_id": detector_id,
                    "gantry_id": gantry_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "begin": begin_sec,
                    "end": end_sec,
                    "flow": flow,                    # 核心字段：交通流量
                    "volume": volume,                # 兼容字段：车辆计数
                    "speed": speed,                  # 平均速度
                    "occupancy": occupancy,          # 占有率
                    "nVehContrib": n_veh_contrib,   # 贡献车辆数
                    "nVehEntered": n_veh_entered,   # 进入车辆数
                    "harmonicMeanSpeed": harmonic_mean_speed,  # 调和平均速度
                    "vehicleLength": vehicle_length, # 车辆长度
                }
                
                rows.append(row)
            
            if not rows:
                logger.warning(f"XML文件 {e1_file} 解析后无数据")
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(rows)
            
            # 验证flow字段
            if "flow" in df.columns:
                flow_stats = df["flow"].describe()
                logger.debug(f"文件 {e1_file.name} flow字段统计: {flow_stats}")
            else:
                logger.error(f"文件 {e1_file.name} flow字段缺失！")
            
            logger.info(f"成功解析E1 XML文件: {e1_file.name}, 数据行数: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"解析 E1 XML 失败 {e1_file}: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
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


