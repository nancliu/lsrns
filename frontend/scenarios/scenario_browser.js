// 全局状态
let allScenarios = [];
let filteredScenarios = [];
let currentPage = 1;
const pageSize = 20;
let currentFilters = {
    eventType: 'all',
    strategy: 'all',
    searchText: ''
};
let currentScenario = null;
let scenarioCaseMap = {};  // 存储场景ID -> 案例信息的映射
let currentView = 'table';  // 当前视图模式: 'table' 或 'event'

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadCreatedCases();  // 先加载已创建的案例
    loadScenarios();
    setupEventListeners();
});

// 加载已创建的案例（事件场景生成的案例）
async function loadCreatedCases() {
    try {
        // 策略 1: 首先尝试从scenario_index.json直接读取案例映射（更准确）
        // 这会从scenario_index.json的created_cases数组中获取所有案例
        try {
            const response = await fetch('/output/scenarios/scenario_index.json');
            if (response.ok) {
                const data = await response.json();
                const scenarios = data.scenarios || [];

                // 构建从scenario_index.json中的created_cases数组
                scenarioCaseMap = {};
                let totalCases = 0;

                for (const scenario of scenarios) {
                    const scenario_id = scenario.files?.scenario_dir;
                    if (!scenario_id) continue;

                    const created_cases = scenario.created_cases || [];
                    if (created_cases.length > 0) {
                        scenarioCaseMap[scenario_id] = created_cases.map(c => ({
                            case_id: c.case_id,
                            case_name: c.case_name || c.case_id,
                            status: c.status || 'unknown',
                            created_at: c.created_at,
                            source_scenario: c.source_scenario
                        }));
                        totalCases += created_cases.length;
                    }
                }

                console.log(`✓ 从scenario_index.json加载了 ${totalCases} 个案例，涉及 ${Object.keys(scenarioCaseMap).length} 个场景`);
                return; // 成功加载，直接返回
            }
        } catch (e) {
            console.warn('从scenario_index.json加载案例映射失败，降级到API方式:', e);
        }

        // 策略 2: 降级到API方式（用于没有scenario_index.json或加载失败的情况）
        // 调用 API 获取所有案例列表
        const response = await fetch('/api/v1/case/list_cases/?page_size=1000');
        const data = await response.json();
        const allCases = (data.data?.cases || data.data?.items || data.cases || data.items || []);

        // 过滤事件场景案例（包括所有事件场景类型）
        const eventScenarioCases = allCases.filter(c => {
            const sourceType = c.source_type || '';
            const caseType = c.case_type || '';

            // 检查多种事件场景案例标识：
            // 1. source_type 包含 'event_scenario' (包括 'event_scenario' 和 'event_scenario_batch')
            // 2. case_type 为 'event_based' (旧版本事件场景案例)
            // 3. case_type 为 'event_scenario_case' (新版本事件场景案例)
            // 4. metadata_version === '2.0' (v2.0元数据表示事件场景案例)
            return sourceType.includes('event_scenario') ||
                   caseType === 'event_based' ||
                   caseType === 'event_scenario_case' ||
                   c.metadata_version === '2.0';
        });

        // 构建场景ID -> 案例信息的映射
        scenarioCaseMap = {};
        for (const caseItem of eventScenarioCases) {
            // 支持多种源场景ID字段名
            let scenario_id = null;

            // 尝试从source_scenario字段中获取
            if (caseItem.source_scenario) {
                scenario_id = caseItem.source_scenario.scenario_id ||
                             caseItem.source_scenario;
            }

            // 降级到其他字段
            if (!scenario_id) {
                scenario_id = caseItem.scenario_id ||
                            caseItem.source_scenario_id;
            }

            if (!scenario_id) continue;

            if (!scenarioCaseMap[scenario_id]) {
                scenarioCaseMap[scenario_id] = [];
            }

            scenarioCaseMap[scenario_id].push({
                case_id: caseItem.case_id,
                case_name: caseItem.case_name || caseItem.case_id,
                status: caseItem.status || 'unknown',
                created_at: caseItem.created_at
            });
        }

        console.log(`✓ 从API加载了 ${eventScenarioCases.length} 个事件场景案例，涉及 ${Object.keys(scenarioCaseMap).length} 个场景`);
    } catch (error) {
        console.warn('加载已创建案例失败:', error);
        scenarioCaseMap = {};
    }
}

// 加载场景数据
async function loadScenarios() {
    try {
        const response = await fetch('/output/scenarios/scenario_index.json');
        if (!response.ok) {
            throw new Error('无法加载场景索引文件');
        }
        const data = await response.json();
        const rawScenarios = data.scenarios || [];

        // 数据字段映射
        allScenarios = rawScenarios.map(scenario => ({
            scenario_id: scenario.files?.scenario_dir || scenario.scenario_id || '',
            event_id: scenario.event_id || '',
            event_type: scenario.event_type || '',
            control_strategy: scenario.strategy || scenario.control_strategy || '',
            strategy: scenario.strategy || scenario.control_strategy || '',
            road: scenario.location?.road || scenario.road || '',
            location: scenario.location?.mileage || scenario.location || '',
            event_start: scenario.time?.start_time || scenario.event_start || '',
            event_end: scenario.time?.end_time || scenario.event_end || '',
            duration_hours: scenario.time?.duration_hours || scenario.duration_hours || 0,
            case_count: scenario.case_count || 0,
            report_id: scenario.event_id || scenario.report_id || '',
            _raw: scenario
        }));

        console.log(`✓ 加载了 ${allScenarios.length} 个场景`);
        initializeFilters();
        applyFilters();
    } catch (error) {
        console.error('加载场景失败:', error);
        document.getElementById('scenarioTable').innerHTML = '<div class="empty-state">加载失败，请检查网络或刷新页面</div>';
    }
}

// 初始化筛选器
function initializeFilters() {
    const eventTypes = [...new Set(allScenarios.map(s => s.event_type))].sort();
    const strategies = [...new Set(allScenarios.map(s => s.strategy))].sort();

    // 事件类型芯片
    const eventTypeChips = document.getElementById('eventTypeChips');
    eventTypeChips.innerHTML = '<button class="chip active" onclick="filterByEventType(\'all\')">全部</button>' +
        eventTypes.map(type => `<button class="chip" onclick="filterByEventType('${type}')">${getEventTypeDisplay(type)}</button>`).join('');

    // 管控策略芯片
    const strategyChips = document.getElementById('strategyChips');
    strategyChips.innerHTML = '<button class="chip active" onclick="filterByStrategy(\'all\')">全部</button>' +
        strategies.map(s => `<button class="chip" onclick="filterByStrategy('${s}')">${getStrategyDisplay(s)}</button>`).join('');

    // 计算典型场景种类数量
    // 定义：不同的(事件类型 + 管控策略)组合种类
    // 包括：无管控、VSS、TEC、DHS等所有管控策略
    // 注：只统计存在场景的组合（场景数 > 0）
    const typicalScenarioCombinations = new Set(
        allScenarios.map(s => `${s.event_type}|||${s.strategy}`)
    );
    const typicalScenariosCount = typicalScenarioCombinations.size;

    // 更新统计信息
    document.getElementById('totalScenarios').textContent = allScenarios.length;
    document.getElementById('eventTypeCount').textContent = eventTypes.length;
    document.getElementById('strategyCount').textContent = strategies.length;
    document.getElementById('typicalScenarios').textContent = typicalScenariosCount;
}

// 筛选函数
function filterByEventType(type) {
    currentFilters.eventType = type;
    currentPage = 1;
    updateChips('eventTypeChips', type);
    applyFilters();
}

function filterByStrategy(strategy) {
    currentFilters.strategy = strategy;
    currentPage = 1;
    updateChips('strategyChips', strategy);
    applyFilters();
}

function updateChips(containerId, activeValue) {
    document.querySelectorAll(`#${containerId} .chip`).forEach(chip => {
        chip.classList.remove('active');
        const value = chip.textContent.trim();
        if ((activeValue === 'all' && value === '全部') ||
            (activeValue !== 'all' && chip.onclick.toString().includes(`'${activeValue}'`))) {
            chip.classList.add('active');
        }
    });
}

// 应用筛选
function applyFilters() {
    filteredScenarios = allScenarios.filter(s => {
        const eventTypeMatch = currentFilters.eventType === 'all' || s.event_type === currentFilters.eventType;
        const strategyMatch = currentFilters.strategy === 'all' || s.strategy === currentFilters.strategy;
        const searchMatch = currentFilters.searchText === '' ||
            s.scenario_id.toLowerCase().includes(currentFilters.searchText) ||
            s.road.toLowerCase().includes(currentFilters.searchText) ||
            s.event_id.toLowerCase().includes(currentFilters.searchText);
        return eventTypeMatch && strategyMatch && searchMatch;
    });
    currentPage = 1;
    renderCurrentView();
    renderPagination();
}

// 根据当前视图模式渲染
function renderCurrentView() {
    if (currentView === 'table') {
        renderScenarios();
    } else {
        renderEventView();
    }
}

// 切换视图模式
function switchView(viewMode) {
    currentView = viewMode;

    // 更新按钮状态
    document.getElementById('tableViewBtn').classList.toggle('active', viewMode === 'table');
    document.getElementById('eventViewBtn').classList.toggle('active', viewMode === 'event');

    // 渲染相应视图
    renderCurrentView();

    // 事件卡片视图不需要分页
    if (viewMode === 'event') {
        document.getElementById('pagination').innerHTML = '';
    } else {
        renderPagination();
    }
}

// 渲染事件卡片视图
function renderEventView() {
    // 更新匹配计数
    document.getElementById('matchedCount').textContent = filteredScenarios.length;
    document.getElementById('totalCount').textContent = allScenarios.length;

    // 按事件分组
    const eventGroups = groupScenariosByEvent(filteredScenarios);

    // 渲染事件卡片
    renderEventCards(eventGroups);
}

