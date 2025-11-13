# Phase 2 API Reference

**Version**: 1.0
**Base URL**: `/api/v1`
**Date**: 2025-11-12

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Case Management](#case-management)
4. [Simulation Execution](#simulation-execution)
5. [Analysis Orchestration](#analysis-orchestration)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## Overview

All Phase 2 APIs use REST principles with JSON request/response bodies.

**Common Headers:**
```
Content-Type: application/json
Accept: application/json
```

**Success Response Format:**
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

**Error Response Format:**
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request parameters",
  "details": { ... }
}
```

---

## Authentication

Currently no authentication required. Future versions will implement JWT-based auth.

---

## Case Management

### Create Case from Scenario

Create a new case from an event scenario.

**Endpoint:** `POST /api/v1/case/create-from-scenario`

**Request Body:**
```json
{
  "scenario_id": "scenario_10754_vss",
  "event_id": "10754",
  "event_type": "01_accident",
  "control_strategy_type": "VSS",
  "simulation_duration_hours": 2.0,
  "random_seed": 42
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scenario_id` | string | Yes | Scenario identifier (e.g., "scenario_10754_vss") |
| `event_id` | string | Yes | Event identifier |
| `event_type` | string | Yes | Event type: "01_accident", "02_congestion", "03_construction" |
| `control_strategy_type` | string | Yes | Control strategy: "baseline", "VSS", "TEC", "DHS" |
| `simulation_duration_hours` | float | No | Simulation duration (default: 2.0) |
| `random_seed` | integer | No | Random seed for reproducibility (default: null) |

**Response:** `201 Created`
```json
{
  "status": "success",
  "data": {
    "case_id": "case_20251112_120000",
    "metadata_version": "2.0",
    "source_scenario": {
      "scenario_id": "scenario_10754_vss",
      "event_id": "10754",
      "event_type": "01_accident",
      "control_strategy_type": "VSS"
    },
    "created_at": "2025-11-12T12:00:00"
  }
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | `INVALID_SCENARIO` | Scenario not found |
| 422 | `VALIDATION_ERROR` | Invalid request parameters |
| 500 | `INTERNAL_ERROR` | Server error during case creation |

---

### Get Case Metadata

Retrieve case metadata including scenario linkage.

**Endpoint:** `GET /api/v1/case/{case_id}/metadata`

**Response:** `200 OK`
```json
{
  "metadata_version": "2.0",
  "case_id": "case_20251112_120000",
  "case_name": "Morning Peak VSS Control Case",
  "created_at": "2025-11-12T12:00:00",
  "source_scenario": {
    "scenario_id": "scenario_10754_vss",
    "event_id": "10754",
    "event_type": "01_accident",
    "control_strategy_type": "VSS"
  },
  "immutable_fields": {
    "event_id": "10754",
    "event_type": "01_accident",
    "location": {
      "road": "G4202",
      "km_point": 30.5
    }
  },
  "overridable_fields": {
    "simulation_duration_hours": 2.0,
    "random_seed": 42
  }
}
```

---

## Simulation Execution

### Prepare Simulation

Prepare a simulation from a case.

**Endpoint:** `POST /api/v1/simulation/prepare`

**Request Body:**
```json
{
  "case_id": "case_20251112_120000"
}
```

**Response:** `201 Created`
```json
{
  "status": "success",
  "data": {
    "simulation_id": "sim_20251112_120530",
    "case_id": "case_20251112_120000",
    "status": "pending",
    "sumocfg_path": "cases/case_20251112_120000/simulations/sim_20251112_120530/simulation.sumocfg"
  }
}
```

---

### Start Batch Simulations

Start multiple simulations concurrently.

**Endpoint:** `POST /api/v1/simulation/batch-start`

**Request Body:**
```json
{
  "simulation_ids": [
    "sim_20251112_120530",
    "sim_20251112_120545",
    "sim_20251112_120600"
  ],
  "parallel_workers": 4,
  "auto_run_analysis": true
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `simulation_ids` | array[string] | Yes | List of simulation IDs (1-100) |
| `parallel_workers` | integer | No | Concurrent workers (2-8, default: 4) |
| `auto_run_analysis` | boolean | No | Auto-run analysis after completion (default: true) |

**Response:** `202 Accepted`
```json
{
  "status": "success",
  "data": {
    "batch_id": "batch_20251112_121000",
    "simulation_ids": [...],
    "total": 3,
    "created_at": "2025-11-12T12:10:00",
    "parallel_workers": 4
  }
}
```

---

### Get Batch Execution Status

Monitor batch simulation progress.

**Endpoint:** `GET /api/v1/simulation/batch-status/{batch_id}`

**Response:** `200 OK`
```json
{
  "batch_id": "batch_20251112_121000",
  "total": 10,
  "completed": 4,
  "failed": 1,
  "in_progress": 2,
  "queued": 3,
  "estimated_completion": "2025-11-12T18:45:00",
  "simulations": [
    {
      "simulation_id": "sim_123",
      "status": "running",
      "progress_percent": 45,
      "vehicles_completed": 5234,
      "total_vehicles": 11650,
      "elapsed_time": "00:45:30",
      "eta": "01:05:15",
      "current_step": 1620,
      "total_steps": 7200
    },
    {
      "simulation_id": "sim_456",
      "status": "completed",
      "progress_percent": 100,
      "elapsed_time": "01:32:45",
      "result_files": {
        "summary": "outputs/summary.xml",
        "tripinfo": "outputs/tripinfo.xml",
        "edgedata": "outputs/edgedata.xml"
      }
    },
    {
      "simulation_id": "sim_789",
      "status": "failed",
      "error_message": "SUMO configuration invalid: missing network file"
    }
  ]
}
```

**Status Values:**
- `pending`: Queued, not started
- `running`: Currently executing
- `completed`: Successfully finished
- `failed`: Encountered error

---

### Cancel Batch Simulations

Stop a running batch gracefully.

**Endpoint:** `POST /api/v1/simulation/batch-cancel`

**Request Body:**
```json
{
  "batch_id": "batch_20251112_121000"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Batch cancellation initiated",
  "batch_id": "batch_20251112_121000",
  "in_progress_simulations": 2
}
```

---

## Analysis Orchestration

### Create Analysis Batch

Run analyses on completed simulations.

**Endpoint:** `POST /api/v1/analysis/run-batch`

**Request Body:**
```json
{
  "simulation_ids": [
    "sim_20251112_120530",
    "sim_20251112_120545"
  ],
  "case_id": "case_20251112_120000",
  "baseline_scenario_id": "scenario_10754_none",
  "comparison_scenario_id": null,
  "analysis_focus": ["summary", "edgedata"],
  "parallel_workers": 4
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `simulation_ids` | array[string] | Yes | Completed simulation IDs |
| `case_id` | string | Yes | Case identifier |
| `baseline_scenario_id` | string | Yes | Baseline scenario for comparison |
| `comparison_scenario_id` | string | No | Additional comparison scenario |
| `analysis_focus` | array[string] | No | Analysis types (default: ["summary", "edgedata"]) |
| `parallel_workers` | integer | No | Concurrent workers (2-8, default: 4) |

**Analysis Types:**
- `summary`: Summary statistics (vehicle counts, speeds, delays)
- `edgedata`: Road segment analysis (required)
- `tripinfo`: Trip-level analysis
- `performance`: System performance metrics

**Response:** `202 Accepted`
```json
{
  "status": "success",
  "data": {
    "batch_id": "analysis_batch_20251112_140000",
    "total_tasks": 8,
    "analysis_focus": ["summary", "edgedata"],
    "created_at": "2025-11-12T14:00:00"
  }
}
```

---

### Get Analysis Progress

Monitor analysis batch progress.

**Endpoint:** `GET /api/v1/analysis/batch-progress/{batch_id}`

**Response:** `200 OK`
```json
{
  "batch_id": "analysis_batch_20251112_140000",
  "total_tasks": 8,
  "completed": 3,
  "failed": 0,
  "in_progress": 2,
  "queued": 3,
  "estimated_completion": "2025-11-12T16:30:00",
  "current_tasks": [
    {
      "task_id": "task_001",
      "simulation_id": "sim_123",
      "analysis_type": "edgedata",
      "status": "running",
      "progress_percent": 65,
      "message": "Processing 2847 edges...",
      "started_at": "2025-11-12T14:05:00"
    },
    {
      "task_id": "task_002",
      "simulation_id": "sim_123",
      "analysis_type": "tripinfo",
      "status": "queued"
    }
  ]
}
```

---

### Get Analysis Results

Retrieve aggregated analysis results.

**Endpoint:** `GET /api/v1/analysis/results/{batch_id}`

**Query Parameters:**
- `format`: Response format ("json" or "summary", default: "json")

**Response:** `200 OK`
```json
{
  "batch_id": "analysis_batch_20251112_140000",
  "case_id": "case_20251112_120000",
  "created_at": "2025-11-12T14:00:00",
  "completed_at": "2025-11-12T16:15:00",
  "source_scenario": {
    "scenario_id": "scenario_10754_vss",
    "event_id": "10754"
  },
  "summary": {
    "total_vehicles": 8934,
    "avg_trip_time": 245.6,
    "completion_rate": 98.7,
    "avg_speed": 52.3
  },
  "edgedata": {
    "num_edges_analyzed": 247,
    "avg_speed_improvement": 12.5,
    "congestion_reduction": 28.3,
    "most_congested_edges": [
      {
        "edge_id": "edge_247",
        "avg_speed": 25.3,
        "congestion_level": "high"
      }
    ]
  },
  "comparison": {
    "baseline_scenario_id": "scenario_10754_none",
    "metrics": {
      "avg_speed": {
        "baseline": 45.0,
        "with_control": 52.3,
        "improvement_percent": 16.2
      },
      "trip_time": {
        "baseline": 200.0,
        "with_control": 185.0,
        "improvement_percent": -7.5
      }
    }
  }
}
```

---

## Data Models

### EventScenarioCaseRequest

```typescript
interface EventScenarioCaseRequest {
  scenario_id: string;          // Required
  event_id: string;              // Required
  event_type: string;            // Required: "01_accident" | "02_congestion" | "03_construction"
  control_strategy_type: string; // Required: "baseline" | "VSS" | "TEC" | "DHS"
  simulation_duration_hours?: number; // Optional, default: 2.0
  random_seed?: number;          // Optional, default: null
}
```

### BatchSimulationStartRequest

```typescript
interface BatchSimulationStartRequest {
  simulation_ids: string[];      // Required, 1-100 items
  parallel_workers?: number;     // Optional, 2-8, default: 4
  auto_run_analysis?: boolean;   // Optional, default: true
}
```

### AnalysisBatchRequest

```typescript
interface AnalysisBatchRequest {
  simulation_ids: string[];           // Required
  case_id: string;                    // Required
  baseline_scenario_id: string;       // Required
  comparison_scenario_id?: string;    // Optional
  analysis_focus?: string[];          // Optional, default: ["summary", "edgedata"]
  parallel_workers?: number;          // Optional, 2-8, default: 4
}
```

---

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_SCENARIO` | 400 | Scenario does not exist |
| `SIMULATION_NOT_READY` | 400 | Simulation not prepared |
| `ANALYSIS_REQUIRES_EDGEDATA` | 400 | EdgeData output required |
| `BATCH_NOT_FOUND` | 404 | Batch ID not found |
| `INTERNAL_ERROR` | 500 | Server error |
| `TIMEOUT` | 504 | Operation timed out |

### Retry Strategy

For transient errors (network, timeouts), implement exponential backoff:
- Attempt 1: Immediate
- Attempt 2: Wait 1s
- Attempt 3: Wait 2s
- Attempt 4: Wait 4s
- Max attempts: 3

**Non-retryable errors:** `VALIDATION_ERROR`, `NOT_FOUND`, `INVALID_SCENARIO`

---

## Rate Limiting

Currently no rate limits. Future versions will implement:
- 100 requests/minute per IP
- 10 concurrent batch operations per user

---

## Examples

### Complete Workflow Example (Python)

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# 1. Create case from scenario
response = requests.post(f"{BASE_URL}/case/create-from-scenario", json={
    "scenario_id": "scenario_10754_vss",
    "event_id": "10754",
    "event_type": "01_accident",
    "control_strategy_type": "VSS",
    "simulation_duration_hours": 0.5,
    "random_seed": 42
})
case_data = response.json()["data"]
case_id = case_data["case_id"]

# 2. Prepare simulation
response = requests.post(f"{BASE_URL}/simulation/prepare", json={
    "case_id": case_id
})
sim_data = response.json()["data"]
sim_id = sim_data["simulation_id"]

# 3. Start batch simulation
response = requests.post(f"{BASE_URL}/simulation/batch-start", json={
    "simulation_ids": [sim_id],
    "parallel_workers": 1,
    "auto_run_analysis": True
})
batch_data = response.json()["data"]
batch_id = batch_data["batch_id"]

# 4. Monitor progress
while True:
    response = requests.get(f"{BASE_URL}/simulation/batch-status/{batch_id}")
    status = response.json()

    print(f"Progress: {status['completed']}/{status['total']}")

    if status["queued"] == 0 and status["in_progress"] == 0:
        break

    time.sleep(10)

print("Simulation completed!")

# 5. Analysis runs automatically if auto_run_analysis=True
# Retrieve results
response = requests.get(f"{BASE_URL}/analysis/results/{batch_id}")
results = response.json()
print(f"Analysis results: {results['summary']}")
```

---

**Last Updated**: 2025-11-12
**Version**: 1.0
**Feedback**: Report API issues via GitHub
