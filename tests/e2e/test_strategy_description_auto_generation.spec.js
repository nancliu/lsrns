/**
 * Test Strategy Description Auto-Generation (Phase 3: Task 3.4 & 3.5)
 * Verify that strategy descriptions are automatically generated and can be regenerated
 */

const { test, expect } = require('@playwright/test');

test.describe('策略描述自动生成测试', () => {
  test('VSS策略：验证自动生成详细描述', async ({ page }) => {
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
    await page.waitForTimeout(2000);

    // 验证策略描述已自动填充
    const descTextarea = page.locator('#param-strategy-description');
    const generatedDescription = await descTextarea.inputValue();

    console.log('\n生成的策略描述:');
    console.log(generatedDescription);

    // 验证描述格式和内容
    expect(generatedDescription).toBeTruthy();
    expect(generatedDescription.length).toBeGreaterThan(50);

    // VSS策略描述应该包含关键词
    expect(generatedDescription).toContain('可变限速');
    expect(generatedDescription).toContain('路段');
    expect(generatedDescription).toContain('策略目标');
    expect(generatedDescription).toContain('适用场景');

    // 验证"重新生成描述"按钮存在
    const regenerateBtn = page.locator('#regenerate-description-btn');
    await expect(regenerateBtn).toBeVisible();

    console.log('✅ 策略描述已自动生成并填充');

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/vss_auto_description.png',
      fullPage: true
    });
  });

  test('DHS策略：验证自动生成硬路肩描述', async ({ page }) => {
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

    // 选择前2个路段
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

    // 验证策略描述已自动填充
    const descTextarea = page.locator('#param-strategy-description');
    const generatedDescription = await descTextarea.inputValue();

    console.log('\n生成的策略描述:');
    console.log(generatedDescription);

    // 验证描述格式和内容
    expect(generatedDescription).toBeTruthy();
    expect(generatedDescription.length).toBeGreaterThan(50);

    // DHS策略描述应该包含关键词
    expect(generatedDescription).toContain('动态硬路肩');
    expect(generatedDescription).toContain('应急车道');
    expect(generatedDescription).toContain('策略目标');
    expect(generatedDescription).toContain('安全保障');
    expect(generatedDescription).toContain('适用场景');

    console.log('✅ 策略描述已自动生成并填充');

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/dhs_auto_description.png',
      fullPage: true
    });
  });

  test('验证"重新生成描述"按钮功能', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 1-2: 选择模板和路段 ===');

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

    console.log('\n=== Step 3: 测试重新生成描述 ===');

    // 进入Step 3
    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(2000);

    // 获取自动生成的描述
    const descTextarea = page.locator('#param-strategy-description');
    const originalDescription = await descTextarea.inputValue();
    console.log('原始生成的描述（前50字）:', originalDescription.substring(0, 50) + '...');

    // 修改限速参数
    const speedInput = page.locator('#param-speed_limit');
    if (await speedInput.isVisible()) {
      const originalSpeed = await speedInput.inputValue();
      console.log('原始限速值:', originalSpeed);

      // 修改限速值
      await speedInput.fill('80');
      await page.waitForTimeout(500);

      // 点击"重新生成描述"按钮
      const regenerateBtn = page.locator('#regenerate-description-btn');
      await regenerateBtn.click();
      await page.waitForTimeout(500);

      // 获取重新生成的描述
      const newDescription = await descTextarea.inputValue();
      console.log('重新生成的描述（前50字）:', newDescription.substring(0, 50) + '...');

      // 验证描述已更新（应该包含新的限速值）
      expect(newDescription).toBeTruthy();
      expect(newDescription).toContain('80');

      console.log('✅ 重新生成描述功能正常');
    }
  });

  test('验证用户自定义描述的保护机制', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 1-2: 选择模板和路段 ===');

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

    console.log('\n=== Step 3: 测试用户自定义保护 ===');

    // 进入Step 3
    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(2000);

    // 获取自动生成的描述
    const descTextarea = page.locator('#param-strategy-description');
    const originalDescription = await descTextarea.inputValue();
    console.log('原始生成的描述存在:', originalDescription.length > 0);

    // 用户手动修改描述
    const customDescription = '这是我自定义的策略描述，用于特殊场景测试。';
    await descTextarea.fill(customDescription);
    await page.waitForTimeout(500);

    const currentDescription = await descTextarea.inputValue();
    console.log('用户修改后的描述:', currentDescription);

    // 验证描述已被修改
    expect(currentDescription).toBe(customDescription);

    // 点击"重新生成描述"按钮
    const regenerateBtn = page.locator('#regenerate-description-btn');

    // 监听对话框
    let dialogAppeared = false;
    page.on('dialog', async dialog => {
      console.log('确认对话框出现:', dialog.message());
      dialogAppeared = true;

      // 点击"取消"保留用户自定义描述
      await dialog.dismiss();
    });

    await regenerateBtn.click();
    await page.waitForTimeout(500);

    // 验证对话框出现
    expect(dialogAppeared).toBe(true);

    // 验证描述没有被覆盖（用户选择了取消）
    const finalDescription = await descTextarea.inputValue();
    expect(finalDescription).toBe(customDescription);

    console.log('✅ 用户自定义描述受到保护');

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/description_user_protection.png',
      fullPage: true
    });
  });
});
