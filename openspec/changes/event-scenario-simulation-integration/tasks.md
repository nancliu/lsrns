# Phase 2: Event Scenario Simulation Integration - Task List

**Total Effort**: 3-4 weeks (2-person team)
**Current Status**: Ready for implementation
**Last Updated**: 2025-11-12
**Design Clarifications**: See DESIGN_CLARIFICATIONS.md for Q1-Q14 decisions

---

## Week 1: Foundation (P0 - Blocking Everything Else)

### Task 1.0: Metadata Version Support (NEW - Q5, Q6, Q7)
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Blocks**: All other tasks

**Description**: Add metadata versioning support to enable backward compatibility.

**Design Decision**: Q5, Q6, Q7 - Dual schema support (v1.0 implicit, v2.0 explicit)

**Deliverables**:
- [x] Extend `api/services/base_service.py` or `base_metadata_service.py`:
  - Method: `detect_metadata_version(metadata: Dict) -> str` - Returns "1.0" or "2.0"
  - Method: `is_event_scenario_case(metadata: Dict) -> bool` - Checks for source_scenario
  - Method: `load_metadata_safely(metadata_file: Path) -> Dict` - Null-safe loading
  - Method: `get_simulation_source_type(metadata: Dict) -> str` - Source detection

**Requirements**:
- ✅ Detect version 1.0 (no metadata_version field) implicitly
- ✅ Detect version 2.0 (has metadata_version field) explicitly
- ✅ Null-safe handling of source_scenario field
- ✅ Backward compatible with existing cases and simulations

**Acceptance Criteria**:
- Old cases (v1.0) load without errors
- New cases (v2.0) load with source_scenario field
- Services adapt behavior based on detected version
- No breaking changes to existing code

**Tests Required**:
- Unit test: Detect v1.0 metadata (no metadata_version field)
- Unit test: Detect v2.0 metadata (has metadata_version field)
- Unit test: Null-safe read of source_scenario (v1.0 case)
- Integration test: Load existing OD case, verify no errors

**Files Modified**:
- `api/services/base_metadata_service.py` or `api/services/base_service.py`

---

### Task 1.1: SimulationOrchestrator - Core Implementation (NEW - Q1, Q2, Q3)
**Type**: Backend | **Effort**: 2 days | **Priority**: P0 | **Blocks**: 1.2, 2.x

**Description**: Create orchestration layer that detects simulation source and delegates to appropriate services.

**Design Decision**: Q1-C - Orchestration layer with delegation pattern; Q2 - Reuse BatchSimulationScheduler

**Deliverables**:
- [x] File created: `api/services/simulation_orchestrator.py` (290 LOC)
  - Class: `SimulationOrchestrator`
  - Methods:
    - `batch_start_simulations()` - Unified batch execution interface
    - `_detect_simulation_source()` - Source detection (Q3 backward compat, uses BaseMetadataService)
    - `_batch_start_event_scenarios()` - Delegate to BatchSimulationScheduler
    - `_batch_start_od_simulations()` - Delegate to SimulationService
    - `get_batch_execution_status()` - Status monitoring
    - `cancel_batch_simulations()` - Cancellation support

**Requirements**:
- ✅ Detect source from metadata version and source_scenario field (Q3)
- ✅ Delegate event-scenario → BatchSimulationScheduler (Q2 reuse)
- ✅ Delegate OD extraction → SimulationService (unchanged)
- ✅ Delegate control-plan → BatchOptimizationService (unchanged)
- ✅ Preserve existing workflows (PRINCIPLE-INTEGRATION-002)

**Acceptance Criteria**:
- Correctly detects "event-scenario", "od-extraction", "control-plan" sources
- Event-scenario simulations use BatchSimulationScheduler
- Existing OD and control-plan workflows unaffected
- Returns unified BatchExecutionResponse

**Tests Required**:
- Unit test: Detect event-scenario source (v2.0 metadata)
- Unit test: Detect OD extraction source (v1.0 metadata, no plan_id)
- Unit test: Detect control-plan source (has plan_id)
- Integration test: Batch start event-scenarios, verify delegation

