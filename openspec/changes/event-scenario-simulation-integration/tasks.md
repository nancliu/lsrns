# Phase 2: Event Scenario Simulation Integration - Task List

**Total Effort**: 3-4 weeks (2-person team)
**Current Status**: Ready for implementation
**Last Updated**: 2025-11-12

---

## Week 1: Foundation (P0 - Blocking Everything Else)

### Task 1.1: Analysis Orchestration Service - Core Implementation
**Type**: Backend | **Effort**: 2-3 days | **Priority**: P0 | **Blocks**: 2.x, 3.x

**Description**: Create `AnalysisOrchestrationService` to queue and execute analysis tasks for multiple simulations.

**Deliverables**:
- [ ] File created: `api/services/analysis_orchestration_service.py` (300-400 LOC)
  - Class: `AnalysisOrchestrationService`
  - Methods:
    - `create_analysis_batch()` - Queue analysis tasks
    - `get_analysis_progress()` - Real-time monitoring
    - `cancel_analysis_batch()` - Graceful shutdown
  - Helper: `_queue_analysis_tasks()` - Generate task list
  - Helper: `_execute_task_queue()` - Worker pool executor

**Requirements**:
- ✅ Support 4 analysis types: EdgeData (mandatory), TripInfo, Accuracy, Performance (optional)
- ✅ Configurable worker pool: 2-8 workers (default 4)
- ✅ Task state tracking: `analysis_tasks_index.json` in case directory
- ✅ Progress updates: Every 10 seconds with ETA calculation
- ✅ Metadata linkage: Each task stores source_simulation_id and source_scenario_id
- ✅ Error handling: Automatic retry (max 3 attempts) for transient failures
- ✅ Isolation: Never modify case or simulation metadata

**Acceptance Criteria**:
- All methods have docstrings and type hints
- Service creates analysis_tasks_index.json with correct structure
- Real-time progress API returns data within 2 seconds
- Tasks execute serially (not parallel to analyses) to avoid resource exhaustion
- Edge case: Handle empty simulation_ids list gracefully

**Tests Required**:
- Unit test: Task queue creation with 10 simulations
- Unit test: Progress calculation (completed/total)
- Unit test: Analysis type validation
- Unit test: Worker pool initialization

**Files Modified**:
- `api/services/__init__.py` - Add AnalysisOrchestrationService export

---

### Task 1.2: Analysis Orchestration API Routes
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.1

**Description**: Create API endpoints for analysis orchestration.

**Deliverables**:
- [ ] File created: `api/routes/analysis_orchestration_routes.py` (150-200 LOC)
  - Route: `POST /api/v1/analysis/run` - Create analysis batch
  - Route: `GET /api/v1/analysis/batch-progress/{batch_id}` - Monitor progress
  - Route: `DELETE /api/v1/analysis/batch/{batch_id}` - Cancel batch

**Requirements**:
- ✅ Request validation using Pydantic models
- ✅ Error handling with descriptive messages
- ✅ CORS support
- ✅ Logging for all operations

**Acceptance Criteria**:
- Endpoints return proper HTTP status codes
- Error responses include `error_code` and `message` fields
- Request validation catches invalid input

**Tests Required**:
- Unit test: POST /api/v1/analysis/run with valid request
- Unit test: GET /api/v1/analysis/batch-progress/{batch_id}
- Unit test: Invalid request returns 400

**Files Modified**:
- `api/routes/__init__.py` - Register analysis_orchestration_router

---

### Task 1.3: Data Models for Analysis Orchestration
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.1

**Description**: Create Pydantic models for request/response validation.

**Deliverables**:
- [ ] File created: `api/models/requests/analysis_orchestration_request.py` (100-150 LOC)
  - Model: `AnalysisBatchRequest`
  - Model: `AnalysisBatchCancelRequest`

- [ ] File created: `api/models/responses/analysis_orchestration_response.py` (100-150 LOC)
  - Model: `AnalysisBatchResponse`
  - Model: `AnalysisTaskInfo`
  - Model: `AnalysisBatchProgressResponse`

**Requirements**:
- ✅ Field validation (min/max values, enum validation)
- ✅ Descriptive docstrings
- ✅ Example values in Field descriptions

