/**
 * Analysis Results Visualization Component (Task 3.3 - Week 3 Phase 2)
 *
 * 分析结果可视化仪表板
 *
 * 功能:
 * - EdgeData热力图
 * - 统计指标展示
 * - 对比图表 (绿色=改善, 红色=恶化)
 * - 改善排名
 *
 * @module analysis-results
 */

import {
    formatDate,
    formatTime,
    getStatusBadgeClass,
    getColorForStatus,
    calculatePercentage,
    formatFileSize
} from './shared-utils.js';

import { defaultAPIClient } from './api-client.js';


/**
 * 分析结果可视化组件
 *
 * @class AnalysisResultsViewer
 */
export class AnalysisResultsViewer {
    /**
     * 构造函数
     *
     * @param {string} containerId - 容器元素ID
     * @param {Object} options - 配置选项
     * @param {APIClient} options.apiClient - API客户端实例
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container element not found: ${containerId}`);
        }

        this.apiClient = options.apiClient || defaultAPIClient;

        this.batchId = null;
        this.caseId = null;
        this.analysisData = null;
        this.comparisonData = null;

        this._initializeUI();
    }


    /**
     * 初始化UI结构
     *
     * @private
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="analysis-results-viewer">
                <!-- 总览 -->
                <div class="analysis-summary-section">
                    <h4>分析结果总览</h4>
                    <div id="analysis-summary" class="summary-cards">
                        <p>加载中...</p>
                    </div>
                </div>

                <!-- 对比图表 -->
                <div class="comparison-charts-section">
                    <h4>场景对比</h4>
                    <div id="comparison-charts" class="charts-container">
                        <p>暂无数据</p>
                    </div>
                </div>

                <!-- EdgeData 热力图 -->
                <div class="edgedata-heatmap-section">
                    <h4>EdgeData 热力图</h4>
                    <div id="edgedata-heatmap" class="heatmap-container">
                        <p>暂无数据</p>
                    </div>
                </div>

                <!-- TripInfo 统计 -->
                <div class="tripinfo-stats-section">
                    <h4>TripInfo 统计</h4>
                    <div id="tripinfo-stats" class="stats-container">
                        <p>暂无数据</p>
                    </div>
                </div>

                <!-- 改善排名 -->
                <div class="improvement-ranking-section">
                    <h4>改善排名</h4>
                    <div id="improvement-ranking" class="ranking-container">
                        <p>暂无数据</p>
                    </div>
                </div>
            </div>
        `;
    }


    /**
     * 加载分析结果
     *
     * @param {string} batchId - 分析批次ID
     * @param {string} caseId - 案例ID
     * @returns {Promise<void>}
     */
    async loadAnalysisResults(batchId, caseId) {
        this.batchId = batchId;
        this.caseId = caseId;

        try {
            // 并行加载分析结果和对比报告
            const [analysisResponse, comparisonResponse] = await Promise.all([
                this.apiClient.getAnalysisResults(batchId, caseId),
                this.apiClient.getComparisonReport(batchId, caseId)
            ]);

            this.analysisData = analysisResponse.data || analysisResponse;
            this.comparisonData = comparisonResponse.data || comparisonResponse;

            // 渲染UI
            this.render();

        } catch (error) {
            console.error('[AnalysisResultsViewer] Failed to load analysis results:', error);
            this._showError('加载分析结果失败: ' + error.message);
        }
    }


    /**
     * 渲染UI
     */
    render() {
        if (!this.analysisData || !this.comparisonData) {
            this._showError('暂无分析数据');
            return;
        }

        // 渲染各个部分
        this._renderSummary();
        this._renderComparisonCharts();
        this._renderEdgeDataHeatmap();
        this._renderTripInfoStats();
        this._renderImprovementRanking();
    }


    // ========================================================================
    // Private Methods - Rendering
    // ========================================================================

