/**
 * Parameter Form Generation Test
 * 测试参数表单生成功能
 */

const { test, expect } = require('@playwright/test');

test.describe('参数表单生成测试', () => {
  test('完整测试: 选择模板 → 选择路段 → 生成参数表单', async ({ page }) => {
    // 启用控制台日志
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`[Browser Error]:`, msg.text());
      }
    });

    // 访问页面
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');

    console.log('\n=== 步骤1: 选择DHS模板 ===');

    // 等待模板加载
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 查找并点击 DHS 模板
    const dhsCard = page.locator('.template-card').filter({ hasText: /DHS|动态硬路肩/ }).first();
    await dhsCard.click();
    await page.waitForTimeout(500);

    // 检查 selectedTemplate
    const selectedTemplate = await page.evaluate(() => window.selectedTemplate);
    console.log('Selected template:', selectedTemplate ? selectedTemplate.template_name : 'null');
    console.log('Strategy type:', selectedTemplate ? selectedTemplate.strategy_type : 'null');
    console.log('Parameters schema length:', selectedTemplate ? Object.keys(selectedTemplate.parameters_schema || {}).length : 0);

    if (selectedTemplate && selectedTemplate.parameters_schema) {
      const paramNames = Object.keys(selectedTemplate.parameters_schema).slice(0, 5);
      console.log('First 5 parameter names:', paramNames);
    }

    expect(selectedTemplate).toBeTruthy();

    console.log('\n=== 步骤2: 进入步骤2并手动设置路段 ===');

    // 点击下一步（假设"下一步"按钮存在）
    await page.locator('button:has-text("下一步")').click();
    await page.waitForTimeout(1000);

    // 手动设置 selectedEdges（模拟路段选择）
    await page.evaluate(() => {
      window.selectedEdges = ['-5880', '-5881', '-5882', '-5883', '-5884'];
      console.log('[Test] Set selectedEdges:', window.selectedEdges);
    });

    console.log('\n=== 步骤3: 进入步骤3并生成参数表单 ===');

    // 点击下一步进入步骤3
    await page.locator('button:has-text("下一步")').last().click();
    await page.waitForTimeout(2000);

    // 检查步骤3是否可见
    const step3Visible = await page.locator('#step3-content').isVisible();
    console.log('Step 3 visible:', step3Visible);
    expect(step3Visible).toBe(true);

    // 检查参数表单
    const paramsForm = page.locator('#params-form');
    const formGroupCount = await paramsForm.locator('.form-group').count();
    console.log('Form groups count:', formGroupCount);

    // 检查 edge-display-container
    const edgeDisplayContainer = page.locator('#edge-display-container');
    const edgeDisplayHTML = await edgeDisplayContainer.innerHTML();
    console.log('Edge display container has content:', edgeDisplayHTML.length > 50);

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/step3_params_form_test.png',
      fullPage: true
    });

    // 如果表单为空，输出调试信息
    if (formGroupCount === 0) {
      console.error('\n❌ 参数表单为空！调试信息:');

      // 检查 selectedTemplate
      const template = await page.evaluate(() => window.selectedTemplate);
      console.log('selectedTemplate exists:', !!template);

      if (template) {
        console.log('parameters_schema exists:', !!template.parameters_schema);
        console.log('parameters_schema type:', Array.isArray(template.parameters_schema) ? 'array' : typeof template.parameters_schema);

        if (template.parameters_schema) {
          if (Array.isArray(template.parameters_schema)) {
            console.log('parameters_schema length:', template.parameters_schema.length);
            console.log('First parameter:', template.parameters_schema[0]);
          } else {
            console.log('parameters_schema keys:', Object.keys(template.parameters_schema));
          }
        }
      }

      // 手动调用 generateParamsForm
      console.log('\n尝试手动调用 generateParamsForm...');
      const manualCallResult = await page.evaluate(() => {
        if (window.selectedTemplate) {
          try {
            generateParamsForm(window.selectedTemplate);
            return { success: true };
          } catch (err) {
            return { error: err.message, stack: err.stack };
          }
        } else {
          return { error: 'selectedTemplate is null' };
        }
      });

      console.log('Manual call result:', manualCallResult);

      // 再次检查表单
      await page.waitForTimeout(1000);
      const formGroupCountAfter = await paramsForm.locator('.form-group').count();
      console.log('Form groups after manual call:', formGroupCountAfter);
    }

    // 验证表单至少有一些内容（策略名称 + 策略描述 + 至少一个参数）
    expect(formGroupCount).toBeGreaterThan(2);
  });
});
