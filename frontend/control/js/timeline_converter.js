/**
 * Timeline Data Converter (时间轴数据转换器)
 *
 * 在SUMO步骤点格式和UI时间段格式之间转换
 * - SUMO格式: [{time_hours, speed_kmh}, ...] (步骤点)
 * - UI格式: [{start_hours, end_hours, speed_kmh}, ...] (时间段)
 *
 * @module timeline_converter
 */

(function() {
  'use strict';

  /**
   * 将步骤点数组转换为时间段数组 (SUMO → UI)
   *
   * @param {Array} steps - 步骤点数组 [{time_hours, speed_kmh}, ...]
   * @param {number} endHour - 结束小时 (默认24)
   * @returns {Array} 时间段数组 [{start_hours, end_hours, speed_kmh}, ...]
   *
   * @example
   * input: [{time_hours: 7, speed_kmh: 80}, {time_hours: 9, speed_kmh: 60}]
   * output: [{start_hours: 7, end_hours: 9, speed_kmh: 80}, {start_hours: 9, end_hours: 24, speed_kmh: 60}]
   */
  function stepsToIntervals(steps, endHour = 24) {
    if (!Array.isArray(steps) || steps.length === 0) {
      console.warn('[stepsToIntervals] Empty or invalid steps array');
      return [];
    }

    // 按时间排序
    const sortedSteps = [...steps].sort((a, b) => a.time_hours - b.time_hours);
    const intervals = [];

    for (let i = 0; i < sortedSteps.length; i++) {
      const currentStep = sortedSteps[i];
      const nextStep = sortedSteps[i + 1];

      const start_hours = currentStep.time_hours;
      const end_hours = nextStep ? nextStep.time_hours : endHour;
      const speed_kmh = currentStep.speed_kmh;

      intervals.push({
        start_hours,
        end_hours,
        speed_kmh
      });
    }

    console.log('[stepsToIntervals] Converted:', { steps: sortedSteps, intervals });
    return intervals;
  }

  /**
   * 将时间段数组转换为步骤点数组 (UI → SUMO)
   *
   * @param {Array} intervals - 时间段数组 [{start_hours, end_hours, speed_kmh}, ...]
   * @returns {Array} 步骤点数组 [{time_hours, speed_kmh}, ...]
   *
   * @example
   * input: [{start_hours: 7, end_hours: 9, speed_kmh: 80}, {start_hours: 9, end_hours: 17, speed_kmh: 60}]
   * output: [{time_hours: 7, speed_kmh: 80}, {time_hours: 9, speed_kmh: 60}]
   */
  function intervalsToSteps(intervals) {
    if (!Array.isArray(intervals) || intervals.length === 0) {
      console.warn('[intervalsToSteps] Empty or invalid intervals array');
      return [];
    }

    // 按开始时间排序
    const sortedIntervals = [...intervals].sort((a, b) => a.start_hours - b.start_hours);
    const steps = [];

    sortedIntervals.forEach(interval => {
      steps.push({
        time_hours: interval.start_hours,
        speed_kmh: interval.speed_kmh
      });
    });

    console.log('[intervalsToSteps] Converted:', { intervals: sortedIntervals, steps });
    return steps;
  }

  /**
   * 验证时间段数组的连续性和完整性
   *
   * @param {Array} intervals - 时间段数组
   * @param {Object} options - 验证选项
   * @param {boolean} options.requireContinuous - 是否要求连续 (默认true)
   * @param {boolean} options.requireFullCoverage - 是否要求覆盖0-24小时 (默认false)
   * @returns {Object} { valid: boolean, errors: Array }
   */
  function validateIntervals(intervals, options = {}) {
    const {
      requireContinuous = true,
      requireFullCoverage = false
    } = options;

    const errors = [];

    if (!Array.isArray(intervals) || intervals.length === 0) {
      return { valid: false, errors: ['时间段数组为空或无效'] };
    }

    // 按开始时间排序
    const sorted = [...intervals].sort((a, b) => a.start_hours - b.start_hours);

    // 检查每个区间
    sorted.forEach((interval, index) => {
      // 检查时间范围
      if (interval.start_hours < 0 || interval.start_hours >= 24) {
        errors.push(`区间${index + 1}: 开始时间超出范围 (${interval.start_hours})`);
      }
      if (interval.end_hours <= 0 || interval.end_hours > 24) {
        errors.push(`区间${index + 1}: 结束时间超出范围 (${interval.end_hours})`);
      }

      // 检查开始时间 < 结束时间
      if (interval.start_hours >= interval.end_hours) {
        errors.push(`区间${index + 1}: 开始时间 (${interval.start_hours}) 必须小于结束时间 (${interval.end_hours})`);
      }

      // 检查连续性
      if (requireContinuous && index > 0) {
        const prevInterval = sorted[index - 1];
        if (interval.start_hours !== prevInterval.end_hours) {
          errors.push(`区间${index + 1}: 与前一区间不连续 (间隙或重叠)`);
        }
      }
    });

    // 检查完整覆盖
    if (requireFullCoverage) {
      if (sorted[0].start_hours !== 0) {
        errors.push('未覆盖0点开始');
      }
      if (sorted[sorted.length - 1].end_hours !== 24) {
        errors.push('未覆盖到24点结束');
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * 自动修复时间段数组的连续性
   * 通过调整结束时间来确保连续性
   *
   * @param {Array} intervals - 时间段数组
   * @returns {Array} 修复后的时间段数组
   */
  function fixIntervalContinuity(intervals) {
    if (!Array.isArray(intervals) || intervals.length === 0) {
      return intervals;
    }

    const sorted = [...intervals].sort((a, b) => a.start_hours - b.start_hours);
    const fixed = [];

    sorted.forEach((interval, index) => {
      const nextInterval = sorted[index + 1];

      fixed.push({
        start_hours: interval.start_hours,
        end_hours: nextInterval ? nextInterval.start_hours : 24,
        speed_kmh: interval.speed_kmh
      });
    });

    console.log('[fixIntervalContinuity] Fixed:', { original: intervals, fixed });
    return fixed;
  }

  // Export to global scope
  window.TimelineConverter = {
    stepsToIntervals,
    intervalsToSteps,
    validateIntervals,
    fixIntervalContinuity
  };

  console.log('[TimelineConverter] Module loaded successfully');

})();
