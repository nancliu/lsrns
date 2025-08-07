"""
精度分析工具模块
"""

import os
import re
import shutil
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# 数据库配置
DB_CONFIG = {
    "dbname": "sdzg",
    "user": "lsrns",
    "password": "Abcd@1234",
    "host": "10.149.235.123",
    "port": "5432"
}

# 精度分析配置
ANALYSIS_CONFIG = {
    "time_interval": 5,  # 分钟
    "mape_threshold": 15,  # MAPE阈值
    "geh_threshold": 5,   # GEH阈值
    "output_formats": ["csv", "html", "charts"]
}

def parse_time_from_filename(filename: str) -> Tuple[datetime, datetime]:
    """
    从文件名解析时间范围
    格式：dwd_od_weekly_YYYYMMDDHHMMSS_YYYYMMDDHHMMSS.od.xml
    """
    pattern = r'dwd_od_weekly_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})'
    match = re.search(pattern, filename)
    
    if not match:
        raise ValueError(f"无法从文件名解析时间范围: {filename}")
    
    # 提取时间组件
    year1, month1, day1, hour1, min1, sec1 = map(int, match.group(1, 2, 3, 4, 5, 6))
    year2, month2, day2, hour2, min2, sec2 = map(int, match.group(7, 8, 9, 10, 11, 12))
    
    start_time = datetime(year1, month1, day1, hour1, min1, sec1)
    end_time = datetime(year2, month2, day2, hour2, min2, sec2)
    
    return start_time, end_time

def get_table_names_from_date(date: datetime) -> Dict[str, str]:
    """
    根据日期获取对应的表名
    """
    if date.year == 2024:
        return {
            'od_table': 'dwd_od_g4202',
            'gantry_table': 'dwd_flow_gantry',
            'onramp_table': 'dwd_flow_onramp',
            'offramp_table': 'dwd_flow_offramp'
        }
    else:
        return {
            'od_table': 'dwd_od_weekly',
            'gantry_table': 'dwd_flow_gantry_weekly',
            'onramp_table': 'dwd_flow_onramp_weekly',
            'offramp_table': 'dwd_flow_offramp_weekly'
        }

def find_folder_with_prefix(base_path: str, prefix: str) -> Optional[str]:
    """
    查找指定前缀的文件夹
    """
    if not os.path.exists(base_path):
        return None
    
    for item in os.listdir(base_path):
        if item.startswith(prefix) and os.path.isdir(os.path.join(base_path, item)):
            return os.path.join(base_path, item)
    
    return None

def create_timestamp_folder(base_path: str, prefix: str = "") -> str:
    """
    创建带时间戳的文件夹
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = f"{prefix}_{timestamp}" if prefix else timestamp
    folder_path = os.path.join(base_path, folder_name)
    
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def copy_folder_with_new_name(src_path: str, dst_path: str) -> bool:
    """
    复制文件夹并重命名
    """
    try:
        if os.path.exists(src_path):
            shutil.copytree(src_path, dst_path)
            return True
        return False
    except Exception as e:
        print(f"复制文件夹失败: {e}")
        return False

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    验证DataFrame是否包含必需的列
    """
    if df is None or df.empty:
        return False
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        print(f"缺少必需的列: {missing_columns}")
        return False
    
    return True

def clean_numeric_data(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    清理数值数据，处理异常值和缺失值
    """
    df_clean = df.copy()
    
    for col in columns:
        if col in df_clean.columns:
            # 转换为数值类型
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            
            # 处理缺失值
            if df_clean[col].isnull().any():
                print(f"列 {col} 中有 {df_clean[col].isnull().sum()} 个缺失值")
                # 根据业务逻辑填充缺失值
                df_clean[col] = df_clean[col].fillna(0)
            
            # 处理异常值（负值）
            if (df_clean[col] < 0).any():
                print(f"列 {col} 中有 {(df_clean[col] < 0).sum()} 个负值，将被设为0")
                df_clean[col] = df_clean[col].clip(lower=0)
    
    return df_clean

def format_time_interval(minutes: int) -> str:
    """
    格式化时间间隔
    """
    if minutes < 60:
        return f"{minutes}分钟"
    elif minutes < 1440:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}小时{remaining_minutes}分钟" if remaining_minutes > 0 else f"{hours}小时"
    else:
        days = minutes // 1440
        remaining_hours = (minutes % 1440) // 60
        return f"{days}天{remaining_hours}小时" if remaining_hours > 0 else f"{days}天"

def get_file_size(file_path: str) -> str:
    """
    获取文件大小的人类可读格式
    """
    if not os.path.exists(file_path):
        return "文件不存在"
    
    size_bytes = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f}TB"

def log_analysis_progress(message: str, level: str = "INFO"):
    """
    记录分析进度
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def calculate_time_statistics(df: pd.DataFrame, time_column: str = 'start_time') -> Dict[str, Any]:
    """
    计算时间统计信息
    """
    if time_column not in df.columns:
        return {}
    
    time_stats = {
        'total_records': len(df),
        'time_range': {
            'start': df[time_column].min(),
            'end': df[time_column].max(),
            'duration': df[time_column].max() - df[time_column].min()
        },
        'unique_time_points': df[time_column].nunique()
    }
    
    return time_stats