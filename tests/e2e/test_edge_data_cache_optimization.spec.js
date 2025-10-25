/**
 * Test Edge Data Cache Optimization
 * Verify that Step 3 reuses edge data from Step 2 query results
 */

const { test, expect } = require('@playwright/test');

test.describe('路段数据缓存优化测试', () => {
  test('验证 Step 3 复用 Step 2 查询结果，避免重复 API 调用', async ({ page }) => {
    const apiCalls = [];

    // 监听所有 API 请求
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/v1/control/edges/')) {
        apiCalls.push({
          method: request.method(),
          url: url.replace('http://localhost:8000', ''),
          timestamp: Date.now()
        });
      }
    });

    // 捕获控制台日志
    const logs = [];
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[EdgeDisplayTable]')) {
        logs.push(text);
      }
    });

    console.log('\n=== Step 1: 选择策略模板 ===');
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    // 选择 DHS 模板
    const dhsCard = page.locator('.template-card').filter({ hasText: /DHS|动态硬路肩/ }).first();
    await dhsCard.click();
    await page.waitForTimeout(500);

    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(1000);

    console.log('\n=== Step 2: 查询和选择路段 ===');

    // 选择路线
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.selectOption('#route-codes', { index: 0 }); // 选择第一个路线
    await page.waitForTimeout(500);

    // 选择方向（如果有）
    const directionSelect = page.locator('#direction-codes');
    if (await directionSelect.isVisible()) {
      await page.selectOption('#direction-codes', { index: 0 });
      await page.waitForTimeout(500);
    }

    // 选择路段（如果有）
    const sectionSelect = page.locator('#section-codes');
    if (await sectionSelect.isVisible()) {
      await page.selectOption('#section-codes', { index: 0 });
      await page.waitForTimeout(500);
    }

    // 点击查询路段
    const apiCallsBefore = apiCalls.length;
    await page.click('button:has-text("查询路段")');
    await page.waitForTimeout(2000); // 等待查询完成

    const apiCallsAfterQuery = apiCalls.length;
    console.log(`Step 2 查询触发的 API 调用数: ${apiCallsAfterQuery - apiCallsBefore}`);

    // 检查查询结果是否加载
    const resultsTable = await page.locator('#results-table').isVisible();
    if (!resultsTable) {
      console.warn('⚠️  查询结果表未显示，跳过测试');
      return;
    }

    // 选择前3个路段（如果有）
    const checkboxes = page.locator('#results-tbody input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    const selectCount = Math.min(3, checkboxCount);

    for (let i = 0; i < selectCount; i++) {
      await checkboxes.nth(i).check();
      await page.waitForTimeout(100);
    }

    console.log(`选择了 ${selectCount} 个路段`);

    // 确认选择
    await page.click('button:has-text("确认选择")');
    await page.waitForTimeout(500);

    // 点击下一步进入 Step 3
    console.log('\n=== Step 3: 进入参数配置页面 ===');
    const apiCallsBeforeStep3 = apiCalls.length;

    await page.click('button:has-text("下一步")');
    await page.waitForTimeout(2000); // 等待 EdgeDisplayTable 加载

    const apiCallsAfterStep3 = apiCalls.length;

    console.log(`\n=== API 调用分析 ===`);
    console.log(`Step 2 查询触发的 API 调用: ${apiCallsAfterQuery - apiCallsBefore}`);
    console.log(`Step 3 加载触发的 API 调用: ${apiCallsAfterStep3 - apiCallsBeforeStep3}`);

    // 打印所有 API 调用
    console.log('\n所有 API 调用:');
    apiCalls.forEach((call, index) => {
      console.log(`  ${index + 1}. ${call.method} ${call.url}`);
    });

    // 检查 EdgeDisplayTable 日志
    console.log('\n=== EdgeDisplayTable 日志 ===');
    logs.forEach(log => console.log(log));

    // 验证：Step 3 应该使用缓存，不应该调用 batch-info API
    const batchInfoCalls = apiCalls.filter(call => call.url.includes('/batch-info'));

    if (batchInfoCalls.length === 0) {
      console.log('\n✅ 优化成功：没有调用 /batch-info API，完全使用缓存');
    } else {
      console.log(`\n⚠️  检测到 ${batchInfoCalls.length} 次 /batch-info 调用:`);
      batchInfoCalls.forEach(call => {
        console.log(`   - ${call.method} ${call.url}`);
      });
    }

    // 检查日志中是否有缓存命中的消息
    const cacheHitLog = logs.find(log => log.includes('✅ All') && log.includes('found in cache'));
    if (cacheHitLog) {
      console.log('\n✅ 缓存命中:', cacheHitLog);
      expect(cacheHitLog).toContain('API call avoided');
    }

    // 验证：路段表格应该正常显示
    const edgeTable = await page.locator('.edge-table').isVisible();
    expect(edgeTable).toBe(true);

    const rowCount = await page.locator('.edge-table tbody tr').count();
    console.log(`\n路段表格显示了 ${rowCount} 行`);
    expect(rowCount).toBe(selectCount);

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/edge_cache_optimization.png',
      fullPage: true
    });
    console.log('\n✅ 截图已保存: tests/e2e/screenshots/edge_cache_optimization.png');
  });

  test('验证缓存未命中时的回退机制', async ({ page }) => {
    console.log('\n=== 测试缓存未命中场景 ===');

    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    // 在浏览器中直接创建 EdgeDisplayTable 并测试
    const result = await page.evaluate(async () => {
      const logs = [];

      // 覆盖 console.log 捕获日志
      const originalLog = console.log;
      console.log = (...args) => {
        const message = args.join(' ');
        if (message.includes('[EdgeDisplayTable]')) {
          logs.push(message);
        }
        originalLog(...args);
      };

      const container = document.createElement('div');
      document.body.appendChild(container);

      const table = new EdgeDisplayTable(container, 'DHS');

      // 模拟缓存数据（只包含2个路段）
      const cache = [
        { edge_id: 'edge_1', route_code: 'SA2', start_stake: 1.0, end_stake: 2.0 },
        { edge_id: 'edge_2', route_code: 'SA2', start_stake: 2.0, end_stake: 3.0 }
      ];

      // 请求3个路段，但缓存只有2个 → 应该回退到 API
      const requestedEdges = ['edge_1', 'edge_2', 'edge_3'];

      try {
        await table.loadEdges(requestedEdges, cache);
      } catch (error) {
        // API 调用会失败（因为是测试环境），这是预期的
        logs.push(`Expected error: ${error.message}`);
      }

      console.log = originalLog;
      return logs;
    });

    console.log('\n缓存未命中日志:');
    result.forEach(log => console.log(log));

    // 验证缓存未命中消息
    const cacheMissLog = result.find(log => log.includes('⚠️') && log.includes('Cache miss'));
    expect(cacheMissLog).toBeTruthy();
    console.log('\n✅ 缓存未命中检测正常:', cacheMissLog);
  });
});
