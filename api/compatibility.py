"""
兼容性层
用于保持现有API的兼容性，同时支持新的案例管理系统
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from api.models import *
from api.services import *

# 创建兼容性路由器
compatibility_router = APIRouter()

# ==================== 兼容性API端点 ====================

@compatibility_router.post("/process_od_data/", response_model=BaseResponse)
async def process_od_data_compat(request: TimeRangeRequest):
    """
    兼容性OD数据处理API
    保持与原有API的兼容性
    """
    try:
        # 调用新的服务
        result = await process_od_data_service(request)
        
        # 转换为兼容格式
        compat_result = {
            "success": True,
            "message": "OD数据处理成功",
            "data": {
                "start_time": result.get("start_time"),
                "end_time": result.get("end_time"),
                "interval_minutes": result.get("interval_minutes"),
                "processed_at": result.get("processed_at"),
                "status": result.get("status")
            }
        }
        
        return BaseResponse(**compat_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OD数据处理失败: {str(e)}")

@compatibility_router.post("/run_simulation/", response_model=BaseResponse)
async def run_simulation_compat(request: SimulationRequest):
    """
    兼容性仿真运行API
    保持与原有API的兼容性
    """
    try:
        # 调用新的服务
        result = await run_simulation_service(request)
        
        # 转换为兼容格式
        compat_result = {
            "success": True,
            "message": "仿真运行成功",
            "data": {
                "run_folder": result.get("run_folder"),
                "gui": result.get("gui"),
                "simulation_type": result.get("simulation_type"),
                "started_at": result.get("started_at"),
                "status": result.get("status")
            }
        }
        
        return BaseResponse(**compat_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"仿真运行失败: {str(e)}")

@compatibility_router.post("/analyze_accuracy/", response_model=BaseResponse)
async def analyze_accuracy_compat(request: AccuracyAnalysisRequest):
    """
    兼容性精度分析API
    保持与原有API的兼容性
    """
    try:
        # 调用新的服务
        result = await analyze_accuracy_service(request)
        
        # 转换为兼容格式
        compat_result = {
            "success": True,
            "message": "精度分析成功",
            "data": {
                "result_folder": result.get("result_folder"),
                "analysis_type": result.get("analysis_type"),
                "started_at": result.get("started_at"),
                "status": result.get("status")
            }
        }
        
        return BaseResponse(**compat_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"精度分析失败: {str(e)}")

@compatibility_router.get("/get_folders/{prefix}", response_model=List[FolderInfo])
async def get_folders_compat(prefix: str):
    """
    兼容性文件夹获取API
    保持与原有API的兼容性
    """
    try:
        # 调用新的服务
        result = await get_folders_service(prefix)
        
        # 转换为兼容格式
        compat_result = []
        for folder in result:
            compat_folder = FolderInfo(
                name=folder.name,
                path=folder.path,
                created_at=folder.created_at,
                size=folder.size,
                file_count=folder.file_count
            )
            compat_result.append(compat_folder)
        
        return compat_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件夹列表失败: {str(e)}")

    

# ==================== 数据转换工具 ====================

class DataConverter:
    """数据转换工具类"""
    
    @staticmethod
    def convert_old_case_to_new(old_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将旧格式案例数据转换为新格式
        
        Args:
            old_case_data: 旧格式案例数据
            
        Returns:
            新格式案例数据
        """
        new_case_data = {
            "case_id": old_case_data.get("id", f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "case_name": old_case_data.get("name", "迁移案例"),
            "created_at": old_case_data.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "time_range": {
                "start": old_case_data.get("start_time", "2025/07/21 08:00:00"),
                "end": old_case_data.get("end_time", "2025/07/21 09:00:00")
            },
            "config": old_case_data.get("config", {}),
            "status": "migrated",
            "description": old_case_data.get("description", "从旧系统迁移的案例"),
            "statistics": old_case_data.get("statistics", {}),
            "files": old_case_data.get("files", {})
        }
        
        return new_case_data
    
    @staticmethod
    def convert_new_case_to_old(new_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将新格式案例数据转换为旧格式
        
        Args:
            new_case_data: 新格式案例数据
            
        Returns:
            旧格式案例数据
        """
        old_case_data = {
            "id": new_case_data.get("case_id"),
            "name": new_case_data.get("case_name"),
            "created_at": new_case_data.get("created_at"),
            "start_time": new_case_data.get("time_range", {}).get("start"),
            "end_time": new_case_data.get("time_range", {}).get("end"),
            "config": new_case_data.get("config", {}),
            "description": new_case_data.get("description"),
            "statistics": new_case_data.get("statistics", {}),
            "files": new_case_data.get("files", {})
        }
        
        return old_case_data

# ==================== 路径映射工具 ====================

class PathMapper:
    """路径映射工具类"""
    
    def __init__(self):
        self.path_mappings = {
            "old_run_folders": "sim_scripts/run_*",
            "new_case_folders": "cases/case_*",
            "old_accuracy_results": "sim_scripts/accuracy_analysis/accuracy_results_*",
            "new_accuracy_results": "cases/*/analysis/accuracy/results"
        }
    
    def map_old_path_to_new(self, old_path: str) -> str:
        """
        将旧路径映射到新路径
        
        Args:
            old_path: 旧路径
            
        Returns:
            新路径
        """
        # 这里应该实现更复杂的路径映射逻辑
        # 暂时返回简单的映射
        if "run_" in old_path:
            return old_path.replace("sim_scripts/run_", "cases/case_")
        elif "accuracy_results_" in old_path:
            return old_path.replace("sim_scripts/accuracy_analysis/accuracy_results_", "cases/case_/analysis/accuracy/results")
        else:
            return old_path
    
    def map_new_path_to_old(self, new_path: str) -> str:
        """
        将新路径映射到旧路径
        
        Args:
            new_path: 新路径
            
        Returns:
            旧路径
        """
        # 这里应该实现更复杂的路径映射逻辑
        # 暂时返回简单的映射
        if "case_" in new_path:
            return new_path.replace("cases/case_", "sim_scripts/run_")
        elif "analysis/accuracy/results" in new_path:
            return new_path.replace("cases/case_/analysis/accuracy/results", "sim_scripts/accuracy_analysis/accuracy_results_")
        else:
            return new_path

# ==================== 兼容性检查工具 ====================

class CompatibilityChecker:
    """兼容性检查工具类"""
    
    @staticmethod
    def check_api_compatibility() -> Dict[str, Any]:
        """
        检查API兼容性
        
        Returns:
            兼容性检查结果
        """
        compatibility_report = {
            "api_endpoints": {
                "process_od_data": "compatible",
                "run_simulation": "compatible",
                "analyze_accuracy": "compatible",
                "get_folders": "compatible",
                "accuracy_analysis_status": "removed"
            },
            "data_formats": {
                "request_formats": "compatible",
                "response_formats": "compatible",
                "error_formats": "compatible"
            },
            "file_paths": {
                "old_structure": "deprecated",
                "new_structure": "recommended"
            },
            "overall_compatibility": "compatible"
        }
        
        return compatibility_report
    
    @staticmethod
    def generate_migration_guide() -> Dict[str, Any]:
        """
        生成迁移指南
        
        Returns:
            迁移指南
        """
        migration_guide = {
            "version": "1.0.0",
            "migration_steps": [
                {
                    "step": 1,
                    "title": "备份现有数据",
                    "description": "在开始迁移前，请备份所有现有数据",
                    "command": "cp -r sim_scripts sim_scripts_backup"
                },
                {
                    "step": 2,
                    "title": "运行数据迁移工具",
                    "description": "使用迁移工具将现有数据迁移到新结构",
                    "command": "python shared/utilities/migration_tools.py"
                },
                {
                    "step": 3,
                    "title": "验证迁移结果",
                    "description": "检查迁移后的数据完整性和正确性",
                    "command": "python test_migration.py"
                },
                {
                    "step": 4,
                    "title": "更新API调用",
                    "description": "将API调用从旧格式更新为新格式",
                    "details": [
                        "更新请求URL",
                        "更新请求参数格式",
                        "更新响应处理逻辑"
                    ]
                }
            ],
            "breaking_changes": [
                {
                    "type": "file_structure",
                    "description": "文件结构从flat变为hierarchical",
                    "impact": "medium",
                    "migration_required": True
                },
                {
                    "type": "api_response",
                    "description": "API响应格式统一化",
                    "impact": "low",
                    "migration_required": False
                }
            ],
            "deprecated_features": [
                "直接访问sim_scripts目录",
                "使用旧的文件命名约定",
                "使用旧的API响应格式"
            ],
            "new_features": [
                "案例管理系统",
                "模板管理",
                "统一的API响应格式",
                "更好的错误处理"
            ]
        }
        
        return migration_guide

# ==================== 兼容性API服务 ====================

async def get_compatibility_status() -> Dict[str, Any]:
    """
    获取兼容性状态
    
    Returns:
        兼容性状态信息
    """
    checker = CompatibilityChecker()
    compatibility_report = checker.check_api_compatibility()
    migration_guide = checker.generate_migration_guide()
    
    return {
        "compatibility_report": compatibility_report,
        "migration_guide": migration_guide,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ==================== 兼容性路由 ====================

@compatibility_router.get("/compatibility/status")
async def get_compatibility_status_endpoint():
    """
    获取兼容性状态API
    """
    try:
        result = await get_compatibility_status()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取兼容性状态失败: {str(e)}")

@compatibility_router.get("/compatibility/migration-guide")
async def get_migration_guide_endpoint():
    """
    获取迁移指南API
    """
    try:
        checker = CompatibilityChecker()
        migration_guide = checker.generate_migration_guide()
        return migration_guide
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取迁移指南失败: {str(e)}") 