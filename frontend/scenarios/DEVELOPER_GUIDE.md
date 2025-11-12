# 场景库浏览器 - 开发者指南

## 快速开始

### 文件位置
```
frontend/scenarios/scenario_browser.html
```

### 依赖
- Bootstrap 5.3.2 (via unpkg.com CDN)
- Bootstrap Icons 1.11.1 (via unpkg.com CDN)
- 无其他外部依赖

### 打开页面
```
http://localhost:8000/scenarios/scenario_browser.html
```

## 代码结构

### HTML 部分（~300 行）
```html
<head>
  - 元数据和链接
  - CSS 变量定义
  - 样式表 (<style>)
</head>

<body>
  - 导航栏
  - 统计卡片（4 个）
  - 二维筛选器
  - 场景列表表格
  - 快速创建案例模态框
  - 仿真分析配置模态框
  - JavaScript (<script>)
</body>
```

### CSS 部分（~300 行）
```css
:root - CSS 变量
  --primary-color: #1976d2
  --secondary-color: #388e3c
  --background-color: #f5f7fa
  --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.08)

组件样式：
  .navbar
  .stats-card
  .filter-section
  .dimension-chips / .dimension-chip
  .search-box
  .scenarios-table-wrapper
  .table
  .event-badge / .control-badge
  .action-buttons
  .modal-*
  .simulation-config-section
  等等
```

### JavaScript 部分（~400 行）

#### 全局变量
```javascript
let allScenarios = []              // 所有场景数据
let filteredScenarios = []         // 过滤后的场景
let currentFilters = {             // 当前筛选器状态
  eventType: 'all',
  controlStrategy: 'all',
  hasCasesOnly: true,
  searchText: ''
}
let currentScenario = null         // 当前选中的场景
```

#### 主要函数

**初始化相关**
```javascript
initializeFilters()        // 绑定筛选器事件监听
loadScenarios()           // 从 JSON 加载场景数据（异步）
generateMockData()        // 生成模拟数据用于演示
```

**数据处理相关**
```javascript
updateStats()             // 更新统计卡片
getEventTypeDisplay(type) // 获取事件类型显示名称
getControlBadgeClass()    // 获取管控策略 CSS 类
getEventBadgeClass(type)  // 获取事件类型 CSS 类
applyFilters()            // 应用所有筛选条件
renderScenarios()         // 渲染表格行
```

**交互相关**
```javascript
openQuickCreate()         // 打开创建案例模态框
submitQuickCreate()       // 提交创建案例请求（异步）
openSimulationAnalysis()  // 打开分析配置模态框
submitSimulationAnalysis()// 提交分析请求（异步）
refreshData()             // 刷新所有数据
```

## 数据格式

### scenario_index.json 格式
```json
{
  "scenarios": [
    {
      "scenario_id": "scenario_accident_12547",
      "event_type": "accident",
      "control_strategy": "VSS",
      "road": "G5京昆高速（绵广段）",
      "location": "K1576+000",
      "event_start": "2025-07-14 01:53:49",
      "event_end": "2025-07-14 03:22:39",
      "duration_hours": 1.48,
      "case_count": 3,
      "report_id": "12547"
    },
    // 更多场景...
  ]
}
```

### 事件类型编码
```javascript
'accident'     // 交通事故
'congestion'   // 交通阻塞/流量激增
'control'      // 交通管制
'geological'   // 地质灾害
'breakdown'    // 车辆故障
'weather'      // 恶劣天气
```

### 管控策略编码
```javascript
'VSS'          // 动态限速
'DHS'          // 应急车道
'TEC'          // 收费管控
'none'         // 无管控
```

## API 集成

### 1. 创建案例 API

**端点**
```
POST /api/v1/scenario/create-case
```

**请求体**
```javascript
{
  "scenario_id": "scenario_accident_12547",
  "simulation_duration_hours": 2.0,
  "random_seed": null,  // 或整数
  "output_config": {
    "generate_edgedata": true,    // 必需
    "generate_tripinfo": true,
    "generate_vehroute": true
  }
}
```

**成功响应 (200)**
```javascript
{
  "case_id": "case_20251111_001",
  "scenario_id": "scenario_accident_12547",
  "created_at": "2025-11-11T10:30:00Z",
  "status": "created"
}
```

**错误处理**
- 404: 场景不存在
- 400: 参数无效
- 500: 服务器错误

### 2. 仿真分析 API

**端点**
```
POST /api/v1/scenario/run-analysis
```

**请求体**
```javascript
{
  "scenario_id": "scenario_accident_12547",
  "compare_baseline": true,        // 对比基线
  "compare_no_control": true,      // 对比无管控
  "analysis_focus": {
    "edgedata": true,              // 道路段分析
    "tripinfo": true               // 行程分析
  }
}
```

**成功响应 (200)**
```javascript
{
  "analysis_id": "analysis_20251111_001",
  "scenario_id": "scenario_accident_12547",
  "status": "started",
  "estimated_duration": 300        // 秒
}
```

**错误处理**
- 404: 场景不存在
- 400: 参数无效
- 500: 服务器错误

## 修改指南

### 添加新的事件类型

1. **HTML 中的 Chip 选择器**
```html
<div class="dimension-chip" data-value="new_type">新事件类型</div>
```

