# SUMO网络数据库表结构文档

## 概述

本文档描述数据库 `dim` schema 中存储的SUMO仿真网络数据表结构。这些表存储了从SUMO网络文件（.net.xml）中提取的网络拓扑信息，包括路段（edges）、车道（lanes）、交叉口（junctions）和连接关系（connections）。

**数据来源**: SUMO网络文件（推荐使用 `sichuan202508v7.net.xml`）
**Schema**: `dim`
**表数量**: 4 个核心表
**总记录数**: 112,995 条（截至查询时间）

---

## 表关系图

```
dim.sim_network_junctions (9,491条)
         ↑                    ↑
         |                    |
    from_junction        to_junction
         |                    |
dim.sim_network_edges (20,124条)
         ↑                    ↑
         |                    |
      edge_id              edge_id
         |                    |
         ├─────────────┬──────┘
         |             |
dim.sim_network_lanes  dim.sim_network_connections
   (39,904条)            (42,476条)
```

---

## 1. dim.sim_network_edges

**描述**: 存储SUMO网络的路段（Edge）信息，包括道路几何、拓扑关系和业务属性。

**记录数**: 20,124 条

### 字段说明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | integer | PK, NOT NULL | 自增主键 |
| edge_id | varchar(255) | NOT NULL, Indexed | SUMO边ID（业务主键） |
| function | varchar(50) | NULL | 边功能类型（normal/internal等） |
| from_junction | varchar(255) | NULL, Indexed | 起始交叉口ID |
| to_junction | varchar(255) | NULL, Indexed | 终止交叉口ID |
| priority | integer | NULL | 道路优先级 |
| type | varchar(100) | NULL | 道路类型 |
| spread_type | varchar(50) | NULL | 车道展开类型 |
| length | double precision | NULL | 边长度（米） |
| shape | text | NULL | 几何形状（坐标串） |
| geom | geometry | NULL, Indexed | PostGIS几何对象 |
| created_at | timestamp | NULL | 创建时间 |
| updated_at | timestamp | NULL | 更新时间 |
| **业务扩展字段** | | | |
| route_code | varchar(20) | NULL | 路线编码 |
| section_code | varchar(20) | NULL | 路段编码 |
| demonstration_id | integer | NULL | 示范段ID |
| start_stake | numeric | NULL | 起始桩号 |
| end_stake | numeric | NULL | 终止桩号 |
| route_direction | varchar(20) | NULL | 路线方向 |
| attribute_source | varchar(20) | NULL | 属性来源 |

### 索引

- `sim_network_edges_pkey1` (UNIQUE): id
- `idx_sim_edges_id`: edge_id
- `idx_sim_edges_from_junction`: from_junction
- `idx_sim_edges_to_junction`: to_junction
- `idx_sim_edges_geom`: geom (空间索引)

### 使用场景

- 网络拓扑分析（查询路段连接关系）
- EdgeData分析结果关联（通过edge_id）
- 路段几何可视化（geom字段）
- 业务数据关联（route_code, section_code等）

---

## 2. dim.sim_network_lanes

**描述**: 存储SUMO网络的车道（Lane）信息，包括速度限制、长度和几何形状。

**记录数**: 39,904 条

### 字段说明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | integer | PK, NOT NULL | 自增主键 |
| lane_id | varchar(255) | NOT NULL, Indexed | SUMO车道ID（格式：edge_id_lane_index） |
| edge_id | varchar(255) | NULL, Indexed | 所属边ID（关联到edges表） |
| lane_index | integer | NULL | 车道索引号（从0开始） |
| speed | double precision | NULL | 速度限制（m/s） |
| length | double precision | NULL | 车道长度（米） |
| disallow | text | NULL | 禁止通行的车辆类型 |
| shape | text | NULL | 几何形状（坐标串） |
| geom | geometry | NULL, Indexed | PostGIS几何对象 |
| created_at | timestamp | NULL | 创建时间 |
| updated_at | timestamp | NULL | 更新时间 |

### 索引

- `sim_network_lanes_pkey` (UNIQUE): id
- `idx_sim_lanes_id`: lane_id
- `idx_sim_lanes_edge_id`: edge_id
- `idx_sim_lanes_geom`: geom (空间索引)

