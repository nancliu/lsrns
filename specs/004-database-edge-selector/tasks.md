# Implementation Tasks: Database-Driven Edge Selector (Phase 1B)

**Feature**: Database-Driven Edge Selector
**Branch**: `004-database-edge-selector`
**Status**: Ready for Implementation
**Generated**: 2025-10-20

---

## Quick Reference

**Total Tasks**: 46
**Estimated Duration**: 5-7 days
**MVP Scope**: Phase 1-4 (US1 basic filtering - 18 tasks)
**Parallelization Opportunities**: 32 parallelizable tasks (marked with [P])

### Task Count by Phase

- Phase 1: Setup (6 tasks)
- Phase 2: Foundational (3 tasks)
- Phase 3: US1 - Basic Filtering (9 tasks) ⭐ MVP
- Phase 4: US5 - Hierarchical Filtering (7 tasks)
- Phase 5: US2 - TEC Support (6 tasks)
- Phase 6: US3 - DHS Support (8 tasks - OPTIONAL)
- Phase 7: US4 - Visualization (7 tasks - OPTIONAL)

### User Story Priority Order

1. **P1 - US1**: Basic filtering API + frontend (MUST HAVE for MVP)
2. **P2 - US5**: Hierarchical filtering metadata endpoints (SHOULD HAVE)
3. **P2 - US2**: TEC entrance filtering (SHOULD HAVE)
4. **P3 - US3**: DHS emergency lane filtering (OPTIONAL - can defer)
5. **P4 - US4**: Network visualization (OPTIONAL - can defer)

---

## Implementation Strategy

### MVP-First Approach

**MVP = Phase 1-3 (US1 Basic Filtering)**
- Delivers core value: Multi-dimensional edge filtering
- Independently testable through API and frontend
- Enables immediate use for VSS control strategy selection
- **Estimated time**: 3 days

**Incremental Additions**:
- **+US5** (Hierarchical filtering): Adds route/section metadata for better UX (+ 1 day)
- **+US2** (TEC support): Adds entrance node filtering (+ 0.5 day)
- **+US3** (DHS support): Adds emergency lane detection (+ 1 day - OPTIONAL)
- **+US4** (Visualization): Adds Canvas network map (+ 1.5 days - OPTIONAL)

### Parallel Execution Strategy

**Within Each Phase**:
- Model creation tasks can run in parallel ([P] marked)
- Service and route implementations can overlap with model creation
- Frontend components independent from backend (after API contract defined)
- Test files can be created in parallel with implementation

**Example - Phase 3 (US1) Parallelization**:
```
Time Slot 1 (Parallel):
  - T007 [P]: Create EdgeQueryRequest model
  - T008 [P]: Create EdgeQueryResponse models
  - T009 [P]: Create control_strategy_service.py

Time Slot 2 (Parallel):
  - T010 [P]: Implement query_edges service method
  - T011 [P]: Create control_routes.py

Time Slot 3 (Sequential):
  - T012: Implement /query endpoint (depends on T007-T011)

Time Slot 4 (Parallel):
  - T013 [P]: Create edge_selector.html
  - T014 [P]: Create edge_filter.js

Time Slot 5 (Sequential):
  - T015: Integrate frontend with API (depends on T012-T014)
```

**Result**: 15 task steps → 5 time slots (3x speedup)

---

## Phase 1: Setup

**Goal**: Initialize project infrastructure for control domain

**Prerequisites**: Database indexes are assumed pre-existing (route_code, section_code, junction fields from Phase 1A or DBA setup)

**Tasks**:

