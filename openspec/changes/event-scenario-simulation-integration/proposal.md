# event-scenario-simulation-integration Change Proposal

## Title

Complete Event Scenario-to-Analysis Pipeline: Unified Simulation and Result Analysis Workflow for 449 Event Scenarios

## Summary

Implement the complete Phase 2 workflow enabling users to seamlessly convert event scenarios (from Phase 1) into executable simulations, run them with full monitoring, and automatically process results through comprehensive analysis (EdgeData, TripInfo). This closes the gap from scenario library (Phase 1) to actionable insights.

**Scope**: Backend service orchestration (P0), simulation optimization (P1), analysis workflow (P2), and frontend UX (P1)
**Estimated Effort**: 3-4 weeks for 2-person team
**Dependencies**: Phase 1 complete ✅ (449 scenarios, scenario_index.json, scenario browser)

---

## Problem Statement

### Current Limitations

1. **Scenario Library Incomplete**: Phase 1 created 449 scenarios but no way to execute them
2. **Broken End-to-End Flow**: Users can see scenarios → create cases → but then must manually create simulations
3. **Analysis Isolation**: Analysis services exist but no orchestration layer to run them in sequence
4. **No Progress Visibility**: Long-running simulations/analyses appear to hang
5. **Metadata Gap**: No tracking from scenario → case → simulation → analysis (chain is broken)
6. **Frontend Monolithic**: 74 KB `script.js` blocks implementation of new case/simulation/analysis UIs

### Business Impact

- **MVP Incomplete**: Cannot deliver full scenario library to end users
- **Resource Inefficiency**: Users must manually orchestrate what should be automated
- **Data Loss Risk**: No metadata linkage means analysis results can't be traced back to original scenario
- **User Confusion**: Different UIs for case/simulation management, no unified workflow
- **Batch Capability Unused**: Infrastructure exists (BatchOptimizationService proven in production) but not connected to scenario pipeline

### Technical Debt

- Analysis services isolated from simulation execution
- Three-level metadata structure incomplete (AD-7, AD-8, AD-9 defined but not implemented)
- SUMO configuration generation doesn't handle relative paths (portable configs)
- No analysis progress tracking (metrics only available after completion)

---

## Impact on Existing Functionality (Non-Breaking Guarantee)

### Workflows That Will NOT Be Affected

✅ **Workflow 1: OD提取仿真 (OD Extraction Simulation)**
- API endpoints: `/api/v1/case/create`, `/api/v1/simulation/prepare`, `/api/v1/simulation/start`
- Services: `CaseService.create_case()`, `SimulationService.prepare/start()`
- Metadata: Version 1.0 schema (no `source_scenario` field)
- **Impact**: ZERO - Continues working unchanged

✅ **Workflow 2: 管控方案优化 (Control Plan Optimization)**
- API endpoints: `/api/v1/batch/*`
- Services: `BatchOptimizationService`, `BatchSimulationScheduler`
- Analysis: `SummaryAnalyzer`, `EdgeDataAnalyzer` (shared layer)
- **Impact**: ZERO - Shared infrastructure reused via adapters, not modified

✅ **Frontend Pages**
- `index.html` + `script.js` (main page)
- `frontend/control/*` (control plan UI)
- `frontend/scenarios/scenario_browser.html` (Phase 1)
- **Impact**: ZERO - No modifications to existing pages

### New Additions (Phase 2)

🆕 **New Workflow: Event Scenario Simulation & Analysis**
- **New Endpoint**: `POST /api/v1/case/create-from-scenario`
- **New Services**: `SimulationOrchestrator`, `AnalysisOrchestrationService`
- **New Metadata**: Version 2.0 schema (with `source_scenario` field)
- **New Components**: `simulation-monitor.js`, `analysis-results.js` (generic, reusable)

### Backward Compatibility Strategy

**Principle**: Old and new systems coexist without interference

