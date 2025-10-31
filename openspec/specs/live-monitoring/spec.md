# live-monitoring Specification

## Purpose
TBD - created by archiving change enhance-batch-simulation-monitoring. Update Purpose after archive.
## Requirements
### Requirement: 系统实时提取运行中仿真的状态指标

系统MUST在批次进度查询时，对每个状态为"running"的任务，从其对应的summary.xml文件中提取最新的仿真状态指标，包括当前步数(current_step)、在网车辆数(running_vehicles)、已完成车辆数(ended_vehicles)。系统SHOULD使用增量解析方式（仅解析最后一个`<step>`元素），避免重复解析整个文件。

**注**：进度监控阶段不提取平均速度(mean_speed)，简化进度视图。速度指标仅在结果视图中展示。

**优先级**: P0
**状态**: 新增

#### Scenario: 提取运行中仿真的最新状态

**Given**:
- 批次batch_001正在运行
- 任务task_001（plan_001, seed=66）状态为"running"
- 对应仿真目录存在summary.xml文件
- summary.xml包含当前1500步数据（总14400步）
- 最新<step>元素：
  ```xml
  <step time="1500" running="320" loaded="500" ended="150" meanSpeed="25.3" />
  ```

**When**:
- 用户调用 `GET /api/v1/control/batch-optimization/batch/batch_001/progress`

**Then**:
- 系统检测到task_001状态为"running"
- 系统定位summary.xml: `cases/case_001/simulations/plan_opti/batch_001/plan_001/sim_66/summary.xml`
- 系统解析最后一个`<step>`元素
- 系统提取状态指标
- 返回task_001的live_status（简化版，不含速度）:
  ```json
  {
    "task_id": "task_001",
    "status": "running",
    "live_status": {
      "current_step": 1500,
      "total_steps": 14400,
      "progress_percent": 10.4,
      "running_vehicles": 320,
      "ended_vehicles": 150,
      "loaded_vehicles": 500
    }
  }
  ```

---

#### Scenario: 处理summary.xml不存在的情况

**Given**:
- 任务task_002状态为"running"
- 仿真刚启动，summary.xml尚未生成

**When**:
- 系统尝试提取live_status

**Then**:
- 系统检测到summary.xml不存在
- 系统返回task_002的状态：
  ```json
  {
    "task_id": "task_002",
    "status": "running",
    "live_status": {
      "current_step": 0,
      "total_steps": 14400,
      "progress_percent": 0,
      "message": "仿真正在初始化..."
    }
  }
  ```
- 不报错，继续处理其他任务

---

#### Scenario: 处理summary.xml解析失败

**Given**:
- 任务task_003状态为"running"
- summary.xml存在但格式错误（文件损坏或写入中）

**When**:
- 系统尝试解析summary.xml

**Then**:
- 系统捕获XML解析异常
- 系统记录警告日志："Failed to parse summary.xml for task_003"
- 系统返回task_003的状态：
  ```json
  {
    "task_id": "task_003",
    "status": "running",
    "live_status": {
      "error": "无法读取仿真状态"
    }
  }
  ```
- 不报错，继续处理其他任务

---

### Requirement: 系统估算单个仿真任务的剩余时间

系统MUST基于已完成的步数和平均步时长，估算单个仿真任务的剩余时间。系统SHOULD使用以下公式：
- `avg_step_duration = (current_time - started_at) / current_step`
- `remaining_steps = total_steps - current_step`
- `estimated_remaining_seconds = avg_step_duration * remaining_steps`

**优先级**: P0
**状态**: 新增

#### Scenario: 估算仿真剩余时间

**Given**:
- 任务task_001已运行150秒
- current_step = 1500, total_steps = 14400
- started_at = "2025-10-29T10:00:00"
- current_time = "2025-10-29T10:02:30"

**When**:
- 系统计算剩余时间

**Then**:
- 计算avg_step_duration: 150秒 / 1500步 = 0.1秒/步
- 计算remaining_steps: 14400 - 1500 = 12900步
- 计算estimated_remaining_seconds: 0.1 * 12900 = 1290秒 (21分30秒)
- 返回live_status:
  ```json
  {
    "current_step": 1500,
    "total_steps": 14400,
    "progress_percent": 10.4,
    "estimated_remaining_seconds": 1290,
    "estimated_remaining_display": "21分30秒"
  }
  ```

---

#### Scenario: 仿真初期剩余时间估算不准确

**Given**:
- 任务task_002刚运行5秒
- current_step = 10（样本太少）
- 仿真预计持续1-24小时（取决于管控复杂度和策略配置）

**When**:
- 系统计算剩余时间

**Then**:
- 系统检测到current_step < 100（阈值可配置）
- 系统返回：
  ```json
  {
    "estimated_remaining_seconds": null,
    "estimated_remaining_display": "计算中..."
  }
  ```
