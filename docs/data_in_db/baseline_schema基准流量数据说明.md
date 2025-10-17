# 基准流量数据说明

**Schema**: `baseline`
**版本**: v0.8.0
**更新时间**: 2025-10-07
**v0.8.1说明**: baseline schema结构无变化，仅highway层KPI系统有更新（详见 [highway_schema数据说明.md](highway_schema数据说明.md)）

## 概述

baseline schema 存储基准流量模式数据，用于高速公路路网仿真的基础流量输入。数据包括四个空间维度（门架、OD对、收费广场驶入、收费广场驶离）的基准流量模式，支持多种时间模式（工作日、周末、节假日等）。

## 数据来源

基准流量数据通过历史实测流量数据的统计分析生成，统计周期以批次（batch）管理。当前数据集覆盖多个批次的流量模式数据。

## 表结构

### 1. baseflow_batch_stat - 批次统计表

**用途**: 记录基准流量数据生成批次的元信息（该表更新有异常，请暂不使用）


| 字段          | 类型         | 说明           |
| ------------- | ------------ | -------------- |
| id            | INTEGER      | 自增ID（主键） |
| batch_id      | VARCHAR(50)  | 批次ID         |
| data_type     | VARCHAR(32)  | 数据类型       |
| start_time    | TIMESTAMP    | 统计开始时间   |
| end_time      | TIMESTAMP    | 统计结束时间   |
| generate_time | TIMESTAMP    | 生成时间       |
| data_count    | INTEGER      | 数据条数       |
| is_latest     | BOOLEAN      | 是否最新批次   |
| remark        | VARCHAR(200) | 备注           |

**数据规模**: 63 条

---

### 2. baseflow_pattern_gantry - 门架流量模式表

**用途**: 存储各门架点位的24小时分时段流量统计模式

| 字段              | 类型          | 说明                |
| ----------------- | ------------- | ------------------- |
| gantry_id         | VARCHAR(50)   | 门架ID（主键1）     |
| pattern_type      | VARCHAR(50)   | 模式类型（主键2）   |
| hour              | INTEGER       | 小时（主键3，0-23） |
| batch_id          | VARCHAR(20)   | 批次ID（主键4）     |
| mean              | NUMERIC(10,2) | 流量均值            |
| stddev            | NUMERIC(10,2) | 流量标准差          |
| median            | NUMERIC(10,2) | 流量中位数          |
| p75               | NUMERIC(10,2) | 75分位数            |
| p85               | NUMERIC(10,2) | 85分位数            |
| data_points_count | INTEGER       | 统计样本点数        |
| passenger_small   | NUMERIC(12,2) | 客车小型车流量      |
| passenger_large   | NUMERIC(12,2) | 客车大型车流量      |
| truck_small       | NUMERIC(12,2) | 货车小型车流量      |
| truck_large       | NUMERIC(12,2) | 货车大型车流量      |
| special_small     | NUMERIC(12,2) | 专项小型车流量      |
| special_large     | NUMERIC(12,2) | 专项大型车流量      |
| truck_ratio       | NUMERIC(6,4)  | 货车占比            |
| update_time       | TIMESTAMP     | 更新时间            |
| avg_speed         | NUMERIC(6,2)  | 平均速度（km/h）    |
| speed_stddev      | NUMERIC(6,2)  | 速度标准差          |
| speed_p50         | NUMERIC(6,2)  | 速度中位数          |
| speed_p85         | NUMERIC(6,2)  | 速度85分位数        |
| free_flow_speed   | NUMERIC(6,2)  | 自由流速度          |
| avg_duration      | NUMERIC(10,2) | 平均行程时间（秒）  |
| distance_km       | NUMERIC(10,2) | 距离（公里）        |

**数据规模**: 180,934 条
**索引**:

- 主键索引：(gantry_id, pattern_type, hour, batch_id)
- batch_id 索引

**模式类型**:

- `workday` - 工作日模式
- `weekend` - 周末模式
- `holiday_nofree` - 节假日非免费模式

---

### 3. baseflow_pattern_od - OD流量模式表

**用途**: 存储起讫点（OD）对的24小时分时段流量统计模式

