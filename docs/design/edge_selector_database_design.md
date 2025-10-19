# 边选择器数据库设计方案

**版本**: v1.0
**创建日期**: 2025-10-19
**数据库**: sdzg, dim schema

---

## 1. 核心表结构

### 1.1 dim.sim_network_edges（路段表）⭐核心

**用途**：SUMO路网边缘数据，是边选择器的主数据源

**关键字段**：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| edge_id | varchar(255) | 路段ID（SUMO edge ID） |
| from_junction | varchar(255) | 起点junction ID |
| to_junction | varchar(255) | 终点junction ID |
| route_code | varchar(20) | 路线编码（G4202, G5, SA2等） |
| section_code | varchar(20) | 路段编码 |
| demonstration_id | integer | 示范段ID |
| start_stake | numeric | 起点桩号（公里） |
| end_stake | numeric | 终点桩号（公里） |
| route_direction | varchar(20) | 方向（clockwise/counterclockwise） |
| length | double precision | 路段长度（米） |
| num_lanes | integer | 车道数 |
| function | varchar(50) | 功能类型（normal等） |
| type | varchar(100) | 道路类型（highway.motorway等） |

**样例数据**：
```
edge_id: -582
from_junction: -25367, to_junction: -25372
route_code: SA2, section_code: SA002002
start_stake: 211.435, end_stake: 210.711
route_direction: counterclockwise
length: 723.63, num_lanes: 3
```

---

### 1.2 dim.multiscale_node_units（节点单元表）⭐重要

**用途**：多尺度节点聚合，包含节点类型和连接的路段信息

**关键字段**：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| unit_id | varchar(50) | 节点单元ID |
| unit_name | varchar(100) | 节点名称 |
| junction_id | varchar(50) | junction ID |
| node_type | varchar(20) | 节点类型（diverging/merging/entrance/exit等） |
| route_code | varchar(20) | 路线编码 |
| section_code | varchar(50) | 路段编码 |
| demonstration_id | integer | 示范段ID |
| stake_number | numeric | 桩号 |
| in_edge_count | integer | 入边数量 |
| out_edge_count | integer | 出边数量 |
| connected_edge_ids | array | 连接的路段ID列表 |

**节点类型说明**：
- `diverging`: 分流点（出边 > 入边）
- `merging`: 汇流点（入边 > 出边）
- `entrance`: 入口匝道节点
- `exit`: 出口匝道节点

**样例数据**：
```
unit_id: 1929482403_dive
junction_id: 1929482403
node_type: diverging
route_code: G76
in_edge_count: 1, out_edge_count: 2
connected_edge_ids: ['-2000000020', ...]
```

---

### 1.3 dim.sim_network_junctions（节点表）

**用途**：SUMO junction节点数据

**关键字段**：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| junction_id | varchar(255) | junction ID |
| junction_type | varchar(50) | 节点类型（priority等） |
| route_code | varchar(20) | 路线编码 |
| section_code | varchar(20) | 路段编码 |
| stake_number | numeric | 桩号 |
| route_direction | varchar(20) | 方向 |
| longitude | double precision | 经度 |
| latitude | double precision | 纬度 |

---

### 1.4 dim.point_gantry（门架点表）

**用途**：门架位置信息，可用于关联路段上的门架

**关键字段**：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| gantry_id | varchar(255) | 门架ID |
| gantry_name | varchar(255) | 门架名称 |
| route_code | varchar(255) | 路线编码 |
| section_code | varchar(100) | 路段编码 |
| gantry_stake | double precision | 门架桩号 |
| demonstration_id | integer | 示范段ID |
| lng_84 | numeric | 经度（WGS84） |
| lat_84 | numeric | 纬度（WGS84） |

---

## 2. 边选择器查询策略

### 2.1 筛选维度

#### 维度1：路线编码（route_code）
```sql
SELECT DISTINCT route_code, COUNT(*) as edge_count
FROM dim.sim_network_edges
WHERE route_code IS NOT NULL
GROUP BY route_code
ORDER BY route_code;
-- 结果：G4202, G5, SA2, G76, S81等
```

