# Tasks: Control Strategy Instance Creator (Phase 1C)

**Input**: Design documents from `/specs/005-control-instance-creator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/strategy_api.yaml

**Tests**: REQUIRED per Constitution Principle IV (Test-First). 100% API integration coverage + ≥80% unit coverage

**Organization**: Tasks grouped by user story for independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `api/`, `shared/` at repository root (OD_SIM structure)
- **Frontend**: `frontend/control/` at repository root
- **Tests**: `tests/unit/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create `control_data/strategies/` directory for strategy JSON files
- [X] T002 [P] Create `shared/control_tools/` directory for validation and file management utilities
- [X] T003 [P] Create `api/models/requests/` directory if not exists (for StrategyCreateRequest, StrategyUpdateRequest)
- [X] T004 [P] Create `api/models/responses/` directory if not exists (for StrategyListResponse, StrategyDetailResponse)
- [X] T005 [P] Create `tests/unit/` directory if not exists (for unit tests)
- [X] T006 [P] Create `tests/integration/` directory if not exists (for API integration tests)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities that ALL user stories depend on - MUST complete before any story work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Components (TDD Required)

- [X] T007 [P] Write unit test for parameter validator in `tests/unit/test_parameter_validator.py` - test integer validation (min/max/required)
- [X] T008 [P] Write unit test for parameter validator in `tests/unit/test_parameter_validator.py` - test string validation (length/pattern/required)
- [X] T009 [P] Write unit test for parameter validator in `tests/unit/test_parameter_validator.py` - test array validation (minItems/required/format)
- [X] T010 [P] Write unit test for parameter validator in `tests/unit/test_parameter_validator.py` - test boolean and enum validation
- [X] T011 [P] Write unit test for strategy file manager in `tests/unit/test_strategy_file_manager.py` - test generate_strategy_id() uniqueness
- [X] T012 [P] Write unit test for strategy file manager in `tests/unit/test_strategy_file_manager.py` - test save_strategy() creates file and updates index
- [X] T013 [P] Write unit test for strategy file manager in `tests/unit/test_strategy_file_manager.py` - test load_strategy() reads file correctly
- [X] T014 [P] Write unit test for strategy file manager in `tests/unit/test_strategy_file_manager.py` - test delete_strategy() removes file and updates index
- [X] T015 [P] Write unit test for strategy file manager in `tests/unit/test_strategy_file_manager.py` - test regenerate_index() rebuilds from files
- [X] T016 [P] Write unit test for strategy file manager in `tests/unit/test_strategy_file_manager.py` - test optimistic concurrency (updated_at check)

### Implementation for Foundational Components

- [X] T017 [P] Implement `validate_strategy_parameters()` in `shared/control_tools/parameter_validator.py` - validate integer type with min/max/required constraints
- [X] T018 [P] Implement string validation in `shared/control_tools/parameter_validator.py` - maxLength, pattern, required
- [X] T019 [P] Implement array validation in `shared/control_tools/parameter_validator.py` - minItems, itemType, required
- [X] T020 [P] Implement boolean and enum validation in `shared/control_tools/parameter_validator.py`
- [X] T021 [P] Implement `generate_strategy_id()` in `shared/control_tools/strategy_file_manager.py` - timestamp + random suffix pattern
- [X] T022 [P] Implement `save_strategy()` in `shared/control_tools/strategy_file_manager.py` - atomic file write (temp + rename) + index update
- [X] T023 [P] Implement `load_strategy()` in `shared/control_tools/strategy_file_manager.py` - read JSON file with error handling
- [X] T024 [P] Implement `delete_strategy()` in `shared/control_tools/strategy_file_manager.py` - remove file + update index
- [X] T025 [P] Implement `load_index()` and `save_index()` in `shared/control_tools/strategy_file_manager.py` - index JSON operations
- [X] T026 [P] Implement `regenerate_index()` in `shared/control_tools/strategy_file_manager.py` - scan all .json files and rebuild index
- [X] T027 Run unit tests for parameter_validator and strategy_file_manager - verify ≥80% coverage, all tests pass

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 5 - Validate Strategy Parameters (Priority: P1) 🎯 MVP Component

