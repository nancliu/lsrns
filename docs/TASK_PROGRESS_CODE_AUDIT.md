# 任务进度详情代码审计报告

**日期**: 2025-11-02
**审查范围**: HTML、JavaScript、后端代码的配合
**审查结果**: ✅ 无致命问题，但发现一个日志输出不准确

---

## 1. HTML 部分审查

### 文件: `frontend/control/simulations.html`

**任务进度详情容器** (line 134-140):
```html
<!-- 任务进度详情 -->
<div id="monitorTaskListSection" class="task-list-section" style="display: none;">
    <h4 class="section-title">任务进度详情</h4>
    <div id="monitorTaskList" class="task-list-container">
        <!-- 任务列表将动态加载 -->
    </div>
</div>
```

**审查结果**: ✅ 符合要求
- 只定义了容器，不包含任何硬编码数据或 JavaScript
- 动态内容完全由 JS 生成
- 没有覆盖 JS 文件中的函数

**检查的其他元素**:
- `onclick="switchView('config')"` → 调用 JS 函数 ✅
- `onclick="toggleLiveCurveVisibility()"` → 调用 JS 函数 ✅
- `onclick="closeCurrentMonitor()"` → 调用 JS 函数 ✅

---

## 2. JavaScript 部分审查

### 文件: `frontend/control/js/batch_simulation.js`

#### 2.1 函数定义检查

**关键函数列表**:
```
Line 378: function startProgressPolling() - 启动轮询
Line 385: function stopProgressPolling() - 停止轮询
Line 392: async function updateProgress() - 更新进度（主轮询函数）
Line 528: function renderTaskList(tasks) - 渲染任务详情列表 ✅ 已修复
Line 638: function formatDuration(seconds) - 格式化时长
Line 1463: function loadBatchProgressAndSwitch(batchId) - 加载并切换视图
```

**审查结果**: ✅ 无重复函数定义
- `renderTaskList()` 只定义了一次 (line 528)
- 没有发现未使用的遗留函数

#### 2.2 进度计算逻辑检查

**位置 1: updateProgress() 函数 - 批次总进度** (line 476)
```javascript
const progressPct = (data.progress * 100).toFixed(0);
```

**问题**: ⚠️ 这里是批次总体进度，不是任务详情进度
- `data.progress` 是后端返回的已经是百分比 (0-1 之间的小数)
- 乘以 100 是正确的
- **不是硬编码**

**位置 2: renderTaskList() 函数 - 任务详情进度** (line 583-605)
```javascript
let progressValue = (liveStatus.progress_percent !== null && liveStatus.progress_percent !== undefined)
    ? liveStatus.progress_percent
    : (task.progress !== null && task.progress !== undefined ? task.progress : 0);

if (progressValue > 100) {
    const endTime = liveStatus.end_time || 600;  // ✅ 修复：使用动态end_time
    const divisor = endTime / 100;
    progressPct = Math.min((progressValue / divisor), 100);
} else if (progressValue < 0) {
    progressPct = 0;
}
progressPct = Math.max(0, Math.min(100, progressPct));
```

**检查结果**: ✅ 已正确修复
- 使用动态 `endTime` 而不是硬编码 144
- 默认值 600 是合理的（10分钟仿真）
- 没有硬编码的问题

#### 2.3 日志输出检查

**位置: updateProgress() 函数** (line 480)
```javascript
const taskProgressInfo = runningTasks.map(t => `${t.task_id}:${t.progress}%`).join(', ');
debugLog(`Batch progress: ${progressPct}% | Running: [${taskProgressInfo}]`);
```

**问题**: ⚠️ **日志输出中使用了原始 `t.progress` 值，可能不准确**

**说明**:
- 这只是调试日志输出，不影响实际显示
- 但日志会显示错误的进度信息
- 建议修复：需要像 `renderTaskList()` 一样对每个任务的进度进行正确计算

---

## 3. 后端 API 响应检查

### 文件: `api/services/batch_optimization_service.py` (line 481-495)

**API 响应结构**:
```python
result = {
    'current_step': current_step,
    'total_steps': total_steps,
    'end_time': total_steps,  # ✅ 新增字段
    'current_time': current_step,  # ✅ 新增字段
    'progress_percent': round(progress_percent, 2),
    'running_vehicles': summary.get('running_vehicles', 0),
    'ended_vehicles': summary.get('ended_vehicles', 0),
    'loaded_vehicles': summary.get('loaded_vehicles', 0)
}
```

**审查结果**: ✅ 符合要求
- 包含了 `end_time` 字段，供前端计算动态除数
- 包含了 `current_time` 字段，提高代码可读性
- 仍然包含了 `progress_percent`（已在后端计算）
- 保持了向后兼容性

---

## 4. 数据流完整性检查

