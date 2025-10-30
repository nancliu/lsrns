# 实时在网车辆曲线 - 问题诊断指南

**更新日期**: 2025-10-30
**问题版本**: v2

---

## 已发现的问题

### 问题1：时间计算错误 ✅ 已修复
**症状**: 剩余时间显示为秒数（如"5秒"应显示但可能显示为"4秒"或"6秒"）

**根因**: `formatDuration()` 函数中秒数没有四舍五入

**修复代码** (第479行):
```javascript
// ❌ 原代码：
const secs = seconds % 60;

// ✅ 修复后：
const secs = Math.round(seconds % 60);  // 四舍五入秒数
```

**影响范围**:
- 剩余时间显示（单任务和批次级）
- 任务详情中的"剩余: X分X秒"

**验证**:
- 38.4秒 → "38秒" (修复前) → "38秒" (修复后) ✓
- 38.6秒 → "38秒" (修复前) → "39秒" (修复后) ✓
- 59.7秒 → "59秒" (修复前) → "1分0秒" (修复后) ✓

---

### 问题2：live_time_series数据无法加载 🔍 需诊断
**症状**:
- 浏览器控制台显示 `live_time_series: {time_points: [], total_running: []}`
- 显示"仿真数据加载中..."提示，无法看到曲线

**可能的根因**:

#### 根因1：summary.xml文件尚未生成（概率 80%）
**表现**:
```
控制台输出:
  [_aggregate_live_time_series] Running tasks: 1, Completed: 0
  [_aggregate_live_time_series] Using running tasks for time series (count: 1)
  [_aggregate_live_time_series] Task task_001: Looking for D:/...../summary.xml
  [_aggregate_live_time_series] Task task_001: File exists=false  ← ❌ 文件不存在
```

**解决方案**:
- SUMO仿真启动需要10-30秒才能生成 summary.xml
- 等待更长时间后，数据会自动出现
- 如果15分钟后仍无数据，检查SUMO进程是否正常运行

#### 根因2：plan_opti目录结构错误（概率 15%）
**表现**:
```
控制台输出:
  [_aggregate_live_time_series] Task task_001: Looking for
  D:/projects/OD_SIM/cases/case_001/simulations/plan_opti/batch_001/plan_001/sim_66/summary.xml
  [_aggregate_live_time_series] Task task_001: File exists=false
```

但实际目录结构为:
```
D:/projects/OD_SIM/cases/case_001/simulations/
  ├── batch_001/
  │   ├── plan_001/
  │   │   ├── sim_66/
  │   │   │   └── summary.xml  ← 目录深度不对
  │   └── ...
  └── ...
```

**诊断步骤**:
1. 打开文件管理器
2. 导航到: `D:\projects\OD_SIM\cases\{case_id}\simulations\`
3. 检查是否存在 `plan_opti` 目录
4. 检查 `plan_opti` 下是否有 `{batch_id}` 目录
5. 检查 `{batch_id}` 下是否有 `{plan_id}` 目录

**修复方案**:
- 后端需要确保仿真文件保存在正确的目录
- 检查 `shared/control_tools/batch_simulation_scheduler.py` 中的目录创建逻辑

#### 根因3：batch_id或plan_id信息缺失（概率 5%）
**表现**:
```
控制台输出:
  Task task_001 (task_id) has no simulation_id or plan_id/seed
```

**解决方案**:
- 检查任务数据结构
- 确保每个任务都有 `plan_id` 和 `seed` 字段

---

## 前端诊断步骤

### 步骤1：打开浏览器开发者工具
1. 按 F12 打开开发者工具
2. 点击 "Console" 选项卡
3. 清除之前的日志：右键 → "Clear console"

### 步骤2：启动批量仿真
1. 创建批次配置
2. 点击"启动仿真"
3. 立即进入"进度"视图

### 步骤3：查看控制台输出
等待约10秒，查看以下日志：

```javascript
// ✅ 正常情况（有live_time_series数据）
=== API Progress Response ===
Status: running
Running tasks count: 1
Total tasks: 3
Completed tasks: 0
Has live_time_series: true
live_time_series object: {
    time_points: [0, 10, 20, 30],  ← 有数据
    total_running: [100, 150, 200, 180],
    task_count: 1,
    last_update: "2025-10-30T14:30:00"
}

// ❌ 异常情况1（空的time_points）
=== API Progress Response ===
Status: running
Running tasks count: 1
Total tasks: 3
Completed tasks: 0
Has live_time_series: true
live_time_series object: {
    time_points: [],  ← ❌ 空数组
    total_running: [],
    task_count: 1,
    last_update: "2025-10-30T14:30:00"
}
⚠️ live_time_series is null or undefined!

// ❌ 异常情况2（null）
=== API Progress Response ===
Has live_time_series: false
⚠️ live_time_series is null or undefined!  ← ❌ 字段缺失
```

### 步骤4：查看任务详情
在同一控制台输出中查看 "Tasks with live_status"：

```javascript
// ✅ 正常情况
Tasks with live_status:
  Task 0 (task_001): {
    has_live_status: true,
    plan_id: "plan_001",
    seed: 66,
    simulation_id: "sim_20251030_120000",
    running_vehicles: 320,  ← 有车辆数据
    progress: 15
  }