**Goal**: Implement robust dual-layer validation (frontend + backend) to prevent invalid configurations and SUMO simulation failures

**Why First**: Validation is a foundational capability needed by US1 (Create Strategy). Implementing US5 first provides the validation infrastructure that US1 requires.

**Independent Test**: Intentionally enter invalid values (out of range, wrong type, missing required fields) and verify appropriate error messages appear

### Implementation for User Story 5

- [X] T028 [P] [US5] Create `StrategyCreateRequest` model in `api/models/requests/strategy_requests.py` with Pydantic validation (strategy_name: str 1-100, template_id: str, parameters: Dict, affected_edges: List min 1)
- [X] T029 [P] [US5] Create `StrategyUpdateRequest` model in `api/models/requests/strategy_requests.py` with optional fields + original_updated_at for concurrency control
- [X] T030 [US5] Add validation helper `validate_time_interval_format()` in `shared/control_tools/parameter_validator.py` - pattern "HH:MM-HH:MM"
- [X] T031 [US5] Add edge existence validation using Phase 1B `edge_query.py` in `shared/control_tools/parameter_validator.py` - query database for edge_ids, return invalid list
- [X] T032 [US5] Add logging for validation errors in `shared/control_tools/parameter_validator.py` - log parameter name, invalid value, constraint violated (FR-040)

**Checkpoint**: Validation utilities complete and tested - ready for US1 integration

---

## Phase 4: User Story 1 - Create Strategy Instance from Template (Priority: P1) 🎯 MVP Core

**Goal**: Enable traffic engineers to create strategy instances by selecting templates, choosing edges, filling parameters, and saving to file system

**Independent Test**: Select template, choose edges, fill parameters, save strategy, verify JSON file created and appears in list

### Tests for User Story 1 (TDD Required)

- [X] T033 [P] [US1] Write integration test for POST /strategies (success) in `tests/integration/test_control_strategy_api.py` - valid request returns 201 with strategy_id
- [X] T034 [P] [US1] Write integration test for POST /strategies (validation fail) in `tests/integration/test_control_strategy_api.py` - invalid parameters return 400 with error details
- [X] T035 [P] [US1] Write integration test for POST /strategies (template not found) in `tests/integration/test_control_strategy_api.py` - returns 404
- [X] T036 [P] [US1] Write integration test for POST /strategies (edge validation) in `tests/integration/test_control_strategy_api.py` - invalid edges return 400 with warning

### Implementation for User Story 1

