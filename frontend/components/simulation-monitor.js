/**
 * Real-Time Simulation Monitor Component (Task 2.5 - Week 2 Phase 2)
 *
 * 实时仿真监控组件 - 支持批量仿真进度跟踪
 *
 * 设计决策 Q14: 通用组件,支持所有仿真类型:
 * - Event-scenario simulations (Phase 2 实现)
 * - OD extraction simulations (未来兼容)
 * - Control plan batch simulations (现有,考虑兼容性)
 *
 * @module simulation-monitor
 */

import {
    formatDate,
    formatTime,
    getStatusBadgeClass,
    getStatusText,
    getColorForStatus,
    calculatePercentage,
    delay,
    showError,
    showSuccess
} from './shared-utils.js';

import { defaultAPIClient } from './api-client.js';


/**
 * 仿真监控组件类
 *
 * 提供实时进度监控功能:
 * - 批次总体进度 (completed/failed/in_progress/queued)
 * - 单个仿真详细状态
 * - 进度条可视化
 * - ETA估算
 * - 日志查看 (可展开)
 * - 自动停止轮询 (完成后)
 *
 * @class SimulationMonitor
 */
export class SimulationMonitor {
    /**
     * 构造函数
     *
     * @param {string} containerId - 容器元素ID
     * @param {Object} options - 配置选项
     * @param {APIClient} options.apiClient - API客户端实例 (可选)
     * @param {number} options.updateInterval - 更新间隔 (毫秒, default: 5000)
     * @param {boolean} options.autoStart - 是否自动开始监控 (default: false)
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container element not found: ${containerId}`);
        }

        this.apiClient = options.apiClient || defaultAPIClient;
        this.updateInterval = options.updateInterval || 5000; // 5秒轮询
        this.autoStart = options.autoStart || false;

        this.batchId = null;
        this.simType = null;
        this.isMonitoring = false;
        this.monitoringTimer = null;

        this._initializeUI();
    }


    /**
     * 初始化UI结构
     *
     * @private
     */
    _initializeUI() {
        this.container.innerHTML = `
            <div class="simulation-monitor">
                <!-- 批次进度概览 -->
                <div class="batch-progress-section">
                    <h5>批次进度</h5>
                    <div class="progress-summary" id="progress-summary">
                        <p>等待数据...</p>
                    </div>
                    <div class="progress mb-3" style="height: 30px;">
                        <div class="progress-bar bg-success" role="progressbar"
                             id="progress-bar-completed" style="width: 0%">
                            <span id="progress-text-completed">0</span>
                        </div>
                        <div class="progress-bar bg-primary" role="progressbar"
                             id="progress-bar-running" style="width: 0%">
                            <span id="progress-text-running">0</span>
                        </div>
                        <div class="progress-bar bg-danger" role="progressbar"
                             id="progress-bar-failed" style="width: 0%">
                            <span id="progress-text-failed">0</span>
                        </div>
                        <div class="progress-bar bg-secondary" role="progressbar"
                             id="progress-bar-queued" style="width: 0%">
                            <span id="progress-text-queued">0</span>
                        </div>
                    </div>
                </div>

                <!-- 仿真列表 -->
                <div class="simulations-list-section">
                    <h5>仿真列表</h5>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>仿真ID</th>
                                    <th>状态</th>
                                    <th>进度</th>
                                    <th>已用时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="simulations-table-body">
                                <tr>
                                    <td colspan="5" class="text-center">暂无数据</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 控制按钮 -->
                <div class="monitor-controls mt-3">
                    <button class="btn btn-danger" id="btn-cancel-batch" style="display: none;">
                        取消批次
                    </button>
                    <button class="btn btn-secondary" id="btn-stop-monitoring">
                        停止监控
                    </button>
                </div>
            </div>
        `;

        this._attachEventListeners();
    }


    /**
     * 绑定事件监听器
     *
     * @private
     */
    _attachEventListeners() {
        const btnCancel = this.container.querySelector('#btn-cancel-batch');
        const btnStop = this.container.querySelector('#btn-stop-monitoring');

        if (btnCancel) {
            btnCancel.addEventListener('click', () => this.cancelBatch());
        }

        if (btnStop) {
            btnStop.addEventListener('click', () => this.stopMonitoring());
        }
    }


    /**
     * 开始监控批次仿真
     *
     * @param {string} batchId - 批次ID
     * @param {string} simType - 仿真类型 ('event-scenario'|'od-extraction'|'control-plan')
     * @returns {Promise<void>}
     *
     * @example
     * monitor.startMonitoring('batch_20251112_100000', 'event-scenario');
     */
    async startMonitoring(batchId, simType = 'event-scenario') {
        this.batchId = batchId;
        this.simType = simType;
        this.isMonitoring = true;

        console.log(`[SimulationMonitor] Starting monitoring for batch: ${batchId}`);

        // 显示取消按钮
        const btnCancel = this.container.querySelector('#btn-cancel-batch');
        if (btnCancel) {
            btnCancel.style.display = 'inline-block';
        }

        // 开始轮询
        await this._monitoringLoop();
    }


