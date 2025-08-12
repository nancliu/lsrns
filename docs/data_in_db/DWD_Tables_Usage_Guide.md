# DWD数据表使用说明

## 📋 概述

本文档为开发人员和课题研究人员提供DWD层数据表的使用指南。DWD schema 增加4个按周分区的数据表和1个数据目录表，用于高效存储和查询动态更新的交通流量数据，数据来自蜀道云控。

## 📊 数据表概览

### 主要数据表

| 表名                            | 用途     | 分区策略 | 数据量(阶段统计，增加中) |
| ------------------------------- | -------- | -------- | ------------------------ |
| `dwd.dwd_od_weekly`           | OD数据   | 按周分区 | 36,917,917条             |
| `dwd.dwd_flow_gantry_weekly`  | 门架流量 | 按周分区 | 1,785,795条              |
| `dwd.dwd_flow_offramp_weekly` | 出口流量 | 按周分区 | 970,021条                |
| `dwd.dwd_flow_onramp_weekly`  | 入口流量 | 按周分区 | 972,146条                |

### 数据目录表

| 表名                     | 用途           | 记录数 |
| ------------------------ | -------------- | ------ |
| `dwd.dwd_data_catalog` | 数据可用性目录 | 112条  |

## 📅 当前数据时间范围

### 当前数据覆盖期间

- **起始日期**: 2025年6月9日
- **结束日期**: 2025年7月6日
- **总天数**: 28天
- **覆盖周数**: 4周

### 分区分布

```sql
-- 查看当前数据分区分布
SELECT 
    table_name,
    COUNT(*) as days_count,
    MIN(data_date) as start_date,
    MAX(data_date) as end_date,
    COUNT(DISTINCT week_start) as weeks_count
FROM dwd.dwd_data_catalog
GROUP BY table_name
ORDER BY table_name;
```

**预期结果：**

| table_name              | days_count | start_date | end_date   | weeks_count |
| ----------------------- | ---------- | ---------- | ---------- | ----------- |
| dwd_flow_gantry_weekly  | 28         | 2025-06-09 | 2025-07-06 | 4           |
| dwd_flow_offramp_weekly | 28         | 2025-06-09 | 2025-07-06 | 4           |
| dwd_flow_onramp_weekly  | 28         | 2025-06-09 | 2025-07-06 | 4           |
| dwd_od_weekly           | 28         | 2025-06-09 | 2025-07-06 | 4           |

## 🔄 数据更新机制

### 按周分区更新

数据表采用按周分区策略，每周的数据存储在独立的分区中：

```sql
-- 查看分区命名规则
-- 格式：表名_YYYY_WW（年份_周数）
-- 示例：dwd_od_weekly_2025_24 表示2025年第24周的数据
```

### 分区示例

- `dwd_od_weekly_2025_24` - 2025年第24周（6月9-15日）
- `dwd_od_weekly_2025_25` - 2025年第25周（6月16-22日）
- `dwd_od_weekly_2025_26` - 2025年第26周（6月23-29日）
- `dwd_od_weekly_2025_27` - 2025年第27周（6月30日-7月6日）

### 数据更新频率

- **历史数据**: 已完成导入，数据稳定
- **增量数据**: 按批次每周导入上一周数据时自动创建新分区
- **数据目录**: 每次数据导入后自动更新

## 🔍 数据可用性检查

### 使用数据目录表检查数据是否存在

```sql
-- 1. 检查指定日期范围的数据可用性
SELECT * FROM dwd.user_check_data_availability(
    'dwd_od_weekly',           -- 表名
    '2025-06-15'::DATE,        -- 开始日期
    '2025-06-20'::DATE         -- 结束日期
);
```

### 快速检查数据概览

```sql
-- 2. 查看所有表的数据概览
SELECT * FROM dwd.user_get_table_data_summary()
ORDER BY table_name;
```

### 检查特定时间段数据

```sql
-- 3. 检查某个表在指定日期是否有数据
SELECT 
    data_date,
    is_available,
    record_count,
    data_status
FROM dwd.user_check_data_availability('dwd_flow_gantry_weekly', '2025-06-25', '2025-06-25')
WHERE is_available = true;
```

### 批量检查多个日期

