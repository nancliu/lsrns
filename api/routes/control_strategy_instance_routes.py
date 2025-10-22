"""
Control Strategy Instance Routes (Phase 1C)

REST API endpoints for strategy instance CRUD operations.
Separate from control_strategy_routes.py (Phase 1B - edge selector).

Endpoints:
- POST   /api/v1/control/strategy-instances          - Create strategy
- GET    /api/v1/control/strategy-instances          - List strategies (paginated)
- GET    /api/v1/control/strategy-instances/{id}     - Get strategy details
- PUT    /api/v1/control/strategy-instances/{id}     - Update strategy
- DELETE /api/v1/control/strategy-instances/{id}     - Delete strategy
- POST   /api/v1/control/strategy-instances/reindex  - Regenerate index (admin)
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from api.services.strategy_instance_service import StrategyInstanceService
from api.models.requests.strategy_requests import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
)
from api.models.responses.strategy_responses import (
    StrategyCreateResponse,
    StrategyDetailResponse,
    StrategyListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/control/strategy-instances",
    tags=["Strategy Instances"]
)

# Service instance (singleton pattern)
_service_instance = None


def get_strategy_service() -> StrategyInstanceService:
    """Get or create strategy instance service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = StrategyInstanceService()
    return _service_instance


@router.post(
    "/",
    response_model=StrategyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Strategy Instance",
    description="Create a new traffic control strategy instance from a template"
)
async def create_strategy(
    request: StrategyCreateRequest
) -> StrategyCreateResponse:
    """
    Create a new strategy instance.

    **Request Body**:
    - `strategy_name`: User-defined name (1-100 characters)
    - `template_id`: Reference to existing template (Phase 1A)
    - `parameters`: Configured parameter values (validated against template schema)
    - `affected_edges`: List of edge IDs (minimum 1 required)

    **Response**: 201 Created with strategy_id and success message

    **Errors**:
    - 400 Bad Request: Validation failed (invalid parameters, edges)
    - 404 Not Found: Template not found
    - 500 Internal Server Error: File save failed
    """
    try:
        service = get_strategy_service()
        response = service.create_strategy(request)
        return response

    except ValueError as e:
        error_msg = str(e)

        # Check if error is due to missing template (should be 404)
        if "Template not found" in error_msg:
            logger.warning(f"Template not found: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        # All other ValueError are validation errors (400)
        logger.error(f"Validation error creating strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        # Internal errors
        logger.error(f"Error creating strategy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create strategy"
        )


@router.get(
    "/",
    response_model=StrategyListResponse,
    summary="List Strategy Instances",
    description="Get paginated list of strategy instances with optional filtering"
)
async def list_strategies(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by strategy name"),
    strategy_type: Optional[str] = Query(None, description="Filter by type (VSS/DHS/TEC)")
) -> StrategyListResponse:
    """
    List strategies with pagination and filtering.

    **Query Parameters**:
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `search`: Optional search string for strategy name
    - `strategy_type`: Optional filter by type (VSS, DHS, TEC)

    **Response**: Paginated list with total count
    """
    try:
        service = get_strategy_service()
        response = service.list_strategies(
            page=page,
            page_size=page_size,
            search=search,
            strategy_type=strategy_type
        )
        return response

    except Exception as e:
        logger.error(f"Error listing strategies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list strategies"
        )


@router.get(
    "/{strategy_id}",
    response_model=StrategyDetailResponse,
    summary="Get Strategy Details",
    description="Get complete details of a strategy instance including enriched edge data"
)
async def get_strategy(
    strategy_id: str
) -> StrategyDetailResponse:
    """
    Get strategy details by ID.

    **Path Parameters**:
    - `strategy_id`: Unique strategy identifier

    **Response**: Complete strategy details with:
    - Basic info (name, type, template)
    - Configured parameters
    - Affected edges with details (route, stake, length)
    - Metadata (created_at, updated_at, version)

    **Errors**:
    - 404 Not Found: Strategy does not exist
    """
    try:
        service = get_strategy_service()
        response = service.get_strategy(strategy_id)

        if response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy"
        )


@router.put(
    "/{strategy_id}",
    response_model=StrategyDetailResponse,
    summary="Update Strategy Instance",
    description="Update an existing strategy instance with optimistic concurrency control"
)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateRequest
) -> StrategyDetailResponse:
    """
    Update an existing strategy.

    **Path Parameters**:
    - `strategy_id`: Unique strategy identifier

    **Request Body**:
    - `strategy_name`: Optional updated name
    - `parameters`: Optional updated parameter values
    - `affected_edges`: Optional updated edge list
    - `original_updated_at`: Required for concurrency check (ISO8601 timestamp)

    **Response**: Updated strategy details with incremented version

    **Errors**:
    - 400 Bad Request: Validation failed
    - 404 Not Found: Strategy does not exist
    - 409 Conflict: Concurrency conflict (strategy modified by another user)
    """
    try:
        service = get_strategy_service()
        response = service.update_strategy(strategy_id, request)

        if response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        return response

    except ValueError as e:
        # Check if concurrency conflict
        if "Concurrency conflict" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        # Validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update strategy"
        )


@router.delete(
    "/{strategy_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Strategy Instance",
    description="Delete a strategy instance (fails if used in plans)"
)
async def delete_strategy(
    strategy_id: str
) -> dict:
    """
    Delete a strategy instance.

    **Path Parameters**:
    - `strategy_id`: Unique strategy identifier

    **Response**: Success message

    **Errors**:
    - 404 Not Found: Strategy does not exist
    - 409 Conflict: Strategy is used in plans (Phase 2)
    """
    try:
        service = get_strategy_service()
        success = service.delete_strategy(strategy_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        return {
            "message": f"Strategy {strategy_id} deleted successfully"
        }

    except ValueError as e:
        # Used in plans
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy {strategy_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete strategy"
        )


@router.post(
    "/reindex",
    summary="Regenerate Strategy Index",
    description="Admin endpoint to regenerate the strategy index from all files"
)
async def reindex_strategies() -> dict:
    """
    Regenerate the strategy index.

    Scans all strategy JSON files and rebuilds the index.
    Used for recovery when index is corrupted or missing.

    **Response**: Count of indexed strategies and duration

    **Note**: This is an admin operation and should be used sparingly.
    """
    try:
        service = get_strategy_service()
        result = service.reindex_strategies()
        return result

    except Exception as e:
        logger.error(f"Error reindexing strategies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reindex strategies"
        )