- [x] T001 Create API models directory structure: `api/models/requests/` and `api/models/responses/`
- [x] T002 Create frontend control directory structure: `frontend/control/` and `frontend/control/js/`
- [x] T003 Create tests directory structure: `tests/unit/` and `tests/integration/`
- [x] T004 [P] Create cache_utils.py in shared/utilities/ for TTL caching mechanism
- [x] T005 [P] Update connection.py to use SQLAlchemy connection pooling (pool_size=10, max_overflow=5)
- [x] T006 [P] Configure structured logging (JSON-compatible format) in api/services/control_strategy_service.py and implement log events per FR-045 to FR-049: query parameters, result counts, execution time (ms), error types, slow query warnings (>1500ms threshold)

**Dependencies**: None (all can start immediately)

**Note**: Database indexes on route_code, section_code, and junction fields are assumed pre-existing from Phase 1A or DBA setup

**Parallel Opportunities**: T004, T005, T006 can run in parallel after directory structure (T001-T003)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Establish shared infrastructure required by all user stories

**Tasks**:

- [x] T007 [P] Create EdgeQueryRequest Pydantic model in api/models/requests/edge_query_request.py with validators for stake/length ranges, route_direction, node_types
- [x] T008 [P] Create EdgeInfoResponse, EdgeQueryResponse, RouteInfo, SectionInfo, DemonstrationInfo Pydantic models in api/models/responses/edge_query_response.py
- [x] T009 [P] Create control_strategy_service.py in api/services/ with base structure and retry logic decorator

**Dependencies**: Phase 1 complete

**Parallel Opportunities**: All 3 tasks are independent and can run in parallel

**Validation**:
- T007: EdgeQueryRequest validates invalid stake ranges, route_direction enums, node_type enums
- T008: EdgeInfoResponse.from_edge_info() correctly converts EdgeInfo dataclass
- T009: Service module imports successfully with correct logging configuration
- T009 (Retry Logic): Test database connection failure scenarios to validate FR-050-FR-053 retry mechanism - verify exponential backoff (1s, 2s delays), maximum 2 retry attempts, connection timeout handling (30s), and appropriate error logging

---

## Phase 3: User Story 1 - Basic Filtering (Priority: P1) ⭐ MVP

**Goal**: Enable traffic control engineers to filter road segments for VSS control strategy using multi-dimensional criteria

**Independent Test**: Submit filter criteria (route_codes=G4202, min_lanes=3, route_direction=clockwise) through API and verify returned edges match all conditions within 2 seconds

**User Story Reference**: spec.md lines 9-26

**Tasks**:

- [x] T010 [P] [US1] Implement query_edges_with_filters() service method in api/services/control_strategy_service.py that calls shared/data_access/edge_query.query_edges_with_filters()
- [x] T011 [P] [US1] Create control_routes.py in api/routes/ with APIRouter for /api/v1/control prefix
- [x] T012 [US1] Implement GET /api/v1/control/edges/query endpoint in api/routes/control_routes.py with EdgeQueryRequest validation
- [x] T013 [P] [US1] Create edge_selector.html in frontend/control/ with filter form for 9 filter dimensions (route, section, stake range, length, lanes, direction, node type, demonstration, gantry)
- [x] T014 [P] [US1] Create edge_filter.js in frontend/control/js/ with queryEdges() function and filter parameter handling
- [x] T015 [US1] Implement results table display in edge_selector.html showing edge_id, route_code, section_code, stake_range, length, lanes, node_type, gantry_count with checkboxes for selection
- [x] T016 [US1] Add loading state and error handling to edge_filter.js for API query operations
- [x] T017 [P] [US1] Create test_control_api.py in tests/integration/ with test_query_edges_basic() and test_query_edges_with_filters()
- [x] T018 [US1] Register control_routes.py in api/main.py with app.include_router()

**Dependencies**:
- T010-T012 depend on T007-T009 (models and service base)
- T013-T016 can start after T012 (API contract defined)
- T017 can start after T007 (models defined)
- T018 depends on T011-T012 (routes created)

**Parallel Opportunities**:
- T010, T011 can run in parallel (different files)
- T013, T014 can run in parallel (different files)
- T017 can run in parallel with T013-T016 (independent test file)