**Tests Required**:
- Unit test: AnalysisBatchRequest validation (valid + invalid cases)
- Unit test: AnalysisBatchProgressResponse serialization

**Files Modified**:
- `api/models/__init__.py` - Add new model exports

---

### Task 1.4: Three-Level Metadata Structure Implementation
**Type**: Backend | **Effort**: 1.5 days | **Priority**: P0 | **Blocks**: 1.1, 2.x, 3.x

**Description**: Ensure metadata tracking through all three levels (Case → Simulation → Analysis).

**Deliverables**:
- [ ] Update `api/services/simulation_service.py`:
  - Ensure case metadata includes `source_scenario_id`
  - Ensure case metadata includes `immutable_fields` and `overridable_fields`

- [ ] Update `shared/data_processors/simulation_processor.py`:
  - Generate simulation_metadata.json with correct structure
  - Copy scenario configs (event, control) into simulation metadata
  - Track `source_scenario_id` field

- [ ] Update `api/services/analysis_orchestration_service.py`:
  - Generate analysis_metadata.json with complete lineage
  - Backtrack: analysis → simulation → scenario
  - Mark analysis as read-only (never modify case/sim files)

**Requirements**:
- ✅ Case metadata has `source_scenario_id` from AD-7
- ✅ Simulation metadata has `source_scenario_id` for backtracking
- ✅ Analysis metadata has `source_simulation_id` and can compute `source_scenario_id`
- ✅ Metadata files are JSON with consistent schema
- ✅ Metadata is validated at creation time

**Acceptance Criteria**:
- All three metadata files exist after operations complete
- Metadata can be traced back: analysis_metadata → simulation_metadata → case_metadata
- Analysis operations never modify case or simulation metadata
- Metadata includes timestamps and status fields

**Tests Required**:
- Unit test: Case creation sets source_scenario_id
- Unit test: Simulation creation copies scenario configs
- Unit test: Analysis metadata includes full lineage
- Unit test: Metadata read-only validation

**Files Modified**:
- `api/services/simulation_service.py`
- `shared/data_processors/simulation_processor.py`
- `api/services/analysis_orchestration_service.py`

---

### Task 1.5: Analysis Progress Tracking Infrastructure
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.1, 1.4

**Description**: Real-time progress monitoring for analysis batches.

**Deliverables**:
- [ ] Utility: `shared/utilities/analysis_progress_tracker.py` (100-150 LOC)
  - Class: `AnalysisProgressTracker`
  - Methods:
    - `init_batch()` - Create task queue
    - `update_task_progress()` - Update single task
    - `get_batch_progress()` - Calculate overall progress
    - `calculate_eta()` - Estimate completion time

**Requirements**:
- ✅ Update progress every 10 seconds (not 1-second)
- ✅ ETA calculation based on completed/total and elapsed time
- ✅ Progress percentage calculation
- ✅ Handle edge cases: zero tasks, zero elapsed time

**Acceptance Criteria**:
- ETA updates as tasks complete
- Progress percentages are accurate
- No division by zero errors

**Tests Required**:
- Unit test: ETA calculation with 5 tasks (2 complete, 3 remaining)
- Unit test: Progress percentage (25 of 100 tasks = 25%)

---

### Task 1.6: Unit Tests for Week 1
**Type**: Testing | **Effort**: 1.5 days | **Priority**: P0 | **Depends on**: 1.1-1.5

**Description**: Comprehensive unit tests for all Week 1 components.

**Deliverables**:
- [ ] File: `tests/unit/services/test_analysis_orchestration_service.py` (200-300 LOC)
  - Test class: `TestAnalysisOrchestrationService`
  - 8-10 test methods covering core functionality

**Test Coverage Required**:
- ✅ create_analysis_batch() with valid inputs
- ✅ create_analysis_batch() with invalid simulation_ids
- ✅ get_analysis_progress() returns correct structure
- ✅ Task queue generation with 4 analysis types
- ✅ Metadata linkage (scenario → simulation → analysis)
- ✅ Worker pool initialization
- ✅ Error handling and retries

**Acceptance Criteria**:
- All tests pass with mocked dependencies
- Code coverage > 80% for service methods
- Tests are isolated (no cross-test dependencies)

