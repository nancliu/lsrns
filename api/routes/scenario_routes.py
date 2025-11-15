"""
场景管理API路由 (Phase 5.3.3)
支持场景查询和快速创建案例工作流
"""

import logging
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..models import (
    ScenarioListQueryRequest, ScenarioListResponse, CaseFromScenarioResponse,
    EventScenarioQuickCreateRequest, BatchCaseCreationResponse,
    ScenarioAnalysisRequest, AnalysisResult,
    CsvGenerationRequest, CsvGenerationResponse
)
from ..models.requests.case_requests import CreateEventCaseBatchRequest
from ..models.responses.scenario_responses import EventCaseBatchCreationResponse
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


@router.get("/list-csv-files")
async def list_csv_files():
    """
    列出events文件夹中可用的CSV文件

    返回events文件夹中所有的.csv文件列表，供前端下拉选择框使用。

    Returns:
        {
            "files": ["all_extracted_events.csv", "failed_events.csv", ...],
            "count": 2
        }
    """
    try:
        events_dir = Path("events")

        if not events_dir.exists():
            logger.warning(f"Events directory not found: {events_dir}")
            return JSONResponse(
                status_code=200,
                content={"files": [], "count": 0, "message": "events文件夹不存在"}
            )

        # 扫描所有CSV文件
        csv_files = []
        for file_path in events_dir.glob("*.csv"):
            if file_path.is_file():
                csv_files.append(file_path.name)

        # 按文件名排序
        csv_files.sort()

        logger.info(f"Found {len(csv_files)} CSV files in events directory")

        return {
            "files": csv_files,
            "count": len(csv_files)
        }

    except Exception as e:
        logger.error(f"Error listing CSV files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list CSV files: {str(e)}")


@router.post("/generate-from-csv", response_model=CsvGenerationResponse)
async def generate_scenarios_from_csv(request: CsvGenerationRequest):
    """
    Generate scenarios from CSV file in batch.

    This endpoint processes an event CSV file and generates scenario bundles for new events.
    Existing scenarios are automatically skipped (duplicate detection).

    Args:
        request: CSV generation request with:
          - csv_file: CSV filename in events/ folder
          - generate_all_strategies: Generate all strategies or just NO_CONTROL

    Returns:
        CsvGenerationResponse with:
          - task_id: Unique task ID
          - status: processing|completed|failed
          - state_file: Path to state tracking JSON
          - generated_count: Number of scenarios generated

    Process:
        1. Validate CSV exists
        2. Create state tracking file
        3. Load CSV and process events
        4. Check duplicates against scenario_index.json
        5. Generate scenarios for new events only
        6. Update state file with results
        7. Update scenario_index.json

    State File Location:
        events/csv_extraction_status/{csv_filename}_status.json

    Example Request:
        POST /api/v1/scenario/generate-from-csv
        {
            "csv_file": "all_extracted_events.csv",
            "generate_all_strategies": true
        }

    Example Response:
        {
            "task_id": "csv_gen_20251114_143000",
            "csv_file": "all_extracted_events.csv",
            "status": "completed",
            "message": "场景生成完成：50个事件生成，100个已存在",
            "state_file": "events/csv_extraction_status/all_extracted_events_status.json",
            "generated_count": 150
        }
    """
    try:
        logger.info(f"CSV generation requested: {request.csv_file}, all_strategies={request.generate_all_strategies}")

        result = await scenario_service.generate_scenarios_from_csv(
            csv_file=request.csv_file,
            generate_all_strategies=request.generate_all_strategies
        )

        return CsvGenerationResponse(**result)

    except FileNotFoundError as e:
        logger.error(f"CSV file not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"CSV generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate scenarios: {str(e)}")


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


@router.post("/create-case-batch", response_model=EventCaseBatchCreationResponse)
async def create_event_case_batch(request: CreateEventCaseBatchRequest):
    """
    批量创建事件案例 - 一次创建一个事件下的所有场景

    核心功能:
    1. 在一个case下创建多个simulations（每个场景一个）
    2. 聚合事件和所有管控策略的影响边缘，生成统一的edgeData.add.xml
    3. 所有仿真共享同一个edgeData配置

    优势:
    - 一次操作创建所有场景（无管控、VSS、TEC、DHS）
    - 统一edgeData确保所有场景监测相同的边缘
    - 节省75%的操作时间
    - 98%的数据量减少（5000 edges → ~120 edges）

    Args:
        request: 批量创建请求，包含event_id和多个场景定义

    Returns:
        批量创建结果，包含案例ID、各场景创建状态、edgeData信息

    示例请求:
        {
            "event_id": "12547",
            "event_type": "01_accident",
            "scenarios": [
                {
                    "scenario_id": "scenario_12547_no_control",
                    "strategy": "NO_CONTROL",
                    "event_location": {"edge_id": "3026"},
                    ...
                },
                {
                    "scenario_id": "scenario_12547_vss",
                    "strategy": "VSS",
                    "control_strategy": {
                        "strategy_type": "VSS",
                        "parameters": {"edge_range": ["3000", "3050"]}
                    },
                    ...
                }
            ],
            "network_file": "templates/network_files/highway.net.xml",
            "od_file": "dwd.dwd_od_weekly",
            "time_range": {"start": "...", "end": "..."}
        }
    """
    try:
        # 调用case_service的批量创建方法
        from ..services.case_service import case_service

        result = await case_service.create_event_case_batch(request)

        logger.info(f"✓ 批量创建成功: event={request.event_id}, "
                    f"scenarios={result['successful_scenarios']}/{result['total_scenarios']}")

        return EventCaseBatchCreationResponse(**result)

    except Exception as e:
        logger.error(f"✗ 批量创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建失败: {str(e)}")