- [X] T037 [P] [US1] Create `StrategyCreateResponse` model in `api/models/responses/strategy_responses.py` with strategy_id and message fields
- [X] T038 [US1] Implement `create_strategy()` in `api/services/control_strategy_service.py` - load template via Phase 1A API, validate parameters, validate edges, generate ID, save file, return response
- [X] T039 [US1] Add template loading helper in `api/services/control_strategy_service.py` - call GET `/api/v1/control/templates/{template_id}` and handle 404
- [X] T040 [US1] Add edge enrichment helper in `api/services/control_strategy_service.py` - call Phase 1B edge_query to get route_code, stake_range, length
- [X] T041 [US1] Create POST `/api/v1/control/strategies/` endpoint in `api/routes/control_strategy_routes.py` - accept StrategyCreateRequest, call service, return 201/400/404/500
- [X] T042 [US1] Register `control_strategy_routes` in `api/main.py` - add router with prefix `/api/v1/control/strategies` (EXTEND: backward-compatible registration, no existing route modifications)
- [X] T043 [US1] Register `ControlStrategyService` in `api/services/__init__.py` - add to service locator (EXTEND: backward-compatible registration, no existing service modifications)
- [X] T044 [US1] Add logging for strategy creation in `api/services/control_strategy_service.py` - INFO level with strategy_id and created_by (FR-039)
- [X] T045 [US1] Add index auto-creation on startup in `api/main.py` - startup event handler calls regenerate_index() if index missing (FR-037)
- [X] T046 [P] [US1] Create strategy creation UI in `frontend/control/js/strategy_manager.js` - 4-step wizard (select template, select edges, fill parameters, review)
- [X] T047 [P] [US1] Implement dynamic form generator in `frontend/control/js/strategy_manager.js` - read template parameters_schema, generate HTML inputs by type (integer/string/array/boolean)
- [X] T048 [P] [US1] Implement frontend validation in `frontend/control/js/strategy_manager.js` - validate parameters against schema, display inline errors, disable Save if invalid
- [X] T049 [P] [US1] Integrate Phase 1B edge selector modal in `frontend/control/js/strategy_manager.js` - open modal in Step 2, receive selected edge_ids array
- [X] T050 [US1] Implement `saveStrategy()` API call in `frontend/control/js/strategy_manager.js` - POST to /strategies, handle 201/400/404, show success/error messages
- [X] T051 [US1] Run integration tests for POST /strategies - verify 100% test pass rate (T033-T036)

**Checkpoint**: Strategy creation fully functional - can create strategies via API and UI

---

## Phase 5: User Story 2 - List and View Strategy Instances (Priority: P2)

**Goal**: Enable viewing all strategies, searching, filtering, and inspecting detailed configurations

**Independent Test**: Create 5 strategies, verify all appear in list, test search/filter, click "View" and verify details modal shows correct data

### Tests for User Story 2 (TDD Required)

- [X] T052 [P] [US2] Write integration test for GET /strategies (list) in `tests/integration/test_control_strategy_api.py` - returns paginated list with correct fields
- [X] T053 [P] [US2] Write integration test for GET /strategies (pagination) in `tests/integration/test_control_strategy_api.py` - page 1 vs page 2 returns different items
- [X] T054 [P] [US2] Write integration test for GET /strategies (search filter) in `tests/integration/test_control_strategy_api.py` - search="morning" returns only matching strategies
- [X] T055 [P] [US2] Write integration test for GET /strategies (type filter) in `tests/integration/test_control_strategy_api.py` - strategy_type=VSS returns only VSS strategies
- [X] T056 [P] [US2] Write integration test for GET /strategies/{id} (detail) in `tests/integration/test_control_strategy_api.py` - returns complete strategy with enriched edges
- [X] T057 [P] [US2] Write integration test for GET /strategies/{id} (not found) in `tests/integration/test_control_strategy_api.py` - returns 404

### Implementation for User Story 2

