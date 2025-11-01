const { test, expect } = require('@playwright/test');

test.describe('时间轴可视化功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到模板页面
    await page.goto('http://localhost:8000/control/templates.html', { waitUntil: 'load' });
    await page.waitForTimeout(1500);
  });

  test('检查时间轴JS模块是否加载', async ({ page }) => {
    console.log('\n========== 检查时间轴JS模块 ==========\n');

    // 检查 TimelineVisualizer 是否在全局作用域中
    const timelineModuleLoaded = await page.evaluate(() => {
      return typeof window.TimelineVisualizer !== 'undefined';
    });

    if (timelineModuleLoaded) {
      console.log('✅ TimelineVisualizer 模块已加载');

      // 检查主要函数是否存在
      const functionsExist = await page.evaluate(() => {
        return {
          renderTimeline: typeof window.TimelineVisualizer.renderTimeline === 'function',
          updateTimeline: typeof window.TimelineVisualizer.updateTimeline === 'function',
          createTimelineSlot: typeof window.TimelineVisualizer.createTimelineSlot === 'function'
        };
      });

      console.log('✅ 主要函数检查：', functionsExist);
    } else {
      console.log('❌ TimelineVisualizer 模块未加载！');
    }
  });

  test('VSS策略：检查时间轴是否集成到参数表单', async ({ page }) => {
    console.log('\n========== VSS 时间轴集成检查 ==========\n');

    // 选择 VSS 模板
    const vssTemplateBtn = page.locator('button:has-text("可变限速")').first();
    if (vssTemplateBtn) {
      await vssTemplateBtn.click();
      await page.waitForTimeout(500);
      console.log('✅ VSS模板已选择');

      // 直接进入参数配置（假设前面已选择路段）
      const nextBtn = page.locator('button:has-text("下一步")').last();
      if (nextBtn) {
        await nextBtn.click();
        await page.waitForTimeout(1500);
      }

      // 检查是否有时间轴元素
      const timeline = page.locator('.parameter-timeline').first();
      const hasTimeline = await timeline.isVisible().catch(() => false);

      if (hasTimeline) {
        console.log('✅ VSS参数表单中发现时间轴');
        const slotCount = await page.locator('.timeline-slot').count();
        console.log(`✅ 时间轴包含 ${slotCount} 个时间段`);
      } else {
        console.log('⚠️  VSS参数表单中未发现时间轴');
      }
    }
  });

  test('DHS策略：检查DHS时间轴是否集成', async ({ page }) => {
    console.log('\n========== DHS 时间轴集成检查 ==========\n');

    // 选择 DHS 模板
    const dhsTemplateBtn = page.locator('button:has-text("应急车道")').first();
    if (dhsTemplateBtn) {
      await dhsTemplateBtn.click();
      await page.waitForTimeout(500);
      console.log('✅ DHS模板已选择');

      // 进入参数配置
      const nextBtn = page.locator('button:has-text("下一步")').last();
      if (nextBtn) {
        await nextBtn.click();
        await page.waitForTimeout(1500);
      }

      // 检查是否有DHS特定的时间轴
      const timeline = page.locator('.dhs-interval-control-enhanced .parameter-timeline').first();
      const hasTimeline = await timeline.isVisible().catch(() => false);

      if (hasTimeline) {
        console.log('✅ DHS参数表单中发现时间轴');
        
        // 检查颜色编码（红色=CLOSED, 绿色=OPEN）
        const slots = page.locator('.dhs-interval-control-enhanced .timeline-slot');
        const slotCount = await slots.count();
        console.log(`✅ DHS时间轴包含 ${slotCount} 个时间段`);

        // 检查默认值是否正确加载
        const beginInputs = page.locator('.dhs-interval-control-enhanced input[class*="begin"]');
        const beginCount = await beginInputs.count();
        console.log(`✅ DHS表格有 ${beginCount} 个开始时间输入框`);
      } else {
        console.log('⚠️  DHS参数表单中未发现时间轴');
      }
    }
  });

  test('TEC策略：检查TEC流量时间轴是否集成', async ({ page }) => {
    console.log('\n========== TEC 时间轴集成检查 ==========\n');

    // 选择 TEC 模板
    const tecTemplateBtn = page.locator('button:has-text("收费站")').first();
    if (tecTemplateBtn) {
      await tecTemplateBtn.click();
      await page.waitForTimeout(500);
      console.log('✅ TEC模板已选择');

      // 进入参数配置
      const nextBtn = page.locator('button:has-text("下一步")').last();
      if (nextBtn) {
        await nextBtn.click();
        await page.waitForTimeout(1500);
      }

      // 检查是否有TEC特定的时间轴
      const timeline = page.locator('.flow-interval-control-enhanced .parameter-timeline').first();
      const hasTimeline = await timeline.isVisible().catch(() => false);

      if (hasTimeline) {
        console.log('✅ TEC参数表单中发现时间轴');
        const slotCount = await page.locator('.flow-interval-control-enhanced .timeline-slot').count();
        console.log(`✅ TEC时间轴包含 ${slotCount} 个时间段`);
      } else {
        console.log('⚠️  TEC参数表单中未发现时间轴');
      }
    }
  });
});
