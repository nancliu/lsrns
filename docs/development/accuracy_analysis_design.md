### 精度分析设计方案（v1.0）

#### 1. 目标

- 以统一管线评估仿真与观测数据的一致性，快速定位偏差来源，支持回归对比与持续改进。
- 产出可视化报告（HTML）与结构化结果（JSON/CSV），供前端展示与二次分析。

#### 2. 范围

- 输入：SUMO 仿真输出（E1、summary.xml）、观测数据（门架/断面）。
- 输出：核心指标、层级细分指标、诊断图表、明细数据与报告页面。
- 暂不包含：模型参数自动校准/寻优（后续版本）。

#### 3. 数据输入

- 仿真路径：`cases/{case_id}/simulation`
  - E1：`simulation/e1/**/*.xml` 或 `e1_detectors/*.xml`（自动递归）
  - summary：`simulation/summary.xml`（用于统计辅助）
- 观测数据：API 先内置模拟数据，预留数据库/文件（CSV/Parquet）接入接口。
- 时间/容量配置（可选）：用于计算 V/C、自由流速度等。

#### 4. 目录与产出

- 图表：`cases/{case_id}/analysis/accuracy/charts/*.png`
- 报告：`cases/{case_id}/analysis/accuracy/reports/accuracy_report.html`
- 结构化：`cases/{case_id}/analysis/accuracy/reports/analysis_results.json`
- 静态访问：`/cases/{case_id}/analysis/accuracy/{charts|reports}/...`

#### 4.1 目录结构对齐（与《工程结构优化设计方案.md》一致）

```
O```
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

```

```

说明：

- 报告内图片使用相对路径 `../charts/*.png`；服务层已挂载 `/cases` 为静态目录，浏览器可直接访问报告与图表。
- E1 数据递归加载，兼容 `simulation/e1` 及以 `e1*` 命名的子目录。

#### 5. 指标体系

- 核心一致性指标（对 flow/occupancy/speed 分别计算）：
  - MAE/MSE/RMSE、MAPE（过滤 0 分母）、Pearson 相关系数。
  - GEH：`sqrt(2*(sim-obs)^2/(sim+obs))`，统计均值/分布/合格率（≤5）。
- 层级细分：
  - 门架/断面：每个 id 的指标与 Top 榜。
  - 时间粒度：分钟/5分钟/10分钟聚合（默认与观测粒度一致）。
- 诊断统计：
  - 残差分布（sim - obs）、峰值偏移、拟合线（斜率/截距）判断系统性偏差。

#### 6. 可视化

- 时间序列对比（flow/occupancy/speed）。
- 散点图（含对角线/拟合线）。
- 分布直方图（仿真 vs 观测重叠）。
- 残差直方图（flow）。
- 指标柱状图（汇总）。
- 门架 Top 榜图（后续增强：热力图/基本图 flow–speed）。

#### 7. 报告页面（HTML）

- 概览卡片：MAPE、GEH均值/合格率、相关系数、样本量。
- 图表区：按数据类型分组插图，支持折叠/展开。
- 表格区：Top 偏差门架、异常明细（可下载CSV）。
- 元信息：案例ID、时间范围、生成时间、图表清单。
- 链接：图表相对路径 `../charts/*.png`，外部可通过 `/cases` 访问。

#### 8. 后端设计

- 分析器抽象 `BaseAnalyzer`：
  - `load_data(simulation_folder)`
  - `compute_metrics(sim, obs)`
  - `generate_charts(...)`
  - `generate_report(...)`
  - `export_results(...)`
- `AccuracyAnalyzer`（当前实现并持续增强）：
  - 递归加载 E1、多命名兼容、健壮解析 summary.xml。
  - 公共列对齐、长度对齐、容错去噪。
  - 输出 charts/report/results，并回传 `report_url`/`chart_urls`。
- API 协议（已兼容）：
  - 请求：`{ result_folder, analysis_type }`
  - 响应：`{ result_folder, analysis_type, status, metrics, report_url, chart_urls, analysis_time }`

#### 9. 健壮性与性能

- 输入容错：空目录、损坏XML、异构E1结构、无公共列。
- 大数据策略：图表采样、限数量（前5列）、错误跳过不阻断整体。
- 字体与本地化：优先系统中文字体（Microsoft YaHei / SimHei / Noto Sans CJK），`rcParams` 统一设置。

#### 10. 日志与可观测性

- 关键阶段 INFO：加载数据、文件计数、指标完成、图表数量、报告路径。
- 前端调试面板默认隐藏，可按需启用。

#### 11. 后续扩展

- 观测数据接入数据库（配置 schemas/table）。
- 可选容量表与自由流速度，用于 V/C 与拥堵指数（交通流分析）。
- 多案例对比与回归报告（基线 vs 当前）。
