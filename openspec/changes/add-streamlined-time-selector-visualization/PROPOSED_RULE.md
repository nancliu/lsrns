# 提议的项目规则：避免硬编码和代码重复

## 规则名称
**Rule: No Hardcoded Data & No Duplicate Code in Frontend**

**中文**: 前端禁止硬编码数据和代码重复

---

## 问题背景

在本项目开发中，发现表单参数初始化时出现硬编码的占位符值（placeholder），导致表格显示示例数据而不是实际的模板默认值。

**根本原因**: 存在两套重复的代码实现：
- HTML 模板中的旧版本（硬编码 placeholder="7", placeholder="9" 等）
- JavaScript 中的新版本（从模板 schema.default_value 动态加载）

前端仍然使用了旧的 HTML 版本，导致显示硬编码的占位符而非实际值。

---

## 规则定义

### Rule 1.1: 禁止在 HTML 中硬编码示例数据

**规则**:
- ❌ 禁止在 HTML `<input>`, `<select>`, `<textarea>` 的 `placeholder`, `value`, `content` 中硬编码任何示例数据
- ❌ 禁止在 HTML 中硬编码任何会随模板/配置变化的值
- ✅ 仅允许在 `placeholder` 中使用格式提示（如 "例如: 7" → "00:00" 这样的格式提示可以）
- ✅ 所有初始数据都应从 JSON 模板的 `default_value` 字段加载

**示例**:

```javascript
// ❌ 错误：硬编码示例数据
row.innerHTML = `
    <input type="number" placeholder="7" />      // ❌ 硬编码的数值
    <input type="number" placeholder="9" />      // ❌ 硬编码的数值
    <input type="number" placeholder="400" />    // ❌ 硬编码的流量值
    <select>
        <option value="open">开放</option>      // ❌ 硬编码的选项
    </select>
`;

// ✅ 正确：从参数加载数据
function addIntervalRow(tbody, beginHours, endHours, flowRate) {
    const row = document.createElement('tr');

    const beginInput = document.createElement('input');
    beginInput.type = 'number';
    beginInput.value = beginHours || 0;  // ✅ 从参数获取

    const endInput = document.createElement('input');
    endInput.type = 'number';
    endInput.value = endHours || 1;      // ✅ 从参数获取

    // ... 其他字段

    tbody.appendChild(row);
}
```

---

### Rule 1.2: 禁止代码重复 - 单一数据源原则

**规则**:
- ❌ 禁止同一功能在不同地方有多套实现
- ❌ 禁止 HTML、JS、Python 中有相同功能的重复代码
- ✅ 每个功能应有唯一的实现位置（Single Source of Truth）
- ✅ 其他位置应引用或调用这个唯一实现

**应用场景**:

| 场景 | 唯一源 | 其他位置 |
|------|-------|--------|
| 参数表单生成 | `parameter_form.js` | HTML 应删除重复的表单生成函数 |
| 时间轴渲染 | `timeline_visualizer.js` | 不应在其他地方重复实现 |
| 数据验证规则 | `shared/utilities/validation_utils.py` | 前端应调用 API 验证，不自行验证 |
| 枚举值定义 | 模板 `enum_values` 字段 | 前端不应硬编码枚举列表 |

**检查清单**:

```
在实现某个功能前，必须检查：
- [ ] 这个功能在 HTML 中是否已经有实现？
- [ ] 这个功能在 JS 中是否已经有实现？
- [ ] 这个功能在 Python 后端是否已经有实现？
- [ ] 如果有，我应该用现有实现，而不是重写一遍
```

**示例 - 反面教材**:

```javascript
// ❌ 错误：在 templates.html 中有一套实现
function addFlowIntervalRow(tbody) {
    row.innerHTML = `<input placeholder="7" />...`;
}

// ❌ 错误：在 parameter_form.js 中又有一套实现
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
    const row = document.createElement("tr");
    // ... 完全不同的实现
}

// ❌ 结果：两套代码混淆，维护困难，前端使用了错误的版本
```

**示例 - 正面教材**:

```javascript
// ✅ 正确：只在 parameter_form.js 中有一套实现
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
    const row = document.createElement("tr");
    const beginInput = document.createElement("input");
    beginInput.value = beginHours || 0;
    // ...
    tbody.appendChild(row);
}

// ✅ 在 HTML 中删除重复的函数

// ✅ 需要使用时直接调用这个函数
addFlowIntervalRow(tbody, 'flow_intervals', 7, 9, 480, 15);
```

---

