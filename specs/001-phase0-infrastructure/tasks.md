# Tasks: 交通管控仿真 - Phase 0 基础设施准备

**Input**: Design documents from `/specs/001-phase0-infrastructure/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: NOT included - Phase 0 is scaffolding only. Tests explicitly out of scope per spec.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Project Type**: Web application with existing api/ + frontend/ structure
- **Backend**: api/ (models, routes, services)
- **Shared**: shared/ (utilities, data access)
- **Frontend**: frontend/ (HTML/CSS/JS)
- **Templates**: templates/ (configuration templates)
- **Data**: control_data/ (runtime data storage)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure creation

- [X] T001 Create directory templates/control_strategies/ for strategy template storage
- [X] T002 [P] Create directory control_data/strategies/ for user strategy data
- [X] T003 [P] Create directory control_data/plans/ for control plan data
- [X] T004 [P] Create directory control_data/optimizations/ for optimization results
- [X] T005 [P] Create directory api/models/control/entities/ for control domain models
- [X] T006 [P] Create directory api/services/control/ for control service layer
- [X] T007 [P] Create directory shared/control_tools/ for control shared utilities
- [X] T008 [P] Create directory frontend/control/ for control frontend pages
- [X] T009 [P] Create .gitkeep files in templates/control_strategies/, control_data/strategies/, control_data/plans/, control_data/optimizations/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core enums that MUST be complete before ANY user story can implement models

**⚠️ CRITICAL**: No data model work can begin until enums are defined

- [X] T010 Add StrategyType enum (vss/dhs/tec) to api/models/enums.py
- [X] T011 Add BatchSimulationStatus enum (pending/running/completed/failed) to api/models/enums.py

**Checkpoint**: Foundation ready - data models can now be implemented

---

## Phase 3: User Story 1 - 开发者初始化控制策略功能模块 (Priority: P1) 🎯 MVP

**Goal**: Establish complete infrastructure including data models, API skeleton, and frontend skeleton for traffic control simulation optimization module

**Independent Test**:
- Directory structure exists (all 7 directories)
- Data models pass type checking (mypy)
- API routes accessible (return empty data)
- Frontend page loads (basic layout visible)

### Data Models for User Story 1

- [X] T012 [P] [US1] Create __init__.py in api/models/control/
- [X] T013 [P] [US1] Create __init__.py in api/models/control/entities/
- [X] T014 [P] [US1] Create ControlTemplate model in api/models/control/entities/template.py
- [X] T015 [P] [US1] Create Strategy model in api/models/control/entities/strategy.py
- [X] T016 [P] [US1] Create Plan model in api/models/control/entities/plan.py
- [X] T017 [P] [US1] Create BatchSimulation model in api/models/control/entities/batch_simulation.py
- [X] T018 [US1] Add model exports to api/models/control/entities/__init__.py
- [X] T019 [US1] Add model exports to api/models/control/__init__.py

### API Routes for User Story 1

- [X] T020 [US1] Create control_strategy_routes.py in api/routes/ with empty route stubs for templates (2 endpoints)
- [X] T021 [US1] Add empty route stubs for strategies (5 endpoints: list/create/get/update/delete) to api/routes/control_strategy_routes.py
- [X] T022 [US1] Add empty route stubs for plans (3 endpoints + generate) to api/routes/control_strategy_routes.py
- [X] T023 [US1] Add empty route stubs for batch_simulations (3 endpoints + start) to api/routes/control_strategy_routes.py
- [X] T024 [US1] Register control routes in api/routes/__init__.py with prefix /control and tag 交通管控

### API Services for User Story 1

- [X] T025 [P] [US1] Create __init__.py in api/services/control/
- [X] T026 [P] [US1] Create ControlStrategyService class in api/services/control/control_strategy_service.py with empty methods
- [X] T027 [US1] Add service exports to api/services/control/__init__.py

### Frontend Skeleton for User Story 1

- [X] T028 [P] [US1] Create index.html in frontend/control/ with basic HTML structure (header, nav placeholder, main, footer)
- [X] T029 [P] [US1] Create styles.css in frontend/control/ with basic layout styles
- [X] T030 [P] [US1] Create app.js in frontend/control/ with placeholder navigation logic

**Checkpoint**: At this point, User Story 1 should be fully functional and testable:
- ✅ All directories created
- ✅ All 4 data models defined and pass type checking
- ✅ All 13 API endpoints registered (return empty data)
- ✅ Frontend page loads at /control/index.html

---

## Phase 4: User Story 2 - 验证数据库连接能访问dim schema (Priority: P1)

**Goal**: Confirm database connection can access dim schema tables (sim_network_edges, multiscale_node_units, point_gantry) for future edge selector functionality

**Independent Test**:
- Run test script: `python shared/data_access/test_dim_schema.py`
- Script connects to database successfully
- All 3 table queries return count > 0
- No connection errors

### Implementation for User Story 2

- [X] T031 [US2] Create test_dim_schema.py in shared/data_access/ with database connection test logic
- [X] T032 [US2] Add query test for dim.sim_network_edges table with count output
- [X] T033 [US2] Add query test for dim.multiscale_node_units table with count output
- [X] T034 [US2] Add query test for dim.point_gantry table with count output
- [X] T035 [US2] Add error handling and diagnostic messages for connection failures

**Checkpoint**: Database access verified - ready for Phase 1B edge selector development

---

## Phase 5: User Story 3 - 前端页面框架提供导航切换能力 (Priority: P2)

**Goal**: Provide frontend navigation framework allowing users to switch between different modules (strategy management, plan management, batch simulation, optimization analysis)

**Independent Test**:
- Open http://localhost:8000/control/index.html
- Navigation menu displays 4 options
- Clicking navigation switches views correctly
- Page refresh preserves active view

### Implementation for User Story 3

- [X] T036 [US3] Update index.html in frontend/control/ to add navigation buttons with data-view attributes
- [X] T037 [US3] Add 4 view sections (strategies, plans, batch, optimization) to frontend/control/index.html
- [X] T038 [US3] Update styles.css in frontend/control/ with navigation button styles and view switching animations
- [X] T039 [US3] Update app.js in frontend/control/ to implement navigation click handlers
- [X] T040 [US3] Add sessionStorage logic to app.js for preserving active view on page refresh

**Checkpoint**: Frontend navigation fully functional - users can explore module structure

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification and validation that all Phase 0 requirements are met

- [ ] T041 [P] Verify all 7 directories exist using file system check
- [ ] T042 [P] Verify all 4 data models can be imported: `from api.models.control import ControlTemplate, Strategy, Plan, BatchSimulation`
- [ ] T043 [P] Run type checking on api/models/control/ using mypy (expect 0 errors)
- [ ] T044 [P] Verify API server starts without errors: `python api/main.py`
- [ ] T045 [P] Verify /api/v1/control/strategies/ returns {"total": 0, "items": []} via curl/browser
- [ ] T046 [P] Verify /api/v1/control/templates/ returns [] via curl/browser
- [ ] T047 [P] Verify API docs show "交通管控" tag at http://localhost:8000/docs
- [ ] T048 [P] Verify frontend page loads at http://localhost:8000/control/index.html
- [ ] T049 [P] Verify navigation buttons switch views in browser
- [ ] T050 [P] Verify database test script runs successfully: `python shared/data_access/test_dim_schema.py`
- [ ] T051 [P] 使用 pydocstyle 验证所有路由函数都有文档字符串
- [ ] T052 Update quickstart.md verification checklist with actual test results (optional)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
  - Creates all required directory structures

- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all data model work
  - Defines enums needed by data models

- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
  - Creates data models (needs enums from Phase 2)
  - Creates API routes (needs models)
  - Creates frontend skeleton

- **User Story 2 (Phase 4)**: Depends on Setup completion - INDEPENDENT of User Story 1
  - Only needs shared/data_access/ directory (from Setup)
  - Can run in parallel with User Story 1 if team capacity allows

- **User Story 3 (Phase 5)**: Depends on User Story 1 frontend skeleton
  - Enhances frontend/control/index.html created in US1

- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on Setup (Phase 1) - INDEPENDENT of User Story 1 (can run in parallel)
- **User Story 3 (P2)**: Depends on User Story 1 frontend skeleton - Cannot start until US1 frontend files exist

### Within Each User Story

#### User Story 1 Internal Dependencies
- T012-T013 (init files) BEFORE T014-T017 (model files)
- T014-T017 (models) can run in parallel [P]
- T018-T019 (exports) AFTER models complete
- T020-T024 (routes) can start after T010-T011 (enums) - route order sequential
- T025-T027 (services) can run in parallel with routes [P]
- T028-T030 (frontend) can run in parallel with API work [P]

#### User Story 2 Internal Dependencies
- T031-T035 are sequential (building up test script)

#### User Story 3 Internal Dependencies
- T036-T040 are sequential (enhancing frontend files)

### Parallel Opportunities

**Phase 1 (Setup)**: Tasks T002-T009 can run in parallel [P]

**Phase 2 (Foundational)**: Tasks T010-T011 are quick, run sequentially

**Phase 3 (User Story 1)**:
- After init files (T012-T013): T014-T017 can run in parallel [P] (different model files)
- After enums ready: T025-T027 can run in parallel [P] with T020-T024 (services vs routes)
- After enums ready: T028-T030 can run in parallel [P] with API work (frontend vs backend)

**Phase 4 (User Story 2)**: Can run in parallel with Phase 3 if multiple developers

**Phase 6 (Polish)**: Tasks T041-T050 can run in parallel [P] (independent verification checks)

---

## Parallel Example: User Story 1

```bash
# After Phase 2 (Foundational) completes, launch in parallel:

# Parallel Group 1: Data models (after init files)
Task: "[US1] Create ControlTemplate model in api/models/control/entities/template.py"
Task: "[US1] Create Strategy model in api/models/control/entities/strategy.py"
Task: "[US1] Create Plan model in api/models/control/entities/plan.py"
Task: "[US1] Create BatchSimulation model in api/models/control/entities/batch_simulation.py"

# Parallel Group 2: API services (independent of routes)
Task: "[US1] Create ControlStrategyService class in api/services/control/control_strategy_service.py"

# Parallel Group 3: Frontend skeleton (independent of backend)
Task: "[US1] Create index.html in frontend/control/"
Task: "[US1] Create styles.css in frontend/control/"
Task: "[US1] Create app.js in frontend/control/"
```

---

## Parallel Example: Cross-Story (with multiple developers)

```bash
# After Phase 2 completes, two developers can work in parallel:

# Developer A: User Story 1 (Infrastructure)
Task: "[US1] Create data models..."
Task: "[US1] Create API routes..."
Task: "[US1] Create frontend skeleton..."

# Developer B: User Story 2 (Database Test) - INDEPENDENT
Task: "[US2] Create test_dim_schema.py..."
Task: "[US2] Add query tests..."
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

**Recommended for Phase 0 - delivers complete infrastructure:**