- 或使用默认估算值（基于历史批次平均时长）
- **注**：对于长时仿真（6-24小时），初期准确估算更为关键，建议在运行5-10分钟后提供相对准确的预估

---

### Requirement: 系统估算批次总剩余时间

系统MUST基于所有任务的状态和剩余时间，估算批次总剩余时间。系统SHOULD考虑并发执行的影响，使用以下逻辑：
- 对running任务：使用单个任务的estimated_remaining_seconds
- 对pending任务：使用已完成任务的平均时长
- 考虑max_concurrent并发数，计算任务队列的等待时间

**优先级**: P1
**状态**: 新增

#### Scenario: 估算批次总剩余时间

**Given**:
- 批次包含60个任务
- 15个已完成，平均时长600秒/任务
- 5个running：
  - task_a: 剩余300秒
  - task_b: 剩余450秒
  - task_c: 剩余200秒
  - task_d: 剩余500秒
  - task_e: 剩余400秒
- 40个pending
- max_concurrent = 5

**When**:
- 系统计算批次剩余时间

**Then**:
- 计算running任务的最长剩余时间: max(300, 450, 200, 500, 400) = 500秒
- 计算pending任务总时长: 40 * 600 = 24000秒
- 考虑并发，分批执行: 24000 / 5 = 4800秒
- 批次总剩余时间: 500 + 4800 = 5300秒 (约88分钟)
- 返回:
  ```json
  {
    "batch_status": "running",
    "progress": 0.25,
    "estimated_completion_seconds": 5300,
    "estimated_completion_display": "约1小时28分",
    "estimated_completion_time": "2025-10-29T11:30:00"
  }
  ```

---

### Requirement: 前端实时显示仿真状态和剩余时间

前端进度视图MUST在任务列表中显示每个running任务的实时状态，包括在网车辆数、进度百分比、预计剩余时间。前端SHOULD以倒计时形式显示剩余时间，每秒更新。前端MUST每10秒轮询一次进度API（从原2秒调整为10秒）。

**注**：进度视图简化，不显示平均速度。速度指标移至结果视图展示。

**优先级**: P0
**状态**: 新增

#### Scenario: 进度视图显示实时状态

**Given**:
- 批量仿真页面进度视图已打开
- 批次正在运行
- 前端每2秒轮询一次进度API

**When**:
- 前端收到包含live_status的进度数据
- 任务task_001状态为"running"，live_status包含：
  - running_vehicles: 320
  - mean_speed_kmh: 91.1
  - progress_percent: 10.4
  - estimated_remaining_seconds: 1290

**Then**:
- 前端在任务列表中显示task_001的状态（简化版）：
  ```
  | 任务ID    | 方案   | 种子 | 状态     | 进度 | 在网车辆 | 预计剩余 |
  |-----------|--------|------|----------|------|----------|----------|
  | task_001  | 方案A  | 66   | 运行中   | 10%  | 320辆    | 21分30秒 |
  ```
- 进度条显示10.4%（带动画）
- 剩余时间每秒递减（客户端倒计时）
- 在网车辆数实时更新（每10秒刷新）
- **不显示平均速度**（简化进度视图）

---

#### Scenario: 批次级剩余时间显示

**Given**:
- 批次总剩余时间为5300秒（约88分钟）
- 预计完成时间：2025-10-29T11:30:00

**When**:
- 前端显示批次进度

**Then**:
- 批次信息卡片显示：
  ```
  批次ID: batch_001
  状态: 运行中
  总进度: 25% (15/60 已完成)
  预计完成时间: 11:30 AM
  剩余时间: 约1小时28分
  ```
- 剩余时间每秒递减
- 如剩余时间 <5分钟，显示精确秒数："4分32秒"

---

### Requirement: 系统优化进度查询性能

系统MUST使用缓存机制优化进度查询性能，避免频繁读取文件系统和重复解析XML。系统SHOULD实现：
1. 内存缓存（TTL=5秒）：批次进度数据
2. 增量解析summary.xml：仅解析最后一个`<step>`元素
3. 异步更新：后台定时更新缓存，前端查询直接返回缓存

**优先级**: P1
**状态**: 新增

#### Scenario: 缓存机制减少文件读取

**Given**:
- 批次batch_001正在运行
- 前端每2秒轮询进度
- 未使用缓存时，每次查询需读取60个summary.xml文件

**When**:
- 第1次请求：`GET /progress` at 10:00:00
- 第2次请求：`GET /progress` at 10:00:02 (2秒后)
- 第3次请求：`GET /progress` at 10:00:04 (4秒后)
- 第4次请求：`GET /progress` at 10:00:06 (6秒后，超过TTL)

**Then**:
- 第1次请求：
  - 缓存未命中
  - 读取文件系统，解析数据
  - 存入缓存（TTL=5秒）
  - 响应时间：150ms