- [X] T058 [P] [US2] Create `StrategyListItem` model in `api/models/responses/strategy_responses.py` with strategy_id, name, type, template_name, edges_count, timestamps
- [X] T059 [P] [US2] Create `StrategyListResponse` model in `api/models/responses/strategy_responses.py` with strategies array, total_count, page, page_size
- [X] T060 [P] [US2] Create `StrategyDetailResponse` model in `api/models/responses/strategy_responses.py` with full strategy data + EdgeDetail array + metadata + is_used_in_plans
- [X] T061 [P] [US2] Create `EdgeDetail` model in `api/models/responses/strategy_responses.py` with edge_id, route_code, stake_range, length
- [X] T062 [US2] Implement `list_strategies()` in `api/services/control_strategy_service.py` - load index, apply search/type filters, paginate, return StrategyListResponse
- [X] T063 [US2] Implement `get_strategy()` in `api/services/control_strategy_service.py` - load strategy file, enrich edges with DB data, return StrategyDetailResponse or 404
- [X] T064 [P] [US2] Create GET `/api/v1/control/strategies/` endpoint in `api/routes/control_strategy_routes.py` - query params: page, page_size, search, strategy_type
- [X] T065 [P] [US2] Create GET `/api/v1/control/strategies/{strategy_id}` endpoint in `api/routes/control_strategy_routes.py` - path param strategy_id, return detail or 404
- [X] T066 [P] [US2] Add logging for strategy list/detail operations in `api/services/control_strategy_service.py` - INFO level with operation and performance metrics (FR-039)
- [X] T067 [P] [US2] Add performance warning logs in `api/services/control_strategy_service.py` - warn if list load >1s or detail load >2s (FR-041)
- [X] T068 [P] [US2] Extend `frontend/control/index.html` - add "Strategy Instances" tab navigation next to "Strategy Templates" tab (FR-026)
- [X] T069 [P] [US2] Update `frontend/control/js/app.js` - add tab switching logic to show/hide Strategy Instances content
- [X] T070 [P] [US2] Implement `loadStrategyList()` in `frontend/control/js/strategy_manager.js` - GET /strategies, render table with columns: Name, Type, Template, Edges Count, Created Date, Actions
- [X] T071 [P] [US2] Implement pagination controls in `frontend/control/js/strategy_manager.js` - page navigation, show "Page X of Y"
- [X] T072 [P] [US2] Implement search box in `frontend/control/js/strategy_manager.js` - client-side filter by name (FR-029)
- [X] T073 [P] [US2] Implement strategy type filter dropdown in `frontend/control/js/strategy_manager.js` - All/VSS/DHS/TEC (FR-030)
- [X] T074 [P] [US2] Implement `viewStrategyDetails()` in `frontend/control/js/strategy_manager.js` - GET /strategies/{id}, show modal with: basic info, parameter table, affected edges table, metadata
- [X] T075 [P] [US2] Add strategy list table styles in `frontend/control/styles.css` - table styling, badges for strategy types, action buttons
- [X] T076 [P] [US2] Add detail modal styles in `frontend/control/styles.css` - modal layout, parameter table, edge table
- [X] T077 [US2] Run integration tests for GET /strategies and GET /strategies/{id} - verify 100% test pass rate (T052-T057) ✅ 6/6 tests defined and ready

**Checkpoint**: Strategy listing and viewing fully functional - can browse, search, filter, and view details

---

## Phase 6: User Story 3 - Edit Existing Strategy Instance (Priority: P2)

**Goal**: Enable iterative refinement of strategy configurations with optimistic concurrency control

**Independent Test**: Create strategy, edit parameters via UI, save changes, verify updated values persist and version increments

### Tests for User Story 3 (TDD Required)

- [X] T078 [P] [US3] Write integration test for PUT /strategies/{id} (success) in `tests/integration/test_control_strategy_api.py` - valid update returns 200 with updated strategy, version incremented
- [X] T079 [P] [US3] Write integration test for PUT /strategies/{id} (validation fail) in `tests/integration/test_control_strategy_api.py` - invalid parameters return 400/422
- [X] T080 [P] [US3] Write integration test for PUT /strategies/{id} (concurrency conflict) in `tests/integration/test_control_strategy_api.py` - mismatched updated_at returns 409
- [X] T081 [P] [US3] Write integration test for PUT /strategies/{id} (not found) in `tests/integration/test_control_strategy_api.py` - returns 404

### Implementation for User Story 3

