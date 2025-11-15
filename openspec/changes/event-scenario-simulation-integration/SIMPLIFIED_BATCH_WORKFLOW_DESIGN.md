# Simplified Event-Scenario Batch Workflow Design

**Date:** 2025-11-15
**Issue:** Current case management page has confusing logic with separated tabs
**Solution:** Treat event-scenario batches like optimization batches (one event = one batch)

---

## Problem Analysis

### Current Implementation Issues

**case-simulation-center.html** has 3 tabs:
1. Tab 1: Case Management (individual cases)
2. Tab 2: Simulation Monitoring (batch progress)
3. Tab 3: Analysis (results)

**Problems:**
- ❌ Cases and batches are separate concepts (confusing)
- ❌ User must manage individual cases AND batches
- ❌ No clear linkage between event → batch → analysis
- ❌ Doesn't leverage existing optimization workflow patterns

### Optimization Workflow Pattern (Reference)

**control/optimization.html** workflow:
```
Plan (方案) → Batch (批次) → Monitoring (监控) → Results (结果)
```

**Key Features:**
- One plan creates one batch
- Batch contains multiple simulations (different strategies)
- Unified batch monitoring page
- Integrated results visualization

---

## Proposed Solution: Event-Scenario Batch Workflow

### Conceptual Model

```
Event (事件) ≈ Plan (方案)
Event-Scenario Batch (事件场景批次) ≈ Optimization Batch (优化批次)
```

**Workflow:**
```
Event 8210655 (Flow Surge)
    ↓
Event-Scenario Batch (batch_event_8210655_20251115)
    ├── Case 1: scenario_8210655_no_control (Baseline)
    ├── Case 2: scenario_8210655_vss
    ├── Case 3: scenario_8210655_tec
    └── Case 4: scenario_8210655_dhs
    ↓
Batch Simulation (4 simulations running in parallel)
    ↓
Batch Analysis (multi-scenario comparison)
```

### Data Model

#### Event-Scenario Batch Metadata

**Location:** `cases/batch_event_{event_id}_{timestamp}/batch_metadata.json`

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
        },
        {
            "scenario_id": "scenario_8210655_vss",
            "strategy_type": "VSS",
            "case_id": "case_20251115_002",
            "simulation_id": "sim_20251115_002"
        },
        {
            "scenario_id": "scenario_8210655_tec",
            "strategy_type": "TEC",
            "case_id": "case_20251115_003",
            "simulation_id": "sim_20251115_003"
        }
    ],

    "status": "created|running|completed|failed",
    "total_simulations": 3,
    "completed_simulations": 0,
    "failed_simulations": 0,

    "simulation_progress": {
        "started_at": null,
        "completed_at": null,
        "estimated_completion": null
    },

    "analysis_batch_id": null
}
```

### Simplified Page Structure

#### Page: case-simulation-center.html (Renamed from current)

**New Name:** `event-batch-center.html` or keep `case-simulation-center.html` but simplify

**Structure (3 Views, similar to optimization.html):**

```
┌─ View 1: Batch Configuration (批次配置) ─────────────┐
│ ✅ Event selector (from scenario_index.json)         │
│ ✅ Scenario preview (NO_CONTROL, VSS, TEC, DHS)     │
│ ✅ Simulation config (duration, seeds, output)       │
│ ✅ [Create Batch] button                             │
└──────────────────────────────────────────────────────┘

┌─ View 2: Batch Monitoring (批次监控) ────────────────┐
│ ✅ Batch list (event-based batches)                  │
│ ✅ Batch selector (select active/completed batch)    │
│ ✅ Real-time progress (total, running, completed)    │
│ ✅ Simulation table (status, progress, logs)         │
│ ✅ [Start Batch] [Cancel Batch] buttons              │
└──────────────────────────────────────────────────────┘

