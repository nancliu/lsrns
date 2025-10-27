"""
交通管控策略路由
"""

from fastapi import APIRouter, Response
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# 创建控制策略路由器
router = APIRouter()


# ==================== 策略模板 Templates ====================
# Phase 1A: Full implementation with template loading and validation

import logging
from fastapi import HTTPException, status
from api.services.control_template_service import ControlTemplateService
from api.models.control.responses.template_responses import (
    TemplateListResponse,
    TemplateDetailResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Initialize template service
template_service = ControlTemplateService()


@router.get("/templates/", response_model=TemplateListResponse)
async def list_control_templates(response: Response):
    """
    获取所有策略模板列表 (Phase 1A implemented)

    Returns:
        TemplateListResponse with all valid templates and statistics
    """
    try:
        logger.info("GET /api/v1/control/templates/ - Listing templates")
        templates_response = template_service.list_templates()
        logger.info(f"Successfully returned {templates_response.total_count} templates")

        # Add cache control headers to prevent caching stale template list
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return templates_response
    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Failed to retrieve templates",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.get("/templates/{template_id}", response_model=TemplateDetailResponse)
async def get_control_template(template_id: str):
    """
    获取指定模板详情 (Phase 1A implemented)

    Args:
        template_id: Unique template identifier

    Returns:
        TemplateDetailResponse with complete template details
    """
    try:
        logger.info(f"GET /api/v1/control/templates/{template_id} - Retrieving template")
        response = template_service.get_template_detail(template_id)

        if response is None:
            logger.warning(f"Template not found: {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "TEMPLATE_NOT_FOUND",
                    "message": f"Template with ID '{template_id}' not found",
                    "details": {"requested_id": template_id}
                }
            )

        logger.info(f"Successfully returned template: {template_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Failed to retrieve template",
                "details": {"template_id": template_id, "error_type": type(e).__name__}
            }
        )


# ==================== 路段选择器 Edge Selector (Phase 1B) ====================

from fastapi import Query
from api.models.requests.edge_query_request import EdgeQueryRequest
from api.models.responses.edge_query_response import EdgeQueryResponse
from api.services.control_strategy_service import ControlStrategyService

# Initialize control strategy service
control_service = ControlStrategyService()


