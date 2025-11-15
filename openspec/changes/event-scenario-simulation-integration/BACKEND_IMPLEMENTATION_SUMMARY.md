# Event-Scenario Batch Backend Implementation Summary

**Date**: 2025-11-15
**Status**: ✅ Backend Implementation Complete
**Architecture**: Event Batch Workflow (One Event = One Batch)

---

## Overview

Implemented complete backend infrastructure for event-scenario batch management following the simplified workflow design where one event creates one batch containing multiple scenarios (NO_CONTROL, VSS, TEC, DHS).

This implementation follows the proven optimization.html batch pattern for consistency and code reuse.

---

## Implementation Details

### 1. EventBatchService (Backend Core)

**File**: `api/services/event_batch_service.py` (~650 LOC)

**Purpose**: Manages event-scenario batches (one event = one batch with multiple scenarios)

**Key Methods**:

1. **`create_event_batch(event_id, scenario_ids, simulation_config)`**
   - Creates batch directory structure
   - Generates cases for each scenario
   - Prepares simulations for each case
   - Saves batch metadata with scenario linkage
   - Returns batch_id, case_ids, simulation_ids

2. **`list_event_batches(status, limit)`**
   - Lists all event batches from `cases/batch_event_*` directories
   - Filters by status (created|running|completed|failed|all)
   - Sorts by creation time (newest first)
   - Returns paginated results

3. **`get_event_batch_status(batch_id)`**
   - Loads batch metadata
   - Queries real-time simulation status for each scenario
   - Calculates overall progress percentage
   - Updates and returns current status

4. **`start_event_batch(batch_id, parallel_workers, auto_run_analysis)`**
   - Starts all simulations in the batch
   - Supports parallel execution (1-8 workers)
   - Updates batch status to "running"
   - Returns execution status

5. **`get_event_batch_results(batch_id)`**
   - Aggregates simulation metrics by strategy type
   - Parses summary.xml for each simulation
   - Calculates improvement vs baseline (NO_CONTROL)
   - Ranks strategies by overall improvement
   - Returns comparison data and rankings

6. **`_get_simulation_metrics(case_id, simulation_id)`** ⭐ NEW
   - **Real summary.xml parsing** (replaced mock data)
   - Extracts: avg_speed, avg_trip_duration, completion_rate, total_vehicles, total_delay
   - Handles missing files gracefully
   - Converts m/s to km/h for speed
   - Calculates derived metrics

7. **`_calculate_improvements(metrics, baseline)`**
   - Calculates percentage improvements vs baseline
   - Handles "higher is better" metrics (speed, completion_rate)
   - Handles "lower is better" metrics (trip_duration, delay)

8. **`_rank_strategies(strategy_comparison, baseline)`**
   - Ranks strategies by weighted overall improvement
   - Assigns rank numbers (1=best)
   - Returns sorted ranking list

**Data Structures**:

```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "batch_type": "event_scenario",
  "event_id": "8210655",
  "event_type": "congestion",
  "created_at": "2025-11-15T10:00:00",
  "scenarios": [
    {
      "scenario_id": "scenario_8210655_no_control",
      "strategy_type": "NO_CONTROL",
      "case_id": "case_20251115_001",
      "simulation_id": "sim_20251115_001"
    }
  ],
  "status": "created|running|completed|failed",
  "total_simulations": 3,
  "completed_simulations": 0,
  "running_simulations": 0,
  "failed_simulations": 0
}
```

---

### 2. API Routes

**File**: `api/routes/batch_routes.py` (~220 LOC)

**Router**: `/api/v1/batch`
**Tag**: "Event Batch Management"

**Endpoints**:

1. **POST `/create-from-event`**
   - Request: CreateEventBatchRequest
   - Response: EventBatchCreatedResponse (201)
   - Creates event-scenario batch

2. **GET `/list-event-batches?status={status}&limit={limit}`**
   - Query: status (optional), limit (default: 50)
   - Response: EventBatchListResponse
   - Lists event batches

3. **GET `/event-batch-status/{batch_id}`**
   - Path: batch_id
   - Response: EventBatchStatusResponse
   - Returns real-time status

