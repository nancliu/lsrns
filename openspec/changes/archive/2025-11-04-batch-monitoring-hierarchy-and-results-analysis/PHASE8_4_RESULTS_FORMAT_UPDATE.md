# Phase 8.4: 结果页面数据格式更新

**Date**: 2025-11-03
**Status**: ✅ **已完成**
**Commit**: `3aef185`

---

## 📋 问题描述

### 症状
虽然后端 API 已修复并返回正确的数据，但前端结果页面仍然显示"暂无对比数据"或其他旧实现的内容。

### 原因
前端 `batch_results.js` 中的 `renderBatchResultsView()` 函数期望的是**旧的数据格式**：

```javascript
// 旧格式期望
batchResultsData.analysis.comparison_summary.rows
batchResultsData.metadata
```

但后端现在返回的是**新格式**：

```javascript
// 新格式实际返回
batchResultsData.plan_results  // ← 直接是方案结果列表！
batchResultsData.created_at
batchResultsData.completed_at
```

### 数据格式对比

**旧格式**（使用 BatchResultAnalyzer）：
```json
{
  "batch_id": "batch_xxx",
  "case_id": "case_xxx",
  "status": "completed",
  "analysis": {
    "plan_results": {},
    "comparison_summary": {},
    "improvement_rates": {}
  },
  "metadata": {
    "created_at": "2025-11-03...",
    "completed_at": "2025-11-03..."
  }
}
```

**新格式**（直接从 sim 结果）：
```json
{
  "batch_id": "batch_xxx",
  "status": "completed",
  "plan_results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案（无管控）",
      "simulations": [
        {
          "seed": 66,
          "simulation_id": "...",
          "avg_travel_time": 1450.2,
          "avg_speed": 22.5,
          "total_vehicles": 4200
        },
        {
          "seed": 67,
          ...
        }
      ],
      "aggregated_metrics": {
        "avg_travel_time": {
          "mean": 1448.5,
          "std": 5.2,
          "min": 1442.0,
          "max": 1455.0
        },
        "avg_speed": {
          "mean": 22.55,
          "std": 0.15,
          "min": 22.4,
          "max": 22.7
        }
      }
    },
    {
      "plan_id": "plan_002",
      ...
    }
  ],
  "created_at": "2025-11-03T09:54:02.262840",
  "completed_at": "2025-11-03T09:55:38.724147"
}
```

---

## ✅ 解决方案

### 1. 更新 `renderBatchResultsView()` 函数

```javascript
function renderBatchResultsView() {
    // Phase 8.4修复：支持新的 API 响应格式
    const planResults = batchResultsData.plan_results || [];
    const metadata = {
        created_at: batchResultsData.created_at,
        completed_at: batchResultsData.completed_at
    };

    renderResultsSummary(metadata);

    // 优先使用新格式
    if (planResults && planResults.length > 0) {
        renderNewBatchResults(planResults);
    } else {
        // 降级到旧格式（向后兼容）
        const analysis = batchResultsData.analysis || {};
        // ... 旧实现
    }
}
```

**关键改进**：
- ✅ 检查 `plan_results` 字段（新格式）
- ✅ 如果存在则使用新的渲染函数
- ✅ 否则降级到旧格式（向后兼容）

### 2. 新增 `renderNewBatchResults()` 函数

处理新的数据格式，从 `plan_results` 列表中构建对比表格：

```javascript
function renderNewBatchResults(planResults) {
    // 1. 获取基准方案（通常是第一个）
    const baselinePlan = planResults[0];
    const testPlans = planResults.slice(1);

    // 2. 从 aggregated_metrics 提取所有指标名称
    const metricKeys = Object.keys(baselinePlan.aggregated_metrics);

    // 3. 构建对比表格
    // 对于每个指标，显示：
    // - 基准方案的均值和标准差
    // - 各 test 方案的均值和改进率

    // 4. 计算改进率
    // - 对于速度（越高越好）：(test - baseline) / baseline
    // - 对于延误（越低越好）：反向计算
}
```

**函数特点**：
- ✅ 支持任意数量的指标
- ✅ 动态计算改进率
- ✅ 指标反向处理（延误/等待时间）
- ✅ 正确的表格布局（基准 vs 所有 test）

---

## 📊 新旧实现对比

| 特性 | 旧实现 | 新实现 |
|------|--------|--------|
| **数据来源** | BatchResultAnalyzer（路径查找有bug） | 直接从 sim 结果聚合 |
| **指标获取** | `comparison_summary.rows` 预先计算 | 从 `aggregated_metrics` 动态读取 |
| **改进率** | 预先在后端计算 | 前端动态计算 |
| **灵活性** | 固定格式 | 支持任意指标 |
| **可靠性** | ❌ 依赖路径查找 | ✅ 直接使用现有数据 |

---

## 🧪 测试方案

1. **创建新批次** → 等待完成
2. **点击"查看结果"** → 切换到结果视图
3. **验证表格显示**：
   - ✅ 表头正确（基准 + test 方案）
   - ✅ 指标正确显示
   - ✅ 改进率计算正确
   - ✅ 色彩标识（绿=改进, 红=恶化）

### 预期结果

对于包含多个种子的批次，应显示：
```
指标                基准方案              plan_id_001
                   均值    标准差        均值    改进%
avg_speed          22.55   0.15         23.10   +2.4%  (绿)
avg_travel_time    1448.5  5.2          1420.0  -1.9%  (绿)
total_vehicles     4205.0  2.5          4208.0  +0.1%  (绿)
```

---

## 🔄 向后兼容性

函数使用"优先新格式、降级旧格式"的策略：

```javascript
if (planResults && planResults.length > 0) {
    renderNewBatchResults(planResults);  // 新格式
} else {
    // 旧实现代码...  // 旧格式（如果 API 还返回）
}
```

这样即使 API 暂时返回旧格式，页面也能继续工作。

---

## 📝 相关改动

**修改文件**：
- `frontend/control/js/batch_results.js` (+98 行)
  - 修改 `renderBatchResultsView()` 函数
  - 新增 `renderNewBatchResults()` 函数

**关联 commit**：
- `3aef185` - feat: Phase 8.4 - 更新结果页面支持新的API数据格式

---

## 🎓 技术细节

### 指标反向处理

某些指标的"好"的方向与其他指标相反：

```javascript
// 速度、车辆数等：越高越好
improvement = (test - baseline) / baseline

// 延误、等待时间：越低越好 → 反向
if (metricKey.includes('delay') || metricKey.includes('waiting')) {
    improvementRate = -improvementRate;
}
```

### 聚合统计

从多个仿真结果（sim_66, sim_67, sim_68...）中计算：
- **均值（mean）**：所有运行的平均值
- **标准差（std）**：样本间的变异
- **最小值（min）**、**最大值（max）**：范围

这些统计值已在后端计算，前端直接使用。

---

**Status**: ✅ **已实现并提交**
**Next**: 刷新浏览器重新测试，批次结果现在应显示新格式的数据！
