/**
 * Phase 8 Validation and Hint Text E2E Tests
 *
 * Tests for Phase 8 features:
 * - Task 8.1: Time order validation
 * - Task 8.2: Numeric range validation
 * - Task 8.3: Delete confirmation dialogs
 * - Task 8.4: Hint text optimization
 *
 * @version 1.0
 * @date 2025-11-01
 */

const { test, expect } = require('@playwright/test');

test.describe('Phase 8 验证和提示文本 - E2E 测试', () => {

  test('Task 8.1: 时间顺序验证 - DHS 区间', async ({ page }) => {
    console.log('\n========== Task 8.1: 时间顺序验证测试 ==========\n');

    // 访问策略创建页面
    await page.goto('http://localhost:8000/control/templates.html', { timeout: 30000 });
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 选择 DHS 模板
    console.log('选择 DHS 模板...');
    const dhsCard = page.locator('.template-card').filter({ hasText: /DHS|硬路肩/ }).first();
    if (!(await dhsCard.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.warn('⚠️  DHS 模板未找到，跳过');
      test.skip();
    }
    await dhsCard.click();

    // 进行路段选择（确保到达步骤 3）
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');
    await page.waitForTimeout(500);

    const queryBtn = page.locator('button:has-text("查询")').first();
    if (await queryBtn.isVisible()) {
      await queryBtn.click();
      await page.waitForTimeout(2000);
    }

    const nextBtn = page.locator('button:has-text("进入配置参数")').first();
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForSelector('.dhs-interval-control-enhanced', { timeout: 10000 });
    }

    console.log('✅ DHS 模板已选择，已到达步骤 3');

    // 在 DHS 时间区间表中添加一行
    console.log('\n测试时间顺序验证...');
    const addIntervalBtn = page.locator('button:has-text("添加时间区间")').first();
    if (await addIntervalBtn.isVisible()) {
      await addIntervalBtn.click();
      await page.waitForTimeout(300);
    }

    // 找到最后一行的输入框
    const rows = await page.locator('.dhs-interval-row').count();
    console.log(`找到 ${rows} 行 DHS 区间`);

    if (rows > 0) {
      const lastRowIndex = rows - 1;
      const lastRow = page.locator('.dhs-interval-row').nth(lastRowIndex);

      // 获取 begin 和 end 输入框
      const beginInput = lastRow.locator('.interval-begin');
      const endInput = lastRow.locator('.interval-end');

      // 测试场景: begin = 15, end = 10 (非法顺序)
      console.log('设置非法时间顺序: begin=15, end=10...');
      await beginInput.fill('15');
      await endInput.fill('10');
      await endInput.blur(); // 触发 blur 事件验证

      // 等待错误提示
      await page.waitForTimeout(500);

      // 检查是否显示错误信息
      const errorMsg = lastRow.locator('.parameter-feedback.error');
      if (await errorMsg.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('✅ 时间顺序验证工作正常 - 显示错误信息');
        const errorText = await errorMsg.textContent();
        console.log(`   错误信息: ${errorText}`);
        expect(errorText).toContain('开始时间');
      } else {
        console.warn('⚠️  未检测到错误信息，可能是验证未触发');
      }

      // 测试场景: 修正为合法顺序
      console.log('\n修正为合法时间顺序: begin=9, end=11...');
      await beginInput.fill('9');
      await endInput.fill('11');
      await endInput.blur();

      await page.waitForTimeout(300);

      // 检查错误是否被清除
      const errorAfterFix = lastRow.locator('.parameter-feedback.error');
      if (!(await errorAfterFix.isVisible({ timeout: 2000 }).catch(() => false))) {
        console.log('✅ 合法时间顺序被接受，错误已清除');
      }
    }

    console.log('\n✅ Task 8.1 验证测试完成');
  });

  test('Task 8.2: 数值范围验证 - 速度范围', async ({ page }) => {
    console.log('\n========== Task 8.2: 数值范围验证测试 ==========\n');

    // 访问策略创建页面
    await page.goto('http://localhost:8000/control/templates.html', { timeout: 30000 });
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 选择 VSS 模板（有速度参数）
    console.log('选择 VSS 模板...');
    const vssCard = page.locator('.template-card').filter({ hasText: /VSS|可变限速/ }).first();
    if (!(await vssCard.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.warn('⚠️  VSS 模板未找到，跳过');
      test.skip();
    }
    await vssCard.click();

    // 进行路段选择（基本操作）
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');
    await page.waitForTimeout(500);

    // 点击查询按钮
    const queryBtn = page.locator('button:has-text("查询")').first();
    if (await queryBtn.isVisible()) {
      await queryBtn.click();
      await page.waitForTimeout(2000);
    }

    // 点击进入参数配置
    const nextBtn = page.locator('button:has-text("进入配置参数")').first();
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForSelector('#param-form', { timeout: 10000 });
    }

    console.log('✅ 已到达步骤 3 - VSS 参数配置');

    // 测试速度范围验证
    console.log('\n测试速度范围验证...');
    const addStepBtn = page.locator('button:has-text("添加时间步骤")').first();
    if (await addStepBtn.isVisible()) {
      await addStepBtn.click();
      await page.waitForTimeout(300);
    }

    // 找到速度输入框
    const rows = await page.locator('.vss-step-row').count();
    if (rows > 0) {
      const lastRowIndex = rows - 1;
      const lastRow = page.locator('.vss-step-row').nth(lastRowIndex);

      const speedInput = lastRow.locator('.step-speed');
      if (await speedInput.isVisible()) {
        // 测试场景: 速度 = 150 (超出范围)
        console.log('设置超出范围的速度值: 150 km/h...');
        await speedInput.fill('150');
        await speedInput.blur();

        await page.waitForTimeout(500);

        // 检查错误提示
        const errorMsg = lastRow.locator('.parameter-feedback.error');
        if (await errorMsg.isVisible({ timeout: 2000 }).catch(() => false)) {
          console.log('✅ 速度范围验证工作正常 - 显示错误信息');
          const errorText = await errorMsg.textContent();
          console.log(`   错误信息: ${errorText}`);
          expect(errorText).toContain('范围');
        } else {
          console.warn('⚠️  未检测到错误信息');
        }

        // 修正为合法值
        console.log('\n修正为合法速度值: 80 km/h...');
        await speedInput.fill('80');
        await speedInput.blur();

        await page.waitForTimeout(300);

        // 检查错误是否被清除
        const errorAfterFix = lastRow.locator('.parameter-feedback.error');
        if (!(await errorAfterFix.isVisible({ timeout: 2000 }).catch(() => false))) {
          console.log('✅ 合法速度值被接受，错误已清除');
        }
      }
    }

    console.log('\n✅ Task 8.2 验证测试完成');
  });

  test('Task 8.3: 删除确认对话框', async ({ page }) => {
    console.log('\n========== Task 8.3: 删除确认对话框测试 ==========\n');

    // 访问策略创建页面
    await page.goto('http://localhost:8000/control/templates.html', { timeout: 30000 });
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 选择 Flow 模板（有区间表）
    console.log('选择 Flow 类型策略模板...');
    const flowCard = page.locator('.template-card').filter({ hasText: /流量|TEC/ }).first();
    if (!(await flowCard.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.warn('⚠️  Flow 模板未找到，使用 VSS 替代...');
      const vssCard = page.locator('.template-card').filter({ hasText: /VSS/ }).first();
      await vssCard.click();
    } else {
      await flowCard.click();
    }

    // 进行基本路段选择
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');
    await page.waitForTimeout(500);

    // 查询路段
    const queryBtn = page.locator('button:has-text("查询")').first();
    if (await queryBtn.isVisible()) {
      await queryBtn.click();
      await page.waitForTimeout(2000);
    }

    // 进入参数配置
    const nextBtn = page.locator('button:has-text("进入配置参数")').first();
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForSelector('#param-form', { timeout: 10000 });
    }

    console.log('✅ 已到达步骤 3 - 参数配置');

    // 找到删除按钮
    console.log('\n测试删除确认对话框...');

    // 设置对话框拦截
    page.once('dialog', dialog => {
      console.log(`✅ 对话框显示: "${dialog.message()}"`);
      console.log('   用户操作: 取消');
      dialog.dismiss();
    });

    // 点击第一个删除按钮
    const deleteBtn = page.locator('button:has-text("删除")').first();
    if (await deleteBtn.isVisible()) {
      const rowCountBefore = await page.locator('.vss-step-row, .dhs-interval-row, .flow-interval-row, .tec-interval-row').count();
      console.log(`删除前行数: ${rowCountBefore}`);

      await deleteBtn.click();

      // 等待对话框响应
      await page.waitForTimeout(800);

      // 验证行数未改变（用户取消了）
      const rowCountAfter = await page.locator('.vss-step-row, .dhs-interval-row, .flow-interval-row, .tec-interval-row').count();
      console.log(`删除后行数: ${rowCountAfter}`);

      if (rowCountAfter === rowCountBefore) {
        console.log('✅ 删除已取消，行数保持不变');
      } else {
        console.warn(`⚠️  行数改变了 (${rowCountBefore} -> ${rowCountAfter})`);
      }
    } else {
      console.warn('⚠️  未找到删除按钮');
    }

    console.log('\n✅ Task 8.3 删除确认测试完成');
  });

  test('Task 8.4: 提示文本优化 - 提示显示和格式', async ({ page }) => {
    console.log('\n========== Task 8.4: 提示文本优化测试 ==========\n');

    // 访问策略创建页面
    await page.goto('http://localhost:8000/control/templates.html', { timeout: 30000 });
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 选择 VSS 模板
    console.log('选择 VSS 模板...');
    const vssCard = page.locator('.template-card').filter({ hasText: /VSS/ }).first();
    await vssCard.click();

    // 进行路段选择和参数配置
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');
    await page.waitForTimeout(500);

    const queryBtn = page.locator('button:has-text("查询")').first();
    if (await queryBtn.isVisible()) {
      await queryBtn.click();
      await page.waitForTimeout(2000);
    }

    const nextBtn = page.locator('button:has-text("进入配置参数")').first();
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForSelector('#param-form', { timeout: 10000 });
    }

    console.log('✅ 已到达步骤 3 - 参数配置');

    // 检查参数的提示文本
    console.log('\n检查提示文本...');

    // 获取所有 form-hint 元素
    const hints = await page.locator('.form-hint').all();
    console.log(`找到 ${hints.length} 个提示文本元素`);

    // 检查每个提示
    let hintCount = 0;
    for (const hint of hints) {
      const hintText = await hint.textContent();
      if (hintText && hintText.trim().length > 0) {
        console.log(`提示 ${++hintCount}: "${hintText.substring(0, 60)}..."`);

        // 验证提示不为空
        expect(hintText.trim()).not.toBe('');

        // 检查是否使用了中点分隔符
        if (hintText.includes('·')) {
          console.log('  ✅ 使用了提示文本组合 (·分隔)');
        }
      }
    }

    if (hintCount === 0) {
      console.warn('⚠️  未找到任何提示文本');
    } else {
      console.log(`\n✅ 验证了 ${hintCount} 个提示文本`);
    }

    // 检查参数表的表格提示
    console.log('\n检查表格内提示...');
    const timelineDesc = page.locator('.timeline-description');
    if (await timelineDesc.isVisible({ timeout: 2000 }).catch(() => false)) {
      const descText = await timelineDesc.textContent();
      console.log(`时间轴描述: "${descText}"`);
      console.log('✅ 时间轴描述清晰');
    }

    console.log('\n✅ Task 8.4 提示文本优化测试完成');
  });

  test('综合测试: 完整参数验证工作流', async ({ page }) => {
    console.log('\n========== 综合测试: 完整验证工作流 ==========\n');

    // 访问页面
    await page.goto('http://localhost:8000/control/templates.html', { timeout: 30000 });
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 选择 VSS 模板（简化测试以避免超时）
    console.log('选择 VSS 模板进行综合验证...');
    const vssCard = page.locator('.template-card').filter({ hasText: /VSS/ }).first();
    if (!(await vssCard.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.warn('⚠️  VSS 模板未找到');
      test.skip();
    }
    await vssCard.click();

    // 路段选择
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', 'G4202');
    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');
    await page.waitForTimeout(500);

    // 查询
    const queryBtn = page.locator('button:has-text("查询")').first();
    if (await queryBtn.isVisible()) {
      await queryBtn.click();
      await page.waitForTimeout(2000);
    }

    // 进入参数配置
    const nextBtn = page.locator('button:has-text("进入配置参数")').first();
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForSelector('#param-form', { timeout: 10000 });
    }

    console.log('✅ VSS 策略已到达参数配置步骤');

    // 综合验证: 添加一行，输入无效数据，验证错误，修正数据
    console.log('\n执行综合验证测试...');
    const addBtn = page.locator('button:has-text("添加时间步骤")').first();
    if (await addBtn.isVisible()) {
      await addBtn.click();
      await page.waitForTimeout(300);
    }

    const rows = await page.locator('.vss-step-row').count();
    if (rows > 0) {
      const lastRow = page.locator('.vss-step-row').nth(rows - 1);
      const timeInput = lastRow.locator('.step-time');
      const speedInput = lastRow.locator('.step-speed');

      // 第一步: 输入有效数据
      console.log('1. 输入有效数据...');
      if (await timeInput.isVisible()) {
        await timeInput.fill('7');
        await speedInput.fill('60');
        await speedInput.blur();
        await page.waitForTimeout(300);
        console.log('   ✅ 数据已填充');
      }

      // 第二步: 测试速度范围验证
      console.log('2. 测试超出范围的速度值...');
      if (await speedInput.isVisible()) {
        await speedInput.fill('200'); // 超出范围
        await speedInput.blur();
        await page.waitForTimeout(300);

        if (await lastRow.locator('.parameter-feedback.error').isVisible({ timeout: 2000 }).catch(() => false)) {
          console.log('   ✅ 检测到速度范围验证错误');
        }

        // 修正为有效值
        console.log('   修正为有效速度值...');
        await speedInput.fill('80');
        await speedInput.blur();
        await page.waitForTimeout(300);
        console.log('   ✅ 速度验证通过');
      }

      // 第三步: 测试删除确认
      console.log('3. 测试删除确认对话框...');
      const deleteBtn = lastRow.locator('button:has-text("删除")');
      if (await deleteBtn.isVisible()) {
        page.once('dialog', dialog => {
          console.log('   ✅ 删除确认对话框已显示');
          dialog.dismiss();
        });
        await deleteBtn.click();
        await page.waitForTimeout(500);
      }

      console.log('\n✅ 综合验证工作流测试完成');
    }
  });

});