**Test Scenarios for T017**:
```python
def test_query_edges_basic():
    response = client.get("/api/v1/control/edges/query?route_codes=G4202")
    assert response.status_code == 200
    assert response.json()["total_count"] > 0

def test_query_edges_with_filters():
    response = client.get("/api/v1/control/edges/query?route_codes=G4202&min_lanes=3&route_direction=clockwise")
    data = response.json()
    assert all(edge["route_code"] == "G4202" for edge in data["edges"])
    assert all(edge["num_lanes"] >= 3 for edge in data["edges"])
    assert all(edge["route_direction"] == "clockwise" for edge in data["edges"])

def test_query_edges_invalid_stake_range():
    response = client.get("/api/v1/control/edges/query?min_stake=50&max_stake=10")
    assert response.status_code == 400
    assert "max_stake must be >= min_stake" in response.json()["detail"]
```

**Acceptance Criteria (from spec)**:
- ✅ System returns 10-20 road segments matching all criteria within 2 seconds
- ✅ Results table displays edge_id, route_code, section_code, stake range, length, lane count, node type, gantry count
- ✅ "Only segments with gantries" filter (with_gantry=true) returns only edges with gantry_count > 0

---

## Phase 4: User Story 5 - Hierarchical Filtering (Priority: P2)

**Goal**: Enable hierarchical filtering workflow (Route → Section → Edge) to efficiently narrow down segment selection

**Independent Test**: Query available sections for route G4202, verify sections returned with edge counts, then filter edges within section G4202001 and verify result count reduces from 621 to <20

**User Story Reference**: spec.md lines 85-99

**Tasks**:

- [x] T019 [P] [US5] Implement get_available_routes() service method in api/services/control_strategy_service.py with cachetools TTLCache(maxsize=100, ttl=300)
- [x] T020 [P] [US5] Implement get_available_sections() service method in api/services/control_strategy_service.py with cachetools TTLCache and optional route_code filter
- [x] T021 [P] [US5] Implement get_demonstration_info() service method in api/services/control_strategy_service.py with cachetools TTLCache
- [x] T022 [US5] Implement GET /api/v1/control/edges/routes endpoint in api/routes/control_strategy_routes.py returning List[Dict]
- [x] T023 [US5] Implement GET /api/v1/control/edges/sections endpoint in api/routes/control_strategy_routes.py with optional route_code query parameter
- [x] T024 [US5] Implement GET /api/v1/control/edges/demonstrations endpoint in api/routes/control_strategy_routes.py
- [x] T025 [US5] Add hierarchical dropdowns to edge_selector.html: route dropdown that triggers section dropdown population, section dropdown that filters by selected route

**Dependencies**:
- T019-T021 depend on T009 (service base structure)
- T022-T024 depend on T008 (response models), T019-T021 (service methods)
- T025 depends on T022-T024 (API endpoints) and T013-T014 (frontend base)

**Parallel Opportunities**:
- T019, T020, T021 can run in parallel (different service methods)
- T022, T023, T024 can run in parallel after T019-T021 (different endpoints)

**Test Scenarios**:
```python
def test_get_routes():
    response = client.get("/api/v1/control/edges/routes")
    assert response.status_code == 200
    routes = response.json()
    assert isinstance(routes, list)
    assert "G4202" in routes

def test_get_sections_filtered_by_route():
    response = client.get("/api/v1/control/edges/sections?route_code=G4202")
    assert response.status_code == 200
    sections = response.json()
    assert all(s["route_code"] == "G4202" for s in sections)
    assert any(s["section_code"] == "G4202001" for s in sections)
```

**Acceptance Criteria (from spec)**:
- ✅ System returns sections "G4202001" (621 edges) and "G4202002" (577 edges) with stake ranges
- ✅ Result count reduces from 621 to under 20 segments when additional filters applied within section
- ✅ Changing section maintains other filter criteria and updates results

---

## Phase 5: User Story 2 - TEC Support (Priority: P2)