---

## Week 2: Simulation Execution & Frontend Refactoring (P1)

### Task 2.1: Simulation Execution Service - Batch Methods
**Type**: Backend | **Effort**: 1.5 days | **Priority**: P1 | **Depends on**: 1.4

**Description**: Extend `SimulationExecutionService` with batch execution capabilities.

**Deliverables**:
- [ ] File update: `api/services/simulation_service.py`
  - Add method: `batch_start_simulations()`
    - Input: simulation_ids[], parallel_workers (2-8)
    - Output: batch_id for tracking
    - Process: Queue simulations, start executor
  - Add method: `get_batch_execution_status()`
    - Input: batch_id
    - Output: Real-time progress with per-simulation details
  - Add helper: `_validate_simulation_results()`
    - Check: summary.xml exists and valid
    - Check: tripinfo.xml (if enabled) valid
    - Check: edgedata.xml (if enabled) valid and has data

**Requirements**:
- ✅ Reuse `BatchOptimizationService` worker pool pattern
- ✅ Create `batch_execution_index.json` to track state
- ✅ Per-simulation progress: vehicles completed, elapsed time, ETA
- ✅ Result validation: Check output files exist and are valid
- ✅ Auto-trigger analysis when all simulations complete (if enabled)
- ✅ SUMO log capture: Store in `simulations/sim_id/sumo_logs/`

**Acceptance Criteria**:
- Batch start accepts 1-100 simulation IDs
- Parallel workers: 2-8 (enforced)
- Progress updates every 10 seconds
- All output files validated before marking "completed"
- SUMO logs captured and compressed

**Tests Required**:
- Unit test: batch_start_simulations() with 5 simulations
- Unit test: Progress calculation (3 completed, 1 running, 1 queued)
- Unit test: Result validation with mock output files
- Unit test: Auto-trigger analysis on completion

---

### Task 2.2: SUMO Configuration with Relative Paths
**Type**: Backend | **Effort**: 1.5 days | **Priority**: P1 | **Depends on**: 1.4, 2.1

**Description**: Generate SUMO `.sumocfg` files with portable relative paths (AD-13).

**Deliverables**:
- [ ] File update: `shared/utilities/sumo_utils.py`
  - New function: `generate_sumocfg_with_relative_paths()`
    - Input: case_id, simulation_id, config params
    - Output: Path to generated sumocfg file
    - Process:
      1. Compute relative paths from sim dir to network, OD, TAZ
      2. Generate XML with relative paths
      3. Validate paths at generation time
  - New function: `validate_sumocfg_paths()`
    - Input: sumocfg file path
    - Output: (is_valid, error_list)
    - Checks: All file references exist and are reachable

**Requirements**:
- ✅ Compute relative paths using `pathlib.Path.relative_to()`
- ✅ Handle different directory structures (e.g., cases in different parents)
- ✅ Use forward slashes for SUMO compatibility
- ✅ Validate at generation time (not runtime)
- ✅ Store absolute paths in simulation metadata (for logging)
- ✅ Store relative paths in sumocfg (for portability)

**Example Paths**:
```
From: cases/case_id/simulations/sim_id/simulation.sumocfg
To:   templates/network_files/xxx.net.xml
Path: ../../templates/network_files/xxx.net.xml

To:   data/od_data.xml
Path: ../../data/od_data.xml
```

**Acceptance Criteria**:
- Generated sumocfg uses relative paths
- All paths in sumocfg are reachable from sim directory
- Paths work on different machines (portable)
- Validation catches missing files before SUMO starts

**Tests Required**:
- Unit test: Relative path computation
- Unit test: Different directory structure handling
- Unit test: Path validation success/failure

---

### Task 2.3: Simulation Execution API Routes
**Type**: Backend | **Effort**: 1 day | **Priority**: P1 | **Depends on**: 2.1

**Description**: Add API endpoints for batch simulation execution.

**Deliverables**:
- [ ] File update: `api/routes/simulation_routes.py`
  - Route: `POST /api/v1/simulation/batch-start` - Start batch
  - Route: `GET /api/v1/simulation/batch-status/{batch_id}` - Monitor progress

