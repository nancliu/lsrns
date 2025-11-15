# 场景浏览器多事件批量创建设计（改进版）

**Date**: 2025-11-15
**Goal**: 支持多事件选择 + 保证每个事件的场景完整性

---

## 核心设计原则

### 原则1：每个事件必须包含所有场景
**理由**：避免edgeData不一致，简化实现

### 原则2：支持同时创建多个事件
**理由**：提高批量操作效率

### 原则3：提供灵活性，但有明确约束
**理由**：平衡易用性和复杂度

---

## 改进方案：两级选择模式

### UI设计

```
┌─────────────────────────────────────────────────────────────┐
│ 🎯 批量创建事件案例                                         │
│                                                             │
│ 选择要创建的事件: [全选事件] [取消全选]                     │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☑ Event 7180720 - 交通事故                             │ │
│ │   📍 成温邛高速 K23+500                                │ │
│ │   🕐 2025-06-13 15:22:37 ~ 16:49:16                   │ │
│ │                                                         │ │
│ │   包含场景: ⚪无控制 🚦VSS 🛂TEC 🛣️DHS  [展开详情 ▼]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☑ Event 8260655 - 交通阻塞                             │ │
│ │   📍 成温邛高速 K18+200                                │ │
│ │   🕐 2025-06-15 09:15:00 ~ 10:45:00                   │ │
│ │                                                         │ │
│ │   包含场景: ⚪无控制 🚦VSS 🛂TEC 🛣️DHS                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☐ Event 9030655 - 恶劣天气                             │ │
│ │   包含场景: ⚪无控制 🚦VSS                             │ │
│ │   ⚠️ 缺少策略: TEC, DHS                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 📊 已选: 2个事件, 8个场景 (平均4个场景/事件)                │
│ ⏱️ 预计: 约6分钟 (OD生成 + 场景配置)                        │
│                                                             │
│ [批量创建所有选中事件] [高级选项▼]                          │
└─────────────────────────────────────────────────────────────┘
```

### 展开详情后（可选）

```
┌─────────────────────────────────────────────────────────┐
│ ☑ Event 7180720 - 交通事故                     [收起 ▲] │
│   📍 成温邛高速 K23+500                                │
│   🕐 2025-06-13 15:22:37 ~ 16:49:16                   │
│                                                         │
│   创建策略（建议全选以保证数据一致性）:                  │
│   ☑ ⚪ 无控制 (基线)          状态: 未创建             │
│   ☑ 🚦 VSS - 可变限速         状态: 未创建             │
│   ☑ 🛂 TEC - 收费站管控       状态: 未创建             │
│   ☑ 🛣️ DHS - 动态硬路肩       状态: 未创建             │
│                                                         │
│   ⚠️ 提示: 取消某些策略可能导致后续无法添加              │
│   建议: 先创建所有策略，后续可选择性运行仿真              │
└─────────────────────────────────────────────────────────┘
```

---

## 设计策略

### 策略A：强制全选所有场景（最简单）⭐ 推荐

**规则**：
- 事件级复选框：选中事件 = 自动选中该事件的所有场景
- 不允许单独取消某个策略
- 如果事件缺少某些策略，显示警告但允许创建

**实现**：
```javascript
function selectEvent(eventId, checked) {
    const eventCard = document.getElementById(`event-${eventId}`);
    const eventCheckbox = eventCard.querySelector('.event-checkbox');

    // 事件复选框状态改变时，自动选中/取消所有场景
    eventCheckbox.checked = checked;

    // 不显示场景级别的复选框，直接全选
    // 用户只能选择事件，不能选择单个场景
}

// 批量创建
async function batchCreateMultipleEvents() {
    const selectedEvents = getSelectedEvents(); // 获取选中的事件

    // 每个事件包含所有可用场景
    for (const event of selectedEvents) {
        await createEventCaseBatch(event.event_id, event.all_scenarios);
    }
}
```

**优点**：
- ✅ 最简单，用户无需考虑场景选择
- ✅ 保证edgeData完整性
- ✅ 避免增量更新问题

