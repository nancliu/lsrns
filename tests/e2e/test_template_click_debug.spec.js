/**
 * Debug Template Click
 */

const { test, expect } = require('@playwright/test');

test('调试模板点击', async ({ page }) => {
  const errors = [];
  const logs = [];

  // 捕获所有控制台消息
  page.on('console', msg => {
    const text = msg.text();
    logs.push(`[${msg.type()}] ${text}`);
    console.log(`[Browser ${msg.type()}]:`, text);
  });

  // 捕获页面错误
  page.on('pageerror', err => {
    errors.push(err.message);
    console.error(`[Page Error]:`, err.message);
  });

  // 访问页面
  await page.goto('http://localhost:8000/control/templates.html');
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  console.log('\n=== 查找模板卡片 ===');

  // 等待模板加载
  await page.waitForSelector('.template-card');

  // 列出所有模板
  const templates = await page.$$eval('.template-card', cards => {
    return cards.map((card, i) => {
      const title = card.querySelector('.template-title')?.textContent;
      const badge = card.querySelector('.strategy-badge')?.textContent;
      return { index: i, title, badge };
    });
  });

  console.log('所有模板:', templates);

  // 找到第一个 DHS 模板
  const dhsIndex = templates.findIndex(t => t.badge && t.badge.includes('动态硬路肩'));
  console.log('DHS 模板索引:', dhsIndex);

  if (dhsIndex >= 0) {
    console.log('\n=== 点击 DHS 模板 ===');

    // 直接通过索引点击
    await page.locator('.template-card').nth(dhsIndex).click();

    await page.waitForTimeout(1500);

    console.log('\n=== 检查结果 ===');

    // 检查 selectedTemplate
    const result = await page.evaluate(() => {
      return {
        selectedTemplate: window.selectedTemplate ? {
          template_name: window.selectedTemplate.template_name,
          strategy_type: window.selectedTemplate.strategy_type
        } : null,
        currentStep: window.currentStep
      };
    });

    console.log('Result:', JSON.stringify(result, null, 2));

    // 检查控制台错误
    console.log('\n=== 错误列表 ===');
    if (errors.length > 0) {
      console.error('发现错误:', errors);
    } else {
      console.log('无错误');
    }

    // 检查是否有 selectTemplate 相关的日志
    const selectTemplateLogs = logs.filter(log => log.includes('selectTemplate'));
    console.log('\n=== selectTemplate 相关日志 ===');
    console.log(selectTemplateLogs);

    expect(result.selectedTemplate).toBeTruthy();
  } else {
    console.error('未找到 DHS 模板');
  }
});