4. **POST `/start-event-batch`**
   - Request: StartEventBatchRequest
   - Response: EventBatchStartedResponse
   - Starts batch simulations

5. **GET `/event-batch-results/{batch_id}`**
   - Path: batch_id
   - Response: EventBatchResultsResponse
   - Returns aggregated results with strategy comparison

**Error Handling**:
- 404: Batch not found
- 400: Invalid request (missing event_id, invalid config)
- 500: Internal server error (with detailed logging)

---

### 3. Request/Response Models

**Files Created**:

1. **`api/models/requests/batch_requests.py`**
   - `CreateEventBatchRequest`
   - `StartEventBatchRequest`

2. **`api/models/responses/batch_responses.py`**
   - `EventBatchCreatedResponse`
   - `EventBatchStatusResponse`
   - `EventBatchListResponse`
   - `EventBatchStartedResponse`
   - `EventBatchResultsResponse`
   - `SimulationStatusDetail`
   - `StrategyMetrics`
   - `StrategyRanking`

**Example Response** (EventBatchResultsResponse):

```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "event_id": "8210655",
  "strategy_comparison": {
    "NO_CONTROL": {
      "avg_speed": 45.2,
      "avg_trip_duration": 1200.0,
      "completion_rate": 96.5,
      "total_vehicles": 8934
    },
    "VSS": {
      "avg_speed": 52.8,
      "avg_trip_duration": 1050.0,
      "completion_rate": 98.2,
      "improvement_vs_baseline": {
        "avg_speed": 16.8,
        "avg_trip_duration": -12.5
      }
    }
  },
  "strategy_ranking": [
    {"strategy": "VSS", "overall_improvement": 15.5, "rank": 1},
    {"strategy": "TEC", "overall_improvement": 10.2, "rank": 2}
  ]
}
```

---

### 4. Service Registration

**File Modified**: `api/services/__init__.py`

```python
from .event_batch_service import EventBatchService

event_batch_service = EventBatchService()

__all__ = [
    # ... existing exports ...
    "EventBatchService",
    "event_batch_service",
]
```

**File Modified**: `api/routes/__init__.py`

```python
from .batch_routes import router as batch_router

router.include_router(batch_router, tags=["事件批次管理"])
```

---

## Batch Metadata Structure

**Location**: `cases/batch_event_{event_id}_{timestamp}/batch_metadata.json`

```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "batch_type": "event_scenario",
  "event_id": "8210655",
  "event_type": "congestion",
  "created_at": "2025-11-15T10:00:00",

  "scenarios": [
    {
      "scenario_id": "scenario_8210655_no_control",
      "strategy_type": "NO_CONTROL",
      "case_id": "case_20251115_001",
      "simulation_id": "sim_20251115_001",
      "event_type": "congestion",
      "location": {
        "road": "G5京昆高速",
        "direction": "下行",
        "edge_id": "-3734"
      }
    }
  ],

  "status": "created",
  "total_simulations": 3,
  "completed_simulations": 0,
  "running_simulations": 0,
  "failed_simulations": 0,

  "simulation_progress": {
    "started_at": null,
    "completed_at": null,
    "estimated_completion": null
  },

  "analysis_batch_id": null,
  "simulation_config": {
    "duration_hours": null,
    "random_seed": 12345,
    "output_config": {
      "tripinfo": true,
      "edgedata": true,
      "summary": true
    }
  }
}
```

---

## Summary.xml Parsing

**Implementation**: `_get_simulation_metrics()` method

**Extracted Metrics**:
- `loaded`: Total vehicles loaded
- `ended`: Vehicles that completed trips
- `running`: Vehicles still running
- `waiting`: Vehicles waiting to insert
- `speed`: Average speed (converted to km/h)

**Calculated Metrics**:
- `avg_speed`: Average speed in km/h
- `avg_trip_duration`: Simulation time / ended vehicles
- `completion_rate`: (ended / loaded) * 100
- `total_vehicles`: loaded
- `total_delay`: Estimated from waiting vehicles
- `avg_waiting_time`: waiting / total_vehicles

