# Batch Loading Feature Implementation

## 概述（Overview）

本特性实现了批次智能加载功能，允许用户在以下两种情况下自动加载上次查看的批次或最新完成的批次：

1. **从导航栏进入方案优化（排序结果页）**：应加载上次查看的批次或加载最新仿真完成的批次的排序结果
2. **从批量仿真-结果标签直接进入批次结果页**：应加载上次查看批次的结果或加载最新仿真完成的批次的批次结果

## 实现细节（Implementation Details）

### 1. 持久化存储（Persistence）

#### 保存上次查看的批次信息
**文件**: `frontend/control/js/batch_results.js`

当用户加载批次结果时，自动保存到 `localStorage`：

```javascript
// 💾 保存上次查看的批次 (用于导航栏进入时恢复)
localStorage.setItem('lastViewedBatchId', batchId);
localStorage.setItem('lastViewedCaseId', caseId);
localStorage.setItem('lastViewedBatchTimestamp', new Date().toISOString());
```

**触发时机**：每当调用 `loadBatchResults(batchId, caseId)` 时

### 2. 方案优化页面（optimization.html）

#### 自动加载批次
**文件**: `frontend/control/js/strategy_ranking.js`

**初始化逻辑** (`initializeRankingPage()`):

```
优先级 1：URL 参数中的 batch_id 和 case_id
  ↓
优先级 2：localStorage 中保存的 lastViewedBatchId 和 lastViewedCaseId
  ↓
优先级 3：搜索所有案例，找到最新完成的批次
```

**流程**:
1. 如果 URL 有参数 `batch_id` 和 `case_id`，使用这些参数
2. 如果没有，从 localStorage 恢复上次查看的批次
3. 如果都没有，调用 `loadLatestCompletedBatch()` 查找最新完成的批次
4. 自动加载排序结果并展示

#### 查找最新完成的批次
**函数**: `loadLatestCompletedBatch()`

该函数：
- 获取所有案例列表
- 遍历每个案例的批次列表
- 找到状态为 `completed` 且 `completed_at` 最新的批次
- 加载该批次的排序结果

### 3. 批量仿真结果页面（simulations.html）

#### 点击结果标签页时自动加载
**文件**: `frontend/control/js/batch_simulation.js`

**修改的 switchView 函数**:

```javascript
if (view === 'results') {
    if (currentBatchId && !batchResultsData) {
        // 有当前批次且数据未加载，加载数据
        loadResults();
    } else if (!currentBatchId && !batchResultsData) {
        // 无当前批次，尝试加载上次查看的批次
        loadLastViewedBatchResults();
    }
}
```

#### 加载上次查看的批次
**函数**: `loadLastViewedBatchResults()`

该函数：
1. 从 localStorage 恢复 `lastViewedBatchId` 和 `lastViewedCaseId`
2. 如果有保存的批次，加载该批次的结果
3. 如果没有，调用 `loadLatestCompletedBatchResults()` 查找最新完成的批次

#### 在当前案例中查找最新完成的批次
**函数**: `loadLatestCompletedBatchResults()`

该函数：
- 获取当前案例的批次列表
- 找到状态为 `completed` 且 `completed_at` 最新的批次
- 加载该批次的结果

## 用户体验流程（User Experience Flow）

### 场景 1：从导航栏点击"方案优化"

```
用户点击左侧导航栏"方案优化"
  ↓
进入 optimization.html
  ↓
initializeRankingPage() 执行
  ↓
检查 URL 参数
  │ ├─ 有 → 使用 URL 参数的批次
  │ └─ 无 → 检查 localStorage
  │       ├─ 有 → 使用保存的批次
  │       └─ 无 → 查找最新完成的批次
  ↓
自动加载排序结果
  ↓
显示排序表格和推荐方案
```

### 场景 2：点击批量仿真的"结果"标签页

```
用户点击"结果"标签页
  ↓
switchView('results') 执行
  ↓
检查当前批次
  │ ├─ 有 → 加载该批次的结果
  │ └─ 无 → 调用 loadLastViewedBatchResults()
  │       ├─ 有保存的批次 → 加载该批次
  │       └─ 无 → 在当前案例查找最新完成的批次
  ↓
显示批次结果对比
```

## 数据存储（Data Storage）

### localStorage 键值对

| 键 | 值 | 用途 |
|---|---|---|
| `lastViewedBatchId` | 批次ID (e.g., `batch_20251105_000102`) | 记录上次查看的批次ID |
| `lastViewedCaseId` | 案例ID (e.g., `case_20251103_141612`) | 记录上次查看的案例ID |
| `lastViewedBatchTimestamp` | ISO 8601 时间戳 | 记录上次查看的时间 |

## 错误处理（Error Handling）

### 优雅降级（Graceful Degradation）

1. **URL 参数无效** → 回退到 localStorage
2. **localStorage 无效** → 查找最新完成的批次
3. **最新批次查询失败** → 显示错误信息，提示用户手动创建/选择批次

### 用户提示（User Messages）

- "📋 从 localStorage 恢复上次查看的批次: {batchId}"
- "✅ 找到最新完成的批次: {batchId}"
- "未找到已完成的批次，请从批量仿真页面创建并运行批次"
- "请先选择案例"

## API 端点依赖（API Dependencies）

### 获取案例列表
```
GET /api/v1/data/case-management/cases
```

### 获取案例的批次列表
```
GET /api/v1/control/batch-optimization/case/{case_id}/batches
```

### 加载批次结果
```
GET /api/v1/control/batch-optimization/batch/{batch_id}/results
```

### 生成策略排序
```
POST /api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking
```

## 测试清单（Test Checklist）

- [x] 语法检查：所有 JavaScript 文件通过语法验证
- [ ] 功能测试：从 optimization.html 导航栏进入，自动加载上次查看的批次
- [ ] 功能测试：从 optimization.html 导航栏进入，无历史记录时加载最新批次
- [ ] 功能测试：点击结果标签页，自动加载上次查看的批次
- [ ] 功能测试：点击结果标签页，无历史记录时加载最新批次
- [ ] 集成测试：localStorage 中的数据正确保存和恢复
- [ ] 错误处理：API 调用失败时显示正确的错误信息
- [ ] 性能测试：自动加载过程不影响页面加载时间

## 修改的文件（Modified Files）

1. **frontend/control/js/batch_results.js**
   - 添加 localStorage 保存逻辑

2. **frontend/control/js/strategy_ranking.js**
   - 修改 `initializeRankingPage()` 支持 localStorage 恢复
   - 添加 `loadLatestCompletedBatch()` 函数

3. **frontend/control/js/batch_simulation.js**
   - 修改 `switchView()` 支持自动加载
   - 添加 `loadLastViewedBatchResults()` 函数
   - 添加 `loadLatestCompletedBatchResults()` 函数

## 未来增强（Future Enhancements）

1. **批次历史记录**：在 UI 中显示最近访问的批次列表
2. **清空历史**：提供清空 localStorage 中保存的历史记录的选项
3. **时间过期**：设置历史记录过期时间（如 30 天后自动删除）
4. **多用户支持**：为不同用户保存不同的历史记录（需后端支持）

---

**实现日期**: 2025-11-05
**特性状态**: ✅ 已实现