**Requirements**:
- ✅ Request validation using Pydantic models
- ✅ Proper error responses
- ✅ CORS support
- ✅ Logging

**Acceptance Criteria**:
- Endpoints return correct status codes
- Error messages are descriptive
- Progress updates are real-time

**Tests Required**:
- Unit test: POST /api/v1/simulation/batch-start
- Unit test: GET /api/v1/simulation/batch-status/{batch_id}

---

### Task 2.4: Frontend Component Refactoring - Shared Utils
**Type**: Frontend | **Effort**: 1.5 days | **Priority**: P1 | **Depends on**: None

**Description**: Extract common functions from `script.js` into reusable modules.

**Deliverables**:
- [ ] File created: `frontend/components/shared-utils.js` (100-150 LOC)
  - Function: `formatDate()` - Format datetime to locale string
  - Function: `formatTime()` - Format seconds to HH:MM:SS
  - Function: `getStatusBadgeClass()` - CSS class for status badge
  - Function: `delay()` - Promise-based delay
  - Function: `parseQuery()` - Parse URL query parameters
  - Function: `getColorForStatus()` - Color mapping for status

- [ ] File created: `frontend/components/api-client.js` (100-150 LOC)
  - Class: `APIClient`
  - Method: `request()` - Generic HTTP request with error handling
  - Method: `getSimulationBatchStatus()` - Wrapper for batch status API
  - Method: `getAnalysisProgress()` - Wrapper for analysis progress API
  - Method: `startAnalysisBatch()` - Wrapper for analysis start API

**Requirements**:
- ✅ No external dependencies (vanilla JavaScript)
- ✅ Error handling with try-catch
- ✅ Type hints in JSDoc comments
- ✅ Reusable across all pages

**Acceptance Criteria**:
- Functions work correctly in multiple contexts
- No console errors
- Error messages are user-friendly

**Tests Required**:
- Manual: formatDate() with various inputs
- Manual: formatTime() with 3600 seconds = "01:00:00"

---

### Task 2.5: Frontend Component - Simulation Monitor
**Type**: Frontend | **Effort**: 2 days | **Priority**: P1 | **Depends on**: 2.4, 2.1

**Description**: Build real-time simulation execution monitor UI.

**Deliverables**:
- [ ] File created: `frontend/components/simulation-monitor.js` (200-250 LOC)
  - Class: `SimulationMonitor`
  - Method: `startMonitoring()` - Poll API and update UI
  - Method: `render()` - Render simulation list and progress
  - Method: `renderSimulationRow()` - Single simulation row
  - Method: `expandLogs()` - Show/hide SUMO logs

**UI Structure**:
```
┌─ Batch Progress ─────────────────────────────┐
│ Total: 10 | Completed: 4 | Failed: 1        │
│ In Progress: 2 | Queued: 3                   │
│ ETA: 2025-11-12 18:45:00                    │
├──────────────────────────────────────────────┤
│ Simulation List                              │
├─────────────┬─────────┬──────────┬──────────┤
│ SIM ID      │ Status  │ Progress │ Actions  │
├─────────────┼─────────┼──────────┼──────────┤
│ sim_123     │ Running │ 45% ▓▓▓▓ │ [Logs]   │
│ sim_456     │ Done    │ 100%    │ [Results]│
│ sim_789     │ Pending │ 0%      │ -        │
└─────────────┴─────────┴──────────┴──────────┘
```

**Requirements**:
- ✅ Update every 5-10 seconds (via polling)
- ✅ Progress bars show execution progress
- ✅ Status badges with color coding
- ✅ Expandable log viewer
- ✅ Auto-stop polling when batch completes
- ✅ Error handling: Retry on API failure

**Acceptance Criteria**:
- Progress bars update smoothly
- Logs display correctly
- UI responsive (no freezing during updates)
- Auto-stops polling when all done

**Tests Required**:
- Manual: Start batch, monitor progress
- Manual: Expand/collapse logs
- Manual: Verify auto-stop on completion

---

### Task 2.6: Data Models for Batch Execution
**Type**: Backend | **Effort**: 1 day | **Priority**: P1 | **Depends on**: 2.1

