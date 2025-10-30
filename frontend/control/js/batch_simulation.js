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
let progressPollInterval = null;
let currentView = 'config'; // config, progress, results
let liveCurveVisible = true; // 动态曲线显示状态（默认显示）

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', async () => {
    await loadCases();
    await loadPlans();

    // 绑定事件
    document.getElementById('caseSelector').addEventListener('change', onCaseChange);
    document.getElementById('createBatchBtn').addEventListener('click', createBatch);
    document.getElementById('startBatchBtn').addEventListener('click', startBatchExecution);
    document.getElementById('cancelBatchBtn').addEventListener('click', cancelBatch);
    document.getElementById('clearConfigBtn').addEventListener('click', clearConfig);
    document.getElementById('backToConfigBtn').addEventListener('click', () => switchView('config'));
    document.getElementById('viewOptimizationBtn').addEventListener('click', viewOptimizationAnalysis);
    document.getElementById('exportResultsBtn').addEventListener('click', exportResults);
    document.getElementById('toggleLiveCurveBtn').addEventListener('click', toggleLiveCurveVisibility);

    // 计算预估
    document.getElementById('numSeeds').addEventListener('input', updateEstimate);
    document.getElementById('baseSeed').addEventListener('input', updateEstimate);
});

// ========== 视图切换 ==========

function switchView(view) {
    currentView = view;

    // Update views
    document.getElementById('configView').classList.toggle('active', view === 'config');
    document.getElementById('progressView').classList.toggle('active', view === 'progress');
    document.getElementById('resultsView').classList.toggle('active', view === 'results');

    // Update tabs
    document.getElementById('configViewTab').classList.toggle('active', view === 'config');
    document.getElementById('progressViewTab').classList.toggle('active', view === 'progress');
    document.getElementById('resultsViewTab').classList.toggle('active', view === 'results');

    if (view === 'progress' && currentBatchId) {
        startProgressPolling();
    } else {
        stopProgressPolling();
    }

    if (view === 'results' && currentBatchId) {
        loadResults();
    }
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
            option.textContent = `${c.case_id} - ${c.description || ''}`;
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

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `plan-${plan.plan_id}`;
            checkbox.value = plan.plan_id;
            checkbox.checked = plan.is_baseline; // baseline自动选中
            checkbox.disabled = plan.is_baseline; // baseline不可取消
            checkbox.addEventListener('change', updateEstimate);

            const label = document.createElement('label');
            label.htmlFor = `plan-${plan.plan_id}`;
            label.textContent = `${plan.plan_name}${plan.is_baseline ? ' (必选)' : ''}`;

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

    document.getElementById('estimateText').textContent =
        `${selectedPlans.length} 个方案 × ${numSeeds} 次随机 = ${totalTasks} 次仿真`;
}

async function onCaseChange() {
    const caseId = document.getElementById('caseSelector').value;
    // 可以在这里加载case的特定配置
}

function clearConfig() {
    document.getElementById('caseSelector').value = '';
    const checkboxes = document.querySelectorAll('#planSelector input[type="checkbox"]:not([disabled])');
    checkboxes.forEach(cb => cb.checked = false);
    document.getElementById('numSeeds').value = 3;
    document.getElementById('baseSeed').value = 66;
    updateEstimate();
}