```sql
-- 4. 批量检查一周内每天的数据可用性
WITH date_series AS (
    SELECT generate_series(
        '2025-06-23'::DATE, 
        '2025-06-29'::DATE, 
        '1 day'::INTERVAL
    )::DATE as check_date
)
SELECT 
    ds.check_date,
    COALESCE(dc.record_count, 0) as record_count,
    CASE WHEN dc.data_date IS NOT NULL THEN '✅ 可用' ELSE '❌ 无数据' END as status
FROM date_series ds
LEFT JOIN dwd.dwd_data_catalog dc ON dc.data_date = ds.check_date 
    AND dc.table_name = 'dwd_od_weekly'
ORDER BY ds.check_date;
```

## 🎯 高效查询字段选择

### 新增字段说明

相比原有的 `dwd.dwd_od_g4202` 等表，新的DWD表增加了以下字段：

- `id` - 自增主键
- `batch_id` - 批次标识
- `created_at` - 创建时间
- `updated_at` - 更新时间

### 查询优化建议

#### 1. 时间范围查询优化

```sql
-- ✅ 推荐：利用分区裁剪，指定具体字段
SELECT 
    pass_id,
    start_time,
    start_square_code,
    end_square_code,
    vehicle_type
FROM dwd.dwd_od_weekly 
WHERE start_time >= '2025-06-15 00:00:00'
  AND start_time < '2025-06-16 00:00:00'
  AND vehicle_type = '1';

-- ❌ 不推荐：SELECT * 查询所有字段
SELECT * FROM dwd.dwd_od_weekly 
WHERE start_time >= '2025-06-15 00:00:00';
```

#### 2. 索引字段优化

```sql
-- ✅ 推荐：使用索引字段进行过滤
SELECT 
    start_gantryid,
    end_gantryid,
    start_time,
    total,
    k1, k2, k3, k4
FROM dwd.dwd_flow_gantry_weekly 
WHERE start_gantryid = 'G000551005000210010'
  AND start_time >= '2025-06-20 00:00:00'
  AND start_time < '2025-06-21 00:00:00';
```

#### 3. 聚合查询优化

```sql
-- ✅ 推荐：只选择需要的聚合字段
SELECT 
    DATE(start_time) as date,
    COUNT(*) as trip_count,
    COUNT(DISTINCT pass_id) as unique_vehicles
FROM dwd.dwd_od_weekly 
WHERE start_time >= '2025-06-20 00:00:00'
  AND start_time < '2025-06-27 00:00:00'
GROUP BY DATE(start_time)
ORDER BY date;
```

## 📝 调用示例

### OD表查询示例

#### 重要说明：OD数据的起终点字段处理

在OD数据中，起终点信息有两套字段：

- **square_code/square_name**: 广场代码/名称（优先使用）
- **station_code/station_name**: 收费站代码/名称（square_code为空时使用）

**字段使用规则：**

- 当 `start_square_code` 不为空时，使用 `start_square_code` 和 `start_square_name`
- 当 `start_square_code` 为空时，退化使用 `start_station_code` 和 `start_station_name`
- `station_code` 代表示范路段边缘门架的编号
- `station_name` 提供对应的名称信息

#### 示例1：查询特定时间段的OD数据（处理空值情况）

```sql
-- 查询2025年6月20日的OD数据，智能处理起终点字段
SELECT
    pass_id,
    vehicle_type,
    start_time,
    -- 起点处理：优先使用square，为空时使用station
    COALESCE(start_square_code, start_station_code) as origin_code,
    COALESCE(start_square_name, start_station_name) as origin_name,
    -- 终点处理：优先使用square，为空时使用station
    COALESCE(end_square_code, end_station_code) as destination_code,
    COALESCE(end_square_name, end_station_name) as destination_name,
    -- 标识数据来源类型
    CASE
        WHEN start_square_code IS NOT NULL THEN 'square'
        WHEN start_station_code IS NOT NULL THEN 'station'
        ELSE 'unknown'
    END as origin_type,
    direction
FROM dwd.dwd_od_weekly
WHERE start_time >= '2025-06-20 00:00:00'
  AND start_time < '2025-06-21 00:00:00'
ORDER BY start_time
LIMIT 100;
```

#### 示例2：统计每日OD流量

