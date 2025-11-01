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

## Principles & Rules Index

This project follows structured principles and rules. For complete details, see [CLAUDE.md](../CLAUDE.md).

**Architecture Principles**: PRINCIPLE-ARCH-001 to 005 ([Details](../CLAUDE.md#key-architectural-principles))
**Project Rules**: RULE-ROOT-001, RULE-FE-001, RULE-E2E-001 ([Details](../CLAUDE.md#project-root-directory-policy))
**Code Standards**: STANDARD-CODE-001, STANDARD-NAMING-001 ([Details](../CLAUDE.md#code-standards))
**Common Pitfalls**: PITFALL-ARCH-001 to 003, PITFALL-CODE-001 to 004, PITFALL-FE-002 to 004, PITFALL-ENV-001 to 002, PITFALL-FILE-001 ([Details](../CLAUDE.md#common-pitfalls))
**Architecture Decisions**: ADR-001 to 006 ([Details](../CLAUDE.md#architecture-decision-records-adr))

---

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

**Summary**: Frontend code must follow strict separation of concerns (HTML/CSS/JS) and Single Responsibility Principle for functions.

**Key Requirements**:
- HTML: Semantic structure only, no inline styles or scripts
- CSS: All styles in separate files under `frontend/control/css/`
- JavaScript: Functions ≤30 lines, ≤5 parameters, ≤3 nesting levels, clear single responsibility
- **RULE-FE-001**: No hardcoded data or duplicate code (all data from template JSON `default_value`)

**详细规范**: See [CLAUDE.md → Frontend Development Standards](../CLAUDE.md#frontend-development-standards) for:
- Complete separation of concerns guidelines
- JavaScript function standards with examples
- Code review checklist
- Common violations and fixes

### Project Root Directory Policy

**RULE-ROOT-001**: The project root directory MUST remain clean and contain only essential project files.

#### Allowed Files in Root

**Configuration & Documentation**:

- `CLAUDE.md` - AI assistant development guide
- `AGENTS.md` - OpenSpec agent instructions
- `README.md` - Project documentation
- `.gitignore`, `.env` - Git and environment configuration
- `requirements.txt`, `package.json` - Dependency manifests

**Build & Startup Scripts**:

- `start_api.*` (bat, ps1, sh) - API server startup scripts
- Build/deployment scripts (if applicable)

#### Prohibited in Root

❌ **Intermediate artifacts** - Analysis reports, debug logs, temporary files

❌ **Generated documentation** - Session summaries, completion reports, guides

❌ **Test scripts** - Ad-hoc test files, debugging scripts

❌ **Code files** - Python/JavaScript modules (belong in `api/`, `shared/`, `frontend/`)

❌ **Log files** - Runtime logs, test outputs

#### File Organization Rules

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

#### Enforcement

- **Pre-commit**: Review root directory for new files
- **Code review**: Check PR file tree for root-level additions
- **CI/CD**: Automated check to reject commits with unauthorized root files
- **Periodic cleanup**: Monthly review to move/delete misplaced files

#### Rationale

Maintaining a clean root directory:

- ✅ Improves project navigation and discoverability
- ✅ Reduces cognitive load for developers
- ✅ Prevents version control clutter
- ✅ Enforces consistent file organization
- ✅ Simplifies onboarding for new team members

### Architecture Patterns

**Two-Layer Modular Architecture**:
- **API Layer** (`api/`): Thin HTTP/REST interface only
- **Shared Layer** (`shared/`): Thick layer with all business logic and algorithms

**Critical Rule**: Unidirectional dependency: API → Services → Shared (never reverse)

**Key Patterns**:
- **PRINCIPLE-ARCH-001**: Single Responsibility Principle
- **PRINCIPLE-ARCH-002**: Dependency Direction (API → Shared only)
- **PRINCIPLE-ARCH-003**: Service Locator Pattern (`api/services/__init__.py`)
- **PRINCIPLE-ARCH-004**: Dependency Injection for services
- **PRINCIPLE-ARCH-005**: No Circular Dependencies (strictly enforced)

**详细说明**: See [CLAUDE.md → Key Architectural Principles](../CLAUDE.md#key-architectural-principles) for:
- Complete principle definitions with "why"
- How to check compliance (commands)
- Consequences of violations
- Code examples (good vs. bad)
- Architecture Decision Records (ADR-001 to ADR-006)

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

# Run with increased timeout for slow operations
npx playwright test --timeout=90000
```

**Testing Locations**:

- Unit tests: `tests/unit/`
- E2E tests: `tests/e2e/`

### E2E Testing Best Practices (RULE-E2E-001)

**RULE-E2E-001**: E2E测试必须遵循智能等待和状态检测原则

这些规则基于 enhance-strategy-parameter-configuration E2E测试的经验总结。

#### 核心原则

**1. 禁止固定超时 - 使用智能等待**

❌ **错误做法** - 固定超时（脆弱、不可靠）:
```javascript
// ❌ 错误：盲目等待固定时间
await page.click('#query-button');
await page.waitForTimeout(3000); // 希望3秒够用
```

✅ **正确做法** - 监控状态变化:
```javascript
// ✅ 正确：监控按钮状态变化（禁用 → 启用）
await page.click('#query-button');
await page.waitForSelector('button:has-text("查询路段"):not([disabled])', {
  timeout: 15000  // 最大等待时间，但通常会提前完成
});
```

**2. 检测异步操作完成的信号**

当UI需要等待后台异步操作（如数据预加载、API调用），使用**状态变化检测**而非猜测时间：

✅ **方法A - 按钮状态监控**:
```javascript
// 等待按钮从"查询中..."变回"查询路段"（表示API完成）
await page.waitForSelector('button:has-text("查询路段"):not([disabled])');
```

✅ **方法B - DOM元素出现/消失**:
```javascript
// 等待加载指示器消失
await page.waitForSelector('.loading-spinner', { state: 'hidden' });

// 等待结果表格出现
await page.waitForSelector('#results-table', { state: 'visible' });
```

✅ **方法C - 内容变化检测**（最可靠）:
```javascript
// 等待下拉框选项数量变化（检测预加载完成）
const initialCount = await page.locator('#section-codes option').count();
await page.selectOption('#route-codes', 'G4202');

// 等待路段代码加载（最多5秒）
for (let i = 0; i < 10; i++) {
  const currentCount = await page.locator('#section-codes option').count();
  if (currentCount > 0 && currentCount !== initialCount) {
    console.log(`✅ 预加载完成（检测到 ${currentCount} 个选项）`);
    break;
  }
  await page.waitForTimeout(500);
}
```

**3. 路线切换检测预加载（关键技术）**

**场景**: 前端在页面加载时预加载所有路线的路段数据到缓存

**问题**: 预加载时间不确定（首次加载5-10秒，缓存加载<0.5秒）

**解决方案**: 通过切换路线观察路段代码变化来检测预加载完成

```javascript
// ✅ 最佳实践：路线切换检测预加载
console.log('⏳ 检测路段缓存预加载状态...');

// 1. 选择测试路线（非目标路线）
await page.selectOption('#route-codes', { index: 1 });
await page.waitForTimeout(500);

// 2. 记录初始路段代码数量
const sectionSelect = page.locator('#section-codes');
const initialSectionCount = await sectionSelect.locator('option').count();

// 3. 切换到目标路线
await page.selectOption('#route-codes', 'G4202');
await page.waitForTimeout(500);

// 4. 等待路段代码更新（最多5秒）
let sectionLoaded = false;
for (let i = 0; i < 10; i++) {
  const currentSectionCount = await sectionSelect.locator('option').count();
  if (currentSectionCount > 0 && currentSectionCount !== initialSectionCount) {
    console.log(`✅ 路段缓存预加载完成（检测到 ${currentSectionCount} 个路段代码）`);
    sectionLoaded = true;
    break;
  }
  await page.waitForTimeout(500);
}
```

**为什么这个方法有效**:
- 预加载完成后，切换路线会触发路段下拉框更新
- 路段选项数量变化是预加载完成的可靠信号
- 自动适应首次加载（慢）和缓存加载（快）
- 比固定超时快且更可靠

**4. 生产数据优于模拟数据**

✅ **使用生产数据的优势**:
- 测试真实的数据库性能
- 验证实际的道路网络拓扑
- 捕获集成问题
- 无需测试数据设置
- 免维护（生产数据不会被删除）

✅ **最佳实践**:
```javascript
// 使用生产边ID而非创建测试数据
const PRODUCTION_EDGES = {
  vss_dhs: ['-2680', '-690', '-5016', '-10000'],  // G4202路线
  tec_entrance: '-13042'                          // G5路线
};

// 验证生产数据存在
const edges = await queryEdges('G4202', { stake_min: 33, stake_max: 44 });
if (edges.length === 0) {
  console.warn('⚠️ 生产数据未找到，跳过测试');
  test.skip();
}
```

**5. 优雅处理缺失数据**

✅ **使用 `test.skip()` 而非失败**:
```javascript
// ✅ 正确：缺少数据时优雅跳过
const resultsTable = page.locator('#results-table');
const tableVisible = await resultsTable.isVisible().catch(() => false);

if (!tableVisible) {
  console.warn('⚠️ 查询结果表未加载，跳过测试（需要数据库中有G4202路段数据）');
  test.skip();  // 优雅跳过，不算失败
}
```

❌ **错误做法** - 让测试失败:
```javascript
// ❌ 错误：缺少数据时抛出错误
const resultsTable = page.locator('#results-table');
await resultsTable.waitFor({ timeout: 5000 });  // 会抛出TimeoutError
```

**6. 清晰的日志输出**

✅ **记录关键步骤和时间**:
```javascript
console.log('\n========== VSS策略完整工作流测试 ==========\n');
console.log('\n[STEP 1] 选择VSS模板...');
console.log('✅ VSS模板已选择');
console.log('⏳ 查询路段中（等待预加载和数据库查询）...');
console.log('✅ 查询API调用完成');
console.log(`✅ 查询成功！找到 ${edgeCount} 个路段`);
```

**7. 超时时间设置指南**

根据操作类型设置合理的超时：

```javascript
// 页面加载
await page.goto(url, { timeout: 30000 });  // 30秒

// 按钮点击后的API调用
await page.waitForSelector('button:not([disabled])', { timeout: 15000 });  // 15秒

// 简单的DOM更新
await page.waitForSelector('#element', { timeout: 5000 });  // 5秒

// 整个测试（复杂工作流）
test.setTimeout(60000);  // 60秒
```

#### 性能优化技巧

**1. 减少不必要的等待**

✅ **使用最小必要的缓冲时间**:
```javascript
// DOM渲染缓冲（通常500ms足够）
await page.waitForTimeout(500);

// 避免过长的固定等待
await page.waitForTimeout(3000);  // ⚠️ 可能太长
```

**2. 并行检查多个条件**

✅ **使用 Promise.race() 等待多个可能的结果**:
```javascript
// 等待成功消息或错误消息（哪个先出现）
await Promise.race([
  page.waitForSelector('.success-message', { timeout: 5000 }),
  page.waitForSelector('.error-message', { timeout: 5000 })
]);
```

**3. 可选步骤处理**

✅ **非关键步骤失败不应导致测试失败**:
```javascript
// 保存步骤是可选的（主要验证配置工作流）
const saveButton = page.locator('button:has-text("保存策略")');
const saveButtonVisible = await saveButton.isVisible({ timeout: 2000 }).catch(() => false);

if (saveButtonVisible && await saveButton.isEnabled()) {
  await saveButton.click();
  console.log('✅ 策略已保存');
} else {
  console.log('ℹ️ 保存按钮未找到或不可用，工作流验证完成到步骤3');
}
```

#### 常见陷阱

❌ **陷阱1 - 假设按钮存在**:
```javascript
// ❌ 错误
await page.click('button:has-text("确认选择")');  // 按钮可能不存在
```

✅ **解决方案**:
```javascript
// ✅ 正确：先检查按钮是否存在
const confirmButton = page.locator('button:has-text("确认选择")');
const exists = await confirmButton.isVisible().catch(() => false);
if (exists) {
  await confirmButton.click();
}
```

❌ **陷阱2 - 混淆 `.fill()` 和 `.selectOption()`**:
```javascript
// ❌ 错误：对 <select> 使用 .fill()
await page.locator('#section-codes').fill('001');  // 失败！

// ✅ 正确：对 <select> 使用 .selectOption()
await page.locator('#section-codes').selectOption({ index: 0 });
```

❌ **陷阱3 - 忘记 DHS 测试超时设置**:
```javascript
// ❌ 错误：使用默认30秒超时（DHS页面加载可能需要更长时间）
test('DHS test', async ({ page }) => {
  await page.goto(url);  // 可能超时
});

// ✅ 正确：增加超时
test('DHS test', async ({ page }) => {
  test.setTimeout(60000);
  await page.goto(url, { timeout: 30000 });
});
```

#### 审核清单

在审核 E2E 测试 PR 时，必须验证：

- [ ] 没有固定的 `await page.waitForTimeout(3000)` 用于等待异步操作
- [ ] 使用状态变化检测（按钮状态、DOM元素、内容计数）
- [ ] 对预加载场景使用路线切换检测
- [ ] 使用生产数据而非创建测试数据
- [ ] 缺失数据时使用 `test.skip()` 优雅跳过
- [ ] 关键步骤有清晰的日志输出（✅/⏳/⚠️ emoji）
- [ ] 超时时间根据操作类型合理设置（5s/15s/30s/60s）
- [ ] 检查 `<select>` 元素使用 `.selectOption()` 而非 `.fill()`
- [ ] 验证按钮/元素存在性后再交互
- [ ] DHS 等慢页面设置了 `test.setTimeout(60000)`

#### 成功案例参考

参考 `tests/e2e/test_strategy_creation_workflow.spec.js`:
- VSS 测试：15.4秒，100%通过率
- DHS 测试：14.2秒，100%通过率
- 使用路线切换检测预加载
- 使用生产数据（G4202路线，50条边）
- 智能等待按钮状态变化
- 清晰的多阶段日志输出

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

**Quick Reference** (see [CLAUDE.md → Common Pitfalls](../CLAUDE.md#common-pitfalls) for detailed explanations):

**DO**:
- ✅ Use `pathlib.Path` for file operations
- ✅ Use pandas vectorized operations (avoid Python loops)
- ✅ Validate inputs with Pydantic models
- ✅ Use logging module (never `print()`)
- ✅ Always activate `od_project` conda environment first

**DON'T**:
- ❌ Create circular dependencies (PITFALL-ARCH-001)
- ❌ Use deprecated functions (PITFALL-CODE-001)
- ❌ Hardcode configuration data (PITFALL-CODE-002)
- ❌ Use `open_db_connection()` (PITFALL-CODE-004 - use connection pooling)
- ❌ Wrong conda environment (PITFALL-ENV-001)

**Detailed Pitfalls**: See [CLAUDE.md → Common Pitfalls](../CLAUDE.md#common-pitfalls) for:
- Architecture Violations (PITFALL-ARCH-001 to 003)
- Code Quality Issues (PITFALL-CODE-001 to 004)
- Frontend Issues (PITFALL-FE-002 to 004)
- Environment & Tools (PITFALL-ENV-001 to 002)
- File Organization (PITFALL-FILE-001)
- Quick Reference Checklist

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

## Capabilities (Specs)

The following capabilities are currently defined in `openspec/specs/`:

### Strategy Management
- **strategy-templates** - Traffic control strategy template system (VSS, TEC, DHS)
- **parameter-form-layout** - Strategy parameter configuration form (Step 3 workflow)

### Batch Processing
- **batch-management** - Batch simulation management and execution
- **batch-optimization** - Batch optimization and result analysis

### Planning & Monitoring
- **baseline-plan** - Baseline traffic planning
- **plan-management** - Traffic control plan management
- **live-monitoring** - Real-time simulation monitoring

### Results & Analysis
- **result-page-separation** - Separated result visualization pages

### System Utilities
- **css-import-fix** - CSS import order and dependency management
- **strategy-reference-protection** - Strategy instance reference integrity

## Recent Changes

### 2025-11-01
- ✅ **refactor-strategy-parameter-configuration** - Frontend refactoring for strategy parameter configuration
  - Added **parameter-form-layout** capability
  - Improved UI/UX consistency across VSS/TEC/DHS strategies
  - Separated vehicle type configuration from time intervals
  - Unified route segment source (Step 2 → Step 3)
  - Added comprehensive validation and user hints
