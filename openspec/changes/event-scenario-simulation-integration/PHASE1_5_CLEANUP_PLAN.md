# Phase 1.5 Cleanup Plan - Batch Event Simulation Management

**Date**: 2025-11-15
**Status**: Ready for Implementation
**Base Document**: CASE_AND_ANALYSIS_CLEANUP_GUIDE.md (Phase 1.5 section)
**Goal**: Implement batch simulation management for event scenarios

---

## Overview

Phase 1.5 extends Phase 1's consolidated case creation API with dedicated batch simulation management endpoints. This closes the gap between case creation and simulation analysis.

### Key Addition
**3 new REST endpoints** for batch event simulation management:
- `POST /api/v1/event-simulation/batch-start` - Launch batch
- `GET /api/v1/event-simulation/batch-progress/{batch_id}` - Track progress
- `GET /api/v1/event-simulation/batch-results/{batch_id}` - Collect results

### Key Deletion
**4 obsolete endpoints** are now safe to delete:
- `POST /api/v1/simulation/` - Create simulation (deprecated)
- `GET /api/v1/simulation/` - List simulations (deprecated)
- `GET /api/v1/simulation/{sim_id}` - Get details (deprecated)
- `POST /api/v1/simulation/{sim_id}/start` - Start simulation (deprecated)

---

## Implementation Steps

### Step 1: Create Request/Response Models

**File**: `api/models/requests/batch_event_simulation_requests.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class BatchStartEventSimulationRequest(BaseModel):
    """Request to start batch of event simulations"""
    case_ids: Optional[List[str]] = None           # Case IDs containing simulations
    sim_ids: Optional[List[str]] = None            # Direct simulation IDs
    description: Optional[str] = None              # Batch description
    parallel_workers: int = 4                      # Concurrency level (default 4)
    auto_cleanup: bool = True                      # Cleanup after completion
```

**File**: `api/models/responses/batch_event_simulation_responses.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class BatchStartResponse(BaseModel):
    """Response after batch start"""
    batch_id: str                                  # Unique batch identifier
    total_simulations: int                         # Number of simulations
    status: str                                    # "batch_started"
    created_at: datetime

class SimulationProgress(BaseModel):
    """Progress of single simulation"""
    sim_id: str
    case_id: str
    status: str                                    # "pending", "running", "completed", "failed"
    progress: int                                  # 0-100
    eta: Optional[str]                             # ISO 8601 format
    error_msg: Optional[str]

class BatchProgressResponse(BaseModel):
    """Batch progress status"""
    batch_id: str
    total_simulations: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float                        # 0-100
    simulations: List[SimulationProgress]
    batch_status: str                              # "in_progress", "completed", "failed"
    eta_completion: Optional[str]

class SimulationResult(BaseModel):
    """Result of single simulation"""
    sim_id: str
    case_id: str
    status: str
    output_files: List[str]                        # summary.xml, edgedata.xml, etc
    error_msg: Optional[str]

class BatchResultsResponse(BaseModel):
    """Batch results"""
    batch_id: str
    total_simulations: int
    successful: int
    failed: int
    results: List[SimulationResult]
```

---

### Step 2: Implement Event Simulation Service

**File**: `api/services/event_simulation_service.py`

