/**
 * Event Scenario Comparison Table Component
 *
 * 事件场景对比表格组件
 * 参考优化仿真中的批量仿真结果页面对比表格
 *
 * 功能:
 * - 显示多策略对比表格（NO_CONTROL作为基准）
 * - 计算相比基准的改善百分比
 * - 使用颜色和箭头指示改善方向
 * - 支持多种指标：速度、行程时间、完成率、延误等
 */

const API_BASE = '/api/v1';

/**
 * 渲染事件场景对比表格
 *
 * @param {Object} batchResults - 批次分析结果
 * @param {string} containerId - 容器元素ID
 *
 * 数据结构:
 * {
 *   event_id: "8210655",
 *   strategy_comparison: {
 *     "NO_CONTROL": {
 *       avg_speed: 45.2,
 *       avg_trip_duration: 1200,
 *       completion_rate: 96.5,
 *       total_vehicles: 8934,
 *       total_delay: 45000,
 *       avg_waiting_time: 120
 *     },
 *     "VSS": {
 *       avg_speed: 52.8,
 *       avg_trip_duration: 1050,
 *       completion_rate: 98.2,
 *       total_vehicles: 8934,
 *       total_delay: 38000,
 *       avg_waiting_time: 95,
 *       improvement_vs_baseline: {
 *         avg_speed: 16.8,
 *         avg_trip_duration: -12.5,
 *         completion_rate: 1.76
 *       }
 *     }
 *   }
 * }
 */