#### 维度2：节点类型（node_type）
```sql
-- 查询分流点关联的路段
SELECT DISTINCT e.edge_id, e.route_code, e.start_stake, e.end_stake
FROM dim.sim_network_edges e
JOIN dim.multiscale_node_units n
  ON e.from_junction::varchar = n.junction_id OR e.to_junction::varchar = n.junction_id
WHERE n.node_type = 'diverging'
  AND e.route_code = 'G4202';
```

#### 维度3：桩号范围（stake_number）
```sql
SELECT edge_id, route_code, start_stake, end_stake
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND start_stake >= 10.0
  AND end_stake <= 50.0
ORDER BY start_stake;
```

#### 维度4：路段长度（length）
```sql
SELECT edge_id, route_code, length, num_lanes
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND length BETWEEN 500 AND 2000
ORDER BY length DESC;
```

#### 维度5：方向（route_direction）
```sql
SELECT edge_id, route_code, route_direction, start_stake, end_stake
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND route_direction = 'clockwise'
ORDER BY start_stake;
```

#### 维度6：示范段（demonstration_id）
```sql
SELECT edge_id, route_code, demonstration_id, start_stake, end_stake
FROM dim.sim_network_edges
WHERE demonstration_id = 5  -- 5对应G4202
ORDER BY start_stake;
```

### 2.2 组合查询示例

**示例1：查询G4202早高峰拥堵的分流点路段**
```sql
SELECT
    e.edge_id,
    e.route_code,
    e.start_stake,
    e.end_stake,
    e.length,
    e.num_lanes,
    n.node_type,
    n.unit_name
FROM dim.sim_network_edges e
JOIN dim.multiscale_node_units n
  ON e.from_junction::varchar = n.junction_id
WHERE e.route_code = 'G4202'
  AND n.node_type IN ('diverging', 'merging')
  AND e.length BETWEEN 800 AND 3000  -- 适合管控的路段长度
  AND e.num_lanes >= 3               -- 至少3车道
ORDER BY e.start_stake;
```

**示例2：查询路段及其门架分布**
```sql
SELECT
    e.edge_id,
    e.route_code,
    e.start_stake,
    e.end_stake,
    e.length,
    COUNT(g.gantry_id) as gantry_count,
    STRING_AGG(g.gantry_id, ', ') as gantries
FROM dim.sim_network_edges e
LEFT JOIN dim.point_gantry g
  ON e.route_code = g.route_code
  AND g.gantry_stake BETWEEN e.start_stake AND e.end_stake
WHERE e.route_code = 'G4202'
  AND e.demonstration_id = 5
GROUP BY e.edge_id, e.route_code, e.start_stake, e.end_stake, e.length
HAVING COUNT(g.gantry_id) >= 1  -- 至少有1个门架
ORDER BY e.start_stake;
```

---

## 3. 边选择器API设计

### 3.1 核心查询函数

