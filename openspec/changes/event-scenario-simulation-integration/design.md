# Phase 2: Event Scenario Simulation Integration - Design Document

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Phase 2 Architecture                           │
└─────────────────────────────────────────────────────────────────────┘

USER WORKFLOW:
1. Click "Create Case from Scenario" (Phase 1 UI)
   ↓
2. Case created with source_scenario_id tracked (AD-7)
   ↓
3. Click "Create Simulation" → SimulationService.create_from_case()
   ├─ Copy case config (network, OD, TAZ)
   ├─ Generate scenario.add.xml with relative paths
   ├─ Create simulation_metadata.json with scenario lineage
   └─ Return simulation_id
   ↓
4. Click "Start Simulation" or batch "Run Analysis"
   ├─ SimulationExecutionService.batch_start_simulations()
   ├─ Real-time progress monitoring
   └─ Auto-run analyses when complete
   ↓
5. Analysis automatically runs (AnalysisOrchestrationService)
   ├─ Load simulation results
   ├─ Run 4 analyses in parallel (with AD-10 EdgeData mandatory)
   ├─ Save results with complete scenario lineage
   └─ Update analysis_index.json
   ↓
6. View Results Dashboard
   ├─ Show analysis progress in real-time
   ├─ Display heat maps, statistics, comparisons
   └─ Download reports

BACKEND SERVICES:
┌─────────────────────────────────────────────────────────────────┐
│ API Layer (api/routes/, api/services/)                          │
├─────────────────────────────────────────────────────────────────┤
│ • scenario_routes.py          ← Phase 1 (case creation)         │
│ • simulation_routes.py        ← NEW (batch execution)           │
│ • analysis_routes.py          ← EXTENDED (orchestration)        │
│ • SimulationExecutionService  ← NEW (batch executor)            │
│ • AnalysisOrchestrationService ← NEW (analysis scheduler)      │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Shared Layer (shared/)                                           │
├─────────────────────────────────────────────────────────────────┤
│ • sumo_utils.py               ← EXTENDED (relative paths)      │
│ • simulation_processor.py     ← EXTENDED (batch integration)    │
│ • analysis_tools/            ← USES (4 existing services)       │
│ • batch_result_analyzer.py    ← REUSES (aggregation)           │
└─────────────────────────────────────────────────────────────────┘

FRONTEND LAYER (frontend/)
┌─────────────────────────────────────────────────────────────────┐
│ Components (NEW)                                                  │
├─────────────────────────────────────────────────────────────────┤
│ • simulation-monitor.js       ← NEW (batch progress)            │
│ • analysis-results.js         ← NEW (visualization)             │
│ • shared-utils.js             ← REFACTORED                      │
│ • api-client.js               ← REFACTORED                      │
└─────────────────────────────────────────────────────────────────┘

DATABASE / FILE SYSTEM:
┌─────────────────────────────────────────────────────────────────┐
│ cases/case_id/                                                   │
│ ├─ metadata.json              ← source_scenario_id              │
│ ├─ config/                    ← network, OD, TAZ refs          │
│ └─ simulations/sim_id/        ← AD-7 1:1 binding               │
│    ├─ simulation.sumocfg      ← RELATIVE PATHS (AD-13)        │
│    ├─ scenario.add.xml        ← event + control XML            │
│    ├─ simulation_metadata.json ← event/control config copy     │
│    └─ sumo_logs/              ← NEW (real-time logging)        │
│                                                                  │
│ cases/case_id/analysis/batch_id/
│ ├─ analysis_metadata.json     ← source_simulation_id          │
│ ├─ edgedata/                  ← EdgeData analysis (MANDATORY) │
│ ├─ tripinfo/                  ← TripInfo analysis (OPTIONAL)  │
│ ├─ accuracy/                  ← Accuracy analysis (OPTIONAL)  │
│ └─ performance/               ← Performance analysis          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Three-Level Metadata Tracking (AD-12)

### Design Principle

**Goal**: Enable complete traceability from analysis result back to originating scenario, with strict metadata isolation.

### Level 1: Case Metadata

**Location**: `cases/case_id/metadata.json`

