### 维度映射表（TAZ/门架/收费广场 ↔ 示范道路）设计与使用说明

本文档说明利用 `TAZ_5_validated.add.xml` 与维度表 `dim.point_gantry`、`dim.point_toll_square` 生成以下四张映射表的结构、来源与使用方式。

- **参考表**：`dim.demonstration_route_ref` — `demonstration_id → (demonstration_route_code, demonstration_route_name)` 唯一映射
- **门架映射**：`dim.gantry_demonstration_mapping` — `gantry_id → (demonstration信息)`
- **收费广场映射**：`dim.toll_square_demonstration_mapping` — `square_code → (demonstration信息)`
- **TAZ 映射**：`dim.taz_demonstration_mapping` — `taz_id → (来源类型、来源ID、demonstration信息)`

文档对应的生成工具：`shared/utilities/taz_tools/build_taz_mappings.py`。

---

### 一、表结构（DDL）

以下为推荐的 DDL，与生成脚本落库一致（存在即不变，运行时会 TRUNCATE 刷新数据）。

```sql
-- 1) 示范路线参考表
CREATE TABLE IF NOT EXISTS dim.demonstration_route_ref (
  demonstration_id integer PRIMARY KEY,
  demonstration_route_code text NOT NULL,
  demonstration_route_name text NOT NULL,
  source_table text NOT NULL DEFAULT 'dim.point_gantry'
);

-- 2) 门架与示范路线映射
CREATE TABLE IF NOT EXISTS dim.gantry_demonstration_mapping (
  gantry_id text PRIMARY KEY,
  demonstration_id integer NOT NULL,
  demonstration_route_code text NOT NULL,
  demonstration_route_name text NOT NULL
);

-- 3) 收费广场与示范路线映射
CREATE TABLE IF NOT EXISTS dim.toll_square_demonstration_mapping (
  square_code text PRIMARY KEY,
  demonstration_id integer,
  demonstration_route_code text,
  demonstration_route_name text
);

-- 4) TAZ 与示范路线映射
CREATE TABLE IF NOT EXISTS dim.taz_demonstration_mapping (
  taz_id text PRIMARY KEY,
  source_type text,                 -- 'gantry' | 'toll_square'，优先匹配门架
  source_id text,                   -- 与 source_type 对应的 gantry_id 或 square_code
  demonstration_id integer,
  demonstration_route_code text,
  demonstration_route_name text
);
```

字段说明：
- **demonstration_id**：整数，示范道路顺序编号（来源于 `dim.point_gantry.demonstration_id`，忽略空值）。
- **demonstration_route_code/name**：示范道路编码/名称（来自 `dim.point_gantry` 中与 demonstration_id 唯一对应的信息）。
- **source_type/source_id**：在 `taz_demonstration_mapping` 中表明 `taz_id` 匹配来源及其 ID，优先门架，其次收费广场。

---

### 二、数据来源与构建逻辑

生成脚本：`shared/utilities/taz_tools/build_taz_mappings.py`

1) `dim.demonstration_route_ref`
- 从 `dim.point_gantry` 提取 `demonstration_id` 非空记录，并聚合出唯一的 `(demonstration_route_code, demonstration_route_name)`。

2) `dim.gantry_demonstration_mapping`
- 以 `dim.point_gantry` 的 `gantry_id`、`demonstration_id` 为基础，关联 `dim.demonstration_route_ref` 得到编码与名称。

3) `dim.toll_square_demonstration_mapping`
- 以 `dim.point_toll_square` 的 `square_code`、`demonstration_id` 为基础，左关联 `dim.demonstration_route_ref`（允许 `demonstration_id` 为空时 route 信息为空）。

4) `dim.taz_demonstration_mapping`
- 从 `templates/taz_files/TAZ_5_validated.add.xml` 解析 `<taz id="..."/>` 得到 `taz_id` 列表。
- 依次尝试匹配：
  - 先与 `dim.point_gantry.gantry_id` 等值匹配，若命中，`source_type='gantry'`。
  - 否则与 `dim.point_toll_square.square_code` 等值匹配，若命中，`source_type='toll_square'`。
  - 仅当匹配到非空 `demonstration_id` 时才写入映射。

