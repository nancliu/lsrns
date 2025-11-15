/**
 * Event Batch Management Module
 *
 * 事件场景批次管理模块
 * 处理事件批次的创建、监控和结果展示
 */

const BATCH_API_BASE = '/api/v1/batch';

/**
 * 事件批次管理类
 */
class EventBatchManager {
    constructor(apiClient) {
        this.api = apiClient;
        this.monitoringInterval = null;
        this.currentBatchId = null;
    }

    /**
     * 获取已完成的批次列表
     */
    async getCompletedBatches(limit = 50) {
        try {
            const response = await this.api.request(`${BATCH_API_BASE}/list-event-batches?status=completed&limit=${limit}`);
            return response.data?.batches || response.batches || [];
        } catch (error) {
            console.error('获取批次列表失败:', error);
            return [];
        }
    }

    /**
     * 获取批次状态
     */
    async getBatchStatus(batchId) {
        try {
            const response = await this.api.request(`${BATCH_API_BASE}/event-batch-status/${batchId}`);
            return response.data || response;
        } catch (error) {
            console.error(`获取批次状态失败 (${batchId}):`, error);
            throw error;
        }
    }

    /**
     * 获取批次结果
     */
    async getBatchResults(batchId) {
        try {
            const response = await this.api.request(`${BATCH_API_BASE}/event-batch-results/${batchId}`);
            return response.data || response;
        } catch (error) {
            console.error(`获取批次结果失败 (${batchId}):`, error);
            throw error;
        }
    }

    /**
     * 创建事件批次
     */
    async createEventBatch(eventId, scenarioIds, simulationConfig) {
        try {
            const response = await this.api.request(`${BATCH_API_BASE}/create-from-event`, {
                method: 'POST',
                body: JSON.stringify({
                    event_id: eventId,
                    scenario_ids: scenarioIds,
                    simulation_config: simulationConfig
                })
            });
            return response.data || response;
        } catch (error) {
            console.error('创建事件批次失败:', error);
            throw error;
        }
    }

    /**
     * 启动事件批次仿真
     */
    async startEventBatch(batchId, parallelWorkers = 4, autoRunAnalysis = true) {
        try {
            const response = await this.api.request(`${BATCH_API_BASE}/start-event-batch`, {
                method: 'POST',
                body: JSON.stringify({
                    batch_id: batchId,
                    parallel_workers: parallelWorkers,
                    auto_run_analysis: autoRunAnalysis
                })
            });
            return response.data || response;
        } catch (error) {
            console.error('启动事件批次失败:', error);
            throw error;
        }
    }

    /**
     * 启动批次监控
     */
    startMonitoring(batchId, callback, interval = 10000) {
        this.currentBatchId = batchId;
        this.stopMonitoring();

        const monitor = async () => {
            try {
                const status = await this.getBatchStatus(batchId);
                if (callback) {
                    callback(status);
                }

                // 如果批次完成，停止监控
                if (status.status === 'completed' || status.status === 'failed') {
                    this.stopMonitoring();
                }
            } catch (error) {
                console.error('监控批次状态失败:', error);
            }
        };

        // 立即执行一次
        monitor();

        // 设置定时器
        this.monitoringInterval = setInterval(monitor, interval);
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
    }
}

// 导出供全局使用
window.EventBatchManager = EventBatchManager;
