# 场景浏览器批量创建实现方案

**Date**: 2025-11-15
**Goal**: 改造场景浏览器，支持按事件分组、多选场景、批量创建事件案例

---

## 当前实现分析

### 当前数据结构

```javascript
// 场景数据（来自 scenario_index.json）
{
  scenario_id: "scenario_7180720_vss",
  event_id: "7180720",
  strategy: "vss",
  event_type: "交通事故",
  road: "成温邛高速",
  event_start: "2025-06-13 15:22:37",
  duration_hours: 1.5
}
```

**Key Point**: 同一个 `event_id` 对应多个 `scenario_id`（不同策略）

示例：
```
event_id: 7180720
  ├─ scenario_7180720_no_control  (strategy: no_control)
  ├─ scenario_7180720_vss         (strategy: vss)
  ├─ scenario_7180720_tec         (strategy: tec)
  └─ scenario_7180720_dhs         (strategy: dhs)
```

### 当前UI问题

❌ **表格式展示**：每行一个场景，无法看出事件关系
❌ **单个创建**：每次只能创建一个场景
❌ **重复操作**：要创建4个场景需要点击4次

---

## 改进方案：事件卡片 + 策略多选

### UI设计

#### 方案1：卡片式分组（推荐）⭐

```
┌────────────────────────────────────────────────────────────┐
│ Event 7180720 - 交通事故                                   │
│ 📍 成温邛高速 K23+500                                      │
│ 🕐 2025-06-13 15:22:37 ~ 16:49:16 (1.5小时)               │
│                                                            │
│ 选择要创建的场景策略:                                       │
│ ☑ 无控制 (基线)             状态: 未创建                  │
│ ☑ VSS - 可变限速            状态: 未创建                  │
│ ☑ TEC - 收费站管控          状态: 未创建                  │
│ ☑ DHS - 动态硬路肩          状态: 未创建                  │
│                                                            │
│ [全选] [取消全选] [批量创建事件案例]                        │
└────────────────────────────────────────────────────────────┘
```

#### 方案2：折叠表格（兼容性好）

```
表格行:
┌─────────────────────────────────────────────────────┐
│ ▼ Event 7180720 - 交通事故 - 成温邛高速            │ [展开/收起]
├─────────────────────────────────────────────────────┤
│   ☑ 无控制   未创建                                 │
│   ☑ VSS      未创建                                 │
│   ☑ TEC      未创建                                 │
│   ☑ DHS      未创建                                 │
│                                                     │
│   [批量创建选中场景]                                │
└─────────────────────────────────────────────────────┘
```

---

## 实现方案（推荐：卡片式）

### Step 1: 数据分组 - 按事件聚合场景

```javascript
// frontend/scenarios/scenario_browser.js

// 新增：按事件ID分组场景
function groupScenariosByEvent(scenarios) {
    const eventGroups = {};

    scenarios.forEach(scenario => {
        const eventId = scenario.event_id;

        if (!eventGroups[eventId]) {
            eventGroups[eventId] = {
                event_id: eventId,
                event_type: scenario.event_type,
                road: scenario.road,
                location: scenario.location,
                event_start: scenario.event_start,
                event_end: scenario.event_end,
                duration_hours: scenario.duration_hours,
                scenarios: []  // 该事件下的所有场景
            };
        }

        eventGroups[eventId].scenarios.push(scenario);
    });

    return Object.values(eventGroups);
}

// 使用示例
let eventGroups = [];  // 全局变量

async function loadScenarios() {
    // ... 现有代码加载 allScenarios ...

    // 新增：按事件分组
    eventGroups = groupScenariosByEvent(allScenarios);

    console.log(`加载了 ${eventGroups.length} 个事件，${allScenarios.length} 个场景`);

    // 渲染
    renderEventGroups();
}
```

### Step 2: 渲染事件卡片

