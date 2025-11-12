# analysis-orchestration Specification

## Purpose

Enable automatic execution of multiple analysis types (EdgeData, TripInfo, Accuracy, Performance) across multiple simulations with real-time progress tracking and complete metadata lineage tracking.

---

## Requirements

### Requirement: Analysis Batch Creation and Task Queuing

The system SHALL create an analysis batch and queue analysis tasks for multiple simulations.

**Rationale**: Users need to run multiple analysis types on multiple simulations efficiently without manual orchestration.

#### Scenario: Create analysis batch with valid simulations

- **GIVEN** 10 completed simulations with simulation_metadata.json present
- **AND** baseline_scenario_id="scenario_12547_none"
- **AND** analysis_focus=["edgedata", "tripinfo"]
- **WHEN** `create_analysis_batch()` is called
- **THEN** returns batch_id (e.g., "analysis_batch_20251112_130000")
- **AND** creates `analysis_tasks_index.json` in case directory with:
  ```json
  {
    "batch_id": "analysis_batch_20251112_130000",
    "total_tasks": 20,  // 10 sims × 2 analysis types
    "tasks": [
      {"task_id": "task_001", "simulation_id": "sim_1", "analysis_type": "edgedata", "status": "queued"},
      {"task_id": "task_002", "simulation_id": "sim_1", "analysis_type": "tripinfo", "status": "queued"},
      ...
    ]
  }
  ```
- **AND** all tasks have status="queued"
- **AND** background executor begins processing tasks

#### Scenario: Enforce EdgeData as mandatory analysis (AD-10)

- **GIVEN** analysis_focus=["tripinfo"]  (missing edgedata)
- **WHEN** `create_analysis_batch()` is called
- **THEN** automatically adds "edgedata" to analysis_focus
- **AND** ensures edgedata analysis is always included
- **AND** logs: "EdgeData added (mandatory per AD-10)"

#### Scenario: Validate simulation exists before queueing

- **GIVEN** simulation_ids=["sim_valid", "sim_invalid"]
- **WHEN** `create_analysis_batch()` is called
- **THEN** raises ValidationError for "sim_invalid"
- **AND** error message: "Simulation not found: sim_invalid"
- **AND** no batch is created

#### Scenario: Handle optional analysis types

- **GIVEN** analysis_focus=["edgedata", "accuracy", "performance"]
- **WHEN** `create_analysis_batch()` is called
- **THEN** queues all 3 analysis types
- **AND** creates tasks for each combination (sim × analysis_type)
- **AND** optional analyses can be skipped if dependencies unavailable (e.g., no gantry data for accuracy)

---

### Requirement: Real-Time Analysis Progress Tracking

The system SHALL provide real-time progress updates for running analysis batches.

**Rationale**: Long-running analyses (EdgeData on large simulations) need progress visibility to prevent users from thinking the system is hung.

#### Scenario: Get progress with active tasks

- **GIVEN** analysis batch with 40 tasks (10 sims × 4 analysis types)
- **AND** 10 tasks completed, 5 running, 25 queued
- **WHEN** `get_analysis_progress(batch_id)` is called
- **THEN** returns:
  ```json
  {
    "batch_id": "analysis_batch_20251112_130000",
    "total_tasks": 40,
    "completed": 10,
    "failed": 0,
    "in_progress": 5,
    "queued": 25,
    "progress_percent": 25,
    "estimated_completion": "2025-11-12T16:30:00",
    "current_tasks": [
      {
        "task_id": "task_001",
        "simulation_id": "sim_1",
        "analysis_type": "edgedata",
        "status": "running",
        "progress": 65,
        "message": "Processing 2847 edges..."
      },
      ...
    ]
  }
  ```
- **AND** estimated_completion calculated as: `current_time + (elapsed_time / completed_tasks) × remaining_tasks`
- **AND** response completes within 2 seconds
- **AND** progress updates every 10 seconds (not 1-second for DB efficiency)

#### Scenario: Handle batch completion

- **GIVEN** all 40 tasks completed
- **WHEN** `get_analysis_progress(batch_id)` is called
- **THEN** returns:
  ```json
  {
    "batch_id": "analysis_batch_20251112_130000",
    "total_tasks": 40,
    "completed": 40,
    "failed": 0,
    "in_progress": 0,
    "queued": 0,
    "progress_percent": 100,
    "status": "completed"
  }
  ```
- **AND** estimated_completion is null
- **AND** no longer updates progress

#### Scenario: Detect analysis failures