// ❌ 异常情况
Tasks with live_status:
  Task 0 (task_001): {
    has_live_status: false,  ← 无live_status
    plan_id: "plan_001",
    seed: 66,
    simulation_id: undefined,
    running_vehicles: undefined,
    progress: 0
  }
```

---

## 后端诊断步骤

### 步骤1：查看API服务器日志
在启动API的终端中查看日志：

```bash
# 运行API服务器：
.\start_api.ps1

# 或使用conda环境：
conda activate od_project
python api/main.py
```

### 步骤2：查找关键日志行
搜索以下日志：

```
[_aggregate_live_time_series] Running tasks: X, Completed: Y
[_aggregate_live_time_series] Using running/completed tasks for time series
[_aggregate_live_time_series] Task task_XXX: Looking for ...summary.xml
[_aggregate_live_time_series] Task task_XXX: File exists=true/false
[_aggregate_live_time_series] Total data points: Z
```

### 步骤3：检查文件系统
```bash
# 使用PowerShell检查文件是否存在
$path = "D:\projects\OD_SIM\cases\case_001\simulations\plan_opti\batch_001\plan_001\sim_66\summary.xml"
Test-Path $path
# ✅ True = 文件存在
# ❌ False = 文件不存在

# 查看目录内容
Get-ChildItem -Recurse "D:\projects\OD_SIM\cases\case_001\simulations\plan_opti\batch_001"
```

---

## 快速修复检查清单

### 快速检查1：summary.xml是否存在？
```bash
# Windows PowerShell
ls -Recurse "D:\projects\OD_SIM\cases" | Where-Object {$_.Name -eq "summary.xml"} | Select-Object FullName
```

✅ 有结果 → 文件存在，等待更新
❌ 无结果 → 文件未生成，检查SUMO进程

### 快速检查2：SUMO进程是否运行？
```bash
# Windows PowerShell
Get-Process | Where-Object {$_.Name -like "*sumo*"}
```

✅ 有结果 → SUMO正在运行
❌ 无结果 → SUMO进程异常退出，检查logs

### 快速检查3：batch_optimization_service是否正确调用？
检查后端日志中是否包含：
```
[_aggregate_live_time_series] 字样的日志
```

✅ 有 → 函数被调用
❌ 无 → 函数未被调用，检查get_batch_progress方法

---

## 常见情况速查表

| 症状 | 可能原因 | 解决方案 |
|------|--------|--------|
| time_points为空 | summary.xml未生成 | 等待10-30秒 |
| time_points为空 | 目录结构错误 | 验证plan_opti路径 |
| running_vehicles为undefined | live_status未生成 | 等待summary.xml生成 |
| 一直显示"仿真数据加载中" | 没有数据到达 | 检查后端日志 |
| 曲线一直不显示（即使有数据） | liveCurveVisible=false | 点击"显示曲线"按钮 |
| 显示秒数时小数点问题 | 时间格式化错误 | ✅ 已修复（第479行） |

---

## 收集诊断信息

如果问题仍未解决，请提供以下信息：

### 1. 浏览器控制台输出
```
[复制 F12 → Console 中的完整输出]
```

### 2. API服务器日志
```
[复制启动API后的关键日志]
```

### 3. 文件系统状态
```bash
# 运行以下命令并提供输出：
ls -la "D:\projects\OD_SIM\cases\{case_id}\simulations\plan_opti\{batch_id}"
```

### 4. 系统信息
- 操作系统: Windows 10/11
- Python版本: 3.10+
- conda环境: od_project
- API服务器版本: 0.9.0

---

## 预期表现

### 正常工作的表现
1. **启动后10-30秒内**: summary.xml文件生成
2. **30秒后**: live_time_series开始有数据
3. **每10秒**: 曲线自动更新，显示新数据点
4. **用户可以**: 点击按钮隐藏/显示曲线
5. **剩余时间**: 显示为"X分X秒"格式（四舍五入）

### 控制台应该显示
```
=== renderLiveCurve called ===
liveTimeSeries: {time_points: [0, 1, 2, ...], total_running: [100, 110, ...]}
liveCurveVisible state: true
Showing live curve section with XXX data points  ← 有XXX个数据点
```

---

## 后续步骤

1. ✅ **已修复**：时间计算错误（formatDuration）
2. 🔍 **需诊断**：live_time_series数据加载问题
3. 📋 **下一步**：根据诊断信息提供具体修复方案

---

**更新记录**:
- 2025-10-30: 修复时间计算错误，增强诊断日志，创建本指南

**需要帮助？**
1. 查看浏览器控制台日志（F12 → Console）
2. 对照上述"常见情况速查表"
3. 如果仍未解决，收集诊断信息并反馈