@router.get("/edges/query", response_model=EdgeQueryResponse)
async def query_edges(
    route_codes: str = Query(None, description="Comma-separated route codes"),
    section_codes: str = Query(None, description="Comma-separated section codes"),
    node_types: str = Query(None, description="Comma-separated node types"),
    min_stake: float = Query(None, ge=0, description="Minimum stake (km)"),
    max_stake: float = Query(None, ge=0, description="Maximum stake (km)"),
    min_length: float = Query(None, gt=0, description="Minimum length (m)"),
    max_length: float = Query(None, gt=0, description="Maximum length (m)"),
    route_direction: str = Query(None, description="Direction: clockwise/counterclockwise"),
    demonstration_ids: str = Query(None, description="Comma-separated demonstration IDs"),
    min_lanes: int = Query(None, ge=1, description="Minimum lanes"),
    with_gantry: bool = Query(False, description="Only edges with gantries")
):
    """
    Query road edges with multi-dimensional filters (Phase 1B - US1).

    Supports 11 filter parameters for precise edge selection:
    - Route/section filtering
    - Stake range filtering (km)
    - Length range filtering (m)
    - Lane count filtering
    - Direction filtering (clockwise/counterclockwise)
    - Node type filtering (diverging/merging/entrance/exit)
    - Demonstration area filtering
    - Gantry presence filtering

    Returns:
        EdgeQueryResponse with matching edges and metadata
    """
    try:
        # Create request model for validation
        request = EdgeQueryRequest(
            route_codes=route_codes,
            section_codes=section_codes,
            node_types=node_types,
            min_stake=min_stake,
            max_stake=max_stake,
            min_length=min_length,
            max_length=max_length,
            route_direction=route_direction,
            demonstration_ids=demonstration_ids,
            min_lanes=min_lanes,
            with_gantry=with_gantry
        )

        # Convert to query parameters
        query_params = request.to_query_params()

        # Execute query
        edges = control_service.query_edges_with_filters(**query_params)

        # Convert to response model
        response = EdgeQueryResponse.from_edge_infos(edges)

        return response

    except ValueError as e:
        logger.error(f"Validation error in edge query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "VALIDATION_ERROR",
                "message": str(e),
                "details": {"error_type": "ValueError"}
            }
        )
    except Exception as e:
        logger.error(f"Error querying edges: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            if "connection" in str(e).lower() or "database" in str(e).lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "QUERY_ERROR",
                "message": "Failed to query edges",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.get("/edges/routes", response_model=List[Dict[str, Any]])
async def get_available_routes():
    """
    Get available routes with edge counts (Phase 1B - US5/T022).

    Returns list of routes with metadata for hierarchical filtering.
    Cached for 5 minutes for performance.

    Returns:
        List of route information dicts with route_code and edge_count
    """
    try:
        logger.info("GET /api/v1/control/edges/routes - Fetching available routes")
        routes = control_service.get_available_routes()
        logger.info(f"Successfully returned {len(routes)} routes")
        return routes

    except Exception as e:
        logger.error(f"Error fetching routes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            if "connection" in str(e).lower() or "database" in str(e).lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "METADATA_ERROR",
                "message": "Failed to fetch available routes",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.get("/edges/sections", response_model=List[Dict[str, Any]])
async def get_available_sections(
    route_code: str = Query(None, description="Optional route code filter")
):
    """
    Get available sections with metadata (Phase 1B - US5/T023).

    Optionally filtered by route_code for hierarchical filtering workflow.
    Cached for 5 minutes for performance.

    Args:
        route_code: Optional route code to filter sections

    Returns:
        List of section information dicts with metadata and stake ranges
    """
    try:
        logger.info(
            f"GET /api/v1/control/edges/sections - Fetching sections"
            f"{' for route ' + route_code if route_code else ''}"
        )
        sections = control_service.get_available_sections(route_code=route_code)
        logger.info(f"Successfully returned {len(sections)} sections")
        return sections

    except Exception as e:
        logger.error(f"Error fetching sections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            if "connection" in str(e).lower() or "database" in str(e).lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "METADATA_ERROR",
                "message": "Failed to fetch available sections",
                "details": {"error_type": type(e).__name__, "route_code": route_code}
            }
        )


@router.get("/edges/demonstrations", response_model=List[Dict[str, Any]])
async def get_demonstration_info():
    """
    Get demonstration area information (Phase 1B - US5/T024).

    Returns predefined demonstration areas with edge counts and stake ranges.
    Cached for 5 minutes for performance.

    Returns:
        List of demonstration information dicts with metadata
    """
    try:
        logger.info("GET /api/v1/control/edges/demonstrations - Fetching demonstration info")
        demonstrations = control_service.get_demonstration_info()
        logger.info(f"Successfully returned {len(demonstrations)} demonstration areas")
        return demonstrations

    except Exception as e:
        logger.error(f"Error fetching demonstrations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            if "connection" in str(e).lower() or "database" in str(e).lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "METADATA_ERROR",
                "message": "Failed to fetch demonstration information",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.get("/edges/network_geometry", response_model=Dict[str, Any])
async def get_network_geometry(
    route_codes: str = Query(None, description="Comma-separated route codes to filter geometry")
):
    """
    Get network geometry for Canvas visualization (Phase 1B - US4/T046).

    Returns junction coordinates and edge connections for rendering the network map.
    Cached for 10 minutes for performance.

    Args:
        route_codes: Optional comma-separated route codes (e.g., 'G4202,SA2')

    Returns:
        Dict with junctions and edges:
        {
            "junctions": [
                {"junction_id": "123", "longitude": 104.12, "latitude": 30.67},
                ...
            ],
            "edges": [
                {"edge_id": "-5880", "from_junction": "123", "to_junction": "456", "route_code": "G4202"},
                ...
            ]
        }
    """
    try:
        logger.info(
            f"GET /api/v1/control/edges/network_geometry - Fetching geometry"
            f"{' for routes: ' + route_codes if route_codes else ''}"
        )

        # Parse route codes if provided
        route_list = None
        if route_codes:
            route_list = [r.strip() for r in route_codes.split(',')]

        geometry = control_service.get_network_geometry(route_codes=route_list)

        logger.info(
            f"Successfully returned geometry with {len(geometry['junctions'])} junctions "
            f"and {len(geometry['edges'])} edges"
        )

        return geometry

    except Exception as e:
        logger.error(f"Error fetching network geometry: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            if "connection" in str(e).lower() or "database" in str(e).lower()
            else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "GEOMETRY_ERROR",
                "message": "Failed to fetch network geometry",
                "details": {"error_type": type(e).__name__, "route_codes": route_codes}
            }
        )


class BatchEdgeInfoRequest(BaseModel):
    edge_ids: List[str]


@router.post("/edges/batch-info", response_model=List[Dict[str, Any]])
async def get_batch_edge_info(request: BatchEdgeInfoRequest):
    """
    批量获取路段详细信息 (Phase 2: Task 2.1)

    用于第3步参数配置页面展示完整的路段信息表格。

    Args:
        edge_ids: Edge ID列表

    Returns:
        List of edge information dictionaries with full details:
        - edge_id: Edge标识符
        - route_code: 路线代码 (如 G4202, SA2)
        - section_code: 路段代码 (如 G4202001)
        - start_stake: 起始桩号(米)
        - end_stake: 结束桩号(米)
        - length_m: 长度(米)
        - lane_count: 车道数
        - direction: 方向 (upstream/downstream/clockwise/counterclockwise)
        - node_type: 节点类型
        - from_junction_id: 起点路口ID
        - to_junction_id: 终点路口ID
        - demonstration_segment: 示范段名称(如有)
    """
    try:
        edge_ids = request.edge_ids
        logger.info(f"POST /api/v1/control/edges/batch-info - Fetching {len(edge_ids)} edges")

        # 调用服务获取路段详细信息
        edges_info = control_service.get_batch_edge_info(edge_ids)

        logger.info(f"Successfully returned {len(edges_info)} edge details")

        return edges_info

    except Exception as e:
        logger.error(f"Error fetching batch edge info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "BATCH_EDGE_INFO_ERROR",
                "message": "Failed to fetch batch edge information",
                "details": {"error_type": type(e).__name__, "edge_count": len(request.edge_ids) if request else 0}
            }
        )


