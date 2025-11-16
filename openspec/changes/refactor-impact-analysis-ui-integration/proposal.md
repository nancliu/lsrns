# 影响分析页面集成与功能拓展提案

## 概述

集成已验证的策略对比后端功能到前端影响分析页面，并重新设计分析UI以支持多维度的策略对比分析。用户可从案例列表的"分析"按键进入，在功能完整的影响分析页面中查看与对比各类分析结果。

**核心目标**：
1. **数据流集成** - 从案例列表 → 影响分析页面的无缝导航
2. **策略对比分析** - 展示 4 个控制策略（DHS/NO_CONTROL/TEC/VSS）的 8 个交通性能指标对比
3. **多维度可视化** - 聚合指标、时序图表、对比表格、改进指标
4. **现代化UI** - 响应式布局、模块化组件、丰富的交互

**Status**: 提案中（待审批）
**Scope**: 前端功能增强 + 后端API集成

## 问题陈述

### 当前现状
- ✅ 策略对比后端服务已实现（StrategyComparisonService）
- ✅ 3个API端点已验证：
  - `POST /api/v1/analysis/strategy-comparison/generate/{case_id}`
  - `GET /api/v1/analysis/strategy-comparison/{case_id}`
  - `GET /api/v1/analysis/strategy-timeseries/{case_id}`
- ❌ 前端仍缺乏完整的分析页面
- ❌ 无法在案例列表中快速进入分析
- ❌ 分析页面功能有限（仅有基础UI框架）

### 核心需求
1. **导航集成** - 案例列表添加"分析"操作按键，点击进入case_id对应的影响分析页面
2. **完整分析页面** - 重新设计analysis_viewer.html，包含：
   - **策略对比总览** - 4个策略的关键指标卡片
   - **详细对比表格** - 8个指标的完整数据矩阵
   - **时序数据可视化** - 多条线图展示关键指标随时间变化
   - **改进指标分析** - 对标baseline（NO_CONTROL）的改进百分比
3. **数据加载** - 自动从后端加载case_id对应的所有分析数据
4. **交互功能** - 指标筛选、策略对比、导出等高级功能

## 解决方案

### 整体架构

```
案例列表页面 (case-simulation-center.html)
    ↓ [点击"分析"按键]
    ↓
影响分析页面 (impact_analysis.html) - NEW
    ├── 【数据加载层】
    │   ├── 获取case_id参数
    │   ├── 调用 /strategy-comparison/{case_id}
    │   └── 调用 /strategy-timeseries/{case_id}
    │
    ├── 【分析展示层】
    │   ├── 策略对比总览（4个卡片）
    │   ├── 详细对比表格（8个指标）
    │   ├── 时序图表区域（5个图表）
    │   ├── 改进指标分析（与NO_CONTROL对比）
    │   └── 数据导出功能
    │
    └── 【样式层】
        ├── 响应式网格布局
        ├── 深色/浅色主题支持
        └── 打印友好的CSS
```

### 功能模块设计

#### 1. 数据加载模块
- 从URL参数获取case_id
- 并行加载策略对比和时序数据
- 错误处理和Loading状态管理
- 数据验证和格式转换

#### 2. 策略对比总览
- 4个大卡片，分别展示：
  - DHS、TEC、VSS 与 NO_CONTROL的性能对比
  - 关键指标：completed_vehicles, avg_speed, waiting_vehicles
  - 改进百分比显示（↑/↓）

#### 3. 详细对比表格
- 8列：指标名、NO_CONTROL、DHS、TEC、VSS
- 8行：8个交通性能指标
- 排序、筛选、高亮功能
- 支持按单元格展开查看详细说明

#### 4. 时序数据可视化
- 使用Chart.js或类似库
- 5个独立图表：
  - 当前运行车数 (current_vehicles)
  - 平均速度 (avg_speed)
  - 已完成车数 (completed_vehicles)
  - 等待车数 (waiting_vehicles)
  - 已载入车数 (loaded_vehicles)
- 图例显示4个策略（不同颜色）
- 支持悬停查看数值

#### 5. 改进指标分析
- 对标baseline（NO_CONTROL）的改进百分比
- 展示改进指标排行（best/worst）
- 可视化柱状图表

