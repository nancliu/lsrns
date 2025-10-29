/**
 * 方案优化分析 JavaScript
 *
 * 功能:
 * - 从URL参数加载批次结果
 * - 显示详细的方案对比分析
 * - 在网车辆峰值曲线可视化
 * - 多指标雷达图对比
 */

const API_BASE = '/api/v1';

// 全局状态
let currentBatchId = null;
let batchData = null;
let peakCurveChart = null;
let radarChart = null;

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', async () => {
    // 从URL参数读取batch_id
    const urlParams = new URLSearchParams(window.location.search);
    const batchId = urlParams.get('batch_id');

    if (batchId) {
        // URL包含batch_id，直接加载该批次结果
        currentBatchId = batchId;
        await loadBatchResults(batchId);
    } else {
        // 显示批次选择界面
        showBatchSelector();
    }

    // 绑定事件
    document.getElementById('backToBatchBtn').addEventListener('click', backToBatchSimulation);
    document.getElementById('exportReportBtn').addEventListener('click', exportReport);
});

// ========== 批次选择 ==========

async function showBatchSelector() {
    document.getElementById('batchSelectorSection').style.display = 'block';
    document.getElementById('batchInfoSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';

    await loadBatchesList();
}

async function loadBatchesList() {
    try {
        // TODO: 实现 GET /api/v1/control/optimization/batches API
        // 暂时显示提示
        const container = document.getElementById('batchSelectorContainer');
        container.innerHTML = `
            <div class="empty-state">
                <h3>批次列表功能开发中...</h3>
                <p>请从批量仿真页面完成仿真后查看结果</p>
                <a href="simulations.html" class="btn btn-primary" style="display: inline-block; margin-top: 20px;">返回批量仿真</a>
            </div>
        `;
    } catch (error) {
        console.error('Load batches error:', error);
    }
}

// ========== 加载批次结果 ==========

async function loadBatchResults(batchId) {
    try {
        // 显示加载状态
        document.getElementById('batchSelectorSection').style.display = 'none';
        document.getElementById('batchInfoSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'block';

        // 加载结果数据（包含时序数据）
        const response = await fetch(
            `${API_BASE}/control/optimization/batch/${batchId}/results?include_time_series=true`
        );

        if (!response.ok) {
            throw new Error('Failed to load batch results');
        }

        batchData = await response.json();

        // 渲染批次信息
        renderBatchInfo(batchData);

        // 渲染结果
        renderComparisonTable(batchData);
        renderPeakCurveChart(batchData);
        renderRadarChart(batchData);

    } catch (error) {
        console.error('Load batch results error:', error);
        showError('加载批次结果失败: ' + error.message);
    }
}

// ========== 批次信息展示 ==========

function renderBatchInfo(data) {
    const container = document.getElementById('batchInfoContainer');

    const completedAt = data.completed_at ? new Date(data.completed_at).toLocaleString('zh-CN') : '未知';

    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            <div class="info-card">
                <div class="info-label">批次ID</div>
                <div class="info-value">${data.batch_id}</div>
            </div>
            <div class="info-card">
                <div class="info-label">案例</div>
                <div class="info-value">${data.case_id || '未知'}</div>
            </div>
            <div class="info-card">
                <div class="info-label">方案数量</div>
                <div class="info-value">${data.plan_results.length} 个</div>
            </div>
            <div class="info-card">
                <div class="info-label">完成时间</div>
                <div class="info-value">${completedAt}</div>
            </div>
        </div>
    `;
}

// ========== 方案对比表格 ==========

function renderComparisonTable(data) {
    const container = document.getElementById('comparisonTableContainer');

    if (!data.plan_results || data.plan_results.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无方案结果</div>';
        return;
    }

    // 找到基准方案
    const baselinePlan = data.plan_results.find(p => p.plan_id === 'baseline_plan');
    const baselineMetrics = baselinePlan ? baselinePlan.aggregated_metrics : null;

    let html = `
        <table>
            <thead>
                <tr>
                    <th>方案名称</th>
                    <th>平均行程时间 (s)</th>
                    <th>相比基准</th>
                    <th>平均速度 (km/h)</th>
                    <th>相比基准</th>
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

        // 计算相比基准的改善
        let travelTimeChange = '-';
        let speedChange = '-';

        if (baselineMetrics && plan.plan_id !== 'baseline_plan') {
            if (metrics.avg_travel_time?.mean && baselineMetrics.avg_travel_time?.mean) {
                const pct = ((metrics.avg_travel_time.mean - baselineMetrics.avg_travel_time.mean) / baselineMetrics.avg_travel_time.mean * 100);
                const icon = pct < 0 ? '↓' : '↑';
                const color = pct < 0 ? 'green' : 'red';
                travelTimeChange = `<span style="color: ${color};">${icon} ${Math.abs(pct).toFixed(1)}%</span>`;
            }

            if (metrics.avg_speed?.mean && baselineMetrics.avg_speed?.mean) {
                const pct = ((metrics.avg_speed.mean - baselineMetrics.avg_speed.mean) / baselineMetrics.avg_speed.mean * 100);
                const icon = pct > 0 ? '↑' : '↓';
                const color = pct > 0 ? 'green' : 'red';
                speedChange = `<span style="color: ${color};">${icon} ${Math.abs(pct).toFixed(1)}%</span>`;
            }
        }

        html += `
            <tr>
                <td><strong>${plan.plan_name}</strong></td>
                <td>${travelTime}</td>
                <td>${travelTimeChange}</td>
                <td>${speed}</td>
                <td>${speedChange}</td>
                <td>${vehicles}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ========== 在网车辆峰值曲线 ==========

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
    if (peakCurveChart) {
        peakCurveChart.destroy();
    }

    // 创建图表
    const ctx = document.getElementById('peakCurveChart').getContext('2d');
    peakCurveChart = new Chart(ctx, {
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
                        size: 18
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
    const container = document.getElementById('peakMetricsContainer');

    let html = '';
    metrics.forEach(metric => {
        const peakHours = Math.floor(metric.peak_time / 3600);
        const peakMinutes = Math.floor((metric.peak_time % 3600) / 60);
        const peakTimeStr = `${peakHours.toString().padStart(2, '0')}:${peakMinutes.toString().padStart(2, '0')}`;

        html += `
            <div class="metric-card">
                <h4>${metric.plan_name}</h4>
                <div class="metric-item">
                    <span class="metric-label">峰值车辆数:</span>
                    <span class="metric-value">${metric.max_running.toFixed(0)} 辆</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">峰值时刻:</span>
                    <span class="metric-value">${peakTimeStr}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">平均车辆数:</span>
                    <span class="metric-value">${metric.avg_running.toFixed(0)} 辆</span>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ========== 雷达图对比 ==========

function renderRadarChart(data) {
    if (!data.plan_results || data.plan_results.length === 0) {
        document.getElementById('radarChartSection').style.display = 'none';
        return;
    }

    document.getElementById('radarChartSection').style.display = 'block';

    // 准备雷达图数据
    const labels = [
        '平均速度',
        '行程时间',
        '总车辆数',
        '峰值车辆数',
        '系统稳定性'
    ];

    const datasets = [];
    const colors = [
        'rgba(54, 162, 235, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(255, 159, 64, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 99, 132, 0.6)',
    ];

    // 找到各指标的最大值用于归一化
    let maxSpeed = 0;
    let maxTravelTime = 0;
    let maxVehicles = 0;
    let maxPeakRunning = 0;

    data.plan_results.forEach(plan => {
        const metrics = plan.aggregated_metrics;
        if (metrics.avg_speed?.mean) maxSpeed = Math.max(maxSpeed, metrics.avg_speed.mean);
        if (metrics.avg_travel_time?.mean) maxTravelTime = Math.max(maxTravelTime, metrics.avg_travel_time.mean);
        if (metrics.total_vehicles?.mean) maxVehicles = Math.max(maxVehicles, metrics.total_vehicles.mean);
        if (plan.time_series?.running?.mean) {
            const peakRunning = Math.max(...plan.time_series.running.mean);
            maxPeakRunning = Math.max(maxPeakRunning, peakRunning);
        }
    });

    data.plan_results.forEach((plan, index) => {
        const metrics = plan.aggregated_metrics;

        // 归一化数据（0-100）
        const speedScore = metrics.avg_speed?.mean ? (metrics.avg_speed.mean / maxSpeed * 100) : 0;
        // 行程时间越小越好，所以需要反转
        const travelTimeScore = metrics.avg_travel_time?.mean ? ((maxTravelTime - metrics.avg_travel_time.mean) / maxTravelTime * 100) : 0;
        const vehiclesScore = metrics.total_vehicles?.mean ? (metrics.total_vehicles.mean / maxVehicles * 100) : 0;

        let peakRunningScore = 0;
        if (plan.time_series?.running?.mean) {
            const peakRunning = Math.max(...plan.time_series.running.mean);
            // 峰值越小越好，所以需要反转
            peakRunningScore = maxPeakRunning > 0 ? ((maxPeakRunning - peakRunning) / maxPeakRunning * 100) : 0;
        }

        // 系统稳定性：基于标准差，标准差越小越稳定
        const stabilityScore = metrics.avg_speed?.std ? (1 / (1 + metrics.avg_speed.std) * 100) : 50;

        datasets.push({
            label: plan.plan_name,
            data: [speedScore, travelTimeScore, vehiclesScore, peakRunningScore, stabilityScore],
            backgroundColor: colors[index % colors.length],
            borderColor: colors[index % colors.length].replace('0.6', '1'),
            borderWidth: 2
        });
    });

    // 销毁旧图表实例
    if (radarChart) {
        radarChart.destroy();
    }

    // 创建雷达图
    const ctx = document.getElementById('radarChart').getContext('2d');
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
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
                    text: '多指标综合对比（归一化）',
                    font: {
                        size: 18
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            }
        }
    });
}

// ========== 导航和导出 ==========

function backToBatchSimulation() {
    window.location.href = 'simulations.html';
}

async function exportReport() {
    alert('报告导出功能开发中...');
    // TODO: 实现报告导出（PDF/Excel）
}

// ========== 工具函数 ==========

function showError(message) {
    alert('错误: ' + message);
}
