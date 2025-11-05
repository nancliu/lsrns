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

// ========== 全局变量 ==========
let rankingResultsData = null;
let rankingCharts = {};

// 注意: currentBatchId, currentCaseId 由 optimization.js 定义和管理
// 本模块使用 optimization.js 中定义的全局变量，避免重复声明
// API_BASE 也由 optimization.js 定义和管理

// ========== 初始化：从 URL 参数加载批次 ==========

/**
 * 页面加载时初始化 - 从 URL 参数获取 batch_id，自动加载和排序
 *
 * URL 格式: optimization.html?batch_id=batch_20251105_000102&case_id=case_20251103_141612
 */
function initializeRankingPage() {
    // 从 URL 获取参数
    const params = new URLSearchParams(window.location.search);
    const batchId = params.get('batch_id');
    const caseId = params.get('case_id');

    if (!batchId || !caseId) {
        console.warn('Missing batch_id or case_id in URL parameters');
        showError('缺少批次或案例信息，请从批量仿真页面进入');
        return;
    }

    // 使用 optimization.js 中的全局变量
    currentBatchId = batchId;
    currentCaseId = caseId;

    // 自动加载排序结果
    loadAndDisplayRanking();
}

/**
 * 加载并展示排序结果
 */
async function loadAndDisplayRanking() {
    try {
        // 显示加载指示器
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
            `${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`,
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
            `${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`,
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
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStrategyRanking);
} else {
    initStrategyRanking();
}
