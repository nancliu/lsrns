# 数据库查询性能优化计划

**计划日期**: 2025-11-01
**目标**: 将查询API耗时从 5.4秒 降低到 <2秒 (降低70%)
**优先级**: P1
**影响范围**: /api/v1/control/edges/query 接口

---

## 📊 性能现状分析

### 当前性能指标

```
API响应时间: 5463ms
  - 数据库查询: ~5400ms (99%)
  - Python处理: ~63ms (1%)
```

### 性能瓶颈识别

#### 问题1: 连接管理低效 ⚠️

**代码位置**: shared/data_access/edge_query.py:88

**问题**: 每次查询都建立新的TCP连接到数据库
- 连接建立耗时: 100-200ms
- 这是完全可避免的开销

**解决方案**: 使用SQLAlchemy连接池
- 预期改善: **节省 150-200ms/查询**

#### 问题2: 复杂JOIN查询 ⚠️

**代码位置**: shared/data_access/edge_query.py:92-166

**问题**:
- 3表JOIN (edges + nodes + gantries)
- GROUP BY 包含9个字段
- 类型转换阻止索引使用

**解决方案**: 分离查询
- 预期改善: **节省 2000-3000ms**

#### 问题3: 缺少查询结果缓存 ⚠️

**问题**: 相同参数的查询重复执行

**解决方案**: 添加查询结果LRU缓存
- 预期改善: **有缓存时: <50ms**

#### 问题4: 可优化的索引使用 ⚠️

**解决方案**: 添加范围查询专用索引
- 预期改善: **500-1000ms**

---

## 🔧 优化方案详情

### 优化1: 迁移到连接池 (快速修复)

**修改前**:
```python
conn = open_db_connection()  # 100-200ms
cur = conn.cursor()
cur.execute(sql, params)
conn.close()
```

**修改后**:
```python
from .connection import get_pooled_connection

conn = get_pooled_connection()  # <1ms
try:
    cur = conn.cursor()
    cur.execute(sql, params)
finally:
    conn.close()
```

**性能改善**: **150-200ms** | 难度: ⭐ 低

### 优化2: 分离查询 (中等修复)

**原理**: 将3表JOIN分解为3个简单查询

```python
# 查询1: 主要路段数据
edges = query_edges_base(...)

# 查询2: 批量获取节点类型
node_types = get_node_types_batch(...)

# 查询3: 批量获取门架信息
gantry_info = get_gantry_info_batch(...)

# 客户端合并结果 (毫秒级)
for edge in edges:
    edge.node_type = node_types.get(edge.from_junction)
    edge.gantry_info = gantry_info.get(...)
```

**性能改善**: **2000-3000ms** | 难度: ⭐⭐ 中

### 优化3: 添加查询结果缓存 (推荐)

**实现**: LRU缓存装饰器，TTL 5分钟

```python
@cached_query
def query_edges_with_filters(...) -> List[EdgeInfo]:
    # 原始实现
    ...
```

**性能改善**: 首次同前，后续 <50ms | 难度: ⭐ 低

### 优化4: 索引优化 (数据库优化)

**添加新索引**:
```sql
CREATE INDEX idx_edges_route_stake
ON dim.sim_network_edges(route_code, start_stake, end_stake);

CREATE INDEX idx_edges_route_lanes
ON dim.sim_network_edges(route_code, num_lanes);
```

**性能改善**: **500-1000ms** | 难度: ⭐ 低

---

## 📈 预期性能改善

| 场景 | 优化方案 | 耗时 | 改善 |
|------|---------|------|------|
| 原始 | 无 | 5463ms | - |
| 1 | 连接池 | 5313ms | 2.7% |
| 2 | 连接池 + 分离 | 2813ms | 48.5% |
| 3 | + 缓存 | 879ms | 84% |
| 4 | + 索引优化 | 654ms | 88% |

---

## 🚀 实施计划

### Phase 1: 快速修复 (连接池) - 30分钟
- [ ] 修改 edge_query.py 使用 get_pooled_connection()
- [ ] 测试和验证
- 预期: 5463ms → 5313ms

### Phase 2: 查询优化 (分离查询) - 2小时
- [ ] 创建查询函数分组
- [ ] 重构主查询函数
- [ ] 完整测试
- 预期: 5313ms → 2813ms

### Phase 3: 缓存实现 - 1小时
- [ ] 实现 cached_query 装饰器
- [ ] 应用到查询函数
- [ ] 添加监控
- 预期: 2813ms → 879ms

### Phase 4: 数据库优化 - 30分钟
- [ ] 创建新索引
- [ ] 验证使用情况
- [ ] EXPLAIN ANALYZE 确认
- 预期: 879ms → 654ms

### Phase 5: 测试验证 - 1小时
- [ ] E2E测试
- [ ] 性能基准对比
- [ ] 文档更新

---

## 📋 实现清单

| 文件 | 修改内容 | 优先级 |
|------|---------|-------|
| shared/data_access/edge_query.py | 连接池 + 分离查询 + 缓存 | P1 |
| database/migrations/005_optimize_edge_query_indexes.sql | 新索引 | P2 |
| api/services/control_strategy_service.py | 移除重复缓存 | P2 |

---

## 🎯 成功标准

| 指标 | 目标 |
|------|------|
| 查询响应时间 | <2000ms (首次) / <100ms (缓存) |
| 缓存命中率 | >70% |
| 索引使用率 | 100% |
| 功能完整性 | 100% (所有过滤条件) |
| 回归测试 | 0失败 |

---

**计划完成日期**: 2025-11-02
**优化负责人**: Claude Code + 开发团队
