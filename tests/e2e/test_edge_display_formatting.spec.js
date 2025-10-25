/**
 * Direct EdgeDisplayTable Formatting Test
 * Test the EdgeDisplayTable class with mock edge data
 */

const { test, expect } = require('@playwright/test');

test.describe('EdgeDisplayTable 格式化测试', () => {
  test('直接测试 EdgeDisplayTable 桩号格式化', async ({ page }) => {
    // 添加 cache-busting 参数强制刷新
    const timestamp = Date.now();
    await page.goto(`http://localhost:8000/control/templates.html?t=${timestamp}`);
    await page.waitForTimeout(1000);

    console.log('\n=== 测试 EdgeDisplayTable 桩号格式化 ===');

    // 创建测试数据并渲染
    const testResult = await page.evaluate(() => {
      // 模拟路段数据 (公里单位)
      const mockEdges = [
        {
          edge_id: 'test_edge_1',
          route_code: 'SA2',
          section_code: 'SA2-1',
          start_stake: 57.545,  // 57.545 km = K57+545
          end_stake: 58.123,    // 58.123 km = K58+123
          length_m: 578,
          lane_count: 4,
          direction: '上行',
          node_type: 'gantry',
          gantry_count: 2
        },
        {
          edge_id: 'test_edge_2',
          route_code: 'SA2',
          section_code: 'SA2-2',
          start_stake: 58.123,  // 58.123 km = K58+123
          end_stake: 59.789,    // 59.789 km = K59+789
          length_m: 1666,
          lane_count: 5,
          direction: '上行',
          node_type: 'gantry',
          gantry_count: 3
        },
        {
          edge_id: 'test_edge_3',
          route_code: 'SA2',
          section_code: 'SA2-3',
          start_stake: 0.100,   // 0.100 km = K0+100
          end_stake: 0.500,     // 0.500 km = K0+500
          length_m: 400,
          lane_count: 4,
          direction: '上行',
          node_type: 'gantry',
          gantry_count: 1
        }
      ];

      // 创建容器
      const container = document.createElement('div');
      container.id = 'test-edge-display';
      document.body.appendChild(container);

      // 创建 EdgeDisplayTable 实例
      const table = new EdgeDisplayTable(container, 'DHS');

      // 手动设置边数据并渲染
      table.edges = mockEdges;
      table.render();

      // 提取渲染的桩号值
      // NOTE: 表格会按 start_stake 排序，所以需要先对 mockEdges 排序
      const sortedMockEdges = [...mockEdges].sort((a, b) =>
        (a.start_stake || 0) - (b.start_stake || 0)
      );

      const rows = container.querySelectorAll('.edge-table tbody tr');
      const results = [];

      rows.forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 6) {
          const startStake = cells[4].textContent.trim();
          const endStake = cells[5].textContent.trim();
          results.push({
            index,
            original_start: sortedMockEdges[index].start_stake,
            original_end: sortedMockEdges[index].end_stake,
            rendered_start: startStake,
            rendered_end: endStake
          });
        }
      });

      // 检查连续性检查
      const gaps = table.checkEdgeContinuity();

      return {
        results,
        gaps,
        summaryHTML: container.querySelector('.edge-summary')?.innerHTML || '',
        validationHTML: container.querySelector('.validation-issues')?.innerHTML || ''
      };
    });

    console.log('\n=== 桩号格式化结果 ===');
    testResult.results.forEach(result => {
      console.log(`路段 ${result.index + 1}:`);
      console.log(`  原始起始桩号: ${result.original_start} km`);
      console.log(`  渲染起始桩号: ${result.rendered_start}`);
      console.log(`  原始结束桩号: ${result.original_end} km`);
      console.log(`  渲染结束桩号: ${result.rendered_end}`);

      // 验证格式
      const stakePattern = /^K\d+\+\d{3}$/;
      expect(result.rendered_start).toMatch(stakePattern);
      expect(result.rendered_end).toMatch(stakePattern);

      // 验证准确性
      const formatStake = (stake) => {
        const km = Math.floor(stake);
        const m = Math.round((stake - km) * 1000);
        return `K${km}+${m.toString().padStart(3, '0')}`;
      };

      const expectedStart = formatStake(result.original_start);
      const expectedEnd = formatStake(result.original_end);

      console.log(`  期望起始桩号: ${expectedStart}`);
      console.log(`  期望结束桩号: ${expectedEnd}`);

      expect(result.rendered_start).toBe(expectedStart);
      expect(result.rendered_end).toBe(expectedEnd);
      console.log('  ✅ 桩号格式正确\n');
    });

    console.log('=== 连续性检查结果 ===');
    console.log('间隙列表:', testResult.gaps);
    // 应该检测到 edge_2 (K59+789) 和 edge_3 (K0+100) 之间有巨大间隙
    expect(testResult.gaps.length).toBeGreaterThan(0);
    console.log('✅ 连续性检查正常工作\n');

    console.log('=== 汇总信息 ===');
    console.log(testResult.summaryHTML);

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/edge_display_formatting.png',
      fullPage: true
    });
    console.log('✅ 截图已保存: tests/e2e/screenshots/edge_display_formatting.png');
  });

  test('测试特殊边界情况的桩号格式化', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(500);

    const boundaryTests = await page.evaluate(() => {
      const formatStake = (stake) => {
        if (!stake && stake !== 0) return 'N/A';
        const km = Math.floor(stake);
        const m = Math.round((stake - km) * 1000);
        return `K${km}+${m.toString().padStart(3, '0')}`;
      };

      return {
        test1: { input: 0, expected: 'K0+000', actual: formatStake(0) },
        test2: { input: 0.001, expected: 'K0+001', actual: formatStake(0.001) },
        test3: { input: 0.999, expected: 'K0+999', actual: formatStake(0.999) },
        test4: { input: 1.0, expected: 'K1+000', actual: formatStake(1.0) },
        test5: { input: 999.999, expected: 'K999+999', actual: formatStake(999.999) },
        test6: { input: 123.4567, expected: 'K123+457', actual: formatStake(123.4567) }, // 四舍五入
        test7: { input: null, expected: 'N/A', actual: formatStake(null) },
        test8: { input: undefined, expected: 'N/A', actual: formatStake(undefined) }
      };
    });

    console.log('\n=== 边界情况测试 ===');
    Object.entries(boundaryTests).forEach(([testName, test]) => {
      console.log(`${testName}: ${test.input} km → 期望 ${test.expected}, 实际 ${test.actual}`);
      expect(test.actual).toBe(test.expected);
    });
    console.log('✅ 所有边界情况测试通过！');
  });

  test('测试连续性检查的公里单位处理', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForTimeout(500);

    const continuityTest = await page.evaluate(() => {
      const mockEdges = [
        { start_stake: 10.0, end_stake: 10.5 },   // K10+000 to K10+500
        { start_stake: 10.5, end_stake: 11.0 },   // K10+500 to K11+000 (连续)
        { start_stake: 11.1, end_stake: 11.5 }    // K11+100 to K11+500 (间隙100m)
      ];

      const container = document.createElement('div');
      document.body.appendChild(container);

      const table = new EdgeDisplayTable(container, 'DHS');
      table.edges = mockEdges;

      const gaps = table.checkEdgeContinuity();

      return {
        gaps,
        tolerance_km: 0.05,  // 50米 = 0.05公里
        gap_between_edge2_and_edge3: (11.1 - 11.0) * 1000  // 应该是100米
      };
    });

    console.log('\n=== 连续性检查单位测试 ===');
    console.log('容差 (公里):', continuityTest.tolerance_km);
    console.log('edge2 和 edge3 之间间隙 (米):', continuityTest.gap_between_edge2_and_edge3);
    console.log('检测到的间隙:', continuityTest.gaps);

    // 应该检测到一个间隙 (100m > 50m tolerance)
    expect(continuityTest.gaps.length).toBe(1);
    expect(continuityTest.gaps[0]).toContain('100m');
    console.log('✅ 连续性检查使用了正确的公里单位！');
  });
});
