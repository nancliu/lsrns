### 精度与机理-性能分析设计方案（v1.1）

#### 1. 目标与导航

- 统一评估“仿真输出 vs 观测数据”的一致性（仿真精度），提供问题定位（形成机理）与系统效率（效率性能）。
- 页面主导航：仿真精度｜形成机理｜效率性能，并提供标签化筛选以支持灵活组合与钻取。
- 产出可视化报告（HTML）与结构化结果（JSON/CSV），供前端展示与二次分析。

导航与标签：

- 主导航标签：`accuracy`（仿真精度）、`mechanism`（形成机理）、`performance`（效率性能）
- 维度标签：对象（`gantry` 门架/断面，`toll` 收费站，`od` OD窗口）、道路（`route` 线路/走廊/道路）、尺度（`1min`/`5min`/`10min`/`period`）、数据源（`sim_e1`/`sim_summary`/`obs_gantry`/`obs_toll`/`obs_od`）、指标类型（`flow`/`speed`）

#### 2. 范围与数据前提

- 输入（仿真）：E1 检测器（支持递归与多命名）、`summary.xml`（辅助统计）。
- 输入（观测）：
  - 门架/断面：流量、平均速度
  - 收费站广场：入口流量、出口流量
  - OD：起止点时刻（窗口）
- 输出：核心指标、层级细分指标、诊断图表、明细数据与报告页面。
- 暂不包含：依赖无法获取数据的指标（如拥堵指数、V/C、LOS、旅行时间可靠性等）。

#### 3. 数据输入

- 仿真路径：`cases/{case_id}/simulation`
  - E1：`simulation/e1/*.xml` 或 `e1_detectors/*.xml`（自动递归），读取 `nVehContrib/flow/speed`
  - summary：`simulation/summary.xml`（用于基础计数统计，如 loaded/running 等）
- 观测数据：数据库（门架/断面流量与平均速度、收费站入口/出口流量、OD起止窗口）。
- 注：只在指标层使用“当前可取到的数据列”。无法获得的字段不进入本设计。

#### 3.1 观测数据来源与字段（DWD 周分区表）

- 门架流量与平均速度：`dwd.dwd_flow_gantry_weekly`
  - 关键字段：`start_gantryid`（门架ID）、`start_time`（时间）、`k1..k4`（客车）、`h1..h6`（货车）、`t1..t6`（专项）、`total`（总流量）、`avg_speed`（平均速度）
  - 用途：
    - 流量精度对齐：按门架 × 时间间隔聚合，直接使用 `total` 作为观测总流量口径（`obs_flow = SUM(total)`）；分车型 `k*/h*/t*` 仅作为诊断字段保留
    - 速度机理/精度（阶段B）：按门架 × 时间间隔“流量加权平均”得到 `obs_avg_speed`

- 收费站入口流量：`dwd.dwd_flow_onramp_weekly`
  - 关键字段：`station_code`、`square_code/square_name`、`start_time`、`k*`/`h*`/`t*`、`total`
  - 用途：按 `COALESCE(square_code, station_code)` 归一为 `plaza_code`，再按时间间隔聚合 `total → entrance_flow`

- 收费站出口流量：`dwd.dwd_flow_offramp_weekly`
  - 字段与处理同入口表，聚合得到 `exit_flow`

- OD 明细：`dwd.dwd_od_weekly`
  - 关键字段：`start_time`、`end_time`、`start_square_code/station_code`、`end_square_code/station_code`
  - 用途：用于校验仿真投放时间窗口的覆盖性与可用性（阶段C），不直接参与门架精度计算

数据可用性：建议在查询前调用目录函数检查（示例函数名称遵循 user_ 前缀约定）：
- `dwd.user_check_data_availability(table_name, start_date, end_date)`
- `dwd.user_get_table_data_summary()`

#### 3.2 观测数据接入与聚合对齐规范

- 连接：使用 `psycopg2` + `pandas.read_sql_query`，连接参数来自 `accuracy_analysis/utils.py` 的 `DB_CONFIG`
- 时间对齐：
  - 将 `start_time` 转换为“从午夜起的分钟数”，再按配置的粒度分箱（如 5/10 分钟）：`interval_start = (hour*60+minute) // step * step`
  - 与仿真端 E1 的 `begin/end` 转分钟并分箱规则一致
