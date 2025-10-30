/**
 * 通用提示组件 - 居中显示的消息提示框
 *
 * 用法:
 * showNotification('成功消息', 'success');
 * showNotification('错误消息', 'error');
 * showNotification('警告消息', 'warning');
 * showNotification('信息消息', 'info');
 */

// 确保 DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initNotificationContainer();
});

// 如果页面已经加载完成，立即初始化
if (document.readyState === 'loading') {
    // DOM 还在加载中，事件监听器会处理
} else {
    // DOM 已经加载完成
    initNotificationContainer();
}

/**
 * 初始化提示框容器
 */
function initNotificationContainer() {
    // 检查是否已存在容器
    if (document.getElementById('notification-container')) {
        return;
    }

    // 创建容器
    const container = document.createElement('div');
    container.id = 'notification-container';
    document.body.appendChild(container);

    // 添加样式
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            #notification-container {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 10000;
                pointer-events: none;
            }

            .notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                padding: 16px 24px;
                margin-bottom: 12px;
                min-width: 300px;
                max-width: 500px;
                pointer-events: auto;
                animation: notification-slide-in 0.3s ease-out;
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .notification.notification-success {
                border-left: 4px solid #27ae60;
            }

            .notification.notification-error {
                border-left: 4px solid #e74c3c;
            }

            .notification.notification-warning {
                border-left: 4px solid #f39c12;
            }

            .notification.notification-info {
                border-left: 4px solid #3498db;
            }

            .notification-icon {
                font-size: 24px;
                flex-shrink: 0;
            }

            .notification-success .notification-icon {
                color: #27ae60;
            }

            .notification-error .notification-icon {
                color: #e74c3c;
            }

            .notification-warning .notification-icon {
                color: #f39c12;
            }

            .notification-info .notification-icon {
                color: #3498db;
            }

            .notification-message {
                flex: 1;
                font-size: 14px;
                line-height: 1.5;
                color: #333;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 20px;
                color: #999;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }

            .notification-close:hover {
                color: #666;
            }

            .notification.notification-hiding {
                animation: notification-slide-out 0.3s ease-in forwards;
            }

            @keyframes notification-slide-in {
                from {
                    opacity: 0;
                    transform: translateY(-20px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }

            @keyframes notification-slide-out {
                from {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                to {
                    opacity: 0;
                    transform: translateY(-20px) scale(0.95);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * 显示通知
 * @param {string} message - 消息内容
 * @param {string} type - 类型: 'success', 'error', 'warning', 'info'
 * @param {number} duration - 显示时长(毫秒)，0表示不自动关闭，默认3000
 */
function showNotification(message, type = 'info', duration = 3000) {
    // 确保容器已初始化
    initNotificationContainer();

    const container = document.getElementById('notification-container');

    // 创建提示框元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    // 图标映射
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };

    notification.innerHTML = `
        <div class="notification-icon">${icons[type] || icons.info}</div>
        <div class="notification-message">${message}</div>
        <button class="notification-close" aria-label="关闭">&times;</button>
    `;

    // 添加到容器
    container.appendChild(notification);

    // 关闭按钮事件
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        closeNotification(notification);
    });

    // 自动关闭
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notification);
        }, duration);
    }

    return notification;
}

/**
 * 关闭通知
 * @param {HTMLElement} notification - 通知元素
 */
function closeNotification(notification) {
    notification.classList.add('notification-hiding');
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300); // 等待动画完成
}

/**
 * 显示成功消息
 * @param {string} message - 消息内容
 * @param {number} duration - 显示时长(毫秒)
 */
function showSuccess(message, duration = 3000) {
    return showNotification(message, 'success', duration);
}

/**
 * 显示错误消息
 * @param {string} message - 消息内容
 * @param {number} duration - 显示时长(毫秒)，错误消息默认显示更久
 */
function showError(message, duration = 5000) {
    return showNotification(message, 'error', duration);
}

/**
 * 显示警告消息
 * @param {string} message - 消息内容
 * @param {number} duration - 显示时长(毫秒)
 */
function showWarning(message, duration = 4000) {
    return showNotification(message, 'warning', duration);
}

/**
 * 显示信息消息
 * @param {string} message - 消息内容
 * @param {number} duration - 显示时长(毫秒)
 */
function showInfo(message, duration = 3000) {
    return showNotification(message, 'info', duration);
}
