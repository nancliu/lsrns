# batch-optimization Specification

## Purpose
TBD - created by archiving change implement-plan-management-and-batch-optimization. Update Purpose after archive.
## Requirements
### Requirement: 用户可以创建批量仿真批次

用户MUST能够选择一个case和多个方案（包含基准方案），配置随机仿真次数和种子参数，创建批量仿真批次。系统自动生成所有任务（方案×种子数），创建批次目录结构，初始化元数据和进度跟踪文件。

**优先级**: P0
**状态**: 新增

#### Scenario: 创建包含3个方案的批量仿真批次

**Given**:
- Case case_001已存在
- 3个方案已存在：baseline_plan, plan_001, plan_002
- 所有方案的control.add.xml已生成

**When**:
- 用户发送POST /api/v1/control/optimization/batch
- 请求体包含：
  ```json
  {
    "case_id": "case_001",
    "plan_ids": ["baseline_plan", "plan_001", "plan_002"],
    "num_seeds": 3,
    "base_seed": 66
  }
  ```

**Then**:
- 系统生成batch_id（格式：batch_YYYYMMDD_HHMMSS）
- 系统创建批次目录：cases/case_001/simulations/plan_opti/{batch_id}/
- 系统生成9个任务（3 plans × 3 seeds）：
  - baseline_plan: seeds 66, 67, 68
  - plan_001: seeds 66, 67, 68
  - plan_002: seeds 66, 67, 68
- 系统保存batch_metadata.json
- 系统初始化batch_progress.json，所有任务status="pending"
- 返回201响应，包含batch_id和total_tasks=9
- 批次status为"pending"

---

#### Scenario: 创建批次时缺少基准方案

**Given**:
- 用户选择了plan_001和plan_002，但未包含baseline_plan

**When**:
- 用户发送POST /api/v1/control/optimization/batch
- 请求体plan_ids不包含"baseline_plan"

**Then**:
- 系统自动添加baseline_plan到plan_ids列表
- 或返回警告："建议包含基准方案用于对比"
- 批次正常创建（包含baseline_plan）

---

### Requirement: 系统执行批量并行仿真

系统MUST使用异步调度器并行执行批量仿真任务，支持动态并发控制（基于CPU线程数自动计算，默认为线程数×75%，可配置，支持40-60个任务并发）。对每个任务创建独立仿真目录、复制配置文件、添加随机种子参数、调用仿真服务，并实时更新任务状态和批次进度。

**优先级**: P0
**状态**: 新增

#### Scenario: 启动批量仿真并行执行

**Given**:
- 批次batch_001已创建，包含9个任务
- 批次status为"pending"

**When**:
- 用户发送POST /api/v1/control/optimization/batch/batch_001/start

**Then**:
- 系统更新批次status为"running"
- 系统记录started_at时间戳
- 系统启动异步调度器
- 调度器根据CPU线程数计算最大并发数（例如64线程服务器→48个并发）
- 调度器开始并发执行任务（根据计算结果并行）
- 对于每个任务：
  - 创建仿真目录：{batch_id}/{plan_id}/sim_{seed}/
  - 复制case配置文件
  - 复制plan的control.add.xml
  - 调用simulation_service.prepare_simulation()
  - 在sumocfg中添加--seed参数
  - 调用simulation_service.start_simulation()
  - 更新任务status为"running"
- 返回202响应："批量仿真已启动"

---

#### Scenario: 单个仿真任务成功完成

**Given**:
- 批次中的任务task_001正在运行
- 对应的仿真simulation_001

**When**:
- 仿真simulation_001完成

**Then**:
- 系统更新task_001的status为"completed"
- 记录completed_at时间戳
- 更新批次进度（progress增加1/9）
- 如有等待任务，启动下一个任务（保持配置的最大并发数）
- 更新batch_progress.json

---

#### Scenario: 单个仿真任务失败

**Given**:
- 批次中的任务task_002正在运行
- 仿真因错误失败

**When**:
- 仿真失败并抛出异常

**Then**:
- 系统更新task_002的status为"failed"
- 记录error消息
- 记录completed_at时间戳
- 批次继续执行其他任务（不中断）
- 如有等待任务，启动下一个
- 批次最终status可能为"completed_with_errors"

---