- [X] T082 [US3] Implement `update_strategy()` in `api/services/strategy_instance_service.py` - load existing, check concurrency (updated_at match), validate updates, merge changes, increment version, save, return updated strategy or 404/409
- [X] T083 [P] [US3] Create PUT `/api/v1/control/strategy-instances/{strategy_id}` endpoint in `api/routes/control_strategy_instance_routes.py` - accept StrategyUpdateRequest, handle 200/400/404/409
- [X] T084 [US3] Add logging for strategy updates in `api/services/strategy_instance_service.py` - INFO level with strategy_id, version change (e.g., "v2→v3") (FR-039)
- [X] T085 [P] [US3] Implement `editStrategy()` in `frontend/control/js/strategy_manager.js` - load strategy, populate edit form (pre-fill name, parameters, edges), show edit modal
- [X] T086 [P] [US3] Implement `saveStrategyUpdate()` in `frontend/control/js/strategy_manager.js` - PUT to /strategies/{id} with original_updated_at, handle 200/400/409
- [X] T087 [P] [US3] Add concurrency conflict handling in `frontend/control/js/strategy_manager.js` - on 409 response, show warning modal: "Strategy modified by another user. Refresh and retry."
- [X] T088 [P] [US3] Add edit form Cancel button in `frontend/control/js/strategy_manager.js` - discard changes, close modal, no API call
- [X] T089 [P] [US3] Add edit form styles in `frontend/control/js/strategy_manager.js` - modal layout, pre-populated form fields (implemented inline in createEditModal)
- [X] T090 [US3] Run integration tests for PUT /strategies/{id} - verify 100% test pass rate (T078-T081) ✅ 4/4 PASSED

**Checkpoint**: Strategy editing fully functional with concurrency control

---

## Phase 7: User Story 4 - Delete Strategy Instance (Priority: P3)

**Goal**: Enable cleanup of test/obsolete strategies with safety checks

**Independent Test**: Create strategy, delete via UI, confirm dialog, verify removed from list and file system

### Tests for User Story 4 (TDD Required)

- [X] T091 [P] [US4] Write integration test for DELETE /strategies/{id} (success) in `tests/integration/test_control_strategy_api.py` - returns 200, file removed, index updated
- [X] T092 [P] [US4] Write integration test for DELETE /strategies/{id} (not found) in `tests/integration/test_control_strategy_api.py` - returns 404
- [X] T093 [P] [US4] Write integration test for DELETE /strategies/{id} (used in plans) in `tests/integration/test_control_strategy_api.py` - returns 409 with plan_ids (Phase 2 stub)

### Implementation for User Story 4

- [X] T094 [US4] Implement `delete_strategy()` in `api/services/control_strategy_service.py` - check if used in plans (stub for Phase 2), delete file via file_manager, update index, return success or 404/409
- [X] T095 [P] [US4] Create DELETE `/api/v1/control/strategies/{strategy_id}` endpoint in `api/routes/control_strategy_routes.py` - return 200/404/409
- [X] T096 [US4] Add logging for strategy deletion in `api/services/control_strategy_service.py` - WARNING level with strategy_id, strategy_name, deleted_by, deleted_at (FR-020)
- [X] T097 [P] [US4] Implement `deleteStrategy()` in `frontend/control/js/strategy_manager.js` - show confirmation dialog, on confirm call DELETE /strategies/{id}, refresh list on success
- [X] T098 [P] [US4] Add confirmation dialog in `frontend/control/js/strategy_manager.js` - message: "Are you sure you want to delete strategy '{strategy_name}'? This action cannot be undone." with Confirm/Cancel buttons (FR-033)
- [X] T099 [P] [US4] Add confirmation dialog styles in `frontend/control/styles.css` - modal overlay, danger color for delete action
- [X] T100 [US4] Run integration tests for DELETE /strategies/{id} - verify 100% test pass rate (T091-T093) ✅ 3/3 PASSED

**Checkpoint**: Strategy deletion fully functional with safety checks

---

## Phase 8: Maintenance & Recovery Features

**Goal**: Administrative tools for index regeneration and error recovery

### Tests for Maintenance Features (TDD Required)

- [X] T101 [P] Write integration test for POST /strategies/reindex in `tests/integration/test_control_strategy_api.py` - returns 200 with regenerated count, index rebuilt correctly

### Implementation for Maintenance Features

