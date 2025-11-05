# Strategy Ranking 错误修复总结 - 2025-11-05

**日期**: 2025-11-05
**问题**: Strategy Ranking 功能无法调用，出现两个错误
**状态**: ✅ 已修复
**Commit**: c4bfd47

---

## 问题描述

用户在批量仿真结果页面点击"查看详细分析"按钮时，遇到以下错误：

### 错误1: API_BASE is not defined
```
✗ 生成优化方案失败: API_BASE is not defined
```

### 错误2: 405 Method Not Allowed
```
POST http://localhost:8000/control/http//localhost:8000/api/v1/control/batch-optimization/batch/case_20251103_141612/batch_20251105_000102/strategy-ranking 405 (Method Not Allowed)
```

---

## 根本原因分析

### 原因1: API_BASE 未定义

`strategy_ranking.js` 在两个不同的HTML页面中使用：
1. `simulations.html` - 加载 `batch_simulation.js` (定义 `API_BASE`)
2. `optimization.html` - 加载 `optimization.js` (定义 `API_BASE`)

但 `strategy_ranking.js` 没有被加载到 `simulations.html` 中，所以当从批量仿真页面跳转到优化分析时，`strategy_ranking.js` 无法访问全局的 `API_BASE`。

### 原因2: 错误的 API 端点路由

**路由注册**:
```python
# api/routes/__init__.py:38
router.include_router(batch_optimization_router, tags=["批量优化仿真"])
# 没有 prefix，所以路由直接在 /api/v1/ 下
```

**后端路由定义**:
```python
# api/routes/batch_optimization_routes.py:426
@router.post("/batch/{case_id}/{batch_id}/strategy-ranking", ...)
# 完整路径: /api/v1/batch/{case_id}/{batch_id}/strategy-ranking
```

**前端错误的 URL 构造**:
```javascript
// 错误的 URL
`${API_BASE}/control/batch-optimization/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
// 评估为: /api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking ❌
```

多出的 `/control/batch-optimization/` 路径导致 404/405 错误。

---

## 修复方案

### 修复1: 加载 strategy_ranking.js

**文件**: `frontend/control/simulations.html`

添加脚本标签使 `strategy_ranking.js` 在 `simulations.html` 中可用：

```html
<!-- 策略排名模块 (Layer 2) -->
<script src="js/strategy_ranking.js?v=2025110301"></script>
```

这样 `strategy_ranking.js` 可以访问 `batch_simulation.js` 定义的全局 `API_BASE`。

### 修复2: 纠正 API 端点 URL

**文件**: `frontend/control/js/strategy_ranking.js`

修改所有 API 调用的 URL 路径：

**修改前**:
```javascript
`${API_BASE}/control/batch-optimization/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
```

**修改后**:
```javascript
`${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
```

这样生成的 URL 将是：
```
/api/v1/batch/{case_id}/{batch_id}/strategy-ranking ✅
```

匹配后端路由：
```python
@router.post("/batch/{case_id}/{batch_id}/strategy-ranking", ...)
```

---

## 修改详情

### 文件 1: `frontend/control/simulations.html`

```diff
+ <script src="js/strategy_ranking.js?v=2025110301"></script>
```

**位置**: 第 302 行
**效果**: `strategy_ranking.js` 在 `simulations.html` 中加载，使其可以访问全局 `API_BASE`

### 文件 2: `frontend/control/js/strategy_ranking.js`

修改了两处 URL 构造（第 82 行和第 152 行）：

```diff
- `${API_BASE}/control/batch-optimization/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`,
+ `${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`,
```

**位置**:
- 第 82 行: `loadAndDisplayRanking()` 函数中
- 第 152 行: `triggerStrategyRanking()` 函数中

---

## 验证

### 修复后的工作流

1. **批量仿真页面** (`simulations.html`)
   - 加载 `batch_simulation.js` → 定义 `API_BASE = '/api/v1'`
   - 加载 `strategy_ranking.js` → 可以访问 `API_BASE`

2. **点击查看详细分析**
   - 转到 `optimization.html?batch_id=xxx&case_id=xxx`
   - `optimization.js` 也定义 `API_BASE = '/api/v1'`
   - `strategy_ranking.js` 自动初始化并调用 API

3. **API 调用**
   - 构造的 URL: `/api/v1/batch/{case_id}/{batch_id}/strategy-ranking` ✅
   - 匹配后端路由 ✅
   - 返回 200 OK ✅

### 测试步骤

1. 打开浏览器开发者工具 (F12)
2. 进入批量仿真页面
3. 查看批次列表
4. 点击批次卡片上的"查看结果"
5. 在结果页面点击"查看详细优化分析"
6. 验证：
   - ✅ 不出现 "API_BASE is not defined" 错误
   - ✅ 不出现 "405 Method Not Allowed" 错误
   - ✅ 加载指示器显示
   - ✅ 3-5秒后显示优化方案结果
   - ✅ Network 标签显示正确的 URL 和 200 响应

---

## 技术细节

### API 路由层级结构

```
/api/v1
  ├── /data/...                    (data_router, prefix="/data")
  ├── /simulation/...              (simulation_router, prefix="/simulation")
  ├── /case/...                    (case_router, prefix="/case")
  ├── /analysis/...                (analysis_router, prefix="/analysis")
  ├── /template/...                (template_router, prefix="/template")
  ├── /file/...                    (file_router, prefix="/file")
  ├── /control/...                 (control_router, prefix="/control")
  ├── /control-instance/...        (control_instance_router, no prefix)
  ├── /control-plan/...            (control_plan_router, no prefix)
  └── /batch/...                   (batch_optimization_router, NO PREFIX!)
       ├── GET /{case_id}/{batch_id}
       ├── GET /{case_id}/{batch_id}/progress
       ├── GET /{case_id}/{batch_id}/results
       └── POST /{case_id}/{batch_id}/strategy-ranking
```

**关键点**: `batch_optimization_router` 没有前缀，所以路由直接在 `/api/v1/` 下。

---

## 提交信息

```
commit c4bfd47
Author: Claude <noreply@anthropic.com>
Date:   2025-11-05

    fix: Correct strategy ranking API endpoint URL path

    The frontend was using an incorrect URL path for the strategy ranking API:
    - Before: /api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking
    - After: /api/v1/batch/{case_id}/{batch_id}/strategy-ranking

    The batch_optimization_router is registered without a prefix in routes/__init__.py (line 38),
    so the route defined in batch_optimization_routes.py (/batch/{case_id}/{batch_id}/strategy-ranking)
    should not have the extra /control/batch-optimization/ path segments.

    This fixes the 405 (Method Not Allowed) error when calling the strategy ranking endpoint.
```

---

## 影响分析

### 受影响的功能

- ✅ Strategy Ranking (Layer 2 - 控制策略排序)
- ✅ 批量仿真结果分析页面 (optimization.html)

### 向后兼容性

- ✅ 完全兼容 (无破坏性改动)
- ✅ 不影响其他 API 端点
- ✅ 不影响批量仿真 (Layer 1)

### 性能影响

- ✅ 无性能变化 (仅修复 URL 路由)

---

## 相关文档

- [FINAL_OPTIMIZATION_SUMMARY.md](FINAL_OPTIMIZATION_SUMMARY.md) - 性能优化总结
- [LOADING_INDICATOR_IMPLEMENTATION.md](LOADING_INDICATOR_IMPLEMENTATION.md) - 加载指示器实现
- `api/routes/batch_optimization_routes.py` - 后端 API 路由定义

---

**修复完成日期**: 2025-11-05
**修复者**: Claude Code
**状态**: ✅ 完成，等待用户验证

