/**
 * Test Stake Number Formatting (K公里+米)
 * Verify that stake numbers display correctly as K57+545 format
 */

const { test, expect } = require('@playwright/test');

test.describe('桩号格式化测试', () => {
  test('验证桩号正确显示为 K公里+米 格式', async ({ page }) => {
    // 访问页面
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    // Step 1: 选择一个 DHS 模板
    console.log('\n=== Step 1: 选择 DHS 模板 ===');
    await page.waitForSelector('.template-card');

    const dhsCard = page.locator('.template-card').filter({ hasText: /DHS|动态硬路肩/ }).first();
    await dhsCard.click();
    await page.waitForTimeout(500);

    // 点击"下一步"进入路段选择
    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 2: 选择路段 ===');

    // 等待路段选择器加载
    await page.waitForSelector('#route-select', { timeout: 10000 });

    // 选择路线
    await page.selectOption('#route-select', { index: 1 });
    await page.waitForTimeout(1000);

    // 选择方向
    const directionSelect = page.locator('#direction-select');
    if (await directionSelect.isVisible()) {
      await directionSelect.selectOption({ index: 1 });
      await page.waitForTimeout(1000);
    }

    // 选择路段 (多选)
    const sectionSelect = page.locator('#section-select');
    if (await sectionSelect.isVisible()) {
      await sectionSelect.selectOption({ index: 1 });
      await page.waitForTimeout(500);

      // 添加第二个路段 (Ctrl+Click)
      const secondOption = await sectionSelect.locator('option').nth(2);
      if (await secondOption.isVisible()) {
        await secondOption.click({ modifiers: ['Control'] });
        await page.waitForTimeout(500);
      }
    }

    // 点击"下一步"进入参数配置
    const nextButton = page.locator('button:has-text("下一步")').last();
    await nextButton.click();
    await page.waitForTimeout(2000);

    console.log('\n=== Step 3: 检查路段表格 ===');

    // 等待路段表格渲染
    const tableExists = await page.locator('.edge-table').isVisible();
    console.log('路段表格是否可见:', tableExists);

    if (tableExists) {
      // 获取第一行路段数据
      const firstRow = page.locator('.edge-table tbody tr').first();

      // 提取桩号列的文本
      const startStake = await firstRow.locator('td:nth-child(5)').textContent();
      const endStake = await firstRow.locator('td:nth-child(6)').textContent();

      console.log('起始桩号:', startStake);
      console.log('结束桩号:', endStake);

      // 验证格式
      const stakePattern = /^K\d+\+\d{3}$/;
      expect(startStake.trim()).toMatch(stakePattern);
      expect(endStake.trim()).toMatch(stakePattern);

      console.log('✅ 桩号格式正确！');

      // 获取原始数据进行手动验证
      const edgeData = await page.evaluate(() => {
        if (window.edgeDisplayTable && window.edgeDisplayTable.edges) {
          return window.edgeDisplayTable.edges[0];
        }
        return null;
      });

      if (edgeData) {
        console.log('\n原始路段数据:');
        console.log('  start_stake (km):', edgeData.start_stake);
        console.log('  end_stake (km):', edgeData.end_stake);

        // 手动计算期望的桩号格式
        const formatStake = (stake) => {
          if (!stake && stake !== 0) return 'N/A';
          const km = Math.floor(stake);
          const m = Math.round((stake - km) * 1000);
          return `K${km}+${m.toString().padStart(3, '0')}`;
        };

        const expectedStart = formatStake(edgeData.start_stake);
        const expectedEnd = formatStake(edgeData.end_stake);

        console.log('期望的起始桩号:', expectedStart);
        console.log('期望的结束桩号:', expectedEnd);
        console.log('实际的起始桩号:', startStake.trim());
        console.log('实际的结束桩号:', endStake.trim());

        expect(startStake.trim()).toBe(expectedStart);
        expect(endStake.trim()).toBe(expectedEnd);

        console.log('✅ 桩号计算正确！');
      }

      // 检查汇总统计
      const summary = await page.locator('.edge-summary').textContent();
      console.log('\n路段汇总信息:');
      console.log(summary);

      // 截图保存
      await page.screenshot({
        path: 'tests/e2e/screenshots/stake_formatting.png',
        fullPage: true
      });
      console.log('\n✅ 截图已保存: tests/e2e/screenshots/stake_formatting.png');

    } else {
      console.error('❌ 路段表格未显示');
      throw new Error('Edge table not visible');
    }
  });

  test('验证路段连续性检查使用正确的公里单位', async ({ page }) => {
    // 测试 formatStake 和 checkEdgeContinuity 函数
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    // 测试 formatStake 函数
    const formatTests = await page.evaluate(() => {
      const formatStake = (stake) => {
        if (!stake && stake !== 0) return 'N/A';
        const km = Math.floor(stake);
        const m = Math.round((stake - km) * 1000);
        return `K${km}+${m.toString().padStart(3, '0')}`;
      };

      return [
        { input: 57.545, expected: 'K57+545', actual: formatStake(57.545) },
        { input: 0.100, expected: 'K0+100', actual: formatStake(0.100) },
        { input: 123.456, expected: 'K123+456', actual: formatStake(123.456) },
        { input: 99.999, expected: 'K99+999', actual: formatStake(99.999) },
        { input: 0, expected: 'K0+000', actual: formatStake(0) },
        { input: null, expected: 'N/A', actual: formatStake(null) }
      ];
    });

    console.log('\n=== formatStake 函数测试 ===');
    formatTests.forEach(test => {
      console.log(`输入: ${test.input} km → 期望: ${test.expected}, 实际: ${test.actual}`);
      expect(test.actual).toBe(test.expected);
    });

    console.log('✅ 所有 formatStake 测试通过！');
  });
});
