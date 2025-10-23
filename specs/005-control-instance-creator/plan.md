# Implementation Plan: Control Strategy Instance Creator (Phase 1C)

**Branch**: `005-control-instance-creator` | **Date**: 2025-10-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-control-instance-creator/spec.md`

## Summary

Phase 1C implements a complete CRUD system for traffic control strategy instances, bridging Phase 1A (strategy templates) and Phase 1B (edge selector) to enable traffic engineers to create, manage, and configure concrete control strategies. The system stores strategy instances as JSON files in `control_data/strategies/` with a searchable index, provides full REST API endpoints, and extends the existing `/control/index.html` page with a tabbed interface for strategy management.

**Primary Requirements**:
- Create strategy instances from templates with dynamic parameter forms
- List, view, edit, and delete strategy instances with full validation
- Integrate Phase 1B edge selector for target edge selection
- Extend Phase 1A frontend with "Strategy Instances" tab
- File-based storage with searchable index for 100-500 strategies

**Technical Approach**:
- Backend: FastAPI + Pydantic validation, file-based JSON storage
- Frontend: Tab-based UI embedded in existing `/control/index.html`
- Validation: Dual-layer (frontend + backend) using template schemas
- Storage: JSON files + index with optimistic concurrency control

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI 0.104+, Pydantic 2.0+, pathlib (stdlib)
**Storage**: File system (JSON files in `control_data/strategies/`), PostgreSQL (edge validation only)
**Testing**: pytest (unit ≥80%, integration 100%), existing test infrastructure
**Target Platform**: Windows 10/11 server (existing OD_SIM environment)
**Project Type**: Web application (backend API + frontend JavaScript)
**Performance Goals**:
- API response <2 seconds for all endpoints
- Strategy list load <1 second with 100+ strategies
- Frontend validation <200ms
- Edge detail loading <2 seconds

**Constraints**:
- No authentication system (use system identifier for created_by)
- File-based storage only (no database for strategy data)
- Must not modify existing Phase 1A/1B code (Module Isolation principle)
- Optimistic concurrency control (timestamp-based, no locking)
- Single-page tab integration (extend existing `/control/index.html`)

**Scale/Scope**:
- Target: 100-500 strategy instances
- Pagination: 20 strategies per page
- Template integration: 5 templates from Phase 1A
- Edge selection: Hundreds of edges per strategy (from Phase 1B)
- 44 functional requirements, 4 key entities, 10 success criteria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Layered Architecture (NON-NEGOTIABLE)

**Status**: PASS

- API layer in `api/services/control_strategy_service.py`, `api/routes/control_strategy_routes.py`
- Shared layer in `shared/control_tools/parameter_validator.py`, `shared/control_tools/strategy_file_manager.py`
- Dependency flow: API → Shared ✅
- No circular dependencies ✅

### ✅ II. Module Isolation (NON-NEGOTIABLE)

**Status**: PASS

**API Layer**:
- ✅ New files only: `api/services/control_strategy_service.py`, `api/routes/control_strategy_routes.py`
- ✅ New API prefix: `/api/v1/control/strategies/*`
- ✅ Calls existing APIs: GET `/api/v1/control/templates/{id}` (Phase 1A), edge query functions (Phase 1B)
- ❌ NO modifications to existing service/route files
- ✅ Integration tests required (100% pass rate)

**Shared Layer**:
- ✅ New tools only: `shared/control_tools/parameter_validator.py`, `shared/control_tools/strategy_file_manager.py`
- ✅ Uses existing tools: `shared/data_access/edge_query.py` (Phase 1B, no modifications)
- ❌ NO function signature changes
- ✅ Unit tests required (≥80% coverage)

**Frontend**:
- ✅ Extends existing `/control/index.html` (Phase 1A) with new tab
- ✅ New JavaScript files: `frontend/control/js/strategy_manager.js`
- ❌ NO modifications to Phase 1A template browsing code

### ✅ III. Single Responsibility

**Status**: PASS

- `control_strategy_service.py`: Strategy instance business logic only (no template management, no edge queries)
- `parameter_validator.py`: Parameter validation only (reuses template schemas)
- `strategy_file_manager.py`: File I/O operations only (JSON read/write, index management)
- API routes grouped: `/control/strategies/*` (separate from `/control/templates/*`)
- Frontend: Tab separation (Templates vs. Strategy Instances)

### ✅ IV. Test-First (NON-NEGOTIABLE)

**Status**: COMPLIANT

**Test Requirements**:
- API integration tests: 100% pass rate for all 7 endpoints (POST, GET list, GET detail, PUT, DELETE, plus metadata endpoints)
- Unit tests: ≥80% coverage for `parameter_validator.py`, `strategy_file_manager.py`
- TDD workflow: Write tests → Tests fail → Implement → Tests pass
- Independent test execution (no external state dependencies)

**Test Coverage Plan**:
- `test_control_strategy_api.py`: All 7 API endpoints
- `test_parameter_validator.py`: Validation rules, edge cases
- `test_strategy_file_manager.py`: File operations, index management, concurrency scenarios

**TDD Implementation**: tasks.md implements full TDD workflow with 38 test tasks (32% of total 118 tasks) written BEFORE implementation tasks. All test tasks include explicit "verify test fails" step.

### ✅ V. Configuration Over Code

**Status**: PASS

- Strategy templates from Phase 1A provide `parameters_schema` (no hard coding)
- Vehicle types from `templates/config_templates/vehicle_templates/vehicle_types.json` (existing)
- No hardcoded parameters in strategy instance logic ✅

### ✅ VI. File-Based Storage (NON-NEGOTIABLE)

**Status**: PASS

- All strategy instances stored as JSON files: `control_data/strategies/{strategy_id}.json` ✅
- Index file: `control_data/strategies/strategies_index.json` ✅
- ❌ NO database storage for strategy data
- ✅ Database used ONLY for edge validation (read-only queries via `shared/data_access/edge_query.py`)

**File Structure**:
```
control_data/strategies/
├── strat_20251021_a3f7b9.json      # Individual strategy instances
├── strat_20251021_b8k2m4.json
├── strat_20251021_c1n5p7.json
└── strategies_index.json            # Searchable metadata index
```

### Constitution Compliance Summary

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layered Architecture | ✅ PASS | API → Shared, no circular deps |
| II. Module Isolation | ✅ PASS | New files only, no existing file modifications |
| III. Single Responsibility | ✅ PASS | Service/tool/route separation clear |
| IV. Test-First | ✅ WILL COMPLY | TDD workflow, 100% API + ≥80% unit tests |
| V. Configuration Over Code | ✅ PASS | Uses Phase 1A template schemas |
| VI. File-Based Storage | ✅ PASS | JSON files, no database storage |

**Overall**: ✅ **APPROVED TO PROCEED**

No complexity violations. No justifications required.

## Project Structure

### Documentation (this feature)

```
specs/005-control-instance-creator/
├── plan.md              # This file (✅ complete)
├── research.md          # Phase 0 output (🔄 in progress)
├── data-model.md        # Phase 1 output (pending)
├── quickstart.md        # Phase 1 output (pending)
├── contracts/           # Phase 1 output (pending)
│   └── strategy_api.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```
# Backend (Python FastAPI)
api/
├── models/
│   ├── requests/
│   │   └── strategy_requests.py         # NEW: StrategyCreateRequest, StrategyUpdateRequest
│   └── responses/
│       └── strategy_responses.py        # NEW: StrategyListResponse, StrategyDetailResponse
├── services/
│   ├── __init__.py                      # EXTEND: Register ControlStrategyService (backward-compatible)
│   └── control_strategy_service.py      # NEW: Strategy CRUD business logic
└── routes/
    └── control_strategy_routes.py       # NEW: /api/v1/control/strategies/* endpoints

shared/
├── control_tools/
│   ├── parameter_validator.py           # NEW: validate_strategy_parameters()
│   └── strategy_file_manager.py         # NEW: File I/O, index management
└── data_access/
    └── edge_query.py                    # EXISTING: Reuse for edge validation (no changes)

# Frontend (HTML/CSS/JavaScript)
frontend/control/
├── index.html                           # EXTEND: Add "Strategy Instances" tab (preserves Phase 1A content)
├── js/
│   ├── app.js                           # EXTEND: Add tab switching logic (backward-compatible)
│   └── strategy_manager.js              # NEW: Strategy CRUD UI logic
└── styles.css                           # EXTEND: Add strategy list/form styles (additive only)

# File Storage
control_data/strategies/                 # NEW: Strategy instance JSON files
├── strat_{timestamp}_{random}.json      # Individual strategies
└── strategies_index.json                # Searchable index

# Tests
tests/
├── integration/
│   └── test_control_strategy_api.py     # NEW: API endpoint tests (100% coverage)
└── unit/
    ├── test_parameter_validator.py      # NEW: Validation logic tests
    └── test_strategy_file_manager.py    # NEW: File I/O tests
```

**Structure Decision**: Web application structure following existing OD_SIM conventions. Backend uses `api/` layer for HTTP endpoints and `shared/` for business logic. Frontend extends existing single-page control interface (`/control/index.html`) with tab-based navigation. Storage layer uses file system (`control_data/strategies/`) with JSON files, consistent with Constitution Principle VI (File-Based Storage).

## Complexity Tracking

*No violations identified. This section intentionally left empty.*
