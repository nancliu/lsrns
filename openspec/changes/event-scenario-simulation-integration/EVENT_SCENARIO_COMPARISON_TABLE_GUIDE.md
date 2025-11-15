# 事件场景对比表格组件 - 集成指南

**创建日期:** 2025-11-15
**组件版本:** 1.0
**参考来源:** 优化仿真批量结果对比表格 (control/optimization.html)

---

## 概述

事件场景对比表格组件用于在影响分析页面中展示多个控制策略的效果对比。该组件完全参考了**优化仿真中批量仿真结果页面的对比表格**设计，保持了一致的用户体验。

### 核心功能

1. **多策略对比表格**
   - 以 NO_CONTROL（无控制）为基准
   - 对比 VSS、TEC、DHS 等控制策略
   - 显示关键指标：速度、行程时间、完成率、延误等
   - 计算并展示相对基准的改善百分比

2. **策略效果排名**
   - 按综合改善率排序
   - 显示排名奖牌（🥇🥈🥉）
   - 提供效果评价（优秀/良好/一般/较差）

3. **视觉设计**
   - 颜色编码：绿色=改善，红色=恶化
   - 箭头指示：↑=提升，↓=降低
   - 响应式布局，支持移动端

---

## 文件组成

### 1. JavaScript 组件

**文件:** `frontend/scenarios/js/event-scenario-comparison.js`

**主要函数:**

```javascript
// 渲染对比表格
renderEventScenarioComparisonTable(batchResults, containerId)

// 渲染策略排名
renderStrategyRanking(batchResults, containerId)

// 加载批次结果（包含以上两个渲染）
loadEventBatchResults(batchId)

// 工具函数
calculateImprovement(value, baseline, higherIsBetter)  // 计算改善百分比
formatDelay(seconds)  // 格式化延误时间
```

### 2. CSS 样式

**文件:** `frontend/scenarios/css/event-scenario-comparison.css`

**核心样式类:**

- `.comparison-table` - 对比表格
- `.ranking-table` - 排名表格
- `.improvement` - 改善指示（绿色）
- `.deterioration` - 恶化指示（红色）
- `.baseline-badge` - 基准标记
- `.evaluation-badge` - 评价徽章

### 3. 使用示例

**文件:** `frontend/scenarios/event-batch-results-example.html`

---

## 数据结构

### 输入数据格式

```json
{
  "event_id": "8210655",
  "batch_id": "batch_event_8210655_20251115_100000",

  "strategy_comparison": {
    "NO_CONTROL": {
      "avg_speed": 45.2,
      "avg_trip_duration": 1200,
      "completion_rate": 96.5,
      "total_vehicles": 8934,
      "total_delay": 45000,
      "avg_waiting_time": 120
    },
    "VSS": {
      "avg_speed": 52.8,
      "avg_trip_duration": 1050,
      "completion_rate": 98.2,
      "total_vehicles": 8934,
      "total_delay": 38000,
      "avg_waiting_time": 95,
      "improvement_vs_baseline": {
        "avg_speed": 16.8,
        "avg_trip_duration": -12.5,
        "completion_rate": 1.76
      }
    }
  },

  "strategy_ranking": [
    {
      "strategy": "VSS",
      "overall_improvement": 15.5,
      "rank": 1
    },
    {
      "strategy": "TEC",
      "overall_improvement": 10.2,
      "rank": 2
    }
  ]
}
```

### 指标说明

| 指标 | 说明 | 单位 | 越高越好 |
|------|------|------|----------|
| `avg_speed` | 平均速度 | km/h | ✅ |
| `avg_trip_duration` | 平均行程时间 | 秒 | ❌ |
| `completion_rate` | 完成率 | % | ✅ |
| `total_vehicles` | 总车辆数 | 辆 | - |
| `total_delay` | 总延误 | 秒 | ❌ |
| `avg_waiting_time` | 平均等待时间 | 秒 | ❌ |

---

## 集成步骤

### 方案 A: 集成到现有 analysis_viewer.html

**步骤 1: 引入 CSS 和 JS**

```html
<!-- 在 <head> 中添加 -->
<link rel="stylesheet" href="css/event-scenario-comparison.css">

<!-- 在 </body> 前添加 -->
<script src="js/event-scenario-comparison.js"></script>
```

