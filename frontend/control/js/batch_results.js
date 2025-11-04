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
// Note: currentBatchId and currentCaseId are declared in batch_simulation.js
// to avoid duplicate declaration errors when both scripts are loaded
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

        const response = await fetch(`${API_BASE}/control/batch-optimization/batch/${batchId}/results`, {
            method: 'GET'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to load batch results');
        }

        batchResultsData = await response.json();

        // 渲染结果视图
        renderBatchResultsView();

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
        renderEmptyResultsState();
        return;
    }

    // Phase 8.4: 统一使用新的 API 响应格式
    // 新格式：plan_results（列表）、created_at、completed_at 都在顶级
    const planResults = batchResultsData.plan_results || [];
    const metadata = {
        output_level: batchResultsData.output_level || 'standard',
        num_seeds: batchResultsData.num_seeds || 3,
        base_seed: batchResultsData.base_seed || 66,
        created_at: batchResultsData.created_at,
        completed_at: batchResultsData.completed_at,
        analyzed_at: batchResultsData.analyzed_at
    };

    // 渲染摘要信息
    renderResultsSummary(metadata);

    // Phase 8.4: 完全使用新的实现（不降级）
    if (planResults && planResults.length > 0) {
        renderNewBatchResults(planResults);
    } else {
        // 如果没有 plan_results，显示错误信息而不是降级
        const container = document.getElementById('comparisonTable') || createComparisonTableContainer();
        container.innerHTML = '<p style="color: #e74c3c; padding: 20px;">❌ 结果数据格式错误或为空</p>';
        console.error('Expected plan_results in API response, but got:', batchResultsData);
    }
}

/**
 * 渲染结果摘要卡片
 * @param {Object} metadata - 批次元数据
 */
function renderResultsSummary(metadata) {
    const summaryContainer = document.querySelector('.results-summary');
    if (!summaryContainer) return;

    // Phase 8.4: 适配新的数据格式
    const analyzedAt = metadata.analyzed_at ? new Date(metadata.analyzed_at).toLocaleString() : '未知';
    const completedAt = metadata.completed_at ? new Date(metadata.completed_at).toLocaleString() : '未知';

    const html = `
        <h3>📊 分析摘要</h3>
        <p><strong>输出级别:</strong> ${metadata.output_level || 'standard'}</p>
        <p><strong>随机种子数:</strong> ${metadata.num_seeds || 1} (起始: ${metadata.base_seed || 66})</p>
        ${metadata.analyzed_at ? `<p><strong>分析时间:</strong> ${analyzedAt}</p>` : ''}
        <p><strong>完成时间:</strong> ${completedAt}</p>
    `;

    summaryContainer.innerHTML = html;
}

/**
 * 渲染空状态 - 当没有选中批次时显示
 * 功能：提示用户如何使用结果页面
 */
function renderEmptyResultsState() {
    // 清空对比表格
    const comparisonTable = document.getElementById('comparisonTable');
    if (comparisonTable) {
        comparisonTable.innerHTML = `
            <div style="
                background: #f5f7fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                padding: 40px 20px;
                text-align: center;
                color: #7f8c8d;
            ">
                <h3 style="font-size: 1.5em; margin: 0 0 15px 0; color: #34495e;">📋 暂无批次结果</h3>
                <p style="margin: 0 0 20px 0; font-size: 1.05em;">
                    请先在<strong style="color: #2980b9;">批次监控</strong>中选择一个批次
                </p>
                <div style="
                    background: white;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    border-radius: 4px;
                    text-align: left;
                    display: inline-block;
                    margin-bottom: 20px;
                ">
                    <p style="margin: 5px 0; color: #555;"><strong>✓ 方式 1（推荐）：</strong> 返回批次监控，点击任意批次卡片上的 <strong>"查看结果"</strong> 按钮</p>
                    <p style="margin: 5px 0; color: #555;"><strong>✓ 方式 2：</strong> 如已查看过批次结果，直接点击此标签栏查看</p>
                </div>
                <button class="btn btn-primary" onclick="switchView('monitoring')" style="padding: 10px 20px;">
                    返回批次监控 →
                </button>
            </div>
        `;
    }

    // 隐藏峰值曲线图表
    const peakCurveSection = document.getElementById('peakCurveSection');
    if (peakCurveSection) {
        peakCurveSection.style.display = 'none';
    }
}