**Files Modified**:
- `api/services/__init__.py` - Add SimulationOrchestrator export

---

### Task 1.2: Analysis Orchestration Service - Adapter Layer (UPDATED - Q8, Q9)
**Type**: Backend | **Effort**: 2 days | **Priority**: P0 | **Blocks**: 2.x, 3.x

**Description**: Create adapter layer that converts event-scenario structure to batch analysis format and reuses existing analyzers.

**Design Decision**: Q8 - Do NOT use OD analysis services; Q9 - Create adapter, do NOT modify existing services

**Deliverables**:
- [x] File exists: `api/services/analysis_orchestration_service.py` (already implemented)
  - Class: `AnalysisOrchestrationService`
  - Methods:
    - `create_analysis_batch()` - Queue analysis tasks
    - `get_analysis_progress()` - Real-time monitoring
    - `_validate_simulations()` - Validate completed simulations
    - Uses `BatchResultAnalyzer` from shared layer (adapter pattern)

**Requirements**:
- ✅ Reuse SummaryAnalyzer (shared layer, unchanged) - Q9
- ✅ Reuse EdgeDataAnalyzer (shared layer, unchanged) - Q9
- ✅ Do NOT use OD analysis services (accuracy/mechanism/performance/edgedata_service) - Q8
- ✅ Adapter converts event-scenario dir structure to batch format
- ✅ Store results with scenario lineage metadata
- ✅ Isolation: Never modify case or simulation metadata

**Acceptance Criteria**:
- All methods have docstrings and type hints
- Adapter successfully converts event-scenario structure to batch format
- SummaryAnalyzer and EdgeDataAnalyzer called without modifications
- Results stored with source_scenario_id metadata
- OD analysis services NOT called

**Tests Required**:
- Unit test: Convert event-scenario dir structure to batch format
- Unit test: Call SummaryAnalyzer with converted data
- Unit test: Call EdgeDataAnalyzer with converted data
- Unit test: Verify analysis results have scenario lineage
- Integration test: Run analysis batch on 5 event-scenario simulations

**Files Modified**:
- `api/services/__init__.py` - Add AnalysisOrchestrationService export

---

### Task 1.3: Case Creation from Scenario Endpoint (NEW - Q4)
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.0

**Description**: Create separate endpoint for creating cases from event scenarios (not modifying existing case creation).

**Design Decision**: Q4 - Two separate endpoints (business semantics differ)

**Deliverables**:
- [ ] Extend `api/services/case_service.py`:
  - Method: `create_case_from_scenario()` - Create case with metadata v2.0
  - Ensure existing `create_case()` method unchanged
- [ ] Extend `api/routes/case_routes.py`:
  - Route: `POST /api/v1/case/create-from-scenario` (NEW)
  - Ensure existing `POST /api/v1/case/create` unchanged

**Requirements**:
- ✅ Create case with metadata_version: "2.0"
- ✅ Include source_scenario field in metadata
- ✅ Do NOT modify existing `/api/v1/case/create` endpoint
- ✅ Do NOT modify existing `create_case()` method signature
- ✅ Backward compatible with existing OD extraction workflow

**Acceptance Criteria**:
- New endpoint creates v2.0 cases with source_scenario
- Existing endpoint creates v1.0 cases (unchanged behavior)
- Both endpoints work simultaneously
- No breaking changes to existing OD workflow

**Tests Required**:
- Unit test: Create case from scenario, verify metadata v2.0
- Unit test: Existing create case endpoint still works (v1.0)
- Integration test: Create both types, verify isolation

**Files Modified**:
- `api/services/case_service.py`
- `api/routes/case_routes.py`
- `api/models/requests/case_requests.py` (add EventScenarioCaseRequest)

---

### Task 1.5: Analysis Orchestration API Routes
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.2

**Description**: Create API endpoints for analysis orchestration (adapter layer).

**Deliverables**:
- [ ] File created or extend: `api/routes/analysis_routes.py` (add new routes)
  - Route: `POST /api/v1/analysis/run-batch` - Create analysis batch (NEW)
  - Route: `GET /api/v1/analysis/batch-progress/{batch_id}` - Monitor progress (NEW)
  - Ensure existing analysis routes unchanged