#### Scenario: 所有任务完成后批次状态更新

**Given**:
- 批次包含9个任务
- 8个任务已完成，1个正在运行

**When**:
- 最后1个任务完成

**Then**:
- 系统更新批次status为"completed"
- 记录completed_at时间戳
- 更新progress为1.0
- 生成批次汇总数据
- 保存batch_summary.json

---

### Requirement: 用户可以实时监控批量仿真进度

用户MUST能够通过API查询批次的实时进度，包括总体进度百分比、各任务状态、预计完成时间。前端通过轮询（每2秒）或WebSocket实时更新进度显示，展示每个方案和种子的执行状态。

**优先级**: P0
**状态**: 新增

#### Scenario: 查询批次进度

**Given**:
- 批次batch_001正在运行
- 15个任务已完成，30个正在运行，15个等待中（总共60个任务）

**When**:
- 用户发送GET /api/v1/control/optimization/batch/batch_001/progress

**Then**:
- 返回200响应
- 返回批次信息：
  - batch_id, status="running"
  - progress=0.25（15/60完成）
  - max_concurrent=48（当前配置的最大并发数）
  - estimated_completion（基于已完成任务的平均时长估算）
- 返回任务列表（60个），每个任务包含：
  - task_id, plan_id, plan_name, seed
  - status（"completed"/"running"/"pending"/"failed"）
  - simulation_id（如已启动）
  - started_at, completed_at（如适用）
  - progress（如running，显示仿真内部进度）
  - error（如失败）

---

#### Scenario: 前端轮询进度更新

**Given**:
- 前端批量仿真监控页面已打开
- JavaScript设置每2秒轮询一次

**When**:
- 定时器触发，发送GET /progress请求

**Then**:
- 后端返回最新进度
- 前端更新进度条（总进度和各任务进度）
- 前端更新任务状态图标
- 前端更新预计完成时间
- 如批次已完成，停止轮询并显示结果

---

### Requirement: 系统汇总批量仿真结果

系统MUST在批次完成后自动读取所有仿真结果文件，提取关键指标（平均行程时间、延误、速度、吞吐量），计算每个方案的聚合统计（均值、标准差、最小值、最大值），并生成方案对比摘要。

**优先级**: P0
**状态**: 新增

#### Scenario: 获取批次结果汇总

**Given**:
- 批次batch_001已完成
- 所有9个仿真都成功生成了tripinfo.xml和summary.xml

**When**:
- 用户发送GET /api/v1/control/optimization/batch/batch_001/results

**Then**:
- 系统读取所有仿真结果文件
- 对每个方案：
  - 提取3次仿真的关键指标（avg_travel_time, total_delay, avg_speed, throughput）
  - 计算聚合统计：mean, std, min, max
- 返回200响应，包含：
  ```json
  {
    "batch_id": "batch_001",
    "status": "completed",
    "plan_results": [
      {
        "plan_id": "baseline_plan",
        "plan_name": "基准方案",
        "simulations": [
          {"seed": 66, "simulation_id": "sim_001", "metrics": {...}},
          {"seed": 67, "simulation_id": "sim_002", "metrics": {...}},
          {"seed": 68, "simulation_id": "sim_003", "metrics": {...}}
        ],
        "aggregated_metrics": {
          "avg_travel_time": {"mean": 1448.5, "std": 5.2, ...},
          ...
        }
      },
      {
        "plan_id": "plan_001",
        ...
      },
      {
        "plan_id": "plan_002",
        ...
      }
    ]
  }
  ```

---

#### Scenario: 对比方案效果（基础对比）

**Given**:
- 批次结果已汇总
- baseline_plan平均行程时间为1448.5s
- plan_001平均行程时间为1250.3s
- plan_002平均行程时间为1180.8s

**When**:
- 用户查看结果汇总

**Then**:
- 前端显示对比表格：
  | 方案 | 平均行程时间 | 相比基准 |
  |------|--------------|----------|
  | 基准方案 | 1448.5s | - |
  | 方案A | 1250.3s | ↓ -13.7% |
  | 方案B | 1180.8s | ↓ -18.5% |
- 显示改善百分比
- 标记最优方案（方案B）

---

### Requirement: 系统提取并可视化在网车辆峰值曲线

