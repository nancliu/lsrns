/**
 * 批量优化仿真 JavaScript
 *
 * 功能:
 * - 批量仿真配置
 * - 进度监控(轮询)
 * - 结果展示
 */

const API_BASE = '/api/v1';

// ========== 调试配置 ==========
const DEBUG_PROGRESS = false; // 改为 true 来启用详细日志

function debugLog(message, data = null) {
    if (!DEBUG_PROGRESS) return;
    console.log(message, data || '');
}

function debugLogObject(title, obj) {
    if (!DEBUG_PROGRESS) return;
    console.log(`=== ${title} ===`);
    console.log(obj);
}

// ========== 全局状态 ==========
const STATUS_MAP = {
    'pending': '等待启动（请点击下方"启动仿真"按钮）',
    'running': '运行中...',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
};

// 全局状态
let currentBatchId = null;
let currentCaseId = null; // 当前选中的案例ID（用于批次历史加载）
let progressPollInterval = null;
let currentView = 'config'; // config, monitoring, results
let liveCurveVisible = true; // 动态曲线显示状态（默认显示）
let expandedBatchId = null; // 当前展开的批次ID（用于批次监控）

// 暴露全局变量给 window 对象（用于E2E测试）
window.currentBatchId = currentBatchId;
window.currentCaseId = currentCaseId;

// ========== CSS 动态样式辅助函数 (Phase 2c-Extended) ==========

/**
 * 策略类型转换为徽章 CSS 类名
 * 用于替代内联 style 属性中的动态颜色
 * @param {string} type - 策略类型 (VSS, DHS, TEC)
 * @returns {string} - 对应的 CSS 类名 (badge-vss, badge-dhs, badge-tec, badge-default)
 */
function strategyTypeToClass(type) {
    const classMap = {
        'VSS': 'badge-vss',
        'DHS': 'badge-dhs',
        'TEC': 'badge-tec'
    };
    return classMap[type] || 'badge-default';
}

/**
 * 显示元素（使用CSS类）
 * @param {string} elementId - 元素ID
 */
function showElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('active');
        element.style.display = ''; // 清除内联样式
    }
}

/**
 * 隐藏元素（使用CSS类）
 * @param {string} elementId - 元素ID
 */
function hideElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('active');
        element.style.display = 'none'; // 保持隐藏
    }
}

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', async () => {
    await loadCases();
    await loadPlans();
    await loadVehicleTemplates(); // Revision 2: 动态加载车辆模板

    // 恢复案例ID（从URL参数或localStorage）
    const urlParams = new URLSearchParams(window.location.search);
    const caseIdFromUrl = urlParams.get('case_id');

    let selectedCaseId = null;

    if (caseIdFromUrl) {
        // 优先使用URL参数
        selectedCaseId = caseIdFromUrl;
    } else {
        // 回退到localStorage
        selectedCaseId = localStorage.getItem('lastSelectedCaseId');
    }

    // 如果没有保存的案例，自动选择第一个（Bug Fix: 首次进入时自动选择）
    if (!selectedCaseId) {
        const caseSelector = document.getElementById('caseSelector');
        if (caseSelector.options.length > 1) {
            // options[0]是placeholder，选择options[1]
            selectedCaseId = caseSelector.options[1].value;
            localStorage.setItem('lastSelectedCaseId', selectedCaseId);
        }
    }

    if (selectedCaseId) {
        currentCaseId = selectedCaseId;
        window.currentCaseId = currentCaseId;
        document.getElementById('caseSelector').value = selectedCaseId;
        // 加载该案例的时长
        await loadCaseDuration(selectedCaseId);
    }

    // 初始化仿真配置事件监听 (Phase 2, 3)
    initSimulationConfigListeners();

    // 绑定事件
    document.getElementById('caseSelector').addEventListener('change', onCaseChange);
    document.getElementById('createBatchBtn').addEventListener('click', createBatch);

    // TODO Phase 2-3: Re-enable when batch card controls are implemented
    // document.getElementById('startBatchBtn').addEventListener('click', startBatchExecution);
    // document.getElementById('cancelBatchBtn').addEventListener('click', cancelBatch);
    // document.getElementById('toggleLiveCurveBtn').addEventListener('click', toggleLiveCurveVisibility);

    document.getElementById('clearConfigBtn').addEventListener('click', clearConfig);
    document.getElementById('backToConfigBtn').addEventListener('click', () => switchView('config'));
    document.getElementById('viewOptimizationBtn').addEventListener('click', viewOptimizationAnalysis);
    document.getElementById('exportResultsBtn').addEventListener('click', exportResults);

    // 计算预估 (Phase 1-4: 包含seed变化)
    document.getElementById('numSeeds').addEventListener('input', updateEstimate);
    document.getElementById('baseSeed').addEventListener('input', updateEstimate);
});

// ========== 视图切换 ==========

function switchView(view) {
    currentView = view;

    // Update views (3-tab structure: config, monitoring, results)
    document.getElementById('configView').classList.toggle('active', view === 'config');
    document.getElementById('monitoringView').classList.toggle('active', view === 'monitoring');
    document.getElementById('resultsView').classList.toggle('active', view === 'results');

    // Update tabs (顶部标签栏)
    document.getElementById('configViewTab').classList.toggle('active', view === 'config');
    document.getElementById('monitoringViewTab').classList.toggle('active', view === 'monitoring');
    document.getElementById('resultsViewTab').classList.toggle('active', view === 'results');

    // Update tabs (底部标签栏 - 保持同步)
    document.getElementById('configViewTabBottom').classList.toggle('active', view === 'config');
    document.getElementById('monitoringViewTabBottom').classList.toggle('active', view === 'monitoring');
    document.getElementById('resultsViewTabBottom').classList.toggle('active', view === 'results');

    // Load data when switching to monitoring view
    if (view === 'monitoring' && currentCaseId) {
        loadBatchList();
    }

    // Load results when switching to results view
    if (view === 'results' && currentBatchId) {
        loadResults();
    }
}

// Load batch list (unified monitoring view)
// Phase 1: Reuses loadBatchHistory() with updated element IDs
function loadBatchList() {
    loadBatchHistory();
}

// Filtering and sorting (Phase 1: Basic implementation)
function filterBatches() {
    // Phase 1: Reuses existing filter logic
    filterBatchHistory();
}

function sortBatches() {
    // TODO: Phase 5 - Implement batch sorting
    // For now, just reload the list
    loadBatchHistory();
}

// ========== 数据加载 ==========