**Requirements**:
- ✅ Request validation using Pydantic models
- ✅ Error handling with descriptive messages
- ✅ Do NOT modify existing analysis routes
- ✅ Logging for all operations

**Acceptance Criteria**:
- Endpoints return proper HTTP status codes
- Error responses include `error_code` and `message` fields
- Request validation catches invalid input
- Existing analysis endpoints (if any) still work

**Tests Required**:
- Unit test: POST /api/v1/analysis/run-batch with valid request
- Unit test: GET /api/v1/analysis/batch-progress/{batch_id}
- Unit test: Invalid request returns 400

**Files Modified**:
- `api/routes/__init__.py` - Register new routes
- `api/routes/analysis_routes.py` - Add new routes

---

### Task 1.6: Data Models for Analysis Orchestration
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

### Task 2.1: SUMO Configuration with Relative Paths (UPDATED - Q12)
**Type**: Backend | **Effort**: 1 day | **Priority**: P1 | **Depends on**: 1.0

**Description**: Generate SUMO `.sumocfg` files with portable relative paths (AD-13).

**Design Decision**: Q12 - Metadata stores paths relative to project root (source of truth), sumocfg uses paths relative to sumocfg location

**Deliverables**:
- [x] File update: `shared/utilities/sumo_utils.py`
  - New function: `generate_sumocfg_with_relative_paths()`
    - Input: case_id, simulation_id, metadata paths (relative to project root)
    - Output: Path to generated sumocfg file
    - Process:
      1. Read paths from metadata (relative to project root)
      2. Convert to relative paths from sumocfg location
      3. Generate XML with relative paths
      4. Validate paths resolve correctly
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
- [x] File update: `api/routes/simulation_routes.py`
  - Route: `POST /api/v1/simulation/batch-start` - Start batch
  - Route: `GET /api/v1/simulation/batch-status/{batch_id}` - Monitor progress
  - Route: `POST /api/v1/simulation/batch-cancel` - Cancel batch

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
- [x] File created: `frontend/components/shared-utils.js` (350 LOC)
  - Function: `formatDate()` - Format datetime to locale string
  - Function: `formatTime()` - Format seconds to HH:MM:SS
  - Function: `getStatusBadgeClass()` - CSS class for status badge
  - Function: `delay()` - Promise-based delay
  - Function: `parseQuery()` - Parse URL query parameters
  - Function: `getColorForStatus()` - Color mapping for status

- [x] File created: `frontend/components/api-client.js` (400 LOC)
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
- [x] File created: `frontend/components/simulation-monitor.js` (480 LOC)
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
- [x] File update: `api/models/requests/batch_simulation_requests.py`
  - Model: `BatchSimulationStartRequest`
  - Model: `BatchSimulationCancelRequest`

- [x] File update: `api/models/responses/batch_simulation_responses.py`
  - Model: `SimulationProgressInfo`
  - Model: `BatchSimulationStartResponse`
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
- [x] File created: `api/services/analysis_results_service.py` (~966 LOC, all TODO items completed)
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
- [x] File update: `api/routes/analysis_routes.py` (+140 LOC)
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
- [x] File created: `frontend/components/analysis-results.js` (~531 LOC)
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
- [x] File created: `api/models/responses/analysis_results_responses.py` (~359 LOC)
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

## Phase 2.5: Frontend Integration & Workflow Implementation (P1 - CRITICAL)

### Task 2.7: Workflow Design & Page Linking (NEW)
**Type**: Design | **Effort**: 1 day | **Priority**: P0 | **Blocks**: 2.8-2.10

**Description**: Design and document the complete workflow connecting scenario browser → case management → simulation monitoring → analysis viewer.

**Deliverables**:
- [x] File created: `openspec/changes/event-scenario-simulation-integration/WORKFLOW_DESIGN.md`
  - Complete workflow diagram and page relationships
  - Design decisions (Q1-Q5) documented
  - Data flow and API call sequences
  - Implementation priority and sequence