- **GIVEN** analysis batch with 40 tasks
- **AND** 5 tasks have failed (e.g., missing output files)
- **WHEN** `get_analysis_progress(batch_id)` is called
- **THEN** returns:
  ```json
  {
    "failed": 5,
    "failed_tasks": [
      {
        "task_id": "task_005",
        "simulation_id": "sim_2",
        "analysis_type": "edgedata",
        "status": "failed",
        "error": "Output file not found: edgedata.xml"
      },
      ...
    ]
  }
  ```
- **AND** allows user to retry failed tasks

---

### Requirement: Three-Level Metadata Tracking (AD-12)

The system SHALL track metadata through Case → Simulation → Analysis for complete lineage.

**Rationale**: Users need to trace analysis results back to the originating scenario for impact assessment and reproducibility.

#### Scenario: Create analysis metadata with complete lineage

- **GIVEN** simulation_metadata.json with source_scenario_id="scenario_12547_vss"
- **WHEN** analysis batch is created
- **THEN** generates analysis_metadata.json with:
  ```json
  {
    "analysis_batch_id": "analysis_batch_20251112_130000",
    "simulation_id": "sim_20251112_120530",
    "source_scenario": {
      "scenario_id": "scenario_12547_vss",
      "event_id": "12547",
      "event_type": "01_accident",
      "control_strategy_type": "VSS"
    },
    "source_simulation": {
      "source_scenario_id": "scenario_12547_vss"
    }
  }
  ```
- **AND** enables complete backtracking: analysis → simulation → scenario

#### Scenario: Analysis isolation (never modify case/simulation metadata)

- **GIVEN** case_metadata.json and simulation_metadata.json exist
- **WHEN** analysis batch executes and completes
- **THEN** case_metadata.json is not modified
- **AND** simulation_metadata.json is not modified
- **AND** results stored only in `case/analysis/batch_id/` directory
- **AND** all analysis services use read-only pattern for case/sim metadata

#### Scenario: Backtrack from analysis to scenario

- **GIVEN** analysis result: "edgedata analysis shows edge_5 avg_speed=25 km/h"
- **WHEN** user needs to trace back to event
- **THEN** can compute:
  1. analysis_metadata.json → source_simulation_id: "sim_20251112_120530"
  2. simulation_metadata.json → source_scenario_id: "scenario_12547_vss"
  3. scenario_index.json → event_12547 details (location, time, type)
- **AND** can identify that edge_5 is on G4202 K30 (most_congested area)
- **AND** complete lineage chain visible to user

---

### Requirement: Configurable Worker Pool

The system SHALL support configurable parallel execution (2-8 workers).

**Rationale**: Different hardware configurations need different concurrency levels. 2 workers for lightweight, 8 for production.

#### Scenario: Execute tasks with 4 workers

- **GIVEN** analysis batch with 40 tasks
- **AND** parallel_workers=4
- **WHEN** executor starts
- **THEN** maintains 4 concurrent analysis processes
- **AND** when a task completes, immediately picks next queued task
- **AND** progress updates reflect worker utilization
- **AND** completes all 40 tasks in ~1/4 the time of serial execution

#### Scenario: Validate worker count bounds

- **GIVEN** parallel_workers=1 (too low)
- **WHEN** `create_analysis_batch()` is called
- **THEN** raises ValidationError: "parallel_workers must be 2-8"
- **AND** defaults to 4 if not specified

#### Scenario: Handle worker crashes gracefully

- **GIVEN** worker process crashes mid-analysis
- **WHEN** executor detects crash (exit code != 0)
- **THEN** marks task as "failed"
- **AND** retries up to 3 times with exponential backoff (1s, 2s, 4s)
- **AND** continues with next task
- **AND** logs crash details for debugging

---

### Requirement: Automatic Retry on Transient Failures

The system SHALL automatically retry failed tasks with exponential backoff.

**Rationale**: Transient failures (network blip, temp file lock) shouldn't stop the entire batch.

#### Scenario: Retry on transient network error

- **GIVEN** analysis task fails with connection timeout
- **WHEN** executor detects transient error
- **THEN** retries immediately with 1 second delay
- **AND** if still fails, retries with 2 second delay
- **AND** if still fails, retries with 4 second delay
- **AND** if still fails after 3 attempts, marks as "failed"

#### Scenario: Fail immediately on validation errors

- **GIVEN** analysis task fails because "output file not found"
- **WHEN** executor detects validation error
- **THEN** immediately marks as "failed"
- **AND** does NOT retry (no point)
- **AND** logs validation error with task details

#### Scenario: Retry count enforcement

- **GIVEN** max_retry_attempts=3
- **WHEN** task fails 3 times
- **THEN** stops retrying and marks as "failed"
- **AND** logs: "Task failed after 3 retries"
- **AND** moves to next task