**缺点**：
- ❌ 缺乏灵活性
- ❌ 如果用户只想要基线，也必须创建所有策略

---

### 策略B：默认全选 + 允许部分选择（有警告）⭐ 平衡方案

**规则**：
1. 默认全选所有场景
2. 允许用户取消某些场景
3. 如果取消了场景，显示明确警告
4. 提供"只创建基线"快捷按钮

**实现**：
```javascript
function renderEventCard(event) {
    const scenarios = event.scenarios;
    const allStrategies = ['no_control', 'vss', 'tec', 'dhs'];

    return `
        <div class="event-card">
            <div class="event-header">
                <input type="checkbox" class="event-checkbox"
                       data-event-id="${event.event_id}"
                       onchange="toggleEventSelection('${event.event_id}')"
                       checked>
                <h3>Event ${event.event_id}</h3>

                <!-- 快捷操作 -->
                <div class="quick-actions">
                    <button onclick="selectPreset('${event.event_id}', 'all')">
                        全部策略
                    </button>
                    <button onclick="selectPreset('${event.event_id}', 'baseline')">
                        仅基线
                    </button>
                </div>
            </div>

            <div class="scenario-selection">
                ${allStrategies.map(strategy => {
                    const scenario = scenarios.find(s => s.strategy === strategy);
                    const available = !!scenario;

                    return `
                        <label class="scenario-item ${!available ? 'unavailable' : ''}">
                            <input type="checkbox"
                                   class="scenario-checkbox"
                                   data-event-id="${event.event_id}"
                                   data-strategy="${strategy}"
                                   ${available ? 'checked' : 'disabled'}
                                   onchange="validateScenarioSelection('${event.event_id}')">
                            ${getStrategyIcon(strategy)} ${getStrategyDisplay(strategy)}
                            ${!available ? '<span class="badge-warn">不可用</span>' : ''}
                        </label>
                    `;
                }).join('')}
            </div>

            <!-- 警告提示 -->
            <div class="warning-box" id="warning-${event.event_id}" style="display:none;">
                ⚠️ 警告: 未选择全部场景将导致edgeData不完整，后续无法添加缺失的策略。
                建议选择所有可用策略以保证数据一致性。
            </div>
        </div>
    `;
}

// 验证场景选择
function validateScenarioSelection(eventId) {
    const allCheckboxes = document.querySelectorAll(
        `.scenario-checkbox[data-event-id="${eventId}"]:not(:disabled)`
    );
    const checkedCheckboxes = document.querySelectorAll(
        `.scenario-checkbox[data-event-id="${eventId}"]:checked`
    );

    const warningBox = document.getElementById(`warning-${eventId}`);

    if (checkedCheckboxes.length < allCheckboxes.length) {
        // 未全选，显示警告
        warningBox.style.display = 'block';
    } else {
        warningBox.style.display = 'none';
    }
}

// 预设选择
function selectPreset(eventId, preset) {
    const checkboxes = document.querySelectorAll(
        `.scenario-checkbox[data-event-id="${eventId}"]:not(:disabled)`
    );

    checkboxes.forEach(cb => {
        const strategy = cb.dataset.strategy;

        if (preset === 'all') {
            cb.checked = true;
        } else if (preset === 'baseline') {
            cb.checked = (strategy === 'no_control');
        }
    });

    validateScenarioSelection(eventId);
}
```

**优点**：
- ✅ 灵活性高，用户可以选择
- ✅ 明确警告，用户知道后果
- ✅ 提供快捷预设（全部/仅基线）

**缺点**：
- ⚠️ 仍可能导致不完整案例
- ⚠️ 需要用户理解警告含义

---

### 策略C：允许部分选择 + 支持后续补充（最复杂）

**规则**：
1. 允许任意选择场景
2. 后续可以添加缺失的场景
3. 添加时自动更新edgeData（增量更新）
4. 标记旧仿真需要重运行

**实现**：需要实现增量更新方案（前面设计的EDGEDATA_INCREMENTAL_UPDATE_DESIGN.md）

**优点**：
- ✅ 最大灵活性