// 渲染场景表格
function renderScenarios() {
    // 更新匹配计数
    document.getElementById('matchedCount').textContent = filteredScenarios.length;
    document.getElementById('totalCount').textContent = allScenarios.length;

    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageScenarios = filteredScenarios.slice(start, end);

    if (pageScenarios.length === 0) {
        document.getElementById('scenarioTable').innerHTML = '<div class="empty-state">未找到匹配的场景</div>';
        return;
    }

    const html = `
        <table>
            <thead>
                <tr>
                    <th>场景ID</th>
                    <th>事件类型</th>
                    <th>管控策略</th>
                    <th>道路位置</th>
                    <th>事件时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                ${pageScenarios.map(s => `
                    <tr>
                        <td>${s.scenario_id}</td>
                        <td><span class="badge badge-${getEventTypeClass(s.event_type)}">${getEventTypeDisplay(s.event_type)}</span></td>
                        <td><span class="badge badge-${getStrategyClass(s.strategy)}">${getStrategyDisplay(s.strategy)}</span></td>
                        <td>
                            <strong>${s.road}</strong><br>
                            <small style="color: #666;">${s.location}</small>
                        </td>
                        <td>
                            <div>${s.event_start.split(' ')[1] || s.event_start}</div>
                            <small style="color: #666;">${s.duration_hours}h</small>
                        </td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-info" onclick="openScenarioDetailsModal('${s.scenario_id}')" title="查看场景详情">详情</button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    document.getElementById('scenarioTable').innerHTML = html;
}

// ========== 事件分组功能（批量创建） ==========

/**
 * 按事件分组场景
 * @param {Array} scenarios - 场景列表
 * @returns {Array} - 分组后的事件数组，每个事件包含其所有场景
 */
function groupScenariosByEvent(scenarios) {
    const eventGroups = {};

    scenarios.forEach(scenario => {
        const eventId = scenario.event_id;

        if (!eventGroups[eventId]) {
            eventGroups[eventId] = {
                event_id: eventId,
                event_type: scenario.event_type,
                event_start: scenario.event_start,
                event_end: scenario.event_end,
                duration_hours: scenario.duration_hours,
                road: scenario.road,
                location: scenario.location,
                scenarios: []
            };
        }

        eventGroups[eventId].scenarios.push(scenario);
    });

    return Object.values(eventGroups);
}

/**
 * 渲染事件卡片（用于批量创建）
 * @param {Array} eventGroups - 事件分组数组
 */