```sql
-- 统计每日OD流量分布（智能处理起终点字段）
SELECT
    DATE(start_time) as date,
    vehicle_type,
    COUNT(*) as trip_count,
    -- 统计有效起点数量（square优先，station补充）
    COUNT(DISTINCT COALESCE(start_square_code, start_station_code)) as origin_count,
    -- 统计有效终点数量（square优先，station补充）
    COUNT(DISTINCT COALESCE(end_square_code, end_station_code)) as destination_count,
    -- 统计数据来源类型分布
    SUM(CASE WHEN start_square_code IS NOT NULL THEN 1 ELSE 0 END) as square_based_count,
    SUM(CASE WHEN start_square_code IS NULL AND start_station_code IS NOT NULL THEN 1 ELSE 0 END) as station_based_count
FROM dwd.dwd_od_weekly
WHERE start_time >= '2025-06-20 00:00:00'
  AND start_time < '2025-06-27 00:00:00'
GROUP BY DATE(start_time), vehicle_type
ORDER BY date, vehicle_type;
```

#### 示例3：热门OD对分析

```sql
-- 查询热门OD对（起终点对），智能处理square_code为空的情况
WITH od_data AS (
    SELECT
        -- 起点处理：优先使用square，为空时使用station
        COALESCE(start_square_code, start_station_code) as origin_code,
        COALESCE(start_square_name, start_station_name) as origin_name,
        -- 标记起点数据来源
        CASE WHEN start_square_code IS NOT NULL THEN 'square' ELSE 'station' END as origin_type,

        -- 终点处理：优先使用square，为空时使用station
        COALESCE(end_square_code, end_station_code) as destination_code,
        COALESCE(end_square_name, end_station_name) as destination_name,
        -- 标记终点数据来源
        CASE WHEN end_square_code IS NOT NULL THEN 'square' ELSE 'station' END as destination_type,

        start_time
    FROM dwd.dwd_od_weekly
    WHERE start_time >= '2025-06-23 00:00:00'
      AND start_time < '2025-06-30 00:00:00'
      -- 确保起点和终点至少有一个有效值
      AND (start_square_code IS NOT NULL OR start_station_code IS NOT NULL)
      AND (end_square_code IS NOT NULL OR end_station_code IS NOT NULL)
)
SELECT
    origin_code,
    origin_name,
    origin_type,
    destination_code,
    destination_name,
    destination_type,
    COUNT(*) as trip_count,
    COUNT(DISTINCT DATE(start_time)) as active_days
FROM od_data
GROUP BY
    origin_code, origin_name, origin_type,
    destination_code, destination_name, destination_type
HAVING COUNT(*) >= 100  -- 过滤出行次数>=100的OD对
ORDER BY trip_count DESC
LIMIT 20;
```

### 门架流量表查询示例

#### 示例1：查询特定门架的流量数据

```sql
-- 查询特定门架在指定时间段的流量
SELECT 
    start_gantryid,
    end_gantryid,
    start_time,
    k1, k2, k3, k4,           -- 客车流量
    h1, h2, h3, h4, h5, h6,   -- 货车流量
    total,                     -- 总流量
    distance                   -- 门架间距离
FROM dwd.dwd_flow_gantry_weekly 
WHERE start_gantryid = 'G000551005000210010'
  AND start_time >= '2025-06-25 00:00:00'
  AND start_time < '2025-06-26 00:00:00'
ORDER BY start_time;
```

#### 示例2：门架流量统计分析

```sql
-- 统计门架每小时流量分布
SELECT 
    start_gantryid,
    EXTRACT(HOUR FROM start_time) as hour,
    AVG(total) as avg_flow,
    MAX(total) as max_flow,
    COUNT(*) as record_count
FROM dwd.dwd_flow_gantry_weekly 
WHERE start_time >= '2025-06-24 00:00:00'
  AND start_time < '2025-06-25 00:00:00'
  AND total > 0
GROUP BY start_gantryid, EXTRACT(HOUR FROM start_time)
ORDER BY start_gantryid, hour;
```

#### 示例3：门架对流量对比

