# Tasks - Strategy Template System (Phase 1A)

**Feature**: 002-strategy-template-system
**Status**: Ready for Implementation
**Total Tasks**: 61

## Task Organization

Tasks are organized by implementation phases and mapped to user stories:
- **US1**: Browse Available Strategy Templates (Priority 1)
- **US2**: View Detailed Template Information (Priority 2)
- **US3**: System Loads and Validates Templates (Priority 3)

**Legend**:
- `[P]` = Parallelizable (can run concurrently with other [P] tasks)
- `[US#]` = User Story mapping
- Task IDs: T001-T035 (sequential execution order within phase)

---

## Phase 1: Project Setup (Prerequisites)

**Goal**: Initialize project structure and foundational models

- [ ] T001 Create directory structure for control module: `api/models/control/`, `api/models/control/entities/`, `shared/control_tools/`
- [ ] T002 Create directory structure for templates: `templates/control_strategies/variable_speed_sign/`, `templates/control_strategies/dynamic_hard_shoulder/`, `templates/control_strategies/toll_entrance_control/`
- [ ] T003 Create directory structure for frontend: `frontend/control/`
- [ ] T004 Create directory structure for tests: `tests/unit/shared/`, `tests/integration/api/`
- [ ] T005 Create StrategyType enum in `api/models/control/entities/template.py`
- [ ] T006 Create ParameterSchema Pydantic model in `api/models/control/entities/template.py`
- [ ] T007 Create ControlTemplate Pydantic model with validators in `api/models/control/entities/template.py`
- [ ] T008 Create TemplateIndexEntry and TemplatesIndex Pydantic models in `api/models/control/entities/template.py`
- [ ] T009 Create response models in `api/models/control/responses/template_responses.py` with TemplateListResponse, TemplateDetailResponse, and ErrorResponse classes

---

## Phase 2: Foundational Tools (Blocking Prerequisites)

**Goal**: Implement template loading and validation (required by all user stories)

**TDD Workflow**: Tests written first (T010-T013) → Implementation (T014-T022) → Tests pass

### Test-First: Write Core Tests (Constitution Principle IV)

- [ ] T010 Write unit test `test_load_valid_template()` in `tests/unit/shared/test_template_loader.py`
- [ ] T011 Write unit test `test_validate_template_missing_field()` in `tests/unit/shared/test_template_loader.py`
- [ ] T012 Write unit test `test_generate_index()` in `tests/unit/shared/test_template_loader.py`
- [ ] T013 Write unit test `test_unique_id_constraint()` in `tests/unit/shared/test_template_loader.py`

### Implementation: Make Tests Pass

- [ ] T014 Implement `_load_json_file()` helper in `shared/control_tools/template_loader.py`
- [ ] T015 Implement `_validate_template_structure()` with Pydantic validation in `shared/control_tools/template_loader.py`
- [ ] T016 Implement `_validate_parameter_schema()` with type checking in `shared/control_tools/template_loader.py`
- [ ] T017 Implement `validate_template()` multi-layer validation in `shared/control_tools/template_loader.py`
- [ ] T018 Implement `load_template_from_file()` with error handling in `shared/control_tools/template_loader.py`
- [ ] T019 Implement `scan_template_directory()` recursive file scanner in `shared/control_tools/template_loader.py`
- [ ] T020 Implement `generate_templates_index()` with auto-generation logic in `shared/control_tools/template_loader.py`
- [ ] T021 Implement `list_all_templates()` with index loading/generation in `shared/control_tools/template_loader.py`
- [ ] T022 Implement `get_template_by_id()` with file lookup in `shared/control_tools/template_loader.py`

---

## Phase 3: User Story 1 - Browse Available Strategy Templates (P1)

**Goal**: Implement template listing API and frontend display

### Backend (US1)

- [ ] T023 [US1] Create ControlTemplateService class in `api/services/control_template_service.py`
- [ ] T024 [US1] Implement `list_templates()` method calling TemplateLoader in `api/services/control_template_service.py`
- [ ] T025 [US1] Create APIRouter with `/api/v1/control` prefix in `api/routes/control_template_routes.py`
- [ ] T026 [US1] Implement `GET /templates/` endpoint with response model in `api/routes/control_template_routes.py`
- [ ] T027 [US1] Register control routes in `api/main.py` app.include_router()
- [ ] T028 [US1] Write integration test `test_get_templates_returns_all_valid_templates()` in `tests/integration/api/test_control_template_routes.py`

### Frontend (US1)

- [ ] T029 [P] [US1] Create HTML structure with template card grid in `frontend/control/index.html`
- [ ] T030 [P] [US1] Implement CSS for card layout and responsive design in `frontend/control/styles.css`
- [ ] T031 [P] [US1] Implement `fetchTemplates()` API call in `frontend/control/app.js`
- [ ] T032 [P] [US1] Implement `renderTemplateCards()` dynamic card generation in `frontend/control/app.js`
- [ ] T033 [P] [US1] Add navigation link to control page in `frontend/index.html`

---

## Phase 4: User Story 2 - View Detailed Template Information (P2)

**Goal**: Implement template detail API and modal dialog

### Backend (US2)

- [ ] T034 [US2] Implement `get_template_by_id()` method in `api/services/control_template_service.py`
- [ ] T035 [US2] Implement `GET /templates/{template_id}` endpoint with 404 handling in `api/routes/control_template_routes.py`
- [ ] T036 [US2] Write integration test `test_get_template_by_id_returns_full_details()` in `tests/integration/api/test_control_template_routes.py`
- [ ] T037 [US2] Write integration test `test_get_template_invalid_id_returns_404()` in `tests/integration/api/test_control_template_routes.py`

