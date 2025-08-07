"""
精度指标计算模块
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class MetricsCalculator:
    """精度指标计算器"""
    
    def __init__(self, mape_threshold: float = 15.0, geh_threshold: float = 5.0):
        """
        初始化精度指标计算器
        
        Args:
            mape_threshold: MAPE阈值，默认15%
            geh_threshold: GEH阈值，默认5
        """
        self.mape_threshold = mape_threshold
        self.geh_threshold = geh_threshold
    
    @staticmethod
    def calculate_mape(simulated: np.ndarray, observed: np.ndarray) -> float:
        """
        计算MAPE (Mean Absolute Percentage Error)
        
        Args:
            simulated: 仿真值数组
            observed: 观测值数组
            
        Returns:
            MAPE值（百分比）
        """
        # 确保输入为numpy数组
        simulated = np.asarray(simulated)
        observed = np.asarray(observed)
        
        # 过滤掉观测值为0的情况
        mask = observed != 0
        if not mask.any():
            return np.nan
        
        sim_filtered = simulated[mask]
        obs_filtered = observed[mask]
        
        # 计算MAPE
        mape = np.mean(np.abs((sim_filtered - obs_filtered) / obs_filtered)) * 100
        
        return mape
    
    @staticmethod
    def calculate_geh(simulated: np.ndarray, observed: np.ndarray) -> np.ndarray:
        """
        计算GEH (Geoffrey E. Havers)指标
        
        Args:
            simulated: 仿真值数组
            observed: 观测值数组
            
        Returns:
            GEH值数组
        """
        # 确保输入为numpy数组
        simulated = np.asarray(simulated, dtype=float)
        observed = np.asarray(observed, dtype=float)
        
        # 计算分母
        denominator = (simulated + observed) / 2
        
        # 处理分母为0的情况
        mask = denominator != 0
        geh_values = np.full_like(simulated, np.nan)
        
        if mask.any():
            geh_values[mask] = np.sqrt((simulated[mask] - observed[mask]) ** 2 / denominator[mask])
        
        return geh_values
    
    def calculate_geh_mean(self, simulated: np.ndarray, observed: np.ndarray) -> float:
        """
        计算平均GEH值
        
        Args:
            simulated: 仿真值数组
            observed: 观测值数组
            
        Returns:
            平均GEH值
        """
        geh_values = self.calculate_geh(simulated, observed)
        return np.nanmean(geh_values)
    
    def calculate_geh_pass_rate(self, simulated: np.ndarray, observed: np.ndarray) -> float:
        """
        计算GEH合格率（GEH <= 5的比例）
        
        Args:
            simulated: 仿真值数组
            observed: 观测值数组
            
        Returns:
            GEH合格率（百分比）
        """
        geh_values = self.calculate_geh(simulated, observed)
        valid_geh = geh_values[~np.isnan(geh_values)]
        
        if len(valid_geh) == 0:
            return 0.0
        
        pass_rate = np.mean(valid_geh <= self.geh_threshold) * 100
        return pass_rate
    
    def calculate_all_metrics(self, sim_values: np.ndarray, obs_values: np.ndarray) -> Dict[str, float]:
        """
        计算所有精度指标
        
        Args:
            sim_values: 仿真值数组
            obs_values: 观测值数组
            
        Returns:
            包含所有精度指标的字典
        """
        # 过滤无效数据
        mask = ~(np.isnan(sim_values) | np.isnan(obs_values) | (obs_values == 0))
        sim_filtered = sim_values[mask]
        obs_filtered = obs_values[mask]
        
        if len(sim_filtered) == 0:
            return {
                'mape': np.nan,
                'geh_mean': np.nan,
                'geh_pass_rate': 0.0,
                'sample_size': 0
            }
        
        metrics = {
            'mape': self.calculate_mape(sim_filtered, obs_filtered),
            'geh_mean': self.calculate_geh_mean(sim_filtered, obs_filtered),
            'geh_pass_rate': self.calculate_geh_pass_rate(sim_filtered, obs_filtered),
            'sample_size': len(sim_filtered)
        }
        
        return metrics
    
    def calculate_group_metrics(self, df: pd.DataFrame, 
                             sim_col: str = 'sim_flow', 
                             obs_col: str = 'obs_flow',
                             group_col: str = 'gantry_id') -> pd.DataFrame:
        """
        按组计算精度指标
        
        Args:
            df: 包含仿真和观测数据的DataFrame
            sim_col: 仿真流量列名
            obs_col: 观测流量列名
            group_col: 分组列名
            
        Returns:
            包含分组精度指标的DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        results = []
        
        for group_name, group_data in df.groupby(group_col):
            sim_values = group_data[sim_col].values
            obs_values = group_data[obs_col].values
            
            metrics = self.calculate_all_metrics(sim_values, obs_values)
            metrics[group_col] = group_name
            
            # 计算额外统计信息
            metrics['total_sim_flow'] = np.nansum(sim_values)
            metrics['total_obs_flow'] = np.nansum(obs_values)
            metrics['flow_ratio'] = metrics['total_sim_flow'] / metrics['total_obs_flow'] if metrics['total_obs_flow'] > 0 else np.nan
            metrics['record_count'] = len(group_data)
            
            results.append(metrics)
        
        return pd.DataFrame(results)
    
    def calculate_time_interval_metrics(self, df: pd.DataFrame,
                                      sim_col: str = 'sim_flow',
                                      obs_col: str = 'obs_flow',
                                      time_col: str = 'interval_start') -> pd.DataFrame:
        """
        按时间间隔计算精度指标
        
        Args:
            df: 包含仿真和观测数据的DataFrame
            sim_col: 仿真流量列名
            obs_col: 观测流量列名
            time_col: 时间列名
            
        Returns:
            包含时间间隔精度指标的DataFrame
        """
        if df.empty:
            return pd.DataFrame()
        
        # 添加详细的GEH计算
        df['geh'] = self.calculate_geh(df[sim_col].values, df[obs_col].values)
        df['mape'] = np.abs((df[sim_col] - df[obs_col]) / df[obs_col]) * 100
        df['mape'] = df['mape'].replace([np.inf, -np.inf], np.nan)
        
        # 按时间间隔分组计算指标
        time_metrics = df.groupby(time_col).agg({
            sim_col: 'sum',
            obs_col: 'sum',
            'geh': 'mean',
            'mape': 'mean'
        }).reset_index()
        
        # 重命名列
        time_metrics.columns = [time_col, 'total_sim_flow', 'total_obs_flow', 'geh_mean', 'mape_mean']
        
        # 计算GEH合格率
        geh_pass_rates = df.groupby(time_col).apply(
            lambda x: np.mean(x['geh'] <= self.geh_threshold) * 100 if len(x) > 0 else 0
        ).reset_index(name='geh_pass_rate')
        
        time_metrics = time_metrics.merge(geh_pass_rates, on=time_col)
        
        # 计算流量比例
        time_metrics['flow_ratio'] = time_metrics['total_sim_flow'] / time_metrics['total_obs_flow']
        time_metrics['flow_ratio'] = time_metrics['flow_ratio'].replace([np.inf, -np.inf], np.nan)
        
        return time_metrics
    
    def generate_accuracy_summary(self, df: pd.DataFrame,
                                sim_col: str = 'sim_flow',
                                obs_col: str = 'obs_flow') -> Dict[str, Any]:
        """
        生成精度分析摘要
        
        Args:
            df: 包含仿真和观测数据的DataFrame
            sim_col: 仿真流量列名
            obs_col: 观测流量列名
            
        Returns:
            精度分析摘要字典
        """
        if df.empty:
            return {}
        
        sim_values = df[sim_col].values
        obs_values = df[obs_col].values
        
        # 计算总体指标
        overall_metrics = self.calculate_all_metrics(sim_values, obs_values)
        
        # 计算分组指标
        group_metrics = self.calculate_group_metrics(df, sim_col, obs_col, 'gantry_id')
        
        # 计算时间间隔指标
        time_metrics = self.calculate_time_interval_metrics(df, sim_col, obs_col, 'interval_start')
        
        # 统计信息
        summary = {
            'overall_metrics': overall_metrics,
            'group_metrics': group_metrics,
            'time_metrics': time_metrics,
            'data_statistics': {
                'total_records': len(df),
                'unique_gantry_ids': df['gantry_id'].nunique() if 'gantry_id' in df.columns else 0,
                'unique_time_intervals': df['interval_start'].nunique() if 'interval_start' in df.columns else 0,
                'total_sim_flow': np.nansum(sim_values),
                'total_obs_flow': np.nansum(obs_values)
            }
        }
        
        return summary
    
    def get_accuracy_level(self, mape: float) -> str:
        """
        根据MAPE值获取精度等级
        
        Args:
            mape: MAPE值
            
        Returns:
            精度等级描述
        """
        if pd.isna(mape):
            return "无法计算"
        elif mape <= 10:
            return "优秀"
        elif mape <= 15:
            return "良好"
        elif mape <= 20:
            return "一般"
        elif mape <= 30:
            return "较差"
        else:
            return "很差"
    
    def get_geh_accuracy_level(self, geh_pass_rate: float) -> str:
        """
        根据GEH合格率获取精度等级
        
        Args:
            geh_pass_rate: GEH合格率
            
        Returns:
            精度等级描述
        """
        if geh_pass_rate >= 85:
            return "优秀"
        elif geh_pass_rate >= 75:
            return "良好"
        elif geh_pass_rate >= 60:
            return "一般"
        elif geh_pass_rate >= 40:
            return "较差"
        else:
            return "很差"