```python
# shared/data_access/edge_query.py

def query_edges_with_filters(
    route_codes: List[str] = None,          # 路线编码列表
    node_types: List[str] = None,           # 节点类型（分流/汇流）
    min_stake: float = None,                # 最小桩号
    max_stake: float = None,                # 最大桩号
    min_length: float = None,               # 最小长度（米）
    max_length: float = None,               # 最大长度（米）
    route_direction: str = None,            # 方向（clockwise/counterclockwise）
    demonstration_ids: List[int] = None,    # 示范段ID列表
    min_lanes: int = None,                  # 最小车道数
    with_gantry: bool = False               # 是否仅返回有门架的路段
) -> List[EdgeInfo]:
    """
    多维度筛选路段

    Returns:
        List[EdgeInfo]: 包含以下字段的EdgeInfo列表
            - edge_id: 路段ID
            - route_code: 路线编码
            - section_code: 路段编码
            - start_stake: 起点桩号
            - end_stake: 终点桩号
            - length: 长度（米）
            - num_lanes: 车道数
            - route_direction: 方向
            - node_type: 关联节点类型
            - gantry_count: 门架数量
            - gantry_ids: 门架ID列表
    """
    conn = open_db_connection()
    cur = conn.cursor()

    # 构建SQL查询
    sql = """
        SELECT DISTINCT
            e.edge_id,
            e.route_code,
            e.section_code,
            e.start_stake,
            e.end_stake,
            e.length,
            e.num_lanes,
            e.route_direction,
            n.node_type,
            COUNT(g.gantry_id) as gantry_count,
            STRING_AGG(g.gantry_id, ',') as gantry_ids
        FROM dim.sim_network_edges e
        LEFT JOIN dim.multiscale_node_units n
          ON e.from_junction::varchar = n.junction_id
        LEFT JOIN dim.point_gantry g
          ON e.route_code = g.route_code
          AND g.gantry_stake BETWEEN e.start_stake AND e.end_stake
        WHERE 1=1
    """

    params = []

    if route_codes:
        sql += " AND e.route_code = ANY(%s)"
        params.append(route_codes)

    if node_types:
        sql += " AND n.node_type = ANY(%s)"
        params.append(node_types)

    if min_stake is not None:
        sql += " AND e.start_stake >= %s"
        params.append(min_stake)

    if max_stake is not None:
        sql += " AND e.end_stake <= %s"
        params.append(max_stake)

    if min_length is not None:
        sql += " AND e.length >= %s"
        params.append(min_length)

    if max_length is not None:
        sql += " AND e.length <= %s"
        params.append(max_length)

    if route_direction:
        sql += " AND e.route_direction = %s"
        params.append(route_direction)

    if demonstration_ids:
        sql += " AND e.demonstration_id = ANY(%s)"
        params.append(demonstration_ids)

    if min_lanes:
        sql += " AND e.num_lanes >= %s"
        params.append(min_lanes)

    sql += " GROUP BY e.edge_id, e.route_code, e.section_code, e.start_stake, e.end_stake, e.length, e.num_lanes, e.route_direction, n.node_type"

    if with_gantry:
        sql += " HAVING COUNT(g.gantry_id) > 0"

    sql += " ORDER BY e.route_code, e.start_stake"

    cur.execute(sql, params)
    rows = cur.fetchall()

    # 转换为EdgeInfo对象
    edges = [
        EdgeInfo(
            edge_id=row[0],
            route_code=row[1],
            section_code=row[2],
            start_stake=float(row[3]) if row[3] else None,
            end_stake=float(row[4]) if row[4] else None,
            length=float(row[5]) if row[5] else None,
            num_lanes=row[6],
            route_direction=row[7],
            node_type=row[8],
            gantry_count=row[9],
            gantry_ids=row[10].split(',') if row[10] else []
        )
        for row in rows
    ]

    cur.close()
    conn.close()

    return edges
```

### 3.2 辅助查询函数

```python
def get_available_route_codes() -> List[str]:
    """获取所有可用的路线编码"""
    conn = open_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT route_code
        FROM dim.sim_network_edges
        WHERE route_code IS NOT NULL
        ORDER BY route_code
    """)
    route_codes = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return route_codes


def get_demonstration_info() -> List[Dict]:
    """获取示范段信息"""
    conn = open_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
            demonstration_id,
            route_code,
            COUNT(*) as edge_count,
            MIN(start_stake) as min_stake,
            MAX(end_stake) as max_stake
        FROM dim.sim_network_edges
        WHERE demonstration_id IS NOT NULL
        GROUP BY demonstration_id, route_code
        ORDER BY demonstration_id
    """)
    results = [
        {
            "demonstration_id": row[0],
            "route_code": row[1],
            "edge_count": row[2],
            "stake_range": f"{row[3]:.2f}-{row[4]:.2f}km"
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return results
```

---

## 4. 前端筛选界面设计

