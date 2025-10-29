# Control Plan and Batch Optimization API Documentation

## Overview

This document describes the API endpoints for traffic control plan management and batch optimization simulation. These endpoints enable creating, managing, and executing multi-plan comparison simulations with comprehensive result analysis.

**Base URL**: `http://localhost:8000/api/v1/control`

**Content Type**: `application/json`

---

## Control Plan Management

### Create Plan

**Endpoint**: `POST /api/v1/control/plans`

Creates a new traffic control plan with referenced strategies.

**Request Body**:
```json
{
  "plan_name": "plan_vss_morning_peak_simple",
  "plan_description": "早高峰可变限速简单方案",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    }
  ],
  "tags": ["早高峰", "VSS", "G4202"],
  "target_scenario": "工作日早高峰(7:00-9:00)",
  "is_baseline": false
}
```

**Request Parameters**:
- `plan_name` (string, required): Unique plan identifier (max 100 chars)
- `plan_description` (string, optional): Plan description (max 500 chars)
- `strategy_references` (array, required): List of strategy references
  - `strategy_id` (string, required): ID of strategy instance to reference
  - `is_enabled` (boolean, optional): Whether strategy is active (default: true)
  - `priority` (integer, optional): Execution priority (default: 0)
- `tags` (array[string], optional): Categorization tags
- `target_scenario` (string, optional): Target traffic scenario (max 200 chars)
- `is_baseline` (boolean, optional): Whether this is a baseline plan (default: false)

**Response** (200 OK):
```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "plan_name": "plan_vss_morning_peak_simple",
  "plan_description": "早高峰可变限速简单方案",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    }
  ],
  "tags": ["早高峰", "VSS", "G4202"],
  "target_scenario": "工作日早高峰(7:00-9:00)",
  "is_baseline": false,
  "created_at": "2025-10-27T10:30:00Z",
  "updated_at": "2025-10-27T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request data
  ```json
  {
    "detail": "Plan name must not exceed 100 characters"
  }
  ```
- `404 Not Found`: Referenced strategy not found
  ```json
  {
    "detail": "Strategy 'strategy_xxx' not found"
  }
  ```
- `409 Conflict`: Plan with same name already exists
  ```json
  {
    "detail": "Plan 'plan_vss_morning_peak_simple' already exists"
  }
  ```

---

### List Plans

**Endpoint**: `GET /api/v1/control/plans`

Retrieves all control plans with optional filtering.

**Query Parameters**:
- `case_id` (string, optional): Filter by case ID
- `include_baseline` (boolean, optional): Include baseline plans (default: true)
- `tags` (string, optional): Comma-separated tag filter (e.g., "早高峰,VSS")

**Response** (200 OK):
```json
{
  "plans": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "baseline_plan",
      "plan_description": "无控制策略基准方案",
      "strategy_references": [],
      "tags": ["baseline"],
      "target_scenario": "",
      "is_baseline": true,
      "created_at": "2025-10-26T08:00:00Z",
      "updated_at": "2025-10-26T08:00:00Z"
    },
    {
      "plan_id": "plan_vss_morning_peak_simple",
      "plan_name": "plan_vss_morning_peak_simple",
      "plan_description": "早高峰可变限速简单方案",
      "strategy_references": [
        {
          "strategy_id": "strategy_real_vss_g4202_001",
          "is_enabled": true,
          "priority": 1
        }
      ],
      "tags": ["早高峰", "VSS", "G4202"],
      "target_scenario": "工作日早高峰(7:00-9:00)",
      "is_baseline": false,
      "created_at": "2025-10-27T10:30:00Z",
      "updated_at": "2025-10-27T10:30:00Z"
    }
  ],
  "total": 2
}
```

---

### Get Plan Details

**Endpoint**: `GET /api/v1/control/plans/{plan_id}`

Retrieves detailed information about a specific plan.

**Path Parameters**:
- `plan_id` (string, required): Plan identifier

**Response** (200 OK):
```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "plan_name": "plan_vss_morning_peak_simple",
  "plan_description": "早高峰可变限速简单方案",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    }
  ],
  "tags": ["早高峰", "VSS", "G4202"],
  "target_scenario": "工作日早高峰(7:00-9:00)",
  "is_baseline": false,
  "created_at": "2025-10-27T10:30:00Z",
  "updated_at": "2025-10-27T10:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Plan not found
  ```json
  {
    "detail": "Plan 'plan_xxx' not found"
  }
  ```

---

