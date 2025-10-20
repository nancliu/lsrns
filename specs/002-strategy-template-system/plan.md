# Implementation Plan: Strategy Template System (Phase 1A)

**Branch**: `002-strategy-template-system` | **Date**: 2025-10-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-strategy-template-system/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a read-only strategy template browsing system that enables traffic engineers to discover and understand available traffic control strategies (VSS, DHS, TEC). The system will:
- Store 5 template JSON files (VSS: 2 variants, DHS: 1, TEC: 2 variants) with parameter schemas
- Provide TemplateLoader utility for loading, validating, and retrieving templates
- Expose 2 REST API endpoints (GET /control/templates/, GET /control/templates/{id})
- Display template cards with modal detail view on frontend

Technical approach: File-based JSON storage with auto-generated index, FastAPI REST endpoints, vanilla JavaScript frontend with modal dialog pattern.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI (web framework), Pydantic (data validation), pathlib (file operations)
**Storage**: File-based (JSON templates in `templates/control_strategies/`, auto-generated index)
**Testing**: pytest (unit + integration tests), test coverage ≥80% for shared utilities, 100% for API endpoints
**Target Platform**: Windows 10/11 (development), HTTP API accessible via browser (frontend)
**Project Type**: Web (FastAPI backend + vanilla JS frontend)
**Performance Goals**: Template list load <1s, template detail load <500ms, startup template validation <2s
**Constraints**: Read-only template access, no database dependencies, Chinese-only UI, 5 initial templates
**Scale/Scope**: 5 templates Phase 1A (expandable manually), 2 API endpoints, 1 frontend page with modal

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Layered Architecture** | ✅ PASS | New code follows API → Shared dependency: `api/routes/control_template_routes.py` → `api/services/control_template_service.py` → `shared/control_tools/template_loader.py`. No circular dependencies. |
| **II. Module Isolation** | ✅ PASS | New independent control module (`/api/v1/control/*` endpoints, `control_template_service.py`, `shared/control_tools/template_loader.py`). **Zero modifications** to existing simulation/analysis code. Calls existing APIs only if needed (none required for Phase 1A). |
| **III. Single Responsibility** | ✅ PASS | `control_template_service.py` handles only template management (load/list/validate). Frontend page (`frontend/control/index.html`) manages only control UI. Each function has single purpose (e.g., `load_template()`, `validate_template()`). |
| **IV. Test-First** | ✅ PASS | Commit to TDD workflow: write tests → implement → validate. API integration tests for both endpoints (100% coverage). Unit tests for `template_loader.py` (≥80% coverage). Edge case tests for validation logic. |
| **V. Configuration Over Code** | ✅ PASS | All templates stored as JSON in `templates/control_strategies/`. Parameter schemas define configurable values. No hardcoded strategy parameters. Templates read-only at runtime. |
| **VI. File-Based Storage** | ✅ PASS | Templates stored in file system (`templates/control_strategies/{type}/{name}.json`). Index auto-generated at startup. No database storage for templates. Follows existing pattern for vehicle templates. |

### Gate Decision

**✅ ALL GATES PASSED** - Proceed to Phase 0 research.

**Justification**: This feature perfectly aligns with constitution principles:
- Adds new isolated module without touching existing code (Module Isolation)
- Uses file-based configuration for templates (Configuration Over Code + File-Based Storage)
- Maintains clean layered architecture (API → Shared)
- Commits to test-first development (Test-First)
- Each component has single responsibility (Single Responsibility)

No violations detected. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
api/
├── routes/
│   └── control_template_routes.py      # NEW: GET /api/v1/control/templates/ endpoints
├── services/
│   └── control_template_service.py     # NEW: Template management business logic
└── models/
    └── control/
        ├── entities/
        │   └── template.py              # NEW: ControlTemplate entity
        ├── requests/
        │   └── template_requests.py     # NEW: Request models (if needed)
        └── responses/
            └── template_responses.py    # NEW: Response models

shared/
├── control_tools/
│   └── template_loader.py               # NEW: Template loading, validation, retrieval
└── utilities/
    └── (existing utilities remain untouched)

templates/
└── control_strategies/
    ├── variable_speed_sign/
    │   ├── vss_moderate.json            # NEW: VSS moderate variant
    │   └── vss_strict.json              # NEW: VSS strict variant
    ├── dynamic_hard_shoulder/
    │   └── dhs_peak_hours.json          # NEW: DHS peak hours template
    ├── toll_entrance_control/
    │   ├── tec_truck_ban.json           # NEW: TEC truck ban variant
    │   └── tec_entrance_close.json      # NEW: TEC entrance close variant
    └── templates_index.json             # AUTO-GENERATED at startup

frontend/
└── control/
    ├── index.html                       # NEW: Template browsing page
    ├── styles.css                       # NEW: Control module styles
    └── app.js                           # NEW: Template display logic, modal handling

tests/
├── integration/
│   └── api/
│       └── test_control_template_routes.py  # NEW: API integration tests (100% coverage)
└── unit/
    └── shared/
        └── test_template_loader.py      # NEW: Unit tests (≥80% coverage)
```

**Structure Decision**: Web application following existing OD_SIM architecture (API + Shared + Frontend). All new files are isolated to control module paths (`control/`, `control_tools/`, `control_strategies/`). Zero modifications to existing simulation/analysis code (Module Isolation principle).

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**N/A** - All constitution gates passed. No violations detected. No complexity tracking required.