**Description**: Create Pydantic models for batch simulation requests/responses.

**Deliverables**:
- [ ] File update: `api/models/requests/batch_simulation_request.py`
  - Model: `BatchSimulationStartRequest`
  - Model: `BatchSimulationCancelRequest`

- [ ] File update: `api/models/responses/batch_simulation_response.py`
  - Model: `SimulationProgressInfo`
  - Model: `BatchSimulationResponse`
  - Model: `BatchExecutionStatusResponse`

**Requirements**:
- ✅ Field validation
- ✅ Descriptive docstrings
- ✅ Type hints

**Tests Required**:
- Unit test: Model validation

---

## Week 3: Analysis Results & Visualization (P2)

### Task 3.1: Analysis Results Aggregation
**Type**: Backend | **Effort**: 1.5 days | **Priority**: P2 | **Depends on**: 1.1, 2.1

**Description**: Aggregate analysis results from multiple simulations and generate comparison metrics.

**Deliverables**:
- [ ] File created: `api/services/analysis_results_service.py` (200-250 LOC)
  - Class: `AnalysisResultsService`
  - Method: `aggregate_batch_results()` - Combine results from all simulations
  - Method: `generate_comparison_report()` - Create comparison metrics
  - Method: `get_result_summary()` - High-level overview

**Requirements**:
- ✅ Reuse `batch_result_analyzer.py` patterns
- ✅ Aggregate EdgeData metrics across simulations
- ✅ Aggregate TripInfo metrics across simulations
- ✅ Generate comparison (baseline vs with event vs with control)
- ✅ Handle missing/failed analyses gracefully

**Acceptance Criteria**:
- Results aggregated correctly
- Comparisons show meaningful differences
- No division by zero on edge cases

**Tests Required**:
- Unit test: Aggregate 5 simulation results
- Unit test: Comparison calculation

---

### Task 3.2: Analysis Results API Routes
**Type**: Backend | **Effort**: 1 day | **Priority**: P2 | **Depends on**: 3.1

**Description**: Add API endpoints to retrieve analysis results.

**Deliverables**:
- [ ] File update: `api/routes/analysis_orchestration_routes.py`
  - Route: `GET /api/v1/analysis/results/{batch_id}` - Get aggregated results
  - Route: `GET /api/v1/analysis/comparison/{batch_id}` - Get comparison report

**Requirements**:
- ✅ Return aggregated metrics
- ✅ Return comparison data in visualization-ready format
- ✅ Include metadata for filtering/grouping

**Tests Required**:
- Unit test: GET /api/v1/analysis/results/{batch_id}

---

### Task 3.3: Frontend Component - Analysis Results Dashboard
**Type**: Frontend | **Effort**: 2 days | **Priority**: P2 | **Depends on**: 2.4, 3.1

**Description**: Build analysis results visualization dashboard.

**Deliverables**:
- [ ] File created: `frontend/components/analysis-results.js` (250-300 LOC)
  - Class: `AnalysisResultsDashboard`
  - Method: `displayEdgeDataHeatmap()` - Visualize road segment speeds
  - Method: `displayStatistics()` - Show metrics and comparisons
  - Method: `displayComparison()` - Baseline vs event vs control

**UI Structure**:
```
┌─ Analysis Results Dashboard ─────────────────┐
│                                              │
│ ┌─ EdgeData Analysis ──────────────────────┐ │
│ │ Road Segment Heat Map (avg speed)        │ │
│ │ [Map/List view with colors]              │ │
│ │ Most Congested: Edge_5 (avg 25 km/h)    │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌─ Statistics ────────────────────────────┐ │
│ │ Total Vehicles: 8,934                    │ │
│ │ Avg Trip Time: 245.6 minutes             │ │
│ │ Completion Rate: 98.7%                   │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌─ Comparison (Event + Control vs Baseline)─┐ │
│ │ Metric          │ Baseline │ With Control │ │
│ │ Avg Speed       │  45 km/h │  52 km/h ↑   │ │
│ │ Trip Time       │  200 min │  185 min ↓   │ │
│ │ Congestion      │  Medium  │  Low ↓↓      │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ [Download Report] [Export Data]             │
└──────────────────────────────────────────────┘
```

