/**
 * Shared Utility Functions (Task 2.4 - Week 2 Phase 2)
 *
 * 通用工具函数,可在所有前端组件中复用
 * 遵循 RULE-FE-001: 无硬编码数据,无重复函数
 *
 * @module shared-utils
 */


/**
 * 格式化日期时间为本地字符串
 *
 * @param {string} dateString - ISO格式日期字符串 (e.g., "2025-11-12T10:30:00")
 * @param {string} locale - 语言区域 (default: 'zh-CN')
 * @returns {string} 格式化的日期时间字符串
 *
 * @example
 * formatDate("2025-11-12T10:30:00")
 * // => "2025/11/12 10:30:00"
 */
export function formatDate(dateString, locale = 'zh-CN') {
    if (!dateString) return '-';

    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            return dateString; // 无效日期,返回原字符串
        }
        return date.toLocaleString(locale, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    } catch (error) {
        console.error('Date formatting error:', error);
        return dateString;
    }
}


/**
 * 格式化秒数为 HH:MM:SS 格式
 *
 * @param {number} seconds - 总秒数
 * @returns {string} 格式化的时间字符串
 *
 * @example
 * formatTime(3661) // => "01:01:01"
 * formatTime(90)   // => "00:01:30"
 */
export function formatTime(seconds) {
    if (seconds == null || isNaN(seconds)) return '00:00:00';

    const totalSeconds = Math.floor(seconds);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;

    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}


/**
 * 获取状态对应的 Badge CSS 类名
 *
 * @param {string} status - 状态值 (pending|running|completed|failed|queued|cancelled)
 * @returns {string} Bootstrap badge class
 *
 * @example
 * getStatusBadgeClass('running')   // => 'badge-primary'
 * getStatusBadgeClass('completed') // => 'badge-success'
 */
export function getStatusBadgeClass(status) {
    const mapping = {
        'pending': 'badge-secondary',
        'queued': 'badge-secondary',
        'running': 'badge-primary',
        'in_progress': 'badge-primary',
        'completed': 'badge-success',
        'done': 'badge-success',
        'failed': 'badge-danger',
        'error': 'badge-danger',
        'cancelled': 'badge-warning',
        'canceled': 'badge-warning'
    };
    return mapping[status?.toLowerCase()] || 'badge-secondary';
}


/**
 * 获取状态对应的中文文本
 *
 * @param {string} status - 状态值
 * @returns {string} 中文状态文本
 */
export function getStatusText(status) {
    const mapping = {
        'pending': '等待中',
        'queued': '排队中',
        'running': '运行中',
        'in_progress': '进行中',
        'completed': '已完成',
        'done': '完成',
        'failed': '失败',
        'error': '错误',
        'cancelled': '已取消',
        'canceled': '已取消'
    };
    return mapping[status?.toLowerCase()] || status;
}


/**
 * 获取状态对应的颜色
 *
 * @param {string} status - 状态值
 * @returns {string} 颜色值 (hex)
 */
export function getColorForStatus(status) {
    const mapping = {
        'pending': '#6c757d',    // gray
        'queued': '#6c757d',
        'running': '#007bff',    // blue
        'in_progress': '#007bff',
        'completed': '#28a745',  // green
        'done': '#28a745',
        'failed': '#dc3545',     // red
        'error': '#dc3545',
        'cancelled': '#ffc107',  // yellow
        'canceled': '#ffc107'
    };
    return mapping[status?.toLowerCase()] || '#6c757d';
}


/**
 * Promise 延迟工具函数
 *
 * @param {number} ms - 延迟毫秒数
 * @returns {Promise<void>}
 *
 * @example
 * await delay(1000); // 延迟 1 秒
 */
export async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


/**
 * 解析 URL 查询参数
 *
 * @param {string} queryString - URL 查询字符串 (可选,默认使用当前页面)
 * @returns {Object} 键值对对象
 *
 * @example
 * // URL: http://example.com?case_id=123&tab=simulations
 * parseQuery() // => { case_id: "123", tab: "simulations" }
 */
