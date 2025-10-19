# 边选择器特殊场景支持方案

**版本**: v1.0
**创建日期**: 2025-10-19
**场景**: TEC收费入口管控 + DHS动态硬路肩管控

---

## 1. 场景需求分析

### 场景1: 收费入口管控（TEC - Toll Entrance Control）

**业务需求**：
- 根据TAZ（交通分析区）选择入口处的边
- 控制特定入口的流量
- 通常针对收费广场（toll square）或入口匝道

**技术挑战**：
- TAZ与边的映射关系
- 入口边的准确识别

---

### 场景2: 动态硬路肩管控（DHS - Dynamic Hard Shoulder）

**业务需求**：
- 选择具备应急车道的主路
- 应急车道默认禁止所有车辆通行（disallow="all"）
- 通过策略动态开放应急车道

**技术挑战**：
- 应急车道的识别（车道级别信息）
- 主路与匝道的区分

---

## 2. 数据库现状分析

### 2.1 现有数据支持 ✅

#### TAZ映射表（dim.taz_demonstration_mapping）

**表结构**：
| 字段 | 类型 | 说明 |
|------|------|------|
| taz_id | text | TAZ标识（来自门架或收费广场） |
| source_type | text | 来源类型（gantry/toll_square） |
| source_id | text | 来源ID（门架ID或收费广场ID） |
| demonstration_id | integer | 示范段ID |
| demonstration_route_code | text | 路线编码 |
| demonstration_route_name | text | 路线名称 |

**数据规模**：461条记录，覆盖8个示范段

**示例数据**：
```
taz_id: G00055100200104010
source_type: toll_square
source_id: G00055100200104010
demonstration_id: 1
demonstration_route_code: G5
```

---

#### 车道配置表（dim.sim_network_lanes）

**表结构**：
| 字段 | 类型 | 说明 |
|------|------|------|
| lane_id | varchar | 车道ID |
| edge_id | varchar | 关联的边ID |
| lane_index | integer | 车道索引（0开始） |
| speed | double precision | 限速（m/s） |
| length | double precision | 车道长度（米） |
| disallow | text | 禁止通行的车辆类型 |
| shape | text | 车道形状（坐标串） |

**关键发现**：
- ✅ 有车道级别配置
- ✅ 有disallow字段（可用于识别应急车道）
- ❌ 无width字段
- ❌ 无allow字段

---

### 2.2 入口边特征分析

**节点类型筛选**：
```sql
SELECT e.*
FROM dim.sim_network_edges e
JOIN dim.multiscale_node_units n
  ON e.from_junction::varchar = n.junction_id
WHERE n.node_type = 'entrance'
```

**边类型特征**：
- type = `highway.motorway_link` (入口匝道)
- type = `highway.motorway` (主路接入点)

**实际数据**：
- 找到15+个入口边
- 主要分布在SA2、G5、G4202等路线
- 大部分是1车道（匝道），少数是3车道（主路接入）

---

### 2.3 主路应急车道特征

**主路特征**：
```sql
SELECT e.*
FROM dim.sim_network_edges e
WHERE e.type = 'highway.motorway'
  AND e.num_lanes >= 3
```

**车道数量分布**（G4202示例）：
- 6车道: 1条边
- 5车道: 18条边
- 4车道: 众多
- 3车道: 大量

**推断规则**：
- 5-6车道的主路 → 很可能有应急车道
- 3-4车道的主路 → 可能有应急车道
- disallow字段 → 需要检查实际值

---

## 3. 解决方案

### 3.1 场景1: 收费入口管控 ✅ **完全支持**

#### 方案A: 基于节点类型筛选（推荐）

```python
from shared.data_access.edge_query import query_edges_with_filters

# 筛选G4202路线的所有入口边
entrance_edges = query_edges_with_filters(
    route_codes=["G4202"],
    node_types=["entrance"]  # ✅ 已支持
)
```

**优点**：
- ✅ 直接使用现有边选择器
- ✅ 节点类型明确（entrance）
- ✅ 无需额外开发

---

#### 方案B: 基于TAZ筛选（需扩展）