- ID 对齐：
  - E1 检测器ID前缀解析为门架ID：`gantry_id = detector_id.split('_')[0]`
  - 需与 `dwd_flow_gantry_weekly.start_gantryid` 一致；如存在差异，维护映射表或规整规则
  - 道路/线路对齐（可选但推荐）：通过映射文件统一门架/广场到道路：`cases/{case_id}/config/route_mapping.csv`
    - 字段建议：`gantry_id, plaza_code, route_id, route_name`（至少提供其一：`gantry_id` 或 `plaza_code`）
    - 仿真侧 E1 聚合后通过 `gantry_id` 关联；观测侧门架用 `start_gantryid` 关联；收费站用 `plaza_code` 关联
    - 若无映射文件，则仅提供“全网”汇总与门架/广场级视图，不阻断分析
- 聚合口径：
  - 门架流量：`obs_flow = SUM(total)`
  - 门架平均速度（阶段B）：`obs_avg_speed = SUM(avg_speed * total) / NULLIF(SUM(total), 0)`
  - 收费站入口/出口：`entrance_flow/exit_flow = SUM(total)`，站点标识使用 `COALESCE(square_code, station_code)`
- 缺失与异常：
  - 门架速度为 NULL 或总流量为 0 时不参与加权；MAPE 分母为 0 的记录过滤
  - 列名统一：流量使用 `obs_flow`/`sim_flow`，时间列 `interval_start`

#### 3.3 观测侧查询模板（实现参考）

- 门架平均速度与总流量（5 分钟加权）
```sql
WITH base AS (
  SELECT start_gantryid AS gantry_id,
         date_trunc('minute', start_time) AS ts_min,
         total,
         avg_speed
  FROM dwd.dwd_flow_gantry_weekly
  WHERE start_time >= %(start)s
    AND start_time <  %(end)s
    -- AND start_gantryid = ANY(%(gantry_ids)s) -- 可选筛选
), bucket AS (
  SELECT gantry_id,
         (EXTRACT(HOUR FROM ts_min)::int*60 + EXTRACT(MINUTE FROM ts_min)::int)/5*5 AS interval_start,
         SUM(total) AS obs_flow,
         SUM(avg_speed*total) AS speed_flow,
         SUM(total) AS flow_sum
  FROM base
  GROUP BY gantry_id, ((EXTRACT(HOUR FROM ts_min)::int*60 + EXTRACT(MINUTE FROM ts_min)::int)/5*5)
)
SELECT gantry_id,
       interval_start,
       obs_flow,
       CASE WHEN flow_sum>0 THEN speed_flow/flow_sum ELSE NULL END AS obs_avg_speed
FROM bucket
ORDER BY gantry_id, interval_start;
```

- 收费站入口/出口流量（5 分钟）
```sql
SELECT COALESCE(square_code, station_code) AS plaza_code,
       (EXTRACT(HOUR FROM start_time)::int*60 + EXTRACT(MINUTE FROM start_time)::int)/5*5 AS interval_start,
       SUM(total) AS entrance_flow
FROM dwd.dwd_flow_onramp_weekly
WHERE start_time >= %(start)s AND start_time < %(end)s
GROUP BY COALESCE(square_code, station_code), ((EXTRACT(HOUR FROM start_time)::int*60 + EXTRACT(MINUTE FROM start_time)::int)/5*5);

SELECT COALESCE(square_code, station_code) AS plaza_code,
       (EXTRACT(HOUR FROM start_time)::int*60 + EXTRACT(MINUTE FROM start_time)::int)/5*5 AS interval_start,
       SUM(total) AS exit_flow
FROM dwd.dwd_flow_offramp_weekly
WHERE start_time >= %(start)s AND start_time < %(end)s
GROUP BY COALESCE(square_code, station_code), ((EXTRACT(HOUR FROM start_time)::int*60 + EXTRACT(MINUTE FROM start_time)::int)/5*5);
```

#### 3.4 道路-TAZ-门架/广场映射（route_taz matching）