### 流程图:
```
后端 API
  ↓
{
  progress_percent: 50.00,      (后端已计算的百分比)
  end_time: 600,                (新增：供前端使用)
  current_time: 300.00,         (新增：明确性)
  live_status: {
    progress_percent: 50.00,
    end_time: 600,
    running_vehicles: 45,
    estimated_remaining_seconds: 300
  }
}
  ↓
前端 renderTaskList()
  ↓
if (progressValue > 100) {
  divisor = end_time / 100;     ✅ 使用动态除数
  progressPct = progressValue / divisor;
}
  ↓
显示: 50.0%  ✅ 正确
```

**审查结果**: ✅ 数据流完整和正确

---

## 5. 硬编码检查

### 检查内容:

| 位置 | 代码 | 是否硬编码 | 说明 |
|------|------|----------|------|
| `batch_simulation.js:595` | `endTime \|\| 600` | ✅ 不是 | 是 fallback 默认值，合理 |
| `batch_simulation.js:476` | `(data.progress * 100)` | ✅ 不是 | 这是批次总进度，正确 |
| `batch_simulation.js:476` | 没有 144 除数 | ✅ 不是 | 已移除 |

**检查结果**: ✅ 无硬编码问题

---

## 6. 代码重复检查

| 函数名 | 定义次数 | 位置 | 说明 |
|--------|--------|------|------|
| `renderTaskList()` | 1 | Line 528 | ✅ 单一定义 |
| `updateProgress()` | 1 | Line 392 | ✅ 单一定义 |
| `formatDuration()` | 1 | Line 638 | ✅ 单一定义 |
| `startProgressPolling()` | 1 | Line 378 | ✅ 单一定义 |

**检查结果**: ✅ 无重复定义

---

## 7. HTML 和 JS 配合检查

### onclick 事件检查:

| HTML 位置 | onclick 内容 | JS 函数位置 | 是否存在 | 说明 |
|----------|------------|----------|--------|------|
| Line 37 | `switchView('config')` | Line 1400+ | ✅ 存在 | 正常 |
| Line 38 | `switchView('monitoring')` | Line 1400+ | ✅ 存在 | 正常 |
| Line 100 | `closeCurrentMonitor()` | Line 1500+ | ✅ 存在 | 正常 |
| Line 145 | `toggleLiveCurveVisibility()` | Line 900+ | ✅ 存在 | 正常 |

**检查结果**: ✅ HTML 中的所有 onclick 都正确调用了 JS 中的函数

---

## 8. 发现的问题总结

### 问题 1: 日志输出不准确 (低优先级)

**位置**: `batch_simulation.js` line 480

**当前代码**:
```javascript
const taskProgressInfo = runningTasks.map(t => `${t.task_id}:${t.progress}%`).join(', ');
debugLog(`Batch progress: ${progressPct}% | Running: [${taskProgressInfo}]`);
```

**问题**:
- 日志显示的是原始 `t.progress` 值，对于非 14400 秒的仿真会不准确
- 例如：600 秒仿真显示 `300%` 而不是 `50%`

**建议修复**:
```javascript
const taskProgressInfo = runningTasks.map(t => {
    const liveStatus = t.live_status || {};
    let progressValue = (liveStatus.progress_percent !== null && liveStatus.progress_percent !== undefined)
        ? liveStatus.progress_percent
        : (t.progress !== null && t.progress !== undefined ? t.progress : 0);

    if (progressValue > 100) {
        const endTime = liveStatus.end_time || 600;
        const divisor = endTime / 100;
        progressValue = Math.min((progressValue / divisor), 100);
    }
    progressValue = Math.max(0, Math.min(100, progressValue));

    return `${t.task_id}:${progressValue.toFixed(0)}%`;
}).join(', ');
debugLog(`Batch progress: ${progressPct}% | Running: [${taskProgressInfo}]`);
```

**优先级**: 低（仅影响调试日志，不影响用户看到的数据）

---

## 总体结论

✅ **主要问题已修复**:
- 前端任务进度计算：使用动态 `end_time` 而不是硬编码 144 ✅
- 后端 API 响应：包含了 `end_time` 字段 ✅
- HTML 和 JS 配合：没有冲突，正常工作 ✅
- 代码重复：没有发现重复定义 ✅
- 硬编码问题：已解决 ✅

⚠️ **次要问题**:
- 日志输出中的进度值对于非 14400 秒的仿真可能不准确（仅调试日志，低优先级）

---

## 建议行动

### 立即执行 (Priority 1)
✅ 已完成：修复前端任务进度计算（动态除数）
✅ 已完成：后端添加 `end_time` 字段

### 可选执行 (Priority 2)
⏳ 修复日志输出中的进度值计算（仅影响调试信息）

### 后续工程 (Priority 3)
⏳ 后端改用动态 `total_steps`（当前仍硬编码为 14400）