- 第2次请求：
  - 缓存命中（2秒 < 5秒TTL）
  - 直接返回缓存数据
  - 响应时间：10ms
- 第3次请求：
  - 缓存命中（4秒 < 5秒TTL）
  - 直接返回缓存数据
  - 响应时间：10ms
- 第4次请求：
  - 缓存过期（6秒 > 5秒TTL）
  - 重新读取文件系统，刷新缓存
  - 响应时间：150ms

---

#### Scenario: 增量解析summary.xml

**Given**:
- summary.xml文件大小：5MB（包含1500个<step>元素）
- 仅需最后一个<step>的数据

**When**:
- 系统解析summary.xml获取最新状态

**Then**:
- 系统使用seekable文件读取
- 从文件末尾向前搜索最后一个`</step>`标签
- 提取最后一个<step>元素（约200字节）
- 解析时间：<5ms（相比全文解析的50ms）

---

### Requirement: 系统提供动态在网车辆数曲线

系统MUST在批次进度查询响应中，提供汇总所有running任务的实时时序数据(live_time_series)，用于前端绘制动态在网车辆曲线。系统SHOULD汇总当前所有running任务的在网车辆数，按时间点聚合。

**优先级**: P1
**状态**: 新增

#### Scenario: 汇总多个运行中任务的时序数据

**Given**:
- 批次batch_001正在运行
- 3个任务处于running状态：
  - task_001: current_step=1500, running_vehicles=320
  - task_002: current_step=1500, running_vehicles=280
  - task_003: current_step=1000, running_vehicles=150
- 所有任务的总steps=14400

**When**:
- 系统计算live_time_series

**Then**:
- 系统从每个running任务的summary.xml提取完整时序数据
- 系统按时间点对齐并汇总在网车辆数
- 返回汇总的时序数据:
  ```json
  {
    "live_time_series": {
      "time_points": [0, 100, 200, ..., 1500],
      "total_running": [0, 80, 150, ..., 600],
      "task_count": 3,
      "last_update": "2025-10-29T10:25:00"
    }
  }
  ```
- time_points包含从0到当前最长任务的步数
- total_running为所有任务在每个时间点的在网车辆数之和

---

#### Scenario: 无运行中任务时返回空时序数据

**Given**:
- 批次batch_001所有任务都已完成或等待中
- 没有running状态的任务

**When**:
- 系统计算live_time_series

**Then**:
- 系统返回空时序数据:
  ```json
  {
    "live_time_series": {
      "time_points": [],
      "total_running": [],
      "task_count": 0
    }
  }
  ```
- 前端检测到空数据后，自动隐藏动态曲线区域

---

### Requirement: 前端显示动态在网车辆曲线

前端进度视图MUST在任务列表下方显示动态在网车辆曲线，汇总所有running任务的在网车辆数。前端SHOULD使用简单折线图（无放大、缩放、导出等复杂功能）。前端MUST在无运行批次时自动隐藏曲线区域。

**优先级**: P1
**状态**: 新增

#### Scenario: 进度视图显示动态曲线

**Given**:
- 批量仿真页面进度视图已打开
- 批次正在运行
- 进度API返回live_time_series数据（非空）

**When**:
- 前端接收到进度数据，包含live_time_series
- 前端调用renderLiveCurve()方法

**Then**:
- 前端在任务列表下方显示"动态在网车辆数曲线"区域
- 使用Chart.js绘制简单折线图：
  - X轴：仿真时间（HH:MM格式）
  - Y轴：总在网车辆数（辆）
  - 单一曲线，浅绿色填充
  - 无图例（只有一条曲线）
  - 无缩放、平移、导出按钮
- 曲线随每次轮询（10秒）自动更新
- 曲线平滑渲染（使用Chart.js tension参数）

---

#### Scenario: 无运行批次时自动隐藏曲线

**Given**:
- 进度视图已打开
- 批次已完成或无运行中任务
- 进度API返回live_time_series为空数组

**When**:
- 前端接收到空的live_time_series数据
- 前端调用renderLiveCurve()方法

**Then**:
- 前端检测到time_points数组为空
- 自动隐藏"动态在网车辆数曲线"区域（display: none）
- 不显示空白图表或占位符

---

#### Scenario: 曲线每10秒自动更新

**Given**:
- 动态曲线已显示
- 前端每10秒轮询进度API

**When**:
- 前端接收到新的live_time_series数据
- time_points从[0, 100, ..., 1500]更新为[0, 100, ..., 1600]
- total_running也相应更新

**Then**:
- 前端销毁旧的Chart实例
- 使用新数据重新创建Chart实例
- 曲线自动向右延伸，显示新的数据点
- 动画平滑过渡（Chart.js默认动画）

---