- 目的：支持“按道路/线路（route）”汇总的精度与机理视图，将仿真与观测归集到同一路线维度。
- 推荐表结构（数据库优先，CSV可兜底）：
  - 字段：
    - `route_id`（必填）、`route_name`（可选）
    - `taz_id`（可选；用于按TAZ归属到路线）
    - `match_type` ENUM('gantry','plaza')（必填）
    - `gantry_id`（当 match_type='gantry' 时必填；映射 E1/门架观测的ID）
    - `plaza_code`（当 match_type='plaza' 时必填；映射收费站入口/出口的 `COALESCE(square_code, station_code)`）
    - `direction`（可选；上/下行或方向编码）
    - `weight` NUMERIC（可选；用于贡献权重汇总）
    - `valid_from`, `valid_to`（可选；有效期）
- 建议位置与命名：
  - 数据库表：`meta.route_taz_matching`（示例命名）
  - 或案例级CSV：`cases/{case_id}/config/route_taz_mapping.csv`（列同上，空缺列允许为空）
- 已建立的维度映射（可直接使用，详见 `docs/data_in_db/DIM_TAZ_GANTRY_SQUARE_Mappings.md`）：
  - `dim.demonstration_route_ref`（示范路线参考）
  - `dim.gantry_demonstration_mapping`（门架→示范路线）
  - `dim.toll_square_demonstration_mapping`（收费广场→示范路线）
  - `dim.taz_demonstration_mapping`（TAZ→示范路线，来源优先门架、其次收费广场）
- 关联与汇总规则：
  - 仿真 E1：按 `gantry_id, interval_start` 聚合后，`gantry_id = route_taz_matching.gantry_id` → 汇总到 `route_id`
  - 门架观测：`dwd_flow_gantry_weekly.start_gantryid = route_taz_matching.gantry_id` → 汇总到 `route_id`
  - 收费站观测：`COALESCE(square_code, station_code) = route_taz_matching.plaza_code` 且 `match_type='plaza'`
  - 若存在 `weight`，按路线汇总时可采用加权（如流量×权重）
- 回退策略：
  1) 存在 `route_taz_matching` → 优先按路线产出
  2) 无→ 回退 `route_mapping.csv`（简单映射：`gantry_id, plaza_code, route_id, route_name`）
  3) 再无→ 仅提供全网与门架/广场级视图

#### 4. 目录与产出

- 图表：`cases/{case_id}/analysis/accuracy/accuracy_results_时间戳/charts/*.png`
- 报告：`cases/{case_id}/analysis/accuracy/accuracy_results_时间戳/accuracy_report.html`
- 结构化：`cases/{case_id}/analysis/accuracy/accuracy_results_时间戳/{accuracy_results.csv|gantry_accuracy_analysis.csv|time_accuracy_analysis.csv|detailed_records.csv|anomaly_analysis.csv}`
- 静态访问：
  - 精度：`/cases/{case_id}/analysis/accuracy/accuracy_results_时间戳/...`
  - 机理：`/cases/{case_id}/analysis/mechanism/accuracy_results_时间戳/...`

#### 4.1 目录结构对齐（与《工程结构优化设计方案.md》一致）