    /**
     * 渲染总览
     *
     * @private
     */
    _renderSummary() {
        const summary = this.analysisData.summary;
        const summaryDiv = this.container.querySelector('#analysis-summary');

        if (!summaryDiv || !summary) return;

        summaryDiv.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="summary-card">
                        <div class="card-title">总仿真数</div>
                        <div class="card-value">${summary.total_simulations}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card">
                        <div class="card-title">已分析</div>
                        <div class="card-value text-success">${summary.analyzed_simulations}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card">
                        <div class="card-title">分析耗时</div>
                        <div class="card-value">${formatTime(summary.analysis_duration_seconds)}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="summary-card">
                        <div class="card-title">完成时间</div>
                        <div class="card-value">${formatDate(summary.analysis_completed_at)}</div>
                    </div>
                </div>
            </div>
        `;
    }


    /**
     * 渲染对比图表
     *
     * @private
     */
    _renderComparisonCharts() {
        const chartsDiv = this.container.querySelector('#comparison-charts');
        const metrics = this.comparisonData.comparison_metrics || [];

        if (!chartsDiv) return;

        if (metrics.length === 0) {
            chartsDiv.innerHTML = '<p>暂无对比数据</p>';
            return;
        }

        // 构建对比表格
        const tableRows = metrics.map(metric => this._renderComparisonRow(metric)).join('');

        chartsDiv.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>指标名称</th>
                            <th>基线值</th>
                            <th>对比值</th>
                            <th>差异</th>
                            <th>改善状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
        `;
    }


    /**
     * 渲染单个对比行
     *
     * @private
     * @param {Object} metric - 对比指标
     * @returns {string} HTML字符串
     */
    _renderComparisonRow(metric) {
        const improvementColor = metric.improvement_color || 'gray';
        const improvementIcon = improvementColor === 'green' ? '▲' :
                                (improvementColor === 'red' ? '▼' : '●');

        return `
            <tr>
                <td>${metric.metric_name}</td>
                <td>${metric.baseline_value.toFixed(2)}</td>
                <td>${metric.comparison_value.toFixed(2)}</td>
                <td>
                    <span style="color: ${improvementColor}">
                        ${improvementIcon} ${metric.absolute_difference.toFixed(2)}
                        (${metric.relative_difference_percent.toFixed(1)}%)
                    </span>
                </td>
                <td>
                    <span class="badge" style="background-color: ${improvementColor}">
                        ${this._getImprovementText(metric.improvement_status)}
                    </span>
                </td>
            </tr>
        `;
    }


    /**
     * 获取改善状态文本
     *
     * @private
     * @param {string} status - 改善状态
     * @returns {string} 中文文本
     */
    _getImprovementText(status) {
        const mapping = {
            'improved': '改善',
            'deteriorated': '恶化',
            'unchanged': '无变化'
        };
        return mapping[status] || status;
    }