async function loadCases() {
    try {
        const response = await fetch(`${API_BASE}/case/list_cases/`);
        if (!response.ok) throw new Error('Failed to load cases');

        const data = await response.json();
        const select = document.getElementById('caseSelector');
        select.innerHTML = '<option value="">-- 选择案例 --</option>';

        data.cases.forEach(c => {
            const option = document.createElement('option');
            option.value = c.case_id;

            // Revision 4: 在案例列表中显示时间范围信息
            let displayText = c.case_id;
            if (c.time_range && c.time_range.start && c.time_range.end) {
                // 提取时间范围：2025/09/01 07:00:00 -> 07:00-07:10
                const startTime = c.time_range.start.split(' ')[1]; // HH:MM:SS
                const endTime = c.time_range.end.split(' ')[1];     // HH:MM:SS
                displayText += ` - 案例时间: ${startTime}-${endTime}`;
            } else if (c.description) {
                displayText += ` - ${c.description}`;
            }

            option.textContent = displayText;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Load cases error:', error);
        showError('加载案例失败: ' + error.message);
    }
}

async function loadPlans() {
    try {
        const response = await fetch(`${API_BASE}/control/plans/`);
        if (!response.ok) throw new Error('Failed to load plans');

        const data = await response.json();
        const container = document.getElementById('planSelector');
        container.innerHTML = '';

        data.plans.forEach(plan => {
            const div = document.createElement('div');
            div.className = 'plan-item';

            // Phase 4: 标记基准方案为特殊样式
            if (plan.is_baseline) {
                div.classList.add('baseline-plan-item');
            }

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `plan-${plan.plan_id}`;
            checkbox.value = plan.plan_id;
            checkbox.checked = plan.is_baseline; // baseline自动选中
            checkbox.disabled = plan.is_baseline; // baseline不可取消
            checkbox.addEventListener('change', updateEstimate);

            const label = document.createElement('label');
            label.htmlFor = `plan-${plan.plan_id}`;

            // Phase 4: 在基准方案名称后添加徽章
            if (plan.is_baseline) {
                label.innerHTML = `${plan.plan_name} <span class="baseline-badge">基准方案（必选）</span>`;
            } else {
                label.textContent = plan.plan_name;
            }

            div.appendChild(checkbox);
            div.appendChild(label);
            container.appendChild(div);
        });

        updateEstimate();
    } catch (error) {
        console.error('Load plans error:', error);
        showError('加载方案失败');
    }
}

// ========== 配置和启动 ==========

function getSelectedPlans() {
    const checkboxes = document.querySelectorAll('#planSelector input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function updateEstimate() {
    const selectedPlans = getSelectedPlans();
    const numSeeds = parseInt(document.getElementById('numSeeds').value) || 3;
    const totalTasks = selectedPlans.length * numSeeds;

    // 更新任务数预估
    document.getElementById('estimateText').textContent =
        `${selectedPlans.length}个方案 × ${numSeeds} 个随机种子 = ${totalTasks} 个并行仿真任务`;
}

/**
 * 加载案例仿真时长
 * Revision 3: 从API获取case元数据中的时长信息
 * @param {string} caseId - 案例ID
 */
async function loadCaseDuration(caseId) {
    try {
        const response = await fetch(`${API_BASE}/control/batch-optimization/cases/${caseId}/duration`);

        if (!response.ok) {
            throw new Error(`Failed to load case duration: ${response.statusText}`);
        }

        const data = await response.json();
        const durationInfo = document.getElementById('currentDurationInfo');

        if (!durationInfo) {
            console.warn('currentDurationInfo element not found');
            return;
        }

        // 显示格式化的时长信息
        durationInfo.textContent = data.display_text;
        durationInfo.style.color = '#333';

        // 将数据保存到全局变量供createBatch使用
        window.caseDuration = data;

        console.log(`Case duration loaded: ${data.display_text}`);
    } catch (error) {
        console.error('Load case duration error:', error);
        const durationInfo = document.getElementById('currentDurationInfo');
        if (durationInfo) {
            durationInfo.textContent = '无法获取时长信息';
            durationInfo.style.color = '#d32f2f';
        }
    }
}

async function onCaseChange() {
    const caseId = document.getElementById('caseSelector').value;

    // 更新全局案例ID状态
    currentCaseId = caseId;
    window.currentCaseId = currentCaseId;

    // 保存到 localStorage 以便页面刷新后恢复
    if (caseId) {
        localStorage.setItem('lastSelectedCaseId', caseId);
        console.log('Case selected:', currentCaseId);

        // Revision 3: 加载案例时长
        await loadCaseDuration(caseId);
    } else {
        localStorage.removeItem('lastSelectedCaseId');
        // 清空时长显示
        const durationInfo = document.getElementById('currentDurationInfo');
        if (durationInfo) {
            durationInfo.textContent = '请选择案例';
        }
    }
}

function clearConfig() {
    document.getElementById('caseSelector').value = '';
    const checkboxes = document.querySelectorAll('#planSelector input[type="checkbox"]:not([disabled])');
    checkboxes.forEach(cb => cb.checked = false);
    document.getElementById('numSeeds').value = 3;
    document.getElementById('baseSeed').value = 66;
    updateEstimate();
}

/**
 * 获取仿真输出配置
 * Phase 1: 从output checkboxes收集配置
 * @returns {Object} 输出配置对象 {summary_xml, e1_detector_data, edgedata_xml, tripinfo_xml}
 */
function getOutputConfig() {
    return {
        summary_xml: document.getElementById('outputSummary').checked,
        e1_detector_data: document.getElementById('outputE1').checked,
        edgedata_xml: document.getElementById('outputEdgedata').checked,
        tripinfo_xml: document.getElementById('outputTripinfo').checked
    };
}

/**
 * 获取车辆类型模板
 * Phase 2: 获取选中的template
 * @returns {string} 选中的template文件名
 */
function getVehicleTemplate() {
    return document.getElementById('vehicleTypesTemplate').value || 'vehicle_types.json';
}

/**
 * 获取仿真时长配置
 * Phase 3: 从case元数据读取时长（Revision 3: 改为只读）
 * @returns {Object|null} 时长配置对象或null
 */
function getSimulationDuration() {
    // Revision 5: 支持自定义时长覆盖case元数据
    const useCustom = document.getElementById('useCustomDuration')?.checked || false;

    if (useCustom) {
        // 使用自定义时长
        const hours = parseInt(document.getElementById('customDurationHours')?.value || 1);
        const minutes = parseInt(document.getElementById('customDurationMinutes')?.value || 0);
        const totalMinutes = hours * 60 + minutes;

        return {
            use_default: false,
            hours: hours,
            minutes: minutes,
            total_minutes: totalMinutes
        };
    }

    // Revision 3: 时长从case元数据读取
    if (window.caseDuration) {
        return {
            use_default: true,
            hours: window.caseDuration.duration_hours,
            minutes: window.caseDuration.duration_minutes,
            total_minutes: window.caseDuration.total_minutes,
            start_time: window.caseDuration.start_time,
            end_time: window.caseDuration.end_time
        };
    }

    // 如果没有加载case信息
    showError('请先选择案例');
    return null;
}

/**
 * 动态加载车辆模板列表
 * Revision 2: 从API获取可用的vehicle_types*.json文件
 */
async function loadVehicleTemplates() {
    try {
        const response = await fetch(`${API_BASE}/control/batch-optimization/templates/vehicle-types`);
        if (!response.ok) {
            throw new Error(`Failed to load templates: ${response.statusText}`);
        }

        const data = await response.json();
        const selectElement = document.getElementById('vehicleTypesTemplate');

        if (!selectElement) {
            console.warn('vehicleTypesTemplate element not found');
            return;
        }

        // 清空现有选项（保留第一个作为默认）
        selectElement.innerHTML = '';

        // 添加模板选项
        if (data.templates && Array.isArray(data.templates)) {
            data.templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.filename;
                option.textContent = template.display_name;
                selectElement.appendChild(option);
            });

            console.log(`Loaded ${data.templates.length} vehicle template(s)`);
        } else {
            console.warn('No templates found in response');
        }
    } catch (error) {
        console.error('Load vehicle templates error:', error);
        // 回退到默认模板（HTML中已有）
        console.log('Using default vehicle template');
    }
}

/**
 * 初始化仿真配置事件监听
 * Phase 2: 添加交互事件（Revision 5: 添加自定义时长复选框监听）
 */
function initSimulationConfigListeners() {
    // Phase 2: 车辆模板选择
    const vehicleTemplateSelect = document.getElementById('vehicleTypesTemplate');
    if (vehicleTemplateSelect) {
        vehicleTemplateSelect.addEventListener('change', () => {
            debugLog('Vehicle template changed:', getVehicleTemplate());
        });
    }

    // Revision 5: 自定义时长复选框监听
    const useCustomDurationCheckbox = document.getElementById('useCustomDuration');
    const customDurationInputs = document.getElementById('customDurationInputs');
    if (useCustomDurationCheckbox && customDurationInputs) {
        useCustomDurationCheckbox.addEventListener('change', () => {
            if (useCustomDurationCheckbox.checked) {
                customDurationInputs.style.display = 'block';
                debugLog('Custom duration enabled');
            } else {
                customDurationInputs.style.display = 'none';
                debugLog('Custom duration disabled');
            }
        });
    }
}

async function createBatch() {
    const caseId = document.getElementById('caseSelector').value;
    const planIds = getSelectedPlans();
    const numSeeds = parseInt(document.getElementById('numSeeds').value) || 3;
    const baseSeed = parseInt(document.getElementById('baseSeed').value) || 66;
    const outputConfig = getOutputConfig();
    const vehicleTemplate = getVehicleTemplate();
    const simulationDuration = getSimulationDuration();

    if (!caseId) {
        showError('请选择案例');
        return;
    }

    if (planIds.length === 0) {
        showError('请至少选择一个方案');
        return;
    }

    if (simulationDuration === null) {
        // Error already shown in getSimulationDuration()
        return;
    }

    try {
        // 创建批次 (Phase 1-3: 使用output_config, vehicle_template, simulation_duration)
        const requestBody = {
            case_id: caseId,
            plan_ids: planIds,
            num_seeds: numSeeds,
            base_seed: baseSeed,
            output_config: outputConfig,
            vehicle_types_template: vehicleTemplate
        };

        // 仅在需要时添加simulation_duration
        if (simulationDuration) {
            requestBody.simulation_duration = simulationDuration;
        }

        const createResponse = await fetch(`${API_BASE}/control/batch-optimization/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!createResponse.ok) {
            const error = await createResponse.json();
            throw new Error(error.detail || 'Failed to create batch');
        }

        const batch = await createResponse.json();
        currentBatchId = batch.batch_id;
        window.currentBatchId = currentBatchId;

        // 保存案例ID（从API响应或当前选择）
        if (batch.case_id) {
            currentCaseId = batch.case_id;
            window.currentCaseId = currentCaseId;
        }

        // Stay on config view, don't auto-switch
        updateBatchInfo(batch);

        // 显示提示，引导用户查看批次监控
        showSuccess('批次创建成功！可在"批次监控"标签查看和管理批次。');

    } catch (error) {
        console.error('Create batch error:', error);
        showError('创建批次失败: ' + error.message);
    }
}

async function startBatchExecution() {
    if (!currentBatchId) return;

    try {
        const startResponse = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentBatchId}/start`,
            { method: 'POST' }
        );

        if (!startResponse.ok) {
            throw new Error('Failed to start batch');
        }

        // 隐藏启动按钮,显示取消按钮
        hideElement('startBatchBtn');
        showElement('cancelBatchBtn');

        // 开始轮询进度
        startProgressPolling();

    } catch (error) {
        console.error('Start batch execution error:', error);
        showError('启动仿真失败: ' + error.message);
    }
}

function updateBatchInfo(batch) {
    // Phase 1: These elements are in the old progressView which was removed
    // Phase 2 will implement batch info display in expandable cards
    const batchTitle = document.getElementById('batchTitle');
    const batchStatus = document.getElementById('batchStatus');

    if (batchTitle) {
        batchTitle.textContent = `批次: ${batch.batch_id}`;
    }
    if (batchStatus) {
        const statusText = STATUS_MAP[batch.status] || batch.status || STATUS_MAP['pending'];
        batchStatus.textContent = `状态: ${statusText}`;
    }
}

// ========== 进度监控 ==========

function startProgressPolling() {
    if (progressPollInterval) return;

    updateProgress(); // 立即更新一次
    progressPollInterval = setInterval(updateProgress, 1000); // 每1秒更新（提升曲线平滑度）
}

function stopProgressPolling() {
    if (progressPollInterval) {
        clearInterval(progressPollInterval);
        progressPollInterval = null;
    }
}

async function updateProgress() {
    if (!currentBatchId) return;

    try {
        // 添加时间戳参数来破坏浏览器缓存，确保获取最新数据
        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentBatchId}/progress?t=${Date.now()}`,
            {
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            }
        );

        if (!response.ok) throw new Error('Failed to get progress');

        const data = await response.json();

        // 调试日志（仅在 DEBUG_PROGRESS 启用时输出）
        debugLogObject('API Progress Response', {
            status: data.status,
            running_tasks: data.running_tasks,
            total_tasks: data.total_tasks,
            completed_tasks: data.completed_tasks,
            has_live_time_series: !!data.live_time_series,
            live_time_series: data.live_time_series
        });

        // 更新批次信息 (监控区域)
        const statusText = STATUS_MAP[data.status] || data.status;
        const monitorStatus = document.getElementById('monitorBatchStatus');
        if (monitorStatus) {
            monitorStatus.textContent = `状态: ${statusText}`;
        }

        // 更新任务统计信息 (监控区域)
        const taskStatsDiv = document.getElementById('monitorTaskStats');
        if (taskStatsDiv && data.status !== 'pending') {
            taskStatsDiv.style.display = 'block';
            const totalElem = document.getElementById('monitorTotalTasks');
            const completedElem = document.getElementById('monitorCompletedTasks');
            const runningElem = document.getElementById('monitorRunningTasks');
            const failedElem = document.getElementById('monitorFailedTasks');

            if (totalElem) totalElem.textContent = data.total_tasks || 0;
            if (completedElem) completedElem.textContent = data.completed_tasks || 0;
            if (runningElem) runningElem.textContent = data.running_tasks || 0;
            if (failedElem) failedElem.textContent = data.failed_tasks || 0;

            // 显示预计完成时间 - 使用运行中任务的最长剩余时间
            const estimatedCompletionDiv = document.getElementById('estimatedCompletion');
            if (estimatedCompletionDiv) {
                if (data.status === 'running' && data.tasks) {
                    // 找出运行中任务的最长剩余时间
                    const runningTasks = data.tasks.filter(t => t.status === 'running');
                    let maxRemainingSeconds = 0;

                    runningTasks.forEach(task => {
                        const liveStatus = task.live_status || {};
                        const remainingSec = liveStatus.estimated_remaining_seconds;
                        if (remainingSec && remainingSec > maxRemainingSeconds) {
                            maxRemainingSeconds = remainingSec;
                        }
                    });

                    if (maxRemainingSeconds > 0) {
                        const remainingDisplay = formatDuration(maxRemainingSeconds);
                        const completionTime = new Date(Date.now() + maxRemainingSeconds * 1000)
                            .toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
                        estimatedCompletionDiv.innerHTML = `
                            <strong>⏱️ 预计剩余:</strong> ${remainingDisplay}
                            <span style="margin-left: 15px;"><strong>📅 预计完成:</strong> ${completionTime}</span>
                        `;
                    } else {
                        estimatedCompletionDiv.innerHTML = '<strong>⏱️ 正在估算剩余时间...</strong>';
                    }
                } else {
                    estimatedCompletionDiv.innerHTML = '';
                }
            }
        }

        // 更新总进度
        const progressPct = (data.progress * 100).toFixed(0);

        // 计算并显示详细的任务进度（使用与 renderTaskList() 相同的逻辑）
        const runningTasks = data.tasks ? data.tasks.filter(t => t.status === 'running') : [];
        const taskProgressInfo = runningTasks.map(t => {
            const liveStatus = t.live_status || {};
            let progressPct = 0;

            // 优先使用后端已计算的 progress_percent（0-100之间的百分比）
            if (liveStatus.progress_percent !== null && liveStatus.progress_percent !== undefined) {
                // 后端返回的是已计算的百分比（0-100），直接使用
                progressPct = liveStatus.progress_percent;
            } else if (liveStatus.current_time !== null && liveStatus.current_time !== undefined &&
                       liveStatus.end_time !== null && liveStatus.end_time !== undefined) {
                // 如果没有 progress_percent，但有 current_time 和 end_time，使用它们计算
                progressPct = (liveStatus.current_time / liveStatus.end_time) * 100;
            } else if (t.progress !== null && t.progress !== undefined) {
                // 最后的备选：使用 task.progress
                let progressValue = t.progress;
                if (progressValue > 100) {
                    // 如果 > 100，说明是原始仿真时间（秒），需要转换
                    const endTime = liveStatus.end_time || 600;
                    const divisor = endTime / 100;
                    progressPct = (progressValue / divisor);
                } else {
                    // 否则已经是百分比
                    progressPct = progressValue;
                }
            }

            // 确保进度在有效范围内 [0, 100]
            progressPct = Math.max(0, Math.min(100, progressPct));

            return `${t.task_id}:${progressPct.toFixed(0)}%`;
        }).join(', ');

        // 进度日志输出
        console.log(`[Progress] ${progressPct}% | Tasks: [${taskProgressInfo}]`);
        debugLog(`Batch progress: ${progressPct}% | Running: [${taskProgressInfo}]`);

        const progressBar = document.getElementById('monitorProgressBar');
        const progressText = document.getElementById('monitorProgressText');

        if (progressBar) {
            progressBar.style.width = `${progressPct}%`;
        }

        if (progressText) {
            // 显示进度百分比（剩余时间已在上方taskStats中显示）
            progressText.textContent = `${progressPct}%`;
        }

        // 更新任务详情
        renderTaskList(data.tasks || []);

        // 更新动态在网车辆曲线
        renderLiveCurve(data.live_time_series);

        // 如果完成，停止轮询（不再自动跳转，让用户查看曲线）
        if (data.status === 'completed') {
            stopProgressPolling();
            hideElement('cancelBatchBtn');

            // ✅ 修复：不再自动跳转到结果视图
            // 用户可以在进度视图查看最终的曲线图，然后手动点击"结果"tab
            console.info('✓ 仿真完成！曲线已更新，可在进度视图查看最终结果');

            // ✅ 显示完成提示（可选）
            const estimatedCompletionDiv = document.getElementById('estimatedCompletion');
            if (estimatedCompletionDiv) {
                estimatedCompletionDiv.innerHTML = `
                    <strong style="color: #27ae60;">✓ 仿真已完成！</strong>
                    <span style="margin-left: 15px; font-size: 0.9em;">点击上方"结果"tab查看详细分析</span>
                `;
            }
        } else if (data.status === 'failed' || data.status === 'cancelled') {
            stopProgressPolling();
            hideElement('cancelBatchBtn');
        }

    } catch (error) {
        console.error('Update progress error:', error);
    }
}

function renderTaskList(tasks) {
    // 按plan_id分组
    const grouped = {};
    tasks.forEach(task => {
        if (!grouped[task.plan_id]) {
            grouped[task.plan_id] = {
                plan_name: task.plan_name,
                tasks: []
            };
        }
        grouped[task.plan_id].tasks.push(task);
    });

    // Phase 1.5: Render to monitor panel
    const container = document.getElementById('monitorTaskList');
    const section = document.getElementById('monitorTaskListSection');

    if (!container) {
        console.warn('monitorTaskList element not found');
        return;
    }

    container.innerHTML = '';

    if (tasks.length === 0) {
        // Hide the section if no tasks
        if (section) section.style.display = 'none';
        return;
    }

    // Show the section when there are tasks
    if (section) section.style.display = 'block';

    for (const [planId, planData] of Object.entries(grouped)) {
        const planDiv = document.createElement('div');
        planDiv.className = 'plan-tasks';

        const planTitle = document.createElement('h4');
        planTitle.textContent = planData.plan_name;
        planDiv.appendChild(planTitle);

        planData.tasks.forEach(task => {
            const taskDiv = document.createElement('div');
            taskDiv.className = `task-item task-${task.status}`;

            const icon = getStatusIcon(task.status);
            const statusText = getStatusText(task.status);

            // 构建任务显示内容
            let content = `<span class="task-icon">${icon}</span> Seed ${task.seed}: ${statusText}`;

            // 如果任务正在运行，显示进度条和实时状态
            if (task.status === 'running') {
                const liveStatus = task.live_status || {};

                // 优先使用后端已计算的 progress_percent（0-100之间的百分比，已由后端计算）
                let progressPct = 0;

                if (liveStatus.progress_percent !== null && liveStatus.progress_percent !== undefined) {
                    // 后端返回的是已计算的百分比（0-100），直接使用
                    progressPct = liveStatus.progress_percent;
                } else if (liveStatus.current_time !== null && liveStatus.current_time !== undefined &&
                           liveStatus.end_time !== null && liveStatus.end_time !== undefined) {
                    // 如果没有 progress_percent，但有 current_time 和 end_time，使用它们计算
                    progressPct = (liveStatus.current_time / liveStatus.end_time) * 100;
                } else if (task.progress !== null && task.progress !== undefined) {
                    // 最后的备选：使用 task.progress
                    let progressValue = task.progress;
                    if (progressValue > 100) {
                        // 如果 > 100，说明是原始仿真时间（秒），需要转换
                        const endTime = liveStatus.end_time || 600;
                        const divisor = endTime / 100;
                        progressPct = (progressValue / divisor);
                    } else {
                        // 否则已经是百分比
                        progressPct = progressValue;
                    }
                }

                // 确保进度在有效范围内 [0, 100]
                progressPct = Math.max(0, Math.min(100, progressPct));

                const runningVeh = liveStatus.running_vehicles;
                const remainingSec = liveStatus.estimated_remaining_seconds;

                content += `
                    <div class="task-progress-bar" style="
                        margin-top: 5px;
                        height: 8px;
                        background: #ecf0f1;
                        border-radius: 4px;
                        overflow: hidden;
                    ">
                        <div style="
                            height: 100%;
                            width: ${progressPct}%;
                            background: linear-gradient(90deg, #3498db 0%, #2ecc71 100%);
                            transition: width 0.3s;
                        "></div>
                    </div>
                    <div class="task-live-status" style="
                        font-size: 0.85em;
                        color: #7f8c8d;
                        margin-top: 3px;
                        display: flex;
                        justify-content: space-between;
                    ">
                        <span>${progressPct.toFixed(1)}%</span>
                        ${runningVeh !== undefined ? `<span>在网: ${runningVeh}辆</span>` : ''}
                        ${remainingSec !== undefined ? `<span>剩余: ${formatDuration(remainingSec)}</span>` : ''}
                    </div>
                `;
            }

            taskDiv.innerHTML = content;
            planDiv.appendChild(taskDiv);
        });

        container.appendChild(planDiv);
    }
}

function formatDuration(seconds) {
    if (seconds === null || seconds === undefined || seconds < 0) {
        return '--';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.round(seconds % 60);  // ✅ 修复：四舍五入秒数

    if (hours > 0) {
        return `${hours}小时${minutes}分`;
    } else if (minutes > 0) {
        return `${minutes}分${secs}秒`;
    } else {
        return `${secs}秒`;
    }
}

// 动态在网车辆曲线 - 状态管理
let liveCurveChartInstance = null;
let liveCurveLastDataState = null;  // 存储上次数据状态用于增量更新

// 创建新图表实例
function createLiveCurveChart(canvas, liveTimeSeries) {
    debugLog('Creating new live curve chart with', liveTimeSeries.time_points.length, 'data points');

    // 将数据转换为 {x, y} 格式以使用线性x轴
    const chartData = liveTimeSeries.time_points.map((time, index) => ({
        x: time,
        y: liveTimeSeries.total_running[index]
    }));

    const ctx = canvas.getContext('2d');
    const chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: '总在网车辆数',
                data: chartData,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,  // 允许容器控制尺寸
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            const seconds = tooltipItems[0].parsed.x;
                            // 转换为可读的HH:MM:SS格式
                            const hours = Math.floor(seconds / 3600);
                            const minutes = Math.floor((seconds % 3600) / 60);
                            const secs = seconds % 60;
                            const timeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                            return `时间: ${timeStr} (${seconds}秒)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',  // 使用线性刻度处理数值
                    title: {
                        display: true,
                        text: '仿真时间 (秒)'
                    },
                    ticks: {
                        maxTicksLimit: 15,  // 增加刻度限制以避免拥挤
                        callback: function(value, index, ticks) {
                            // 显示整数秒
                            return Math.round(value);
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '在网车辆数'
                    },
                    beginAtZero: true
                }
            }
        }
    });

    return chartInstance;
}