**Structure**:
```json
{
  "case_id": "case_20251112_120000",
  "case_name": "Morning Peak VSS Control Case",
  "created_at": "2025-11-12T12:00:00",

  "source_scenario": {
    "scenario_id": "scenario_12547_vss",
    "event_id": "12547",
    "event_type": "01_accident",
    "control_strategy_type": "VSS",
    "description": "Accident at K30, VSS control activated"
  },

  "immutable_fields": {
    "event_id": "12547",
    "event_type": "01_accident",
    "location": {"road": "G4202", "km_point": 30.5},
    "affected_edges": ["edge_1", "edge_2"],
    "control_strategy_type": "VSS"
  },

  "overridable_fields": {
    "simulation_duration_hours": 2.5,
    "random_seed": null,
    "output_config": {
      "generate_edgedata": true,
      "generate_summary": true,
      "generate_tripinfo": true,
      "generate_vehroute": false
    }
  },

  "case_config": {
    "network_file": "templates/network_files/sichuan202508v7.net.xml",
    "od_file": "data/od_data_sichuan_202507.xml",
    "taz_file": "templates/taz_files/TAZ_6.add.xml"
  }
}
```

**Responsibility**: Stores case-level configuration and scenario origin. **Never modified after creation** (except status field).

**Status Tracking**: Case status = `created` | `simulating` | `completed` | `failed`

---

### Level 2: Simulation Metadata

**Location**: `cases/case_id/simulations/sim_id/simulation_metadata.json`

**Structure**:
```json
{
  "simulation_id": "sim_20251112_120530",
  "case_id": "case_20251112_120000",
  "created_at": "2025-11-12T12:05:30",

  "source_scenario": {
    "scenario_id": "scenario_12547_vss",  ← BACKTRACK to scenario
    "event_id": "12547",
    "event_type": "01_accident"
  },

  "scenario_config": {
    "event_description": {...},           ← COPY of scenario event_description.json
    "control_strategy_config": {...}      ← COPY of scenario control_strategy_config.json
  },

  "simulation_parameters": {
    "duration_hours": 2.5,
    "start_time": "2025-11-12T12:00:00",
    "end_time": "2025-11-12T14:30:00",
    "random_seed": 42,
    "warmup_duration": 600,
    "output_config": {
      "generate_summary": true,
      "generate_tripinfo": true,
      "generate_vehroute": false,
      "generate_edgedata": true
    }
  },

  "input_files": {
    "sumocfg": "simulation.sumocfg",
    "network": "templates/network_files/sichuan202508v7.net.xml",
    "routes": "data/od_data_sichuan_202507.xml",
    "scenario_add": "scenario.add.xml"
  },

  "output_files": {
    "summary": "outputs/summary.xml",
    "tripinfo": "outputs/tripinfo.xml",
    "edgedata": "outputs/edgedata.xml",
    "vehroute": null
  },

  "execution": {
    "status": "pending" | "running" | "completed" | "failed",
    "started_at": null,
    "completed_at": null,
    "elapsed_seconds": null,
    "sumo_log": "sumo_logs/sumo_20251112_120530.log"
  }
}
```

**Responsibility**: Tracks simulation-specific configuration and execution state. Scenario config is **copied** (not referenced) to preserve immutability.

**Key Design**:
- `source_scenario` field enables backtracking to scenario
- Config files are **copies**, not references (snapshots for reproducibility)
- Never modified by analysis services

---

### Level 3: Analysis Metadata

**Location**: `cases/case_id/analysis/batch_id/analysis_metadata.json`

**Structure**:
```json
{
  "analysis_batch_id": "analysis_batch_20251112_130000",
  "case_id": "case_20251112_120000",
  "simulation_id": "sim_20251112_120530",
  "created_at": "2025-11-12T13:00:00",

  "source_scenario": {
    "scenario_id": "scenario_12547_vss",  ← BACKTRACK through simulation
    "event_id": "12547"
  },

  "analysis_config": {
    "baseline_scenario_id": "scenario_12547_none",
    "comparison_scenario_id": null,
    "analysis_types": [
      {
        "type": "edgedata",      ← MANDATORY
        "enabled": true,
        "status": "completed",
        "result_dir": "edgedata/",
        "metrics": ["avg_speed", "congestion_index", "emission"]
      },
      {
        "type": "tripinfo",      ← OPTIONAL
        "enabled": true,
        "status": "completed",
        "result_dir": "tripinfo/",
        "metrics": ["avg_trip_time", "completion_rate"]
      },
      {
        "type": "accuracy",      ← OPTIONAL
        "enabled": false,
        "status": "skipped",
        "reason": "No gantry data available"
      },
      {
        "type": "performance",   ← OPTIONAL
        "enabled": true,
        "status": "completed",
        "result_dir": "performance/",
        "metrics": ["vehicle_count", "avg_speed"]
      }
    ]
  },

  "results_summary": {
    "edgedata": {
      "num_edges_analyzed": 247,
      "avg_speed_improvement": 12.5,
      "congestion_reduction": 28.3,
      "most_congested_edges": [...]
    },
    "tripinfo": {
      "total_vehicles": 8934,
      "avg_trip_time": 245.6,
      "completion_rate": 98.7
    }
  }
}
```

