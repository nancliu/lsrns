# Highway Schema 数据说明文档

**版本**: v0.8.1
**更新日期**: 2025-10-17
**数据批次**: 16批次（20250609_20250615 至 20250922_20250928）
**数据状态**: 生产就绪 ✅（批次分析与KPI系统完整）

---

## 📋 目录

- [1. 概述](#1-概述)
- [2. 数据表结构](#2-数据表结构)
  - [2.1 门架基准表 (baseline_gantry_hourly)](#21-门架基准表-baseline_gantry_hourly)
  - [2.2 节点基准表 (baseline_node_hourly)](#22-节点基准表-baseline_node_hourly)
  - [2.3 路段基准表 (baseline_edge_hourly)](#23-路段基准表-baseline_edge_hourly)
  - [2.4 设施基准表 (baseline_facility_hourly)](#24-设施基准表-baseline_facility_hourly)
  - [2.5 路网基准表 (baseline_network_hourly)](#25-路网基准表-baseline_network_hourly)
  - [2.6 收费广场基准表 (baseline_tollsquare_*_hourly)](#26-收费广场基准表-baseline_tollsquare__hourly)
  - [2.7 OD基准表 (baseline_od_hourly)](#27-od基准表-baseline_od_hourly)
  - [2.8 路线编码映射表 (route_code_mapping)](#28-路线编码映射表-route_code_mapping)
  - [2.9 基准元数据表 (baseline_metadata)](#29-基准元数据表-baseline_metadata)
  - [2.10 历史基线表 (historical_baseline)](#210-历史基线表-historical_baseline)
- [3. 核心查询函数](#3-核心查询函数)
- [4. 数据视图](#4-数据视图)
- [5. 数据统计](#5-数据统计)
- [6. 使用示例](#6-使用示例)
- [7. 数据质量指标](#7-数据质量指标)

---

## 1. 概述

Highway schema 是 HOMDS 系统的**核心分析工作区**，存储多维度交通批次分析数据和KPI评估结果。数据来源于真实收费站流量（zngs schema）和基准流量（baseline schema），通过批次聚合计算生成周级别的KPI指标。

**核心特性（v0.8.1）**：

- ✅ **批次分析系统**：16个周批次（2025-W24至W39），182,922条KPI记录
- ✅ **四维度架构**：门架、OD对、收费广场入口、收费广场出口
- ✅ **四模式支持**：工作日/周末/节假日（免费/不免费）
- ✅ **KPI指标体系**：9个实际可用KPI（流量/速度/时间/拥堵/质量类）
- ✅ **历史基线系统**：3个月滚动窗口，μ±2σ阈值，趋势预警
- ✅ **KPI分组对比**：5个分组（流量与容量/速度/时间/拥堵/质量）
- ✅ **周模式分析**：Monday-Sunday分天统计，周末系数计算
- ✅ **货车影响量化**：协方差、贡献度、速度惩罚分析

---

## 2. 数据表结构

### 2.1 门架基准表 (baseline_gantry_hourly)

**用途**：单个收费门架的小时级交通基准数据，是最基础的数据源。

**主键**：`(gantry_id, pattern_type, hour)`

**关键字段**：

| 字段名                 | 类型          | 说明                              | 示例                                                           |
| ---------------------- | ------------- | --------------------------------- | -------------------------------------------------------------- |
| `gantry_id`          | varchar(50)   | 门架ID（与dim.all_gantry_84一致） | `G420200100010`                                              |
| `pattern_type`       | varchar(20)   | 模式类型                          | `workday`, `weekend`, `holiday_free`, `holiday_nofree` |
| `hour`               | integer       | 小时（0-23）                      | `8`                                                          |
| `mean_flow`          | numeric(10,2) | 平均流量（辆/小时）               | `1256.50`                                                    |
| `median_flow`        | numeric(10,2) | 中位数流量（P50）                 | `1180.00`                                                    |
| `p75_flow`           | numeric(10,2) | 75分位数流量                      | `1420.00`                                                    |
| `p85_flow`           | numeric(10,2) | 85分位数流量                      | `1580.00`                                                    |
| `p95_flow`           | numeric(10,2) | 95分位数流量（由P85×1.1估算）    | `1738.00`                                                    |
| `stddev_flow`        | numeric(10,2) | 流量标准差                        | `320.50`                                                     |
| `truck_ratio`        | numeric(6,4)  | 货车占比（0-1）                   | `0.2350`                                                     |
| `avg_speed`          | numeric(10,2) | 平均速度（km/h）                  | `85.30`                                                      |
| `free_flow_speed`    | numeric(10,2) | 自由流速度（km/h）                | `100.00`                                                     |
| `estimated_capacity` | numeric(10,2) | 估算容量（veh/h，P85÷0.85）      | `1858.82`                                                    |
| `sample_count`       | integer       | 样本数量（0表示补充数据）         | `28`                                                         |
| `baseline_batch_id`  | varchar(50)   | 批次ID                            | `20250616_20250713`                                          |

**车型分布字段**：

- `passenger_small`：小型客车流量
- `passenger_large`：大型客车流量
- `truck_small`：小型货车流量
- `truck_large`：大型货车流量
- `special_small`：小型专用车流量
- `special_large`：大型专用车流量

**索引**：

- PRIMARY KEY: `(gantry_id, pattern_type, hour)`
- `idx_baseline_gantry_batch`: 快速按批次查询
- `idx_baseline_gantry_pattern`: 快速按模式查询
- `idx_baseline_gantry_updated`: 支持增量同步

**数据规模**：

- 总记录数：16,344条
- 唯一门架数：228个
- 模式类型：3种（workday、weekend、holiday_free）
- 每门架每模式：24小时记录

---

### 2.2 节点基准表 (baseline_node_hourly)

**用途**：仿真路网节点（junction）级别的聚合基准，支持分流/汇流点分析。

**主键**：`(unit_id, pattern_type, hour, baseline_batch_id)`

**关键字段**：

| 字段名               | 类型          | 说明                | 示例                                                                                                 |
| -------------------- | ------------- | ------------------- | ---------------------------------------------------------------------------------------------------- |
| `unit_id`          | varchar(100)  | 节点单元ID          | `node_j123456`                                                                                     |
| `unit_name`        | varchar(255)  | 节点名称            | `绕城高速-三环互通`                                                                                |
| `junction_id`      | varchar(100)  | 仿真路网junction ID | `j123456`                                                                                          |
| `node_type`        | varchar(50)   | 节点类型            | `diverging`, `merging`, `normal`, `entrance`, `exit`, `lane_increase`, `lane_decrease` |
| `route_code`       | varchar(20)   | 路线编码            | `G4202`                                                                                            |
| `section_code`     | varchar(50)   | 路段编码            | `G4202-S01`                                                                                        |
| `demonstration_id` | integer       | 示范段ID            | `1`                                                                                                |
| `stake_number`     | numeric(10,3) | 桩号（公里）        | `K35+500`                                                                                          |
| `in_edge_count`    | integer       | 入边数量            | `2`                                                                                                |
| `out_edge_count`   | integer       | 出边数量            | `3`                                                                                                |
| `total_in_lanes`   | integer       | 入口总车道数        | `6`                                                                                                |
| `total_out_lanes`  | integer       | 出口总车道数        | `9`                                                                                                |
| `edge_count`       | integer       | 关联路段数          | `5`                                                                                                |
| `gantry_count`     | integer       | 关联门架数          | `3`                                                                                                |
| `mean_flow`        | numeric(10,2) | 平均流量            | `2345.60`                                                                                          |
| `p85_flow`         | numeric(10,2) | 85分位数流量        | `2890.00`                                                                                          |

**节点类型说明**：

- `normal`：普通节点
- `diverging`：分流点（出边数 > 入边数）
- `merging`：汇流点（入边数 > 出边数）
- `entrance`：入口匝道节点
- `exit`：出口匝道节点
- `lane_increase`：车道增加节点
- `lane_decrease`：车道减少节点

**数据规模**：

- 总记录数：49,668条
- 唯一节点数：690个
- 节点类型：7种

---

### 2.3 路段基准表 (baseline_edge_hourly)

**用途**：仿真路网路段（edge）级别的基准，用于路段性能评估。

**主键**：`(edge_id, pattern_type, hour, baseline_batch_id)`

**关键字段**：

| 字段名              | 类型          | 说明             | 示例                               |
| ------------------- | ------------- | ---------------- | ---------------------------------- |
| `edge_id`         | varchar(100)  | 路段ID           | `edge_e789012`                   |
| `from_junction`   | varchar(100)  | 起点junction ID  | `j123456`                        |
| `to_junction`     | varchar(100)  | 终点junction ID  | `j123457`                        |
| `route_code`      | varchar(20)   | 路线编码         | `G4202`                          |
| `edge_length`     | numeric(10,2) | 路段长度（米）   | `1250.50`                        |
| `start_stake`     | numeric(10,3) | 起点桩号         | `K35.500`                        |
| `end_stake`       | numeric(10,3) | 终点桩号         | `K36.750`                        |
| `gantry_count`    | integer       | 路段包含门架数   | `2`                              |
| `gantry_ids`      | text[]        | 门架ID数组       | `{G420200100010, G420200100020}` |
| `avg_speed`       | numeric(6,2)  | 平均速度（km/h） | `82.50`                          |
| `free_flow_speed` | numeric(6,2)  | 自由流速度       | `100.00`                         |

**用途示例**：

```sql
-- 查找拥堵路段（速度 < 60km/h）
SELECT edge_id, route_code, avg_speed, mean_flow, p85_flow
FROM highway.baseline_edge_hourly
WHERE pattern_type = 'workday'
  AND hour = 8
  AND avg_speed < 60
ORDER BY avg_speed;
```

---

### 2.4 设施基准表 (baseline_facility_hourly)

**用途**：路网设施级别（如互通立交、服务区）的聚合基准。

**主键**：`(facility_id, pattern_type, hour)`

**关键字段**：

| 字段名                 | 类型          | 说明           | 示例                                                |
| ---------------------- | ------------- | -------------- | --------------------------------------------------- |
| `facility_id`        | varchar(50)   | 设施ID         | `facility_f001`                                   |
| `facility_type`      | varchar(20)   | 设施类型       | `interchange`, `service_area`, `toll_station` |
| `gantry_count`       | integer       | 设施包含门架数 | `4`                                               |
| `estimated_capacity` | numeric(10,2) | 估算容量       | `5600.00`                                         |

**设施类型**：

- `interchange`：互通立交
- `service_area`：服务区
- `toll_station`：收费站
- `rest_area`：停车区

---

### 2.5 路网基准表 (baseline_network_hourly)

**用途**：全路网级别的聚合统计，用于宏观评估。

**主键**：`(network_id, pattern_type, hour)`

**关键字段**：

| 字段名                       | 类型          | 说明           | 示例                 |
| ---------------------------- | ------------- | -------------- | -------------------- |
| `network_id`               | varchar(50)   | 路网ID         | `G4202_NETWORK`    |
| `network_name`             | varchar(100)  | 路网名称       | `成都绕城高速全线` |
| `avg_capacity_utilization` | numeric(6,4)  | 平均容量利用率 | `0.6523`           |
| `total_estimated_capacity` | numeric(10,2) | 总估算容量     | `125000.00`        |
| `facility_count`           | integer       | 设施数量       | `12`               |
| `gantry_count`             | integer       | 门架数量       | `84`               |

**用途示例**：

```sql
-- 查看全天容量利用率变化
SELECT hour,
       mean_flow,
       total_estimated_capacity,
       avg_capacity_utilization
FROM highway.baseline_network_hourly
WHERE network_id = 'G4202_NETWORK'
  AND pattern_type = 'workday'
ORDER BY hour;
```

---

### 2.6 收费广场基准表 (baseline_tollsquare_*_hourly)

**用途**：收费站入口/出口流量基准，来源于真实收费数据。

**表名**：

- `baseline_tollsquare_entry_hourly`：入口流量
- `baseline_tollsquare_exit_hourly`：出口流量

**主键**：`(square_code, pattern_type, hour)`

**关键字段**：

| 字段名           | 类型          | 说明                 | 示例         |
| ---------------- | ------------- | -------------------- | ------------ |
| `square_code`  | varchar(50)   | 收费广场编码         | `51044001` |
| `pattern_type` | varchar(20)   | 模式类型             | `workday`  |
| `hour`         | integer       | 小时                 | `8`        |
| `mean_flow`    | numeric(10,2) | 平均流量             | `1850.50`  |
| `p95_flow`     | numeric(10,2) | 95分位数流量         | `2456.00`  |
| `sample_count` | integer       | 样本数（0=补充数据） | `28`       |

**数据规模**：

- 入口表：6,855条记录
- 出口表：6,746条记录
- 覆盖模式：workday, weekend, holiday_free

**重要说明**：

- `sample_count = 0` 表示由 `supplement_holiday_free_baseline()` 函数补充的数据
- `holiday_free` 模式部分数据通过 workday 模式插值生成

---

### 2.7 OD基准表 (baseline_od_hourly)

**用途**：Top-500热点OD对的出行特征基准，支持拥堵预测和路径优化。

**主键**：`(origin_id, destination_id, pattern_type, hour)`

**关键字段**：

| 字段名                  | 类型          | 说明                     | 示例                                         |
| ----------------------- | ------------- | ------------------------ | -------------------------------------------- |
| `origin_id`           | varchar(100)  | 起点ID（门架或收费广场） | `G420200100010`                            |
| `destination_id`      | varchar(100)  | 终点ID                   | `G420200100050`                            |
| `od_type_combination` | varchar(30)   | OD类型组合               | `gantry-gantry`, `tollsquare-tollsquare` |
| `origin_type`         | varchar(20)   | 起点类型                 | `gantry`, `tollsquare`                   |
| `destination_type`    | varchar(20)   | 终点类型                 | `gantry`, `tollsquare`                   |
| `mean_flow`           | numeric(10,2) | 平均流量                 | `356.80`                                   |
| `avg_travel_time`     | numeric(10,2) | 平均出行时间（秒）       | `1850.50`                                  |
| `od_rank`             | integer       | OD流量排名（1-500）      | `15`                                       |
| `avg_flow_rank`       | numeric(10,2) | 平均流量排名值           | `356.80`                                   |

**OD类型**：

- `gantry-gantry`：门架到门架（1,445对 workday，1,445对 weekend）
- `tollsquare-tollsquare`：收费广场到收费广场（952对）

**数据规模**：

- 总记录数：114,022条
- 唯一起点数：232个
- 唯一终点数：226个
- 覆盖模式：workday, weekend（暂无holiday_free）

**数据覆盖率**：

- **当前版本（v3.1）**：20.37% OD基准覆盖率
  - Top-500 gantry-gantry OD对：覆盖 35.13% 流量
  - Top-500 tollsquare-tollsquare OD对：覆盖 65.24% 流量

**用途示例**：

```sql
-- 查找早高峰Top10拥堵OD对（出行时间最长）
SELECT origin_id, destination_id,
       mean_flow, avg_travel_time,
       od_rank
FROM highway.baseline_od_hourly
WHERE pattern_type = 'workday'
  AND hour = 8
  AND od_type_combination = 'gantry-gantry'
ORDER BY avg_travel_time DESC
LIMIT 10;
```

---

### 2.8 路线编码映射表 (route_code_mapping)

**用途**：解决 DIM schema 与 Baseline 数据源路线编码不一致问题。

**主键**：`(dim_route_code, baseline_code_prefix)`

**关键字段**：

| 字段名                   | 类型        | 说明               | 示例                                          |
| ------------------------ | ----------- | ------------------ | --------------------------------------------- |
| `dim_route_code`       | varchar(20) | DIM schema路线编码 | `G4202`                                     |
| `baseline_code_prefix` | varchar(10) | Baseline数据前缀   | `G4201`                                     |
| `mapping_type`         | varchar(20) | 映射类型           | `exact`, `alias`, `legacy`, `unknown` |
| `notes`                | text        | 备注说明           | `成都绕城高速 - 可能的主编码`               |
| `verified`             | boolean     | 是否验证           | `true`                                      |

**映射类型说明**：

- `exact`：完全匹配（如G5 → G0005）
- `alias`：别名映射（如G4202 → G4201）
- `legacy`：历史遗留编码
- `unknown`：待确认映射

**当前映射**：

| DIM编码 | Baseline前缀 | 说明                   |
| ------- | ------------ | ---------------------- |
| G5      | G0005        | 京昆高速               |
| G42     | G0042        | 沪蓉高速               |
| G76     | G0076        | 厦蓉高速               |
| G4202   | G4201        | 成都绕城高速（主编码） |
| G4215   | G4215        | 蓉遵高速               |
| G5013   | G5013        | 渝蓉高速               |
| SA2     | S4202        | 成都第二绕城高速       |
| S4      | S0004        | 省道4                  |
| S81     | S0081        | 德会高速               |

**使用函数**：

```sql
-- 根据DIM编码获取Baseline前缀
SELECT highway.get_baseline_prefixes('G4202');
-- 返回: {G4201}

-- 根据Baseline前缀反查DIM编码
SELECT highway.get_dim_route_code('G4201');
-- 返回: G4202
```

---

### 2.9 基准元数据表 (baseline_metadata)

**用途**：记录每个批次的处理状态、数据质量、时间范围等元信息。

**主键**：`baseline_batch_id`

**关键字段**：

| 字段名                         | 类型         | 说明                   | 示例                                      |
| ------------------------------ | ------------ | ---------------------- | ----------------------------------------- |
| `baseline_batch_id`          | varchar(50)  | 批次ID                 | `20250616_20250713`                     |
| `baseline_start_time`        | timestamp    | 基准数据起始时间       | `2025-06-16 00:00:00`                   |
| `baseline_end_time`          | timestamp    | 基准数据结束时间       | `2025-07-13 23:59:59`                   |
| `highway_process_time`       | timestamp    | Highway处理时间        | `2025-10-02 21:46:12`                   |
| `highway_process_status`     | varchar(20)  | 处理状态               | `completed`, `processing`, `failed` |
| `gantry_records`             | integer      | 门架记录数             | `10,895`                                |
| `tollsquare_entry_records`   | integer      | 收费广场入口记录数     | `6,855`                                 |
| `tollsquare_exit_records`    | integer      | 收费广场出口记录数     | `6,746`                                 |
| `od_records`                 | integer      | OD记录数               | `114,022`                               |
| `od_pairs`                   | integer      | OD对数                 | `2,400`                                 |
| `total_records`              | integer      | 总记录数               | `143,414`                               |
| `data_quality_score`         | numeric(5,2) | 数据质量分数（0-100）  | `75.00`                                 |
| `missing_holiday_free_count` | integer      | 缺失holiday_free数据数 | `0`                                     |
| `is_latest_batch`            | boolean      | 是否最新批次           | `true`                                  |

**当前批次状态**：

```
批次ID: 20250616_20250713
数据时间范围: 2025-06-16 ~ 2025-07-13 (28天)
处理状态: completed ✅
总记录数: 143,414条
数据质量分数: 75.00/100
```

---

### 2.10 历史基线表 (historical_baseline)

**用途**：存储3个月滚动窗口的历史基线数据，用于趋势监测和异常检测。

**数据来源**：基于 `highway.batch_kpi_summary` 表的历史批次数据聚合生成。

**更新机制**：
- 使用函数 `highway.update_historical_baseline(dimension, lookback_months)` 更新
- 默认使用3个月滚动窗口（`lookback_months=3`）
- 支持维度：`gantry`, `od`, `tollsquare_on`, `tollsquare_off`
- 特殊处理：`tollsquare` 维度会自动更新 `tollsquare_on` 和 `tollsquare_off` 两个子维度

**数据特点**：
- 主键：`(dimension, entity_id, pattern_type)`
- 统计基线：基于历史批次计算均值和标准差
- 阈值设置：μ ± 2σ（均值 ± 2倍标准差）
- 元数据：记录基线批次列表、时间范围、更新时间

**字段说明**：
- `dimension`: 分析维度（gantry/od/tollsquare_on/tollsquare_off）
- `entity_id`: 实体ID（门架ID/OD对/收费广场ID）
- `pattern_type`: 模式类型（workday/weekend/holiday_free/holiday_nofree）
- `mtt_baseline_mean/std`: MTT基线均值和标准差（仅OD维度有效）
- `speed_baseline_mean/std`: 速度基线均值和标准差（仅门架维度有效）
- `flow_baseline_mean/std`: 流量基线均值和标准差（所有维度有效）
- `*_upper/lower_threshold`: 上下阈值（μ ± 2σ）
- `baseline_batch_ids`: 基线批次列表（数组）
- `baseline_batch_count`: 基线批次数量
- `baseline_start/end_date`: 基线时间范围
- `baseline_updated_at`: 基线更新时间

**使用示例**：
```sql
-- 更新门架维度的历史基线
SELECT highway.update_historical_baseline('gantry', 3);

-- 更新OD维度的历史基线
SELECT highway.update_historical_baseline('od', 3);

-- 更新收费广场维度（自动处理on和off）
SELECT highway.update_historical_baseline('tollsquare', 3);

-- 查询历史基线数据
SELECT entity_id, pattern_type, 
       mtt_baseline_mean, speed_baseline_mean, flow_baseline_mean,
       baseline_batch_count, baseline_start_date, baseline_end_date
FROM highway.historical_baseline 
WHERE dimension = 'gantry' 
  AND entity_id = 'G000551001000110010'
ORDER BY pattern_type;
```

---

## 3. 核心查询函数

### 3.1 获取门架基准

```sql
-- 函数签名
highway.get_baseline_hourly_simple(
    p_gantry_id varchar,
    p_pattern_type varchar,
    p_hour integer
) RETURNS TABLE(...)
```

**示例**：

```sql
-- 查询某门架工作日早8点基准
SELECT * FROM highway.get_baseline_hourly_simple(
    'G420200100010',
    'workday',
    8
);
```

**返回字段**：

- `mean_flow`, `median_flow`, `p85_flow`, `p95_flow`
- `stddev_flow`, `truck_ratio`, `sample_count`
- `baseline_batch_id`

---

### 3.2 获取OD基准

```sql
-- 函数签名
highway.get_od_baseline(
    p_origin_id varchar,
    p_destination_id varchar,
    p_pattern_type varchar,
    p_hour integer
) RETURNS TABLE(...)
```

**示例**：

```sql
-- 查询特定OD对的基准
SELECT * FROM highway.get_od_baseline(
    'G420200100010',
    'G420200100050',
    'workday',
    8
);
```

**返回字段**：

- `mean_flow`, `median_flow`, `p85_flow`, `p95_flow`
- `avg_travel_time`（秒）
- `truck_ratio`, `od_rank`, `sample_count`

---

### 3.3 获取Top OD对

```sql
-- 函数签名
highway.get_top_od_pairs(
    p_limit integer DEFAULT 10,
    p_pattern_type varchar DEFAULT NULL
) RETURNS TABLE(...)
```

**示例**：

```sql
-- 获取Top-50 OD对
SELECT * FROM highway.get_top_od_pairs(50, 'workday');
```

**返回字段**：

- `od_rank`, `origin_id`, `destination_id`
- `od_type_combination`, `avg_flow`, `avg_travel_time`
- `pattern_type`

---

### 3.4 获取收费广场基准

```sql
-- 函数签名
highway.get_tollsquare_baseline(
    p_square_code varchar,
    p_direction varchar,  -- 'entry' 或 'exit'
    p_pattern_type varchar,
    p_hour integer
) RETURNS TABLE(...)
```

**示例**：

```sql
-- 查询收费广场入口基准
SELECT * FROM highway.get_tollsquare_baseline(
    '51044001',
    'entry',
    'workday',
    8
);
```

---

### 3.5 模式类型判定

```sql
-- 函数签名
highway.get_pattern_type_v2(p_date date) RETURNS varchar
```

**示例**：

```sql
-- 判定2025年10月1日的模式
SELECT highway.get_pattern_type_v2('2025-10-01');
-- 返回: 'holiday_free'

-- 判定2025年10月8日
SELECT highway.get_pattern_type_v2('2025-10-08');
-- 返回: 'workday'（调休）
```

**返回值**：

- `workday`：工作日（含调休）
- `weekend`：周末
- `holiday_free`：法定节假日（免费）
- `holiday_nofree`：法定节假日（不免费）

---

## 4. 数据视图

### 4.1 基准数据摘要视图 (v_baseline_summary)

```sql
SELECT * FROM highway.v_baseline_summary;
```

**返回字段**：

- `baseline_batch_id`：批次ID
- `baseline_start_time` / `baseline_end_time`：时间范围
- `gantry_records`, `tollsquare_entry_records`, `od_records`：各表记录数
- `total_records`：总记录数
- `data_quality_score`：数据质量分数
- `is_latest_batch`：是否最新批次

---

### 4.2 OD数据摘要视图 (v_od_summary)

```sql
SELECT * FROM highway.v_od_summary;
```

**返回字段**：

- `od_type_combination`：OD类型
- `pattern_type`：模式类型
- `unique_od_pairs`：唯一OD对数
- `total_records`：总记录数
- `avg_flow`, `min_flow`, `max_flow`：流量统计
- `avg_travel_time_sec`：平均出行时间
- `best_rank`, `worst_rank`：排名范围

**示例输出**：

```
od_type_combination  | pattern_type | unique_od_pairs | avg_flow | avg_travel_time_sec
---------------------+--------------+-----------------+----------+--------------------
gantry-gantry        | workday      |            1448 |   357.98 |              2098.42
tollsquare-tollsquare| workday      |             952 |   237.37 |              1517.81
```

---

### 4.3 路线编码映射摘要 (v_route_code_mapping_summary)

```sql
SELECT * FROM highway.v_route_code_mapping_summary;
```

**返回字段**：

- `dim_route_code`：DIM编码
- `baseline_prefixes`：Baseline前缀数组
- `prefix_count`：前缀数量
- `mapping_type`：映射类型
- `has_verified_mapping`：是否已验证
- `notes`：备注

---

### 4.4 门架-路段映射视图 (v_gantry_edge_mapping)

```sql
SELECT * FROM highway.v_gantry_edge_mapping;
```

**用途**：展示门架与路段的归属关系，支持数据追溯。

---

## 5. 数据统计

### 5.1 总体规模

| 指标         | 数值                     |
| ------------ | ------------------------ |
| 总记录数     | 143,414条                |
| 门架基准记录 | 16,344条                 |
| 节点基准记录 | 49,668条                 |
| 路段基准记录 | 14,832条                 |
| OD基准记录   | 114,022条                |
| 收费广场记录 | 13,601条                 |
| 数据批次     | 1个（20250616_20250713） |

### 5.2 空间覆盖

| 类型              | 数量    |
| ----------------- | ------- |
| 唯一门架数        | 228个   |
| 唯一节点数        | 690个   |
| OD对数（Top-500） | 2,400对 |
| 收费广场数        | 约80个  |

### 5.3 时间覆盖

| 维度         | 覆盖范围                              |
| ------------ | ------------------------------------- |
| 模式类型     | 3种（workday, weekend, holiday_free） |
| 小时粒度     | 0-23小时（24个时间片）                |
| 基准时间范围 | 2025-06-16 ~ 2025-07-13（28天）       |

### 5.4 数据质量

| 指标               | 状态                    |
| ------------------ | ----------------------- |
| 数据质量分数       | 75.00/100               |
| holiday_free缺失数 | 0（已通过补充函数填充） |
| 批次状态           | completed ✅            |

---

## 6. 使用示例

### 6.1 查询门架早高峰基准

```sql
-- 查询G4202路线所有门架的早8点工作日基准
SELECT
    gantry_id,
    mean_flow,
    median_flow,
    p85_flow,
    estimated_capacity,
    truck_ratio,
    avg_speed
FROM highway.baseline_gantry_hourly
WHERE pattern_type = 'workday'
  AND hour = 8
  AND gantry_id LIKE 'G4201%'
ORDER BY mean_flow DESC
LIMIT 10;
```

### 6.2 识别拥堵节点

```sql
-- 查找分流点中流量最高的前10个节点
SELECT
    unit_id,
    unit_name,
    node_type,
    mean_flow,
    p85_flow,
    estimated_capacity,
    ROUND(mean_flow / NULLIF(estimated_capacity, 0) * 100, 2) AS capacity_utilization_pct
FROM highway.baseline_node_hourly
WHERE pattern_type = 'workday'
  AND hour = 18  -- 晚高峰
  AND node_type IN ('diverging', 'merging')
ORDER BY mean_flow DESC
LIMIT 10;
```

### 6.3 分析OD出行时间

```sql
-- 查找出行时间异常长的OD对（可能存在拥堵）
SELECT
    origin_id,
    destination_id,
    mean_flow,
    avg_travel_time,
    ROUND(avg_travel_time / 60, 1) AS travel_time_minutes,
    od_rank
FROM highway.baseline_od_hourly
WHERE pattern_type = 'workday'
  AND hour BETWEEN 7 AND 9
  AND od_type_combination = 'gantry-gantry'
  AND avg_travel_time > 3000  -- 超过50分钟
ORDER BY avg_travel_time DESC
LIMIT 20;
```

### 6.4 对比工作日与周末流量

```sql
-- 对比同一门架在工作日与周末的流量差异
SELECT
    gantry_id,
    hour,
    MAX(CASE WHEN pattern_type = 'workday' THEN mean_flow END) AS workday_flow,
    MAX(CASE WHEN pattern_type = 'weekend' THEN mean_flow END) AS weekend_flow,
    ROUND(
        (MAX(CASE WHEN pattern_type = 'workday' THEN mean_flow END) -
         MAX(CASE WHEN pattern_type = 'weekend' THEN mean_flow END)) /
        NULLIF(MAX(CASE WHEN pattern_type = 'weekend' THEN mean_flow END), 0) * 100,
        2
    ) AS pct_increase
FROM highway.baseline_gantry_hourly
WHERE gantry_id = 'G420200100010'
GROUP BY gantry_id, hour
ORDER BY hour;
```

### 6.5 全路网容量利用率分析

```sql
-- 查看G4202全线全天容量利用率
SELECT
    hour,
    mean_flow,
    total_estimated_capacity,
    avg_capacity_utilization,
    ROUND(avg_capacity_utilization * 100, 2) AS utilization_pct,
    CASE
        WHEN avg_capacity_utilization > 0.85 THEN '拥堵'
        WHEN avg_capacity_utilization > 0.70 THEN '繁忙'
        WHEN avg_capacity_utilization > 0.50 THEN '正常'
        ELSE '畅通'
    END AS traffic_status
FROM highway.baseline_network_hourly
WHERE network_id = 'G4202_NETWORK'
  AND pattern_type = 'workday'
ORDER BY hour;
```

### 6.6 使用查询函数快速查询

```sql
-- 快速查询特定门架基准
SELECT * FROM highway.get_baseline_hourly_simple(
    'G420200100010',
    'workday',
    8
);

-- 快速查询Top-20 OD对
SELECT
    od_rank,
    origin_id,
    destination_id,
    avg_flow,
    ROUND(avg_travel_time / 60, 1) AS travel_time_minutes
FROM highway.get_top_od_pairs(20, 'workday')
ORDER BY od_rank;

-- 查询收费广场流量
SELECT * FROM highway.get_tollsquare_baseline(
    '51044001',
    'entry',
    'workday',
    8
);
```

---

## 7. 数据质量指标

### 7.1 完整性检查

```sql
-- 检查门架数据完整性（每个门架应有3种模式×24小时=72条记录）
SELECT
    gantry_id,
    COUNT(*) AS record_count,
    COUNT(DISTINCT pattern_type) AS pattern_count,
    COUNT(DISTINCT hour) AS hour_count
FROM highway.baseline_gantry_hourly
GROUP BY gantry_id
HAVING COUNT(*) < 72
ORDER BY record_count;
```

### 7.2 异常值检查

```sql
-- 检查流量异常值（P95 < P85 或标准差异常大）
SELECT
    gantry_id,
    pattern_type,
    hour,
    p85_flow,
    p95_flow,
    stddev_flow,
    mean_flow
FROM highway.baseline_gantry_hourly
WHERE p95_flow < p85_flow
   OR stddev_flow > mean_flow * 1.5
ORDER BY gantry_id, hour;
```

### 7.3 样本数量统计

```sql
-- 统计样本数量分布（sample_count = 0 表示补充数据）
SELECT
    pattern_type,
    COUNT(*) FILTER (WHERE sample_count = 0) AS supplemented_records,
    COUNT(*) FILTER (WHERE sample_count > 0) AS original_records,
    ROUND(
        COUNT(*) FILTER (WHERE sample_count = 0)::numeric /
        COUNT(*) * 100,
        2
    ) AS supplement_pct
FROM highway.baseline_gantry_hourly
GROUP BY pattern_type;
```

### 7.4 OD覆盖率分析

```sql
-- 分析OD基准覆盖情况
SELECT
    od_type_combination,
    pattern_type,
    COUNT(DISTINCT origin_id || '-' || destination_id) AS unique_pairs,
    SUM(mean_flow) AS total_flow,
    AVG(avg_travel_time) AS avg_travel_time_sec
FROM highway.baseline_od_hourly
GROUP BY od_type_combination, pattern_type
ORDER BY od_type_combination, pattern_type;
```

---

## 8. 注意事项

### 8.1 数据使用规范

1. **批次管理**

   - 始终通过 `baseline_batch_id` 追溯数据版本
   - 使用 `v_baseline_summary.is_latest_batch` 确认是否最新数据
2. **模式选择**

   - 使用 `highway.get_pattern_type_v2(date)` 自动判定模式
   - 调休日归类为 `workday`，不要误用 `weekend`
3. **流量分位数**

   - `p85_flow`：接近峰值，适合容量估算
   - `p95_flow`：极端峰值，由 `p85 × 1.1` 估算
   - `median_flow`：中位数，抗异常值干扰
4. **容量估算**

   - `estimated_capacity = p85_flow / 0.85`
   - 基于HCM理论（Highway Capacity Manual）
   - 仅供参考，非设计容量

### 8.2 数据局限性

1. **OD基准覆盖不全**

   - 当前仅覆盖 Top-500 OD对（约20.37%覆盖率）
   - 缺失 `holiday_free` 模式OD数据
   - 长尾OD对需单独查询源数据
2. **holiday_free补充数据**

   - 部分 `holiday_free` 数据由 `workday` 插值生成
   - `sample_count = 0` 表示补充数据，可信度较低
3. **时间范围限制**

   - 当前批次仅覆盖28天（2025-06-16 ~ 2025-07-13）
   - 季节性变化需跨批次分析

### 8.3 性能优化建议

1. **使用索引字段查询**

   - 优先使用 `gantry_id`, `pattern_type`, `hour` 组合
   - OD查询优先使用 `od_rank` 过滤
2. **使用查询函数**

   - `get_baseline_hourly_simple()` 已优化索引
   - `get_top_od_pairs()` 已缓存热点数据
3. **避免全表扫描**

   - 大批量查询使用 `baseline_batch_id` 分区
   - 时间范围查询使用 `hour BETWEEN` 而非 `hour IN`

---

## 9. 更新日志

### v1.0 (2025-10-03)

- ✅ 初始版本发布
- ✅ 覆盖10张核心表
- ✅ 20个查询函数
- ✅ 4个数据视图
- ✅ 143,414条基准记录
- ✅ 数据批次：20250616_20250713

---

## 10. 相关文档

- [数据源整合方案 v3.1](../03-开发方案/数据源整合方案-v3.1.md)
- [Phase2A 多尺度聚合方案](../03-开发方案/Phase2A-多尺度聚合方案.md)
- [Phase2B 收费广场基准方案](../03-开发方案/Phase2B-收费广场基准方案.md)
- [Phase2C OD基准导入方案](../03-开发方案/Phase2C-OD基准导入方案.md)
- [路线编码映射问题](../03-开发方案/Phase2A-路线编码映射问题.md)

---

**文档维护者**: HOMDS开发团队
**最后更新**: 2025-10-03
**联系方式**: 参见项目 README.md

---

## 11. v0.8.0 升级：Highway 表清单与状态

以下根据实际数据库内 `highway` schema 的表清单（估算行数）与《v0.8.0升级方案》进行对照，给出各表在 v0.8.0 Phase1 的处置建议：

### 11.1 表状态矩阵（核心 + 辅助）

| 表名                              | 估算行数 | 状态             | 说明                                                                         |
| --------------------------------- | -------: | ---------------- | ---------------------------------------------------------------------------- |
| `batch_kpi_summary`             |  182,922 | 保留（核心）     | v0.8.0 核心批次KPI结果表，4维度×4模式；统一KPI入口                          |
| `weekly_pattern_kpi`            |  100,526 | 保留（核心）     | 周模式KPI（Mon~Sun），支撑周模式系数等派生指标                               |
| `truck_impact_analysis`         |  182,922 | 保留（核心）     | 货车影响量化（协方差、贡献度等）                                             |
| `historical_baseline`           |      N/A | 保留（核心）     | 3个月滚动基线与阈值（μ±2σ），趋势检测输入                                 |
| `kpi_trend_alert`               |      N/A | 保留（核心）     | 趋势预警记录，含偏离σ与告警等级                                             |
| `route_code_mapping`            |      N/A | 保留（基础）     | 路线编码映射（DIM→Baseline），生产依赖                                      |
| `baseline_metadata`             |       13 | 保留（基础）     | 批次元数据与规模统计，视图 `v_baseline_summary` 的基础                     |
| `kpi_od_summary`                |        - | 已删除           | 统一到 `batch_kpi_summary`（OD维度KPI从该表查询）                          |
| `kpi_tollsquare_summary`        |        - | 已删除           | 统一到 `batch_kpi_summary`（收费广场维度KPI从该表查询）                    |
| `anomaly_summary`               |   22,974 | 建议保留（辅助） | 异常小时聚合的中间结果，供热点视图 `v_anomaly_hotspots` 使用               |
| `batch_baseline_overview`       |       14 | 保留（辅助）     | 批次级Baseline概览统计（轻量）                                               |
| `batch_dwd_overview`            |      112 | 保留（辅助）     | 批次级DWD输入概览（监控）                                                    |
| `batch_trends`                  |      N/A | 建议废弃/迁移    | 与趋势预警功能重叠，统一迁移到 `kpi_trend_alert`/相关函数                  |
| `batch_quality_score`           |      N/A | 建议废弃/迁移    | 质量评分建议迁移到方案内的 `baseline_quality_report`（本库未见，计划新增） |
| `batch_quality_summary`         |      N/A | 建议废弃/迁移    | 同上，迁移到质量报告表/视图体系                                              |
| `batch_analysis_gantry`         |      N/A | 建议归档         | 临时/分析产物，后续以视图/物化视图替代                                       |
| `batch_analysis_od`             |      N/A | 建议归档         | 同上                                                                         |
| `batch_analysis_tollsquare_on`  |      N/A | 建议归档         | 同上                                                                         |
| `batch_analysis_tollsquare_off` |      N/A | 建议归档         | 同上                                                                         |
| `entity_distance`               |      N/A | 保留（辅助）     | 实体间距离缓存（若存在），供速度/时耗换算                                    |
| `od_route_distance`             |    3,000 | 保留（辅助）     | OD距离（SUMO/时间法混合），被 `v_od_distance_hybrid` 使用                  |

说明：

- N/A 表示系统估算行数不可用或目前为空表；不影响结构与状态判断。
- “建议合并/过渡”：建议将字段与口径对齐 `batch_kpi_summary`，中期改造为视图或物化视图。
- “建议废弃/迁移/归档”：不立即删除，先冻结写入并由新表/函数/视图替代，确保查询链路平滑切换。

### 11.2 视图（参考）

- `v_anomaly_hotspots`：基于 `anomaly_summary` 的异常热点打分聚合。
- `v_baseline_summary`：汇总 `baseline_metadata` 与 `baseline.baseflow_batch_stat`，输出批次级摘要。
- `v_top3000_od_pairs` / `v_od_distance_hybrid`：OD优先级与距离融合视图，服务于OD分析与速度/拥堵指标推导。
- `v_route_code_mapping_summary`：路线映射汇总视图。

### 11.3 与升级方案的差异与待办

- 方案中的 `baseline_quality_report`、质量检查与修复函数目前未见实际建表；待 Phase1/2 落地后补充（不影响KPI主链路）。
- `kpi_od_summary`、`kpi_tollsquare_summary` 等历史汇总表建议逐步并入 `batch_kpi_summary` 统一出口，减少多口径。
- 趋势相关中间表（如 `batch_trends`）统一迁移到 `historical_baseline` + `kpi_trend_alert` + 检测函数的组合。

### 11.4 查询示例（行数/结构）

仅示例结构/规模查询，避免拉取实际数据：

```sql
-- 列出highway全部表与估算行数
SELECT n.nspname AS schema_name,
       c.relname AS table_name,
       c.reltuples::bigint AS est_rows
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'highway' AND c.relkind = 'r'
ORDER BY c.relname;

-- 查看指定表的列（不返回数据）
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_schema='highway' AND table_name='batch_kpi_summary'
ORDER BY ordinal_position;
```

### 11.5 表结构与字段说明（v0.8.0 重点）

以下字段清单依据当前升级方案与现有脚本约定汇总，供开发与数据消费参考（不含数据行）。

#### 11.5.1 `highway.batch_kpi_summary`

- 主键：`(batch_id, dimension, entity_id, pattern_type)`
- 关键字段：
  - `batch_id`：批次ID（周窗口）
  - `dimension`：维度（gantry|tollsquare_entry|tollsquare_exit|od）
  - `entity_id`：实体标识（如门架ID/收费广场编码/OD键）
  - `pattern_type`：模式（workday|weekend|holiday_free|holiday_nofree）
  - 字段（字段名: 类型 [可空]）：
    - `batch_id`: varchar [NO]
    - `dimension`: varchar [NO]
    - `entity_id`: varchar [NO]
    - `pattern_type`: varchar [NO]
    - `mtt_mean`: numeric [YES]
    - `mtt_p85`: numeric [YES]
    - `mtt_std`: numeric [YES]
    - `speed_mean`: numeric [YES]
    - `speed_p85`: numeric [YES]
    - `free_flow_speed`: numeric [YES]
    - `flow_p85`: numeric [YES]
    - `flow_p95`: numeric [YES]
    - `flow_mean`: numeric [YES]
    - `throughput_capacity`: numeric [YES]
    - `vc_ratio`: numeric [YES]
    - `congestion_hours`: numeric [YES]
    - `speed_data_quality`: varchar [YES]
    - `speed_coverage_pct`: numeric [YES]
    - `has_speed_gaps`: boolean [YES]
    - `data_points_count`: integer [YES]
    - `distance_km`: numeric [YES]
    - `created_at`: timestamp [YES]
    - `updated_at`: timestamp [YES]
    - `tt50`: numeric [YES]
    - `tt85`: numeric [YES]
    - `tt95`: numeric [YES]
    - `flow_p50`: numeric [YES]
    - `speed_std`: numeric [YES]
    - `throughput_total`: numeric [YES]
    - `estimated_capacity`: numeric [YES]
    - `capacity_utilization`: numeric [YES]
    - `speed_volatility_index`: numeric [YES]
    - `peak_dispersion`: numeric [YES]
    - `capacity_redundancy`: numeric [YES]
    - `sample_count`: integer [YES]
    - `data_completeness`: numeric [YES]

#### 11.5.2 `highway.weekly_pattern_kpi`

- 主键：`(batch_id, dimension, entity_id)`
- 关键字段：
  - 字段（字段名: 类型 [可空]）：
    - `batch_id`: varchar [NO]
    - `dimension`: varchar [NO]
    - `entity_id`: varchar [NO]
    - `monday_mtt`: numeric [YES]
    - `tuesday_mtt`: numeric [YES]
    - `wednesday_mtt`: numeric [YES]
    - `thursday_mtt`: numeric [YES]
    - `friday_mtt`: numeric [YES]
    - `saturday_mtt`: numeric [YES]
    - `sunday_mtt`: numeric [YES]
    - `weekday_avg_mtt`: numeric [YES]
    - `weekend_avg_mtt`: numeric [YES]
    - `weekly_pattern_coef`: numeric [YES]
    - `weekday_data_points`: integer [YES]
    - `weekend_data_points`: integer [YES]
    - `created_at`: timestamp [YES]
    - `monday_flow`: numeric [YES]
    - `tuesday_flow`: numeric [YES]
    - `wednesday_flow`: numeric [YES]
    - `thursday_flow`: numeric [YES]
    - `friday_flow`: numeric [YES]
    - `saturday_flow`: numeric [YES]
    - `sunday_flow`: numeric [YES]
    - `weekday_weekend_ratio`: numeric [YES]
    - `friday_premium`: numeric [YES]

#### 11.5.3 `highway.truck_impact_analysis`

- 主键：`(batch_id, dimension, entity_id, pattern_type)`
- 关键字段：
  - 字段（字段名: 类型 [可空]）：
    - `batch_id`: varchar [NO]
    - `dimension`: varchar [NO]
    - `entity_id`: varchar [NO]
    - `pattern_type`: varchar [NO]
    - `truck_ratio_mean`: numeric [YES]
    - `truck_ratio_std`: numeric [YES]
    - `truck_ratio_peak`: numeric [YES]
    - `truck_mtt_contribution`: numeric [YES]
    - `truck_speed_penalty`: numeric [YES]
    - `cov_truck_mtt`: numeric [YES]
    - `corr_truck_mtt`: numeric [YES]
    - `data_points_count`: integer [YES]
    - `created_at`: timestamp [YES]

#### 11.5.4 `highway.historical_baseline`

**用途**：存储3个月滚动窗口的历史基线数据，用于趋势监测和异常检测。

**数据来源**：基于 `highway.batch_kpi_summary` 表的历史批次数据聚合生成。

**更新机制**：
- 使用函数 `highway.update_historical_baseline(dimension, lookback_months)` 更新
- 默认使用3个月滚动窗口（`lookback_months=3`）
- 支持维度：`gantry`, `od`, `tollsquare_on`, `tollsquare_off`
- 特殊处理：`tollsquare` 维度会自动更新 `tollsquare_on` 和 `tollsquare_off` 两个子维度

**数据特点**：
- 主键：`(dimension, entity_id, pattern_type)`
- 统计基线：基于历史批次计算均值和标准差
- 阈值设置：μ ± 2σ（均值 ± 2倍标准差）
- 元数据：记录基线批次列表、时间范围、更新时间

**关键字段**：
  - 字段（字段名: 类型 [可空]）：
    - `dimension`: varchar [NO]
    - `entity_id`: varchar [NO]
    - `pattern_type`: varchar [NO]
    - `mtt_baseline_mean`: numeric [YES]
    - `mtt_baseline_std`: numeric [YES]
    - `speed_baseline_mean`: numeric [YES]
    - `speed_baseline_std`: numeric [YES]
    - `flow_baseline_mean`: numeric [YES]
    - `flow_baseline_std`: numeric [YES]
    - `mtt_upper_threshold`: numeric [YES]
    - `mtt_lower_threshold`: numeric [YES]
    - `speed_upper_threshold`: numeric [YES]
    - `speed_lower_threshold`: numeric [YES]
    - `flow_upper_threshold`: numeric [YES]
    - `flow_lower_threshold`: numeric [YES]
    - `baseline_batch_ids`: ARRAY [YES]
    - `baseline_batch_count`: integer [YES]
    - `baseline_start_date`: date [YES]
    - `baseline_end_date`: date [YES]
    - `baseline_updated_at`: timestamp [YES]

**使用示例**：
```sql
-- 更新门架维度的历史基线
SELECT highway.update_historical_baseline('gantry', 3);

-- 更新OD维度的历史基线
SELECT highway.update_historical_baseline('od', 3);

-- 更新收费广场维度（自动处理on和off）
SELECT highway.update_historical_baseline('tollsquare', 3);

-- 查询历史基线数据
SELECT entity_id, pattern_type, 
       mtt_baseline_mean, speed_baseline_mean, flow_baseline_mean,
       baseline_batch_count, baseline_start_date, baseline_end_date
FROM highway.historical_baseline 
WHERE dimension = 'gantry' 
  AND entity_id = 'G000551001000110010'
ORDER BY pattern_type;
```

#### 11.5.5 `highway.kpi_trend_alert`

- 主键：`alert_id`（自增）
- 关键字段：
  - 字段（字段名: 类型 [可空]）：
    - `alert_id`: integer [NO]
    - `batch_id`: varchar [NO]
    - `dimension`: varchar [NO]
    - `entity_id`: varchar [NO]
    - `pattern_type`: varchar [NO]
    - `kpi_name`: varchar [NO]
    - `current_value`: numeric [YES]
    - `baseline_mean`: numeric [YES]
    - `baseline_std`: numeric [YES]
    - `deviation_value`: numeric [YES]
    - `deviation_sigma`: numeric [YES]
    - `t_statistic`: numeric [YES]
    - `p_value`: numeric [YES]
    - `is_significant`: boolean [YES]
    - `trend_direction`: varchar [YES]
    - `alert_level`: varchar [YES]
    - `consecutive_batches`: integer [YES]
    - `primary_driver`: varchar [YES]
    - `driver_contribution_pct`: numeric [YES]
    - `secondary_driver`: varchar [YES]
    - `alert_message`: text [YES]
    - `created_at`: timestamp [YES]

#### 11.5.6 `highway.route_code_mapping`

- 主键：`(dim_route_code, baseline_code_prefix)`
- 字段：`dim_route_code`, `baseline_code_prefix`, `mapping_type`, `notes`, `verified`, `created_at`, `updated_at`

#### 11.5.7 `highway.baseline_metadata`

- 主键：`baseline_batch_id`
- 字段：
  - 时间：`baseline_start_time`, `baseline_end_time`, `highway_process_time`
  - 处理：`highway_process_status`, `is_latest_batch`（可由关联得到）
  - 规模：`gantry_records`, `tollsquare_entry_records`, `tollsquare_exit_records`, `od_records`, `facility_records`, `network_records`, `od_pairs`, `total_records`
  - 质量：`data_quality_score`, `missing_holiday_free_count`
  - 维护：`created_at`, `updated_at`

#### 11.5.8 `highway.anomaly_summary`

- 用途：异常小时聚合汇总（被 `v_anomaly_hotspots` 使用）
- 常见字段：`batch_id`, `unit_type`, `unit_id`, `pattern_type`, `anomaly_level`, `severe_anomaly_hours`, `high_anomaly_hours`, `low_anomaly_hours`, `max_z_score`, `min_z_score`, `total_hours`

#### 11.5.9 `highway.kpi_od_summary`

- 用途：OD口径KPI汇总（建议过渡至 `batch_kpi_summary`）
- 常见字段：`batch_id`, `origin_id`, `destination_id`, `pattern_type`, `mtt_mean`, `flow_mean`, 以及与OD分析相关的派生统计

#### 11.5.10 `highway.kpi_tollsquare_summary`

- 用途：收费广场口径KPI汇总（建议过渡至 `batch_kpi_summary`）
- 常见字段：`batch_id`, `square_code`, `direction`（entry/exit）, `pattern_type`, `flow_mean`, `flow_p85`, 车型占比等

#### 11.5.11 `highway.batch_baseline_overview`

- 用途：批次级Baseline摘要（轻量）
- 常见字段：`baseline_batch_id`, 各维度记录数、覆盖率、是否最新批次标记等

#### 11.5.12 `highway.batch_dwd_overview`

- 用途：输入侧DWD批次与供给质量监控
- 常见字段：`batch_id`, 数据量、门架/收费场站覆盖、关键字段缺失计数等

#### 11.5.13 `highway.od_route_distance`

- 主键：可为 `(origin_id, destination_id)` 或包含优先级字段
- 字段：`origin_id`, `destination_id`, `sumo_distance_km`, `time_based_distance_km`, `distance_source`, `sumo_edge_count`, `sumo_edges`, `sumo_coverage_pct`, `sumo_calculated_at`, `time_based_calculated_at`, `updated_at`, `is_top_3000`, `priority_rank`

#### 11.5.14 `highway.entity_distance`

- 用途：实体（门架/节点/广场）距离缓存，支撑速度/时耗换算
- 字段：实体A/B标识、类型、距离（km）、来源、更新时间等
