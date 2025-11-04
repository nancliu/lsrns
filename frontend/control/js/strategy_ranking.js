/**
 * 控制策略排序结果展示 (Layer 2)
 *
 * 职责：
 * - 触发策略排序分析
 * - 加载并展示排序结果
 * - 渲染排序表格和推荐等级
 * - 展示雷达图表和分数对比
 */

// ========== 全局变量 ==========
let rankingResultsData = null;
let rankingCharts = {};

// ========== 4.1.1: 添加排序触发按钮 ==========

/**
 * 在批次结果页面添加"生成优化方案"按钮
 */
function addRankingTriggerButton() {
    const resultsContainer = document.getElementById('batchResultsContainer');
    if (!resultsContainer) {
        console.warn('Batch results container not found');
        return;
    }

    // 检查按钮是否已存在
    if (document.getElementById('btn-generate-ranking')) {
        return;
    }

    // 创建按钮容器
    const buttonContainer = document.createElement('div');
    buttonContainer.style.marginTop = '20px';
    buttonContainer.style.marginBottom = '20px';
    buttonContainer.style.display = 'flex';
    buttonContainer.style.gap = '10px';
    buttonContainer.style.justifyContent = 'center';

    // 创建排序按钮
    const rankingButton = document.createElement('button');
    rankingButton.id = 'btn-generate-ranking';
    rankingButton.className = 'btn btn-primary';
    rankingButton.textContent = '🎯 生成优化方案';
    rankingButton.style.minWidth = '160px';
    rankingButton.style.padding = '10px 20px';
    rankingButton.style.fontSize = '14px';
    rankingButton.style.fontWeight = 'bold';
    rankingButton.onclick = triggerStrategyRanking;

    // 创建报告下载按钮（初始隐藏）
    const reportButton = document.createElement('button');
    reportButton.id = 'btn-download-report';
    reportButton.className = 'btn btn-info';
    reportButton.textContent = '📄 下载报告';
    reportButton.style.minWidth = '160px';
    reportButton.style.padding = '10px 20px';
    reportButton.style.fontSize = '14px';
    reportButton.style.display = 'none';
    reportButton.onclick = downloadRankingReport;

    buttonContainer.appendChild(rankingButton);
    buttonContainer.appendChild(reportButton);

    // 插入到结果容器
    resultsContainer.insertBefore(buttonContainer, resultsContainer.firstChild);
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
 * 渲染排序结果
 */
function renderRankingResults() {
    if (!rankingResultsData) {
        console.warn('No ranking results to render');
        return;
    }

    // 获取或创建结果容器
    let resultsSection = document.getElementById('strategyRankingSection');
    if (!resultsSection) {
        resultsSection = createRankingResultsSection();
        const container = document.getElementById('batchResultsContainer');
        if (container) {
            container.appendChild(resultsSection);
        }
    }

    // 清空旧内容
    resultsSection.innerHTML = '';

    // 添加标题
    const title = document.createElement('h2');
    title.textContent = '🏆 控制策略排序结果';
    title.style.color = '#1976D2';
    title.style.marginBottom = '20px';
    title.style.borderLeft = '4px solid #2196F3';
    title.style.paddingLeft = '15px';
    resultsSection.appendChild(title);

    // 添加摘要信息
    renderRankingSummary(resultsSection);

    // 添加排序表格
    renderRankingTable(resultsSection);

    // 添加首推方案详情
    if (rankingResultsData.ranked_strategies && rankingResultsData.ranked_strategies.length > 0) {
        renderTopStrategyDetails(resultsSection, rankingResultsData.ranked_strategies[0]);
    }

    // 添加可视化图表
    renderRankingCharts(resultsSection);
}

/**
 * 创建排序结果容器
 */
function createRankingResultsSection() {
    const section = document.createElement('section');
    section.id = 'strategyRankingSection';
    section.style.marginTop = '40px';
    section.style.padding = '20px';
    section.style.backgroundColor = '#f9f9f9';
    section.style.borderRadius = '4px';
    section.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
    return section;
}

/**
 * 渲染排序摘要
 */
function renderRankingSummary(container) {
    if (!rankingResultsData.ranking_metadata) {
        return;
    }

    const metadata = rankingResultsData.ranking_metadata;
    const summary = document.createElement('div');
    summary.className = 'summary-text';
    summary.style.backgroundColor = '#e8f5e9';
    summary.style.borderLeft = '4px solid #4CAF50';
    summary.style.padding = '15px';
    summary.style.marginBottom = '20px';
    summary.style.borderRadius = '4px';

    const topStrategy = rankingResultsData.ranked_strategies[0];
    summary.innerHTML = `
        <strong>🎯 最优策略: ${topStrategy.plan_name}</strong><br>
        总体评分 <span style="color: #2196F3; font-weight: bold;">${topStrategy.overall_score.toFixed(1)}/100</span>，
        推荐等级为"<strong>${topStrategy.recommendation}</strong>"。<br><br>
        📊 本次评估共纳入 <strong>${metadata.total_strategies}</strong> 个控制策略。
        系统采用多准则评估方法，综合考虑策略的有效性、覆盖率、效率和可靠性，
        为交通管理者提供科学的决策支持。
    `;

    container.appendChild(summary);
}

/**
 * 渲染排序表格
 */
function renderRankingTable(container) {
    if (!rankingResultsData.ranked_strategies) {
        return;
    }

    const table = document.createElement('table');
    table.className = 'ranking-table';
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.marginBottom = '20px';
    table.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';

    // 表头
    const thead = document.createElement('thead');
    thead.style.backgroundColor = '#1976D2';
    thead.style.color = 'white';
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
 */
function initStrategyRanking() {
    // 在批次结果加载完成后添加排序按钮
    const observer = new MutationObserver(() => {
        const resultsContainer = document.getElementById('batchResultsContainer');
        if (resultsContainer && !document.getElementById('btn-generate-ranking')) {
            addRankingTriggerButton();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // 或直接调用（如果结果容器已存在）
    setTimeout(() => {
        addRankingTriggerButton();
    }, 500);
}

// 页面加载时初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStrategyRanking);
} else {
    initStrategyRanking();
}