---

### Requirement: Analysis Batch Cancellation

The system SHALL support graceful cancellation of analysis batches.

**Rationale**: Users may need to stop long-running analysis batches to save resources.

#### Scenario: Cancel running analysis batch

- **GIVEN** analysis batch with 40 tasks
- **AND** 10 completed, 5 running, 25 queued
- **WHEN** `cancel_analysis_batch(batch_id)` is called
- **THEN** marks batch status as "cancelled"
- **AND** stops queuing new tasks
- **AND** allows in-flight tasks to complete gracefully
- **AND** waits max 30 seconds for in-flight tasks
- **AND** updates batch_status to "cancelled" with timestamp

#### Scenario: Cancel completed batch (no-op)

- **GIVEN** analysis batch with all 40 tasks completed
- **WHEN** `cancel_analysis_batch(batch_id)` is called
- **THEN** returns success response
- **AND** no action taken (already completed)

---

## API Endpoints (Reference)

### POST /api/v1/analysis/run

Create analysis batch and start execution.

**Request**:
```json
{
  "simulation_ids": ["sim_1", "sim_2", ...],
  "case_id": "case_20251112_120000",
  "baseline_scenario_id": "scenario_12547_none",
  "comparison_scenario_id": null,
  "analysis_focus": ["edgedata", "tripinfo"],
  "parallel_workers": 4
}
```

**Response**:
```json
{
  "batch_id": "analysis_batch_20251112_130000",
  "simulation_ids": ["sim_1", "sim_2", ...],
  "total_tasks": 20,
  "created_at": "2025-11-12T13:00:00"
}
```

### GET /api/v1/analysis/batch-progress/{batch_id}

Get real-time progress of analysis batch.

**Response**: See progress tracking requirement above.

### DELETE /api/v1/analysis/batch/{batch_id}

Cancel analysis batch.

**Response**:
```json
{
  "batch_id": "analysis_batch_20251112_130000",
  "status": "cancelled",
  "cancelled_at": "2025-11-12T13:30:00"
}
```

---

## Data Structures

### analysis_tasks_index.json

Located at: `cases/case_id/analysis/batch_id/analysis_tasks_index.json`

```json
{
  "batch_id": "analysis_batch_20251112_130000",
  "case_id": "case_20251112_120000",
  "created_at": "2025-11-12T13:00:00",
  "status": "running",
  "config": {
    "simulation_ids": ["sim_1", "sim_2"],
    "baseline_scenario_id": "scenario_12547_none",
    "analysis_focus": ["edgedata", "tripinfo"]
  },
  "summary": {
    "total_tasks": 4,
    "completed": 1,
    "failed": 0,
    "in_progress": 1,
    "queued": 2
  },
  "tasks": [
    {
      "task_id": "task_001",
      "simulation_id": "sim_1",
      "analysis_type": "edgedata",
      "status": "completed",
      "started_at": "2025-11-12T13:05:00",
      "completed_at": "2025-11-12T13:35:00",
      "elapsed_seconds": 1800
    }
  ]
}
```

### analysis_metadata.json

Located at: `cases/case_id/analysis/batch_id/analysis_metadata.json`

```json
{
  "analysis_batch_id": "analysis_batch_20251112_130000",
  "case_id": "case_20251112_120000",
  "simulation_id": "sim_20251112_120530",
  "created_at": "2025-11-12T13:00:00",
  "source_scenario": {
    "scenario_id": "scenario_12547_vss",
    "event_id": "12547",
    "event_type": "01_accident"
  },
  "analysis_config": {
    "baseline_scenario_id": "scenario_12547_none",
    "analysis_types": [
      {
        "type": "edgedata",
        "enabled": true,
        "status": "completed",
        "result_dir": "edgedata/"
      },
      {
        "type": "tripinfo",
        "enabled": true,
        "status": "completed",
        "result_dir": "tripinfo/"
      }
    ]
  }
}
```

---

## Constraints & Dependencies

- **AD-10**: EdgeData is MANDATORY (cannot disable)
- **AD-12**: Metadata isolation enforced (analysis never modifies case/sim files)
- **Depends on**: Simulation execution service must be completed first
- **Blocks**: Analysis results aggregation (depends on this batch completing)

---

## Testing Strategy

- Unit tests: Task queue creation, progress calculation, retry logic
- Integration tests: Full batch execution with mocked analyses
- E2E tests: Real analysis execution with 5 simulations
- Performance: 80 simulations × 4 analysis types (320 tasks) completes in < 10 hours

---

**Specification Complete**
