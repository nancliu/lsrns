# 前端代码渐进式重构策略

**创建日期**: 2025-10-31
**关联文档**: [FRONTEND_CODE_COMPLIANCE_REPORT.md](./FRONTEND_CODE_COMPLIANCE_REPORT.md)
**适用范围**: `frontend/control/` 目录

---

## 核心原则

> **"不要一次性大重构，而是在开发过程中逐步改进"**

- ✅ 机会性重构：修改功能时顺便重构相关代码
- ✅ 渐进式改进：每次提交改进一小部分
- ✅ 测试先行：重构前确保有测试覆盖
- ❌ 避免大爆炸式重构：风险高、难以审查

---

## 重构优先级矩阵

### P0 - 关键（立即处理）

当您需要修改以下模块时，**必须**进行重构：

| 模块 | 文件 | 主要问题 | 重构收益 |
|------|------|----------|----------|
| 参数表单生成 | [parameter_form.js](../../frontend/control/js/parameter_form.js:1) | 10+函数>100行<br/>代码重复严重 | 提高可维护性<br/>减少bug |
| 策略管理 | [strategy_manager.js](../../frontend/control/js/strategy_manager.js:1) | `createInputElement()`145行<br/>单一职责违规 | 易于扩展新类型<br/>降低复杂度 |
| 批量仿真 | [batch_simulation.js](../../frontend/control/js/batch_simulation.js:1) | 图表函数>130行<br/>嵌套深度过深 | 图表复用<br/>性能优化 |

### P1 - 高优先级（计划处理）

当您有时间优化以下内容时处理：

| 模块 | 文件 | 重构内容 | 预计时间 |
|------|------|----------|----------|
| HTML模板 | [templates.html](../../frontend/control/templates.html:1) | 组件化拆分<br/>移除内联样式 | 8小时 |
| 网络可视化 | [network_viz.js](../../frontend/control/js/network_viz.js:1) | 拆分渲染/交互逻辑 | 6小时 |
| 路段选择器 | [edge_selector_embedded.js](../../frontend/control/js/edge_selector_embedded.js:1) | 拆分API/状态/渲染 | 4小时 |

### P2 - 中优先级（长期改进）

日常开发中持续改进：

- 改进函数命名（消除 `handle()`, `process()` 等模糊名称）
- 添加 JSDoc 注释
- 提取魔法数字为常量
- 统一错误处理模式

---

## 开发工作流集成

### 工作流图

```
┌─────────────────┐
│  接到开发任务    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ 1. 识别涉及的前端文件        │
└────────┬───────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 2. 查看 COMPLIANCE_REPORT.md       │
│    - 该文件有哪些违规？             │
│    - 优先级是什么？                 │
└────────┬───────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 3. 决策：是否顺便重构？             │
│    - P0问题 → 必须重构              │
│    - P1问题 + 时间充裕 → 建议重构   │
│    - P2问题 → 可选                  │
└────────┬───────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  是         否
    │         │
    │    ┌────┴────────────┐
    │    │ 仅实现新功能     │
    │    └─────────────────┘
    │
    ▼
┌────────────────────────────┐
│ 4. 重构前准备               │
│    - 创建测试（如无）       │
│    - 记录当前行为           │
│    - 新建功能分支           │
└────────┬──────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 5. 先重构，再开发           │
│    Commit 1: refactor       │
│    Commit 2: feat           │
└────────┬──────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 6. 测试 & 更新文档          │
│    - 运行E2E测试            │
│    - 更新重构进度           │
└────────────────────────────┘
```

---

## 每次修改前的检查清单

### 📋 代码修改前自查表

复制到您的代码审查工具或备忘录中：

