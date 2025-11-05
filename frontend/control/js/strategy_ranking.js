/**
 * 控制策略排序结果展示 (Layer 2)
 *
 * 页面位置：方案优化 (optimization.html)
 *
 * 职责：
 * - 从 batch_id 参数自动加载批次数据
 * - 自动触发策略排序分析
 * - 加载并展示排序结果
 * - 渲染排序表格和推荐等级
 * - 展示雷达图表和分数对比
 *
 * 架构：两层分离
 * - Layer 1（simulations.html）: 批次结果分析 - 8 个基础指标对比
 * - Layer 2（optimization.html）: 控制策略排序 - 多准则评分和推荐
 */

// ========== API 配置 ==========
// 注意：API_BASE 在 batch_simulation.js 中已定义
// 在 optimization.html 中需要定义（该页面不加载 batch_simulation.js）
if (typeof API_BASE === 'undefined') {
    var API_BASE = '/api/v1';
}

// ========== 全局变量 ==========
let rankingResultsData = null;
let rankingCharts = {};
let currentBatchId = null;
let currentCaseId = null;
let batchResultsData = null; // 批次结果数据（包含批次元数据）

// ========== 初始化：从 URL 参数加载批次 ==========

/**
 * 页面加载时初始化 - 从 URL 参数获取 batch_id，或从 localStorage 恢复上次查看的批次
 *
 * URL 格式: optimization.html?batch_id=batch_20251105_000102&case_id=case_20251103_141612
 *
 * 如果 URL 中没有参数，尝试加载：
 * 1. localStorage 中保存的上次查看的批次
 * 2. 若无，尝试加载最新完成的批次
 */
function initializeRankingPage() {
    // 从 URL 获取参数
    const params = new URLSearchParams(window.location.search);
    currentBatchId = params.get('batch_id');
    currentCaseId = params.get('case_id');

    // 如果 URL 中没有参数，尝试从 localStorage 恢复
    if (!currentBatchId || !currentCaseId) {
        const lastBatchId = localStorage.getItem('lastViewedBatchId');
        const lastCaseId = localStorage.getItem('lastViewedCaseId');

        if (lastBatchId && lastCaseId) {
            console.log(`📋 从 localStorage 恢复上次查看的批次: ${lastBatchId}`);
            currentBatchId = lastBatchId;
            currentCaseId = lastCaseId;
        } else {
            console.warn('缺少批次信息，尝试加载最新完成的批次...');
            // 尝试加载最新完成的批次
            loadLatestCompletedBatch();
            return;
        }
    }

    // 保存当前查看的批次到 localStorage
    localStorage.setItem('lastViewedBatchId', currentBatchId);
    localStorage.setItem('lastViewedCaseId', currentCaseId);

    // 自动加载排序结果
    loadAndDisplayRanking();
}

/**
 * 加载并展示排序结果
 */
