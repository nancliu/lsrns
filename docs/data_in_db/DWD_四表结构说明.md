### DWD 层四张周分区表表结构说明

本文基于 `sql/ods2dwd/01_create_dwd_partition_tables.sql` 总结四张 DWD 周分区表（`dwd_od_weekly`、`dwd_flow_gantry_weekly`、`dwd_flow_offramp_weekly`、`dwd_flow_onramp_weekly`）的结构、主键、分区策略、索引/唯一约束与触发器。

- **Schema**: `dwd`
- **分区策略**: 所有表均按 `start_time` 进行 RANGE 分区（周分区由分区管理函数在另一脚本中创建）
- **通用列**: `id BIGSERIAL`，`start_time TIMESTAMP NOT NULL`，`batch_id VARCHAR(50)`，`created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`，`updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- **通用主键**: `(id, start_time)`
- **通用触发器**: `BEFORE UPDATE` 触发器在每次更新行时自动刷新 `updated_at`

---

### 快速参考

| 表名                        | 分区键         | 主键                 | 主要唯一约束                     | 关键二级索引                                      |
| --------------------------- | -------------- | -------------------- | -------------------------------- | ------------------------------------------------- |
| `dwd_od_weekly`           | `start_time` | `(id, start_time)` | `(pass_id, start_time)`        | `start_time`                                    |
| `dwd_flow_gantry_weekly`  | `start_time` | `(id, start_time)` | `(start_gantryid, start_time)` | `start_time`、`start_gantryid`                |
| `dwd_flow_offramp_weekly` | `start_time` | `(id, start_time)` | `(square_code, start_time)`    | `start_time`、`station_code`、`square_code` |
| `dwd_flow_onramp_weekly`  | `start_time` | `(id, start_time)` | `(square_code, start_time)`    | `start_time`、`station_code`、`square_code` |

---

### 1) dwd_od_weekly（OD 明细，周分区）

- 分区方式: `PARTITION BY RANGE (start_time)`
- 主键: `(id, start_time)`
- 唯一约束: `(pass_id, start_time)`
- 索引: `start_time`

字段说明：

| 列名                   | 类型             | 约束/默认值                   | 说明                       |
| ---------------------- | ---------------- | ----------------------------- | -------------------------- |
| `id`                 | `BIGSERIAL`    | 主键组成                      | 自增ID                     |
| `pass_id`            | `VARCHAR(50)`  | NOT NULL；唯一约束包含此列    | 通行单号/过车标识          |
| `vehicle_type`       | `VARCHAR(10)`  |                               | 车型                       |
| `start_time`         | `TIMESTAMP`    | NOT NULL；分区键；主键组成    | 入分区/统计时间            |
| `start_square_code`  | `VARCHAR(50)`  |                               | 起点广场编码               |
| `start_square_name`  | `VARCHAR(100)` |                               | 起点广场名称               |
| `start_station_code` | `VARCHAR(50)`  |                               | 起点站编码                 |
| `start_station_name` | `VARCHAR(100)` |                               | 起点站名称                 |
| `end_time`           | `TIMESTAMP`    |                               | 结束时间                   |
| `end_square_code`    | `VARCHAR(50)`  |                               | 终点广场编码               |
| `end_square_name`    | `VARCHAR(100)` |                               | 终点广场名称               |
| `end_station_code`   | `VARCHAR(50)`  |                               | 终点站编码                 |
| `end_station_name`   | `VARCHAR(100)` |                               | 终点站名称                 |
| `direction`          | `VARCHAR(10)`  |                               | 方向                       |
| `batch_id`           | `VARCHAR(50)`  |                               | 批次ID                     |
| `created_at`         | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` | 创建时间                   |
| `updated_at`         | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` | 更新时间（更新时自动刷新） |

---

### 2) dwd_flow_gantry_weekly（门架流量，周分区）

- 分区方式: `PARTITION BY RANGE (start_time)`
- 主键: `(id, start_time)`
- 唯一约束: `(start_gantryid, start_time)`
- 索引: `start_time`、`start_gantryid`

字段说明：

| 列名               | 类型              | 约束/默认值                   | 说明                       |
| ------------------ | ----------------- | ----------------------------- | -------------------------- |
| `id`             | `BIGSERIAL`     | 主键组成                      | 自增ID                     |
| `start_gantryid` | `VARCHAR(50)`   | NOT NULL；唯一约束包含此列    | 起始门架编码               |
| `end_gantryid`   | `VARCHAR(50)`   | NOT NULL                      | 结束门架编码               |
| `gantry_name`    | `VARCHAR(100)`  |                               | 门架名称                   |
| `start_time`     | `TIMESTAMP`     | NOT NULL；分区键；主键组成    | 入分区/统计时间            |
| `k1`             | `INTEGER`       |                               | 客车1类流量                |
| `k2`             | `INTEGER`       |                               | 客车2类流量                |
| `k3`             | `INTEGER`       |                               | 客车3类流量                |
| `k4`             | `INTEGER`       |                               | 客车4类流量                |
| `h1`             | `INTEGER`       |                               | 货车1类流量                |
| `h2`             | `INTEGER`       |                               | 货车2类流量                |
| `h3`             | `INTEGER`       |                               | 货车3类流量                |
| `h4`             | `INTEGER`       |                               | 货车4类流量                |
| `h5`             | `INTEGER`       |                               | 货车5类流量                |
| `h6`             | `INTEGER`       |                               | 货车6类流量                |
| `t1`             | `INTEGER`       |                               | 特种车1类流量              |
| `t2`             | `INTEGER`       |                               | 特种车2类流量              |
| `t3`             | `INTEGER`       |                               | 特种车3类流量              |
| `t4`             | `INTEGER`       |                               | 特种车4类流量              |
| `t5`             | `INTEGER`       |                               | 特种车5类流量              |
| `t6`             | `INTEGER`       |                               | 特种车6类流量              |
| `total`          | `INTEGER`       |                               | 总流量                     |
| `total_k`        | `INTEGER`       |                               | 客车总流量                 |
| `total_h`        | `INTEGER`       |                               | 货车总流量                 |
| `total_t`        | `INTEGER`       |                               | 特种车总流量               |
| `avg_speed`      | `NUMERIC(10,2)` |                               | 平均速度                   |
| `avg_duration`   | `NUMERIC(10,2)` |                               | 平均耗时                   |
| `distance`       | `NUMERIC(10,3)` |                               | 距离                       |
| `batch_id`       | `VARCHAR(50)`   |                               | 批次ID                     |
| `created_at`     | `TIMESTAMP`     | DEFAULT `CURRENT_TIMESTAMP` | 创建时间                   |
| `updated_at`     | `TIMESTAMP`     | DEFAULT `CURRENT_TIMESTAMP` | 更新时间（更新时自动刷新） |

---

### 3) dwd_flow_offramp_weekly（出口广场流量，周分区）

- 分区方式: `PARTITION BY RANGE (start_time)`
- 主键: `(id, start_time)`
- 唯一约束: `(square_code, start_time)`
- 索引: `start_time`、`station_code`、`square_code`

字段说明：

| 列名             | 类型             | 约束/默认值                   | 说明                       |
| ---------------- | ---------------- | ----------------------------- | -------------------------- |
| `id`           | `BIGSERIAL`    | 主键组成                      | 自增ID                     |
| `station_code` | `VARCHAR(50)`  | NOT NULL                      | 站编码（出口）             |
| `station_name` | `VARCHAR(100)` |                               | 站名称（出口）             |
| `square_code`  | `VARCHAR(50)`  |                               | 广场编码（出口）           |
| `square_name`  | `VARCHAR(100)` |                               | 广场名称（出口）           |
| `start_time`   | `TIMESTAMP`    | NOT NULL；分区键；主键组成    | 入分区/统计时间            |
| `k1`           | `INTEGER`      |                               | 客车1类流量                |
| `k2`           | `INTEGER`      |                               | 客车2类流量                |
| `k3`           | `INTEGER`      |                               | 客车3类流量                |
| `k4`           | `INTEGER`      |                               | 客车4类流量                |
| `h1`           | `INTEGER`      |                               | 货车1类流量                |
| `h2`           | `INTEGER`      |                               | 货车2类流量                |
| `h3`           | `INTEGER`      |                               | 货车3类流量                |
| `h4`           | `INTEGER`      |                               | 货车4类流量                |
| `h5`           | `INTEGER`      |                               | 货车5类流量                |
| `h6`           | `INTEGER`      |                               | 货车6类流量                |
| `t1`           | `INTEGER`      |                               | 特种车1类流量              |
| `t2`           | `INTEGER`      |                               | 特种车2类流量              |
| `t3`           | `INTEGER`      |                               | 特种车3类流量              |
| `t4`           | `INTEGER`      |                               | 特种车4类流量              |
| `t5`           | `INTEGER`      |                               | 特种车5类流量              |
| `t6`           | `INTEGER`      |                               | 特种车6类流量              |
| `total`        | `INTEGER`      |                               | 总流量                     |
| `total_k`      | `INTEGER`      |                               | 客车总流量                 |
| `total_h`      | `INTEGER`      |                               | 货车总流量                 |
| `total_t`      | `INTEGER`      |                               | 特种车总流量               |
| `batch_id`     | `VARCHAR(50)`  |                               | 批次ID                     |
| `created_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` | 创建时间                   |
| `updated_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` | 更新时间（更新时自动刷新） |

---

### 4) dwd_flow_onramp_weekly（入口广场流量，周分区）

- 分区方式: `PARTITION BY RANGE (start_time)`
- 主键: `(id, start_time)`
- 唯一约束: `(square_code, start_time)`
- 索引: `start_time`、`station_code`、`square_code`

字段说明：

| 列名             | 类型             | 约束/默认值                   | 说明                       |
| ---------------- | ---------------- | ----------------------------- | -------------------------- |
| `id`           | `BIGSERIAL`    | 主键组成                      | 自增ID                     |
| `station_code` | `VARCHAR(50)`  | NOT NULL                      | 站编码（入口）             |
| `station_name` | `VARCHAR(100)` |                               | 站名称（入口）             |
| `square_code`  | `VARCHAR(50)`  |                               | 广场编码（入口）           |
| `square_name`  | `VARCHAR(100)` |                               | 广场名称（入口）           |
| `start_time`   | `TIMESTAMP`    | NOT NULL；分区键；主键组成    | 入分区/统计时间            |
| `k1`           | `INTEGER`      |                               | 客车1类流量                |
| `k2`           | `INTEGER`      |                               | 客车2类流量                |
| `k3`           | `INTEGER`      |                               | 客车3类流量                |
| `k4`           | `INTEGER`      |                               | 客车4类流量                |
| `h1`           | `INTEGER`      |                               | 货车1类流量                |
| `h2`           | `INTEGER`      |                               | 货车2类流量                |
| `h3`           | `INTEGER`      |                               | 货车3类流量                |
| `h4`           | `INTEGER`      |                               | 货车4类流量                |
| `h5`           | `INTEGER`      |                               | 货车5类流量                |
| `h6`           | `INTEGER`      |                               | 货车6类流量                |
| `t1`           | `INTEGER`      |                               | 特种车1类流量              |
| `t2`           | `INTEGER`      |                               | 特种车2类流量              |
| `t3`           | `INTEGER`      |                               | 特种车3类流量              |
| `t4`           | `INTEGER`      |                               | 特种车4类流量              |
| `t5`           | `INTEGER`      |                               | 特种车5类流量              |
| `t6`           | `INTEGER`      |                               | 特种车6类流量              |
| `total`        | `INTEGER`      |                               | 总流量                     |
| `total_k`      | `INTEGER`      |                               | 客车总流量                 |
| `total_h`      | `INTEGER`      |                               | 货车总流量                 |
| `total_t`      | `INTEGER`      |                               | 特种车总流量               |
| `batch_id`     | `VARCHAR(50)`  |                               | 批次ID                     |
| `created_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` | 创建时间                   |
| `updated_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` | 更新时间（更新时自动刷新） |

---

### 触发器与维护

- 触发器函数：
  - 名称：`update_updated_at_column()`
  - 行为：在 `BEFORE UPDATE` 时，将 `NEW.updated_at` 置为 `CURRENT_TIMESTAMP`
- 每表触发器：`update_<table>_updated_at`
  - 作用于：`dwd_od_weekly`、`dwd_flow_gantry_weekly`、`dwd_flow_offramp_weekly`、`dwd_flow_onramp_weekly`
  - 时机：`BEFORE UPDATE FOR EACH ROW`

---

### 说明与建议

- 分区创建采用范围分区（键：`start_time`）。周粒度分区的实际创建与管理，请参考同目录 `02_create_partition_management.sql` 中的分区管理函数（例如 `user_create_weekly_partition` 等）。
- 写入或更新数据时，`updated_at` 将由触发器自动维护，无需手工赋值。
- 为保障查询性能，建议在应用查询中充分利用已存在的唯一约束与二级索引（如按 `start_time`、`start_gantryid`、`square_code` 等过滤）。

---

### 车型业务定义

本节说明 `k1`-`k4`（客车）、`h1`-`h6`（货车）与 `t1`-`t6`（专项作业车）的业务含义及其与源系统车型代码的对应关系。定义依据仓库中数据导入脚本的显式映射规则。

- 定义分组：

  - `k*`：客车（4 类）
  - `h*`：货车（6 类）
  - `t*`：专项作业车（最多 6 类，按源系统提供情况映射）
- 源系统中文名称到目标列映射（示例）：

  - 客车：`一型客车`→`k1`，`二型客车`→`k2`，`三型客车`→`k3`，`四型客车`→`k4`
  - 货车：`一型货车`→`h1`，`二型货车`→`h2`，`三型货车`→`h3`，`四型货车`→`h4`，`五型货车`→`h5`，`六型货车`→`h6`
  - 专项作业车：`一型专项作业车`→`t1`，`二型专项作业车`→`t2`，`三型专项作业车`→`t3`，`四型专项作业车`→`t4`，`五型专项作业车`→`t5`，`六型专项作业车`→`t6`
