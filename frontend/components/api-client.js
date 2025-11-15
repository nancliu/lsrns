/**
 * Centralized API Client (Task 2.4 - Week 2 Phase 2)
 *
 * 集中管理所有API调用,提供错误处理和请求重试
 * 遵循 RULE-FE-001: 单一数据源,无重复代码
 *
 * @module api-client
 */


/**
 * API 客户端类
 *
 * 提供统一的 HTTP 请求接口,支持:
 * - 自动错误处理
 * - 请求重试 (可选)
 * - 统一的响应格式
 * - 日志记录
 *
 * @class APIClient
 */
export class APIClient {
    /**
     * 构造函数
     *
     * @param {string} baseUrl - API 基础 URL (default: '/api/v1')
     * @param {Object} options - 配置选项
     * @param {number} options.timeout - 超时时间 (毫秒, default: 30000)
     * @param {number} options.maxRetries - 最大重试次数 (default: 0)
     */
    constructor(baseUrl = '/api/v1', options = {}) {
        this.baseUrl = baseUrl;
        this.timeout = options.timeout || 30000;
        this.maxRetries = options.maxRetries || 0;
    }


    /**
     * 通用 HTTP 请求方法
     *
     * @param {string} endpoint - API 端点 (e.g., '/simulation/batch-start')
     * @param {Object} options - Fetch 选项
     * @param {string} options.method - HTTP 方法 (GET|POST|PUT|DELETE)
     * @param {Object} options.headers - 请求头
     * @param {Object|FormData} options.body - 请求体
     * @param {number} retryCount - 当前重试次数 (内部使用)
     * @returns {Promise<Object>} API 响应数据
     *
     * @throws {Error} 网络错误或API错误
     */
    async request(endpoint, options = {}, retryCount = 0) {
        const url = `${this.baseUrl}${endpoint}`;

        const defaultHeaders = {
            'Content-Type': 'application/json'
        };

        const config = {
            method: options.method || 'GET',
            headers: {
                ...defaultHeaders,
                ...options.headers
            },
            ...options
        };

        // 处理请求体 (仅适用于 POST/PUT/PATCH)
        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        try {
            // 创建超时控制
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // 检查 HTTP 状态码
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({
                    message: `HTTP ${response.status}: ${response.statusText}`
                }));

                throw new Error(errorData.message || `Request failed with status ${response.status}`);
            }

            // 解析响应
            const data = await response.json();

            // 检查业务状态码 (假设后端返回 { code, message, data })
            if (data.code && data.code !== 200) {
                throw new Error(data.message || 'API request failed');
            }