// 增量更新现有图表数据
function updateLiveCurveChart(chartInstance, liveTimeSeries) {
    debugLog('Updating live curve chart with', liveTimeSeries.time_points.length, 'data points');

    try {
        // 将数据转换为 {x, y} 格式
        const chartData = liveTimeSeries.time_points.map((time, index) => ({
            x: time,
            y: liveTimeSeries.total_running[index]
        }));

        // 直接替换数据数组（Chart.js会自动处理）
        chartInstance.data.datasets[0].data = chartData;

        // 使用'none'模式避免动画，提升性能
        chartInstance.update('none');

        debugLog('Chart updated successfully');
    } catch (error) {
        console.error('Error updating chart:', error);
        // 更新失败时返回false，让调用者重新创建图表
        return false;
    }

    return true;
}

// 检测数据是否发生变化
function hasDataChanged(oldData, newData) {
    if (!oldData) return true;
    if (!newData) return false;

    // 检查数据点数量是否变化
    if (oldData.time_points.length !== newData.time_points.length) {
        return true;
    }

    // 检查最后一个时间点是否不同（快速检测）
    const oldLastTime = oldData.time_points[oldData.time_points.length - 1];
    const newLastTime = newData.time_points[newData.time_points.length - 1];
    if (oldLastTime !== newLastTime) {
        return true;
    }

    // 检查最后一个车辆数是否不同
    const oldLastCount = oldData.total_running[oldData.total_running.length - 1];
    const newLastCount = newData.total_running[newData.total_running.length - 1];
    if (oldLastCount !== newLastCount) {
        return true;
    }

    return false;
}

