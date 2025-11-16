# Phase 1.5 Implementation Strategy - Batch Event Simulation Management

**Date**: 2025-11-15
**Status**: Planning & Preparation
**Scope**: Event simulation batch management APIs
**Duration**: ~1 day for full implementation
**Dependencies**: Phase 1 complete ✅ (API consolidated, service methods unified)

---

## Executive Summary

Phase 1.5 extends Phase 1's consolidated API with batch simulation management capabilities for event scenarios. This enables users to:
- ✅ Launch multiple simulations in parallel
- ✅ Track progress in real-time
- ✅ Collect results in batches
- ✅ Monitor ETA and resource utilization

**Key Addition**: 3 new REST endpoints for batch event simulation management

---

## Scope Definition

### What Phase 1.5 Implements

**3 New Endpoints:**
```
POST   /api/v1/event-simulation/batch-start              Batch start simulations
GET    /api/v1/event-simulation/batch-progress/{batch_id} Query batch progress
GET    /api/v1/event-simulation/batch-results/{batch_id}  Get batch results
```

**1 New Service:**
```
api/services/event_simulation_service.py  Batch simulation orchestration
```

**Models for:**
- BatchStartEventSimulationRequest
- BatchStartResponse
- BatchProgressResponse
- BatchResultsResponse

### What Phase 1.5 REMOVES

**4 Obsolete Endpoints** (now safe to delete):
```
❌ POST /api/v1/simulation/              Create individual simulation
❌ GET  /api/v1/simulation/              List simulations
❌ GET  /api/v1/simulation/{sim_id}      Get simulation details
❌ POST /api/v1/simulation/{sim_id}/start Start individual simulation
```

**Rationale**: Event simulations are now created automatically via case creation. Batch management replaces individual simulation management.

### What Phase 1.5 PRESERVES

**Existing functionality:**
- ✅ OD simulation workflow (unchanged)
- ✅ Control plan optimization (unchanged)
- ✅ Case management (unchanged)
- ✅ Event case creation with auto-simulation (from Phase 1)

---

## Technical Architecture

### New Service: EventSimulationService

**Purpose**: Coordinate batch execution and progress tracking for event simulations

**Methods to Implement:**

```python
class EventSimulationService(BaseService):
    """Event simulation batch management"""

    # 1. Batch Launch
    async def batch_start_event_simulations(
        self,
        request: BatchStartEventSimulationRequest
    ) -> BatchStartResponse:
        """Start multiple event simulations in parallel"""
        # Validate simulations exist
        # Create batch record in DB
        # Trigger async execution
        # Return batch_id for tracking

    # 2. Progress Tracking
    async def get_batch_progress(
        self,
        batch_id: str
    ) -> BatchProgressResponse:
        """Get real-time progress of running batch"""
        # Query batch from DB
        # Get status of each simulation
        # Calculate aggregate stats (%, ETA, etc)
        # Return comprehensive progress info

    # 3. Results Collection
    async def get_batch_results(
        self,
        batch_id: str
    ) -> BatchResultsResponse:
        """Get final results of completed batch"""
        # Query completed batch
        # Aggregate output files
        # Include error details if any failed
        # Return summary + detailed results
```

### New Routes: event_simulation_routes.py

```python
@router.post("/batch-start", response_model=BaseResponse)
async def batch_start_event_simulations(request: BatchStartEventSimulationRequest):
    """Start multiple event simulations"""
    service = EventSimulationService()
    result = await service.batch_start_event_simulations(request)
    return create_success_response("Batch started", result)

@router.get("/batch-progress/{batch_id}", response_model=BaseResponse)
async def get_batch_progress(batch_id: str):
    """Get batch progress"""
    service = EventSimulationService()
    progress = await service.get_batch_progress(batch_id)
    return create_success_response("Progress retrieved", progress)

@router.get("/batch-results/{batch_id}", response_model=BaseResponse)
async def get_batch_results(batch_id: str):
    """Get batch results"""
    service = EventSimulationService()
    results = await service.get_batch_results(batch_id)
    return create_success_response("Results retrieved", results)
```

### New Models

**Request:**
```python
class BatchStartEventSimulationRequest(BaseModel):
    case_ids: Optional[List[str]] = None      # Case IDs containing simulations
    sim_ids: Optional[List[str]] = None       # Direct simulation IDs
    description: Optional[str] = None         # Batch description
    parallel_workers: int = 4                 # Concurrency level
    auto_cleanup: bool = True                 # Auto-cleanup after completion
```

**Responses:**
```python
class BatchStartResponse(BaseModel):
    batch_id: str                             # Unique batch identifier
    total_simulations: int                    # Number of simulations
    status: str                               # "batch_started", "batch_completed", etc
    created_at: datetime

class SimulationProgress(BaseModel):
    sim_id: str
    status: str                               # "pending", "running", "completed", "failed"
    progress: int                             # 0-100%
    eta: Optional[str]                        # ISO 8601 ETA
    error_msg: Optional[str]                  # Error message if failed

class BatchProgressResponse(BaseModel):
    batch_id: str
    total_simulations: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float                   # 0-100%
    simulations: List[SimulationProgress]
    batch_status: str                         # "in_progress", "completed", etc
    eta_completion: Optional[str]

class BatchResultsResponse(BaseModel):
    batch_id: str
    total_simulations: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]             # Per-simulation results
```

---

## Implementation Stages

### Stage 1: Models (30 min)
**Files**: `api/models/requests/batch_event_simulation_requests.py`, `api/models/responses/batch_event_simulation_responses.py`

```
- [x] Create BatchStartEventSimulationRequest model
- [ ] Create BatchStartResponse model
- [ ] Create BatchProgressResponse & SimulationProgress models
- [ ] Create BatchResultsResponse model
- [ ] Add to __init__.py exports
```

