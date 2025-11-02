/**
 * 方案验证UI更新模块
 *
 * 职责：
 * - 更新验证状态显示
 * - 控制按钮状态
 * - 显示验证警告弹窗
 *
 * 单一职责：仅负责UI更新，不包含业务逻辑
 * 依赖：ui-utils.js（Toast、Modal）
 */

/**
 * 更新验证状态显示
 * @param {string} planId - 方案ID
 * @param {string} status - 状态: 'loading' | 'success' | 'warning' | 'error' | 'pending'
 */
function updateValidationStatus(planId, status) {
    const statusElement = document.getElementById(`validation-status-${planId}`);
    if (!statusElement) {
        console.warn(`验证状态元素未找到: validation-status-${planId}`);
        return;
    }

    const config = getStatusConfig(status);
    statusElement.innerHTML = `<i class="status-icon">${config.icon}</i> ${config.text}`;
    statusElement.className = `validation-status ${config.className}`;
}

/**
 * 获取状态配置
 * @param {string} status - 状态类型
 * @returns {Object} 状态配置对象
 */
function getStatusConfig(status) {
    const statusConfigs = {
        loading: { icon: '⏳', text: '验证中...', className: 'loading' },
        success: { icon: '✓', text: '验证通过', className: 'success' },
        warning: { icon: '⚠', text: '有警告', className: 'warning' },
        error: { icon: '✗', text: '验证失败', className: 'error' },
        pending: { icon: '⏳', text: '未验证', className: 'pending' }
    };

    return statusConfigs[status] || statusConfigs.pending;
}

/**
 * 设置验证加载状态
 * @param {string} planId - 方案ID
 * @param {boolean} isLoading - 是否加载中
 */
function setValidationLoading(planId, isLoading) {
    if (isLoading) {
        updateValidationStatus(planId, 'loading');
    }
}

/**
 * 禁用/启用验证按钮
 * @param {string} planId - 方案ID
 * @param {boolean} disabled - 是否禁用
 */
function disableValidationButton(planId, disabled) {
    const button = findValidationButton(planId);

    if (button) {
        button.disabled = disabled;
    }
}

/**
 * 查找验证按钮
 * @param {string} planId - 方案ID
 * @returns {HTMLElement|null} 按钮元素
 */
function findValidationButton(planId) {
    const card = document.querySelector(`[data-plan-id="${planId}"]`);
    if (!card) return null;

    return card.querySelector('.btn-validate, [data-action="validate"]');
}

/**
 * 显示警告弹窗
 * @param {string} planId - 方案ID
 * @param {Array} warnings - 警告信息数组
 */
function showWarningModal(planId, warnings) {
    const warningListHTML = createWarningListHTML(warnings);
    const modalHTML = createWarningModalHTML(planId, warningListHTML);

    showModal(modalHTML);
}

/**
 * 创建警告列表HTML
 * @param {Array} warnings - 警告数组
 * @returns {string} HTML字符串
 */
function createWarningListHTML(warnings) {
    if (!warnings || warnings.length === 0) {
        return '<li class="warning-item">无警告信息</li>';
    }

    return warnings
        .map(warning => `<li class="warning-item">${escapeHTML(warning)}</li>`)
        .join('');
}

/**
 * 创建警告弹窗HTML
 * @param {string} planId - 方案ID
 * @param {string} warningListHTML - 警告列表HTML
 * @returns {string} Modal HTML字符串
 */
function createWarningModalHTML(planId, warningListHTML) {
    return `
        <div class="modal-content">
            <div class="modal-header">
                <h3>⚠ XML验证警告</h3>
            </div>
            <div class="modal-body">
                <p>方案 <strong>${escapeHTML(planId)}</strong> 的XML包含以下警告：</p>
                <ul class="warning-list">
                    ${warningListHTML}
                </ul>
            </div>
            <div class="modal-footer">
                <button class="btn-primary" data-action="close-modal">知道了</button>
            </div>
        </div>
    `;
}
