# 事件批次仿真 - 两层进度监控测试清单

## 测试环境

- **浏览器**：Chrome/Edge (latest)
- **后端**：Python 3.10+, FastAPI
- **前端**：HTML5, Vanilla JavaScript
- **数据源**：progress.json 文件

---

## 功能测试用例

### TC-001: 监控面板初始化

**前置条件**：
- 系统已启动
- 已创建事件案例（case_event_XXXX）

**测试步骤**：
```
1. 打开场景案例管理页面
2. 选择事件案例复选框
3. 点击 "启动仿真" 按钮
```

**预期结果**：
- ✅ 监控面板出现（#batchMonitoring 显示）
- ✅ 面板默认折叠，显示统计卡片和进度条
- ✅ 统计卡片显示：总计 0, 已完成 0, 运行中 0, 失败 0
- ✅ 进度条显示 0%

**验证点**：
```javascript
// 浏览器控制台验证
document.getElementById('batchMonitoring').style.display !== 'none'  // true
document.getElementById('collapsedContent').style.display !== 'none'  // true
document.getElementById('expandedContent').style.display === 'none'   // true
```

---

### TC-002: 监控面板展开/折叠

**前置条件**：监控面板已显示

**测试步骤**：
```
1. 点击展开按钮（▼ 图标）
```

**预期结果**：
- ✅ 折叠内容隐藏（统计卡片、进度条）
- ✅ 展开内容显示（详细仿真表格）
- ✅ 按钮图标变为 ▶

**验证点**：
```javascript
document.getElementById('collapsedContent').style.display === 'none'    // true
document.getElementById('expandedContent').style.display !== 'none'     // true
document.getElementById('toggleMonitoringBtn').textContent.includes('▶') // true
```

---

### TC-003: 事件级进度实时更新

**前置条件**：
- 监控面板已显示
- 至少有 1 个 simulation 在运行

**测试步骤**：
```
1. 监控面板自动刷新（1秒间隔）
2. 观察进度条变化
3. 等待 simulation 完成
```

**预期结果**：
- ✅ 每 1 秒刷新一次进度
- ✅ 进度条宽度逐步增加
- ✅ 进度百分比正确更新
- ✅ 统计卡片数字更新

**验证计算**：
```javascript
// 公式验证
eventProgress = (completed_simulations / total_simulations) * 100

示例：
- 总 simulation: 6
- 已完成: 2
- 期望进度: (2/6)*100 = 33%
```

**验证点**：
```javascript
// 浏览器控制台
Math.round((2/6)*100)  // 33
```

---

### TC-004: 场景级进度计算

**前置条件**：
- 监控面板展开，显示详细表格
- 至少有 2 个场景

**测试步骤**：
```
1. 点击展开按钮查看详细表格
2. 找到场景行（灰色背景，缩进 40px）
3. 观察场景级进度条
```

**预期结果**：
- ✅ 场景行正确显示（标签格式：├─ scenario_xxx）
- ✅ 背景色为灰色（#f5f5f5）
- ✅ 显示场景统计：总数、进行、完成
- ✅ 进度条正确计算

**验证计算**：
```javascript
// 场景级进度公式
scenarioProgress = (completed_in_scenario / total_in_scenario) * 100

示例 - 场景1：
- Simulation 1.1: status='completed'
- Simulation 1.2: status='running', progress=45%
- Simulation 1.3: status='queued'
- 期望: (1/3)*100 = 33%
- （虽然 1.2 显示 45%，但场景级仍为 33%）
```

---

### TC-005: Simulation 级进度（来自 progress.json）

**前置条件**：
- 表格展开，显示 simulation 行
- 至少有 1 个 simulation 在运行

**测试步骤**：
```
1. 找到 simulation 行（缩进 80px）
2. 观察 progress 列的进度条
3. 检查 progress.json 文件内容
```

**预期结果**：
- ✅ Simulation 行标签格式：└─ sim_xxx
- ✅ 进度条显示 progress.json 中的 percent 值
- ✅ 进度条宽度与百分比匹配

