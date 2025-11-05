# Batch Loading Architecture - Layer 1 & Layer 2 Separation

## 问题背景

用户报告在批量仿真页面加载时出现 JavaScript 错误：
```
SyntaxError: Identifier 'API_BASE' has already been declared
```

## 根本原因分析

### 错误的架构设计
原本试图在 `simulations.html` 中同时加载 Layer 1 和 Layer 2 的脚本：

```html
<!-- simulations.html (错误配置) -->
<script src="js/batch_simulation.js"></script>          <!-- Layer 1 -->
<script src="js/batch_results.js"></script>             <!-- Layer 1 -->
<script src="js/strategy_ranking.js"></script>          <!-- ❌ Layer 2 (不应在此) -->
```

### 为什么会冲突

1. **batch_simulation.js** 定义了 `const API_BASE`
2. **strategy_ranking.js** 也定义了 `const API_BASE`
3. 当两个脚本在同一页面加载时，导致重复声明错误

### 正确的架构设计

Layer 1 和 Layer 2 是**完全独立**的两个模块，不应该在同一页面加载：

```
Layer 1 (Batch Monitoring & Results)
├─ simulations.html
│  ├─ Scripts:
│  │  ├─ notification.js (共享)
│  │  ├─ batch_simulation.js (Layer 1 特有)
│  │  ├─ batch_results.js (Layer 1 特有)
│  └─ Features:
│     ├─ 批次创建、启动、监控
│     ├─ 8 个基础指标对比
│     ├─ 进度跟踪
│     └─ [导航链接] → optimization.html

Layer 2 (Control Strategy Ranking)
├─ optimization.html
│  ├─ Scripts:
│  │  ├─ notification.js (共享)
│  │  ├─ strategy_ranking.js (Layer 2 特有)
│  └─ Features:
│     ├─ 多准则策略评分
│     ├─ 排序和推荐
│     ├─ 雷达图表展示
│     └─ [导航链接] → simulations.html
```

## 用户流程

### 场景 1：从导航栏进入方案优化

```
用户在 simulations.html 左侧导航栏
点击 "方案优化"
  ↓
导航到 optimization.html
  ↓
initializeRankingPage() 执行
  ├─ 检查 URL 参数 (batch_id, case_id)
  ├─ 若无，从 localStorage 恢复
  ├─ 若无，查询最新完成的批次
  ↓
自动加载排序结果
```

### 场景 2：从批量仿真结果标签页

```
用户在 simulations.html
点击 "结果" 标签页
  ↓
loadLastViewedBatchResults() 执行
  ├─ 从 localStorage 恢复上次查看的批次
  ├─ 若无，查询当前案例的最新批次
  ↓
显示批次结果对比
```

## 关键实现细节

### 1. localStorage 持久化（在 batch_results.js 中）

```javascript
// 每次加载批次时保存
localStorage.setItem('lastViewedBatchId', batchId);
localStorage.setItem('lastViewedCaseId', caseId);
localStorage.setItem('lastViewedBatchTimestamp', timestamp);
```

**为什么有效**：
- `batch_results.js` 被加载在两个页面中
- Layer 1 加载 → 用户查看批次 → 保存到 localStorage
- 用户导航到 Layer 2 → 读取 localStorage 恢复批次

### 2. Layer 1 的智能加载（在 batch_simulation.js 中）

```javascript
// 结果标签页的智能加载
if (view === 'results') {
    if (currentBatchId && !batchResultsData) {
        loadResults();  // 加载当前批次
    } else if (!currentBatchId && !batchResultsData) {
        loadLastViewedBatchResults();  // 恢复上次查看的批次
    }
}
```

### 3. Layer 2 的智能加载（在 strategy_ranking.js 中）