```markdown
## 修改文件：____________________
## 功能描述：____________________

### 重构前检查
- [ ] 该文件在 COMPLIANCE_REPORT 中有违规记录吗？
- [ ] 我要修改的函数超过30行吗？
- [ ] 这个函数做了多件事吗（违反SRP）？
- [ ] 函数参数超过5个吗？
- [ ] 有重复代码可以提取吗？
- [ ] HTML中有 `style=""` 内联样式吗？
- [ ] 有硬编码的数据（magic numbers）吗？

### 如果勾选了任意一项 → 计划重构
- [ ] 评估重构时间：____ 小时
- [ ] 是否在本次任务中处理？ ☐ 是  ☐ 否（记录技术债务）
- [ ] 创建重构前测试用例

### 重构后验证
- [ ] 所有函数 ≤30 行
- [ ] 参数 ≤5 个（或使用config对象）
- [ ] 嵌套深度 ≤3 层
- [ ] 单一职责（每个函数只做一件事）
- [ ] 无代码重复
- [ ] E2E测试通过
```

---

## 具体重构指南

### 场景1：函数过长（>30行）

**识别**：在 [COMPLIANCE_REPORT.md](./FRONTEND_CODE_COMPLIANCE_REPORT.md:80) 中查找"Function Length Violations"

**示例**：`createInputElement()` (145行 → 需拆分为9个函数)

#### 重构步骤

**Step 1**: 识别职责边界

```javascript
// ❌ 原函数 - 145行，10个switch case
function createInputElement(param) {
    const container = document.createElement('div');

    switch(param.type) {
        case 'number':
            // 20行创建数字输入框
            break;
        case 'string':
            // 15行创建文本框
            break;
        case 'enum':
            // 25行创建下拉框
            break;
        // ... 7 more cases
    }

    return container;
}
```

**Step 2**: 提取类型处理器

```javascript
// ✅ 重构后 - 主函数只负责路由（12行）
function createInputElement(param) {
    const creators = {
        'number': createNumberInput,
        'string': createStringInput,
        'enum': createEnumInput,
        'boolean': createBooleanInput,
        'array': createArrayInput,
        'time_range': createTimeRangeInput,
        'step_array': createStepArrayInput,
        'enum_array': createEnumArrayInput,
    };

    const creator = creators[param.type] || createDefaultInput;
    return creator(param);
}

// ✅ 每个类型独立函数 - 各自<30行
function createNumberInput(param) {
    const container = document.createElement('div');
    container.className = 'form-group';

    const input = document.createElement('input');
    input.type = 'number';
    input.id = `param-${param.name}`;
    input.name = param.name;
    input.value = param.default_value || '';
    input.min = param.constraints?.min ?? '';
    input.max = param.constraints?.max ?? '';
    input.step = param.constraints?.step ?? 'any';
    input.placeholder = param.placeholder || '';
    input.required = param.required || false;

    const label = createLabel(param);
    const hint = createHint(param);

    container.appendChild(label);
    container.appendChild(input);
    if (hint) container.appendChild(hint);

    return container;
} // 24行 ✓

function createStringInput(param) {
    // 类似逻辑，<30行
}

// ... 其他类型
```

**Step 3**: 提取公共辅助函数

```javascript
// 辅助函数 - 可被多个creator复用
function createLabel(param) {
    const label = document.createElement('label');
    label.textContent = param.label || param.name;
    if (param.required) {
        const required = document.createElement('span');
        required.className = 'required';
        required.textContent = ' *';
        label.appendChild(required);
    }
    return label;
} // 10行 ✓

function createHint(param) {
    if (!param.description) return null;
    const hint = document.createElement('small');
    hint.className = 'form-hint';
    hint.textContent = param.description;
    return hint;
} // 7行 ✓
```

---

### 场景2：代码重复

**识别**：在报告中查找"Code Duplication Violations"

**示例**：[parameter_form.js](../../frontend/control/js/parameter_form.js:39) 中4个重复的时间轴更新函数

#### 重构步骤

**Before**（重复代码 ~200行）:

