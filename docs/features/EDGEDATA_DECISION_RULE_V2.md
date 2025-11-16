# EdgeData智能决策规则升级 (P2 v2)

**日期**: 2025-11-15
**变更**: 修改EdgeData启用决策规则
**版本**: P2 修复 v2
**状态**: ✅ 完成

---

## 问题与需求

### 用户反馈
```
case_event_10814的EdgeData配置：
- 边缘数: 2条（< 10条最小阈值）
- 验证率: 50%（= 50%最小阈值）
- 输出状态: ❌ 禁用

即使有验证通过的边，也被禁用了。
请改为：只要有验证通过的edge_id就生成，保证有输出。
```

### 根本需求
**"保证有有价值的EdgeData输出"**

即使边数较少，只要有验证通过的边，就应该生成EdgeData分析，不要完全禁用。

---

## 规则变更

### 原规则 (P2 v1) - 同时满足

```python
should_enable = (edge_count >= 10) AND (validation_rate >= 0.5)
```

**两个条件都要满足**：
- ✅ 边数 >= 10
- ✅ 验证率 >= 50%

**问题**：两个条件是AND关系，任何一个不满足就禁用输出，太严格了。

### 新规则 (P2 v2) - 只需有验证通过的边

```python
should_enable = edge_count > 0
```

**只需一个条件**：
- ✅ 有验证通过的边 (edge_count > 0)

**逻辑**：edge_count > 0 意味着确实有已验证的边，值得生成EdgeData分析。

---

## 实际影响

### case_event_10814 - 从"禁用"变为"启用"

#### 修改前 (P2 v1)
```
EdgeData配置:
  - edge_count: 2
  - validation_rate: 50%

判断:
  - edge_count >= 10? ❌ 否 (2 < 10)
  - validation_rate >= 50%? ✓ 是 (50% = 50%)

决策: 禁用 (因为2 < 10) ❌
```

#### 修改后 (P2 v2)
```
EdgeData配置:
  - edge_count: 2
  - validation_rate: 50%

判断:
  - edge_count > 0? ✓ 是 (2 > 0)

决策: 启用 (有2条已验证的边) ✅
输出消息: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)"
```

### 适用于所有类似情况

所有满足以下条件的cases都会改为启用：
```
edge_count > 0 (有验证通过的边)
```

---

## 代码改动

**文件**: `shared/utilities/sumo_utils.py`
**函数**: `should_enable_edgedata_output()`
**第15-87行**

### 核心逻辑变更

```python
# 修改前（v1）
edge_count_ok = edge_count >= min_edge_threshold      # >= 10
validation_ok = validation_rate >= min_validation_rate # >= 0.5
should_enable = edge_count_ok and validation_ok       # 两个都要满足

# 修改后（v2）
has_verified_edges = edge_count > 0                   # 只要 > 0
should_enable = has_verified_edges                    # 只需一个条件
```

### 日志输出改进

修改前：
```
EdgeData决策: 边缘数量不足 (2/10) + 验证通过率过低 (50.0%/50.0%)
  - ❌ 禁用edgedata输出 (仅输出summary.xml)
```

修改后：
```
EdgeData决策 (P2 v2): Have verified edges (2), enable output for analysis
  - ✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)
```

---

## 向后兼容性

✅ **完全向后兼容**

函数签名不变：
```python
def should_enable_edgedata_output(
    edge_count: int,
    validation_rate: float,
    min_edge_threshold: int = 10,          # 保留但不使用
    min_validation_rate: float = 0.5       # 保留但不使用
) -> tuple[bool, Dict[str, Any]]:
```

所有调用代码无需修改，只是决策结果会不同。

---

## 决策对比表

### 不同边缘数和验证率的情况

| edge_count | validation_rate | P2 v1 | P2 v2 | 说明 |
|-----------|-----------------|-------|-------|------|
| 0 | 0% | ❌ 禁用 | ❌ 禁用 | 无验证边，都禁用 |
| 1 | 100% | ❌ 禁用 | ✅ 启用 | P2 v1太严格 |
| 2 | 50% | ❌ 禁用 | ✅ 启用 | case_event_10814 |
| 5 | 80% | ❌ 禁用 | ✅ 启用 | 少数边但质量高 |
| 10 | 50% | ✅ 启用 | ✅ 启用 | 刚好满足两个条件 |
| 10 | 40% | ❌ 禁用 | ✅ 启用 | P2 v2更宽松 |
| 100 | 95% | ✅ 启用 | ✅ 启用 | 高质量，都启用 |

**核心区别**：P2 v2 在 edge_count > 0 的情况下全部启用，不再关心 min_edge_threshold。

---

## 用户影响分析

### 哪些cases会受到影响？

原本被禁用，现在启用的cases：
```
情况1: edge_count > 0 但 edge_count < 10
       → 原因：数据量少，但有验证通过的边

情况2: validation_rate < 50%
       → 原因：验证通过率低，但有一些边被验证
```

### EdgeData输出的价值

即使只有2-5条边，仍然可以提供：
- ✅ 事件影响范围的基本认知（哪些道路受到影响）
- ✅ 交通流量的初步观察（流量变化方向）
- ✅ 优化决策的参考（控制效果分析）

虽然不如10条以上的数据全面，但比完全禁用更有价值。

---

## 测试验证

### 验证清单

✅ **代码层面**
- [x] Python语法检查通过
- [x] 函数逻辑正确
- [x] 向后兼容性保证
- [x] 日志输出改进

✅ **功能层面**
- [x] edge_count > 0 时启用
- [x] edge_count == 0 时禁用
- [x] 决策信息准确

✅ **预期行为**
- case_event_10814: ✗ 禁用 → ✅ 启用 (with 2 edges)
- 类似cases: ✗ 禁用 → ✅ 启用

---

## 后续建议

### 短期（立即实施）
- ✅ 已完成本次修改

### 中期（下个版本）
1. 考虑添加配置参数
   ```python
   # 允许用户自定义最小边数
   edge_count_threshold = config.get('edge_count_min', 1)
   should_enable = edge_count >= edge_count_threshold
   ```

2. 添加边质量评分
   ```python
   # 考虑边的平均验证率
   edge_quality_score = sum(validated_count) / total_edges
   should_enable = edge_count > 0 and edge_quality_score > threshold
   ```

### 长期（Phase 2+）
1. 实现动态阈值
   - 根据网络规模自动调整

2. 添加分级输出
   - 不再完全禁用/启用，而是分"完整输出"和"简化输出"两级

---

## 总结

### 规则变更简述

| 项目 | P2 v1 | P2 v2 |
|------|-------|-------|
| 决策规则 | edge_count >= 10 AND validation_rate >= 50% | edge_count > 0 |
| 复杂度 | 中等 (两个条件AND) | 简洁 (一个条件) |
| 输出保证 | 严格 (两个都满足才启用) | 宽松 (有边就启用) |
| case_event_10814 | ❌ 禁用 | ✅ 启用 (2 edges) |

### 核心改进

✅ 避免因边数不足而完全禁用分析
✅ 保证只要有验证通过的边就提供输出
✅ 用户能获得有价值的分析结果，而不是空白输出

**系统状态**: 🟢 **P2规则升级完成，EdgeData输出更有保障**

---

## 相关文件变更

| 文件 | 修改 | 行数 |
|------|------|------|
| shared/utilities/sumo_utils.py | 修改should_enable_edgedata_output() | 15-87 |

**总计**: 约70行代码变更（简化 + 完善日志说明）
