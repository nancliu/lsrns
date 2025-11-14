// 全局状态
let allScenarios = [];
let filteredScenarios = [];
let currentPage = 1;
const pageSize = 20;
let currentFilters = {
    eventType: 'all',
    strategy: 'all',
    searchText: '',
    hasOnlyCases: true
};
let currentScenario = null;
let scenarioCaseMap = {};  // 存储场景ID -> 案例信息的映射

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

        // 过滤事件场景案例
        const eventScenarioCases = allCases.filter(c =>
            c.source_type === 'event_scenario' ||
            c.case_type === 'event_scenario_case' ||
            c.metadata_version === '2.0'  // v2.0元数据表示事件场景案例
        );

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

// 获取场景的创建状态显示
function getScenarioStatusDisplay(scenario_id) {
    const cases = scenarioCaseMap[scenario_id] || [];

    if (cases.length === 0) {
        return '<span class="status-badge status-none">— 未创建</span>';
    }

    const caseItem = cases[0];
    const status = caseItem.status || 'unknown';

    switch(status) {
        case 'od_generating':
            return '<span class="status-badge status-progress">⏳ 生成中</span>';
        case 'processing':
            // processing 也表示生成中（更通用的状态）
            return '<span class="status-badge status-progress">⏳ 处理中</span>';
        case 'od_generation_failed':
            return '<span class="status-badge status-error">⚠️ 生成失败</span>';
        case 'created':
            return '<span class="status-badge status-success">✓ 已创建</span>';
        case 'simulating':
            return '<span class="status-badge status-running">▶️ 仿真中</span>';
        case 'analyzing':
            return '<span class="status-badge status-running">📊 分析中</span>';
        case 'completed':
            return '<span class="status-badge status-completed">✅ 已完成</span>';
        case 'failed':
            return '<span class="status-badge status-error">✗ 失败</span>';
        default:
            return `<span class="status-badge status-unknown">◯ ${status}</span>`;
    }
}