### Frontend (US2)

- [ ] T038 [P] [US2] Create modal HTML structure with close button in `frontend/control/index.html`
- [ ] T039 [P] [US2] Implement CSS for modal overlay and content styling in `frontend/control/styles.css`
- [ ] T040 [P] [US2] Implement `showTemplateDetail(templateId)` with fetch call in `frontend/control/app.js`
- [ ] T041 [P] [US2] Implement `renderTemplateDetail(template)` parameter table generation in `frontend/control/app.js`
- [ ] T042 [P] [US2] Implement modal open/close event handlers with ESC key support in `frontend/control/app.js`

---

## Phase 5: User Story 3 - System Validation (P3)

**Goal**: Create template files and implement robust validation

### Template Files (US3)

- [ ] T043 [P] [US3] Create VSS moderate template with 5 parameters in `templates/control_strategies/variable_speed_sign/vss_moderate.json`
- [ ] T044 [P] [US3] Create VSS strict template with 5 parameters in `templates/control_strategies/variable_speed_sign/vss_strict.json`
- [ ] T045 [P] [US3] Create DHS peak hours template with 4 parameters in `templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json`
- [ ] T046 [P] [US3] Create TEC truck ban template with 4 parameters in `templates/control_strategies/toll_entrance_control/tec_truck_ban.json`
- [ ] T047 [P] [US3] Create TEC entrance close template with 3 parameters in `templates/control_strategies/toll_entrance_control/tec_entrance_close.json`

### Validation & Error Handling (US3)

- [ ] T048 [US3] Add logging for template validation errors in `shared/control_tools/template_loader.py`
- [ ] T049 [US3] Implement graceful degradation (reject invalid, keep valid) in `shared/control_tools/template_loader.py`
- [ ] T050 [US3] Add structured error responses (JSON format) in `api/routes/control_template_routes.py`
- [ ] T051 [US3] Write unit test `test_graceful_degradation_invalid_templates()` in `tests/unit/shared/test_template_loader.py`
- [ ] T052 [US3] Write integration test `test_api_error_format()` in `tests/integration/api/test_control_template_routes.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation, testing, and documentation

### Testing & Validation

- [ ] T053 Run all unit tests and verify ≥80% coverage for `shared/control_tools/template_loader.py`
- [ ] T054 Run all integration tests and verify 100% pass rate for control API endpoints
- [ ] T055 Verify startup template index auto-generation (delete index, restart API, check regeneration)
- [ ] T056 Manual test: Access `http://localhost:8000/control/index.html` and verify 5 template cards display
- [ ] T057 Manual test: Click each template card and verify modal shows complete parameter details

### Documentation & Finalization

- [ ] T058 Update `CLAUDE.md` with control module documentation (API endpoints, file paths, development patterns)
- [ ] T059 Verify quickstart.md matches actual implementation (file paths, code examples)
- [ ] T060 Create commit following constitution git protocol with message ending in Claude Code attribution
- [ ] T061 Verify constitution compliance: No modifications to existing files outside `api/routes/`, `api/services/`, `shared/control_tools/`, `frontend/control/`

---

## Task Dependencies Summary

**Critical Path**:
```
T001-T008 (Setup)
  → T009 (Response models)
    → T010-T022 (TemplateLoader: tests → implementation, TDD workflow)
      → T023-T028 (US1 backend)
        → T029-T033 (US1 frontend, parallel)
      → T034-T037 (US2 backend)
        → T038-T042 (US2 frontend, parallel)
      → T043-T052 (US3 templates + validation)
        → T053-T061 (Polish & finalization)
```

**Parallelization Opportunities**:
- T029-T033 (US1 frontend) can run parallel with T034-T037 (US2 backend)
- T038-T042 (US2 frontend) can run parallel with T043-T047 (template files)
- T043-T047 (5 template files) can all be created in parallel

---

## Success Criteria Checklist

**Functional Requirements**:
- [ ] FR-001: System provides 5 strategy templates (VSS 2, DHS 1, TEC 2)
- [ ] FR-002: GET /control/templates/ returns all templates with metadata
- [ ] FR-003: GET /control/templates/{id} returns full template details
- [ ] FR-004: Templates stored in file system (not database)
- [ ] FR-005: TemplateLoader validates all templates at startup
- [ ] FR-006: Frontend displays template cards with strategy type badges
- [ ] FR-007: Modal dialog shows complete parameter information

**Non-Functional Requirements**:
- [ ] NFR-001: Template list API responds <1 second
- [ ] NFR-002: Template detail API responds <500ms
- [ ] NFR-003: Startup template validation completes <2 seconds
- [ ] NFR-004: API test coverage = 100%
- [ ] NFR-005: Unit test coverage ≥80%
- [ ] NFR-006: Zero modifications to existing simulation/case/analysis code

**Constitution Compliance**:
- [ ] Module Isolation: All code in new `control/` paths
- [ ] Layered Architecture: API → Shared dependency flow maintained
- [ ] Test-First: Tests written before implementation
- [ ] File-Based Storage: Templates stored as JSON files
- [ ] Single Responsibility: TemplateLoader only handles template management

---

**Total Estimated Effort**: 8-12 hours
**Recommended Approach**: Follow phases sequentially, parallelize within phases where marked [P]