### Update Plan

**Endpoint**: `PUT /api/v1/control/plans/{plan_id}`

Updates an existing control plan.

**Path Parameters**:
- `plan_id` (string, required): Plan identifier

**Request Body**:
```json
{
  "plan_description": "更新的早高峰可变限速简单方案",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    },
    {
      "strategy_id": "strategy_real_vss_g4202_002",
      "is_enabled": true,
      "priority": 2
    }
  ],
  "tags": ["早高峰", "VSS", "G4202", "多策略"],
  "target_scenario": "工作日早高峰(7:00-9:00) - 优化版"
}
```

**Response** (200 OK):
```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "plan_name": "plan_vss_morning_peak_simple",
  "plan_description": "更新的早高峰可变限速简单方案",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    },
    {
      "strategy_id": "strategy_real_vss_g4202_002",
      "is_enabled": true,
      "priority": 2
    }
  ],
  "tags": ["早高峰", "VSS", "G4202", "多策略"],
  "target_scenario": "工作日早高峰(7:00-9:00) - 优化版",
  "is_baseline": false,
  "created_at": "2025-10-27T10:30:00Z",
  "updated_at": "2025-10-27T11:45:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Plan not found
- `400 Bad Request`: Invalid update data
- `403 Forbidden`: Cannot modify baseline plan

---

### Delete Plan

**Endpoint**: `DELETE /api/v1/control/plans/{plan_id}`

Deletes a control plan.

**Path Parameters**:
- `plan_id` (string, required): Plan identifier

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Plan 'plan_vss_morning_peak_simple' deleted successfully"
}
```

**Error Responses**:
- `404 Not Found`: Plan not found
- `403 Forbidden`: Cannot delete baseline plan
- `409 Conflict`: Plan is currently in use by active batch

---

## Batch Optimization

### Create Batch Simulation

**Endpoint**: `POST /api/v1/control/optimization/batch`

Creates a new batch simulation configuration for multi-plan comparison.

**Request Body**:
```json
{
  "case_id": "case_20251027_morning_peak",
  "batch_name": "早高峰VSS策略对比测试",
  "plan_ids": [
    "baseline_plan",
    "plan_vss_morning_peak_simple",
    "plan_vss_dhs_morning_composite"
  ],
  "num_seeds": 3,
  "base_seed": 66
}
```

**Request Parameters**:
- `case_id` (string, required): Case ID for simulation
- `batch_name` (string, optional): Batch description
- `plan_ids` (array[string], required): List of plan IDs to compare (2-10 plans)
- `num_seeds` (integer, optional): Number of random seeds (1-10, default: 3)
- `base_seed` (integer, optional): Starting seed value (default: 66)

