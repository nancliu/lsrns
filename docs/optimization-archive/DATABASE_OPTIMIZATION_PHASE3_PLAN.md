# 数据库查询性能优化 - Phase 3 计划

**预期完成时间**: ~1小时
**预期性能改善**: 60-80% (考虑70%缓存命中率)
**预期响应时间**: ~160ms (相比5440ms的97%改善)

---

## 背景

Phase 2 已经将查询时间从5440ms降低到539ms (90%改善)。Phase 3将通过缓存进一步改善，预期在70%缓存命中率下达到97%的总体改善。

### 性能预期

```
首次查询 (无缓存): 539ms
缓存命中 (cache hit): ~1ms
平均响应时间 (70%命中率): (539 * 0.3) + (1 * 0.7) = ~162ms

改善: (5440 - 162) / 5440 = 97% ✅
```

---

## 实现方案

### 方案选择: functools.lru_cache + TTL

**理由**:
- 简单易用 (Python标准库)
- 低开销 (内存高效)
- 支持maxsize限制
- 易于监控命中率

### 缓存策略

**缓存键**:
```python
hash((
    tuple(route_codes) if route_codes else None,
    tuple(section_codes) if section_codes else None,
    tuple(node_types) if node_types else None,
    min_stake,
    max_stake,
    min_length,
    max_length,
    route_direction,
    tuple(demonstration_ids) if demonstration_ids else None,
    min_lanes,
    with_gantry
))
```

**缓存TTL**: 5分钟 (300秒)

**缓存大小**: maxsize=128 (保存最近128个查询结果)

**缓存命中条件**: 用户输入相同的过滤参数

---

## 实现步骤

### 步骤1: 创建TTL缓存装饰器

```python
import functools
import time
from typing import Callable, Any, Dict, Tuple

class TTLCache:
    """带TTL的LRU缓存装饰器"""

    def __init__(self, ttl_seconds: int = 300, maxsize: int = 128):
        self.ttl_seconds = ttl_seconds
        self.maxsize = maxsize
        self.cache = {}
        self.timestamps = {}
        self.hits = 0
        self.misses = 0

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self._make_key(args, kwargs)
            current_time = time.time()

            # 检查缓存是否存在且未过期
            if cache_key in self.cache:
                cached_time = self.timestamps[cache_key]
                if current_time - cached_time < self.ttl_seconds:
                    self.hits += 1
                    logger.debug(f"Cache HIT: {cache_key}")
                    return self.cache[cache_key]
                else:
                    # 缓存已过期，删除
                    del self.cache[cache_key]
                    del self.timestamps[cache_key]

            # 缓存未命中，执行函数
            self.misses += 1
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            # 保存到缓存
            if len(self.cache) >= self.maxsize:
                # 移除最旧的项
                oldest_key = min(self.timestamps, key=self.timestamps.get)
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]

            self.cache[cache_key] = result
            self.timestamps[cache_key] = current_time

            return result

        wrapper.cache_stats = self._get_stats
        return wrapper

    def _make_key(self, args: Tuple, kwargs: Dict) -> str:
        """生成缓存键"""
        key_parts = []

        # 从kwargs中提取参数
        for param in ['route_codes', 'section_codes', 'node_types',
                      'min_stake', 'max_stake', 'min_length', 'max_length',
                      'route_direction', 'demonstration_ids', 'min_lanes', 'with_gantry']:
            value = kwargs.get(param)
            if isinstance(value, list):
                key_parts.append(tuple(value))
            else:
                key_parts.append(value)

        return str(tuple(key_parts))

    def _get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': total,
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache),
            'maxsize': self.maxsize
        }
```

### 步骤2: 应用缓存到查询函数

```python
# 在edge_query.py中

# 创建缓存实例
_query_cache = TTLCache(ttl_seconds=300, maxsize=128)

@_query_cache
def query_edges_with_filters(
    route_codes: Optional[List[str]] = None,
    section_codes: Optional[List[str]] = None,
    node_types: Optional[List[str]] = None,
    min_stake: Optional[float] = None,
    max_stake: Optional[float] = None,
    min_length: Optional[float] = None,
    max_length: Optional[float] = None,
    route_direction: Optional[str] = None,
    demonstration_ids: Optional[List[int]] = None,
    min_lanes: Optional[int] = None,
    with_gantry: bool = False
) -> List[EdgeInfo]:
    """
    多维度筛选路段 (带缓存)

    PERFORMANCE OPTIMIZATION (Phase 1 + 2 + 3):
    =============================================
    Phase 1: 连接池 → 150-200ms改善 ✅
    Phase 2: 分离查询 → 4901ms改善 (90%) ✅
    Phase 3: 结果缓存 → 额外60-80%改善 ⏳

    缓存策略:
    - TTL: 5分钟
    - 大小: 128个查询结果
    - 命中时间: ~1ms
    - 预期命中率: 70%
    """
    # ... 现有实现 ...
```

### 步骤3: 添加缓存统计端点

```python
# 在api/routes/control_routes.py中

@router.get("/api/v1/control/cache-stats")
async def get_cache_stats():
    """获取查询缓存统计信息"""
    from shared.data_access.edge_query import query_edges_with_filters

    stats = query_edges_with_filters.cache_stats()
    return {
        "cache_stats": stats,
        "ttl_seconds": 300,
        "status": "active"
    }

@router.post("/api/v1/control/cache-clear")
async def clear_cache():
    """清除查询缓存"""
    from shared.data_access.edge_query import _query_cache

    _query_cache.cache.clear()
    _query_cache.timestamps.clear()
    _query_cache.hits = 0
    _query_cache.misses = 0

    return {"status": "cache cleared"}
```

