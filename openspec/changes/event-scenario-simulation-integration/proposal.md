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

### 3. Analysis Orchestration Service (NEW - P0 Priority)

**Current State**: 4 separate analysis services (Accuracy, Mechanism, Performance, EdgeData) but no way to run them together on N simulations.

**New Service**: `api/services/analysis_orchestration_service.py`

```python
class AnalysisOrchestrationService:

    async def create_analysis_batch(
        self,
        simulation_ids: List[str],
        baseline_scenario_id: str,
        comparison_scenario_id: Optional[str] = None,
        analysis_focus: List[str] = ["edgedata", "tripinfo"],  # Mandatory vs Optional
        parallel_workers: int = 4
    ) -> AnalysisBatchResponse:
        """
        Execute all required analyses for a set of simulations.

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

**Integration Pattern** (borrowed from proven `BatchOptimizationService`):

- Use task queue: `analysis_tasks_index.json` tracks state
- Each task: `{simulation_id, analysis_type, status, start_time, end_time}`
- Parallel executor with configurable workers (default 4, max 8)
- Automatic retry on transient failures (network, temp file locks)

**Reuses Existing Code**:

- Analysis service methods unchanged: `accuracy_service.run()`, `mechanism_service.run()`, etc.
- Metadata isolation principle maintained
- Uses `batch_result_analyzer.py` pattern for aggregation

---

### 4. Batch Simulation Execution Enhanced (P1)

**Current**: `simulation_service.start_simulation()` runs ONE simulation

**Extend to**:

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

## Version History

- **v1.0** - Initial proposal (2025-11-12)
  - Complete Phase 2 workflow design
  - Three new ADRs (AD-12, AD-13, AD-14)
  - Clear roadmap and success criteria

---

**Proposal Status**: Ready for detailed specification design
**Next Step**: Create detailed specs for each component in `/specs/` subdirectories
