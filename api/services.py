"""
OD数据处理与仿真系统 - 业务逻辑服务
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio

from api.models import *
from api.utils import *

# ==================== 数据处理服务 ====================

async def process_od_data_service(request: TimeRangeRequest) -> Dict[str, Any]:
    """
    OD数据处理服务
    """
    try:
        # 这里应该调用原有的OD数据处理逻辑
        # 暂时返回模拟数据
        result = {
            "start_time": request.start_time,
            "end_time": request.end_time,
            "interval_minutes": request.interval_minutes,
            "processed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        return result
    except Exception as e:
        raise Exception(f"OD数据处理失败: {str(e)}")

async def run_simulation_service(request: SimulationRequest) -> Dict[str, Any]:
    """
    仿真运行服务
    """
    try:
        # 这里应该调用原有的仿真运行逻辑
        # 暂时返回模拟数据
        result = {
            "run_folder": request.run_folder,
            "gui": request.gui,
            "simulation_type": request.simulation_type.value,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        return result
    except Exception as e:
        raise Exception(f"仿真运行失败: {str(e)}")

async def analyze_accuracy_service(request: AccuracyAnalysisRequest) -> Dict[str, Any]:
    """
    精度分析服务
    """
    try:
        # 这里应该调用原有的精度分析逻辑
        # 暂时返回模拟数据
        result = {
            "result_folder": request.result_folder,
            "analysis_type": request.analysis_type.value,
            "started_at": datetime.now().isoformat(),
            "status": "analyzing"
        }
        return result
    except Exception as e:
        raise Exception(f"精度分析失败: {str(e)}")

# ==================== 案例管理服务 ====================

async def create_case_service(request: CaseCreationRequest) -> Dict[str, Any]:
    """
    创建案例服务
    """
    try:
        # 生成案例ID
        case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建案例目录结构
        case_dir = Path("cases") / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (case_dir / "config").mkdir(exist_ok=True)
        (case_dir / "simulation").mkdir(exist_ok=True)
        (case_dir / "analysis").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "results").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "charts").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "reports").mkdir(exist_ok=True)
        
        # 创建元数据
        metadata = {
            "case_id": case_id,
            "case_name": request.case_name or case_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "time_range": request.time_range,
            "config": request.config,
            "status": CaseStatus.CREATED.value,
            "description": request.description,
            "statistics": {},
            "files": {}
        }
        
        # 保存元数据
        with open(case_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "case_id": case_id,
            "case_dir": str(case_dir),
            "metadata": metadata
        }
    except Exception as e:
        raise Exception(f"案例创建失败: {str(e)}")

async def list_cases_service(
    page: int = 1,
    page_size: int = 10,
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None
) -> CaseListResponse:
    """
    列出案例服务
    """
    try:
        cases = []
        cases_dir = Path("cases")
        
        if not cases_dir.exists():
            return CaseListResponse(cases=[], total_count=0, page=page, page_size=page_size)
        
        # 获取所有案例目录
        case_dirs = [d for d in cases_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]
        
        # 过滤和排序
        filtered_cases = []
        for case_dir in case_dirs:
            metadata_file = case_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # 状态过滤
                if status and metadata.get("status") != status.value:
                    continue
                
                # 搜索过滤
                if search:
                    case_name = metadata.get("case_name", "")
                    description = metadata.get("description", "")
                    if search.lower() not in case_name.lower() and search.lower() not in description.lower():
                        continue
                
                filtered_cases.append(metadata)
        
        # 按创建时间排序
        filtered_cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 分页
        total_count = len(filtered_cases)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_cases = filtered_cases[start_idx:end_idx]
        
        # 转换为CaseMetadata对象
        case_metadata_list = []
        for case_data in page_cases:
            case_metadata = CaseMetadata(**case_data)
            case_metadata_list.append(case_metadata)
        
        return CaseListResponse(
            cases=case_metadata_list,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise Exception(f"获取案例列表失败: {str(e)}")

async def get_case_service(case_id: str) -> CaseMetadata:
    """
    获取案例详情服务
    """
    try:
        case_dir = Path("cases") / case_id
        metadata_file = case_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise Exception(f"案例 {case_id} 不存在")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        return CaseMetadata(**metadata)
    except Exception as e:
        raise Exception(f"获取案例详情失败: {str(e)}")

async def delete_case_service(case_id: str) -> Dict[str, Any]:
    """
    删除案例服务
    """
    try:
        case_dir = Path("cases") / case_id
        
        if not case_dir.exists():
            raise Exception(f"案例 {case_id} 不存在")
        
        # 删除案例目录
        shutil.rmtree(case_dir)
        
        return {
            "case_id": case_id,
            "deleted_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise Exception(f"删除案例失败: {str(e)}")

async def clone_case_service(case_id: str, request: CaseCloneRequest) -> Dict[str, Any]:
    """
    克隆案例服务
    """
    try:
        source_case_dir = Path("cases") / case_id
        if not source_case_dir.exists():
            raise Exception(f"源案例 {case_id} 不存在")
        
        # 生成新案例ID
        new_case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_case_dir = Path("cases") / new_case_id
        
        # 复制案例目录
        shutil.copytree(source_case_dir, new_case_dir)
        
        # 更新元数据
        metadata_file = new_case_dir / "metadata.json"
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        metadata.update({
            "case_id": new_case_id,
            "case_name": request.new_case_name or f"{metadata.get('case_name', '')}_copy",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "description": request.new_description or f"克隆自 {case_id}",
            "status": CaseStatus.CREATED.value
        })
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "original_case_id": case_id,
            "new_case_id": new_case_id,
            "new_case_dir": str(new_case_dir),
            "cloned_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise Exception(f"克隆案例失败: {str(e)}")

# ==================== 文件管理服务 ====================

async def get_folders_service(prefix: str) -> List[FolderInfo]:
    """
    获取文件夹列表服务
    """
    try:
        folders = []
        base_dir = Path(".")
        
        # 查找匹配前缀的文件夹
        for item in base_dir.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                folder_info = FolderInfo(
                    name=item.name,
                    path=str(item),
                    created_at=datetime.fromtimestamp(item.stat().st_ctime),
                    size=get_folder_size(item),
                    file_count=count_files(item)
                )
                folders.append(folder_info)
        
        return folders
    except Exception as e:
        raise Exception(f"获取文件夹列表失败: {str(e)}")

async def get_accuracy_analysis_status_service(result_folder: str) -> AnalysisStatus:
    """
    获取精度分析状态服务
    """
    try:
        # 这里应该检查实际的分析状态
        # 暂时返回模拟数据
        status = AnalysisStatus(
            result_folder=result_folder,
            status="completed",
            progress=100.0,
            message="分析完成",
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        return status
    except Exception as e:
        raise Exception(f"获取分析状态失败: {str(e)}")

# ==================== 模板管理服务 ====================

async def get_taz_templates_service() -> List[TemplateInfo]:
    """
    获取TAZ模板列表服务
    """
    try:
        templates = []
        taz_dir = Path("templates/taz_files")
        config_file = taz_dir / "taz_templates.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for template_id, template_data in config.get("taz_templates", {}).items():
                template = TemplateInfo(
                    name=template_data["name"],
                    description=template_data["description"],
                    file_path=str(taz_dir / template_data["file_path"]),
                    version=template_data["version"],
                    created_date=template_data["created_date"],
                    status=template_data["validation_status"]
                )
                templates.append(template)
        
        return templates
    except Exception as e:
        raise Exception(f"获取TAZ模板失败: {str(e)}")

async def get_network_templates_service() -> List[TemplateInfo]:
    """
    获取网络模板列表服务
    """
    try:
        templates = []
        network_dir = Path("templates/network_files")
        config_file = network_dir / "network_configs.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for template_id, template_data in config.get("network_templates", {}).items():
                template = TemplateInfo(
                    name=template_data["name"],
                    description=template_data["description"],
                    file_path=str(network_dir / template_data["file_path"]),
                    version=template_data["version"],
                    created_date=template_data["created_date"],
                    status=template_data["status"]
                )
                templates.append(template)
        
        return templates
    except Exception as e:
        raise Exception(f"获取网络模板失败: {str(e)}")

async def get_simulation_templates_service() -> List[TemplateInfo]:
    """
    获取仿真配置模板列表服务
    """
    try:
        templates = []
        sim_dir = Path("templates/config_templates/simulation_templates")
        
        template_files = {
            "default.sumocfg": "默认仿真配置",
            "mesoscopic.sumocfg": "中观仿真配置",
            "microscopic.sumocfg": "微观仿真配置"
        }
        
        for filename, description in template_files.items():
            file_path = sim_dir / filename
            if file_path.exists():
                template = TemplateInfo(
                    name=filename,
                    description=description,
                    file_path=str(file_path),
                    version="1.0",
                    created_date="2025-01-08",
                    status="available"
                )
                templates.append(template)
        
        return templates
    except Exception as e:
        raise Exception(f"获取仿真模板失败: {str(e)}")

# ==================== 工具服务 ====================

async def validate_taz_file_service(file_path: str) -> Dict[str, Any]:
    """
    验证TAZ文件服务
    """
    try:
        # 这里应该调用TAZ验证工具
        # 暂时返回模拟数据
        result = {
            "file_path": file_path,
            "is_valid": True,
            "validation_time": datetime.now().isoformat(),
            "issues": []
        }
        return result
    except Exception as e:
        raise Exception(f"TAZ文件验证失败: {str(e)}")

async def fix_taz_file_service(file_path: str) -> Dict[str, Any]:
    """
    修复TAZ文件服务
    """
    try:
        # 这里应该调用TAZ修复工具
        # 暂时返回模拟数据
        result = {
            "file_path": file_path,
            "fixed": True,
            "fix_time": datetime.now().isoformat(),
            "changes": []
        }
        return result
    except Exception as e:
        raise Exception(f"TAZ文件修复失败: {str(e)}")

async def compare_taz_files_service(file1: str, file2: str) -> Dict[str, Any]:
    """
    比较TAZ文件服务
    """
    try:
        # 这里应该调用TAZ比较工具
        # 暂时返回模拟数据
        result = {
            "file1": file1,
            "file2": file2,
            "comparison_time": datetime.now().isoformat(),
            "differences": [],
            "similarities": []
        }
        return result
    except Exception as e:
        raise Exception(f"TAZ文件比较失败: {str(e)}")

# ==================== 辅助函数 ====================

def get_folder_size(folder_path: Path) -> int:
    """获取文件夹大小"""
    total_size = 0
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
    except:
        pass
    return total_size

def count_files(folder_path: Path) -> int:
    """统计文件夹中的文件数量"""
    file_count = 0
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                file_count += 1
    except:
        pass
    return file_count 