# ==================== 策略参数验证和XML预览 Validation & Preview ====================

from shared.control_tools.parameter_validator import validate_strategy_parameters
from shared.control_tools.template_loader import load_template_with_schema


class ValidateParametersRequest(BaseModel):
    """Request model for parameter validation."""
    template_id: str
    parameters: Dict[str, Any]


class ValidateParametersResponse(BaseModel):
    """Response model for parameter validation."""
    valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    converted_parameters: Optional[Dict[str, Any]] = None


class GenerateXMLPreviewRequest(BaseModel):
    """Request model for XML preview generation."""
    template_id: str
    parameters: Dict[str, Any]


class GenerateXMLPreviewResponse(BaseModel):
    """Response model for XML preview generation."""
    valid: bool
    xml_content: Optional[str] = None
    validation_message: str
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []


@router.post("/strategies/validate-params", response_model=ValidateParametersResponse)
async def validate_strategy_parameters_endpoint(request: ValidateParametersRequest):
    """
    Validate strategy parameters against template schema.

    Performs comprehensive validation including:
    - Parameter type checking
    - Constraint validation (min/max, ranges, enums)
    - SUMO-specific validation (vehicle types, time ranges)
    - Unit conversion (hours→seconds, km/h→m/s)

    Args:
        request: ValidateParametersRequest with template_id and parameters

    Returns:
        ValidateParametersResponse with validation result and converted parameters
    """
    try:
        logger.info(f"Validating parameters for template: {request.template_id}")

        # Load template schema
        from pathlib import Path
        templates_dir = Path(__file__).parent.parent.parent / "templates" / "control_strategies"
        template = load_template_with_schema(request.template_id, templates_dir)

        if template is None:
            logger.warning(f"Template not found: {request.template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "TEMPLATE_NOT_FOUND",
                    "message": f"Template '{request.template_id}' not found"
                }
            )

        # Validate parameters
        strategy_type = template.get("strategy_type")
        param_schema = template.get("parameters_schema", [])

        result = validate_strategy_parameters(
            parameters_schema=param_schema,
            parameters=request.parameters,
            strategy_type=strategy_type
        )

        logger.info(
            f"Parameter validation completed",
            extra={
                "template_id": request.template_id,
                "valid": result.valid,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings)
            }
        )

        return ValidateParametersResponse(
            valid=result.valid,
            errors=result.errors,
            warnings=result.warnings,
            converted_parameters=result.converted_parameters
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating parameters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "VALIDATION_ERROR",
                "message": "Failed to validate parameters",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.post("/strategies/generate-xml-preview", response_model=GenerateXMLPreviewResponse)
async def generate_xml_preview_endpoint(request: GenerateXMLPreviewRequest):
    """
    Generate SUMO XML preview from strategy parameters.

    Creates a preview of the generated XML element(s) that will be used in
    the SUMO simulation configuration. Validates parameters first to ensure
    XML generation will succeed.

    Args:
        request: GenerateXMLPreviewRequest with template_id and parameters

    Returns:
        GenerateXMLPreviewResponse with generated XML and validation status
    """
    try:
        logger.info(f"Generating XML preview for template: {request.template_id}")

        # Load template schema
        from pathlib import Path
        templates_dir = Path(__file__).parent.parent.parent / "templates" / "control_strategies"
        template = load_template_with_schema(request.template_id, templates_dir)

        if template is None:
            logger.warning(f"Template not found: {request.template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "TEMPLATE_NOT_FOUND",
                    "message": f"Template '{request.template_id}' not found"
                }
            )

        # Validate parameters first
        strategy_type = template.get("strategy_type")
        param_schema = template.get("parameters_schema", [])

        validation_result = validate_strategy_parameters(
            parameters_schema=param_schema,
            parameters=request.parameters,
            strategy_type=strategy_type
        )

        # If validation fails, return errors without XML
        if not validation_result.valid:
            logger.info(f"XML preview skipped due to validation errors for {request.template_id}")
            return GenerateXMLPreviewResponse(
                valid=False,
                xml_content=None,
                validation_message="Parameters have validation errors. Fix errors before generating XML.",
                errors=validation_result.errors,
                warnings=validation_result.warnings
            )

        # Generate XML preview
        try:
            from shared.control_tools.additional_generator import generate_strategy_xml

            xml_content = generate_strategy_xml(
                template_id=request.template_id,
                template=template,
                parameters=validation_result.converted_parameters or request.parameters
            )

            logger.info(
                f"XML preview generated successfully for {request.template_id}",
                extra={
                    "template_id": request.template_id,
                    "xml_length": len(xml_content) if xml_content else 0
                }
            )

            return GenerateXMLPreviewResponse(
                valid=True,
                xml_content=xml_content,
                validation_message="XML preview generated successfully",
                errors=[],
                warnings=validation_result.warnings
            )

        except Exception as e:
            logger.error(f"Error generating XML: {e}", exc_info=True)
            return GenerateXMLPreviewResponse(
                valid=False,
                xml_content=None,
                validation_message=f"Failed to generate XML: {str(e)}",
                errors=[{
                    "parameter": "all",
                    "message": f"XML generation failed: {str(e)}"
                }],
                warnings=validation_result.warnings
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in XML preview endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PREVIEW_ERROR",
                "message": "Failed to generate XML preview",
                "details": {"error_type": type(e).__name__}
            }
        )


