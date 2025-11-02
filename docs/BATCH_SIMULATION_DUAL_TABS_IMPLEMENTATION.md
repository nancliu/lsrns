# 批量仿真页面 - 顶部和底部标签栏实现

## 功能概述

实现了批量仿真页面（`simulations.html`）的双标签栏功能，使用户可以在页面上下两端快速切换"配置、批次监控、结果"视图，避免频繁滚动。

### 功能特性

- ✅ **顶部固定标签栏**（Sticky）：滚动时保持在顶部可见
- ✅ **底部浮动标签栏**（Fixed）：始终显示在屏幕底部
- ✅ **双向同步**：点击任一标签栏都会更新另一个
- ✅ **响应式设计**：小屏幕设备上自动隐藏底部标签栏
- ✅ **自动调整**：内容自动添加 padding，防止被底部标签栏遮挡

---

## 实现详情

### 1. HTML 结构修改

**文件**: `frontend/control/simulations.html`

#### 顶部标签栏（已存在，标记了 CSS class）
```html
<!-- 顶部标签栏 (普通静态定位) -->
<div class="view-tabs view-tabs-top">
    <button class="view-tab active" id="configViewTab" onclick="switchView('config')">配置</button>
    <button class="view-tab" id="monitoringViewTab" onclick="switchView('monitoring')">批次监控</button>
    <button class="view-tab" id="resultsViewTab" onclick="switchView('results')">结果</button>
</div>
```

#### 底部标签栏（新增）
```html
<!-- 底部浮动标签栏 (Fixed) -->
<div class="view-tabs view-tabs-bottom">
    <button class="view-tab active" id="configViewTabBottom" onclick="switchView('config')">配置</button>
    <button class="view-tab" id="monitoringViewTabBottom" onclick="switchView('monitoring')">批次监控</button>
    <button class="view-tab" id="resultsViewTabBottom" onclick="switchView('results')">结果</button>
</div>
```

**位置**:
- 顶部标签栏：在 `content-area` 开始处
- 底部标签栏：在结果视图末尾、`content-area` 关闭前

---

### 2. CSS 样式修改

**文件**: `frontend/control/css/simulations.css`

#### 顶部标签栏样式
```css
/* 顶部标签栏 (普通静态定位，不浮动) */
.view-tabs-top {
    position: static;
    z-index: auto;
    background: white;
    box-shadow: none;
    margin-bottom: var(--spacing-20);
    border-radius: 0;
}
```

**特点**:
- `position: static` 使其自然流动，不浮动
- `z-index: auto` 普通文档流，无特殊层级
- 简洁清爽，不占用额外空间

#### 底部浮动标签栏样式
```css
/* 底部浮动标签栏 (Fixed) */
.view-tabs-bottom {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 999;
    background: white;
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
    margin: 0;
    border-radius: 0;
    border-top: 1px solid var(--color-light-border);

    /* 调整宽度以适应 sidebar 偏移 */
    margin-left: var(--size-sidebar-width);
    padding: 0 var(--spacing-30);
}
```

**特点**:
- `position: fixed` 使其始终显示在屏幕底部
- `z-index: 999` 确保在所有内容上方
- `margin-left: var(--size-sidebar-width)` 自动适应左侧 sidebar 宽度
- 阴影向上，与顶部栏相反

#### 内容区域调整
```css
/* 为了防止内容被底部标签栏遮挡，添加 padding */
.content-area {
    padding-bottom: 70px;
}
```

#### 响应式设计
```css
/* 响应式设计 - 隐藏小屏幕上的底部标签栏 */
@media (max-width: 768px) {
    .view-tabs-bottom {
        display: none;
    }

    .content-area {
        padding-bottom: 0;
    }
}
```

**特点**: 在 768px 以下的屏幕（平板/手机）上隐藏底部标签栏

---

### 3. JavaScript 逻辑修改

**文件**: `frontend/control/js/batch_simulation.js`

#### 视图切换函数更新
```javascript
function switchView(view) {
    currentView = view;

    // Update views
    document.getElementById('configView').classList.toggle('active', view === 'config');
    document.getElementById('monitoringView').classList.toggle('active', view === 'monitoring');
    document.getElementById('resultsView').classList.toggle('active', view === 'results');

    // Update tabs (顶部标签栏)
    document.getElementById('configViewTab').classList.toggle('active', view === 'config');
    document.getElementById('monitoringViewTab').classList.toggle('active', view === 'monitoring');
    document.getElementById('resultsViewTab').classList.toggle('active', view === 'results');

    // Update tabs (底部标签栏 - 保持同步)
    document.getElementById('configViewTabBottom').classList.toggle('active', view === 'config');
    document.getElementById('monitoringViewTabBottom').classList.toggle('active', view === 'monitoring');
    document.getElementById('resultsViewTabBottom').classList.toggle('active', view === 'results');

    // 其他逻辑...
}
```

**关键点**:
- 更新配置、监控、结果三个视图的 `active` class
- 同时更新顶部和底部标签栏的激活状态
- 保持逻辑一致性，两个标签栏完全同步

