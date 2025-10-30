# 实时在网车辆曲线控制按钮 - 快速参考

## 功能概述

添加了一个**切换按钮**，允许用户手动控制"实时在网车辆数"曲线的显示/隐藏。

```
[实时在网车辆数]  [隐藏曲线] ← 新增按钮
┌─────────────────────────────┐
│                             │
│      Chart.js 折线图         │
│  (或 "仿真数据加载中...")    │
│                             │
└─────────────────────────────┘
```

---

## 核心改动

### 1. HTML (simulations.html)

```html
<button id="toggleLiveCurveBtn" class="btn btn-secondary">隐藏曲线</button>
```

### 2. JavaScript (batch_simulation.js)

**状态变量**：
```javascript
let liveCurveVisible = true;  // 控制曲线是否显示
```

**事件监听**：
```javascript
document.getElementById('toggleLiveCurveBtn')
  .addEventListener('click', toggleLiveCurveVisibility);
```

**切换函数**：
```javascript
function toggleLiveCurveVisibility() {
    liveCurveVisible = !liveCurveVisible;
    // 更新UI...
}
```

**渲染逻辑**：
```javascript
function renderLiveCurve(liveTimeSeries) {
    // 检查用户的toggle状态
    if (section) {
        section.style.display = liveCurveVisible ? 'block' : 'none';
    }
    // 根据状态显示/隐藏图表...
}
```

---

## 使用方式

### 场景1：隐藏不需要的曲线
1. 点击按钮"隐藏曲线"
2. 曲线区域消失
3. 按钮变为"显示曲线"

### 场景2：查看曲线数据
1. 点击按钮"显示曲线"
2. 曲线区域出现
3. 按钮变为"隐藏曲线"

### 场景3：数据加载中
1. 仿真刚启动，数据还在加载
2. 如果曲线显示，会看到"仿真数据加载中..."提示
3. 等待10秒后，数据到达，提示消失，曲线显示

---

## 状态转换图

```
┌─────────────────┐
│  初始状态       │
│ visible = true  │
│ 显示"隐藏曲线"  │
└────────┬────────┘
         │ 点击按钮
         ▼
┌─────────────────┐
│  用户隐藏       │
│ visible = false │
│ 显示"显示曲线"  │
└────────┬────────┘
         │ 点击按钮
         ▼
┌─────────────────┐
│  用户显示       │
│ visible = true  │
│ 显示"隐藏曲线"  │
└─────────────────┘
```

---

## 数据流

```
updateProgress()
  ├─> renderTaskList()
  │
  └─> renderLiveCurve(data.live_time_series)
      │
      ├─> 检查是否有数据
      │
      ├─> 检查liveCurveVisible状态 ⭐
      │   │
      │   ├─> true: 显示 (display: block)
      │   └─> false: 隐藏 (display: none)
      │
      └─> 有数据时渲染Chart.js图表
```

---

## 按钮样式

- **CSS类**: `btn btn-secondary`
- **文本**: 动态切换
  - 显示时: "隐藏曲线"
  - 隐藏时: "显示曲线"
- **事件**: `click` → `toggleLiveCurveVisibility()`

---

## 调试

**查看状态**：打开浏览器F12控制台，查看日志：
```
=== renderLiveCurve called ===
liveTimeSeries: {...}
liveCurveVisible state: true  ← 当前状态
Toggle live curve visibility to: false  ← 用户点击时
```

---

## 兼容性

- ✅ 所有现代浏览器
- ✅ 无需后端修改
- ✅ 不影响现有功能
- ✅ 向后兼容

---

## 文件清单

| 文件 | 修改行 | 说明 |
|------|--------|------|
| `frontend/control/simulations.html` | 556-563 | 添加切换按钮 |
| `frontend/control/js/batch_simulation.js` | 16 | 添加全局状态变量 |
| `frontend/control/js/batch_simulation.js` | 33 | 添加事件监听器 |
| `frontend/control/js/batch_simulation.js` | 493-621 | 更新renderLiveCurve函数 |
| `frontend/control/js/batch_simulation.js` | 623-640 | 添加toggleLiveCurveVisibility函数 |

---

## 测试清单

- [ ] 按钮在曲线区域显示
- [ ] 点击按钮，曲线显示/隐藏
- [ ] 按钮文本正确切换
- [ ] 轮询更新时，状态保持不变
- [ ] 无数据时，仍能切换显示
- [ ] 浏览器控制台无错误

---

**快速开始**：
1. 刷新页面（Ctrl+F5）
2. 启动批量仿真
3. 点击曲线旁的按钮切换显示

---
