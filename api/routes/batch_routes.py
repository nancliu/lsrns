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


@router.delete("/reset-scenario-mapping/{case_id}", status_code=200)
async def reset_case_scenario_mapping(case_id: str):
    """
    重置/删除某个case在scenario_index.json中的所有关联

    从所有scenario的created_cases中删除该case（反向操作）

    **Path Parameters:**
    - case_id: 案例ID (e.g., "case_event_10754")

    **Returns:**
    - 删除结果统计

    **Example:**
    DELETE /api/v1/batch/reset-scenario-mapping/case_event_10754
    """
    try:
        logger.info(f"Resetting scenario mapping for case: {case_id}")

        from shared.utilities.scenario_case_mapping import ScenarioCaseMapper
        mapper = ScenarioCaseMapper()

        removed_count = mapper.unregister_case_from_all_scenarios(case_id)

        return {
            "success": True,
            "case_id": case_id,
            "scenarios_affected": removed_count,
            "message": f"✓ 已从 {removed_count} 个scenario中删除该case"
        }

    except Exception as e:
        logger.error(f"Failed to reset scenario mapping: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset scenario mapping: {str(e)}"
        )


@router.delete("/clear-scenario-cases/{scenario_id}", status_code=200)
async def clear_scenario_created_cases(scenario_id: str):
    """
    清空某个scenario的所有created_cases（重置操作）

    删除该scenario中的所有已创建案例的关联信息

    **Path Parameters:**
    - scenario_id: 场景ID (e.g., "scenario_10754_no_control")

    **Returns:**
    - 清空结果统计

    **Example:**
    DELETE /api/v1/batch/clear-scenario-cases/scenario_10754_no_control
    """
    try:
        logger.info(f"Clearing created cases for scenario: {scenario_id}")

        from shared.utilities.scenario_case_mapping import ScenarioCaseMapper
        mapper = ScenarioCaseMapper()

        removed_count = mapper.clear_scenario_cases(scenario_id)

        return {
            "success": True,
            "scenario_id": scenario_id,
            "cases_removed": removed_count,
            "message": f"✓ 已清空该scenario的 {removed_count} 个created_cases"
        }

    except Exception as e:
        logger.error(f"Failed to clear scenario cases: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear scenario cases: {str(e)}"
        )


@router.post("/reset-all-scenario-mappings", status_code=200)
async def reset_all_scenario_mappings():
    """
    重置整个scenario_index.json - 清空所有created_cases（管理员操作）

    **⚠️ 警告**: 这是一个破坏性操作，将清空所有scenario的created_cases关联
    仅在确实需要重置整个系统时使用

    **Returns:**
    - 重置结果统计

    **Example:**
    POST /api/v1/batch/reset-all-scenario-mappings
    """
    try:
        logger.warning("⚠️ ADMIN ACTION: Resetting all scenario mappings!")

        from shared.utilities.scenario_case_mapping import ScenarioCaseMapper
        mapper = ScenarioCaseMapper()

        result = mapper.reset_all_cases()

        logger.warning(
            f"✓ Reset completed: {result['total_cases_removed']} cases removed "
            f"from {result['total_scenarios_affected']} scenarios"
        )

        return {
            "success": True,
            "total_cases_removed": result['total_cases_removed'],
            "total_scenarios_affected": result['total_scenarios_affected'],
            "message": f"✓ 已清空所有 {result['total_cases_removed']} 个case，影响 {result['total_scenarios_affected']} 个scenarios"
        }

    except Exception as e:
        logger.error(f"Failed to reset all scenario mappings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset all scenario mappings: {str(e)}"
        )


@router.delete("/delete-event-cases/{event_id}", status_code=200)
async def delete_event_cases(event_id: str):
    """
    Delete the case folder for an event

    Deletes the case folder (case_event_{event_id}) created for a specific event
    and resets the created_cases in scenario_index.json.

    **Process:**
    1. Delete cases/case_event_{event_id} folder
    2. Clear created_cases for all scenarios of this event in scenario_index.json
    3. Save updated scenario_index.json

    **Args:**
        event_id: The event ID (e.g., "10754")

    **Response:**
        {
            "success": true,
            "event_id": "10754",
            "scenarios_affected": 3,
            "message": "✓ 已删除事件10754的案例文件夹，清除3个scenarios的关联"
        }

    **Example:**
        DELETE /api/v1/batch/delete-event-cases/10754
    """
    try:
        from pathlib import Path
        import shutil
        import json

        cases_dir = Path("cases")
        case_folder_name = f"case_event_{event_id}"
        case_folder = cases_dir / case_folder_name
        scenario_index_path = Path("output") / "scenarios" / "scenario_index.json"

        # Load scenario_index.json
        if not scenario_index_path.exists():
            return {
                "success": True,
                "event_id": event_id,
                "scenarios_affected": 0,
                "message": f"✓ 事件{event_id}没有创建的案例"
            }

        with open(scenario_index_path, 'r', encoding='utf-8') as f:
            scenario_index = json.load(f)

        # Find all scenarios for this event
        scenarios_for_event = [
            s for s in scenario_index.get('scenarios', [])
            if s.get('event_id') == event_id
        ]

        if not scenarios_for_event:
            return {
                "success": True,
                "event_id": event_id,
                "scenarios_affected": 0,
                "message": f"✓ 事件{event_id}没有创建的案例"
            }

        # Delete the case folder
        if case_folder.exists():
            try:
                shutil.rmtree(case_folder)
                logger.info(f"✓ Deleted case folder: {case_folder_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete case folder {case_folder_name}: {e}")

        # Clear created_cases for all scenarios of this event
        scenarios_affected = 0
        for scenario in scenarios_for_event:
            if scenario.get('created_cases'):
                scenario['created_cases'] = []
                scenarios_affected += 1

        # Save updated scenario_index.json
        with open(scenario_index_path, 'w', encoding='utf-8') as f:
            json.dump(scenario_index, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Updated scenario_index.json for event {event_id}")

        return {
            "success": True,
            "event_id": event_id,
            "scenarios_affected": scenarios_affected,
            "message": f"✓ 已删除事件{event_id}的案例文件夹，清除{scenarios_affected}个scenarios的关联"
        }

    except Exception as e:
        logger.error(f"Failed to delete event cases: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete event cases: {str(e)}"
        )