// 检测是否需要重置图表（数据回退或仿真重启）
function shouldResetChart(oldData, newData) {
    if (!oldData) return false;
    if (!newData) return true;

    // 如果新数据点少于旧数据，说明仿真可能被重启
    if (newData.time_points.length < oldData.time_points.length) {
        debugLog('Data reset detected: new length', newData.time_points.length, '< old length', oldData.time_points.length);
        return true;
    }

    return false;
}

function renderLiveCurve(liveTimeSeries) {
    debugLogObject('renderLiveCurve', { liveTimeSeries, liveCurveVisible });

    // 动态曲线数据来源日志
    if (liveTimeSeries && liveTimeSeries.time_points && liveTimeSeries.time_points.length > 0) {
        const timeRange = `${liveTimeSeries.time_points[0]}-${liveTimeSeries.time_points[liveTimeSeries.time_points.length - 1]}s`;
        console.log(`[Live Curve] ${liveTimeSeries.time_points.length} data points (${timeRange})`);
    }

    // Phase 1.5: Use monitor canvas elements
    const section = document.getElementById('monitorLiveCurveSection');
    const canvas = document.getElementById('monitorLiveCurveChart');
    const controlBar = document.getElementById('monitorLiveCurveControlBar');
    const toggleBtn = document.getElementById('toggleMonitorCurveBtn');

    // 检查是否有数据
    const hasData = liveTimeSeries && liveTimeSeries.time_points && liveTimeSeries.time_points.length > 0;

    if (hasData) {
        debugLog('Showing live curve section with', liveTimeSeries.time_points.length, 'data points');

        // 显示控制栏（始终可见，用于切换曲线显示/隐藏）
        if (controlBar) {
            controlBar.style.display = 'flex';
        }

        // 根据liveCurveVisible显示/隐藏曲线区域
        if (section) {
            section.style.display = liveCurveVisible ? 'block' : 'none';
        }

        // 更新按钮文本
        if (toggleBtn) {
            toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
        }
    } else {
        debugLog('No live time series data');

        // 无数据时隐藏控制栏和曲线区域
        if (controlBar) {
            controlBar.style.display = 'none';
        }
        if (section) {
            section.style.display = 'none';
        }

        if (liveCurveVisible) {
            // 显示"加载中"提示
            if (canvas) {
                canvas.style.display = 'none';
            }
            // 创建提示信息
            if (section && !section.querySelector('.curve-loading-notice')) {
                const notice = document.createElement('div');
                notice.className = 'curve-loading-notice';
                notice.style.cssText = 'padding: 20px; text-align: center; color: #7f8c8d; background: white; border-radius: 4px;';
                notice.textContent = '仿真数据加载中...';
                section.appendChild(notice);
            }
            return;
        } else {
            return;
        }
    }

    // 清除加载提示
    const notice = section?.querySelector('.curve-loading-notice');
    if (notice) notice.remove();

    // 如果没有数据，不继续渲染图表
    if (!hasData) return;

    // 确保canvas显示
    if (canvas) canvas.style.display = 'block';

    // Dispatcher逻辑：决定创建新图表还是更新现有图表

    // 检查数据是否变化
    const dataChanged = hasDataChanged(liveCurveLastDataState, liveTimeSeries);

    if (!dataChanged) {
        debugLog('Data unchanged, skipping chart update');
        return;
    }

    // 检查是否需要重置图表
    const needsReset = shouldResetChart(liveCurveLastDataState, liveTimeSeries);

    if (needsReset && liveCurveChartInstance) {
        debugLog('Resetting chart due to data reset/simulation restart');
        liveCurveChartInstance.destroy();
        liveCurveChartInstance = null;
        liveCurveLastDataState = null;
    }

    // 创建或更新图表
    if (!liveCurveChartInstance) {
        // 首次创建或重置后重新创建
        liveCurveChartInstance = createLiveCurveChart(canvas, liveTimeSeries);
        // 创建后调整高度
        setTimeout(() => {
            resizeLiveCurveCanvas();
        }, 50);
    } else {
        // 增量更新
        const updateSuccess = updateLiveCurveChart(liveCurveChartInstance, liveTimeSeries);

        if (!updateSuccess) {
            // 更新失败，fallback到重新创建
            debugLog('Chart update failed, recreating chart');
            liveCurveChartInstance.destroy();
            liveCurveChartInstance = createLiveCurveChart(canvas, liveTimeSeries);
            setTimeout(() => {
                resizeLiveCurveCanvas();
            }, 50);
        } else {
            // 更新成功后调整高度
            setTimeout(() => {
                resizeLiveCurveCanvas();
            }, 50);
        }
    }

    // 保存当前数据状态
    liveCurveLastDataState = {
        time_points: [...liveTimeSeries.time_points],
        total_running: [...liveTimeSeries.total_running]
    };
}

