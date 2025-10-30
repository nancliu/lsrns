# 批量仿真实时监控调试 - 下一步操作指南

## 📋 问题概述

您报告的问题：
- ✅ 批次进度UI已更新（任务统计卡片、预计完成时间）
- ❌ 车辆数(`running_vehicles`)未显示在任务列表中
- ❌ 动态曲线(`live_time_series`)未显示在页面下方

## 🔧 已完成的工作

### 1. 前端调试日志增强

**文件**: `frontend/control/js/batch_simulation.js`

在 `updateProgress()` 函数中添加了详细日志：
```javascript
=== API Progress Response ===
Status: running
Running tasks count: 2
Has live_time_series: true/false
Tasks with live_status:
  Task 0 (task_001):
    has_live_status: true/false
    running_vehicles: XXX / undefined
```

在 `renderLiveCurve()` 函数中添加了追踪日志：
```javascript
=== renderLiveCurve called ===
liveTimeSeries: {...}
Showing/hiding live curve chart
```

### 2. 后端调试日志增强

**文件**: `api/services/batch_optimization_service.py`

在 `_get_simulation_live_status()` 方法中添加了日志：
- 记录 `simulation_id` 是否已分配
- 记录 `summary.xml` 文件路径和存在性
- 记录提取的最后一步数据

### 3. 诊断工具

**文件**: `debug_batch_progress.py`

命令行诊断脚本，可以：
- 检查API响应的数据结构
- 验证 `live_status` 和 `live_time_series` 是否存在
- 检查 `summary.xml` 文件是否生成
- 输出完整的JSON响应

### 4. 诊断指南

**文件**: `BATCH_MONITORING_DEBUG_GUIDE.md`

详细的故障排除文档，包含：
- 5种常见根因分析
- 数据流追踪图
- 完整的诊断步骤
- 预期行为示例

### 5. OpenSpec文档更新

- `design.md`: 添加了第12节"调试与故障排除"
- `tasks.md`: 添加了M1.5里程碑"实时监控调试与诊断"

## 🚀 接下来您需要做什么

### 步骤1：重启API服务器（重要！）

确保后端代码更新已生效：

```powershell
# 停止现有API服务器（按 Ctrl+C）

# 重新启动
.\start_api.ps1
```

### 步骤2：启动批量仿真

1. 打开浏览器访问 `http://localhost:8000/control/simulations.html`
2. 创建并启动一个批量仿真批次
3. 等待至少1-2个任务开始运行（状态变为 `running`）
4. **等待至少30秒**，让SUMO生成 `summary.xml` 文件

### 步骤3：检查浏览器控制台（关键！）

打开浏览器开发者工具（按 F12），查看 Console 标签页：

**重点检查**：
- `Has live_time_series` 是否为 `true`？
- `time_points length` 是否大于 0？
- 每个运行中任务的 `has_live_status` 是否为 `true`？
- `running_vehicles` 是否有数值（不是 `undefined`）？

**请将控制台输出截图或复制文本发给我！**

### 步骤4：运行诊断脚本

```bash
# 激活conda环境
conda activate od_project

# 运行诊断脚本（替换为您的实际case_id和batch_id）
python debug_batch_progress.py <your_case_id> <your_batch_id>

# 示例
python debug_batch_progress.py case_20251015_baseline batch_20251029_143000
```

**请将诊断脚本的完整输出发给我！**

### 步骤5：（可选）检查文件系统

手动检查 `summary.xml` 是否存在：

```powershell
# 替换为您的实际路径
ls "D:\projects\OD_SIM\cases\{case_id}\simulations\plan_opti\{batch_id}\{plan_id}\sim_{seed}\summary.xml"
```

## 🔍 快速诊断清单

| 检查项 | 期望结果 | 如果失败 |
|--------|---------|---------|
| API服务器已重启 | ✅ | 重启并等待30秒 |
| 至少1个任务为running状态 | ✅ | 等待任务启动 |
| 浏览器控制台有调试日志 | ✅ | 刷新页面（Ctrl+F5） |
| `Has live_time_series: true` | ✅ | 查看API日志 |
| `has_live_status: true` | ✅ | 检查summary.xml |
| `running_vehicles` 有数值 | ✅ | 等待30秒后重试 |

## 📊 预期的正常行为

### 浏览器控制台应显示：

```
=== API Progress Response ===
Status: running
Running tasks count: 2
Has live_time_series: true
  - time_points length: 150
  - total_running length: 150
Tasks with live_status:
  Task 0 (task_001):
    has_live_status: true
    running_vehicles: 456
    simulation_id: sim_001

=== renderLiveCurve called ===
liveTimeSeries: {time_points: Array(150), total_running: Array(150), ...}
Showing live curve chart with 150 data points
```

### 前端UI应显示：

1. **任务列表中**：
   - 运行中任务显示进度条
   - 显示 `在网: XXX辆`
   - 显示 `剩余: X分钟`

2. **页面下方**：
   - 显示 "实时在网车辆数" 标题
   - 显示折线图，X轴为时间，Y轴为车辆数
   - 图表每10秒自动更新

## ❓ 如果问题仍然存在

请提供以下信息：

1. **浏览器控制台输出**（截图或文本）
2. **诊断脚本输出**（完整文本）
3. **API服务器终端日志**（最近50行）
4. **回答以下问题**：
   - API服务器是否已重启？
   - 是否有任务处于running状态？
   - 等待了多长时间（是否超过30秒）？
   - summary.xml文件是否存在？

## 📝 相关文档

- **详细诊断指南**: `BATCH_MONITORING_DEBUG_GUIDE.md`
- **设计文档**: `openspec/changes/enhance-batch-simulation-monitoring/design.md`（第12节）
- **任务清单**: `openspec/changes/enhance-batch-simulation-monitoring/tasks.md`（M1.5里程碑）

---

**重要提示**：90%的情况下，问题是因为API服务器未重启或SUMO刚启动summary.xml尚未生成。请先确保这两点！
