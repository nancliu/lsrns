# Project Context

## Purpose

OD Data Processing and Simulation System (OD数据处理与仿真系统) - A modular traffic simulation and analysis platform for Origin-Destination (OD) data processing using SUMO (Simulation of Urban MObility).

**Key Goals**:

- Manage traffic simulation cases with multi-layer workflow support
- Process real-world OD data from PostgreSQL database
- Run microscopic/mesoscopic traffic simulations using SUMO
- Compare simulation results against real gantry observation data
- Generate comprehensive analysis reports with charts and metrics
- Support accuracy, mechanism, performance, and EdgeData analysis types

**Current Version**: v0.9.0

## Tech Stack

### Backend

- **Language**: Python 3.10+
- **API Framework**: FastAPI + Pydantic
- **Database**: PostgreSQL (gantry data, network topology, OD tables)
- **Data Processing**: pandas (vectorized operations required)
- **Simulation Engine**: SUMO (Simulation of Urban MObility) v1.19+
- **Environment Management**: conda (od_project environment)

### Frontend

- **HTML/CSS/JavaScript**: Custom implementation
- **Key Components**: Dual-layer canvas, control plan management, case workflow UI
- **Testing**: Playwright E2E tests

### Platform

- **OS**: Windows 10/11
- **Python Environment**: `od_project` conda environment (CRITICAL - never use base)

## Project Conventions

### Code Style

**Language Standards**:

- **Variable/Function Names**: snake_case (`process_gantry_data`)
- **Class Names**: PascalCase (`GantryDataProcessor`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- **File Names**: snake_case (`gantry_processor.py`)
- **Private Methods**: Prefix with underscore (`_process_data`)

**Code Quality Requirements**:

- **Line Length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Type Hints**: Required on all functions (parameters + return values)
- **Docstrings**: Required (Google style format)
- **Logging**: Use logging module, NO print() statements
- **Formatters**: black (code formatting)
- **Linters**: flake8 (code quality)

**Function Limits**:

- Max function length: 30 lines
- Max parameters: 5
- Max nesting depth: 3 levels
- Max class length: 300 lines
- Flag if >10 methods per class

### Architecture Patterns

**Two-Layer Modular Architecture**:

1. **API Layer** (`api/`) - HTTP interface, business coordination, request/response handling
2. **Shared Layer** (`shared/`) - Core business logic, algorithms, data access, reusable utilities

**Critical Rule**: API layer calls Shared layer only. No circular dependencies allowed.

**API Layer Structure**:

```
api/
├── main.py              # ONLY entry point
├── routes/              # Route definitions by domain
│   ├── data_routes.py
│   ├── case_routes.py
│   ├── simulation_routes.py
│   ├── analysis_routes.py
│   ├── template_routes.py
│   └── file_routes.py
├── services/            # Business logic (calls shared/)
│   ├── data_service.py
│   ├── case_service.py
│   ├── simulation_service.py
│   ├── accuracy_service.py
│   ├── mechanism_service.py
│   ├── performance_service.py
│   ├── edgedata_service.py
│   └── template_service.py
└── models/              # Data validation
    ├── requests/
    ├── responses/
    ├── entities/
    └── enums.py
```

**Shared Layer Structure**:

```
shared/
├── utilities/           # Generic helper functions
├── data_access/         # Database access (connection pooling)
├── analysis_tools/      # Analysis algorithms
└── data_processors/     # Core data processing
```

**Dependency Flow**: API → Services → Shared (utilities/data_access/analysis_tools/data_processors)

**Key Patterns**:

- Service Locator Pattern for service management (`api/services/__init__.py`)
- Dependency Injection for service instances
- Pydantic models for request/response validation

### Testing Strategy

**Test Environment** (CRITICAL):

- **Always activate**: `conda activate od_project` before testing
- Never run tests in conda base environment
- Python 3.10+ with all dependencies configured

**Unit Tests**:

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_specific.py

# Run with coverage
pytest --cov=api --cov=shared
```

**E2E Tests** (Playwright):

```bash
# Run all E2E tests
npx playwright test

# Run specific test
npx playwright test tests/e2e/test_dual_layer_canvas.spec.js

# Run in headed mode (visible browser)
npx playwright test --headed
```

**Testing Locations**:

- Unit tests: `tests/unit/`
- E2E tests: `tests/e2e/`

### Git Workflow

**Branching Strategy**:

- Main branch: `main` (for PRs)
- Feature branches: Follow pattern for proposed features
- Use OpenSpec for planning (see openspec/AGENTS.md)

**Commit Conventions**:

- Clear, descriptive commit messages
- Reference related features or fixes
- Use conventional commit format when possible

**OpenSpec Integration**:

- Use `/speckit.specify` for feature specifications
- Use `/speckit.plan` for implementation planning
- Use `/speckit.tasks` for task generation
- Use `/speckit.implement` for execution

## Domain Context

### Traffic Simulation Domain

**Key Concepts**:

- **OD Data**: Origin-Destination traffic demand matrix
- **TAZ**: Traffic Analysis Zones (zones.taz.xml, default: TAZ_6.add.xml)
- **Network**: Road network topology (default: sichuan202508v7.net.xml)
- **Gantry Data**: Real-world toll gantry observations (from database)
- **E1 Detector**: SUMO loop detectors for vehicle counting
- **SUMO Config**: simulation.sumocfg files for simulation setup

**Case Directory Structure**:

```
cases/{case_id}/
├── config/                  # OD/routes/SUMO config files
├── simulations/{sim_id}/    # Individual simulation runs
│   ├── simulation.sumocfg
│   ├── summary.xml
│   ├── tripinfo.xml
│   ├── e1/
│   └── edgedata/
├── analysis/
│   ├── accuracy/
│   ├── mechanism/
│   ├── performance/
│   └── edgedata/
└── metadata.json
```

**Simulation Workflow (Two-Step Model)**:

1. **Prepare** - Generate simulation.sumocfg and directory structure, status→pending
2. **Start** - Run background simulation, status→running
3. **Legacy One-Step** - Backward compatible (calls prepare→start internally)

**Vehicle Types**:

- Defined in: `templates/config_templates/vehicle_templates/vehicle_types.json`
- Supported: passenger_small, truck_large, special_small, special_large, etc.
- Parameters: accel, decel, length, maxSpeed, color, vClass, carFollowModel
- Never hardcode - always use template configuration

**Analysis Types**:

1. **Accuracy**: Gantry E1 detector data vs observed gantry (MAPE, GEH, correlation)
2. **Mechanism**: Traffic flow mechanism analysis (OD/input/output comparisons)
3. **Performance**: System performance (summary.xml stats, file analysis)
4. **EdgeData**: SUMO road segment level statistics

**Important**: Analysis workflows DO NOT create/update case or simulation metadata

### Metadata Architecture (Three Levels)

1. **Case Metadata** (`cases/{case_id}/metadata.json`)

   - Fields: case_id, created_at, updated_at, status, description
   - Updated by: case creation, simulation start/complete
2. **Simulation Index** (`cases/{case_id}/simulations/simulations_index.json`)

   - Lists all simulations for case
   - Fields: simulation_id, simulation_name, simulation_type, status, timestamps
3. **Simulation Metadata** (`cases/{case_id}/simulations/{sim_id}/simulation_metadata.json`)

   - Fields: simulation_id, case_id, simulation_type, status, timestamps, input_files
   - Analysis workflows MUST NOT modify this file

### Database Access

**Connection Management**:

- Use connection pooling from `shared/data_access/connection.py`
- DO NOT use `open_db_connection()` (deprecated - creates new connection each time) 
- Database requires `.env` file with PGNAME, PGUSER, PGPASSWORD, PGHOST, PGPORT

**Key Modules**:

- `shared/data_access/gantry_loader.py` - Gantry data loading
- `shared/data_access/od_table_resolver.py` - OD table resolution
- `shared/data_access/edge_query.py` - Edge queries with indexing
- `shared/data_access/connection.py` - Connection pooling

### SUMO Integration

**Critical Rule**: ONLY use `shared/utilities/sumo_utils.generate_sumocfg_for_simulation()`

- DO NOT use deprecated `shared/data_processors/simulation_processor.generate_sumocfg()` (raises exception)

**SUMO Setup**:

- Requires SUMO installation and SUMO_HOME environment variable
- Alternatively: Set SUMO_BIN to full path of sumo.exe
- Version: 1.19+ recommended

### Language & Documentation

- **Primary Language for Comments**: Chinese (中文)
- **Code Variable Names**: English (lowercase with underscores)
- **Documentation**: Bilingual when possible

## Important Constraints

### Technical Constraints

1. **Python Environment**: MUST use `od_project` conda environment (not base, not od-sim)
2. **Path Handling**: Use `pathlib.Path` for all file operations (cross-platform)
3. **No Circular Dependencies**: Strictly enforced between API and Shared layers
4. **Pandas Operations**: Use vectorized operations (NO Python loops for data processing)
5. **File Operations**: Always check if files exist before reading
6. **Data Validation**: All API inputs must use Pydantic models
7. **Error Handling**: Use early returns, no broad except clauses
8. **Logging**: Never log sensitive data (credentials, passwords)
9. **Database**: Use connection pooling, SQLAlchemy for new code

### Operational Constraints

1. **Windows Platform**: System designed for Windows 10/11
2. **SUMO Installation**: Required for simulation execution
3. **Database Access**: PostgreSQL connection required for some features
4. **Environment Activation**: Always `conda activate od_project` before any work
5. **Server Startup**: Use `.\start_api.ps1` or `.\start_api.bat` scripts

### DO's and DON'Ts

**DO**:

- Use pathlib.Path for file operations
- Use pandas for data processing (vectorized)
- Validate inputs using Pydantic models
- Use logging module for output
- Return structured data from services
- Handle errors gracefully
- Use mamba for dependency installation

**DON'T**:

- Create circular dependencies
- Use deprecated `simulation_processor.generate_sumocfg()`
- Hardcode vehicle types
- Modify case/simulation metadata in analysis workflows
- Install dependencies in conda base environment
- Use print() statements (use logging)
- Create files in sim_scripts/ or accuracy_analysis/ (legacy code)
- Mix old and new simulation API endpoints inconsistently
- Run tests without activating `od_project` environment
- Use `open_db_connection()` - use connection pooling instead

## External Dependencies

### Required Services

- **PostgreSQL**: Gantry data, network topology, OD tables (10.149.235.123:5432)
- **SUMO (Simulation of Urban MObility)**: Traffic simulation engine
- **Python conda**: Environment management (od_project environment)

### External APIs

- None (closed system with database backend)

### Configuration Files

- `.env` - Database credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- `templates/` - Network, TAZ, vehicle type templates
- `templates/config_templates/vehicle_templates/vehicle_types.json` - Vehicle configuration
- `templates/edge_add/` - EdgeData configuration templates

### Key Documentation

- [CLAUDE.md](../CLAUDE.md) - Detailed AI assistant guidance
- [docs/development/新架构开发指南.md](../docs/development/新架构开发指南.md) - Development guide
- [docs/api_docs/新架构API指南.md](../docs/api_docs/新架构API指南.md) - Complete API documentation
- [docs/DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md) - Deployment instructions
- [openspec/AGENTS.md](./AGENTS.md) - OpenSpec change management process
