# 场景浏览器创建模式设计（单个vs批量）

**Date**: 2025-11-15
**Goal**: 优化创建流程，支持快速单个创建和批量创建

---

## 当前问题分析

### 当前实现

**单个场景创建**：
```
用户点击[创建]
  ↓
弹出模态框（caseCreationModal）
  ├─ 加载event_description.json
  ├─ 加载traffic_input_config.json
  ├─ 加载control_strategy_config.json
  ├─ 显示所有参数（只读）
  └─ 用户确认后点击[确认创建]
  ↓
调用API创建
```

**目的**：确保参数正确加载，用户可以验证

### 用户需求

1. ✅ **批量创建**：不需要弹框，自动提取参数
2. ❓ **单个创建**：是否保留？是否需要弹框？
3. ✅ **参数正确性**：必须保证提取到所有必需参数

---

## 推荐方案：三种创建模式

### 模式1：批量创建（主要模式）⭐

**使用场景**：用户想创建一个或多个事件的所有场景

**UI**：
```
┌────────────────────────────────────────────┐
│ ☑ Event 7180720 - 交通事故 (4个场景)      │
│   ⚪无控制 🚦VSS 🛂TEC 🛣️DHS            │
│   [批量创建事件案例]                       │
└────────────────────────────────────────────┘
```

**流程**：
```
用户点击[批量创建事件案例]
  ↓
显示确认对话框（简化版，显示关键参数摘要）
  ├─ 事件ID: 7180720
  ├─ 场景数: 4
  ├─ 策略: 无控制、VSS、TEC、DHS
  └─ 预计时间: 约3分钟
  ↓
用户确认
  ↓
自动提取参数（无需弹框）:
  ├─ 从allScenarios获取基本信息
  ├─ 从event_description.json获取位置
  ├─ 从traffic_input_config.json获取仿真配置
  └─ 从control_strategy_config.json获取策略参数
  ↓
调用API批量创建
```

**优点**：
- ✅ 快速，无需手动确认每个参数
- ✅ 一次创建多个场景
- ✅ 参数自动提取，减少用户操作

---

### 模式2：快速创建（保留单个创建按钮，简化流程）⭐

**使用场景**：用户只想创建某个特定场景（例如只要基线）

**UI**：
```
表格行:
┌──────────────────────────────────────────┐
│ scenario_7180720_vss  │ [快速创建]      │
└──────────────────────────────────────────┘
```

**流程**：
```
用户点击[快速创建]
  ↓
显示简化确认对话框
  ├─ 场景: scenario_7180720_vss
  ├─ 策略: VSS
  ├─ 事件: Event 7180720 - 交通事故
  └─ 确认创建？
  ↓
用户点击[确定]
  ↓
自动提取参数（与批量创建相同逻辑）
  ↓
调用API创建
```

**关键改动**：
- ❌ **移除详细参数弹框**
- ✅ 使用简化的确认对话框
- ✅ 参数自动提取（与批量创建共用代码）

---

### 模式3：调试模式（可选，仅供调试）

**使用场景**：开发调试或用户想查看参数详情

**UI**：
```
┌────────────────────────────────────────────┐
│ Event 7180720 - 交通事故                   │
│ [批量创建] [预览参数▼]                     │
└────────────────────────────────────────────┘
```

**点击[预览参数]**：
```
显示参数详情弹框（类似现有的caseCreationModal）
  ├─ 场景信息
  ├─ 事件位置
  ├─ 仿真配置
  ├─ 管控策略参数
  └─ [仅查看，不创建] [确认并创建]
```

**用途**：
- 调试参数提取逻辑
- 用户想确认参数细节
- **不作为主要创建流程**

---

## 参数提取保证机制

### 核心原则

✅ **统一参数提取函数**：批量创建和单个创建使用相同的参数提取逻辑

✅ **参数验证**：提取后验证必需参数是否完整

✅ **降级策略**：如果某个JSON文件加载失败，使用默认值或从场景数据推导

### 实现：统一参数提取器

