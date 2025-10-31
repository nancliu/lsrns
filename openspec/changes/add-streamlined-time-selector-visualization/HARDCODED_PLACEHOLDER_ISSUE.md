# 硬编码 Placeholder 问题分析

**优先级**: 🔴 P0 - 关键缺陷
**发现日期**: 2025-10-31
**状态**: 🔍 分析中
**影响**: 表格初始化显示占位符而非实际值

---

## 问题描述

前端截图显示表格行中有硬编码的 `placeholder` 值（如 7, 9, 400, 60），而不是实际的数据值。

### 现象
```html
<!-- 截图中显示的 HTML 结构 -->
<input type="number" class="interval-begin" min="0" max="24" step="0.5" placeholder="7">
<input type="number" class="interval-end" min="0" max="24" step="0.5" placeholder="9">
<input type="number" class="interval-flow" min="0" step="10" placeholder="400">
<input type="number" class="interval-speed" min="0" step="1" placeholder="60">
```

**问题**: 用户看到的都是 placeholder（占位符），而不是实际的 value 值

---

## Root Cause Analysis（根本原因分析）

### 发现 1: 存在两套代码

**HTML 中的旧代码** (`templates.html` lines 1372-1510):
```javascript
function addDHSIntervalRow(tbody) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="p-8">
            <input type="number" class="dhs-interval-begin" min="0" max="24" step="0.5"
                   placeholder="7" class="input-field" />  // ❌ 硬编码示例值
        </td>
        // ... 更多硬编码 placeholder
    `;
}

function addFlowIntervalRow(tbody) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="p-8">
            <input type="number" class="interval-begin" min="0" max="24" step="0.5"
                   placeholder="7" class="input-field" />  // ❌ 硬编码示例值
        </td>
        // ... 更多硬编码 placeholder
    `;
}
```

**JS 中的新代码** (`parameter_form.js` lines 1095-1167):
```javascript
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
    const row = document.createElement("tr");

    const beginInput = document.createElement("input");
    beginInput.type = "number";
    beginInput.value = beginHours || 0;  // ✅ 设置实际值

    const endInput = document.createElement("input");
    endInput.type = "number";
    endInput.value = endHours || 1;  // ✅ 设置实际值

    // ... 类似处理 flowRate, targetSpeed
}
```

### 发现 2: 问题的本质

| 位置 | 代码质量 | 值设置 | 状态 |
|-----|--------|--------|------|
| templates.html (旧) | ❌ 硬编码 | placeholder 示例 | 已过时 |
| parameter_form.js (新) | ✅ 动态 | input.value = 实际值 | 应该使用 |

**问题**: 前端加载的可能仍然是旧的 HTML 函数，而不是 parameter_form.js 中的新函数

### 发现 3: 函数调用路径

```
模板加载页面
  ↓
renderFlowIntervalControl() (parameter_form.js 新版本)
  ├─→ container.appendChild(table)  ✅ 使用新的 addFlowIntervalRow
  └─→ addFlowIntervalRow(tbody) 调用
      ↓
      但如果页面仍加载 templates.html 中的旧版本函数...
      ↓
      使用硬编码的 placeholder，显示占位符而非实际值
```

---

## 诊断

### 问题 1: 两套重复代码

**HTML 中的函数** (已过时，应该删除):
- `addDHSIntervalRow(tbody)` - Line 1372
- `createFlowIntervalControl(param)` - Line 1414
- `addFlowIntervalRow(tbody)` - Line 1481
- `createVehicleTypeControl(param)` - Line 1518

**JS 中的函数** (现在应该使用):
- `addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed)` - parameter_form.js Line 1095
- `renderFlowIntervalControl(paramName, schema)` - parameter_form.js Line 978
- `renderDHSIntervalControl(paramName, schema)` - parameter_form.js Line 1149

### 问题 2: 硬编码的占位符值

HTML 中的硬编码示例:
```javascript
// ❌ 这些值都是硬编码的，与模板 default_value 无关
placeholder="7"   // 示例开始时间
placeholder="9"   // 示例结束时间
placeholder="400" // 示例流量
placeholder="60"  // 示例速度
```

### 问题 3: 没有设置 value 属性

HTML 中的代码只设置 placeholder，没有设置 value：
```html
<!-- ❌ 错误：只有 placeholder，没有 value -->
<input type="number" placeholder="7" />

<!-- ✅ 正确：应该设置 value -->
<input type="number" value="7" />
```

---

## 解决方案

### 方案 1: 删除 HTML 中的旧代码（推荐）

删除 `templates.html` 中的以下函数：
- Line 1372-1406: `addDHSIntervalRow()` 函数
- Line 1414-1475: `createFlowIntervalControl()` 函数
- Line 1481-1510: `addFlowIntervalRow()` 函数
- Line 1518+: `createVehicleTypeControl()` 函数