**Requirements**:
- ✅ Display EdgeData in table or heat map
- ✅ Show key metrics with visual comparisons
- ✅ Color coding: Green (improvement) / Red (degradation)
- ✅ Responsive layout
- ✅ Download report as PDF/JSON

**Acceptance Criteria**:
- Visualizations render without errors
- Data is accurate (matches backend)
- Layout responsive on desktop/tablet/mobile
- Download works correctly

**Tests Required**:
- Manual: Render with sample data
- Manual: Download functionality

---

### Task 3.4: Analysis Results Data Models
**Type**: Backend | **Effort**: 1 day | **Priority**: P2 | **Depends on**: 3.1

**Description**: Create Pydantic models for analysis results.

**Deliverables**:
- [ ] File created: `api/models/responses/analysis_results_response.py` (150-200 LOC)
  - Model: `EdgeDataMetrics`
  - Model: `TripInfoMetrics`
  - Model: `AnalysisResultsSummary`
  - Model: `ComparisonMetrics`

**Requirements**:
- ✅ Type hints
- ✅ Validation
- ✅ Nested model support

---

## Week 4: Polish & Production Readiness (P2/P3)

### Task 4.1: Error Recovery and Retry Logic
**Type**: Backend | **Effort**: 1 day | **Priority**: P2

**Description**: Implement automatic retry for transient failures.

**Deliverables**:
- [ ] Utility: `shared/utilities/retry_utils.py` (50-100 LOC)
  - Decorator: `@retry(max_attempts=3, backoff_factor=2)`
  - Function: `exponential_backoff()` - Calculate delay between retries

**Requirements**:
- ✅ Transient errors (connection, temp file lock): Retry
- ✅ Validation errors (missing file): Fail immediately
- ✅ Exponential backoff: 1s → 2s → 4s
- ✅ Max 3 attempts

**Acceptance Criteria**:
- Retry logic works for mock failures
- Exponential backoff correct
- Max attempts enforced

---

### Task 4.2: Integration Tests - End-to-End Workflows
**Type**: Testing | **Effort**: 1.5 days | **Priority**: P2 | **Depends on**: All Week 1-3

**Description**: E2E tests covering complete Phase 2 workflows.

**Deliverables**:
- [ ] File created: `tests/integration/test_phase_2_workflows.py` (300-400 LOC)
  - Test: Scenario → Case → Simulation → Analysis (Full workflow)
  - Test: Batch simulations (10 scenarios, batch execution)
  - Test: Analysis batch (run 4 analysis types)
  - Test: Error recovery (failed simulation → retry)

**Requirements**:
- ✅ Use real case/scenario data (or comprehensive mocks)
- ✅ Test all 4 analysis types
- ✅ Verify metadata linkage
- ✅ Check result files exist

**Acceptance Criteria**:
- All workflows complete successfully
- Metadata chain intact
- Result files present and valid

---

### Task 4.3: E2E Tests - User Workflows (Playwright)
**Type**: Testing | **Effort**: 1.5 days | **Priority**: P2 | **Depends on**: 2.5, 3.3

**Description**: Playwright E2E tests for Phase 2 UI workflows.

**Deliverables**:
- [ ] File created: `tests/e2e/test_scenario_to_analysis.spec.js` (200-300 LOC)
  - Test: Create case from scenario
  - Test: Create simulation from case
  - Test: Start batch simulations
  - Test: Monitor progress
  - Test: View analysis results

**Requirements**:
- ✅ Use production-like test data (real scenarios)
- ✅ Wait for actual API responses (not hardcoded timeouts)
- ✅ Verify UI updates in real-time
- ✅ Test error scenarios

**Acceptance Criteria**:
- All tests pass
- UI responsive throughout workflow
- Error messages display correctly

---

### Task 4.4: Performance Testing
**Type**: Testing | **Effort**: 1 day | **Priority**: P2

**Description**: Verify system performance under load.

**Tests Required**:
- Load test: 50 concurrent simulations
- Load test: 100 analysis tasks
- Benchmark: API response times
- Benchmark: Frontend update latency

**Acceptance Criteria**:
- 50 concurrent sims complete without errors
- API responses < 1 second
- Frontend updates smooth (no jank)

