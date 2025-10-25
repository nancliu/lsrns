/**
 * Quick Edge Display Test
 * 快速测试 EdgeDisplayTable 类是否正确加载
 */

const { test, expect } = require('@playwright/test');

test.describe('EdgeDisplayTable 快速测试', () => {
  test('检查 EdgeDisplayTable 类是否存在', async ({ page }) => {
    // 访问页面
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');

    // 等待一下确保 JavaScript 加载完成
    await page.waitForTimeout(1000);

    // 检查 EdgeDisplayTable 类是否存在
    const edgeDisplayTableExists = await page.evaluate(() => {
      return typeof EdgeDisplayTable !== 'undefined';
    });

    console.log('EdgeDisplayTable exists:', edgeDisplayTableExists);

    if (edgeDisplayTableExists) {
      console.log('✅ EdgeDisplayTable 类已成功加载！');

      // 检查类的方法
      const methods = await page.evaluate(() => {
        const proto = EdgeDisplayTable.prototype;
                return Object.getOwnPropertyNames(proto).filter(name => typeof proto[name] === 'function');
      });

      console.log('EdgeDisplayTable 方法列表:', methods);
      expect(methods).toContain('loadEdges');
      expect(methods).toContain('render');
      expect(methods).toContain('checkValidation');
    } else {
      console.log('❌ EdgeDisplayTable 类未加载！');
    }

    expect(edgeDisplayTableExists).toBe(true);
  });

  test('检查 generateParamsForm 函数是否存在', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const generateParamsFormExists = await page.evaluate(() => {
      return typeof generateParamsForm !== 'undefined';
    });

    console.log('generateParamsForm exists:', generateParamsFormExists);
    expect(generateParamsFormExists).toBe(true);
  });

  test('检查 initializeEdgeDisplay 函数是否存在', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const initializeEdgeDisplayExists = await page.evaluate(() => {
      return typeof initializeEdgeDisplay !== 'undefined';
    });

    console.log('initializeEdgeDisplay exists:', initializeEdgeDisplayExists);
    expect(initializeEdgeDisplayExists).toBe(true);
  });
});