**Goal**: Enable identification of entrance ramp segments for Toll Entrance Control (TEC) strategies

**Independent Test**: Query edges with route_codes=G4202, node_types=entrance and verify all returned segments are entrance ramps

**User Story Reference**: spec.md lines 29-44

**Tasks**:

- [x] T026 [P] [US2] Add node_types dropdown to edge_selector.html with options: diverging, merging, entrance, exit (multiple selection)
- [x] T027 [P] [US2] Add demonstration_ids dropdown to edge_selector.html populated from /api/v1/control/edges/demonstrations endpoint
- [ ] T028 [P] [US2] Create test_tec_scenario() integration test in tests/integration/test_control_api.py verifying entrance node filtering (DEFERRED - testing optional for initial delivery)
- [x] T029 [US2] Document TEC filtering workflow in quickstart.md with example: filter route G4202 + node_type entrance (ALREADY DOCUMENTED)
- [x] T030 [P] [US2] Add validation in EdgeQueryRequest for node_types to ensure values are in {diverging, merging, entrance, exit}
- [x] T031 [US2] Update edge_filter.js to handle multi-select node_types and demonstration_ids as comma-separated values

**Dependencies**:
- T026-T027 depend on T013 (frontend base), T024 (demonstrations endpoint)
- T028 can start after T012 (query endpoint)
- T029 can start anytime (documentation)
- T030 depends on T007 (EdgeQueryRequest model)
- T031 depends on T014 (edge_filter.js base), T026-T027 (UI controls)

**Parallel Opportunities**:
- T026, T027, T028 can run in parallel
- T029, T030 can run in parallel with T026-T028

**Test Scenarios**:
```python
def test_tec_scenario():
    # TEC: Filter entrance ramps on G4202
    response = client.get("/api/v1/control/edges/query?route_codes=G4202&node_types=entrance")
    data = response.json()
    assert all(edge["node_type"] == "entrance" for edge in data["edges"])
    assert data["total_count"] >= 10  # Expect multiple entrance ramps

def test_tec_with_demonstration():
    response = client.get("/api/v1/control/edges/query?demonstration_ids=5&node_types=entrance")
    data = response.json()
    assert all(edge["node_type"] == "entrance" for edge in data["edges"])
```

**Acceptance Criteria (from spec)**:
- ✅ System returns all entrance ramp segments for route G4202 when filtering with node_type=entrance
- ✅ Each segment shows connection to toll plaza or TAZ information when available
- ✅ Filtering by demonstration_id + entrance returns only entrance segments within that demonstration area

---

## Phase 6: User Story 3 - DHS Support (Priority: P3) - DEFERRED

**Goal**: Enable identification of mainroad segments with emergency lanes for Dynamic Hard Shoulder (DHS) strategies

**Independent Test**: Query edges with route_codes=G4202, min_lanes=4 and verify returned segments have potential emergency lanes based on lane count

**User Story Reference**: spec.md lines 47-62

**Status**: ⏸️ **DEFERRED** (2025-10-21)

**Note**: This phase has been DEFERRED based on user decision. Current DHS support using min_lanes≥4 inference is sufficient for most use cases. Full emergency lane detection with sim_network_lanes table integration can be implemented later if needed (estimated 1 day, 8 tasks).

**Current Implementation**:
- ✅ DHS threshold updated from ≥5 to ≥4 lanes
- ✅ Frontend hint显示 "DHS≥4"
- ✅ Documentation updated (edge_selector_database_design.md, quickstart.md)
- ✅ Inference-based filtering works through existing query endpoint

**Tasks**:

