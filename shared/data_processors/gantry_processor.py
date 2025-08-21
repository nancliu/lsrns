"""
门架数据处理模块
负责处理门架数据并生成待比较的CSV文件，专注于精度分析需求
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GantryDataProcessor:
    """门架数据处理器 - 专注于精度分析"""
    
    def __init__(self):
        self.processed_data = {}
        self.alignment_metadata = {}
        
    def load_gantry_data(self, gantry_dir: Path) -> pd.DataFrame:
        """从目录加载门架数据
        
        Args:
            gantry_dir: 包含门架数据文件的目录
            
        Returns:
            加载的门架数据DataFrame
        """
        try:
            if not gantry_dir.exists() or not gantry_dir.is_dir():
                logger.warning(f"门架数据目录不存在或不可用: {gantry_dir}")
                return pd.DataFrame()
            
            # 查找CSV文件
            csv_files = list(gantry_dir.glob("*.csv"))
            if not csv_files:
                logger.warning(f"门架数据目录下未发现CSV文件: {gantry_dir}")
                return pd.DataFrame()
            
            # 加载第一个CSV文件（通常只有一个）
            gantry_file = csv_files[0]
            logger.info(f"加载门架数据文件: {gantry_file}")
            
            # 读取CSV文件
            gantry_data = pd.read_csv(gantry_file)
            
            if gantry_data.empty:
                logger.warning("门架数据文件为空")
                return pd.DataFrame()
            
            logger.info(f"成功加载门架数据: {len(gantry_data)} 条记录")
            return gantry_data
            
        except Exception as e:
            logger.error(f"加载门架数据失败: {e}")
            return pd.DataFrame()

    def process_for_accuracy_analysis(self, gantry_data: pd.DataFrame, 
                                    e1_data: pd.DataFrame) -> Dict[str, Any]:
        """
        处理门架数据用于精度分析
        
        Args:
            gantry_data: 门架原始数据
            e1_data: E1检测器数据
            
        Returns:
            处理结果字典
        """
        try:
            logger.info("开始处理门架数据用于精度分析...")
            
            # 1. 标准化门架数据（不再平移时间）
            processed_gantry = self._standardize_gantry_data(gantry_data)
            
            # 2. 标准化E1数据
            processed_e1 = self._standardize_e1_data(e1_data)
            
            # 3. 生成对齐数据（用于精度分析）
            aligned_data, alignment_metadata = self._align_data_for_accuracy(processed_gantry, processed_e1)
            
            # 4. 保存处理结果
            self.processed_data = {
                "gantry_standardized": processed_gantry,
                "e1_standardized": processed_e1,
                "aligned_data": aligned_data
            }
            
            self.alignment_metadata = alignment_metadata
            
            logger.info("门架数据处理完成")
            return self.processed_data
            
        except Exception as e:
            logger.error(f"门架数据处理失败: {e}")
            return {}
    
    def _standardize_gantry_data(self, gantry_data: pd.DataFrame) -> pd.DataFrame:
        """标准化门架数据格式"""
        try:
            if gantry_data.empty:
                return pd.DataFrame()
            
            # 复制数据
            processed = gantry_data.copy()
            
            # 标准化列名
            processed.columns = [str(col).strip().lower() for col in processed.columns]
            
            # 确保必要列存在
            required_cols = ['gantry_id', 'start_time', 'flow']
            missing_cols = [col for col in required_cols if col not in processed.columns]
            if missing_cols:
                logger.warning(f"门架数据缺少必要列: {missing_cols}")
                return pd.DataFrame()
            
            # 时间处理
            processed['start_time'] = pd.to_datetime(processed['start_time'])
            
            # 直接以区间开始时间生成时间键（用于对齐，精确到分钟）
            processed['time_key'] = processed['start_time'].dt.floor('1min')
            
            # 数据类型转换
            if 'flow' in processed.columns:
                processed['flow'] = pd.to_numeric(processed['flow'], errors='coerce')
            if 'speed' in processed.columns:
                processed['speed'] = pd.to_numeric(processed['speed'], errors='coerce')
            
            # 过滤无效数据
            processed = processed.dropna(subset=['gantry_id', 'start_time', 'flow'])
            
            logger.info(f"门架数据标准化完成: {len(processed)}条记录")
            logger.info(f"时间范围: {processed['start_time'].min()} - {processed['start_time'].max()}")
            # 不再记录调整后时间范围
            
            return processed
            
        except Exception as e:
            logger.error(f"门架数据标准化失败: {e}")
            return pd.DataFrame()
    
    def _standardize_e1_data(self, e1_data: pd.DataFrame) -> pd.DataFrame:
        """标准化E1检测器数据格式"""
        try:
            if e1_data.empty:
                return pd.DataFrame()
            
            # 复制数据
            processed = e1_data.copy()
            
            # 标准化列名
            processed.columns = [str(col).strip().lower() for col in processed.columns]
            
            # 检查并处理列名映射
            # E1数据应该包含detector_id和gantry_id两列
            # detector_id是原始检测器ID（如G420151001000110010_0）
            # gantry_id是门架ID（如G420151001000110010）
            
            # 确保必要列存在
            required_cols = ['gantry_id', 'start_time', 'flow']
            missing_cols = [col for col in required_cols if col not in processed.columns]
            if missing_cols:
                logger.warning(f"E1数据缺少必要列: {missing_cols}")
                logger.warning(f"可用列: {list(processed.columns)}")
                return pd.DataFrame()
            
            # 时间处理：确保start_time是datetime格式
            if 'start_time' in processed.columns:
                processed['start_time'] = pd.to_datetime(processed['start_time'])
            
            # 生成时间键（用于对齐，精确到分钟）
            processed['time_key'] = processed['start_time'].dt.floor('1min')
            
            # 数据类型转换
            if 'flow' in processed.columns:
                processed['flow'] = pd.to_numeric(processed['flow'], errors='coerce')
            if 'speed' in processed.columns:
                processed['speed'] = pd.to_numeric(processed['speed'], errors='coerce')
            if 'occupancy' in processed.columns:
                processed['occupancy'] = pd.to_numeric(processed['occupancy'], errors='coerce')
            
            # 过滤无效数据
            processed = processed.dropna(subset=['gantry_id', 'start_time', 'flow'])
            
            logger.info(f"E1数据标准化完成: {len(processed)}条记录")
            logger.info(f"时间范围: {processed['start_time'].min()} - {processed['start_time'].max()}")
            logger.info(f"门架ID数量: {processed['gantry_id'].nunique()}")
            
            return processed
            
        except Exception as e:
            logger.error(f"E1数据标准化失败: {e}")
            return pd.DataFrame()
    
    def _align_data_for_accuracy(self, gantry_data: pd.DataFrame, 
                                e1_data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """生成用于精度分析的对齐数据（向量化实现，遵循KISS）"""
        try:
            if gantry_data.empty or e1_data.empty:
                logger.warning("门架数据或E1数据为空，无法对齐")
                return pd.DataFrame(), {}

            # 仅保留字段并重命名，便于 merge
            g_cols = ['gantry_id', 'time_key', 'start_time', 'flow', 'speed']
            e_cols = ['gantry_id', 'time_key', 'start_time', 'flow', 'speed', 'occupancy']

            g = gantry_data.copy()
            e = e1_data.copy()

            # 防御性：缺列时安全子集
            g = g[[c for c in g_cols if c in g.columns]]
            e = e[[c for c in e_cols if c in e.columns]]

            # 计算ID交集
            gantry_ids = set(g['gantry_id'].unique()) if 'gantry_id' in g.columns else set()
            e1_ids = set(e['gantry_id'].unique()) if 'gantry_id' in e.columns else set()
            common_ids = gantry_ids.intersection(e1_ids)

            alignment_metadata: Dict[str, Any] = {
                "total_gantry_ids": len(gantry_ids),
                "total_e1_ids": len(e1_ids),
                "matched_ids": len(common_ids),
                "match_rate": (len(common_ids) / len(gantry_ids) * 100) if len(gantry_ids) > 0 else 0,
            }

            if not common_ids:
                logger.warning("门架ID与E1检测器ID无交集，无法进行精度分析")
                return pd.DataFrame(), alignment_metadata

            # 过滤到共同ID
            g = g[g['gantry_id'].isin(list(common_ids))]
            e = e[e['gantry_id'].isin(list(common_ids))]

            # 记录时间范围交集
            if 'time_key' in g.columns and 'time_key' in e.columns:
                gantry_time_range = (g['time_key'].min(), g['time_key'].max())
                e1_time_range = (e['time_key'].min(), e['time_key'].max())
                common_time_range = (max(gantry_time_range[0], e1_time_range[0]), min(gantry_time_range[1], e1_time_range[1]))
                if common_time_range[0] > common_time_range[1]:
                    logger.warning("门架数据与E1数据时间范围无交集，无法进行精度分析")
                    alignment_metadata["time_alignment"] = "failed"
                    alignment_metadata["time_range_gantry"] = [str(gantry_time_range[0]), str(gantry_time_range[1])]
                    alignment_metadata["time_range_e1"] = [str(e1_time_range[0]), str(e1_time_range[1])]
                    return pd.DataFrame(), alignment_metadata
                alignment_metadata["time_alignment"] = "success"
                alignment_metadata["time_range_gantry"] = [str(gantry_time_range[0]), str(gantry_time_range[1])]
                alignment_metadata["time_range_e1"] = [str(e1_time_range[0]), str(e1_time_range[1])]
                alignment_metadata["common_time_range"] = [str(common_time_range[0]), str(common_time_range[1])]

            # 重命名列后合并
            g_renamed = g.rename(columns={
                'start_time': 'gantry_time',
                'flow': 'gantry_flow',
                'speed': 'gantry_speed',
            })
            e_renamed = e.rename(columns={
                'start_time': 'e1_time',
                'flow': 'e1_flow',
                'speed': 'e1_speed',
                'occupancy': 'e1_occupancy',
            })

            merge_keys = [k for k in ['gantry_id', 'time_key'] if k in g_renamed.columns and k in e_renamed.columns]
            if len(merge_keys) < 2:
                logger.warning("对齐所需键缺失，无法进行合并")
                return pd.DataFrame(), alignment_metadata

            aligned_df = g_renamed.merge(e_renamed, on=merge_keys, how='inner')

            logger.info(f"数据对齐完成: {len(aligned_df)}条记录")
            if not aligned_df.empty and 'time_key' in aligned_df.columns:
                logger.info(f"对齐数据时间范围: {aligned_df['time_key'].min()} - {aligned_df['time_key'].max()}")
            if not aligned_df.empty and 'gantry_id' in aligned_df.columns:
                logger.info(f"对齐数据门架数量: {aligned_df['gantry_id'].nunique()}")

            alignment_metadata["final_aligned_records"] = int(len(aligned_df))
            alignment_metadata["final_aligned_gantries"] = int(aligned_df['gantry_id'].nunique()) if not aligned_df.empty and 'gantry_id' in aligned_df.columns else 0
            alignment_metadata["final_time_points"] = int(aligned_df['time_key'].nunique()) if not aligned_df.empty and 'time_key' in aligned_df.columns else 0

            return aligned_df, alignment_metadata

        except Exception as e:
            logger.error(f"数据对齐失败: {e}")
            return pd.DataFrame(), {}
    
    def export_analysis_csvs(self, output_dir: Path) -> Dict[str, str]:
        """导出精度分析用的CSV文件"""
        try:
            if not self.processed_data:
                logger.warning("没有处理后的数据，无法导出CSV")
                return {}
            
            output_dir.mkdir(parents=True, exist_ok=True)
            exported_files = {}
            
            # 1. 导出门架标准化数据
            if "gantry_standardized" in self.processed_data:
                gantry_file = output_dir / "gantry_data_standardized.csv"
                self.processed_data["gantry_standardized"].to_csv(gantry_file, index=False, encoding="utf-8-sig")
                exported_files["gantry_data_standardized.csv"] = str(gantry_file)
                logger.info(f"导出门架标准化数据: {gantry_file}")
            
            # 2. 导出E1标准化数据
            if "e1_standardized" in self.processed_data:
                e1_file = output_dir / "e1_data_standardized.csv"
                self.processed_data["e1_standardized"].to_csv(e1_file, index=False, encoding="utf-8-sig")
                exported_files["e1_data_standardized.csv"] = str(e1_file)
                logger.info(f"导出E1标准化数据: {e1_file}")
            
            # 3. 导出对齐数据（用于精度分析）
            if "aligned_data" in self.processed_data:
                aligned_file = output_dir / "aligned_data_for_accuracy.csv"
                self.processed_data["aligned_data"].to_csv(aligned_file, index=False, encoding="utf-8-sig")
                exported_files["aligned_data_for_accuracy.csv"] = str(aligned_file)
                logger.info(f"导出对齐数据: {aligned_file}")
            
            # 4. 导出对齐元数据
            if self.alignment_metadata:
                metadata_file = output_dir / "alignment_metadata.json"
                import json
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.alignment_metadata, f, ensure_ascii=False, indent=2, default=str)
                exported_files["alignment_metadata.json"] = str(metadata_file)
                logger.info(f"导出对齐元数据: {metadata_file}")
            
            logger.info(f"CSV文件导出完成: {len(exported_files)}个文件")
            return exported_files
            
        except Exception as e:
            logger.error(f"导出CSV文件失败: {e}")
            return {}
    
    def get_aligned_data(self) -> pd.DataFrame:
        """获取对齐后的数据"""
        return self.processed_data.get("aligned_data", pd.DataFrame())
    
    def get_alignment_metadata(self) -> Dict[str, Any]:
        """获取对齐元数据"""
        return self.alignment_metadata
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要信息"""
        summary = {}
        
        if "gantry_standardized" in self.processed_data:
            gantry_data = self.processed_data["gantry_standardized"]
            if not gantry_data.empty:
                summary["gantry"] = {
                    "total_records": len(gantry_data),
                    "unique_gantries": gantry_data['gantry_id'].nunique() if 'gantry_id' in gantry_data.columns else 0,
                    "time_range": f"{gantry_data['start_time'].min()} - {gantry_data['start_time'].max()}" if 'start_time' in gantry_data.columns else "N/A"
                }
        
        if "e1_standardized" in self.processed_data:
            e1_data = self.processed_data["e1_standardized"]
            if not e1_data.empty:
                summary["e1"] = {
                    "total_records": len(e1_data),
                    "unique_detectors": e1_data['gantry_id'].nunique() if 'gantry_id' in e1_data.columns else 0,
                    "time_range": f"{e1_data['start_time'].min()} - {e1_data['start_time'].max()}" if 'start_time' in e1_data.columns else "N/A"
                }
        
        if "aligned_data" in self.processed_data:
            aligned_data = self.processed_data["aligned_data"]
            if not aligned_data.empty:
                summary["aligned"] = {
                    "total_records": len(aligned_data),
                    "unique_gantries": aligned_data['gantry_id'].nunique() if 'gantry_id' in aligned_data.columns else 0,
                    "time_points": aligned_data['time_key'].nunique() if 'time_key' in aligned_data.columns else 0
                }
        
        # 添加对齐元数据
        if self.alignment_metadata:
            summary["alignment_metadata"] = self.alignment_metadata
        
        return summary