### Rule 1.3: 数据流清晰化 - 来源可追溯

**规则**:
- ✅ 所有初始数据必须可以追溯到来源（模板文件中的 `default_value`）
- ✅ 代码中应有清晰的注释说明数据来源
- ✅ 不应有"神奇的数字"（Magic Number）
- ❌ 禁止在代码中出现来源不明的硬编码值

**数据流示例**:

```
正确的数据流：

模板 JSON 文件
  ↓
schema.default_value = [
  { begin_hours: 7, end_hours: 9, flow_vph: 480, target_speed: 15 },
  { begin_hours: 17, end_hours: 19, flow_vph: 300, target_speed: 10 }
]
  ↓
参数表单生成（parameter_form.js）
  ↓
const defaultIntervals = schema.default_value || [];
defaultIntervals.forEach(interval => {
  addFlowIntervalRow(
    tbody,
    paramName,
    interval.begin_hours,      // ✅ 来源：schema.default_value
    interval.end_hours,        // ✅ 来源：schema.default_value
    interval.flow_vph,         // ✅ 来源：schema.default_value
    interval.target_speed      // ✅ 来源：schema.default_value
  );
});
  ↓
表格行渲染
  ↓
用户看到的就是模板定义的默认值
```

---

### Rule 1.4: 代码审查清单 - 前端表单实现

在实现任何参数表单控件时，必须检查：

```
前端表单实现清单：

□ 数据来源
  □ 所有初始数据都来自 schema.default_value 吗？
  □ 有硬编码的示例数据吗？ ❌
  □ 代码中有注释说明数据来源吗？ ✅

□ 代码重复
  □ HTML 中是否有重复的表单生成代码？ ❌
  □ 是否在 parameter_form.js 中有对应的新版本？ ✅
  □ 是否已删除 HTML 中的旧版本？ ✅

□ 属性使用
  □ 使用的是 value 属性还是 placeholder 属性？ (value ✅)
  □ placeholder 中是否有硬编码的数值？ ❌
  □ placeholder 是否仅用于格式提示？ ✅

□ 功能完整性
  □ 新函数是否接受参数化的数据？ ✅
  □ 是否正确处理 undefined/null 值？ ✅
  □ 是否有错误处理？ ✅

□ 测试验证
  □ 是否用模板的 default_value 测试过？ ✅
  □ 是否用空值测试过？ ✅
  □ 是否在浏览器中验证了显示？ ✅
```

---

## 适用范围

### 适用于
- ✅ 前端 HTML/JavaScript 代码
- ✅ 参数表单生成（尤其是 parameter_form.js）
- ✅ 时间轴可视化（timeline_visualizer.js）
- ✅ 时间间隔、流量控制、速度限制等参数表单
- ✅ 所有从模板加载数据的地方

### 不适用于
- ❌ 后端 Python 代码（有自己的规则）
- ❌ 固定的 UI 框架代码（如导航栏、侧边栏）
- ❌ 纯粹的样式代码（CSS）

---

## 违反规则时的后果

| 违反规则 | 表现 | 影响 |
|---------|------|------|
| 硬编码示例数据 | 表格显示错误的初始值 | 用户困惑，功能不符预期 |
| 代码重复 | 修复一个地方，另一个地方仍有问题 | 维护困难，容易引入 bug |
| 数据来源不清晰 | 无法追踪值从何而来 | 调试困难，难以修复 |
| 混用 value 和 placeholder | 用户看不到实际的初始数据 | 严重的用户体验问题 |

---

## 执行方式

### 代码审查步骤

**在 Code Review 时检查**:

1. **搜索硬编码值**:
   ```bash
   # 查找可疑的 placeholder 值
   grep -n "placeholder=['\"]7['\"]" frontend/control/**/*.js
   grep -n "placeholder=['\"][0-9]" frontend/control/**/*.html

   # 查找硬编码的数据
   grep -n "begin_hours: 7\|end_hours: 9" frontend/control/**/*.js
   ```

2. **检查重复代码**:
   ```bash
   # 查找重复的函数定义
   grep -n "function addFlowIntervalRow" frontend/control/**/*.{js,html}
   grep -n "function renderFlowIntervalControl" frontend/control/**/*.{js,html}
   ```

3. **验证数据来源**:
   ```javascript
   // 追踪每个值的来源
   // 问：这个值从哪里来的？
   // 答：应该来自 schema.default_value 或函数参数
   // 如果答案是"硬编码"，那就违反规则了
   ```

### Git Commit 检查

