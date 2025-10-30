/**
 * Timeline Visualizer Module (时间轴可视化模块)
 *
 * 为管控策略参数提供24小时可视化时间轴组件
 * 支持 VSS（速度步骤）、DHS（区间）和 TEC（流量控制）
 *
 * @module TimelineVisualizer
 * @version 1.0.0
 */

(function(window) {
  'use strict';

  // ==================== 颜色常量 ====================

  const VSS_COLORS = {
    veryHigh: '#10b981',  // ≥100 km/h - 绿色
    high: '#3b82f6',      // 80-99 km/h - 蓝色
    medium: '#f59e0b',    // 60-79 km/h - 橙色
    low: '#ef4444'        // <60 km/h - 红色
  };

  const DHS_COLORS = {
    open: '#10b981',      // OPEN 状态 - 绿色
    closed: '#ef4444'     // CLOSED 状态 - 红色
  };

  const TEC_COLORS = {
    high: '#ef4444',      // ≥400 vph - 红色（高拥堵）
    medium: '#f59e0b',    // 200-399 vph - 橙色
    low: '#10b981'        // <200 vph - 绿色（顺畅）
  };

  // ==================== 工具函数 ====================

  /**
   * 将小时（0-24）转换为百分比（0-100）
   * @param {number} hours - 小时值 (0-24)
   * @returns {number} 百分比值 (0-100)
   */
  function timeToPercentage(hours) {
    // 输入验证：限制在 0-24 范围
    const clampedHours = Math.max(0, Math.min(24, hours));
    return (clampedHours / 24) * 100;
  }

  /**
   * 根据速度值获取颜色（VSS）
   * @param {number} speed_kmh - 速度值（km/h）
   * @returns {string} 十六进制颜色值
   */
  function getSpeedColor(speed_kmh) {
    if (speed_kmh >= 100) return VSS_COLORS.veryHigh;
    if (speed_kmh >= 80) return VSS_COLORS.high;
    if (speed_kmh >= 60) return VSS_COLORS.medium;
    return VSS_COLORS.low;
  }

  /**
   * 根据状态获取颜色（DHS）
   * @param {string} status - 状态值 ('OPEN' | 'CLOSED')
   * @returns {string} 十六进制颜色值
   */
  function getDHSColor(status) {
    return status === 'OPEN' ? DHS_COLORS.open : DHS_COLORS.closed;
  }

  /**
   * 根据流量值获取颜色（TEC）
   * @param {number} vehsPerHour - 每小时车辆数
   * @returns {string} 十六进制颜色值
   */
  function getFlowColor(vehsPerHour) {
    if (vehsPerHour >= 400) return TEC_COLORS.high;
    if (vehsPerHour >= 200) return TEC_COLORS.medium;
    return TEC_COLORS.low;
  }

  /**
   * 根据区间和类型获取颜色
   * @param {Object} interval - 区间对象
   * @param {string} type - 策略类型 ('speed' | 'dhs' | 'flow')
   * @returns {string} 十六进制颜色值
   */
  function getColorForValue(interval, type) {
    switch (type) {
      case 'speed':
        return getSpeedColor(interval.speed_kmh);
      case 'dhs':
        return getDHSColor(interval.status);
      case 'flow':
        return getFlowColor(interval.flow_vph);
      default:
        return '#6b7280'; // 默认灰色
    }
  }

  /**
   * 根据区间和类型获取标签文本
   * @param {Object} interval - 区间对象
   * @param {string} type - 策略类型 ('speed' | 'dhs' | 'flow')
   * @returns {string} 标签文本
   */
  function getSlotLabel(interval, type) {
    switch (type) {
      case 'speed':
        return `${interval.speed_kmh} km/h`;
      case 'dhs':
        return interval.status === 'OPEN' ? '开启' : '关闭';
      case 'flow':
        return `${interval.flow_vph} 车/时`;
      default:
        return '';
    }
  }

  // ==================== DOM 创建函数 ====================

  /**
   * 创建时间槽 DOM 元素
   * @param {Object} interval - 区间对象
   * @param {number} interval.start - 开始时间（小时）
   * @param {number} interval.width - 宽度（小时）
   * @param {*} interval.value - 值（速度/状态/流量）
   * @param {Object} options - 选项
   * @param {string} options.type - 策略类型
   * @returns {HTMLElement} 时间槽元素
   */
  function createTimelineSlot(interval, options) {
    const slot = document.createElement('div');
    slot.className = 'timeline-slot';

    // 计算位置和宽度（百分比）
    const leftPercent = timeToPercentage(interval.start);
    const widthPercent = timeToPercentage(interval.width);

    slot.style.left = `${leftPercent}%`;
    slot.style.width = `${widthPercent}%`;

    // 设置背景颜色和透明度
    const bgColor = getColorForValue(interval, options.type);
    slot.style.backgroundColor = bgColor;
    slot.style.opacity = '0.7';

    // 创建标签
    const label = document.createElement('div');
    label.className = 'timeline-slot-label';
    label.textContent = getSlotLabel(interval, options.type);
    slot.appendChild(label);

    return slot;
  }

  /**
   * 创建空时间轴（无数据时显示）
   * @param {string} parameterName - 参数名称
   * @returns {HTMLElement} 空时间轴元素
   */
  function createEmptyTimeline(parameterName) {
    const container = document.createElement('div');
    container.className = 'parameter-timeline parameter-timeline-empty';
    container.dataset.parameterName = parameterName;

    const message = document.createElement('div');
    message.className = 'timeline-empty-message';
    message.textContent = '未配置时间数据';
    container.appendChild(message);

    return container;
  }

  // ==================== 时间槽计算函数 ====================

  /**
   * 从 VSS 步骤数组计算时间槽
   * @param {Array} steps - 步骤数组
   * @returns {Array} 时间槽数组
   */
  function calculateStepSlots(steps) {
    const slots = [];
    for (let i = 0; i < steps.length; i++) {
      const start = steps[i].time_hours;
      const end = (i + 1 < steps.length) ? steps[i + 1].time_hours : 24;
      const width = end - start;

      if (width > 0) {
        slots.push({
          start: start,
          width: width,
          speed_kmh: steps[i].speed_kmh
        });
      }
    }
    return slots;
  }

  /**
   * 从 DHS/TEC 区间数组计算时间槽
   * @param {Array} intervals - 区间数组
   * @returns {Array} 时间槽数组
   */
  function calculateIntervalSlots(intervals) {
    return intervals.map(interval => ({
      start: interval.begin_hours,
      width: interval.end_hours - interval.begin_hours,
      status: interval.status,
      flow_vph: interval.flow_vph
    })).filter(slot => slot.width > 0);
  }

  // ==================== 主渲染函数 ====================

  /**
   * 渲染时间轴组件
   * @param {string} parameterName - 参数名称
   * @param {Array} intervals - 区间数组
   * @param {Object} options - 选项对象
   * @param {string} options.type - 策略类型 ('speed' | 'dhs' | 'flow')
   * @param {number} [options.height=100] - 时间轴高度（像素）
   * @param {boolean} [options.showLabels=true] - 是否显示标签
   * @returns {HTMLElement} 时间轴容器元素
   */
  function renderTimeline(parameterName, intervals, options) {
    // 验证输入
    if (!Array.isArray(intervals) || intervals.length === 0) {
      console.warn(`Timeline: 无数据用于参数 "${parameterName}"`);
      return createEmptyTimeline(parameterName);
    }

    // 过滤有效区间
    const validIntervals = intervals.filter(interval => {
      const start = interval.time_hours !== undefined ? interval.time_hours : interval.begin_hours;
      const end = interval.end_hours !== undefined ? interval.end_hours : 24;
      return start !== undefined && start >= 0 && start < 24 && (end === undefined || (end > start && end <= 24));
    });

    if (validIntervals.length === 0) {
      console.warn(`Timeline: 所有区间无效，参数 "${parameterName}"`);
      return createEmptyTimeline(parameterName);
    }

    // 创建容器
    const container = document.createElement('div');
    container.className = 'parameter-timeline';
    container.dataset.parameterName = parameterName;
    container.dataset.type = options.type;

    // 设置高度
    if (options.height) {
      container.style.height = `${options.height}px`;
    }

    // 创建小时标记
    const hoursContainer = document.createElement('div');
    hoursContainer.className = 'timeline-hours';

    for (let i = 0; i < 24; i++) {
      const hourDiv = document.createElement('div');
      hourDiv.className = 'timeline-hour';
      hourDiv.textContent = i.toString().padStart(2, '0');
      hoursContainer.appendChild(hourDiv);
    }
    container.appendChild(hoursContainer);

    // 创建时间槽容器
    const slotsContainer = document.createElement('div');
    slotsContainer.className = 'timeline-slots';

    // 计算时间槽
    let slots;
    if (options.type === 'speed') {
      slots = calculateStepSlots(validIntervals);
    } else {
      slots = calculateIntervalSlots(validIntervals);
    }

    // 渲染时间槽
    slots.forEach(slot => {
      const slotElement = createTimelineSlot(slot, options);
      slotsContainer.appendChild(slotElement);
    });

    container.appendChild(slotsContainer);

    return container;
  }

  /**
   * 更新现有时间轴
   * @param {HTMLElement} timelineElement - 现有时间轴元素
   * @param {Array} intervals - 新的区间数组
   * @param {Object} options - 选项对象
   */
  function updateTimeline(timelineElement, intervals, options) {
    if (!timelineElement || !timelineElement.classList.contains('parameter-timeline')) {
      console.error('Timeline: 无效的时间轴元素');
      return;
    }

    // 获取时间槽容器
    const slotsContainer = timelineElement.querySelector('.timeline-slots');
    if (!slotsContainer) {
      console.error('Timeline: 找不到时间槽容器');
      return;
    }

    // 清除现有时间槽
    slotsContainer.innerHTML = '';

    // 验证输入
    if (!Array.isArray(intervals) || intervals.length === 0) {
      return;
    }

    // 过滤有效区间
    const validIntervals = intervals.filter(interval => {
      const start = interval.time_hours !== undefined ? interval.time_hours : interval.begin_hours;
      const end = interval.end_hours !== undefined ? interval.end_hours : 24;
      return start !== undefined && start >= 0 && start < 24 && (end === undefined || (end > start && end <= 24));
    });

    if (validIntervals.length === 0) {
      return;
    }

    // 计算时间槽
    let slots;
    if (options.type === 'speed') {
      slots = calculateStepSlots(validIntervals);
    } else {
      slots = calculateIntervalSlots(validIntervals);
    }

    // 渲染新时间槽
    slots.forEach(slot => {
      const slotElement = createTimelineSlot(slot, options);
      slotsContainer.appendChild(slotElement);
    });
  }

  // ==================== 导出 API ====================

  window.TimelineVisualizer = {
    renderTimeline: renderTimeline,
    updateTimeline: updateTimeline,
    // 导出工具函数供测试使用
    utils: {
      timeToPercentage: timeToPercentage,
      getSpeedColor: getSpeedColor,
      getDHSColor: getDHSColor,
      getFlowColor: getFlowColor
    }
  };

})(window);