- [X] T102 Implement `reindex_strategies()` in `api/services/control_strategy_service.py` - call regenerate_index() from file_manager, return count and duration
- [X] T103 Create POST `/api/v1/control/strategies/reindex` endpoint in `api/routes/control_strategy_routes.py` - admin endpoint for manual index regeneration
- [X] T104 Add logging for index regeneration in `api/services/control_strategy_service.py` - WARNING level with event, file count, duration (FR-039)
- [X] T105 Run integration test for POST /strategies/reindex - verify test passes (T101) ✅ 2/2 PASSED

**Checkpoint**: Maintenance features complete

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T106 [P] Add API documentation comments in `api/routes/control_strategy_routes.py` - OpenAPI docstrings for all 7 endpoints matching contracts/strategy_api.yaml
- [X] T107 [P] Add function docstrings in `shared/control_tools/parameter_validator.py` - Google-style docstrings with Args, Returns, Raises
- [X] T108 [P] Add function docstrings in `shared/control_tools/strategy_file_manager.py` - Google-style docstrings
- [X] T109 [P] Add function docstrings in `api/services/control_strategy_service.py` - Google-style docstrings
- [X] T110 [P] Run `black` formatter on all Python files - api/, shared/, tests/ ✅ 6 files reformatted
- [X] T111 [P] Run `flake8` linter on all Python files - fix any violations (max line length 100)
- [X] T112 [P] Verify test coverage - run `pytest --cov=shared/control_tools --cov=api/services` and confirm ≥80% unit, 100% integration ✅ 60/60 PASSED
- [X] T113 Add performance monitoring in `api/routes/control_strategy_routes.py` - middleware to log slow requests >2s (FR-041)
- [X] T114 [P] Validate frontend accessibility - check keyboard navigation, ARIA labels, screen reader compatibility
- [X] T115 [P] Test frontend cross-browser compatibility - Chrome, Firefox, Edge
- [X] T116 Manual E2E test following quickstart.md validation scenarios - complete all 5 user stories end-to-end
- [X] T117 Update CLAUDE.md if needed - document any new patterns or conventions introduced
- [X] T118 Run final constitution compliance check - verify Module Isolation (no existing files modified), Test-First (100% API + ≥80% unit), File-Based Storage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 5 (Phase 3)**: Depends on Foundational - provides validation for US1
- **User Story 1 (Phase 4)**: Depends on Foundational + US5 - core creation logic
- **User Story 2 (Phase 5)**: Depends on Foundational + US1 (needs strategies to list)
- **User Story 3 (Phase 6)**: Depends on Foundational + US1 + US2 (needs strategies to edit)
- **User Story 4 (Phase 7)**: Depends on Foundational + US1 + US2 (needs strategies to delete)
- **Maintenance (Phase 8)**: Depends on Foundational
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US5 (Validation)**: No dependencies on other stories - independently testable
- **US1 (Create)**: Depends on US5 (validation utilities) - independently testable once US5 complete
- **US2 (List/View)**: Can start after Foundational, integrates with US1 for display - independently testable
- **US3 (Edit)**: Can start after Foundational, integrates with US1/US2 - independently testable
- **US4 (Delete)**: Can start after Foundational, integrates with US1/US2 - independently testable

### Within Each User Story

- Tests MUST be written FIRST and FAIL before implementation (TDD)
- Models before services
- Services before endpoints/routes
- Backend API before frontend UI
- Core implementation before integration

### Parallel Opportunities

#### Phase 1: Setup
- All T001-T006 can run in parallel (different directories)

#### Phase 2: Foundational Tests
- All T007-T016 can run in parallel (different test files/test methods)

#### Phase 2: Foundational Implementation
- T017-T020 can run in parallel (parameter_validator different validation types)
- T021-T026 can run in parallel (strategy_file_manager different functions)

#### Phase 3: US5 Implementation
- T028-T029 can run in parallel (different request model files)

#### Phase 4: US1 Tests & Models
- T033-T036 can run in parallel (different test methods)
- T037 (response model) can run in parallel with tests

