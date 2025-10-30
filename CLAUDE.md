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

### Database Performance

**Performance Issue (Fixed 2025-10-22)**: Route selection causing 5+ second delay

**Root Causes Identified**:

1. **Frontend**: Unnecessary `updateDirectionOptions()` API call on every route selection
   - Called `GET /api/v1/control/edges/query` with complex 3-table JOIN
   - Added 2-4 seconds delay just to populate direction dropdown
2. **Database**: Missing indexes on `dim.sim_network_edges` table (`route_code`, `section_code`)
3. **Database**: Missing indexes on JOIN tables (`multiscale_node_units`, `point_gantry`)
4. **Connection**: Using `open_db_connection()` (new connection each time) instead of pooling

**Solutions Applied**:

1. **Frontend Optimization** (`frontend/control/js/edge_selector_embedded.js`):

   - Removed dynamic direction query from `updateDirectionOptions()`
   - Implemented static route classification based on network topology:
     - **Ring expressways** (SA2, G4202): Show clockwise/counterclockwise
     - **Linear highways** (other routes): Show upstream/downstream
   - Instant response (0ms) with correct direction options per route type
2. **Database Indexes** (`database/migrations/004_add_edge_query_indexes.sql`):

   - `idx_sim_network_edges_route_code` - For route filtering
   - `idx_sim_network_edges_section_code` - For section grouping
   - `idx_sim_network_edges_route_section` - Composite index for common query pattern
   - `idx_sim_network_edges_demonstration_id` - Partial index for demonstration queries
   - `idx_multiscale_node_units_junction_id` - For JOIN optimization
   - `idx_point_gantry_route_stake` - For gantry range queries

**Performance Improvement**:

- **Before**: 5-10 seconds total (2-4s frontend delay + 3-6s database query)
- **After**: <500ms total (<100ms frontend + <400ms database with indexes)
- **User Experience**: Near-instant section dropdown population

**Future Optimizations** (if needed):

1. Migrate `edge_query.py` functions to use `get_pooled_connection()` from `connection.py`
2. Add query result caching (Redis or in-memory LRU cache)
3. Add database query monitoring/logging for slow queries (>2s threshold)

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
9. **Don't** run tests or scripts without activating `od_project` conda environment first
10. **Don't** run Playwright tests in conda base environment - always use `od_project`
11. **Don't** use `open_db_connection()` in new code - use connection pooling from `shared/data_access/connection.py` instead
12. **Don't** generate documentation or code files in the project root during testing/debugging - always create them in appropriate subdirectories:
    - Analysis documents → `docs/` (with suitable subdirectory like `docs/control_frontend/parameter_config_analysis/`)
    - Temporary test files → `tests/` or `test-results/`
    - Generated code → appropriate `api/`, `shared/`, or `frontend/` subdirectory
    - Never leave unorganized files in the root directory

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