**缺点**：
- ❌ 实现复杂度高（增量更新逻辑）
- ❌ 用户需要理解版本和重运行概念
- ❌ 增加维护成本

---

## 推荐方案：策略B（默认全选 + 允许部分 + 明确警告）

### 理由

1. **平衡简单性和灵活性**
   - 默认行为简单（全选）
   - 允许高级用户自定义

2. **明确的用户引导**
   - 快捷按钮（全部/仅基线）
   - 清晰的警告提示
   - 保留用户选择权

3. **适应实际需求**
   - 大多数用户：选择全部策略
   - 快速测试：只选基线
   - 分阶段分析：先基线，后续手动创建其他

---

## 多事件批量创建实现

### API设计

**方案1：循环调用单事件API（推荐）**

```javascript
async function batchCreateMultipleEvents() {
    const selectedEvents = getSelectedEvents();

    if (selectedEvents.length === 0) {
        alert('请至少选择一个事件');
        return;
    }

    // 确认
    const confirmMsg = `
即将批量创建 ${selectedEvents.length} 个事件的案例:

${selectedEvents.map(e =>
    `• Event ${e.event_id} (${e.scenario_count}个场景)`
).join('\n')}

总计: ${selectedEvents.reduce((sum, e) => sum + e.scenario_count, 0)} 个场景
预计: 约 ${Math.ceil(selectedEvents.length * 3)} 分钟

确认创建？
    `;

    if (!confirm(confirmMsg)) return;

    // 依次创建每个事件
    const results = [];
    for (const event of selectedEvents) {
        try {
            showProgress(`正在创建 Event ${event.event_id} (${results.length + 1}/${selectedEvents.length})`);

            const result = await createSingleEventCase(event);
            results.push({
                event_id: event.event_id,
                success: true,
                case_id: result.case_id,
                scenarios_created: result.scenarios_created
            });

        } catch (error) {
            results.push({
                event_id: event.event_id,
                success: false,
                error: error.message
            });
        }
    }

    // 显示结果
    hideProgress();
    showBatchResults(results);
}

// 创建单个事件案例
async function createSingleEventCase(event) {
    const selectedScenarios = getSelectedScenariosForEvent(event.event_id);

    const requestData = {
        event_id: event.event_id,
        event_type: mapEventTypeToFolder(event.event_type),
        scenarios: selectedScenarios,
        // ... 其他配置
    };

    const response = await fetch('/api/v1/event/create_case_batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || '创建失败');
    }

    return await response.json();
}

// 显示批量创建结果
function showBatchResults(results) {
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    const message = `
批量创建完成！

✅ 成功: ${successCount} 个事件
${results.filter(r => r.success).map(r =>
    `  • Event ${r.event_id}: ${r.case_id} (${r.scenarios_created}个场景)`
).join('\n')}

${failCount > 0 ? `
❌ 失败: ${failCount} 个事件
${results.filter(r => !r.success).map(r =>
    `  • Event ${r.event_id}: ${r.error}`
).join('\n')}
` : ''}
    `;

    alert(message);

    // 刷新页面
    loadCreatedCases();
    renderEventGroups();
}
```

**方案2：单次API调用多事件（备选）**

```javascript
// 如果后端支持批量多事件创建
async function batchCreateMultipleEventsV2() {
    const selectedEvents = getSelectedEvents();

    const requestData = {
        events: selectedEvents.map(event => ({
            event_id: event.event_id,
            event_type: mapEventTypeToFolder(event.event_type),
            scenarios: getSelectedScenariosForEvent(event.event_id),
            // ... 其他配置
        }))
    };

    const response = await fetch('/api/v1/events/create_cases_batch', {
        method: 'POST',
        body: JSON.stringify(requestData)
    });

    // 后端并行或串行创建所有事件的案例
}
```

**推荐**：方案1（循环调用）
- 更简单，复用现有API
- 更容易错误处理
- 进度反馈更清晰

---

## 数据验证逻辑

### 检查事件是否有完整场景