    /**
     * 渲染 EdgeData 热力图
     *
     * @private
     */
    _renderEdgeDataHeatmap() {
        const heatmapDiv = this.container.querySelector('#edgedata-heatmap');
        const edgedata = this.analysisData.edgedata_metrics || [];

        if (!heatmapDiv) return;

        if (edgedata.length === 0) {
            heatmapDiv.innerHTML = '<p>暂无 EdgeData 数据</p>';
            return;
        }

        // 简化版: 显示表格而非真实热力图
        const tableRows = edgedata.map(edge => `
            <tr>
                <td>${edge.edge_id}</td>
                <td>${edge.edge_name || '-'}</td>
                <td>${edge.avg_speed.toFixed(1)} km/h</td>
                <td>${edge.avg_density.toFixed(1)} veh/km</td>
                <td>${edge.avg_occupancy.toFixed(1)}%</td>
                <td>
                    <span class="badge ${this._getCongestionBadgeClass(edge.congestion_level)}">
                        ${this._getCongestionText(edge.congestion_level)}
                    </span>
                </td>
            </tr>
        `).join('');

        heatmapDiv.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm table-hover">
                    <thead>
                        <tr>
                            <th>道路段ID</th>
                            <th>名称</th>
                            <th>平均速度</th>
                            <th>平均密度</th>
                            <th>平均占用率</th>
                            <th>拥堵等级</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
            </div>
        `;
    }


    /**
     * 获取拥堵等级徽章类名
     *
     * @private
     * @param {string} level - 拥堵等级
     * @returns {string} CSS类名
     */
    _getCongestionBadgeClass(level) {
        const mapping = {
            'smooth': 'badge-success',
            'moderate': 'badge-warning',
            'congested': 'badge-danger',
            'severe': 'badge-dark'
        };
        return mapping[level] || 'badge-secondary';
    }


    /**
     * 获取拥堵等级文本
     *
     * @private
     * @param {string} level - 拥堵等级
     * @returns {string} 中文文本
     */
    _getCongestionText(level) {
        const mapping = {
            'smooth': '畅通',
            'moderate': '缓行',
            'congested': '拥堵',
            'severe': '严重拥堵'
        };
        return mapping[level] || level;
    }


    /**
     * 渲染 TripInfo 统计
     *
     * @private
     */
    _renderTripInfoStats() {
        const statsDiv = this.container.querySelector('#tripinfo-stats');
        const tripinfo = this.analysisData.tripinfo_metrics;

        if (!statsDiv || !tripinfo) return;

        statsDiv.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-title">总行程数</div>
                        <div class="stat-value">${tripinfo.total_trips}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-title">完成率</div>
                        <div class="stat-value text-success">${tripinfo.completion_rate.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-title">平均行程时间</div>
                        <div class="stat-value">${formatTime(tripinfo.avg_trip_duration)}</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-title">平均延误</div>
                        <div class="stat-value text-warning">${formatTime(tripinfo.avg_delay)}</div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-title">平均行程距离</div>
                        <div class="stat-value">${tripinfo.avg_trip_length.toFixed(1)} km</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-title">平均行程速度</div>
                        <div class="stat-value">${tripinfo.avg_trip_speed.toFixed(1)} km/h</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card">
                        <div class="stat-title">平均等待时间</div>
                        <div class="stat-value">${formatTime(tripinfo.avg_waiting_time)}</div>
                    </div>
                </div>
            </div>
        `;
    }


    /**
     * 渲染改善排名
     *
     * @private
     */
    _renderImprovementRanking() {
        const rankingDiv = this.container.querySelector('#improvement-ranking');
        const ranking = this.comparisonData.improvement_ranking || [];

        if (!rankingDiv) return;

        if (ranking.length === 0) {
            rankingDiv.innerHTML = '<p>暂无排名数据</p>';
            return;
        }

        const rankingRows = ranking.map(item => `
            <tr>
                <td>
                    <span class="rank-badge">#${item.rank}</span>
                </td>
                <td>${item.scenario_id}</td>
                <td>${item.scenario_name || '-'}</td>
                <td>
                    <span class="text-success">
                        ▲ ${item.overall_improvement.toFixed(1)}%
                    </span>
                </td>
            </tr>
        `).join('');

        rankingDiv.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>场景ID</th>
                            <th>场景名称</th>
                            <th>总体改善</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rankingRows}
                    </tbody>
                </table>
            </div>
        `;
    }


    /**
     * 显示错误
     *
     * @private
     * @param {string} message - 错误消息
     */
    _showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>错误:</strong> ${message}
            </div>
        `;
    }


    /**
     * 销毁组件
     */
    destroy() {
        this.container.innerHTML = '';
    }
}


/**
 * 全局辅助函数: 查看详细分析结果
 *
 * @param {string} batchId - 批次ID
 * @param {string} caseId - 案例ID
 */
window.viewAnalysisResults = function(batchId, caseId) {
    // 跳转到分析结果页面
    window.location.href = `/analysis/results?batch_id=${batchId}&case_id=${caseId}`;
};
