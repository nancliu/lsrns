"""
交通管控策略路由
"""

from fastapi import APIRouter
from typing import List, Dict, Any

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
async def list_control_templates():
    """
    获取所有策略模板列表 (Phase 1A implemented)

    Returns:
        TemplateListResponse with all valid templates and statistics
    """
    try:
        logger.info("GET /api/v1/control/templates/ - Listing templates")
        response = template_service.list_templates()
        logger.info(f"Successfully returned {response.total_count} templates")
        return response
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


# ==================== 控制策略 Strategies ====================
@router.get("/strategies/", response_model=Dict[str, Any])
async def list_strategies():
    """获取所有策略列表 (Phase 0 stub)"""
    return {"total": 0, "items": []}


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
@router.get("/plans/", response_model=List[Dict[str, Any]])
async def list_plans():
    """获取所有方案列表 (Phase 0 stub)"""
    return []


@router.post("/plans/", status_code=501)
async def create_plan():
    """创建新方案 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


@router.get("/plans/{plan_id}", response_model=Dict[str, Any])
async def get_plan(plan_id: str):
    """获取方案详情 (Phase 0 stub)"""
    return {}


@router.post("/plans/{plan_id}/generate", status_code=501)
async def generate_plan_additional(plan_id: str):
    """生成Additional文件 (Phase 0 not implemented)"""
    return {"detail": "Phase 0: Not implemented yet"}


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
