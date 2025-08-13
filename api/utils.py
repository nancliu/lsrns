"""
OD数据处理与仿真系统 - 工具函数
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 时间处理工具 ====================

def calculate_duration(start_time: str, end_time: str) -> int:
    """
    计算时间间隔（秒）
    
    Args:
        start_time: 开始时间，格式：YYYY/MM/DD HH:MM:SS
        end_time: 结束时间，格式：YYYY/MM/DD HH:MM:SS
    
    Returns:
        时间间隔（秒）
    """
    try:
        start_dt = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")
        duration = (end_dt - start_dt).total_seconds()
        return int(duration)
    except Exception as e:
        raise Exception(f"时间计算失败: {str(e)}")

def split_time_range(start_time: str, end_time: str, interval_minutes: int = 5) -> List[Dict[str, str]]:
    """
    将时间范围分割为多个时间间隔
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        interval_minutes: 时间间隔（分钟）
    
    Returns:
        时间间隔列表
    """
    try:
        start_dt = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")
        
        intervals = []
        current_dt = start_dt
        
        while current_dt < end_dt:
            next_dt = current_dt + timedelta(minutes=interval_minutes)
            if next_dt > end_dt:
                next_dt = end_dt
            
            interval = {
                "start": current_dt.strftime("%Y/%m/%d %H:%M:%S"),
                "end": next_dt.strftime("%Y/%m/%d %H:%M:%S")
            }
            intervals.append(interval)
            current_dt = next_dt
        
        return intervals
    except Exception as e:
        raise Exception(f"时间范围分割失败: {str(e)}")

# ==================== TAZ处理工具 ====================

def load_taz_ids(taz_file: str) -> List[str]:
    """
    从TAZ文件中加载TAZ ID列表
    
    Args:
        taz_file: TAZ文件路径
    
    Returns:
        TAZ ID列表
    """
    try:
        taz_ids = []
        with open(taz_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'id=' in line and 'taz' in line:
                    # 简单的TAZ ID提取逻辑
                    parts = line.split('id="')
                    if len(parts) > 1:
                        taz_id = parts[1].split('"')[0]
                        taz_ids.append(taz_id)
        return taz_ids
    except Exception as e:
        raise Exception(f"TAZ ID加载失败: {str(e)}")

def validate_taz_file(taz_file: str) -> Dict[str, Any]:
    """
    验证TAZ文件
    
    Args:
        taz_file: TAZ文件路径
    
    Returns:
        验证结果
    """
    try:
        result = {
            "file_path": taz_file,
            "is_valid": True,
            "issues": [],
            "taz_count": 0
        }
        
        if not os.path.exists(taz_file):
            result["is_valid"] = False
            result["issues"].append("文件不存在")
            return result
        
        with open(taz_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查基本结构
        if '<tazs>' not in content or '</tazs>' not in content:
            result["is_valid"] = False
            result["issues"].append("缺少tazs标签")
        
        # 统计TAZ数量
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
            "taz_count": 0
        }

# ==================== OD数据处理工具 ====================

def generate_od_xml(od_matrix: Dict[str, Any], start_time: str, end_time: str, od_file: str) -> bool:
    """
    生成OD XML文件
    
    Args:
        od_matrix: OD矩阵数据
        start_time: 开始时间
        end_time: 结束时间
        od_file: 输出文件路径
    
    Returns:
        是否成功
    """
    try:
        # 这里应该实现OD XML生成逻辑
        # 暂时返回成功
        return True
    except Exception as e:
        raise Exception(f"OD XML生成失败: {str(e)}")

def process_od_data(start_time: str, end_time: str, interval_minutes: int = 5) -> Dict[str, Any]:
    """
    处理OD数据
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        interval_minutes: 时间间隔
    
    Returns:
        处理结果
    """
    try:
        # 这里应该实现OD数据处理逻辑
        # 暂时返回模拟数据
        result = {
            "start_time": start_time,
            "end_time": end_time,
            "interval_minutes": interval_minutes,
            "processed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        return result
    except Exception as e:
        raise Exception(f"OD数据处理失败: {str(e)}")

# ==================== 仿真配置工具 ====================

def generate_sumocfg(route_file: str, net_file: str, start_time: str, end_time: str, **kwargs) -> str:
    """
    生成SUMO配置文件
    
    Args:
        route_file: 路由文件路径
        net_file: 网络文件路径
        start_time: 开始时间
        end_time: 结束时间
        **kwargs: 其他参数
    
    Returns:
        配置文件内容
    """
    try:
        # 计算仿真时长
        duration = calculate_duration(start_time, end_time)
        # 标准化为POSIX分隔符（不改变相对/绝对，仅分隔符）
        route_val = (route_file or "").replace('\\', '/')
        net_val = (net_file or "").replace('\\', '/')
        add_val = (kwargs.get("additional_file") or "").replace('\\', '/') if kwargs.get("additional_file") else None
        output_prefix_val = None
        if kwargs.get("output_prefix"):
            # 允许显式传入；否则默认不写<output-prefix>
            output_prefix_val = (kwargs.get("output_prefix") or "").replace('\\', '/')
        summary_output_val = (kwargs.get("summary_output") or "").replace('\\', '/') if kwargs.get("summary_output") else None
        tripinfo_output_val = (kwargs.get("tripinfo_output") or "").replace('\\', '/') if kwargs.get("tripinfo_output") else None
        vehroute_output_val = (kwargs.get("vehroute_output") or "").replace('\\', '/') if kwargs.get("vehroute_output") else None
        netstate_output_val = (kwargs.get("netstate_output") or "").replace('\\', '/') if kwargs.get("netstate_output") else None
        fcd_output_val = (kwargs.get("fcd_output") or "").replace('\\', '/') if kwargs.get("fcd_output") else None
        emission_output_val = (kwargs.get("emission_output") or "").replace('\\', '/') if kwargs.get("emission_output") else None
        
        # 生成配置文件内容
        input_additional = f"\n        <additional-files value=\"{add_val}\"/>" if add_val else ""
        # 组装 <output> 段
        output_lines = []
        if output_prefix_val:
            output_lines.append(f"        <output-prefix value=\"{output_prefix_val}\"/>")
        if summary_output_val:
            output_lines.append(f"        <summary-output value=\"{summary_output_val}\"/>")
        if tripinfo_output_val:
            output_lines.append(f"        <tripinfo-output value=\"{tripinfo_output_val}\"/>")
        if vehroute_output_val:
            output_lines.append(f"        <vehroute-output value=\"{vehroute_output_val}\"/>")
        if netstate_output_val:
            output_lines.append(f"        <netstate-dump value=\"{netstate_output_val}\"/>")
        if fcd_output_val:
            output_lines.append(f"        <fcd-output value=\"{fcd_output_val}\"/>")
        if emission_output_val:
            output_lines.append(f"        <emission-output value=\"{emission_output_val}\"/>")
        output_block = ("\n    <output>\n" + "\n".join(output_lines) + "\n    </output>") if output_lines else ""
        config_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{net_val}"/>
        <route-files value="{route_val}"/>{input_additional}
    </input>{output_block}
    
    <time>
        <begin value="0"/>
        <end value="{duration}"/>
    </time>
    
    <processing>
        <ignore-route-errors value="true"/>
        <collision.action value="warn"/>
    </processing>
    
    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>
</configuration>'''
        return config_content
    except Exception as e:
        raise Exception(f"SUMO配置文件生成失败: {str(e)}")

def save_sumocfg(config_content: str, config_file: str) -> bool:
    """
    保存SUMO配置文件
    
    Args:
        config_content: 配置文件内容
        config_file: 配置文件路径
    
    Returns:
        是否成功
    """
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        return True
    except Exception as e:
        raise Exception(f"配置文件保存失败: {str(e)}")

# ==================== 仿真运行工具 ====================

def run_sumo(sumocfg_file: str, gui: bool = False) -> bool:
    """
    运行SUMO仿真
    
    Args:
        sumocfg_file: 配置文件路径
        gui: 是否启用GUI
    
    Returns:
        是否成功
    """
    try:
        # 构建SUMO命令
        cmd = ["sumo"]
        if not gui:
            cmd.append("--no-step-log")
            cmd.append("--no-warnings")
        
        cmd.extend(["-c", sumocfg_file])
        
        # 运行SUMO
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            raise Exception(f"SUMO运行失败: {result.stderr}")
    except Exception as e:
        raise Exception(f"仿真运行失败: {str(e)}")

def run_sumo_gui(sumocfg_file: str) -> bool:
    """
    运行SUMO GUI仿真
    
    Args:
        sumocfg_file: 配置文件路径
    
    Returns:
        是否成功
    """
    return run_sumo(sumocfg_file, gui=True)

# ==================== 文件操作工具 ====================

def ensure_directory(directory: str) -> bool:
    """
    确保目录存在
    
    Args:
        directory: 目录路径
    
    Returns:
        是否成功
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        raise Exception(f"目录创建失败: {str(e)}")

