# 影响分析UI集成 - 详细设计文档

## 概述

本文档详细描述影响分析页面的技术设计、组件结构、数据流程和实现细节。

## 1. 系统架构

### 1.1 高层组件拓扑

```
┌─────────────────────────────────────────────────────────────────┐
│                    Impact Analysis Page (impact_analysis.html)   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Header Section                                          │   │
│  │  - Case ID + 返回按键                                    │   │
│  │  - 数据状态指示（Loading / Ready / Error）              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Strategy Overview Section (4 Cards)                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │   DHS    │ │   TEC    │ │   VSS    │ │ NO_CTRL  │   │   │
│  │  │ +0.67%   │ │ +0.20%   │ │ +0.25%   │ │ Baseline │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Comparison Table Section                              │   │
│  │  ┌───────────────┬──────┬──────┬──────┬──────┐         │   │
│  │  │ Metric        │ DHS  │ TEC  │ VSS  │ NC   │         │   │
│  │  ├───────────────┼──────┼──────┼──────┼──────┤         │   │
│  │  │ avg_speed     │ 75.7 │ 74.8 │ 75.9 │ 75.3 │         │   │
│  │  │ ...           │ ...  │ ...  │ ...  │ ...  │         │   │
│  │  └───────────────┴──────┴──────┴──────┴──────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Timeseries Charts Section (2x3 Grid)                  │   │
│  │  ┌──────────────────┐  ┌──────────────────┐            │   │
│  │  │  current_vehicles│  │ avg_speed        │            │   │
│  │  │  [Line Chart]    │  │ [Line Chart]     │            │   │
│  │  └──────────────────┘  └──────────────────┘            │   │
│  │  ┌──────────────────┐  ┌──────────────────┐            │   │
│  │  │loaded_vehicles   │  │collisions        │            │   │
│  │  │  [Line Chart]    │  │ [Line Chart]     │            │   │
│  │  └──────────────────┘  └──────────────────┘            │   │
│  │  ┌──────────────────┐  ┌──────────────────┐            │   │
│  │  │meanWaitingTime   │  │completed_vehicles│            │   │
│  │  │  [Line Chart]    │  │ [Line Chart]     │            │   │
│  │  └──────────────────┘  └──────────────────┘            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Improvement Analysis Section                          │   │
│  │  - Strategy Rankings (Best / Worst)                    │   │
│  │  - Improvement Bar Chart (vs NO_CONTROL)              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Footer / Export Section                               │   │
│  │  - Export to CSV / PDF / PNG buttons                   │   │
│  │  - Print button                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流程图

```
用户点击案例的"分析"按键
           │
           ↓
impact_analysis.html 加载
           │
           ├─→ 解析 URL 参数 (case_id)
           │
           ├─→ 显示 Loading 状态
           │
           ├─→ API 并行调用
           │   ├─→ GET /strategy-comparison/{case_id}
           │   └─→ GET /strategy-timeseries/{case_id}
           │
           ├─→ 数据转换与验证
           │   ├─→ aggregated_metrics = {strategy: {metric: value}}
           │   ├─→ timeseries_data = {strategy: {metric: [points]}}
           │   └─→ improvements = {strategy: {metric: percentage}}
           │
           ├─→ 隐藏 Loading，显示内容
           │
           └─→ 渲染各个 Section
               ├─→ Strategy Overview Cards
               ├─→ Comparison Table
               ├─→ Timeseries Charts (5个)
               └─→ Improvement Analysis
```

## 2. 功能模块设计

### 2.1 数据加载模块 (`loadAnalysisData()`)

**职责**: 从后端API加载数据，转换格式，处理错误

**输入**:
- case_id: string (来自 URL 参数)

**输出**:
```javascript
{
  success: boolean,
  aggregated_metrics: {
    'DHS': { avg_speed: 75.74, completed_vehicles: 66971, ... },
    'TEC': { ... },
    'VSS': { ... },
    'NO_CONTROL': { ... }
  },
  timeseries_data: {
    'DHS': {
      'current_vehicles': [
        { time: 0, value: 215 },
        { time: 1, value: 220 },
        ...
      ],
      ...
    },
    ...
  },
  error?: string
}
```

**实现关键点**:
1. 解析 case_id 参数，验证非空
2. 并行加载两个API：`Promise.all()`
3. 转换API响应格式（若需要）
4. 验证数据完整性和有效性
5. 错误捕获和用户提示

### 2.2 总览卡片渲染 (`renderStrategyOverview()`)

**职责**: 渲染4个策略对比卡片

**数据结构**:
```javascript
strategy_overview = {
  'DHS': {
    improvement_percent: 0.67,  // (66971-66928)/66928*100
    key_metrics: {
      completed_vehicles: 66971,
      avg_speed: 75.74,
      improvement_direction: '+' // '+' 或 '-'
    },
    color: '#f9a825'  // 橙色
  },
  'TEC': { ... },
  'VSS': { ... },
  'NO_CONTROL': {
    improvement_percent: 0,  // Baseline，不计算
    is_baseline: true,
    key_metrics: { ... },
    color: '#ff6b6b'
  }
}
```

**HTML 结构**:
```html
<div class="strategy-overview">
  <div class="strategy-card" data-strategy="DHS">
    <div class="strategy-header">
      <h3>DHS (动态硬路肩)</h3>
      <span class="improvement-badge positive">+0.67%</span>
    </div>
    <div class="strategy-metrics">
      <div class="metric">
        <span>已完成车数</span>
        <strong>66971</strong>
      </div>
      <div class="metric">
        <span>平均速度</span>
        <strong>75.74 km/h</strong>
      </div>
    </div>
  </div>
  <!-- 重复4个卡片 -->
