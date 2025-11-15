# Task 2.6: 显示新旧Case区别 - 解释说明

**Date**: 2025-11-14

---

## 问题：显示新旧case的区别是指什么？

### 背景：Event-Based架构的核心特性

Event-Based Case Architecture的核心创新是**case复用**：

```
同一个事件的多个策略场景 → 共享1个case
```

**示例**：
```
Event 10754（交通事故）有3个策略场景：
├── scenario_10754_no_control  → 第1次创建 → 创建 case_event_10754 ✅ 新case
├── scenario_10754_tec         → 第2次创建 → 复用 case_event_10754 ♻️  旧case
└── scenario_10754_vss         → 第3次创建 → 复用 case_event_10754 ♻️  旧case
```

---

## "新旧case区别"的含义

### 新Case (is_new_case = True)

**定义**：第一次为某个event创建case

**特征**：
- ✅ 创建全新的 `case_event_{event_id}` 目录
- ✅ 生成完整的config文件（network, TAZ, edgeData）
- ✅ **触发OD数据生成**（耗时2-5分钟）
- ✅ 状态：`od_generating`

**用户体验**：
```
用户点击"创建" scenario_10754_tec
→ 系统显示："正在创建新案例 case_event_10754"
→ 系统显示："OD数据生成中，预计需要3-5分钟..."
→ 用户需要等待OD生成完成才能启动仿真
```

---

### 旧Case (is_new_case = False)

**定义**：复用已存在的event case

**特征**：
- ✅ 找到已存在的 `case_event_{event_id}` 目录
- ✅ **复用现有config文件**（不重新生成）
- ✅ **跳过OD数据生成**（已有数据）
- ✅ 状态：`ready`
- ✅ 只创建新的simulation目录

**用户体验**：
```
用户点击"创建" scenario_10754_vss（event 10754的第2个场景）
→ 系统显示："复用已有案例 case_event_10754"
→ 系统显示："配置文件已存在，跳过OD生成"
→ 系统显示："仿真已就绪，可以立即启动"
→ 用户可以立即启动仿真（无需等待）
```

---

## 为什么要做这个区分？

### 1. **用户体验改进** ✅

#### 问题（没有区分时）：
```
用户创建第2个场景
→ 没有任何提示说这是复用已有case
→ 用户不知道为什么没有OD生成进度
→ 用户困惑："是不是出错了？"
```

#### 解决（有区分时）：
```
用户创建第2个场景
→ 明确提示："复用已有案例 case_event_10754"
→ 说明："配置文件已存在，跳过OD生成"
→ 用户理解："原来是复用，所以很快"
```

---

### 2. **透明度和可预测性** ✅

#### 用户需要知道：

**创建新case时**：
- ⏳ 需要等待多久？（OD生成时间）
- 📊 系统在做什么？（生成OD数据）
- ⚠️  什么时候可以仿真？（等OD完成）

**复用旧case时**：
- ✅ 为什么这么快？（跳过OD生成）
- ♻️  是否使用正确的数据？（复用同一event的配置）
- 🚀 可以立即启动吗？（是的）

---

### 3. **性能提升的可见化** ✅

Event-Based架构的主要优势之一是**性能提升**：

| 指标 | 传统方式 | Event-Based | 提升 |
|-----|---------|-------------|------|
| OD生成时间 | 8分钟（4个场景×2分钟） | 2分钟（只生成1次） | **75%** ⬆️ |
| 磁盘占用 | 2000 MB | 600 MB | **70%** ⬇️ |

**但用户看不到这个提升，除非我们告诉他们！**

#### 没有提示时：
```
用户："为什么第2个场景创建这么快？是不是少做了什么？"
```

#### 有提示时：
```
系统："复用已有案例，跳过OD生成"
用户："哦，原来是复用配置，所以快！设计得真好！"
```

---

### 4. **状态同步和轮询** ✅

前端需要根据case状态决定UI行为：

**新case**：
```javascript
if (data.is_new_case && data.od_generation_status === 'in_progress') {
    // 显示进度条
    showProgressBar("OD数据生成中...");

    // 启动轮询检查OD生成完成
    pollODGenerationStatus(data.case_id);

    // 禁用"启动仿真"按钮
    disableSimulationButton("等待OD生成完成");
}
```

**旧case**：
```javascript
if (!data.is_new_case) {
    // 无需进度条

    // 无需轮询

    // 立即启用"启动仿真"按钮
    enableSimulationButton("就绪");
}
```

---

## Task 2.6 的具体实现

### 前端显示改进

**Location**: `frontend/scenarios/scenario_browser.js`

#### 当前问题：
```javascript
// 现在：没有区分新旧case
async function submitCreateCaseWithSimulation() {
    const response = await fetch('/api/v1/scenario/create_case_with_simulation', {...});
    const data = await response.json();

    // ❌ 只显示通用成功消息
    showNotification('案例创建成功', 'success');
}
```

