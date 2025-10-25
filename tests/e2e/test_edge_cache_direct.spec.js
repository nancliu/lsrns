/**
 * Direct Test for Edge Data Cache
 * Directly test cache hit scenario without going through full workflow
 */

const { test, expect } = require('@playwright/test');

test.describe('路段数据缓存直接测试', () => {
  test('直接测试缓存命中场景', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== 测试缓存命中场景 ===');

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

      // 创建容器
      const container = document.createElement('div');
      container.id = 'test-container';
      document.body.appendChild(container);

      // 创建 EdgeDisplayTable
      const table = new EdgeDisplayTable(container, 'DHS');

      // 模拟完整的缓存数据（Step 2 查询结果，使用 Step 2 字段名）
      const cache = [
        {
          edge_id: 'test_edge_1',
          route_code: 'SA2',
          section_code: 'SA2-1',
          start_stake: 57.545,
          end_stake: 58.123,
          length: 578,              // Step 2 字段名
          num_lanes: 4,             // Step 2 字段名
          route_direction: 'upstream', // Step 2 字段名
          node_type: 'gantry',
          gantry_count: 2
        },
        {
          edge_id: 'test_edge_2',
          route_code: 'SA2',
          section_code: 'SA2-2',
          start_stake: 58.123,
          end_stake: 59.789,
          length: 1666,
          num_lanes: 5,
          route_direction: 'upstream',
          node_type: 'gantry',
          gantry_count: 3
        },
        {
          edge_id: 'test_edge_3',
          route_code: 'SA2',
          section_code: 'SA2-3',
          start_stake: 0.100,
          end_stake: 0.500,
          length: 400,
          num_lanes: 4,
          route_direction: 'upstream',
          node_type: 'gantry',
          gantry_count: 1
        }
      ];

      // 请求所有3个路段 → 应该全部命中缓存
      const requestedEdges = ['test_edge_1', 'test_edge_2', 'test_edge_3'];

      await table.loadEdges(requestedEdges, cache);

      console.log = originalLog;

      return {
        logs,
        edgeCount: table.edges.length,
        tableHTML: container.innerHTML
      };
    });

    console.log('\n=== EdgeDisplayTable 日志 ===');
    result.logs.forEach(log => console.log(log));

    // 验证缓存命中
    const cacheHitLog = result.logs.find(log => log.includes('✅') && log.includes('found in cache'));
    expect(cacheHitLog).toBeTruthy();
    expect(cacheHitLog).toContain('API call avoided');
    console.log('\n✅ 缓存完全命中:', cacheHitLog);

    // 验证路段数据正确加载
    expect(result.edgeCount).toBe(3);
    console.log(`✅ 路段数据已加载: ${result.edgeCount} 个路段`);

    // 验证表格渲染
    expect(result.tableHTML).toContain('edge-table');
    expect(result.tableHTML).toContain('K57+545'); // 验证桩号格式正确
    expect(result.tableHTML).toContain('K58+123');
    expect(result.tableHTML).toContain('K0+100');
    expect(result.tableHTML).toContain('上行'); // 验证方向翻译
    expect(result.tableHTML).toContain('578.0'); // 验证长度显示
    console.log('✅ 路段表格渲染正确，桩号格式、方向翻译、数据显示正确');

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/edge_cache_direct_test.png',
      fullPage: true
    });
    console.log('\n✅ 截图已保存: tests/e2e/screenshots/edge_cache_direct_test.png');
  });

  test('测试部分缓存命中场景', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== 测试部分缓存命中场景 ===');

    const result = await page.evaluate(async () => {
      const logs = [];

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

      const table = new EdgeDisplayTable(container, 'VSS');

      // 缓存只包含部分路段（使用 Step 2 字段名）
      const cache = [
        { edge_id: 'edge_A', route_code: 'G4202', start_stake: 10.0, end_stake: 11.0, num_lanes: 3 },
        { edge_id: 'edge_B', route_code: 'G4202', start_stake: 11.0, end_stake: 12.0, num_lanes: 3 }
        // edge_C 不在缓存中
      ];

      // 请求3个路段，但缓存只有2个
      const requestedEdges = ['edge_A', 'edge_B', 'edge_C'];

      try {
        await table.loadEdges(requestedEdges, cache);
      } catch (error) {
        logs.push(`[Error] ${error.message}`);
      }

      console.log = originalLog;
      return logs;
    });

    console.log('\n=== 部分缓存命中日志 ===');
    result.forEach(log => console.log(log));

    // 验证检测到缓存未命中
    const cacheMissLog = result.find(log => log.includes('Cache miss') && log.includes('2/3'));
    expect(cacheMissLog).toBeTruthy();
    console.log('\n✅ 部分缓存命中检测正常');

    // 验证回退到 API
    const apiFallbackLog = result.find(log => log.includes('falling back to API'));
    expect(apiFallbackLog).toBeTruthy();
    console.log('✅ 回退到 API 机制正常');
  });

  test('测试缓存为空或无效的场景', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(1000);

    console.log('\n=== 测试缓存为空/无效场景 ===');

    const scenarios = await page.evaluate(async () => {
      const results = {};

      const testScenario = async (name, cache) => {
        const logs = [];
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

        try {
          await table.loadEdges(['edge_1', 'edge_2'], cache);
        } catch (error) {
          logs.push(`[Error] ${error.message}`);
        }

        console.log = originalLog;
        results[name] = logs;
      };

      // Scenario 1: cache = null
      await testScenario('null_cache', null);

      // Scenario 2: cache = undefined
      await testScenario('undefined_cache', undefined);

      // Scenario 3: cache = [] (empty array)
      await testScenario('empty_cache', []);

      // Scenario 4: cache = {} (invalid type)
      await testScenario('invalid_cache', {});

      return results;
    });

    console.log('\n=== 各种缓存场景测试结果 ===');

    Object.entries(scenarios).forEach(([scenario, logs]) => {
      console.log(`\n${scenario}:`);
      logs.forEach(log => console.log(`  ${log}`));

      // 所有场景都应该直接调用 API（跳过缓存检查）
      const apiCallLog = logs.find(log => log.includes('Fetching edge data from API'));
      expect(apiCallLog).toBeTruthy();
    });

    console.log('\n✅ 所有缓存无效场景都正确回退到 API');
  });
});