```
OD生成脚本/
├── cases/                           # 案例根目录 ✅
│   ├── case_20250808_103528/        # 迁移的仿真案例 ✅
│   │   ├── config/                  # 配置文件 ✅
│   │   │   ├── od_data.xml         # OD数据 ✅
│   │   │   ├── simulation.sumocfg  # 仿真配置 ✅
│   │   │   └── static.xml          # 静态文件 ✅
│   │   ├── simulation/              # 仿真结果 ✅
│   │   │   ├── e1_detectors/       # E1检测器输出 ✅
│   │   │   ├── gantry_data/        # 门架数据 ✅
│   │   │   └── summary.xml         # 仿真摘要 ✅
│   │   ├── analysis/                # 分析结果 ✅
│   │   │   └── accuracy/           # 精度分析 ✅
│   │   └── metadata.json           # 案例元数据 ✅
│   └── case_20250808_101848/        # 精度分析案例 ✅
│       └── analysis/accuracy/results/ # 精度分析结果 ✅
├── templates/                       # 模板文件 ✅
│   ├── taz_files/                  # TAZ文件模板 ✅
│   │   ├── TAZ_5_validated.add.xml
│   │   ├── TAZ_4.add.xml
│   │   └── taz_templates.json      # TAZ配置模板 ✅
│   ├── network_files/              # 网络文件模板 ✅
│   │   ├── sichuan202503v6.net.xml
│   │   ├── sichuan202503v5.net.xml
│   │   └── network_configs.json    # 网络配置模板 ✅
│   └── config_templates/           # 配置模板 ✅
│       ├── simulation_templates/    # 仿真配置模板 ✅
│       │   ├── default.sumocfg     # 默认仿真配置 ✅
│       │   ├── mesoscopic.sumocfg  # 中观仿真配置 ✅
│       │   └── microscopic.sumocfg # 微观仿真配置 ✅
│       └── vehicle_templates/       # 车辆类型模板 ✅
│           └── vehicle_types.json  # 车辆类型配置 ✅
├── shared/                         # 共享资源 ✅
│   └── utilities/                  # 通用工具 ✅
│       └── taz_tools/              # TAZ相关工具 ✅
│           ├── analyze_duplicate_taz.py
│           ├── compare_taz_files.py
│           ├── fix_duplicate_taz.py
│           ├── fix_taz.bat
│           ├── taz_validator.py
│           ├── README.md
│           └── output/              # 输出文件目录 ✅
│               ├── taz_to_simnetwork_updated.csv
│               ├── taz_to_simnetwork_updated_oppo.csv
│               └── taz_validation_results.csv
├── api/                            # API服务 ✅
│   ├── main.py                     # FastAPI主程序入口 ✅
│   ├── models.py                   # Pydantic数据模型 ✅
│   ├── routes.py                   # API路由定义 ✅
│   ├── services.py                 # 业务逻辑服务 ✅
│   ├── utils.py                    # 工具函数 ✅
│   ├── compatibility.py            # 兼容性层 ✅
│   └── __init__.py                 # 包初始化文件 ✅
├── frontend/                       # 前端界面 ✅
│   ├── index.html                  # 主页面 ✅
│   ├── styles.css                  # 样式文件 ✅
│   ├── script.js                   # JavaScript逻辑 ✅
│   └── test_pages/                 # 测试页面 ✅
├── docs/                           # 文档 ✅
│   ├── README.md                   # 项目说明 ✅
│   ├── api_docs/                   # API文档 ✅
│   │   └── README.md               # API文档说明 ✅
│   └── development/                # 开发文档 ✅
│       └── phase2_summary.md       # 第二阶段总结 ✅
├── shared/utilities/migration_tools.py # 数据迁移工具 ✅
├── test_migration.py               # 迁移测试脚本 ✅
├── requirements.txt                 # 项目依赖 ✅
├── start_api.bat                   # API启动脚本 ✅
└── test_api.py                     # API测试脚本 ✅
```

说明：

- 报告内图片使用相对路径 `../charts/*.png`；服务层已挂载 `/cases` 为静态目录。
- E1 数据递归加载，兼容 `simulation/e1` 与以 `e1*` 命名的子目录。

#### 5. 指标体系（仅列出“可从当前数据直接得到”的指标）

- 仿真精度（accuracy）

  - 总体与分组（门架/时间）对“流量 flow”的一致性：
    - MAPE（过滤观测为0）、GEH均值、GEH≤5合格率、样本量
    - 相关性统计用于图表说明（Pearson/Spearman），不作为核心KPI
  - 可选分组：按 `route_id`（道路/线路）汇总精度与流量比例
  - 产出：总体卡片、门架TOP榜、时间序列与分布图、残差散点、（可选）按道路汇总表
- 形成机理（mechanism）

  - 基于“仿真数据可得”的机理视图（不依赖观测密度/容量）：
    - 流-速散点（sim：`flow` vs `speed`）
    - 速度时间序列（sim：`speed`）
    - 流量残差随时间的峰值偏移（基于精度层合并后的残差时间序列）
  - 注：因缺乏观测密度/容量，暂不纳入 V/C、LOS、FD/MFD 关键点等指标
  - 可选分组：按 `route_id` 展示不同道路的流-速分布差异