**Responsibility**: Stores analysis configuration and results. **Read-only**, never modifies case or simulation metadata.

**Key Design**:
- Can backtrack to scenario through simulation_id
- Multiple analysis types tracked independently
- Results stored in separate subdirectories (edgedata/, tripinfo/, etc.)
- Analysis isolation enforced

---

## 2. SUMO Configuration Relative Paths (AD-13)

### Problem & Solution

**Problem**: Absolute paths in `.sumocfg` won't work when cases move to different machines or paths change.

**Solution**: Use relative paths computed from simulation directory.

### Implementation Strategy

**File Locations Reference**:
```
D:\projects\OD_SIM\
├─ templates/
│  ├─ network_files/sichuan202508v7.net.xml
│  └─ taz_files/TAZ_6.add.xml
├─ data/
│  └─ od_data_sichuan_202507.xml
├─ cases/
│  └─ case_id/
│     └─ simulations/
│        └─ sim_id/
│           ├─ simulation.sumocfg    ← WE ARE HERE
│           └─ scenario.add.xml
└─ output/
   └─ scenarios/
      └─ [event_type]/scenario_id/
         └─ scenario_12547_vss.add.xml
```

**Relative Paths from `simulation.sumocfg`**:
```
simulation.sumocfg → templates/network_files/...
  Path: ../../templates/network_files/sichuan202508v7.net.xml

simulation.sumocfg → data/...
  Path: ../../data/od_data_sichuan_202507.xml

simulation.sumocfg → scenario.add.xml (same dir)
  Path: scenario.add.xml
```

### Algorithm

```python
def compute_relative_path(from_file: Path, to_file: Path) -> str:
    """
    Compute relative path from from_file to to_file.

    Example:
        from_file: D:\projects\OD_SIM\cases\case_id\simulations\sim_id\simulation.sumocfg
        to_file: D:\projects\OD_SIM\templates\network_files\xxx.net.xml
        result: ../../templates/network_files/xxx.net.xml
    """
    from_dir = Path(from_file).parent
    rel_path = Path(to_file).relative_to(from_dir)
    return str(rel_path).replace('\\', '/')  # Unix-style paths for SUMO
```

### Generated SUMOCFG Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">

  <input>
    <!-- Relative paths from simulation.sumocfg location -->
    <net-file value="../../templates/network_files/sichuan202508v7.net.xml"/>
    <route-files value="../../data/od_data_sichuan_202507.xml"/>
    <additional-files value="scenario.add.xml,../../templates/taz_files/TAZ_6.add.xml"/>
  </input>

  <time>
    <begin value="0"/>
    <end value="9000"/>  <!-- 2.5 hours in seconds -->
  </time>

  <output>
    <summary-output value="outputs/summary.xml"/>
    <tripinfo-output value="outputs/tripinfo.xml"/>
    <edgedata-output value="outputs/edgedata.xml"/>
  </output>

  <processing>
    <time-to-teleport value="300"/>
    <max-depart-delay value="1"/>
  </processing>