**扩展查询函数**：
```python
def query_edges_by_taz(
    taz_ids: List[str] = None,
    source_types: List[str] = None,  # gantry, toll_square
    demonstration_ids: List[int] = None
) -> List[EdgeInfo]:
    """
    根据TAZ筛选边

    实现思路:
    1. 从taz_demonstration_mapping表获取TAZ关联的demonstration_id
    2. 从sim_network_edges筛选对应示范段的边
    3. 结合node_type='entrance'精确定位入口边
    """

    conn = open_db_connection()
    cur = conn.cursor()

    sql = """
        SELECT DISTINCT
            e.edge_id,
            e.route_code,
            e.section_code,
            e.start_stake,
            e.end_stake,
            e.num_lanes,
            n.node_type,
            t.taz_id,
            t.source_type
        FROM dim.sim_network_edges e
        JOIN dim.taz_demonstration_mapping t
          ON e.demonstration_id = t.demonstration_id
        LEFT JOIN dim.multiscale_node_units n
          ON e.from_junction::varchar = n.junction_id
        WHERE n.node_type = 'entrance'
    """

    params = []

    if taz_ids:
        sql += " AND t.taz_id = ANY(%s)"
        params.append(taz_ids)

    if source_types:
        sql += " AND t.source_type = ANY(%s)"
        params.append(source_types)

    if demonstration_ids:
        sql += " AND t.demonstration_id = ANY(%s)"
        params.append(demonstration_ids)

    sql += " ORDER BY e.route_code, e.start_stake"

    cur.execute(sql, params)
    # ... 处理结果
```

**使用示例**：
```python
# 筛选指定TAZ的入口边
edges = query_edges_by_taz(
    taz_ids=["G00055100200104010"],  # 具体的TAZ ID
    source_types=["toll_square"]      # 仅收费广场
)

# 或按示范段筛选
edges = query_edges_by_taz(
    demonstration_ids=[1],            # 示范段1（G5）
    source_types=["toll_square", "gantry"]
)
```

---

#### 方案C: 基于边类型筛选（补充）

**扩展边选择器参数**：
```python
edges = query_edges_with_filters(
    route_codes=["G4202"],
    edge_types=["highway.motorway_link"],  # 新增参数 ⭐
    node_types=["entrance"]
)
```

**实现**：在`edge_query.py`中添加：
```python
def query_edges_with_filters(
    ...,
    edge_types: Optional[List[str]] = None,  # 新增
    ...
):
    # ...
    if edge_types:
        sql += " AND e.type = ANY(%s)"
        params.append(edge_types)
```

---

### 3.2 场景2: 动态硬路肩管控 △ **部分支持，需扩展**

#### 方案A: 基于车道数推断（当前可用）

```python
# 筛选可能有应急车道的主路
mainroad_edges = query_edges_with_filters(
    route_codes=["G4202"],
    section_codes=["G4202001"],
    edge_types=["highway.motorway"],    # 新增参数
    min_lanes=5,                        # ≥5车道很可能有应急车道
    min_length=500,                     # 足够长的路段
    route_direction="clockwise"
)
```

**优点**：
- ✅ 现有数据即可支持（添加edge_types参数）
- ✅ 简单直接

**缺点**：
- ⚠️ 不够精确（基于推断）
- ⚠️ 可能遗漏或误判

---