// 动态调整 Live Curve Canvas 的高度 (基于数据点数量和上下文)
function resizeLiveCurveCanvas() {
    const canvas = document.getElementById('monitorLiveCurveChart');
    if (!canvas) return;

    // 根据图表实例数据点计算高度
    if (liveCurveChartInstance && liveCurveChartInstance.data && liveCurveChartInstance.data.datasets[0]) {
        const dataPoints = liveCurveChartInstance.data.datasets[0].data.length;

        // 动态高度计算：数据点越多，给予更多空间，但有最大限制
        let calculatedHeight = 250 + Math.min(dataPoints * 2, 150);

        // 应用高度限制
        calculatedHeight = Math.min(calculatedHeight, 400);
        calculatedHeight = Math.max(calculatedHeight, 250);

        canvas.style.maxHeight = calculatedHeight + 'px';
        debugLog('Canvas height adjusted to:', calculatedHeight, 'px for', dataPoints, 'data points');

        // 触发图表resize事件以重新绘制
        if (liveCurveChartInstance) {
            setTimeout(() => {
                liveCurveChartInstance.resize();
            }, 50);
        }
    }
}

// 切换动态在网车辆曲线的显示/隐藏
function toggleLiveCurveVisibility() {
    liveCurveVisible = !liveCurveVisible;
    debugLog('Toggle live curve visibility to:', liveCurveVisible);

    // 使用新的分离式控制栏
    const section = document.getElementById('monitorLiveCurveSection');
    const controlBar = document.getElementById('monitorLiveCurveControlBar');
    const toggleBtn = document.getElementById('toggleMonitorCurveBtn');

    // 控制栏始终保持显示（因为它包含切换按钮）
    // 曲线区域根据toggle状态显示/隐藏
    if (section) {
        section.style.display = liveCurveVisible ? 'block' : 'none';

        // 显示后调整高度
        if (liveCurveVisible) {
            setTimeout(() => {
                resizeLiveCurveCanvas();
            }, 100);
        }
    }

    // 更新按钮文本
    if (toggleBtn) {
        toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
    }
}

function getStatusIcon(status) {
    switch(status) {
        case 'completed': return '✓';
        case 'running': return '▶';
        case 'failed': return '✗';
        default: return '⏸';
    }
}

function getStatusText(status) {
    switch(status) {
        case 'completed': return '完成';
        case 'running': return '运行中...';
        case 'failed': return '失败';
        default: return '等待中...';
    }
}