```javascript
// ❌ 4个几乎相同的函数
function updateTimelineFromTable(tbody) {
    const parameterName = tbody.dataset.parameterName;
    const container = tbody.closest('.step-array-control-enhanced');
    const timeline = container.querySelector('.parameter-timeline');
    const rows = tbody.querySelectorAll('.step-row');
    const steps = [];

    rows.forEach(row => {
        const timeInput = row.querySelector('.step-time');
        const speedInput = row.querySelector('.step-speed');
        if (timeInput && speedInput) {
            steps.push({
                time_hours: parseFloat(timeInput.value) || 0,
                speed_kmh: parseFloat(speedInput.value) || 0
            });
        }
    });

    steps.sort((a, b) => a.time_hours - b.time_hours);
    window.TimelineVisualizer.updateTimeline(timeline, steps, { type: 'speed' });
}

function updateDHSTimelineFromTable(tbody) {
    // 几乎完全相同的代码...只是字段名不同
}

function updateFlowTimelineFromTable(tbody) {
    // 几乎完全相同的代码...
}

function updateTECTimelineFromTable(tbody) {
    // 几乎完全相同的代码...
}
```

**After**（单一函数 ~30行）:

```javascript
// ✅ 统一的参数化函数
function updateTimelineFromTable(tbody, options = {}) {
    const {
        timeField = 'time_hours',
        valueField = 'speed_kmh',
        timeSelector = '.step-time',
        valueSelector = '.step-speed',
        visualizationType = 'speed'
    } = options;

    const container = tbody.closest('.step-array-control-enhanced');
    if (!container) {
        console.warn('[updateTimeline] Container not found');
        return;
    }

    const timeline = container.querySelector('.parameter-timeline');
    if (!timeline) return;

    const rows = tbody.querySelectorAll('.step-row, .interval-row');
    const steps = Array.from(rows)
        .map(row => extractStepData(row, timeSelector, valueSelector, timeField, valueField))
        .filter(step => step !== null)
        .sort((a, b) => a[timeField] - b[timeField]);

    window.TimelineVisualizer.updateTimeline(timeline, steps, {
        type: visualizationType
    });
}

// 辅助函数
function extractStepData(row, timeSelector, valueSelector, timeField, valueField) {
    const timeInput = row.querySelector(timeSelector);
    const valueInput = row.querySelector(valueSelector);

    if (!timeInput || !valueInput) return null;

    return {
        [timeField]: parseFloat(timeInput.value) || 0,
        [valueField]: parseFloat(valueInput.value) || 0
    };
}

// 使用方式
updateTimelineFromTable(tbody); // 默认：speed类型
updateTimelineFromTable(tbody, { valueField: 'status', visualizationType: 'status' }); // DHS
updateTimelineFromTable(tbody, { valueField: 'flow_vph', visualizationType: 'flow' }); // Flow
```

---

### 场景3：参数过多（>5个）

**识别**：在报告中查找"Parameter Count Violations"

**示例**：`addDHSIntervalRow()` 有7个参数

#### 重构步骤

**Before**:

```javascript
// ❌ 7个参数 - 难以记忆，容易出错
function addDHSIntervalRow(tbody, paramName, beginHours, endHours, status, allowedVehicles, intervalStructure) {
    // 99行函数体...
}

// 调用时容易搞错顺序
addDHSIntervalRow(tbody, 'dhs_intervals', 7, 9, 'open', ['passenger'], {...});
```

**After**:

```javascript
// ✅ 使用配置对象 - 清晰、可扩展
function addDHSIntervalRow(tbody, config) {
    const {
        paramName,
        beginHours = 0,
        endHours = 24,
        status = 'closed',
        allowedVehicles = [],
        intervalStructure = {}
    } = config;

    // 函数体...
}

// 调用时清晰明了
addDHSIntervalRow(tbody, {
    paramName: 'dhs_intervals',
    beginHours: 7,
    endHours: 9,
    status: 'open',
    allowedVehicles: ['passenger'],
    intervalStructure: {...}
});
```

---

### 场景4：嵌套深度过深（>3层）

**识别**：在报告中查找"Nesting Depth Violations"

**示例**：`updateProgress()` 中的多层if嵌套

#### 重构步骤

**Before**:

```javascript
// ❌ 4-5层嵌套
function updateProgress(batchId) {
    fetch(`/api/v1/batch/${batchId}/progress`)
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'pending') {
                const estimatedDiv = document.getElementById('estimated-completion');
                if (estimatedDiv) {
                    if (data.estimated_remaining_seconds) {
                        if (data.estimated_remaining_seconds > 0) {
                            estimatedDiv.textContent = formatTime(data.estimated_remaining_seconds);
                        } else {
                            estimatedDiv.textContent = '即将完成';
                        }
                    } else {
                        estimatedDiv.textContent = '计算中...';
                    }
                }
            }
        });
}
```

**After**:

```javascript
// ✅ 使用早期返回 + 辅助函数
async function updateProgress(batchId) {
    const data = await fetchProgressData(batchId);
    if (data.status === 'pending') return;

    updateEstimatedCompletion(data);
    updateTaskList(data);
    updateLiveCurve(data);
}

function updateEstimatedCompletion(data) {
    const estimatedDiv = document.getElementById('estimated-completion');
    if (!estimatedDiv) return;

    estimatedDiv.textContent = getEstimatedText(data.estimated_remaining_seconds);
}

function getEstimatedText(remainingSeconds) {
    if (!remainingSeconds) return '计算中...';
    if (remainingSeconds <= 0) return '即将完成';
    return formatTime(remainingSeconds);
}
```

---

### 场景5：移除内联样式

**识别**：在HTML中搜索 `style="`

**示例**：[templates.html:232](../../frontend/control/templates.html:232)

#### 重构步骤

**Before**:

```html
<!-- ❌ 内联样式 -->
<div class="step-navigation" style="display: none; margin-bottom: 15px;">
    <button onclick="nextStep()">下一步</button>
</div>

<div class="viz-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; padding: 20px; color: #7f8c8d;">
    正在加载...
</div>
```

**After**:

```html
<!-- ✅ 使用CSS类 -->
<div class="step-navigation hidden">
    <button onclick="nextStep()">下一步</button>
</div>

<div class="viz-loading">
    正在加载...
</div>
```

```css
/* 在 templates-layout.css 中 */
.step-navigation {
    margin-bottom: 15px;
}

.step-navigation.hidden {
    display: none;
}

.viz-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    padding: 20px;
    color: #7f8c8d;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 8px;
    min-width: 200px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    z-index: 10;
}
```

---

## Git 提交规范

### 提交信息格式

```
<type>(scope): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `refactor` | 重构（不改变功能） | `refactor(parameter-form): Split renderStepArrayControl` |
| `feat` | 新功能 | `feat(strategy): Add multi-select for routes` |
| `fix` | Bug修复 | `fix(timeline): Correct time conversion logic` |
| `style` | 代码格式（不影响逻辑） | `style(frontend): Remove inline styles from templates.html` |
| `docs` | 文档更新 | `docs(refactor): Update progress tracking` |

### 重构提交示例

```bash
# 示例1：函数拆分
git commit -m "refactor(strategy-manager): Split createInputElement into type handlers

- Extract 9 type-specific input creators (number, string, enum, etc.)
- Reduce function length from 145 lines to <30 lines each
- Improve testability and maintainability

Refs: FRONTEND_CODE_COMPLIANCE_REPORT.md Section 1.1
Closes: #ISSUE-123"

# 示例2：消除重复
git commit -m "refactor(parameter-form): Consolidate timeline update functions

- Merge 4 duplicate functions into single parameterized function
- Reduce code duplication by ~200 lines
- Add config options for different timeline types

Refs: FRONTEND_CODE_COMPLIANCE_REPORT.md Section 4"

# 示例3：样式分离
git commit -m "style(templates): Move inline styles to CSS files

- Remove 24 inline style attributes from templates.html
- Add utility classes in templates-inline-utilities.css
- Improve style consistency and maintainability

Refs: FRONTEND_CODE_COMPLIANCE_REPORT.md Section 5"
```

### 功能开发 + 重构的提交策略

**策略A：两次提交（推荐）**

```bash
# Commit 1: 先重构
git add frontend/control/js/strategy_manager.js
git commit -m "refactor(strategy-manager): Split createInputElement before adding new type"