- [ ] T032 [P] [US3] Create EdgeInfoWithLanes dataclass in shared/data_access/edge_query.py extending EdgeInfo with emergency_lane_count, emergency_lane_indexes, total_lanes
- [ ] T033 [P] [US3] Implement query_edges_with_emergency_lanes() function in shared/data_access/edge_query.py that JOINs sim_network_lanes table to identify lanes with disallow="all"
- [ ] T034 [P] [US3] Create EdgeInfoWithLanesResponse Pydantic model in api/models/responses/edge_query_response.py
- [ ] T035 [US3] Implement get_edges_with_emergency_lanes() service method in api/services/control_strategy_service.py calling query_edges_with_emergency_lanes()
- [ ] T036 [US3] Implement GET /api/v1/control/edges/query_dhs endpoint in api/routes/control_routes.py for emergency lane queries
- [ ] T037 [US3] Add emergency lane display columns to edge_selector.html results table: emergency_lane_count, emergency_lane_indexes
- [ ] T038 [P] [US3] Create test_dhs_scenario() integration test in tests/integration/test_control_api.py verifying emergency lane detection
- [ ] T039 [US3] Document DHS filtering workflow in quickstart.md with examples: min_lanes=5 (inference) vs query_dhs endpoint (precise)

**Dependencies**:
- T032-T033 independent (new shared layer code)
- T034 depends on T032 (dataclass defined)
- T035 depends on T033 (query function)
- T036 depends on T034, T035 (model + service)
- T037 depends on T036 (API endpoint)
- T038 can start after T036 (endpoint defined)
- T039 can start anytime (documentation)

**Parallel Opportunities**:
- T032, T033 can run in parallel
- T034, T035 can run after T032-T033 in parallel
- T037, T038, T039 can run in parallel after T036

**Test Scenarios**:
```python
def test_dhs_inference():
    # Basic DHS: Filter by min_lanes >= 5
    response = client.get("/api/v1/control/edges/query?route_codes=G4202&min_lanes=5")
    data = response.json()
    assert all(edge["num_lanes"] >= 5 for edge in data["edges"])

def test_dhs_precise():
    # Precise DHS: Query emergency lanes
    response = client.get("/api/v1/control/edges/query_dhs?route_codes=G4202")
    data = response.json()
    assert all("emergency_lane_count" in edge for edge in data["edges"])
    assert all(edge["emergency_lane_count"] > 0 for edge in data["edges"])
```

**Acceptance Criteria (from spec)**:
- ✅ System returns mainroad segments with 5+ lanes when filtering edge_type=highway.motorway, min_lanes=5
- ✅ Detailed segment information shows lane count, emergency lane count, emergency lane indexes
- ✅ Emergency lane filter returns only segments confirmed to have emergency lanes with disallow="all"

---

## Phase 7: User Story 4 - Visualization (Priority: P4) - ✅ IMPLEMENTED

**Goal**: Provide spatial visualization of filtered road segments on network map

**Independent Test**: Filter 15 segments, verify they display highlighted on Canvas network map, click segment to toggle selection state

**User Story Reference**: spec.md lines 65-82

**Status**: ✅ **IMPLEMENTED** (2025-10-21)

**Note**: Phase 7 visualization has been successfully implemented with full Canvas-based network rendering, interactive pan/zoom, edge highlighting, and selection synchronization with the table UI.

**Implemented Features**:
- ✅ Canvas-based network visualization with junction coordinates
- ✅ Interactive pan (drag) and zoom (mouse wheel) controls
- ✅ Filtered edge highlighting in blue
- ✅ Selected edge highlighting in green
- ✅ Hover tooltips showing edge information
- ✅ Click-to-select functionality
- ✅ Selection synchronization between table and visualization
- ✅ Legend display for edge color meanings
- ✅ Coordinate transformation from lon/lat to canvas coordinates
- ✅ Network geometry API endpoint with caching

**Tasks**:

