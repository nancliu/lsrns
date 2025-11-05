# Batch API 性能优化指南

快速参考: 为什么批量仿真API很快，以及如何保持这一点。

## 🚀 关键优化

### 1. Backend Case查询优化
**函数**: `_find_case_id_for_batch()` in `api/routes/batch_optimization_routes.py`

**使用场景**: 任何需要从batch_id获取case_id的地方

```python
# ✅ 推荐做法
from api.routes.batch_optimization_routes import _find_case_id_for_batch

case_id = _find_case_id_for_batch(batch_id)
```

**性能**: <100ms (vs 5-10秒的目录遍历)

**不要做这样的事**:
```python
# ❌ 错误：会造成5-10秒延迟
cases_dir = Path("cases")
for case_dir in cases_dir.iterdir():
    possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
    if possible_path.exists():
        case_id = case_dir.name
        break
```

---

## 🎯 高频Endpoint优化

### /batch/{batch_id}/progress (轮询endpoint)
**优化**: 使用_find_case_id_for_batch()
**频率**: 每1-2秒轮询一次(重要)
**性能**: 3-5ms per request
**用户体验**: 流畅的进度更新，无延迟

### /batch/{batch_id}/results (主要endpoint)
**优化**:
1. 使用_find_case_id_for_batch() (-8秒)
2. 前端缓存避免重复请求 (-3秒)
3. 包含include_time_series参数 (bug fix)

**性能**: <100ms API + <100ms缓存检查
**首次加载**: 300-500ms
**缓存命中**: 0ms

---

## 📊 网络优化

### 批次列表API
**优化**: limit=50 (vs 1000)
**影响**: 减少95%的不必要数据传输

```javascript
// ✅ 推荐
const params = new URLSearchParams({
    case_id: caseInfo.case_id,
    page: 1,
    limit: 50  // 只加载实际需要的
});
```

**数据量对比**:
- limit=1000: 500KB-2.5MB per case
- limit=50: 50-250KB per case

---

## 🎨 前端优化清单

- [x] 使用requestAnimationFrame()批量Chart.js渲染
- [x] 实现5分钟TTL内存缓存(最多10个batch)
- [x] 移除全局MutationObserver(用局部替代)
- [x] 批次列表使用limit=50分页

---

## 🔍 调试性能问题

### 如果API响应变慢

1. **检查是否使用了_find_case_id_for_batch()**
   ```python
   case_id = _find_case_id_for_batch(batch_id)  # ✅ 正确
   ```

2. **检查网络请求大小**
   - 批次列表应该<500KB (limit=50)
   - 如果>1MB,检查limit参数

3. **检查进度轮询频率**
   - 应该每1-2秒一次
   - 确保使用了异步/await避免阻塞

4. **Profile service层**
   ```python
   import time
   start = time.time()
   # your code
   print(f"耗时: {time.time() - start:.2f}s")
   ```

---

## 📈 性能基准

**目标值** (优化后):
| 操作 | 目标 | 实际 | 状态 |
|-----|-----|------|------|
| 获取batch结果 | <100ms | 80-100ms | ✅ |
| 进度轮询 | <10ms | 3-5ms | ✅ |
| 批次列表 | <300ms | 200-300ms | ✅ |
| 缓存命中 | 0ms | <1ms | ✅ |

**警告值** (需要调查):
| 操作 | 警告值 | 说明 |
|-----|------|------|
| 获取batch结果 | >500ms | 检查service层或网络 |
| 进度轮询 | >50ms | 检查是否目录扫描 |
| 批次列表 | >1s | 检查limit参数 |

---

## 🔧 常见陷阱

### 陷阱 1: 忘记使用辅助函数
```python
# ❌ 错误
for case_dir in cases_dir.iterdir():  # 5-10秒延迟
    ...

# ✅ 修复
case_id = _find_case_id_for_batch(batch_id)  # <100ms
```

### 陷阱 2: limit=1000导致数据膨胀
```python
# ❌ 错误
params = {"limit": 1000}  # 2.5MB per case

# ✅ 修复
params = {"limit": 50}  # 250KB per case
```

### 陷阱 3: 未传递include_time_series参数
```python
# ❌ 错误
result = batch_service.get_batch_results(case_id, batch_id)

# ✅ 修复
result = batch_service.get_batch_results(
    case_id, batch_id,
    include_time_series=include_time_series  # 不能遗漏!
)
```

### 陷阱 4: 前端重复API调用
```javascript
// ❌ 错误：每次点击重新加载
onclick="loadBatchResults(id)"

// ✅ 修复：使用缓存机制
const cached = getCachedBatchResults(id);
if (cached) return cached;
```

---

## 📚 相关文件

- **代码**:
  - `api/routes/batch_optimization_routes.py` - 优化的路由
  - `frontend/control/js/batch_results.js` - 前端缓存
  - `api/services/batch_optimization_service.py` - 服务层

- **文档**:
  - `PERFORMANCE_OPTIMIZATION_SUMMARY.md` - 详细优化总结
  - `NETWORK_PERFORMANCE_ANALYSIS.md` - 网络瓶颈分析

- **测试**:
  - `tests/unit/routes/test_batch_optimization_routes.py`
  - `tests/unit/routes/test_batch_include_timeseries_fix.py`

---

## ✅ 代码审查检查清单

添加新的batch API endpoint时:

- [ ] 使用了_find_case_id_for_batch()而不是目录遍历
- [ ] 设置了合理的limit参数(默认50)
- [ ] 如果需要时序数据，传递了include_time_series参数
- [ ] 添加了性能评论说明优化
- [ ] 编写了单元测试验证功能
- [ ] 验证响应时间<100ms (API部分)

---

## 🚦 性能监控

### 定期检查
```bash
# 检查所有batch endpoints
grep -n "def.*batch" api/routes/batch_optimization_routes.py

# 查找潜在的N+1问题
grep -n "for.*iterdir\|for.*list" api/routes/batch_optimization_routes.py
```

### 预警信号
- 🔴 API响应>1秒
- 🔴 内存使用持续上升(未清理缓存)
- 🔴 网络请求大小>2MB
- 🟡 directory iteration calls

---

## 联系和反馈

如有性能问题或建议改进，请参考:
- `docs/testing/PERFORMANCE_OPTIMIZATION_SUMMARY.md` - 完整背景
- `docs/testing/NETWORK_PERFORMANCE_ANALYSIS.md` - 分析方法

---

**最后更新**: 2025-11-05
**维护者**: 性能优化小组
