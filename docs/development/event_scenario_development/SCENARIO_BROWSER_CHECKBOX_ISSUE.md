# "只显示有案例的类别"复选框问题分析

**Date**: 2025-11-14
**Status**: ❌ **功能未实现**

---

## 问题描述

在场景浏览器界面中，有一个复选框：
```
☑ 只显示有案例的类别
```

**实际情况**: 这个复选框**没有任何作用**，是一个"死功能"。

---

## 代码分析

### 1. HTML中的复选框

**File**: `frontend/scenarios/scenario_browser.html:77-80`

```html
<label class="checkbox-label">
    <input type="checkbox" id="hasOnlyCases" checked>
    <span>只显示有案例的类别</span>
</label>
```

**状态**: 默认勾选 (`checked`)

---

### 2. JavaScript中的事件监听

**File**: `frontend/scenarios/scenario_browser.js:535-541`

```javascript
// "只显示有案例的类别" 复选框
const hasOnlyCasesCheckbox = document.getElementById('hasOnlyCases');
if (hasOnlyCasesCheckbox) {
    hasOnlyCasesCheckbox.addEventListener('change', (e) => {
        currentFilters.hasOnlyCases = e.target.checked;  // ✅ 更新状态
        applyFilters();  // ✅ 调用筛选函数
    });
}
```

**状态**: ✅ 事件监听器正常，会更新 `currentFilters.hasOnlyCases` 并调用 `applyFilters()`

---

### 3. 筛选逻辑 - 问题所在！

**File**: `frontend/scenarios/scenario_browser.js:279-292`

```javascript
function applyFilters() {
    filteredScenarios = allScenarios.filter(s => {
        const eventTypeMatch = currentFilters.eventType === 'all' || s.event_type === currentFilters.eventType;
        const strategyMatch = currentFilters.strategy === 'all' || s.strategy === currentFilters.strategy;
        const searchMatch = currentFilters.searchText === '' ||
            s.scenario_id.toLowerCase().includes(currentFilters.searchText) ||
            s.road.toLowerCase().includes(currentFilters.searchText) ||
            s.event_id.toLowerCase().includes(currentFilters.searchText);

        // ❌ 问题：这里只检查了3个条件，没有使用 hasOnlyCases！
        return eventTypeMatch && strategyMatch && searchMatch;
    });
    currentPage = 1;
    renderScenarios();
    renderPagination();
}
```

**问题**:
- ❌ 筛选逻辑中**完全没有使用** `currentFilters.hasOnlyCases`
- ❌ 无论复选框是否勾选，显示结果都一样
- ❌ 这是一个"死功能"，只是摆设

---

## 预期功能（未实现）

如果这个复选框按照其标签文字来实现，应该具有以下功能：

### 场景表格筛选模式

**勾选时** (☑ 只显示有案例的类别):
- 只显示 `scenarioCaseMap[scenario_id]` 不为空的场景
- 即：只显示有 `created_cases` 的场景

**取消勾选时** (☐ 只显示有案例的类别):
- 显示所有场景（无论是否有案例）

---

## 实际影响

### 当前状态
由于功能未实现，复选框状态对显示结果**没有任何影响**：

```
☑ 勾选 → 显示全部 473 个场景
☐ 取消 → 显示全部 473 个场景  (结果相同！)
```

### 用户体验问题
1. 误导用户：用户以为勾选会起作用，实际上没有
2. 混淆功能：复选框默认勾选，但没有任何效果
3. 浪费界面空间：占用了筛选区域的位置

---

## 解决方案

### 方案1: 实现这个功能（推荐）

修改 `applyFilters()` 函数，添加案例筛选逻辑：

```javascript
function applyFilters() {
    filteredScenarios = allScenarios.filter(s => {
        const eventTypeMatch = currentFilters.eventType === 'all' || s.event_type === currentFilters.eventType;
        const strategyMatch = currentFilters.strategy === 'all' || s.strategy === currentFilters.strategy;
        const searchMatch = currentFilters.searchText === '' ||
            s.scenario_id.toLowerCase().includes(currentFilters.searchText) ||
            s.road.toLowerCase().includes(currentFilters.searchText) ||
            s.event_id.toLowerCase().includes(currentFilters.searchText);

        // ✅ 新增：只显示有案例的场景
        const hasCasesMatch = !currentFilters.hasOnlyCases ||
                             (scenarioCaseMap[s.scenario_id] && scenarioCaseMap[s.scenario_id].length > 0);

        return eventTypeMatch && strategyMatch && searchMatch && hasCasesMatch;
    });
    currentPage = 1;
    renderScenarios();
    renderPagination();
}
```

**效果**:
- ☑ 勾选时：只显示有案例的场景（目前3个场景）
- ☐ 取消时：显示所有场景（473个场景）

---

### 方案2: 移除这个复选框

如果不需要这个功能，直接删除：

**删除 HTML** (`scenario_browser.html:77-80`):
```html
<!-- 删除这段 -->
<label class="checkbox-label">
    <input type="checkbox" id="hasOnlyCases" checked>
    <span>只显示有案例的类别</span>
</label>
```

**删除 JavaScript** (`scenario_browser.js:535-541`):
```javascript
// 删除这段事件监听器
const hasOnlyCasesCheckbox = document.getElementById('hasOnlyCases');
if (hasOnlyCasesCheckbox) {
    hasOnlyCasesCheckbox.addEventListener('change', (e) => {
        currentFilters.hasOnlyCases = e.target.checked;
        applyFilters();
    });
}
```

**删除初始化** (`scenario_browser.js:10`):
```javascript
// 删除这行
hasOnlyCases: true
```

---

## 建议

### 推荐方案1：实现功能

**理由**:
1. 这个功能很有用，可以快速定位已创建案例的场景
2. 界面已经设计好，只需添加筛选逻辑
3. 符合用户预期（有这个复选框就应该有作用）

### 实现优先级

**高优先级** - 如果用户经常需要：
- 查找已创建案例的场景
- 区分有案例和无案例的场景
- 管理和追踪场景案例状态

**低优先级** - 如果：
- 场景数量不多（目前473个）
- 已创建案例很少（目前只有3个）
- 用户很少使用这个筛选功能

---

## 当前数据

如果实现方案1，筛选效果如下：

### ☑ 勾选时（只显示有案例的场景）
显示 **2个场景**（去重后的event_case数量）:
```
1. scenario_10754_no_control (case_event_10754)
2. scenario_10754_tec (case_event_10754)
3. scenario_10814_tec (case_event_10814)
```

### ☐ 取消勾选时（显示所有场景）
显示 **473个场景**（全部场景）

---

## Summary

| 项目 | 状态 |
|-----|------|
| 复选框存在 | ✅ 有 |
| 事件监听 | ✅ 正常 |
| 筛选逻辑 | ❌ **未实现** |
| 实际作用 | ❌ **无** |
| 误导用户 | ✅ 是 |

**结论**: 这是一个"半成品"功能，界面和事件监听都有，但核心筛选逻辑缺失。

**建议**: 实现筛选逻辑或移除复选框，避免误导用户。

---

**Last Updated**: 2025-11-14