| Component | Version 1.0 (Existing) | Version 2.0 (New) | Compatibility |
|-----------|------------------------|-------------------|---------------|
| Case Metadata | No `metadata_version` field | Has `metadata_version: "2.0"` | Services detect version |
| Simulation Metadata | No `source_scenario` field | Has `source_scenario` field | Optional field, null-safe |
| API Endpoints | `/case/create` (unchanged) | `/case/create-from-scenario` (new) | Separate endpoints |
| Services | SimulationService (unchanged) | SimulationOrchestrator (new) | Delegation pattern |
| Analysis | OD analysis services (unchanged) | Adapter using batch tools | No interface changes |

---

## Proposed Solution

### 1. Scenario → Simulation → Analysis Metadata Linkage (CRITICAL - AD-12)

**Architecture Decision AD-12: Three-Level Metadata Tracking**

```
Level 1: Case Metadata (case/metadata.json)
├── source_scenario_id: "scenario_12547_vss"
├── source_event_id: "12547"
├── source_event_type: "01_accident"
├── immutable_fields: {event_id, location, strategy_type, affected_edges}
└── overridable_fields: {duration_hours, random_seed, output_config}

    ↓ 1:1 BINDING (AD-7)

Level 2: Simulation Metadata (simulations/sim_id/simulation_metadata.json)
├── source_scenario_id: "scenario_12547_vss"  ← Links back to case
├── scenario_config: {...}
├── event_config: {...}
├── control_config: {...}
├── output_files: {summary, tripinfo, edgedata, vehroute}
└── simulation_parameters: {duration, seed, start_time, end_time}

    ↓ 1:N (ONE SIMULATION → MULTIPLE ANALYSES)

Level 3: Analysis Metadata (case/analysis/{batch_id}/{type}/)
├── source_simulation_id: "sim_id"
├── source_scenario_id: "scenario_12547_vss"  ← Backtrack to scenario
├── baseline_scenario_id: "scenario_12547_none"
├── comparison_config: {...}
└── analysis_results: {metrics, charts, statistics}
```

**Benefits**:

- ✅ Full traceability: analysis result → scenario that generated it
- ✅ Metadata isolation: analyses never modify case/simulation metadata
- ✅ Enables scenario impact analysis: "show me all scenarios of event type X and their combined analysis"

---

### 2. SUMO Configuration Generation with Portable Relative Paths (AD-13)

**Problem**: Different users have different absolute paths. `sumocfg` files currently use absolute paths and won't work on other machines.

**Solution**: Generate `sumocfg` with relative paths from the sumocfg location:

```xml
<!-- BEFORE (Absolute Paths - Not Portable)
<net-file value="D:\projects\OD_SIM\templates\network_files\sichuan.net.xml"/>
<route-files value="C:\data\od_data.xml"/>
-->

<!-- AFTER (Relative Paths - Portable)
<net-file value="../../templates/network_files/sichuan.net.xml"/>
<route-files value="../../data/od_data.xml"/>
<additional-files value="scenario.add.xml,../../templates/taz_files/TAZ_6.add.xml"/>
-->
```

**Implementation**:

- New utility: `shared/utilities/sumo_utils.py::generate_sumocfg_with_relative_paths()`
- Compute relative path from sim dir to templates/data dirs
- Store absolute paths in metadata, use relative in sumocfg
- Validate paths at simulation start time

**Use Cases**:

- Users can move entire `cases/` directory and simulations still work
- Cases can be transferred between machines without path remapping
- Docker containers can mount at any path

---

### 3. Simulation Orchestration Service (NEW - Design Decision Q1-C)

**Current State**: Different simulation workflows use different services (SimulationService, BatchOptimizationService)

**New Service**: `api/services/simulation_orchestrator.py` (Orchestration Layer)

**Purpose**: Detect simulation source and delegate to appropriate services