async function loadAndDisplayRanking() {
    try {
        // 显示加载指示器
        showLoadingIndicator('正在加载批次信息...');

        // 步骤1: 先加载批次结果数据（包含批次元数据）
        const batchResponse = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentBatchId}/results`,
            {
                method: 'GET'
            }
        );

        if (!batchResponse.ok) {
            const error = await batchResponse.json();
            throw new Error(error.detail || '加载批次结果失败');
        }

        batchResultsData = await batchResponse.json();
        console.log('Batch Results Data:', batchResultsData);

        // 显示批次信息面板
        renderBatchInfoPanel(batchResultsData);

        // 步骤2: 更新加载提示
        showLoadingIndicator('正在生成优化方案...');

        // 构建请求
        const request = {
            case_id: currentCaseId,
            batch_id: currentBatchId,
            baseline_plan_id: 'baseline_plan',
            ranking_criteria: {
                effectiveness_weight: 0.40,
                coverage_weight: 0.25,
                efficiency_weight: 0.20,
                reliability_weight: 0.15
            }
        };

        // 发送请求
        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request)
            }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '策略排序失败');
        }

        rankingResultsData = await response.json();
        console.log('Ranking Results:', rankingResultsData);

        // 隐藏加载指示器
        hideLoadingIndicator();

        // 显示排序结果
        renderRankingResults();

        showSuccess('优化方案生成成功');

    } catch (error) {
        console.error('Error loading ranking:', error);
        hideLoadingIndicator();
        showError('生成优化方案失败: ' + error.message);
    }
}

/**
 * 加载最新完成的批次
 * 当用户从导航栏进入优化方案页面，但没有指定批次时调用
 * 逻辑：
 * 1. 获取所有案例
 * 2. 对每个案例，获取批次列表
 * 3. 找到最新完成的批次
 * 4. 加载该批次的排序结果
 */
async function loadLatestCompletedBatch() {
    try {
        showLoadingIndicator('正在查找最新批次...');

        // 获取案例列表
        const casesResponse = await fetch(`${API_BASE}/data/case-management/cases`);
        if (!casesResponse.ok) {
            throw new Error('无法获取案例列表');
        }

        const casesData = await casesResponse.json();
        const cases = casesData.cases || [];

        let latestBatch = null;
        let latestCaseId = null;
        let latestCompletedTime = null;

        // 遍历所有案例，找到最新完成的批次
        for (const caseItem of cases) {
            try {
                const caseId = caseItem.case_id;
                // 获取该案例的批次列表
                const batchesResponse = await fetch(
                    `${API_BASE}/control/batch-optimization/case/${caseId}/batches`
                );

                if (!batchesResponse.ok) continue;

                const batchesData = await batchesResponse.json();
                const batches = batchesData.batches || [];

                // 找到已完成的批次中最新的
                for (const batch of batches) {
                    if (batch.status === 'completed' && batch.completed_at) {
                        const completedTime = new Date(batch.completed_at);
                        if (!latestCompletedTime || completedTime > latestCompletedTime) {
                            latestCompletedTime = completedTime;
                            latestBatch = batch;
                            latestCaseId = caseId;
                        }
                    }
                }
            } catch (error) {
                console.warn(`无法获取案例 ${caseItem.case_id} 的批次列表:`, error);
                continue;
            }
        }

        if (!latestBatch || !latestCaseId) {
            hideLoadingIndicator();
            showError('未找到已完成的批次，请从批量仿真页面创建并运行批次');
            return;
        }

        console.log(`✅ 找到最新完成的批次: ${latestBatch.batch_id} (${latestCaseId})`);

        // 加载找到的最新批次
        currentBatchId = latestBatch.batch_id;
        currentCaseId = latestCaseId;

        // 保存到 localStorage
        localStorage.setItem('lastViewedBatchId', currentBatchId);
        localStorage.setItem('lastViewedCaseId', currentCaseId);

        // 加载排序结果
        await loadAndDisplayRanking();

    } catch (error) {
        console.error('Error loading latest batch:', error);
        hideLoadingIndicator();
        showError('加载最新批次失败: ' + error.message);
    }
}

// ========== 4.1.2: 实现排序请求逻辑 ==========

/**
 * 触发策略排序分析
 */
async function triggerStrategyRanking() {
    try {
        // 验证必要数据
        if (!currentBatchId || !currentCaseId) {
            showError('缺少批次或案例信息');
            return;
        }

        if (!batchResultsData || !batchResultsData.plan_results || batchResultsData.plan_results.length < 2) {
            showError('需要至少包含基准方案和1个测试方案');
            return;
        }

        // 显示加载指示器
        showLoadingIndicator('正在生成优化方案...');

        // 构建请求
        const request = {
            case_id: currentCaseId,
            batch_id: currentBatchId,
            baseline_plan_id: 'baseline_plan',
            // strategy_plan_ids: 不指定，让后端自动检测
            ranking_criteria: {
                effectiveness_weight: 0.40,
                coverage_weight: 0.25,
                efficiency_weight: 0.20,
                reliability_weight: 0.15
            }
        };

        // 发送请求
        const response = await fetch(
            `${API_BASE}/control/batch-optimization/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request)
            }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '策略排序失败');
        }

        rankingResultsData = await response.json();
        console.log('Ranking Results:', rankingResultsData);

        // 隐藏加载指示器
        hideLoadingIndicator();

        // 显示排序结果
        renderRankingResults();

        // 显示下载按钮
        const reportButton = document.getElementById('btn-download-report');
        if (reportButton) {
            reportButton.style.display = 'block';
        }

        showSuccess('优化方案生成成功');

    } catch (error) {
        console.error('Error triggering ranking:', error);
        hideLoadingIndicator();
        showError('生成优化方案失败: ' + error.message);
    }
}

// ========== 4.1.3: 创建排序结果展示模块 ==========