# Commit 2: 再开发
git add frontend/control/js/strategy_manager.js
git commit -m "feat(strategy): Add date-time input type support"
```

**策略B：单次提交（小改动）**

```bash
git commit -m "feat(strategy): Add date-time input type

- Add createDateTimeInput() function (28 lines)
- Refactor createInputElement() to use type handler pattern
- Update form validation for datetime fields"
```

---

## 重构进度追踪

### 追踪表模板

创建文件：`docs/frontend_analysis/REFACTORING_PROGRESS.md`

```markdown
# 前端重构进度追踪

**开始日期**: 2025-10-31
**预计完成**: 2025-12-31 (8周)

## P0 - 关键模块

### parameter_form.js (2,258行)

| 函数 | 原长度 | 状态 | 完成日期 | PR链接 |
|------|--------|------|----------|--------|
| renderStepArrayControl | 100行 | ⏳ 进行中 | - | - |
| addDHSIntervalRow | 99行 | 📋 待处理 | - | - |
| renderDHSIntervalControl | 110行 | 📋 待处理 | - | - |
| renderFlowIntervalControl | 107行 | 📋 待处理 | - | - |
| renderTECIntervalControl | 106行 | 📋 待处理 | - | - |
| extractFormParameters | 100行 | 📋 待处理 | - | - |
| addFlowIntervalRow | 73行 | 📋 待处理 | - | - |

**进度**: 0/7 (0%)

### strategy_manager.js (2,509行)

| 函数 | 原长度 | 状态 | 完成日期 | PR链接 |
|------|--------|------|----------|--------|
| createInputElement | 145行 | 📋 待处理 | - | - |
| createEnumArrayControl | 61行 | 📋 待处理 | - | - |
| generateParameterForm | 52行 | 📋 待处理 | - | - |

**进度**: 0/3 (0%)

### batch_simulation.js (1,105行)

| 函数 | 原长度 | 状态 | 完成日期 | PR链接 |
|------|--------|------|----------|--------|
| createInputElement | 145行 | 📋 待处理 | - | - |
| renderPeakCurveChart | 139行 | 📋 待处理 | - | - |
| renderLiveCurve | 136行 | 📋 待处理 | - | - |
| updateProgress | 118行 | 📋 待处理 | - | - |
| renderTaskList | 82行 | 📋 待处理 | - | - |

**进度**: 0/5 (0%)

## P1 - 高优先级

### templates.html (4,108行)

| 任务 | 状态 | 完成日期 | 备注 |
|------|------|----------|------|
| 移除内联样式(24处) | 📋 待处理 | - | - |
| 拆分为组件 | 📋 待处理 | - | 需要架构设计 |

### network_viz.js (1,245行)

| 函数 | 原长度 | 状态 | 完成日期 |
|------|--------|------|----------|
| renderNetworkProgressive | 82行 | 📋 待处理 | - |
| showTooltip | 59行 | 📋 待处理 | - |
| resizeCanvas | 60行 | 📋 待处理 | - |

## 总体进度

| 优先级 | 总任务数 | 已完成 | 进行中 | 待处理 | 完成率 |
|--------|---------|--------|--------|--------|--------|
| P0 | 15 | 0 | 0 | 15 | 0% |
| P1 | 6 | 0 | 0 | 6 | 0% |
| P2 | ~ | - | - | - | - |
| **合计** | 21+ | 0 | 0 | 21 | **0%** |

## 本周计划 (Week of YYYY-MM-DD)

- [ ] 重构 `createInputElement()` - 预计4小时
- [ ] 移除 templates.html 内联样式 - 预计2小时

## 已完成里程碑

_待更新..._

## 技术债务变化

| 日期 | 估算工时 | 变化 | 备注 |
|------|---------|------|------|
| 2025-10-31 | 146小时 | 基线 | 初始评估 |

## 备注

