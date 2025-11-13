# Phase 2: Event Scenario Simulation Integration - Design Document

## Design Principles (Non-Breaking Integration)

### PRINCIPLE-INTEGRATION-001: Non-Breaking Extension Principle
- **新服务不修改现有服务接口** - New services MUST NOT modify existing service interfaces
- **新元数据字段可选** - New metadata fields MUST be optional for backward compatibility
- **新API使用独立端点** - New APIs MUST use separate endpoints (not override existing)

### PRINCIPLE-INTEGRATION-002: Workflow Isolation Principle
- **事件场景工作流代码隔离** - Event-scenario workflow code isolated in dedicated services
- **共享基础设施通过适配器访问** - Shared infrastructure (BatchSimulationScheduler) accessed via adapters
- **现有OD/控制方案工作流继续正常工作** - Existing OD/Control Plan workflows continue working unchanged

### PRINCIPLE-INTEGRATION-003: Gradual Migration Principle
- **新旧元数据Schema并存** - Old and new metadata schemas coexist
- **服务检测Schema版本并适配** - Services detect schema version and adapt behavior
- **提供迁移工具但非强制** - Migration tools provided but not mandatory

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Phase 2 Architecture (Non-Breaking Extension)              │
└─────────────────────────────────────────────────────────────────────────────┘

EXISTING WORKFLOWS (UNCHANGED):
┌─────────────────────────────────────────────────────────────────┐
│ Workflow 1: OD提取仿真 (OD Extraction Simulation)                │
│   CaseService.create_case() → SimulationService.prepare/start() │
│   ✅ 不受影响 - API和元数据结构保持不变                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Workflow 2: 管控方案优化 (Control Plan Optimization)             │
│   BatchOptimizationService → BatchSimulationScheduler           │
│   ✅ 不受影响 - 共享基础设施通过适配器复用                       │
└─────────────────────────────────────────────────────────────────┘

NEW WORKFLOW (PHASE 2):
┌─────────────────────────────────────────────────────────────────┐
│ Workflow 3: 事件场景仿真分析 (Event Scenario Sim + Analysis)     │
│   ScenarioService → SimulationOrchestrator → AnalysisAdapter    │
│   ✅ 新增 - 不影响现有工作流                                     │
└─────────────────────────────────────────────────────────────────┘

USER WORKFLOW (Event Scenario):
1. Click "Create Case from Scenario" (Phase 1 UI)
   ↓
2. POST /api/v1/case/create-from-scenario (NEW endpoint)
   ├─ CaseService.create_case_from_scenario() (NEW method)
   ├─ Case created with source_scenario (metadata_version: "2.0")
   └─ Backward compatible: v1.0 cases continue working
   ↓
3. Click "Batch Start Simulations"
   ├─ SimulationOrchestrator.batch_start() (NEW - orchestration layer)
   ├─ Detects simulation source (event-scenario vs OD vs control-plan)
   ├─ Delegates to appropriate service:
   │  • Event-scenario → Uses BatchSimulationScheduler (reused)
   │  • OD extraction → Existing SimulationService (unchanged)
   │  • Control plan → Existing BatchOptimizationService (unchanged)
   └─ Real-time progress monitoring
   ↓
4. Analysis automatically runs (AnalysisOrchestrationService)
   ├─ Adapter layer converts event-scenario structure to batch format
   ├─ Reuses: SummaryAnalyzer + EdgeDataAnalyzer (shared layer, unchanged)
   ├─ Does NOT use: OD analysis services (accuracy/mechanism/performance/edgedata)
   ├─ Save results with scenario lineage
   └─ Update analysis_index.json
   ↓
5. View Results Dashboard (NEW UI, does not modify existing pages)
   ├─ simulation-monitor.js (generic, supports all sim types)
   ├─ Display heat maps, statistics, comparisons
   └─ Download reports

