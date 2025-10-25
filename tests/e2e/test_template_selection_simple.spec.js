/**
 * Simple Template Selection Test
 */

const { test, expect } = require('@playwright/test');

test('测试模板选择', async ({ page }) => {
  // 强制刷新，不使用缓存
  await page.goto('http://localhost:8000/control/templates.html', {
    waitUntil: 'networkidle'
  });

  // 硬刷新
  await page.reload({ waitUntil: 'networkidle' });

  console.log('页面已加载');

  // 等待模板加载
  await page.waitForSelector('.template-card', { timeout: 10000 });

  const templateCount = await page.locator('.template-card').count();
  console.log(`找到 ${templateCount} 个模板`);

  // 获取第一个包含 DHS 的模板
  const dhsCard = page.locator('.template-card').filter({ hasText: /DHS|动态硬路肩/ }).first();

  // 点击前检查 selectedTemplate
  const before = await page.evaluate(() => window.selectedTemplate);
  console.log('点击前 selectedTemplate:', before);

  // 点击模板卡片
  await dhsCard.click();

  // 等待一下
  await page.waitForTimeout(1000);

  // 点击后检查 selectedTemplate
  const after = await page.evaluate(() => {
    if (window.selectedTemplate) {
      return {
        template_name: window.selectedTemplate.template_name,
        strategy_type: window.selectedTemplate.strategy_type,
        has_params_schema: !!window.selectedTemplate.parameters_schema
      };
    }
    return null;
  });

  console.log('点击后 selectedTemplate:', after);

  expect(after).toBeTruthy();
  expect(after.strategy_type).toBe('DHS');
});
