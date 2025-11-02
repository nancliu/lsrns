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
- **STANDARD-NAMING-001**: Naming Conventions → [Details](#standard-naming-001-naming-conventions)

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

## Essential Commands

### Development

```powershell
# Start API server (includes frontend)
.\start_api.ps1

# Alternative (batch script)
.\start_api.bat

# Direct Python execution
python api\main.py

# Access points
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Frontend: http://localhost:8000/index.html
```

### Testing

**IMPORTANT**: Always activate the `od_project` conda environment before running tests:

```bash
# Activate the correct conda environment first
conda activate od_project

# Run Python unit tests (from project root)
pytest

# Run specific test
pytest tests/unit/test_specific.py

# Run with coverage
pytest --cov=api --cov=shared

# Run Playwright E2E tests (requires od_project environment)
npx playwright test

# Run specific E2E test
npx playwright test tests/e2e/test_dual_layer_canvas.spec.js

# Run E2E tests in headed mode (visible browser)
npx playwright test --headed
```

**Environment Requirements**:

- Python tests: Requires `od_project` conda environment (Python 3.10+)
- Playwright tests: Requires Node.js and Playwright installed (already configured in `od_project` environment)
- **Never run tests in conda base environment**

### Dependencies

```powershell
# Install dependencies (use mamba first, then pip)
mamba install -y -c conda-forge --file requirements.txt
pip install -r requirements.txt
```

### Database Migrations

```powershell
# Apply database migration (from project root)
.\database\apply_migration.ps1 -MigrationFile "004_add_edge_query_indexes.sql"

# Verify indexes exist
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -c "SELECT indexname FROM pg_indexes WHERE tablename = 'sim_network_edges'"
```

### Code Quality

```bash
# Format code
black api/ shared/

# Lint code
flake8 api/ shared/

# Check types (if using mypy)
mypy api/ shared/
```

## Architecture

### High-Level Design

The system uses a **two-layer modular architecture**:

1. **API Layer** (`api/`) - HTTP interface, business coordination, request/response handling
2. **Shared Layer** (`shared/`) - Core business logic, algorithms, data access, reusable utilities

**Critical**: API layer calls Shared layer, never the reverse. No circular dependencies allowed.

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

**定义**: Each module has one clear purpose and reason to change.

**如何检查**:
- Can the module name be described with a single verb phrase?
- Does the module have only one reason to change?
- Run: `grep -r "^class\|^def" <module_file>` - if >10 classes/functions, consider splitting

**违反后果**:
- Code becomes difficult to test in isolation
- Changes have unpredictable side effects
- High coupling between unrelated concerns

**示例**:
- ✅ **Good**: `shared/data_access/gantry_loader.py` - Only loads gantry data from database
- ✅ **Good**: `api/services/accuracy_service.py` - Only orchestrates accuracy analysis workflow
- ❌ **Bad**: `data_handler.py` - Vague name, unclear responsibility
- ❌ **Bad**: A service that handles both file I/O AND database queries AND business logic

#### PRINCIPLE-ARCH-002: Dependency Direction Rule

**定义**: Dependencies flow in ONE direction only: API Layer → Services → Shared Layer

**严格规则**:
- ✅ `api/services/` CAN import from `shared/`
- ✅ `api/routes/` CAN import from `api/services/` and `api/models/`
- ❌ `shared/` MUST NEVER import from `api/`
- ❌ Services MUST NEVER import from routes

**如何检查**:
```bash
# Check if shared/ imports from api/ (should return empty)
grep -r "from api" shared/
grep -r "import api" shared/

# Check if services import from routes (should return empty)
grep -r "from api.routes" api/services/
```

**违反后果**:
- Circular dependencies prevent module initialization
- Cannot test shared layer independently
- Cannot reuse shared logic outside API context
- Tight coupling makes refactoring risky

**依赖流程图**:
```
api/routes/          (HTTP endpoints)
    ↓
api/services/        (Business orchestration)
    ↓
shared/utilities/    (Generic helpers)
shared/data_access/  (Database layer)
shared/analysis_tools/ (Analysis algorithms)
shared/data_processors/ (Core data processing)
```

#### PRINCIPLE-ARCH-003: Service Locator Pattern

**定义**: All service instances are centrally managed through `api/services/__init__.py`

**实现方式**:
```python
# api/services/__init__.py
from .data_service import DataService
from .case_service import CaseService
from .simulation_service import SimulationService

# Singleton instances
data_service = DataService()
case_service = CaseService(data_service)
simulation_service = SimulationService(case_service)
```

**使用方式**:
```python
# api/routes/data_routes.py
from api.services import data_service

@router.post("/process_od")
async def process_od(request: ODRequest):
    return data_service.process_od_data(request)
```

**好处**:
- ✅ Single instance management (singleton pattern)
- ✅ Easy to mock services for testing
- ✅ Clear dependency relationships
- ✅ Centralized initialization and configuration

**如何检查**:
- All service imports should be from `api.services`, not direct module imports
- Search for anti-pattern: `from api.services.data_service import DataService` (should be `from api.services import data_service`)

#### PRINCIPLE-ARCH-004: Dependency Injection for Services

**定义**: Services receive their dependencies through constructor parameters, not by creating them internally

**正确示例**:
```python
# ✅ GOOD: Dependencies injected via constructor
class CaseService:
    def __init__(self, data_service: DataService):
        self.data_service = data_service

    def create_case(self, params):
        od_data = self.data_service.load_od_data()
        # ...
```

**错误示例**:
```python
# ❌ BAD: Service creates its own dependencies
class CaseService:
    def __init__(self):
        self.data_service = DataService()  # Hard-coded dependency!

    def create_case(self, params):
        # ...
```

**好处**:
- ✅ Easy to replace dependencies for testing
- ✅ Clear dependency graph
- ✅ Loose coupling between services
- ✅ Enables composition over inheritance

#### PRINCIPLE-ARCH-005: No Circular Dependencies

**定义**: Module A imports B, B imports C, C MUST NOT import A (direct or indirect)

**如何检查**:
```bash
# Install pydeps if not available
# pip install pydeps

# Check for cycles in API layer
pydeps api/ --show-cycles

# Check for cycles in Shared layer
pydeps shared/ --show-cycles
```

**常见违规场景**:
- ❌ Service A imports Service B, Service B imports Service A
- ❌ Shared utility imports API model for type hints
- ❌ Data processor imports analysis tool, analysis tool imports processor

**违反后果**:
- Module import fails with `ImportError`
- Cannot instantiate classes (initialization order issues)
- Testing becomes impossible (cannot isolate modules)
- High refactoring risk

**解决方法**:
1. **Extract shared interfaces**: Create a `base.py` or `interfaces.py` with shared types
2. **Use dependency injection**: Pass dependencies as parameters instead of importing
3. **Redesign module boundaries**: If A and B depend on each other, they might belong in the same module
4. **Type hints only**: Use `from typing import TYPE_CHECKING` for type-only imports

**示例解决方案**:
```python
# ❌ BAD: Circular dependency
# module_a.py
from module_b import ClassB
class ClassA:
    def use_b(self):
        return ClassB()

# module_b.py
from module_a import ClassA  # Circular!
class ClassB:
    def use_a(self):
        return ClassA()

# ✅ GOOD: Use dependency injection
# module_a.py
class ClassA:
    def use_b(self, b_instance):  # Inject dependency
        return b_instance.do_something()

# module_b.py
class ClassB:
    def use_a(self, a_instance):  # Inject dependency
        return a_instance.do_something()
```

## Architecture Decision Records (ADR)

This section documents key architectural decisions, their context, and rationale.

### ADR-001: Two-Layer Modular Architecture

**Date**: 2024-10 (Architecture Refactoring v0.65 → v0.7)

**Status**: ✅ Accepted and Implemented

**Context**:
- Original single-layer architecture mixed HTTP handling with business logic
- Core logic couldn't be reused outside API context (e.g., CLI tools, batch jobs)
- Testing required HTTP request simulation, making unit tests slow and complex
- Difficult to reason about dependencies and responsibilities

**Decision**: Adopt a strict two-layer architecture:
- **API Layer** (`api/`): Thin layer for HTTP/REST interface only
- **Shared Layer** (`shared/`): Thick layer with all business logic, algorithms, data access

**Consequences**:
- ✅ **Positive**:
  - Shared layer can be tested independently without API server
  - Core logic reusable by CLI tools, batch scripts, or future gRPC services
  - Clear separation of concerns (protocol vs. business logic)
  - Easier to migrate to different frameworks (e.g., from FastAPI to Django)
  - Dependency direction is explicit and enforceable
- ⚠️ **Negative**:
  - Requires discipline to avoid circular dependencies
  - May seem over-engineered for small projects
  - More boilerplate (models in both layers)

**Related**:
- PRINCIPLE-ARCH-002 (Dependency Direction)
- [Architecture Refactoring Report](docs/development/架构重构完成报告.md)

---

### ADR-002: FastAPI + Pydantic for API Framework

**Date**: 2023-Q4 (Initial Development)

**Status**: ✅ Accepted

**Context**:
- Need for modern Python web framework with async support
- Strong type validation required (traffic simulation data is complex)
- Automatic API documentation desired for frontend integration
- Team familiar with Python, not JavaScript/TypeScript

**Decision**: Use FastAPI with Pydantic for:
- API routing and request handling
- Request/response validation
- Automatic OpenAPI/Swagger documentation

**Alternatives Considered**:
- **Django REST Framework**: Too heavyweight, synchronous only
- **Flask**: No built-in validation, manual API docs
- **Express.js (Node.js)**: Team lacks JavaScript expertise

**Consequences**:
- ✅ **Positive**:
  - Automatic data validation catches errors early
  - `/docs` endpoint provides interactive API testing
  - Async support enables background simulation runs
  - Type hints improve IDE support and code quality
- ⚠️ **Negative**:
  - Learning curve for FastAPI-specific patterns
  - Pydantic v2 migration required manual updates

---

### ADR-003: Connection Pooling for Database Access

**Date**: 2025-10 (Database Performance Optimization Phase 1)

**Status**: ✅ Accepted and Implemented

**Context**:
- Original code used `open_db_connection()` creating new connection per query
- TCP handshake + authentication took 150-200ms per query
- Route segment query API took 5.4 seconds (unacceptable UX)
- Database queries dominated API response time

**Decision**:
- Implement SQLAlchemy connection pooling in `shared/data_access/connection.py`
- Create `PooledConnectionWrapper` adapter for backward compatibility
- Deprecate `open_db_connection()` for new code

**Consequences**:
- ✅ **Positive**:
  - 90% performance improvement (5.4s → 0.54s after Phase 2)
  - Reduced database load (connection reuse)
  - Better resource management (configurable pool size)
- ⚠️ **Negative**:
  - Requires careful connection lifecycle management
  - Connection pool exhaustion possible under high load
  - Some legacy code still uses old method (gradual migration)

**Related**:
- PITFALL-CODE-004 (Deprecated Database Connection)
- [Database Optimization Summary](DATABASE_OPTIMIZATION_SUMMARY.md)

---

### ADR-004: Two-Step Simulation Workflow (Prepare + Start)

**Date**: 2024-11 (v0.9.0)

**Status**: ✅ Accepted and Implemented

**Context**:
- Original one-step API (`/run_simulation`) didn't allow configuration inspection
- Users wanted to modify `simulation.sumocfg` before execution
- Hard to debug simulation setup issues (config generation hidden)
- External tools needed access to generated config files

**Decision**: Split simulation into two steps:
1. **Prepare** (`/prepare_simulation`) - Generate config, return paths, status → `pending`
2. **Start** (`/start_simulation`) - Execute simulation, status → `running`
3. Keep one-step API for backward compatibility (internally calls prepare + start)

**Alternatives Considered**:
- **CLI-based config generation**: Rejected (requires terminal access, not web-friendly)
- **Config file upload**: Too complex for non-expert users

**Consequences**:
- ✅ **Positive**:
  - Users can inspect/modify configs before execution
  - Better error messages (fail fast at prepare stage)
  - External tools can use `config_file_abs` path
  - Clear separation of config generation vs. execution
- ⚠️ **Negative**:
  - API surface increased (more endpoints to maintain)
  - Frontend needs to handle two-step workflow
  - Potential confusion with legacy one-step API

**Related**:
- Critical Implementation Details → Simulation Workflow
- PITFALL-ARCH-003 (Mixed API Versions)

---

### ADR-005: JSON Templates for Configuration

**Date**: 2024-Q2 (v0.7)

**Status**: ✅ Accepted

**Context**:
- Vehicle types were hardcoded in Python code
- Every vehicle parameter change required code modification + deployment
- Simulation configurations couldn't be shared between environments
- Traffic engineers (non-coders) couldn't modify vehicle parameters

**Decision**:
- Store vehicle types in `vehicle_types.json` template
- Support multiple template versions (microscopic, mesoscopic)
- Load templates dynamically at runtime, not compile time

**Consequences**:
- ✅ **Positive**:
  - Configuration changes don't require code deployment
  - Traffic engineers can modify templates directly
  - Easy to A/B test different vehicle configurations
  - Templates can be version-controlled independently
- ⚠️ **Negative**:
  - Runtime validation needed (invalid JSON can cause failures)
  - Template schema must be documented
  - Backward compatibility with old template versions

**Related**:
- PITFALL-CODE-002 (Hardcoded Configuration)
- Vehicle Type Configuration section

---

### ADR-006: E2E Tests Use Production Data

**Date**: 2025-11 (E2E Testing Standardization)

**Status**: ✅ Accepted

**Context**:
- Creating test data fixtures was time-consuming and brittle
- Test data often became stale or was deleted
- Wanted to test against real database performance and topology
- Production data is stable (road network doesn't change frequently)

**Decision**:
- E2E tests query production database for test data
- Use well-known stable routes (G4202, G5) and edges
- Gracefully skip tests if production data unavailable (`test.skip()`)

**Alternatives Considered**:
- **Mock data**: Rejected (doesn't test real database performance)
- **Separate test database**: Rejected (maintenance burden, data synchronization issues)

**Consequences**:
- ✅ **Positive**:
  - Tests validate real-world scenarios
  - No test fixture maintenance
  - Catches database performance regressions
  - No setup/teardown overhead
- ⚠️ **Negative**:
  - Tests depend on external database availability
  - Production data changes could break tests
  - Cannot test edge cases not present in production

**Related**:
- RULE-E2E-001 (E2E Testing Best Practices)
- [test_strategy_creation_workflow.spec.js](tests/e2e/test_strategy_creation_workflow.spec.js)

---

### Decision Log

| ADR | Title | Date | Status |
|-----|-------|------|--------|
| ADR-001 | Two-Layer Modular Architecture | 2024-10 | ✅ Implemented |
| ADR-002 | FastAPI + Pydantic | 2023-Q4 | ✅ Implemented |
| ADR-003 | Connection Pooling | 2025-10 | ✅ Implemented |
| ADR-004 | Two-Step Simulation Workflow | 2024-11 | ✅ Implemented |
| ADR-005 | JSON Templates for Configuration | 2024-Q2 | ✅ Implemented |
| ADR-006 | E2E Tests Use Production Data | 2025-11 | ✅ Implemented |

## Development Workflow

### Adding New Features

1. **Determine Layer**:

   - Core logic/algorithm? → Add to `shared/`
   - Business workflow? → Add to `api/services/`
   - HTTP endpoint? → Add to `api/routes/`
2. **Service Development Order**:

   ```
   shared/ (core logic)
   → api/models/ (request/response models)
   → api/services/ (business logic)
   → api/routes/ (HTTP endpoints)
   ```
3. **Example - Adding New Analysis Type**:

   - Create analyzer in `shared/analysis_tools/new_analysis.py`
   - Create service in `api/services/new_analysis_service.py`
   - Add models in `api/models/requests/` and `api/models/responses/`
   - Define routes in `api/routes/analysis_routes.py`
   - Register in `api/services/__init__.py`

### Service Assignment by Feature

- **Data Processing** → `api/services/data_service.py`
- **Case Management** → `api/services/case_service.py`
- **Simulation Control** → `api/services/simulation_service.py`
- **Accuracy Analysis** → `api/services/accuracy_service.py`
- **Mechanism Analysis** → `api/services/mechanism_service.py`
- **Performance Analysis** → `api/services/performance_service.py`
- **EdgeData Analysis** → `api/services/edgedata_service.py`
- **Template Management** → `api/services/template_service.py`

## Critical Implementation Details

### Simulation Workflow (Two-Step Model)

The system supports a two-step simulation model introduced in v0.9.0:

1. **Prepare** (`POST /api/v1/simulation/prepare_simulation/`)

   - Generates `simulation.sumocfg` and directory structure
   - Sets status to `pending`
   - Returns `config_file_abs` for external use
   - Allows manual configuration inspection/modification
2. **Start** (`POST /api/v1/simulation/start_simulation/`)

   - Starts background simulation using `simulation_id`
   - Updates status to `running`
   - Enables progress polling
3. **Legacy One-Step** (`POST /api/v1/simulation/run_simulation/`)

   - Internally calls prepare → start
   - Maintained for backward compatibility

### SUMO Configuration Generation

**ONLY use**: `shared/utilities/sumo_utils.generate_sumocfg_for_simulation()`

**DEPRECATED**: `shared/data_processors/simulation_processor.generate_sumocfg()` (raises exception)

### Vehicle Type Configuration

Vehicle types are defined in `templates/config_templates/vehicle_templates/vehicle_types.json`:

- Supports: passenger_small, truck_large, special_small, special_large, etc.
- Parameters: accel, decel, length, maxSpeed, color, vClass, carFollowModel
- Dynamically generates vType definitions in rou.xml
- Never hardcode vehicle types - always use template configuration

### Metadata Architecture (Three Levels)

**Important**: Analysis workflows do NOT create/update case or simulation metadata.

1. **Case Level** (`cases/{case_id}/metadata.json`)

   - Fields: case_id, created_at, updated_at, status, description
   - Updated by: case creation, simulation start/complete
2. **Simulation Index** (`cases/{case_id}/simulations/simulations_index.json`)

   - Lists all simulations for a case
   - Fields: simulation_id, simulation_name, simulation_type, status, timestamps
   - Updated by: simulation create/start/complete/delete
3. **Simulation Metadata** (`cases/{case_id}/simulations/{sim_id}/simulation_metadata.json`)

   - Fields: simulation_id, case_id, simulation_type, status, timestamps, input_files
   - `input_files` populated from case metadata at creation
   - Analysis workflows MUST NOT modify this file or `simulation_type`

## File Paths and Conventions

### Case Directory Structure

```
cases/{case_id}/
├── config/                  # OD/routes/SUMO config files
├── simulations/{sim_id}/    # Individual simulation runs
│   ├── simulation.sumocfg
│   ├── summary.xml
│   ├── tripinfo.xml
│   ├── e1/                  # E1 detector outputs
│   └── edgedata/            # EdgeData outputs
├── analysis/
│   ├── accuracy/accuracy_results_{timestamp}/
│   ├── mechanism/accuracy_results_{timestamp}/
│   ├── performance/accuracy_results_{timestamp}/
│   └── edgedata/edgedata_results_{timestamp}/
└── metadata.json
```

### Path Handling

- Use `pathlib.Path` for all file operations (cross-platform)
- Always use absolute paths when calling external tools (SUMO)
- Relative paths for storage in metadata/config files
- Convert Windows paths correctly for SUMO (it accepts Windows paths)

## Project Root Directory Policy

**RULE-ROOT-001**: The project root directory MUST remain clean and contain only essential project files.

### Allowed Files in Root

**Configuration & Documentation**:
- `CLAUDE.md` - AI assistant development guide
- `AGENTS.md` - OpenSpec agent instructions
- `README.md` - Project documentation
- `.gitignore`, `.env` - Git and environment configuration
- `requirements.txt`, `package.json` - Dependency manifests

**Build & Startup Scripts**:
- `start_api.*` (bat, ps1, sh) - API server startup scripts
- Build/deployment scripts (if applicable)

### Prohibited in Root

❌ **Intermediate artifacts** - Analysis reports, debug logs, temporary files
❌ **Generated documentation** - Session summaries, completion reports, guides
❌ **Test scripts** - Ad-hoc test files, debugging scripts
❌ **Code files** - Python/JavaScript modules (belong in `api/`, `shared/`, `frontend/`)
❌ **Log files** - Runtime logs, test outputs

### File Organization Rules

1. **Analysis & Documentation** → `docs/` with appropriate subdirectory:
   - Session summaries → `docs/session-summaries/`
   - Testing guides → `docs/testing/`
   - Feature docs → `docs/features/`
   - Development guides → `docs/development/`
   - Refactoring notes → `docs/refactoring/`

2. **Test Files** → `tests/` or `test-results/`:
   - E2E test specs → `tests/e2e/`
   - Unit tests → `tests/unit/`
   - Test outputs → `test-results/`

3. **Generated Code** → Module-specific directories:
   - API code → `api/`
   - Shared utilities → `shared/`
   - Frontend code → `frontend/`

4. **Temporary Files** → `.gitignore` and use appropriate temp directory:
   - Logs → `logs/` (git-ignored)
   - Debug outputs → `debug/` or `test-results/` (git-ignored)

5. **Version Archives** → `archive/`

### Enforcement

- **Pre-commit**: Review root directory for new files
- **Code review**: Check PR file tree for root-level additions
- **CI/CD**: Automated check to reject commits with unauthorized root files
- **Periodic cleanup**: Monthly review to move/delete misplaced files

### Rationale

Maintaining a clean root directory:
- ✅ Improves project navigation and discoverability
- ✅ Reduces cognitive load for developers
- ✅ Prevents version control clutter
- ✅ Enforces consistent file organization
- ✅ Simplifies onboarding for new team members

## Database Access

### Configuration

**Database credentials are already configured in system environment variables:**

```env
DB_NAME=sdzg
DB_USER=ln
DB_PASSWORD=caneln
DB_HOST=10.149.235.123
DB_PORT=5432
```

**Important**:

- Environment variables are set at OS level (no `.env` file needed)
- PostgreSQL client tools (psql) can be used directly without explicit password parameters
- Python code uses `shared/data_access/db_config.py` to read these environment variables

**Example psql usage:**

```bash
# Direct access (credentials from environment)
psql -h 10.149.235.123 -U ln -d sdzg -c "SELECT COUNT(*) FROM baseline.baseflow_pattern_gantry"

# List schemas
psql -h 10.149.235.123 -U ln -d sdzg -c "\dn"

# List tables in baseline schema
psql -h 10.149.235.123 -U ln -d sdzg -c "\dt baseline.*"
```

### Database Usage

- **Gantry data loading**: `shared/data_access/gantry_loader.py`
- **OD table resolution**: `shared/data_access/od_table_resolver.py`
- **Edge queries**: `shared/data_access/edge_query.py`
- **Connection management**: `shared/data_access/connection.py`
- Always use connection pooling (SQLAlchemy)
- Never log sensitive data (credentials)

### Available Schemas

- **dim**: Dimension tables (road network edges, nodes, routes)
- **baseline**: Baseline traffic flow data (gantry patterns, OD patterns, toll square patterns)
- Other schemas contain additional traffic data

### Database Performance Optimization (2025-11-01)

**Current Status**: Phase 2 Complete ✅ (**90% improvement**, far exceeded 70% target)

**Original Issue**: Route segment query API taking 5.4 seconds

**Performance Phases**:

#### Phase 1: Connection Pooling ✅ (Completed 2025-10-22)
- Migrated from `open_db_connection()` to `get_pooled_connection()`
- Created `PooledConnectionWrapper` adapter for SQLAlchemy-to-psycopg2 compatibility
- **Improvement**: 150-200ms per query (eliminated TCP connection + authentication overhead)
- **Files**: `shared/data_access/connection.py`, `shared/data_access/edge_query.py`

#### Phase 2: Separate Queries ✅ (Completed 2025-11-01) - SUPER EFFECTIVE!
**New approach: Break 3-table JOIN into 3 simple queries + Python merging**

Implemented 3 new functions in `shared/data_access/edge_query.py`:
1. `query_edges_base()` - Edge data filtering without JOIN (~500ms)
2. `get_node_types_batch()` - Batch node type lookup (~20ms)
3. `get_gantry_info_batch()` - Batch gantry query + Python matching (~19ms)

**Results**:
- Query response: 5440ms → **539ms** ✅
- **Performance improvement: 90%** (exceeded 37% target by 2.5x!)
- All E2E tests passing
- Fully backward compatible
- **Why so fast**: Eliminated complex JOIN execution plan, GROUP BY overhead, and DISTINCT operations

#### Phase 3: Result Caching ⏳ (Planned)
- Implement LRU cache with 5-minute TTL
- Expected additional improvement: 60-80% (70% cache hit rate)
- Expected final response: ~160ms (**97% total improvement**)
- **Plan**: [DATABASE_OPTIMIZATION_PHASE3_PLAN.md](./DATABASE_OPTIMIZATION_PHASE3_PLAN.md)

#### Phase 4: Index Optimization ⏳ (Optional)
- Additional index tuning (marginal gains at this point)
- Phase 2 performance already excellent
- **Priority**: Low

**Overall Performance Achievement**:

| Metric | Original | Phase 1 | Phase 2 | Target | Status |
|--------|----------|---------|---------|--------|--------|
| Query time | 5440ms | 5250ms | 539ms | <2000ms | ✅ Exceeded |
| Improvement | 0% | 3% | 90% | 70% | ✅ Exceeded |
| User experience | 5-10s | 5-10s | <600ms | Good | ✅ Excellent |

**Documentation**:
- [DATABASE_OPTIMIZATION_SUMMARY.md](./DATABASE_OPTIMIZATION_SUMMARY.md) - Overall strategy
- [DATABASE_OPTIMIZATION_PHASE2_COMPLETE.md](./DATABASE_OPTIMIZATION_PHASE2_COMPLETE.md) - Phase 2 details
- [PHASE2_SESSION_SUMMARY.md](./PHASE2_SESSION_SUMMARY.md) - Implementation summary
- [DATABASE_OPTIMIZATION_PHASE3_PLAN.md](./DATABASE_OPTIMIZATION_PHASE3_PLAN.md) - Phase 3 plan

## Control Strategies - Real Data Analysis

### Overview

The system supports traffic control strategies based on real baseline data analysis. Strategy configurations are stored in `control_data/strategies/` and managed through the Control Strategies API.

### Strategy Types

- **VSS (可变限速)**: Variable Speed Signs - Dynamic speed limit control
- **TEC (收费站管控)**: Toll/Entrance Control - Flow metering at ramps
- **DHS (动态硬路肩)**: Dynamic Hard Shoulder - Emergency lane opening during peak hours

### Real Data Analysis Results (2025-10-26)

**Data Source**: `baseline.baseflow_pattern_gantry` (batch: 20251013_20251019)

**Routes Analyzed**: G4202 (成都绕城高速), G5 (京昆高速四川段)

**Key Findings**:

1. **Severe Congestion Identified**:

   - G4202 K52.4: 15.14 km/h (morning peak) - Extreme congestion
   - G4202 K42.32: 15.65 km/h (evening peak, 478 veh/hr) - Extreme congestion
   - G5 K1820.15: 17.97 km/h (evening peak) - Extreme congestion
   - G4202 K32.51: 18.22 km/h (morning peak, 489 veh/hr) - Extreme congestion
2. **Actual DHS (Dynamic Hard Shoulder) Segments on G4202**:

   - **Segment 1**: K38.2 - K36.9 (Counterclockwise, 1.47 km, 4 edges)
   - **Segment 2**: K36.9 - K32.968 (Counterclockwise, 3.69 km, 12 edges) - **Covers K32.51 congestion point**
   - **Segment 3**: K51.8 - K43.3 (Counterclockwise, 8.78 km, 18 edges) - **Covers K42.32 & K42.35 congestion points**
   - **Segment 4**: K25.1 - K33.9 (Clockwise, 15.59 km, 36 edges) - Longest segment
   - **Total**: 29.53 km, 70 edges
3. **Strategy Validation**:

   - ✅ Our baseline data analysis **accurately identified** the same congestion points already covered by actual DHS segments
   - ✅ K42.32 and K32.51 (identified as TOP congestion points) are covered by existing DHS segments 2 & 3
   - ✅ This validates that **baseline data-driven congestion identification is reliable**

### Strategy Configuration Files

**Location**: `control_data/strategies/`

**File Format**:

- Individual strategies: `strategy_*.json` or `strat_*.json`
- Index file: `strategies_index.json`

**Key Fields**:

```json
{
  "strategy_id": "strategy_real_vss_g4202_001",
  "strategy_name": "G4202绕西双流段早高峰可变限速",
  "strategy_type": "VSS",
  "configured_params": {
    "affected_edges": ["-8712", "-15452.627", ...],
    "speed_steps": [
      {"time_hours": 7, "speed_kmh": 50},
      ...
    ]
  },
  "data_source": {
    "gantry_id": "G420151002000220010",
    "batch_id": "20251013_20251019",
    "min_speed": 15.14,
    "max_flow": 445.08
  }
}
```

### Plan XML Validation (v0.9.0+)

**Feature**: Automated SUMO XML validation for control plans with frontend validation button

**Backend Validation**:
- **Module**: `shared/control_tools/xml_validator.py` (600+ lines)
- **Function**: `validate_xml_string(xml_content: str) -> ValidationResult`
- **API Endpoint**: `POST /api/v1/control/plans/{plan_id}/generate_additional`
- **Validation Coverage**:
  - XML well-formedness (syntax checking)
  - SUMO v1.19+ attribute compatibility
  - Parameter constraints (time: 0-86400s, speed: 0-200 km/h)
  - Edge list validation (empty/duplicate warnings)
  - Strategy-specific rules (VSS steps, DHS intervals, TEC flow rates)

**Response Format**:
```json
{
  "regenerated": true,
  "plan_id": "plan_001",
  "validation": {
    "is_valid": true,
    "warnings": ["Edge list has duplicates: [-8712]"],
    "errors": []
  }
}
```

**Frontend Implementation** (HTML/CSS/JS Three-Layer Separation):
- **UI Components**: `frontend/control/js/ui-utils.js` - Toast notifications, Modal dialogs
- **Validation UI**: `frontend/control/js/plan-validation-ui.js` - Status display updates
- **Business Logic**: `frontend/control/js/plan-validation.js` - API orchestration
- **Styles**: `frontend/control/css/plan-validation.css`, `frontend/control/css/ui-utils.css`

**Frontend Integration**:
```html
<!-- CSS -->
<link rel="stylesheet" href="css/ui-utils.css">
<link rel="stylesheet" href="css/plan-validation.css">

<!-- JavaScript (order matters) -->
<script src="js/ui-utils.js"></script>
<script src="js/plan-validation-ui.js"></script>
<script src="js/plan-validation.js"></script>

<!-- Validation status display -->
<span id="validation-status-{plan_id}" class="validation-status pending">
  <i class="status-icon">⏳</i> 未验证
</span>

<!-- Validation button -->
<button class="btn-validate" onclick="validatePlan('{plan_id}')">验证XML</button>
```

**Cascade Regeneration** (Phase 2):
- When a strategy is updated, all referencing plans automatically regenerate XML
- Each regeneration includes validation check
- Audit logging: CASCADE_START, CASCADE_REGEN, CASCADE_COMPLETE, CASCADE_FAIL events
- Validation failures block XML save and propagate error to user

**Code Quality Standards**:
- ✅ HTML/CSS/JS three-layer separation (no inline styles/events)
- ✅ Single responsibility principle (functions ≤30 lines, parameters ≤5)
- ✅ XSS protection via `escapeHTML()` function
- ✅ Event delegation for scalability
- ✅ Responsive design (mobile/tablet/desktop)

**Related Documentation**:
- **OpenSpec Change**: `openspec/changes/validate-strategy-xml-generation/`
- **Phase 1 Report**: `openspec/changes/validate-strategy-xml-generation/PHASE1_FINAL_REPORT.md`
- **Phase 2 Report**: `openspec/changes/validate-strategy-xml-generation/PHASE2_COMPLETION_REPORT.md`

### Documentation

Detailed analysis and strategy recommendations:

- **Main Document**: `docs/真实数据分析与策略建议_G4202_G5综合.md`
- **Methodology Guide**: `docs/真实策略生成指南.md`
- **API Endpoints**: `/api/v1/control/strategies/instances`

### Implementation Priority

| Priority | Strategy                    | Route | Target Segment | Type    | Expected Effect  |
| -------- | --------------------------- | ----- | -------------- | ------- | ---------------- |
| P0       | strategy_real_vss_g4202_001 | G4202 | K52.4          | VSS     | Speed +230%      |
| P0       | strategy_real_vss_g4202_002 | G4202 | K42.32         | VSS+DHS | Speed +220%~283% |
| P0       | strategy_real_vss_g5_001    | G5    | K1820          | VSS+DHS | Speed +123%~178% |
| P1       | strategy_real_vss_g4202_003 | G4202 | K32.51         | VSS+DHS | Speed +174%~229% |
| P1       | strategy_real_vss_g5_002    | G5    | K1768          | VSS     | Speed +121%      |

## Frontend Development Standards

### CSS and HTML Separation

All frontend pages MUST follow strict separation of concerns:

**HTML Requirements**:
- Semantic HTML structure only (no inline styles)
- Use semantic tags (`<header>`, `<nav>`, `<main>`, `<footer>`, etc.)
- No `style=""` attributes in HTML files
- Meaningful `class` and `id` attributes for styling hooks
- Location: `frontend/control/` or appropriate module directory

**CSS Requirements**:
- All styling rules in separate `.css` files
- Organized by component or page section
- Class-based selectors (prefer classes over IDs)
- Store in `frontend/control/css/` directory
- Naming: `[page-or-component]-name.css`

**CSS Organization Example**:
- `templates-base.css` - Base styles and reset
- `templates-layout.css` - Layout and grid
- `templates-forms.css` - Form styles
- `templates-results.css` - Results display
- `templates-inline-utilities.css` - Utility classes
- `edge_selector.css` - Component-specific styles

### JavaScript Function Standards (Single Responsibility Principle)

All JavaScript functions MUST follow SRP:

**Constraints**:
- **Purpose**: Each function has ONE clear responsibility
- **Length**: Maximum 30 lines
- **Parameters**: Maximum 5
- **Nesting**: Maximum 3 levels
- **Naming**: Descriptive camelCase reflecting the single responsibility
  - Good: `updateRouteDropdown()`, `validateFormInput()`, `fetchSimulationStatus()`
  - Bad: `handleChange()`, `process()`, `doStuff()`

**Function Categories**:
1. **Event Handlers**: One handler per event, delegates to action functions
   ```javascript
   document.getElementById('btn').onclick = () => performAction();
   ```

2. **Data Fetchers**: One function per API endpoint
   ```javascript
   async function fetchSimulationResults() { ... }
   async function loadCaseMetadata() { ... }
   ```

3. **DOM Manipulators**: One function per UI update task
   ```javascript
   function updateProgressBar(percent) { ... }
   function renderResultsTable(data) { ... }
   ```

4. **Validators**: One function per validation rule
   ```javascript
   function validateSpeedRange(speed) { ... }
   function validateTimeFormat(time) { ... }
   ```

5. **Formatters**: One function per format conversion
   ```javascript
   function formatTimestamp(date) { ... }
   function formatSpeedValue(speed) { ... }
   ```

**Best Practices**:
- Use early returns for error handling
- Avoid nested callbacks; use Promise chains or async/await
- Keep functions pure when possible (avoid side effects)
- Test each function independently
- Document complex functions with clear comments

**Example - Before (BAD)**:
```javascript
function handleFormSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData);

  if (!data.speed || data.speed < 0 || data.speed > 120) {
    alert('Invalid speed');
    return;
  }

  fetch('/api/update', { method: 'POST', body: JSON.stringify(data) })
    .then(r => r.json())
    .then(result => {
      document.getElementById('output').innerHTML = `
        <div class="result">
          <p>Speed: ${result.speed} km/h</p>
          <p>Time: ${new Date(result.timestamp).toLocaleString()}</p>
        </div>
      `;
    })
    .catch(err => console.error(err));
}
```

**Example - After (GOOD)**:
```javascript
// Separate validation
function validateSpeedInput(speed) {
  return speed > 0 && speed <= 120;
}

// Separate API call
async function updateSimulationSpeed(data) {
  const response = await fetch('/api/update', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  return response.json();
}

// Separate formatting
function formatResultDisplay(result) {
  const timestamp = new Date(result.timestamp).toLocaleString();
  return `<div class="result">
    <p>Speed: ${result.speed} km/h</p>
    <p>Time: ${timestamp}</p>
  </div>`;
}

// Separate DOM update
function renderResult(html) {
  document.getElementById('output').innerHTML = html;
}

// Event handler delegates to specific functions
async function handleFormSubmit(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData);

  if (!validateSpeedInput(data.speed)) {
    alert('Invalid speed');
    return;
  }

  try {
    const result = await updateSimulationSpeed(data);
    const html = formatResultDisplay(result);
    renderResult(html);
  } catch (err) {
    console.error('Error updating simulation:', err);
  }
}
```

### Module Organization

- **One Responsibility Per File**: Each JavaScript file handles one distinct feature
- **Avoid God Files**: Files >300 lines should be split into smaller modules
- **Clear Exports**: Export only necessary functions
- **Dependency Management**: Minimize cross-file dependencies

### Frontend Data Rules: No Hardcoded Data & No Duplicate Code

**RULE-FE-001**: Frontend code MUST NOT hardcode data or duplicate functionality.

**Core Rules**:

1. **No Hardcoded Example Data in HTML**
   - ❌ Prohibited: `placeholder="7"`, `placeholder="9"`, `placeholder="400"` (hardcoded values)
   - ✅ Allowed: `placeholder="例如: 7:00"` (format hints only)
   - ✅ All initial data MUST come from `schema.default_value` in template JSON
   - ✅ Use `value="..."` attribute for actual data, not `placeholder`

2. **Single Source of Truth - No Code Duplication**
   - ❌ Prohibited: Same function implemented in both `templates.html` AND `parameter_form.js`
   - ❌ Prohibited: Different versions of `addFlowIntervalRow()` in multiple files
   - ✅ Required: Each functionality has ONE implementation location
   - ✅ Example: Parameter form generation lives ONLY in `parameter_form.js`, not duplicated in HTML

3. **Data Source Traceability**
   - ✅ Every data value must be traceable to its origin (template `default_value`)
   - ✅ Code MUST have comments explaining where data comes from
   - ❌ Prohibited: Magic numbers with unknown origins
   - Example:
     ```javascript
     // ✅ CORRECT - Data source is clear
     const defaultIntervals = schema.default_value || [];  // From template
     defaultIntervals.forEach(interval => {
         addFlowIntervalRow(
             tbody,
             paramName,
             interval.begin_hours,    // ← From template's default_value
             interval.end_hours,      // ← From template's default_value
             interval.flow_vph,       // ← From template's default_value
             interval.target_speed    // ← From template's default_value
         );
     });
     ```

4. **Parameterized Functions - Not Hardcoded Values**
   - ✅ Functions accept parameters for all variable data
   - ✅ Example:
     ```javascript
     // ✅ CORRECT - All data comes from parameters
     function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
         const row = document.createElement("tr");
         const beginInput = document.createElement("input");
         beginInput.value = beginHours;  // ← Parameter-driven
         // ... rest of fields ...
     }
     ```
   - ❌ Wrong approach (hardcoded in HTML template string):
     ```javascript
     // ❌ WRONG - Hardcoded values, no parameters
     function addFlowIntervalRow(tbody) {
         row.innerHTML = `<input placeholder="7" />`;  // ← Hardcoded!
     }
     ```

**Code Review Checklist for Frontend**:

Before approving frontend PRs, verify:
- [ ] No hardcoded numeric values in `placeholder` attributes
- [ ] No duplicate function definitions (search both HTML and JS)
- [ ] All initial data loads from template's `default_value`, not hardcoded
- [ ] Functions are parameterized (accept data as arguments)
- [ ] Data source is documented in comments
- [ ] Use `value` attribute for actual data, not `placeholder`

**Impact**: Violations cause incorrect data display, maintenance issues, and inconsistent behavior across features.

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

### STANDARD-NAMING-001: Naming Conventions

See STANDARD-CODE-001 → Naming Conventions above.

## Analysis Types

### 1. Accuracy Analysis

- Compares gantry E1 detector data vs observed gantry data
- Metrics: MAPE, GEH, correlation
- Output: reports (HTML/Markdown), charts (PNG), CSV files
- Location: `cases/{case_id}/analysis/accuracy/`

### 2. Mechanism Analysis

- Traffic flow mechanism analysis
- Comparisons: OD observed vs input, input vs output
- E1 speed time series analysis
- Requires: tripinfo or vehroute output enabled
- Location: `cases/{case_id}/analysis/mechanism/`

### 3. Performance Analysis

- System performance evaluation
- Metrics: summary.xml stats (steps, loaded/inserted/ended, running_max, waiting_max)
- File size and count analysis
- Optimization suggestions
- Location: `cases/{case_id}/analysis/performance/`

### 4. EdgeData Analysis

- SUMO EdgeData traffic flow analysis
- Road segment level statistics
- Requires: output_edgedata enabled in simulation
- Location: `cases/{case_id}/analysis/edgedata/`

## Common Pitfalls

### Architecture Violations

**PITFALL-ARCH-001: Circular Dependencies**
- ❌ **Don't** create circular dependencies between modules
- **检查方法**: `pydeps api/ --show-cycles` and `pydeps shared/ --show-cycles`
- **后果**: Module import failures, testing impossible
- **相关原则**: PRINCIPLE-ARCH-005

**PITFALL-ARCH-002: Reverse Dependency Flow**
- ❌ **Don't** let `shared/` import from `api/`
- ❌ **Don't** let analysis workflows modify case/simulation metadata
- **检查方法**: `grep -r "from api" shared/`
- **后果**: Cannot reuse shared logic, tight coupling
- **相关原则**: PRINCIPLE-ARCH-002

**PITFALL-ARCH-003: Mixed API Versions**
- ❌ **Don't** mix old and new simulation API endpoints inconsistently
- **正确做法**: Use two-step API (prepare + start) for new code, one-step only for backward compatibility
- **相关文档**: Critical Implementation Details → Simulation Workflow

### Code Quality Issues

**PITFALL-CODE-001: Using Deprecated Functions**
- ❌ **Don't** use `shared/data_processors/simulation_processor.generate_sumocfg()` - deprecated
- ✅ **Use**: `shared/utilities/sumo_utils.generate_sumocfg_for_simulation()`
- **后果**: Exception raised, simulation fails

**PITFALL-CODE-002: Hardcoded Configuration**
- ❌ **Don't** hardcode vehicle types in code
- ✅ **Use**: `templates/config_templates/vehicle_templates/vehicle_types.json`
- **原因**: Configuration should be data-driven, not code-driven
- **相关原则**: Configuration as Data

**PITFALL-CODE-003: Using print() Instead of Logging**
- ❌ **Don't** use `print()` statements for output
- ✅ **Use**: Python `logging` module
- **原因**: Logs can be configured, filtered, and directed to files
- **标准**: STANDARD-CODE-001

**PITFALL-CODE-004: Deprecated Database Connection**
- ❌ **Don't** use `open_db_connection()` in new code
- ✅ **Use**: Connection pooling from `shared/data_access/connection.py`
- **原因**: Connection pooling improves performance by 90%+
- **相关文档**: Database Performance Optimization

### Frontend Code Issues

**PITFALL-FE-002: Inline Styles in HTML**
- ❌ **Don't** include inline styles in HTML files (`style=""` attributes)
- ✅ **Use**: Separate CSS files in `frontend/control/css/`
- **相关规则**: RULE-FE-001
- **后果**: Poor maintainability, inconsistent styling

**PITFALL-FE-003: Violating Single Responsibility (Functions)**
- ❌ **Don't** create functions that do multiple things
- ❌ **Don't** write functions longer than 30 lines
- ❌ **Don't** use vague names like `handle()`, `process()`, `doStuff()`
- ❌ **Don't** mix event handling, data fetching, validation, and DOM manipulation in one function
- ✅ **Do**: Split into small, focused functions with clear names
- **相关标准**: JavaScript Function Standards (Single Responsibility Principle)
- **后果**: Hard to test, debug, and maintain

**PITFALL-FE-004: Deep Callback Nesting**
- ❌ **Don't** nest callbacks more than 3 levels deep
- ✅ **Use**: Promise chains or async/await
- **示例**:
  ```javascript
  // ❌ BAD
  fetch(url1).then(r1 => {
    fetch(url2).then(r2 => {
      fetch(url3).then(r3 => {
        // Callback hell!
      });
    });
  });

  // ✅ GOOD
  const r1 = await fetch(url1);
  const r2 = await fetch(url2);
  const r3 = await fetch(url3);
  ```

### Environment and Tools

**PITFALL-ENV-001: Wrong Conda Environment**
- ❌ **Don't** install dependencies in conda base environment
- ❌ **Don't** run tests or scripts without activating `od_project` first
- ❌ **Don't** run Playwright tests in conda base environment
- ✅ **Always**: `conda activate od_project` before ANY operations
- **原因**: Ensures correct Python version, dependencies, and Playwright installation
- **后果**: Tests fail, dependency conflicts, import errors

**PITFALL-ENV-002: Working in Legacy Directories**
- ❌ **Don't** create files in `sim_scripts/` or `accuracy_analysis/` directories
- **原因**: These are legacy code, kept for reference only
- ✅ **Use**: New architecture paths (`api/`, `shared/`, `frontend/`)

### File Organization

**PITFALL-FILE-001: Root Directory Pollution**
- ❌ **Don't** generate documentation or code files in the project root during testing/debugging
- **相关规则**: RULE-ROOT-001
- **正确组织**:
  - Analysis documents → `docs/` (with suitable subdirectory)
  - Temporary test files → `tests/` or `test-results/`
  - Generated code → appropriate `api/`, `shared/`, or `frontend/` subdirectory
- **后果**: Poor discoverability, version control clutter, cognitive overload

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

## Templates and Configuration

### Available Templates

- **TAZ files**: `templates/taz_files/` (default: TAZ_6.add.xml)
- **Network files**: `templates/network_files/` (default: sichuan202508v7.net.xml)
- **Simulation configs**: `templates/config_templates/` (microscopic, mesoscopic)
- **Vehicle types**: `templates/config_templates/vehicle_templates/vehicle_types.json`
- **EdgeData config**: `templates/edge_add/`

### Template Usage

Templates are copied/referenced during case creation. Never modify templates directly during processing - copy them first.

## API Endpoint Groups

All endpoints use prefix `/api/v1/`:

- **Data Processing**: `/api/v1/data/*`
- **Case Management**: `/api/v1/case/*`
- **Simulation**: `/api/v1/simulation/*`
- **Analysis**: `/api/v1/analysis/*`
- **Templates**: `/api/v1/template/*`
- **Files**: `/api/v1/file/*`

See [docs/api_docs/新架构API指南.md](docs/api_docs/新架构API指南.md) for complete API documentation.

## Environment and External Dependencies

### SUMO Configuration

The system requires SUMO (Simulation of Urban MObility) to be installed:

- Set `SUMO_HOME` environment variable to SUMO installation directory
- Add `%SUMO_HOME%\bin` to `PATH`
- Alternatively, set `SUMO_BIN` to full path of sumo.exe
- Version: 1.19+ recommended

### Python Environment

**CRITICAL**: This project uses the `od_project` conda environment (NOT `od-sim`):

- **Environment name**: `od_project` (already configured with Python 3.10+, Playwright, and all dependencies)
- **ALWAYS activate before any operations**: `conda activate od_project`
- **Never** install in conda base environment
- Use mamba for installation (conda-forge channel), pip as fallback
- If environment doesn't exist, create it: `mamba create -n od_project python=3.10`

**Testing Environment**:

- Playwright is already configured in `od_project` environment
- All E2E tests require `od_project` to be active
- Python unit tests also require `od_project` environment

## Documentation Resources

- **Development Guide**: [docs/development/新架构开发指南.md](docs/development/新架构开发指南.md)
- **API Guide**: [docs/api_docs/新架构API指南.md](docs/api_docs/新架构API指南.md)
- **Deployment Guide**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **Architecture Report**: [docs/development/架构重构完成报告.md](docs/development/架构重构完成报告.md)
- **Testing Checklist**: [docs/testing/Playwright_MCP_测试任务清单.md](docs/testing/Playwright_MCP_测试任务清单.md)

## Version History

- **v0.9.0** (current): Two-step simulation API, frontend updates for prepare/start workflow
- **v0.8**: EdgeData analysis integration, complete analysis toolchain
- **v0.7**: Vehicle template configuration, default template updates, frontend optimization
- **v0.65**: Three analysis types (accuracy/mechanism/performance), automated testing validation

## Project Context

This is a traffic simulation project. Comments, variable names, and documentation are primarily in Chinese. The system:

- Processes real-world OD (Origin-Destination) data from a PostgreSQL database
- Uses SUMO for microscopic/mesoscopic traffic simulation
- Compares simulation results against real gantry observation data
- Generates comprehensive analysis reports with charts and metrics
- Supports case-based workflow for managing multiple simulation scenarios