```python
class SimulationOrchestrator:
    """
    Orchestrates batch simulation execution across different sources.

    Delegation Pattern:
    - Event-scenario → BatchSimulationScheduler (reused, Q2)
    - OD extraction → SimulationService (unchanged)
    - Control plan → BatchOptimizationService (unchanged)
    """

    async def batch_start_simulations(simulation_ids: List[str]) -> BatchExecutionResponse:
        # 1. Detect source from metadata (Q3: backward compatible)
        # 2. Delegate to appropriate service
        # 3. Return unified response
```

**Benefits**:
- ✅ Unified batch execution interface
- ✅ Preserves existing workflows (non-breaking)
- ✅ Reuses BatchSimulationScheduler (Q2 decision)
- ✅ Automatic source detection (Q3 backward compatibility)

---

### 4. Analysis Orchestration Service (NEW - Adapter Layer, Q8/Q9 Decisions)

**Current State**: OD analysis services (accuracy/mechanism/performance/edgedata) exist but not suitable for event-scenario analysis

**Design Decisions**:
- **Q8**: Does NOT use OD analysis services (incompatible interfaces)
- **Q9**: Does NOT modify existing services - creates adapter layer instead
- **Reuses**: SummaryAnalyzer + EdgeDataAnalyzer from batch_result_analyzer.py (shared layer, unchanged)

**New Service**: `api/services/analysis_orchestration_service.py`

```python
class AnalysisOrchestrationService:
    """
    Adapter layer: converts event-scenario structure to batch analysis format.

    Reuses (unchanged):
    - SummaryAnalyzer (shared/analysis_tools/batch_result_analyzer.py)
    - EdgeDataAnalyzer (shared/analysis_tools/batch_result_analyzer.py)

    Does NOT use (Q8):
    - accuracy_service (OD-specific)
    - mechanism_service (OD-specific)
    - performance_service (OD-specific)
    - edgedata_service (OD-specific)
    """

    async def create_analysis_batch(
        self,
        simulation_ids: List[str],
        baseline_scenario_id: str,
        comparison_scenario_id: Optional[str] = None,
        analysis_focus: List[str] = ["summary", "edgedata"],
        parallel_workers: int = 4
    ) -> AnalysisBatchResponse:
        """
        Execute batch analysis for event-scenario simulations.

        Adapter Pattern:
        1. Convert event-scenario structure to batch format
        2. Call SummaryAnalyzer.analyze() and EdgeDataAnalyzer.analyze()
        3. Store results with scenario lineage metadata

        Returns:
            - batch_id: For progress tracking
            - task_queue: Analysis tasks to execute
            - metadata: Configuration for analysis
        """

    async def get_analysis_progress(self, batch_id: str) -> AnalysisBatchProgressResponse:
        """
        Real-time progress tracking (10-second updates):
        {
            "batch_id": "batch_20251112_120000",
            "total_tasks": 320,      # 80 sims × 4 analysis types
            "completed": 45,
            "failed": 2,
            "in_progress": 10,
            "estimated_completion": "2025-11-12T14:30:00",
            "current_analysis": {
                "simulation_id": "sim_123",
                "analysis_type": "edgedata",
                "progress": 65,
                "message": "Processing 2847 edges..."
            }
        }
        """
```

**Integration Pattern**:

- Reuses `batch_result_analyzer.py` infrastructure (Q9: no modifications)
- Adapter converts event-scenario directory structure to batch format
- Calls existing SummaryAnalyzer and EdgeDataAnalyzer directly
- Stores results with scenario lineage metadata

**Key Architecture**:

- **Shared Layer Tools** (unchanged): SummaryAnalyzer, EdgeDataAnalyzer
- **Adapter Layer** (new): AnalysisOrchestrationService
- **OD Services** (unchanged, not used): accuracy/mechanism/performance/edgedata services

---

### 5. Relative Path Generation (AD-13 - Q12 Decision)

**Problem**: Absolute paths in sumocfg won't work when cases are moved

**Solution (Q12)**: Unified relative path strategy
- **Metadata**: Store paths relative to project root (source of truth)
- **sumocfg**: Store paths relative to sumocfg location (generated from metadata)
- **Authority**: Metadata is canonical, sumocfg regenerated as needed