**步骤 2: 添加容器元素**

```html
<!-- 替换现有的对比分析标签页内容 -->
<div class="analysis-content" id="tab-comparison">
    <h3>📈 控制策略对比分析</h3>

    <!-- 对比表格容器 -->
    <div id="comparisonTableContainer">
        <div class="empty-state">加载中...</div>
    </div>

    <!-- 策略排名容器 -->
    <div style="margin-top: 30px;">
        <h3>🏆 策略效果排名</h3>
        <div id="strategyRankingContainer">
            <div class="empty-state">加载中...</div>
        </div>
    </div>
</div>
```

**步骤 3: 调用渲染函数**

```html
<script type="module">
    import { APIClient } from '../components/api-client.js';

    const api = new APIClient();
    let batchId = new URLSearchParams(window.location.search).get('batch_id');

    // 加载分析结果
    async function loadAnalysisResults() {
        try {
            // 假设批次结果 API 返回包含 strategy_comparison 和 strategy_ranking
            const response = await api.request(`/analysis/results/${batchId}`);
            const batchResults = response.data || response;

            // 渲染对比表格
            renderEventScenarioComparisonTable(batchResults, 'comparisonTableContainer');

            // 渲染策略排名
            renderStrategyRanking(batchResults, 'strategyRankingContainer');

        } catch (error) {
            console.error('加载分析结果失败:', error);
        }
    }

    // 页面加载时自动执行
    loadAnalysisResults();
</script>
```

### 方案 B: 集成到 event-batch-center.html 的结果视图

**步骤 1: 在 View 3 (结果视图) 中添加容器**

```html
<!-- View 3: 批次结果 -->
<div id="resultsView" class="view-content">
    <div class="section">
        <h3>控制策略对比表</h3>
        <div id="comparisonTableContainer">
            <div class="empty-state">加载中...</div>
        </div>
    </div>

    <div class="section">
        <h3>策略效果排名</h3>
        <div id="strategyRankingContainer">
            <div class="empty-state">加载中...</div>
        </div>
    </div>

    <div class="btn-group">
        <button class="btn btn-secondary" onclick="backToMonitoring()">返回监控</button>
        <button class="btn btn-primary" onclick="exportReport()">导出报告</button>
    </div>
</div>
```

**步骤 2: 在 JavaScript 中调用**

```javascript
// 切换到结果视图时加载数据
async function switchTab(tabName) {
    // ... 其他逻辑 ...

    if (tabName === 'results' && currentBatchId) {
        // 加载批次结果
        await loadEventBatchResults(currentBatchId);
    }
}
```

---

## 对比表格展示效果

### 表格列结构