---

### Task 4.5: Documentation
**Type**: Documentation | **Effort**: 1.5 days | **Priority**: P2

**Description**: Write comprehensive documentation for Phase 2.

**Deliverables**:
- [ ] File created: `docs/PHASE_2_USER_GUIDE.md`
  - User workflow: Create case → Simulation → Analysis
  - Screenshots and step-by-step instructions
  - Troubleshooting guide

- [ ] File created: `docs/PHASE_2_API_REFERENCE.md`
  - All new endpoints documented
  - Request/response examples
  - Error codes and meanings

- [ ] File created: `docs/PHASE_2_DEVELOPER_GUIDE.md`
  - Architecture overview
  - How to extend services
  - Testing guidelines

- [ ] File update: `CLAUDE.md`
  - Add AD-12, AD-13, AD-14 to architecture section
  - Document new patterns

**Requirements**:
- ✅ Clear examples
- ✅ Troubleshooting section
- ✅ Architecture diagrams

---

### Task 4.6: Code Review Checklist & Quality
**Type**: Quality Assurance | **Effort**: 1 day | **Priority**: P2

**Description**: Final code review and quality checks.

**Checklist**:
- [ ] No `print()` statements (use `logger`)
- [ ] All functions have docstrings
- [ ] Type hints on all functions
- [ ] No circular dependencies
- [ ] Metadata isolation enforced
- [ ] Tests pass (unit + integration + E2E)
- [ ] Code coverage > 80%
- [ ] No hardcoded values
- [ ] Error handling complete
- [ ] Performance acceptable

**Acceptance Criteria**:
- All checklist items passed
- Code ready for production

---

## Task Dependencies Map

```
Week 1 (Foundation):
1.1 → 1.2 → 1.3
1.4 (parallel with 1.1)
1.5 (parallel with 1.1, depends on 1.4)
1.6 (depends on 1.1-1.5)

Week 2 (Execution):
2.1 (depends on 1.4)
2.2 (depends on 1.4, 2.1)
2.3 (depends on 2.1)
2.4 (no dependencies)
2.5 (depends on 2.4, 2.1)
2.6 (depends on 2.1)

Week 3 (Results):
3.1 (depends on 1.1, 2.1)
3.2 (depends on 3.1)
3.3 (depends on 2.4, 3.1)
3.4 (depends on 3.1)

Week 4 (Polish):
4.1 (independent)
4.2 (depends on all Week 1-3)
4.3 (depends on 2.5, 3.3)
4.4 (depends on all Week 1-3)
4.5 (can be parallel)
4.6 (final, depends on all)
```

---

## Parallelization Strategy

**Can run in parallel** (separate team members):
- Week 1: 1.4 + 1.1 (while someone writes tests 1.6)
- Week 2: 2.4 (frontend) + 2.1/2.2/2.3 (backend)
- Week 3: 3.1/3.2 (backend) + 3.3 (frontend)
- Week 4: Documentation + QA in parallel

**Suggested allocation for 2-person team**:
- Person A: Backend services (1.1-1.6, 2.1-2.3, 3.1-3.2, 4.1-4.6)
- Person B: Frontend + Testing (2.4-2.5, 3.3, 3.4, 4.2-4.4)

---

## Validation Criteria by Task

| Task | Validation Method |
|------|-------------------|
| 1.1-1.5 | Unit tests pass |
| 1.6 | All tests pass, coverage > 80% |
| 2.1 | Unit tests + manual batch execution |
| 2.2 | Unit tests + SUMO successfully runs |
| 2.3 | API endpoints return correct responses |
| 2.4-2.5 | Manual testing + no console errors |
| 2.6 | Model validation tests pass |
| 3.1-3.2 | Results computed correctly |
| 3.3 | Visualizations render correctly |
| 3.4 | Model tests pass |
| 4.1 | Retry logic works on mock failures |
| 4.2 | Full E2E test flows complete successfully |
| 4.3 | Playwright tests pass |
| 4.4 | Performance benchmarks met |
| 4.5 | Documentation is clear and complete |
| 4.6 | Code review checklist 100% |

---

**Task List Complete. Ready for sprint planning.**