/**
 * [已弃用] T6.2: 旧的对比表格渲染函数
 * Phase 8.4: 替换为 renderNewBatchResults()
 * 保留此函数以防降级使用，但不应该被调用
 * @deprecated 使用 renderNewBatchResults() 代替
 */
function renderComparisonTable(comparisonSummary, improvementRates) {
    // Phase 8.4: 此函数已被弃用，应使用 renderNewBatchResults()
    console.warn('[Deprecated] renderComparisonTable() is deprecated. Use renderNewBatchResults() instead.');
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

// ========== [已弃用] T6.3: 性能图表渲染 ==========

/**
 * [已弃用] T6.3: 旧的性能对比图表渲染
 * Phase 8.4: 此函数已被弃用
 * @deprecated 新的实现应该直接使用 renderNewBatchResults()
 */
function renderPerformanceCharts(analysis) {
    console.warn('[Deprecated] renderPerformanceCharts() is deprecated. Use renderNewBatchResults() instead.');
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

    // Phase 2: 获取指标元数据配置（来自API响应）
    let metricConfig = batchResultsData.metric_config || {};

    // 如果 API 没有返回 metric_config，使用本地 fallback
    if (Object.keys(metricConfig).length === 0) {
        console.warn('⚠️ API 未返回 metric_config，使用 fallback 配置');
        metricConfig = {
            "step": { "label": "仿真步数", "unit": "秒", "direction": "verification", "is_verification_metric": true },
            "ended": { "label": "已完成车数", "unit": "辆", "direction": "higher" },
            "waiting": { "label": "等待车数", "unit": "辆", "direction": "lower" },
            "running": { "label": "当前运行车数", "unit": "辆", "direction": "lower" },
            "teleports": { "label": "传送次数", "unit": "次", "direction": "lower" },
            "inserted": { "label": "已插入车数", "unit": "辆", "direction": "higher" },
            "loaded": { "label": "已加载车数", "unit": "辆", "direction": "neutral" },
            "collisions": { "label": "碰撞次数", "unit": "次", "direction": "lower" },
            "avgSpeed": { "label": "平均速度", "unit": "m/s", "direction": "higher" }
        };
    }

    // 🔍 调试：验证metric_config是否正确接收
    console.log('📊 [DEBUG] 批次结果数据:', {
        hasData: !!batchResultsData,
        hasMetricConfig: !!batchResultsData?.metric_config,
        metricConfigKeys: Object.keys(batchResultsData?.metric_config || {})
    });
    console.log('✅ metricConfig:', metricConfig);

    // 获取基准方案（通常是第一个）
    const baselinePlan = planResults[0];
    const testPlans = planResults.slice(1);

    // 提取所有指标名称
    const allMetricKeys = baselinePlan.aggregated_metrics ? Object.keys(baselinePlan.aggregated_metrics) : [];

    // 🎯 区分对比指标和验证指标
    const comparisonMetrics = [];
    const verificationMetrics = [];

    allMetricKeys.forEach(metricKey => {
        const config = metricConfig[metricKey] || {};
        // 如果是验证指标（direction为verification或is_verification_metric为true）则分开处理
        if (config.direction === 'verification' || config.is_verification_metric === true || metricKey === 'step') {
            verificationMetrics.push(metricKey);
        } else {
            comparisonMetrics.push(metricKey);
        }
    });

    console.log('📊 指标分类:', {
        comparisonCount: comparisonMetrics.length,
        verificationCount: verificationMetrics.length,
        comparisonMetrics: comparisonMetrics,
        verificationMetrics: verificationMetrics
    });

    // 构建对比表格
    let tableHtml = '<div class="comparison-table-container">';

    // 对比指标表格
    tableHtml += '<h3 style="margin-top: 20px; margin-bottom: 10px;">🎯 交通性能对比指标（' + comparisonMetrics.length + '个）</h3>';
    tableHtml += '<table class="comparison-table"><thead><tr>';

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

    // 只渲染对比指标（不包括验证指标）
    comparisonMetrics.forEach(metricKey => {
        const baselineMetrics = baselinePlan.aggregated_metrics[metricKey] || {};

        // Phase 2: 使用元数据获取中文标签和单位
        // 处理键名大小写不匹配的情况（查找 metricConfig 中匹配的键）
        let config = metricConfig[metricKey] || {};

        // 如果未找到且键名包含大小写混合，尝试查找匹配的键
        if (Object.keys(config).length === 0) {
            // 尝试找到大小写不敏感的匹配
            const matchingKey = Object.keys(metricConfig).find(
                key => key.toLowerCase() === metricKey.toLowerCase()
            );
            if (matchingKey) {
                config = metricConfig[matchingKey];
                console.log(`🔍 键名修正: ${metricKey} → ${matchingKey}`);
            }
        }

        const metricLabel = config.label || metricKey;
        const unit = config.unit || '';
        const direction = config.direction || 'neutral';

        tableHtml += '<tr>';
        // 显示中文标签而非英文键名
        tableHtml += `<td><strong>${metricLabel}</strong> ${unit ? `<span style="color: #999; font-size: 0.9em;">(${unit})</span>` : ''}</td>`;
        tableHtml += `<td>${(baselineMetrics.mean || 0).toFixed(2)}</td>`;
        tableHtml += `<td>${(baselineMetrics.std || 0).toFixed(2)}</td>`;

        testPlans.forEach(testPlan => {
            const testMetrics = testPlan.aggregated_metrics[metricKey] || {};
            const testMean = testMetrics.mean || 0;
            const baselineMean = baselineMetrics.mean || 0;

            // Phase 2: 根据 direction 正确计算改进率
            let improvementRate = 0;
            if (baselineMean !== 0) {
                const rawChange = ((testMean - baselineMean) / baselineMean) * 100;
                
                // 根据指标元数据的方向来判断改进
                if (direction === 'lower') {
                    // 越低越好：减少是改进，所以负变化 = 正改进
                    improvementRate = -rawChange;
                } else if (direction === 'higher') {
                    // 越高越好：增加是改进，所以正变化 = 正改进
                    improvementRate = rawChange;
                } else {
                    // 中立（不计算改进率）
                    improvementRate = null;
                }
            }

            tableHtml += `<td>${testMean.toFixed(2)}</td>`;

            // 只有在有改进率时才显示
            if (improvementRate !== null) {
                const improvementClass = improvementRate > 0 ? 'positive' : 'negative';
                const sign = improvementRate > 0 ? '+' : '';
                tableHtml += `<td><span class="improvement ${improvementClass}">${sign}${improvementRate.toFixed(1)}%</span></td>`;
            } else {
                tableHtml += `<td><span style="color: #999;">-</span></td>`;
            }
        });

        tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table>';

    // 添加验证指标区块
    if (verificationMetrics.length > 0) {
        tableHtml += '<h3 style="margin-top: 30px; margin-bottom: 10px;">🔍 仿真验证指标（' + verificationMetrics.length + '个）</h3>';
        tableHtml += '<div style="padding: 15px; background-color: #f0f8ff; border-left: 4px solid #3498db; border-radius: 4px;">';

        verificationMetrics.forEach(metricKey => {
            const config = metricConfig[metricKey] || {};
            const metricLabel = config.label || metricKey;
            const unit = config.unit || '';

            const baselineMetrics = baselinePlan.aggregated_metrics[metricKey] || {};
            const baselineMean = baselineMetrics.mean || 0;

            // 验证仿真完整性
            // Step 从 0 开始计数，不是从 1 开始（第一步是 0）
            // 判断逻辑：所有计划的 step 值应该都相等（因为它们在同一个案例中运行时长相同）
            const allStepValues = [];
            planResults.forEach(plan => {
                if (plan.aggregated_metrics && plan.aggregated_metrics[metricKey]) {
                    allStepValues.push(plan.aggregated_metrics[metricKey].mean || 0);
                }
            });

            // 验证所有计划的 step 值是否一致（允许 <1 秒的差异）
            let isComplete = true;
            if (allStepValues.length > 0) {
                const minStep = Math.min(...allStepValues);
                const maxStep = Math.max(...allStepValues);
                isComplete = (maxStep - minStep) < 1; // 所有值应该几乎相等
            }

            const status = isComplete ? '✅ 完整执行' : '⚠️ 未完整';

            tableHtml += `<div style="margin-bottom: 8px; font-size: 14px;">`;
            tableHtml += `<strong>${metricLabel}</strong> (${unit}): `;
            tableHtml += `${baselineMean.toFixed(2)} ${unit} — ${status}`;
            tableHtml += `</div>`;
        });

        tableHtml += '</div>';
    }

    tableHtml += '</div>';
    container.innerHTML = tableHtml;

    // T6.3: 在表格下方添加图表可视化
    renderResultsCharts(planResults);
}

// ========== T6.3: 图表可视化实现 ==========

/**
 * T6.3: 使用Chart.js渲染批次结果图表
 * @param {Array} planResults - 方案结果列表
 */
function renderResultsCharts(planResults) {
    if (!planResults || planResults.length === 0) {
        return;
    }

    const container = document.getElementById('comparisonTable');
    if (!container) return;

    // 创建图表容器
    const chartsContainer = document.createElement('div');
    chartsContainer.className = 'charts-container';
    chartsContainer.style.marginTop = '30px';
    chartsContainer.style.display = 'grid';
    chartsContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(400px, 1fr))';
    chartsContainer.style.gap = '20px';

    // 获取所有指标
    const allMetricKeys = planResults[0].aggregated_metrics ? Object.keys(planResults[0].aggregated_metrics) : [];

    // 过滤出对比指标（排除验证指标）
    const metricConfig = batchResultsData.metric_config || {};
    const comparisonMetrics = allMetricKeys.filter(metricKey => {
        const config = metricConfig[metricKey] || {};
        return !(config.direction === 'verification' || config.is_verification_metric === true || metricKey === 'step');
    });

    // 为每个对比指标创建图表（显示全部8个，分多行布局）
    const mainMetrics = comparisonMetrics; // 显示所有对比指标

    mainMetrics.forEach(metricKey => {
        const chartDiv = document.createElement('div');
        chartDiv.style.position = 'relative';
        chartDiv.style.height = '300px';
        chartDiv.style.backgroundColor = '#f9f9f9';
        chartDiv.style.padding = '15px';
        chartDiv.style.borderRadius = '8px';
        chartDiv.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';

        const canvas = document.createElement('canvas');
        canvas.id = `chart-${metricKey}`;
        canvas.style.maxHeight = '100%';

        chartDiv.appendChild(canvas);
        chartsContainer.appendChild(chartDiv);

        // 在下一个事件循环中渲染图表（确保DOM已更新）
        setTimeout(() => {
            renderMetricChart(canvas.id, metricKey, planResults, metricConfig);
        }, 0);
    });

    container.appendChild(chartsContainer);
}

/**
 * T6.3: 为单个指标渲染柱状图
 * @param {string} canvasId - Canvas元素ID
 * @param {string} metricKey - 指标名称
 * @param {Array} planResults - 方案结果列表
 * @param {Object} metricConfig - 指标配置元数据
 */
function renderMetricChart(canvasId, metricKey, planResults, metricConfig) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    try {
        // 获取指标的中文标签和单位
        const config = metricConfig[metricKey] || {};
        const metricLabel = config.label || metricKey;
        const unit = config.unit || '';

        // 准备数据
        const planNames = [];
        const meanValues = [];
        const stdValues = [];
        const colors = [];

        // 颜色方案：基准方案用灰色，其他方案用渐变色
        const colorScheme = ['#95a5a6', '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'];

        planResults.forEach((plan, index) => {
            planNames.push(plan.plan_name);
            const metrics = plan.aggregated_metrics[metricKey] || {};
            meanValues.push(metrics.mean || 0);
            stdValues.push(metrics.std || 0);
            colors.push(colorScheme[index % colorScheme.length]);
        });

        // 创建图表
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: planNames,
                datasets: [
                    {
                        label: `${metricLabel} - 均值 ${unit ? `(${unit})` : ''}`,
                        data: meanValues,
                        backgroundColor: colors,
                        borderColor: colors,
                        borderWidth: 1,
                        borderRadius: 4,
                        yAxisID: 'y'
                    },
                    {
                        label: `${metricLabel} - 标准差 ${unit ? `(${unit})` : ''}`,
                        data: stdValues,
                        backgroundColor: colors.map(c => c + '33'),
                        borderColor: colors,
                        borderWidth: 1,
                        borderRadius: 4,
                        yAxisID: 'y1',
                        order: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${metricLabel} ${unit ? `(${unit})` : ''} - 方案对比`,
                        font: { size: 14, weight: 'bold' },
                        padding: 10
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            font: { size: 11 },
                            padding: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 10,
                        titleFont: { size: 12 },
                        bodyFont: { size: 11 },
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y || 0;
                                return `${context.dataset.label}: ${value.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: false,
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {
                            font: { size: 10 }
                        },
                        title: {
                            display: true,
                            text: '均值'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            font: { size: 10 }
                        },
                        title: {
                            display: true,
                            text: '标准差'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error(`Error rendering chart for ${metricKey}:`, error);
    }
}

/**
 * T6.3: 渲染改进率对比图表
 * @param {Array} planResults - 方案结果列表
 */
function renderImprovementRateChart(planResults) {
    if (planResults.length <= 1) return; // 需要至少2个方案来计算改进率

    const container = document.querySelector('.charts-container') || document.getElementById('comparisonTable');
    if (!container) return;

    const chartDiv = document.createElement('div');
    chartDiv.style.position = 'relative';
    chartDiv.style.height = '300px';
    chartDiv.style.backgroundColor = '#f9f9f9';
    chartDiv.style.padding = '15px';
    chartDiv.style.borderRadius = '8px';
    chartDiv.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    chartDiv.style.marginTop = '20px';

    const canvas = document.createElement('canvas');
    canvas.id = 'improvement-rate-chart';

    chartDiv.appendChild(canvas);
    container.appendChild(chartDiv);

    setTimeout(() => {
        renderImprovementRateChartData(canvas.id, planResults);
    }, 0);
}

/**
 * T6.3: 实际渲染改进率图表数据
 * @param {string} canvasId - Canvas元素ID
 * @param {Array} planResults - 方案结果列表
 */
function renderImprovementRateChartData(canvasId, planResults) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    try {
        const baselinePlan = planResults[0];
        const testPlans = planResults.slice(1);

        // 获取第一个指标的改进率作为示例
        const firstMetricKey = baselinePlan.aggregated_metrics ? Object.keys(baselinePlan.aggregated_metrics)[0] : null;
        if (!firstMetricKey) return;

        const baselineMetric = baselinePlan.aggregated_metrics[firstMetricKey];
        const baselineMean = baselineMetric?.mean || 0;

        const testPlanNames = [];
        const improvementRates = [];
        const colors = [];

        testPlans.forEach((plan, index) => {
            testPlanNames.push(plan.plan_name);
            const testMetric = plan.aggregated_metrics[firstMetricKey] || {};
            const testMean = testMetric.mean || 0;

            let rate = 0;
            if (baselineMean !== 0) {
                rate = ((testMean - baselineMean) / baselineMean) * 100;
            }

            improvementRates.push(rate);
            colors.push(rate > 0 ? '#2ecc71' : '#e74c3c');
        });

        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: testPlanNames,
                datasets: [{
                    label: '相对基准方案的改进率(%)',
                    data: improvementRates,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${firstMetricKey} - 改进率对比`,
                        font: { size: 14, weight: 'bold' },
                        padding: 10
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.x;
                                const sign = value > 0 ? '+' : '';
                                return `${sign}${value.toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering improvement rate chart:', error);
    }
}