async function cancelBatch() {
    if (!currentBatchId) return;

    if (!confirm('确定要取消批量仿真吗？')) return;

    try {
        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentBatchId}`,
            { method: 'DELETE' }
        );

        if (!response.ok) throw new Error('Failed to cancel batch');

        stopProgressPolling();
        switchView('config');
        currentBatchId = null;
        window.currentBatchId = null;

    } catch (error) {
        console.error('Cancel batch error:', error);
        showError('取消批量仿真失败');
    }
}

// ========== 批次卡片操作 (Phase 1.5 - 添加卡片级别控制) ==========

/**
 * 启动指定批次的仿真
 * @param {string} batchId - 批次ID
 */
async function startBatchById(batchId) {
    if (!batchId) return;

    try {
        const startResponse = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${batchId}/start`,
            { method: 'POST' }
        );

        if (!startResponse.ok) {
            throw new Error('Failed to start batch');
        }

        showSuccess('批次启动成功！');

        // 刷新批次列表以更新状态
        loadBatchHistory();

    } catch (error) {
        console.error('Start batch error:', error);
        showError('启动批次失败: ' + error.message);
    }
}

/**
 * 取消指定批次的仿真
 * @param {string} batchId - 批次ID
 */
async function cancelBatchById(batchId) {
    if (!batchId) return;

    if (!confirm('确定要取消该批次吗？取消后可以保留仿真目录并重新启动。')) return;

    try {
        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${batchId}/cancel`,
            { method: 'POST' }
        );

        if (!response.ok) throw new Error('Failed to cancel batch');

        const result = await response.json();
        const data = result.data || {};

        showSuccess(`批次已取消 (${data.cancelled_count || 0} 个任务被取消)`);

        // 刷新批次列表以更新状态
        loadBatchHistory();

    } catch (error) {
        console.error('Cancel batch error:', error);
        showError('取消批次失败: ' + error.message);
    }
}

// ========== 结果展示 ==========

async function loadResults() {
    if (!currentBatchId) return;

    try {
        // 请求包含时序数据的结果
        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentBatchId}/results?include_time_series=true`
        );

        if (!response.ok) throw new Error('Failed to load results');

        const data = await response.json();
        renderResults(data);
        renderPeakCurveChart(data);

    } catch (error) {
        console.error('Load results error:', error);
        showError('加载结果失败');
    }
}

function renderResults(data) {
    const container = document.getElementById('comparisonTable');

    // 检查容器是否存在
    if (!container) {
        console.warn('comparisonTable container not found, skipping renderResults');
        return;
    }

    // 检查数据
    if (!data || !data.plan_results) {
        container.innerHTML = '<p style="color: #999; padding: 20px;">暂无结果数据</p>';
        return;
    }

    // 创建表格
    let html = `
        <h3>方案对比结果</h3>
        <table>
            <thead>
                <tr>
                    <th>方案</th>
                    <th>平均行程时间 (s)</th>
                    <th>平均速度 (km/h)</th>
                    <th>总车辆数</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.plan_results.forEach(plan => {
        const metrics = plan.aggregated_metrics;
        const travelTime = metrics.avg_travel_time?.mean?.toFixed(1) || 'N/A';
        const speed = metrics.avg_speed?.mean?.toFixed(1) || 'N/A';
        const vehicles = metrics.total_vehicles?.mean?.toFixed(0) || 'N/A';

        html += `
            <tr>
                <td>${plan.plan_name}</td>
                <td>${travelTime}</td>
                <td>${speed}</td>
                <td>${vehicles}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ========== 在网车辆峰值曲线图表 ==========

let peakCurveChartInstance = null; // 保存Chart实例

function renderPeakCurveChart(data) {
    // 检查是否有时序数据
    const hasTimeSeries = data.plan_results.some(plan => plan.time_series);

    if (!hasTimeSeries) {
        document.getElementById('peakCurveSection').style.display = 'none';
        return;
    }

    document.getElementById('peakCurveSection').style.display = 'block';

    // 准备图表数据
    const datasets = [];
    const colors = [
        'rgb(54, 162, 235)',   // 蓝色 - 基准
        'rgb(75, 192, 192)',   // 绿色 - 方案1
        'rgb(255, 159, 64)',   // 橙色 - 方案2
        'rgb(153, 102, 255)',  // 紫色 - 方案3
        'rgb(255, 99, 132)',   // 红色 - 方案4
    ];

    let timePoints = null;
    const peakMetrics = [];

    data.plan_results.forEach((plan, index) => {
        if (!plan.time_series || !plan.time_series.running) return;

        // 使用第一个方案的时间点
        if (!timePoints) {
            timePoints = plan.time_series.time_points;
        }

        const runningMean = plan.time_series.running.mean;

        // 计算峰值指标
        const maxRunning = Math.max(...runningMean);
        const maxIndex = runningMean.indexOf(maxRunning);
        const peakTime = timePoints[maxIndex];
        const avgRunning = runningMean.reduce((a, b) => a + b, 0) / runningMean.length;

        peakMetrics.push({
            plan_name: plan.plan_name,
            max_running: maxRunning,
            peak_time: peakTime,
            avg_running: avgRunning
        });

        // 添加数据集
        datasets.push({
            label: plan.plan_name,
            data: runningMean,
            borderColor: colors[index % colors.length],
            backgroundColor: colors[index % colors.length].replace('rgb', 'rgba').replace(')', ', 0.1)'),
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 0,
            fill: false
        });
    });

    // 转换时间点为小时:分钟格式
    const timeLabels = timePoints.map(t => {
        const hours = Math.floor(t / 3600);
        const minutes = Math.floor((t % 3600) / 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    });

    // 销毁旧图表实例
    if (peakCurveChartInstance) {
        peakCurveChartInstance.destroy();
    }

    // 创建图表
    const ctx = document.getElementById('peakCurveChart').getContext('2d');
    peakCurveChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: '在网车辆峰值曲线对比',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return '时间: ' + context[0].label;
                        },
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(0) + ' 辆';
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '仿真时间'
                    },
                    ticks: {
                        maxTicksLimit: 20
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '在网车辆数 (辆)'
                    },
                    beginAtZero: true
                }
            }
        }
    });

    // 渲染峰值指标卡片
    renderPeakMetrics(peakMetrics);
}

