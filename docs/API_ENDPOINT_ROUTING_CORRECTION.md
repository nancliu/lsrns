# API 端点路由修正说明 - 2025-11-05

**问题**: Strategy Ranking API 返回 405 Method Not Allowed
**根本原因**: 前端 URL 缺少后端路由器的 prefix
**状态**: ✅ 已修复
**Commit**: fb905d8

---

## 问题分析

### 错误信息

```
POST http://localhost:8000/api/v1/batch/case_20251103_141612/batch_20251105_000102/strategy-ranking 405 (Method Not Allowed)
```

### 根本原因

**后端路由定义** (`api/routes/batch_optimization_routes.py:26`):
```python
router = APIRouter(prefix="/control/batch-optimization", tags=["Batch Optimization"])
```

**路由处理器** (`api/routes/batch_optimization_routes.py:426`):
```python
@router.post("/batch/{case_id}/{batch_id}/strategy-ranking", ...)
```

**完整的实际路由**:
```
/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking
```

**前端调用的 URL** (修复前):
```
/api/v1/batch/{case_id}/{batch_id}/strategy-ranking  ❌
```

**正确的 URL** (修复后):
```
/api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking  ✅
```

---

## 之前的错误修复

### 为什么第一次修复是错的？

在之前的修复中，我们改为：
```javascript
`${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
```

**假设**: batch_optimization_router 在 `routes/__init__.py` 中没有 prefix

**查证**:
```python
# api/routes/__init__.py:38
router.include_router(batch_optimization_router, tags=["批量优化仿真"])
# 这里没有 prefix 参数
```

但实际上，**prefix 定义在路由器本身**！

```python
# api/routes/batch_optimization_routes.py:26
router = APIRouter(prefix="/control/batch-optimization", ...)
# prefix 在这里定义，不是在 include_router 时定义
```

---

## FastAPI 路由器 prefix 工作原理

### 关键概念

当创建 APIRouter 时设置 prefix：
```python
router = APIRouter(prefix="/control/batch-optimization")

@router.post("/batch/{case_id}/{batch_id}/strategy-ranking")
async def rank_strategies(...):
    pass
```

**最终路由路径** = `prefix` + `route`:
```
/control/batch-optimization + /batch/{case_id}/{batch_id}/strategy-ranking
= /control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking
```

### 注册到主路由器时

```python
# api/routes/__init__.py
router.include_router(batch_optimization_router, tags=["批量优化仿真"])
# include_router 时不指定 prefix，因为 prefix 已经在 APIRouter 中定义
```

### 最终的完整路径

```
/api/v1  (main.py 的 prefix)
+ /control/batch-optimization (batch_optimization_router 的 prefix)
+ /batch/{case_id}/{batch_id}/strategy-ranking (handler 的 path)
= /api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking
```

---

## 修复步骤

### 修改

**文件**: `frontend/control/js/strategy_ranking.js` (第73行和第143行)

**修改前**:
```javascript
`${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
```

**修改后**:
```javascript
`${API_BASE}/control/batch-optimization/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
```

### 验证

正确的 URL 应该是：
```
POST /api/v1/control/batch-optimization/batch/case_20251103_141612/batch_20251105_000102/strategy-ranking
```

---

## 为什么前面搞混了？

### 关键发现

在查看 `api/routes/__init__.py` 时，我看到：
```python
router.include_router(batch_optimization_router, tags=["批量优化仿真"])
```

**误解**: "batch_optimization_router 没有 prefix，因为 include_router 时没有指定"

**正确理解**: "prefix 是定义在 APIRouter 创建时的，不是在 include_router 时定义"

### 根本原因

有两种方式设置 prefix：

**方式1**: 在 APIRouter 创建时
```python
router = APIRouter(prefix="/control/batch-optimization")
```

**方式2**: 在 include_router 时
```python
router.include_router(child_router, prefix="/control/batch-optimization")
```

batch_optimization 使用的是**方式1**，我之前检查的是**方式2 的位置**。

---

## 最终的正确架构

### 路由层级

```
FastAPI app (main.py)
  ├── prefix: /api/v1
  └── include_router(router)
       │
       └── Main Router (routes/__init__.py)
            │
            └── include_router(batch_optimization_router)
                 │
                 └── batch_optimization_router (batch_optimization_routes.py)
                      ├── prefix: /control/batch-optimization
                      ├── @router.post("/batch/{case_id}/{batch_id}/strategy-ranking")
                      ├── @router.get("/batch/{case_id}/{batch_id}/progress")
                      └── @router.get("/batch/{case_id}/{batch_id}/results")
```

### 完整路径

```
/api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking
```

### 路径组成

| 层级 | prefix | path | 来源 |
|-----|--------|------|------|
| 1 | /api/v1 | | main.py |
| 2 | /control/batch-optimization | | batch_optimization_routes.py |
| 3 | | /batch/{case_id}/{batch_id}/strategy-ranking | @router.post(...) |

---

## 学习点

### ✅ 正确的调试方法

1. **检查 APIRouter 的定义**，不仅是 include_router
2. **理解 FastAPI 如何组合 prefix**
3. **查看完整的路由层级树**

### ✅ 最佳实践

1. 在 APIRouter 创建时就指定 prefix
2. 在 include_router 时不重复指定 prefix
3. 前端 URL 要包含所有层级的 prefix

### ❌ 常见错误

1. 只看 include_router，忽视 APIRouter 的 prefix
2. 假设 prefix 是分离的，实际是组合的
3. 忘记在 URL 中包含完整的路径

---

## 提交历史回顾

| Commit | 说明 | 是否正确 |
|--------|------|---------|
| c4bfd47 | 移除 `/control/batch-optimization/` | ❌ 错误 |
| 3a3e1fb | 分离 Layer 1 和 Layer 2 | ✅ 正确 |
| fb905d8 | 重新添加 `/control/batch-optimization/` | ✅ 正确 |

---

## 验证

### 测试步骤

1. **清除浏览器缓存** (Ctrl+Shift+Delete)
2. **重新加载 optimization.html**
3. **查看 Network 标签**
   - 请求 URL 应该是: `/api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking`
   - 响应状态应该是: 200 (不是 405)
4. **验证排序结果显示**
   - 应该能看到排序表格
   - 应该能看到推荐等级
   - 应该能看到雷达图

### 预期结果

```
✅ POST /api/v1/control/batch-optimization/batch/case_20251103_141612/batch_20251105_000102/strategy-ranking
✅ Status: 200 OK
✅ Response: { ranked_strategies: [...], scores: {...}, ... }
✅ UI: 排序结果正常显示
```

---

**修复完成日期**: 2025-11-05
**Commit**: fb905d8
**状态**: ✅ 完成