```javascript
// 渲染事件分组卡片
function renderEventGroups() {
    const container = document.getElementById('eventGroupsContainer');

    if (eventGroups.length === 0) {
        container.innerHTML = '<div class="empty-state">未找到事件场景</div>';
        return;
    }

    const html = eventGroups.map(event => renderEventCard(event)).join('');
    container.innerHTML = html;
}

// 渲染单个事件卡片
function renderEventCard(event) {
    const eventId = event.event_id;

    // 检查哪些场景已创建
    const scenarioStatuses = event.scenarios.map(s => ({
        scenario_id: s.scenario_id,
        strategy: s.strategy,
        isCreated: isScenarioCreated(s.scenario_id),
        statusDisplay: getScenarioStatusDisplay(s.scenario_id)
    }));

    // 是否所有场景都已创建
    const allCreated = scenarioStatuses.every(s => s.isCreated);

    return `
        <div class="event-card" id="event-${eventId}">
            <div class="event-header">
                <div class="event-info">
                    <h3>
                        <span class="event-id">Event ${eventId}</span>
                        <span class="badge badge-${getEventTypeClass(event.event_type)}">
                            ${getEventTypeDisplay(event.event_type)}
                        </span>
                    </h3>
                    <div class="event-details">
                        <span class="detail-item">
                            📍 ${event.road} ${event.location}
                        </span>
                        <span class="detail-item">
                            🕐 ${event.event_start} ~ ${event.event_end.split(' ')[1]}
                        </span>
                        <span class="detail-item">
                            ⏱ ${event.duration_hours} 小时
                        </span>
                    </div>
                </div>
            </div>

            <div class="event-scenarios">
                <h4>选择要创建的场景策略:</h4>

                ${scenarioStatuses.map(s => `
                    <div class="scenario-checkbox-item">
                        <label>
                            <input
                                type="checkbox"
                                class="scenario-checkbox"
                                data-event-id="${eventId}"
                                data-scenario-id="${s.scenario_id}"
                                data-strategy="${s.strategy}"
                                ${s.isCreated ? 'disabled checked' : ''}
                                ${!s.isCreated ? 'checked' : ''}
                            >
                            <span class="strategy-label">
                                ${getStrategyIcon(s.strategy)} ${getStrategyDisplay(s.strategy)}
                            </span>
                            <span class="scenario-status">
                                ${s.statusDisplay}
                            </span>
                        </label>
                    </div>
                `).join('')}
            </div>

            <div class="event-actions">
                <button
                    class="btn btn-sm btn-secondary"
                    onclick="selectAllScenarios('${eventId}', true)"
                >
                    全选
                </button>
                <button
                    class="btn btn-sm btn-secondary"
                    onclick="selectAllScenarios('${eventId}', false)"
                >
                    取消全选
                </button>
                <button
                    class="btn btn-primary"
                    onclick="batchCreateEventCase('${eventId}')"
                    ${allCreated ? 'disabled' : ''}
                >
                    ${allCreated ? '所有场景已创建' : '批量创建事件案例'}
                </button>
            </div>
        </div>
    `;
}

// 获取策略图标
function getStrategyIcon(strategy) {
    const icons = {
        'no_control': '⚪',
        'vss': '🚦',
        'tec': '🛂',
        'dhs': '🛣️',
        'ramp_metering': '🚥'
    };
    return icons[strategy] || '📋';
}
```

### Step 3: 多选控制函数

```javascript
// 全选/取消全选该事件的场景
function selectAllScenarios(eventId, checked) {
    const checkboxes = document.querySelectorAll(
        `.scenario-checkbox[data-event-id="${eventId}"]:not(:disabled)`
    );

    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
    });
}

// 获取选中的场景
function getSelectedScenarios(eventId) {
    const checkboxes = document.querySelectorAll(
        `.scenario-checkbox[data-event-id="${eventId}"]:checked:not(:disabled)`
    );

    return Array.from(checkboxes).map(cb => ({
        scenario_id: cb.dataset.scenarioId,
        strategy: cb.dataset.strategy
    }));
}
```

### Step 4: 批量创建API调用

```javascript
// 批量创建事件案例
async function batchCreateEventCase(eventId) {
    // 1. 获取选中的场景
    const selectedScenarios = getSelectedScenarios(eventId);

    if (selectedScenarios.length === 0) {
        alert('请至少选择一个场景策略');
        return;
    }

    // 2. 获取事件信息
    const event = eventGroups.find(e => e.event_id === eventId);
    if (!event) {
        alert('未找到事件信息');
        return;
    }

    // 3. 准备请求数据
    const requestData = {
        event_id: eventId,
        event_type: mapEventTypeToFolder(event.event_type),
        scenarios: selectedScenarios,
        network_file: "templates/network_files/sichuan202508v7.net.xml",
        od_file: "dwd.dwd_od_weekly",
        taz_file: "templates/taz_files/TAZ_6.add.xml",
        time_range: {
            start: event.event_start,
            end: event.event_end
        },
        simulation_duration_hours: event.duration_hours,
        output_config: {
            generate_edgedata: true,
            generate_e1: true,
            generate_summary: true,
            generate_tripinfo: true
        }
    };

    // 4. 显示确认对话框
    const confirmMessage = `