- 状态说明：✅ 已完成 | ⏳ 进行中 | 📋 待处理 | ⏸️ 暂停 | ❌ 取消
- 更新频率：每次重构完成后更新
```

---

## 测试策略

### 重构前测试

**目标**：确保现有功能不被破坏

#### 1. 创建快照测试

```javascript
// tests/frontend/snapshot_test.js
describe('Parameter Form - Before Refactoring', () => {
    test('renderStepArrayControl generates correct HTML structure', () => {
        const template = {
            parameter_schema: {
                speed_steps: {
                    type: 'step_array',
                    label: '速度步骤',
                    default_value: [
                        { time_hours: 7, speed_kmh: 60 },
                        { time_hours: 9, speed_kmh: 80 }
                    ]
                }
            }
        };

        const container = document.createElement('div');
        // 调用原函数
        const result = renderStepArrayControl(container, 'speed_steps', template.parameter_schema.speed_steps);

        // 保存HTML快照
        expect(container.innerHTML).toMatchSnapshot();
    });
});
```

#### 2. E2E测试覆盖

```javascript
// tests/e2e/strategy_creation.spec.js
test('策略创建完整流程', async ({ page }) => {
    // Step 1: 选择模板
    await page.goto('http://localhost:8000/frontend/control/templates.html');
    await page.click('[data-template-id="template_vss_001"]');

    // Step 2: 选择路段
    await page.click('#step2-next-bottom');
    // ... 路段选择逻辑

    // Step 3: 配置参数
    await page.click('#step3-next-bottom');
    await page.fill('#param-strategy-name', '测试策略');

    // 添加速度步骤
    await page.click('.add-step-btn');
    await page.fill('.step-time', '7');
    await page.fill('.step-speed', '60');

    // 提交
    await page.click('#submit-strategy-btn');

    // 验证成功
    await expect(page.locator('.success-message')).toBeVisible();
});
```

### 重构后测试

**目标**：验证重构后功能一致

#### 1. 行为一致性测试

```javascript
describe('Parameter Form - After Refactoring', () => {
    test('createNumberInput produces same result as before', () => {
        const param = {
            type: 'number',
            name: 'max_speed',
            label: '最大速度',
            default_value: 120,
            constraints: { min: 0, max: 200 }
        };

        const result = createNumberInput(param);

        // 验证结构
        expect(result.querySelector('input')).toBeTruthy();
        expect(result.querySelector('label').textContent).toBe('最大速度');
        expect(result.querySelector('input').value).toBe('120');
        expect(result.querySelector('input').min).toBe('0');
        expect(result.querySelector('input').max).toBe('200');
    });
});
```

#### 2. 集成测试

```javascript
test('Refactored functions integrate correctly', () => {
    const template = loadTestTemplate('vss_template.json');

    // 使用重构后的函数
    const form = generateFormFromTemplate(template);

    // 验证与快照一致
    expect(form.outerHTML).toMatchSnapshot('vss-form-structure');

    // 验证交互
    const addButton = form.querySelector('.add-step-btn');
    addButton.click();
    expect(form.querySelectorAll('.step-row').length).toBe(3);
});
```

---

## 常见问题 (FAQ)

### Q1: 重构时遇到紧急bug怎么办？

**A**: 优先修复bug，但仍然遵循代码标准：

```bash
# 1. 快速修复（可以暂时不完美）
git commit -m "fix(critical): Quick fix for production issue #123"

# 2. 后续重构（纳入计划）
# 在 REFACTORING_PROGRESS.md 中添加该模块的重构任务
```

### Q2: 重构后测试失败怎么办？

**A**: 检查清单：

1. 是否改变了DOM结构？→ 更新测试选择器
2. 是否改变了API响应？→ 检查mock数据
3. 是否改变了行为？→ **回滚，这不是重构**

真正的重构不应改变外部行为。

### Q3: 如何决定是否在当前任务中重构？

**A**: 决策树：

```
该模块有P0违规？
├─ 是 → 必须重构
└─ 否 →
    该函数>50行或SRP违规严重？
    ├─ 是 →
    │   有充足时间（>当前任务50%）？
    │   ├─ 是 → 建议重构
    │   └─ 否 → 记录技术债务，下次处理
    └─ 否 → 可选（时间允许时处理）