    /**
     * 监控循环 (轮询)
     *
     * @private
     */
    async _monitoringLoop() {
        while (this.isMonitoring) {
            try {
                const statusData = await this.apiClient.getSimulationBatchStatus(this.batchId);

                // 更新UI
                this.render(statusData.data || statusData);

                // 检查是否完成 (completed + failed == total)
                const data = statusData.data || statusData;
                const isComplete = (
                    data.batch_status === 'completed' ||
                    data.batch_status === 'failed' ||
                    data.batch_status === 'cancelled' ||
                    (data.queued === 0 && data.in_progress === 0)
                );

                if (isComplete) {
                    console.log('[SimulationMonitor] Batch completed, stopping monitoring');
                    this.stopMonitoring();
                    showSuccess('批次仿真已完成');
                    break;
                }

                // 等待下一次轮询
                await delay(this.updateInterval);

            } catch (error) {
                console.error('[SimulationMonitor] Failed to fetch status:', error);
                showError('获取仿真状态失败,正在重试...');

                // 出错后继续重试
                await delay(this.updateInterval);
            }
        }
    }


    /**
     * 渲染UI (更新进度数据)
     *
     * @param {Object} statusData - 批次状态数据
     * @param {string} statusData.batch_id - 批次ID
     * @param {number} statusData.total_simulations - 总仿真数
     * @param {number} statusData.completed - 已完成数
     * @param {number} statusData.failed - 失败数
     * @param {number} statusData.in_progress - 进行中数
     * @param {number} statusData.queued - 排队中数
     * @param {string} statusData.batch_status - 批次状态
     * @param {string} statusData.estimated_completion - 预计完成时间
     * @param {Array} statusData.simulations - 仿真列表
     */
    render(statusData) {
        const {
            total_simulations,
            completed = 0,
            failed = 0,
            in_progress = 0,
            queued = 0,
            batch_status,
            estimated_completion,
            simulations = [],
            elapsed_seconds = 0
        } = statusData;

        // 更新进度概览
        this._updateProgressSummary({
            total: total_simulations,
            completed,
            failed,
            in_progress,
            queued,
            batch_status,
            estimated_completion,
            elapsed_seconds
        });

        // 更新进度条
        this._updateProgressBars(total_simulations, completed, in_progress, failed, queued);

        // 更新仿真列表
        this._updateSimulationsList(simulations);
    }


    /**
     * 更新进度概览
     *
     * @private
     */
    _updateProgressSummary(data) {
        const summaryDiv = this.container.querySelector('#progress-summary');
        if (!summaryDiv) return;

        const progressPercent = calculatePercentage(data.completed, data.total, 1);
        const etaText = data.estimated_completion
            ? formatDate(data.estimated_completion)
            : '计算中...';

        summaryDiv.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <strong>总数:</strong> ${data.total}
                </div>
                <div class="col-md-3">
                    <strong>已完成:</strong> <span class="text-success">${data.completed}</span>
                </div>
                <div class="col-md-3">
                    <strong>失败:</strong> <span class="text-danger">${data.failed}</span>
                </div>
                <div class="col-md-3">
                    <strong>进行中:</strong> <span class="text-primary">${data.in_progress}</span>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-4">
                    <strong>排队中:</strong> ${data.queued}
                </div>
                <div class="col-md-4">
                    <strong>批次状态:</strong> <span class="badge ${getStatusBadgeClass(data.batch_status)}">${getStatusText(data.batch_status)}</span>
                </div>
                <div class="col-md-4">
                    <strong>预计完成:</strong> ${etaText}
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-12">
                    <strong>总体进度:</strong> ${progressPercent}%
                    (已用时间: ${formatTime(data.elapsed_seconds)})
                </div>
            </div>
        `;
    }


    /**
     * 更新进度条
     *
     * @private
     */
    _updateProgressBars(total, completed, inProgress, failed, queued) {
        if (total === 0) return;

        const completedPercent = calculatePercentage(completed, total, 1);
        const inProgressPercent = calculatePercentage(inProgress, total, 1);
        const failedPercent = calculatePercentage(failed, total, 1);
        const queuedPercent = calculatePercentage(queued, total, 1);

        // 更新进度条宽度和文本
        this._updateProgressBar('completed', completedPercent, completed);
        this._updateProgressBar('running', inProgressPercent, inProgress);
        this._updateProgressBar('failed', failedPercent, failed);
        this._updateProgressBar('queued', queuedPercent, queued);
    }


    /**
     * 更新单个进度条
     *
     * @private
     */
    _updateProgressBar(type, percent, count) {
        const bar = this.container.querySelector(`#progress-bar-${type}`);
        const text = this.container.querySelector(`#progress-text-${type}`);

        if (bar) {
            bar.style.width = `${percent}%`;
            bar.setAttribute('aria-valuenow', percent);
        }

        if (text) {
            text.textContent = count > 0 ? `${count}` : '';
        }
    }


