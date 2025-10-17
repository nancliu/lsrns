# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OD数据处理与仿真系统 (OD Data Processing and Simulation System) - A modular traffic simulation and analysis platform for Origin-Destination (OD) data processing using SUMO (Simulation of Urban MObility). The system manages cases, runs traffic simulations, and performs multiple types of analysis (accuracy, mechanism, performance, EdgeData).

**Current Version**: v0.9.0
**Language**: Python 3.10+
**Framework**: FastAPI + Pydantic
**Platform**: Windows 10/11

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

```bash
# Run tests (from project root)
pytest

# Run specific test
pytest tests/unit/test_specific.py

# Run with coverage
pytest --cov=api --cov=shared
```

### Dependencies

```powershell
# Install dependencies (use mamba first, then pip)
mamba install -y -c conda-forge --file requirements.txt
pip install -r requirements.txt
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

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Direction**: API → Services → Shared (utilities/data_access/analysis_tools/data_processors)
3. **Service Locator Pattern**: Services are managed through `api/services/__init__.py`
4. **Dependency Injection**: Used for managing service instances
5. **No Circular Dependencies**: Strictly enforced

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

## Database Access

### Configuration

Database connection requires `.env` file:
```env
DB_NAME=sdzg
DB_USER=username
DB_PASSWORD=password
DB_HOST=10.149.235.123
DB_PORT=5432
```

### Database Usage

- **Gantry data loading**: `shared/data_access/gantry_loader.py`
- **OD table resolution**: `shared/data_access/od_table_resolver.py`
- **Connection management**: `shared/data_access/connection.py`
- Always use connection pooling (SQLAlchemy)
- Never log sensitive data (credentials)

## Code Standards from Cursor Rules

### Function/Method Limits

- Max function length: 30 lines
- Max parameters: 5
- Max nesting depth: 3 levels
- Max class length: 300 lines
- Suggest split if >10 methods

### Naming Conventions

- **Variables/Functions**: snake_case (`process_gantry_data`)
- **Classes**: PascalCase (`GantryDataProcessor`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- **Files**: snake_case (`gantry_processor.py`)
- **Private methods**: prefix with underscore (`_process_data`)

### Required Practices

- Type hints on all functions (parameters and return values)
- Docstrings required (Google style)
- No `print()` statements (use logging)
- Use pandas vectorized operations (avoid Python loops for data processing)
- Early returns for error handling
- No broad except clauses

### Code Quality Tools

- **Formatter**: black
- **Linter**: flake8 (also consider ruff)
- **Line length**: 100 characters max
- **Indentation**: 4 spaces

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

### What NOT to Do

1. **Don't** create circular dependencies between modules
2. **Don't** use `shared/data_processors/simulation_processor.generate_sumocfg()` - it's deprecated
3. **Don't** hardcode vehicle types - use vehicle_templates.json
4. **Don't** let analysis workflows modify case/simulation metadata
5. **Don't** install dependencies in conda base environment
6. **Don't** use `print()` - use logging module
7. **Don't** create files in `sim_scripts/` or `accuracy_analysis/` directories (legacy code, kept for reference only)
8. **Don't** mix old and new simulation API endpoints inconsistently

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

- **Never** install in conda base environment
- Create dedicated environment: `mamba create -n od-sim python=3.10`
- Use mamba for installation (conda-forge channel), pip as fallback
- Activate environment before running: `mamba activate od-sim`

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
