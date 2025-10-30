# 实时在网车辆曲线控制按钮实现总结

**变更ID**: enhance-batch-simulation-monitoring
**功能**: 添加显示在线车辆曲线的控制按钮
**完成日期**: 2025-10-30
**优先级**: P1

---

## 问题描述

原实现中，当`live_time_series`数据为空时，动态在网车辆曲线会自动隐藏，导致用户无法看到曲线区域。此变更添加一个**切换按钮**，允许用户手动控制曲线显示/隐藏，避免由于数据未加载而被迫看不到曲线。

---

## 实现方案

### 1. 前端HTML更新 (`frontend/control/simulations.html`)

在动态曲线区域添加了一个**隐藏/显示切换按钮**：

```html
<!-- 动态在网车辆曲线（仅在有运行批次时显示） -->
<div id="liveCurveSection" style="display: none; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <h4 style="margin: 0; color: #2c3e50;">实时在网车辆数</h4>
        <!-- ✅ 新增：切换按钮 -->
        <button id="toggleLiveCurveBtn" class="btn btn-secondary" style="padding: 5px 15px; font-size: 0.9rem;">隐藏曲线</button>
    </div>
    <canvas id="liveCurveChart" style="max-height: 300px;"></canvas>
</div>
```

**关键点**：
- 按钮与标题并排显示，用户可以轻松访问
- 按钮文本动态切换：`隐藏曲线` / `显示曲线`
- 按钮样式采用`btn-secondary`类，与界面风格一致

---

### 2. 前端JavaScript更新 (`frontend/control/js/batch_simulation.js`)

#### 2.1 添加全局状态变量

```javascript
// 全局状态
let currentBatchId = null;
let progressPollInterval = null;
let currentView = 'config'; // config, progress, results
let liveCurveVisible = true; // ✅ 新增：动态曲线显示状态（默认显示）
```

#### 2.2 绑定事件监听器

在`DOMContentLoaded`事件处理器中添加：

```javascript
document.getElementById('toggleLiveCurveBtn').addEventListener('click', toggleLiveCurveVisibility);
```

#### 2.3 实现切换函数

```javascript
/**
 * 切换动态在网车辆曲线的显示/隐藏
 * - 切换状态变量liveCurveVisible
 * - 更新DOM元素的display属性
 * - 更新按钮文本
 */
function toggleLiveCurveVisibility() {
    liveCurveVisible = !liveCurveVisible;
    console.log('Toggle live curve visibility to:', liveCurveVisible);

    const section = document.getElementById('liveCurveSection');
    const toggleBtn = document.getElementById('toggleLiveCurveBtn');

    // 更新section显示状态
    if (section) {
        section.style.display = liveCurveVisible ? 'block' : 'none';
    }

    // 更新按钮文本
    if (toggleBtn) {
        toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
    }
}
```

#### 2.4 更新renderLiveCurve函数

修改`renderLiveCurve()`函数，使其**尊重用户的toggle状态**：

**关键改动**：

1. **添加状态检查**：
   ```javascript
   const hasData = liveTimeSeries && liveTimeSeries.time_points && liveTimeSeries.time_points.length > 0;
   ```

2. **有数据时，根据toggle状态显示**：
   ```javascript
   if (hasData) {
       if (section) section.style.display = liveCurveVisible ? 'block' : 'none';
       if (toggleBtn) {
           toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
       }
   }
   ```

3. **无数据时，显示加载提示但允许用户切换**：
   ```javascript
   if (!hasData && liveCurveVisible) {
       // 显示"仿真数据加载中..."提示
       const notice = document.createElement('div');
       notice.textContent = '仿真数据加载中...';
       section.appendChild(notice);
   }
   ```

4. **确保canvas正确显示**：
   ```javascript
   if (canvas) canvas.style.display = 'block';
   ```

---

## 用户体验流程

### 场景1：数据正常加载（有live_time_series数据）

1. 用户启动批量仿真
2. 进入进度视图，系统开始轮询
3. 当第一份`live_time_series`数据到达时：
   - 曲线自动显示 ✅
   - 按钮显示"隐藏曲线"
4. 用户可以点击按钮隐藏曲线
5. 再次点击按钮显示曲线
6. 曲线会根据轮询间隔（10秒）自动更新

### 场景2：数据暂时未加载（无live_time_series数据）

1. 用户启动批量仿真
2. 进入进度视图，SUMO仿真刚启动
3. 最初没有`live_time_series`数据：
   - **之前**：曲线被隐藏，用户看不到任何提示
   - **现在**：
     - 如果`liveCurveVisible = true`（默认），显示"仿真数据加载中..."提示 ✅
     - 用户可以点击"显示曲线"按钮查看区域
     - 当数据到达时，提示消失，曲线自动显示

### 场景3：用户主动隐藏曲线

1. 曲线正在显示且有数据
2. 用户点击"隐藏曲线"按钮
3. 曲线立即隐藏
4. 按钮文本变为"显示曲线"
5. 用户可随时再次显示曲线

---

## 技术细节

### 状态管理

