"""
场景管理API路由 (Phase 5.3.3)
支持场景查询和快速创建案例工作流
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..models import (
    ScenarioListQueryRequest, ScenarioListResponse, CaseFromScenarioResponse,
    EventScenarioQuickCreateRequest, BatchCaseCreationResponse,
    ScenarioAnalysisRequest, AnalysisResult
)
from ..services.scenario_service import ScenarioService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenario", tags=["scenarios"])

# 初始化服务
scenario_service = ScenarioService()


@router.get("/list", response_model=ScenarioListResponse)
async def list_scenarios(
    event_type: Optional[str] = Query(None, description="按事件类型筛选"),
    strategy: Optional[str] = Query(None, description="按控制策略筛选"),
    event_id: Optional[str] = Query(None, description="按事件ID查询"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    列出场景，支持过滤和分页

    按照Phase 5.3.3支持的查询方式:
    - event_type: 按事件类型筛选 (01_accident, 02_congestion等)
    - strategy: 按控制策略筛选 (vss, dhs, tec, no_control)
    - event_id: 按事件ID查询
    - page/page_size: 分页参数
    """
    try:
        query = ScenarioListQueryRequest(
            event_type=event_type,
            strategy=strategy,
            event_id=event_id,
            page=page,
            page_size=page_size
        )
        result = await scenario_service.list_scenarios(query)
        return result
    except Exception as e:
        logger.error(f"Error listing scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")


@router.get("/by-event/{event_id}")
async def get_event_scenarios(event_id: str):
    """
    获取特定事件的所有场景变量

    按照AD-7 (1:1 Case-Scenario Binding):
    - 返回该事件的所有变量 (no_control, vss, tec等)
    - 每个变量可以单独创建一个案例
    """
    try:
        scenarios = await scenario_service.get_event_scenarios(event_id)
        return {
            "event_id": event_id,
            "scenarios": scenarios,
            "total_count": len(scenarios)
        }
    except Exception as e:
        logger.error(f"Error getting event scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get event scenarios: {str(e)}")


@router.post("/create-case", response_model=CaseFromScenarioResponse)
async def create_case_from_scenario(request: EventScenarioQuickCreateRequest):
    """
    从事件场景快速创建案例 (Phase 5.3.3核心API)

    按照以下架构决策实施:
    - AD-7: 1:1 Case-Scenario Binding
      每个场景变量对应一个案例
      case.metadata.source_scenario_id追踪场景来源

    - AD-8: Configuration Override Policy
      不可变字段: event_id, event_type, location, affected_edges, control_strategy_type
      可覆盖字段: simulation_duration, random_seed, output_config (edgedata强制启用)

    - 自动设置案例元数据
    - 复制场景的.add.xml和配置文件到案例目录
    - 为后续仿真做好准备

    Args:
        request: 案例创建请求，包含:
          - case_name: 案例名称
          - event_type: 事件类型
          - scenario_id: 场景ID (e.g., 'scenario_12547_vss')
          - event_id: 事件ID (e.g., '12547')
          - strategy: 控制策略 (vss|dhs|tec|no_control)
          - network_file: 网络文件路径
          - od_file: OD/路由文件路径
          - taz_file: TAZ文件路径 (可选)

    Returns:
        CaseFromScenarioResponse: 创建的案例信息
    """
    try:
        # 验证场景是否存在
        scenario_exists = await scenario_service.validate_scenario_exists(request.scenario_id)
        if not scenario_exists:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {request.scenario_id}")

        # 创建案例
        result = await scenario_service.create_case_from_scenario(request)

        logger.info(f"Created case {result.case_id} from scenario {request.scenario_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating case from scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")


@router.get("/health")
async def health_check():
    """
    场景服务健康检查

    验证scenario_index.json是否可访问
    """
    try:
        index_data = scenario_service._load_scenario_index(force_reload=True)
        scenario_count = len(index_data.get("scenarios", []))

        return {
            "status": "healthy",
            "scenario_count": scenario_count,
            "index_path": str(scenario_service.scenario_index_path)
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "index_path": str(scenario_service.scenario_index_path)
            }
        )


@router.get("/{scenario_id}")
async def get_scenario_details(scenario_id: str):
    """
    获取场景详细信息

    Args:
        scenario_id: 场景ID (e.g., 'scenario_12547_vss')

    Returns:
        场景的详细信息和配置文件
    """
    try:
        scenario_files = await scenario_service.get_scenario_files(scenario_id)

        if not scenario_files:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

        # 加载JSON配置
        import json
        config = {}
        if "event_description" in scenario_files:
            with open(scenario_files["event_description"], 'r', encoding='utf-8') as f:
                config["event"] = json.load(f)

        if "traffic_input_config" in scenario_files:
            with open(scenario_files["traffic_input_config"], 'r', encoding='utf-8') as f:
                config["traffic"] = json.load(f)

        if "control_strategy_config" in scenario_files:
            with open(scenario_files["control_strategy_config"], 'r', encoding='utf-8') as f:
                config["control"] = json.load(f)

        return {
            "scenario_id": scenario_id,
            "files": {k: str(v) for k, v in scenario_files.items()},
            "config": config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scenario details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scenario details: {str(e)}")


@router.post("/batch-create-cases")
async def batch_create_cases_from_scenarios(requests: list[EventScenarioQuickCreateRequest]):
    """
    批量从场景创建案例 (Phase 5.3.3扩展)

    支持并发创建多个案例，每个对应一个场景

    Args:
        requests: 案例创建请求列表

    Returns:
        批量创建结果
    """
    try:
        created_cases = []
        errors = []
        batch_id = scenario_service.generate_unique_id("batch")

        for idx, request in enumerate(requests):
            try:
                case = await scenario_service.create_case_from_scenario(request)
                created_cases.append(case)
            except Exception as e:
                error_msg = f"Request {idx + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    "scenario_id": request.scenario_id,
                    "error": error_msg
                })

        return BatchCaseCreationResponse(
            batch_id=batch_id,
            total_scenarios=len(requests),
            created_cases=len(created_cases),
            failed_count=len(errors),
            cases=created_cases,
            errors=errors,
            created_at=scenario_service.generate_unique_id("batch").split("_")[0]  # timestamp
        )

    except Exception as e:
        logger.error(f"Error in batch case creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch creation failed: {str(e)}")


@router.post("/run-analysis", response_model=AnalysisResult)
async def run_analysis(request: ScenarioAnalysisRequest):
    """
    启动场景分析 (Phase 5.3.3)

    支持按照批量仿真第二层结果分析实现：
    - EdgeData 分析（主要）：分析事件对路网的空间影响
    - TripInfo 分析（可选）：补充分析车辆行为
    - 对比分析：支持与无控制策略场景比较

    Args:
        request: 分析请求，包含:
          - case_id: 案例ID
          - scenario_id: 场景ID
          - event_id: 事件ID
          - compare_no_control: 是否与无控制策略比较
          - analysis_focus: 分析聚焦 (edgedata|tripinfo)

    Returns:
        AnalysisResult: 分析结果，包含分析ID和状态

    说明:
        - 分析异步执行，立即返回分析ID
        - 若仿真未完成，分析将等待仿真结果
        - 自动处理 EdgeData 分析（强制启用）
        - TripInfo 分析为可选（由 analysis_focus 控制）
    """
    try:
        result = await scenario_service.run_analysis(request)
        logger.info(f"Analysis {result.analysis_id} initiated for case {request.case_id}")
        return result

    except Exception as e:
        logger.error(f"Error running analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run analysis: {str(e)}")
