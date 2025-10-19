# 边选择器特殊场景适用性分析

**问题1**: 收费入口管控需要根据TAZ选择入口边，边选择器还有效吗？
**问题2**: 动态硬路肩需要选择具备应急车道的主路，如何选择？

---

## 快速答案

### ✅ 问题1: 收费入口管控 - **边选择器完全有效**

**答案**: **有效 ✅**，现有边选择器已经支持，无需额外开发！

**立即可用的方法**：
```python
from shared.data_access.edge_query import query_edges_with_filters

# 筛选G4202路线的所有入口边
entrance_edges = query_edges_with_filters(
    route_codes=["G4202"],
    node_types=["entrance"]  # ✅ 已支持
)

# 结果：找到所有入口边，包括：
# - 入口匝道（highway.motorway_link）
# - 主路接入点（highway.motorway）
```

**数据支持**：
- ✅ `multiscale_node_units` 表有 `node_type='entrance'`
- ✅ 实测找到15+个入口边
- ✅ TAZ映射表存在（`dim.taz_demonstration_mapping`，461条记录）

**如果需要TAZ筛选**（可选增强）：
```python
# 方法1: 通过示范段间接筛选TAZ
edges = query_edges_with_filters(
    demonstration_ids=[1],  # TAZ关联的示范段ID
    node_types=["entrance"]
)

# 方法2: 新增函数（需要开发）
edges = query_edges_by_taz(
    taz_ids=["G00055100200104010"],
    source_types=["toll_square"]  # 收费广场
)
```

---

### △ 问题2: 动态硬路肩管控 - **边选择器基本有效，需要扩展**

**答案**: **部分有效 △**，可以筛选主路，但应急车道识别需要扩展。

---

#### 方案A: 基于车道数推断（立即可用，推荐用于测试）

```python
# 筛选可能有应急车道的主路（≥5车道）
dhs_edges = query_edges_with_filters(
    route_codes=["G4202"],
    section_codes=["G4202001"],
    min_lanes=5,              # ≥5车道很可能有应急车道
    min_length=800,           # 足够长
    route_direction="clockwise"
)

# 还需添加edge_types参数（简单扩展）
dhs_edges = query_edges_with_filters(
    ...,
    edge_types=["highway.motorway"]  # 筛选主路（需新增此参数）
)
```

**优点**：
- ✅ 简单直接
- ✅ 现有数据即可支持

**缺点**：
- ⚠️ 不够精确（基于推断）
- ⚠️ 无法明确哪个车道是应急车道

---

#### 方案B: 关联车道表精确识别（推荐用于生产）

**数据支持**：
- ✅ `sim_network_lanes` 表存在（车道级别配置）
- ✅ 有 `disallow` 字段（应急车道通常disallow="all"）
- ✅ 实测找到大量5-6车道的主路

**新增查询函数**：
```python
def query_edges_with_emergency_lanes(
    route_codes: Optional[List[str]] = None,
    section_codes: Optional[List[str]] = None,
    route_direction: Optional[str] = None,
    min_stake: Optional[float] = None,
    max_stake: Optional[float] = None,
    min_length: Optional[float] = None
) -> List[EdgeInfoWithLanes]:
    """
    筛选具备应急车道的边

    Args:
        route_codes: 路线编码列表
        section_codes: 路段编码列表
        route_direction: 方向（clockwise/counterclockwise）
        min_stake: 最小桩号
        max_stake: 最大桩号
        min_length: 最小长度

    实现逻辑:
    1. type = 'highway.motorway' (主路)
    2. num_lanes >= 3
    3. JOIN sim_network_lanes 检查 disallow='all' 的车道
    """
    # 关联sim_network_lanes表，识别应急车道
    ...
```

**使用示例**：
```python
# 精确筛选有应急车道的主路
dhs_edges = query_edges_with_emergency_lanes(
    route_codes=["G4202"],
    section_codes=["G4202001"],
    route_direction="clockwise",  # 方向筛选
    min_stake=10.0,
    max_stake=50.0,
    min_length=800
)

# 返回结果包含应急车道信息
for edge in dhs_edges:
    print(f"边ID: {edge.edge_id}")
    print(f"总车道数: {edge.num_lanes}")
    print(f"应急车道数: {edge.emergency_lane_count}")
    print(f"应急车道索引: {edge.emergency_lane_indexes}")  # 如 [0] 或 [4]
```

---

#### 方案C: 数据库预处理（长期方案）

```sql
-- 在sim_network_edges表中新增字段
ALTER TABLE dim.sim_network_edges
ADD COLUMN has_emergency_lane BOOLEAN,
ADD COLUMN emergency_lane_indexes INTEGER[];

-- 预处理脚本标记应急车道
UPDATE dim.sim_network_edges e
SET has_emergency_lane = TRUE, ...
WHERE EXISTS (
    SELECT 1 FROM dim.sim_network_lanes l
    WHERE l.edge_id = e.edge_id AND l.disallow LIKE '%all%'
);
```