系统MUST从summary.xml文件中提取时序数据，包括每个时间步的在网车辆数（running vehicles）、已装载车辆数（loaded）、已完成车辆数（ended）等指标。对于同一方案的多次随机仿真，系统计算平均值和标准差，并在结果视图中以折线图形式可视化在网车辆峰值曲线，支持多方案对比。

**优先级**: P1
**状态**: 新增

#### Scenario: 提取在网车辆时序数据

**Given**:
- 批次batch_001已完成
- plan_001包含3次仿真（seeds: 66, 67, 68）
- 每个仿真的summary.xml包含完整的step级别统计

**When**:
- 用户发送GET /api/v1/control/optimization/batch/batch_001/results?include_time_series=true

**Then**:
- 系统解析每个summary.xml文件
- 对每个<step>元素提取：
  - time: 仿真时间戳（秒）
  - running: 在网车辆数
  - loaded: 已装载车辆数
  - ended: 已完成车辆数
  - meanSpeed: 平均速度
- 对同一方案的3次仿真，按时间对齐并计算：
  - running_mean: 在网车辆数均值
  - running_std: 在网车辆数标准差
  - loaded_mean, ended_mean: 同理
- 返回时序数据结构：
  ```json
  {
    "plan_id": "plan_001",
    "time_series": {
      "time_points": [0, 60, 120, 180, ...],
      "running_vehicles": {
        "mean": [0, 45, 120, 230, ...],
        "std": [0, 2.1, 5.3, 8.7, ...],
        "max": [0, 47, 125, 239, ...],
        "min": [0, 43, 115, 221, ...]
      },
      "loaded_vehicles": {...},
      "ended_vehicles": {...}
    }
  }
  ```

---

#### Scenario: 前端可视化在网车辆峰值曲线

**Given**:
- 批次结果包含时序数据
- 结果视图已打开

**When**:
- 用户查看结果页面

**Then**:
- 前端使用Chart.js或ECharts渲染折线图
- X轴：仿真时间（秒或小时:分钟格式）
- Y轴：在网车辆数
- 每个方案显示一条曲线（不同颜色）
- 主线：running_vehicles_mean
- 阴影区域：mean ± std（可选）
- 图例显示方案名称
- 支持鼠标悬停查看具体数值
- 支持缩放和平移

---

#### Scenario: 多方案在网车辆对比

**Given**:
- 批次包含3个方案（baseline_plan, plan_001, plan_002）
- 所有方案已完成仿真并提取时序数据

**When**:
- 用户在结果视图查看"在网车辆峰值曲线"

**Then**:
- 图表同时显示3条曲线：
  - 蓝色实线：基准方案（无管控）
  - 绿色实线：方案A（管控措施1）
  - 橙色实线：方案B（管控措施2）
- 用户可观察：
  - 峰值差异：管控措施是否降低了峰值
  - 峰值时刻：峰值是否提前或延后
  - 曲线面积：总在网车辆时长差异
- 图表下方显示关键指标：
  - 峰值在网车辆数
  - 峰值发生时刻
  - 平均在网车辆数

---

### Requirement: 用户可以取消正在运行的批量仿真

用户MUST能够随时取消正在运行的批量仿真批次。系统停止启动新任务、尝试终止运行中的任务、将等待中的任务标记为已取消，并保留已完成任务的结果。

**优先级**: P1
**状态**: 新增

#### Scenario: 取消批量仿真

**Given**:
- 批次batch_001正在运行
- 2个任务已完成，2个正在运行，5个等待中

**When**:
- 用户发送DELETE /api/v1/control/optimization/batch/batch_001

**Then**:
- 系统停止启动新任务
- 系统尝试停止正在运行的2个仿真
- 系统更新所有pending任务为"cancelled"
- 系统更新批次status为"cancelled"
- 返回204响应
- 已完成的2个任务结果保留

---

### Requirement: 系统管理仿真结果存储

系统MUST为每个批量仿真任务创建规范的目录结构，存储在cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/路径下。每个仿真目录包含完整的配置文件、输出文件和元数据，元数据记录plan_id、seed、batch_id等关键信息。

**优先级**: P0
**状态**: 新增

#### Scenario: 存储仿真结果到正确目录