/**
 * 渲染排序结果 (Layer 2: 控制策略排序)
 *
 * 位置：optimization.html
 * 容器：resultsSection (页面设计中已定义)
 *
 * 约束：
 * - 独立页面展示，与 Layer 1 (simulations.html) 完全分离
 * - 使用 optimization.html 中的 #resultsSection 容器
 * - 清晰的两层架构
 */
function renderRankingResults() {
    if (!rankingResultsData) {
        console.warn('No ranking results to render');
        return;
    }

    // Layer 2: 获取优化页面的结果容器
    const resultsSection = document.getElementById('resultsSection');
    if (!resultsSection) {
        console.error('Results section not found in optimization.html');
        return;
    }

    // 清空旧内容并显示容器
    resultsSection.innerHTML = '';
    resultsSection.style.display = 'block';

    // ===== 第一部分：排序摘要卡片 =====
    const summaryCard = document.createElement('div');
    summaryCard.className = 'ranking-section'; // ✅ 使用 CSS 类

    const summaryTitle = document.createElement('h3');
    summaryTitle.textContent = '🎯 策略排序摘要';
    summaryCard.appendChild(summaryTitle);

    // 添加摘要信息
    const summary = document.createElement('div');
    summary.className = 'ranking-summary-box'; // ✅ 使用 CSS 类代替内联样式

    const topStrategy = rankingResultsData.ranked_strategies[0];
    const metadata = rankingResultsData.ranking_metadata || {};

    summary.innerHTML = `
        <strong>🏆 首推策略: ${topStrategy.plan_name}</strong><br>
        总体评分 <span style="color: #2196F3; font-weight: bold;">${topStrategy.overall_score.toFixed(1)}/100</span>，
        推荐等级为"<strong>${topStrategy.recommendation}</strong>"。<br><br>
        📊 本次评估共纳入 <strong>${metadata.total_strategies}</strong> 个控制策略。
        系统采用多准则评估方法，综合考虑策略的有效性、覆盖率、效率和可靠性，
        为交通管理者提供科学的决策支持。
    `;

    summaryCard.appendChild(summary);
    resultsSection.appendChild(summaryCard);

    // ===== 第二部分：排序表格 =====
    const tableCard = document.createElement('div');
    tableCard.className = 'ranking-section'; // ✅ 使用 CSS 类

    const tableTitle = document.createElement('h3');
    tableTitle.textContent = '📋 策略排序表';
    tableCard.appendChild(tableTitle);

    renderRankingTable(tableCard);
    resultsSection.appendChild(tableCard);

    // ===== 第三部分：首推方案详情 =====
    const detailCard = document.createElement('div');
    detailCard.className = 'ranking-section'; // ✅ 使用 CSS 类

    const detailTitle = document.createElement('h3');
    detailTitle.textContent = '✨ 首推方案详情';
    detailCard.appendChild(detailTitle);

    renderTopStrategyDetails(detailCard, topStrategy);
    resultsSection.appendChild(detailCard);

    // ===== 第四部分：可视化图表 =====
    renderRankingCharts(resultsSection);
}


/**
 * 渲染排序表格
 */