**使用**：
```python
# 直接筛选
dhs_edges = query_edges_with_filters(
    route_codes=["G4202"],
    has_emergency_lane=True  # 新增参数
)
```

---

## 实现清单

### 场景1: 收费入口管控（TEC）

| 任务 | 优先级 | 工作量 | 状态 |
|------|-------|--------|-----|
| 使用现有`node_types=["entrance"]` | P0 | 0天 | ✅ 立即可用 |
| 新增`edge_types`参数 | P1 | 0.5天 | 📋 可选 |
| 新增`query_edges_by_taz()`函数 | P2 | 1天 | 📋 可选 |

**结论**: ✅ **立即可用，无需任何开发**

---

### 场景2: 动态硬路肩管控（DHS）

| 任务 | 优先级 | 工作量 | 状态 |
|------|-------|--------|-----|
| **短期方案** | | | |
| 新增`edge_types`参数 | P0 | 0.5天 | 📋 推荐 |
| 基于`min_lanes≥5`推断 | P0 | 0天 | ✅ 立即可用 |
| | | | |
| **中期方案（推荐）** | | | |
| 新增`query_edges_with_emergency_lanes()` | P1 | 1-2天 | 📋 推荐 |
| 新增`EdgeInfoWithLanes`数据模型 | P1 | 0.5天 | 📋 推荐 |
| | | | |
| **长期方案** | | | |
| 数据库添加`has_emergency_lane`字段 | P2 | 0.5天 | 📋 可选 |
| 预处理脚本标记应急车道 | P2 | 1天 | 📋 可选 |

**结论**: △ **基本可用（推断），推荐扩展（精确识别）**

---

## 测试验证

### 场景1测试（入口边筛选）

```bash
# 运行测试
python tests/test_special_scenarios.py

# 预期结果：
# ✅ 找到15+个entrance类型的边
# ✅ 主要类型：highway.motorway_link
# ✅ 覆盖SA2、G5、G4202等路线
```

### 场景2测试（主路应急车道）

```bash
# 运行测试
python tests/test_detailed_scenarios.py

# 预期结果：
# ✅ 找到20+个主路边（≥3车道）
# ✅ G4202路线有5-6车道的主路
# ✅ sim_network_lanes表有车道配置
```

---

## 推荐方案总结

### 🎯 收费入口管控（TEC）

**推荐**: **使用现有边选择器** ⭐⭐⭐⭐⭐

```python
# 立即可用，无需修改
entrance_edges = query_edges_with_filters(
    route_codes=["G4202"],
    section_codes=["G4202001"],
    node_types=["entrance"],
    min_stake=10.0,
    max_stake=50.0
)
```

---

### 🎯 动态硬路肩管控（DHS）

**推荐**: **短期用推断，中期扩展精确识别** ⭐⭐⭐⭐

**Phase 1（立即可用）**:
```python
# 基于车道数推断
dhs_edges = query_edges_with_filters(
    route_codes=["G4202"],
    min_lanes=5,  # 5车道+很可能有应急车道
    edge_types=["highway.motorway"]  # 需添加此参数（0.5天）
)
```

**Phase 2（1-2周后）**:
```python
# 精确识别应急车道
dhs_edges = query_edges_with_emergency_lanes(
    route_codes=["G4202"],
    min_stake=10.0,
    max_stake=50.0
)
```

---

## 相关文档导航

### 核心文档
- 📘 **边选择器数据库设计**: [edge_selector_database_design.md](edge_selector_database_design.md) - 总体设计（v1.1）
- 📗 **边选择器测试报告**: [edge_selector_test_report.md](edge_selector_test_report.md) - 功能验证（v1.1）

### 特殊场景文档
- 📕 **快速答案**（本文档）: [edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md) - TEC/DHS立即可用方案
- 📙 **详细方案**: [edge_selector_special_scenarios.md](edge_selector_special_scenarios.md) - TEC/DHS完整实现方案

### 测试脚本
- 🧪 基础筛选测试: [tests/test_edge_selector_simple.py](../../tests/test_edge_selector_simple.py)
- 🧪 路段筛选测试: [tests/test_section_filter.py](../../tests/test_section_filter.py)
- 🧪 **特殊场景分析**: [tests/test_special_scenarios.py](../../tests/test_special_scenarios.py) ⭐
- 🧪 **深入场景分析**: [tests/test_detailed_scenarios.py](../../tests/test_detailed_scenarios.py) ⭐

### 代码实现
- 💻 查询模块: [shared/data_access/edge_query.py](../../shared/data_access/edge_query.py)

### 开发路线图
```
Phase 1A（已完成）
├─ 基础9维度筛选 ✅
├─ TEC收费入口管控支持 ✅
└─ 测试验证 ✅

Phase 1B（规划中）
├─ edge_types参数（P0，0.5天）📋
├─ query_edges_with_emergency_lanes()（P1，1-2天）📋
└─ query_edges_by_taz()（P2，可选）📋

Phase 2（未来）
└─ 数据库优化和预处理 📋
```

---

**结论版本**: v1.0
**最后更新**: 2025-10-19
**维护者**: OD_SIM开发团队