```javascript
/**
 * 提取场景的完整参数
 * @param {Object} scenario - 场景对象（来自allScenarios）
 * @returns {Object} 完整的创建参数
 */
async function extractScenarioParameters(scenario) {
    const scenarioId = scenario.scenario_id;
    const eventType = scenario.event_type;
    const strategy = scenario.strategy;

    // 映射事件类型到文件夹
    const eventFolder = mapEventTypeToFolder(eventType);
    const scenarioDir = scenarioId;

    // 初始化参数对象
    const params = {
        scenario_id: scenarioId,
        event_id: scenario.event_id,
        event_type: eventFolder,  // 英文文件夹名
        strategy: strategy,

        // 默认值（如果JSON加载失败会使用这些）
        network_file: "templates/network_files/sichuan202508v7.net.xml",
        od_file: "dwd.dwd_od_weekly",
        taz_file: "templates/taz_files/TAZ_6.add.xml",

        time_range: {
            start: scenario.event_start,
            end: scenario.event_end
        },

        simulation_duration_hours: scenario.duration_hours || 2.5,

        output_config: {
            generate_edgedata: true,
            generate_e1: true,
            generate_summary: true,
            generate_tripinfo: true
        },

        event_location: {},
        strategy_config: {}
    };

    try {
        // 1. 加载事件位置信息（event_description.json）
        const eventDescUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/event_description.json`;
        const eventDescResponse = await fetch(eventDescUrl);

        if (eventDescResponse.ok) {
            const eventDesc = await eventDescResponse.json();

            params.event_location = {
                road: eventDesc.location?.road,
                direction: eventDesc.location?.direction,
                mileage: eventDesc.location?.mileage,
                edge_id: eventDesc.location?.edge_id,
                junction_id: eventDesc.location?.junction_id,
                coordinates: eventDesc.location?.coordinates
            };

            console.log(`✓ 加载事件位置: ${scenarioId}`);
        } else {
            console.warn(`⚠️ 事件位置加载失败: ${scenarioId}, 使用场景数据`);
            params.event_location = {
                road: scenario.road,
                mileage: scenario.location
            };
        }

    } catch (error) {
        console.warn(`⚠️ 事件位置加载异常: ${scenarioId}`, error);
    }

    try {
        // 2. 加载仿真配置（traffic_input_config.json）
        const trafficConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/traffic_input_config.json`;
        const trafficResponse = await fetch(trafficConfigUrl);

        if (trafficResponse.ok) {
            const trafficConfig = await trafficResponse.json();

            // 更新OD时间范围
            if (trafficConfig.od_time_range) {
                params.time_range = {
                    start: trafficConfig.od_time_range.start,
                    end: trafficConfig.od_time_range.end
                };
            }

            // 更新仿真时长
            if (trafficConfig.simulation_duration_hours !== undefined) {
                params.simulation_duration_hours = trafficConfig.simulation_duration_hours;
            }

            // 更新文件路径
            if (trafficConfig.network_file) {
                params.network_file = trafficConfig.network_file;
            }
            if (trafficConfig.od_table) {
                params.od_file = trafficConfig.od_table;
            }
            if (trafficConfig.taz_file) {
                params.taz_file = trafficConfig.taz_file;
            }

            console.log(`✓ 加载仿真配置: ${scenarioId}`);
        } else {
            console.warn(`⚠️ 仿真配置加载失败: ${scenarioId}, 使用默认值`);
        }

    } catch (error) {
        console.warn(`⚠️ 仿真配置加载异常: ${scenarioId}`, error);
    }

    try {
        // 3. 加载管控策略配置（control_strategy_config.json）
        if (strategy !== 'no_control' && strategy !== 'NO_CONTROL') {
            const strategyConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/control_strategy_config.json`;
            const strategyResponse = await fetch(strategyConfigUrl);

            if (strategyResponse.ok) {
                const strategyConfig = await strategyResponse.json();

                params.strategy_config = {
                    strategy_type: strategyConfig.strategy_type,
                    strategy_name: strategyConfig.strategy_name,
                    activation_time: strategyConfig.activation_time,
                    deactivation_time: strategyConfig.deactivation_time,
                    response_delay_minutes: strategyConfig.response_delay_minutes,

                    // 策略特定参数
                    vss_speed_limit: strategyConfig.vss_speed_limit,
                    tec_flow_reduction: strategyConfig.tec_flow_reduction,
                    dhs_shoulder_lanes: strategyConfig.dhs_shoulder_lanes
                };

                console.log(`✓ 加载策略配置: ${scenarioId} (${strategy})`);
            } else {
                console.warn(`⚠️ 策略配置加载失败: ${scenarioId}`);
            }
        }

    } catch (error) {
        console.warn(`⚠️ 策略配置加载异常: ${scenarioId}`, error);
    }

    // 4. 参数验证
    const validation = validateParameters(params);
    if (!validation.valid) {
        console.error(`❌ 参数验证失败: ${scenarioId}`, validation.errors);
        throw new Error(`参数验证失败: ${validation.errors.join(', ')}`);
    }

    console.log(`✅ 参数提取完成: ${scenarioId}`);
    return params;
}

