from __future__ import annotations

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def ensure_directory(directory: Path) -> None:
    """确保目录存在"""
    directory.mkdir(parents=True, exist_ok=True)

def copy_template_file(source: Path, destination: Path) -> bool:
    """复制模板文件"""
    try:
        ensure_directory(destination.parent)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"模板文件复制失败: {e}")
        return False

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """获取文件信息"""
    if not file_path.exists():
        return {"error": "文件不存在"}
    
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "path": str(file_path)
    }

def load_config(config_path: Path) -> Dict[str, Any]:
    """加载配置文件"""
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config_path: Path, config: Dict[str, Any]) -> None:
    """保存配置文件"""
    ensure_directory(config_path.parent)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 元数据管理功能
def load_metadata(file_path: Path) -> Dict[str, Any]:
    """加载JSON元数据文件"""
    if not file_path.exists():
        raise FileNotFoundError(f"元数据文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metadata(file_path: Path, metadata: Dict[str, Any]) -> None:
    """保存JSON元数据文件"""
    ensure_directory(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def update_timestamp(metadata: Dict[str, Any]) -> None:
    """更新元数据的时间戳"""
    metadata["updated_at"] = datetime.now().isoformat()

def copy_file_safe(source: Path, destination: Path) -> bool:
    """安全复制文件"""
    try:
        ensure_directory(destination.parent)
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(f"文件复制失败 {source} -> {destination}: {e}")
        return False

# 目录管理功能
def create_case_structure(case_id: str) -> Path:
    """创建案例目录结构"""
    case_dir = Path("cases") / case_id
    
    # 创建主要目录
    ensure_directory(case_dir)
    ensure_directory(case_dir / "config")
    ensure_directory(case_dir / "simulations")
    ensure_directory(case_dir / "analysis")
    
    return case_dir

def create_simulation_structure(case_path: Path, simulation_id: str) -> Path:
    """创建仿真目录结构"""
    sim_dir = case_path / "simulations" / simulation_id
    ensure_directory(sim_dir)
    
    # 创建子目录
    ensure_directory(sim_dir / "e1")
    
    return sim_dir

def create_analysis_structure(case_path: Path, analysis_id: str) -> Path:
    """创建分析目录结构"""
    analysis_dir = case_path / "analysis" / analysis_id
    ensure_directory(analysis_dir)
    
    # 创建分析子目录
    ensure_directory(analysis_dir / "accuracy")
    ensure_directory(analysis_dir / "charts")
    ensure_directory(analysis_dir / "reports")
    
    return analysis_dir

def create_analysis_batch_dir(case_path: Path) -> Path:
    """创建分析批次目录
    
    Args:
        case_path: 案例根目录
    
    Returns:
        分析批次目录路径
    """
    from datetime import datetime
    
    analysis_root = case_path / "analysis"
    ensure_directory(analysis_root)
    
    # 创建分析批次目录：analysis_MMDD_HHMMSS
    current_time = datetime.now()
    batch_dir = analysis_root / f"analysis_{current_time.strftime('%m%d_%H%M%S')}"
    ensure_directory(batch_dir)
    
    return batch_dir

def get_or_create_gantry_folder(case_path: Path, start_time_str: str, end_time_str: str) -> Path:
    """按 gantry_YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS 命名规则创建/获取门架数据文件夹
    
    Args:
        case_path: 案例根目录
        start_time_str: 开始时间字符串
        end_time_str: 结束时间字符串
    
    Returns:
        门架数据文件夹路径
    """
    from .time_utils import parse_datetime
    
    start_dt = parse_datetime(start_time_str)
    end_dt = parse_datetime(end_time_str)
    start_token = start_dt.strftime("%Y%m%d_%H%M%S")
    end_token = end_dt.strftime("%Y%m%d_%H%M%S")
    folder_name = f"gantry_{start_token}_{end_token}"
    gantry_dir = case_path / folder_name
    ensure_directory(gantry_dir)
    return gantry_dir

def ensure_gantry_data_available(case_path: Path, start_time_str: str, end_time_str: str) -> Path:
    """确保门架数据可用，如果不存在则自动从数据库加载
    
    Args:
        case_path: 案例根目录
        start_time_str: 开始时间字符串
        end_time_str: 结束时间字符串
    
    Returns:
        门架数据文件夹路径
    """
    gantry_dir = get_or_create_gantry_folder(case_path, start_time_str, end_time_str)
    
    # 检查是否已有门架数据文件
    csv_files = list(gantry_dir.glob("*.csv"))
    if not csv_files:
        # 如果没有数据文件，尝试从数据库加载
        from shared.data_access.gantry_loader import GantryDataLoader
        from .time_utils import parse_datetime
        
        try:
            start_dt = parse_datetime(start_time_str)
            end_dt = parse_datetime(end_time_str)
            
            gantry_loader = GantryDataLoader()
            
            # 检查数据可用性
            availability = gantry_loader.check_data_availability(start_dt, end_dt)
            if not availability.get('available', False):
                raise Exception(f"门架数据不可用: {availability.get('error', '未知错误')}")
            
            # 加载数据
            gantry_data = gantry_loader.load_gantry_data(start_dt, end_dt)
            gantry_loader.close()
            
            if gantry_data.empty:
                raise Exception("从数据库加载的门架数据为空")
            
            # 保存数据到CSV文件
            import pandas as pd
            csv_file = gantry_dir / "gantry_data_raw.csv"
            gantry_data.to_csv(csv_file, index=False, encoding='utf-8')
            
            # 创建摘要文件
            summary = {
                "total_records": len(gantry_data),
                "gantry_count": gantry_data['gantry_id'].nunique() if 'gantry_id' in gantry_data.columns else 0,
                "time_range": [str(start_dt), str(end_dt)],
                "columns": gantry_data.columns.tolist(),
                "created_at": pd.Timestamp.now().isoformat()
            }
            
            summary_file = gantry_dir / "gantry_summary.json"
            import json
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"成功从数据库加载门架数据并保存到: {gantry_dir}")
            
        except Exception as e:
            print(f"从数据库加载门架数据失败: {e}")
            raise
    
    return gantry_dir

# 元数据管理器类
class MetadataManager:
    """元数据管理器 - 处理各种元数据文件的读写"""
    
    @staticmethod
    def load_case_metadata(case_path: Path) -> Dict[str, Any]:
        """加载案例元数据"""
        metadata_file = case_path / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"案例元数据不存在: {metadata_file}")
        
        return load_metadata(metadata_file)
    
    @staticmethod
    def save_case_metadata(case_path: Path, metadata: Dict[str, Any]) -> None:
        """保存案例元数据"""
        metadata_file = case_path / "metadata.json"
        save_metadata(metadata_file, metadata)
    
    @staticmethod
    def load_simulation_metadata(sim_path: Path) -> Dict[str, Any]:
        """加载仿真元数据"""
        metadata_file = sim_path / "simulation_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"仿真元数据不存在: {metadata_file}")
        
        return load_metadata(metadata_file)
    
    @staticmethod
    def save_simulation_metadata(sim_path: Path, metadata: Dict[str, Any]) -> None:
        """保存仿真元数据"""
        metadata_file = sim_path / "simulation_metadata.json"
        save_metadata(metadata_file, metadata)
    
    @staticmethod
    def update_simulations_index(case_path: Path, simulation_id: str, sim_metadata: dict):
        """更新仿真索引文件

        要求：
        - 顶层补充 case_id
        - 维护 simulation_count
        - 在 simulations 子项中包含 started_at 字段
        - 刷新顶层 updated_at
        """
        simulations_index_file = case_path / "simulations" / "simulations_index.json"
        
        # 读取现有的仿真索引
        if simulations_index_file.exists():
            with open(simulations_index_file, 'r', encoding='utf-8') as f:
                simulations_index = json.load(f)
        else:
            simulations_index = {"simulations": []}
        
        # 检查是否已存在该仿真记录
        existing_sim = None
        for sim in simulations_index["simulations"]:
            if sim.get("simulation_id") == simulation_id:
                existing_sim = sim
                break
        
        if existing_sim:
            # 更新现有记录
            existing_sim.update({
                "simulation_name": sim_metadata.get("simulation_name"),
                "simulation_type": sim_metadata.get("simulation_type"),
                "status": sim_metadata["status"],
                "updated_at": datetime.now().isoformat(),
                "completed_at": sim_metadata.get("completed_at"),
                "duration": sim_metadata.get("duration"),
                "error_message": sim_metadata.get("error_message"),
                "description": sim_metadata.get("description"),
                "started_at": sim_metadata.get("started_at")
            })
        else:
            # 如果不存在，添加新的仿真记录
            simulations_index["simulations"].append({
                "simulation_id": simulation_id,
                "simulation_name": sim_metadata.get("simulation_name"),
                "simulation_type": sim_metadata.get("simulation_type"),
                "status": sim_metadata["status"],
                "created_at": sim_metadata.get("created_at"),
                "completed_at": sim_metadata.get("completed_at"),
                "duration": sim_metadata.get("duration"),
                "error_message": sim_metadata.get("error_message"),
                "description": sim_metadata.get("description"),
                "started_at": sim_metadata.get("started_at")
            })
        
        # 顶层补充 case_id，并维护 simulation_count
        simulations_index["case_id"] = case_path.name
        simulations_index["simulation_count"] = len(simulations_index.get("simulations", []))
        simulations_index["updated_at"] = datetime.now().isoformat()
        
        # 保存更新的索引数据
        save_metadata(simulations_index_file, simulations_index)

    @staticmethod
    def remove_simulation_from_index(case_path: Path, simulation_id: str) -> None:
        """从仿真索引中移除指定仿真记录，并维护统计与时间戳。

        Args:
            case_path: 案例根目录路径
            simulation_id: 待移除的仿真ID
        """
        simulations_index_file = case_path / "simulations" / "simulations_index.json"
        if not simulations_index_file.exists():
            return

        try:
            with open(simulations_index_file, 'r', encoding='utf-8') as f:
                simulations_index = json.load(f)
        except Exception:
            return

        simulations = simulations_index.get("simulations", [])
        simulations = [s for s in simulations if s.get("simulation_id") != simulation_id]
        simulations_index["simulations"] = simulations
        simulations_index["case_id"] = case_path.name
        simulations_index["simulation_count"] = len(simulations)
        simulations_index["updated_at"] = datetime.now().isoformat()

        save_metadata(simulations_index_file, simulations_index)

