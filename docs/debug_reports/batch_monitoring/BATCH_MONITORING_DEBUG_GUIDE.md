# 批量仿真实时监控诊断指南

## 问题描述

批量仿真进度页面UI已更新，但以下内容未显示：
1. **车辆数** (`running_vehicles`) - 任务列表中运行中任务的在网车辆数
2. **动态曲线** (`live_time_series`) - 实时在网车辆数曲线图

## 已完成的修改

### 1. 前端调试日志增强 (`frontend/control/js/batch_simulation.js`)

在 `updateProgress()` 函数中添加了详细的调试日志：
- 检查API返回的 `live_time_series` 是否存在
- 检查每个运行中任务的 `live_status` 是否存在
- 检查 `running_vehicles` 字段是否有值

在 `renderLiveCurve()` 函数中添加了调试日志：
- 追踪曲线渲染调用
- 显示时序数据点数量

### 2. 后端调试日志增强 (`api/services/batch_optimization_service.py`)

在 `_get_simulation_live_status()` 方法中添加了日志：
- 检查 `simulation_id` 是否已分配
- 检查 `summary.xml` 文件是否存在
- 显示提取的最后一步数据

### 3. 诊断脚本 (`debug_batch_progress.py`)

创建了一个命令行诊断工具，用于：
- 检查API响应的数据结构
- 验证 `live_status` 和 `live_time_series` 是否存在
- 检查 `summary.xml` 文件是否生成
- 输出完整的API响应JSON

## 诊断步骤

### 步骤1：重启API服务器

确保后端代码更新已生效：

```powershell
# 停止现有API服务器（如果正在运行）
# 按 Ctrl+C 停止

# 重新启动API服务器
.\start_api.ps1
```

### 步骤2：启动批量仿真

1. 打开浏览器访问 `http://localhost:8000/control/simulations.html`
2. 创建并启动一个批量仿真批次
3. 等待至少1-2个任务开始运行（状态变为 `running`）

### 步骤3：检查浏览器控制台

打开浏览器开发者工具（F12），查看Console标签：

```
=== API Progress Response ===
Status: running
Running tasks count: 2
Has live_time_series: true/false
  - time_points length: X
  - total_running length: X
Tasks with live_status:
  Task 0 (task_001):
    has_live_status: true/false
    running_vehicles: XXX / undefined
    simulation_id: sim_xxx
```

**关键检查点**：
- `Has live_time_series` 应该为 `true`
- `time_points length` 应该 > 0
- 每个运行中任务的 `has_live_status` 应该为 `true`
- `running_vehicles` 应该有数值，不应该是 `undefined`

### 步骤4：运行诊断脚本

```bash
# 激活conda环境
conda activate od_project

# 运行诊断脚本
python debug_batch_progress.py <case_id> <batch_id>

# 示例
python debug_batch_progress.py case_20251015_baseline batch_20251029_143000
```

诊断脚本会输出：
1. API响应状态
2. `live_time_series` 数据结构
3. 每个运行中任务的 `live_status`
4. `summary.xml` 文件是否存在
5. 完整的API响应JSON

### 步骤5：检查API服务器日志

查看API服务器的终端输出，寻找类似以下的日志：

```
DEBUG: Task task_001 has no simulation_id yet
DEBUG: Looking for summary.xml at: D:\projects\OD_SIM\cases\...\summary.xml
DEBUG: File exists: True/False
DEBUG: Failed to extract last step from ...
DEBUG: Extracted last_step: {'time': 1234, 'running': 567, ...}
```

## 常见问题诊断

### 问题1：`live_time_series` 为空或不存在

**可能原因**：
- 没有任务处于 `running` 状态
- `summary.xml` 文件尚未生成
- `_extract_summary_time_series()` 解析失败

**解决方法**：
1. 确认至少有1个任务状态为 `running`
2. 检查 `cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/summary.xml` 是否存在
3. 查看API服务器日志中的警告信息

### 问题2：`live_status` 不存在或 `running_vehicles` 为 undefined

**可能原因**：
- 任务没有 `simulation_id`（尚未分配或仿真未启动）
- `_extract_summary_last_step()` 返回 `None`（文件不存在或解析失败）
- API服务器未重启，仍在运行旧代码

**解决方法**：
1. 检查任务的 `simulation_id` 字段是否有值
2. 确认 `summary.xml` 文件存在且大小 > 0
3. **重启API服务器**
4. 运行诊断脚本验证文件路径

### 问题3：`summary.xml` 文件不存在

**可能原因**：
- 仿真尚未开始生成输出（SUMO刚启动）
- 目录结构不正确
- 批量仿真调度器未正确创建目录

**解决方法**：
1. 等待10-30秒，让SUMO生成初始输出
2. 手动检查目录结构：
   ```
   cases/
   └── {case_id}/
       └── simulations/
           └── plan_opti/
               └── {batch_id}/
                   └── {plan_id}/
                       └── sim_{seed}/
                           └── summary.xml
   ```
3. 检查批量仿真调度器日志，确认任务是否真正启动

### 问题4：浏览器控制台有JavaScript错误

**可能原因**：
- Chart.js未正确加载
- DOM元素不存在
- 数据格式不匹配

**解决方法**：
1. 检查浏览器控制台的红色错误信息
2. 确认 `liveCurveSection` 和 `liveCurveChart` 元素存在
3. 清除浏览器缓存并刷新页面

## 预期行为

### 正常工作时的现象

1. **浏览器控制台**：
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

2. **前端UI**：
   - 任务列表中运行中任务显示：`在网: XXX辆`
   - 页面下方显示 "实时在网车辆数" 曲线图
   - 曲线图实时更新（每10秒刷新）

3. **API响应**：
   ```json
   {
     "status": "running",
     "live_time_series": {
       "time_points": [0, 1, 2, ...],
       "total_running": [320, 350, ...],
       "task_count": 2
     },
     "tasks": [
       {
         "task_id": "task_001",
         "status": "running",
         "simulation_id": "sim_001",
         "live_status": {
           "running_vehicles": 456,
           "current_step": 1234,
           "progress_percent": 8.6
         }
       }
     ]
   }
   ```

## 下一步

根据诊断结果：

1. **如果API响应正确但前端不显示** → 检查JavaScript错误和DOM元素
2. **如果API响应缺少字段** → 检查后端日志和summary.xml文件
3. **如果summary.xml不存在** → 检查目录结构和批量仿真调度器
4. **如果问题仍然存在** → 提供诊断脚本输出和浏览器控制台截图

## 联系与反馈

如果按照此指南仍无法解决问题，请提供：
1. 诊断脚本的完整输出
2. 浏览器控制台的截图
3. API服务器终端的日志输出
4. `cases/{case_id}/simulations/plan_opti/` 目录结构截图