即将批量创建事件案例:

事件ID: ${eventId}
事件类型: ${getEventTypeDisplay(event.event_type)}
场景数: ${selectedScenarios.length}

选中的策略:
${selectedScenarios.map(s => '  • ' + getStrategyDisplay(s.strategy)).join('\n')}

预计时间: 约 ${Math.ceil(2 + selectedScenarios.length * 0.5)} 分钟

确认创建？
    `;

    if (!confirm(confirmMessage)) {
        return;
    }

    // 5. 调用API
    try {
        showLoadingIndicator(`正在创建事件案例 (Event ${eventId})...`);

        const response = await fetch('/api/v1/event/create_case_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        hideLoadingIndicator();

        if (response.ok) {
            // 成功
            alert(`
✅ 事件案例创建成功！

案例ID: ${result.case_id}
场景数: ${result.scenarios_created}
监测边数: ${result.edgedata_config.total_unique_edges}
OD生成状态: ${result.od_generation_status}

详情:
${result.simulations.map(s =>
    `  • ${getStrategyDisplay(s.strategy)}: ${s.status}`
).join('\n')}
            `);

            // 刷新数据
            await loadCreatedCases();
            renderEventGroups();

        } else {
            alert(`❌ 创建失败: ${result.message || result.error}`);
        }

    } catch (error) {
        hideLoadingIndicator();
        alert(`❌ 创建出错: ${error.message}`);
        console.error('Batch creation error:', error);
    }
}

// 显示/隐藏加载指示器
function showLoadingIndicator(message) {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
        indicator.textContent = message;
        indicator.style.display = 'block';
    }
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}
```

### Step 5: HTML结构更新

```html
<!-- frontend/scenarios/scenario_browser.html -->

<!-- 在现有的 scenarioTable 之前添加 -->
<div class="content-section">
    <div class="section-header">
        <h3>📋 事件场景列表</h3>
        <div class="view-toggle">
            <button
                class="btn btn-sm ${viewMode === 'grouped' ? 'btn-primary' : 'btn-secondary'}"
                onclick="switchViewMode('grouped')"
            >
                📦 按事件分组
            </button>
            <button
                class="btn btn-sm ${viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}"
                onclick="switchViewMode('table')"
            >
                📋 表格视图
            </button>
        </div>
    </div>

    <!-- 事件分组视图 (新) -->
    <div id="eventGroupsContainer" style="display: ${viewMode === 'grouped' ? 'block' : 'none'}">
        <!-- 由 renderEventGroups() 动态生成 -->
    </div>

    <!-- 表格视图 (现有) -->
    <div id="scenarioTable" style="display: ${viewMode === 'table' ? 'block' : 'none'}">
        <!-- 现有的表格渲染 -->
    </div>
</div>

<!-- 加载指示器 -->
<div id="loadingIndicator" class="loading-indicator" style="display: none;">
    正在处理...
</div>
```

### Step 6: CSS样式

```css
/* frontend/scenarios/scenario_browser.css */

/* 事件卡片 */
.event-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 20px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.event-header {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #f0f0f0;
}

.event-info h3 {
    margin: 0 0 10px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.event-id {
    font-size: 18px;
    font-weight: 600;
    color: #333;
}

.event-details {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    color: #666;
    font-size: 14px;
}

.detail-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}

/* 场景多选列表 */
.event-scenarios h4 {
    font-size: 14px;
    color: #666;
    margin: 0 0 15px 0;
    font-weight: 500;
}

.scenario-checkbox-item {
    padding: 10px;
    margin-bottom: 8px;
    background: #f9f9f9;
    border-radius: 6px;
    transition: background-color 0.2s;
}

.scenario-checkbox-item:hover {
    background: #f0f0f0;
}

.scenario-checkbox-item label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    margin: 0;
}

.scenario-checkbox-item input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.scenario-checkbox-item input[type="checkbox"]:disabled {
    cursor: not-allowed;
    opacity: 0.5;
}

.strategy-label {
    flex: 1;
    font-weight: 500;
    color: #333;
}

.scenario-status {
    font-size: 12px;
}

/* 事件操作按钮 */
.event-actions {
    margin-top: 20px;
    padding-top: 15px;
    border-top: 1px solid #e0e0e0;
    display: flex;
    gap: 10px;
    justify-content: flex-end;
}

/* 视图切换按钮 */
.view-toggle {
    display: flex;
    gap: 10px;
}

/* 加载指示器 */
.loading-indicator {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 20px 40px;
    border-radius: 8px;
    font-size: 16px;
    z-index: 9999;
}
```