| 字段                | 类型          | 说明                |
| ------------------- | ------------- | ------------------- |
| origin_id           | VARCHAR(100)  | 起点ID（主键1）     |
| destination_id      | VARCHAR(100)  | 终点ID（主键2）     |
| origin_type         | VARCHAR(20)   | 起点类型            |
| destination_type    | VARCHAR(20)   | 终点类型            |
| od_type_combination | VARCHAR(30)   | OD类型组合          |
| pattern_type        | VARCHAR(50)   | 模式类型（主键3）   |
| hour                | INTEGER       | 小时（主键4，0-23） |
| batch_id            | VARCHAR(20)   | 批次ID（主键5）     |
| mean                | NUMERIC(10,2) | 流量均值            |
| stddev              | NUMERIC(10,2) | 流量标准差          |
| median              | NUMERIC(10,2) | 流量中位数          |
| p75                 | NUMERIC(10,2) | 75分位数            |
| p85                 | NUMERIC(10,2) | 85分位数            |
| data_points_count   | INTEGER       | 统计样本点数        |
| avg_travel_time     | NUMERIC(10,2) | 平均行程时间（秒）  |
| passenger_small     | NUMERIC(12,2) | 客车小型车流量      |
| passenger_large     | NUMERIC(12,2) | 客车大型车流量      |
| truck_small         | NUMERIC(12,2) | 货车小型车流量      |
| truck_large         | NUMERIC(12,2) | 货车大型车流量      |
| special_small       | NUMERIC(12,2) | 专项小型车流量      |
| special_large       | NUMERIC(12,2) | 专项大型车流量      |
| truck_ratio         | NUMERIC(6,4)  | 货车占比            |
| update_time         | TIMESTAMP     | 更新时间            |

**数据规模**: 2,220,272 条
**索引**:

- 主键索引：(origin_id, destination_id, pattern_type, hour, batch_id)
- batch_id 索引

---

### 4. baseflow_pattern_tollsquare_off - 收费广场驶离流量模式表

**用途**: 存储收费广场驶离方向的24小时分时段流量统计模式

| 字段              | 类型          | 说明                  |
| ----------------- | ------------- | --------------------- |
| square_code       | VARCHAR(50)   | 收费广场代码（主键1） |
| pattern_type      | VARCHAR(50)   | 模式类型（主键2）     |
| hour              | INTEGER       | 小时（主键3，0-23）   |
| batch_id          | VARCHAR(20)   | 批次ID（主键4）       |
| mean              | NUMERIC(10,2) | 流量均值              |
| stddev            | NUMERIC(10,2) | 流量标准差            |
| median            | NUMERIC(10,2) | 流量中位数            |
| p75               | NUMERIC(10,2) | 75分位数              |
| p85               | NUMERIC(10,2) | 85分位数              |
| data_points_count | INTEGER       | 统计样本点数          |
| passenger_small   | NUMERIC(12,2) | 客车小型车流量        |
| passenger_large   | NUMERIC(12,2) | 客车大型车流量        |
| truck_small       | NUMERIC(12,2) | 货车小型车流量        |
| truck_large       | NUMERIC(12,2) | 货车大型车流量        |
| special_small     | NUMERIC(12,2) | 专项小型车流量        |
| special_large     | NUMERIC(12,2) | 专项大型车流量        |
| truck_ratio       | NUMERIC(6,4)  | 货车占比              |
| update_time       | TIMESTAMP     | 更新时间              |

**数据规模**: 111,900 条
**索引**:

- 主键索引：(square_code, pattern_type, hour, batch_id)
- batch_id 索引

---

### 5. baseflow_pattern_tollsquare_on - 收费广场驶入流量模式表

**用途**: 存储收费广场驶入方向的24小时分时段流量统计模式

| 字段              | 类型          | 说明                  |
| ----------------- | ------------- | --------------------- |
| square_code       | VARCHAR(50)   | 收费广场代码（主键1） |
| pattern_type      | VARCHAR(50)   | 模式类型（主键2）     |
| hour              | INTEGER       | 小时（主键3，0-23）   |
| batch_id          | VARCHAR(20)   | 批次ID（主键4）       |
| mean              | NUMERIC(10,2) | 流量均值              |
| stddev            | NUMERIC(10,2) | 流量标准差            |
| median            | NUMERIC(10,2) | 流量中位数            |
| p75               | NUMERIC(10,2) | 75分位数              |
| p85               | NUMERIC(10,2) | 85分位数              |
| data_points_count | INTEGER       | 统计样本点数          |
| passenger_small   | NUMERIC(12,2) | 客车小型车流量        |
| passenger_large   | NUMERIC(12,2) | 客车大型车流量        |
| truck_small       | NUMERIC(12,2) | 货车小型车流量        |
| truck_large       | NUMERIC(12,2) | 货车大型车流量        |
| special_small     | NUMERIC(12,2) | 专项小型车流量        |
| special_large     | NUMERIC(12,2) | 专项大型车流量        |
| truck_ratio       | NUMERIC(6,4)  | 货车占比              |
| update_time       | TIMESTAMP     | 更新时间              |

**数据规模**: 113,777 条
**索引**:

- 主键索引：(square_code, pattern_type, hour, batch_id)
- batch_id 索引

---

## 数据统计汇总

| 表名                            | 记录数              | 主要用途                 |
| ------------------------------- | ------------------- | ------------------------ |
| baseflow_batch_stat             | 63                  | 批次元数据管理           |
| baseflow_pattern_gantry         | 180,934             | 门架点位流量模式         |
| baseflow_pattern_od             | 2,220,272           | OD对流量模式（核心数据） |
| baseflow_pattern_tollsquare_off | 111,900             | 收费广场驶离流量模式     |
| baseflow_pattern_tollsquare_on  | 113,777             | 收费广场驶入流量模式     |
| **总计**                  | **2,626,946** | -                        |