export function parseQuery(queryString) {
    const query = queryString || window.location.search;
    const params = new URLSearchParams(query);
    const result = {};

    for (const [key, value] of params.entries()) {
        result[key] = value;
    }

    return result;
}


/**
 * 格式化文件大小
 *
 * @param {number} bytes - 字节数
 * @param {number} decimals - 小数位数 (default: 2)
 * @returns {string} 格式化的文件大小字符串
 *
 * @example
 * formatFileSize(1024)       // => "1.00 KB"
 * formatFileSize(1048576)    // => "1.00 MB"
 * formatFileSize(1073741824) // => "1.00 GB"
 */
export function formatFileSize(bytes, decimals = 2) {
    if (bytes === 0 || bytes == null) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}


/**
 * 计算百分比
 *
 * @param {number} part - 部分值
 * @param {number} total - 总值
 * @param {number} decimals - 小数位数 (default: 1)
 * @returns {number} 百分比 (0-100)
 *
 * @example
 * calculatePercentage(45, 100) // => 45.0
 * calculatePercentage(1, 3, 2) // => 33.33
 */
export function calculatePercentage(part, total, decimals = 1) {
    if (total === 0 || total == null) return 0;
    const percent = (part / total) * 100;
    return parseFloat(percent.toFixed(decimals));
}


/**
 * 估算剩余时间 (ETA)
 *
 * @param {number} completed - 已完成数
 * @param {number} total - 总数
 * @param {number} elapsedSeconds - 已用时间 (秒)
 * @returns {string} 格式化的ETA字符串 (ISO format)
 *
 * @example
 * estimateRemainingTime(40, 100, 600)
 * // 已完成40%,用时600秒 => 剩余需要900秒
 */
export function estimateRemainingTime(completed, total, elapsedSeconds) {
    if (completed === 0 || total === 0) return null;

    const avgTimePerItem = elapsedSeconds / completed;
    const remainingItems = total - completed;
    const remainingSeconds = avgTimePerItem * remainingItems;

    const eta = new Date(Date.now() + remainingSeconds * 1000);
    return eta.toISOString();
}


/**
 * 截断文本 (超出长度添加省略号)
 *
 * @param {string} text - 原始文本
 * @param {number} maxLength - 最大长度
 * @param {string} suffix - 后缀 (default: '...')
 * @returns {string} 截断后的文本
 *
 * @example
 * truncateText("This is a long text", 10) // => "This is a..."
 */
export function truncateText(text, maxLength, suffix = '...') {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + suffix;
}


/**
 * 防抖函数 (Debounce)
 *
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间 (毫秒)
 * @returns {Function} 防抖后的函数
 *
 * @example
 * const debouncedSearch = debounce(searchFunction, 300);
 * input.addEventListener('input', debouncedSearch);
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}


/**
 * 节流函数 (Throttle)
 *
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间 (毫秒)
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}


/**
 * 显示成功提示 (使用 Bootstrap toast 或 alert)
 *
 * @param {string} message - 提示消息
 * @param {number} duration - 持续时间 (毫秒, default: 3000)
 */
export function showSuccess(message, duration = 3000) {
    // 简化版实现 - 可根据实际UI框架调整
    console.log('[SUCCESS]', message);
    // TODO: 集成实际的 Toast 组件
    alert(`✅ ${message}`);
}


/**
 * 显示错误提示
 *
 * @param {string} message - 错误消息
 * @param {Error} error - 错误对象 (可选)
 */
export function showError(message, error = null) {
    console.error('[ERROR]', message, error);
    // TODO: 集成实际的 Toast 组件
    alert(`❌ ${message}`);
}


/**
 * 显示警告提示
 *
 * @param {string} message - 警告消息
 */
export function showWarning(message) {
    console.warn('[WARNING]', message);
    // TODO: 集成实际的 Toast 组件
    alert(`⚠️ ${message}`);
}