### 实现范围

| 模块 | 文件 | 工作量 | 依赖 |
|------|------|--------|------|
| 数据加载 | impact_analysis.html | 100行 | 后端API |
| 总览展示 | impact_analysis.html | 200行 | 数据加载 |
| 对比表格 | impact_analysis.html | 150行 | 数据加载 |
| 时序图表 | impact_analysis.html + chart.js | 300行 | 数据加载 |
| 改进分析 | impact_analysis.html | 100行 | 数据加载 |
| 导航集成 | case-simulation-center.html | 30行 | impact_analysis.html |
| CSS样式 | css/impact_analysis.css | 200行 | HTML结构 |

### 页面流程

```
用户操作流程：
1. [案例列表] 用户点击某个案例的"分析"按键
2. [导航] 跳转到 impact_analysis.html?case_id=case_event_6120705
3. [加载] 页面显示Loading，并行加载两个API
4. [展示] 依次展示：
   - 策略对比总览（4个卡片）
   - 详细对比表格（8个指标×5个策略）
   - 时序数据图表（5个图表）
   - 改进指标分析（改进排行）
5. [交互] 用户可点击卡片、表格、图表进行深度分析
6. [导出] 用户可点击导出按键下载数据或打印报告
```

### 数据结构映射

**后端响应** → **前端展示**：

```javascript
// 策略对比数据 (GET /strategy-comparison/{case_id})
{
  "DHS": {
    "current_vehicles": 0.0,
    "avg_speed": 75.74,
    "completed_vehicles": 66971,
    ...
  },
  "NO_CONTROL": { ... },
  "TEC": { ... },
  "VSS": { ... }
}
↓ 映射 ↓
总览卡片: {
  "DHS": {
    "improvement": "+0.67%",  // (66971-66928)/66928*100
    "key_metrics": [completed_vehicles, avg_speed]
  },
  ...
}

// 时序数据 (GET /strategy-timeseries/{case_id})
{
  "DHS": {
    "current_vehicles": [
      {"time": 0, "value": 215},
      {"time": 1, "value": 218},
      ...
    ],
    ...
  },
  ...
}
↓ 映射 ↓
Chart.js数据集: {
  labels: [0, 1, 2, ..., 5399],  // 时间（秒）
  datasets: [
    {
      label: "DHS",
      data: [215, 218, ...],
      borderColor: "#f9a825",
      ...
    },
    {
      label: "NO_CONTROL",
      data: [215, 220, ...],
      borderColor: "#ff6b6b",
      ...
    },
    ...
  ]
}
```

### 响应式设计

**桌面端** (≥1200px)：
- 4列网格：4个策略卡片
- 2列网格：2个时序图表
- 全宽表格

**平板端** (768px-1199px)：
- 2列网格：2个策略卡片
- 1列网格：1个时序图表
- 可水平滚动的表格

**移动端** (<768px)：
- 1列网格：1个策略卡片（堆叠显示）
- 1列网格：1个时序图表（垂直堆叠）
- 可水平滚动的表格

## 技术栈

- **前端框架**: 原生HTML/CSS/JavaScript（无框架依赖）
- **图表库**: Chart.js 3.9.1（轻量级、高性能）
- **样式**:
  - 分离CSS文件（css/impact_analysis.css）
  - 遵循RULE-FE-001（无硬编码数据）
  - 响应式网格布局（CSS Grid + Flexbox）
- **浏览器兼容性**: Chrome/Edge/Firefox（现代浏览器）

## 依赖与集成

### 后端依赖
- ✅ `api.services.strategy_comparison_service.py` (已实现)
- ✅ `api.routes.analysis_routes.py` (已实现)
- ✅ 3个API端点（已验证）

### 前端依赖
- 📁 `frontend/scenarios/` (新增impact_analysis.html)
- 📁 `frontend/scenarios/css/` (新增impact_analysis.css)
- 📦 Chart.js (CDN引入)
- 🔗 `case-simulation-center.html` (添加导航链接)

### 文件清单