1. ✅ Complete Phase 1: Setup (directories)
2. ✅ Complete Phase 2: Foundational (enums)
3. ✅ Complete Phase 3: User Story 1 (models + API + frontend skeleton)
4. ✅ Complete Phase 4: User Story 2 (database test)
5. **STOP and VALIDATE**:
   - All models defined and pass type checking
   - All API routes accessible (empty data)
   - Database connection verified
   - Frontend page loads
6. ✅ Ready for Phase 1A (strategy templates)

### Incremental Delivery

1. **Foundation**: Setup + Foundational → Directory structure + Enums ready
2. **Core Infrastructure**: User Story 1 → Models + API + Frontend skeleton
3. **Database Validation**: User Story 2 → Database access verified
4. **Enhanced Frontend**: User Story 3 → Navigation fully functional
5. **Validation**: Polish → All checks pass

### Parallel Team Strategy

With 2 developers:

1. **Together**: Complete Setup + Foundational (quick, ~30 min)
2. **Once Foundational is done**:
   - **Developer A**: User Story 1 (models + API + frontend skeleton)
   - **Developer B**: User Story 2 (database test) - INDEPENDENT
3. **After US1 complete**:
   - **Developer A or B**: User Story 3 (frontend navigation)
4. **Together**: Phase 6 validation

**Time Estimate**: 2-3 hours total (per quickstart.md)

---

## Notes

- **[P] tasks** = different files, no dependencies within same phase
- **[Story] label** maps task to specific user story for traceability
- **Tests NOT included** - Phase 0 is scaffolding only (tests in spec.md Out of Scope)
- **Empty routes return empty data** - not 404/500 (design decision from research.md)
- **Type checking is validation** - replaces unit tests for Phase 0 (per plan.md)
- Each user story should be independently completable and testable
- Commit after each logical group of tasks
- Stop at any checkpoint to validate story independently
- **Phase 0 delivers foundation only** - business logic in Phase 1-4

---

## Success Metrics

Per spec.md Success Criteria:

- **SC-001**: 7 directories created (100% success rate)
- **SC-002**: API routes return 200 + empty data (<500ms response)
- **SC-003**: 4 data models pass type checking (0 errors)
- **SC-004**: Database test queries 3 tables (100% success, count > 0 each)
- **SC-005**: Frontend page loads (<2s), navigation switches views (<100ms)
- **SC-006**: Phase 1-4 can proceed without Phase 0 refactoring (0 changes needed)

**Definition of Done**:
- All 52 tasks completed
- All 6 success criteria met
- quickstart.md verification checklist 100% pass
- Ready to proceed with `/speckit.implement` or manual Phase 1A development