```python
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base_service import BaseService
from ..models.requests.batch_event_simulation_requests import BatchStartEventSimulationRequest
from ..models.responses.batch_event_simulation_responses import (
    BatchStartResponse, BatchProgressResponse, BatchResultsResponse
)

logger = logging.getLogger(__name__)

class EventSimulationService(BaseService):
    """
    批量事件仿真管理服务

    负责：
    1. 启动事件仿真批次
    2. 跟踪批次进度
    3. 收集批次结果
    """

    async def batch_start_event_simulations(
        self,
        request: BatchStartEventSimulationRequest
    ) -> Dict[str, Any]:
        """
        批量启动事件仿真

        Args:
            request: 包含 case_ids 或 sim_ids

        Returns:
            batch_id, total_simulations, status, created_at
        """
        try:
            # 1. 获取模拟数据（实际实现会从DB获取）
            simulations = await self._get_simulations_to_start(request)

            if not simulations:
                raise Exception("No simulations found to start")

            # 2. 创建批次记录
            batch_id = self.generate_unique_id("event_sim_batch")

            logger.info(f"Starting batch {batch_id} with {len(simulations)} simulations")

            # 3. 异步启动所有仿真（非阻塞）
            await self._start_all_simulations_async(batch_id, simulations)

            return {
                "batch_id": batch_id,
                "total_simulations": len(simulations),
                "status": "batch_started",
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to start batch: {str(e)}")
            raise

    async def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """
        获取批次进度

        Args:
            batch_id: 批次ID

        Returns:
            批次进度信息
        """
        try:
            # 1. 从DB获取批次信息
            batch = await self._get_batch_from_db(batch_id)

            if not batch:
                raise Exception(f"Batch {batch_id} not found")

            # 2. 获取所有仿真的状态
            simulations = await self._get_batch_simulations(batch_id)

            # 3. 计算统计信息
            stats = self._calculate_batch_stats(simulations)

            return {
                "batch_id": batch_id,
                "total_simulations": len(simulations),
                "completed": stats["completed"],
                "failed": stats["failed"],
                "running": stats["running"],
                "pending": stats["pending"],
                "progress_percent": stats["progress_percent"],
                "simulations": simulations,
                "batch_status": stats["batch_status"],
                "eta_completion": stats["eta_completion"]
            }

        except Exception as e:
            logger.error(f"Failed to get batch progress: {str(e)}")
            raise

    async def get_batch_results(self, batch_id: str) -> Dict[str, Any]:
        """
        获取批次结果

        Args:
            batch_id: 批次ID

        Returns:
            批次结果
        """
        try:
            # 1. 获取批次仿真
            simulations = await self._get_batch_simulations(batch_id)

            # 2. 聚合结果
            results = [
                {
                    "sim_id": sim["sim_id"],
                    "case_id": sim["case_id"],
                    "status": sim["status"],
                    "output_files": sim.get("output_files", []),
                    "error_msg": sim.get("error_msg")
                }
                for sim in simulations
            ]

            return {
                "batch_id": batch_id,
                "total_simulations": len(simulations),
                "successful": sum(1 for r in results if r["status"] == "completed"),
                "failed": sum(1 for r in results if r["status"] == "failed"),
                "results": results
            }

        except Exception as e:
            logger.error(f"Failed to get batch results: {str(e)}")
            raise

    # ===== Helper Methods =====

    async def _get_simulations_to_start(self, request: BatchStartEventSimulationRequest) -> List[Dict]:
        """Get simulations to start from case_ids or sim_ids"""
        # Implementation would query database for simulations
        return []

    async def _start_all_simulations_async(self, batch_id: str, simulations: List[Dict]):
        """Start all simulations asynchronously"""
        # Implementation would trigger parallel simulation execution
        pass

    async def _get_batch_from_db(self, batch_id: str) -> Optional[Dict]:
        """Get batch record from database"""
        # Implementation would query database
        return None

    async def _get_batch_simulations(self, batch_id: str) -> List[Dict]:
        """Get all simulations in batch"""
        # Implementation would query database
        return []

    def _calculate_batch_stats(self, simulations: List[Dict]) -> Dict:
        """Calculate batch statistics"""
        total = len(simulations)
        completed = sum(1 for s in simulations if s.get("status") == "completed")
        failed = sum(1 for s in simulations if s.get("status") == "failed")
        running = sum(1 for s in simulations if s.get("status") == "running")
        pending = total - completed - failed - running

        progress = (completed + failed) / total * 100 if total > 0 else 0

        return {
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": progress,
            "batch_status": "completed" if pending == 0 and running == 0 else "in_progress",
            "eta_completion": None  # Would calculate based on running simulations
        }
```

---

### Step 3: Create Event Simulation Routes

**File**: `api/routes/event_simulation_routes.py`

```python
from fastapi import APIRouter
from ..models.requests.batch_event_simulation_requests import BatchStartEventSimulationRequest
from ..models.responses.base_response import BaseResponse
from ..services.event_simulation_service import EventSimulationService
from .middleware import handle_service_errors, create_success_response

router = APIRouter()

@router.post("/batch-start", response_model=BaseResponse)
@handle_service_errors
async def batch_start_event_simulations(request: BatchStartEventSimulationRequest):
    """
    批量启动事件仿真 (Phase 1.5)

    在一次操作中启动多个事件仿真，返回batch_id用于追踪进度。

    Args:
        request: 包含 case_ids 或 sim_ids，以及并发参数

    Returns:
        batch_id, total_simulations, status
    """
    service = EventSimulationService()
    result = await service.batch_start_event_simulations(request)
    return create_success_response("批量仿真已启动", result)

@router.get("/batch-progress/{batch_id}", response_model=BaseResponse)
@handle_service_errors
async def get_batch_progress(batch_id: str):
    """
    查询批量仿真进度 (Phase 1.5)

    实时获取批次中各仿真的运行状态和聚合进度。

    Args:
        batch_id: 批次ID

    Returns:
        completed, failed, running, pending, progress_percent, simulations, eta
    """
    service = EventSimulationService()
    progress = await service.get_batch_progress(batch_id)
    return create_success_response("获取批次进度成功", progress)

@router.get("/batch-results/{batch_id}", response_model=BaseResponse)
@handle_service_errors
async def get_batch_results(batch_id: str):
    """
    获取批量仿真结果 (Phase 1.5)

    获取已完成批次中所有仿真的最终结果。

    Args:
        batch_id: 批次ID

    Returns:
        total_simulations, successful, failed, results (per-simulation)
    """
    service = EventSimulationService()
    results = await service.get_batch_results(batch_id)
    return create_success_response("获取批次结果成功", results)
```

