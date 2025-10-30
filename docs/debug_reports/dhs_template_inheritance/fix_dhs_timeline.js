/**
 * DHS Timeline Diagnostic and Fix Script
 *
 * 使用方法：
 * 1. 打开浏览器控制台（F12）
 * 2. 复制整个脚本并粘贴到控制台
 * 3. 按 Enter 运行
 *
 * 此脚本将自动诊断并尝试修复 DHS 时间轴问题
 */

(function() {
  'use strict';

  console.log('%c========== DHS Timeline Diagnostic & Fix ==========', 'color: #22c55e; font-weight: bold; font-size: 16px;');
  console.log('运行时间:', new Date().toLocaleString('zh-CN'));
  console.log('');

  let issues = [];
  let fixes = [];

  // ========== 诊断 1: 检查 TimelineVisualizer ==========
  console.log('%c1. 检查 TimelineVisualizer 模块...', 'color: #3b82f6; font-weight: bold;');

  if (typeof window.TimelineVisualizer !== 'undefined') {
    console.log('✅ TimelineVisualizer 已加载');
    console.log('   - renderTimeline:', typeof window.TimelineVisualizer.renderTimeline);
    console.log('   - updateTimeline:', typeof window.TimelineVisualizer.updateTimeline);

    if (typeof window.TimelineVisualizer.utils?.getDHSColor === 'function') {
      console.log('   - getDHSColor:', '✅ 正常');

      // 测试颜色函数
      const openColor = window.TimelineVisualizer.utils.getDHSColor('OPEN');
      const closedColor = window.TimelineVisualizer.utils.getDHSColor('CLOSED');
      console.log('   - OPEN color:', openColor, '(应该是绿色 #22c55e)');
      console.log('   - CLOSED color:', closedColor, '(应该是红色 #ef4444)');
    } else {
      console.warn('⚠️ getDHSColor 函数不可用');
      issues.push('getDHSColor 函数缺失');
    }
  } else {
    console.error('❌ TimelineVisualizer 未加载！');
    issues.push('TimelineVisualizer 模块未加载');
    fixes.push('请检查 templates.html 中是否包含: <script src="js/timeline_visualizer.js"></script>');
    fixes.push('确保该脚本在 parameter_form.js 之前加载');
  }

  console.log('');

  // ========== 诊断 2: 检查 DHS 表格 ==========
  console.log('%c2. 检查 DHS intervals 表格...', 'color: #3b82f6; font-weight: bold;');

  const tbody = document.querySelector('.dhs-intervals-tbody');

  if (tbody) {
    console.log('✅ DHS 表格已找到');
    console.log('   - data-parameter-name:', tbody.dataset.parameterName || '(未设置)');

    const rows = tbody.querySelectorAll('.dhs-interval-row');
    console.log('   - 行数:', rows.length);

    if (rows.length > 0) {
      console.log('✅ 表格有数据行');

      // 验证每一行的输入框
      let allInputsValid = true;
      rows.forEach((row, index) => {
        const beginInput = row.querySelector('.dhs-interval-begin');
        const endInput = row.querySelector('.dhs-interval-end');
        const statusSelect = row.querySelector('.dhs-interval-status');
        const vehiclesInput = row.querySelector('.dhs-interval-vehicles');

        if (!beginInput || !endInput || !statusSelect || !vehiclesInput) {
          console.error(`❌ 第 ${index + 1} 行缺少输入框`);
          allInputsValid = false;
        } else {
          console.log(`   行 ${index + 1}:`, {
            begin: beginInput.value,
            end: endInput.value,
            status: statusSelect.value,
            vehicles: vehiclesInput.value || '(空)'
          });
        }
      });

      if (allInputsValid) {
        console.log('✅ 所有输入框都存在');
      } else {
        issues.push('部分表格行缺少输入框');
      }
    } else {
      console.warn('⚠️ 表格没有数据行');
      issues.push('DHS 表格没有数据行');
      fixes.push('默认应该有 5 行数据，检查 renderDHSIntervalControl() 是否正确添加了默认行');
    }
  } else {
    console.error('❌ DHS 表格未找到！');
    issues.push('DHS intervals 表格未渲染');
    fixes.push('检查 renderDHSIntervalControl() 函数是否被调用');
    fixes.push('检查 parameter_form.js 中的 case "dhs_interval_array" 是否正确路由');

    // 尝试查找其他可能的表格
    const allTables = document.querySelectorAll('tbody[class*="interval"]');
    if (allTables.length > 0) {
      console.log('   找到其他 interval 表格:', allTables.length);
      allTables.forEach((t, i) => {
        console.log(`   [${i}] class="${t.className}", data-parameter-name="${t.dataset.parameterName}"`);
      });
    }
  }

  console.log('');

  // ========== 诊断 3: 检查时间轴元素 ==========
  console.log('%c3. 检查时间轴元素...', 'color: #3b82f6; font-weight: bold;');

  const timeline = document.querySelector('.parameter-timeline');

  if (timeline) {
    const isDHS = timeline.dataset.type === 'dhs';
    console.log(isDHS ? '✅ DHS 时间轴已找到' : '⚠️ 找到时间轴，但类型不是 dhs');
    console.log('   - data-parameter-name:', timeline.dataset.parameterName || '(未设置)');
    console.log('   - data-type:', timeline.dataset.type);

    const hours = timeline.querySelectorAll('.timeline-hour');
    const slots = timeline.querySelectorAll('.timeline-slot');

    console.log('   - 小时标记数:', hours.length, '(应该是 25)');
    console.log('   - 时间槽数:', slots.length);

    if (slots.length > 0) {
      console.log('✅ 时间轴有时间槽');

      // 检查时间槽颜色
      slots.forEach((slot, index) => {
        const bgColor = window.getComputedStyle(slot).backgroundColor;
        const label = slot.querySelector('.timeline-slot-label')?.textContent;
        console.log(`   槽 ${index + 1}: 颜色=${bgColor}, 标签="${label}"`);
      });
    } else {
      console.warn('⚠️ 时间轴没有时间槽');
      issues.push('时间轴渲染但没有时间槽');
      fixes.push('检查 defaultIntervals 是否为空');
      fixes.push('检查 TimelineVisualizer.renderTimeline() 是否正确调用');
    }
  } else {
    console.error('❌ 时间轴元素未找到！');
    issues.push('时间轴未渲染');

    // 检查是否有错误提示
    const errorMsg = document.querySelector('.timeline-error');
    if (errorMsg) {
      console.error('   发现错误提示:', errorMsg.textContent);
      fixes.push('时间轴显示错误提示，说明 TimelineVisualizer 未加载');
    } else {
      fixes.push('时间轴可能在 renderDHSIntervalControl() 中未创建');
      fixes.push('检查是否有 JavaScript 错误阻止了渲染');
    }
  }

  console.log('');

  // ========== 诊断 4: 检查容器 ==========
  console.log('%c4. 检查 DHS 控件容器...', 'color: #3b82f6; font-weight: bold;');

  const container = document.querySelector('.dhs-interval-control-enhanced');

  if (container) {
    console.log('✅ DHS 控件容器已找到');
    console.log('   - 子元素数:', container.children.length);

    Array.from(container.children).forEach((child, i) => {
      let desc = `${child.tagName}`;
      if (child.className) desc += `.${child.className}`;
      if (child.id) desc += `#${child.id}`;
      console.log(`   [${i}] ${desc}`);
    });

    // 验证期望的结构
    const hasTimeline = container.querySelector('.parameter-timeline') !== null;
    const hasTable = container.querySelector('.intervals-table') !== null;
    const hasButtons = container.querySelector('.interval-buttons') !== null;
    const hasHint = container.querySelector('.config-hint') !== null;

    console.log('   结构检查:');
    console.log('      - 时间轴:', hasTimeline ? '✅' : '❌');
    console.log('      - 表格:', hasTable ? '✅' : '❌');
    console.log('      - 按钮:', hasButtons ? '✅' : '❌');
    console.log('      - 使用提示:', hasHint ? '✅' : '❌');

    if (!hasTimeline) {
      issues.push('容器中缺少时间轴元素');
    }
  } else {
    console.error('❌ DHS 控件容器未找到！');
    issues.push('DHS 控件容器未渲染');
    fixes.push('检查 renderDHSIntervalControl() 函数是否被调用');
  }

  console.log('');

  // ========== 诊断 5: 测试参数提取 ==========
  console.log('%c5. 测试参数提取逻辑...', 'color: #3b82f6; font-weight: bold;');

  if (tbody && tbody.querySelectorAll('.dhs-interval-row').length > 0) {
    try {
      const rows = tbody.querySelectorAll('.dhs-interval-row');
      const extractedIntervals = Array.from(rows).map(row => ({
        begin_hours: parseFloat(row.querySelector('.dhs-interval-begin').value),
        end_hours: parseFloat(row.querySelector('.dhs-interval-end').value),
        status: row.querySelector('.dhs-interval-status').value,
        allowed_vehicle_types: row.querySelector('.dhs-interval-vehicles').value
          .split(',').map(v => v.trim()).filter(v => v)
      }));

      console.log('✅ 参数提取成功');
      console.log('   提取的 intervals:', extractedIntervals);

      // 验证数据完整性
      let hasInvalidData = false;
      extractedIntervals.forEach((interval, index) => {
        if (isNaN(interval.begin_hours) || isNaN(interval.end_hours)) {
          console.error(`❌ 第 ${index + 1} 行时间数据无效`);
          hasInvalidData = true;
        }
        if (!interval.status || !['OPEN', 'CLOSED'].includes(interval.status)) {
          console.error(`❌ 第 ${index + 1} 行状态无效:`, interval.status);
          hasInvalidData = true;
        }
      });

      if (!hasInvalidData) {
        console.log('✅ 所有数据有效');
      } else {
        issues.push('部分表格行数据无效');
      }

    } catch (error) {
      console.error('❌ 参数提取失败:', error);
      issues.push('参数提取时出错: ' + error.message);
      fixes.push('检查 templates.html 中的 dhs_interval_array 参数提取逻辑');
    }
  } else {
    console.warn('⚠️ 无法测试参数提取（表格未找到或无数据）');
  }

  console.log('');

  // ========== 总结 ==========
  console.log('%c========== 诊断总结 ==========', 'color: #22c55e; font-weight: bold; font-size: 16px;');

  if (issues.length === 0) {
    console.log('%c✅ 未发现问题！DHS 时间轴应该正常工作。', 'color: #22c55e; font-weight: bold;');
    console.log('如果您仍然看不到时间轴，请尝试：');
    console.log('1. 刷新页面（Ctrl+F5 强制刷新）');
    console.log('2. 清除浏览器缓存');
    console.log('3. 重新选择 DHS 模板');
  } else {
    console.log(`%c❌ 发现 ${issues.length} 个问题:`, 'color: #ef4444; font-weight: bold;');
    issues.forEach((issue, i) => {
      console.log(`   ${i + 1}. ${issue}`);
    });

    console.log('');
    console.log('%c建议的修复方案:', 'color: #f59e0b; font-weight: bold;');
    fixes.forEach((fix, i) => {
      console.log(`   ${i + 1}. ${fix}`);
    });
  }

  console.log('');
  console.log('%c如需进一步帮助，请提供此诊断报告的截图。', 'color: #6b7280;');
  console.log('%c========== 诊断完成 ==========', 'color: #22c55e; font-weight: bold; font-size: 16px;');

  // 返回诊断结果对象（可选）
  return {
    timestamp: new Date().toISOString(),
    issues: issues,
    fixes: fixes,
    hasTimelineVisualizer: typeof window.TimelineVisualizer !== 'undefined',
    hasTable: !!document.querySelector('.dhs-intervals-tbody'),
    hasTimeline: !!document.querySelector('.parameter-timeline'),
    hasContainer: !!document.querySelector('.dhs-interval-control-enhanced')
  };
})();