**验证**：
```bash
# 检查 progress.json 文件
cat cases/case_event_10754/simulations/sim_10754_001/progress.json
# 应包含：
# {
#     "status": "running",
#     "percent": 45,
#     ...
# }
```

---

### TC-006: 状态展示

**前置条件**：运行中的批次

**测试步骤**：
```
1. 观察不同状态的 simulation 显示
2. 监控面板持续刷新
3. 等待 simulation 完成或失败
```

**预期结果**：

| 状态 | 显示文本 | 颜色 | 进度条 |
|------|---------|------|--------|
| `running` | 运行中 | 橙色 (#f57c00) | 动态更新 |
| `simulating` | 仿真中 | 橙色 (#f57c00) | 动态更新 |
| `completed` | 已完成 | 绿色 (#388e3c) | 100% |
| `failed` | 失败 | 红色 (#d32f2f) | 保持当前 |
| `queued` | 等待中 | 灰色 (#999) | 0% |

---

### TC-007: 监控自动停止

**前置条件**：
- 批次有多个 simulation
- 都在运行中

**测试步骤**：
```
1. 监控所有 simulation 状态
2. 等待最后一个 simulation 完成
3. 观察监控是否停止
```

**预期结果**：
- ✅ 当所有 simulation 都完成（completed）或失败（failed）时
- ✅ 监控自动停止（`monitoringInterval` 被清除）
- ✅ 最后显示的进度为 100%

**停止条件代码**：
```javascript
if (stats.queued === 0 && stats.in_progress === 0 && stats.total > 0) {
    clearInterval(monitoringInterval);
}
```

---

### TC-008: 手动刷新

**前置条件**：监控面板已显示

**测试步骤**：
```
1. 点击刷新按钮（🔄 图标）
2. 观察数据变化
```

**预期结果**：
- ✅ 立即发送 API 请求
- ✅ 更新统计卡片
- ✅ 更新进度条
- ✅ 更新详细表格

---

### TC-009: 取消批次

**前置条件**：
- 监控面板已显示
- 批次在运行中

**测试步骤**：
```
1. 点击 "取消批次" 按钮
2. 等待响应
3. 观察 UI 状态
```

**预期结果**：
- ✅ 后端 simulation 进程停止
- ✅ 监控面板隐藏
- ✅ 所有 case 状态重置为 "created"
- ✅ sessionStorage 中的批次信息清除
- ✅ 案例复选框取消选中

---

### TC-010: 隔离性验证 - 不影响管控方案监控

**前置条件**：
- 事件批次仿真在运行
- 管控方案系统可访问

**测试步骤**：
```
1. 在新标签页打开管控方案系统
   URL: /control/simulations.html
2. 启动管控方案批次仿真
3. 观察两个系统的监控是否独立
```

**预期结果**：
- ✅ 事件批次监控（绿色主题，case-simulation-center.html）正常工作
- ✅ 管控方案监控（蓝色主题，simulations.html）正常工作
- ✅ 两个系统的进度条独立更新
- ✅ 互不干扰

**验证交叉引用**：
```bash
# 检查是否有交叉引用
grep -r "renderSimulationTable" /frontend/control/
grep -r "renderTaskList" /frontend/scenarios/case-simulation-center.html
# 都应该返回空
```

---

## 数据验证测试

### DV-001: progress.json 数据准确性

**验证方法**：
```bash
# 查看实际的 progress.json 内容
find cases/case_event_*/simulations/*/progress.json -type f | head -1 | xargs cat

# 应显示类似：
{
    "status": "running",
    "percent": 45,
    "message": "已完成 45 步/100 步",
    "updated_at": "2025-11-16T10:30:00.123456",
    "batch_id": "case_event_10754"
}
```

**验证点**：
- ✅ `percent` 值在 0-100 范围内
- ✅ `status` 值是有效的状态（completed, running, failed, queued）
- ✅ 文件定期更新（`updated_at` 时间戳变化）

---

### DV-002: API 响应数据结构

**验证方法**：
```bash
# 调用 API 获取进度数据
curl "http://localhost:8000/api/v1/simulation/simulation_progress/case_event_10754"

# 应返回类似结构：
{
    "case_id": "case_event_10754",
    "simulations": [
        {
            "simulation_id": "sim_10754_001",
            "case_id": "case_event_10754",
            "scenario_id": "scenario_001",
            "status": "running",
            "progress": 45,
            "progress_message": "...",
            "batch_id": "case_event_10754",
            ...
        },
        ...
    ],
    "progress_percentage": 33,
    "stats": {
        "total": 6,
        "completed": 2,
        "in_progress": 3,
        "failed": 0,
        "queued": 1
    }
}
```

**验证点**：
- ✅ `progress` 字段存在且为数字（0-100）
- ✅ `stats` 统计正确：total == completed + in_progress + failed + queued
- ✅ `progress_percentage` 计算正确：(completed/total)*100

---

## 性能测试

### PF-001: 大量 simulation 处理能力

**测试条件**：
- 创建 100+ simulations（多个场景）

**测试步骤**：
```
1. 启动监控
2. 观察浏览器内存使用
3. 检查刷新速度（应在 1 秒内完成）
```

**预期结果**：
- ✅ 内存占用 < 50MB
- ✅ 每次刷新耗时 < 1 秒
- ✅ UI 响应流畅，无卡顿

---

## 浏览器控制台测试

### 推荐的验证脚本

```javascript
// 1. 检查监控面板是否显示
console.log('监控面板显示:', document.getElementById('batchMonitoring').style.display !== 'none');

// 2. 检查当前统计
console.log('总计:', document.getElementById('totalSims').textContent);
console.log('完成:', document.getElementById('completedSims').textContent);
console.log('运行中:', document.getElementById('runningCount').textContent);
console.log('失败:', document.getElementById('failedCount').textContent);

// 3. 检查进度条
const progressBar = document.getElementById('progressBar');
console.log('进度条宽度:', progressBar.style.width);
console.log('进度百分比:', document.getElementById('progressPercent').textContent);

// 4. 检查表格行数
const tableRows = document.querySelectorAll('#simTableBody tr');
console.log('表格行数:', tableRows.length);

// 5. 验证进度计算
const total = parseInt(document.getElementById('totalSims').textContent);
const completed = parseInt(document.getElementById('completedSims').textContent);
const expectedProgress = total > 0 ? Math.round((completed/total)*100) : 0;
console.log('期望进度:', expectedProgress + '%');
console.log('实际进度:', document.getElementById('progressPercent').textContent);
console.log('进度正确:', expectedProgress === parseInt(document.getElementById('progressPercent').textContent));
```

---

## 已知问题和解决方案

### 问题 1: 场景进度为 0% 但有 simulation 在运行

**现象**：Simulation 显示 45%，但场景行显示 0%

**原因**：场景级进度基于 **完成计数**，而非平均进度

**解决**：这是设计行为，无需修改

---

### 问题 2: 刷新间隔太快导致 API 压力

**现象**：后端日志显示频繁的 API 调用

**原因**：默认 1 秒刷新一次

**解决**：可增加刷新间隔
```javascript
// 修改为 2 秒刷新一次
setInterval(refreshBatchStatus, 2000);
```

---

### 问题 3: progress.json 文件不存在

**现象**：Simulation 进度显示为 0%

**原因**：后端未创建 progress.json

**解决**：确保 simulation 启动时创建初始 progress.json 文件

---

## 测试记录

| 用例 | 日期 | 执行者 | 结果 | 备注 |
|------|------|--------|------|------|
| TC-001 | 2025-11-16 | - | ✅ 通过 | 监控面板初始化正常 |
| TC-002 | - | - | - | 待测试 |
| TC-003 | - | - | - | 待测试 |
| TC-004 | - | - | - | 待测试 |
| ... | ... | ... | ... | ... |

---

## 总结

该清单涵盖了事件批次仿真两层进度监控的完整测试用例，可用于：
- ✅ 功能验证
- ✅ 性能测试
- ✅ 集成测试
- ✅ 回归测试
- ✅ 隔离性验证

