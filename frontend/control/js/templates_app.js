/**
 * templates_app.js
 * 策略管理页面主入口文件
 *
 * 职责:
 * 1. 全局状态管理
 * 2. 模块加载检查
 * 3. 事件总线协调
 * 4. 应用初始化
 *
 * @version 1.0.0
 * @date 2025-10-30
 */

const TemplatesApp = {
    /**
     * 全局应用状态
     */
    state: {
        // 当前步骤 (1: 选择模板, 2: 选择边缘, 3: 配置参数)
        currentStep: 1,

        // 模板数据
        templates: [],
        selectedTemplate: null,

        // 边缘数据
        selectedEdges: [],

        // 策略实例数据
        strategyInstances: {
            all: [],
            currentPage: 1,
            pageSize: 20,
            totalCount: 0
        },

        // UI状态
        isUserEditedName: false,
        isUserEditedDescription: false
    },

    /**
     * 必需的模块列表
     */
    requiredModules: [
        'Notification',
        'TemplateSelector',
        'WizardController',
        'FormValidator',
        'StrategyCRUD',
        'EdgeSelector',
        'networkViz'
    ],

    /**
     * 应用初始化
     */
    init() {
        console.log('=== Templates App Initializing ===');
        console.log('Version: 1.0.0');
        console.log('Timestamp:', new Date().toISOString());

        // 检查模块加载状态
        const allLoaded = this.checkModules();

        if (!allLoaded) {
            console.error('❌ 部分模块未加载，应用可能无法正常工作');
            this.showModuleError();
            return;
        }

        // 绑定全局事件
        this.bindGlobalEvents();

        // 加载初始数据
        this.loadInitialData();

        console.log('✅ Templates App Initialized Successfully');
        console.log('========================================');
    },

    /**
     * 检查所有必需模块是否加载
     * @returns {boolean} 是否所有模块都已加载
     */
    checkModules() {
        console.log('--- Module Loading Check ---');

        let allLoaded = true;
        const moduleStatus = {};

        this.requiredModules.forEach(moduleName => {
            const isLoaded = typeof window[moduleName] !== 'undefined';
            moduleStatus[moduleName] = isLoaded;

            if (isLoaded) {
                console.log(`✅ ${moduleName}: loaded`);
            } else {
                console.error(`❌ ${moduleName}: NOT LOADED`);
                allLoaded = false;
            }
        });

        // 存储模块状态供调试使用
        window._moduleStatus = moduleStatus;

        return allLoaded;
    },

    /**
     * 显示模块加载错误提示
     */
    showModuleError() {
        const errorHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #fff3cd;
                border: 2px solid #ffc107;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                max-width: 500px;
            ">
                <h3 style="margin: 0 0 10px 0; color: #856404;">
                    ⚠️ 模块加载失败
                </h3>
                <p style="margin: 0 0 10px 0;">
                    部分JavaScript模块未能正确加载，页面功能可能受限。
                </p>
                <p style="margin: 0; font-size: 14px; color: #666;">
                    请刷新页面重试，或检查浏览器控制台获取详细信息。
                </p>
                <button onclick="location.reload()" style="
                    margin-top: 15px;
                    padding: 8px 16px;
                    background: #ffc107;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                ">
                    刷新页面
                </button>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', errorHTML);
    },

    /**
     * 绑定全局事件监听器
     */
    bindGlobalEvents() {
        console.log('--- Binding Global Events ---');

        // 模板选择事件
        document.addEventListener('template:selected', (e) => {
            this.state.selectedTemplate = e.detail;
            console.log('📋 Template selected:', e.detail.template_id);
        });

        // 模板更改事件
        document.addEventListener('template:changed', () => {
            this.state.selectedTemplate = null;
            this.state.selectedEdges = [];
            console.log('🔄 Template changed, state reset');
        });

        // 边缘选择事件
        document.addEventListener('edges:selected', (e) => {
            this.state.selectedEdges = e.detail;
            console.log(`🛣️ Edges selected: ${e.detail.length} edges`);
        });

        // 边缘更新事件
        document.addEventListener('edges:updated', (e) => {
            this.state.selectedEdges = e.detail;
            console.log(`🔄 Edges updated: ${e.detail.length} edges`);
        });

        // 步骤切换事件
        document.addEventListener('step:changed', (e) => {
            const { current, previous } = e.detail;
            this.state.currentStep = current;
            console.log(`📍 Step changed: ${previous} → ${current}`);
        });

        // 表单验证事件
        document.addEventListener('form:validated', (e) => {
            const { valid, errors } = e.detail;
            if (valid) {
                console.log('✅ Form validated successfully');
            } else {
                console.warn('⚠️ Form validation failed:', errors);
            }
        });

        // 策略创建成功事件
        document.addEventListener('strategy:created', (e) => {
            console.log('🎉 Strategy created:', e.detail);
            // 刷新策略列表
            if (window.StrategyCRUD) {
                window.StrategyCRUD.fetchStrategyInstances();
            }
        });

        // 策略删除成功事件
        document.addEventListener('strategy:deleted', (e) => {
            console.log('🗑️ Strategy deleted:', e.detail.strategy_id);
            // 刷新策略列表
            if (window.StrategyCRUD) {
                window.StrategyCRUD.fetchStrategyInstances();
            }
        });

        // 可视化加载完成事件
        document.addEventListener('viz:loaded', () => {
            console.log('🗺️ Visualization loaded');
        });

        console.log('✅ Global events bound');
    },

    /**
     * 加载初始数据
     */
    loadInitialData() {
        console.log('--- Loading Initial Data ---');

        // 加载模板列表
        if (window.TemplateSelector && window.TemplateSelector.fetchTemplates) {
            window.TemplateSelector.fetchTemplates();
        } else {
            console.warn('⚠️ TemplateSelector.fetchTemplates not available');
        }

        // 加载策略实例列表
        if (window.StrategyCRUD && window.StrategyCRUD.fetchStrategyInstances) {
            window.StrategyCRUD.fetchStrategyInstances();
        } else {
            console.warn('⚠️ StrategyCRUD.fetchStrategyInstances not available');
        }

        console.log('✅ Initial data loading triggered');
    },

    /**
     * 获取当前状态（供外部模块访问）
     * @returns {Object} 当前应用状态
     */
    getState() {
        return { ...this.state };
    },

    /**
     * 更新状态（供外部模块调用）
     * @param {Object} updates 要更新的状态
     */
    updateState(updates) {
        Object.assign(this.state, updates);
        console.log('🔄 State updated:', Object.keys(updates));
    }
};

/**
 * 暴露到全局作用域（供其他模块访问）
 */
window.TemplatesApp = TemplatesApp;

/**
 * DOM加载完成后初始化应用
 */
document.addEventListener('DOMContentLoaded', () => {
    TemplatesApp.init();
});