```
┌─────────────┬──────────────┬──────────┬──────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ 控制策略     │ 平均速度      │ 相比基准  │ 平均行程时间  │ 相比基准  │ 完成率    │ 相比基准  │ 总延误    │ 相比基准  │ 总车辆数  │
│             │ (km/h)       │          │ (秒)         │          │ (%)      │          │ (秒)     │          │          │
├─────────────┼──────────────┼──────────┼──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 无控制（基准）│ 45.2         │ -        │ 1200         │ -        │ 96.5     │ -        │ 12h 30m  │ -        │ 8934     │
├─────────────┼──────────────┼──────────┼──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 可变限速     │ 52.8         │ ↑16.8%  │ 1050         │ ↓12.5%  │ 98.2     │ ↑1.76%  │ 10h 33m  │ ↓15.6%  │ 8934     │
│             │              │ (绿色)   │              │ (绿色)   │          │ (绿色)   │          │ (绿色)   │          │
├─────────────┼──────────────┼──────────┼──────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 收费站管控   │ 49.5         │ ↑9.5%   │ 1120         │ ↓6.7%   │ 97.8     │ ↑1.35%  │ 11h 15m  │ ↓10.0%  │ 8934     │
│             │              │ (绿色)   │              │ (绿色)   │          │ (绿色)   │          │ (绿色)   │          │
└─────────────┴──────────────┴──────────┴──────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 策略排名表

```
┌──────┬──────────┬────────────────┬──────┐
│ 排名  │ 控制策略  │ 综合改善率 (%)  │ 评价  │
├──────┼──────────┼────────────────┼──────┤
│ 🥇1  │ 可变限速  │ +15.5%         │ 优秀  │
├──────┼──────────┼────────────────┼──────┤
│ 🥈2  │ 收费站管控│ +10.2%         │ 良好  │
├──────┼──────────┼────────────────┼──────┤
│ 🥉3  │ 动态硬路肩│ +7.8%          │ 一般  │
└──────┴──────────┴────────────────┴──────┘
```

---

## 颜色和箭头规则

### 改善指示规则

| 指标类型 | 提升情况 | 颜色 | 箭头 | 示例 |
|---------|---------|------|------|------|
| 速度 (越高越好) | 提升 | 绿色 | ↑ | ↑16.8% |
| 速度 (越高越好) | 降低 | 红色 | ↓ | ↓5.2% |
| 行程时间 (越低越好) | 降低 | 绿色 | ↓ | ↓12.5% |
| 行程时间 (越低越好) | 提升 | 红色 | ↑ | ↑8.3% |
| 完成率 (越高越好) | 提升 | 绿色 | ↑ | ↑1.76% |
| 延误 (越低越好) | 降低 | 绿色 | ↓ | ↓15.6% |

### 评价等级

| 综合改善率 | 评价 | 颜色 |
|-----------|------|------|
| ≥15% | 优秀 | 绿色渐变 |
| 10-15% | 良好 | 蓝色渐变 |
| 5-10% | 一般 | 橙色渐变 |
| <5% | 较差 | 红色渐变 |

---

## 测试和调试

### 使用测试数据

在浏览器控制台中执行：

```javascript
// 加载示例数据
testLoadResults();
```

### 查看组件状态

```javascript
// 检查容器是否存在
document.getElementById('comparisonTableContainer');

// 检查函数是否可用
typeof renderEventScenarioComparisonTable;  // 应该返回 "function"
```

### 常见问题

**Q1: 表格不显示？**
- 检查容器ID是否正确
- 检查数据格式是否符合要求
- 查看浏览器控制台错误信息

**Q2: 改善百分比不正确？**
- 确认基准数据（NO_CONTROL）存在
- 检查 `higherIsBetter` 参数是否正确设置

**Q3: 样式不生效？**
- 确认 CSS 文件已引入
- 检查 CSS 文件路径是否正确

---

## 后端 API 要求

为了使用此组件，后端需要提供以下格式的数据：

### API 端点

```
GET /api/v1/batch/event-batch-results/{batch_id}
```

### 响应格式

```json
{
  "event_id": "string",
  "batch_id": "string",
  "strategy_comparison": {
    "NO_CONTROL": { /* 指标对象 */ },
    "VSS": { /* 指标对象 */ },
    "TEC": { /* 指标对象 */ },
    "DHS": { /* 指标对象 */ }
  },
  "strategy_ranking": [
    {
      "strategy": "string",
      "overall_improvement": number,
      "rank": number
    }
  ]
}
```

### 指标对象结构

```json
{
  "avg_speed": number,              // 必需
  "avg_trip_duration": number,      // 必需
  "completion_rate": number,        // 必需
  "total_vehicles": number,         // 必需
  "total_delay": number,            // 可选
  "avg_waiting_time": number,       // 可选
  "improvement_vs_baseline": {      // 非基准策略才有
    "avg_speed": number,
    "avg_trip_duration": number,
    "completion_rate": number
  }
}
```

---

## 完整集成示例

详见 `event-batch-results-example.html`，包含：

1. ✅ 完整的 HTML 结构
2. ✅ CSS 和 JS 引入
3. ✅ 批次信息展示
4. ✅ 对比表格渲染
5. ✅ 策略排名展示
6. ✅ 测试数据和调试函数

---

## 总结

这个事件场景对比表格组件完全参考了优化仿真的成功设计模式，具有以下优势：

1. **一致性**：与现有优化仿真页面保持视觉和交互一致
2. **可复用**：可在多个页面中使用（analysis_viewer.html, event-batch-center.html）
3. **易集成**：只需3步即可集成（引入文件、添加容器、调用函数）
4. **灵活性**：支持自定义容器ID，可同时展示多个表格
5. **响应式**：支持桌面和移动端显示

**文档状态:** ✅ 完成
**最后更新:** 2025-11-15
**维护者:** 开发团队