</configuration>
```

### Validation at Runtime

```python
def validate_sumocfg_paths(sumocfg_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that all relative paths in sumocfg resolve to existing files.

    Returns:
        (is_valid, error_messages)
    """
    sumocfg_dir = sumocfg_path.parent
    errors = []

    # Parse XML, extract all file references
    tree = ET.parse(sumocfg_path)
    for value_elem in tree.findall('.//*/[@value]'):
        file_path = value_elem.get('value')
        abs_path = (sumocfg_dir / file_path).resolve()

        if not abs_path.exists():
            errors.append(f"File not found: {file_path} → {abs_path}")

    return len(errors) == 0, errors
```

---

## 3. Analysis Orchestration Service

### Class Design

**Location**: `api/services/analysis_orchestration_service.py`

**Key Methods**:

```python
class AnalysisOrchestrationService:
    """
    Orchestrates running multiple analysis types across multiple simulations.

    Pattern:
    1. User completes simulation(s)
    2. Call create_analysis_batch() with simulation IDs
    3. Service queues analysis tasks (N sims × M analysis types)
    4. Executor runs tasks in parallel (configurable workers)
    5. Results stored with complete metadata lineage
    6. get_analysis_progress() provides real-time monitoring
    """

    async def create_analysis_batch(
        self,
        simulation_ids: List[str],
        case_id: str,
        baseline_scenario_id: str,
        comparison_scenario_id: Optional[str] = None,
        analysis_focus: List[str] = ["edgedata", "tripinfo"],
        parallel_workers: int = 4
    ) -> AnalysisBatchResponse:
        """
        Create and queue analysis batch for multiple simulations.

        Args:
            simulation_ids: ["sim_123", "sim_456", ...]
            baseline_scenario_id: "scenario_12547_none" (for comparison)
            analysis_focus: MANDATORY edgedata + OPTIONAL others
            parallel_workers: 2-8 (concurrent analysis tasks)

        Returns:
            AnalysisBatchResponse with batch_id for tracking

        Process:
            1. Validate all simulation_ids exist and are completed
            2. Create analysis_metadata.json for batch
            3. Queue analysis tasks: Sim1-EdgeData, Sim1-TripInfo, Sim2-EdgeData, ...
            4. Return batch_id for progress tracking
            5. Start executor in background
        """

    async def get_analysis_progress(
        self,
        batch_id: str
    ) -> AnalysisBatchProgressResponse:
        """
        Real-time progress tracking (updated every 10 seconds).

        Returns:
        {
            "batch_id": "analysis_batch_20251112_130000",
            "total_tasks": 160,        # 40 sims × 4 analysis types
            "completed": 52,
            "failed": 1,
            "in_progress": 3,
            "queued": 104,
            "estimated_completion": "2025-11-12T16:45:00",
            "current_tasks": [
                {
                    "simulation_id": "sim_123",
                    "analysis_type": "edgedata",
                    "progress": 65,
                    "status": "running",
                    "message": "Processing 2847 edges..."
                },
                {
                    "simulation_id": "sim_123",
                    "analysis_type": "tripinfo",
                    "progress": 0,
                    "status": "queued"
                }
            ]
        }
        """

    async def cancel_analysis_batch(self, batch_id: str) -> CancelResponse:
        """Stop analysis batch gracefully (allows in-flight tasks to complete)."""
```

### Task Queue Design

**Storage**: `cases/case_id/analysis/batch_id/analysis_tasks_index.json`

```json
{
  "batch_id": "analysis_batch_20251112_130000",
  "created_at": "2025-11-12T13:00:00",
  "status": "running",

  "config": {
    "simulation_ids": ["sim_123", "sim_456"],
    "baseline_scenario_id": "scenario_12547_none",
    "analysis_focus": ["edgedata", "tripinfo"]
  },

  "tasks": [
    {
      "task_id": "task_001",
      "simulation_id": "sim_123",
      "analysis_type": "edgedata",
      "status": "completed",
      "started_at": "2025-11-12T13:05:00",
      "completed_at": "2025-11-12T13:35:00",
      "elapsed_seconds": 1800
    },
    {
      "task_id": "task_002",
      "simulation_id": "sim_123",
      "analysis_type": "tripinfo",
      "status": "running",
      "started_at": "2025-11-12T13:35:30",
      "progress_percent": 65
    },
    {
      "task_id": "task_003",
      "simulation_id": "sim_456",
      "analysis_type": "edgedata",
      "status": "queued"
    }
  ]
}
```

### Executor Pattern

**Reuse**: `BatchOptimizationService` worker pool pattern (already proven in production)

```python
class AnalysisTaskExecutor:
    """
    Background executor with configurable worker pool (2-8 workers).

    Pattern:
        1. Load analysis_tasks_index.json
        2. Get next queued task
        3. Call appropriate analysis service (EdgeData, TripInfo, etc.)
        4. Update task status in index (running → completed/failed)
        5. Move to next task
        6. Retry failed tasks (max 3 attempts)
    """

    async def execute(self, batch_id: str, parallel_workers: int = 4):
        """Execute queued tasks with concurrency control."""

        # Create worker pool
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=parallel_workers)

        while has_pending_tasks(batch_id):
            # Get next task
            task = get_next_queued_task(batch_id)
            if not task:
                break

            # Submit to executor
            future = executor.submit(execute_task, task)

            # Register callback to update status
            future.add_done_callback(lambda f: update_task_status(task, f))

        executor.shutdown(wait=True)
```

---

## 4. Simulation Execution Service (Batch)

### Extension Design

**Location**: Extend `api/services/simulation_service.py`

**New Methods**:

```python
class SimulationExecutionService:

    async def batch_start_simulations(
        self,
        simulation_ids: List[str],
        parallel_workers: int = 4,
        auto_run_analysis: bool = True
    ) -> BatchSimulationResponse:
        """
        Start multiple simulations in parallel.

        Args:
            simulation_ids: ["sim_123", "sim_456", ...]
            parallel_workers: 2-8 concurrent simulations
            auto_run_analysis: Auto-run analyses when all sims complete

        Returns:
            BatchSimulationResponse with batch_id for tracking

        Process:
            1. Validate all simulation_ids exist (status="pending")
            2. Create batch_metadata.json
            3. Queue simulation tasks
            4. Start executor with worker pool
            5. Return batch_id
        """

    async def get_batch_execution_status(
        self,
        batch_id: str
    ) -> BatchExecutionStatusResponse:
        """
        Real-time status with per-simulation details.

        Returns:
        {
            "batch_id": "batch_exec_20251112_120000",
            "total": 10,
            "completed": 4,
            "failed": 1,
            "in_progress": 2,
            "queued": 3,
            "estimated_completion": "2025-11-12T18:00:00",
            "simulations": [
                {
                    "simulation_id": "sim_123",
                    "status": "running",
                    "progress_percent": 45,
                    "vehicles_completed": 5234,
                    "elapsed_time": "00:45:30",
                    "eta": "01:05:15"
                },
                {
                    "simulation_id": "sim_456",
                    "status": "completed",
                    "elapsed_time": "01:32:45",
                    "result_files": {
                        "summary": "outputs/summary.xml",
                        "tripinfo": "outputs/tripinfo.xml",
                        "edgedata": "outputs/edgedata.xml"
                    }
                }
            ]
        }
        """

    async def validate_simulation_results(
        self,
        simulation_id: str
    ) -> ValidationResponse:
        """
        Verify all expected output files are present and valid.

        Checks:
            - summary.xml exists and valid XML
            - tripinfo.xml (if enabled) valid
            - edgedata.xml (if enabled) valid and contains edge data
            - Log files captured
        """
```

### Result Validation Logic

```python
async def validate_simulation_results(simulation_id: str) -> Tuple[bool, List[str]]:
    """Validate simulation output files."""

    sim_dir = get_simulation_dir(simulation_id)
    output_dir = sim_dir / "outputs"
    errors = []

    # Always check: summary.xml
    summary_file = output_dir / "summary.xml"
    if not summary_file.exists():
        errors.append("Missing: summary.xml")
    else:
        try:
            ET.parse(summary_file)
        except ET.ParseError as e:
            errors.append(f"Invalid XML in summary.xml: {e}")

    # Check output config to see what files should exist
    metadata = load_simulation_metadata(simulation_id)

    if metadata['simulation_parameters']['output_config'].get('generate_tripinfo'):
        tripinfo_file = output_dir / "tripinfo.xml"
        if not tripinfo_file.exists():
            errors.append("Missing: tripinfo.xml (enabled in config)")

    if metadata['simulation_parameters']['output_config'].get('generate_edgedata'):
        edgedata_file = output_dir / "edgedata.xml"
        if not edgedata_file.exists():
            errors.append("Missing: edgedata.xml (enabled in config)")
        else:
            # Check file has actual edge data
            root = ET.parse(edgedata_file).getroot()
            if len(root.findall('edge')) == 0:
                errors.append("edgedata.xml is empty (no <edge> elements)")

    return len(errors) == 0, errors
```

---

## 5. Frontend Component Refactoring

### Current State
- 74 KB `script.js` with multiple responsibilities
- Mixed concerns: DOM manipulation, API calls, data processing

### Target State
- Component-based architecture
- Reusable modules
- Clear separation of concerns

### File Structure

```
frontend/
├─ components/
│  ├─ shared-utils.js
│  │  ├─ export { formatDate, formatTime, parseQuery, ... }
│  │  └─ Common utilities reused across pages
│  ├─ api-client.js
│  │  ├─ export class APIClient { ... }
│  │  └─ Centralized API calls with error handling
│  ├─ simulation-monitor.js
│  │  ├─ SimulationMonitor class (real-time progress)
│  │  └─ Render simulation list with status indicators
│  └─ analysis-results.js
│     ├─ AnalysisResults class (visualization)
│     └─ Display heat maps, statistics, comparisons
├─ css/
│  └─ styles.css              (Centralized styles)
├─ pages/
│  ├─ scenario-browser.html   (Existing from Phase 1)
│  ├─ case-details.html       (New)
│  ├─ simulations.html        (New)
│  └─ analysis.html           (New)
└─ lib/
   └─ bootstrap-icons/        (Icon library)
```

### Key Components Design

#### shared-utils.js

```javascript
/**
 * Shared utility functions used across components.
 */

export function formatDate(dateString) {
  return new Date(dateString).toLocaleString('zh-CN');
}

export function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

export function getStatusBadgeClass(status) {
  const mapping = {
    'pending': 'badge-secondary',
    'running': 'badge-primary',
    'completed': 'badge-success',
    'failed': 'badge-danger'
  };
  return mapping[status] || 'badge-secondary';
}

export async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

#### api-client.js

```javascript
/**
 * Centralized API client with error handling and request retry.
 */

export class APIClient {
  constructor(baseUrl = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getSimulationBatchStatus(batchId) {
    return this.request(`/simulation/batch-status/${batchId}`);
  }

  async getAnalysisProgress(batchId) {
    return this.request(`/analysis/batch-progress/${batchId}`);
  }
}
```

#### simulation-monitor.js

```javascript
/**
 * Real-time simulation execution monitor.
 */

export class SimulationMonitor {
  constructor(containerId, apiClient) {
    this.container = document.getElementById(containerId);
    this.apiClient = apiClient;
    this.updateInterval = 5000;  // Poll every 5 seconds
  }

  async startMonitoring(batchId) {
    this.batchId = batchId;

    while (true) {
      try {
        const status = await this.apiClient.getSimulationBatchStatus(batchId);
        this.render(status);

        // Stop if all done
        if (status.queued === 0 && status.in_progress === 0) {
          break;
        }

        await delay(this.updateInterval);
      } catch (error) {
        console.error('Failed to fetch status:', error);
        await delay(this.updateInterval);
      }
    }
  }

  render(status) {
    // Update progress bar
    const progressPercent = (status.completed / status.total) * 100;
    this.container.querySelector('.progress-bar').style.width = `${progressPercent}%`;

    // Update simulation list
    const listHtml = status.simulations.map(sim => `
      <div class="simulation-row">
        <div class="col-md-2">${sim.simulation_id}</div>
        <div class="col-md-2">
          <span class="badge ${getStatusBadgeClass(sim.status)}">
            ${sim.status}
          </span>
        </div>
        <div class="col-md-3">
          <div class="progress">
            <div class="progress-bar" style="width: ${sim.progress_percent}%"></div>
          </div>
        </div>
        <div class="col-md-2">${formatTime(sim.elapsed_time)}</div>
        <div class="col-md-3">
          <button class="btn btn-sm btn-outline-primary">View Logs</button>
        </div>
      </div>
    `).join('');

    this.container.innerHTML = listHtml;
  }
}
```

---

## 6. Data Models (Request/Response)

### Batch Simulation Models

**Location**: `api/models/requests/batch_simulation_request.py` and `api/models/responses/batch_simulation_response.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BatchSimulationStartRequest(BaseModel):
    """Request to start multiple simulations."""

    simulation_ids: List[str] = Field(
        ...,
        description="List of simulation IDs to start",
        min_items=1,
        max_items=100
    )

    parallel_workers: int = Field(
        default=4,
        description="Number of concurrent simulations",
        ge=2,
        le=8
    )

    auto_run_analysis: bool = Field(
        default=True,
        description="Automatically run analyses when all simulations complete"
    )


class SimulationProgressInfo(BaseModel):
    """Per-simulation progress information."""

    simulation_id: str
    status: str  # pending, running, completed, failed
    progress_percent: int
    vehicles_completed: Optional[int] = None
    elapsed_time: Optional[str] = None
    eta: Optional[str] = None
    result_files: Optional[dict] = None
    error_message: Optional[str] = None


class BatchSimulationResponse(BaseModel):
    """Response from batch start request."""

    batch_id: str
    simulation_ids: List[str]
    total: int
    created_at: datetime


class BatchExecutionStatusResponse(BaseModel):
    """Real-time status of batch execution."""

    batch_id: str
    total: int
    completed: int
    failed: int
    in_progress: int
    queued: int
    estimated_completion: Optional[datetime] = None
    simulations: List[SimulationProgressInfo]
```

### Analysis Orchestration Models

```python
class AnalysisBatchRequest(BaseModel):
    """Request to run analyses on simulations."""

    simulation_ids: List[str] = Field(..., description="Simulation IDs to analyze")
    case_id: str
    baseline_scenario_id: str
    comparison_scenario_id: Optional[str] = None
    analysis_focus: List[str] = Field(
        default=["edgedata", "tripinfo"],
        description="Analysis types (edgedata mandatory)"
    )
    parallel_workers: int = Field(default=4, ge=2, le=8)


class AnalysisTaskInfo(BaseModel):
    """Information about a single analysis task."""

    task_id: str
    simulation_id: str
    analysis_type: str
    status: str  # queued, running, completed, failed
    progress_percent: int = 0
    message: Optional[str] = None
    elapsed_seconds: Optional[int] = None


class AnalysisBatchProgressResponse(BaseModel):
    """Real-time progress of analysis batch."""

    batch_id: str
    total_tasks: int
    completed: int
    failed: int
    in_progress: int
    queued: int
    estimated_completion: Optional[datetime] = None
    current_tasks: List[AnalysisTaskInfo]
```

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Create `AnalysisOrchestrationService` with task queue
- [ ] Add batch execution routes
- [ ] Implement progress tracking infrastructure
- [ ] Unit tests for orchestration logic
- [ ] Metadata tracking validation tests

### Week 2: Execution
- [ ] Extend `SimulationExecutionService` with batch methods
- [ ] Implement relative path generation (AD-13)
- [ ] SUMO configuration validation
- [ ] Frontend component refactoring
- [ ] Integration tests

### Week 3: Results & UX
- [ ] Analysis result aggregation
- [ ] Analysis results dashboard UI
- [ ] Heat map visualization (basic)
- [ ] E2E testing

### Week 4: Polish
- [ ] Error recovery and retry logic
- [ ] Performance optimization
- [ ] Documentation
- [ ] Production readiness checklist

---

## Testing Strategy

### Unit Tests (Grouped by Component)

**Metadata Tracking**:
- Test 3-level metadata structure and linkages
- Test metadata isolation (analyses don't modify case/sim)

**SUMO Path Generation**:
- Test relative path computation for different directory structures
- Test path validation at runtime

**Analysis Orchestration**:
- Test task queue creation and ordering
- Test concurrent task execution
- Test progress tracking

**Batch Execution**:
- Test simulation queuing and ordering
- Test parallel execution with mocked SUMO
- Test result validation

### Integration Tests

**End-to-End Workflows**:
1. Create case from scenario → Create simulation → Run simulation → Run analysis
2. Batch scenario creation → Batch simulation → Batch analysis
3. Error handling: Failed simulation → Retry → Analysis skips

### E2E Tests (Playwright)

**User Workflows**:
1. Create case from scenario → see simulation created
2. Click "Start Simulation" → see progress UI update
3. Simulation completes → analyses start automatically
4. View analysis results → see visualizations

---

## Performance Considerations

1. **Parallel Execution**: Limit to 4-8 workers (default 4)
2. **Progress Updates**: 10-second interval (not 1-second) to reduce DB queries
3. **Log Files**: Store incrementally, compress after completion
4. **Analysis Aggregation**: Cache intermediate results to avoid recomputation
5. **Frontend Updates**: Use 5-second polling (not 1-second) for real-time UI

---

## Error Handling Strategy

1. **Transient Errors** (Network, temp file lock):
   - Automatic retry (max 3 attempts)
   - Exponential backoff (1s → 2s → 4s)

2. **Validation Errors** (Missing file, invalid XML):
   - Fail immediately with descriptive message
   - No retry

3. **User Cancellation**:
   - Mark batch as "cancelled"
   - Allow in-flight tasks to complete gracefully
   - Stop queuing new tasks

---

**Design Complete. Ready for specification creation.**
