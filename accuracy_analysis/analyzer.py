"""
主分析器模块
"""

import os
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

from .data_loader import DataLoader
from .metrics import MetricsCalculator
from .report_generator import ReportGenerator
from .utils import (
    parse_time_from_filename, find_folder_with_prefix, 
    create_timestamp_folder, copy_folder_with_new_name,
    log_analysis_progress, get_table_names_from_date,
    validate_dataframe, ANALYSIS_CONFIG
)

class AccuracyAnalyzer:
    """仿真精度分析器"""
    
    def __init__(self, run_folder: str, output_base_folder: str = "accuracy_analysis"):
        """
        初始化精度分析器
        
        Args:
            run_folder: 运行文件夹路径
            output_base_folder: 输出基础文件夹路径
        """
        self.run_folder = run_folder
        self.output_base_folder = output_base_folder
        self.config = ANALYSIS_CONFIG.copy()
        
        # 初始化组件
        self.data_loader = DataLoader()
        self.metrics_calculator = MetricsCalculator(
            mape_threshold=self.config['mape_threshold'],
            geh_threshold=self.config['geh_threshold']
        )
        self.report_generator = None
        
        # 解析时间范围
        self.start_time, self.end_time = self._parse_time_from_run_folder()
        
        # 查找数据文件夹
        self.e1_folder = self._find_e1_folder()
        self.gantry_folder = self._find_gantry_folder()
        
        # 创建输出文件夹
        self.output_folder = self._create_output_folder()
        
        # 初始化报告生成器
        self.report_generator = ReportGenerator(self.output_folder)
        
        log_analysis_progress(f"精度分析器初始化完成")
        log_analysis_progress(f"运行文件夹: {self.run_folder}")
        log_analysis_progress(f"时间范围: {self.start_time} ~ {self.end_time}")
        log_analysis_progress(f"E1数据文件夹: {self.e1_folder}")
        log_analysis_progress(f"Gantry数据文件夹: {self.gantry_folder}")
        log_analysis_progress(f"输出文件夹: {self.output_folder}")
    
    def _parse_time_from_run_folder(self) -> Tuple[datetime, datetime]:
        """
        从运行文件夹解析时间范围
        
        Returns:
            开始时间和结束时间的元组
        """
        try:
            # 查找OD文件
            od_files = [f for f in os.listdir(self.run_folder) if f.endswith('.od.xml')]
            
            if not od_files:
                raise ValueError(f"在运行文件夹 {self.run_folder} 中未找到OD文件")
            
            # 使用第一个OD文件解析时间
            od_file = od_files[0]
            return parse_time_from_filename(od_file)
            
        except Exception as e:
            log_analysis_progress(f"解析时间范围失败: {e}", "ERROR")
            raise
    
    def _find_e1_folder(self) -> Optional[str]:
        """
        查找E1数据文件夹
        
        Returns:
            E1文件夹路径，如果未找到则返回None
        """
        # 查找e1_*格式的文件夹
        e1_folder = find_folder_with_prefix(self.run_folder, "e1_")
        
        if e1_folder:
            log_analysis_progress(f"找到E1数据文件夹: {e1_folder}")
            return e1_folder
        
        # 如果没有找到，尝试从根目录的e1文件夹复制
        base_e1_path = os.path.join(os.path.dirname(self.run_folder), "e1")
        
        if os.path.exists(base_e1_path):
            # 创建新的e1文件夹
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_e1_path = os.path.join(self.run_folder, f"e1_{timestamp}")
            
            try:
                if copy_folder_with_new_name(base_e1_path, new_e1_path):
                    log_analysis_progress(f"已复制E1数据到: {new_e1_path}")
                    return new_e1_path
                else:
                    # 如果复制失败，直接使用根目录的e1文件夹
                    log_analysis_progress(f"复制失败，直接使用根目录E1数据: {base_e1_path}")
                    return base_e1_path
            except Exception as e:
                log_analysis_progress(f"复制E1数据时出错: {e}，直接使用根目录E1数据")
                return base_e1_path
        
        log_analysis_progress("未找到E1数据文件夹", "WARNING")
        return None
    
    def _find_gantry_folder(self) -> Optional[str]:
        """
        查找Gantry数据文件夹
        
        Returns:
            Gantry文件夹路径，如果未找到则返回None
        """
        # 查找gantry_*格式的文件夹
        gantry_folder = find_folder_with_prefix(self.run_folder, "gantry_")
        
        if gantry_folder:
            log_analysis_progress(f"找到Gantry数据文件夹: {gantry_folder}")
            return gantry_folder
        
        log_analysis_progress("未找到Gantry数据文件夹", "INFO")
        return None
    
    def _create_output_folder(self) -> str:
        """
        创建输出文件夹
        
        Returns:
            输出文件夹路径
        """
        os.makedirs(self.output_base_folder, exist_ok=True)
        output_folder = create_timestamp_folder(self.output_base_folder, "accuracy_results")
        log_analysis_progress(f"创建输出文件夹: {output_folder}")
        return output_folder
    
    def _prepare_gantry_data(self) -> pd.DataFrame:
        """
        准备门架数据
        
        Returns:
            门架数据DataFrame
        """
        # 如果已存在gantry数据文件夹，尝试从本地加载
        if self.gantry_folder:
            df_gantry = self.data_loader.load_saved_gantry_data(self.gantry_folder)
            
            if not df_gantry.empty:
                log_analysis_progress("从本地文件加载门架数据成功")
                return df_gantry
        
        # 否则从数据库加载
        log_analysis_progress("从数据库加载门架数据...")
        df_gantry = self.data_loader.load_gantry_data(
            self.start_time,
            self.end_time,
            time_interval=self.config['time_interval']
        )
        
        if df_gantry.empty:
            log_analysis_progress("无法获取门架数据", "ERROR")
            return pd.DataFrame()
        
        # 保存门架数据到本地
        if not self.gantry_folder:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.gantry_folder = os.path.join(self.run_folder, f"gantry_{timestamp}")
        
        self.data_loader.save_gantry_data(df_gantry, self.gantry_folder)
        
        return df_gantry
    
    def _prepare_detector_data(self) -> pd.DataFrame:
        """
        准备检测器数据
        
        Returns:
            检测器数据DataFrame
        """
        if not self.e1_folder:
            log_analysis_progress("未找到E1数据文件夹", "ERROR")
            return pd.DataFrame()
        
        log_analysis_progress("加载检测器数据...")
        df_detector = self.data_loader.load_detector_data(
            self.e1_folder,
            time_interval=self.config['time_interval'],
            sim_start_time=self.start_time
        )
        
        return df_detector
    
    def analyze_accuracy(self) -> Dict[str, Any]:
        """
        执行完整的精度分析流程
        
        Returns:
            分析结果字典
        """
        try:
            log_analysis_progress("开始精度分析...")
            
            # 准备数据
            df_gantry = self._prepare_gantry_data()
            df_detector = self._prepare_detector_data()
            
            if df_gantry.empty or df_detector.empty:
                return {
                    'success': False,
                    'error': '数据准备失败',
                    'output_folder': self.output_folder
                }
            
            # 合并数据
            df_merged = self.data_loader.merge_simulation_and_observed_data(
                df_detector, df_gantry
            )
            
            if df_merged.empty:
                return {
                    'success': False,
                    'error': '数据合并失败',
                    'output_folder': self.output_folder
                }
            
            # 验证数据完整性
            validation_result = self.data_loader.validate_data_completeness(df_merged)
            if not validation_result['valid']:
                log_analysis_progress(f"数据完整性验证失败: {validation_result['message']}", "WARNING")
            
            # 计算精度指标
            log_analysis_progress("计算精度指标...")
            accuracy_summary = self.metrics_calculator.generate_accuracy_summary(
                df_merged, 'sim_flow', 'obs_flow'
            )
            
            # 生成详细分析结果
            detailed_results = self._generate_detailed_results(df_merged)
            
            # 生成报告
            log_analysis_progress("生成分析报告...")
            report_files = self.report_generator.generate_all_reports(
                accuracy_summary, detailed_results, df_merged
            )
            
            # 保存原始数据
            self._save_raw_data(df_merged)
            
            log_analysis_progress("精度分析完成")
            
            return {
                'success': True,
                'output_folder': self.output_folder,
                'accuracy_summary': accuracy_summary,
                'detailed_results': detailed_results,
                'report_files': report_files,
                'data_validation': validation_result
            }
            
        except Exception as e:
            log_analysis_progress(f"精度分析过程中发生错误: {e}", "ERROR")
            return {
                'success': False,
                'error': str(e),
                'output_folder': self.output_folder
            }
    
    def _generate_detailed_results(self, df_merged: pd.DataFrame) -> Dict[str, Any]:
        """
        生成详细分析结果
        
        Args:
            df_merged: 合并后的数据
            
        Returns:
            详细分析结果字典
        """
        detailed_results = {}
        
        # 计算每条记录的精度指标
        df_merged['mape'] = np.abs((df_merged['sim_flow'] - df_merged['obs_flow']) / df_merged['obs_flow']) * 100
        df_merged['mape'] = df_merged['mape'].replace([np.inf, -np.inf], np.nan)
        df_merged['geh'] = self.metrics_calculator.calculate_geh(
            df_merged['sim_flow'].values, df_merged['obs_flow'].values
        )
        
        # 门架级别分析
        gantry_metrics = self.metrics_calculator.calculate_group_metrics(
            df_merged, 'sim_flow', 'obs_flow', 'gantry_id'
        )
        detailed_results['gantry_metrics'] = gantry_metrics
        
        # 时间间隔分析
        time_metrics = self.metrics_calculator.calculate_time_interval_metrics(
            df_merged, 'sim_flow', 'obs_flow', 'interval_start'
        )
        detailed_results['time_metrics'] = time_metrics
        
        # 异常值分析
        detailed_results['anomaly_analysis'] = self._analyze_anomalies(df_merged)
        
        # 统计分析
        detailed_results['statistical_analysis'] = self._statistical_analysis(df_merged)
        
        return detailed_results
    
    def _analyze_anomalies(self, df_merged: pd.DataFrame) -> Dict[str, Any]:
        """
        异常值分析
        
        Args:
            df_merged: 合并后的数据
            
        Returns:
            异常值分析结果
        """
        anomalies = {
            'high_mape_records': df_merged[df_merged['mape'] > self.config['mape_threshold']],
            'high_geh_records': df_merged[df_merged['geh'] > self.config['geh_threshold']],
            'zero_flow_records': df_merged[df_merged['obs_flow'] == 0],
            'extreme_ratio_records': df_merged[
                (df_merged['sim_flow'] / df_merged['obs_flow'] > 5) | 
                (df_merged['sim_flow'] / df_merged['obs_flow'] < 0.2)
            ]
        }
        
        # 统计异常值数量
        anomaly_stats = {
            'high_mape_count': len(anomalies['high_mape_records']),
            'high_geh_count': len(anomalies['high_geh_records']),
            'zero_flow_count': len(anomalies['zero_flow_records']),
            'extreme_ratio_count': len(anomalies['extreme_ratio_records']),
            'total_records': len(df_merged)
        }
        
        return {
            'anomalies': anomalies,
            'statistics': anomaly_stats
        }
    
    def _statistical_analysis(self, df_merged: pd.DataFrame) -> Dict[str, Any]:
        """
        统计分析
        
        Args:
            df_merged: 合并后的数据
            
        Returns:
            统计分析结果
        """
        stats = {
            'correlation': {
                'pearson': df_merged['sim_flow'].corr(df_merged['obs_flow']),
                'spearman': df_merged['sim_flow'].corr(df_merged['obs_flow'], method='spearman')
            },
            'flow_distribution': {
                'sim_mean': df_merged['sim_flow'].mean(),
                'sim_std': df_merged['sim_flow'].std(),
                'obs_mean': df_merged['obs_flow'].mean(),
                'obs_std': df_merged['obs_flow'].std(),
                'sim_median': df_merged['sim_flow'].median(),
                'obs_median': df_merged['obs_flow'].median()
            },
            'accuracy_distribution': {
                'mape_mean': df_merged['mape'].mean(),
                'mape_median': df_merged['mape'].median(),
                'mape_std': df_merged['mape'].std(),
                'geh_mean': df_merged['geh'].mean(),
                'geh_median': df_merged['geh'].median(),
                'geh_std': df_merged['geh'].std()
            }
        }
        
        return stats
    
    def _save_raw_data(self, df_merged: pd.DataFrame):
        """
        保存原始数据
        
        Args:
            df_merged: 合并后的数据
        """
        try:
            # 保存完整数据
            raw_data_file = os.path.join(self.output_folder, 'accuracy_raw_data.csv')
            df_merged.to_csv(raw_data_file, index=False, encoding='utf-8-sig')
            
            # 保存处理后的数据（移除NaN值）
            cleaned_data = df_merged.dropna()
            cleaned_data_file = os.path.join(self.output_folder, 'accuracy_cleaned_data.csv')
            cleaned_data.to_csv(cleaned_data_file, index=False, encoding='utf-8-sig')
            
            log_analysis_progress(f"原始数据已保存到: {raw_data_file}")
            
        except Exception as e:
            log_analysis_progress(f"保存原始数据失败: {e}", "ERROR")
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        获取分析摘要信息
        
        Returns:
            分析摘要字典
        """
        return {
            'run_folder': self.run_folder,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_hours': (self.end_time - self.start_time).total_seconds() / 3600,
            'e1_folder': self.e1_folder,
            'gantry_folder': self.gantry_folder,
            'output_folder': self.output_folder,
            'config': self.config
        }