**Example**:
```
Metadata: "network_file": "templates/network_files/sichuan.net.xml"
sumocfg:  <net-file value="../../../../templates/network_files/sichuan.net.xml"/>
```

---

### 6. Frontend Component Refactoring (Q13, Q14 Decisions)

**Q13 Decision**: Incremental refactoring - Create new components, do NOT modify existing code

**Current Impact**:
- `script.js` only used by `index.html` - NOT modified
- Control plan UI - NOT affected
- Phase 1 scenario browser - NOT affected

**New Components (Phase 2)**:
- `simulation-monitor.js` - **Generic** (Q14), supports all simulation types
- `analysis-results.js` - Event-scenario specific
- `shared-utils.js` - Extracted utilities
- `api-client.js` - Centralized API calls

**Q14 Decision**: simulation-monitor.js designed as generic component
- Event-scenario simulations (Phase 2 implementation)
- OD extraction simulations (future compatibility)
- Control plan simulations (existing, consider compatibility)

---

### 7. Batch Simulation Execution (Delegated, Not New Service)

**Current**: `simulation_service.start_simulation()` runs ONE simulation

**Phase 2 Approach** (via SimulationOrchestrator):

```python
class SimulationExecutionService:

    async def batch_start_simulations(
        self,
        simulation_ids: List[str],
        parallel_workers: int = 4
    ) -> BatchExecutionResponse:
        """Start multiple simulations with concurrency control."""

    async def get_batch_execution_status(
        self,
        batch_id: str
    ) -> BatchExecutionStatusResponse:
        """
        Real-time status with detailed per-simulation info:
        {
            "batch_id": "batch_20251112_120000",
            "simulations": [
                {
                    "simulation_id": "sim_1",
                    "status": "running",
                    "progress_percent": 45,
                    "vehicles_completed": 3456,
                    "elapsed_time": "00:23:15",
                    "eta": "00:28:45"
                },
                {
                    "simulation_id": "sim_2",
                    "status": "completed",
                    "result_files": ["summary.xml", "tripinfo.xml", "edgedata.xml"]
                }
            ]
        }
        """
```

**Key Features**:

- Result validation: Auto-check summary.xml, tripinfo.xml, edgedata.xml presence
- SUMO log capture: Store in `simulations/sim_id/sumo_logs/sumo_*.log`
- Error detection: Pattern matching for common SUMO errors (malformed OD, network issues)
- Automatic cleanup: Remove temp files, compress logs after completion

---

### 5. Frontend Refactoring & New UIs (P1)

**Problem**: 74 KB monolithic `script.js` makes it hard to add new features

**Solution**: Component-based refactor (following scenario_browser.js pattern):

```
frontend/
├── components/
│   ├── case-details.js          (new: case info, sim list)
│   ├── simulation-monitor.js    (new: realtime progress, logs)
│   ├── analysis-results.js      (new: EdgeData viz, stats)
│   ├── shared-utils.js          (refactored common functions)
│   └── api-client.js            (shared API calls)
├── pages/
│   ├── cases.html               (existing, updated imports)
│   ├── simulations.html         (new, uses simulation-monitor.js)
│   ├── analysis.html            (new, uses analysis-results.js)
│   └── scenario-browser.html    (existing from Phase 1)
└── css/
    └── styles.css               (centralized styles)
```

**New Pages**:

1. **Simulations Monitor** (`/simulations` or case details → simulations tab)
   - List simulations with filters (status, scenario_id, date range)
   - Real-time progress bars (via polling `get_batch_execution_status()`)
   - Expandable log viewer (last 500 lines of SUMO log)
   - Actions: Start/Stop/Delete/View Results

2. **Analysis Results Dashboard** (after analysis completion)
   - Show EdgeData heat map (road segments, average speed, congestion)
   - TripInfo statistics (avg trip time, vehicle completion %)
   - Comparison charts (baseline vs with event vs with control)
   - Download report (PDF/JSON)

**Component Features**:

- Reuse scenario_browser.js pattern (table, filters, modals)
- Use shared-utils.js for common functions
- API polling for real-time updates (10-second interval)
- Error boundaries with retry logic

---

### 6. New API Endpoints (P0/P1)

| Endpoint | Method | Purpose | New? | Priority |
|----------|--------|---------|------|----------|
| `/api/v1/simulation/batch-start` | POST | Start multiple simulations | Yes | P1 |
| `/api/v1/simulation/batch-status/{batch_id}` | GET | Monitor batch progress | Yes | P1 |
| `/api/v1/analysis/run` | POST | Create analysis batch | Yes | P0 |
| `/api/v1/analysis/batch-progress/{batch_id}` | GET | Monitor analysis progress | Yes | P0 |
| `/api/v1/analysis/results/{batch_id}/{type}` | GET | Retrieve analysis results | Yes | P2 |

**Request/Response Models**:

- `BatchSimulationRequest` / `BatchSimulationResponse`
- `AnalysisBatchRequest` / `AnalysisBatchProgressResponse`
- `AnalysisResultResponse` (with visualization data)

---

## Critical Issue: Scenario Directory Structure (RESOLVED)

### ISSUE: Phase 1 Output Structure Mismatch

**Root Cause**: Data format mismatches between `scenario_index.json` metadata and actual filesystem:

| Component | JSON (`scenario_index.json`) | Filesystem | Issue |
|-----------|-----|----------|-------|
| Event Type | `"交通事故"` (Chinese) | `01_accident/` (Numeric+English) | Cannot construct path from parameter |
| Strategy | `"NO_CONTROL"` (uppercase) | `scenario_10754_no_control/` (lowercase) | Case sensitivity on different OS |
| SUMO Config | Expected in scenario dir | Not present (generated at runtime) | Validation fails |