#### 改进后：
```javascript
async function submitCreateCaseWithSimulation() {
    const response = await fetch('/api/v1/scenario/create_case_with_simulation', {...});
    const data = await response.json();

    // ✅ 根据is_new_case区分显示
    if (data.is_new_case) {
        // 新case
        showNotification(`✅ 创建新案例: ${data.case_id}`, 'success');

        if (data.od_generation_status === 'in_progress') {
            showNotification('⏳ OD数据生成中，预计需要3-5分钟...', 'info');
            showProgressIndicator(data.case_id);

            // 开始轮询OD生成状态
            startODGenerationPolling(data.case_id);
        }
    } else {
        // 旧case (复用)
        showNotification(`✅ 复用已有案例: ${data.case_id}`, 'success');
        showNotification('💡 配置文件已存在，跳过OD生成', 'info');
        showNotification('🚀 仿真已就绪，可以立即启动', 'success');
    }

    // 显示simulation创建信息
    showNotification(`✅ 仿真已创建: ${data.simulation_id}`, 'success');

    // 刷新场景列表
    refreshScenarioList();
}
```

---

## 用户场景对比

### 场景1：创建第1个场景（新case）

**操作流程**：
```
1. 用户点击 scenario_10754_tec 的"创建"按钮
2. 前端显示：
   ┌──────────────────────────────────────────┐
   │ ✅ 创建新案例: case_event_10754          │
   │ ⏳ OD数据生成中，预计需要3-5分钟...       │
   │ 📊 进度: ████░░░░░░ 40%                  │
   └──────────────────────────────────────────┘
3. 5分钟后，OD生成完成
4. 前端更新：
   ┌──────────────────────────────────────────┐
   │ ✅ OD数据生成完成                        │
   │ ✅ 仿真已创建: event_simulation_...     │
   │ 🚀 可以启动仿真                          │
   └──────────────────────────────────────────┘
```

---

### 场景2：创建第2个场景（旧case）

**操作流程**：
```
1. 用户点击 scenario_10754_vss 的"创建"按钮
2. 前端显示（立即）：
   ┌──────────────────────────────────────────┐
   │ ✅ 复用已有案例: case_event_10754        │
   │ 💡 配置文件已存在，跳过OD生成             │
   │ ✅ 仿真已创建: event_simulation_...     │
   │ 🚀 仿真已就绪，可以立即启动               │
   └──────────────────────────────────────────┘
3. 无需等待，可以立即启动仿真
```

**对比**：
- 场景1：需要等待5分钟，有进度条
- 场景2：立即完成，无需等待

**如果没有Task 2.6的改进，用户体验**：
```
场景1 和 场景2 的显示完全相同
→ 用户困惑："为什么场景2这么快？"
→ 用户担心："是不是出错了？"
```

---

## 技术细节

### API响应字段（已实现）

```python
# api/services/case_service.py:1378-1393
return {
    "success": True,
    "case_id": "case_event_10754",
    "case_type": "event_based",
    "simulation_id": "event_simulation_scenario_10754_vss",
    "simulation_path": "...",

    # ✅ 关键字段：区分新旧case
    "is_new_case": False,  # True=新创建，False=复用

    # ✅ 关键字段：OD生成状态
    "od_generation_status": "completed",  # "in_progress"/"completed"

    "case_status": "ready",  # "od_generating"/"ready"
    "simulation_status": "ready",
    "message": "Simulation added to existing case"
}
```

### 前端需要处理的字段

| 字段 | 用途 |
|-----|------|
| `is_new_case` | 判断是否显示"新建"或"复用"消息 |
| `od_generation_status` | 判断是否显示进度条和轮询 |
| `case_status` | 更新场景列表中的状态显示 |
| `message` | 补充说明信息 |

---

## 为什么这是P0优先级？

### 优先级分析

| 任务 | 优先级 | 原因 |
|-----|--------|------|
| Task 2.5 (Concurrent) | P1 (中) | 边缘情况，不太可能发生 |
| **Task 2.6 (Frontend)** | **P0 (高)** | **直接影响用户体验** |

### 理由：

1. **用户困惑** ⚠️
   - 没有明确提示，用户不理解为什么第2个场景创建这么快
   - 可能误以为系统出错或跳过了某些步骤

2. **功能不完整** ⚠️
   - 后端已实现case复用，但前端没有相应的UI反馈
   - 核心功能的价值（性能提升）无法被用户感知

3. **状态同步** ⚠️
   - OD生成状态无法实时反馈给用户
   - 用户不知道什么时候可以启动仿真

4. **可用性** ⚠️
   - 新case需要等待，但没有进度指示
   - 旧case可以立即使用，但没有告知用户

---

## 总结

### "显示新旧case的区别"是指：

**新case (第1次创建)**：
- 提示："创建新案例"
- 显示："OD数据生成中..."
- 显示进度条
- 禁用仿真按钮直到完成

**旧case (复用已有)**：
- 提示："复用已有案例"
- 说明："配置文件已存在，跳过OD生成"
- 提示："可以立即启动"
- 立即启用仿真按钮

---

### 为什么要做：

1. ✅ **提升用户体验** - 清晰的状态反馈
2. ✅ **减少困惑** - 解释为什么有些创建很快
3. ✅ **可见化优势** - 让用户感知到性能提升
4. ✅ **正确的UI行为** - 根据状态启用/禁用按钮
5. ✅ **完整的功能** - 后端实现需要前端配合

---

**Status**: 📝 Explanation Complete
**Priority**: P0 (High)
**Impact**: User Experience & Feature Completeness