---

### 三、使用示例

查询每条示范路线涉及的 TAZ 数量：
```sql
SELECT d.demonstration_id,
       d.demonstration_route_code,
       d.demonstration_route_name,
       COUNT(t.taz_id) AS taz_count
FROM dim.demonstration_route_ref d
LEFT JOIN dim.taz_demonstration_mapping t USING (demonstration_id)
GROUP BY d.demonstration_id, d.demonstration_route_code, d.demonstration_route_name
ORDER BY d.demonstration_id;
```

把门架数据带上示范路线信息：
```sql
SELECT g.*, r.demonstration_route_code, r.demonstration_route_name
FROM dim.point_gantry g
JOIN dim.demonstration_route_ref r USING (demonstration_id);
```

根据 TAZ 过滤某条示范路线的数据：
```sql
SELECT t.taz_id, t.source_type, t.source_id
FROM dim.taz_demonstration_mapping t
WHERE t.demonstration_id = 3; -- 示例：示范顺序号=3
```

---

### 四、生成与刷新（Windows PowerShell）

请勿在 base 环境安装或执行业务包。建议使用 mamba 创建独立环境（已在工程根目录）：

```powershell
cd D:\projects\OD生成脚本\OD生成脚本

mamba create -n od-tools -y python=3.10
mamba activate od-tools

# 优先使用 mamba 安装依赖，不足再用 pip（在 od-tools 环境内）
mamba install -y -c conda-forge click sqlalchemy psycopg2-binary python-dotenv pandas numpy scipy matplotlib seaborn requests httpx
pip install -r .\requirements.txt

# 设置数据库环境变量
$env:PGHOST="127.0.0.1"
$env:PGPORT="5432"
$env:PGDATABASE="your_db"
$env:PGUSER="your_user"
$env:PGPASSWORD="your_password"

# 执行构建脚本（使用默认 XML 路径与 dim schema）
python .\shared\utilities\taz_tools\build_taz_mappings.py

# 可选：指定自定义路径或表名
python .\shared\utilities\taz_tools\build_taz_mappings.py `
  --xml-path ".\templates\taz_files\TAZ_5_validated.add.xml" `
  --dim-schema "dim" `
  --gantry-table "dim.point_gantry" `
  --toll-square-table "dim.point_toll_square"
```

执行完成后会刷新生成以下表：
- `dim.demonstration_route_ref`
- `dim.gantry_demonstration_mapping`
- `dim.toll_square_demonstration_mapping`
- `dim.taz_demonstration_mapping`

---

### 五、校验与排错

快速行数校验：
```sql
SELECT 'route_ref' tbl, COUNT(*) FROM dim.demonstration_route_ref
UNION ALL SELECT 'gantry_map', COUNT(*) FROM dim.gantry_demonstration_mapping
UNION ALL SELECT 'toll_map', COUNT(*) FROM dim.toll_square_demonstration_mapping
UNION ALL SELECT 'taz_map', COUNT(*) FROM dim.taz_demonstration_mapping;
```

常见问题：
- 缺少数据库环境变量 → 设置 `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`。
- XML 未解析到 `<taz id=...>` → 确认 `--xml-path` 是否正确。
- `taz_id` 未命中 → 需要确保 `taz_id` 与 `gantry_id` 或 `square_code` 完全等值；若存在别名或编码差异，请完善匹配规则（可在脚本中加正则/映射表）。

---

### 六、变更与扩展建议

- 若 `dim.point_toll_square` 字段名与本文不同，请同步调整脚本参数或代码。
- 若需改为数据库函数/存储过程（PL/pgSQL）版本，或加入调度（定时刷新），可据此文档的 DDL 与逻辑实现；注意 PostgreSQL 函数命名规范与返回类型一致性要求。