### Stage 2: Service Implementation (2 hours)
**Files**: `api/services/event_simulation_service.py`

```
- [ ] Create EventSimulationService class
- [ ] Implement batch_start_event_simulations() method
- [ ] Implement get_batch_progress() method
- [ ] Implement get_batch_results() method
- [ ] Add helper methods (_get_simulations, _create_batch, etc)
- [ ] Add logging and error handling
- [ ] Add to services/__init__.py exports
```

### Stage 3: Routes (1 hour)
**Files**: `api/routes/event_simulation_routes.py`

```
- [ ] Create new event_simulation_routes.py
- [ ] Implement POST /batch-start endpoint
- [ ] Implement GET /batch-progress/{batch_id} endpoint
- [ ] Implement GET /batch-results/{batch_id} endpoint
- [ ] Add error handling and validation
- [ ] Register routes in main.py (include_router)
```

### Stage 4: Delete Obsolete Endpoints (30 min)
**Files**: `api/routes/simulation_routes.py`

```
- [ ] Delete POST /api/v1/simulation/ endpoint
- [ ] Delete GET /api/v1/simulation/ endpoint
- [ ] Delete GET /api/v1/simulation/{sim_id} endpoint
- [ ] Delete POST /api/v1/simulation/{sim_id}/start endpoint
- [ ] Clean up unused service methods if any
```

### Stage 5: Testing & Verification (1-2 hours)
```
- [ ] Syntax validation
- [ ] Unit tests for service methods
- [ ] Integration tests for endpoints
- [ ] Manual API testing
- [ ] Verify backward compatibility
```

---

## Integration with Phase 1

### Phase 1 Consolidation (Completed)
- ✅ POST /api/v1/case/ (OD workflow)
- ✅ POST /api/v1/case/from-event-scenario (Event workflow with auto-simulation)
- ✅ Event simulations created automatically
- ✅ Service method renamed and unified

### Phase 1.5 Extension (This Phase)
- ⏳ POST /api/v1/event-simulation/batch-start (Batch launch)
- ⏳ GET /api/v1/event-simulation/batch-progress/{batch_id} (Progress tracking)
- ⏳ GET /api/v1/event-simulation/batch-results/{batch_id} (Results collection)
- ⏳ Delete now-safe old simulation endpoints

### Dependency Chain
```
Phase 1: Create event cases + auto-create simulations
    ↓
Phase 1.5: Batch manage those simulations
    ↓
Phase 2: Run comparative analysis on batches
```

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Breaking old simulation endpoints | 🟢 Low | Already consolidated, users expect migration |
| Batch tracking complexity | 🟡 Medium | Use simple DB schema, tested with unit tests |
| Concurrent simulation execution | 🟡 Medium | Use worker pool with configurable concurrency |
| Progress tracking accuracy | 🟡 Medium | Real-time updates via polling or webhooks |

**Overall Risk**: 🟡 **MEDIUM** (More complex than Phase 1, but well-scoped)

---

## Success Criteria

### Functional Requirements
- [x] Batch start accepts case_ids or sim_ids
- [x] Batch creates unique batch_id for tracking
- [x] Progress endpoint returns real-time stats
- [x] Results endpoint aggregates final outcomes
- [x] All simulations execute in parallel
- [x] Errors handled gracefully (partial success)

### Non-Functional Requirements
- [x] Response times < 1 second for progress/results
- [x] Batch tracking persists across server restarts
- [x] Supports 10-1000 simulations per batch
- [x] Progress updates every 5-10 seconds
- [x] No data loss if process crashes

### Backward Compatibility
- [x] OD workflow unaffected
- [x] Control plan optimization unaffected
- [x] Event case creation unaffected
- [x] Existing cases continue to work

---

## Timeline Estimate

| Task | Duration | Status |
|------|----------|--------|
| Models | 30 min | ⏳ Pending |
| Service | 2 hours | ⏳ Pending |
| Routes | 1 hour | ⏳ Pending |
| Delete endpoints | 30 min | ⏳ Pending |
| Testing | 1-2 hours | ⏳ Pending |
| Documentation | 1 hour | ⏳ Pending |
| **Total** | **~6-7 hours** | **⏳ Pending** |

**Can be completed in 1 day** with focused implementation

---

## Documentation Plan

### Files to Create/Update

**New Documentation:**
- PHASE1_5_CLEANUP_PLAN.md - Step-by-step implementation guide
- PHASE1_5_IMPLEMENTATION_STATUS.md - Current state analysis
- PHASE1_5_MIGRATION_GUIDE.md - User migration instructions
- PHASE1_5_READINESS_SUMMARY.md - Executive summary

**Files to Update:**
- CASE_AND_ANALYSIS_CLEANUP_GUIDE.md - Add Phase 1.5 status
- IMPLEMENTATION_INDEX.md - Add Phase 1.5 navigation
- 00_START_HERE.md - Update with Phase 1.5 info

---

## Next Phase (Phase 2)

**What comes after Phase 1.5:**
- Implement comparative analysis endpoints
- Add analysis orchestration service
- Create analysis progress tracking
- Deliver analysis results via API

---

## Sign-Off

**Phase 1.5 Strategy Document**: ✅ **APPROVED FOR IMPLEMENTATION**

All scoping complete. Ready to begin implementation following the 5-stage plan.

**Next Step**: Begin Stage 1 (Models) implementation

---

**Document Status**: Ready for Implementation
**Created**: 2025-11-15
**Base Reference**: CASE_AND_ANALYSIS_CLEANUP_GUIDE.md Phase 1.5 section
