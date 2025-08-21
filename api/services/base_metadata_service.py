"""
基础元数据服务类
提供所有分析服务共用的元数据管理功能
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class BaseMetadataService:
    """基础元数据服务类"""
    
    def __init__(self, cases_dir: Path):
        self.cases_dir = cases_dir
    
    def prepare_analysis_dirs(self, case_dir: Path, analysis_type: str) -> tuple[Path, Path]:
        """准备分析目录结构 - 调用shared层功能"""
        from shared.utilities.file_utils import create_analysis_batch_dir
        
        # 调用shared层的目录创建功能
        batch_dir = create_analysis_batch_dir(case_dir)
        
        logger.info(f"创建分析批次目录: {batch_dir}")
        return batch_dir, batch_dir
    
    def update_metadata_for_analysis(self, case_dir: Path, simulation_ids: List[str], 
                                    analysis_type: str, analysis_results: dict, base_dir: Path = None):
        """为分析更新分析分支相关元数据

        边界约束（重要）：
        - 不创建/不更新 案例级元数据文件 case_dir/metadata.json
        - 不创建/不更新 仿真分支元数据（含 simulations_index.json、simulation_metadata.json）
        - 仅维护 结果分析分支：analysis/<batch>/<type>/metadata.json 与 analysis/analysis_index.json
        """
        
        # 如果没有传入base_dir，需要从analysis_results中获取或创建
        if base_dir is None:
            # 尝试从analysis_results中获取base_dir信息
            if 'analysis_id' in analysis_results:
                analysis_id = analysis_results['analysis_id']
                base_dir = case_dir / "analysis" / analysis_id
            else:
                # 创建新的分析目录：analysis_sim_{simulation_id}
                if simulation_ids:
                    sim_id = simulation_ids[0]  # 取第一个仿真ID
                    batch_id = f"analysis_{sim_id}"
                else:
                    batch_id = f"analysis_{datetime.now().strftime('%m%d_%H%M%S')}"
                
                base_dir = case_dir / "analysis" / batch_id
                from shared.utilities.file_utils import ensure_directory
                ensure_directory(base_dir)
                
                # 确保分析类型子目录存在
                analysis_type_dir = base_dir / analysis_type
                ensure_directory(analysis_type_dir)
                
                # 创建分析批次索引元数据文件
                self._create_analysis_batch_index(base_dir, datetime.now(), case_dir.name)
        
        # 更新分析类型元数据（结果分析分支第三层）
        self._update_analysis_type_metadata(base_dir, analysis_type, analysis_results, simulation_ids)
        
        # 更新分析索引（结果分析分支第二层）
        batch_metadata = {
            "created_at": datetime.now().isoformat(),
            "analysis_types": [analysis_type],
            "simulation_ids": simulation_ids,
            "status": "completed"
        }
        self._update_analysis_index(case_dir, base_dir.name, batch_metadata)
    
    def _manage_case_metadata(self, case_dir: Path):
        """管理案例级元数据 - 第一层

        初始化案例元数据时，统一时间戳字段为 updated_at，移除 simulation_count 与
        analysis_count 字段，保持元数据结构简洁。
        """
        metadata_file = case_dir / "metadata.json"

        if not metadata_file.exists():
            metadata = {
                "case_id": case_dir.name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "description": ""
            }

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _update_simulation_metadata(self, case_dir: Path, simulation_id: str, analysis_type: str):
        """更新仿真级元数据 - 仿真分支第三层

        不再覆盖 simulation_type，不修改仿真运行状态。将结果分析相关信息写入独立字段：
        - analysis_status: 分析状态（例如 "analyzed"）
        - last_analyzed_types: 已执行的分析类型列表（去重追加）
        - analysis_updated_at: 分析信息更新时间
        同时更新通用的 updated_at 字段。

        使用范围限制：该函数仅供仿真流程（或与仿真直接相关的模块）调用，结果分析流程禁止调用。
        """
        simulation_dir = case_dir / "simulations" / simulation_id
        from shared.utilities.file_utils import ensure_directory
        ensure_directory(simulation_dir)
        
        metadata_file = simulation_dir / "simulation_metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {
                "simulation_id": simulation_id,
                "case_id": case_dir.name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "simulation_type": "unknown"
            }
        
        # 结果分析相关字段独立维护，避免跨域影响
        last_types = metadata.get("last_analyzed_types") or []
        if analysis_type not in last_types:
            last_types.append(analysis_type)

        metadata.update({
            "analysis_status": "analyzed",
            "last_analyzed_types": last_types,
            "analysis_updated_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        # 保存元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _create_analysis_batch_index(self, batch_dir: Path, created_time: datetime, case_id: str):
        """创建分析批次索引元数据 - 结果分析分支第二层"""
        index_file = batch_dir / "analysis_index.json"
        
        metadata = {
            "analysis_batch_id": batch_dir.name,
            "case_id": case_id,
            "created_at": created_time.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "created",
            
            # 分析输入数据项 - 标明所分析的数据来源
            "analysis_input_data": {
                "simulation_outputs": {},
                "od_data": {},
                "network_data": {}
            },
            
            # 仿真引用信息
            "simulation_references": {},
            
            # 分析类型状态
            "analysis_types": {
                "accuracy": {
                    "status": "not_started",
                    "created_at": None,
                    "completed_at": None,
                    "results": None
                },
                "mechanism": {
                    "status": "not_started",
                    "created_at": None,
                    "completed_at": None,
                    "results": None
                },
                "performance": {
                    "status": "not_started",
                    "created_at": None,
                    "completed_at": None,
                    "results": None
                }
            },
            
            # 重复分析标识
            "is_reanalysis": False,
            "previous_analysis_batch_id": None,
            "reanalysis_reason": None
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _update_analysis_type_metadata(self, batch_dir: Path, analysis_type: str, 
                                      analysis_results: dict, simulation_ids: List[str]):
        """更新分析类型元数据 - 结果分析分支第三层（在accuracy/mechanism/performance文件夹下）"""
        # 分析类型元数据文件位于对应的子目录下
        analysis_type_dir = batch_dir / analysis_type
        from shared.utilities.file_utils import ensure_directory
        ensure_directory(analysis_type_dir)
        
        metadata_file = analysis_type_dir / "metadata.json"
        
        # 从analysis_results中提取信息
        analysis_id = analysis_results.get("analysis_id", f"{analysis_type}_{datetime.now().strftime('%m%d_%H%M%S')}")
        created_at = analysis_results.get("created_at", datetime.now().isoformat())
        completed_at = analysis_results.get("completed_at", datetime.now().isoformat())
        status = analysis_results.get("status", "completed")
        
        # 创建分析类型元数据
        metadata = {
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "analysis_batch_id": batch_dir.name,
            "case_id": batch_dir.parent.name,  # 从路径中获取案例ID
            "simulation_ids": simulation_ids,
            "created_at": created_at,
            "completed_at": completed_at,
            "status": status,
            
            # 分析结果
            "results": analysis_results.get("results", {}),
            
            # 分析元数据
            "analysis_metadata": analysis_results.get("analysis_metadata", {
                "analysis_tool": f"{analysis_type}_analyzer",
                "analysis_version": "1.0.0",
                "analysis_parameters": {},
                "analysis_workflow": []
            })
        }
        
        # 保存元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _update_analysis_index(self, case_dir: Path, batch_id: str, batch_metadata: dict):
        """更新分析索引 - 结果分析分支第二层"""
        index_file = case_dir / "analysis" / "analysis_index.json"
        
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {
                "case_id": case_dir.name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "analysis_count": 0,
                "analyses": []
            }
        
        # 检查是否已存在相同仿真ID的分析批次
        existing_index = -1
        for i, analysis in enumerate(index_data["analyses"]):
            if analysis.get("analysis_batch_id") == batch_id:
                existing_index = i
                break
        
        # 更新或添加分析批次记录
        analysis_record = {
            "analysis_batch_id": batch_id,
            "simulation_ids": batch_metadata.get("simulation_ids", []),
            "created_at": batch_metadata.get("created_at"),
            "status": batch_metadata.get("status"),
            "analysis_folder": batch_id,
            "simulation_summary": {
                "simulation_name": "待补充",
                "simulation_type": "待补充",
                "status": "待补充"
            },
            "analysis_types": {
                "accuracy": {
                    "status": "not_started",
                    "created_at": None
                },
                "mechanism": {
                    "status": "not_started",
                    "created_at": None
                },
                "performance": {
                    "status": "not_started",
                    "created_at": None
                }
            }
        }
        
        # 更新分析类型状态
        for analysis_type in batch_metadata.get("analysis_types", []):
            if analysis_type in analysis_record["analysis_types"]:
                analysis_record["analysis_types"][analysis_type].update({
                    "status": "completed",
                    "created_at": batch_metadata.get("created_at"),
                    "completed_at": datetime.now().isoformat()
                })
        
        if existing_index >= 0:
            # 更新现有记录
            index_data["analyses"][existing_index] = analysis_record
        else:
            # 添加新记录
            index_data["analyses"].append(analysis_record)
            index_data["analysis_count"] = len(index_data["analyses"])
        
        # 更新时间戳
        index_data["updated_at"] = datetime.now().isoformat()
        
        # 保存索引
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