### 使用场景

- 车道级别速度分析
- E1检测器位置关联（检测器通常部署在车道上）
- 车道几何可视化
- 通行规则分析（disallow字段）

---

## 3. dim.sim_network_junctions

**描述**: 存储SUMO网络的交叉口（Junction）信息，包括类型、位置和车道关联。

**记录数**: 9,491 条

### 字段说明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | integer | PK, NOT NULL | 自增主键 |
| junction_id | varchar(255) | NOT NULL, Indexed | SUMO交叉口ID（业务主键） |
| junction_type | varchar(50) | NULL | 交叉口类型（priority/traffic_light等） |
| inc_lanes | text | NULL | 进入车道列表（逗号分隔） |
| int_lanes | text | NULL | 内部车道列表（逗号分隔） |
| shape | text | NULL | 几何形状（坐标串） |
| longitude | double precision | NULL | 经度 |
| latitude | double precision | NULL | 纬度 |
| category | varchar(50) | NULL | 交叉口类别 |
| geom | geometry | NULL, Indexed | PostGIS几何对象 |
| created_at | timestamp | NULL | 创建时间 |
| updated_at | timestamp | NULL | 更新时间 |
| **业务扩展字段** | | | |
| route_code | varchar(20) | NULL | 路线编码 |
| section_code | varchar(20) | NULL | 路段编码 |
| demonstration_id | integer | NULL | 示范段ID |
| stake_number | numeric | NULL | 桩号 |
| route_direction | varchar(20) | NULL | 路线方向 |
| attribute_source | varchar(20) | NULL | 属性来源 |

### 索引

- `sim_network_junctions_pkey` (UNIQUE): id
- `idx_sim_junctions_id`: junction_id
- `idx_sim_junctions_geom`: geom (空间索引)

### 使用场景

- 交叉口控制策略分析（junction_type）
- 网络拓扑分析（与edges表关联）
- 空间位置查询（经纬度/geom字段）
- 交通信号优化（traffic_light类型交叉口）

---

## 4. dim.sim_network_connections

**描述**: 存储SUMO网络的车道连接关系（Connection），定义了交叉口内部的车道转向规则。

**记录数**: 42,476 条

### 字段说明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | integer | PK, NOT NULL | 自增主键 |
| from_edge | varchar(255) | NULL, Indexed | 起始边ID |
| to_edge | varchar(255) | NULL, Indexed | 目标边ID |
| from_lane | integer | NULL | 起始车道索引 |
| to_lane | integer | NULL | 目标车道索引 |
| via | varchar(255) | NULL | 经由车道ID（内部车道） |
| direction | varchar(10) | NULL | 转向方向（s/l/r/t等） |
| state | varchar(10) | NULL | 连接状态（-/=/m等） |
| created_at | timestamp | NULL | 创建时间 |
| updated_at | timestamp | NULL | 更新时间 |

### 索引

- `sim_network_connections_pkey` (UNIQUE): id
- `idx_sim_connections_from_edge`: from_edge
- `idx_sim_connections_to_edge`: to_edge

### 字段值说明

**direction 字段值**:
- `s`: 直行（straight）
- `l`: 左转（left）
- `r`: 右转（right）
- `t`: 掉头（turn）
- `L`: 部分左转
- `R`: 部分右转

**state 字段值**:
- `-`: 次要道路（需让行）
- `=`: 主要道路（有路权）
- `m`: 次要道路（需让行，旧格式）
- `M`: 主要道路（有路权，旧格式）

### 使用场景

- 路径规划验证（检查OD路径的车道连接合法性）
- 交通流分析（转向流量统计）
- 交叉口信号配时优化（分析各转向关系）
- 仿真路径调试（追踪车辆转向决策）

---

## 数据关系

### 表间关联

