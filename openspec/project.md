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

### 前端数据规则：禁止硬编码数据和代码重复 (RULE-FE-001)

**RULE-FE-001**: 前端代码禁止硬编码数据和功能重复

**核心规则**:

1. **禁止在 HTML 中硬编码示例数据**
   - ❌ 禁止: `placeholder="7"`, `placeholder="9"`, `placeholder="400"` (硬编码数值)
   - ✅ 允许: `placeholder="例如: 7:00"` (仅格式提示)
   - ✅ 所有初始数据必须来自模板 JSON 的 `default_value` 字段
   - ✅ 使用 `value="..."` 属性存储实际数据，而非 `placeholder`

2. **单一数据源原则 - 禁止代码重复**
   - ❌ 禁止: 同一功能在 `templates.html` 和 `parameter_form.js` 中各有一份实现
   - ❌ 禁止: 不同版本的 `addFlowIntervalRow()` 函数存在于多个文件
   - ✅ 必需: 每个功能只有一个实现位置（Single Source of Truth）
   - ✅ 示例: 参数表单生成应仅在 `parameter_form.js` 中，不应在 HTML 中重复

3. **数据来源可追踪**
   - ✅ 每个数据值都必须能追溯到来源（模板的 `default_value`）
   - ✅ 代码必须有注释说明数据来源
   - ❌ 禁止: 来源不明的魔术数字（Magic Number）
   - ✅ 示例:
     ```javascript
     // ✅ 正确 - 数据来源清晰
     const defaultIntervals = schema.default_value || [];  // 来自模板
     defaultIntervals.forEach(interval => {
         addFlowIntervalRow(
             tbody,
             paramName,
             interval.begin_hours,    // ← 来自模板的 default_value
             interval.end_hours,      // ← 来自模板的 default_value
             interval.flow_vph,       // ← 来自模板的 default_value
             interval.target_speed    // ← 来自模板的 default_value
         );
     });
     ```

4. **参数化函数 - 不硬编码值**
   - ✅ 函数接受参数传递所有可变数据
   - ✅ 正确做法:
     ```javascript
     // ✅ 正确 - 所有数据通过参数传入
     function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
         const row = document.createElement("tr");
         const beginInput = document.createElement("input");
         beginInput.value = beginHours;  // ← 参数驱动
         // ... 其他字段 ...
     }
     ```
   - ❌ 错误做法（在 HTML 中硬编码）:
     ```javascript
     // ❌ 错误 - 硬编码值，无参数
     function addFlowIntervalRow(tbody) {
         row.innerHTML = `<input placeholder="7" />`;  // ← 硬编码!
     }
     ```

**前端代码审核检查清单**:

在审核前端 PR 时，必须验证：
- [ ] 不存在 `placeholder` 属性中的硬编码数值
- [ ] 不存在重复的函数定义（搜索 HTML 和 JS 中的同名函数）
- [ ] 所有初始数据都从模板的 `default_value` 加载，不硬编码
- [ ] 函数已参数化（接受数据作为参数）
- [ ] 数据来源在注释中清晰说明
- [ ] 使用 `value` 属性存储实际数据，不使用 `placeholder`

**违反影响**: 硬编码导致数据显示错误，代码重复导致维护困难和 bug 风险，数据来源不清晰导致调试困难。

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