- [x] T040 [P] [US4] Create network_viz.js in frontend/control/js/ with Canvas initialization and coordinate transformation functions
- [x] T041 [P] [US4] Implement loadNetworkGeometry() function in network_viz.js to fetch junction coordinates from database via new /api/v1/control/edges/network_geometry endpoint
- [x] T042 [P] [US4] Implement renderEdges() function in network_viz.js to draw edges as lines between from_junction and to_junction coordinates
- [x] T043 [US4] Implement highlightFilteredEdges() function in network_viz.js to apply distinctive color to filtered edges from query results
- [x] T044 [US4] Add Canvas element to edge_selector.html with pan/zoom controls and tooltip div for edge details on hover
- [x] T045 [US4] Implement click handler in network_viz.js to toggle edge selection state and update selected edges list
- [x] T046 [US4] Create GET /api/v1/control/edges/network_geometry endpoint in api/routes/control_strategy_routes.py returning junction coordinates for visualization

**Dependencies**:
- T040-T042 independent (new JavaScript file)
- T043 depends on T042 (rendering function)
- T044 depends on T040 (network_viz.js created), T013 (edge_selector.html base)
- T045 depends on T043-T044 (rendering + UI)
- T046 independent (new API endpoint)

**Parallel Opportunities**:
- T040, T041, T042 can run in parallel (different functions in same file)
- T044, T046 can run in parallel
- T045 can run after T043-T044

**Test Scenarios**:
```javascript
// Manual testing checklist (Canvas visualization is visual)
// - [ ] Filter 15 segments → all 15 highlighted on map
// - [ ] Hover segment → tooltip shows edge_id, stake_range, length, lanes
// - [ ] Click segment → selection state toggles
// - [ ] Pan/zoom → smooth performance
```

**Acceptance Criteria (from spec)**:
- ✅ System displays all 15 filtered segments highlighted on simplified road network map
- ✅ Tooltip shows edge_id, stake range, length, lane count on hover
- ✅ Clicking highlighted segments toggles selection state and updates selected segments list
- ✅ System supports pan and zoom operations with smooth performance

---

## Dependencies and Execution Order

### User Story Dependency Graph

```
Setup (Phase 1) → Foundational (Phase 2)
                        ↓
                    US1 (Phase 3) ⭐ MVP - BLOCKING
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
    US5 (Phase 4)   US2 (Phase 5)   US3 (Phase 6) - OPTIONAL
                                        ↓
                                    US4 (Phase 7) - OPTIONAL
```

**Execution Sequence**:
1. **MUST complete first**: Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1)
2. **Can parallelize**: Phase 4 (US5), Phase 5 (US2), Phase 6 (US3)
3. **Can defer**: Phase 6 (US3 - DHS), Phase 7 (US4 - Visualization)

**MVP Delivery**:
- Phases 1-3 deliver independently testable basic filtering capability
- US1 enables immediate value for VSS control strategy selection
- US5 and US2 can be added incrementally after MVP deployed

**Inter-Phase Dependencies**:
- Phase 2 tasks (models) block all user story phases
- US1 (Phase 3) blocks US5/US2/US3 (shared API contract patterns)
- US3 (Phase 6 - DHS) is independent, can be deferred
- US4 (Phase 7 - Visualization) is independent, can be deferred

---

## Parallel Execution Examples

### Example 1: Phase 3 (US1) - Maximum Parallelization

**Sequential (no parallelization)**: 9 tasks = 9 time units

**Parallel (optimized)**:
```
Time Unit 1 [3 parallel]:
  - T007 [P]: Create EdgeQueryRequest model
  - T008 [P]: Create EdgeQueryResponse models
  - T009 [P]: Create control_strategy_service.py

Time Unit 2 [2 parallel]:
  - T010 [P]: Implement query_edges service method
  - T011 [P]: Create control_routes.py

Time Unit 3 [1 sequential]:
  - T012: Implement /query endpoint (depends on T010, T011)

Time Unit 4 [3 parallel]:
  - T013 [P]: Create edge_selector.html
  - T014 [P]: Create edge_filter.js
  - T017 [P]: Create test_control_api.py

Time Unit 5 [1 sequential]:
  - T015: Implement results table (depends on T013)

Time Unit 6 [1 parallel]:
  - T016 [P]: Add loading state to edge_filter.js

Time Unit 7 [1 sequential]:
  - T018: Register control_routes in main.py (depends on T012)
```