**Key Design Decisions**:
- Q1: Create case button in scenario_browser.html (not case management page)
- Q2: Use Tab design for case-simulation-center.html (Cases | Monitoring | Batch History)
- Q3: Backend API for scenario-based case filtering
- Q4: Auto-run analysis when all simulations complete
- Q5: Reuse batch analysis tools via AnalysisOrchestrationService

**Acceptance Criteria**:
- [x] Three-page workflow documented
- [x] All page transitions mapped
- [x] API call sequences defined
- [x] Design decisions justified

---

### Task 2.8: Scenario Browser - Create Case Integration (NEW)
**Type**: Frontend | **Effort**: 1.5 days | **Priority**: P0 | **Depends on**: 2.7

**Description**: Add "Create Case" button and modal to scenario_browser.html with proper form validation and API integration.

**Deliverables**:
- [ ] Update `frontend/scenarios/scenario_browser.html`:
  - Add [创建案例] button to scenario table row
  - Create modal with form:
    - scenario_id (read-only, from selected scenario)
    - event_type (read-only)
    - control_strategy (read-only)
    - simulation_duration_hours (input, optional)
    - random_seed (input, optional)
    - output_config (checkbox group)
  - Form validation before submit
  - Submit to POST /api/v1/case/create-from-scenario
  - Success: navigate to case-simulation-center.html?case_id={case_id}

**Requirements**:
- ✅ Pre-fill scenario data in modal
- ✅ Support batch scenario selection + create multiple cases
- ✅ Validation: duration_hours must be 1-24 if provided
- ✅ Handle API errors gracefully (alert + retry)
- ✅ Update created case count in stats

**Tests Required**:
- Manual: Create case from scenario, verify API call
- Manual: Create multiple cases from batch selection
- Manual: Form validation (invalid duration)

---

### Task 2.9: Case Management - Case List & Filtering (NEW)
**Type**: Frontend | **Effort**: 2 days | **Priority**: P0 | **Depends on**: 2.8

**Description**: Implement Tab 1 of case-simulation-center.html with case list, filtering, and scenario-based selection.

**Deliverables**:
- [ ] Implement `frontend/scenarios/case-simulation-center.html` Tab 1:

  **Case List Display**:
  - Fetch from GET /api/v1/case/list with filters:
    - status: all|running|completed|failed
    - source_scenario_id: optional filter
    - search: case_id or scenario_id

  **Table Columns**:
  - Case ID | Source Scenario | Status | Simulations | Created At | Actions

  **Actions Column**:
  - [查看详情] → Show simulations for this case
  - [重新仿真] → Re-run failed simulations
  - [批量仿真] → Batch start all pending simulations

  **Statistics**:
  - Total cases | Running | Completed | Failed
  - Auto-update when new cases created or simulations change

  **Filter Section**:
  - Status dropdown (All|Running|Completed|Failed)
  - Source Scenario dropdown (populated from cases)
  - Search box (case_id or scenario_id)
  - Apply filter button

**Requirements**:
- ✅ Real-time case list fetching
- ✅ Support scenario-based filtering
- ✅ Status filtering
- ✅ Search functionality
- ✅ Pagination (if >50 cases)

**Tests Required**:
- Manual: Load case list, verify all columns
- Manual: Filter by status
- Manual: Filter by scenario
- Manual: Search by case_id

---

### Task 2.10: Case Management - Simulation Monitoring (NEW)
**Type**: Frontend | **Effort**: 2 days | **Priority**: P0 | **Depends on**: 2.4, 2.8

**Description**: Implement Tab 2 of case-simulation-center.html with real-time simulation monitoring using SimulationMonitor component.

