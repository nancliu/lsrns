<!-- OPENSPEC:START -->

# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:

- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:

- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OD数据处理与仿真系统 (OD Data Processing and Simulation System) - A modular traffic simulation and analysis platform for Origin-Destination (OD) data processing using SUMO (Simulation of Urban MObility). The system manages cases, runs traffic simulations, and performs multiple types of analysis (accuracy, mechanism, performance, EdgeData).

**Current Version**: v0.9.0
**Language**: Python 3.10+
**Framework**: FastAPI + Pydantic
**Platform**: Windows 10/11

## Principles & Rules Quick Reference

This project follows a structured set of principles, rules, and standards with unique identifiers for easy reference.

### Architecture Principles

- **PRINCIPLE-ARCH-001**: Single Responsibility Principle → [Details](#principle-arch-001-single-responsibility-principle)
- **PRINCIPLE-ARCH-002**: Dependency Direction Rule → [Details](#principle-arch-002-dependency-direction-rule)
- **PRINCIPLE-ARCH-003**: Service Locator Pattern → [Details](#principle-arch-003-service-locator-pattern)
- **PRINCIPLE-ARCH-004**: Dependency Injection for Services → [Details](#principle-arch-004-dependency-injection-for-services)
- **PRINCIPLE-ARCH-005**: No Circular Dependencies → [Details](#principle-arch-005-no-circular-dependencies)

### Project Rules

- **RULE-ROOT-001**: Project Root Directory Policy → [Details](#project-root-directory-policy)
- **RULE-FE-001**: Frontend Data Rules (No Hardcoded Data) → [Details](#frontend-data-rules-no-hardcoded-data--no-duplicate-code)
- **RULE-E2E-001**: E2E Testing Best Practices → [Details](openspec/project.md#e2e-testing-best-practices-rule-e2e-001)

### Code Standards

- **STANDARD-CODE-001**: Python Code Quality Standards → [Details](#standard-code-001-python-code-quality-standards)
  - Includes naming conventions (snake_case, PascalCase, etc.)

### Common Pitfalls

- **Architecture Violations**:
  - PITFALL-ARCH-001: Circular Dependencies → [Details](#pitfall-arch-001-circular-dependencies)
  - PITFALL-ARCH-002: Reverse Dependency Flow → [Details](#pitfall-arch-002-reverse-dependency-flow)
  - PITFALL-ARCH-003: Mixed API Versions → [Details](#pitfall-arch-003-mixed-api-versions)
- **Code Quality Issues**:
  - PITFALL-CODE-001: Using Deprecated Functions → [Details](#pitfall-code-001-using-deprecated-functions)
  - PITFALL-CODE-002: Hardcoded Configuration → [Details](#pitfall-code-002-hardcoded-configuration)
  - PITFALL-CODE-003: Using print() Instead of Logging → [Details](#pitfall-code-003-using-print-instead-of-logging)
  - PITFALL-CODE-004: Deprecated Database Connection → [Details](#pitfall-code-004-deprecated-database-connection)
- **Frontend Issues**:
  - PITFALL-FE-002: Inline Styles in HTML → [Details](#pitfall-fe-002-inline-styles-in-html)
  - PITFALL-FE-003: Violating Single Responsibility (Functions) → [Details](#pitfall-fe-003-violating-single-responsibility-functions)
  - PITFALL-FE-004: Deep Callback Nesting → [Details](#pitfall-fe-004-deep-callback-nesting)
- **Environment & Tools**:
  - PITFALL-ENV-001: Wrong Conda Environment → [Details](#pitfall-env-001-wrong-conda-environment)
  - PITFALL-ENV-002: Working in Legacy Directories → [Details](#pitfall-env-002-working-in-legacy-directories)
- **File Organization**:
  - PITFALL-FILE-001: Root Directory Pollution → [Details](#pitfall-file-001-root-directory-pollution)

### Architecture Decision Records

- **ADR-001**: Two-Layer Modular Architecture → [Details](#adr-001-two-layer-modular-architecture)
- **ADR-002**: FastAPI + Pydantic → [Details](#adr-002-fastapi--pydantic-for-api-framework)
- **ADR-003**: Connection Pooling → [Details](#adr-003-connection-pooling-for-database-access)
- **ADR-004**: Two-Step Simulation Workflow → [Details](#adr-004-two-step-simulation-workflow-prepare--start)
- **ADR-005**: JSON Templates for Configuration → [Details](#adr-005-json-templates-for-configuration)
- **ADR-006**: E2E Tests Use Production Data → [Details](#adr-006-e2e-tests-use-production-data)

---

## Architecture

### High-Level Design

The system uses a **two-layer modular architecture**:

**Critical**: API layer calls Shared layer, never the reverse. No circular dependencies allowed. see ADR-001

### API Layer Structure

```
api/
├── main.py              # FastAPI entry point (ONLY entry point)
├── routes/              # Route definitions by business domain
│   ├── data_routes.py       # OD data processing routes
│   ├── case_routes.py       # Case management routes
│   ├── simulation_routes.py # Simulation control routes
│   ├── analysis_routes.py   # Analysis routes
│   ├── template_routes.py   # Template management routes
│   └── file_routes.py       # File operations routes
├── services/            # Business logic layer (calls shared/)
│   ├── base_service.py
│   ├── data_service.py
│   ├── case_service.py
│   ├── simulation_service.py
│   ├── accuracy_service.py
│   ├── mechanism_service.py
│   ├── performance_service.py
│   ├── edgedata_service.py
│   └── template_service.py
└── models/              # Data models and validation
    ├── requests/        # Request models (Pydantic)
    ├── responses/       # Response models (Pydantic)
    ├── entities/        # Domain entities
    ├── base.py          # Base models
    └── enums.py         # Enumerations
```

### Shared Layer Structure

```
shared/
├── utilities/           # Generic utility functions
│   ├── file_utils.py        # File operations
│   ├── time_utils.py        # Time/date handling
│   ├── sumo_utils.py        # SUMO simulation utilities
│   ├── validation_utils.py  # Validation helpers
│   ├── taz_utils.py         # TAZ (Traffic Analysis Zone) processing
│   └── data_flow_optimizer.py
├── data_access/         # Data access layer
│   ├── connection.py        # Database connection management
│   ├── db_config.py         # Database configuration
│   ├── gantry_loader.py     # Gantry data loading from DB
│   └── od_table_resolver.py # OD table resolution
├── analysis_tools/      # Analysis algorithms
│   ├── accuracy_analysis.py    # Accuracy metrics (MAPE, GEH, etc.)
│   ├── mechanism_analysis.py   # Traffic flow mechanism analysis
│   ├── performance_analysis.py # System performance evaluation
│   └── edgedata_analysis.py    # SUMO EdgeData analysis
└── data_processors/     # Core data processing
    ├── od_processor.py          # OD data processing
    ├── e1_processor.py          # E1 detector data
    ├── gantry_processor.py      # Gantry data processing
    └── simulation_processor.py  # Simulation result processing
```

### Key Architectural Principles

#### PRINCIPLE-ARCH-001: Single Responsibility Principle

Each module has one clear purpose. Check: Can module name be described with one verb? If >10 classes/functions, consider splitting.

#### PRINCIPLE-ARCH-002: Dependency Direction Rule

Dependencies flow ONE direction: `api/` → `shared/`. Never reverse. Check: `grep -r "from api" shared/` (should return empty).

#### PRINCIPLE-ARCH-003: Service Locator Pattern

All services managed in `api/services/__init__.py`. Import: `from api.services import data_service` (not direct class import).

#### PRINCIPLE-ARCH-004: Dependency Injection for Services

Services receive dependencies via constructor parameters, not by creating them internally. Enables testing and loose coupling.

#### PRINCIPLE-ARCH-005: No Circular Dependencies

No circular imports. Check: `pydeps api/ --show-cycles`. Solution: Use dependency injection or `TYPE_CHECKING` for type hints only.

## Architecture Decision Records (ADR)

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | Two-Layer Architecture: `api/` (HTTP) → `shared/` (business logic) | ✅ Implemented |
| ADR-002 | FastAPI + Pydantic for API framework (async, validation, auto-docs) | ✅ Implemented |
| ADR-003 | SQLAlchemy connection pooling (90% performance improvement) | ✅ Implemented |
| ADR-004 | Two-step simulation: prepare → start (allows config inspection) | ✅ Implemented |
| ADR-005 | JSON templates for vehicle types (runtime configuration) | ✅ Implemented |
| ADR-006 | E2E tests use production data (no fixtures, real scenarios) | ✅ Implemented |


## Development Workflow

**Layer Selection**: Core logic → `shared/`, Business workflow → `api/services/`, HTTP endpoint → `api/routes/`

**Development Order**: `shared/` → `api/models/` → `api/services/` → `api/routes/`

**Service Mapping**: Data → `data_service.py`, Case → `case_service.py`, Simulation → `simulation_service.py`, Analysis → `*_analysis_service.py`, Templates → `template_service.py`

## Essential Commands

**Start**: `.\start_api.ps1` → http://localhost:8000 (API/docs/frontend)

**Testing**: `conda activate od_project` → `pytest` (unit) or `npx playwright test` (E2E)

**Dependencies**: `mamba install -y -c conda-forge --file requirements.txt` then `pip install -r requirements.txt`

**Code Quality**: `black api/ shared/`, `flake8 api/ shared/`

## Critical Implementation Details

**Simulation Workflow**: Two-step model (v0.9.0+): `prepare_simulation` → `start_simulation`. Legacy one-step API internally calls both.

**SUMO Config**: Use `shared/utilities/sumo_utils.generate_sumocfg_for_simulation()`. Deprecated: `simulation_processor.generate_sumocfg()`.

**Vehicle Types**: Defined in `templates/config_templates/vehicle_templates/vehicle_types.json`. Never hardcode.

**Metadata**: Three levels - Case (`metadata.json`), Simulation Index (`simulations_index.json`), Simulation Metadata (`simulation_metadata.json`). Analysis workflows MUST NOT modify case/simulation metadata.

## Code Standards

### STANDARD-CODE-001: Python Code Quality Standards

#### Function/Method Limits

- Max function length: 30 lines
- Max parameters: 5
- Max nesting depth: 3 levels
- Max class length: 300 lines
- Suggest split if >10 methods

#### Naming Conventions

- **Variables/Functions**: snake_case (`process_gantry_data`)
- **Classes**: PascalCase (`GantryDataProcessor`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- **Files**: snake_case (`gantry_processor.py`)
- **Private methods**: prefix with underscore (`_process_data`)

#### Required Practices

- Type hints on all functions (parameters and return values)
- Docstrings required (Google style)
- No `print()` statements (use logging) - see PITFALL-CODE-003
- Use pandas vectorized operations (avoid Python loops for data processing)
- Early returns for error handling
- No broad except clauses

#### Code Quality Tools

- **Formatter**: black
- **Linter**: flake8 (also consider ruff)
- **Line length**: 100 characters max
- **Indentation**: 4 spaces

## Frontend Development Standards

### CSS and HTML Separation

- No inline styles (`style=""` attributes). All CSS in separate files in `frontend/control/css/`
- Semantic HTML structure with meaningful class/id attributes

### JavaScript Function Standards

- **SRP**: Each function has ONE responsibility (max 30 lines, max 5 params, max 3 nesting levels)
- **Naming**: Descriptive camelCase (`updateRouteDropdown()`, not `handle()`)
- **Organization**: One feature per file, avoid files >300 lines

### Frontend Data Rules (RULE-FE-001)

- No hardcoded data in HTML (use `value` from `schema.default_value`, not `placeholder`)
- No duplicate functions (single source of truth)
- All data must be traceable to template JSON
- Functions must be parameterized (no hardcoded values)

## Environment and External Dependencies

**SUMO**: Set `SUMO_HOME` or `SUMO_BIN` (v1.19+). Add `%SUMO_HOME%\bin` to PATH.

**Python**: Use `od_project` conda environment (Python 3.10+, Playwright). Always activate: `conda activate od_project`. Never use base environment.

**Database**: Environment variables at OS level. Use connection pooling (`shared/data_access/connection.py`). Schemas: `dim` (network), `baseline` (traffic flow).

## File Paths and Conventions

**Case Structure**: `cases/{case_id}/` contains `config/`, `simulations/{sim_id}/`, `analysis/`, `metadata.json`

**Path Handling**: Use `pathlib.Path` (cross-platform). Absolute paths for external tools (SUMO), relative paths in metadata/config.

## Project Root Directory Policy (RULE-ROOT-001)

**Allowed**: `CLAUDE.md`, `README.md`, `requirements.txt`, `start_api.*`, config files

**Prohibited**: Analysis reports, logs, test scripts, generated code

**Organization**: Docs → `docs/`, Tests → `tests/`, Code → `api/`/`shared/`/`frontend/`

## Templates and Configuration

**Available**: TAZ (`templates/taz_files/`), Network (`templates/network_files/`), Simulation configs, Vehicle types (`vehicle_types.json`), EdgeData config

**Usage**: Templates copied/referenced during case creation. Never modify directly - copy first.

## Simulation Configuration

**Output Formats**: tripinfo, vehroute, netstate, fcd, emission, edgedata (configurable via `output_config`)

**Duration**: Custom duration (hours/minutes, 1min-24h) or uses case metadata time range. See `shared/utilities/sumo_utils.generate_sumocfg_for_simulation()`

## Analysis Types

**Accuracy**: E1 detector vs observed gantry data (MAPE, GEH, correlation) → `cases/{case_id}/analysis/accuracy/`

**Mechanism**: OD comparisons, speed time series (requires tripinfo/vehroute) → `cases/{case_id}/analysis/mechanism/`

**Performance**: System stats (summary.xml metrics, file sizes) → `cases/{case_id}/analysis/performance/`

**EdgeData**: Road segment statistics (requires output_edgedata) → `cases/{case_id}/analysis/edgedata/`

## Control Strategies

**Types**: VSS (可变限速), TEC (收费站管控), DHS (动态硬路肩)

**Location**: `control_data/strategies/` (JSON files)

**XML Validation**: `shared/control_tools/xml_validator.py` validates SUMO XML (syntax, constraints, strategy-specific rules). Cascade regeneration when strategies update.

## API Endpoint Groups

All endpoints use prefix `/api/v1/`:

- **Data Processing**: `/api/v1/data/*`
- **Case Management**: `/api/v1/case/*`
- **Simulation**: `/api/v1/simulation/*`
- **Analysis**: `/api/v1/analysis/*`
- **Templates**: `/api/v1/template/*`
- **Files**: `/api/v1/file/*`

See [docs/api_docs/新架构API指南.md](docs/api_docs/新架构API指南.md) for complete API documentation.

## Common Pitfalls

**Architecture**: ❌ Circular dependencies (`pydeps --show-cycles`), ❌ `shared/` importing `api/` (`grep -r "from api" shared/`), ❌ Mixed API versions

**Code Quality**: ❌ Deprecated `generate_sumocfg()` (use `sumo_utils.generate_sumocfg_for_simulation()`), ❌ Hardcoded vehicle types (use JSON templates), ❌ `print()` (use `logging`), ❌ `open_db_connection()` (use connection pooling)

**Frontend**: ❌ Inline styles (use separate CSS), ❌ Functions >30 lines or vague names, ❌ Deep callback nesting (use async/await)

**Environment**: ❌ Wrong conda environment (always use `od_project`), ❌ Working in legacy directories (`sim_scripts/`, `accuracy_analysis/`)

**File Organization**: ❌ Root directory pollution (use `docs/`, `tests/`, appropriate subdirectories)

### Quick Reference Checklist

Use this checklist before committing code:

- [ ] No circular dependencies (`pydeps` clean)
- [ ] No reverse imports (`shared/` doesn't import `api/`)
- [ ] Using `sumo_utils.generate_sumocfg_for_simulation()` not deprecated version
- [ ] No hardcoded vehicle types (using JSON template)
- [ ] Using `logging` module, not `print()`
- [ ] Using connection pooling for database access
- [ ] Frontend: No inline styles in HTML
- [ ] Frontend: Functions < 30 lines, single responsibility
- [ ] Frontend: No deep callback nesting (use async/await)
- [ ] Activated `od_project` conda environment
- [ ] No files in legacy directories (`sim_scripts/`, `accuracy_analysis/`)
- [ ] No unorganized files in project root
- [ ] All tests passing in `od_project` environment

### Best Practices

1. **Do** use `pathlib.Path` for file operations
2. **Do** use pandas for data processing (vectorized operations)
3. **Do** validate inputs using Pydantic models
4. **Do** log important operations and errors
5. **Do** return structured data (dicts/models) from services
6. **Do** handle errors gracefully (return empty structures, don't raise)
7. **Do** check if files exist before reading
8. **Do** use mamba for dependency installation, pip as fallback