# ==================== 控制策略 Strategies ====================
from pathlib import Path
from shared.control_tools.strategy_loader import list_all_strategies, get_strategies_summary


@router.get("/strategies/", response_model=Dict[str, Any])
async def list_strategies(
    strategy_type: str = Query(None, description="Filter by strategy type (VSS/DHS/TEC)"),
    tags: str = Query(None, description="Filter by tags (comma-separated)"),
    status: str = Query(None, description="Filter by status (active/inactive)")
):
    """
    获取所有策略实例列表

    支持按策略类型、标签、状态筛选。

    Args:
        strategy_type: 策略类型筛选 (VSS/DHS/TEC)
        tags: 标签筛选（逗号分隔，匹配任一标签即可）
        status: 状态筛选 (active/inactive)

    Returns:
        {
            "total": 总数,
            "items": 策略列表,
            "summary": 统计摘要
        }
    """
    try:
        logger.info(
            f"GET /api/v1/control/strategies/ - Listing strategies "
            f"(type={strategy_type}, status={status}, tags={tags})"
        )

        # 解析标签
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]

        # 获取策略目录
        strategies_dir = Path(__file__).parent.parent.parent / "control_data" / "strategies"

        # 加载策略列表
        strategies = list_all_strategies(
            strategies_dir=strategies_dir,
            strategy_type=strategy_type,
            tags=tags_list,
            status=status
        )

        # 获取统计摘要
        summary = get_strategies_summary(strategies_dir)

        logger.info(f"Successfully returned {len(strategies)} strategies")

        return {
            "total": len(strategies),
            "items": strategies,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error listing strategies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "STRATEGY_LIST_ERROR",
                "message": "Failed to list strategies",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.post("/strategies/", status_code=501)
async def create_strategy():
    """创建新策略 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.get("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy(strategy_id: str):
    """获取策略详情 (Phase 0 stub)"""
    return {}


@router.put("/strategies/{strategy_id}", status_code=501)
async def update_strategy(strategy_id: str):
    """更新策略 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.delete("/strategies/{strategy_id}", status_code=501)
async def delete_strategy(strategy_id: str):
    """删除策略 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


# ==================== 控制方案 Plans ====================
# Plan management endpoints moved to control_plan_routes.py (Phase 1)


# ==================== 批量仿真 Batch Simulations ====================
@router.get("/batch_simulations/", response_model=List[Dict[str, Any]])
async def list_batch_simulations():
    """获取批量仿真任务列表 (Phase 0 stub)"""
    return []


@router.post("/batch_simulations/", status_code=501)
async def create_batch_simulation():
    """创建批量仿真任务 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.get("/batch_simulations/{batch_id}", response_model=Dict[str, Any])
async def get_batch_simulation(batch_id: str):
    """获取批量仿真任务详情 (Phase 0 stub)"""
    return {}


@router.post("/batch_simulations/{batch_id}/start", status_code=501)
async def start_batch_simulation(batch_id: str):
    """启动批量仿真任务 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}
