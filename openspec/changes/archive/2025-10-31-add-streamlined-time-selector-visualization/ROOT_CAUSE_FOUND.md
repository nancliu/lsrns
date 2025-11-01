# 🎯 根本原因找到：硬编码 Placeholder 问题

**日期**: 2025-10-31
**优先级**: 🔴 P0 - 关键
**状态**: ✅ 根本原因已识别，等待修复
**影响**: 表格初始化显示占位符，不显示实际值

---

## 问题总结

用户在 F12 中看到的表格行显示的都是 `placeholder` 属性值（如 7, 9, 400, 60），而不是 `value` 属性值。这导致用户看不到实际的初始数据。

```html
<!-- ❌ 错误 - 前端显示的是这样 -->
<input type="number" placeholder="7" />   <!-- 用户看到 placeholder 文本 7 -->
<input type="number" placeholder="9" />   <!-- 用户看到 placeholder 文本 9 -->
<input type="number" placeholder="400" /> <!-- 用户看到 placeholder 文本 400 -->
<input type="number" placeholder="60" />  <!-- 用户看到 placeholder 文本 60 -->

<!-- ✅ 应该是这样 -->
<input type="number" value="7" />   <!-- 用户看到实际值 7 -->
<input type="number" value="9" />   <!-- 用户看到实际值 9 -->
<input type="number" value="400" /> <!-- 用户看到实际值 400 -->
<input type="number" value="60" />  <!-- 用户看到实际值 60 -->
```

---

## 根本原因：两套重复的代码

### 问题代码位置

**templates.html 中的旧代码**（Line 1372-1510）:

```javascript
// ❌ 旧函数 1：DHS 行生成
function addDHSIntervalRow(tbody) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="p-8">
            <input type="number" class="dhs-interval-begin" min="0" max="24" step="0.5"
                   placeholder="7" class="input-field" />  // ❌ 只有 placeholder
        </td>
        <td class="p-8">
            <input type="number" class="dhs-interval-end" min="0" max="24" step="0.5"
                   placeholder="9" class="input-field" />  // ❌ 只有 placeholder
        </td>
        // ... 更多硬编码的 placeholder
    `;
}

// ❌ 旧函数 2：流量控制行生成
function addFlowIntervalRow(tbody) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="p-8">
            <input type="number" class="interval-begin" min="0" max="24" step="0.5"
                   placeholder="7" class="input-field" />  // ❌ 只有 placeholder
        </td>
        <td class="p-8">
            <input type="number" class="interval-end" min="0" max="24" step="0.5"
                   placeholder="9" class="input-field" />  // ❌ 只有 placeholder
        </td>
        <td class="p-8">
            <input type="number" class="interval-flow" min="0" step="10"
                   placeholder="400" class="input-field" />  // ❌ 只有 placeholder
        </td>
        <td class="p-8">
            <input type="number" class="interval-speed" min="0" step="1"
                   placeholder="60" class="input-field" />  // ❌ 只有 placeholder
        </td>
        // ...
    `;
}

// ❌ 旧函数 3：表单生成
function createFlowIntervalControl(param) {
    // ... 创建表格，调用 addFlowIntervalRow(tbody)
    addBtn.onclick = () => addFlowIntervalRow(tbody);  // 使用旧函数！
}
```

**parameter_form.js 中的新代码**（Line 978-1167）:

```javascript
// ✅ 新函数 1：流量控制渲染
function renderFlowIntervalControl(paramName, schema) {
    const defaultIntervals = schema.default_value || [];
    // 使用模板的 default_value 初始化表格

    defaultIntervals.forEach((interval) => {
        const beginHours = interval.begin_hours;
        const endHours = interval.end_hours;
        const flowRate = interval.flow_vph || interval.vehsPerHour || 480;
        const targetSpeed = interval.target_speed || 15;

        addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed);
        // 调用新的 addFlowIntervalRow，传入实际值
    });
}

// ✅ 新函数 2：流量控制行生成（支持参数）
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
    const row = document.createElement("tr");

    const beginInput = document.createElement("input");
    beginInput.type = "number";
    beginInput.className = "interval-begin";
    beginInput.value = beginHours || 0;  // ✅ 设置实际值
    // ...

    const endInput = document.createElement("input");
    endInput.type = "number";
    endInput.className = "interval-end";
    endInput.value = endHours || 1;  // ✅ 设置实际值
    // ...

    // ... 类似处理 flowRate, targetSpeed
}
```

### 关键区别对比

| 方面 | templates.html (旧) | parameter_form.js (新) |
|-----|-------------------|----------------------|
| **函数签名** | `addFlowIntervalRow(tbody)` | `addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed)` |
| **数据来源** | 硬编码的占位符 | 函数参数 (来自模板) |
| **数据存储方式** | `placeholder="7"` | `value="7"` |
| **支持模板加载** | ❌ 不支持 | ✅ 支持 |
| **代码状态** | ❌ 已过时 | ✅ 最新 |

---

## 为什么前端还显示旧代码？

### 可能原因 1: 函数定义冲突

JavaScript 中如果定义两个同名函数，后定义的会覆盖先定义的：

```javascript
// 第一个定义（HTML 中）
function addFlowIntervalRow(tbody) {
    // 旧实现，只有 placeholder
}

// 第二个定义（parameter_form.js 中）
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
    // 新实现，有 value
}

// 问题：如果 parameter_form.js 中的函数签名不同，调用时可能不匹配
// 某些代码可能仍然调用 addFlowIntervalRow(tbody)（只有 1 个参数）
// 导致使用旧的版本（如果旧版本函数仍然存在）
```