// 获取状态的显示名称（文本）
function getStatusDisplayName(status) {
    const statusNames = {
        'od_generating': '生成中（OD文件正在生成）',
        'processing': '处理中（案例数据正在处理）',
        'od_generation_failed': '生成失败（OD文件生成失败）',
        'created': '已创建（就绪）',
        'simulating': '仿真中（正在运行仿真）',
        'analyzing': '分析中（正在运行分析）',
        'completed': '已完成（仿真/分析已完成）',
        'failed': '失败（处理失败）',
        'unknown': '状态未知'
    };
    return statusNames[status] || `${status}`;
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

    // 更新统计信息
    document.getElementById('totalScenarios').textContent = allScenarios.length;
    document.getElementById('eventTypeCount').textContent = eventTypes.length;
    document.getElementById('strategyCount').textContent = strategies.length;
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
    renderScenarios();
    renderPagination();
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
                    <th>创建状态</th>
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
                            ${getScenarioStatusDisplay(s.scenario_id)}
                        </td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-info" onclick="openScenarioDetailsModal('${s.scenario_id}')" title="查看场景详情">详情</button>
                                <button class="btn btn-sm btn-primary" onclick="openCreateCaseModal('${s.scenario_id}', '${s.event_type}', '${s.strategy}')" title="创建仿真案例">创建</button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    document.getElementById('scenarioTable').innerHTML = html;
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
    const analysisConfig = {
        case_name: caseName || `analysis_${currentScenario.scenario_id}_${Date.now()}`,
        scenario_id: currentScenario.scenario_id,
        event_id: currentScenario.event_id,
        event_type: currentScenario.event_type,
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
    const targetCount = document.getElementById('targetScenarioCount').value;

    if (!csvFile) {
        alert('请选择CSV文件');
        return;
    }

    const uploadConfig = {
        csv_file: csvFile,
        generate_all_strategies: generateAllStrategies,
        target_scenario_count: parseInt(targetCount)
    };

    try {
        // 显示进度提示
        alert(`🔄 场景生成已提交\n\nCSV文件: ${csvFile}\n预期场景数: ${targetCount}×${generateAllStrategies ? '3' : '1'}\n\n后端处理中，请稍候...`);

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

    // "只显示有案例的类别" 复选框
    const hasOnlyCasesCheckbox = document.getElementById('hasOnlyCases');
    if (hasOnlyCasesCheckbox) {
        hasOnlyCasesCheckbox.addEventListener('change', (e) => {
            currentFilters.hasOnlyCases = e.target.checked;
            applyFilters();
        });
    }

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
    await loadScenarios();
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
        '恶劣天气': '恶劣天气'
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
        '恶劣天气': 'weather'
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

// ========== 创建案例相关函数 ==========

/**
 * 直接创建案例（无模态框）
 * @param {string} scenarioId - 场景 ID
 * @param {string} eventType - 事件类型
 * @param {string} strategy - 管控策略
 */
async function directCreateCase(scenarioId, eventType, strategy) {
    // 1. 从allScenarios中查找完整的场景信息
    currentScenario = allScenarios.find(s => s.scenario_id === scenarioId);

    if (!currentScenario) {
        alert('错误: 无法找到场景信息，请重新选择');
        return;
    }

    // 2. 检查该场景是否已有案例
    const existingCases = scenarioCaseMap[scenarioId] || [];
    if (existingCases.length > 0) {
        const existingCase = existingCases[0];
        const caseStatusDisplay = getStatusDisplayName(existingCase.status);

        const action = confirm(
            `该场景已有案例\n\n` +
            `案例 ID: ${existingCase.case_id}\n` +
            `状态: ${caseStatusDisplay}\n\n` +
            `点击"确定"查看案例详情\n` +
            `点击"取消"创建新案例`
        );

        if (action) {
            // 用户选择查看案例详情
            window.location.href = `case-simulation-center.html?case_id=${existingCase.case_id}`;
            return;
        }
        // 否则继续创建新案例
    }

    // 3. 显示创建中提示
    const btn = event?.target;
    const originalText = btn?.textContent;
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ 创建中...';
    }

    // 3. 准备API请求数据
    const requestData = {
        case_name: `case_${currentScenario.scenario_id}_${Date.now()}`,
        scenario_id: currentScenario.scenario_id,
        event_id: currentScenario.event_id,
        event_type: currentScenario.event_type,
        strategy: currentScenario.strategy || currentScenario.control_strategy,
        network_file: 'templates/network_files/sichuan202508v7.net.xml',
        od_file: 'dwd.dwd_od_weekly',  // 完整的schema.table格式用于数据库引用
        taz_file: null,
        description: `从场景 ${currentScenario.scenario_id} 创建的案例`
    };

    try {
        // 4. 调用 API
        const response = await fetch('/api/v1/case/create-from-scenario', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        // 5. 处理响应
        if (!response.ok) {
            const error = await response.json().catch(() => ({
                message: `HTTP ${response.status}: ${response.statusText}`
            }));
            throw new Error(error.message || error.detail || '创建案例失败');
        }

        const result = await response.json();
        const caseId = result.data?.case_id;

        if (!caseId) {
            throw new Error('未获得案例 ID');
        }

        // 6. 检查OD文件状态并显示相应信息
        const odFileStatus = result.data?.od_file_status;
        const odFileType = result.data?.od_file_type;
        const odGenerationStarted = result.data?.od_generation_started;
        const caseStatus = result.data?.case_status;
        let successMessage = `✓ 案例创建成功！\n案例 ID: ${caseId}`;

        if (odFileStatus === 'pending' && odFileType === 'database') {
            if (odGenerationStarted) {
                successMessage += `\n\n⏳ OD文件正在生成中...\n系统已启动后台OD生成任务。\n（通常需要3-5分钟）\n\n当前状态: ${caseStatus === 'od_generating' ? '生成中' : '等待中'}`;
            } else {
                successMessage += `\n\n⚠️ OD文件处于待生成状态\n系统将在启动仿真时自动生成。`;
            }
        } else if (odFileStatus === 'exists') {
            successMessage += `\n✓ OD文件已就绪，可立即启动仿真`;
        }

        alert(successMessage);

        // 7. 更新 scenarioCaseMap 以反映新创建的案例
        if (!scenarioCaseMap[scenarioId]) {
            scenarioCaseMap[scenarioId] = [];
        }
        scenarioCaseMap[scenarioId].push({
            case_id: caseId,
            status: caseStatus || 'created',
            created_at: new Date().toISOString()
        });

        // 8. 刷新表格以显示更新的状态
        renderScenarios();

        // 9. 如果OD正在生成或处理中，启动状态轮询以实时更新
        if (caseStatus === 'od_generating' || caseStatus === 'processing') {
            console.log(`启动案例状态轮询: ${caseId} (当前状态: ${caseStatus})`);
            startStatusPolling(caseId, scenarioId);

            if (caseStatus === 'od_generating') {
                showNotification('⏳ OD文件正在后台生成中，进度会实时更新...', 'info');
            } else if (caseStatus === 'processing') {
                showNotification('⏳ 案例数据正在处理中，请稍候...', 'info');
            }
        } else if (caseStatus === 'created' && odFileStatus === 'exists') {
            showNotification('✓ 案例已就绪，可以立即创建仿真！', 'success');
        }

        // 10. 不再立即导航 - 用户留在场景浏览器页面
        // window.location.href = `case-simulation-center.html?case_id=${caseId}`;

    } catch (error) {
        console.error('创建案例失败:', error);
        alert(`✗ 创建案例失败: ${error.message}`);

        // 恢复按钮状态
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

// ========== 统一案例+仿真创建模态框函数 ==========

/**
 * 打开创建仿真案例的模态框
 * @param {string} scenarioId - 场景ID
 * @param {string} eventType - 事件类型
 * @param {string} strategy - 管控策略
 */
function openCreateCaseModal(scenarioId, eventType, strategy) {
    // 查找完整的场景信息
    currentScenario = allScenarios.find(s => s.scenario_id === scenarioId);

    if (!currentScenario) {
        alert('错误: 无法找到场景信息，请重新选择');
        return;
    }

    // 检查该场景是否已有案例
    const existingCases = scenarioCaseMap[scenarioId] || [];
    if (existingCases.length > 0) {
        const existingCase = existingCases[0];
        const caseStatusDisplay = getStatusDisplayName(existingCase.status);

        const action = confirm(
            `该场景已有案例\n\n` +
            `案例 ID: ${existingCase.case_id}\n` +
            `状态: ${caseStatusDisplay}\n\n` +
            `点击"确定"查看案例详情\n` +
            `点击"取消"创建新案例`
        );

        if (action) {
            // 用户选择查看案例详情
            window.location.href = `case-simulation-center.html?case_id=${existingCase.case_id}`;
            return;
        }
        // 否则继续创建新案例
    }

    // 填充场景信息（只读部分）
    document.getElementById('caseCreation_scenarioId').value = scenarioId;
    document.getElementById('caseCreation_eventType').value = getEventTypeDisplay(eventType) || eventType;
    document.getElementById('caseCreation_strategy').value = getStrategyDisplay(strategy) || strategy;

    // 格式化时间范围显示
    let startTime = '未知';
    let endTime = '未知';
    let duration = '未知';

    if (currentScenario.time && typeof currentScenario.time === 'object') {
        startTime = currentScenario.time.start_time || startTime;
        endTime = currentScenario.time.end_time || endTime;
        duration = currentScenario.time.duration_hours || duration;
    } else {
        startTime = currentScenario.event_start || startTime;
        endTime = currentScenario.event_end || endTime;
        duration = currentScenario.duration_hours || duration;
    }

    const displayStart = typeof startTime === 'string' ? startTime.substring(0, 19) : startTime;
    const displayEnd = typeof endTime === 'string' ? endTime.substring(0, 19) : endTime;
    document.getElementById('caseCreation_timeRange').value = `${displayStart} ~ ${displayEnd} (${duration}h)`;

    // 重置输出配置为默认值
    document.getElementById('caseCreation_edgedata').checked = true;
    document.getElementById('caseCreation_tripinfo').checked = true;

    // 打开模态框
    const modal = document.getElementById('caseCreationModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('caseCreation_submitBtn').disabled = false;
        document.getElementById('caseCreation_submitBtn').textContent = '✓ 创建';
    }
}

/**
 * 提交统一案例+仿真创建请求（简化版）
 */
async function submitCreateCaseWithSimulation() {
    if (!currentScenario) {
        alert('错误: 场景信息丢失，请重新打开模态框');
        return;
    }

    // 输出配置（简化：只有EdgeData和TripInfo）
    const outputConfig = {
        generate_edgedata: document.getElementById('caseCreation_edgedata').checked,
        generate_summary: true,  // 始终启用
        generate_tripinfo: document.getElementById('caseCreation_tripinfo').checked,
        generate_vehroute: false  // 始终禁用
    };

    // 准备请求数据（使用默认值）
    const requestData = {
        scenario_id: currentScenario.scenario_id,
        event_id: currentScenario.event_id,
        event_type: currentScenario.event_type,
        strategy: currentScenario.strategy || currentScenario.control_strategy,

        // 自动生成案例名称
        case_name: null,  // 后端会自动生成

        // 使用默认仿真参数
        simulation_duration_hours: 2.5,
        random_seed: null,  // 自动生成
        simulation_type: 'microscopic',  // 使用微观仿真
        output_config: outputConfig,

        network_file: 'templates/network_files/sichuan202508v7.net.xml',
        od_file: 'dwd.dwd_od_weekly',
        taz_file: null,
        description: `从场景 ${currentScenario.scenario_id} 创建的案例`
    };

    // 禁用提交按钮并显示加载状态
    const submitBtn = document.getElementById('caseCreation_submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ 创建中...';

    try {
        // 发送请求到统一创建端点
        const response = await fetch('/api/v1/case/create-case-with-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({
                message: `HTTP ${response.status}: ${response.statusText}`
            }));
            throw new Error(error.message || error.detail || '创建案例失败');
        }

        const result = await response.json();
        const caseId = result.data?.case_id;
        const simulationId = result.data?.simulation_id;
        const caseStatus = result.data?.case_status;

        if (!caseId) {
            throw new Error('未获得案例 ID');
        }

        // 关闭模态框
        closeCaseCreationModal();

        // 更新 scenarioCaseMap 以反映新创建的案例
        const scenarioId = currentScenario.scenario_id;
        if (!scenarioCaseMap[scenarioId]) {
            scenarioCaseMap[scenarioId] = [];
        }
        scenarioCaseMap[scenarioId].push({
            case_id: caseId,
            case_name: caseId,  // 使用自动生成的ID
            status: caseStatus || 'ready_to_simulate',
            created_at: new Date().toISOString(),
            source_scenario: scenarioId
        });

        // 刷新表格以显示更新的状态
        renderScenarios();

        // 显示成功信息
        const successMessage = `✓ 仿真案例创建成功！\n\n` +
                               `案例 ID: ${caseId}\n` +
                               `仿真 ID: ${simulationId || 'N/A'}\n\n` +
                               `✓ 案例和仿真配置已准备就绪`;
        alert(successMessage);

    } catch (error) {
        console.error('创建案例失败:', error);
        alert(`✗ 创建案例失败: ${error.message}`);

        // 恢复按钮状态
        submitBtn.disabled = false;
        submitBtn.textContent = '✓ 创建';
    }
}

/**
 * 关闭案例创建模态框
 */
function closeCaseCreationModal() {
    const modal = document.getElementById('caseCreationModal');
    if (modal) {
        modal.style.display = 'none';
    }
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
        '恶劣天气': '06_weather',
        '路面异常': '06_weather',
        // 备选/兼容名称
        '拥堵': '02_congestion',
        '道路管制': '03_road_control',
        '车辆故障': '05_breakdown'
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
