/**
 * 通用UI工具模块
 *
 * 职责：
 * - 提供Toast通知组件
 * - 提供Modal弹窗组件
 * - 提供HTML转义工具（防XSS）
 *
 * 遵循单一职责原则，每个函数≤30行
 */

/**
 * 显示Toast提示
 * @param {string} type - 类型: 'success' | 'error' | 'warning' | 'info'
 * @param {string} message - 提示信息
 * @param {number} duration - 显示时长（毫秒），默认3000
 */
function showToast(type, message, duration = 3000) {
    const container = getToastContainer();
    const toast = createToastElement(type, message);

    container.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => removeToast(toast), duration);
}

/**
 * 获取Toast容器（不存在则创建）
 * @returns {HTMLElement} Toast容器
 */
function getToastContainer() {
    let container = document.getElementById('toast-container');

    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    return container;
}

/**
 * 创建Toast元素
 * @param {string} type - Toast类型
 * @param {string} message - 消息内容
 * @returns {HTMLElement} Toast元素
 */
function createToastElement(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    return toast;
}

/**
 * 移除Toast（带淡出动画）
 * @param {HTMLElement} toast - Toast元素
 */
function removeToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
}

/**
 * 显示Modal弹窗
 * @param {string} contentHTML - Modal内容HTML
 */
function showModal(contentHTML) {
    const modal = createModalElement(contentHTML);
    const container = getModalContainer();

    container.innerHTML = '';
    container.appendChild(modal);
    container.style.display = 'flex';

    attachModalCloseHandlers(container);
}

/**
 * 创建Modal元素
 * @param {string} contentHTML - 内容HTML
 * @returns {HTMLElement} Modal元素
 */
function createModalElement(contentHTML) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = contentHTML;
    return modal;
}

/**
 * 获取Modal容器（不存在则创建）
 * @returns {HTMLElement} Modal容器
 */
function getModalContainer() {
    let container = document.getElementById('modal-container');

    if (!container) {
        container = document.createElement('div');
        container.id = 'modal-container';
        container.className = 'modal-container';
        document.body.appendChild(container);
    }

    return container;
}

/**
 * 绑定Modal关闭事件处理器
 * @param {HTMLElement} container - Modal容器
 */
function attachModalCloseHandlers(container) {
    // 点击背景关闭
    container.addEventListener('click', (e) => {
        if (e.target === container) {
            closeModal(container);
        }
    });

    // 点击关闭按钮
    const closeButtons = container.querySelectorAll('[data-action="close-modal"]');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => closeModal(container));
    });
}

/**
 * 关闭Modal弹窗
 * @param {HTMLElement} container - Modal容器
 */
function closeModal(container) {
    container.style.display = 'none';
    container.innerHTML = '';
}

/**
 * HTML转义（防止XSS攻击）
 * @param {string} str - 原始字符串
 * @returns {string} 转义后的字符串
 */
function escapeHTML(str) {
    if (!str) return '';

    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