function renderEventCards(eventGroups) {
    if (eventGroups.length === 0) {
        document.getElementById('scenarioTable').innerHTML = '<div class="empty-state">未找到匹配的事件</div>';
        return;
    }

    const html = eventGroups.map(event => {
        const scenarios = event.scenarios;
        const hasNoControl = scenarios.some(s => s.strategy === 'NO_CONTROL' || s.strategy === '无管控');
        const hasVSS = scenarios.some(s => s.strategy === 'VSS' || s.strategy === '可变限速标志');
        const hasTEC = scenarios.some(s => s.strategy === 'TEC' || s.strategy === '收费站管控');
        const hasDHS = scenarios.some(s => s.strategy === 'DHS' || s.strategy === '动态硬路肩');

        // 检查该事件下是否已有案例创建
        const hasCreatedCases = scenarios.some(s => {
            const cases = scenarioCaseMap[s.scenario_id] || [];
            return cases.length > 0;
        });

        const createdCount = scenarios.reduce((count, s) => {
            const cases = scenarioCaseMap[s.scenario_id] || [];
            return count + cases.length;
        }, 0);

        return `
            <div class="event-card" data-event-id="${event.event_id}">
                <div class="event-card-header">
                    <div class="event-card-header-left">
                        <div class="event-title">
                            <strong>事件 ${event.event_id}</strong>
                            <span class="badge badge-${getEventTypeClass(event.event_type)}">${getEventTypeDisplay(event.event_type)}</span>
                        </div>
                    </div>
                    <div class="event-card-header-right">
                        ${hasCreatedCases ? `<span class="badge badge-success">${createdCount}个案例已创建</span>` : ''}
                    </div>
                </div>
                <div class="event-card-info">
                    <div class="event-info-item">
                        <strong>道路位置:</strong> ${event.road} - ${event.location}
                    </div>
                    <div class="event-info-item">
                        <strong>事件时间:</strong> ${event.event_start} ~ ${event.event_end} (${event.duration_hours}h)
                    </div>
                    <div class="event-info-item">
                        <strong>可用场景:</strong> ${scenarios.length} 个
                    </div>
                </div>
                <div class="scenario-checkboxes">
                    <div class="scenario-checkbox-group">
                        ${hasNoControl ? `
                        <label class="scenario-checkbox-label">
                            <input type="checkbox" class="scenario-checkbox"
                                   data-event-id="${event.event_id}"
                                   data-scenario-id="${scenarios.find(s => s.strategy === 'NO_CONTROL' || s.strategy === '无管控').scenario_id}"
                                   data-strategy="NO_CONTROL"
                                   checked
                                   onchange="validateScenarioSelection('${event.event_id}')">
                            <span class="badge badge-secondary">无管控</span>
                        </label>
                        ` : ''}
                        ${hasVSS ? `
                        <label class="scenario-checkbox-label">
                            <input type="checkbox" class="scenario-checkbox"
                                   data-event-id="${event.event_id}"
                                   data-scenario-id="${scenarios.find(s => s.strategy === 'VSS' || s.strategy === '可变限速标志').scenario_id}"
                                   data-strategy="VSS"
                                   checked
                                   onchange="validateScenarioSelection('${event.event_id}')">
                            <span class="badge badge-warning">可变限速</span>
                        </label>
                        ` : ''}
                        ${hasTEC ? `
                        <label class="scenario-checkbox-label">
                            <input type="checkbox" class="scenario-checkbox"
                                   data-event-id="${event.event_id}"
                                   data-scenario-id="${scenarios.find(s => s.strategy === 'TEC' || s.strategy === '收费站管控').scenario_id}"
                                   data-strategy="TEC"
                                   checked
                                   onchange="validateScenarioSelection('${event.event_id}')">
                            <span class="badge badge-info">收费站管控</span>
                        </label>
                        ` : ''}
                        ${hasDHS ? `
                        <label class="scenario-checkbox-label">
                            <input type="checkbox" class="scenario-checkbox"
                                   data-event-id="${event.event_id}"
                                   data-scenario-id="${scenarios.find(s => s.strategy === 'DHS' || s.strategy === '动态硬路肩').scenario_id}"
                                   data-strategy="DHS"
                                   checked
                                   onchange="validateScenarioSelection('${event.event_id}')">
                            <span class="badge badge-primary">动态硬路肩</span>
                        </label>
                        ` : ''}
                    </div>
                    <div id="warning_${event.event_id}" class="scenario-warning" style="display: none;">
                        <span class="warning-icon">⚠️</span>
                        <span>建议选择该事件下的所有场景，以生成完整的edgeData配置</span>
                    </div>
                </div>
                <div class="event-card-actions">
                    <button class="btn btn-sm btn-primary batch-create-btn"
                            onclick="batchCreateEventCase('${event.event_id}')"
                            title="批量创建选中的场景案例">
                        批量创建
                    </button>
                    <button class="btn btn-sm btn-secondary preset-btn"
                            onclick="selectAllScenarios('${event.event_id}')"
                            title="选择所有场景">
                        全选
                    </button>
                    <button class="btn btn-sm btn-secondary preset-btn"
                            onclick="deselectAllScenarios('${event.event_id}')"
                            title="取消所有选择">
                        全不选
                    </button>
                    ${hasCreatedCases ? `
                    <button class="btn btn-sm btn-danger"
                            onclick="deleteEventCreatedCases('${event.event_id}', this)"
                            title="删除该事件创建的所有案例"
                            style="margin-left: auto;">
                        🗑️ 删除案例
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('scenarioTable').innerHTML = html;
}

/**
 * 验证场景选择完整性
 * @param {string} eventId - 事件ID
 */
function validateScenarioSelection(eventId) {
    const allCheckboxes = document.querySelectorAll(`.scenario-checkbox[data-event-id="${eventId}"]`);
    const checkedCheckboxes = document.querySelectorAll(`.scenario-checkbox[data-event-id="${eventId}"]:checked`);

    const warningBox = document.getElementById(`warning_${eventId}`);

    if (checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length) {
        // 部分选择 - 显示警告
        warningBox.style.display = 'flex';
    } else {
        // 全选或全不选 - 隐藏警告
        warningBox.style.display = 'none';
    }
}

/**
 * 选择所有场景
 * @param {string} eventId - 事件ID
 */
function selectAllScenarios(eventId) {
    const scenarioCheckboxes = document.querySelectorAll(`.scenario-checkbox[data-event-id="${eventId}"]`);
    scenarioCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    validateScenarioSelection(eventId);
}

/**
 * 取消所有场景选择
 * @param {string} eventId - 事件ID
 */
function deselectAllScenarios(eventId) {
    const scenarioCheckboxes = document.querySelectorAll(`.scenario-checkbox[data-event-id="${eventId}"]`);
    scenarioCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    validateScenarioSelection(eventId);
}

/**
 * 全局变量: 存储待创建的批量请求信息
 */
let pendingBatchCreationRequest = null;

/**
 * 批量创建事件案例 - 显示确认模态框
 * @param {string} eventId - 事件ID
 */
async function batchCreateEventCase(eventId) {
    const checkedCheckboxes = document.querySelectorAll(`.scenario-checkbox[data-event-id="${eventId}"]:checked`);

    if (checkedCheckboxes.length === 0) {
        alert('请至少选择一个场景');
        return;
    }

    // 获取选中的场景信息
    const selectedScenarios = [];
    for (const checkbox of checkedCheckboxes) {
        const scenarioId = checkbox.dataset.scenarioId;
        const scenario = allScenarios.find(s => s.scenario_id === scenarioId);
        if (scenario) {
            selectedScenarios.push(scenario);
        }
    }

    if (selectedScenarios.length === 0) {
        alert('未找到选中的场景信息');
        return;
    }

    // 提取所有场景的参数
    try {
        const scenarioParams = [];
        for (const scenario of selectedScenarios) {
            const params = await extractScenarioParameters(scenario);
            scenarioParams.push(params);
        }

        // 保存请求信息供确认时使用
        const eventInfo = selectedScenarios[0];
        const strategyList = scenarioParams.map(p => getStrategyDisplay(p.strategy)).join(', ');

        pendingBatchCreationRequest = {
            event_id: eventId,
            event_type: mapEventTypeToFolder(eventInfo.event_type),
            scenarios: scenarioParams,
            network_file: "templates/network_files/sichuan202508v7.net.xml",
            od_file: "dwd.dwd_od_weekly",
            taz_file: "templates/taz_files/TAZ_6.add.xml",
            time_range: {
                start_time: scenarioParams[0].time.sim_start_time,
                end_time: scenarioParams[0].time.sim_end_time
            },
            simulation_type: "microscopic",
            random_seed: null
        };

        // 显示确认模态框
        showBatchCreationModal(eventId, eventInfo, scenarioParams, selectedScenarios.length, strategyList);

    } catch (error) {
        console.error('批量创建失败:', error);
        alert(`✗ 准备批量创建失败: ${error.message}`);
    }
}

/**
 * 显示批量创建确认模态框
 */
function showBatchCreationModal(eventId, eventInfo, scenarioParams, scenarioCount, strategyList) {
    // 填充确认信息
    document.getElementById('batchCreation_eventId').textContent = eventId;
    document.getElementById('batchCreation_eventType').textContent = getEventTypeDisplay(eventInfo.event_type);
    document.getElementById('batchCreation_location').textContent = eventInfo.road || '未指定';
    document.getElementById('batchCreation_scenarioCount').textContent = scenarioCount;
    document.getElementById('batchCreation_strategies').textContent = strategyList;

    // 显示确认阶段，隐藏其他阶段
    document.getElementById('batchCreation_confirmPhase').style.display = 'block';
    document.getElementById('batchCreation_processingPhase').style.display = 'none';
    document.getElementById('batchCreation_completePhase').style.display = 'none';
    document.getElementById('batchCreation_confirmButtons').style.display = 'flex';
    document.getElementById('batchCreation_completeButtons').style.display = 'none';

    // 打开模态框
    showModal('batchCreationModal');
}

/**
 * 确认批量创建 - 执行API调用
 */
async function confirmBatchCreation() {
    if (!pendingBatchCreationRequest) {
        alert('请求信息丢失，请重试');
        return;
    }

    // 切换到进行中阶段
    document.getElementById('batchCreation_confirmPhase').style.display = 'none';
    document.getElementById('batchCreation_processingPhase').style.display = 'block';

    try {
        // 调用批量创建API
        const response = await fetch('/api/v1/scenario/create-case-batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(pendingBatchCreationRequest)
        });

        if (response.ok) {
            const result = await response.json();

            // 显示完成阶段
            showBatchCreationComplete(result);

            // 刷新数据
            loadCreatedCases();
            applyFilters();

        } else {
            const error = await response.json();
            showBatchCreationError(`${error.detail || error.message || '未知错误'}`);
        }

    } catch (error) {
        console.error('批量创建失败:', error);
        showBatchCreationError(error.message);
    }
}

/**
 * 显示批量创建完成信息
 */
function showBatchCreationComplete(result) {
    // 隐藏进行中，显示完成
    document.getElementById('batchCreation_processingPhase').style.display = 'none';
    document.getElementById('batchCreation_completePhase').style.display = 'block';
    document.getElementById('batchCreation_confirmButtons').style.display = 'none';
    document.getElementById('batchCreation_completeButtons').style.display = 'flex';

    // 填充完成信息
    document.getElementById('batchCreation_caseId').textContent = result.case_id;
    document.getElementById('batchCreation_completeEventId').textContent = result.event_id;
    document.getElementById('batchCreation_successCount').textContent = result.successful_scenarios;
    document.getElementById('batchCreation_totalCount').textContent = result.total_scenarios;
    document.getElementById('batchCreation_failCount').textContent = result.failed_scenarios;
    document.getElementById('batchCreation_duration').textContent = (result.duration_seconds || 0).toFixed(2);

    // EdgeData信息 - 使用详细的decision_action如果可用
    const edgeDataInfo = result.edgedata_info || {};
    const edgeCountElement = document.getElementById('batchCreation_edgeCount');
    const validationRateElement = document.getElementById('batchCreation_validationRate');
    const edgeDataStatusElement = document.getElementById('batchCreation_edgeDataStatus');

    // 更新边缘数
    if (edgeCountElement) {
        const edgeCount = edgeDataInfo.edge_count || 0;
        edgeCountElement.textContent = edgeCount;
        // 调试日志
        if (edgeCount === 0) {
            console.warn('⚠️ EdgeData边缘数为0，检查edgedata_info:', edgeDataInfo);
        }
    }

    // 更新验证率
    if (validationRateElement) {
        const validationRate = edgeDataInfo.validation_rate !== undefined ? edgeDataInfo.validation_rate : 0;
        validationRateElement.textContent = `${(validationRate * 100).toFixed(1)}%`;
    }

    // 更新输出状态
    if (edgeDataStatusElement) {
        let statusText = '';
        let statusColor = '#999999';  // 默认灰色

        // 优先使用decision_action（包含详细信息）
        if (edgeDataInfo.decision_action && edgeDataInfo.decision_action.trim()) {
            statusText = edgeDataInfo.decision_action;
        } else if (edgeDataInfo.should_enable !== undefined) {
            // 使用should_enable标志
            statusText = edgeDataInfo.should_enable ? '✓ 启用输出' : '✗ 禁用输出';
        } else if (result.edgedata_info === undefined || result.edgedata_info === null) {
            // edgedata_info为空
            statusText = '⚠️ 未生成EdgeData配置';
        } else {
            statusText = '⚠️ 未知状态';
        }

        edgeDataStatusElement.textContent = statusText;

        // 设置颜色编码
        if (edgeDataInfo.should_enable === true) {
            statusColor = '#28a745';  // 绿色 - 启用
        } else if (edgeDataInfo.should_enable === false) {
            statusColor = '#dc3545';  // 红色 - 禁用
        }
        edgeDataStatusElement.style.color = statusColor;

        // 调试日志
        console.log('EdgeData显示信息:', {
            statusText: statusText,
            statusColor: statusColor,
            edgeDataInfo: edgeDataInfo,
            should_enable: edgeDataInfo.should_enable,
            decision_action: edgeDataInfo.decision_action
        });
    }

    // 显示失败详情（如果有失败）
    if (result.failed_scenarios > 0) {
        const failedDetails = result.scenario_results
            .filter(r => !r.success)
            .map(r => `<div style="margin-bottom: 5px;">• ${r.scenario_id}: ${r.error_message || '未知错误'}</div>`)
            .join('');

        document.getElementById('batchCreation_failedList').innerHTML = failedDetails;
        document.getElementById('batchCreation_failedDetails').style.display = 'block';
    } else {
        document.getElementById('batchCreation_failedDetails').style.display = 'none';
    }

    // 启动OD状态轮询
    if (result.case_id) {
        startOdStatusPolling(result.case_id);
    }
}

/**
 * 显示批量创建错误
 */
function showBatchCreationError(errorMsg) {
    // 隐藏进行中，显示确认（返回到确认界面）
    document.getElementById('batchCreation_processingPhase').style.display = 'none';
    document.getElementById('batchCreation_confirmPhase').style.display = 'block';
    document.getElementById('batchCreation_confirmButtons').style.display = 'flex';

    alert(`✗ 批量创建失败: ${errorMsg}`);
}

/**
 * 关闭批量创建模态框
 */
function closeBatchCreationModal() {
    closeModal('batchCreationModal');
    pendingBatchCreationRequest = null;
    // 停止OD状态轮询（如果正在进行）
    if (odStatusPollingInterval) {
        clearInterval(odStatusPollingInterval);
        odStatusPollingInterval = null;
    }
}

/**
 * 删除该事件的所有case文件夹（并清除scenario_index.json中的关联）
 * @param {string} eventId - 事件ID
 * @param {HTMLElement} deleteBtn - 删除按钮元素
 */
async function deleteEventCreatedCases(eventId, deleteBtn) {
    try {
        // 加载scenario_index.json获取确认信息
        const response = await fetch('/output/scenarios/scenario_index.json');
        const data = await response.json();

        // 找出该事件对应的所有scenarios信息
        const scenariosInfo = [];
        let totalCasesCount = 0;

        for (const scenario of data.scenarios || []) {
            if (scenario.event_id == eventId && scenario.created_cases && scenario.created_cases.length > 0) {
                scenariosInfo.push({
                    scenario_id: scenario.scenario_id,
                    case_count: scenario.created_cases.length
                });
                totalCasesCount += scenario.created_cases.length;
            }
        }

        if (scenariosInfo.length === 0) {
            alert('⚠️ 该事件没有已创建的案例');
            return;
        }

        // 确认删除
        const scenarioSummary = scenariosInfo
            .map(s => `${s.scenario_id} (${s.case_count}个案例)`)
            .join('\n');

        const confirmed = confirm(
            `⚠️ 确认要删除事件 "${eventId}" 的所有案例文件夹吗？\n\n` +
            `将删除以下场景的案例：\n${scenarioSummary}\n\n` +
            `总共 ${totalCasesCount} 个案例文件夹将被删除\n\n` +
            `此操作不可撤销！`
        );

        if (!confirmed) {
            return;
        }

        // 显示删除进度
        const originalText = deleteBtn.textContent;
        deleteBtn.disabled = true;
        deleteBtn.textContent = '⏳ 删除中...';
        deleteBtn.style.opacity = '0.6';

        // 调用API删除该事件的所有case文件夹
        try {
            const deleteResponse = await fetch(`/api/v1/batch/delete-event-cases/${eventId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const deleteResult = await deleteResponse.json();

            if (deleteResponse.ok && deleteResult.success) {
                alert(deleteResult.message);
                refreshData();  // 刷新页面数据
            } else {
                throw new Error(deleteResult.message || '删除失败');
            }
        } catch (error) {
            console.error('删除出错:', error);
            alert(`❌ 删除失败: ${error.message}`);
            deleteBtn.disabled = false;
            deleteBtn.textContent = originalText;
            deleteBtn.style.opacity = '1';
        }
    } catch (error) {
        console.error('获取信息出错:', error);
        alert(`❌ 操作失败: ${error.message}`);
    }
}

// 全局变量：OD状态轮询相关
let odStatusPollingInterval = null;
let currentPollingCaseId = null;

/**
 * 启动OD状态轮询
 * 在批量创建API返回后启动，每5秒检查一次OD生成状态
 */
async function startOdStatusPolling(caseId) {
    currentPollingCaseId = caseId;

    // 清除旧的轮询（如果有）
    if (odStatusPollingInterval) {
        clearInterval(odStatusPollingInterval);
    }

    // 立即执行一次检查
    await pollOdStatus();

    // 每5秒轮询一次
    odStatusPollingInterval = setInterval(pollOdStatus, 5000);
}

/**
 * 轮询检查OD生成状态和EdgeData信息
 */
async function pollOdStatus() {
    if (!currentPollingCaseId) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/case/${currentPollingCaseId}/od-status`);

        if (response.ok) {
            const data = await response.json();
            const status = data.data; // 从BaseResponse中获取data字段

            // 更新模态框显示的OD状态
            updateOdStatusDisplay(status);

            // 同时刷新EdgeData信息（确保显示最新的metadata状态）
            await pollEdgeDataInfo();

            // 如果overall_status为ready，停止轮询（表示OD和SUMOCFG都完成）
            if (status.overall_status === 'ready') {
                if (odStatusPollingInterval) {
                    clearInterval(odStatusPollingInterval);
                    odStatusPollingInterval = null;
                }

                // 通知用户OD已准备就绪
                const odStatusElement = document.getElementById('batchCreation_odStatus');
                if (odStatusElement) {
                    odStatusElement.innerHTML = `<span style="color: #28a745;">✓ OD数据和SUMOCFG已就绪，可以启动仿真</span>`;
                }
            }
        }
    } catch (error) {
        console.error('检查OD状态失败:', error);
    }
}

/**
 * 轮询检查EdgeData信息
 * 从case metadata中获取最新的EdgeData配置
 */
async function pollEdgeDataInfo() {
    if (!currentPollingCaseId) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/case/${currentPollingCaseId}`);

        if (response.ok) {
            const data = await response.json();
            const caseMetadata = data.data || data;

            // 从metadata中提取edgedata_config
            const edgeDataConfig = caseMetadata.edgedata_config;

            if (edgeDataConfig) {
                updateEdgeDataDisplay(edgeDataConfig);
            }
        }
    } catch (error) {
        // 静默处理（EdgeData必然存在，不需要特殊错误处理）
        console.debug('刷新EdgeData信息失败 (这是正常的):', error);
    }
}

/**
 * 更新EdgeData显示信息
 * 从metadata中获取最新的EdgeData配置并更新UI
 */
function updateEdgeDataDisplay(edgeDataConfig) {
    if (!edgeDataConfig) return;

    // 更新边缘数
    const edgeCountElement = document.getElementById('batchCreation_edgeCount');
    if (edgeCountElement) {
        edgeCountElement.textContent = edgeDataConfig.edge_count || 0;
    }

    // 更新验证率
    const validationRateElement = document.getElementById('batchCreation_validationRate');
    if (validationRateElement) {
        const rate = edgeDataConfig.validation_rate || 0;
        validationRateElement.textContent = `${(rate * 100).toFixed(1)}%`;
    }

    // 更新输出状态
    const edgeDataStatusElement = document.getElementById('batchCreation_edgeDataStatus');
    if (edgeDataStatusElement) {
        // 使用decision_action如果可用（包含更详细的信息），否则使用简单的启用/禁用
        if (edgeDataConfig.decision_action) {
            edgeDataStatusElement.textContent = edgeDataConfig.decision_action;
            // 根据should_enable设置样式
            if (edgeDataConfig.should_enable) {
                edgeDataStatusElement.style.color = '#28a745';
            } else {
                edgeDataStatusElement.style.color = '#dc3545';
            }
        } else {
            edgeDataStatusElement.textContent = edgeDataConfig.should_enable ? '✓ 启用输出' : '✗ 禁用输出';
            edgeDataStatusElement.style.color = edgeDataConfig.should_enable ? '#28a745' : '#dc3545';
        }
    }
}

/**
 * 更新模态框中的OD状态显示 - 简化版
 *
 * 只显示两种状态：
 * 1. processing - 处理中（OD生成 + SUMOCFG生成）
 * 2. ready - 就绪（OD完成 + 所有SUMOCFG都存在）
 * 3. failed - 失败
 */
function updateOdStatusDisplay(status) {
    const odStatusElement = document.getElementById('batchCreation_odStatus');

    if (!odStatusElement) {
        return;
    }

    let statusHtml = '';
    const overall = status.overall_status || 'processing';

    if (overall === 'failed') {
        // 生成失败
        statusHtml = `
            <div>
                <span style="color: #dc3545;">✗ OD数据生成失败</span>
                <div style="margin-top: 5px; font-size: 12px; color: #666;">
                    ${status.error ? `<div>• 错误: ${status.error}</div>` : ''}
                </div>
            </div>
        `;
    } else if (overall === 'processing') {
        // 处理中（OD生成 + SUMOCFG生成）
        statusHtml = `
            <div>
                <span style="color: #ff6b6b;">⏳ OD数据和SUMOCFG文件生成进行中...</span>
                <div style="margin-top: 5px; font-size: 12px; color: #666;">
                    <div>• 状态: 处理中，请稍候...</div>
                </div>
            </div>
        `;
    } else if (overall === 'ready') {
        // 完全就绪
        statusHtml = `
            <div>
                <span style="color: #28a745;">✓ OD数据和SUMOCFG已就绪</span>
                <div style="margin-top: 5px; font-size: 12px; color: #666;">
                    <div>• OD生成: ✓ 完成</div>
                    <div>• SUMOCFG文件: ✓ 全部就绪</div>
                    <div style="color: #28a745; margin-top: 8px; font-weight: bold;">✓ 可以启动仿真</div>
                    ${status.generated_at ? `<div style="margin-top: 5px; color: #999; font-size: 11px;">完成时间: ${new Date(status.generated_at).toLocaleString()}</div>` : ''}
                </div>
            </div>
        `;
    }

    odStatusElement.innerHTML = statusHtml;
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredScenarios.length / pageSize);
    if (totalPages <= 1) {
        document.getElementById('pagination').innerHTML = '';
        return;
    }

    let html = `<button onclick="previousPage()" ${currentPage === 1 ? 'disabled' : ''}>← 上一页</button>`;
    for (let i = 1; i <= totalPages; i++) {
        html += `<button onclick="goToPage(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
    }
    html += `<button onclick="nextPage()" ${currentPage === totalPages ? 'disabled' : ''}>下一页 →</button>`;
    document.getElementById('pagination').innerHTML = html;
}

// 分页函数
function goToPage(page) {
    currentPage = page;
    renderScenarios();
    renderPagination();
}

function previousPage() {
    if (currentPage > 1) goToPage(currentPage - 1);
}

function nextPage() {
    const totalPages = Math.ceil(filteredScenarios.length / pageSize);
    if (currentPage < totalPages) goToPage(currentPage + 1);
}

// 打开分析模态框
function openAnalysisModal(scenarioId, eventType, strategy) {
    currentScenario = allScenarios.find(s => s.scenario_id === scenarioId);
    if (!currentScenario) {
        alert('未找到场景信息');
        return;
    }

    document.getElementById('analysisScenarioId').value = scenarioId;
    document.getElementById('analysisEventType').value = getEventTypeDisplay(eventType);
    document.getElementById('analysisControlStrategy').value = getStrategyDisplay(strategy);
    showModal('analysisModal');
}

// 提交分析
async function submitAnalysis() {
    if (!currentScenario) {
        alert('请先选择场景');
        return;
    }

    const caseName = document.getElementById('analysisCaseName').value;
    // 映射中文事件类型到英文文件夹名称
    const mappedEventTypeForAnalysis = mapEventTypeToFolder(currentScenario.event_type);

    const analysisConfig = {
        case_name: caseName || `analysis_${currentScenario.scenario_id}_${Date.now()}`,
        scenario_id: currentScenario.scenario_id,
        event_id: currentScenario.event_id,
        event_type: mappedEventTypeForAnalysis,
        control_strategy: currentScenario.strategy,
        compare_no_control: document.getElementById('compareNoControl').checked,
        analysis_focus: {
            edgedata: document.getElementById('analyzeEdgeData').checked,
            tripinfo: document.getElementById('analyzeTripInfo').checked
        }
    };

    try {
        const response = await fetch('/api/v1/scenario/run-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(analysisConfig)
        });

        if (response.ok) {
            const result = await response.json();
            alert(`✅ 仿真分析已启动！\n\n案例: ${analysisConfig.case_name}\n分析ID: ${result.analysis_id || '处理中'}\n\n您可以在任务管理中查看进度`);
            closeModal('analysisModal');
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'API调用失败');
        }
    } catch (error) {
        console.error('启动分析失败:', error);
        alert('启动分析失败: ' + error.message);
    }
}

