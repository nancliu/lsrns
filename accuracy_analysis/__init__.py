"""
仿真精度分析工具

研发版本，已弃用，不要和主程序混用

用于分析SUMO交通仿真结果的精度，通过对比仿真输出的检测器数据与真实门架流量数据，
计算MAPE和GEH精度指标。
"""

from .analyzer import AccuracyAnalyzer
from .data_loader import DataLoader
from .metrics import MetricsCalculator
from .report_generator import ReportGenerator
from .utils import *

__version__ = "1.0.0"
__author__ = "OD生成脚本项目组"

__all__ = [
    'AccuracyAnalyzer',
    'DataLoader', 
    'MetricsCalculator',
    'ReportGenerator'
]