```sql
-- 通过 edges 表关联 junctions
SELECT e.*, j1.junction_id as from_junc, j2.junction_id as to_junc
FROM dim.sim_network_edges e
LEFT JOIN dim.sim_network_junctions j1 ON e.from_junction = j1.junction_id
LEFT JOIN dim.sim_network_junctions j2 ON e.to_junction = j2.junction_id;

-- 通过 lanes 表关联 edges
SELECT l.*, e.from_junction, e.to_junction
FROM dim.sim_network_lanes l
JOIN dim.sim_network_edges e ON l.edge_id = e.edge_id;

-- 通过 connections 表关联 edges
SELECT c.*, e1.edge_id as from_edge_info, e2.edge_id as to_edge_info
FROM dim.sim_network_connections c
JOIN dim.sim_network_edges e1 ON c.from_edge = e1.edge_id
JOIN dim.sim_network_edges e2 ON c.to_edge = e2.edge_id;
```

### 与分析数据的关联

**EdgeData 分析**:
```sql
-- EdgeData 结果通过 edge_id 关联网络数据
SELECT ed.*, ne.route_code, ne.section_code, ne.length
FROM edgedata_analysis_results ed
JOIN dim.sim_network_edges ne ON ed.edge_id = ne.edge_id;
```

**E1检测器数据**:
```sql
-- E1检测器通过 lane_id 关联网络数据
SELECT e1.*, nl.speed as lane_speed, nl.length
FROM e1_detector_data e1
JOIN dim.sim_network_lanes nl ON e1.lane_id = nl.lane_id;
```

---

## 数据统计

| 表名 | 记录数 | 主要用途 |
|------|--------|----------|
| sim_network_edges | 20,124 | 路段拓扑和EdgeData分析 |
| sim_network_lanes | 39,904 | 车道级别分析和E1检测器 |
| sim_network_junctions | 9,491 | 交叉口分析和信号控制 |
| sim_network_connections | 42,476 | 车道连接和转向分析 |
| **总计** | **112,995** | |

### 数据覆盖

- **路段覆盖**: 20,124 条边（edges）
- **车道覆盖**: 平均每条边约 1.98 条车道
- **交叉口覆盖**: 9,491 个交叉口
- **连接覆盖**: 平均每个交叉口约 4.5 条连接

---

## 业务扩展字段说明

部分表（edges, junctions）包含业务扩展字段，用于与实际道路业务系统关联：

### 路线和路段信息
- `route_code`: 路线编码（如 G5）
- `section_code`: 路段编码
- `route_direction`: 路线方向（上行/下行）

### 桩号信息
- `start_stake`: 起始桩号（edges表）
- `end_stake`: 终止桩号（edges表）
- `stake_number`: 桩号（junctions表）

### 其他属性
- `demonstration_id`: 示范段标识
- `attribute_source`: 属性数据来源

这些字段支持将SUMO仿真网络与实际高速公路业务系统（如门架、收费站等）进行关联。

---

## 使用建议

### 性能优化

1. **空间查询**: 三个表都有 `geom` 字段的空间索引，适合基于位置的查询
2. **业务查询**: 使用 `edge_id`, `lane_id`, `junction_id` 索引进行快速查找
3. **关联查询**: 通过 `from_junction`, `to_junction`, `edge_id` 等字段关联表

### 数据维护

- 所有表都有 `created_at` 和 `updated_at` 时间戳字段
- 主键均为自增ID，业务主键为各自的 `*_id` 字段
- 几何数据同时存储文本形式（shape）和空间对象（geom）

### 常见查询模式

```sql
-- 1. 查询某个路段的所有车道
SELECT * FROM dim.sim_network_lanes
WHERE edge_id = 'your_edge_id';

-- 2. 查询某个交叉口的所有进出边
SELECT * FROM dim.sim_network_edges
WHERE from_junction = 'junction_id' OR to_junction = 'junction_id';

-- 3. 查询某条边的所有出向连接
SELECT * FROM dim.sim_network_connections
WHERE from_edge = 'edge_id';

-- 4. 查询带信号灯的交叉口
SELECT * FROM dim.sim_network_junctions
WHERE junction_type = 'traffic_light';
```

---

## 附录：查询脚本

详细的表结构JSON数据保存在项目根目录：
- 文件路径: `sim_network_tables_structure.json`
- 包含完整的字段定义、索引和约束信息

生成此文档的查询脚本：
- 文件路径: `query_sim_network_tables.py`
- 用法: `python query_sim_network_tables.py`

---

**文档版本**: v1.0
**生成时间**: 2025-10-02
**数据来源**: PostgreSQL Database (sdzg)
**维护**: OD数据处理与仿真系统团队