**Result**: 9 tasks in 7 time units (vs 9 sequential)

### Example 2: Phase 4 (US5) + Phase 5 (US2) - Cross-Phase Parallelization

**Approach**: Start US2 tasks while US5 tasks are in progress

```
Time Unit 1 [3 parallel - US5]:
  - T019 [P]: Implement get_available_routes()
  - T020 [P]: Implement get_available_sections()
  - T021 [P]: Implement get_demonstration_info()

Time Unit 2 [4 parallel - US5 + US2]:
  - T022: Implement /routes endpoint (US5)
  - T023: Implement /sections endpoint (US5)
  - T024: Implement /demonstrations endpoint (US5)
  - T029: Document TEC workflow (US2)

Time Unit 3 [4 parallel - US5 + US2]:
  - T025: Add hierarchical dropdowns (US5)
  - T026 [P]: Add node_types dropdown (US2)
  - T027 [P]: Add demonstration_ids dropdown (US2)
  - T028 [P]: Create test_tec_scenario() (US2)

Time Unit 4 [2 parallel - US2]:
  - T030 [P]: Add node_types validation (US2)
  - T031: Update edge_filter.js for multi-select (US2)
```

**Result**: 13 tasks (US5 + US2) in 4 time units (vs 13 sequential)

---

## Testing Strategy

### Unit Tests (≥80% coverage target)

**Test Files**:
- `tests/unit/test_edge_query_models.py`: Pydantic model validation
- `tests/unit/test_cache_utils.py`: TTL caching mechanism
- `tests/unit/test_control_service.py`: Service layer business logic

**Coverage Areas**:
- EdgeQueryRequest validation (stake ranges, length ranges, enums)
- EdgeQueryResponse.from_edge_infos() warning generation
- Cache hit/miss scenarios for metadata endpoints
- Retry logic for database connection failures

### Integration Tests (100% pass rate required)

**Test Files**:
- `tests/integration/test_control_api.py`: All 4+ API endpoints

**Critical Test Scenarios** (from T017, T028, T038):
1. **Basic query**: Route filter returns correct edges
2. **Multi-dimensional query**: Route + lanes + direction all applied
3. **Invalid parameters**: max_stake < min_stake returns 400
4. **Empty results**: No matching edges returns empty array
5. **Large results**: >100 edges returns warning message
6. **TEC scenario**: node_types=entrance returns only entrance ramps
7. **Hierarchical**: Sections filtered by route_code
8. **DHS scenario** (optional): min_lanes=5 returns 5+ lane edges

### Test Execution Order

**TDD Approach (per phase)**:
1. Write failing integration tests for endpoint
2. Write failing unit tests for models/service
3. Implement models → tests pass
4. Implement service → tests pass
5. Implement routes → integration tests pass

**Example - Phase 3 (US1)**:
```
1. Write test_query_edges_basic() in test_control_api.py (fails - endpoint doesn't exist)
2. Implement T007-T012 (models, service, routes)
3. Run pytest tests/integration/test_control_api.py::test_query_edges_basic (passes)
4. Write test_query_edges_with_filters() (fails - no validation)
5. Add validation to T012 (/query endpoint)
6. Run full test suite (all pass)
```

---

## Validation Checklist

### MVP Acceptance (Phases 1-3)

- [ ] API endpoints respond within 2 seconds for typical queries
- [ ] Frontend displays filter form with all 9 filter dimensions
- [ ] Query with route_codes=G4202, min_lanes=3, route_direction=clockwise returns 10-20 matching edges
- [ ] Results table shows edge_id, route_code, section_code, stake_range, length, lanes, node_type, gantry_count
- [ ] with_gantry=true returns only edges with gantry_count > 0
- [ ] Invalid parameters (max_stake < min_stake) return 400 error with clear message
- [ ] Integration tests achieve 100% pass rate
- [ ] Unit tests achieve ≥80% coverage