---

### Step 4: Delete Obsolete Simulation Endpoints

**File**: `api/routes/simulation_routes.py`

**Remove these endpoints:**
```python
# ❌ DELETE:
@router.post("/")  # Create simulation
@router.get("/")   # List simulations
@router.get("/{sim_id}")  # Get simulation details
@router.post("/{sim_id}/start")  # Start simulation
```

**Keep these endpoints:**
```python
# ✅ KEEP:
@router.post("/run_simulation/")  # Run simulation
@router.post("/prepare_simulation/")  # Prepare simulation
@router.post("/start_simulation/")  # Start simulation
@router.get("/simulation_progress/{case_id}")  # Get progress
@router.get("/simulations/{case_id}")  # Get case simulations
@router.get("/simulation/{simulation_id}")  # Get simulation
@router.delete("/simulation/{simulation_id}")  # Delete simulation
@router.post("/cancel_simulation/")  # Cancel simulation
@router.post("/start-with-event/")  # Start with event
@router.post("/batch-start")  # Batch start (from Phase 2)
```

---

### Step 5: Register New Routes

**File**: `api/main.py`

```python
# Add this to main.py's route registration section:
from .routes.event_simulation_routes import router as event_simulation_router

# Include router
app.include_router(
    event_simulation_router,
    prefix="/api/v1/event-simulation",
    tags=["event-simulation"]
)
```

---

## Acceptance Criteria

### Endpoint Implementation
- [ ] `POST /api/v1/event-simulation/batch-start` works for case_ids or sim_ids
- [ ] `GET /api/v1/event-simulation/batch-progress/{batch_id}` returns real-time stats
- [ ] `GET /api/v1/event-simulation/batch-results/{batch_id}` returns aggregated results
- [ ] All endpoints return properly formatted responses

### Service Implementation
- [ ] `EventSimulationService.batch_start_event_simulations()` creates batch records
- [ ] `EventSimulationService.get_batch_progress()` calculates stats accurately
- [ ] `EventSimulationService.get_batch_results()` aggregates results
- [ ] Service methods handle errors gracefully

### Backward Compatibility
- [ ] OD workflow unaffected
- [ ] Event case creation unchanged
- [ ] Existing batch endpoints unaffected
- [ ] Control plan optimization unaffected

### Obsolete Endpoint Deletion
- [ ] 4 old simulation endpoints removed
- [ ] No other code references deleted endpoints
- [ ] Migration path clear for users

---

## Testing Checklist

### Unit Tests
- [ ] Test: Create batch with case_ids
- [ ] Test: Create batch with sim_ids
- [ ] Test: Batch not found error handling
- [ ] Test: No simulations error handling

### Integration Tests
- [ ] Test: Start batch, verify batch_id returned
- [ ] Test: Get progress of running batch
- [ ] Test: Get results of completed batch
- [ ] Test: Batch with mixed success/failure

### Manual Tests
- [ ] Start batch via API (with real case_ids)
- [ ] Query progress endpoint (real batch_id)
- [ ] Query results endpoint
- [ ] Verify old endpoints return 404

---

## Rollback Plan

If critical issues arise:

```bash
# Revert the specific commit
git revert <commit-hash>

# Or revert all Phase 1.5 changes
git reset --hard HEAD~1
```

---

## Status

**Phase 1.5 Cleanup Status**: 🔄 IN_PROGRESS

- [ ] Models created
- [ ] Service implemented
- [ ] Routes created
- [ ] Old endpoints deleted
- [ ] Tests passing
- [ ] Documentation updated

---

## Next Phase (Phase 2)

After Phase 1.5 completes:
- Implement analysis orchestration service
- Add analysis endpoints
- Create comparative analysis workflow

---

**Document Status**: Ready for Implementation
**Created**: 2025-11-15
**Base Reference**: CASE_AND_ANALYSIS_CLEANUP_GUIDE.md Phase 1.5 section