```
┌────────────────────────────────────────────────────────────┐
│ 路段选择器 - 高级筛选                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 路线编码:   [G4202 ▼] [G5 ▼] [+ 添加]                     │
│                                                            │
│ 示范段:     [ 5 - G4202 (1.17-85.68km) ▼]                 │
│                                                            │
│ 节点类型:   ☑ 分流点  ☑ 汇流点  ☐ 入口  ☐ 出口             │
│                                                            │
│ 桩号范围:   K [10.0__] 至 K [50.0__]                       │
│                                                            │
│ 路段长度:   [500__] 米 至 [2000__] 米                      │
│                                                            │
│ 车道数:     至少 [3__] 条车道                              │
│                                                            │
│ 方向:       ◉ 全部  ○ 顺时针  ○ 逆时针                    │
│                                                            │
│ 门架要求:   ☑ 仅显示有门架的路段                           │
│                                                            │
│           [重置] [查询]                                    │
├────────────────────────────────────────────────────────────┤
│ 查询结果: 23个路段                                          │
│                                                            │
│ ┌────────────────────────────────────────────────────┐   │
│ │ edge_id      路线  桩号范围         长度  车道 门架 │   │
│ ├────────────────────────────────────────────────────┤   │
│ │ ☐ -582      SA2   K211.4-K210.7    724m   3    2  │   │
│ │ ☑ -5880     SA2   K139.2-K140.6   1328m   3    3  │   │
│ │ ☐ -5882     G4202 K7.2-K7.1        111m   4    1  │   │
│ └────────────────────────────────────────────────────┘   │
│                                                            │
│ 已选路段 (1):                                              │
│ • -5880 (SA2, K139.2-K140.6, 1328m, 3门架) [x]           │
│                                                            │
│          [清空] [确认选择(1)]                              │
└────────────────────────────────────────────────────────────┘
```

---

## 5. 数据模型

```python
from pydantic import BaseModel
from typing import List, Optional

class EdgeInfo(BaseModel):
    """路段信息"""
    edge_id: str
    route_code: str
    section_code: Optional[str]
    start_stake: Optional[float]
    end_stake: Optional[float]
    length: Optional[float]
    num_lanes: Optional[int]
    route_direction: Optional[str]
    node_type: Optional[str]  # 关联节点类型
    gantry_count: int = 0
    gantry_ids: List[str] = []

class EdgeQueryRequest(BaseModel):
    """路段查询请求"""
    route_codes: Optional[List[str]] = None
    node_types: Optional[List[str]] = None
    min_stake: Optional[float] = None
    max_stake: Optional[float] = None
    min_length: Optional[float] = None
    max_length: Optional[float] = None
    route_direction: Optional[str] = None
    demonstration_ids: Optional[List[int]] = None
    min_lanes: Optional[int] = None
    with_gantry: bool = False

class EdgeQueryResponse(BaseModel):
    """路段查询响应"""
    edges: List[EdgeInfo]
    total_count: int
```

---

## 6. 关键SQL查询模板

### 6.1 获取路线列表
```sql
SELECT DISTINCT route_code, COUNT(*) as edge_count
FROM dim.sim_network_edges
WHERE route_code IS NOT NULL
GROUP BY route_code
ORDER BY route_code;
```

### 6.2 获取示范段列表
```sql
SELECT DISTINCT
    demonstration_id,
    route_code,
    COUNT(*) as edge_count,
    MIN(start_stake) as min_stake,
    MAX(end_stake) as max_stake
FROM dim.sim_network_edges
WHERE demonstration_id IS NOT NULL
GROUP BY demonstration_id, route_code
ORDER BY demonstration_id;
```

### 6.3 筛选分流/汇流点路段
```sql
SELECT
    e.edge_id,
    e.route_code,
    e.start_stake,
    e.end_stake,
    e.length,
    n.node_type
FROM dim.sim_network_edges e
JOIN dim.multiscale_node_units n
  ON e.from_junction::varchar = n.junction_id
WHERE e.route_code = 'G4202'
  AND n.node_type IN ('diverging', 'merging')
ORDER BY e.start_stake;
```

---

## 7. 特殊场景支持 ⭐

### 7.1 收费入口管控（TEC - Toll Entrance Control）

**场景需求**：根据TAZ选择收费入口边，控制特定入口流量

**解决方案**：✅ **已支持，立即可用**