### Full Feature Acceptance (All Phases)

- [ ] Hierarchical filtering reduces results: route (~1000) → section (~600) → filtered (~15)
- [ ] TEC scenario: node_types=entrance returns only entrance ramps
- [ ] DHS scenario (if implemented): emergency_lane_count > 0 for segments with emergency lanes
- [ ] Visualization (if implemented): 15 filtered segments highlighted on Canvas map
- [ ] Performance: Database queries complete in <400ms
- [ ] Scalability: System handles 10 concurrent users without degradation
- [ ] Security: No database credentials in logs
- [ ] Logging: Structured JSON-compatible logs with query params, result count, execution time

---

## Risk Mitigation

### Technical Risks

**Risk 1**: Database query performance > 2 seconds
- **Mitigation**: Implement connection pooling (T005), monitor query execution time in logs, add indexes if needed
- **Early Detection**: Test with Phase 3 (US1) integration tests

**Risk 2**: Connection pool exhaustion under load
- **Mitigation**: Configure pool_size=10, max_overflow=5 (T005), log pool utilization
- **Early Detection**: Load testing with 10 concurrent requests in Phase 3

**Risk 3**: Frontend-backend API contract mismatch
- **Mitigation**: Use OpenAPI contract (contracts/edge_query_api.yaml) as source of truth, validate with integration tests
- **Early Detection**: T012 implementation must match OpenAPI spec exactly

**Risk 4**: Caching staleness for metadata endpoints
- **Mitigation**: Use 5-minute TTL (T019-T021), log cache hits/misses for monitoring
- **Early Detection**: Manual testing in Phase 4 (US5) - update database, verify cache expires after 5 min

### Schedule Risks

**Risk 1**: Phase 6 (DHS) and Phase 7 (Visualization) block delivery
- **Mitigation**: Mark as OPTIONAL, MVP completes at Phase 3 (US1)
- **Decision Point**: After Phase 3 MVP, evaluate if P3/P4 features are needed for initial release

**Risk 2**: Integration test failures block progress
- **Mitigation**: Write tests incrementally per phase, fix failures immediately before proceeding
- **Quality Gate**: Each phase cannot proceed until all integration tests pass

---

## Notes for Implementation

### Key Files to Reference

**Existing (Phase 1A - DO NOT MODIFY)**:
- `shared/data_access/edge_query.py`: Database query functions (already functional)
- `shared/data_access/connection.py`: Database connection (upgrade to SQLAlchemy pooling)

**New (Phase 1B - TO CREATE)**:
- `api/models/requests/edge_query_request.py`: Pydantic request models
- `api/models/responses/edge_query_response.py`: Pydantic response models
- `api/services/control_strategy_service.py`: Business logic layer
- `api/routes/control_routes.py`: API endpoints
- `frontend/control/edge_selector.html`: Filtering interface
- `frontend/control/js/edge_filter.js`: Frontend API integration

### Code Quality Standards

**From plan.md Development Standards**:
- Type hints on all functions
- Google-style docstrings
- Logging module (no print statements)
- Function limits: ≤30 lines, ≤5 parameters, ≤3 nesting levels
- Black formatting (100-character line width)
- Pandas for data processing

### Performance Targets

- Database query: <400ms
- API response: <2 seconds
- Metadata endpoints with cache: <100ms
- Connection pool: 10 connections, 5 overflow
- Cache TTL: 5 minutes (300 seconds)

### Security Considerations

- Use parameterized queries (SQL injection prevention)
- No database credentials in logs
- No authentication required (internal tool)
- Read-only database access

---

**Tasks Status**: ✅ Ready for Implementation

**Recommended Start**: Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1 MVP)

**Next Command**: Start implementing tasks in order, mark completed with `[x]`