// CSV文件上传相关函数
function openUploadCsvModal() {
    showModal('uploadCsvModal');
    // 这里可以加载CSV文件列表（后端支持时）
    setTimeout(() => {
        loadCsvFileList();
    }, 100);
}

async function loadCsvFileList() {
    try {
        const response = await fetch('/api/v1/scenario/list-csv-files');
        if (response.ok) {
            const data = await response.json();
            const fileSelect = document.getElementById('csvFileSelect');
            if (fileSelect && data.files) {
                const options = data.files.map(file =>
                    `<option value="${file}">${file}</option>`
                ).join('');
                fileSelect.innerHTML = '<option value="">-- 从events文件夹加载可用文件 --</option>' + options;
            }
        }
    } catch (error) {
        console.log('无法加载CSV文件列表（功能实现中）:', error);
    }
}

async function submitCsvUpload() {
    const csvFile = document.getElementById('csvFileSelect').value;
    const generateAllStrategies = document.getElementById('generateAllStrategies').checked;

    if (!csvFile) {
        alert('请选择CSV文件');
        return;
    }

    const uploadConfig = {
        csv_file: csvFile,
        generate_all_strategies: generateAllStrategies
    };

    try {
        // 显示进度提示
        alert(`🔄 场景生成已提交\n\nCSV文件: ${csvFile}\n策略类型: ${generateAllStrategies ? '全部策略（VSS/DHS/TEC）' : '无管控基础场景'}\n\n后端处理中，请稍候...`);

        const response = await fetch('/api/v1/scenario/generate-from-csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(uploadConfig)
        });

        if (response.ok) {
            const result = await response.json();
            alert(`✅ 场景生成完成！\n\n生成场景数: ${result.generated_count || '处理中'}\n任务ID: ${result.task_id || '自动跟踪'}\n\n请刷新页面查看新增场景`);
            closeModal('uploadCsvModal');
            // 5秒后自动刷新数据
            setTimeout(() => {
                refreshData();
            }, 3000);
        } else {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'API调用失败');
        }
    } catch (error) {
        console.error('生成场景失败:', error);
        // 标记为后续任务
        alert(`⚠️ 场景生成功能实现中\n\n错误: ${error.message}\n\n该功能将在下一阶段实现：\n✓ 后端CSV处理服务开发\n✓ 批量场景生成API\n✓ 进度监控系统`);
    }
}