/**
 * 验证参数完整性
 */
function validateParameters(params) {
    const errors = [];

    // 必需字段检查
    if (!params.scenario_id) errors.push('缺少scenario_id');
    if (!params.event_id) errors.push('缺少event_id');
    if (!params.event_type) errors.push('缺少event_type');
    if (!params.time_range?.start) errors.push('缺少开始时间');
    if (!params.time_range?.end) errors.push('缺少结束时间');
    if (!params.network_file) errors.push('缺少network_file');
    if (!params.od_file) errors.push('缺少od_file');

    // 警告（不阻止创建，但记录）
    if (!params.event_location?.edge_id) {
        console.warn('⚠️ 缺少edge_id，edgeData生成可能不准确');
    }

    return {
        valid: errors.length === 0,
        errors: errors
    };
}
```

### 批量创建参数提取

```javascript
/**
 * 批量创建事件案例
 */
async function batchCreateEventCase(eventId) {
    const selectedScenarios = getSelectedScenarios(eventId);

    if (selectedScenarios.length === 0) {
        alert('请至少选择一个场景策略');
        return;
    }

    // 获取事件信息
    const event = eventGroups.find(e => e.event_id === eventId);
    if (!event) {
        alert('未找到事件信息');
        return;
    }

    try {
        showLoadingIndicator('正在提取参数...');

        // 提取所有选中场景的参数
        const scenarioParams = [];
        for (const selected of selectedScenarios) {
            const scenario = allScenarios.find(s => s.scenario_id === selected.scenario_id);
            if (!scenario) {
                console.warn(`⚠️ 未找到场景: ${selected.scenario_id}`);
                continue;
            }

            try {
                const params = await extractScenarioParameters(scenario);
                scenarioParams.push(params);
            } catch (error) {
                console.error(`❌ 参数提取失败: ${selected.scenario_id}`, error);

                // 询问用户是否继续
                const continueAnyway = confirm(
                    `场景 ${selected.scenario_id} 参数提取失败:\n${error.message}\n\n是否跳过该场景并继续？`
                );

                if (!continueAnyway) {
                    hideLoadingIndicator();
                    return;
                }
            }
        }

        hideLoadingIndicator();

        if (scenarioParams.length === 0) {
            alert('所有场景参数提取失败，无法创建');
            return;
        }

        // 显示确认对话框（简化版，显示关键参数）
        const confirmMessage = buildBatchConfirmMessage(event, scenarioParams);
        if (!confirm(confirmMessage)) {
            return;
        }

        // 构建API请求
        const requestData = {
            event_id: eventId,
            event_type: scenarioParams[0].event_type,  // 所有场景的event_type相同
            scenarios: scenarioParams.map(p => ({
                scenario_id: p.scenario_id,
                strategy: p.strategy
            })),
            network_file: scenarioParams[0].network_file,
            od_file: scenarioParams[0].od_file,
            taz_file: scenarioParams[0].taz_file,
            time_range: scenarioParams[0].time_range,
            simulation_duration_hours: scenarioParams[0].simulation_duration_hours,
            output_config: scenarioParams[0].output_config
        };

        // 调用API
        showLoadingIndicator(`正在创建事件案例 (Event ${eventId})...`);

        const response = await fetch('/api/v1/event/create_case_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        hideLoadingIndicator();

        if (response.ok) {
            alert(`
✅ 事件案例创建成功！

案例ID: ${result.case_id}
场景数: ${result.scenarios_created}
监测边数: ${result.edgedata_config?.total_unique_edges || '未知'}

详情:
${result.simulations?.map(s =>
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

/**
 * 构建批量创建确认消息
 */
function buildBatchConfirmMessage(event, scenarioParams) {
    const firstParam = scenarioParams[0];

    return `
即将批量创建事件案例:

🎯 事件信息:
  ID: ${event.event_id}
  类型: ${getEventTypeDisplay(event.event_type)}
  位置: ${event.road} ${event.location}
  时间: ${event.event_start.split(' ')[1]} ~ ${event.event_end.split(' ')[1]}

📋 场景数: ${scenarioParams.length}
  ${scenarioParams.map(p => `  • ${getStrategyDisplay(p.strategy)}`).join('\n')}

⚙️ 配置:
  仿真时长: ${firstParam.simulation_duration_hours}小时
  OD时间: ${firstParam.time_range.start} ~ ${firstParam.time_range.end}
  ${firstParam.event_location.edge_id ? `事件边: ${firstParam.event_location.edge_id}` : ''}

⏱️ 预计时间: 约${Math.ceil(2 + scenarioParams.length * 0.5)}分钟

确认创建？
    `;
}
```

### 快速创建参数提取

```javascript
/**
 * 快速创建单个场景（新版，无详细弹框）
 */
async function quickCreateScenario(scenarioId) {
    const scenario = allScenarios.find(s => s.scenario_id === scenarioId);

    if (!scenario) {
        alert('未找到场景信息');
        return;
    }

    // 检查是否已创建
    if (isScenarioCreated(scenarioId)) {
        const existingCase = scenarioCaseMap[scenarioId][0];
        const viewCase = confirm(
            `该场景已有案例: ${existingCase.case_id}\n\n点击"确定"查看案例详情`
        );

        if (viewCase) {
            window.location.href = `case-simulation-center.html?case_id=${existingCase.case_id}`;
        }
        return;
    }

    try {
        showLoadingIndicator('正在提取参数...');

        // 提取参数（使用统一函数）
        const params = await extractScenarioParameters(scenario);

        hideLoadingIndicator();

        // 简化确认对话框
        const confirmMessage = `
快速创建场景:

场景: ${scenarioId}
策略: ${getStrategyDisplay(params.strategy)}
事件: Event ${params.event_id} - ${getEventTypeDisplay(scenario.event_type)}
位置: ${params.event_location.road || '未知'} ${params.event_location.mileage || ''}
${params.event_location.edge_id ? `事件边: ${params.event_location.edge_id}` : ''}

确认创建？
        `;

        if (!confirm(confirmMessage)) {
            return;
        }

        // 调用API（单场景API或批量API with 1 scenario）
        showLoadingIndicator('正在创建场景案例...');

        const requestData = {
            event_id: params.event_id,
            event_type: params.event_type,
            scenarios: [{
                scenario_id: params.scenario_id,
                strategy: params.strategy
            }],
            network_file: params.network_file,
            od_file: params.od_file,
            taz_file: params.taz_file,
            time_range: params.time_range,
            simulation_duration_hours: params.simulation_duration_hours,
            output_config: params.output_config
        };

        const response = await fetch('/api/v1/event/create_case_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        hideLoadingIndicator();

        if (response.ok) {
            alert(`✅ 场景创建成功！\n\n案例ID: ${result.case_id}\nOD生成: ${result.od_generation_status}`);

            // 刷新
            await loadCreatedCases();
            renderEventGroups();
        } else {
            alert(`❌ 创建失败: ${result.message || result.error}`);
        }

    } catch (error) {
        hideLoadingIndicator();
        alert(`❌ 参数提取或创建失败: ${error.message}`);
        console.error('Quick creation error:', error);
    }
}
```

---

## UI改动方案

### 方案A：完全移除单个创建按钮（最简洁）

**表格视图**：
```
┌────────────────────────────────────────────┐
│ scenario_7180720_vss  │ [详情]            │  (只保留详情按钮)
└────────────────────────────────────────────┘
```

**事件卡片视图**：
```
┌────────────────────────────────────────────┐
│ Event 7180720 - 交通事故                   │
│ ☑ 无控制 ☑ VSS ☑ TEC ☑ DHS               │
│ [批量创建事件案例]                          │  (只有批量创建)
└────────────────────────────────────────────┘
```

**优点**：
- ✅ 最简洁
- ✅ 强制用户使用批量创建（保证完整性）

**缺点**：
- ❌ 失去单场景快速创建能力

---

### 方案B：保留快速创建按钮（推荐）⭐

**表格视图**：
```
┌────────────────────────────────────────────┐
│ scenario_7180720_vss  │ [详情] [快速创建] │
└────────────────────────────────────────────┘
```

**事件卡片视图**：
```
┌────────────────────────────────────────────┐
│ Event 7180720 - 交通事故                   │
│ ☑ 无控制 ☑ VSS ☑ TEC ☑ DHS               │
│ [批量创建] [预览参数▼]                     │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ 单个场景行（可选，表格视图中）:             │
│ scenario_7180720_vss  │ [快速创建]        │
└────────────────────────────────────────────┘
```

**优点**：
- ✅ 灵活性高
- ✅ 支持快速单场景创建
- ✅ 统一参数提取逻辑

**缺点**：
- ⚠️ UI按钮稍多

---

### 方案C：条件显示（智能）

**规则**：
- 如果事件有多个场景：只显示批量创建
- 如果只有单个场景（如no_control）：显示快速创建

**实现**：
```javascript
function getCreateButton(scenario) {
    const event = eventGroups.find(e => e.event_id === scenario.event_id);

    if (event && event.scenarios.length > 1) {
        // 多场景事件，引导用户使用批量创建
        return `
            <button class="btn btn-sm btn-secondary" disabled>
                请使用批量创建
            </button>
        `;
    } else {
        // 单场景，提供快速创建
        return `
            <button class="btn btn-sm btn-primary"
                    onclick="quickCreateScenario('${scenario.scenario_id}')">
                快速创建
            </button>
        `;
    }
}
```

---

## 最终推荐配置

### UI设计

| 视图 | 按钮配置 |
|------|---------|
| **事件卡片视图** | [批量创建事件案例] [预览参数▼] |
| **表格视图** | [详情] （移除单个创建按钮）|

### 创建流程

| 模式 | 触发 | 流程 |
|------|------|------|
| **批量创建** | 点击事件卡片的[批量创建] | 提取参数 → 简化确认 → 调用API |
| **快速创建** | （可选）表格视图的[快速创建] | 提取参数 → 简化确认 → 调用API |
| **预览参数** | 点击[预览参数▼] | 显示详细参数弹框（仅查看）|

### 参数提取

✅ **统一函数**: `extractScenarioParameters(scenario)`

✅ **验证**: `validateParameters(params)`

✅ **降级**: JSON加载失败 → 使用默认值或场景数据

✅ **错误处理**: 提取失败 → 询问用户是否跳过

---

## 实现清单

### 必须实现（P0）

- [x] `extractScenarioParameters()` - 统一参数提取函数
- [x] `validateParameters()` - 参数验证
- [x] `batchCreateEventCase()` - 批量创建（使用统一提取）
- [x] `buildBatchConfirmMessage()` - 构建确认消息
- [ ] 移除或简化现有的`openCreateCaseModal()`

### 可选实现（P1）

- [ ] `quickCreateScenario()` - 快速创建单场景
- [ ] `previewParameters()` - 预览参数详情（调试用）
- [ ] 错误重试机制
- [ ] 参数缓存（避免重复加载JSON）

### UI更新（P0）

- [ ] 事件卡片添加[批量创建]按钮
- [ ] （可选）表格视图改[创建]为[快速创建]
- [ ] 移除或隐藏详细参数弹框（caseCreationModal）

---

**Status**: Implementation Ready
**Date**: 2025-11-15
**Recommendation**: 方案B（保留快速创建） + 统一参数提取