**Solution Implemented**: Plan B - Robust scenario validation that:
1. Searches all event_type directories for scenario_id (decouples from encoding format)
2. Validates only ACTUAL files present (event_description.json, traffic_input_config.json, control_strategy_config.json)
3. Does NOT require simulation.sumocfg (it's generated at simulation time)

**Code Updated**:
- `scripts/initialize_scenario_library.py:validate_event_scenario()` (lines 62-139)
- Uses directory scanning instead of path construction
- Includes comprehensive debug logging for troubleshooting

**Documentation Updated**:
- `design.md`: New "Section 0 - Scenario Directory Structure" documents actual structure
- Details all three encoding mismatches and why they occur
- Explains implications for case creation, frontend, and simulation setup

**Result**: ✅ Scenario validation is now ROBUST and works with Phase 1 output structure

---

## Implementation Roadmap

### Week 1: Foundation (P0 - Blocking)

- [ ] Implement AD-12 three-level metadata tracking
- [ ] Create `AnalysisOrchestrationService`
- [ ] Extend `SimulationExecutionService` with batch support
- [ ] Write 20+ unit tests
- [ ] Implement progress tracking infrastructure

### Week 2: Execution (P1)

- [ ] SUMO configuration generator with relative paths (AD-13)
- [ ] Batch execution routes + API
- [ ] Refactor frontend into components
- [ ] Build simulation monitor UI
- [ ] Integration testing

### Week 3: Results (P2)

- [ ] Analysis results aggregation
- [ ] Build analysis results dashboard
- [ ] Generate comparison reports
- [ ] E2E testing (scenario → simulation → analysis)

### Week 4: Polish

- [ ] Error recovery and retry logic
- [ ] Performance optimization
- [ ] Documentation
- [ ] Production readiness

---

## Success Criteria

- [ ] User can click "Create Case from Scenario" → simulation is automatically created
- [ ] User can batch start 10+ simulations and monitor progress in real-time
- [ ] After simulation completes, all 4 analyses (EdgeData, TripInfo, Accuracy, Performance) run automatically
- [ ] Analysis progress visible (not just final results)
- [ ] User can view analysis results (heat maps, statistics, comparisons)
- [ ] Full metadata chain: scenario → case → simulation → analysis (traceable)
- [ ] 100% of 449 scenarios can be simulated and analyzed
- [ ] SUMO configs portable (works on different machines/paths)
- [ ] No data corruption through metadata isolation
- [ ] Frontend responsive and performant
- [ ] Comprehensive E2E tests covering all workflows

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Analysis orchestration blocks on slow analysis (EdgeData on large simulations) | Users wait 30+ min | Progress tracking shows ETA; allow analysis cancellation |
| Relative path generation breaks on circular symlinks | SUMO won't start | Validate paths before sim start; use realpath() |
| Metadata corruption if analysis modifies case/sim JSON | Data loss | Metadata isolation enforced (read-only patterns in services) |
| Frontend UI lags on real-time updates (100 simulations) | Poor UX | Pagination + 5-second update interval (not 1-second) |
| 449 simulations all at once exhausts disk/CPU | Crash | Limit parallel workers to 4-8; queue overflow handling |

---

## Testing Strategy

**Unit Tests** (20+ test cases):

- Test metadata tracking (scenario → case → simulation → analysis)
- Test relative path generation for different directory structures
- Test batch execution with mock SUMO subprocess
- Test analysis orchestration with mock analyses

**Integration Tests** (5+ test cases):

- Create case from scenario → automatic simulation creation
- Batch start 5 simulations → monitor progress
- Batch analysis on completed simulations
- Verify all result files present and valid

**E2E Tests** (3+ test cases):

- Full workflow: Scenario → Case → Simulation (run) → Analysis (run) → View results
- Batch workflow: 10 scenarios → 10 cases → batch simulation → batch analysis
- Error recovery: Failed simulation → retry → analysis skips

---

## References to Related Specifications

- **AD-7**: 1:1 Case-Scenario Binding (Phase 1, implemented)
- **AD-8**: Configuration Override Policy (Phase 1, implemented)
- **AD-9**: Batch Concurrency Support (extends Phase 1)
- **AD-10**: EdgeData Analysis Mandatory (Phase 1, constraint)
- **AD-11**: Manual Result Retention (Phase 1, DELETE pattern)

**New ADRs Created**:

- **AD-12**: Three-Level Metadata Tracking (scenario → case → simulation → analysis)
- **AD-13**: SUMO Configuration Relative Paths (portability)
- **AD-14**: Analysis Orchestration Concurrency (worker pool management)

---

## Effort Estimation

| Component | LOC | Effort | Priority |
|-----------|-----|--------|----------|
| AnalysisOrchestrationService | 400-500 | 2-3 days | P0 |
| SimulationExecutionService (batch) | 200-300 | 1-2 days | P1 |
| SUMO path utilities | 150-200 | 1 day | P0 |
| API routes (simulation + analysis) | 250-300 | 1-2 days | P1 |
| Unit tests | 500-600 | 2 days | P0 |
| Frontend refactoring | 400-500 | 2-3 days | P1 |
| Frontend components | 300-400 | 2-3 days | P1 |
| Integration tests | 200-300 | 1-2 days | P1 |
| Documentation | 200-300 | 1 day | P2 |
| **TOTAL** | **2,600-3,100** | **3-4 weeks** | - |

---

## Extension: CSV Batch Scenario Generation

### Feature Description

Enable users to generate scenario bundles in batch from event CSV files through the scenario browser UI.

**User Story**:
> As a traffic analyst, I want to upload/select an event CSV file and automatically generate scenarios for all new events, so I don't have to manually run scripts or generate scenarios one by one.

### Key Capabilities

1. **CSV File Selection**: Choose from available CSV files in `events/` folder
2. **Duplicate Detection**: Automatically skip events that already have scenarios
3. **Batch Generation**: Generate all scenarios (NO_CONTROL/VSS/TEC/DHS) in one operation
4. **State Tracking**: Track progress and failures in JSON status files
5. **Simple UI**: Minimal frontend changes, simple alerts for status

### Technical Approach

**API Endpoint**: `POST /api/v1/scenario/generate-from-csv`

**Request**:
```json
{
  "csv_file": "all_extracted_events.csv",
  "generate_all_strategies": true
}
```

**Response**:
```json
{
  "task_id": "csv_gen_20251114_143000",
  "status": "processing",
  "message": "CSV场景生成已启动",
  "state_file": "events/csv_extraction_status/all_extracted_events_status.json"
}
```

**Process**:
1. Validate CSV file exists
2. Create state tracking file in `events/csv_extraction_status/`
3. Load CSV and filter events
4. Check `scenario_index.json` to detect existing scenarios
5. Generate scenarios only for new events
6. Update state file with success/failure details
7. Update `scenario_index.json`

**State File Structure** (`events/csv_extraction_status/{csv_name}_status.json`):
```json
{
  "csv_file": "all_extracted_events.csv",
  "task_id": "csv_gen_20251114_143000",
  "started_at": "2025-11-14T14:30:00",
  "completed_at": "2025-11-14T14:35:00",
  "status": "completed",
  "total_events_in_csv": 150,
  "events_processed": 150,
  "events_skipped_existing": 100,
  "events_generated": 50,
  "scenarios_generated": {"no_control": 50, "vss": 50, "tec": 50, "total": 150},
  "failed_events": [...],
  "successful_events": [...]
}
```

### Implementation Scope

**Backend** (Priority: P1):
- ✅ New API endpoint in `api/routes/scenario_routes.py`
- ✅ CSV processing logic in `api/services/scenario_service.py`
- ✅ Reuse `ScenarioGenerator` from `shared/control_tools/`
- ✅ State tracking file creation and updates
- ✅ Duplicate detection against `scenario_index.json`

**Frontend** (Priority: P1 - Already Implemented):
- ✅ CSV file dropdown (loads from `/api/v1/scenario/list-csv-files`)
- ✅ Generate button calls API
- ✅ Simple alert with task_id
- ❌ Real-time progress monitoring (Future enhancement)

**Testing** (Priority: P1):
- ✅ Unit tests for duplicate detection
- ✅ Integration test with sample CSV
- ✅ E2E test: CSV → scenarios → verify state file

### Design Principles

- **Simplicity**: No complex queue system, direct execution
- **Reusability**: Reuse existing `generate_scenarios_from_events.py` logic
- **State Tracking**: Simple JSON files for status (no database)
- **Idempotency**: Safe to re-run, skips existing scenarios
- **Error Tolerance**: Continue processing even if individual events fail

### Success Criteria

1. User can select CSV file from dropdown
2. Click "Generate" creates scenarios for new events only
3. Existing scenarios are not duplicated
4. State file accurately tracks success/failure
5. `scenario_index.json` is updated correctly
6. Failed events are logged with clear error messages

### Estimated Effort

| Component | LOC | Time | Priority |
|-----------|-----|------|----------|
| Backend API endpoint | 50-80 | 2-3 hours | P1 |
| CSV processing service | 150-200 | 4-6 hours | P1 |
| State tracking logic | 80-100 | 2-3 hours | P1 |
| Duplicate detection | 40-60 | 1-2 hours | P1 |
| Unit + integration tests | 100-150 | 3-4 hours | P1 |
| **TOTAL** | **420-590** | **12-18 hours** | - |

**Timeline**: 2-3 days for complete implementation and testing

---

## Version History

- **v1.1** - CSV Batch Generation Extension (2025-11-14)
  - Added CSV batch scenario generation feature
  - State tracking file design
  - Duplicate detection logic
  - Simple UI integration

- **v1.0** - Initial proposal (2025-11-12)
  - Complete Phase 2 workflow design
  - Three new ADRs (AD-12, AD-13, AD-14)
  - Clear roadmap and success criteria

---

**Proposal Status**: Ready for detailed specification design
**Next Step**: Create detailed specs for each component in `/specs/` subdirectories
