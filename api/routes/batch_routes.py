"""
Event-Scenario Batch Routes

API endpoints for event-scenario batch management.
Treats one event as one batch (similar to optimization batches).

Author: Development Team
Date: 2025-11-15
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

from api.services import event_batch_service
from api.models.requests.batch_requests import (
    CreateEventBatchRequest,
    StartEventBatchRequest
)
from api.models.responses.batch_responses import (
    EventBatchCreatedResponse,
    EventBatchStatusResponse,
    EventBatchListResponse,
    EventBatchStartedResponse,
    EventBatchResultsResponse,
    EventBatchListItem
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/batch", tags=["Event Batch Management"])


@router.post("/create-from-event", response_model=EventBatchCreatedResponse, status_code=201)
async def create_event_batch(request: CreateEventBatchRequest):
    """
    Create event-scenario batch

    Creates cases and simulations for all scenarios of a given event.
    Treats one event as one batch (similar to optimization batches).

    **Process:**
    1. Find all scenarios for the event
    2. Create batch directory
    3. Create cases for each scenario
    4. Prepare simulations for each case
    5. Save batch metadata

    **Args:**
    - event_id: Event ID
    - scenario_ids: List of scenario IDs (if None, use all scenarios for this event)
    - simulation_config: Simulation configuration (optional)

    **Returns:**
    - Batch metadata with case_ids and simulation_ids
    """
    try:
        logger.info(f"Creating event batch for event_id={request.event_id}")

        result = await event_batch_service.create_event_batch(
            event_id=request.event_id,
            scenario_ids=request.scenario_ids,
            simulation_config=request.simulation_config
        )

        logger.info(f"Event batch created successfully: {result['batch_id']}")
        return EventBatchCreatedResponse(**result)

    except FileNotFoundError as e:
        logger.error(f"Scenario index not found: {e}")
        raise HTTPException(status_code=404, detail=f"Scenario index not found: {str(e)}")

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to create event batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create event batch: {str(e)}"
        )


@router.get("/list-event-batches", response_model=EventBatchListResponse)
async def list_event_batches(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List event-scenario batches

    **Query Parameters:**
    - status: Filter by status (created|running|completed|failed|all)
    - limit: Max number of batches to return (default: 50)

    **Returns:**
    - List of event batches sorted by creation time (newest first)
    """
    try:
        logger.info(f"Listing event batches: status={status}, limit={limit}")

        batches = await event_batch_service.list_event_batches(
            status=status,
            limit=limit
        )

        batch_items = [EventBatchListItem(**batch) for batch in batches]

        return EventBatchListResponse(
            batches=batch_items,
            total_count=len(batch_items)
        )

    except Exception as e:
        logger.error(f"Failed to list event batches: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list event batches: {str(e)}"
        )


@router.get("/event-batch-status/{batch_id}", response_model=EventBatchStatusResponse)
async def get_event_batch_status(batch_id: str):
    """
    Get event-scenario batch status

    Returns real-time status with simulation progress details.

    **Path Parameters:**
    - batch_id: Batch ID

    **Returns:**
    - Batch status with simulation details
    """
    try:
        logger.info(f"Getting batch status for: {batch_id}")

        status_data = await event_batch_service.get_event_batch_status(batch_id)

        return EventBatchStatusResponse(**status_data)

    except ValueError as e:
        logger.error(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to get batch status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


@router.post("/start-event-batch", response_model=EventBatchStartedResponse)
async def start_event_batch(request: StartEventBatchRequest):
    """
    Start all simulations in an event-scenario batch

    **Request Body:**
    - batch_id: Batch ID
    - parallel_workers: Number of parallel simulation workers (1-8, default: 4)
    - auto_run_analysis: Auto-run analysis after completion (default: true)

    **Returns:**
    - Batch execution status
    """
    try:
        logger.info(f"Starting event batch: {request.batch_id}")

        result = await event_batch_service.start_event_batch(
            batch_id=request.batch_id,
            parallel_workers=request.parallel_workers,
            auto_run_analysis=request.auto_run_analysis
        )

        return EventBatchStartedResponse(**result)

    except ValueError as e:
        logger.error(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to start batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch: {str(e)}"
        )


@router.get("/event-batch-results/{batch_id}", response_model=EventBatchResultsResponse)
async def get_event_batch_results(batch_id: str):
    """
    Get aggregated analysis results for an event-scenario batch

    Aggregates simulation results by strategy type and calculates
    improvement vs baseline (NO_CONTROL).

    **Path Parameters:**
    - batch_id: Batch ID

    **Returns:**
    - Strategy comparison metrics and ranking
    """
    try:
        logger.info(f"Getting batch results for: {batch_id}")

        results = await event_batch_service.get_event_batch_results(batch_id)

        return EventBatchResultsResponse(**results)

    except ValueError as e:
        logger.error(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to get batch results: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch results: {str(e)}"
        )