function renderEventScenarioComparisonTable(batchResults, containerId = 'comparisonTableContainer') {
    const container = document.getElementById(containerId);

    if (!container) {
        console.error(`Container not found: ${containerId}`);
        return;
    }

    if (!batchResults || !batchResults.strategy_comparison) {
        container.innerHTML = '<div class="empty-state">暂无对比数据</div>';
        return;
    }

    const strategyComparison = batchResults.strategy_comparison;

    // 策略顺序（NO_CONTROL放在第一行作为基准）
    const strategyOrder = ['NO_CONTROL', 'VSS', 'TEC', 'DHS'];
    const strategyNames = {
        'NO_CONTROL': '无控制（基准）',
        'VSS': '可变限速',
        'TEC': '收费站管控',
        'DHS': '动态硬路肩'
    };

    // 获取基准数据
    const baseline = strategyComparison['NO_CONTROL'];

    if (!baseline) {
        container.innerHTML = '<div class="empty-state">未找到基准场景（NO_CONTROL）</div>';
        return;
    }

    // 构建表格HTML
    let html = `
        <div class="comparison-table-wrapper">
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th rowspan="2">控制策略</th>
                        <th colspan="2">平均速度 (km/h)</th>
                        <th colspan="2">平均行程时间 (秒)</th>
                        <th colspan="2">完成率 (%)</th>
                        <th colspan="2">总延误 (秒)</th>
                        <th rowspan="2">总车辆数</th>
                    </tr>
                    <tr>
                        <th>数值</th>
                        <th>相比基准</th>
                        <th>数值</th>
                        <th>相比基准</th>
                        <th>数值</th>
                        <th>相比基准</th>
                        <th>数值</th>
                        <th>相比基准</th>
                    </tr>
                </thead>
                <tbody>
    `;

    // 遍历策略，按顺序显示
    strategyOrder.forEach(strategy => {
        if (!strategyComparison[strategy]) return;

        const metrics = strategyComparison[strategy];
        const isBaseline = (strategy === 'NO_CONTROL');

        // 格式化指标
        const avgSpeed = metrics.avg_speed?.toFixed(1) || 'N/A';
        const avgTripDuration = metrics.avg_trip_duration?.toFixed(0) || 'N/A';
        const completionRate = metrics.completion_rate?.toFixed(1) || 'N/A';
        const totalDelay = metrics.total_delay ? formatDelay(metrics.total_delay) : 'N/A';
        const totalVehicles = metrics.total_vehicles?.toFixed(0) || 'N/A';

        // 计算改善百分比
        let speedChange = '-';
        let tripDurationChange = '-';
        let completionRateChange = '-';
        let delayChange = '-';

        if (!isBaseline && baseline) {
            // 平均速度（提高是改善）
            if (metrics.avg_speed && baseline.avg_speed) {
                speedChange = calculateImprovement(
                    metrics.avg_speed,
                    baseline.avg_speed,
                    true  // 数值越高越好
                );
            }

            // 平均行程时间（降低是改善）
            if (metrics.avg_trip_duration && baseline.avg_trip_duration) {
                tripDurationChange = calculateImprovement(
                    metrics.avg_trip_duration,
                    baseline.avg_trip_duration,
                    false  // 数值越低越好
                );
            }

            // 完成率（提高是改善）
            if (metrics.completion_rate && baseline.completion_rate) {
                completionRateChange = calculateImprovement(
                    metrics.completion_rate,
                    baseline.completion_rate,
                    true
                );
            }

            // 总延误（降低是改善）
            if (metrics.total_delay && baseline.total_delay) {
                delayChange = calculateImprovement(
                    metrics.total_delay,
                    baseline.total_delay,
                    false
                );
            }
        }

        // 添加表格行
        const rowClass = isBaseline ? 'baseline-row' : '';
        html += `
            <tr class="${rowClass}">
                <td class="strategy-name">
                    <strong>${strategyNames[strategy] || strategy}</strong>
                    ${isBaseline ? '<span class="baseline-badge">基准</span>' : ''}
                </td>
                <td class="metric-value">${avgSpeed}</td>
                <td class="metric-change">${speedChange}</td>
                <td class="metric-value">${avgTripDuration}</td>
                <td class="metric-change">${tripDurationChange}</td>
                <td class="metric-value">${completionRate}</td>
                <td class="metric-change">${completionRateChange}</td>
                <td class="metric-value">${totalDelay}</td>
                <td class="metric-change">${delayChange}</td>
                <td class="metric-value">${totalVehicles}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>

        <div class="table-legend">
            <div class="legend-item">
                <span class="legend-icon improvement">↑</span>
                <span class="legend-text">改善</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon deterioration">↓</span>
                <span class="legend-text">恶化</span>
            </div>
            <div class="legend-item">
                <span class="legend-text">百分比相对于基准场景（无控制）</span>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * 计算改善百分比并格式化
 *
 * @param {number} value - 当前值
 * @param {number} baseline - 基准值
 * @param {boolean} higherIsBetter - true: 数值越高越好（如速度），false: 数值越低越好（如延误）
 * @returns {string} - 格式化的HTML字符串，包含颜色和箭头
 */
function calculateImprovement(value, baseline, higherIsBetter = true) {
    if (!value || !baseline || baseline === 0) {
        return '-';
    }

    const percentChange = ((value - baseline) / baseline) * 100;
    const absChange = Math.abs(percentChange);

    // 判断是改善还是恶化
    let isImprovement;
    if (higherIsBetter) {
        isImprovement = percentChange > 0;
    } else {
        isImprovement = percentChange < 0;
    }

    // 选择颜色和箭头
    const color = isImprovement ? 'green' : 'red';
    const arrow = percentChange > 0 ? '↑' : '↓';
    const cssClass = isImprovement ? 'improvement' : 'deterioration';

    return `<span class="${cssClass}" style="color: ${color};">${arrow} ${absChange.toFixed(1)}%</span>`;
}

/**
 * 格式化延误时间（秒 → 小时:分钟:秒）
 *
 * @param {number} seconds - 延误秒数
 * @returns {string} - 格式化的时间字符串
 */
function formatDelay(seconds) {
    if (!seconds || seconds < 0) return '0';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

/**
 * 渲染策略排名表格
 *
 * @param {Object} batchResults - 批次分析结果
 * @param {string} containerId - 容器元素ID
 */
function renderStrategyRanking(batchResults, containerId = 'strategyRankingContainer') {
    const container = document.getElementById(containerId);

    if (!container) {
        console.error(`Container not found: ${containerId}`);
        return;
    }

    if (!batchResults || !batchResults.strategy_ranking) {
        container.innerHTML = '<div class="empty-state">暂无排名数据</div>';
        return;
    }

    const ranking = batchResults.strategy_ranking;
    const strategyNames = {
        'NO_CONTROL': '无控制（基准）',
        'VSS': '可变限速',
        'TEC': '收费站管控',
        'DHS': '动态硬路肩'
    };

    let html = `
        <div class="ranking-table-wrapper">
            <table class="ranking-table">
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>控制策略</th>
                        <th>综合改善率 (%)</th>
                        <th>评价</th>
                    </tr>
                </thead>
                <tbody>
    `;

    ranking.forEach((item, index) => {
        const strategyName = strategyNames[item.strategy] || item.strategy;
        const improvement = item.overall_improvement?.toFixed(1) || '0.0';
        const rank = item.rank || (index + 1);

        // 根据改善率确定评价
        let evaluation = '';
        let evaluationClass = '';
        if (item.overall_improvement >= 15) {
            evaluation = '优秀';
            evaluationClass = 'excellent';
        } else if (item.overall_improvement >= 10) {
            evaluation = '良好';
            evaluationClass = 'good';
        } else if (item.overall_improvement >= 5) {
            evaluation = '一般';
            evaluationClass = 'fair';
        } else {
            evaluation = '较差';
            evaluationClass = 'poor';
        }

        // 奖牌图标
        let medalIcon = '';
        if (rank === 1) {
            medalIcon = '<span class="medal gold">🥇</span>';
        } else if (rank === 2) {
            medalIcon = '<span class="medal silver">🥈</span>';
        } else if (rank === 3) {
            medalIcon = '<span class="medal bronze">🥉</span>';
        }

        html += `
            <tr>
                <td class="rank-cell">${medalIcon} ${rank}</td>
                <td class="strategy-cell"><strong>${strategyName}</strong></td>
                <td class="improvement-cell">
                    <span class="improvement-value ${improvement > 0 ? 'positive' : 'negative'}">
                        ${improvement > 0 ? '+' : ''}${improvement}%
                    </span>
                </td>
                <td class="evaluation-cell">
                    <span class="evaluation-badge ${evaluationClass}">${evaluation}</span>
                </td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * 加载并显示事件批次结果
 *
 * @param {string} batchId - 批次ID
 */
async function loadEventBatchResults(batchId) {
    try {
        const response = await fetch(`${API_BASE}/batch/event-batch-results/${batchId}`);

        if (!response.ok) {
            throw new Error('Failed to load batch results');
        }

        const batchResults = await response.json();

        // 渲染对比表格
        renderEventScenarioComparisonTable(batchResults, 'comparisonTableContainer');

        // 渲染策略排名
        renderStrategyRanking(batchResults, 'strategyRankingContainer');

        // 显示结果区域
        document.getElementById('resultsSection').style.display = 'block';

    } catch (error) {
        console.error('Load batch results error:', error);
        alert('加载批次结果失败: ' + error.message);
    }
}

/**
 * 渲染交通性能对比指标（8个）
 * 根据不同控制策略对比交通性能的影响
 *
 * @param {Object} batchResults - 批次分析结果
 * @param {string} containerId - 容器元素ID
 */
window.renderTrafficPerformanceComparison = function(batchResults, containerId = 'trafficPerformanceContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!batchResults || !batchResults.strategy_comparison) {
        container.innerHTML = '<div class="empty-state">暂无交通性能对比数据</div>';
        return;
    }

    const strategyComparison = batchResults.strategy_comparison;
    const strategyOrder = ['NO_CONTROL', 'VSS', 'TEC', 'DHS'];
    const strategyNames = {
        'NO_CONTROL': '无控制（基准）',
        'VSS': '可变限速',
        'TEC': '收费站管控',
        'DHS': '动态硬路肩'
    };

    // 获取基准数据
    const baseline = strategyComparison['NO_CONTROL'];
    if (!baseline) {
        container.innerHTML = '<div class="empty-state">未找到基准场景（NO_CONTROL）</div>';
        return;
    }

    // 8个交通性能指标定义
    const trafficMetrics = [
        { key: 'current_vehicles', label: '当前运行车数', unit: '辆', higher_is_better: false },
        { key: 'avg_speed', label: '平均速度', unit: 'km/h', higher_is_better: true },
        { key: 'loaded_vehicles', label: '已载入车数', unit: '辆', higher_is_better: true },
        { key: 'chain_frequency', label: '链接频率', unit: '次', higher_is_better: true },
        { key: 'transmission_frequency', label: '传送频率', unit: '次', higher_is_better: true },
        { key: 'completed_vehicles', label: '已完成车数', unit: '辆', higher_is_better: true },
        { key: 'terminated_vehicles', label: '已中止车数', unit: '辆', higher_is_better: false },
        { key: 'waiting_vehicles', label: '等待车数', unit: '辆', higher_is_better: false }
    ];

    // 构建表格HTML
    let html = `
        <div class="traffic-performance-table-wrapper">
            <table class="traffic-performance-table">
                <thead>
                    <tr>
                        <th rowspan="2">控制策略</th>
    `;

    // 添加指标列头
    trafficMetrics.forEach(metric => {
        html += `<th colspan="2">${metric.label} (${metric.unit})</th>`;
    });

    html += `
                    </tr>
                    <tr>
    `;

    // 添加数值和对比的子列头
    trafficMetrics.forEach(() => {
        html += `<th>数值</th><th>相比基准</th>`;
    });

    html += `
                    </tr>
                </thead>
                <tbody>
    `;

    // 遍历策略
    strategyOrder.forEach(strategy => {
        if (!strategyComparison[strategy]) return;

        const metrics = strategyComparison[strategy];
        const isBaseline = (strategy === 'NO_CONTROL');

        html += `
            <tr ${isBaseline ? 'class="baseline-row"' : ''}>
                <td class="strategy-name">
                    <strong>${strategyNames[strategy] || strategy}</strong>
                    ${isBaseline ? '<span class="baseline-badge">基准</span>' : ''}
                </td>
        `;

        // 添加每个指标的数值和对比
        trafficMetrics.forEach(metric => {
            const value = metrics[metric.key];
            const displayValue = value !== undefined ? (typeof value === 'number' ? value.toFixed(1) : value) : 'N/A';

            let changeHtml = '-';
            if (!isBaseline && baseline[metric.key] !== undefined) {
                const baselineValue = baseline[metric.key];
                const diff = value - baselineValue;
                const percentChange = baselineValue !== 0 ? ((diff / baselineValue) * 100).toFixed(1) : 0;

                let isImprovement = false;
                if (metric.higher_is_better) {
                    isImprovement = diff > 0;
                } else {
                    isImprovement = diff < 0;
                }

                const changeClass = isImprovement ? 'improvement' : 'deterioration';
                const changeSymbol = isImprovement ? '↑' : '↓';
                changeHtml = `<span class="${changeClass}">${changeSymbol} ${Math.abs(percentChange)}%</span>`;
            }

            html += `
                <td class="metric-value">${displayValue}</td>
                <td class="metric-change">${changeHtml}</td>
            `;
        });

        html += `</tr>`;
    });

    html += `
                </tbody>
            </table>
        </div>

        <div class="table-legend">
            <div class="legend-item">
                <span class="legend-icon improvement">↑</span>
                <span class="legend-text">性能改善</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon deterioration">↓</span>
                <span class="legend-text">性能恶化</span>
            </div>
            <div class="legend-item">
                <span class="legend-text">百分比相对于基准案例（无控制）</span>
            </div>
        </div>
    `;

    container.innerHTML = html;
};

// 导出函数供外部使用
window.renderEventScenarioComparisonTable = renderEventScenarioComparisonTable;
window.renderStrategyRanking = renderStrategyRanking;
window.loadEventBatchResults = loadEventBatchResults;
window.renderTrafficPerformanceComparison = window.renderTrafficPerformanceComparison;