# 目录管理器类
class DirectoryManager:
    """目录管理器 - 处理目录结构的创建和管理"""
    
    @staticmethod
    def create_case_structure(case_id: str) -> Path:
        """创建案例目录结构"""
        return create_case_structure(case_id)
    
    @staticmethod
    def create_simulation_structure(case_path: Path, simulation_id: str) -> Path:
        """创建仿真目录结构"""
        return create_simulation_structure(case_path, simulation_id)
    
    @staticmethod  
    def create_analysis_structure(case_path: Path, analysis_id: str) -> Path:
        """创建分析目录结构"""
        return create_analysis_structure(case_path, analysis_id)

    @staticmethod
    def get_or_create_gantry_folder(case_path: Path, start_time_str: str, end_time_str: str) -> Path:
        """按 gantry_YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS 命名规则创建/获取门架数据文件夹"""
        return get_or_create_gantry_folder(case_path, start_time_str, end_time_str)
    
    @staticmethod
    def ensure_gantry_data_available(case_path: Path, start_time_str: str, end_time_str: str) -> Path:
        """确保门架数据可用，如果不存在则自动从数据库加载"""
        return ensure_gantry_data_available(case_path, start_time_str, end_time_str)
    
    @staticmethod
    def create_analysis_batch_dir(case_path: Path) -> Path:
        """创建分析批次目录"""
        return create_analysis_batch_dir(case_path)