BACKEND SERVICES (Clarified Roles):
┌──────────────────────────────────────────────────────────────────────┐
│ API Layer (api/routes/, api/services/)                               │
├──────────────────────────────────────────────────────────────────────┤
│ EXISTING (UNCHANGED):                                                 │
│ • CaseService                  ← Extended with new method            │
│ • SimulationService            ← Unchanged (OD extraction flow)      │
│ • BatchOptimizationService     ← Unchanged (control plan flow)       │
│                                                                       │
│ NEW (PHASE 2):                                                        │
│ • SimulationOrchestrator       ← NEW orchestration layer (Q1-C)      │
│ • AnalysisOrchestrationService ← NEW adapter for batch analysis      │
└──────────────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────────────┐
│ Shared Layer (shared/)                                                │
├──────────────────────────────────────────────────────────────────────┤
│ REUSED (UNCHANGED):                                                   │
│ • BatchSimulationScheduler     ← Reused via adapter (Q2)             │
│ • SummaryAnalyzer              ← Reused for event-scenario analysis  │
│ • EdgeDataAnalyzer             ← Reused for event-scenario analysis  │
│                                                                       │
│ NOT USED:                                                             │
│ • accuracy_service (OD-specific) ← Not reused (Q8)                   │
│ • mechanism_service (OD-specific) ← Not reused (Q8)                  │
│ • performance_service (OD-specific) ← Not reused (Q8)                │
│ • edgedata_service (OD-specific) ← Not reused (Q8)                   │
│                                                                       │
│ EXTENDED:                                                             │
│ • sumo_utils.py                ← Add relative path generation        │
└──────────────────────────────────────────────────────────────────────┘

