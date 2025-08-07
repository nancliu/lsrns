"""
数据加载模块
"""

import os
import psycopg2
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

from .utils import DB_CONFIG, get_table_names_from_date, validate_dataframe, clean_numeric_data, log_analysis_progress

class DataLoader:
    """数据加载器"""
    
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """
        初始化数据加载器
        
        Args:
            db_config: 数据库配置字典
        """
        self.db_config = db_config or DB_CONFIG
        self.connection = None
    
    def connect_database(self) -> bool:
        """
        连接数据库
        
        Returns:
            连接是否成功
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            log_analysis_progress("数据库连接成功")
            return True
        except Exception as e:
            log_analysis_progress(f"数据库连接失败: {e}", "ERROR")
            return False
    
    def disconnect_database(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            log_analysis_progress("数据库连接已断开")
    
    def load_gantry_data(self, start_time: datetime, end_time: datetime, 
                        gantry_ids: Optional[List[str]] = None,
                        time_interval: int = 5) -> pd.DataFrame:
        """
        从数据库加载门架流量数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            gantry_ids: 门架ID列表，如果为None则查询所有门架
            time_interval: 时间间隔（分钟）
            
        Returns:
            门架流量数据DataFrame
        """
        if not self.connect_database():
            return pd.DataFrame()
        
        try:
            # 获取表名
            table_names = get_table_names_from_date(start_time)
            gantry_table = table_names['gantry_table']
            
            # 构建查询语句
            query = f"""
                SELECT start_gantryid, start_time, k1, k2, k3, k4, h1, h2, h3, h4, h5, h6
                FROM dwd.{gantry_table}
                WHERE start_time >= %s
                  AND start_time < %s
            """
            
            params = [start_time, end_time]
            
            # 如果指定了门架ID，添加过滤条件
            if gantry_ids:
                query += " AND start_gantryid = ANY(%s)"
                params.append(gantry_ids)
            
            query += " ORDER BY start_gantryid, start_time"
            
            # 执行查询
            df = pd.read_sql_query(query, self.connection, params=params)
            
            if df.empty:
                log_analysis_progress("未查询到门架数据", "WARNING")
                return pd.DataFrame()
            
            log_analysis_progress(f"查询到 {len(df)} 条门架数据")
            
            # 数据清理和转换
            df = self._process_gantry_data(df, time_interval)
            
            return df
            
        except Exception as e:
            log_analysis_progress(f"查询门架数据失败: {e}", "ERROR")
            return pd.DataFrame()
        finally:
            self.disconnect_database()
    
    def _process_gantry_data(self, df: pd.DataFrame, time_interval: int) -> pd.DataFrame:
        """
        处理门架数据
        
        Args:
            df: 原始门架数据
            time_interval: 时间间隔（分钟）
            
        Returns:
            处理后的门架数据
        """
        # 确保时间列为datetime类型
        df['start_time'] = pd.to_datetime(df['start_time'])
        
        # 计算总流量
        flow_columns = ['k1', 'k2', 'k3', 'k4', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        # 清理数值数据
        df = clean_numeric_data(df, flow_columns)
        
        # 计算总流量
        df['total_flow'] = df[flow_columns].sum(axis=1)
        
        # 按时间间隔聚合
        df['interval_start'] = df['start_time'].dt.floor(f'{time_interval}min')
        
        # 按门架ID和时间间隔聚合
        df_agg = df.groupby(['start_gantryid', 'interval_start']).agg({
            'total_flow': 'sum',
            **{col: 'sum' for col in flow_columns}
        }).reset_index()
        
        # 重命名列以保持一致性
        df_agg = df_agg.rename(columns={'start_gantryid': 'gantry_id'})
        
        # 将interval_start转换为分钟数（与仿真数据保持一致）
        df_agg['interval_start'] = (df_agg['interval_start'].dt.hour * 60 + df_agg['interval_start'].dt.minute).astype(int)
        
        log_analysis_progress(f"门架数据聚合完成，共 {len(df_agg)} 条记录")
        
        return df_agg
    
    def load_detector_data(self, e1_folder: str, time_interval: int = 5, sim_start_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        从E1检测器XML文件加载数据
        
        Args:
            e1_folder: E1检测器数据文件夹路径
            time_interval: 时间间隔（分钟）
            sim_start_time: 仿真开始时间，用于转换相对时间为绝对时间
            
        Returns:
            检测器数据DataFrame
        """
        if not os.path.exists(e1_folder):
            log_analysis_progress(f"E1文件夹不存在: {e1_folder}", "ERROR")
            return pd.DataFrame()
        
        detector_data = []
        
        # 遍历E1文件夹中的所有XML文件
        for filename in os.listdir(e1_folder):
            if filename.endswith('.xml'):
                file_path = os.path.join(e1_folder, filename)
                
                try:
                    # 解析XML文件
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    # 从文件名提取检测器ID
                    detector_id = filename.replace('.xml', '')
                    
                    # 解析interval数据
                    for interval in root.findall('interval'):
                        begin_time = float(interval.get('begin', 0))
                        end_time = float(interval.get('end', 0))
                        nVehContrib = float(interval.get('nVehContrib', 0))
                        
                        # 计算时间间隔起始分钟数
                        interval_start_min = int(begin_time // 60)
                        interval_group = (interval_start_min // time_interval) * time_interval
                        
                        # 如果提供了仿真开始时间，转换为绝对时间（从午夜开始的分钟数）
                        if sim_start_time:
                            # 计算仿真开始时间从午夜开始的分钟数
                            sim_start_minutes = sim_start_time.hour * 60 + sim_start_time.minute
                            # 将相对时间转换为绝对时间
                            interval_group += sim_start_minutes
                        
                        # 提取门架ID（从检测器ID中提取）
                        gantry_id = detector_id.split('_')[0] if '_' in detector_id else detector_id
                        
                        detector_data.append({
                            'detector_id': detector_id,
                            'gantry_id': gantry_id,
                            'interval_start': interval_group,
                            'sim_flow': nVehContrib,
                            'begin_time': begin_time,
                            'end_time': end_time
                        })
                
                except Exception as e:
                    log_analysis_progress(f"解析文件 {filename} 失败: {e}", "WARNING")
                    continue
        
        if not detector_data:
            log_analysis_progress("未找到有效的检测器数据", "WARNING")
            return pd.DataFrame()
        
        # 创建DataFrame
        df_detector = pd.DataFrame(detector_data)
        
        # 按门架ID和时间间隔聚合
        df_agg = df_detector.groupby(['gantry_id', 'interval_start']).agg({
            'sim_flow': 'sum'
        }).reset_index()
        
        log_analysis_progress(f"检测器数据加载完成，共 {len(df_agg)} 条记录")
        
        return df_agg
    
    def load_detector_config(self, config_file: str) -> List[Dict[str, str]]:
        """
        加载检测器配置文件
        
        Args:
            config_file: 检测器配置文件路径
            
        Returns:
            检测器配置列表
        """
        if not os.path.exists(config_file):
            log_analysis_progress(f"检测器配置文件不存在: {config_file}", "ERROR")
            return []
        
        detectors = []
        
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            
            for detector in root.findall('inductionLoop'):
                detector_id = detector.get('id')
                file_name = detector.get('file')
                lane_id = detector.get('lane')
                
                if detector_id and file_name:
                    detectors.append({
                        'detector_id': detector_id,
                        'file': file_name,
                        'lane_id': lane_id
                    })
            
            log_analysis_progress(f"加载了 {len(detectors)} 个检测器配置")
            
        except Exception as e:
            log_analysis_progress(f"解析检测器配置文件失败: {e}", "ERROR")
        
        return detectors
    
    def save_gantry_data(self, df: pd.DataFrame, output_folder: str) -> bool:
        """
        保存门架数据到本地文件
        
        Args:
            df: 门架数据DataFrame
            output_folder: 输出文件夹路径
            
        Returns:
            保存是否成功
        """
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            # 保存原始数据
            raw_file = os.path.join(output_folder, 'gantry_data_raw.csv')
            df.to_csv(raw_file, index=False, encoding='utf-8-sig')
            
            # 保存汇总数据
            summary_file = os.path.join(output_folder, 'gantry_summary.csv')
            summary_df = df.groupby('gantry_id').agg({
                'total_flow': 'sum',
                'interval_start': 'count'
            }).reset_index()
            summary_df.columns = ['gantry_id', 'total_flow', 'time_intervals']
            summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
            
            log_analysis_progress(f"门架数据已保存到: {output_folder}")
            return True
            
        except Exception as e:
            log_analysis_progress(f"保存门架数据失败: {e}", "ERROR")
            return False
    
    def load_saved_gantry_data(self, gantry_folder: str) -> pd.DataFrame:
        """
        从本地文件加载已保存的门架数据
        
        Args:
            gantry_folder: 门架数据文件夹路径
            
        Returns:
            门架数据DataFrame
        """
        raw_file = os.path.join(gantry_folder, 'gantry_data_raw.csv')
        
        if not os.path.exists(raw_file):
            log_analysis_progress(f"门架数据文件不存在: {raw_file}", "WARNING")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(raw_file)
            # 如果interval_start是字符串格式的时间，先转换为datetime，再转换为分钟数
            if df['interval_start'].dtype == 'object':
                try:
                    # 尝试解析为datetime
                    df['interval_start'] = pd.to_datetime(df['interval_start'])
                    # 转换为分钟数
                    df['interval_start'] = (df['interval_start'].dt.hour * 60 + df['interval_start'].dt.minute).astype(int)
                except:
                    # 如果解析失败，直接转换为numeric
                    df['interval_start'] = pd.to_numeric(df['interval_start'])
            else:
                df['interval_start'] = pd.to_numeric(df['interval_start'])
            log_analysis_progress(f"从本地加载了 {len(df)} 条门架数据")
            return df
            
        except Exception as e:
            log_analysis_progress(f"加载门架数据失败: {e}", "ERROR")
            return pd.DataFrame()
    
    def merge_simulation_and_observed_data(self, df_sim: pd.DataFrame, df_obs: pd.DataFrame) -> pd.DataFrame:
        """
        合并仿真数据和观测数据
        
        Args:
            df_sim: 仿真数据DataFrame
            df_obs: 观测数据DataFrame
            
        Returns:
            合并后的DataFrame
        """
        if df_sim.empty or df_obs.empty:
            log_analysis_progress("仿真数据或观测数据为空", "WARNING")
            return pd.DataFrame()
        
        # 重命名列以便合并
        df_sim_renamed = df_sim.rename(columns={'sim_flow': 'sim_flow'})
        df_obs_renamed = df_obs.rename(columns={'total_flow': 'obs_flow'})
        
        # 合并数据
        df_merged = pd.merge(
            df_sim_renamed,
            df_obs_renamed,
            on=['gantry_id', 'interval_start'],
            how='inner'
        )
        
        if df_merged.empty:
            log_analysis_progress("合并后的数据为空，请检查数据匹配情况", "WARNING")
            return pd.DataFrame()
        
        log_analysis_progress(f"数据合并完成，共 {len(df_merged)} 条匹配记录")
        
        return df_merged
    
    def validate_data_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证数据完整性
        
        Args:
            df: 合并后的数据DataFrame
            
        Returns:
            数据完整性验证结果
        """
        if df.empty:
            return {'valid': False, 'message': '数据为空'}
        
        validation_result = {
            'valid': True,
            'message': '',
            'statistics': {
                'total_records': len(df),
                'unique_gantry_ids': df['gantry_id'].nunique(),
                'unique_time_intervals': df['interval_start'].nunique(),
                'missing_sim_flow': df['sim_flow'].isnull().sum(),
                'missing_obs_flow': df['obs_flow'].isnull().sum(),
                'zero_obs_flow': (df['obs_flow'] == 0).sum(),
                'negative_sim_flow': (df['sim_flow'] < 0).sum(),
                'negative_obs_flow': (df['obs_flow'] < 0).sum()
            }
        }
        
        # 检查数据质量问题
        issues = []
        
        if validation_result['statistics']['missing_sim_flow'] > 0:
            issues.append(f"仿真流量缺失 {validation_result['statistics']['missing_sim_flow']} 条")
        
        if validation_result['statistics']['missing_obs_flow'] > 0:
            issues.append(f"观测流量缺失 {validation_result['statistics']['missing_obs_flow']} 条")
        
        if validation_result['statistics']['zero_obs_flow'] > 0:
            issues.append(f"观测流量为0的有 {validation_result['statistics']['zero_obs_flow']} 条")
        
        if validation_result['statistics']['negative_sim_flow'] > 0:
            issues.append(f"仿真流量为负值的有 {validation_result['statistics']['negative_sim_flow']} 条")
        
        if validation_result['statistics']['negative_obs_flow'] > 0:
            issues.append(f"观测流量为负值的有 {validation_result['statistics']['negative_obs_flow']} 条")
        
        if issues:
            validation_result['valid'] = False
            validation_result['message'] = '; '.join(issues)
        
        return validation_result