| 文件 | 类型 | 操作 | 行数 |
|------|------|------|------|
| frontend/scenarios/impact_analysis.html | 新建 | CREATE | ~800 |
| frontend/scenarios/css/impact_analysis.css | 新建 | CREATE | ~250 |
| frontend/scenarios/case-simulation-center.html | 修改 | MODIFY | +30 |
| openspec/changes/refactor-impact-analysis-ui-integration/ | 文档 | CREATE | - |

## 验收标准

### 功能验收
- ✓ 从案例列表能够正确导航到impact_analysis.html，传递case_id参数
- ✓ 页面自动加载指定case_id的所有分析数据
- ✓ 策略对比总览正确展示4个卡片，改进指标计算正确
- ✓ 对比表格展示8个指标×5个策略，数据来自后端API
- ✓ 时序图表正确绘制5条线（4个策略），显示5400个数据点
- ✓ 改进分析显示与NO_CONTROL的对比百分比

### 性能验收
- ✓ 页面加载时间 <3秒（含API调用）
- ✓ 时序图表交互流畅（12MB JSON加载后）
- ✓ 响应式设计在桌面/平板/移动端正常显示

### 代码质量
- ✓ 遵循RULE-FE-001（无硬编码数据）
- ✓ 遵循前端代码标准（函数<30行，单一职责）
- ✓ 分离HTML/CSS/JavaScript，无内联样式
- ✓ 完整的错误处理和Loading状态
- ✓ 浏览器控制台无错误或警告

## 里程碑与时间表

| 阶段 | 任务 | 预期时间 |
|------|------|----------|
| 1 | 架构设计 & 原型 | 1-2小时 |
| 2 | 数据加载模块 + 总览展示 | 2-3小时 |
| 3 | 对比表格 + 改进分析 | 1-2小时 |
| 4 | 时序图表集成 | 2-3小时 |
| 5 | 样式优化 & 响应式设计 | 1-2小时 |
| 6 | 导航集成 & 测试 | 1小时 |
| 7 | 文档 & 代码审查 | 1小时 |

**总计**: ~10小时

## 风险与缓解

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| Chart.js 加载失败 | 时序图表无法显示 | 使用CDN备份 + 降级处理 |
| 12MB JSON文件解析慢 | 首次加载卡顿 | 增加Loading动画 + 数据流式加载 |
| API响应超时 | 数据加载失败 | 添加超时处理 + 重试机制 |
| 浏览器兼容性 | 功能在旧浏览器失效 | 针对Chrome/Edge/Firefox测试 |

## Phase 2 更新（已实现）

**时序数据指标调整**（基于Phase 1反馈和8个聚合指标优化）：

从原有的5个指标：
- current_vehicles, avg_speed, completed_vehicles, waiting_vehicles, loaded_vehicles

调整为6个指标，移除 `waiting_vehicles`，新增 `collisions` 和 `meanWaitingTime`：
1. `current_vehicles` - 当前运行车数（实时路网饱和度）
2. `avg_speed` - 平均速度（交通流质量）
3. `loaded_vehicles` - 已载入车数（需求侧指标）
4. `collisions` - 碰撞次数（交通安全指标，累计）
5. `meanWaitingTime` - 平均等待时间（拥堵程度实时动态）
6. `completed_vehicles` - 已完成车数（仿真进展）

**调整原因**：
- `meanWaitingTime` 比 `waiting_vehicles` 更具代表性（质量vs数量）
- `collisions` 直接对应8个聚合指标中的安全指标
- 完整覆盖8个聚合指标的核心维度

**UI布局**：2x3网格（6个图表）

---

## 后续改进（Phase 3+）

1. **高级功能**
   - 多案例对比分析
   - 数据导出（Excel/PDF）
   - 自定义报告生成

2. **优化**
   - WebSocket实时数据推送
   - 本地缓存策略
   - 性能指标收集

3. **集成**
   - 与accuracy_analysis、mechanism_analysis集成
   - 统一分析仪表板

## 相关文档与提案

- 📄 [策略对比后端实现](../refactor-event-case-management-ui/DOCUMENTATION_SUMMARY.md)
- 📄 [前端开发标准](../../project.md#frontend-development-standards)
- 📄 [API端点指南](../refactor-event-case-management-ui/API_ENDPOINTS_GUIDE.md)