FRONTEND LAYER (frontend/) - Incremental Refactoring (Q13):
┌──────────────────────────────────────────────────────────────────────┐
│ EXISTING (UNCHANGED):                                                 │
│ • script.js (only used by index.html) ← Not modified                 │
│ • frontend/control/* ← Control plan UI, unchanged                    │
│ • frontend/scenarios/scenario_browser.html ← Phase 1, unchanged      │
│                                                                       │
│ NEW (PHASE 2):                                                        │
│ • components/simulation-monitor.js ← Generic, all sim types (Q14)   │
│ • components/analysis-results.js   ← Event-scenario results          │
│ • components/shared-utils.js       ← Extracted utilities             │
│ • components/api-client.js         ← Centralized API calls           │
└──────────────────────────────────────────────────────────────────────┘

METADATA COMPATIBILITY (Q3, Q6, Q7):
┌──────────────────────────────────────────────────────────────────────┐
│ cases/case_id/metadata.json                                           │
├──────────────────────────────────────────────────────────────────────┤
│ VERSION 1.0 (Existing OD cases):                                      │
│ {                                                                     │
│   "case_id": "...",                                                   │
│   "created_at": "...",                                                │
│   // NO source_scenario field                                        │
│ }                                                                     │
│                                                                       │
│ VERSION 2.0 (Event-scenario cases):                                  │
│ {                                                                     │
│   "metadata_version": "2.0",  ← NEW version field (Q5)               │
│   "case_id": "...",                                                   │
│   "source_scenario": {...},   ← NEW optional field                   │
│   "immutable_fields": {...},                                          │
│   "overridable_fields": {...}                                         │
│ }                                                                     │
│                                                                       │
│ ✅ Backward Compatible: Services check metadata_version              │
└──────────────────────────────────────────────────────────────────────┘


---

## 0. Scenario Directory Structure (CRITICAL - Actual Implementation)

### IMPORTANT: Phase 1 Output Structure (output/scenarios)

This section documents the ACTUAL directory structure created by Phase 1 scenario generation. This is critical for understanding how scenario validation works.

**Actual Directory Tree**:

```
output/scenarios/
├── 01_accident/                              ← Event type directory (numeric code)
│   ├── scenario_10754_no_control/           ← Scenario directory (lowercase strategy)
│   │   ├── event_description.json            ✅ PRESENT
│   │   ├── traffic_input_config.json         ✅ PRESENT
│   │   ├── control_strategy_config.json      ✅ PRESENT
│   │   └── scenario_accident_event_10754.add.xml  ✅ PRESENT (not sumocfg!)
│   ├── scenario_10754_vss/
│   │   └── (same 4 files)
│   ├── scenario_10754_tec/
│   │   └── (same 4 files)
│   ├── scenario_10762_no_control/
│   │   └── (same 4 files)
│   └── ... (40+ more scenarios)
│
├── 02_congestion/                            ← Another event type
│   ├── scenario_20001_no_control/
│   └── ... (30+ scenarios)
│
├── 03_road_control/
├── 05_breakdown/
├── 06_weather/
│
└── scenario_index.json                       ← Master index file
```

### CRITICAL FINDINGS: Data Format Mismatches

**Issue 1: Event Type Encoding Mismatch**
- JSON (`scenario_index.json`): `"event_type": "交通事故"` (Chinese name)
- Filesystem: `01_accident/` (Numeric code + English name)
- **Impact**: Cannot construct path from `event_type` + `strategy` parameters

**Issue 2: Strategy Case Mismatch**
- JSON: `"strategy": "NO_CONTROL"` (Uppercase)
- Filesystem: `scenario_10754_no_control/` (Lowercase)
- **Impact**: Case-sensitive path lookups will fail on Windows/Linux

**Issue 3: SUMO Config Missing**
- Expected by original validation: `simulation.sumocfg`
- Actually present: `scenario_accident_event_10754.add.xml` (SUMO additional file, not config)
- **Impact**: Validation logic must NOT require sumocfg (it's generated at simulation time, not stored)

### Solution: Plan B - Robust Scenario Lookup

**Validation Strategy** (`scripts/initialize_scenario_library.py:validate_event_scenario()`):

1. **Ignore encoding differences**: Don't construct path from parameters
2. **Search directly for scenario_id**: scenario_id already contains all info
3. **Flexible directory scan**: Search all event_type subdirectories
4. **Only validate actual files**: event_description.json, traffic_input_config.json, control_strategy_config.json

```python
# ✅ CORRECT: Search for scenario_id across all event_type directories
def validate_event_scenario(self, event_type: str, strategy: str, scenario_id: str) -> bool:
    scenario_dir = None

    # Search all event_type directories
    if self.scenarios_root.exists():
        for event_type_dir in self.scenarios_root.iterdir():
            if event_type_dir.is_dir():
                potential = event_type_dir / scenario_id
                if potential.exists():
                    scenario_dir = potential
                    break

    # Validate ACTUAL files, not assumed files
    required_files = [
        "event_description.json",
        "traffic_input_config.json",
        "control_strategy_config.json"
        # NOTE: NOT including simulation.sumocfg
    ]

    return all((scenario_dir / f).exists() for f in required_files)
```

### Implications for Other Components

**Case Creation** (`api/services/case_service.py`):
- Receives `scenario_id` from frontend/API
- Passes to validation (which now works correctly)
- Creates case metadata with source_scenario tracking

**Frontend** (`frontend/scenarios/scenario_browser.js`):
- Uses `scenario_id` from scenario_index.json for all operations
- Event type and strategy are informational only (not for path construction)
- Direct case creation now works because validation is robust

**Simulation Setup**:
- SUMO config is generated dynamically at simulation time
- Scenario `.add.xml` is MERGED into SUMO config (not used as primary config)
- Never stored in scenario directory (generated in simulation output)

---

## 1. Three-Level Metadata Tracking (AD-12)

### Design Principle

**Goal**: Enable complete traceability from analysis result back to originating scenario, with strict metadata isolation.

### Level 1: Case Metadata

**Location**: `cases/case_id/metadata.json`

**Backward Compatibility Strategy** (Q3, Q5, Q7):
- Version 1.0 (existing OD cases): No `metadata_version` field, no `source_scenario` field
- Version 2.0 (event-scenario cases): Has `metadata_version: "2.0"`, has `source_scenario` field
- Services MUST check version and handle both schemas

**Structure (Version 2.0 - Event Scenario Cases)**:
```json
{
  "metadata_version": "2.0",
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

**Structure (Version 1.0 - OD Extraction Cases - Unchanged)**:
```json
{
  "case_id": "case_20251110_100000",
  "case_name": "OD Extraction Case",
  "created_at": "2025-11-10T10:00:00",
  "status": "created",
  "case_config": {
    "network_file": "templates/network_files/sichuan202508v7.net.xml",
    "od_file": "data/od_data_sichuan_202507.xml",
    "taz_file": "templates/taz_files/TAZ_6.add.xml"
  }
  // NO metadata_version field
  // NO source_scenario field
}
```

**Responsibility**: Stores case-level configuration and scenario origin. **Never modified after creation** (except status field).

**Status Tracking**: Case status = `created` | `simulating` | `completed` | `failed`

**Version Detection**:
```python
def detect_case_version(metadata: Dict[str, Any]) -> str:
    """Detect case metadata version for backward compatibility."""
    if "metadata_version" in metadata:
        return metadata["metadata_version"]
    return "1.0"  # Default for existing cases
```

---

### Level 2: Simulation Metadata

**Location**: `cases/case_id/simulations/sim_id/simulation_metadata.json`

**Backward Compatibility Strategy** (Q6):
- Version 1.0 (existing simulations): No `source_scenario` field
- Version 2.0 (event-scenario simulations): Has `source_scenario` field
- All new fields are OPTIONAL - old simulations will NOT fail

**Structure (Version 2.0 - Event Scenario Simulations)**:
```json
{
  "metadata_version": "2.0",
  "simulation_id": "sim_20251112_120530",
  "case_id": "case_20251112_120000",
  "created_at": "2025-11-12T12:05:30",

  "source_scenario": {
    "scenario_id": "scenario_12547_vss",  ← BACKTRACK to scenario (OPTIONAL)
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
    "network": "../../templates/network_files/sichuan202508v7.net.xml",
    "routes": "../../data/od_data_sichuan_202507.xml",
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

**Structure (Version 1.0 - OD Extraction Simulations - Unchanged)**:
```json
{
  "simulation_id": "sim_20251110_100530",
  "case_id": "case_20251110_100000",
  "config_file": "simulation.sumocfg",
  "status": "pending",
  "simulation_type": "microscopic"
  // NO metadata_version field
  // NO source_scenario field
  // NO scenario_config field
}
```

**Responsibility**: Tracks simulation-specific configuration and execution state. Scenario config is **copied** (not referenced) to preserve immutability.

**Key Design**:
- `source_scenario` field enables backtracking to scenario (OPTIONAL for backward compatibility)
- Config files are **copies**, not references (snapshots for reproducibility)
- Never modified by analysis services
- Services check `metadata_version` to handle both schemas

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

## 2. SUMO Configuration Relative Paths (AD-13 - Q12 Decision)

### Problem & Solution

**Problem**: Absolute paths in `.sumocfg` won't work when cases move to different machines or paths change.

**Solution (Q12)**: Unified relative path strategy
- **Metadata**: Store paths as relative to project root
- **sumocfg**: Store paths as relative to sumocfg location
- **Authority**: Metadata is source of truth, sumocfg generated from metadata

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

## 3. Simulation Orchestration Service (NEW - Q1 Decision: Option C)

### Class Design

**Location**: `api/services/simulation_orchestrator.py`

**Purpose**: Orchestration layer that detects simulation source and delegates to appropriate services

**Key Methods**:

```python
class SimulationOrchestrator:
    """
    Orchestrates batch simulation execution across different simulation sources.

    Decision Q1-C: Creates orchestration layer, detects simulation source, and delegates.

    Delegates to:
    - Event-scenario simulations → BatchSimulationScheduler (reused)
    - OD extraction simulations → SimulationService (existing, unchanged)
    - Control plan simulations → BatchOptimizationService (existing, unchanged)
    """

    def __init__(self):
        self.simulation_service = SimulationService()
        self.batch_optimization_service = BatchOptimizationService()
        # Reuse existing scheduler (Q2)
        self.batch_scheduler = BatchSimulationScheduler(
            base_dir="cases",
            completion_callback=self._on_batch_completed
        )

    async def batch_start_simulations(
        self,
        simulation_ids: List[str],
        parallel_workers: int = 4,
        auto_run_analysis: bool = True
    ) -> BatchExecutionResponse:
        """
        Start multiple simulations with automatic source detection.

        Process:
        1. Load metadata for first simulation
        2. Detect source: check metadata_version and source_scenario field
        3. Delegate to appropriate service
        4. Return unified response
        """
        # Detect simulation source
        sim_source = self._detect_simulation_source(simulation_ids[0])

        if sim_source == "event-scenario":
            # NEW: Event-scenario batch execution
            return await self._batch_start_event_scenarios(
                simulation_ids, parallel_workers, auto_run_analysis
            )
        elif sim_source == "control-plan":
            # EXISTING: Delegate to BatchOptimizationService (unchanged)
            return await self.batch_optimization_service.start_batch_service(...)
        else:
            # EXISTING: OD extraction - sequential execution
            return await self._batch_start_od_simulations(simulation_ids)

    def _detect_simulation_source(self, simulation_id: str) -> str:
        """
        Detect simulation source from metadata (Q3: Backward compatibility).

        Returns:
            "event-scenario" | "control-plan" | "od-extraction"
        """
        metadata = self._load_simulation_metadata(simulation_id)

        # Check metadata version
        version = metadata.get("metadata_version", "1.0")

        if version == "2.0" and "source_scenario" in metadata:
            return "event-scenario"
        elif "plan_id" in metadata or "control_plan" in metadata:
            return "control-plan"
        else:
            return "od-extraction"

    async def _batch_start_event_scenarios(
        self,
        simulation_ids: List[str],
        parallel_workers: int,
        auto_run_analysis: bool
    ) -> BatchExecutionResponse:
        """
        Start event-scenario simulations using BatchSimulationScheduler (Q2: Reuse).
        """
        # Convert event-scenario structure to batch format
        batch_config = self._convert_to_batch_format(simulation_ids)

        # Reuse existing BatchSimulationScheduler
        batch_id = await self.batch_scheduler.start_batch(
            batch_config,
            max_workers=parallel_workers
        )

        return BatchExecutionResponse(
            batch_id=batch_id,
            simulation_ids=simulation_ids,
            total=len(simulation_ids)
        )
```

---

## 4. Analysis Orchestration Service (Adapter Layer - Q8, Q9 Decisions)

### Class Design

**Location**: `api/services/analysis_orchestration_service.py`

**Purpose**: Adapter layer that converts event-scenario structure to batch analysis format

**Key Decisions**:
- **Q8**: Does NOT use OD analysis services (accuracy/mechanism/performance/edgedata_service)
- **Q9**: Does NOT modify existing analysis services - creates adapter layer instead
- **Reuses**: SummaryAnalyzer + EdgeDataAnalyzer from shared layer (unchanged)

**Key Methods**:

```python
class AnalysisOrchestrationService:
    """
    Orchestrates batch analysis for event-scenario simulations.

    Decision Q9-A: Does NOT modify existing analysis services.
    Instead, creates adapter layer to reuse batch analysis tools.

    Reuses (unchanged):
    - SummaryAnalyzer (shared/analysis_tools/batch_result_analyzer.py)
    - EdgeDataAnalyzer (shared/analysis_tools/batch_result_analyzer.py)

    Does NOT use (Q8):
    - accuracy_service (OD-specific)
    - mechanism_service (OD-specific)
    - performance_service (OD-specific)
    - edgedata_service (OD-specific)
    """

    def __init__(self):
        from shared.analysis_tools.batch_result_analyzer import (
            SummaryAnalyzer, EdgeDataAnalyzer
        )
        self.summary_analyzer = SummaryAnalyzer()
        self.edgedata_analyzer = EdgeDataAnalyzer()

    async def create_analysis_batch(
        self,
        simulation_ids: List[str],
        case_id: str,
        baseline_scenario_id: str,
        comparison_scenario_id: Optional[str] = None,
        analysis_focus: List[str] = ["summary", "edgedata"],
        parallel_workers: int = 4
    ) -> AnalysisBatchResponse:
        """
        Create and queue analysis batch for multiple simulations.

        Adapter Pattern (Q8, Q9):
        1. Convert event-scenario simulation structure to batch format
        2. Call SummaryAnalyzer.analyze() and EdgeDataAnalyzer.analyze()
        3. Store results with scenario lineage metadata

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

## 5. Frontend Component Refactoring (Q13, Q14 Decisions)

### Current State
- 74 KB `script.js` with multiple responsibilities (only used by index.html)
- Mixed concerns: DOM manipulation, API calls, data processing

### Target State (Q13: Incremental Refactoring)
- **Phase 2 Strategy**: Create NEW components, do NOT modify existing code
- **Minimal Impact**: Existing pages (control plan UI, scenario browser) unchanged
- **Gradual Migration**: Extract utilities first, then create new components

### File Structure

```
frontend/
├─ components/ (NEW - Phase 2)
│  ├─ shared-utils.js (NEW)
│  │  ├─ export { formatDate, formatTime, parseQuery, ... }
│  │  └─ Common utilities reused across pages
│  ├─ api-client.js (NEW)
│  │  ├─ export class APIClient { ... }
│  │  └─ Centralized API calls with error handling
│  ├─ simulation-monitor.js (NEW - Q14: Generic for all sim types)
│  │  ├─ SimulationMonitor class (real-time progress)
│  │  ├─ Supports: event-scenario, OD extraction, control-plan
│  │  └─ Render simulation list with status indicators
│  └─ analysis-results.js (NEW - event-scenario specific)
│     ├─ AnalysisResults class (visualization)
│     └─ Display heat maps, statistics, comparisons
│
├─ css/
│  └─ styles.css              (Centralized styles)
│
├─ pages/
│  ├─ index.html              (UNCHANGED - still uses script.js)
│  ├─ scenario-browser.html   (UNCHANGED - Phase 1, independent)
│  ├─ case-details.html       (NEW - Phase 2)
│  ├─ simulations.html        (NEW - Phase 2, uses simulation-monitor.js)
│  └─ analysis.html           (NEW - Phase 2, uses analysis-results.js)
│
├─ control/ (UNCHANGED)
│  └─ *.html                  (Control plan UI - not affected)
│
├─ scenarios/ (UNCHANGED)
│  └─ scenario_browser.html   (Phase 1 - not affected)
│
└─ lib/
   └─ bootstrap-icons/        (Icon library)
```

### Q13: Impact on Existing Pages
✅ **Minimal Impact**:
- `script.js` only used by `index.html` - NOT modified in Phase 2
- Phase 1 scenario browser independent - NOT affected
- Control plan optimization UI independent - NOT affected

**Conclusion**: Phase 2 creates new components, existing code untouched.

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

#### simulation-monitor.js (Q14: Generic Component)

```javascript
/**
 * Real-time simulation execution monitor.
 *
 * Decision Q14: Designed as GENERIC component supporting all simulation types:
 * - Event-scenario simulations (Phase 2 implementation)
 * - OD extraction simulations (future)
 * - Control plan batch simulations (already exists, consider compatibility)
 *
 * Adapts behavior based on simulation metadata.
 */

export class SimulationMonitor {
  constructor(containerId, apiClient) {
    this.container = document.getElementById(containerId);
    this.apiClient = apiClient;
    this.updateInterval = 5000;  // Poll every 5 seconds
  }

  async startMonitoring(batchId, simType = 'event-scenario') {
    this.batchId = batchId;
    this.simType = simType;  // Adapt UI based on simulation type

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
