/**
 * 批量优化仿真 JavaScript
 *
 * 功能:
 * - 批量仿真配置
 * - 进度监控(轮询)
 * - 结果展示
 */

const API_BASE = '/api/v1';

// 全局状态
let currentBatchId = null;
let progressPollInterval = null;
let currentView = 'config'; // config, progress, results

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', async () => {
    await loadCases();
    await loadPlans();

    // 绑定事件
    document.getElementById('caseSelect').addEventListener('change', onCaseChange);
    document.getElementById('startBatchBtn').addEventListener('click', startBatch);
    document.getElementById('cancelBatchBtn').addEventListener('click', cancelBatch);
    document.getElementById('backToConfigBtn').addEventListener('click', () => switchView('config'));
    document.getElementById('viewResultsBtn').addEventListener('click', () => switchView('results'));

    // 计算预估
    document.getElementById('numSeeds').addEventListener('input', updateEstimate);
});

// ========== 视图切换 ==========

function switchView(view) {
    currentView = view;

    document.getElementById('configView').style.display = view === 'config' ? 'block' : 'none';
    document.getElementById('progressView').style.display = view === 'progress' ? 'block' : 'none';
    document.getElementById('resultsView').style.display = view === 'results' ? 'block' : 'none';

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
        const select = document.getElementById('caseSelect');
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
        const container = document.getElementById('plansList');
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
    const checkboxes = document.querySelectorAll('#plansList input[type="checkbox"]:checked');
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
    const caseId = document.getElementById('caseSelect').value;
    // 可以在这里加载case的特定配置
}

async function startBatch() {
    const caseId = document.getElementById('caseSelect').value;
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

        // 启动批次
        const startResponse = await fetch(
            `${API_BASE}/control/optimization/batch/${currentBatchId}/start`,
            { method: 'POST' }
        );

        if (!startResponse.ok) {
            throw new Error('Failed to start batch');
        }

        // 切换到进度视图
        switchView('progress');

    } catch (error) {
        console.error('Start batch error:', error);
        showError('启动批量仿真失败: ' + error.message);
    }
}

// ========== 进度监控 ==========

function startProgressPolling() {
    if (progressPollInterval) return;

    updateProgress(); // 立即更新一次
    progressPollInterval = setInterval(updateProgress, 2000); // 每2秒更新
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
        const response = await fetch(
            `${API_BASE}/control/optimization/batch/${currentBatchId}/progress`
        );

        if (!response.ok) throw new Error('Failed to get progress');

        const data = await response.json();

        // 更新总进度
        const progressPct = (data.progress * 100).toFixed(0);
        document.getElementById('progressBar').style.width = `${progressPct}%`;
        document.getElementById('progressText').textContent =
            `${progressPct}% (${data.completed_tasks}/${data.total_tasks})`;

        // 更新任务详情
        renderTaskList(data.tasks);

        // 如果完成，停止轮询并显示查看结果按钮
        if (data.status === 'completed' || data.status === 'failed') {
            stopProgressPolling();
            document.getElementById('viewResultsBtn').style.display =
                data.status === 'completed' ? 'inline-block' : 'none';
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

    const container = document.getElementById('tasksList');
    container.innerHTML = '';

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
            const text = `Seed ${task.seed}: ${getStatusText(task.status)}`;

            taskDiv.innerHTML = `<span class="task-icon">${icon}</span> ${text}`;
            planDiv.appendChild(taskDiv);
        });

        container.appendChild(planDiv);
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
        const response = await fetch(
            `${API_BASE}/control/optimization/batch/${currentBatchId}/results`
        );

        if (!response.ok) throw new Error('Failed to load results');

        const data = await response.json();
        renderResults(data);

    } catch (error) {
        console.error('Load results error:', error);
        showError('加载结果失败');
    }
}

function renderResults(data) {
    const container = document.getElementById('resultsTable');

    // 创建表格
    let html = `
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

// ========== 工具函数 ==========

function showError(message) {
    alert('错误: ' + message);
}

function showSuccess(message) {
    alert('成功: ' + message);
}