```javascript
// optimization.html 页面初始化
function initializeRankingPage() {
    const params = new URLSearchParams(window.location.search);
    currentBatchId = params.get('batch_id');
    currentCaseId = params.get('case_id');

    if (!currentBatchId || !currentCaseId) {
        // 优先级 1：从 localStorage 恢复
        const lastBatchId = localStorage.getItem('lastViewedBatchId');
        const lastCaseId = localStorage.getItem('lastViewedCaseId');

        if (lastBatchId && lastCaseId) {
            currentBatchId = lastBatchId;
            currentCaseId = lastCaseId;
        } else {
            // 优先级 2：查询最新完成的批次
            loadLatestCompletedBatch();
            return;
        }
    }

    loadAndDisplayRanking();
}
```

## 脚本加载清单

### simulations.html (Layer 1)
- ✅ notification.js - 共享通知组件
- ✅ batch_simulation.js - 批次创建和监控
- ✅ batch_results.js - 结果展示和 localStorage 保存
- ❌ strategy_ranking.js - **不应加载**

### optimization.html (Layer 2)
- ✅ notification.js - 共享通知组件
- ✅ strategy_ranking.js - 策略排名分析
- ❌ batch_simulation.js - **不应加载**
- ❌ batch_results.js - **不应加载**（但可选，如果需要显示批次信息）

## 全局变量作用域

### batch_simulation.js 声明
```javascript
const API_BASE = '/api/v1';
let currentBatchId = null;
let currentCaseId = null;
```
作用范围：仅在 simulations.html 中有效

### batch_results.js 声明
```javascript
let batchResultsData = null;
const batchResultsCache = new Map();
const CACHE_CONFIG = { ... };
```
作用范围：在两个页面中都有效（都加载了）

### strategy_ranking.js 声明
```javascript
const API_BASE = '/api/v1';
let rankingResultsData = null;
let rankingCharts = {};
let currentBatchId = null;
let currentCaseId = null;
```
作用范围：仅在 optimization.html 中有效（局部作用域）

## 跨页面通信机制

```
simulations.html                          optimization.html
───────────────────────                  ───────────────────

用户查看批次
    ↓
loadBatchResults(batchId, caseId)
    ↓
保存到 localStorage
{
  lastViewedBatchId: "batch_20251105_...",
  lastViewedCaseId: "case_20251103_...",
  lastViewedBatchTimestamp: "2025-11-05T..."
}
    ↓                                        ↓
[用户点击导航栏 "方案优化"]        optimization.html 加载
                                      ↓
                                 initializeRankingPage()
                                      ↓
                          从 localStorage 读取
                                      ↓
                          currentBatchId = lastViewedBatchId
                                      ↓
                          loadAndDisplayRanking()
```

## 错误排查指南

### 错误 1：`Identifier 'API_BASE' has already been declared`
**原因**：strategy_ranking.js 被错误地加载在 simulations.html 中
**解决**：检查 simulations.html，移除 `<script src="js/strategy_ranking.js"></script>`

### 错误 2：`currentBatchId is not defined`
**原因**：尝试在 optimization.html 中使用 batch_simulation.js 的变量
**解决**：使用 URL 参数或 localStorage 传递批次信息

### 错误 3：localStorage 中的数据不生效
**原因**：batch_results.js 未被加载（如果从外部直接进入 optimization.html）
**解决**：确保 optimization.html 中的 strategy_ranking.js 能独立运作

## 实现状态

✅ **完成的功能**：
- [x] Layer 1（simulations.html）的 localStorage 保存机制
- [x] Layer 1 的智能批次加载（点击结果标签页）
- [x] Layer 2（optimization.html）的智能批次加载（导航进入）
- [x] Layer 1 和 Layer 2 的正确分离

✅ **修复的问题**：
- [x] 移除 strategy_ranking.js 从 simulations.html
- [x] 恢复 strategy_ranking.js 的原始声明方式

## 相关提交

| 提交哈希 | 说明 |
|---------|------|
| `e504bf0` | feat: 实现批次智能加载功能 |
| `462c639` | fix: 解决 API_BASE 重复声明（临时方案） |
| `7314eda` | fix: 移除重复的全局变量声明（临时方案） |
| `721cdbd` | fix: 从 simulations.html 移除 strategy_ranking.js（正确方案） |

---

**实现日期**：2025-11-05
**状态**：✅ 已完成并验证