**Deliverables**:
- [ ] Implement `frontend/scenarios/case-simulation-center.html` Tab 2:

  **Batch Progress Section**:
  - Display current batch info (if running):
    - Batch ID
    - Total simulations | Completed | Running | Failed | Queued
    - Overall progress bar (%)
    - ETA for completion

  **Batch Actions**:
  - [开始批量仿真] (launch modal to select cases)
  - [取消仿真] (cancel running batch)
  - [暂停仿真] (pause, not cancel)

  **Simulation Table**:
  - Use SimulationMonitor component
  - Columns: SIM ID | Case | Status | Progress | Elapsed | ETA | Logs
  - Real-time polling (5-second interval)
  - Progress bars with smooth animation
  - Log viewer (expandable, last 500 lines)
  - Auto-stop polling when batch completes

  **Start Batch Simulation Flow**:
  ```javascript
  async function startBatchSimulations() {
      // 1. Show modal for case/simulation selection
      const selected = await showSimulationSelectionModal();

      // 2. Call API
      const response = await api.request('/simulation/batch-start', {
          method: 'POST',
          body: JSON.stringify({
              simulation_ids: selected.simulation_ids,
              parallel_workers: 4,
              auto_run_analysis: true
          })
      });

      // 3. Save batch_id to sessionStorage
      sessionStorage.setItem('current_batch_id', response.data.batch_id);

      // 4. Start monitoring
      const monitor = new SimulationMonitor('simulationContainer', api);
      await monitor.startMonitoring(response.data.batch_id, 'event-scenario');
  }
  ```

**Requirements**:
- ✅ Real-time progress updates (5-second polling)
- ✅ Accurate progress calculation
- ✅ ETA estimation
- ✅ Log viewer with tail -f behavior
- ✅ Auto-stop when completed
- ✅ Error handling (retry on API failure)
- ✅ Auto-start analysis when all sims complete (if auto_run_analysis=true)

**Tests Required**:
- Manual: Start batch, verify progress updates
- Manual: Verify log viewer shows last 500 lines
- Manual: Verify auto-stop when completed
- Manual: Verify auto-start analysis call

---

### Task 2.11: Case Management - Batch History (NEW)
**Type**: Frontend | **Effort**: 1 day | **Priority**: P1 | **Depends on**: 2.10

**Description**: Implement Tab 3 of case-simulation-center.html with batch history and results.

**Deliverables**:
- [ ] Implement `frontend/scenarios/case-simulation-center.html` Tab 3:

  **Batch History Table**:
  - Columns: Batch ID | Time | Cases | Simulations | Success Rate | Actions
  - Fetch from GET /api/v1/simulation/batch-list?status=completed
  - Sort by creation time (newest first)

  **Actions**:
  - [分析结果] → Jump to analysis_viewer.html?batch_id={batch_id}
  - [导出] → Export batch results (CSV/JSON)
  - [删除] → Delete batch history

**Requirements**:
- ✅ Load completed batches
- ✅ Navigate to analysis viewer
- ✅ Export functionality

---

### Task 2.12: Analysis Viewer - Progress Monitoring (NEW)
**Type**: Frontend | **Effort**: 1.5 days | **Priority**: P0 | **Depends on**: 3.3

**Description**: Implement real-time analysis progress monitoring in analysis_viewer.html.

**Deliverables**:
- [ ] Update `frontend/scenarios/analysis_viewer.html`:

  **Get batch_id from URL**:
  - Extract from query param: ?batch_id={batch_id}
  - Or from URL param: ?case_id={case_id}

  **Auto-start Analysis if needed**:
  ```javascript
  async function startAnalysisIfNeeded() {
      // Check if analysis already running or completed
      const status = await api.request(`/analysis/batch-progress/${batchId}`);

      if (!status.data.batch_id) {
          // No analysis yet, start one
          const response = await api.request('/analysis/run-batch', {
              method: 'POST',
              body: JSON.stringify({
                  simulation_ids: simIds,
                  case_id: caseId,
                  baseline_scenario_id: baselineScenarioId,
                  analysis_focus: ['edgedata', 'tripinfo', 'performance'],
                  parallel_workers: 4
              })
          });

          batchId = response.data.batch_id;
      }
  }
  ```

  **Display Progress**:
  - Progress bar: [========>     ] 65%
  - Task count: 104/160 completed
  - Current task: sim_123 EdgeData (progress: 72%)
  - ETA: 2025-11-13 16:45:00
  - Polling interval: 5 seconds
  - Auto-load results when completed