---

## 使用流程示例

### 用户操作流程

```
1. 打开场景浏览器
   ↓
2. 看到按事件分组的卡片列表:
   ┌────────────────────────────┐
   │ Event 7180720 - 交通事故   │
   │ ☑ 无控制                   │
   │ ☑ VSS                      │
   │ ☑ TEC                      │
   │ ☑ DHS                      │
   │ [批量创建事件案例]          │
   └────────────────────────────┘
   ↓
3. 点击"批量创建事件案例"
   ↓
4. 确认对话框显示:
   - 事件ID: 7180720
   - 场景数: 4
   - 选中策略: 无控制、VSS、TEC、DHS
   ↓
5. 点击确认
   ↓
6. 加载指示器: "正在创建事件案例 (Event 7180720)..."
   ↓
7. API调用: POST /api/v1/event/create_case_batch
   ↓
8. 后端创建:
   - case_event_7180720/
   - 4个仿真目录
   - 统一edgeData.add.xml (122条边)
   - 触发OD生成
   ↓
9. 成功提示:
   "✅ 事件案例创建成功！
    案例ID: case_event_7180720
    场景数: 4
    监测边数: 122"
   ↓
10. 页面刷新，卡片显示"所有场景已创建"
```

---

## 优势总结

### 用户体验

✅ **一目了然**: 事件卡片显示所有可用场景
✅ **灵活选择**: 可以选择部分或全部策略
✅ **快速操作**: 1次点击创建多个场景
✅ **视觉清晰**: 卡片式布局比表格更直观

### 技术优势

✅ **代码复用**: 利用现有数据结构和API
✅ **向后兼容**: 保留表格视图作为备选
✅ **易于扩展**: 可以轻松添加更多策略
✅ **维护性好**: 代码模块化，职责清晰

---

## 实现检查清单

### 前端修改

- [ ] 添加 `groupScenariosByEvent()` 函数
- [ ] 添加 `renderEventGroups()` 函数
- [ ] 添加 `renderEventCard()` 函数
- [ ] 添加 `selectAllScenarios()` 函数
- [ ] 添加 `getSelectedScenarios()` 函数
- [ ] 添加 `batchCreateEventCase()` 函数
- [ ] 添加视图切换功能
- [ ] 更新HTML结构（事件卡片容器）
- [ ] 添加CSS样式（卡片、多选、按钮）

### 后端API

- [ ] 实现 `/api/v1/event/create_case_batch` 端点
- [ ] 实现 `CreateEventCaseBatchRequest` 模型
- [ ] 实现 `create_event_case_batch()` 服务方法
- [ ] 实现 `_generate_complete_edgedata()` 方法
- [ ] 测试批量创建流程

### 测试

- [ ] 测试事件分组显示
- [ ] 测试多选场景功能
- [ ] 测试全选/取消全选
- [ ] 测试批量创建API
- [ ] 测试edgeData统一生成
- [ ] 测试已创建场景的状态显示

---

## 时间估算

| 任务 | 时间 |
|------|------|
| 前端数据分组逻辑 | 1 小时 |
| 事件卡片UI | 2 小时 |
| 多选交互逻辑 | 1 小时 |
| 批量创建API调用 | 1 小时 |
| CSS样式调整 | 1 小时 |
| 后端API实现 | 3 小时 |
| 测试与调试 | 2 小时 |
| **总计** | **11 小时 (~1.5天)** |

---

**Status**: Implementation Guide Ready
**Date**: 2025-11-15
**Next**: Begin frontend implementation