**Response** (200 OK):
```json
{
  "batch_id": "batch_20251027_103015_abc123",
  "case_id": "case_20251027_morning_peak",
  "batch_name": "早高峰VSS策略对比测试",
  "plan_ids": [
    "baseline_plan",
    "plan_vss_morning_peak_simple",
    "plan_vss_dhs_morning_composite"
  ],
  "num_seeds": 3,
  "base_seed": 66,
  "total_simulations": 9,
  "estimated_duration_minutes": 18,
  "status": "created",
  "created_at": "2025-10-27T10:30:15Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request data
  ```json
  {
    "detail": "Must select between 2 and 10 plans for comparison"
  }
  ```
- `404 Not Found`: Case or plan not found
  ```json
  {
    "detail": "Plan 'plan_xxx' not found"
  }
  ```

---

### Start Batch Simulation

**Endpoint**: `POST /api/v1/control/optimization/batch/{batch_id}/start`

Starts execution of a created batch simulation.

**Path Parameters**:
- `batch_id` (string, required): Batch identifier

**Response** (200 OK):
```json
{
  "batch_id": "batch_20251027_103015_abc123",
  "status": "running",
  "started_at": "2025-10-27T10:31:00Z",
  "total_simulations": 9,
  "completed_simulations": 0
}
```

**Error Responses**:
- `404 Not Found`: Batch not found
- `409 Conflict`: Batch already running or completed
  ```json
  {
    "detail": "Batch is already running"
  }
  ```

---

### Get Batch Progress

**Endpoint**: `GET /api/v1/control/optimization/batch/{batch_id}/progress`

Retrieves real-time progress of a running batch simulation.

**Path Parameters**:
- `batch_id` (string, required): Batch identifier

**Response** (200 OK):
```json
{
  "batch_id": "batch_20251027_103015_abc123",
  "status": "running",
  "progress": {
    "total_simulations": 9,
    "completed_simulations": 4,
    "failed_simulations": 0,
    "running_simulations": 2,
    "pending_simulations": 3,
    "percentage": 44.4
  },
  "current_simulation": {
    "simulation_id": "sim_baseline_plan_seed67",
    "plan_id": "baseline_plan",
    "seed": 67,
    "status": "running",
    "elapsed_seconds": 45
  },
  "estimated_remaining_minutes": 10,
  "started_at": "2025-10-27T10:31:00Z",
  "updated_at": "2025-10-27T10:35:30Z"
}
```

**Error Responses**:
- `404 Not Found`: Batch not found

---

### Get Batch Results (with Peak Curve Data)

**Endpoint**: `GET /api/v1/control/optimization/batch/{batch_id}/results`

Retrieves comparison results for a completed batch simulation.

**Path Parameters**:
- `batch_id` (string, required): Batch identifier

**Query Parameters**:
- `include_time_series` (boolean, optional): Include time-series data for peak curve visualization (default: false)

**Response without time series** (200 OK):
```json
{
  "batch_id": "batch_20251027_103015_abc123",
  "status": "completed",
  "results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "baseline_plan",
      "avg_travel_time": 1245.3,
      "avg_waiting_time": 456.7,
      "avg_throughput": 3280,
      "num_runs": 3,
      "improvement_vs_baseline": {
        "travel_time_pct": 0.0,
        "waiting_time_pct": 0.0,
        "throughput_pct": 0.0
      }
    },
    {
      "plan_id": "plan_vss_morning_peak_simple",
      "plan_name": "plan_vss_morning_peak_simple",
      "avg_travel_time": 1087.2,
      "avg_waiting_time": 312.4,
      "avg_throughput": 3520,
      "num_runs": 3,
      "improvement_vs_baseline": {
        "travel_time_pct": -12.7,
        "waiting_time_pct": -31.6,
        "throughput_pct": 7.3
      }
    },
    {
      "plan_id": "plan_vss_dhs_morning_composite",
      "plan_name": "plan_vss_dhs_morning_composite",
      "avg_travel_time": 1012.5,
      "avg_waiting_time": 289.1,
      "avg_throughput": 3680,
      "num_runs": 3,
      "improvement_vs_baseline": {
        "travel_time_pct": -18.7,
        "waiting_time_pct": -36.7,
        "throughput_pct": 12.2
      }
    }
  ],
  "baseline_plan_id": "baseline_plan",
  "completed_at": "2025-10-27T10:49:00Z"
}
```

**Response with time series** (`?include_time_series=true`) (200 OK):
```json
{
  "batch_id": "batch_20251027_103015_abc123",
  "status": "completed",
  "results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "baseline_plan",
      "avg_travel_time": 1245.3,
      "avg_waiting_time": 456.7,
      "avg_throughput": 3280,
      "num_runs": 3,
      "improvement_vs_baseline": {
        "travel_time_pct": 0.0,
        "waiting_time_pct": 0.0,
        "throughput_pct": 0.0
      },
      "time_series": {
        "timestamps": [0, 300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000],
        "travel_time": [850.2, 1050.3, 1245.8, 1420.5, 1380.2, 1290.4, 1150.6, 980.3, 820.1, 720.5, 650.2],
        "waiting_time": [120.5, 280.3, 456.8, 520.2, 490.1, 420.3, 340.2, 250.1, 180.4, 120.2, 80.1],
        "throughput": [2800, 3100, 3280, 3350, 3320, 3280, 3150, 2980, 2750, 2500, 2300]
      }
    },
    {
      "plan_id": "plan_vss_morning_peak_simple",
      "plan_name": "plan_vss_morning_peak_simple",
      "avg_travel_time": 1087.2,
      "avg_waiting_time": 312.4,
      "avg_throughput": 3520,
      "num_runs": 3,
      "improvement_vs_baseline": {
        "travel_time_pct": -12.7,
        "waiting_time_pct": -31.6,
        "throughput_pct": 7.3
      },
      "time_series": {
        "timestamps": [0, 300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000],
        "travel_time": [820.1, 950.2, 1087.5, 1220.3, 1180.2, 1090.5, 950.3, 820.4, 710.2, 620.3, 550.1],
        "waiting_time": [100.2, 220.4, 312.6, 380.1, 350.2, 290.4, 230.1, 180.3, 130.2, 90.1, 60.3],
        "throughput": [3000, 3350, 3520, 3600, 3580, 3520, 3400, 3200, 2950, 2700, 2450]
      }
    }
  ],
  "baseline_plan_id": "baseline_plan",
  "completed_at": "2025-10-27T10:49:00Z"
}
```

**Time Series Data Format**:
- `timestamps`: Array of time points in seconds from simulation start
- `travel_time`: Average travel time (seconds) at each time point
- `waiting_time`: Average waiting time (seconds) at each time point
- `throughput`: Vehicle count at each time point

**Error Responses**:
- `404 Not Found`: Batch not found
- `409 Conflict`: Batch not yet completed
  ```json
  {
    "detail": "Batch is still running. Results not available yet."
  }
  ```

---

### Cancel/Delete Batch

**Endpoint**: `DELETE /api/v1/control/optimization/batch/{batch_id}`

Cancels a running batch or deletes a completed batch.

**Path Parameters**:
- `batch_id` (string, required): Batch identifier

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Batch 'batch_20251027_103015_abc123' cancelled successfully"
}
```