async function createBatch() {
    const caseId = document.getElementById('caseSelector').value;
    const planIds = getSelectedPlans();
    const numSeeds = parseInt(document.getElementById('numSeeds').value) || 3;
    const baseSeed = parseInt(document.getElementById('baseSeed').value) || 66;

    if (!caseId) {
        showError('请选择案例');
        return;
    }

    if (planIds.length === 0) {
        showError('请至少选择一个方案');
        return;
    }

    try {
        // 创建批次
        const createResponse = await fetch(`${API_BASE}/control/optimization/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: caseId,
                plan_ids: planIds,
                num_seeds: numSeeds,
                base_seed: baseSeed
            })
        });

        if (!createResponse.ok) {
            const error = await createResponse.json();
            throw new Error(error.detail || 'Failed to create batch');
        }

        const batch = await createResponse.json();
        currentBatchId = batch.batch_id;

        // 切换到进度视图 (批次已创建,等待启动)
        updateBatchInfo(batch);
        document.getElementById('startBatchBtn').style.display = 'inline-block';
        document.getElementById('cancelBatchBtn').style.display = 'none';
        switchView('progress');

        // 显示提示，引导用户点击启动按钮
        showSuccess('批次创建成功！请点击"启动仿真"按钮开始执行。');

    } catch (error) {
        console.error('Create batch error:', error);
        showError('创建批次失败: ' + error.message);
    }
}

async function startBatchExecution() {
    if (!currentBatchId) return;

    try {
        const startResponse = await fetch(
            `${API_BASE}/control/optimization/batch/${currentBatchId}/start`,
            { method: 'POST' }
        );

        if (!startResponse.ok) {
            throw new Error('Failed to start batch');
        }

        // 隐藏启动按钮,显示取消按钮
        document.getElementById('startBatchBtn').style.display = 'none';
        document.getElementById('cancelBatchBtn').style.display = 'inline-block';

        // 开始轮询进度
        startProgressPolling();

    } catch (error) {
        console.error('Start batch execution error:', error);
        showError('启动仿真失败: ' + error.message);
    }
}

function updateBatchInfo(batch) {
    document.getElementById('batchTitle').textContent = `批次: ${batch.batch_id}`;
    const statusText = STATUS_MAP[batch.status] || batch.status || STATUS_MAP['pending'];
    document.getElementById('batchStatus').textContent = `状态: ${statusText}`;
}

// ========== 进度监控 ==========

function startProgressPolling() {
    if (progressPollInterval) return;

    updateProgress(); // 立即更新一次
    progressPollInterval = setInterval(updateProgress, 2000); // 每2秒更新（确保及时显示曲线数据）
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
            `${API_BASE}/control/optimization/batch/${currentBatchId}/progress?t=${Date.now()}`,
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

        // 更新批次信息
        const statusText = STATUS_MAP[data.status] || data.status;
        document.getElementById('batchStatus').textContent = `状态: ${statusText}`;

        // 更新任务统计信息
        const taskStatsDiv = document.getElementById('taskStats');
        if (taskStatsDiv && data.status !== 'pending') {
            taskStatsDiv.style.display = 'block';
            document.getElementById('totalTasks').textContent = data.total_tasks || 0;
            document.getElementById('completedTasks').textContent = data.completed_tasks || 0;
            document.getElementById('runningTasks').textContent = data.running_tasks || 0;
            document.getElementById('failedTasks').textContent = data.failed_tasks || 0;

            // 显示预计完成时间
            const estimatedCompletionDiv = document.getElementById('estimatedCompletion');
            if (estimatedCompletionDiv && data.status === 'running') {
                if (data.estimated_remaining_seconds && data.estimated_remaining_seconds > 0) {
                    const remainingDisplay = formatDuration(data.estimated_remaining_seconds);
                    const completionTime = data.estimated_completion ?
                        new Date(data.estimated_completion).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}) :
                        '计算中...';
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

        // 更新总进度
        const progressPct = (data.progress * 100).toFixed(0);

        // 计算并显示详细的任务进度
        const runningTasks = data.tasks.filter(t => t.status === 'running');
        const taskProgressInfo = runningTasks.map(t => `${t.task_id}:${t.progress}%`).join(', ');
        debugLog(`Batch progress: ${progressPct}% | Running: [${taskProgressInfo}]`);

        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        if (progressBar) {
            progressBar.style.width = `${progressPct}%`;
        } else {
            console.error('progressBar element not found!');
        }

        if (progressText) {
            // 显示进度百分比（剩余时间已在上方taskStats中显示）
            progressText.textContent = `${progressPct}%`;
        } else {
            console.error('progressText element not found!');
        }

        // 更新任务详情
        renderTaskList(data.tasks || []);

        // 更新动态在网车辆曲线
        renderLiveCurve(data.live_time_series);

        // 如果完成，停止轮询（不再自动跳转，让用户查看曲线）
        if (data.status === 'completed') {
            stopProgressPolling();
            document.getElementById('cancelBatchBtn').style.display = 'none';

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
            document.getElementById('cancelBatchBtn').style.display = 'none';
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

    const container = document.getElementById('taskList');
    container.innerHTML = '';

    if (tasks.length === 0) {
        container.innerHTML = '<p class="empty-state">暂无任务</p>';
        return;
    }

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
                const progressPct = liveStatus.progress_percent || task.progress || 0;
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

// 动态在网车辆曲线
let liveCurveChartInstance = null;

function renderLiveCurve(liveTimeSeries) {
    debugLogObject('renderLiveCurve', { liveTimeSeries, liveCurveVisible });

    const controlBar = document.getElementById('liveCurveControlBar');
    const section = document.getElementById('liveCurveSection');
    const canvas = document.getElementById('liveCurveChart');
    const toggleBtn = document.getElementById('toggleLiveCurveBtn');

    // 检查是否有数据
    const hasData = liveTimeSeries && liveTimeSeries.time_points && liveTimeSeries.time_points.length > 0;

    if (hasData) {
        debugLog('Showing live curve section with', liveTimeSeries.time_points.length, 'data points');
        // 有数据时，始终显示控制栏，根据用户的toggle状态显示或隐藏图表
        if (controlBar) controlBar.style.display = 'block';
        if (section) section.style.display = liveCurveVisible ? 'block' : 'none';
        // 更新按钮文本
        if (toggleBtn) {
            toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
        }
    } else {
        debugLog('No live time series data');
        // 无数据时，始终显示控制栏（允许用户切换），根据toggle状态显示提示或隐藏
        if (controlBar) controlBar.style.display = 'block';
        if (section) {
            section.style.display = liveCurveVisible ? 'block' : 'none';
        }
        // 无数据时按钮允许用户显示空的图表区域
        if (toggleBtn) {
            toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
        }
        if (!hasData && liveCurveVisible) {
            // 显示"加载中"或"无数据"提示
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
        } else if (!hasData && !liveCurveVisible) {
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

    // 转换时间点为时:分格式
    const timeLabels = liveTimeSeries.time_points.map(t => {
        const hours = Math.floor(t / 3600);
        const minutes = Math.floor((t % 3600) / 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    });

    // 销毁旧图表实例
    if (liveCurveChartInstance) {
        liveCurveChartInstance.destroy();
    }

    // 创建简单折线图
    const ctx = canvas.getContext('2d');
    liveCurveChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: '总在网车辆数',
                data: liveTimeSeries.total_running,
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
            maintainAspectRatio: true,
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
                            const index = tooltipItems[0].dataIndex;
                            const seconds = liveTimeSeries.time_points[index];
                            return `时间: ${timeLabels[index]} (${seconds}秒)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '仿真时间'
                    },
                    ticks: {
                        maxTicksLimit: 10
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
}

// 切换动态在网车辆曲线的显示/隐藏
function toggleLiveCurveVisibility() {
    liveCurveVisible = !liveCurveVisible;
    debugLog('Toggle live curve visibility to:', liveCurveVisible);

    const section = document.getElementById('liveCurveSection');
    const toggleBtn = document.getElementById('toggleLiveCurveBtn');

    // 更新chart section显示状态
    if (section) {
        section.style.display = liveCurveVisible ? 'block' : 'none';
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
            `${API_BASE}/control/optimization/batch/${currentBatchId}`,
            { method: 'DELETE' }
        );

        if (!response.ok) throw new Error('Failed to cancel batch');

        stopProgressPolling();
        switchView('config');
        currentBatchId = null;

    } catch (error) {
        console.error('Cancel batch error:', error);
        showError('取消批量仿真失败');
    }
}

// ========== 结果展示 ==========

async function loadResults() {
    if (!currentBatchId) return;

    try {
        // 请求包含时序数据的结果
        const response = await fetch(
            `${API_BASE}/control/optimization/batch/${currentBatchId}/results?include_time_series=true`
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

    showError('导出功能暂未实现，敬请期待！(计划在 v0.9.1 中实现)');
    // TODO: v0.9.1 中实现 CSV 导出
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

// ========== 工具函数 ==========
// showError 和 showSuccess 由 notification.js 提供（居中显示的提示框）