```sql
-- 对比不同门架对的流量情况
SELECT 
    start_gantryid,
    end_gantryid,
    DATE(start_time) as date,
    SUM(total) as daily_total,
    AVG(total) as avg_hourly_flow,
    SUM(k1+k2+k3+k4) as total_passenger,
    SUM(h1+h2+h3+h4+h5+h6) as total_freight
FROM dwd.dwd_flow_gantry_weekly 
WHERE start_time >= '2025-06-23 00:00:00'
  AND start_time < '2025-06-30 00:00:00'
  AND distance >= 0.5  -- 过滤有效门架对
GROUP BY start_gantryid, end_gantryid, DATE(start_time)
HAVING SUM(total) > 1000  -- 过滤日流量>1000的门架对
ORDER BY date, daily_total DESC;
```

## ⚠️ 注意事项

### 查询性能优化

1. **时间范围查询**: 始终在WHERE条件中包含 `start_time` 字段以利用分区裁剪
2. **字段选择**: 避免使用 `SELECT *`，只选择需要的字段
3. **索引利用**: 优先使用已建立索引的字段进行过滤

### 数据完整性

1. **数据检查**: 查询前使用数据目录表确认数据可用性
2. **NULL值处理**: 注意处理可能的NULL值，特别是名称字段
3. **时间格式**: 统一使用 `YYYY-MM-DD HH:MM:SS` 格式

### OD数据字段处理

1. **起终点字段优先级**:
   - 优先使用 `square_code/square_name`
   - 当 `square_code` 为空时，退化使用 `station_code/station_name`
2. **字段含义**:
   - `square_code/square_name`: 广场代码/名称
   - `station_code/station_name`: 收费站代码/名称，代表示范路段边缘门架
3. **推荐用法**:
   ```sql
   COALESCE(start_square_code, start_station_code) as origin_code
   ```

### 分区感知

1. **跨分区查询**: 大范围时间查询可能涉及多个分区
2. **分区裁剪**: 合理设置时间范围以减少扫描的分区数量
3. **并行处理**: PostgreSQL会自动并行处理多分区查询

## 🔧 高级查询技巧

### 跨表关联查询

#### 示例1：出入口流量对比分析

```sql
-- 对比出口和入口流量，分析收费站的进出平衡情况
WITH exit_flow AS (
    SELECT
        DATE(start_time) as date,
        COALESCE(square_code, station_code) as station_code,
        COALESCE(square_name, station_name) as station_name,
        SUM(total) as exit_total
    FROM dwd.dwd_flow_offramp_weekly
    WHERE start_time >= '2025-06-25 00:00:00'
      AND start_time < '2025-06-26 00:00:00'
    GROUP BY DATE(start_time),
             COALESCE(square_code, station_code),
             COALESCE(square_name, station_name)
),
entrance_flow AS (
    SELECT
        DATE(start_time) as date,
        COALESCE(square_code, station_code) as station_code,
        COALESCE(square_name, station_name) as station_name,
        SUM(total) as entrance_total
    FROM dwd.dwd_flow_onramp_weekly
    WHERE start_time >= '2025-06-25 00:00:00'
      AND start_time < '2025-06-26 00:00:00'
    GROUP BY DATE(start_time),
             COALESCE(square_code, station_code),
             COALESCE(square_name, station_name)
)
SELECT
    COALESCE(e.date, en.date) as date,
    COALESCE(e.station_code, en.station_code) as station_code,
    COALESCE(e.station_name, en.station_name) as station_name,
    COALESCE(e.exit_total, 0) as exit_flow,
    COALESCE(en.entrance_total, 0) as entrance_flow,
    COALESCE(e.exit_total, 0) - COALESCE(en.entrance_total, 0) as flow_balance,
    CASE
        WHEN COALESCE(en.entrance_total, 0) > 0 THEN
            ROUND(COALESCE(e.exit_total, 0)::NUMERIC / en.entrance_total, 2)
        ELSE NULL
    END as exit_entrance_ratio
FROM exit_flow e
FULL OUTER JOIN entrance_flow en
    ON e.date = en.date AND e.station_code = en.station_code
WHERE COALESCE(e.exit_total, 0) + COALESCE(en.entrance_total, 0) > 100
ORDER BY flow_balance DESC;
```

### 时间序列分析

#### 示例2：流量时间趋势分析