**Error Responses**:
- `404 Not Found`: Batch not found

---

## Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 403 | Forbidden - Operation not allowed (e.g., modifying baseline plan) |
| 404 | Not Found - Resource does not exist |
| 409 | Conflict - Resource state conflict (e.g., already running) |
| 500 | Internal Server Error - Server-side error |

---

## Usage Notes

### Plan Management Best Practices

1. **Baseline Plan**: Always create a baseline plan (no strategies) for comparison
2. **Strategy References**: Validate all strategy IDs exist before creating plan
3. **Plan Naming**: Use descriptive names that indicate scenario and strategies (e.g., `plan_vss_dhs_morning_peak`)
4. **Tags**: Use consistent tags for filtering (e.g., "早高峰", "VSS", "G4202")

### Batch Optimization Best Practices

1. **Plan Selection**: Include 2-10 plans for comparison, always include baseline
2. **Random Seeds**: Use 3-5 seeds for statistical significance
3. **Time Series**: Only request `include_time_series=true` when needed for peak curve visualization (larger response)
4. **Monitoring**: Poll progress endpoint every 5-10 seconds during execution
5. **Error Handling**: Check for failed simulations in progress response

### Peak Curve Visualization

To display peak curves in frontend:

1. Request results with `?include_time_series=true`
2. Use `time_series.timestamps` as x-axis labels (convert to HH:MM format)
3. Plot `time_series.travel_time`, `time_series.waiting_time`, or `time_series.throughput` as y-axis
4. Compare multiple plans on same chart using different colors
5. Recommended charting library: Chart.js (already integrated)

---

## Examples

### Complete Workflow Example

```bash
# 1. Create baseline plan
curl -X POST http://localhost:8000/api/v1/control/plans \
  -H "Content-Type: application/json" \
  -d '{
    "plan_name": "baseline_plan",
    "plan_description": "无控制策略基准方案",
    "strategy_references": [],
    "is_baseline": true
  }'

# 2. Create VSS plan
curl -X POST http://localhost:8000/api/v1/control/plans \
  -H "Content-Type: application/json" \
  -d '{
    "plan_name": "plan_vss_morning_peak",
    "plan_description": "早高峰可变限速方案",
    "strategy_references": [
      {
        "strategy_id": "strategy_real_vss_g4202_001",
        "is_enabled": true,
        "priority": 1
      }
    ],
    "tags": ["早高峰", "VSS"]
  }'

# 3. Create batch simulation
curl -X POST http://localhost:8000/api/v1/control/optimization/batch \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_morning_peak",
    "batch_name": "VSS策略效果对比",
    "plan_ids": ["baseline_plan", "plan_vss_morning_peak"],
    "num_seeds": 3
  }'

# Response: {"batch_id": "batch_20251027_103015_abc123", ...}

# 4. Start batch
curl -X POST http://localhost:8000/api/v1/control/optimization/batch/batch_20251027_103015_abc123/start

# 5. Monitor progress
curl http://localhost:8000/api/v1/control/optimization/batch/batch_20251027_103015_abc123/progress

# 6. Get results with peak curves
curl http://localhost:8000/api/v1/control/optimization/batch/batch_20251027_103015_abc123/results?include_time_series=true
```

---

## Changelog

- **2025-10-27**: Added `include_time_series` parameter for peak curve visualization
- **2025-10-26**: Initial API documentation for Phase 2 implementation