### 步骤4: 添加缓存日志

在现有代码基础上，为缓存命中/未命中添加日志:

```python
logger.info(f"[Phase3] Cache HIT - saved {elapsed_time*1000:.1f}ms")
logger.info(f"[Phase3] Cache MISS - executed query in {elapsed_time*1000:.1f}ms")
logger.info(f"[Phase3] Cache stats: hits={hits}, misses={misses}, rate={hit_rate:.1f}%")
```

---

## 测试计划

### 单元测试

```python
def test_cache_hit():
    """测试缓存命中"""
    # 第一次查询: 缓存未命中
    start = time.time()
    result1 = query_edges_with_filters(route_codes=['G4202'])
    first_time = time.time() - start

    # 第二次相同查询: 缓存命中
    start = time.time()
    result2 = query_edges_with_filters(route_codes=['G4202'])
    second_time = time.time() - start

    # 验证结果相同
    assert result1 == result2

    # 验证缓存命中快很多
    assert second_time < first_time / 10  # 至少快10倍

def test_cache_expiry():
    """测试缓存过期"""
    result1 = query_edges_with_filters(route_codes=['G4202'])

    # 等待缓存过期
    time.sleep(301)  # TTL=300秒

    result2 = query_edges_with_filters(route_codes=['G4202'])
    assert result1 == result2  # 结果相同但重新查询

def test_cache_different_params():
    """测试不同参数不共享缓存"""
    result1 = query_edges_with_filters(route_codes=['G4202'], min_stake=33)
    result2 = query_edges_with_filters(route_codes=['G4202'], min_stake=40)

    # 结果不同（因为参数不同）
    assert len(result1) != len(result2) or result1[0].start_stake != result2[0].start_stake
```

### E2E测试

修改现有的 `test_edge_query_performance.spec.js`:

```javascript
// 添加缓存性能测试
test('缓存性能测试 - 首次查询vs缓存命中', async ({ page }) => {
    // 第一次查询: 测量无缓存性能
    await page.selectOption('#route-codes', 'G4202');
    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');

    const firstStart = Date.now();
    await page.click('#query-btn');
    await page.waitForSelector('#results-table');
    const firstTime = Date.now() - firstStart;

    // 清除结果
    await page.click('#clear-results');

    // 第二次查询: 测量缓存命中性能
    const secondStart = Date.now();
    await page.click('#query-btn');
    await page.waitForSelector('#results-table');
    const secondTime = Date.now() - secondStart;

    console.log(`首次查询: ${firstTime}ms`);
    console.log(`缓存命中: ${secondTime}ms`);
    console.log(`改善: ${((firstTime - secondTime) / firstTime * 100).toFixed(1)}%`);

    expect(secondTime).toBeLessThan(firstTime / 2);  // 至少快2倍
});
```

---

## 验证清单

- [ ] 创建TTLCache装饰器类
- [ ] 应用缓存到query_edges_with_filters()
- [ ] 添加缓存统计API端点
- [ ] 添加缓存清除API端点
- [ ] 运行单元测试，验证缓存逻辑
- [ ] 运行E2E测试，验证性能改善
- [ ] 验证缓存命中率达到70%
- [ ] 验证缓存命中响应时间 <10ms
- [ ] 更新文档

---

## 性能指标

### 预期结果

| 场景 | 响应时间 | 相比原始 | 相比Phase2 |
|------|---------|---------|-----------|
| 首次查询 (无缓存) | ~539ms | 90%改善 | 0% |
| 缓存命中 | ~1-10ms | 99.8%改善 | 98%改善 |
| 平均 (70%命中) | ~162ms | 97%改善 | 70%改善 |

### 监控指标

```python
cache_stats = {
    'hits': 150,          # 缓存命中次数
    'misses': 65,         # 缓存未命中次数
    'total': 215,         # 总查询次数
    'hit_rate': '69.8%',  # 命中率
    'size': 32,           # 当前缓存项数
    'maxsize': 128        # 最大缓存项数
}
```

---

## 后续维护

### 缓存监控

建议在生产环境中定期检查缓存统计:

```bash
# 查看缓存状态
curl http://localhost:8000/api/v1/control/cache-stats

# 如需清除缓存
curl -X POST http://localhost:8000/api/v1/control/cache-clear
```

### 缓存失效场景

缓存在以下场景自动失效，无需手动清除:
- TTL过期 (5分钟)
- 用户修改参数 (自动生成新的缓存键)
- 数据库数据更新 (需要手动触发 `/cache-clear` 或等待TTL过期)

---

## 相关文档

- [DATABASE_OPTIMIZATION_SUMMARY.md](./DATABASE_OPTIMIZATION_SUMMARY.md) - 优化总体计划
- [DATABASE_OPTIMIZATION_PHASE2_COMPLETE.md](./DATABASE_OPTIMIZATION_PHASE2_COMPLETE.md) - Phase 2完成报告
- [PHASE2_SESSION_SUMMARY.md](./PHASE2_SESSION_SUMMARY.md) - Phase 2实施总结

---

**准备就绪** ✅ 可随时启动Phase 3实施