在 commit 时，检查是否包含：
- ❌ 新增硬编码的占位符或值
- ❌ 重复的函数定义
- ✅ 完整的数据来源注释
- ✅ 参数化的函数实现

---

## 规则示例应用

### 场景 1: 添加新的参数表单控件

```javascript
// 步骤 1: 定义函数（在 parameter_form.js 中）
function renderMyCustomControl(paramName, schema) {
    const container = document.createElement('div');
    const defaultValue = schema.default_value || [];

    // ✅ 从 schema 加载数据
    defaultValue.forEach(item => {
        createRow(container, item);
    });

    return container;
}

function createRow(container, item) {
    // ✅ 从参数获取数据
    const row = document.createElement('div');
    row.innerHTML = `
        <input value="${item.value}" />
        <!-- ✅ 使用 value，不使用 placeholder -->
    `;
    container.appendChild(row);
}

// 步骤 2: 在 HTML 中删除任何重复的旧实现
// ❌ 不要在 templates.html 中定义相同的函数

// 步骤 3: 调用时传入数据
const control = renderMyCustomControl('my_param', parameterSchema);
```

### 场景 2: 修复硬编码问题

```javascript
// ❌ 发现的问题
row.innerHTML = `
    <input placeholder="7" />
    <input placeholder="9" />
    <input placeholder="400" />
`;

// ✅ 修复方案
function addRow(tbody, beginHours, endHours, flowRate) {
    const row = document.createElement('tr');

    const beginInput = document.createElement('input');
    beginInput.value = beginHours;  // ✅ 参数化

    const endInput = document.createElement('input');
    endInput.value = endHours;      // ✅ 参数化

    const flowInput = document.createElement('input');
    flowInput.value = flowRate;     // ✅ 参数化

    // ... 添加到 row ...
    tbody.appendChild(row);
}

// 调用时从模板加载数据
template.default_value.forEach(item => {
    addRow(tbody, item.begin_hours, item.end_hours, item.flow_vph);
});
```

---

## 规则强制机制

### 推荐配置

**在项目的 lint 或 pre-commit 检查中添加**:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: no-hardcoded-placeholders
      name: Check for hardcoded placeholders
      entry: grep -r "placeholder=['\"][0-9]" frontend/control
      language: system
      types: [javascript, html]
      pass_filenames: false
      fail_code: 1

    - id: no-duplicate-functions
      name: Check for duplicate function definitions
      entry: bash -c 'test $(grep -c "function addFlowIntervalRow" frontend/control/**/*.{js,html}) -eq 1'
      language: system
      pass_filenames: false
      fail_code: 1
```

### 代码审查模板

在 PR 描述或 Code Review 模板中添加：

```markdown
### 前端代码检查清单

- [ ] 是否有硬编码的数据值（placeholder, value 等）？
- [ ] 是否存在重复的函数实现？
- [ ] 所有数据都来自模板的 default_value 吗？
- [ ] 是否正确使用了 value 属性而不是 placeholder？
- [ ] 代码中是否有清晰的数据来源注释？

如果任何项目不符合，请退回 PR 要求修复。
```

---

## 规则版本历史

| 版本 | 日期 | 变更 | 原因 |
|------|------|------|------|
| 1.0 | 2025-10-31 | 初始版本 | 发现硬编码 placeholder 问题 |

---

## 相关文档

- [ROOT_CAUSE_FOUND.md](./ROOT_CAUSE_FOUND.md) - 问题的根本原因分析
- [HARDCODED_PLACEHOLDER_ISSUE.md](./HARDCODED_PLACEHOLDER_ISSUE.md) - 硬编码问题的详细分析

---

## 常见问题 (FAQ)

**Q: 如果真的需要硬编码一些示例数据怎么办？**
A: 将其放在模板的 `default_value` 字段中，而不是在代码中硬编码。

**Q: placeholder 属性应该怎么用？**
A: placeholder 只应用于格式提示，如 "格式: HH:MM" 或 "例如: 60"，不应包含数值。

**Q: 如何处理遗留代码中的硬编码值？**
A: 创建 issue，优先级标记为 P1/P2，在下一个迭代中逐步清理。

**Q: 重复的函数该保留哪一个？**
A: 保留功能最完整、最新的版本（通常在 parameter_form.js 中），删除旧的版本。

---

**规则提议者**: Claude Code Assistant
**提议日期**: 2025-10-31
**规则 ID**: RULE-FE-001-NO-HARDCODE
**优先级**: 🔴 高（直接影响数据正确性）
**生效日期**: 待项目确认