- 效率性能（performance）

  - 数据与运行信息：
    - 文件与记录：E1 XML文件数、有效记录数、门架观测记录数
    - 处理耗时：端到端分析耗时（分析器返回时间戳计算）
    - 产物规模：图表数量、CSV与HTML大小
    - 仿真摘要：`summary.xml` 基础计数（loaded/inserted/running 等的总量或极值）

#### 6. 可视化

- 仿真精度：
  - 时间序列对比（flow）、散点（sim vs obs）、MAPE/GEH分布、残差图、门架TOP榜
  - （可选）道路级精度汇总条形图/表格
- 形成机理：
  - 流-速散点（sim）、速度时间序列（sim）
  - （可选）按道路分面的流-速散点
- 效率性能：
  - 处理耗时条/统计表、文件与记录数表、`summary.xml` 计数概览

#### 7. 报告页面（HTML）

- 概览卡片：MAPE、GEH均值/合格率、样本量
- 图表区：按主导航（精度/机理/性能）分组插图，支持折叠/展开
- 表格区：门架TOP榜、效率统计表（文件/记录/耗时）
- 元信息：案例ID、时间范围、生成时间、图表清单
- 链接：图表相对路径 `../charts/*.png`，外部可通过 `/cases` 访问；CSV 在结果时间戳目录根下

#### 8. 后端设计

- 分析器 `AccuracyAnalyzer`（已实现，持续增强）：
  - 仿真数据：递归加载 E1、多命名兼容；解析 `summary.xml`
  - 数据对齐：以门架ID × 时间间隔（分钟）聚合与合并
  - 指标：MAPE、GEH均值、GEH≤5合格率、样本量；图表含相关性统计
  - 结果：charts/report/results，并回传 `report_url`/`chart_urls`
- 标签化：在返回的 `metrics` 与 `chart_urls` 中增加元信息字段（后续版本），如：
  - `tags: {nav: 'accuracy'|'mechanism'|'performance', object: 'gantry'|'toll'|'od', scale: '5min'|'10min', source: 'sim_e1'|'obs_gantry', metric: 'flow'|'speed'}`
- API 协议：
  - 请求：`POST /api/v1/analyze_accuracy/`，Body：`{ result_folder, analysis_type }`
  - 响应：`{ result_folder, analysis_type, status, metrics, report_url, chart_urls, csv_urls, analysis_time }`
  - 历史结果回看：`GET /api/v1/analysis_results/{case_id}?analysis_type=accuracy|mechanism|performance` → 返回各时间戳目录的 `report_html/csv_files/chart_files`

#### 9. 健壮性与性能

- 输入容错：空目录、损坏XML、异构E1结构、无公共列
- 大数据：图表采样、数量上限（前5列）、错误跳过不阻断整体
- 字体与本地化：优先系统中文字体（Microsoft YaHei / SimHei / Noto Sans CJK），`rcParams` 统一设置

#### 10. 日志与可观测性

- 关键阶段 INFO：加载数据、文件计数、指标完成、图表数量、报告路径、总耗时
- 前端调试面板默认隐藏，可按需启用

#### 11. 分阶段实现（最小化可用优先）

- 阶段A（MVP，已具备/小改即得）

  - 仿真精度（flow）：总体/门架/时间的 MAPE、GEH均值、GEH≤5合格率、样本量；相关性统计入图表
  - 形成机理（sim-only）：流-速散点（sim）、速度时间序列（sim）、残差峰值偏移概览
  - 效率性能：E1文件数与有效记录、观测记录数、分析端到端耗时、产物规模、`summary.xml` 基础计数
- 阶段B（增强，需接入观测速度与收费站数据）

  - 仿真精度（speed）：门架平均速度的 MAPE/相关性（观测速度 × 仿真速度对齐）
  - 收费站：入口/出口流量对齐（前提：仿真侧存在相应E1或聚合输出）
  - 标签化：在 API 返回中附带图表/指标标签元数据
- 阶段C（对齐OD窗口与多案例回归）

  - OD起止窗口校验（仿真投放时段与观测窗口的一致性校验与提示）
  - 多案例对比与回归报告（基线 vs 当前）

注：不纳入 V/C、LOS、旅行时间可靠性等依赖“容量/旅行时间观测”的指标，直至相关数据可用。