function renderPeakMetrics(metrics) {
    const container = document.getElementById('peakMetrics');

    let html = '';
    metrics.forEach(metric => {
        const peakHours = Math.floor(metric.peak_time / 3600);
        const peakMinutes = Math.floor((metric.peak_time % 3600) / 60);
        const peakTimeStr = `${peakHours.toString().padStart(2, '0')}:${peakMinutes.toString().padStart(2, '0')}`;

        html += `
            <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0 0 10px 0; color: #667eea;">${metric.plan_name}</h4>
                <div style="font-size: 0.9rem; color: #666;">
                    <p style="margin: 5px 0;"><strong>峰值车辆数:</strong> ${metric.max_running.toFixed(0)} 辆</p>
                    <p style="margin: 5px 0;"><strong>峰值时刻:</strong> ${peakTimeStr}</p>
                    <p style="margin: 5px 0;"><strong>平均车辆数:</strong> ${metric.avg_running.toFixed(0)} 辆</p>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ========== 结果导出 ==========

async function exportResults() {
    if (!currentBatchId) return;

    // Phase 6: 使用batch_results.js中的导出函数
    if (typeof exportResultsAsCSV === 'function') {
        exportResultsAsCSV();
    } else {
        showError('导出功能暂未实现，敬请期待！(计划在 v0.9.1 中实现)');
    }
}

// ========== 加载批次结果 (Phase 6: 结果可视化) ==========

/**
 * Phase 8.4修复：从批次卡片加载结果并切换到结果视图
 *
 * @param {string} batchId - 批次ID
 * @param {string} caseId - 案例ID（可选，用于调用batch_results.js的loadBatchResults）
 */
async function loadBatchResultsAndSwitch(batchId, caseId) {
    try {
        currentBatchId = batchId;

        // 如果没有提供caseId，从currentCaseId获取或通过API查找
        if (!caseId) {
            caseId = currentCaseId || 'unknown';
        }

        // 使用batch_results.js中的加载函数
        if (typeof loadBatchResults === 'function') {
            await loadBatchResults(batchId, caseId);
        } else {
            // 备选：直接获取结果数据（如果batch_results.js未加载）
            const response = await fetch(`${API_BASE}/control/batch-optimization/batch/${batchId}/results`);
            if (!response.ok) throw new Error('Failed to fetch batch results');
            const data = await response.json();
            console.log('Batch results:', data);
            showError('结果可视化模块加载中...');
        }

        // 显示结果视图
        switchView('results');
    } catch (error) {
        console.error('Error loading batch results:', error);
        showError('加载结果失败: ' + error.message);
    }
}

// ========== 导航到优化页面 ==========

function viewOptimizationAnalysis() {
    if (!currentBatchId) {
        showError('未找到批次ID');
        return;
    }

    // 跳转到方案优化页面，传递 batch_id 参数
    window.location.href = `optimization.html?batch_id=${currentBatchId}`;
}

// ========== 批次历史管理 (Phase 1: 已升级为case分组视图) ==========

async function loadBatchHistory() {
    try {
        // 先加载所有案例
        const casesResponse = await fetch(`${API_BASE}/case/list_cases/`);
        const casesData = casesResponse.ok ? await casesResponse.json() : { cases: [] };
        const caseMetadata = {};
        const allBatches = [];

        casesData.cases.forEach(c => {
            caseMetadata[c.case_id] = c;
        });

        // 为每个案例加载该案例的批次
        for (const caseInfo of casesData.cases) {
            try {
                const params = new URLSearchParams({
                    case_id: caseInfo.case_id,
                    page: 1,
                    limit: 1000
                });

                const response = await fetch(`${API_BASE}/control/batch-optimization/batches?${params}`);
                if (response.ok) {
                    const data = await response.json();
                    const caseBatches = data.batches || [];
                    allBatches.push(...caseBatches);
                }
            } catch (e) {
                logger.warn(`Failed to load batches for case ${caseInfo.case_id}:`, e);
            }
        }

        if (allBatches.length === 0) {
            const listContainer = document.getElementById('batchList');
            const emptyState = document.getElementById('batchListEmpty');
            if (listContainer) listContainer.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        // 按案例ID分组批次并按最新创建时间排序
        renderBatchListGroupedByCase(allBatches, caseMetadata);

    } catch (error) {
        console.error('Error loading batch history:', error);
        showError('加载批次历史失败');
    }
}

/**
 * Phase 1: 按案例ID分组渲染批次列表，并按最新批次时间排序
 * @param {Array} batches - 所有批次列表
 * @param {Object} caseMetadata - 案例元数据映射 (case_id → case info)
 */
function renderBatchListGroupedByCase(batches, caseMetadata) {
    const container = document.getElementById('batchList');
    const emptyState = document.getElementById('batchListEmpty');

    if (!container) return;

    container.innerHTML = '';

    if (batches.length === 0) {
        container.innerHTML = '';
        if (emptyState) emptyState.style.display = 'block';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    // 按 case_id 分组批次
    const groupedByCase = {};
    batches.forEach(batch => {
        const caseId = batch.case_id || 'unknown';
        if (!groupedByCase[caseId]) {
            groupedByCase[caseId] = [];
        }
        groupedByCase[caseId].push(batch);
    });

    // 按最新批次创建时间排序案例组（最新的在前）
    const sortedCases = Object.entries(groupedByCase)
        .sort((a, b) => {
            const latestA = Math.max(...a[1].map(batch => new Date(batch.created_at).getTime()));
            const latestB = Math.max(...b[1].map(batch => new Date(batch.created_at).getTime()));
            return latestB - latestA;
        });

    // 渲染每个案例分组
    sortedCases.forEach(([caseId, caseBatches]) => {
        const caseInfo = caseMetadata[caseId] || { case_id: caseId, description: '' };
        const caseGroup = createCaseGroup(caseId, caseInfo, caseBatches);
        container.appendChild(caseGroup);
    });

    // Phase 8.4: 启动批次卡片进度定时刷新
    startBatchCardProgressRefresh();
}

/**
 * Phase 1: 创建案例分组元素
 * @param {string} caseId - 案例ID
 * @param {Object} caseInfo - 案例信息
 * @param {Array} caseBatches - 该案例下的所有批次
 * @returns {HTMLElement} 案例分组元素
 */
function createCaseGroup(caseId, caseInfo, caseBatches) {
    const groupEl = document.createElement('div');
    groupEl.className = 'case-group';
    groupEl.id = `case-group-${caseId}`;

    // 分组头：案例名、批次数、最新状态
    const headerEl = document.createElement('div');
    headerEl.className = 'case-group-header';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'case-group-toggle';
    toggleBtn.textContent = '[-]'; // 默认展开
    toggleBtn.onclick = (e) => {
        e.preventDefault();
        toggleCaseGroup(caseId);
    };

    const titleEl = document.createElement('div');
    titleEl.className = 'case-group-title';

    const caseIdSpan = document.createElement('span');
    caseIdSpan.className = 'case-id';
    caseIdSpan.textContent = caseId;

    const caseNameSpan = document.createElement('span');
    caseNameSpan.className = 'case-name';
    caseNameSpan.textContent = caseInfo.description || '未命名';

    const batchCountSpan = document.createElement('span');
    batchCountSpan.className = 'batch-count';
    batchCountSpan.textContent = `${caseBatches.length}个批次`;

    titleEl.appendChild(caseIdSpan);
    titleEl.appendChild(caseNameSpan);
    titleEl.appendChild(batchCountSpan);

    // 最新批次状态
    const latestBatch = caseBatches.sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
    )[0];

    const latestStatusEl = document.createElement('span');
    latestStatusEl.className = `batch-status status-${latestBatch.status}`;
    latestStatusEl.textContent = getStatusLabel(latestBatch.status);

    headerEl.appendChild(toggleBtn);
    headerEl.appendChild(titleEl);
    headerEl.appendChild(latestStatusEl);

    // 分组体：批次卡片
    const bodyEl = document.createElement('div');
    bodyEl.className = 'case-group-body';
    bodyEl.id = `case-group-body-${caseId}`;

    caseBatches
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .forEach(batch => {
            const batchCard = createBatchCard(batch);
            bodyEl.appendChild(batchCard);
        });

    groupEl.appendChild(headerEl);
    groupEl.appendChild(bodyEl);

    return groupEl;
}

/**
 * Phase 1: 创建单个批次卡片
 * @param {Object} batch - 批次数据
 * @returns {HTMLElement} 批次卡片元素
 */
function createBatchCard(batch) {
    const card = document.createElement('div');
    card.className = 'batch-history-card';
    card.id = `batch-card-${batch.batch_id}`;
    card.dataset.batchId = batch.batch_id;

    const headerDiv = document.createElement('div');
    headerDiv.className = 'batch-card-header';

    const h4 = document.createElement('h4');
    h4.textContent = batch.batch_id;

    const statusSpan = document.createElement('span');
    statusSpan.className = `batch-status ${batch.status}`;
    statusSpan.textContent = getStatusLabel(batch.status);
    statusSpan.id = `batch-status-${batch.batch_id}`;

    headerDiv.appendChild(h4);
    headerDiv.appendChild(statusSpan);

    const infoDiv = document.createElement('div');
    infoDiv.className = 'batch-card-info';

    let infoHtml = `
        <p><strong>方案数:</strong> ${batch.plan_count}</p>
        <p><strong>总任务:</strong> ${batch.total_tasks}</p>
        <p><strong>创建时间:</strong> ${new Date(batch.created_at).toLocaleString()}</p>
    `;

    if (batch.duration_seconds) {
        infoHtml += `<p><strong>耗时:</strong> ${formatDuration(batch.duration_seconds)}</p>`;
    }
    if (batch.success_rate !== undefined) {
        infoHtml += `<p><strong>成功率:</strong> ${(batch.success_rate * 100).toFixed(1)}%</p>`;
    }

    infoDiv.innerHTML = infoHtml;

    // 为运行中的批次添加进度条
    let progressHtml = '';
    if (batch.status === 'running') {
        progressHtml = `
            <div class="batch-card-progress">
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progress-bar-${batch.batch_id}" style="width: 0%">
                        <span class="progress-text" id="progress-text-${batch.batch_id}">0%</span>
                    </div>
                </div>
            </div>
        `;
    }

    const progressDiv = document.createElement('div');
    progressDiv.innerHTML = progressHtml;

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'batch-card-actions';

    // 根据状态生成不同的操作按钮
    let actionsHtml = '';
    if (batch.status === 'running') {
        actionsHtml = `
            <button class="btn btn-small btn-success" onclick="loadBatchProgressAndSwitch('${batch.batch_id}')">监控进度</button>
            <button class="btn btn-small btn-warning" onclick="cancelBatchById('${batch.batch_id}')">取消</button>
        `;
    } else if (batch.status === 'cancelled') {
        actionsHtml = `
            <button class="btn btn-small btn-primary" onclick="startBatchById('${batch.batch_id}')">启动仿真</button>
            <button class="btn btn-small btn-success" onclick="loadBatchResultsAndSwitch('${batch.batch_id}', '${batch.case_id || ''}')">查看结果</button>
            <button class="btn btn-small btn-danger" onclick="deleteBatchHistory('${batch.batch_id}')">删除</button>
        `;
    } else if (batch.status === 'completed') {
        actionsHtml = `
            <button class="btn btn-small btn-info" onclick="loadBatchProgressAndSwitch('${batch.batch_id}')">查看进度</button>
            <button class="btn btn-small btn-success" onclick="loadBatchResultsAndSwitch('${batch.batch_id}', '${batch.case_id || ''}')">查看结果</button>
            <button class="btn btn-small btn-danger" onclick="deleteBatchHistory('${batch.batch_id}')">删除</button>
        `;
    } else if (batch.status === 'failed') {
        actionsHtml = `
            <button class="btn btn-small btn-primary" onclick="startBatchById('${batch.batch_id}')">重新启动</button>
            <button class="btn btn-small btn-success" onclick="loadBatchResultsAndSwitch('${batch.batch_id}', '${batch.case_id || ''}')">查看结果</button>
            <button class="btn btn-small btn-danger" onclick="deleteBatchHistory('${batch.batch_id}')">删除</button>
        `;
    } else if (batch.status === 'pending') {
        actionsHtml = `
            <button class="btn btn-small btn-primary" onclick="startBatchById('${batch.batch_id}')">启动仿真</button>
        `;
    }

    actionsDiv.innerHTML = actionsHtml;

    card.appendChild(headerDiv);
    card.appendChild(infoDiv);
    if (batch.status === 'running') {
        card.appendChild(progressDiv);
    }
    card.appendChild(actionsDiv);

    return card;
}

/**
 * Phase 1: 切换案例分组的展开/折叠状态
 * @param {string} caseId - 案例ID
 */
function toggleCaseGroup(caseId) {
    const body = document.getElementById(`case-group-body-${caseId}`);
    const toggle = document.querySelector(`#case-group-${caseId} .case-group-toggle`);

    if (!body || !toggle) return;

    body.classList.toggle('hidden');
    toggle.textContent = body.classList.contains('hidden') ? '[+]' : '[-]';
}

// ========== 批次卡片进度更新 (Phase 8.4: 新增) ==========

let batchCardProgressInterval = null;

/**
 * 启动批次卡片进度定时刷新
 * 每5秒刷新一次运行中批次的进度条
 */
function startBatchCardProgressRefresh() {
    if (batchCardProgressInterval) {
        clearInterval(batchCardProgressInterval);
    }

    batchCardProgressInterval = setInterval(() => {
        updateAllBatchCardProgress();
    }, 5000); // 每5秒刷新一次

    // 立即更新一次
    updateAllBatchCardProgress();
}

/**
 * 停止批次卡片进度定时刷新
 */
function stopBatchCardProgressRefresh() {
    if (batchCardProgressInterval) {
        clearInterval(batchCardProgressInterval);
        batchCardProgressInterval = null;
    }
}

/**
 * 更新所有运行中批次的进度条
 */
async function updateAllBatchCardProgress() {
    const runningCards = document.querySelectorAll('[data-batch-id][data-batch-id*="batch_"]');

    for (const card of runningCards) {
        const batchId = card.dataset.batchId;
        const statusSpan = document.getElementById(`batch-status-${batchId}`);

        // 只更新运行中的批次
        if (statusSpan && statusSpan.textContent.includes('运行中')) {
            updateBatchCardProgress(batchId);
        }
    }
}

/**
 * 更新单个批次卡片的进度
 * @param {string} batchId - 批次ID
 */
async function updateBatchCardProgress(batchId) {
    try {
        // 从卡片中获取case_id（通过查找最近的case-group）
        const card = document.getElementById(`batch-card-${batchId}`);
        if (!card) return;

        const caseGroup = card.closest('.case-group');
        if (!caseGroup) return;

        const caseId = caseGroup.id.replace('case-group-', '');

        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${batchId}/progress`
        );

        if (!response.ok) {
            logger.warn(`Failed to fetch progress for batch ${batchId}`);
            return;
        }

        const data = await response.json();
        // 🔧 FIX: Convert progress from 0.0-1.0 float to 0-100 percentage
        // The API returns data.progress as a float (0.0 to 1.0)
        const progress = Math.round((data.progress || 0) * 100);

        // 更新进度条宽度
        const progressBar = document.getElementById(`progress-bar-${batchId}`);
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }

        // 更新进度文字
        const progressText = document.getElementById(`progress-text-${batchId}`);
        if (progressText) {
            progressText.textContent = `${progress}%`;
        }

        // 如果完成或失败，更新状态并停止刷新
        if (data.status && (data.status === 'completed' || data.status === 'failed')) {
            const statusSpan = document.getElementById(`batch-status-${batchId}`);
            if (statusSpan) {
                statusSpan.textContent = getStatusLabel(data.status);
                statusSpan.className = `batch-status ${data.status}`;
            }

            // 重新加载批次列表以更新状态
            loadBatchHistory();
        }

    } catch (error) {
        logger.warn(`Error updating batch progress for ${batchId}:`, error);
    }
}

function filterBatchHistory() {
    loadBatchHistory();
}

/**
 * 手动刷新批次列表
 */
async function refreshBatchList() {
    try {
        loadBatchHistory();
        showSuccess('批次列表已刷新');
    } catch (error) {
        console.error('Error refreshing batch list:', error);
        showError('刷新失败');
    }
}

async function deleteBatchHistory(batchId) {
    if (!confirm('确认删除该批次吗？此操作不可撤销。')) return;

    try {
        const response = await fetch(`${API_BASE}/control/batch-optimization/batch/${batchId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete batch');

        showSuccess('批次已删除');
        loadBatchHistory();
    } catch (error) {
        console.error('Error deleting batch:', error);
        showError('删除批次失败');
    }
}

function loadBatchProgressAndSwitch(batchId) {
    currentBatchId = batchId;
    window.currentBatchId = batchId;

    // Phase 1.5: Show current batch monitor (上栏)
    const monitor = document.getElementById('currentBatchMonitor');
    if (monitor) {
        monitor.style.display = 'block';
        document.getElementById('monitorBatchTitle').textContent = `当前监控批次: ${batchId}`;

        // Start polling for this batch
        startProgressPolling();
    }

    // Stay on monitoring view
    if (currentView !== 'monitoring') {
        switchView('monitoring');
    }
}

/**
 * 关闭当前批次监控区域
 */
function closeCurrentMonitor() {
    const monitor = document.getElementById('currentBatchMonitor');
    if (monitor) {
        monitor.style.display = 'none';
    }

    // Stop polling
    stopProgressPolling();

    currentBatchId = null;
    window.currentBatchId = null;
}

function getStatusLabel(status) {
    const labels = {
        'pending': '待运行',
        'running': '运行中',
        'completed': '已完成',
        'cancelled': '已取消',
        'failed': '失败',
        'archived': '已归档'
    };
    return labels[status] || status;
}

// ========== 工具函数 ==========
// showError 和 showSuccess 由 notification.js 提供（居中显示的提示框）
