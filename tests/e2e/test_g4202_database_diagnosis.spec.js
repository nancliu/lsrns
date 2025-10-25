/**
 * G4202 路段数据诊断测试
 *
 * 目的：诊断为什么G4202路线查询不返回数据
 *
 * 测试策略：
 * 1. 直接测试API端点
 * 2. 检查数据库中是否有G4202数据
 * 3. 测试不同的查询参数组合
 * 4. 检查前端请求参数格式
 */

const { test, expect } = require('@playwright/test');

test.describe('G4202 路段数据诊断', () => {
  const BASE_URL = 'http://localhost:8000';

  test.beforeEach(async ({ page }) => {
    console.log('\n========================================');
    console.log('G4202 Database Diagnosis Test');
    console.log('========================================\n');
  });

  test('诊断1: 测试路线列表API', async ({ page }) => {
    console.log('=== Step 1: 获取可用路线列表 ===');

    const response = await page.request.get(`${BASE_URL}/api/v1/control/edges/routes`);
    expect(response.ok()).toBeTruthy();

    const routes = await response.json();
    console.log(`✓ 找到 ${routes.length} 条路线`);
    console.log('路线列表:', routes.map(r => r.route_code).join(', '));

    const hasG4202 = routes.some(r => r.route_code === 'G4202');
    console.log(`✓ G4202 在路线列表中: ${hasG4202 ? '是' : '否'}`);

    if (hasG4202) {
      const g4202Route = routes.find(r => r.route_code === 'G4202');
      console.log('✓ G4202 详细信息:', JSON.stringify(g4202Route, null, 2));
    }
  });

  test('诊断2: 直接测试G4202路段查询API (仅route_codes)', async ({ page }) => {
    console.log('\n=== Step 2: 测试G4202路段查询 (仅route_codes) ===');

    // 测试1: 仅使用route_codes参数
    console.log('\n测试A: GET /api/v1/control/edges/query?route_codes=G4202');
    const response1 = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_codes=G4202`
    );

    console.log(`HTTP状态: ${response1.status()}`);
    const data1 = await response1.json();

    if (response1.ok()) {
      console.log(`✓ 返回数据条数: ${data1.total_count}`);
      if (data1.edges && data1.edges.length > 0) {
        console.log('✓ 第一条数据示例:', JSON.stringify(data1.edges[0], null, 2));
        console.log(`✓ 桩号范围: ${Math.min(...data1.edges.map(e => e.start_stake))} - ${Math.max(...data1.edges.map(e => e.end_stake))}`);
      } else {
        console.log('⚠️  查询成功但返回0条数据');
      }
    } else {
      console.log('❌ 查询失败:', data1);
    }
  });

  test('诊断3: 测试G4202路段查询API (带多个参数)', async ({ page }) => {
    console.log('\n=== Step 3: 测试G4202路段查询 (带多个参数) ===');

    // 测试2: 使用route_codes + route_direction参数
    console.log('\n测试B: route_codes=G4202 + route_direction=clockwise');
    const response2 = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_codes=G4202&route_direction=clockwise`
    );

    console.log(`HTTP状态: ${response2.status()}`);
    const data2 = await response2.json();

    if (response2.ok()) {
      console.log(`✓ 返回数据条数: ${data2.total_count}`);
    } else {
      console.log('❌ 查询失败:', data2);
    }

    // 测试3: 使用route_codes + route_direction=counterclockwise参数
    console.log('\n测试C: route_codes=G4202 + route_direction=counterclockwise');
    const response3 = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_codes=G4202&route_direction=counterclockwise`
    );

    console.log(`HTTP状态: ${response3.status()}`);
    const data3 = await response3.json();

    if (response3.ok()) {
      console.log(`✓ 返回数据条数: ${data3.total_count}`);
    } else {
      console.log('❌ 查询失败:', data3);
    }
  });

  test('诊断4: 测试前端实际使用的查询参数', async ({ page }) => {
    console.log('\n=== Step 4: 模拟前端查询 ===');

    // 打开控制页面
    await page.goto(`${BASE_URL}/frontend/control/`);
    await page.waitForLoadState('networkidle');

    // 监听网络请求
    const requests = [];
    page.on('request', request => {
      if (request.url().includes('/api/v1/control/edges/query')) {
        requests.push({
          url: request.url(),
          method: request.method(),
          postData: request.postData()
        });
      }
    });

    // 点击Step 1的VSS模板
    console.log('✓ 选择VSS模板');
    await page.click('input[name="strategy-template"][value="vss"]');
    await page.click('button#next-step-1');
    await page.waitForSelector('#step-2', { state: 'visible', timeout: 5000 });

    // 选择路线G4202
    console.log('✓ 选择路线G4202');
    await page.selectOption('select#route-select', 'G4202');

    // 点击查询路段
    console.log('✓ 点击查询路段按钮');
    await page.click('button#query-edges-btn');

    // 等待请求完成
    await page.waitForTimeout(3000);

    console.log('\n捕获到的请求:');
    requests.forEach((req, index) => {
      console.log(`\n请求 ${index + 1}:`);
      console.log(`  URL: ${req.url}`);
      console.log(`  Method: ${req.method}`);
      if (req.postData) {
        console.log(`  POST Data: ${req.postData}`);
      }
    });

    // 检查结果表是否显示
    const resultTable = await page.locator('#edge-select-table').isVisible();
    console.log(`\n✓ 结果表显示: ${resultTable ? '是' : '否'}`);

    if (resultTable) {
      const rowCount = await page.locator('#edge-select-table tbody tr').count();
      console.log(`✓ 结果行数: ${rowCount}`);
    }
  });

  test('诊断5: 测试其他路线是否返回数据', async ({ page }) => {
    console.log('\n=== Step 5: 测试其他路线 ===');

    // 先获取路线列表
    const routesResponse = await page.request.get(`${BASE_URL}/api/v1/control/edges/routes`);
    const routes = await routesResponse.json();

    // 测试前3条路线（排除G4202）
    const testRoutes = routes
      .filter(r => r.route_code !== 'G4202')
      .slice(0, 3);

    console.log(`测试路线: ${testRoutes.map(r => r.route_code).join(', ')}\n`);

    for (const route of testRoutes) {
      console.log(`测试路线: ${route.route_code}`);
      const response = await page.request.get(
        `${BASE_URL}/api/v1/control/edges/query?route_codes=${route.route_code}`
      );

      if (response.ok()) {
        const data = await response.json();
        console.log(`  ✓ 返回 ${data.total_count} 条数据`);
      } else {
        console.log(`  ❌ 查询失败`);
      }
    }
  });

  test('诊断6: 测试数据库连接和原始SQL', async ({ page }) => {
    console.log('\n=== Step 6: 测试数据库原始查询 ===');

    // 这个测试需要后端支持，我们通过API间接测试
    console.log('提示: 如果以上测试都失败，建议手动执行以下SQL:');
    console.log('');
    console.log('SQL 1: 检查G4202是否存在');
    console.log(`  SELECT COUNT(*) FROM dim.sim_network_edges WHERE route_code = 'G4202';`);
    console.log('');
    console.log('SQL 2: 检查路线表中有哪些数据');
    console.log(`  SELECT route_code, COUNT(*) FROM dim.sim_network_edges GROUP BY route_code;`);
    console.log('');
    console.log('SQL 3: 查看G4202的数据示例');
    console.log(`  SELECT * FROM dim.sim_network_edges WHERE route_code = 'G4202' LIMIT 5;`);
    console.log('');
    console.log('SQL 4: 检查索引是否存在');
    console.log(`  SELECT indexname FROM pg_indexes WHERE tablename = 'sim_network_edges';`);
    console.log('');
  });
});
