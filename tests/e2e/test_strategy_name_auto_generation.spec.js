/**
 * Test Strategy Name Auto-Generation (Phase 3: Task 3.1)
 * Verify that strategy names are automatically generated and populated in Step 3
 */

const { test, expect } = require('@playwright/test');

test.describe('策略名称自动生成测试', () => {
  test('VSS策略：验证自动生成限速策略名称', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 1: 选择VSS模板 ===');

    // 选择VSS模板（可变限速）
    const vssCard = page.locator('.template-card').filter({ hasText: /VSS|可变限速/ }).first();
    await vssCard.click();
    await page.waitForTimeout(500);

    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 2: 查询和选择路段 ===');

    // 选择路线
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202'); // 选择G4202
    await page.waitForTimeout(500);

    // 点击查询路段
    await page.click('button:has-text("查询路段")');
    await page.waitForTimeout(2000);

    // 等待查询结果
    const resultsTable = page.locator('#results-table');
    const isVisible = await resultsTable.isVisible();
    if (!isVisible) {
      console.warn('⚠️  查询结果表未显示，跳过测试');
      test.skip();
    }

    // 选择前3个路段
    const checkboxes = page.locator('#results-tbody input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    console.log(`找到 ${checkboxCount} 个路段`);

    if (checkboxCount === 0) {
      console.warn('⚠️  没有找到路段，跳过测试');
      test.skip();
    }

    const selectCount = Math.min(3, checkboxCount);
    for (let i = 0; i < selectCount; i++) {
      await checkboxes.nth(i).check();
      await page.waitForTimeout(100);
    }

    console.log(`选择了 ${selectCount} 个路段`);

    // 确认选择
    await page.click('button:has-text("确认选择")');
    await page.waitForTimeout(500);

    console.log('\n=== Step 3: 进入参数配置页面 ===');

    // 进入Step 3
    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(2000); // 等待边表格加载和名称生成

    // 验证策略名称已自动填充
    const nameInput = page.locator('#param-strategy-name');
    const generatedName = await nameInput.inputValue();

    console.log('\n生成的策略名称:', generatedName);

    // 验证名称格式：应该包含路线、路段、限速信息
    expect(generatedName).toBeTruthy();
    expect(generatedName.length).toBeGreaterThan(0);

    // VSS策略名称格式：{Route} {Section} 限速{Speed}km/h ({Time})
    // 示例：G4202 K40-K45 限速60km/h (早高峰)
    expect(generatedName).toContain('限速');
    expect(generatedName).toContain('km/h');

    console.log('✅ 策略名称已自动生成并填充');

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/vss_auto_name.png',
      fullPage: true
    });
  });

  test('DHS策略：验证自动生成硬路肩策略名称', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 1: 选择DHS模板 ===');

    // 选择DHS模板（动态硬路肩）
    const dhsCard = page.locator('.template-card').filter({ hasText: /DHS|动态硬路肩/ }).first();
    await dhsCard.click();
    await page.waitForTimeout(500);

    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 2: 查询和选择路段 ===');

    // 选择路线
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.waitForTimeout(500);

    // 点击查询路段
    await page.click('button:has-text("查询路段")');
    await page.waitForTimeout(2000);

    // 等待查询结果
    const resultsTable = page.locator('#results-table');
    const isVisible = await resultsTable.isVisible();
    if (!isVisible) {
      console.warn('⚠️  查询结果表未显示，跳过测试');
      test.skip();
    }

    // 选择前2个路段（DHS至少需要2个连续路段）
    const checkboxes = page.locator('#results-tbody input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    console.log(`找到 ${checkboxCount} 个路段`);

    if (checkboxCount === 0) {
      console.warn('⚠️  没有找到路段，跳过测试');
      test.skip();
    }

    const selectCount = Math.min(2, checkboxCount);
    for (let i = 0; i < selectCount; i++) {
      await checkboxes.nth(i).check();
      await page.waitForTimeout(100);
    }

    console.log(`选择了 ${selectCount} 个路段`);

    // 确认选择
    await page.click('button:has-text("确认选择")');
    await page.waitForTimeout(500);

    console.log('\n=== Step 3: 进入参数配置页面 ===');

    // 进入Step 3
    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(2000);

    // 验证策略名称已自动填充
    const nameInput = page.locator('#param-strategy-name');
    const generatedName = await nameInput.inputValue();

    console.log('\n生成的策略名称:', generatedName);

    // 验证名称格式
    expect(generatedName).toBeTruthy();
    expect(generatedName.length).toBeGreaterThan(0);

    // DHS策略名称格式：{Route} {Section} 应急车道开放 ({Time})
    expect(generatedName).toContain('应急车道开放');

    console.log('✅ 策略名称已自动生成并填充');

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/dhs_auto_name.png',
      fullPage: true
    });
  });

  test('验证参数变化时名称不自动更新（保护用户输入）', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    // 选择VSS模板
    const vssCard = page.locator('.template-card').filter({ hasText: /VSS|可变限速/ }).first();
    await vssCard.click();
    await page.waitForTimeout(500);

    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(1000);

    // 选择路线并查询
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.waitForTimeout(500);

    await page.click('button:has-text("查询路段")');
    await page.waitForTimeout(2000);

    // 等待查询结果
    const resultsTable = page.locator('#results-table');
    const isVisible = await resultsTable.isVisible();
    if (!isVisible) {
      console.warn('⚠️  查询结果表未显示，跳过测试');
      test.skip();
    }

    const checkboxes = page.locator('#results-tbody input[type="checkbox"]');
    await checkboxes.first().check();
    await page.waitForTimeout(100);

    await page.click('button:has-text("确认选择")');
    await page.waitForTimeout(500);

    // 进入Step 3
    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(2000);

    // 获取自动生成的名称
    const nameInput = page.locator('#param-strategy-name');
    const originalName = await nameInput.inputValue();
    console.log('原始生成的名称:', originalName);

    // 用户手动修改名称
    const customName = '我的自定义策略名称';
    await nameInput.fill(customName);
    await page.waitForTimeout(200);

    const currentName = await nameInput.inputValue();
    console.log('用户修改后的名称:', currentName);

    // 验证名称已被修改
    expect(currentName).toBe(customName);
    expect(currentName).not.toBe(originalName);

    // 修改其他参数（例如限速值）
    const speedInput = page.locator('#param-speed_limit');
    if (await speedInput.isVisible()) {
      await speedInput.fill('80');
      await page.waitForTimeout(500);
    }

    // 验证名称没有自动更新（保护用户输入）
    const finalName = await nameInput.inputValue();
    expect(finalName).toBe(customName);

    console.log('✅ 用户修改的名称没有被覆盖，符合预期');
  });
});
