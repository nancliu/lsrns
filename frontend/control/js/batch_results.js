/**
 * 批量仿真结果可视化 (Phase 6: T6.1-T6.4)
 *
 * 职责：
 * - 加载批次结果数据（T6.1）
 * - 构建对比表格（T6.2）
 * - 渲染性能图表（T6.3）
 * - 计算并显示改进率（T6.4）
 */

// ========== 全局变量 ==========
let currentBatchId = null;
let currentCaseId = null;
let batchResultsData = null;

// ========== T6.1: 加载批次结果 ==========

/**
 * 从API加载批次结果数据
 * @param {string} batchId - 批次ID
 * @param {string} caseId - 案例ID
 */
async function loadBatchResults(batchId, caseId) {
    try {
        currentBatchId = batchId;
        currentCaseId = caseId;

        showLoading('加载结果中...');

        const response = await fetch(`${API_BASE}/control/batch-optimization/batch/${batchId}/results`, {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load batch results');
        }

        batchResultsData = await response.json();

        logger.info(`Loaded results for batch ${batchId}:`, batchResultsData);

        // 渲染结果视图
        renderBatchResultsView();
        hideLoading();

    } catch (error) {
        console.error('Error loading batch results:', error);
        showError('加载结果失败: ' + error.message);
    }
}

/**
 * 从API获取指定批次的结果
 * @param {string} batchId - 批次ID
 * @returns {Promise<Object>} 结果数据
 */
async function fetchBatchResults(batchId) {
    const response = await fetch(`${API_BASE}/control/batch-optimization/batch/${batchId}/results`);
    if (!response.ok) {
        throw new Error('Failed to fetch batch results');
    }
    return await response.json();
}

// ========== T6.2: 构建对比表格 ==========

/**
 * 渲染批次结果视图
 */
function renderBatchResultsView() {
    if (!batchResultsData) {
        showError('结果数据为空');
        return;
    }

    // Phase 8.4修复：支持新的 API 响应格式
    // 新格式：直接有 plan_results（列表），而不是 analysis.plan_results
    const planResults = batchResultsData.plan_results || [];
    const metadata = {
        output_level: 'standard',
        num_seeds: 3,
        base_seed: 66,
        created_at: batchResultsData.created_at,
        completed_at: batchResultsData.completed_at
    };

    // 渲染摘要信息
    renderResultsSummary(metadata);

    // Phase 8.4修复：新的数据格式需要新的处理逻辑
    if (planResults && planResults.length > 0) {
        renderNewBatchResults(planResults);
    } else {
        // 降级：尝试使用旧格式（analysis）
        const analysis = batchResultsData.analysis || {};
        const comparisonSummary = analysis.comparison_summary || {};
        if (comparisonSummary.rows && comparisonSummary.rows.length > 0) {
            renderComparisonTable(comparisonSummary, analysis.improvement_rates || {});
        }
        // 渲染性能图表 (T6.3)
        renderPerformanceCharts(analysis);
    }
}

/**
 * 渲染结果摘要卡片
 * @param {Object} metadata - 批次元数据
 */
function renderResultsSummary(metadata) {
    const summaryContainer = document.querySelector('.results-summary');
    if (!summaryContainer) return;

    const html = `
        <h3>📊 分析摘要</h3>
        <p><strong>输出级别:</strong> ${metadata.output_level || 'standard'}</p>
        <p><strong>随机种子数:</strong> ${metadata.num_seeds || 1} (起始: ${metadata.base_seed || 66})</p>
        <p><strong>分析时间:</strong> ${new Date(metadata.analyzed_at).toLocaleString()}</p>
        ${metadata.completed_at ? `<p><strong>完成时间:</strong> ${new Date(metadata.completed_at).toLocaleString()}</p>` : ''}
    `;

    summaryContainer.innerHTML = html;
}

/**
 * T6.2: 构建并渲染对比表格
 * @param {Object} comparisonSummary - 对比总结数据
 * @param {Object} improvementRates - 改进率数据
 */
function renderComparisonTable(comparisonSummary, improvementRates) {
    const container = document.getElementById('comparisonTable') || createComparisonTableContainer();

    if (!comparisonSummary.rows || comparisonSummary.rows.length === 0) {
        container.innerHTML = '<p style="color: #999; padding: 20px;">暂无对比数据</p>';
        return;
    }

    // 获取所有方案ID（除baseline）
    const planIds = Object.keys(improvementRates);

    // 构建表格HTML
    let tableHtml = '<div class="comparison-table-container"><table class="comparison-table"><thead><tr>';

    // 表头
    tableHtml += '<th>指标</th>';
    tableHtml += '<th>基准方案</th>';

    // 每个test方案两列（值 + 改进率）
    planIds.forEach(planId => {
        tableHtml += `<th colspan="2">${planId}</th>`;
    });

    tableHtml += '</tr><tr>';
    tableHtml += '<th></th><th>值</th>';

    planIds.forEach(() => {
        tableHtml += '<th>值</th><th>改进率%</th>';
    });

    tableHtml += '</tr></thead><tbody>';

    // 表体
    comparisonSummary.rows.forEach(row => {
        tableHtml += '<tr class="plan-row baseline">';
        tableHtml += `<td><strong>${row.metric_name}</strong></td>`;
        tableHtml += `<td>${formatMetricValue(row.baseline_value, row.metric)} ${row.unit}</td>`;

        // 各test方案的值和改进率
        planIds.forEach(planId => {
            const testData = row.test_values[planId] || {};
            const testValue = testData.value;
            const improvementRate = testData.improvement_rate;

            tableHtml += `<td>${formatMetricValue(testValue, row.metric)} ${row.unit}</td>`;

            // 改进率显示（带色彩）
            if (improvementRate !== null && improvementRate !== undefined) {
                const improvementClass = improvementRate > 0 ? 'positive' : 'negative';
                const sign = improvementRate > 0 ? '+' : '';
                tableHtml += `<td><span class="improvement ${improvementClass}">${sign}${improvementRate.toFixed(1)}%</span></td>`;
            } else {
                tableHtml += '<td>-</td>';
            }
        });

        tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table></div>';

    container.innerHTML = tableHtml;
}

/**
 * 创建对比表格容器
 */
function createComparisonTableContainer() {
    const resultsContainer = document.querySelector('.results-container');
    if (!resultsContainer) return null;

    const container = document.createElement('div');
    container.id = 'comparisonTable';
    container.className = 'config-section';

    const heading = document.createElement('h3');
    heading.textContent = '方案对比表';

    container.appendChild(heading);
    resultsContainer.appendChild(container);

    return container;
}

/**
 * 格式化指标值
 * @param {any} value - 值
 * @param {string} metric - 指标名
 * @returns {string} 格式化后的值
 */
function formatMetricValue(value, metric) {
    if (value === null || value === undefined) {
        return '-';
    }

    if (typeof value === 'number') {
        // 对于速度指标，保留2位小数
        if (metric === 'avgSpeed') {
            return value.toFixed(2);
        }
        // 对于整数指标
        return Math.round(value).toString();
    }

    return String(value);
}

// ========== T6.3: 性能图表渲染 ==========

/**
 * T6.3: 渲染性能对比图表
 * @param {Object} analysis - 分析数据
 */
function renderPerformanceCharts(analysis) {
    const comparisonSummary = analysis.comparison_summary || {};

    if (!comparisonSummary.rows || comparisonSummary.rows.length === 0) {
        return;
    }

    // 获取关键性能指标：avgSpeed, waiting, teleports
    const performanceMetrics = comparisonSummary.rows.filter(row =>
        ['avgSpeed', 'waiting', 'teleports'].includes(row.metric)
    );

    if (performanceMetrics.length === 0) {
        return;
    }

    // 为每个性能指标创建图表
    performanceMetrics.forEach(metric => {
        renderMetricChart(metric, analysis.improvement_rates || {});
    });
}

/**
 * 为单个指标渲染图表
 * @param {Object} metricRow - 指标行数据
 * @param {Object} improvementRates - 改进率数据
 */
function renderMetricChart(metricRow, improvementRates) {
    const chartContainerId = `chart-${metricRow.metric}`;
    let chartContainer = document.getElementById(chartContainerId);

    if (!chartContainer) {
        const chartsSection = document.querySelector('.results-charts') || createChartsSection();
        chartContainer = document.createElement('div');
        chartContainer.id = chartContainerId;
        chartContainer.className = 'metric-chart';
        chartContainer.style.marginBottom = '30px';
        chartsSection.appendChild(chartContainer);
    }

    // 准备数据
    const planIds = Object.keys(improvementRates);
    const labels = ['基准', ...planIds];
    const values = [
        metricRow.baseline_value,
        ...planIds.map(id => metricRow.test_values[id]?.value || 0)
    ];

    // 确定图表类型和配置
    const isHigherBetter = ['avgSpeed'].includes(metricRow.metric);
    const colors = [
        'rgba(200, 200, 200, 0.7)',  // 基准灰色
        ...planIds.map((_, i) => {
            const improvementRate = improvementRates[planIds[i]]?.[metricRow.metric];
            if (improvementRate === null || improvementRate === undefined) {
                return 'rgba(52, 152, 219, 0.7)';
            }
            // 改进为绿色，恶化为红色
            const isImprovement = (improvementRate > 0 && isHigherBetter) ||
                                 (improvementRate < 0 && !isHigherBetter);
            return isImprovement ? 'rgba(46, 204, 113, 0.7)' : 'rgba(231, 76, 60, 0.7)';
        })
    ];

    // 销毁旧图表
    if (window[`chart_${metricRow.metric}`]) {
        window[`chart_${metricRow.metric}`].destroy();
    }

    // 创建新图表
    const ctx = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(ctx);

    window[`chart_${metricRow.metric}`] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: metricRow.metric_name,
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: `${metricRow.metric_name} (${metricRow.unit})`
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * 创建图表容器
 */
function createChartsSection() {
    const resultsContainer = document.querySelector('.results-container');
    if (!resultsContainer) return null;

    const chartsSection = document.createElement('div');
    chartsSection.className = 'results-charts config-section';

    const heading = document.createElement('h3');
    heading.textContent = '性能对比图表';

    chartsSection.appendChild(heading);
    resultsContainer.appendChild(chartsSection);

    return chartsSection;
}

// ========== T6.4: 改进率显示 ==========

/**
 * T6.4: 计算并显示整体改进率摘要
 * @param {Object} improvementRates - 改进率数据
 */
function renderImprovementSummary(improvementRates) {
    const summaryContainer = document.createElement('div');
    summaryContainer.className = 'improvement-summary config-section';

    let summaryHtml = '<h3>🎯 改进率摘要</h3>';
    summaryHtml += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">';

    Object.entries(improvementRates).forEach(([planId, rates]) => {
        const avgImprovement = Object.values(rates).filter(v => v !== null).reduce((a, b) => a + b, 0) /
                             Object.values(rates).filter(v => v !== null).length;

        const improveClass = avgImprovement > 0 ? 'positive' : 'negative';
        const sign = avgImprovement > 0 ? '+' : '';

        summaryHtml += `
            <div style="padding: 15px; border-radius: 8px; background: #f9f9f9; border-left: 4px solid ${avgImprovement > 0 ? '#27ae60' : '#c0392b'};">
                <strong>${planId}</strong><br/>
                <span class="improvement ${improveClass}">
                    ${sign}${avgImprovement.toFixed(1)}% 平均改进
                </span>
            </div>
        `;
    });

    summaryHtml += '</div>';
    summaryContainer.innerHTML = summaryHtml;

    const resultsContainer = document.querySelector('.results-container');
    if (resultsContainer) {
        resultsContainer.insertBefore(summaryContainer, resultsContainer.firstChild);
    }
}

// ========== 工具函数 ==========

function showLoading(message = '加载中...') {
    const container = document.querySelector('.results-container') || document.body;
    container.innerHTML = `<div style="text-align: center; padding: 40px; color: #999;">${message}</div>`;
}

function hideLoading() {
    // 已在renderBatchResultsView中处理
}

function showError(message) {
    alert(`❌ ${message}`);
}

/**
 * 导出结果为CSV
 */
function exportResultsAsCSV() {
    if (!batchResultsData) {
        showError('结果数据为空');
        return;
    }

    const analysis = batchResultsData.analysis || {};
    const comparisonSummary = analysis.comparison_summary || {};

    if (!comparisonSummary.rows) {
        showError('对比数据为空');
        return;
    }

    // 构建CSV
    let csv = 'Metric,Baseline,Unit';
    const planIds = Object.keys(analysis.improvement_rates || {});
    planIds.forEach(planId => {
        csv += `,${planId},${planId} Improvement %`;
    });
    csv += '\n';

    comparisonSummary.rows.forEach(row => {
        csv += `"${row.metric_name}",${row.baseline_value},${row.unit}`;
        planIds.forEach(planId => {
            const testData = row.test_values[planId] || {};
            csv += `,${testData.value || '-'},${testData.improvement_rate || '-'}`;
        });
        csv += '\n';
    });

    // 下载
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `batch_results_${currentBatchId}_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showSuccess('结果已导出为CSV');
}

function showSuccess(message) {
    alert(`✅ ${message}`);
}

/**
 * Phase 8.4新增：渲染新格式的批次结果（plan_results）
 * @param {Array} planResults - 方案结果列表
 */
function renderNewBatchResults(planResults) {
    const container = document.getElementById('comparisonTable') || createComparisonTableContainer();

    if (!planResults || planResults.length === 0) {
        container.innerHTML = '<p style="color: #999; padding: 20px;">暂无结果数据</p>';
        return;
    }

    // 构建对比表格
    let tableHtml = '<div class="comparison-table-container"><table class="comparison-table"><thead><tr>';

    // 获取基准方案（通常是第一个）
    const baselinePlan = planResults[0];
    const testPlans = planResults.slice(1);

    // 表头
    tableHtml += '<th>指标</th>';
    tableHtml += '<th colspan="2">基准方案</th>';

    testPlans.forEach(plan => {
        tableHtml += `<th colspan="2">${plan.plan_name}</th>`;
    });

    tableHtml += '</tr><tr>';
    tableHtml += '<th></th><th>均值</th><th>标准差</th>';

    testPlans.forEach(() => {
        tableHtml += '<th>均值</th><th>改进%</th>';
    });

    tableHtml += '</tr></thead><tbody>';

    // 提取所有指标名称
    const metricKeys = baselinePlan.aggregated_metrics ? Object.keys(baselinePlan.aggregated_metrics) : [];

    metricKeys.forEach(metricKey => {
        const baselineMetrics = baselinePlan.aggregated_metrics[metricKey] || {};

        tableHtml += '<tr>';
        tableHtml += `<td><strong>${metricKey}</strong></td>`;
        tableHtml += `<td>${(baselineMetrics.mean || 0).toFixed(2)}</td>`;
        tableHtml += `<td>${(baselineMetrics.std || 0).toFixed(2)}</td>`;

        testPlans.forEach(testPlan => {
            const testMetrics = testPlan.aggregated_metrics[metricKey] || {};
            const testMean = testMetrics.mean || 0;
            const baselineMean = baselineMetrics.mean || 0;

            // 简单计算改进率 (对于速度：越高越好，对于延误：越低越好)
            let improvementRate = 0;
            if (baselineMean !== 0) {
                improvementRate = ((testMean - baselineMean) / baselineMean) * 100;
                // 对于某些指标需要反向（如延误时间）
                if (metricKey.includes('delay') || metricKey.includes('waiting')) {
                    improvementRate = -improvementRate;
                }
            }

            tableHtml += `<td>${testMean.toFixed(2)}</td>`;

            const improvementClass = improvementRate > 0 ? 'positive' : 'negative';
            const sign = improvementRate > 0 ? '+' : '';
            tableHtml += `<td><span class="improvement ${improvementClass}">${sign}${improvementRate.toFixed(1)}%</span></td>`;
        });

        tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table></div>';
    container.innerHTML = tableHtml;
}