**File Location**:
```
cases/{case_id}/simulations/{simulation_id}/output/summary.xml
```

**Error Handling**:
- Returns zero metrics if file not found
- Logs warning but doesn't crash
- Allows batch to continue even if some simulations failed

---

## Workflow Example

### 1. Create Event Batch

```http
POST /api/v1/batch/create-from-event
{
  "event_id": "8210655",
  "scenario_ids": null,  // Use all scenarios for this event
  "simulation_config": {
    "duration_hours": null,
    "random_seed": 12345,
    "output_config": {
      "tripinfo": true,
      "edgedata": true,
      "summary": true
    }
  }
}

Response:
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "event_id": "8210655",
  "total_scenarios": 3,
  "case_ids": ["case_001", "case_002", "case_003"],
  "simulation_ids": ["sim_001", "sim_002", "sim_003"],
  "status": "created"
}
```

### 2. Start Batch

```http
POST /api/v1/batch/start-event-batch
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "parallel_workers": 4,
  "auto_run_analysis": true
}
```

### 3. Monitor Status

```http
GET /api/v1/batch/event-batch-status/batch_event_8210655_20251115_100000

Response:
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "status": "running",
  "total_simulations": 3,
  "completed_simulations": 1,
  "running_simulations": 2,
  "progress_percent": 33,
  "simulations": [...]
}
```

### 4. Get Results

```http
GET /api/v1/batch/event-batch-results/batch_event_8210655_20251115_100000

Response:
{
  "strategy_comparison": {...},
  "strategy_ranking": [
    {"strategy": "VSS", "overall_improvement": 15.5, "rank": 1}
  ]
}
```

---

## Files Created/Modified

### Created:
1. `api/services/event_batch_service.py` (~650 LOC)
2. `api/routes/batch_routes.py` (~220 LOC)
3. `api/models/requests/batch_requests.py` (~60 LOC)
4. `api/models/responses/batch_responses.py` (~200 LOC)

### Modified:
1. `api/services/__init__.py` (+3 lines)
2. `api/routes/__init__.py` (+2 lines)

**Total New Code**: ~1,130 LOC
**Total Modified Code**: ~5 LOC

---

## Testing Checklist

- [ ] Create event batch via API
- [ ] List event batches
- [ ] Get batch status (real-time)
- [ ] Start batch simulations
- [ ] Monitor simulation progress
- [ ] Get batch results with comparison
- [ ] Verify summary.xml parsing
- [ ] Test error handling (missing files, invalid IDs)

---

## Next Steps

1. ✅ Backend Implementation (COMPLETED)
2. 🔄 Frontend Implementation (IN PROGRESS)
   - Refactor case-simulation-center.html to 3-view structure
   - Implement batch configuration UI
   - Implement batch monitoring UI
   - Integrate comparison table component
3. ⏳ Integration Testing
4. ⏳ Documentation Update

---

## Comparison with Optimization Workflow

| Feature | Optimization Batch | Event Batch |
|---------|-------------------|-------------|
| **Concept** | Plan → Batch → Simulations | Event → Batch → Scenarios |
| **Grouping** | One plan per batch | One event per batch |
| **Baseline** | baseline_plan | NO_CONTROL scenario |
| **Strategies** | Control strategies | NO_CONTROL, VSS, TEC, DHS |
| **Results** | Plan comparison | Strategy comparison |
| **Metrics** | summary.xml | summary.xml |
| **Ranking** | By improvement | By improvement |

**Design Goal**: Maximum code reuse from proven optimization pattern

---

## Architecture Compliance

✅ **Non-Breaking**: No changes to existing OD/Control workflows
✅ **Backward Compatible**: Uses v2.0 metadata with source_scenario field
✅ **Service Isolation**: EventBatchService independent from existing services
✅ **API Separation**: New endpoints under `/api/v1/batch/`
✅ **Metadata Versioning**: Explicit batch_type = "event_scenario"

---

## Status

**Backend**: ✅ Complete
**Frontend**: 🔄 In Progress
**Testing**: ⏳ Pending
**Documentation**: ✅ Complete

**Last Updated**: 2025-11-15
**Maintainer**: Development Team
