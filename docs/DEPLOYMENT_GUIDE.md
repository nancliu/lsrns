# 部署与使用指导（Windows）

本工程用于“生成仿真 → 运行 SUMO → 结果分析（精度/机理/性能）→ 报告输出”的全流程。本文档面向团队成员的本地/服务器部署与日常使用。

---

## 1. 环境要求

- 操作系统：Windows 10/11
- Python：3.10（建议使用 mamba/conda 虚拟环境）
- SUMO：1.19+（需安装并配置环境变量）
- VPN登录，可访问数据库服务器（门架/OD 等）

## 2. 安装步骤（推荐）

> 禁止在 base 环境安装业务包；优先使用 mamba 安装，也可使用conda，无法安装的再用 pip。

1) 创建并启用虚拟环境

```powershell
mamba create -n od-sim python=3.10 -y
mamba activate od-sim
```

2) 安装依赖（先尝试 mamba 基于 requirements.txt 安装，其次 pip 补充）

```powershell
# 先尝试使用 mamba 基于 requirements.txt 安装（推荐）
mamba install -y -c conda-forge --file requirements.txt

# 如 mamba 报冲突或对诸如 "uvicorn[standard]" 等 extras 不支持，再使用 pip 补充安装
pip install -r requirements.txt
```

3) 安装 SUMO 并配置环境变量

- 安装 SUMO 后设置系统变量 `SUMO_HOME` 指向 SUMO 安装目录
- 将 `%SUMO_HOME%\bin` 加入 `PATH`
- 也可设置 `SUMO_BIN` 为 sumo.exe 完整路径
- powershell或cmd中可正常调用sumo及sumo-gui命令

4) 数据库连接（观测数据）

- 使用 `.env` 文件（后端会自动读取）。先复制模板：

```powershell
copy templates\env.example .env
```

- 按需编辑 `.env` 内容：

```env
DB_NAME=sdzg
DB_USER=你的用户名
DB_PASSWORD=你的密码
DB_HOST=10.149.235.123
DB_PORT=5432

# 可选：SUMO 定位（未在 PATH 时使用其一）
# SUMO_HOME=C:\Program Files (x86)\Eclipse\Sumo
# SUMO_BIN=C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe
```

## 3. 启动后端与前端

- 启动 API（包含前端静态资源）

```powershell
./start_api.bat
```

- 浏览器访问前端主页：`http://localhost:8000/index.html`

## 4. 典型使用流程

### 4.1 模板查看

- 在“模板查看”栏目中查看可用的 TAZ 与道路网络模板（建议选择 TAZ_5 与 v6 网络模板）。

### 4.2 OD 数据处理

- 设置时间窗（建议整分钟）
- 选择 TAZ 与网络文件
- 仿真输出配置：默认开启 `summary` 与 `tripinfo`（机理分析需要）；`vehroute/netstate/fcd/emission` 视诊断需要开启
- 提交后将生成案例：`cases/case_YYYYMMDD_HHMMSS/`，并写入 `config/simulation.sumocfg` 与路由/OD 文件

### 4.3 仿真运行

- 在“仿真运行”栏目选择案例，点击“启动仿真”
- 页面自动轮询进度（基于 `simulation/summary.xml`），完成后产物在 `cases/{case_id}/simulation/`

### 4.4 结果分析（结果分析栏目）

- 分析类型：
  - 精度：门架 E1 vs 门架观测（MAPE/GEH 等），生成报告与图表/CSV
  - 机理：OD“观测 vs 输入”“输入 vs 输出”对比，E1 速度机理图，生成报告与图表/CSV
  - 性能：summary.xml 步数/峰值，产物规模与体量，生成报告
- 点击“开始分析”→ 完成后可“查看报告”
- “查看历史结果”按类型列出 `analysis/{accuracy|mechanism|performance}/accuracy_results_*` 目录中的产物

## 5. 产物目录结构（案例内）

```
cases/{case_id}/
  ├─ config/                         # OD/ROU/SUMO 配置
  ├─ simulation/                     # SUMO 运行输出（summary.xml/tripinfo.xml/e1/*.xml 等）
  └─ analysis/
      ├─ accuracy/accuracy_results_时间戳/     # 精度分析报告、图表、CSV
      ├─ mechanism/accuracy_results_时间戳/    # 机理分析报告、图表、CSV
      └─ performance/accuracy_results_时间戳/  # 性能分析报告
  └─ metadata.json                   # 记录三类分析最近一次报告链接与时间等摘要
```

## 6. 机理分析要点

- CSV 对比：
  - `od_observed_vs_input.csv`（观测 vs 输入）
  - `od_input_vs_simoutput.csv`（输入 vs 输出）
- 速度时间序列：使用 E1 interval 的速度字段（`speed` 或 `meanSpeed`，自动转为 km/h）
- 若“输入 vs 输出”缺失：需在“OD 数据处理”时勾选 `tripinfo`（或 `vehroute`）

## 7. 性能分析要点

- 报告包含：
  - summary.xml 摘要（steps、loaded/inserted/ended、running_max、waiting_max）
  - 产物规模（simulation/analysis 目录文件数与总体积）
  - 建议：当 waiting_max 较高或 analysis 体量过大时的优化提示（调小时间切片、关闭重输出、启用 .xml.gz 压缩）

## 8. 常见问题与排查

- 精度分析“无法解析时间范围”
  - 检查 `cases/{case_id}/metadata.json` 的 `time_range` 是否完整
  - 或确认 `config/simulation.sumocfg` 中存在 `<!-- real_start=..., real_end=... -->` 注释
- 机理分析无“输入 vs 输出”
  - tripinfo/vehroute 未生成 → 在“OD 数据处理”勾选 `tripinfo`
- E1 无速度
  - 使用的检测器未输出速度字段 → 可仅生成 OD 对比类图表，速度图表将自动跳过
- SUMO 未找到
  - 设置 `SUMO_HOME` 与 `PATH`；或设置 `SUMO_BIN` 指向 sumo.exe

## 9. 注意事项与弃用说明

- 唯一 sumocfg 生成实现：`api/utils.generate_sumocfg`（避免混用）
- `shared/data_processors/simulation_processor.generate_sumocfg` 已弃用（保留但抛出说明性异常）
- `sim_scripts/*`、`accuracy_analysis` 目录下部分脚本为旧版/样例，仅用于研发/验证，勿与主实现混用
- 安装依赖必须在非 base 环境；优先 mamba 安装，无法安装的再 pip

## 10. 后端 API（自动化集成）

- 触发分析（统一入口）

```http
POST /api/v1/analyze_accuracy/
Body: { "result_folder": "cases/{case_id}/analysis/accuracy", "analysis_type": "accuracy|traffic_flow|performance" }
```

- 历史结果

```http
GET /api/v1/analysis_results/{case_id}?analysis_type=accuracy|mechanism|performance
```

- 仿真进度

```http
GET /api/v1/simulation_progress/{case_id}
```

## 11. 上线前检查清单

- [ ] Python 虚拟环境已用 mamba 创建并激活
- [ ] requirements 已安装
- [ ] SUMO_HOME 与 PATH 设置正确（可运行 sumo.exe）
- [ ] 数据库 .env 已配置（DB_NAME/USER/PASSWORD/HOST/PORT）
- [ ] 启动后端成功，前端可访问
- [ ] 选择模板 → 处理OD → 运行仿真 → 三类分析 → 报告可打开
