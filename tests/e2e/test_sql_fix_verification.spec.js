/**
 * 验证SQL修复是否生效
 */

const { test, expect } = require('@playwright/test');

test.describe('验证SQL修复', () => {
  const BASE_URL = 'http://localhost:8000';

  test('测试：route_codes=G4202 应该成功', async ({ page }) => {
    const response = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query?route_codes=G4202`
    );

    console.log(`✓ route_codes=G4202: HTTP ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`✓ 返回 ${data.total_count} 条数据`);
      expect(data.total_count).toBeGreaterThan(0);

      // 验证没有NULL route_code
      const hasNull = data.edges.some(e => !e.route_code);
      console.log(`✓ 是否包含NULL route_code: ${hasNull ? '是' : '否'}`);
      expect(hasNull).toBeFalsy();
    } else {
      const error = await response.json();
      console.log(`❌ 失败:`, error);
      expect(response.ok()).toBeTruthy();
    }
  });

  test('测试：空参数（等价无参数）应该返回什么？', async ({ page }) => {
    const response = await page.request.get(
      `${BASE_URL}/api/v1/control/edges/query`
    );

    console.log(`✓ 无参数查询: HTTP ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log(`✓ 返回 ${data.total_count} 条数据`);

      // 验证所有返回的数据都有route_code
      const nullCount = data.edges.filter(e => !e.route_code).length;
      console.log(`✓ route_code为NULL的数量: ${nullCount}`);
      expect(nullCount).toBe(0);  // 应该是0，因为我们已经过滤了
    } else {
      const error = await response.json();
      console.log(`⚠️  无参数查询失败 (这可能是正常的):`, error.detail?.message);
    }
  });
});