```javascript
function validateEventCompleteness(event) {
    const requiredStrategies = ['no_control', 'vss', 'tec', 'dhs'];
    const availableStrategies = event.scenarios.map(s => s.strategy);

    const missingStrategies = requiredStrategies.filter(
        s => !availableStrategies.includes(s)
    );

    return {
        isComplete: missingStrategies.length === 0,
        missingStrategies: missingStrategies,
        availableStrategies: availableStrategies
    };
}

// 渲染时显示完整性状态
function renderEventCompleteness(event) {
    const validation = validateEventCompleteness(event);

    if (validation.isComplete) {
        return `
            <span class="completeness-badge complete">
                ✓ 场景完整 (${validation.availableStrategies.length}/4)
            </span>
        `;
    } else {
        return `
            <span class="completeness-badge incomplete">
                ⚠️ 缺少策略: ${validation.missingStrategies.map(getStrategyDisplay).join(', ')}
            </span>
        `;
    }
}
```

---

## 用户体验优化

### 1. 进度反馈

```javascript
function showProgress(message, current, total) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    progressBar.style.display = 'block';
    progressText.textContent = message;

    if (current && total) {
        const percent = Math.round((current / total) * 100);
        progressBar.querySelector('.progress-fill').style.width = `${percent}%`;
        progressText.textContent = `${message} (${current}/${total})`;
    }
}
```

### 2. 批量操作确认

```javascript
function confirmBatchCreation(selectedEvents) {
    const totalScenarios = selectedEvents.reduce(
        (sum, e) => sum + e.scenario_count, 0
    );

    return confirm(`
📦 批量创建确认

选中事件: ${selectedEvents.length} 个
总场景数: ${totalScenarios} 个
预计时间: 约 ${estimateTime(selectedEvents.length)} 分钟

明细:
${selectedEvents.map(e =>
    `  • Event ${e.event_id}: ${e.scenario_count}个场景`
).join('\n')}

是否继续？
    `);
}
```

### 3. 错误处理

```javascript
async function createWithRetry(event, maxRetries = 2) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await createSingleEventCase(event);
        } catch (error) {
            if (attempt === maxRetries) {
                throw error;
            }
            console.warn(`Retry ${attempt}/${maxRetries} for Event ${event.event_id}`);
            await sleep(1000 * attempt); // 指数退避
        }
    }
}
```

---

## 最终推荐配置

### UI配置

| 功能 | 实现 |
|------|------|
| 事件选择 | 复选框，支持多选 |
| 场景选择 | 默认全选，允许取消（有警告）|
| 快捷按钮 | "全部策略" / "仅基线" |
| 批量创建 | 循环调用单事件API |
| 进度显示 | 进度条 + 当前/总数 |

### 验证规则

| 验证项 | 规则 |
|--------|------|
| 场景完整性 | 显示缺少的策略（允许但警告）|
| 重复创建 | 检查事件是否已有案例 |
| 最小选择 | 至少选择1个事件 |
| 场景数量 | 至少包含1个场景（通常是no_control）|

### API调用策略

```
用户选择: Event A, Event B, Event C
  ↓
循环创建:
  1. POST /api/v1/event/create_case_batch (Event A)
     → case_event_A (4个场景)
  2. POST /api/v1/event/create_case_batch (Event B)
     → case_event_B (4个场景)
  3. POST /api/v1/event/create_case_batch (Event C)
     → case_event_C (3个场景, 缺少DHS)
  ↓
显示结果:
  ✅ 成功: 3个事件, 11个场景
  ⚠️ Event C缺少DHS策略
```

---

## 实现优先级

### P0 (必须实现)
- [x] 事件级复选框
- [x] 默认全选所有场景
- [x] 批量创建（循环调用）
- [x] 基本进度显示
- [x] 场景完整性检查

### P1 (重要)
- [ ] 快捷预设按钮（全部/仅基线）
- [ ] 场景选择警告
- [ ] 详细的结果反馈
- [ ] 错误重试机制

### P2 (增强)
- [ ] 高级筛选（只显示完整事件）
- [ ] 批量导出配置
- [ ] 创建历史记录

---

**Status**: Enhanced Design Complete
**Date**: 2025-11-15
**Recommendation**: 策略B + 循环API调用