**理由**:
- 这些函数已被 parameter_form.js 中的版本替代
- HTML 中的版本使用硬编码，不从模板加载数据
- 删除减少重复代码，降低维护成本

### 方案 2: 更新 HTML 中的函数（如必须保留）

如果必须在 HTML 中保留这些函数，应该：

1. 为 `addFlowIntervalRow()` 添加参数：
```javascript
function addFlowIntervalRow(tbody, beginHours, endHours, flowRate, targetSpeed) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="p-8">
            <input type="number" class="interval-begin" min="0" max="24" step="0.5"
                   value="${beginHours || ''}" />  // ✅ 使用 value 而非 placeholder
        </td>
        <td class="p-8">
            <input type="number" class="interval-end" min="0" max="24" step="0.5"
                   value="${endHours || ''}" />
        </td>
        <td class="p-8">
            <input type="number" class="interval-flow" min="0" step="10"
                   value="${flowRate || ''}" />
        </td>
        <td class="p-8">
            <input type="number" class="interval-speed" min="0" step="1"
                   value="${targetSpeed || ''}" />
        </td>
        <td class="table-cell-center">
            <button type="button" class="delete-row btn btn-delete btn-small">删除</button>
        </td>
    `;
    row.querySelector('.delete-row').onclick = () => row.remove();
    tbody.appendChild(row);
}
```

2. 在调用时传入参数：
```javascript
// 从模板加载数据
const defaultIntervals = schema.default_value || [];
defaultIntervals.forEach(interval => {
    const beginHours = interval.begin_hours || 0;
    const endHours = interval.end_hours || 1;
    const flowRate = interval.flow_vph || interval.vehsPerHour || 480;
    const targetSpeed = interval.target_speed || 15;

    addFlowIntervalRow(tbody, beginHours, endHours, flowRate, targetSpeed);
});
```

---

## 建议采用的方案：方案 1（删除旧代码）

### 理由
1. **代码重复**: HTML 和 JS 中有完全相同的功能
2. **维护困难**: 修改一个地方需要同时修改两个地方
3. **数据一致性**: 新的 parameter_form.js 版本已支持从模板加载数据
4. **系统架构**: parameter_form.js 是统一的参数表单生成器，应该是唯一的真实来源

### 执行步骤

1. **确认 parameter_form.js 中的函数完整**:
   - ✅ `renderFlowIntervalControl()` 已完成
   - ✅ `renderDHSIntervalControl()` 已完成
   - ✅ `renderTECIntervalControl()` 已完成
   - ✅ `addFlowIntervalRow()` 已完成

2. **删除 templates.html 中的重复函数**:
   ```
   删除 Line 1359-1362（createDHSIntervalControl 的 addBtn 回调）
   删除 Line 1372-1406（addDHSIntervalRow 函数）
   删除 Line 1414-1475（createFlowIntervalControl 函数）
   删除 Line 1468（addFlowIntervalRow 回调）
   删除 Line 1481-1510（addFlowIntervalRow 函数）
   删除 Line 1518+ （createVehicleTypeControl 函数）
   ```

3. **验证 parameter_form.js 中的函数被正确调用**:
   - 检查 templates.html 中是否正确导入 parameter_form.js
   - 检查参数表单生成时是否调用了正确的函数

4. **测试所有表单控件**:
   - TEC 流量控制表单
   - DHS 时间区间表单
   - 其他参数表单

---

## 现象对应关系

### 当前观察到的问题
```
参数配置表单
  ├─→ 时间轴 (蓝色段，正确)
  └─→ 表格 (显示 placeholder)
       ├─ Start: placeholder="7" ❌
       ├─ End: placeholder="9" ❌
       ├─ Flow: placeholder="400" ❌
       └─ Speed: placeholder="60" ❌
```

### 原因推链
```
HTML 加载 templates.html
  ↓
parameter_form.js 加载（应该覆盖）
  ↓
但 HTML 中仍然有旧的 addFlowIntervalRow() 定义
  ↓
当调用 addFlowIntervalRow() 时，可能使用的是 HTML 版本
  ↓
HTML 版本只有 placeholder，没有 value
  ↓
显示占位符而非实际值
```

---

## 验收标准

### 修复后
- [ ] templates.html 中删除了所有旧的行生成函数
- [ ] parameter_form.js 中的函数被正确使用
- [ ] 表格行显示 `value` 而不是 `placeholder`
- [ ] 时间轴和表格数据一致
- [ ] 所有参数表单都正确显示默认值

### 测试清单
- [ ] 创建 TEC 流量控制策略，验证表格显示正确的数值
- [ ] 创建 DHS 策略，验证时间区间表格显示默认的 5 个时段
- [ ] 修改表格值，验证时间轴实时同步
- [ ] 刷新页面，验证数据正确保存和加载
- [ ] 检查浏览器控制台，确保没有错误或重复定义的函数警告

---

**文档版本**: v1.0
**完成度**: 分析完成，待实施修复
**下一步**: 删除旧代码，验证新代码正确运行