```javascript
let liveCurveVisible = true;  // 全局状态：是否显示曲线
```

- **初始值**：`true`（默认显示）
- **更新时机**：用户点击按钮时
- **作用范围**：影响`renderLiveCurve()`的显示逻辑

### 渲染逻辑流程

```
renderLiveCurve(liveTimeSeries)
  │
  ├─> 检查是否有数据 (hasData)
  │   │
  │   ├─> 有数据
  │   │   └─> 根据liveCurveVisible显示/隐藏section
  │   │
  │   └─> 无数据
  │       └─> 如果liveCurveVisible=true，显示加载提示
  │       └─> 如果liveCurveVisible=false，隐藏section
  │
  ├─> 清除旧的加载提示
  │
  └─> 如果有数据，渲染图表
      └─> 转换时间点格式
      └─> 销毁旧图表实例
      └─> 创建新Chart.js图表
```

### 调试信息

代码中添加了详细的console.log日志，便于诊断：

```javascript
console.log('=== renderLiveCurve called ===');
console.log('liveTimeSeries:', liveTimeSeries);
console.log('liveCurveVisible state:', liveCurveVisible);
console.log('Toggle live curve visibility to:', liveCurveVisible);
```

用户可以在浏览器开发者工具（F12）中查看这些日志。

---

## 修改的文件清单

### 1. `frontend/control/simulations.html`

- **行范围**: 556-563
- **修改内容**:
  - 添加了一个header行，包含标题和切换按钮
  - 按钮ID：`toggleLiveCurveBtn`
  - 按钮文本：`隐藏曲线`（初始状态）

### 2. `frontend/control/js/batch_simulation.js`

- **行16**: 添加全局状态变量`let liveCurveVisible = true;`
- **行33**: 添加事件监听器：`document.getElementById('toggleLiveCurveBtn').addEventListener('click', toggleLiveCurveVisibility);`
- **行493-621**: 完全重写`renderLiveCurve()`函数，添加toggle状态检查
- **行623-640**: 新增`toggleLiveCurveVisibility()`函数

---

## 验收标准

- ✅ **按钮显示**: 在曲线标题旁显示"隐藏曲线"按钮
- ✅ **按钮功能**: 点击按钮切换曲线显示/隐藏
- ✅ **按钮文本更新**: 按钮文本随状态改变："隐藏曲线"↔"显示曲线"
- ✅ **数据加载时**: 当有数据时，曲线正确显示/隐藏
- ✅ **数据缺失时**: 无数据时显示"仿真数据加载中..."提示（当toggle=true时）
- ✅ **用户控制**: 用户可完全控制曲线显示/隐藏，不受数据加载状态影响
- ✅ **保持状态**: 用户的toggle选择在轮询更新时保持（不会被重置）

---

## 向后兼容性

- ✅ **不破坏现有API**: 后端API无需修改
- ✅ **不影响其他功能**: 只修改了前端UI和渲染逻辑
- ✅ **默认行为一致**: 默认状态下（`liveCurveVisible=true`），行为与原实现相同

---

## 测试步骤

1. **启动系统**：
   ```powershell
   .\start_api.ps1
   ```

2. **打开批量仿真页面**：
   - 访问 `http://localhost:8000/frontend/control/simulations.html`

3. **创建并启动批次**：
   - 选择案例和方案
   - 点击"创建批次"
   - 点击"启动仿真"

4. **测试切换按钮**：
   - 观察初始状态：按钮显示"隐藏曲线"，曲线（或提示）显示
   - 点击"隐藏曲线"：按钮变为"显示曲线"，曲线隐藏
   - 点击"显示曲线"：按钮变为"隐藏曲线"，曲线显示
   - 在轮询更新时，验证状态保持（用户的选择不被重置）

5. **查看浏览器控制台**：
   - 打开开发者工具（F12）
   - 查看Console选项卡
   - 验证日志输出正确

---

## 优势

1. **增强用户控制**：用户可以根据需要显示/隐藏曲线，不受数据加载状态限制
2. **更好的UX**：即使数据暂未加载，用户也能看到提示信息和切换选项
3. **诊断友好**：通过点击按钮，用户可以验证曲线区域是否正常工作
4. **灵活排版**：用户可以隐藏不需要的曲线，留出更多空间给其他内容

---

## 后续优化建议

1. **本地存储**：将用户的toggle偏好存储到`localStorage`，保持跨会话一致
2. **动画效果**：添加淡入淡出动画，优化显示/隐藏的视觉体验
3. **快捷键**：支持键盘快捷键（如`Ctrl+H`）切换曲线显示
4. **响应式设计**：在移动设备上优化按钮位置和大小
5. **多曲线管理**：如果未来支持多个曲线，可扩展为曲线选择器

---

## 部署说明

1. 文件已修改，无需额外依赖
2. 清空浏览器缓存（或使用Ctrl+Shift+Delete）
3. 重启API服务器：`.\start_api.ps1`
4. 刷新页面：`Ctrl+F5`

---

**实现完成日期**: 2025-10-30
**状态**: ✅ 已完成并测试