</div>
```

**样式特点**:
- 卡片宽度响应式（4列 → 2列 → 1列）
- 改进方向用颜色和箭头表示
- 鼠标悬停显示更多信息

### 2.3 对比表格渲染 (`renderComparisonTable()`)

**职责**: 展示8个指标×5个策略的完整数据矩阵

**表结构**:
```
┌─────────────────┬─────────┬─────────┬─────────┬─────────┐
│ Metric          │ DHS     │ TEC     │ VSS     │ NO_CTRL │
├─────────────────┼─────────┼─────────┼─────────┼─────────┤
│ current_vehicles│ 0.00    │ 0.00    │ 0.00    │ 0.00    │
│ avg_speed       │ 75.74   │ 74.84   │ 75.92   │ 75.28   │
│ loaded_vehicles │ 126455  │ 126455  │ 126455  │ 126455  │
│ ...             │ ...     │ ...     │ ...     │ ...     │
└─────────────────┴─────────┴─────────┴─────────┴─────────┘
```

**HTML 结构** (简化):
```html
<table class="comparison-table">
  <thead>
    <tr>
      <th>指标</th>
      <th>DHS</th>
      <th>TEC</th>
      <th>VSS</th>
      <th>NO_CONTROL</th>
    </tr>
  </thead>
  <tbody>
    <!-- 8行数据 -->
  </tbody>