**Given**:
- 批次batch_001包含plan_001
- 任务执行plan_001的seed=66仿真

**When**:
- 仿真执行并完成

**Then**:
- 结果存储在：
  `cases/case_001/simulations/plan_opti/batch_001/plan_001/sim_66/`
- 目录包含：
  - simulation.sumocfg
  - control.add.xml（从方案复制）
  - summary.xml
  - tripinfo.xml
  - simulation_metadata.json（包含plan_id和seed）
- simulation_metadata.json包含：
  ```json
  {
    "simulation_id": "sim_001",
    "case_id": "case_001",
    "plan_id": "plan_001",
    "seed": 66,
    "batch_id": "batch_001",
    ...
  }
  ```

---

### Requirement: 系统处理多次随机仿真的种子管理

系统MUST为每个方案生成多次随机仿真任务（默认3次），使用连续递增的种子值（默认从66开始）。同一方案的不同次仿真使用不同种子，不同方案的同一轮次使用相同种子，便于交叉对比。每个仿真的sumocfg正确配置对应的种子参数。

**优先级**: P0
**状态**: 新增

#### Scenario: 为每个方案生成3次随机仿真

**Given**:
- 用户配置num_seeds=3, base_seed=66
- 批次包含2个方案

**When**:
- 系统创建批次

**Then**:
- 生成6个任务：
  - plan_001: seed 66, 67, 68
  - plan_002: seed 66, 67, 68
- 每个任务的sumocfg包含对应的--seed参数
- 同一方案的3次仿真使用不同种子
- 不同方案的同一轮次使用相同种子（便于对比）

---

### Requirement: 用户可以查看详细的方案优化分析

用户MUST能够在批次完成后查看详细的方案优化分析。系统提供两种入口：
1. 批量仿真页面完成后显示"查看详细优化分析"按钮
2. 方案优化页面直接通过URL参数加载批次结果

前端通过URL参数传递batch_id，方案优化页面自动加载对应批次的结果数据，展示详细的对比分析、在网车辆峰值曲线和多指标雷达图。

**优先级**: P0
**状态**: 新增

#### Scenario: 批次完成后从批量仿真页面查看详细分析

**Given**:
- 批次batch_001在批量仿真页面已完成
- 用户查看结果视图

**When**:
- 用户点击"查看详细优化分析"按钮

**Then**:
- 前端跳转到：/control/optimization.html?batch_id=batch_001
- 方案优化页面自动加载batch_001的结果数据
- 显示批次信息卡片（batch_id、case_id、方案数量、完成时间）
- 显示方案对比表（包含相比基准的改善百分比）
- 显示在网车辆峰值曲线（多方案对比折线图）
- 显示峰值指标卡片（峰值车辆数、峰值时刻、平均车辆数）
- 显示多指标雷达图（归一化的综合对比）

---

#### Scenario: 直接访问方案优化页面（带batch_id参数）

**Given**:
- 用户从外部链接或书签访问 optimization.html?batch_id=batch_002
- batch_002已完成

**When**:
- 页面加载

**Then**:
- optimization.js 从URL参数读取 batch_id=batch_002
- 调用 GET /api/v1/control/optimization/batch/batch_002/results?include_time_series=true
- 加载并显示批次结果（同上）

---

#### Scenario: 直接访问方案优化页面（无batch_id参数）

**Given**:
- 用户直接访问 /control/optimization.html（不带batch_id参数）

**When**:
- 页面加载

**Then**:
- 显示批次选择区域
- 提示用户：请从批量仿真页面完成仿真后查看结果
- 显示"返回批量仿真"链接
- （未来可扩展：显示历史批次列表供选择）

---

#### Scenario: 从方案优化页面返回批量仿真页面

**Given**:
- 用户在方案优化页面查看结果

**When**:
- 用户点击"返回批量仿真"按钮

**Then**:
- 前端跳转到：/control/simulations.html
- 批量仿真页面加载（默认显示配置视图）

---

#### Scenario: sumocfg正确配置随机种子

**Given**:
- 任务使用seed=67

**When**:
- 系统准备仿真配置

**Then**:
- sumocfg的<random>部分包含：
  ```xml
  <random>
      <seed value="67"/>
  </random>
  ```
- 或命令行添加：--seed 67

---