// 模态框控制
function showModal(id) {
    document.getElementById(id).classList.add('show');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

// 事件监听
function setupEventListeners() {
    document.getElementById('searchBox').addEventListener('input', (e) => {
        currentFilters.searchText = e.target.value.toLowerCase();
        applyFilters();
    });

    // 点击模态框背景关闭
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    // CSV文件选择框启用按钮
    const csvFileSelect = document.getElementById('csvFileSelect');
    if (csvFileSelect) {
        csvFileSelect.addEventListener('change', (e) => {
            const uploadBtn = document.getElementById('uploadCsvBtn');
            if (uploadBtn) {
                uploadBtn.disabled = !e.target.value;
            }
        });
    }
}

// 刷新数据
async function refreshData() {
    await loadCreatedCases();  // 重新加载案例状态
    await loadScenarios();      // 重新加载场景数据
}

// 健康检查
async function checkHealth() {
    try {
        // 首先尝试获取场景服务的健康状态
        const scenarioResponse = await fetch('/api/v1/scenario/health');
        if (scenarioResponse.ok) {
            const data = await scenarioResponse.json();
            alert(`后端健康检查 ✅\n\n场景服务\n状态: ${data.status}\n场景数: ${data.scenario_count}\n\nAPI 地址: ${data.index_path}`);
        } else {
            // 降级：检查全局API健康状态
            const apiResponse = await fetch('/api/v1/health');
            const data = await apiResponse.json();
            alert(`后端健康检查 ✅\n\nAPI 状态: ${data.status}\n\n场景数据: ${allScenarios.length} (已缓存)`);
        }
    } catch (error) {
        console.error('健康检查失败:', error);
        // 降级：显示本地加载的数据
        alert(`后端连接状态\n\n✓ 场景数据已加载: ${allScenarios.length} 个\n✓ 应用正常运行\n\n错误: ${error.message}`);
    }
}

// 辅助函数
function getEventTypeDisplay(type) {
    const map = {
        '交通事故': '交通事故',
        '交通阻塞': '交通阻塞',
        '交通管制': '交通管制',
        '地质灾害': '地质灾害',
        '车辆故障': '路面异常',  // 前端显示别名
        '恶劣天气': '恶劣天气',
        '流量激增工况': '流量激增工况'
    };
    return map[type] || type;
}

function getEventTypeClass(type) {
    const map = {
        '交通事故': 'accident',
        '交通阻塞': 'congestion',
        '交通管制': 'control',
        '地质灾害': 'geological',
        '车辆故障': 'breakdown',
        '恶劣天气': 'weather',
        '流量激增工况': 'traffic-surge'
    };
    return map[type] || 'control';
}

function getStrategyDisplay(strategy) {
    const map = {
        'VSS': 'VSS (动态限速)',
        'TEC': 'TEC (收费管控)',
        'DHS': 'DHS (动态硬路肩)',
        'NO_CONTROL': '无管控'
    };
    return map[strategy] || strategy;
}

function getStrategyClass(strategy) {
    const map = {
        'VSS': 'vss',
        'TEC': 'tec',
        'DHS': 'dhs',
        'NO_CONTROL': 'no-control'
    };
    return map[strategy] || 'no-control';
}

// ========== 状态轮询和通知相关函数 ==========

/**
 * 启动案例状态轮询
 * 每3秒检查一次案例状态，直到OD生成完成或超时
 * @param {string} caseId - 案例ID
 * @param {string} scenarioId - 场景ID（用于更新状态徽章）
 * @param {number} maxDuration - 最大轮询时间（秒，默认600=10分钟）
 */
function startStatusPolling(caseId, scenarioId, maxDuration = 600) {
    const startTime = Date.now();
    let pollCount = 0;

    const pollInterval = setInterval(async () => {
        pollCount++;
        try {
            // 获取最新的案例状态
            const response = await fetch(`/api/v1/case/${caseId}`);
            if (!response.ok) {
                // API可能不支持单案例查询，尝试列表API
                const listResponse = await fetch(`/api/v1/case/list_cases/?page_size=1`);
                const data = await listResponse.json();
                const caseList = data.data?.cases || data.cases || [];
                const caseData = caseList.find(c => c.case_id === caseId);

                if (!caseData) {
                    console.warn(`无法找到案例: ${caseId}`);
                    return;
                }

                updateCaseStatus(caseId, scenarioId, caseData.status);
                return;
            }

            const caseData = await response.json();
            const newStatus = caseData.data?.status || caseData.status || 'unknown';

            // 更新状态
            updateCaseStatus(caseId, scenarioId, newStatus);

            // 如果状态不再是生成中/处理中，停止轮询
            // processing 和 od_generating 都表示还在进行中，继续轮询
            if (newStatus !== 'od_generating' && newStatus !== 'processing') {
                clearInterval(pollInterval);
                console.log(`✓ 案例 ${caseId} 状态轮询完成，最终状态: ${newStatus}`);

                // 显示完成通知
                if (newStatus === 'created') {
                    showNotification('✓ OD文件已生成完成！案例已就绪，可以创建仿真', 'success');
                } else if (newStatus === 'od_generation_failed') {
                    showNotification('⚠️ OD文件生成失败，请查看详情或重新创建案例', 'error');
                } else if (newStatus === 'failed') {
                    showNotification('⚠️ 案例处理失败，请重新尝试', 'error');
                }
            }

            // 检查超时（防止无限轮询）
            const elapsedSeconds = (Date.now() - startTime) / 1000;
            if (elapsedSeconds > maxDuration) {
                clearInterval(pollInterval);
                console.log(`状态轮询已超时（${maxDuration}秒），停止轮询`);
                // 显示超时提示但不中断用户
                console.warn(`⚠️ 案例 ${caseId} OD生成超过${Math.round(elapsedSeconds / 60)}分钟，请手动检查`);
            }

        } catch (error) {
            console.warn(`状态轮询出错 (第${pollCount}次): ${error.message}`);
            // 继续轮询，不因网络错误中断
        }
    }, 3000); // 每3秒轮询一次

    // 标记轮询已启动
    if (!window.activePolls) {
        window.activePolls = new Set();
    }
    window.activePolls.add(caseId);
    console.log(`✓ 已启动轮询，当前活跃轮询: ${window.activePolls.size}`);
}

/**
 * 更新案例状态在内存和UI中
 * @param {string} caseId - 案例ID
 * @param {string} scenarioId - 场景ID
 * @param {string} newStatus - 新状态
 */
function updateCaseStatus(caseId, scenarioId, newStatus) {
    // 更新内存中的scenarioCaseMap
    if (scenarioCaseMap[scenarioId]) {
        const caseIndex = scenarioCaseMap[scenarioId].findIndex(c => c.case_id === caseId);
        if (caseIndex >= 0) {
            scenarioCaseMap[scenarioId][caseIndex].status = newStatus;
            console.log(`更新状态: ${scenarioId} -> ${caseId} = ${newStatus}`);

            // 刷新表格以显示更新后的状态
            renderScenarios();
        }
    }
}

/**
 * 显示临时通知消息
 * @param {string} message - 消息文本
 * @param {string} type - 消息类型: 'success' | 'error' | 'info' | 'warning'
 * @param {number} duration - 显示时长（毫秒，默认5000）
 */
function showNotification(message, type = 'info', duration = 5000) {
    // 创建通知容器（如果不存在）
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(container);
    }

    // 创建通知元素
    const toast = document.createElement('div');
    const colors = {
        'success': { bg: '#4CAF50', icon: '✓' },
        'error': { bg: '#f44336', icon: '✗' },
        'info': { bg: '#2196F3', icon: 'ℹ' },
        'warning': { bg: '#ff9800', icon: '⚠' }
    };
    const config = colors[type] || colors['info'];

    toast.style.cssText = `
        padding: 12px 20px;
        background-color: ${config.bg};
        color: white;
        border-radius: 6px;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease forwards;
        max-width: 400px;
        word-wrap: break-word;
    `;
    toast.innerHTML = `${config.icon} ${message}`;

    // 添加到容器
    document.getElementById('notification-container').appendChild(toast);

    // 自动移除
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ========== 统一参数提取函数 ==========

/**
 * 统一参数提取函数 - 从场景JSON文件中提取所有创建案例所需的参数
 * 用于批量创建和快速创建，确保参数提取的一致性
 * @param {object} scenario - 场景对象（来自allScenarios）
 * @returns {Promise<object>} - 提取的参数对象
 */
async function extractScenarioParameters(scenario) {
    const scenarioId = scenario.scenario_id;
    const eventType = scenario.event_type || '交通事故';
    const strategy = scenario.strategy || 'NO_CONTROL';

    // 映射事件类型到文件夹
    const eventFolder = mapEventTypeToFolder(eventType);
    const scenarioDir = scenarioId;

    // 初始化参数对象（带默认值）
    const params = {
        scenario_id: scenarioId,
        event_id: scenario.event_id || 'unknown',
        event_type: eventType,
        strategy: strategy,

        // 位置信息（默认值）
        event_location: {
            road: '未知',
            direction: '未知',
            mileage: '未知',
            edge_id: '未知',
            junction_id: '未知'
        },

        // 时间信息（默认值）
        time: {
            event_start_time: '未知',
            event_end_time: '未知',
            event_duration_hours: 0,
            sim_start_time: '未知',
            sim_end_time: '未知',
            sim_duration_hours: 0
        },

        // 输出配置（默认值）
        output_config: {
            generate_edgedata: true,
            generate_summary: true,
            generate_tripinfo: true,
            generate_vehroute: false
        },

        // 管控策略参数（可选）
        control_strategy: null
    };

    // 1. 加载事件描述信息（event_description.json）
    try {
        const eventDescUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/event_description.json`;
        const eventDescResponse = await fetch(eventDescUrl);

        if (eventDescResponse.ok) {
            const eventDesc = await eventDescResponse.json();

            // 填充位置信息
            if (eventDesc.location) {
                params.event_location = {
                    road: eventDesc.location.road || '未知',
                    direction: eventDesc.location.direction || '未知',
                    mileage: eventDesc.location.mileage || '未知',
                    edge_id: eventDesc.location.edge_id || '未知',
                    junction_id: eventDesc.location.junction_id || '未知'
                };
            }
        } else {
            console.warn(`加载event_description.json失败: ${eventDescUrl}`);
        }
    } catch (error) {
        console.warn('加载event_description.json异常:', error);
    }

    // 2. 提取事件时间信息（从scenario对象）
    if (scenario.time && typeof scenario.time === 'object') {
        params.time.event_start_time = scenario.time.start_time || '未知';
        params.time.event_end_time = scenario.time.end_time || '未知';
        params.time.event_duration_hours = scenario.time.duration_hours || 0;
    } else {
        params.time.event_start_time = scenario.event_start || '未知';
        params.time.event_end_time = scenario.event_end || '未知';
        params.time.event_duration_hours = scenario.duration_hours || 0;
    }

    // 3. 加载仿真配置信息（traffic_input_config.json）
    try {
        const trafficConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/traffic_input_config.json`;
        const trafficResponse = await fetch(trafficConfigUrl);

        if (trafficResponse.ok) {
            const trafficConfig = await trafficResponse.json();

            // 填充仿真时间信息
            if (trafficConfig.od_time_range) {
                params.time.sim_start_time = trafficConfig.od_time_range.start || '未知';
                params.time.sim_end_time = trafficConfig.od_time_range.end || '未知';
            }

            // 填充仿真时长
            if (trafficConfig.simulation_duration_hours !== undefined) {
                params.time.sim_duration_hours = trafficConfig.simulation_duration_hours;
            }
        } else {
            console.warn(`加载traffic_input_config.json失败: ${trafficConfigUrl}`);
        }
    } catch (error) {
        console.warn('加载traffic_input_config.json异常:', error);
    }

    // 4. 加载管控策略配置（control_strategy_config.json）
    if (strategy !== 'NO_CONTROL' && strategy !== '无管控') {
        try {
            const strategyConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/control_strategy_config.json`;
            const strategyResponse = await fetch(strategyConfigUrl);

            if (strategyResponse.ok) {
                const strategyConfig = await strategyResponse.json();

                params.control_strategy = {
                    strategy_type: strategyConfig.strategy_type || strategyConfig.strategy_name || '未知',
                    strategy_name: strategyConfig.strategy_name || strategyConfig.strategy_type || '未知',
                    timing: {
                        activation_time: strategyConfig.timing?.activation_time || '未知',
                        deactivation_time: strategyConfig.timing?.deactivation_time || '未知',
                        response_delay_minutes: strategyConfig.timing?.response_delay_minutes || 0
                    },
                    parameters: strategyConfig.parameters || {}
                };
            } else {
                console.warn(`加载control_strategy_config.json失败: ${strategyConfigUrl}`);
            }
        } catch (error) {
            console.warn('加载control_strategy_config.json异常:', error);
        }
    }

    // 5. 验证参数完整性
    const validation = validateParameters(params);
    if (!validation.valid) {
        console.warn('参数验证警告:', validation.warnings);
    }

    return params;
}

/**
 * 验证参数完整性
 * @param {object} params - 参数对象
 * @returns {object} - 验证结果 {valid: boolean, warnings: array}
 */
function validateParameters(params) {
    const warnings = [];

    // 检查必需字段
    if (!params.scenario_id || params.scenario_id === 'unknown') {
        warnings.push('场景ID缺失');
    }

    if (!params.event_id || params.event_id === 'unknown') {
        warnings.push('事件ID缺失');
    }

    if (params.event_location.edge_id === '未知') {
        warnings.push('事件edge_id缺失');
    }

    if (params.time.sim_duration_hours === 0) {
        warnings.push('仿真时长为0或未设置');
    }

    // 检查管控策略参数（如果有管控）
    if (params.strategy !== 'NO_CONTROL' && params.strategy !== '无管控') {
        if (!params.control_strategy) {
            warnings.push('管控策略配置缺失');
        }
    }

    return {
        valid: warnings.length === 0,
        warnings: warnings
    };
}


/**
 * 将中文事件类型映射到英文文件夹名称
 * 映射关系：
 * 交通事故 → 01_accident
 * 交通阻塞 → 02_congestion
 * 交通管制 → 03_road_control
 * 恶劣天气 → 05_breakdown（或 06_weather）
 * 路面异常 → 06_weather
 */
function mapEventTypeToFolder(eventType) {
    const eventTypeMap = {
        '交通事故': '01_accident',
        '交通阻塞': '02_congestion',
        '交通管制': '03_road_control',
        '地质灾害': '04_geological',
        '车辆故障': '05_breakdown',
        '恶劣天气': '06_weather',
        '路面异常': '06_weather',
        '流量激增工况': '07_flowsurge',
        // 备选/兼容名称
        '拥堵': '02_congestion',
        '道路管制': '03_road_control'
    };
    return eventTypeMap[eventType] || '01_accident';
}

/**
 * 打开场景详情模态框
 */
async function openScenarioDetailsModal(scenarioId) {
    // 查找完整的场景信息
    currentScenario = allScenarios.find(s => s.scenario_id === scenarioId);

    if (!currentScenario) {
        alert('错误: 无法找到场景信息');
        return;
    }

    // 打开模态框
    const modal = document.getElementById('scenarioDetailsModal');
    if (modal) {
        modal.style.display = 'flex';
    }

    // 异步加载事件描述文件并填充详情
    try {
        // 构建事件描述文件路径
        // 格式: /output/scenarios/{event_folder}/{scenario_dir}/event_description.json
        // 注意：event_type 是中文，需要映射到英文文件夹名称
        const eventTypeChina = currentScenario.event_type || '交通事故';
        const eventFolder = mapEventTypeToFolder(eventTypeChina);
        const scenarioDir = currentScenario.scenario_id;

        const eventDescUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/event_description.json`;

        const response = await fetch(eventDescUrl);
        let eventDesc = null;

        if (response.ok) {
            eventDesc = await response.json();
        }

        // 填充基本信息
        document.getElementById('scenarioDetails_scenarioId').value = currentScenario.scenario_id || '未知';
        document.getElementById('scenarioDetails_eventId').value = currentScenario.event_id || '未知';
        document.getElementById('scenarioDetails_eventType').value = getEventTypeDisplay(currentScenario.event_type) || currentScenario.event_type || '未知';
        document.getElementById('scenarioDetails_strategy').value = getStrategyDisplay(currentScenario.strategy) || currentScenario.strategy || '未知';

        // 事件描述优先从event_description.json获取
        const description = (eventDesc?.event_description) || currentScenario.description || '暂无描述';
        document.getElementById('scenarioDetails_description').value = description;

        // 填充事件详情（位置信息）
        // 优先使用从event_description.json加载的location数据
        let road = currentScenario.road || '未知';
        let direction = currentScenario.location || '未知';
        let mileage = currentScenario.mileage || '未知';
        let edgeId = currentScenario.edge_id || currentScenario.edgeId || '未知';
        let junctionId = currentScenario.junction_id || currentScenario.junctionId || '未知';

        if (eventDesc && eventDesc.location) {
            road = eventDesc.location.road || road;
            direction = eventDesc.location.direction || direction;
            mileage = eventDesc.location.mileage || mileage;
            edgeId = eventDesc.location.edge_id || edgeId;
            junctionId = eventDesc.location.junction_id || junctionId;
        }

        document.getElementById('scenarioDetails_road').value = road;
        document.getElementById('scenarioDetails_direction').value = direction;
        document.getElementById('scenarioDetails_mileage').value = mileage;
        document.getElementById('scenarioDetails_edgeId').value = edgeId;
        document.getElementById('scenarioDetails_junctionId').value = junctionId;

        // 填充时间信息
        let startTime = '未知';
        let endTime = '未知';
        let duration = '未知';

        if (eventDesc && eventDesc.time) {
            startTime = eventDesc.time.start_time || startTime;
            endTime = eventDesc.time.end_time || endTime;
            duration = eventDesc.time.duration_hours || duration;
        } else if (currentScenario.time && typeof currentScenario.time === 'object') {
            startTime = currentScenario.time.start_time || startTime;
            endTime = currentScenario.time.end_time || endTime;
            duration = currentScenario.time.duration_hours || duration;
        } else {
            startTime = currentScenario.event_start || startTime;
            endTime = currentScenario.event_end || endTime;
            duration = currentScenario.duration_hours || duration;
        }

        document.getElementById('scenarioDetails_startTime').value = startTime;
        document.getElementById('scenarioDetails_endTime').value = endTime;
        document.getElementById('scenarioDetails_duration').value = `${duration}h`;

        // 加载仿真时间信息（从traffic_input_config.json）
        try {
            const trafficConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/traffic_input_config.json`;
            const trafficResponse = await fetch(trafficConfigUrl);

            if (trafficResponse.ok) {
                const trafficConfig = await trafficResponse.json();

                if (trafficConfig.od_time_range) {
                    const simStart = trafficConfig.od_time_range.start || '未知';
                    const simEnd = trafficConfig.od_time_range.end || '未知';

                    document.getElementById('scenarioDetails_simStartTime').value = simStart;
                    document.getElementById('scenarioDetails_simEndTime').value = simEnd;
                } else {
                    document.getElementById('scenarioDetails_simStartTime').value = '未知';
                    document.getElementById('scenarioDetails_simEndTime').value = '未知';
                }

                // 显示仿真时长
                if (trafficConfig.simulation_duration_hours !== undefined) {
                    const durationHours = trafficConfig.simulation_duration_hours;
                    document.getElementById('scenarioDetails_simDuration').value = `${durationHours}小时`;
                } else {
                    document.getElementById('scenarioDetails_simDuration').value = '未知';
                }
            } else {
                document.getElementById('scenarioDetails_simStartTime').value = '配置文件不存在';
                document.getElementById('scenarioDetails_simEndTime').value = '配置文件不存在';
                document.getElementById('scenarioDetails_simDuration').value = '配置文件不存在';
            }
        } catch (trafficError) {
            console.warn('加载traffic_input_config.json失败:', trafficError);
            document.getElementById('scenarioDetails_simStartTime').value = '加载失败';
            document.getElementById('scenarioDetails_simEndTime').value = '加载失败';
            document.getElementById('scenarioDetails_simDuration').value = '加载失败';
        }

        // 加载管控策略详细信息（从control_strategy_config.json）
        try {
            const strategyConfigUrl = `/output/scenarios/${eventFolder}/${scenarioDir}/control_strategy_config.json`;
            const strategyResponse = await fetch(strategyConfigUrl);

            if (strategyResponse.ok) {
                const strategyConfig = await strategyResponse.json();
                const strategyType = strategyConfig.strategy_type || strategyConfig.strategy_name;

                // 如果是NO_CONTROL，隐藏管控策略部分
                if (strategyType === 'NO_CONTROL') {
                    document.getElementById('scenarioDetails_controlStrategySection').style.display = 'none';
                } else {
                    document.getElementById('scenarioDetails_controlStrategySection').style.display = 'block';

                    // 更新策略类型和名称
                    const strategyTypeName = getStrategyDisplay(strategyType);
                    document.getElementById('scenarioDetails_strategyType').value = strategyTypeName;
                    document.getElementById('scenarioDetails_strategyName').value = strategyConfig.strategy_name || strategyTypeName;

                    // 填充时间信息
                    if (strategyConfig.timing) {
                        document.getElementById('scenarioDetails_activationTime').value =
                            strategyConfig.timing.activation_time || '未知';
                        document.getElementById('scenarioDetails_deactivationTime').value =
                            strategyConfig.timing.deactivation_time || '未知';

                        const responseDelay = strategyConfig.timing.response_delay_minutes ||
                                            (strategyConfig.parameters?.response_delay_seconds ?
                                             strategyConfig.parameters.response_delay_seconds / 60 : null);
                        document.getElementById('scenarioDetails_responseDelay').value =
                            responseDelay ? `${responseDelay.toFixed(1)}分钟` : '未知';

                        const recoveryPeriod = strategyConfig.timing.recovery_period_minutes ||
                                             (strategyConfig.parameters?.recovery_period_seconds ?
                                              strategyConfig.parameters.recovery_period_seconds / 60 : null);
                        document.getElementById('scenarioDetails_recoveryPeriod').value =
                            recoveryPeriod ? `${recoveryPeriod.toFixed(1)}分钟` : '未知';
                    } else {
                        document.getElementById('scenarioDetails_activationTime').value = '未知';
                        document.getElementById('scenarioDetails_deactivationTime').value = '未知';
                        document.getElementById('scenarioDetails_responseDelay').value = '未知';
                        document.getElementById('scenarioDetails_recoveryPeriod').value = '未知';
                    }

                    // 填充影响路段和车道信息
                    if (strategyConfig.parameters) {
                        const params = strategyConfig.parameters;
                        const affectedEdges = params.affected_edges || [];
                        const affectedLanes = params.affected_lanes || [];

                        document.getElementById('scenarioDetails_affectedEdges').value =
                            affectedEdges.length > 0 ? affectedEdges.join(', ') : '未知';
                        document.getElementById('scenarioDetails_affectedLanes').value =
                            affectedLanes.length > 0 ? affectedLanes.join(', ') : '未知';

                        // 隐藏所有策略特定参数区域
                        document.getElementById('scenarioDetails_vssParams').style.display = 'none';
                        document.getElementById('scenarioDetails_tecParams').style.display = 'none';
                        document.getElementById('scenarioDetails_dhsParams').style.display = 'none';

                        // 根据策略类型显示和填充相应的参数
                        if (strategyType === 'VSS') {
                            // VSS 特定参数
                            document.getElementById('scenarioDetails_vssParams').style.display = 'grid';
                            const speedLimit = params.speed_limit_kmh || params.speed_limit || '未知';
                            document.getElementById('scenarioDetails_speedLimit').value =
                                speedLimit !== '未知' ? `${speedLimit} km/h` : speedLimit;

                        } else if (strategyType === 'TEC') {
                            // TEC 特定参数
                            document.getElementById('scenarioDetails_tecParams').style.display = 'grid';

                            // 流量削减率
                            if (params.flow_reduction !== undefined) {
                                const reductionPercent = (params.flow_reduction * 100).toFixed(0);
                                document.getElementById('scenarioDetails_flowReduction').value =
                                    `${reductionPercent}% (削减比例: ${params.flow_reduction})`;
                            } else {
                                document.getElementById('scenarioDetails_flowReduction').value = '未知';
                            }

                            // 入口路段
                            const entranceEdges = params.entrance_edges || [];
                            document.getElementById('scenarioDetails_entranceEdges').value =
                                entranceEdges.length > 0 ? entranceEdges.join(', ') : '未设置';

                            // 是否执行管控
                            if (params.csv_control !== undefined) {
                                document.getElementById('scenarioDetails_csvControl').value =
                                    params.csv_control ? '是' : '否';
                            } else {
                                document.getElementById('scenarioDetails_csvControl').value = '未设置';
                            }

                        } else if (strategyType === 'DHS') {
                            // DHS 特定参数
                            document.getElementById('scenarioDetails_dhsParams').style.display = 'grid';

                            // 硬路肩车道
                            const shoulderLanes = params.shoulder_lanes || [];
                            document.getElementById('scenarioDetails_shoulderLanes').value =
                                shoulderLanes.length > 0 ? shoulderLanes.join(', ') : '未设置';
                        }
                    } else {
                        document.getElementById('scenarioDetails_affectedEdges').value = '未知';
                        document.getElementById('scenarioDetails_affectedLanes').value = '未知';
                        // 隐藏所有策略特定参数区域
                        document.getElementById('scenarioDetails_vssParams').style.display = 'none';
                        document.getElementById('scenarioDetails_tecParams').style.display = 'none';
                        document.getElementById('scenarioDetails_dhsParams').style.display = 'none';
                    }
                }

                // 构建策略参数详情（仅当不是NO_CONTROL时）
                let strategyDetails = [];

                if (strategyType !== 'NO_CONTROL' && strategyConfig.parameters) {
                    const params = strategyConfig.parameters;

                    // 策略特定参数 (优先显示)
                    strategyDetails.push('╔═══════════════════════════════════════════╗');
                    strategyDetails.push('║          策略特定参数                      ║');
                    strategyDetails.push('╚═══════════════════════════════════════════╝');
                    strategyDetails.push('');

                    // VSS特定参数
                    if (params.speed_limit_kmh !== undefined || params.speed_limit !== undefined) {
                        const speedLimit = params.speed_limit_kmh || params.speed_limit;
                        strategyDetails.push(`【可变限速标志 VSS】`);
                        strategyDetails.push(`  ▪ 限速值: ${speedLimit} km/h`);
                        strategyDetails.push(`  ▪ 说明: 在事件发生时自动降低车辆速度限制，提高安全性`);
                        strategyDetails.push('');
                    }

                    // TEC特定参数
                    if (params.flow_reduction !== undefined) {
                        const reductionPercent = (params.flow_reduction * 100).toFixed(0);
                        strategyDetails.push(`【收费站管控 TEC】`);
                        strategyDetails.push(`  ▪ 流量削减率: ${reductionPercent}%`);
                        strategyDetails.push(`  ▪ 削减方式: 通过提高收费或限制通行来减少车流`);

                        if (params.entrance_edges && params.entrance_edges.length > 0) {
                            strategyDetails.push(`  ▪ 管控入口路段: ${params.entrance_edges.join(', ')}`);
                        }

                        if (params.csv_control !== undefined) {
                            strategyDetails.push(`  ▪ 是否执行管控: ${params.csv_control ? '是' : '否'}`);
                        }
                        strategyDetails.push('');
                    }

                    // DHS特定参数
                    if (params.shoulder_lanes && params.shoulder_lanes.length > 0) {
                        strategyDetails.push(`【动态硬路肩 DHS】`);
                        strategyDetails.push(`  ▪ 可用硬路肩车道: ${params.shoulder_lanes.join(', ')}`);
                        strategyDetails.push(`  ▪ 说明: 在拥堵时开放硬路肩作为临时车道`);
                        strategyDetails.push('');
                    }

                    // 基本配置参数
                    strategyDetails.push('╔═══════════════════════════════════════════╗');
                    strategyDetails.push('║          基本配置参数                      ║');
                    strategyDetails.push('╚═══════════════════════════════════════════╝');
                    strategyDetails.push('');

                    if (params.affected_edges && params.affected_edges.length > 0) {
                        strategyDetails.push(`【影响范围】`);
                        strategyDetails.push(`  ▪ 影响路段数量: ${params.affected_edges.length}个`);
                        strategyDetails.push(`  ▪ 路段ID列表: ${params.affected_edges.join(', ')}`);
                    }

                    if (params.affected_lanes && params.affected_lanes.length > 0) {
                        strategyDetails.push(`  ▪ 影响车道数量: ${params.affected_lanes.length}条`);
                        strategyDetails.push(`  ▪ 车道ID列表: ${params.affected_lanes.join(', ')}`);
                    }

                    strategyDetails.push('');
                    strategyDetails.push(`【时间参数】`);

                    if (params.response_delay_seconds !== undefined) {
                        const delayMinutes = (params.response_delay_seconds / 60).toFixed(1);
                        strategyDetails.push(`  ▪ 响应延迟: ${params.response_delay_seconds}秒 (${delayMinutes}分钟)`);
                        strategyDetails.push(`    └─ 从事件发生到策略启动的延迟时间`);
                    }

                    if (params.recovery_period_seconds !== undefined) {
                        const recoveryMinutes = (params.recovery_period_seconds / 60).toFixed(1);
                        strategyDetails.push(`  ▪ 恢复期: ${params.recovery_period_seconds}秒 (${recoveryMinutes}分钟)`);
                        strategyDetails.push(`    └─ 从策略结束到完全恢复正常的时间`);
                    }

                    // 时间配置详情
                    if (strategyConfig.timing) {
                        strategyDetails.push('');
                        strategyDetails.push('╔═══════════════════════════════════════════╗');
                        strategyDetails.push('║          时间配置详情                      ║');
                        strategyDetails.push('╚═══════════════════════════════════════════╝');
                        strategyDetails.push('');

                        if (strategyConfig.timing.activation_time) {
                            strategyDetails.push(`  ▪ 策略启动时间: ${strategyConfig.timing.activation_time}`);
                        }

                        if (strategyConfig.timing.deactivation_time) {
                            strategyDetails.push(`  ▪ 策略结束时间: ${strategyConfig.timing.deactivation_time}`);
                        }

                        if (strategyConfig.timing.response_delay_minutes !== undefined) {
                            strategyDetails.push(`  ▪ 响应延迟: ${strategyConfig.timing.response_delay_minutes}分钟`);
                        }

                        if (strategyConfig.timing.recovery_period_minutes !== undefined) {
                            strategyDetails.push(`  ▪ 恢复期: ${strategyConfig.timing.recovery_period_minutes}分钟`);
                        }
                    }

                    // 其他参数和说明
                    if (params.description) {
                        strategyDetails.push('');
                        strategyDetails.push('╔═══════════════════════════════════════════╗');
                        strategyDetails.push('║          策略说明                          ║');
                        strategyDetails.push('╚═══════════════════════════════════════════╝');
                        strategyDetails.push('');
                        strategyDetails.push(params.description);
                    }
                }

                document.getElementById('scenarioDetails_strategyParams').value =
                    strategyDetails.length > 0 ? strategyDetails.join('\n') : '暂无参数信息';
            } else {
                // 配置文件不存在，隐藏管控策略部分
                console.warn('control_strategy_config.json 不存在');
                document.getElementById('scenarioDetails_controlStrategySection').style.display = 'none';
            }
        } catch (strategyError) {
            console.warn('加载control_strategy_config.json失败:', strategyError);
            // 加载失败，隐藏管控策略部分
            document.getElementById('scenarioDetails_controlStrategySection').style.display = 'none';
        }

        // 填充事件影响（影响车道）
        let impactDesc = '暂无详细影响信息';
        if (eventDesc && eventDesc.impact) {
            // 构建影响描述
            let impactParts = [];
            if (eventDesc.impact.affected_lanes && eventDesc.impact.affected_lanes.length > 0) {
                impactParts.push(`影响车道: ${eventDesc.impact.affected_lanes.join(', ')}`);
            }
            if (eventDesc.impact.lane_ids && eventDesc.impact.lane_ids.length > 0) {
                impactParts.push(`车道ID: ${eventDesc.impact.lane_ids.join(', ')}`);
            }
            if (impactParts.length > 0) {
                impactDesc = impactParts.join('\n');
            }
        }
        document.getElementById('scenarioDetails_impact').value = impactDesc;

        // 填充管控策略详情
        const strategyName = getStrategyDisplay(currentScenario.strategy) || currentScenario.strategy;
        document.getElementById('scenarioDetails_strategyType').value = strategyName;

        // 尝试获取策略参数
        let strategyParams = '暂无参数信息';
        if (currentScenario.strategy_params) {
            strategyParams = typeof currentScenario.strategy_params === 'string'
                ? currentScenario.strategy_params
                : JSON.stringify(currentScenario.strategy_params, null, 2);
        }
        document.getElementById('scenarioDetails_strategyParams').value = strategyParams;

    } catch (error) {
        console.warn('加载事件描述失败:', error);
        // 使用场景数据填充（回退方案）
        populateScenarioDetailsFromScenario(currentScenario);
    }
}

/**
 * 使用场景数据填充详情（回退方案）
 */
function populateScenarioDetailsFromScenario(scenario) {
    // 填充基本信息
    document.getElementById('scenarioDetails_scenarioId').value = scenario.scenario_id || '未知';
    document.getElementById('scenarioDetails_eventId').value = scenario.event_id || '未知';
    document.getElementById('scenarioDetails_eventType').value = getEventTypeDisplay(scenario.event_type) || scenario.event_type || '未知';
    document.getElementById('scenarioDetails_strategy').value = getStrategyDisplay(scenario.strategy) || scenario.strategy || '未知';
    document.getElementById('scenarioDetails_description').value = scenario.description || '暂无描述';

    // 填充事件详情
    document.getElementById('scenarioDetails_road').value = scenario.road || '未知';
    document.getElementById('scenarioDetails_direction').value = scenario.location || '未知';
    document.getElementById('scenarioDetails_mileage').value = scenario.mileage || '未知';
    document.getElementById('scenarioDetails_edgeId').value = scenario.edge_id || scenario.edgeId || '未知';
    document.getElementById('scenarioDetails_junctionId').value = scenario.junction_id || scenario.junctionId || '未知';

    // 填充时间信息
    let startTime = '未知';
    let endTime = '未知';
    let duration = '未知';

    if (scenario.time && typeof scenario.time === 'object') {
        startTime = scenario.time.start_time || startTime;
        endTime = scenario.time.end_time || endTime;
        duration = scenario.time.duration_hours || duration;
    } else {
        startTime = scenario.event_start || startTime;
        endTime = scenario.event_end || endTime;
        duration = scenario.duration_hours || duration;
    }

    document.getElementById('scenarioDetails_startTime').value = startTime;
    document.getElementById('scenarioDetails_endTime').value = endTime;
    document.getElementById('scenarioDetails_duration').value = `${duration}h`;

    // 填充事件影响
    document.getElementById('scenarioDetails_impact').value = scenario.impact || '暂无详细影响信息';

    // 填充管控策略详情
    const strategyName = getStrategyDisplay(scenario.strategy) || scenario.strategy;
    document.getElementById('scenarioDetails_strategyType').value = strategyName;

    let strategyParams = '暂无参数信息';
    if (scenario.strategy_params) {
        strategyParams = typeof scenario.strategy_params === 'string'
            ? scenario.strategy_params
            : JSON.stringify(scenario.strategy_params, null, 2);
    }
    document.getElementById('scenarioDetails_strategyParams').value = strategyParams;
}

/**
 * 关闭场景详情模态框
 */
function closeScenarioDetailsModal() {
    const modal = document.getElementById('scenarioDetailsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}