</table>
```

**交互功能**:
- 鼠标悬停行高亮
- 点击单元格显示趋势图
- 排序功能（可选）

### 2.4 时序图表渲染 (`renderTimeseriesCharts()`)

**职责**: 使用Chart.js渲染6个时序图表

**图表列表** (Phase 2调整):
1. current_vehicles (当前运行车数)
2. avg_speed (平均速度)
3. loaded_vehicles (已载入车数)
4. collisions (碰撞次数 - 安全指标)
5. meanWaitingTime (平均等待时间 - 拥堵指标)
6. completed_vehicles (已完成车数)

**Chart.js 配置** (示例):
```javascript
{
  type: 'line',
  data: {
    labels: [0, 1, 2, ..., 5399],  // 时间轴
    datasets: [
      {
        label: 'DHS',
        data: [215, 218, 222, ...],
        borderColor: '#f9a825',
        backgroundColor: 'rgba(249, 168, 37, 0.1)',
        borderWidth: 2,
        pointRadius: 0,  // 不显示点，否则5400个点太密集
        pointHoverRadius: 6,
        tension: 0.4
      },
      {
        label: 'TEC',
        data: [...],
        borderColor: '#4ecdc4',
        ...
      },
      ...
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { display: true, position: 'top' },
      title: { display: true, text: '当前运行车数' }
    },
    scales: {
      x: {
        title: { display: true, text: '仿真时间 (秒)' }
      },
      y: {
        title: { display: true, text: '车数 (辆)' }
      }
    }
  }
}
```

**性能优化**:
- 不显示数据点（pointRadius=0），仅悬停时显示
- 使用缩采样（decimation）若需要
- 禁用动画加快渲染

### 2.5 改进分析模块 (`renderImprovementAnalysis()`)

**职责**: 计算与NO_CONTROL的对比改进

**算法**:
```javascript
improvements = {}
for (strategy of ['DHS', 'TEC', 'VSS']) {
  improvements[strategy] = {}
  for (metric of TRAFFIC_METRICS) {
    let baseline = aggregated_metrics['NO_CONTROL'][metric]
    let current = aggregated_metrics[strategy][metric]

    // 判断是"越大越好"还是"越小越好"
    let is_higher_better = TRAFFIC_METRICS[metric].higher_is_better

    if (is_higher_better) {
      improvements[strategy][metric] = (current - baseline) / baseline * 100
    } else {
      improvements[strategy][metric] = (baseline - current) / baseline * 100
    }
  }
}
```

**展示形式**:
- 改进排行（Bar Chart）：显示每个策略的总体改进分数
- Best/Worst 指标：列出最优和最差的指标

## 3. 前端代码结构

### 3.1 HTML 文件结构

```
impact_analysis.html (800 行)
├── <head>
│   ├── Meta tags
│   ├── CSS 引入 (impact_analysis.css + Chart.js)
│   └── Chart.js CDN
│
└── <body>
    ├── <header> - 页面头部
    │   ├── 返回按键
    │   ├── Case ID 显示
    │   └── 状态指示
    │
    ├── <main id="content">
    │   ├── <section class="strategy-overview">
    │   │   └── 4个 .strategy-card
    │   │
    │   ├── <section class="comparison-table-section">
    │   │   └── <table class="comparison-table">
    │   │
    │   ├── <section class="timeseries-charts">
    │   │   ├── <div class="chart-container">
    │   │   │   └── <canvas id="chart-current-vehicles">
    │   │   ├── <div class="chart-container">
    │   │   │   └── <canvas id="chart-avg-speed">
    │   │   ├── <div class="chart-container">
    │   │   │   └── <canvas id="chart-loaded-vehicles">
    │   │   ├── <div class="chart-container">
    │   │   │   └── <canvas id="chart-collisions">
    │   │   ├── <div class="chart-container">
    │   │   │   └── <canvas id="chart-meanWaitingTime">
    │   │   ├── <div class="chart-container">
    │   │   │   └── <canvas id="chart-completed-vehicles">
    │   │
    │   └── <section class="improvement-analysis">
    │       ├── <div class="improvement-rankings">
    │       └── <div class="improvement-chart">
    │
    ├── <div id="loading"> - 加载指示
    ├── <div id="error"> - 错误提示
    │
    └── <script>
        ├── 全局配置和常量
        ├── loadAnalysisData()
        ├── renderStrategyOverview()
        ├── renderComparisonTable()
        ├── renderTimeseriesCharts()
        ├── renderImprovementAnalysis()
        ├── 初始化代码
        └── 事件监听
```

### 3.2 JavaScript 模块设计

**模块划分** (遵循单一职责原则):

1. **数据加载模块**
   ```javascript
   async function loadAnalysisData(caseId) {
     // 并行加载两个API
     // 数据转换和验证
     // 返回结构化数据
   }
   ```

2. **渲染模块** (各自独立，不超过150行)
   ```javascript
   function renderStrategyOverview(data) { ... }
   function renderComparisonTable(data) { ... }
   function renderTimeseriesCharts(data) { ... }
   function renderImprovementAnalysis(data) { ... }
   ```

3. **工具函数**
   ```javascript
   function calculateImprovement(baseline, current, isHigherBetter) { ... }
   function formatMetricValue(metric, value) { ... }
   function getStrategyColor(strategy) { ... }
   ```

4. **事件处理**
   ```javascript
   window.addEventListener('DOMContentLoaded', initializePage);
   document.addEventListener('click', handleTableRowClick);
   ```

### 3.3 CSS 文件结构 (impact_analysis.css)

```css
/* 1. 重置和全局样式 (30行) */
* { ... }
body { ... }
html { ... }

/* 2. 布局基础 (50行) */
.container { ... }
.section { ... }
.grid { ... }

/* 3. Header 样式 (40行) */
header { ... }
.case-id-display { ... }
.status-indicator { ... }

/* 4. Strategy Overview 卡片 (70行) */
.strategy-overview { ... }
.strategy-card { ... }
.strategy-header { ... }
.improvement-badge { ... }

/* 5. 对比表格 (60行) */
.comparison-table-section { ... }
.comparison-table { ... }
.comparison-table th { ... }
.comparison-table td { ... }

/* 6. 时序图表 (50行) */
.timeseries-charts { ... }
.chart-container { ... }
canvas { ... }

/* 7. 改进分析 (50行) */
.improvement-analysis { ... }
.improvement-rankings { ... }
.improvement-chart { ... }

/* 8. Loading 和 Error 状态 (40行) */
#loading { ... }
#error { ... }

/* 9. 响应式设计 (80行) */
@media (max-width: 1200px) { ... }
@media (max-width: 768px) { ... }