**Requirements**:
- ✅ Auto-start analysis if not running
- ✅ Real-time progress display
- ✅ Accurate task counting
- ✅ ETA calculation
- ✅ Auto-transition to results when done

---

### Task 2.13: Analysis Viewer - Results Display (NEW)
**Type**: Frontend | **Effort**: 1.5 days | **Priority**: P0 | **Depends on**: 3.3

**Description**: Load and display analysis results using AnalysisResultsDashboard component.

**Deliverables**:
- [ ] Update `frontend/scenarios/analysis_viewer.html`:

  **Load Results**:
  ```javascript
  async function loadAnalysisResults() {
      const results = await api.request(`/analysis/results/${batchId}`);

      const dashboard = new AnalysisResultsDashboard('analysisContainer', api);
      dashboard.render({
          edgedata: results.data.edgedata,
          tripinfo: results.data.tripinfo,
          performance: results.data.performance,
          comparison: results.data.comparison
      });
  }
  ```

  **Tab Structure** (from component):
  - [概览] - Summary metrics
  - [路段分析] - EdgeData heat map
  - [对比分析] - Baseline vs event vs control
  - [详细指标] - All metrics table
  - [导出] - Download PDF/JSON

**Requirements**:
- ✅ Fetch results from API
- ✅ Render with AnalysisResultsDashboard
- ✅ Support all analysis types
- ✅ Export functionality

---

### Task 2.14: Backend - Case List API Enhancement (NEW)
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 2.9

**Description**: Add filtering support to case list API for scenario-based queries.

**Deliverables**:
- [ ] Update `api/routes/case_routes.py`:
  - Extend GET /api/v1/case/list to support:
    - status filter
    - source_scenario_id filter
    - search by case_id or scenario_id
    - pagination (limit, offset)

- [ ] Add new endpoint: GET /api/v1/case/list-by-scenario
  - Query: ?scenario_id=xxx
  - Returns all cases created from a specific scenario

**Requirements**:
- ✅ Backward compatible with existing endpoint
- ✅ Filter by status (created|running|completed|failed)
- ✅ Filter by source_scenario_id
- ✅ Full-text search
- ✅ Pagination support

**Tests Required**:
- Unit test: List cases by status
- Unit test: List cases by scenario
- Unit test: Search by case_id

---

### Task 2.15: Backend - Batch Start Simulation API (NEW - Verification)
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.1

**Description**: Verify and fix SimulationOrchestrator integration in batch-start route.

**Deliverables**:
- [ ] Update `api/routes/simulation_routes.py`:
  - Verify batch-start route uses SimulationOrchestrator
  - Ensure orchestrator.batch_start_simulations() is called
  - Pass auto_run_analysis parameter to orchestrator
  - Return proper BatchExecutionResponse

**Current Issue**:
- Routes exist but may not use new orchestrator
- Need to verify orchestrator delegation works

**Acceptance Criteria**:
- ✅ Route imports SimulationOrchestrator
- ✅ batch-start calls orchestrator.batch_start_simulations()
- ✅ auto_run_analysis parameter passed through
- ✅ Response includes batch_id and simulation_ids

---

### Task 2.16: Backend - Analysis Auto-Start Integration (NEW)
**Type**: Backend | **Effort**: 1 day | **Priority**: P0 | **Depends on**: 1.2, 2.15

**Description**: Implement auto-start analysis when all simulations complete.

**Deliverables**:
- [ ] Update `api/services/simulation_orchestrator.py`:
  - When batch completes (all simulations done):
    - Check if auto_run_analysis=true
    - Call AnalysisOrchestrationService.create_analysis_batch()
    - Return analysis_batch_id in response

  - Update response:
    ```python
    class BatchExecutionResponse:
        batch_id: str
        simulation_ids: List[str]
        analysis_batch_id: Optional[str] = None  # NEW
        status: str  # pending|running|completed
    ```

**Requirements**:
- ✅ Check auto_run_analysis flag
- ✅ Call analysis service when all sims done
- ✅ Pass simulation_ids to analysis service
- ✅ Return analysis_batch_id in response

---

---

**Updated Task List. Ready for integration phase.**