```sql
-- 分析一周内每小时的流量变化趋势
SELECT
    DATE(start_time) as date,
    EXTRACT(HOUR FROM start_time) as hour,
    SUM(total) as hourly_flow,
    AVG(SUM(total)) OVER (
        PARTITION BY EXTRACT(HOUR FROM start_time)
        ORDER BY DATE(start_time)
        ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING
    ) as moving_avg
FROM dwd.dwd_flow_gantry_weekly
WHERE start_time >= '2025-06-23 00:00:00'
  AND start_time < '2025-06-30 00:00:00'
GROUP BY DATE(start_time), EXTRACT(HOUR FROM start_time)
ORDER BY date, hour;
```

### 数据质量检查

#### 示例3：数据完整性检查

```sql
-- 检查数据完整性和质量
SELECT
    table_name,
    data_date,
    record_count,
    CASE
        WHEN record_count = 0 THEN '❌ 无数据'
        WHEN record_count < 1000 THEN '⚠️ 数据量偏少'
        ELSE '✅ 正常'
    END as data_status,
    CASE
        WHEN data_date = CURRENT_DATE - 1 THEN '最新'
        WHEN data_date >= CURRENT_DATE - 7 THEN '近期'
        ELSE '历史'
    END as data_age
FROM dwd.dwd_data_catalog
WHERE table_name = 'dwd_flow_gantry_weekly'
ORDER BY data_date DESC;
```

## 📊 常用查询模板

### 模板1：日流量统计

```sql
-- 通用日流量统计模板
SELECT
    DATE(start_time) as date,
    COUNT(*) as record_count,
    -- 根据表类型选择相应字段
    CASE
        WHEN '{{table_type}}' = 'od' THEN COUNT(DISTINCT pass_id)
        WHEN '{{table_type}}' = 'gantry' THEN SUM(total)
        ELSE COUNT(*)
    END as metric_value
FROM dwd.{{table_name}}
WHERE start_time >= '{{start_date}}'::TIMESTAMP
  AND start_time < '{{end_date}}'::TIMESTAMP
GROUP BY DATE(start_time)
ORDER BY date;

-- 使用示例：
-- 替换 {{table_name}} 为 dwd_od_weekly
-- 替换 {{table_type}} 为 od
-- 替换 {{start_date}} 为 2025-06-20 00:00:00
-- 替换 {{end_date}} 为 2025-06-27 00:00:00
```

### 模板2：峰值时段分析

```sql
-- 通用峰值时段分析模板
WITH hourly_stats AS (
    SELECT
        EXTRACT(HOUR FROM start_time) as hour,
        COUNT(*) as record_count,
        AVG(COUNT(*)) OVER () as avg_count
    FROM dwd.{{table_name}}
    WHERE start_time >= '{{start_date}}'::TIMESTAMP
      AND start_time < '{{end_date}}'::TIMESTAMP
    GROUP BY EXTRACT(HOUR FROM start_time)
)
SELECT
    hour,
    record_count,
    ROUND(record_count::NUMERIC / avg_count, 2) as ratio_to_avg,
    CASE
        WHEN record_count > avg_count * 1.5 THEN '🔴 高峰'
        WHEN record_count > avg_count * 1.2 THEN '🟡 较高'
        WHEN record_count < avg_count * 0.8 THEN '🟢 低谷'
        ELSE '⚪ 正常'
    END as period_type
FROM hourly_stats
ORDER BY hour;
```

## 🚨 常见问题与解决方案

### 问题1：查询速度慢

**原因**: 没有利用分区裁剪或索引
**解决方案**:

```sql
-- ❌ 慢查询示例
SELECT * FROM dwd.dwd_od_weekly WHERE pass_id = 'xxx';

-- ✅ 优化后查询
SELECT pass_id, start_time, start_square_code, end_square_code
FROM dwd.dwd_od_weekly
WHERE start_time >= '2025-06-20 00:00:00'
  AND start_time < '2025-06-21 00:00:00'
  AND pass_id = 'xxx';
```

### 问题2：数据不存在

**原因**: 查询的时间范围没有数据
**解决方案**:

```sql
-- 先检查数据可用性
SELECT * FROM dwd.user_check_data_availability(
    'dwd_od_weekly',
    '2025-06-20',
    '2025-06-20'
);

-- 确认有数据后再进行业务查询
```

**文档版本**: v1.0 | **最后更新**: 2025-07-10 | **适用数据**: 2025年6月9日-7月6日