2. **CSS 中的徽章样式**
```css
.event-badge-new_type {
  background-color: #e0f2f1;
  color: #00695c;
}
```

3. **JavaScript 中的映射**
```javascript
// getEventTypeDisplay()
'new_type': '新事件类型',

// getEventBadgeClass()
'new_type': 'event-badge-new_type',
```

### 添加新的管控策略

1. **HTML 中的 Chip 选择器**
```html
<div class="dimension-chip" data-value="NEW">新策略</div>
```

2. **CSS 中的徽章样式**
```css
.control-badge-new {
  background-color: #e0f2f1;
  color: #00695c;
}
```

3. **JavaScript 中的映射**
```javascript
// getEventTypeDisplay()
'NEW': '新策略',

// getControlBadgeClass()
'NEW': 'control-badge-new',
```

### 修改表格列

1. **添加列**
```html
<!-- HTML 中的表头 -->
<th>新列</th>

<!-- 表体中的单元格 -->
<td>${scenario.new_field}</td>
```

2. **调整列宽**
```html
<th style="width: 100px;">列名</th>
```

### 修改颜色方案

编辑 CSS 变量：
```css
:root {
  --primary-color: #1976d2;      /* 蓝色主题 */
  --secondary-color: #388e3c;    /* 绿色主题 */
  /* ... */
}
```

### 修改筛选逻辑

在 `applyFilters()` 函数中：
```javascript
function applyFilters() {
  filteredScenarios = allScenarios.filter(scenario => {
    // 添加新的筛选条件
    if (/* 条件 */) {
      return false;
    }
    return true;
  });
  renderScenarios();
}
```

## 常见任务

### 如何加载不同的数据源？

修改 `loadScenarios()` 函数：
```javascript
async function loadScenarios() {
  try {
    const response = await fetch('/your/api/endpoint');
    const data = await response.json();
    allScenarios = data.scenarios || [];
  } catch (error) {
    console.error('加载失败:', error);
    allScenarios = generateMockData();
  }
}
```

### 如何添加日期范围筛选？

1. 在 HTML 中添加输入框
2. 在 JavaScript 中添加事件监听
3. 修改 `applyFilters()` 函数添加日期范围检查

### 如何实现表格排序？

1. 给每个列标题添加 click 事件
2. 修改 `renderScenarios()` 前对数据排序
3. 使用 `Array.sort()` 方法

### 如何添加分页？

1. 添加分页控件 HTML
2. 修改 `renderScenarios()` 只显示当前页数据
3. 添加页码切换事件

## 调试技巧

### 检查加载的数据
```javascript
console.log('所有场景:', allScenarios);
console.log('过滤后的场景:', filteredScenarios);
console.log('当前筛选器:', currentFilters);
```

### 检查 API 调用
```javascript
// 在浏览器 DevTools 中
// 1. 打开 Network 标签
// 2. 执行操作
// 3. 查看请求和响应
```

### 检查样式问题
```javascript
// 在浏览器 DevTools 中
// 1. 打开 Elements 标签
// 2. 右键 -> Inspect
// 3. 查看应用的样式
```

### 常见问题排查

**问**：表格不显示任何数据
**答**：检查 JSON 文件路径和格式是否正确

**问**：筛选不工作
**答**：检查事件类型和管控策略编码是否与 JSON 数据匹配

**问**：模态框不显示
**答**：确保 Bootstrap JS 已正确加载

**问**：样式不生效
**答**：清除浏览器缓存，检查 CSS 选择器

## 性能优化建议

### 当场景数量很大（> 1000）时

1. **实现分页**
   - 每页显示 20-50 个场景
   - 减少 DOM 节点

2. **实现虚拟滚动**
   - 只渲染可见区域的行
   - 大幅提升滚动性能

3. **优化搜索**
   - 添加防抖（debounce）
   - 避免频繁重新渲染

4. **优化筛选**
   - 使用 Set 进行快速查找
   - 缓存常用的筛选结果

### 代码示例：添加防抖

```javascript
function debounce(func, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

const searchBox = document.getElementById('searchBox');
searchBox.addEventListener('input', debounce(() => {
  currentFilters.searchText = searchBox.value.toLowerCase();
  applyFilters();
}, 300));
```

## 测试清单

- [ ] 页面加载成功
- [ ] 数据加载成功（从 JSON 或模拟数据）
- [ ] 统计卡片正确显示
- [ ] 事件类型筛选正常工作
- [ ] 管控策略筛选正常工作
- [ ] 只显示有案例的场景选项正常工作
- [ ] 搜索功能正常工作
- [ ] 所有筛选条件联动正常工作
- [ ] 快速创建模态框能打开/关闭
- [ ] 仿真分析模态框能打开/关闭
- [ ] 创建案例 API 调用成功
- [ ] 分析 API 调用成功
- [ ] 表格悬停反馈正常
- [ ] 响应式设计在不同屏幕上正常工作
- [ ] 没有浏览器控制台错误

## 支持联系

如有问题，请查看：
- 设计文档：`frontend/scenarios/DESIGN_NOTES.md`
- 功能对比：`frontend/scenarios/FEATURES_COMPARISON.md`
- 完成总结：`REDESIGN_SUMMARY.md`

---

**最后更新**: 2025-11-11
**版本**: 1.0
**维护者**: AI Assistant