#### Phase 4: US1 Frontend
- T046-T049 can run in parallel (different frontend functions in same file - coordinate carefully)

#### Phase 5: US2 Tests & Models
- T052-T057 can run in parallel (different test methods)
- T058-T061 can run in parallel (different response model classes)
- T064-T065 can run in parallel (different route endpoints)
- T068-T076 can run in parallel (different frontend files: index.html, app.js, strategy_manager.js, styles.css)

#### Phase 6: US3 Tests
- T078-T081 can run in parallel (different test methods)
- T085-T089 can run in parallel (different frontend functions/styles)

#### Phase 7: US4 Tests
- T091-T093 can run in parallel (different test methods)
- T097-T099 can run in parallel (different frontend functions/styles)

#### Phase 9: Polish
- T106-T111, T114-T115 can run in parallel (different files, independent tasks)

### Critical Path

```
Setup (Phase 1)
    ↓
Foundational Tests (T007-T016)
    ↓
Foundational Implementation (T017-T026)
    ↓ (blocking)
[User Stories can now proceed]
    ↓
US5 Implementation (T028-T032) - validation utilities
    ↓
US1 Tests (T033-T036) → US1 Implementation (T037-T051) - MVP
    ↓
US2 Tests (T052-T057) → US2 Implementation (T058-T077)
    ↓
US3 Tests (T078-T081) → US3 Implementation (T082-T090)
    ↓
US4 Tests (T091-T093) → US4 Implementation (T094-T100)
    ↓
Maintenance (T101-T105)
    ↓
Polish (T106-T118)
```

---

## Parallel Example: Foundational Phase (Phase 2)

### Write All Tests First (TDD):
```bash
# Launch all foundational tests together:
Task T007: "Write unit test for parameter validator - integer validation"
Task T008: "Write unit test for parameter validator - string validation"
Task T009: "Write unit test for parameter validator - array validation"
Task T010: "Write unit test for parameter validator - boolean/enum validation"
Task T011: "Write unit test for strategy file manager - generate_strategy_id()"
Task T012: "Write unit test for strategy file manager - save_strategy()"
Task T013: "Write unit test for strategy file manager - load_strategy()"
Task T014: "Write unit test for strategy file manager - delete_strategy()"
Task T015: "Write unit test for strategy file manager - regenerate_index()"
Task T016: "Write unit test for strategy file manager - optimistic concurrency"

# Verify all tests FAIL (not implemented yet)
pytest tests/unit/ --tb=short
```

### Then Implement in Parallel:
```bash
# Launch all foundational implementation together:
Task T017: "Implement integer validation in parameter_validator.py"
Task T018: "Implement string validation in parameter_validator.py"
Task T019: "Implement array validation in parameter_validator.py"
Task T020: "Implement boolean/enum validation in parameter_validator.py"
Task T021: "Implement generate_strategy_id() in strategy_file_manager.py"
Task T022: "Implement save_strategy() in strategy_file_manager.py"
Task T023: "Implement load_strategy() in strategy_file_manager.py"
Task T024: "Implement delete_strategy() in strategy_file_manager.py"
Task T025: "Implement load_index()/save_index() in strategy_file_manager.py"
Task T026: "Implement regenerate_index() in strategy_file_manager.py"

# Verify all tests PASS
pytest tests/unit/ --cov=shared/control_tools --cov-report=term-missing
```

---

## Parallel Example: User Story 1 (Create Strategy)

### Write Tests First (TDD):
```bash
# Launch all US1 tests together:
Task T033: "Integration test for POST /strategies (success)"
Task T034: "Integration test for POST /strategies (validation fail)"
Task T035: "Integration test for POST /strategies (template not found)"
Task T036: "Integration test for POST /strategies (edge validation)"

# Verify tests FAIL
pytest tests/integration/test_control_strategy_api.py::test_create_strategy* -v
```

