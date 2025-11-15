# 前端开发最佳实践

**版本**: 1.1
**最后更新**: 2025-11-15

## 目录

1. [案例筛选与数据加载](#案例筛选与数据加载)
2. [表单验证与选项处理](#表单验证与选项处理)
3. [API调用与错误处理](#api调用与错误处理)
4. [LocalStorage使用规范](#localstorage使用规范)
5. [代码复用与一致性](#代码复用与一致性)

---

## 案例筛选与数据加载

### 规范1: 加载所有相关数据

**问题**: 依赖默认分页可能导致数据遗漏

❌ **错误示例**:
```javascript
// 只加载第1页（默认10条）
const response = await fetch(`/api/v1/case/list_cases/`);
// 如果有20个案例，会遗漏后10个
```

✅ **正确示例**:
```javascript
// 对于全局选择器，加载所有数据
const response = await fetch(`/api/v1/case/list_cases/?page_size=1000`);
```

**适用场景**:
- 下拉选择框（`<select>`）
- 全局筛选器
- 数据导出功能

**性能考虑**:
- 数据量 < 1000: 一次加载所有
- 数据量 > 1000: 考虑虚拟滚动或搜索功能

### 规范2: 完整的案例类型识别

**问题**: 案例类型标识演化导致筛选不完整

❌ **错误示例**:
```javascript
// 只检查一个字段，无法识别所有事件场景案例
const isEventScenario = c.source_type === 'event_scenario';
```

✅ **正确示例**:
```javascript
// 检查所有可能的标识字段
const isEventScenario = (c) => {
    const sourceType = c.source_type || '';
    const caseType = c.case_type || '';

    return sourceType.includes('event_scenario') ||  // 包括batch
           caseType === 'event_based' ||             // 旧版本
           caseType === 'event_scenario_case';       // 新版本
};

// OD提取案例（排除事件场景）
const odCases = allCases.filter(c => !isEventScenario(c));

// 事件场景案例（包含事件场景）
const eventCases = allCases.filter(isEventScenario);
```

**标准案例类型标识**:

| 案例类型 | source_type | case_type | 优先级 |
|---------|-------------|-----------|--------|
| OD提取案例 | `od_extraction` | `null` 或其他 | - |
| 事件场景（单个） | `event_scenario` | - | 1 |
| 事件场景（批量） | `event_scenario_batch` | - | 1 |
| 事件场景（旧版） | `event_based` 或 `null` | `event_based` | 2 |
| 事件场景（新版） | - | `event_scenario_case` | 2 |

**检查优先级**:
1. 优先检查 `source_type`（最新标识）
2. 降级检查 `case_type`（向后兼容）
3. 使用 `includes()` 而非 `===` 匹配变种

### 规范3: 筛选逻辑一致性

**问题**: 多个页面使用不同的筛选逻辑导致结果不一致

✅ **解决方案**: 创建共享筛选函数

```javascript
// shared/case-filters.js
export function isEventScenarioCase(caseData) {
    const sourceType = caseData.source_type || '';
    const caseType = caseData.case_type || '';

    return sourceType.includes('event_scenario') ||
           caseType === 'event_based' ||
           caseType === 'event_scenario_case';
}

export function isODExtractionCase(caseData) {
    return !isEventScenarioCase(caseData);
}
```

```javascript
// 使用示例
import { isODExtractionCase, isEventScenarioCase } from './shared/case-filters.js';

// 批量优化页面（只要OD案例）
const odCases = allCases.filter(isODExtractionCase);

// 场景浏览器（只要事件场景案例）
const eventCases = allCases.filter(isEventScenarioCase);
```

**受影响的文件**:
- `frontend/control/js/batch_simulation.js`
- `frontend/script.js`
- `frontend/scenarios/scenario_browser.js`

---

## 表单验证与选项处理

### 规范4: 明确设置所有option属性

**问题**: 浏览器fallback到textContent作为value

❌ **错误示例**:
```javascript
const option = document.createElement('option');
option.disabled = true;
option.textContent = '所有案例都是事件场景案例...';
select.appendChild(option);
// 浏览器可能使用textContent作为value
```

✅ **正确示例**:
```javascript
const option = document.createElement('option');
option.value = '';  // ← 明确设置空字符串
option.disabled = true;
option.textContent = '所有案例都是事件场景案例...';
select.appendChild(option);
```

**必须设置的属性**:
- `value`: 始终明确设置（即使是空字符串）
- `disabled`: 禁用选项（如提示信息）
- `selected`: 默认选中（如果需要）

### 规范5: 验证自动选择逻辑

**问题**: 自动选择无效option导致后续错误

❌ **错误示例**:
```javascript
// 盲目选择第一个option，可能是placeholder或错误消息
if (select.options.length > 1) {
    selectedValue = select.options[1].value;
}
```

✅ **正确示例**:
```javascript
// 验证option有效性
for (let i = 1; i < select.options.length; i++) {
    const option = select.options[i];
    if (!option.disabled &&
        option.value &&
        option.value.startsWith('case_')) {  // 验证格式
        selectedValue = option.value;
        break;
    }
}
```

**验证检查清单**:
- [ ] option不是disabled
- [ ] value非空
- [ ] value符合预期格式（如`case_`开头）
- [ ] 记录选择结果（如保存到localStorage）

### 规范6: case_id格式验证

**问题**: 使用无效case_id调用API导致404错误

❌ **错误示例**:
```javascript
// 直接使用未验证的case_id
await fetch(`/api/v1/control/cases/${caseId}/duration`);
```

✅ **正确示例**:
```javascript
// 验证case_id格式
function isValidCaseId(caseId) {
    return caseId &&
           typeof caseId === 'string' &&
           caseId.startsWith('case_') &&
           caseId.length > 6;  // "case_" + 至少1个字符
}

// 使用前验证
if (isValidCaseId(caseId)) {
    await fetch(`/api/v1/control/cases/${caseId}/duration`);
} else {
    console.warn('Invalid case_id, skipping API call:', caseId);
}
```

**标准case_id格式**:
- ✅ `case_20251113_090649` (OD提取案例)
- ✅ `case_event_10754` (事件场景案例)
- ✅ `case_event_20251115_085331` (批量事件场景)
- ❌ `case_` (不完整)
- ❌ `""` (空字符串)
- ❌ `所有案例都是...` (错误消息)

---

## API调用与错误处理

### 规范7: 参数验证优先于API调用

**问题**: 无效参数导致不必要的网络请求和错误

❌ **错误示例**:
```javascript
async function loadCaseDuration(caseId) {
    const response = await fetch(`/api/cases/${caseId}/duration`);
    // 如果caseId无效，服务器返回404
}
```

✅ **正确示例**:
```javascript
async function loadCaseDuration(caseId) {
    // 前置验证
    if (!isValidCaseId(caseId)) {
        console.warn('Invalid case_id, skipping API call:', caseId);
        return null;
    }

    try {
        const response = await fetch(`/api/cases/${caseId}/duration`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to load case duration:', error);
        return null;  // 返回默认值而非抛出异常
    }
}
```

**验证检查清单**:
1. ✅ 参数非空
2. ✅ 参数类型正确
3. ✅ 参数格式有效（正则验证）
4. ✅ 参数在允许范围内

### 规范8: 优雅的错误降级

**问题**: 一个API失败导致整个页面不可用

❌ **错误示例**:
```javascript
// 阻塞式加载
const cases = await loadCases();        // 如果失败，页面卡住
const plans = await loadPlans();        // 永远不会执行
const duration = await loadDuration();  // 永远不会执行
```

✅ **正确示例**:
```javascript
// 并行加载 + 错误降级
const [cases, plans, duration] = await Promise.allSettled([
    loadCases(),
    loadPlans(),
    loadDuration()
]);

// 处理每个结果
if (cases.status === 'fulfilled') {
    populateCaseSelect(cases.value);
} else {
    console.error('Failed to load cases:', cases.reason);
    showWarning('案例列表加载失败，请刷新重试');
}

if (plans.status === 'fulfilled') {
    populatePlanSelect(plans.value);
} else {
    console.error('Failed to load plans:', plans.reason);
    // 计划加载失败不影响案例选择
}
```

**降级策略**:
- API失败 → 显示警告 + 使用缓存数据
- 数据为空 → 显示提示信息
- 格式错误 → 使用默认值

---

## LocalStorage使用规范

### 规范9: 存储前验证，读取后清理

**问题**: localStorage中存储无效数据导致后续错误

❌ **错误示例**:
```javascript
// 存储未验证的数据
localStorage.setItem('lastCaseId', someValue);

// 读取未验证的数据
const caseId = localStorage.getItem('lastCaseId');
loadCaseDuration(caseId);  // 可能是无效值
```

✅ **正确示例**:
```javascript
// 存储前验证
function saveCaseId(caseId) {
    if (isValidCaseId(caseId)) {
        localStorage.setItem('lastCaseId', caseId);
        return true;
    } else {
        console.warn('Invalid case_id, not saving to localStorage:', caseId);
        return false;
    }
}

// 读取后验证和清理
function loadCaseId() {
    const caseId = localStorage.getItem('lastCaseId');

    if (!isValidCaseId(caseId)) {
        // 清理无效数据
        if (caseId) {
            console.warn('Removing invalid case_id from localStorage:', caseId);
            localStorage.removeItem('lastCaseId');
        }
        return null;
    }

    return caseId;
}
```

**存储验证规则**:
- ✅ 类型检查（string, number, boolean）
- ✅ 格式验证（正则表达式）
- ✅ 范围检查（最大长度，允许值列表）
- ✅ 过期检查（时间戳）

### 规范10: 使用命名空间避免冲突

**问题**: 多个页面使用相同键名导致数据覆盖

❌ **错误示例**:
```javascript
// 多个页面都使用 'selectedCase'
localStorage.setItem('selectedCase', caseId);
```

✅ **正确示例**:
```javascript
// 使用页面特定的命名空间
const STORAGE_KEY = {
    BATCH_SIM_CASE: 'batchSim.selectedCaseId',
    BATCH_SIM_PLAN: 'batchSim.selectedPlanId',
    SCENARIO_BROWSER_FILTER: 'scenarioBrowser.filter'
};

localStorage.setItem(STORAGE_KEY.BATCH_SIM_CASE, caseId);
```

**命名规范**:
- 格式: `{页面}.{数据类型}`
- 示例: `batchSim.selectedCaseId`, `scenarioBrowser.filter`
- 避免: 通用名称如 `data`, `config`, `value`

---

## 代码复用与一致性

### 规范11: 提取共享筛选逻辑

**问题**: 多个文件重复相同的筛选代码

当前重复位置:
- `frontend/control/js/batch_simulation.js:233-246`
- `frontend/script.js:1133-1142`
- `frontend/scenarios/scenario_browser.js:75-88`

✅ **解决方案**: 创建共享模块

```javascript
// frontend/shared/case-utils.js

/**
 * 判断是否为事件场景案例
 * 支持所有案例类型标识（向前向后兼容）
 */
export function isEventScenarioCase(caseData) {
    if (!caseData) return false;

    const sourceType = caseData.source_type || '';
    const caseType = caseData.case_type || '';

    return sourceType.includes('event_scenario') ||
           caseType === 'event_based' ||
           caseType === 'event_scenario_case' ||
           caseData.metadata_version === '2.0';
}

/**
 * 判断是否为OD提取案例
 */
export function isODExtractionCase(caseData) {
    return !isEventScenarioCase(caseData);
}

/**
 * 验证case_id格式
 */
export function isValidCaseId(caseId) {
    return caseId &&
           typeof caseId === 'string' &&
           caseId.startsWith('case_') &&
           caseId.length > 6;
}
```

**使用方式**:

```javascript
// batch_simulation.js
import { isODExtractionCase } from '../shared/case-utils.js';

const odCases = allCases.filter(isODExtractionCase);
```

```javascript
// scenario_browser.js
import { isEventScenarioCase } from '../shared/case-utils.js';

const eventCases = allCases.filter(isEventScenarioCase);
```

### 规范12: 统一错误提示文案

**当前状态**: 不同文件使用不同错误提示

✅ **标准文案**:

创建 `frontend/shared/messages.js`:

```javascript
export const MESSAGES = {
    CASE_FILTER: {
        NO_OD_CASES: '所有案例都是事件场景案例，不支持此工作流。请使用OD提取的案例。',
        NO_EVENT_CASES: '暂无事件场景案例',
        INVALID_CASE_ID: '无效的案例ID格式'
    },
    API_ERROR: {
        LOAD_FAILED: '加载失败，请刷新重试',
        NETWORK_ERROR: '网络连接失败',
        SERVER_ERROR: '服务器错误'
    }
};
```

---

## 检查清单

### 新增案例筛选功能
- [ ] 使用 `page_size=1000` 加载所有案例
- [ ] 使用共享的 `isEventScenarioCase()` 或 `isODExtractionCase()`
- [ ] 检查所有案例类型标识（source_type, case_type）
- [ ] 使用 `includes()` 而非 `===` 匹配
- [ ] 添加空数据提示（无案例时）

### 新增选择器（select/dropdown）
- [ ] 明确设置所有option的value属性
- [ ] 验证自动选择逻辑（disabled、格式检查）
- [ ] 选择前验证数据格式
- [ ] 使用localStorage时验证和清理

### API调用
- [ ] 调用前验证所有参数
- [ ] 使用try-catch捕获错误
- [ ] 实现优雅降级（失败时使用默认值）
- [ ] 并行加载独立数据（Promise.allSettled）

### 代码质量
- [ ] 复用共享函数（不重复代码）
- [ ] 使用标准化文案（messages.js）
- [ ] 添加JSDoc注释
- [ ] 单元测试覆盖

---

## 相关文档

- [CLAUDE.md - 前端开发规范](../../CLAUDE.md#frontend-development-standards)
- [案例筛选修复报告](../fixes/CASE_FILTER_FIX_20251115.md)
- [API文档](../api_docs/新架构API指南.md)

---

**维护者**: OD_SIM开发团队
**版本历史**:
- 1.0 (2025-11-01): 初始版本
- 1.1 (2025-11-15): 添加案例筛选、表单验证、localStorage规范