def copy_template_file(template_path: str, target_path: str) -> bool:
    """
    复制模板文件
    
    Args:
        template_path: 模板文件路径
        target_path: 目标文件路径
    
    Returns:
        是否成功
    """
    try:
        import shutil
        shutil.copy2(template_path, target_path)
        return True
    except Exception as e:
        raise Exception(f"模板文件复制失败: {str(e)}")

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息
    """
    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        raise Exception(f"文件信息获取失败: {str(e)}")

# ==================== 数据验证工具 ====================

def validate_time_format(time_str: str) -> bool:
    """
    验证时间格式
    
    Args:
        time_str: 时间字符串
    
    Returns:
        是否有效
    """
    try:
        datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
        return True
    except ValueError:
        return False

def validate_file_path(file_path: str) -> bool:
    """
    验证文件路径
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否有效
    """
    try:
        return os.path.exists(file_path)
    except Exception:
        return False

# ==================== 日志工具 ====================

def log_operation(operation: str, details: Dict[str, Any]) -> None:
    """
    记录操作日志
    
    Args:
        operation: 操作名称
        details: 操作详情
    """
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        }
        
        # 这里可以添加日志写入逻辑
        print(f"LOG: {json.dumps(log_entry, ensure_ascii=False)}")
    except Exception as e:
        print(f"日志记录失败: {str(e)}")

# ==================== 配置管理工具 ====================

def load_config(config_file: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        配置数据
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"配置文件加载失败: {str(e)}")

def save_config(config_data: Dict[str, Any], config_file: str) -> bool:
    """
    保存配置文件
    
    Args:
        config_data: 配置数据
        config_file: 配置文件路径
    
    Returns:
        是否成功
    """
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        raise Exception(f"配置文件保存失败: {str(e)}")

# ==================== 数据库工具 ====================

def get_db_config() -> Dict[str, Any]:
    """
    获取数据库配置，优先从环境变量读取，回退到accuracy_analysis.utils.DB_CONFIG。
    需要的环境变量：DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
    """
    from accuracy_analysis.utils import DB_CONFIG as DEFAULT_DB_CONFIG

    db_config = {
        "dbname": os.getenv("DB_NAME", DEFAULT_DB_CONFIG.get("dbname")),
        "user": os.getenv("DB_USER", DEFAULT_DB_CONFIG.get("user")),
        "password": os.getenv("DB_PASSWORD", DEFAULT_DB_CONFIG.get("password")),
        "host": os.getenv("DB_HOST", DEFAULT_DB_CONFIG.get("host")),
        "port": os.getenv("DB_PORT", DEFAULT_DB_CONFIG.get("port")),
    }
    return db_config

def open_db_connection():
    """
    打开PostgreSQL数据库连接。
    Returns:
        psycopg2连接对象
    """
    try:
        cfg = get_db_config()
        return psycopg2.connect(**cfg)
    except Exception as e:
        raise Exception(f"数据库连接失败: {str(e)}") 