## 使用场景

### 1. 仿真基准流量输入

基准流量模式数据用于为仿真路网提供24小时分时段的流量输入，支持多种典型日类型：

```sql
-- 查询工作日某门架的24小时流量模式（使用最新批次）
SELECT
    hour,
    mean as avg_flow,
    avg_speed,
    truck_ratio,
    passenger_small + passenger_large as passenger_flow,
    truck_small + truck_large as truck_flow
FROM baseline.baseflow_pattern_gantry
WHERE gantry_id = 'G001'
  AND pattern_type = 'workday'
  AND batch_id = (SELECT batch_id FROM baseline.baseflow_batch_stat
                  WHERE is_latest = true AND data_type = 'gantry' LIMIT 1)
ORDER BY hour;
```

### 2. OD流量分析

```sql
-- 查询特定OD对的流量模式
SELECT
    hour,
    mean as avg_flow,
    avg_travel_time,
    truck_ratio
FROM baseline.baseflow_pattern_od
WHERE origin_id = 'TOLL_A'
  AND destination_id = 'TOLL_B'
  AND pattern_type = 'workday'
  AND batch_id = (SELECT batch_id FROM baseline.baseflow_batch_stat
                  WHERE is_latest = true AND data_type = 'od' LIMIT 1)
ORDER BY hour;
```

### 3. 收费广场流量对比

```sql
-- 对比收费广场驶入/驶出流量
SELECT
    t_on.hour,
    t_on.mean as inflow,
    t_off.mean as outflow,
    (t_on.mean - t_off.mean) as flow_diff
FROM baseline.baseflow_pattern_tollsquare_on t_on
JOIN baseline.baseflow_pattern_tollsquare_off t_off
  ON t_on.square_code = t_off.square_code
  AND t_on.pattern_type = t_off.pattern_type
  AND t_on.hour = t_off.hour
  AND t_on.batch_id = t_off.batch_id
WHERE t_on.square_code = 'SQ001'
  AND t_on.pattern_type = 'workday'
ORDER BY t_on.hour;
```

### 4. 门架速度分析

```sql
-- 查询门架速度统计信息
SELECT
    gantry_id,
    hour,
    avg_speed,
    speed_stddev,
    speed_p50,
    speed_p85,
    free_flow_speed
FROM baseline.baseflow_pattern_gantry
WHERE pattern_type = 'workday'
  AND batch_id = (SELECT batch_id FROM baseline.baseflow_batch_stat
                  WHERE is_latest = true AND data_type = 'gantry' LIMIT 1)
ORDER BY gantry_id, hour;
```

## 数据质量说明

### 统计指标

每条流量模式记录包含以下统计指标：

- **mean**: 均值（主要使用指标）
- **stddev**: 标准差（反映波动性）
- **median**: 中位数（抗异常值）
- **p75/p85**: 75/85分位数（高峰流量参考）
- **data_points_count**: 样本数量（数据可靠性指标）

### 车型分类

流量按6类车型统计：

- passenger_small: 客车-小型车（1类车）
- passenger_large: 客车-大型车（2类车）
- truck_small: 货车-小型货车（3类车）
- truck_large: 货车-大型货车（4-5类车）
- special_small: 专项-小型专项车
- special_large: 专项-大型专项车

### 速度数据增强

门架流量模式表新增了丰富的速度统计信息：

- **avg_speed**: 平均速度（km/h）
- **speed_stddev**: 速度标准差
- **speed_p50**: 速度中位数
- **speed_p85**: 速度85分位数
- **free_flow_speed**: 自由流速度
- **avg_duration**: 平均行程时间（秒）
- **distance_km**: 距离（公里）

### 数据更新策略

- 批次ID格式：`YYYYMMDD_YYYYMMDD`（统计起止日期）
- 通过 `baseflow_batch_stat.is_latest` 标识最新批次
- 历史批次保留用于对比分析

## 注意事项

1. **数据量级**: OD流量模式表超过480万条记录，查询时建议加索引过滤条件
2. **批次选择**: 生产环境应使用 `is_latest=true` 的最新批次数据
3. **模式类型**: 多种模式类型适用于不同日历场景，需根据仿真日期选择
4. **时间粒度**: 当前数据为小时级（0-23），未来可扩展至更细粒度
5. **速度数据**: 门架表新增了完整的速度统计信息，可用于交通流分析
6. **数据完整性**: 所有表都包含完整的车型分类和统计指标

## 相关文档

- [多尺度分析单元数据说明.md](多尺度分析单元数据说明.md)
- [仿真路网基础数据说明.md](仿真路网基础数据说明.md)
- [示范路网基础设施静态数据说明.md](示范路网基础设施静态数据说明.md)