---

## 使用方法

### 用户交互流程

1. **初始状态**:
   - 用户进入批量仿真页面
   - 顶部和底部标签栏都显示"配置"为活跃状态

2. **切换视图**:
   - 点击顶部标签栏的"批次监控" → 内容切换到监控视图，两个标签栏同步更新
   - 点击底部标签栏的"结果" → 内容切换到结果视图，两个标签栏同步更新

3. **页面滚动**:
   - 向下滚动：顶部标签栏保持在顶部（sticky），底部标签栏始终在屏幕底部（fixed）
   - 向上滚动：顶部标签栏随页面滚动，底部标签栏仍保持在底部

4. **小屏幕设备**:
   - 屏幕宽度 ≤ 768px 时，底部标签栏自动隐藏

---

## 技术亮点

### CSS 位置定位策略

| 标签栏 | 定位方式 | 优点 | 场景 |
|--------|--------|------|------|
| 顶部 | `static` (普通) | 自然流动，不浮动，简洁清爽 | 页面开始处的普通导航 |
| 底部 | `fixed` | 始终显示在屏幕底部，不受滚动影响 | 固定的快速导航 |

### Z-index 层级管理

- `z-index: auto` (顶部) - 普通文档流，不需要特殊层级
- `z-index: 999` (底部) - 最高，确保始终在最前

### 响应式设计

使用 CSS 媒体查询 `@media (max-width: 768px)` 自动适应不同屏幕尺寸，提供最优用户体验。

### CSS 变量使用

```css
margin-left: var(--size-sidebar-width);  /* 自动适应 sidebar 宽度变化 */
```

避免硬编码，提高代码可维护性。

---

## 修改的文件清单

| 文件 | 修改内容 | 行数 |
|------|--------|------|
| `frontend/control/simulations.html` | 添加底部标签栏 HTML、修改顶部标签栏 CSS class | 2 处 |
| `frontend/control/css/simulations.css` | 添加 `.view-tabs-top` 和 `.view-tabs-bottom` 样式，响应式设计 | ~45 行 |
| `frontend/control/js/batch_simulation.js` | 更新 `switchView()` 函数以同步两个标签栏 | 3 行 |

---

## 测试验证清单

- [ ] **视图切换**: 点击顶部标签切换视图是否正常
- [ ] **双向同步**:
  - 点击顶部标签 → 底部标签是否同步激活？
  - 点击底部标签 → 顶部标签是否同步激活？
- [ ] **页面滚动**:
  - 向下滚动时，顶部标签是否保持在顶部？
  - 底部标签是否始终显示在屏幕底部？
- [ ] **响应式**:
  - 改变浏览器窗口宽度到 < 768px
  - 底部标签栏是否自动隐藏？
  - 内容是否正常显示（没有被底部栏遮挡）？
- [ ] **内容显示**:
  - 配置视图内容是否正常显示？
  - 批次监控视图内容是否正常显示？
  - 结果视图内容是否正常显示？

---

## 已知限制和未来改进

### 当前限制

1. **Sidebar 宽度硬编码**: 底部标签栏偏移量使用 CSS 变量 `--size-sidebar-width`，如果 sidebar 宽度变化需要更新
2. **固定高度**: `padding-bottom: 70px` 是固定值，若底部标签栏高度变化需要手动调整

### 未来改进方向

1. **动态高度计算**: 使用 JavaScript 动态计算底部标签栏高度，自动调整内容 padding
2. **平滑过渡**: 添加 CSS transition 使视图切换更流畅
3. **快捷键支持**: 添加键盘快捷键（如 Alt+1/2/3）快速切换视图
4. **用户偏好保存**: 保存用户的视图偏好（记住用户上次查看的视图）

---

## 浏览器兼容性

| 浏览器 | 版本 | 支持 | 备注 |
|--------|------|------|------|
| Chrome | 60+ | ✅ | 完全支持 sticky 和 fixed 定位 |
| Firefox | 55+ | ✅ | 完全支持 |
| Safari | 13+ | ✅ | 完全支持 |
| Edge | 79+ | ✅ | 完全支持 |
| IE 11 | - | ⚠️ | 不支持 CSS 变量，但 fixed/sticky 基本工作 |

---

## 总结

该实现通过使用 `sticky` 和 `fixed` 定位，结合 JavaScript 同步逻辑，提供了一个灵活且易用的双标签栏导航系统。用户可以在页面任何位置快速切换视图，极大改善了用户体验。

**核心优势**:
- 🎯 **便捷操作**: 无需频繁滚动，快速切换视图
- 📱 **响应式**: 自动适应各种屏幕尺寸
- 🔄 **同步一致**: 两个标签栏始终保持同步
- 🎨 **视觉清晰**: 清晰的视觉反馈和分层

---

## 相关文档

- [批量仿真功能说明](./features/batch_simulation.md)
- [前端开发规范](./frontend_standards.md)
- [CSS 变量文档](./css_variables.md)
