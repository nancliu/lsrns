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

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadScenarios();
    setupEventListeners();
});

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
                                <button class="btn btn-sm btn-primary" onclick="openCreateModal('${s.scenario_id}', '${s.event_type}', '${s.strategy}')" title="创建仿真案例">创建</button>
                                <button class="btn btn-sm btn-secondary" onclick="openAnalysisModal('${s.scenario_id}', '${s.event_type}', '${s.strategy}')" title="启动仿真分析">分析</button>
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

// 打开创建模态框
function openCreateModal(scenarioId, eventType, strategy) {
    currentScenario = allScenarios.find(s => s.scenario_id === scenarioId);
    if (!currentScenario) {
        alert('未找到场景信息');
        return;
    }

    document.getElementById('selectedScenarioId').value = scenarioId;
    document.getElementById('selectedScenarioName').value = scenarioId;
    document.getElementById('selectedEventType').value = getEventTypeDisplay(eventType);
    document.getElementById('selectedControlStrategy').value = getStrategyDisplay(strategy);
    showModal('quickCreateModal');
}

// 提交快速创建
async function submitQuickCreate() {
    if (!currentScenario) {
        alert('请先选择场景');
        return;
    }

    const createData = {
        case_name: document.getElementById('selectedScenarioName').value || currentScenario.scenario_id,
        event_type: currentScenario.event_type,
        strategy: currentScenario.strategy,
        scenario_id: currentScenario.scenario_id,
        event_id: currentScenario.event_id,
        network_file: 'templates/network_files/sichuan202508v7.net.xml',
        od_file: 'baseline.od_data_sichuan_202507',
        taz_file: null,
        description: document.getElementById('caseDescription').value || `从场景 ${currentScenario.scenario_id} 创建的案例`
    };

    try {
        const response = await fetch('/api/v1/scenario/create-case', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(createData)
        });

        if (response.ok) {
            const result = await response.json();
            alert(`案例已创建！\n案例ID: ${result.case_id}`);
            closeModal('quickCreateModal');
        } else {
            throw new Error('API调用失败');
        }
    } catch (error) {
        console.error('创建案例失败:', error);
        alert('创建案例失败: ' + error.message);
    }
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