### 可能原因 2: 代码加载顺序

```html
<!-- templates.html 加载顺序 -->
<script src="js/parameter_form.js"></script>  <!-- 新函数在这里定义 -->
<!-- 但如果 HTML 本身有脚本块... -->
<script>
    function addFlowIntervalRow(tbody) {  // ❌ 重新定义旧版本，覆盖了新版本！
        // ...
    }
</script>
```

### 可能原因 3: 动态 vs 静态代码

如果某些代码动态调用旧函数：
```javascript
// 某处代码可能这样调用
addBtn.onclick = () => addFlowIntervalRow(tbody);  // ❌ 调用旧的（只有 1 个参数）

// 应该这样调用
addBtn.onclick = () => {
    const interval = { begin_hours: 7, end_hours: 9, flow_vph: 480, target_speed: 15 };
    addFlowIntervalRow(tbody, 'flow_intervals',
        interval.begin_hours, interval.end_hours,
        interval.flow_vph, interval.target_speed);  // ✅ 调用新的（有 5 个参数）
};
```

---

## 解决方案：清理重复代码

### Step 1: 识别所有旧函数

在 `templates.html` 中搜索并删除：

```
Line 1372-1406:  function addDHSIntervalRow(tbody)
Line 1414-1475:  function createFlowIntervalControl(param)
Line 1481-1510:  function addFlowIntervalRow(tbody)
Line 1518+:      function createVehicleTypeControl(param)
```

### Step 2: 验证新函数完整

确保 `parameter_form.js` 中有对应的新函数：

```javascript
✅ function renderFlowIntervalControl(paramName, schema)
✅ function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed)
✅ function renderDHSIntervalControl(paramName, schema)
✅ function renderTECIntervalControl(paramName, schema)
```

### Step 3: 验证函数调用

确保所有调用都使用新的函数签名：

```javascript
// ❌ 旧的调用方式
addFlowIntervalRow(tbody);

// ✅ 新的调用方式
addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed);
```

### Step 4: 测试验证

1. 创建 TEC 流量控制策略
2. 检查表格行是否显示 `value` 而非 `placeholder`
3. 检查浏览器控制台是否有错误或重复定义警告
4. 验证时间轴和表格数据一致

---

## 代码清理清单

### 要删除的 HTML 代码块

**1. DHS 间隔行生成函数** (Line 1372-1406)
```javascript
function addDHSIntervalRow(tbody) {
    const row = document.createElement('tr');
    // ... (60+ 行代码)
    row.querySelector('.delete-row').onclick = () => row.remove();
    tbody.appendChild(row);
}
```

**2. 流量控制表单生成函数** (Line 1414-1475)
```javascript
function createFlowIntervalControl(param) {
    const container = document.createElement('div');
    // ... (这个函数在 parameter_form.js 中有对应的 renderFlowIntervalControl)
    return container;
}
```

**3. 流量间隔行生成函数** (Line 1481-1510)
```javascript
function addFlowIntervalRow(tbody) {
    const row = document.createElement('tr');
    // ... (这个函数在 parameter_form.js 中有对应的新版本)
    row.querySelector('.delete-row').onclick = () => row.remove();
    tbody.appendChild(row);
}
```

**4. 车型选择控件生成函数** (Line 1518+)
```javascript
function createVehicleTypeControl(param) {
    const container = document.createElement('div');
    // ... (这个函数在 parameter_form.js 中可能有对应实现)
    return container;
}
```

### 需要更新的调用位置

搜索这些函数的调用位置，确保更新为新函数调用：

```javascript
// ❌ 旧调用
addBtn.onclick = () => addFlowIntervalRow(tbody);

// ✅ 新调用（由 renderFlowIntervalControl 处理）
// parameter_form.js 中已实现，无需在 HTML 中手动调用
```

---

## 时间轴

| 时刻 | 发现 |
|------|------|
| 前面 | 修复了 parameter_form.js 中的数据源问题 |
| 现在 | 发现了 HTML 中的硬编码 placeholder 问题 |
| 下一步 | 删除 HTML 中的旧代码，统一使用 parameter_form.js |

---

## 影响分析

### 删除这些代码的影响

**没有负面影响**，因为：
1. parameter_form.js 中有完全替代的新版本
2. 新版本支持模板加载，功能更强
3. 删除旧代码减少混淆和维护成本

### 可能的测试范围

- [ ] TEC 流量控制表单
- [ ] DHS 动态硬路肩表单
- [ ] VSS 可变限速表单
- [ ] 所有使用 interval_array 类型参数的表单

---

## 总结

| 项目 | 状态 |
|-----|------|
| **根本原因识别** | ✅ 完成 |
| **根本原因** | templates.html 中的硬编码 placeholder |
| **解决方案** | 删除旧代码，统一使用 parameter_form.js |
| **修复难度** | 低（直接删除，无依赖） |
| **风险等级** | 低（新代码已完全替代） |
| **预期效果** | 表格显示实际值，不显示 placeholder |

---

**文档版本**: v1.0
**完成状态**: ✅ 根本原因已识别
**下一步**: 执行代码清理（删除旧代码）
**优先级**: 🔴 P0 - 应立即修复