```

### Q4: 重构时发现架构问题怎么办？

**A**: 分层处理：

- **小重构**（函数拆分、去重）→ 直接在当前任务中完成
- **中重构**（文件拆分、模块化）→ 创建专门的重构任务
- **大重构**（架构调整）→ 需要OpenSpec提案，走正式流程

### Q5: 如何避免过度重构？

**A**: 遵循"三次法则"：

- 第1次写代码 → 完成功能即可
- 第2次看到类似代码 → 记下来，暂不重构
- 第3次遇到 → 确认模式，进行重构

不要为了"可能的未来需求"过度抽象。

---

## 团队协作

### Code Review 检查点

审查者应检查：

#### 对于重构PR：

- [ ] 是否有测试证明行为未改变？
- [ ] 是否真的简化了代码（而非仅仅"不同"）？
- [ ] 是否遵循了30行/5参数/3层嵌套规则？
- [ ] 是否有文档说明重构原因？
- [ ] 提交信息是否清晰（refs报告中的违规项）？

#### 对于功能+重构PR：

- [ ] 重构和功能是否分开提交？
- [ ] 重构提交在前，功能提交在后？
- [ ] 重构是否必要（P0）或合理（P1且时间充足）？

### 知识分享

**定期（双周）前端代码质量回顾会**：

- 展示本周期重构成果
- 分享遇到的难点和解决方案
- 更新重构进度追踪表
- 讨论下个周期计划

---

## 成功指标

### 短期目标（1个月）

- [ ] 完成3个P0函数重构（>100行 → <30行）
- [ ] 消除所有内联样式（24处）
- [ ] 消除1组重复代码（timeline或row函数）
- [ ] E2E测试覆盖率 >60%

### 中期目标（3个月）

- [ ] 所有P0问题解决
- [ ] 至少拆分1个大文件（>2000行）
- [ ] 所有函数 <50行（目标<30行）
- [ ] 代码重复率 <5%

### 长期目标（6个月）

- [ ] 所有文件 <500行
- [ ] 所有函数 <30行
- [ ] 零内联样式
- [ ] 零代码重复
- [ ] 测试覆盖率 >80%

---

## 附录

### 推荐工具

| 工具 | 用途 | 安装 |
|------|------|------|
| ESLint | 自动检测函数长度/复杂度 | `npm install --save-dev eslint` |
| Prettier | 代码格式化 | `npm install --save-dev prettier` |
| SonarLint | IDE实时代码质量检查 | VSCode插件 |
| jscpd | 检测代码重复 | `npm install -g jscpd` |

### ESLint 配置示例

```javascript
// .eslintrc.js
module.exports = {
    rules: {
        // 强制函数最大30行
        'max-lines-per-function': ['error', {
            max: 30,
            skipBlankLines: true,
            skipComments: true
        }],

        // 强制参数最多5个
        'max-params': ['error', 5],

        // 强制最大嵌套3层
        'max-depth': ['error', 3],

        // 强制最大复杂度
        'complexity': ['warn', 10]
    }
};
```

### 快速命令

```bash
# 检测函数长度
grep -n "^function\|^const.*=.*function\|^.*=>.*{" frontend/control/js/*.js | \
  awk -F: '{print $1":"$2}' | \
  while read func; do
    # 统计每个函数的行数
    # （需要更复杂的脚本，这里仅示例）
  done

# 检测内联样式
grep -rn 'style="' frontend/control/*.html

# 检测代码重复（需要 jscpd）
npx jscpd frontend/control/js/

# 运行所有前端测试
npm run test:e2e
pytest tests/unit/frontend/
```

---

## 相关文档

- [FRONTEND_CODE_COMPLIANCE_REPORT.md](./FRONTEND_CODE_COMPLIANCE_REPORT.md) - 详细违规分析
- [REFACTORING_PROGRESS.md](./REFACTORING_PROGRESS.md) - 进度追踪（待创建）
- [../../CLAUDE.md](../../CLAUDE.md) - 项目代码标准
- [../../project.md](../../project.md) - 项目架构指南

---

**文档维护者**: 开发团队
**最后更新**: 2025-10-31
**版本**: v1.0