#### 方案B: 关联车道表精确识别（推荐）

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
        min_stake: 最小桩号（公里）
        max_stake: 最大桩号（公里）
        min_length: 最小长度（米）

    识别规则:
    1. type = 'highway.motorway' (主路)
    2. num_lanes >= 3 (至少3车道)
    3. sim_network_lanes中存在disallow='all'的车道
    """

    conn = open_db_connection()
    cur = conn.cursor()

    sql = """
        SELECT
            e.edge_id,
            e.route_code,
            e.section_code,
            e.start_stake,
            e.end_stake,
            e.num_lanes,
            e.length,
            e.route_direction,
            COUNT(l.lane_index) as total_lane_configs,
            COUNT(CASE WHEN l.disallow LIKE '%all%' THEN 1 END) as emergency_lane_count,
            STRING_AGG(
                CASE WHEN l.disallow LIKE '%all%' THEN l.lane_index::text END,
                ','
            ) as emergency_lane_indexes
        FROM dim.sim_network_edges e
        JOIN dim.sim_network_lanes l
          ON e.edge_id = l.edge_id
        WHERE e.type = 'highway.motorway'
          AND e.num_lanes >= 3
    """

    params = []

    if route_codes:
        sql += " AND e.route_code = ANY(%s)"
        params.append(route_codes)

    if section_codes:
        sql += " AND e.section_code = ANY(%s)"
        params.append(section_codes)

    if route_direction:
        sql += " AND e.route_direction = %s"
        params.append(route_direction)

    if min_stake is not None:
        sql += " AND e.start_stake >= %s"
        params.append(min_stake)

    if max_stake is not None:
        sql += " AND e.end_stake <= %s"
        params.append(max_stake)

    if min_length is not None:
        sql += " AND e.length >= %s"
        params.append(min_length)

    sql += """
        GROUP BY e.edge_id, e.route_code, e.section_code,
                 e.start_stake, e.end_stake, e.num_lanes,
                 e.length, e.route_direction
        HAVING COUNT(CASE WHEN l.disallow LIKE '%all%' THEN 1 END) > 0
        ORDER BY e.route_code, e.start_stake
    """

    cur.execute(sql, params)
    # ... 处理结果
```

**数据模型扩展**：
```python
@dataclass
class EdgeInfoWithLanes(EdgeInfo):
    """带车道信息的边"""
    total_lane_configs: int = 0          # 车道配置总数
    emergency_lane_count: int = 0        # 应急车道数量
    emergency_lane_indexes: List[int] = None  # 应急车道索引列表

    def __post_init__(self):
        super().__post_init__()
        if self.emergency_lane_indexes is None:
            self.emergency_lane_indexes = []
```

**使用示例**：
```python
# 筛选G4202顺时针方向K10-K50的应急车道路段
dhs_edges = query_edges_with_emergency_lanes(
    route_codes=["G4202"],
    section_codes=["G4202001"],
    route_direction="clockwise",  # 方向筛选
    min_stake=10.0,
    max_stake=50.0,
    min_length=800  # 至少800米
)

for edge in dhs_edges:
    print(f"边ID: {edge.edge_id}")
    print(f"车道数: {edge.num_lanes}")
    print(f"应急车道数: {edge.emergency_lane_count}")
    print(f"应急车道索引: {edge.emergency_lane_indexes}")
```

---

#### 方案C: 预处理标记（生产环境推荐）

**数据库扩展**：
```sql
-- 在sim_network_edges表中新增字段
ALTER TABLE dim.sim_network_edges
ADD COLUMN has_emergency_lane BOOLEAN DEFAULT FALSE,
ADD COLUMN emergency_lane_count INTEGER DEFAULT 0,
ADD COLUMN emergency_lane_indexes INTEGER[];

-- 预处理脚本：标记应急车道
UPDATE dim.sim_network_edges e
SET
    has_emergency_lane = TRUE,
    emergency_lane_count = subq.emergency_count,
    emergency_lane_indexes = subq.lane_indexes
FROM (
    SELECT
        edge_id,
        COUNT(*) as emergency_count,
        ARRAY_AGG(lane_index) as lane_indexes
    FROM dim.sim_network_lanes
    WHERE disallow LIKE '%all%'
    GROUP BY edge_id
) subq
WHERE e.edge_id = subq.edge_id;
```

**使用**：
```python
# 直接使用扩展后的边选择器
dhs_edges = query_edges_with_filters(
    route_codes=["G4202"],
    has_emergency_lane=True,  # 新增布尔参数
    min_lanes=3
)
```

---

## 4. 推荐实现方案

### 4.1 场景1: 收费入口管控

**推荐方案**: **方案A（基于节点类型）** ⭐

**理由**：
- ✅ 现有边选择器已支持`node_types`参数
- ✅ 无需额外开发
- ✅ 筛选结果准确

**实现清单**：
- [x] 使用现有`query_edges_with_filters(node_types=["entrance"])`
- [ ] 可选：新增`edge_types`参数过滤`highway.motorway_link`
- [ ] 可选：新增`query_edges_by_taz()`函数支持TAZ筛选

---

### 4.2 场景2: 动态硬路肩管控

**推荐方案**: **方案B（关联车道表）短期 + 方案C（预处理标记）长期** ⭐

**理由**：
- ✅ 方案B：精确识别应急车道，可立即实现
- ✅ 方案C：性能最优，适合生产环境

**实现清单**：
- [ ] **Phase 1（短期）**：
  - [ ] 新增`edge_types`参数到`query_edges_with_filters()`
  - [ ] 新增`query_edges_with_emergency_lanes()`函数
  - [ ] 新增`EdgeInfoWithLanes`数据模型
- [ ] **Phase 2（长期）**：
  - [ ] 数据库添加`has_emergency_lane`等字段
  - [ ] 编写预处理脚本标记应急车道
  - [ ] 更新边选择器支持`has_emergency_lane`参数

---

## 5. API设计

### 5.1 收费入口管控API

```python
# GET /api/v1/control/edges/entrance
@router.get("/edges/entrance")
def query_entrance_edges(
    route_codes: Optional[str] = Query(None, description="路线编码"),
    section_codes: Optional[str] = Query(None, description="路段编码"),
    taz_ids: Optional[str] = Query(None, description="TAZ ID列表"),
    source_types: Optional[str] = Query(None, description="TAZ来源类型"),
    min_stake: Optional[float] = Query(None, description="最小桩号"),
    max_stake: Optional[float] = Query(None, description="最大桩号")
) -> EdgeQueryResponse:
    """筛选收费入口边"""

    # 解析参数
    route_codes_list = route_codes.split(",") if route_codes else None
    section_codes_list = section_codes.split(",") if section_codes else None

    # 基础筛选
    edges = query_edges_with_filters(
        route_codes=route_codes_list,
        section_codes=section_codes_list,
        node_types=["entrance"],
        min_stake=min_stake,
        max_stake=max_stake
    )

    # 可选：TAZ筛选
    if taz_ids:
        taz_ids_list = taz_ids.split(",")
        edges = filter_by_taz(edges, taz_ids_list)

    return EdgeQueryResponse(edges=edges, total_count=len(edges))
```

---

### 5.2 动态硬路肩管控API

```python
# GET /api/v1/control/edges/hardShoulder
@router.get("/edges/hardShoulder")
def query_hard_shoulder_edges(
    route_codes: Optional[str] = Query(None, description="路线编码"),
    section_codes: Optional[str] = Query(None, description="路段编码"),
    route_direction: Optional[str] = Query(None, description="方向"),
    min_stake: Optional[float] = Query(None, description="最小桩号"),
    max_stake: Optional[float] = Query(None, description="最大桩号"),
    min_length: Optional[float] = Query(None, description="最小长度"),
    min_lanes: Optional[int] = Query(3, description="最小车道数")
) -> EdgeQueryResponse:
    """筛选动态硬路肩边"""

    # 解析参数
    route_codes_list = route_codes.split(",") if route_codes else None
    section_codes_list = section_codes.split(",") if section_codes else None

    # 使用应急车道专用查询函数
    edges = query_edges_with_emergency_lanes(
        route_codes=route_codes_list,
        section_codes=section_codes_list,
        min_stake=min_stake,
        max_stake=max_stake,
        min_length=min_length
    )

    return EdgeQueryResponse(edges=edges, total_count=len(edges))
```

---

## 6. 总结

### 6.1 边选择器有效性评估

| 场景 | 当前边选择器 | 需要扩展 | 可行性 |
|------|-------------|---------|-------|
| **收费入口管控（TEC）** | ✅ 基本支持 | 可选（TAZ筛选） | **完全可行** ⭐⭐⭐⭐⭐ |
| **动态硬路肩管控（DHS）** | △ 部分支持 | 必需（车道关联） | **基本可行** ⭐⭐⭐⭐ |

---

### 6.2 开发优先级

#### P0 - 立即可用（无需开发）
- ✅ TEC场景：使用`node_types=["entrance"]`筛选入口边

#### P1 - 短期增强（1-2天）
- 新增`edge_types`参数（扩展边类型筛选）
- 新增`query_edges_with_emergency_lanes()`函数

#### P2 - 中期优化（1周）
- 新增`query_edges_by_taz()`函数（支持TAZ筛选）
- 完善车道信息返回

#### P3 - 长期完善（后续版本）
- 数据库预处理应急车道标记
- 性能优化和缓存

---

### 6.3 数据质量建议

**确认事项**：
1. ✅ 检查`sim_network_lanes.disallow`字段的实际值
2. ✅ 验证应急车道的标识规则
3. ✅ 确认TAZ与边的映射准确性

**数据增强建议**：
1. 预处理标记应急车道（`has_emergency_lane`字段）
2. 建立TAZ-Edge直接映射表（提升查询性能）
3. 补充车道宽度信息（如果SUMO网络文件中有）

---

---

## 7. 相关文档导航

### 📖 阅读顺序建议

**新手开发者**：
1. 📕 [edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md) - 快速了解TEC/DHS场景
2. 📘 [edge_selector_database_design.md](edge_selector_database_design.md) - 理解数据库设计
3. 📙 本文档 - 深入理解实现方案

**经验开发者**：
1. 📙 本文档 - 直接查看详细方案
2. 🧪 测试脚本 - 验证数据支持

### 📚 文档清单

**核心设计文档**：
- [edge_selector_database_design.md](edge_selector_database_design.md) - 数据库设计总览（v1.1，含特殊场景）
- [edge_selector_test_report.md](edge_selector_test_report.md) - 测试报告（v1.1，9种维度验证）

**特殊场景文档**：
- [edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md) - 快速答案（TEC/DHS立即可用方案）⭐
- 本文档 - 详细实现方案（TEC/DHS完整设计）⭐

**测试验证**：
- [tests/test_special_scenarios.py](../../tests/test_special_scenarios.py) - 数据库现状分析
- [tests/test_detailed_scenarios.py](../../tests/test_detailed_scenarios.py) - 深入场景验证

**代码实现**：
- [shared/data_access/edge_query.py](../../shared/data_access/edge_query.py) - 核心查询模块

---

**文档版本**: v1.0
**最后更新**: 2025-10-19
**维护者**: OD_SIM开发团队