function renderRankingTable(container) {
    if (!rankingResultsData.ranked_strategies) {
        return;
    }

    const table = document.createElement('table');
    table.className = 'ranking-table'; // ✅ 使用 CSS 类定义样式

    // 表头
    const thead = document.createElement('thead');
    thead.className = 'ranking-table-head'; // ✅ 使用 CSS 类
    thead.innerHTML = `
        <tr>
            <th style="padding: 12px; text-align: left;">排名</th>
            <th style="padding: 12px; text-align: left;">策略名称</th>
            <th style="padding: 12px; text-align: center;">总体评分</th>
            <th style="padding: 12px; text-align: center;">推荐等级</th>
            <th style="padding: 12px; text-align: center;">有效性</th>
            <th style="padding: 12px; text-align: center;">覆盖率</th>
            <th style="padding: 12px; text-align: center;">效率</th>
            <th style="padding: 12px; text-align: center;">可靠性</th>
        </tr>
    `;
    table.appendChild(thead);

    // 表体
    const tbody = document.createElement('tbody');
    rankingResultsData.ranked_strategies.forEach((strategy, index) => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #ddd';
        row.style.backgroundColor = index % 2 === 0 ? '#fff' : '#f9f9f9';

        const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1;
        const recommendationColor = getRecommendationColor(strategy.recommendation);
        const scoreColor = getScoreColor(strategy.overall_score);

        row.innerHTML = `
            <td style="padding: 12px;">${rankEmoji}</td>
            <td style="padding: 12px;">${escapeHTML(strategy.plan_name)}</td>
            <td style="padding: 12px; text-align: center; font-weight: bold; color: ${scoreColor};">
                ${strategy.overall_score.toFixed(1)}
            </td>
            <td style="padding: 12px; text-align: center;">
                <span style="${recommendationColor}">${strategy.recommendation}</span>
            </td>
            <td style="padding: 12px; text-align: center;">${strategy.scores.effectiveness.toFixed(1)}</td>
            <td style="padding: 12px; text-align: center;">${strategy.scores.coverage.toFixed(1)}</td>
            <td style="padding: 12px; text-align: center;">${strategy.scores.efficiency.toFixed(1)}</td>
            <td style="padding: 12px; text-align: center;">${strategy.scores.reliability.toFixed(1)}</td>
        `;

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

/**
 * 渲染首推方案详情
 */
function renderTopStrategyDetails(container, strategy) {
    const detailsDiv = document.createElement('div');
    detailsDiv.style.marginBottom = '30px';

    const title = document.createElement('h3');
    title.textContent = '⭐ 首推方案详情';
    title.style.color = '#1976D2';
    title.style.marginBottom = '15px';
    detailsDiv.appendChild(title);

    // 评分卡片
    const cardsContainer = document.createElement('div');
    cardsContainer.style.display = 'grid';
    cardsContainer.style.gridTemplateColumns = 'repeat(4, 1fr)';
    cardsContainer.style.gap = '15px';
    cardsContainer.style.marginBottom = '20px';

    const dimensions = [
        { label: '有效性', key: 'effectiveness', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
        { label: '覆盖率', key: 'coverage', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
        { label: '效率', key: 'efficiency', color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
        { label: '可靠性', key: 'reliability', color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }
    ];

    dimensions.forEach(dim => {
        const card = document.createElement('div');
        card.style.background = dim.color;
        card.style.color = 'white';
        card.style.padding = '20px';
        card.style.borderRadius = '8px';
        card.style.textAlign = 'center';
        card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';

        card.innerHTML = `
            <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">${dim.label}</div>
            <div style="font-size: 2em; font-weight: bold;">${strategy.scores[dim.key].toFixed(1)}</div>
        `;

        cardsContainer.appendChild(card);
    });

    detailsDiv.appendChild(cardsContainer);
    container.appendChild(detailsDiv);
}

/**
 * 渲染排序图表
 */
function renderRankingCharts(container) {
    const chartsDiv = document.createElement('div');
    chartsDiv.style.marginTop = '30px';

    const title = document.createElement('h3');
    title.textContent = '📈 可视化分析';
    title.style.color = '#1976D2';
    title.style.marginBottom = '15px';
    chartsDiv.appendChild(title);

    // 图表容器
    const chartContainer = document.createElement('div');
    chartContainer.style.display = 'grid';
    chartContainer.style.gridTemplateColumns = '1fr 1fr';
    chartContainer.style.gap = '30px';
    chartContainer.style.marginBottom = '20px';

    // 雷达图
    const radarWrapper = document.createElement('div');
    radarWrapper.style.backgroundColor = '#fafafa';
    radarWrapper.style.padding = '20px';
    radarWrapper.style.borderRadius = '4px';
    radarWrapper.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
    radarWrapper.innerHTML = `
        <h4 style="text-align: center; margin-bottom: 15px; color: #1976D2;">策略评分雷达图</h4>
        <canvas id="radarChart" style="max-height: 300px;"></canvas>
    `;
    chartContainer.appendChild(radarWrapper);

    // 对比图
    const comparisonWrapper = document.createElement('div');
    comparisonWrapper.style.backgroundColor = '#fafafa';
    comparisonWrapper.style.padding = '20px';
    comparisonWrapper.style.borderRadius = '4px';
    comparisonWrapper.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
    comparisonWrapper.innerHTML = `
        <h4 style="text-align: center; margin-bottom: 15px; color: #1976D2;">评分分布对比</h4>
        <canvas id="comparisonChart" style="max-height: 300px;"></canvas>
    `;
    chartContainer.appendChild(comparisonWrapper);

    chartsDiv.appendChild(chartContainer);
    container.appendChild(chartsDiv);

    // 渲染图表
    setTimeout(() => {
        renderRadarChart();
        renderComparisonChart();
    }, 100);
}

/**
 * 渲染雷达图
 */
function renderRadarChart() {
    const canvas = document.getElementById('radarChart');
    if (!canvas || !rankingResultsData) {
        return;
    }

    const top3 = rankingResultsData.ranked_strategies.slice(0, 3);
    const labels = ['有效性', '覆盖率', '效率', '可靠性'];

    const datasets = top3.map((strategy, index) => {
        const colors = [
            { border: 'rgb(102, 126, 234)', bg: 'rgba(102, 126, 234, 0.1)' },
            { border: 'rgb(240, 147, 251)', bg: 'rgba(240, 147, 251, 0.1)' },
            { border: 'rgb(79, 172, 254)', bg: 'rgba(79, 172, 254, 0.1)' }
        ];

        return {
            label: strategy.plan_name,
            data: [
                strategy.scores.effectiveness,
                strategy.scores.coverage,
                strategy.scores.efficiency,
                strategy.scores.reliability
            ],
            borderColor: colors[index].border,
            backgroundColor: colors[index].bg,
            borderWidth: 2,
            fill: true
        };
    });

    // 销毁旧图表
    if (rankingCharts.radar) {
        rankingCharts.radar.destroy();
    }

    const ctx = canvas.getContext('2d');
    rankingCharts.radar = new Chart(ctx, {
        type: 'radar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

/**
 * 渲染对比柱状图
 */
function renderComparisonChart() {
    const canvas = document.getElementById('comparisonChart');
    if (!canvas || !rankingResultsData) {
        return;
    }

    const strategies = rankingResultsData.ranked_strategies;
    const labels = strategies.map(s => s.plan_name);

    const datasets = [
        {
            label: '有效性',
            data: strategies.map(s => s.scores.effectiveness),
            backgroundColor: 'rgba(102, 126, 234, 0.8)'
        },
        {
            label: '覆盖率',
            data: strategies.map(s => s.scores.coverage),
            backgroundColor: 'rgba(240, 147, 251, 0.8)'
        },
        {
            label: '效率',
            data: strategies.map(s => s.scores.efficiency),
            backgroundColor: 'rgba(79, 172, 254, 0.8)'
        },
        {
            label: '可靠性',
            data: strategies.map(s => s.scores.reliability),
            backgroundColor: 'rgba(67, 233, 123, 0.8)'
        }
    ];

    // 销毁旧图表
    if (rankingCharts.comparison) {
        rankingCharts.comparison.destroy();
    }

    const ctx = canvas.getContext('2d');
    rankingCharts.comparison = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// ========== 4.1.4: 集成排序结果到批次页面 ==========

/**
 * 下载排序报告
 */
function downloadRankingReport() {
    if (!rankingResultsData || !rankingResultsData.report_file) {
        showError('报告文件路径不可用');
        return;
    }

    // 打开报告
    window.open(rankingResultsData.report_file, '_blank');
}

// ========== 工具函数 ==========

// ========== 批次信息面板 ==========

/**
 * 渲染批次信息面板 - 显示批次的完整概览
 * 复用 batch_results.js 中的实现
 * 包括：案例信息、创建时间、仿真参数、方案列表等
 * @param {Object} batchData - 批次数据
 */
function renderBatchInfoPanel(batchData) {
    // 查找 optimization.html 中的结果容器
    const container = document.getElementById('batchInfoContainer');
    if (!container) {
        console.warn('Batch info container not found in optimization.html');
        return;
    }

    // DEBUG: 检查仿真配置数据
    console.log('[DEBUG] Batch simulation config:', {
        num_seeds: batchData.num_seeds,
        base_seed: batchData.base_seed,
        simulation_duration: batchData.simulation_duration,
        output_config: batchData.output_config
    });

    // 移除旧的批次信息面板（防止重复）
    const existingPanel = container.querySelector('.batch-info-panel');
    if (existingPanel) {
        existingPanel.remove();
    }

    // 创建批次信息面板（顶部标题 + 网格布局）
    let infoPanelHtml = '<div class="batch-info-panel">';
    infoPanelHtml += '<div class="batch-info-header">';

    // 标题
    infoPanelHtml += '<h3>📌 批次概览</h3>';

    // 批次ID 在标题行显示
    if (batchData.batch_id) {
        infoPanelHtml += `<p class="batch-id"><strong>批次ID:</strong> <code>${batchData.batch_id}</code></p>`;
    }
    infoPanelHtml += '</div>'; // 结束 batch-info-header

    // 信息网格容器（3列布局，对比方案网格显示）
    infoPanelHtml += '<div class="batch-info-grid">';

    // 1. 案例信息
    infoPanelHtml += '<div class="batch-info-card">';
    infoPanelHtml += '<h4>📋 案例信息</h4>';

    // 从新增的case_info字段中获取数据（优先级最高）
    if (batchData.case_info) {
        const caseInfo = batchData.case_info;
        const caseName = caseInfo.case_name || caseInfo.case_id || '未知';
        infoPanelHtml += `<p><strong>${caseName}</strong></p>`;

        if (caseInfo.case_id) {
            infoPanelHtml += `<p class="text-muted">ID: ${caseInfo.case_id}</p>`;
        }

        // 显示时间范围（开始时间保留日期，结束时间只显示时间，避免日期重复）
        if (caseInfo.time_range && (caseInfo.time_range.start || caseInfo.time_range.end)) {
            const startTime = caseInfo.time_range.start || '未知';
            const endTime = caseInfo.time_range.end || '未知';
            // 提取结束时间的纯时间部分 (HH:MM:SS 格式)
            const endTimeOnly = endTime && endTime.includes(' ') ? endTime.split(' ')[1] : endTime;
            infoPanelHtml += `<p class="text-highlight"><strong>案例时间:</strong> ${startTime} - ${endTimeOnly}</p>`;
        }

        if (caseInfo.description) {
            infoPanelHtml += `<p class="text-muted"><em>${caseInfo.description}</em></p>`;
        }
    } else if (batchData.caseInfo && batchData.caseInfo.case_name) {
        // 备选：使用旧的caseInfo格式
        infoPanelHtml += `<p><strong>${batchData.caseInfo.case_name}</strong></p>`;
        if (batchData.caseInfo.case_id) {
            infoPanelHtml += `<p class="text-muted">ID: ${batchData.caseInfo.case_id}</p>`;
        }
    } else if (batchData.case_id) {
        // 备选：直接使用case_id（现在已在API响应中）
        infoPanelHtml += `<p><strong>案例ID:</strong> <code>${batchData.case_id}</code></p>`;
    } else {
        infoPanelHtml += `<p class="text-muted">暂无信息</p>`;
    }

    infoPanelHtml += '</div>';

    // 2. 执行时间
    infoPanelHtml += '<div class="batch-info-card">';
    infoPanelHtml += '<h4>⏰ 执行时间</h4>';
    const createdAt = batchData.created_at ? new Date(batchData.created_at).toLocaleString('zh-CN') : '未知';
    const completedAt = batchData.completed_at ? new Date(batchData.completed_at).toLocaleString('zh-CN') : '进行中';
    infoPanelHtml += `<p><strong>创建:</strong> ${createdAt}</p>`;
    infoPanelHtml += `<p><strong>完成:</strong> ${completedAt}</p>`;
    if (batchData.duration_seconds) {
        infoPanelHtml += `<p class="text-highlight"><strong>耗时:</strong> ${formatDurationFromSeconds(batchData.duration_seconds)}</p>`;
    }
    infoPanelHtml += '</div>';

    // 3. 仿真配置
    infoPanelHtml += '<div class="batch-info-card">';
    infoPanelHtml += '<h4>⚙️ 仿真配置</h4>';
    infoPanelHtml += `<p><strong>种子数:</strong> ${batchData.num_seeds || 3}</p>`;
    infoPanelHtml += `<p><strong>起始种子:</strong> ${batchData.base_seed || 66}</p>`;

    // 显示仿真时长
    if (batchData.simulation_duration && typeof batchData.simulation_duration === 'object') {
        const duration = batchData.simulation_duration;
        const hours = duration.hours || 0;
        const minutes = duration.minutes || 0;
        const durationText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
        infoPanelHtml += `<p class="text-highlight"><strong>仿真时长:</strong> ${durationText}</p>`;
        console.log('[DEBUG] simulation_duration displayed:', durationText);
    } else {
        console.log('[DEBUG] simulation_duration not available:', batchData.simulation_duration);
    }

    // 输出配置详情
    if (batchData.output_config && typeof batchData.output_config === 'object' && Object.keys(batchData.output_config).length > 0) {
        const outputConfig = batchData.output_config;
        const configs = [];

        if (outputConfig.output_tripinfo) configs.push('✓ tripinfo');
        if (outputConfig.output_emission) configs.push('✓ E1检测器');
        if (outputConfig.output_edgedata) configs.push('✓ edgedata');
        if (outputConfig.output_netstate || outputConfig.output_vehroute) {
            configs.push('✓ summary');
        }

        if (configs.length > 0) {
            const configsText = configs.join(' • ');
            infoPanelHtml += `<p><strong>仿真输出配置:</strong> ${configsText}</p>`;
            console.log('[DEBUG] output_config displayed:', configs);
        }
    }
    infoPanelHtml += '</div>';

    // 4. 对比方案（网格布局，3列显示）
    if (batchData.plan_results && batchData.plan_results.length > 0) {
        infoPanelHtml += '<div class="batch-info-card batch-info-card-full">';
        infoPanelHtml += '<h4>📊 对比方案</h4>';
        infoPanelHtml += '<div class="batch-plans-grid">';
        batchData.plan_results.forEach((plan, index) => {
            const planName = plan.plan_name || plan.plan_id || `方案 ${index + 1}`;
            const isBaseline = plan.is_baseline ? ' <span class="baseline-badge">基准</span>' : '';
            const samplesInfo = plan.sample_count ? ` (${plan.sample_count})` : '';
            infoPanelHtml += `<div class="batch-plan-item"><strong>${planName}</strong>${isBaseline}<span class="text-muted">${samplesInfo}</span></div>`;
        });
        infoPanelHtml += '</div>';
        infoPanelHtml += '</div>';
    }

    infoPanelHtml += '</div>'; // 结束 batch-info-grid
    infoPanelHtml += '</div>'; // 结束 batch-info-panel

    // 插入到容器中
    container.innerHTML = infoPanelHtml;

    // 添加样式
    addBatchInfoStyles();
}

/**
 * 添加批次信息面板的样式
 */
function addBatchInfoStyles() {
    // 检查样式是否已添加
    if (document.getElementById('batch-info-styles')) return;

    const style = document.createElement('style');
    style.id = 'batch-info-styles';
    style.textContent = `
        /* 主面板 */
        .batch-info-panel {
            background: linear-gradient(135deg, #f5f9ff 0%, #f0f6ff 100%);
            border: 1px solid #d6e4f5;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
        }

        /* 头部区域（标题 + Batch ID） */
        .batch-info-header {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(52, 152, 219, 0.15);
        }

        .batch-info-header h3 {
            color: #2c3e50;
            font-size: 1.3em;
            margin: 0;
            font-weight: 600;
        }

        .batch-id {
            color: #1a1a1a;
            font-size: 1em;
            margin: 0;
            font-weight: 700;
        }

        .batch-id code {
            background: white;
            color: #1a1a1a;
            padding: 2px 8px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            font-weight: 700;
        }

        /* 网格容器 */
        .batch-info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }

        /* 网格卡片 */
        .batch-info-card {
            background: white;
            border: 1px solid #ecf0f1;
            border-radius: 6px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            transition: box-shadow 0.2s ease;
        }

        .batch-info-card:hover {
            box-shadow: 0 2px 6px rgba(52, 152, 219, 0.1);
        }

        .batch-info-card h4 {
            color: #2c3e50;
            font-size: 0.95em;
            margin: 0 0 12px 0;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .batch-info-card p {
            margin: 6px 0;
            font-size: 0.9em;
            color: #555;
            line-height: 1.5;
        }

        /* 卡片中的强调文本 */
        .batch-info-card strong {
            color: #2980b9;
        }

        /* 全宽卡片（对比方案） */
        .batch-info-card-full {
            grid-column: 1 / -1;
        }

        /* 辅助文本 */
        .text-muted {
            color: #95a5a6;
            font-size: 0.85em;
        }

        .text-highlight {
            color: #e74c3c;
            font-weight: 500;
        }

        /* 基准标记 */
        .baseline-badge {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            margin-left: 6px;
            font-weight: 500;
        }

        /* 方案网格（新的3列布局） */
        .batch-plans-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin: 8px 0;
        }

        .batch-plan-item {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 0.9em;
            color: #555;
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .batch-plan-item strong {
            color: #2c3e50;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .batch-info-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }

            .batch-info-grid {
                grid-template-columns: 1fr;
            }

            .batch-info-card-full {
                grid-column: auto;
            }

            .batch-info-panel {
                padding: 15px;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * 格式化时间间隔（秒）
 * @param {number} seconds - 秒数
 */
function formatDurationFromSeconds(seconds) {
    if (!seconds) return '未知';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    const parts = [];
    if (hours > 0) parts.push(`${hours}小时`);
    if (minutes > 0) parts.push(`${minutes}分钟`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`);
    return parts.join(' ');
}

// ========== 工具函数 ==========

/**
 * 获取推荐等级的样式
 */
function getRecommendationColor(recommendation) {
    const colors = {
        '强烈推荐': 'background-color: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px;',
        '推荐': 'background-color: #2196F3; color: white; padding: 4px 8px; border-radius: 4px;',
        '可选': 'background-color: #FFC107; color: #333; padding: 4px 8px; border-radius: 4px;',
        '不推荐': 'background-color: #F44336; color: white; padding: 4px 8px; border-radius: 4px;'
    };
    return colors[recommendation] || '';
}

/**
 * 获取评分的颜色
 */
function getScoreColor(score) {
    if (score >= 75) return '#4CAF50';
    if (score >= 60) return '#2196F3';
    return '#F44336';
}

/**
 * HTML转义
 */
function escapeHTML(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 显示加载指示器
 */
function showLoadingIndicator(message) {
    let loader = document.getElementById('loadingIndicator');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'loadingIndicator';
        document.body.appendChild(loader);
    }

    loader.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                    background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    z-index: 1000; text-align: center;">
            <div style="margin-bottom: 15px;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3;
                            border-top: 4px solid #2196F3; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            </div>
            <p style="color: #333; font-weight: bold;">${message || '加载中...'}</p>
        </div>
    `;

    if (!document.getElementById('spinningStyle')) {
        const style = document.createElement('style');
        style.id = 'spinningStyle';
        style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
        document.head.appendChild(style);
    }
}

/**
 * 隐藏加载指示器
 */
function hideLoadingIndicator() {
    const loader = document.getElementById('loadingIndicator');
    if (loader) {
        loader.remove();
    }
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * 显示错误消息
 */
function showError(message) {
    showToast(message, 'error');
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.padding = '15px 20px';
    toast.style.borderRadius = '4px';
    toast.style.color = 'white';
    toast.style.zIndex = '2000';
    toast.style.maxWidth = '400px';

    if (type === 'success') {
        toast.style.backgroundColor = '#4CAF50';
        toast.innerHTML = `✓ ${message}`;
    } else if (type === 'error') {
        toast.style.backgroundColor = '#F44336';
        toast.innerHTML = `✗ ${message}`;
    } else {
        toast.style.backgroundColor = '#2196F3';
        toast.innerHTML = `ℹ ${message}`;
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== 导航功能 ==========

/**
 * 返回批量仿真结果页面
 * 导航回 simulations.html 的"结果"标签页，并保留批次上下文
 */
function backToBatchSimulation() {
    // 从 URL 参数获取当前批次信息
    const params = new URLSearchParams(window.location.search);
    const batchId = params.get('batch_id') || currentBatchId;
    const caseId = params.get('case_id') || currentCaseId;

    if (batchId && caseId) {
        // 导航回仿真页面，使用 URL 参数传递批次信息
        // simulations.html 可以通过 URL 参数自动切换到结果视图并加载该批次
        window.location.href = `simulations.html?batch_id=${batchId}&case_id=${caseId}&view=results`;
    } else {
        // 如果参数缺失，回到仿真页面首页
        window.location.href = 'simulations.html';
    }
}

// ========== 初始化 ==========

/**
 * 初始化排序模块
 * 🚀 性能优化：去除全局 MutationObserver，改用简单的 DOM 检查
 */
function initStrategyRanking() {
    // 注意：addRankingTriggerButton 函数在本文件中未定义
    // 此函数仅用于 optimization.html 中的 Layer 2 展示
    // Layer 1 (simulations.html) 和 Layer 2 (optimization.html) 是完全独立的页面
    console.log('Strategy Ranking module loaded - for optimization.html Layer 2 display only');

    // 绑定返回按钮事件
    const backBtn = document.getElementById('backToBatchBtn');
    if (backBtn) {
        backBtn.addEventListener('click', backToBatchSimulation);
    }

    // 页面加载完成后自动初始化（从 optimization.html 调用）
    // initializeRankingPage() 在 optimization.html 中被显式调用
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStrategyRanking);
} else {
    initStrategyRanking();
}