┌─ View 3: Batch Results (批次结果) ───────────────────┐
│ ✅ Multi-scenario comparison                         │
│ ✅ Strategy ranking                                  │
│ ✅ EdgeData heatmap                                  │
│ ✅ Summary metrics charts                            │
│ ✅ [Export Report] button                            │
└──────────────────────────────────────────────────────┘
```

**Navigation:**
- Default view: View 1 (Configuration)
- After batch creation: Auto-switch to View 2 (Monitoring)
- After simulations complete: Auto-switch to View 3 (Results)

---

## API Design

### Backend Endpoints (New/Modified)

#### 1. Create Event-Scenario Batch

```http
POST /api/v1/batch/create-from-event
Content-Type: application/json

{
    "event_id": "8210655",
    "scenario_ids": [
        "scenario_8210655_no_control",
        "scenario_8210655_vss",
        "scenario_8210655_tec"
    ],
    "simulation_config": {
        "duration_hours": null,  // Use scenario default
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
    "case_ids": ["case_20251115_001", "case_20251115_002", "case_20251115_003"],
    "simulation_ids": ["sim_20251115_001", "sim_20251115_002", "sim_20251115_003"],
    "status": "created"
}
```

#### 2. List Event-Scenario Batches

```http
GET /api/v1/batch/list-event-batches?status=all&limit=50

Response:
{
    "batches": [
        {
            "batch_id": "batch_event_8210655_20251115_100000",
            "event_id": "8210655",
            "event_type": "congestion",
            "created_at": "2025-11-15T10:00:00",
            "status": "completed",
            "total_simulations": 3,
            "completed_simulations": 3,
            "analysis_batch_id": "analysis_20251115_101500"
        }
    ]
}
```

#### 3. Get Event-Scenario Batch Status

```http
GET /api/v1/batch/event-batch-status/{batch_id}

Response:
{
    "batch_id": "batch_event_8210655_20251115_100000",
    "event_id": "8210655",
    "status": "running",
    "total_simulations": 3,
    "completed_simulations": 1,
    "running_simulations": 2,
    "failed_simulations": 0,
    "progress_percent": 33,
    "estimated_completion": "2025-11-15T11:30:00",
    "simulations": [
        {
            "simulation_id": "sim_20251115_001",
            "scenario_id": "scenario_8210655_no_control",
            "strategy_type": "NO_CONTROL",
            "status": "completed",
            "progress": 100
        },
        {
            "simulation_id": "sim_20251115_002",
            "scenario_id": "scenario_8210655_vss",
            "strategy_type": "VSS",
            "status": "running",
            "progress": 45
        }
    ]
}
```

#### 4. Start Event-Scenario Batch

```http
POST /api/v1/batch/start-event-batch
Content-Type: application/json

{
    "batch_id": "batch_event_8210655_20251115_100000",
    "parallel_workers": 4,
    "auto_run_analysis": true
}

Response:
{
    "batch_id": "batch_event_8210655_20251115_100000",
    "status": "running",
    "simulation_ids": ["sim_20251115_001", "sim_20251115_002", "sim_20251115_003"]
}
```

#### 5. Get Event-Scenario Batch Results

```http
GET /api/v1/batch/event-batch-results/{batch_id}

Response:
{
    "batch_id": "batch_event_8210655_20251115_100000",
    "event_id": "8210655",
    "analysis_batch_id": "analysis_20251115_101500",
    "strategy_comparison": {
        "NO_CONTROL": {
            "avg_speed": 45.2,
            "avg_trip_duration": 1200,
            "completion_rate": 96.5
        },
        "VSS": {
            "avg_speed": 52.8,
            "avg_trip_duration": 1050,
            "completion_rate": 98.2,
            "improvement_vs_baseline": {
                "avg_speed": 16.8,
                "avg_trip_duration": -12.5
            }
        },
        "TEC": {
            "avg_speed": 49.5,
            "avg_trip_duration": 1120,
            "completion_rate": 97.8,
            "improvement_vs_baseline": {
                "avg_speed": 9.5,
                "avg_trip_duration": -6.7
            }
        }
    },
    "strategy_ranking": [
        {"strategy": "VSS", "overall_improvement": 15.5, "rank": 1},
        {"strategy": "TEC", "overall_improvement": 8.2, "rank": 2}
    ]
}
```

---

## Frontend Implementation

### File Structure

**Reuse optimization patterns:**
- `frontend/scenarios/event-batch-center.html` (or rename case-simulation-center.html)
- `frontend/scenarios/js/event-batch-management.js` (new, similar to batch_simulation.js)
- Reuse: `frontend/components/simulation-monitor.js`
- Reuse: `frontend/components/analysis-results.js`

### View 1: Batch Configuration

```html
<!-- View 1: 批次配置 -->
<div id="configView" class="view-content active">
    <div class="section">
        <h3>创建事件场景批次</h3>

        <!-- Event Selector -->
        <div class="form-group">
            <label>选择事件</label>
            <select id="eventSelector" onchange="loadEventScenarios()">
                <option value="">-- 选择事件 --</option>
                <!-- Populated from scenario_index.json, grouped by event_id -->
                <option value="8210655">Event 8210655 - Flow Surge (3 scenarios)</option>
                <option value="7180720">Event 7180720 - Accident (4 scenarios)</option>
            </select>
        </div>

        <!-- Scenario Preview -->
        <div id="scenarioPreview" class="scenario-preview" style="display: none;">
            <h4>批次将包含以下场景:</h4>
            <table class="scenario-table">
                <thead>
                    <tr>
                        <th>场景ID</th>
                        <th>策略类型</th>
                        <th>事件类型</th>
                        <th>时长</th>
                    </tr>
                </thead>
                <tbody id="scenarioPreviewBody">
                    <!-- Populated dynamically -->
                </tbody>
            </table>
        </div>

        <!-- Simulation Config -->
        <div class="form-group">
            <label>仿真配置</label>
            <div class="config-grid">
                <div>
                    <label>时长 (小时)</label>
                    <input type="number" id="durationHours" placeholder="使用场景默认值" min="1" max="24">
                </div>
                <div>
                    <label>随机种子</label>
                    <input type="number" id="randomSeed" value="12345">
                </div>
            </div>
        </div>

        <!-- Create Button -->
        <div class="btn-group">
            <button class="btn btn-primary" onclick="createEventBatch()">创建批次</button>
            <button class="btn btn-secondary" onclick="clearConfig()">清除配置</button>
        </div>
    </div>
</div>
```

### View 2: Batch Monitoring

```html
<!-- View 2: 批次监控 -->
<div id="monitoringView" class="view-content">
    <!-- Batch Selector -->
    <div class="section">
        <h3>批次列表</h3>
        <div id="batchListContainer">
            <!-- Batch cards with status -->
            <div class="batch-card" data-batch-id="batch_event_8210655_20251115_100000">
                <div class="batch-header">
                    <span class="batch-id">Batch: Event 8210655</span>
                    <span class="batch-status status-completed">Completed</span>
                </div>
                <div class="batch-info">
                    <div>创建时间: 2025-11-15 10:00:00</div>
                    <div>仿真数: 3 (NO_CONTROL, VSS, TEC)</div>
                    <div>完成率: 100%</div>
                </div>
                <div class="batch-actions">
                    <button class="btn btn-primary" onclick="viewBatchMonitoring('batch_event_8210655_20251115_100000')">
                        查看监控
                    </button>
                    <button class="btn btn-success" onclick="viewBatchResults('batch_event_8210655_20251115_100000')">
                        查看结果
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Active Batch Monitoring (when batch selected) -->
    <div id="activeBatchMonitoring" style="display: none;">
        <div class="section">
            <h3>批次进度</h3>
            <div class="progress-stats">
                <div class="stat-card">
                    <div class="stat-label">总数</div>
                    <div class="stat-value" id="totalSims">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">已完成</div>
                    <div class="stat-value" id="completedSims">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">运行中</div>
                    <div class="stat-value" id="runningSims">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">失败</div>
                    <div class="stat-value" id="failedSims">0</div>
                </div>
            </div>

            <div class="progress-bar-container">
                <div class="progress-bar" id="batchProgressBar" style="width: 0%;">0%</div>
            </div>

            <div class="batch-actions">
                <button class="btn btn-primary" id="startBatchBtn" onclick="startBatch()">
                    启动批次仿真
                </button>
                <button class="btn btn-secondary" id="cancelBatchBtn" onclick="cancelBatch()" style="display: none;">
                    取消仿真
                </button>
            </div>
        </div>

        <!-- Simulation Table (reuse SimulationMonitor component) -->
        <div class="section">
            <h3>仿真详情</h3>
            <div id="simulationMonitorContainer">
                <!-- SimulationMonitor component renders here -->
            </div>
        </div>
    </div>
</div>
```

### View 3: Batch Results

```html
<!-- View 3: 批次结果 -->
<div id="resultsView" class="view-content">
    <!-- Reuse AnalysisResultsViewer component -->
    <div id="analysisResultsContainer">
        <!-- Component renders multi-scenario comparison -->
    </div>

    <div class="btn-group">
        <button class="btn btn-primary" onclick="exportReport()">导出报告</button>
        <button class="btn btn-secondary" onclick="backToMonitoring()">返回监控</button>
    </div>
</div>
```

---

## Backend Service Implementation

### New Service: EventBatchService

**File:** `api/services/event_batch_service.py`

```python
"""
Event-Scenario Batch Service

Manages event-scenario batches (one event = one batch with multiple scenarios)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

from .base_service import BaseService
from .case_service import CaseService
from .simulation_service import SimulationService
from .analysis_orchestration_service import AnalysisOrchestrationService

logger = logging.getLogger(__name__)


class EventBatchService(BaseService):
    """
    Event-Scenario Batch Service

    Treats one event as one batch (similar to optimization batches)
    """

    def __init__(self):
        super().__init__()
        self.case_service = CaseService()
        self.simulation_service = SimulationService()
        self.analysis_service = AnalysisOrchestrationService()

    async def create_event_batch(
        self,
        event_id: str,
        scenario_ids: List[str],
        simulation_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create event-scenario batch

        Args:
            event_id: Event ID
            scenario_ids: List of scenario IDs for this event
            simulation_config: Simulation configuration

        Returns:
            Batch metadata with case_ids and simulation_ids

        Process:
            1. Create batch directory
            2. Create cases for each scenario
            3. Create simulations for each case
            4. Save batch metadata
        """
        # Generate batch ID
        batch_id = f"batch_event_{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        batch_dir = self.cases_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        # Create cases for each scenario
        case_ids = []
        simulation_ids = []
        scenarios_metadata = []

        for scenario_id in scenario_ids:
            # Load scenario metadata
            scenario_meta = self._load_scenario_metadata(scenario_id)

            # Create case from scenario
            case_data = await self.case_service.create_case_from_scenario(
                scenario_id=scenario_id,
                event_id=event_id,
                **simulation_config
            )
            case_id = case_data["case_id"]
            case_ids.append(case_id)

            # Create simulation for this case
            sim_data = await self.simulation_service.create_simulation(
                case_id=case_id,
                **simulation_config
            )
            simulation_id = sim_data["simulation_id"]
            simulation_ids.append(simulation_id)

            scenarios_metadata.append({
                "scenario_id": scenario_id,
                "strategy_type": scenario_meta.get("control_strategy", {}).get("strategy_type", "NO_CONTROL"),
                "case_id": case_id,
                "simulation_id": simulation_id
            })

        # Save batch metadata
        batch_metadata = {
            "batch_id": batch_id,
            "batch_type": "event_scenario",
            "event_id": event_id,
            "event_type": scenario_meta.get("event_type", "unknown"),
            "created_at": datetime.now().isoformat(),
            "scenarios": scenarios_metadata,
            "status": "created",
            "total_simulations": len(simulation_ids),
            "completed_simulations": 0,
            "failed_simulations": 0,
            "simulation_progress": {
                "started_at": None,
                "completed_at": None,
                "estimated_completion": None
            },
            "analysis_batch_id": None
        }

        batch_metadata_file = batch_dir / "batch_metadata.json"
        with open(batch_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(batch_metadata, f, indent=2, ensure_ascii=False)

        return {
            "batch_id": batch_id,
            "event_id": event_id,
            "total_scenarios": len(scenario_ids),
            "case_ids": case_ids,
            "simulation_ids": simulation_ids,
            "status": "created"
        }

    async def list_event_batches(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List event-scenario batches

        Args:
            status: Filter by status (created|running|completed|failed)
            limit: Max number of batches to return

        Returns:
            List of batch metadata
        """
        batches = []

        # Find all batch directories
        for batch_dir in self.cases_dir.glob("batch_event_*"):
            if not batch_dir.is_dir():
                continue

            batch_metadata_file = batch_dir / "batch_metadata.json"
            if not batch_metadata_file.exists():
                continue

            with open(batch_metadata_file, 'r', encoding='utf-8') as f:
                batch_meta = json.load(f)

            # Filter by status
            if status and batch_meta.get("status") != status:
                continue

            batches.append(batch_meta)

        # Sort by created_at (newest first)
        batches.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return batches[:limit]

    async def get_event_batch_status(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Get event-scenario batch status with real-time simulation progress

        Args:
            batch_id: Batch ID

        Returns:
            Batch status with simulation details
        """
        batch_dir = self.cases_dir / batch_id
        batch_metadata_file = batch_dir / "batch_metadata.json"

        if not batch_metadata_file.exists():
            raise ValueError(f"Batch not found: {batch_id}")

        with open(batch_metadata_file, 'r', encoding='utf-8') as f:
            batch_meta = json.load(f)

        # Get real-time simulation status
        simulations = []
        completed = 0
        running = 0
        failed = 0

        for scenario in batch_meta["scenarios"]:
            sim_id = scenario["simulation_id"]
            sim_status = await self.simulation_service.get_simulation_status(sim_id)

            simulations.append({
                "simulation_id": sim_id,
                "scenario_id": scenario["scenario_id"],
                "strategy_type": scenario["strategy_type"],
                "status": sim_status["status"],
                "progress": sim_status.get("progress", 0)
            })

            if sim_status["status"] == "completed":
                completed += 1
            elif sim_status["status"] == "running":
                running += 1
            elif sim_status["status"] == "failed":
                failed += 1

        # Update batch metadata
        batch_meta["completed_simulations"] = completed
        batch_meta["failed_simulations"] = failed
        batch_meta["progress_percent"] = int((completed / batch_meta["total_simulations"]) * 100)

        # Calculate ETA
        if running > 0 and completed > 0:
            # Simple ETA calculation
            avg_sim_time = 1800  # 30 minutes per simulation (estimate)
            remaining_sims = batch_meta["total_simulations"] - completed
            eta_seconds = remaining_sims * avg_sim_time
            batch_meta["simulation_progress"]["estimated_completion"] = (
                datetime.now().timestamp() + eta_seconds
            )

        batch_meta["simulations"] = simulations

        return batch_meta
```

---

## Migration Path

### Phase 1: Create New Event Batch Service (1 day)

1. Implement `EventBatchService` (api/services/event_batch_service.py)
2. Add batch API endpoints (api/routes/batch_routes.py)
3. Add batch metadata models (api/models/requests/batch_requests.py)

### Phase 2: Simplify Frontend (1 day)

1. Rename or create `event-batch-center.html`
2. Implement 3-view structure (Config | Monitoring | Results)
3. Reuse SimulationMonitor and AnalysisResultsViewer components

### Phase 3: Integration & Testing (0.5 day)

1. Test event batch creation
2. Test batch simulation monitoring
3. Test batch results visualization

---

## Success Criteria

1. ✅ User creates event batch from scenario browser
2. ✅ Batch automatically creates all cases (NO_CONTROL, VSS, TEC, DHS)
3. ✅ User clicks batch → View monitoring page
4. ✅ Real-time progress updates
5. ✅ After completion → Auto-show results
6. ✅ Results show multi-scenario comparison and strategy ranking
7. ✅ Workflow similar to optimization batches (familiar UX)

---

**Document Status:** ✅ Design Complete
**Next Steps:** Implement EventBatchService backend