    /**
     * 更新仿真列表
     *
     * @private
     */
    _updateSimulationsList(simulations) {
        const tbody = this.container.querySelector('#simulations-table-body');
        if (!tbody) return;

        if (!simulations || simulations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">暂无数据</td></tr>';
            return;
        }

        const rows = simulations.map(sim => this._renderSimulationRow(sim)).join('');
        tbody.innerHTML = rows;

        // 绑定日志查看按钮事件
        this._attachLogViewers();
    }


    /**
     * 渲染单个仿真行
     *
     * @private
     */
    _renderSimulationRow(sim) {
        const {
            simulation_id,
            status,
            progress_percent = 0,
            started_at,
            completed_at,
            elapsed_seconds,
            error
        } = sim;

        const statusBadge = `<span class="badge ${getStatusBadgeClass(status)}">${getStatusText(status)}</span>`;
        const progressBar = `
            <div class="progress" style="height: 20px;">
                <div class="progress-bar" role="progressbar"
                     style="width: ${progress_percent}%; background-color: ${getColorForStatus(status)};"
                     aria-valuenow="${progress_percent}" aria-valuemin="0" aria-valuemax="100">
                    ${progress_percent}%
                </div>
            </div>
        `;

        const timeText = elapsed_seconds ? formatTime(elapsed_seconds) : '-';

        let actionButtons = '';
        if (status === 'completed') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-primary" onclick="window.viewSimulationResults('${simulation_id}')">
                    查看结果
                </button>
            `;
        } else if (status === 'running') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-secondary btn-view-logs" data-sim-id="${simulation_id}">
                    查看日志
                </button>
            `;
        } else if (status === 'failed') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-danger btn-view-error" data-sim-id="${simulation_id}">
                    查看错误
                </button>
            `;
        }

        return `
            <tr>
                <td>${simulation_id}</td>
                <td>${statusBadge}</td>
                <td>${progressBar}</td>
                <td>${timeText}</td>
                <td>${actionButtons}</td>
            </tr>
        `;
    }


    /**
     * 绑定日志查看器事件
     *
     * @private
     */
    _attachLogViewers() {
        const logButtons = this.container.querySelectorAll('.btn-view-logs');
        logButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const simId = e.target.getAttribute('data-sim-id');
                this.viewSimulationLogs(simId);
            });
        });

        const errorButtons = this.container.querySelectorAll('.btn-view-error');
        errorButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const simId = e.target.getAttribute('data-sim-id');
                this.viewSimulationError(simId);
            });
        });
    }


    /**
     * 查看仿真日志
     *
     * @param {string} simulationId - 仿真ID
     */
    async viewSimulationLogs(simulationId) {
        try {
            const detail = await this.apiClient.getSimulationDetail(simulationId);
            const logs = detail.data?.logs || '暂无日志';

            // 显示日志模态框
            alert(`仿真日志 - ${simulationId}\n\n${logs}`);
            // TODO: 使用实际的模态框组件

        } catch (error) {
            showError('获取日志失败', error);
        }
    }


    /**
     * 查看仿真错误
     *
     * @param {string} simulationId - 仿真ID
     */
    async viewSimulationError(simulationId) {
        try {
            const detail = await this.apiClient.getSimulationDetail(simulationId);
            const errorMsg = detail.data?.error || '无错误信息';

            alert(`仿真错误 - ${simulationId}\n\n${errorMsg}`);
            // TODO: 使用实际的模态框组件

        } catch (error) {
            showError('获取错误信息失败', error);
        }
    }


    /**
     * 停止监控
     */
    stopMonitoring() {
        console.log('[SimulationMonitor] Stopping monitoring');
        this.isMonitoring = false;

        if (this.monitoringTimer) {
            clearInterval(this.monitoringTimer);
            this.monitoringTimer = null;
        }

        // 隐藏取消按钮
        const btnCancel = this.container.querySelector('#btn-cancel-batch');
        if (btnCancel) {
            btnCancel.style.display = 'none';
        }
    }


    /**
     * 取消批次仿真
     */
    async cancelBatch() {
        if (!this.batchId) {
            showError('无批次ID,无法取消');
            return;
        }

        const confirmed = confirm('确定要取消此批次仿真吗?');
        if (!confirmed) return;

        try {
            await this.apiClient.cancelBatchSimulations(this.batchId, true);
            showSuccess('批次已取消');
            this.stopMonitoring();

        } catch (error) {
            showError('取消批次失败', error);
        }
    }


    /**
     * 销毁组件 (清理资源)
     */
    destroy() {
        this.stopMonitoring();
        this.container.innerHTML = '';
    }
}


/**
 * 全局辅助函数: 查看仿真结果
 *
 * @param {string} simulationId - 仿真ID
 */
window.viewSimulationResults = function(simulationId) {
    // 跳转到结果页面
    window.location.href = `/simulations/${simulationId}/results`;
};