            return data;

        } catch (error) {
            // 网络错误或超时 - 尝试重试
            if (error.name === 'AbortError') {
                console.error(`Request timeout: ${endpoint}`);
            }

            if (retryCount < this.maxRetries && this._shouldRetry(error)) {
                console.warn(`Retrying request (${retryCount + 1}/${this.maxRetries}): ${endpoint}`);
                await this._delay(Math.pow(2, retryCount) * 1000); // 指数退避
                return this.request(endpoint, options, retryCount + 1);
            }

            console.error(`Request failed: ${endpoint}`, error);
            throw error;
        }
    }


    /**
     * 判断错误是否应该重试
     *
     * @private
     * @param {Error} error - 错误对象
     * @returns {boolean} 是否重试
     */
    _shouldRetry(error) {
        // 网络错误或超时错误可以重试
        return (
            error.name === 'AbortError' ||
            error.message.includes('network') ||
            error.message.includes('timeout')
        );
    }


    /**
     * 延迟函数
     *
     * @private
     * @param {number} ms - 延迟毫秒数
     * @returns {Promise<void>}
     */
    async _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }


    // ========================================================================
    // Simulation API Methods
    // ========================================================================

    /**
     * 批量启动仿真
     *
     * @param {Object} requestData - 请求数据
     * @param {string[]} requestData.simulation_ids - 仿真ID列表
     * @param {string} requestData.case_id - 案例ID
     * @param {number} requestData.parallel_workers - 并发数 (default: 4)
     * @param {boolean} requestData.auto_run_analysis - 自动分析 (default: true)
     * @returns {Promise<Object>} 响应数据
     *
     * @example
     * const result = await apiClient.batchStartSimulations({
     *     simulation_ids: ['sim_001', 'sim_002'],
     *     case_id: 'case_123',
     *     parallel_workers: 4
     * });
     */
    async batchStartSimulations(requestData) {
        return this.request('/simulation/batch-start', {
            method: 'POST',
            body: requestData
        });
    }


    /**
     * 获取批量仿真状态
     *
     * @param {string} batchId - 批次ID
     * @returns {Promise<Object>} 批次状态数据
     *
     * @example
     * const status = await apiClient.getSimulationBatchStatus('batch_123');
     */
    async getSimulationBatchStatus(batchId) {
        return this.request(`/simulation/batch-status/${batchId}`);
    }


    /**
     * 取消批量仿真
     *
     * @param {string} batchId - 批次ID
     * @param {boolean} graceful - 是否优雅停止 (default: true)
     * @returns {Promise<Object>} 取消结果
     */
    async cancelBatchSimulations(batchId, graceful = true) {
        return this.request('/simulation/batch-cancel', {
            method: 'POST',
            body: { batch_id: batchId, graceful }
        });
    }


    /**
     * 获取单个仿真详情
     *
     * @param {string} simulationId - 仿真ID
     * @returns {Promise<Object>} 仿真详情
     */
    async getSimulationDetail(simulationId) {
        return this.request(`/simulation/${simulationId}`);
    }


    /**
     * 获取案例下的所有仿真
     *
     * @param {string} caseId - 案例ID
     * @returns {Promise<Object>} 仿真列表
     */
    async getCaseSimulations(caseId) {
        return this.request(`/simulations/${caseId}`);
    }


    // ========================================================================
    // Analysis API Methods (Phase 2 - To be implemented)
    // ========================================================================

    /**
     * 启动批量分析
     *
     * @param {Object} requestData - 分析请求数据
     * @returns {Promise<Object>} 分析批次响应
     */
    async startAnalysisBatch(requestData) {
        return this.request('/analysis/run-batch', {
            method: 'POST',
            body: requestData
        });
    }


    /**
     * 获取分析进度
     *
     * @param {string} batchId - 分析批次ID
     * @returns {Promise<Object>} 分析进度数据
     */
    async getAnalysisProgress(batchId) {
        return this.request(`/analysis/batch-progress/${batchId}`);
    }


    /**
     * 获取分析结果 (Task 3.2 - Week 3)
     *
     * @param {string} batchId - 分析批次ID
     * @param {string} caseId - 案例ID
     * @returns {Promise<Object>} 分析结果数据
     */
    async getAnalysisResults(batchId, caseId) {
        const endpoint = `/analysis/results/${batchId}?case_id=${encodeURIComponent(caseId)}`;
        return this.request(endpoint);
    }


    /**
     * 获取对比报告 (Task 3.2 - Week 3)
     *
     * @param {string} batchId - 分析批次ID
     * @param {string} caseId - 案例ID
     * @returns {Promise<Object>} 对比报告数据
     */
    async getComparisonReport(batchId, caseId) {
        const endpoint = `/analysis/comparison/${batchId}?case_id=${encodeURIComponent(caseId)}`;
        return this.request(endpoint);
    }


    // ========================================================================
    // Case API Methods
    // ========================================================================

    /**
     * 创建OD案例
     * 调用 POST /api/v1/case/ 端点创建OD数据处理案例
     *
     * @param {Object} requestData - OD案例创建请求
     * @param {string} requestData.name - 案例名称
     * @param {string} requestData.description - 案例描述
     * @param {string} requestData.network_id - 网络ID (可选)
     * @returns {Promise<Object>} 创建的案例数据
     */
    async createCase(requestData) {
        return this.request('/case/', {
            method: 'POST',
            body: requestData
        });
    }


    /**
     * 从事件场景创建案例（统一端点）
     * 调用统一的事件场景创建端点，包含案例和仿真的自动创建
     *
     * @param {Object} requestData - 案例创建请求
     * @param {string} requestData.scenario_id - 场景ID
     * @param {string} requestData.event_id - 事件ID
     * @returns {Promise<Object>} 创建的案例和仿真数据
     */
    async createCaseFromEventScenario(requestData) {
        return this.request('/case/from-event-scenario', {
            method: 'POST',
            body: requestData
        });
    }


    /**
     * 从事件场景创建案例 - 已弃用
     * 使用 createCaseFromEventScenario() 替代
     *
     * @deprecated 使用 createCaseFromEventScenario() 替代
     */
    async createCaseFromScenario(requestData) {
        return this.createCaseFromEventScenario(requestData);
    }


    /**
     * 获取案例详情
     *
     * @param {string} caseId - 案例ID
     * @returns {Promise<Object>} 案例详情
     */
    async getCaseDetail(caseId) {
        return this.request(`/case/${caseId}`);
    }


    /**
     * 获取所有案例列表
     *
     * @param {Object} filters - 过滤条件 (可选)
     * @returns {Promise<Object>} 案例列表
     */
    async getCaseList(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/case/list?${queryParams}` : '/case/list';
        return this.request(endpoint);
    }


    // ========================================================================
    // File API Methods
    // ========================================================================

    /**
     * 下载文件
     *
     * @param {string} filePath - 文件路径
     * @param {string} filename - 下载的文件名
     * @returns {Promise<void>}
     */
    async downloadFile(filePath, filename) {
        const url = `${this.baseUrl}/file/download?path=${encodeURIComponent(filePath)}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename || 'download';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            console.error('File download error:', error);
            throw error;
        }
    }
}


/**
 * 默认 API 客户端实例
 *
 * @example
 * import { defaultAPIClient } from './api-client.js';
 * const status = await defaultAPIClient.getSimulationBatchStatus('batch_123');
 */
export const defaultAPIClient = new APIClient('/api/v1', {
    timeout: 30000,
    maxRetries: 2
});