```python
# 方案1: 基于节点类型筛选（推荐）
entrance_edges = query_edges_with_filters(
    route_codes=["G4202"],
    node_types=["entrance"]  # ✅ 已支持
)

# 方案2: 基于边类型筛选
entrance_edges = query_edges_with_filters(
    route_codes=["G4202"],
    edge_types=["highway.motorway_link"],  # 入口匝道
    node_types=["entrance"]
)

# 方案3: 结合TAZ筛选（可选扩展）
entrance_edges = query_edges_by_taz(
    taz_ids=["G00055100200104010"],
    source_types=["toll_square"]  # gantry/toll_square
)
```

**数据支持**：
- ✅ `multiscale_node_units.node_type = 'entrance'`（15+个入口边）
- ✅ `taz_demonstration_mapping`表（461条TAZ映射记录）
- ✅ `sim_network_edges.type = 'highway.motorway_link'`（入口匝道标识）

**参考文档**：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md)

---

### 7.2 动态硬路肩管控（DHS - Dynamic Hard Shoulder）

**场景需求**：选择具备应急车道的主路，动态开放应急车道

**解决方案**：△ **基本支持，建议扩展**

**短期方案（推断）**：
```python
# 基于车道数推断（≥5车道可能有应急车道）
dhs_edges = query_edges_with_filters(
    route_codes=["G4202"],
    edge_types=["highway.motorway"],  # 主路
    min_lanes=5,                      # ≥5车道
    min_length=800
)
```

**推荐方案（精确识别）**：
```python
# 关联车道表精确识别应急车道
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
    print(f"应急车道数: {edge.emergency_lane_count}")
    print(f"应急车道索引: {edge.emergency_lane_indexes}")
```

**数据支持**：
- ✅ `sim_network_lanes`表（车道级别配置，含`disallow`字段）
- ✅ `sim_network_edges.type = 'highway.motorway'`（主路标识）
- ✅ G4202路线有20+个5-6车道的主路边

**实现清单**：
- [ ] 新增`edge_types`参数（P0，0.5天）
- [ ] 新增`query_edges_with_emergency_lanes()`函数（P1，1-2天）
- [ ] 可选：数据库添加`has_emergency_lane`字段（P2）

**参考文档**：
- 详细方案：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md)
- 快速答案：[edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md)

---

### 7.3 扩展维度汇总

| 维度 | 参数 | 状态 | 优先级 | 适用场景 |
|------|------|------|--------|---------|
| 路线编码 | route_codes | ✅ 已支持 | P0 | 所有场景 |
| 路段编码 | section_codes | ✅ 已支持 | P0 | 所有场景 |
| 方向 | route_direction | ✅ 已支持 | P0 | 所有场景 |
| 桩号范围 | min/max_stake | ✅ 已支持 | P0 | 所有场景 |
| 路段长度 | min/max_length | ✅ 已支持 | P0 | 所有场景 |
| 车道数 | min_lanes | ✅ 已支持 | P0 | 所有场景 |
| 节点类型 | node_types | ✅ 已支持 | P0 | TEC入口管控 |
| 门架筛选 | with_gantry | ✅ 已支持 | P0 | 需要观测数据 |
| 示范段 | demonstration_ids | ✅ 已支持 | P0 | 预定义区域 |
| **边类型** | **edge_types** | 📋 **待实现** | **P0** | **TEC, DHS** |
| **TAZ筛选** | **taz_ids** | 📋 **可选** | **P2** | **TEC** |
| **应急车道** | **has_emergency_lane** | 📋 **可选** | **P1** | **DHS** |

**总计**: 9种已支持 + 3种待扩展 = **12种筛选维度**

---

## 8. 后续优化方向

1. **缓存机制**：将常用查询结果缓存到Redis
2. **全文搜索**：支持路段名称模糊搜索
3. **空间查询**：基于PostGIS的地理位置筛选
4. **批量操作**：支持批量选择区域内所有路段
5. **历史记录**：保存用户的筛选条件和选择结果
6. **智能推荐**：根据控制策略类型推荐合适的边

---

**文档版本**: v1.1
**最后更新**: 2025-10-19
**更新内容**: 新增特殊场景支持（TEC/DHS）
**维护者**: OD_SIM开发团队
