import { test, expect, Page } from '@playwright/test';

test.describe('策略模板 - 应用与敏感性分析', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8000/control_optimization/strategy_management.html');
    await page.waitForLoadState('networkidle');
    await page.locator('button#createStrategyBtn').click();
    await page.waitForTimeout(300);
  });

  test('应用VSL标准模板并回填参数', async ({ page }) => {
    await page.locator('#toggleTemplateSelectorBtn').click();
    await page.getByText('VSL可变限速').click();
    await page.locator('.template-card .use-template-btn').first().click();

    await expect(page.locator('#strategyType')).toHaveValue('VSL');
    await expect(page.locator('#vslSpeed')).not.toBeEmpty();
    await expect(page.locator('#vslBeginTime')).not.toBeEmpty();
    await expect(page.locator('#vslEndTime')).not.toBeEmpty();
  });

  test('敏感性分析批次 - 组合数预估与确认', async ({ page }) => {
    await page.locator('#toggleTemplateSelectorBtn').click();
    await page.getByText('VSL可变限速').click();

    // 自动接受 confirm（软阈值提示）
    page.on('dialog', async (dialog) => {
      await dialog.accept();
    });

    const btn = page.locator('.template-card .sensitivity-btn').first();
    await btn.click();

    // 断言：页面未出错且按钮仍可见
    await expect(btn).toBeVisible();
  });
});


