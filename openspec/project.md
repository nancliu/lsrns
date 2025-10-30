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

### Frontend Development Standards

**关注点分离原则 (Separation of Concerns)**:

前端代码必须严格遵循 HTML / CSS / JavaScript 分离：

1. **HTML 文件** (`frontend/control/*.html`)
   - 仅包含语义化 HTML 结构
   - NO inline styles (`style=""`)
   - NO inline scripts (`<script>` 内联代码)
   - 使用有意义的 class 和 id 用于样式和脚本钩子

2. **CSS 文件** (`frontend/control/css/*.css`)
   - 所有样式规则在单独的 .css 文件中
   - 优先使用 class 选择器而非 ID
   - 按功能模块或页面分组组织
   - 文件命名: `[page-or-component]-name.css`
   - 示例: `templates-base.css`, `edge_selector.css`, `batch_simulation.css`

3. **JavaScript 文件** (`frontend/control/js/*.js`)
   - 仅包含 JavaScript 逻辑，NO inline styles
   - 每个文件处理一个独立的功能模块
   - 必须遵循最小职责原则（Single Responsibility Principle）

**函数最小职责原则 (Single Responsibility Principle)**:

JavaScript 函数开发严格约束：

- **单一职责**: 每个函数只做一件事，职责清晰
- **最大长度**: 30 行代码
- **最大参数**: 5 个参数
- **最大嵌套**: 3 层深度
- **命名约定**: 函数名称必须清晰描述其单一职责
  - 好: `updateRouteDropdown()`, `validateFormInput()`, `fetchSimulationStatus()`
  - 差: `handleChange()`, `process()`, `doStuff()`

**函数分类与示例**:

```javascript
// 1. 事件处理函数：每个事件一个简单处理器，委托给功能函数
document.getElementById('btn').onclick = () => performAction();

// 2. 数据获取函数：每个 API 端点一个函数
async function fetchSimulationResults() { ... }
async function loadCaseMetadata() { ... }

// 3. DOM 操作函数：每个 UI 更新任务一个函数
function updateProgressBar(percent) { ... }
function renderResultsTable(data) { ... }

// 4. 验证函数：每个验证规则一个函数
function validateSpeedRange(speed) { ... }
function validateTimeFormat(time) { ... }

// 5. 格式化函数：每个格式转换一个函数
function formatTimestamp(date) { ... }
function formatSpeedValue(speed) { ... }
```

**反面例子 (禁止)**:

```javascript
// ❌ 错误：混合多个职责
async function handleFormSubmit(e) {
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
        </div>
      `;
    })
    .catch(err => console.error(err));
}
```

**正面例子 (推荐)**:

```javascript
// ✅ 正确：分离多个小的、职责清晰的函数

// 验证函数
function validateSpeedInput(speed) {
  return speed > 0 && speed <= 120;
}

// API 调用函数
async function updateSimulationSpeed(data) {
  const response = await fetch('/api/update', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  return response.json();
}

// 格式化函数
function formatResultDisplay(result) {
  return `<div class="result"><p>Speed: ${result.speed} km/h</p></div>`;
}

// DOM 更新函数
function renderResult(html) {
  document.getElementById('output').innerHTML = html;
}

// 事件处理函数：委托给其他专门函数
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

**审核清单**:

- [ ] 所有 HTML 文件中没有 `style=""` 属性
- [ ] 所有 HTML 文件中没有 `<script>` 内联代码
- [ ] 所有样式都在 `frontend/control/css/*.css` 文件中
- [ ] 每个 JavaScript 函数长度 ≤ 30 行
- [ ] 每个函数只做一件事，职责清晰
- [ ] 函数名称清晰描述其行为
- [ ] 没有深层嵌套（>3 层）
- [ ] 没有混合事件处理、数据获取、验证和 DOM 操作的函数

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