/* 10. 主题变量和工具类 (30行) */
:root { --color-primary: ...; }
.hidden { ... }
.highlight { ... }
```

## 4. 数据验证与错误处理

### 4.1 输入验证

```javascript
// URL参数验证
const caseId = new URLSearchParams(window.location.search).get('case_id');
if (!caseId || caseId.trim() === '') {
  showError('缺少 case_id 参数');
  return;
}

// API响应验证
function validateComparisonData(data) {
  const required_strategies = ['DHS', 'NO_CONTROL', 'TEC', 'VSS'];
  const required_metrics = [
    'current_vehicles', 'avg_speed', 'loaded_vehicles',
    'chain_frequency', 'transmission_frequency', 'completed_vehicles',
    'terminated_vehicles', 'waiting_vehicles'
  ];

  for (let strategy of required_strategies) {
    if (!data[strategy]) {
      throw new Error(`缺少策略数据: ${strategy}`);
    }
    for (let metric of required_metrics) {
      if (!(metric in data[strategy])) {
        throw new Error(`缺少指标: ${strategy}/${metric}`);
      }
    }
  }

  return true;
}
```

### 4.2 错误处理策略

| 错误场景 | 处理方式 |
|---------|---------|
| URL缺少case_id | 显示错误提示 + 返回按键 |
| API超时 | 显示重试按键 |
| API返回错误 | 显示错误信息 + 返回按键 |
| 数据验证失败 | 显示警告 + 回退显示 |
| Chart.js加载失败 | 显示表格替代视图 |

## 5. 性能优化

### 5.1 数据加载优化

- **并行加载**: 使用 `Promise.all()` 同时请求两个API
- **数据缓存**: 加载完成后缓存到 `sessionStorage`，刷新时复用
- **流式渲染**: 先显示骨架屏，再逐个渲染Section

### 5.2 DOM 操作优化

- **批量更新**: 使用 `DocumentFragment` 构建DOM树，一次性插入
- **事件委托**: 使用事件委托而非为每个元素单独绑定
- **避免重排**: 修改样式前批量计算

### 5.3 图表性能

- **禁用点**: `pointRadius: 0` 和 `pointHoverRadius: 6`
- **禁用动画**: `animation: false`
- **缩采样**: 若需要（当前5400个数据点可接受）

## 6. 测试策略

### 6.1 单元测试

| 模块 | 测试项 |
|------|--------|
| loadAnalysisData() | 正常加载 / API超时 / 无效case_id / 数据验证失败 |
| calculateImprovement() | 正向指标 / 反向指标 / 边界值 |
| formatMetricValue() | 各类指标格式化 / 小数点 |

### 6.2 集成测试

- 导航流程: 案例列表 → impact_analysis.html
- 数据完整性: 加载数据后所有Section都正确渲染（6个时序图表）
- 交互测试: 鼠标悬停、点击等交互正常
- 图表验证: 确保6个图表都正确绘制，数据线正确显示4个策略

### 6.3 浏览器兼容性

- Chrome ≥90
- Edge ≥90
- Firefox ≥88

## 7. 导航集成设计

### 7.1 案例列表修改 (case-simulation-center.html)

**添加分析操作按键** (每个案例行):

```html
<tr data-case-id="case_event_6120705">
  <td>case_event_6120705</td>
  <td>事件案例1</td>
  <td>
    <button class="action-btn" onclick="viewAnalysis('case_event_6120705')">
      分析
    </button>
  </td>
</tr>
```

**JavaScript 导航函数**:

```javascript
function viewAnalysis(caseId) {
  window.location.href = `/scenarios/impact_analysis.html?case_id=${caseId}`;
}
```

### 7.2 面包屑导航

在impact_analysis.html的header显示：

```
[案例列表] > [case_event_6120705] > [分析]
```

点击"案例列表"返回case-simulation-center.html

## 8. 实现清单

### Phase 1: 基础框架 (4小时)
- [ ] 创建 impact_analysis.html 框架
- [ ] 实现数据加载模块
- [ ] 实现总览卡片渲染
- [ ] 基础CSS样式

### Phase 2: 数据展示 (3小时)
- [ ] 实现对比表格
- [ ] 实现时序图表 (Chart.js集成)
- [ ] 实现改进分析
- [ ] 样式优化

### Phase 3: 交互和优化 (2小时)
- [ ] 添加Loading和Error状态
- [ ] 响应式设计测试
- [ ] 浏览器兼容性测试
- [ ] 性能优化

### Phase 4: 集成和测试 (1小时)
- [ ] 导航集成 (case-simulation-center.html)
- [ ] 端到端流程测试
- [ ] 代码审查和文档

## 9. 参考资源

- Chart.js 文档: https://www.chartjs.org/
- CSS Grid 布局: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout
- 前端代码标准: ../../project.md#frontend-development-standards
