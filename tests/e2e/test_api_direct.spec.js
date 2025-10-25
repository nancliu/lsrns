/**
 * 直接API测试 - 使用正确的参数名
 */

const { test, expect } = require('@playwright/test');

test.describe('API直接测试 - 正确参数', () => {
  const BASE_URL = 'http://localhost:8000';

  test('测试route_codes参数（复数）', async ({ page }) => {
    console.log('\n=== 测试1: 使用route_codes参数 ===');

    const response = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_codes=G4202`
    );

    console.log(`HTTP状态: ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`✓ 成功! 返回: ${JSON.stringify(data).substring(0, 200)}...`);
      console.log(`✓ edges数量: ${data.edges?.length || 0}`);
      console.log(`✓ total_count: ${data.total_count || 0}`);

      if (data.edges && data.edges.length > 0) {
        console.log(`✓ 第一条edge示例:`, JSON.stringify(data.edges[0], null, 2));
      }
    } else {
      const errorData = await response.json();
      console.log(`❌ 失败:`, JSON.stringify(errorData, null, 2));
    }
  });

  test('测试route_code参数（单数）', async ({ page }) => {
    console.log('\n=== 测试2: 使用route_code参数 ===');

    const response = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_code=G4202`
    );

    console.log(`HTTP状态: ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`✓ 成功! 返回: ${JSON.stringify(data).substring(0, 200)}...`);
      console.log(`✓ edges数量: ${data.edges?.length || 0}`);
      console.log(`✓ total_count: ${data.total_count || 0}`);
    } else {
      const errorData = await response.json();
      console.log(`❌ 失败:`, JSON.stringify(errorData, null, 2));
    }
  });

  test('测试无参数查询', async ({ page }) => {
    console.log('\n=== 测试3: 无参数查询 ===');

    const response = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query`
    );

    console.log(`HTTP状态: ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`✓ 成功! 返回: ${JSON.stringify(data).substring(0, 200)}...`);
      console.log(`✓ edges数量: ${data.edges?.length || 0}`);
      console.log(`✓ total_count: ${data.total_count || 0}`);

      // 检查是否有route_code为null的数据
      if (data.edges && data.edges.length > 0) {
        const nullRoutes = data.edges.filter(e => !e.route_code);
        console.log(`⚠️  route_code为null的数量: ${nullRoutes.length}`);

        if (nullRoutes.length > 0) {
          console.log(`⚠️  null记录示例:`, JSON.stringify(nullRoutes[0], null, 2));
        }
      }
    } else {
      const errorData = await response.json();
      console.log(`❌ 失败:`, JSON.stringify(errorData, null, 2));
    }
  });

  test('测试SA2路线', async ({ page }) => {
    console.log('\n=== 测试4: SA2路线（作为对比）===');

    const response = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_codes=SA2`
    );

    console.log(`HTTP状态: ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`✓ 成功! SA2返回: ${data.total_count || 0} 条记录`);

      if (data.edges && data.edges.length > 0) {
        console.log(`✓ SA2第一条edge:`, JSON.stringify(data.edges[0], null, 2));
      }
    } else {
      const errorData = await response.json();
      console.log(`❌ SA2查询失败:`, JSON.stringify(errorData, null, 2));
    }
  });
});