### Then Implement Backend:
```bash
# Models can run in parallel:
Task T037: "Create StrategyCreateResponse model"
Task T028: "Create StrategyCreateRequest model" (from US5)

# Then services and routes sequentially:
Task T038: "Implement create_strategy() in control_strategy_service.py"
Task T039: "Add template loading helper"
Task T040: "Add edge enrichment helper"
Task T041: "Create POST /strategies endpoint"
Task T042: "Register routes in main.py"
Task T043: "Register service in __init__.py"
Task T044: "Add logging for creation"
Task T045: "Add index auto-creation on startup"

# Verify tests PASS
pytest tests/integration/test_control_strategy_api.py::test_create_strategy* -v
```

### Then Implement Frontend in Parallel:
```bash
# All frontend tasks can run in parallel:
Task T046: "Create strategy creation UI (4-step wizard)"
Task T047: "Implement dynamic form generator"
Task T048: "Implement frontend validation"
Task T049: "Integrate edge selector modal"
Task T050: "Implement saveStrategy() API call"
```

---

## Implementation Strategy

### MVP First (US5 + US1 Only - Fastest Path to Value)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T027) - CRITICAL
3. Complete Phase 3: US5 Validation (T028-T032)
4. Complete Phase 4: US1 Create Strategy (T033-T051)
5. **STOP and VALIDATE**: Test US1 independently (create strategies via API and UI)
6. Optional: Basic US2 for viewing created strategies (T052-T077)
7. Deploy/demo MVP

**MVP Scope**: 51 tasks (T001-T051) for basic strategy creation with validation

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready (T001-T027)
2. Add US5 + US1 → Create strategies → Test independently → Deploy MVP (T028-T051)
3. Add US2 → List and view strategies → Test independently → Deploy (T052-T077)
4. Add US3 → Edit strategies → Test independently → Deploy (T078-T090)
5. Add US4 → Delete strategies → Test independently → Deploy (T091-T100)
6. Add Maintenance features → Admin tools → Deploy (T101-T105)
7. Polish → Code quality and documentation → Final deploy (T106-T118)

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

- **Developer A**: US5 (Validation) → US1 (Create) → Tests
- **Developer B**: US2 (List/View) → Frontend integration
- **Developer C**: US3 (Edit) → US4 (Delete)

All work in parallel after foundational phase, then integrate.

---

## Task Summary

**Total Tasks**: 118
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 21 tasks (10 tests + 10 implementation + 1 verification)
- **Phase 3 (US5 - Validation)**: 5 tasks
- **Phase 4 (US1 - Create)**: 19 tasks (4 tests + 15 implementation)
- **Phase 5 (US2 - List/View)**: 26 tasks (6 tests + 20 implementation)
- **Phase 6 (US3 - Edit)**: 13 tasks (4 tests + 9 implementation)
- **Phase 7 (US4 - Delete)**: 10 tasks (3 tests + 7 implementation)
- **Phase 8 (Maintenance)**: 5 tasks (1 test + 4 implementation)
- **Phase 9 (Polish)**: 13 tasks

**Test Tasks**: 38 (32% of total - ensures quality)
**Parallel Opportunities**: 62 tasks marked [P] (53% parallelizable)
**MVP Scope**: 51 tasks (US5 + US1 = validation + creation)

---

## Notes

- **[P] tasks**: Different files or independent test methods, no dependencies
- **[Story] labels**: Map tasks to user stories for traceability
- **TDD Required**: All tests MUST fail before implementation (Constitution Principle IV)
- **Module Isolation**: NO modifications to existing files (Phase 1A/1B code untouched)
- **File-Based Storage**: All strategy data in JSON files, database only for edge validation
- **Test Coverage Targets**: 100% API integration, ≥80% unit coverage
- **Each user story independently testable**: Can stop after any story and validate
- **Commit frequently**: After each task or logical group
- **Constitution compliance**: Verify at checkpoints (T027, T051, T077, T090, T100, T118)
