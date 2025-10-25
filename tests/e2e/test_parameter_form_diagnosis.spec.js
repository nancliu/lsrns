/**
 * Parameter Form Diagnosis Test
 * 诊断配置参数页面参数配置内容缺失的问题
 */

const { test, expect } = require('@playwright/test');

test.describe('参数配置页面诊断', () => {
  let page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();

    // 启用控制台日志捕获
    page.on('console', msg => {
      console.log(`[Browser Console ${msg.type()}]:`, msg.text());
    });

    // 捕获页面错误
    page.on('pageerror', err => {
      console.error(`[Page Error]:`, err.message);
    });

    // 捕获请求失败
    page.on('requestfailed', request => {
      console.error(`[Request Failed]: ${request.url()} - ${request.failure().errorText}`);
    });
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('步骤1: 访问模板页面并加载模板', async () => {
    console.log('\n=== 步骤1: 访问模板页面 ===');

    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');

    // 检查页面标题
    const title = await page.title();
    console.log('页面标题:', title);
    expect(title).toContain('策略模板');

    // 等待模板加载
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 检查模板数量
    const templateCount = await page.locator('.template-card').count();
    console.log(`✓ 加载了 ${templateCount} 个模板`);
    expect(templateCount).toBeGreaterThan(0);

    // 截图保存
    await page.screenshot({
      path: 'tests/e2e/screenshots/step1_templates.png',
      fullPage: true
    });
  });

  test('步骤2: 选择DHS模板并检查selectedTemplate', async () => {
    console.log('\n=== 步骤2: 选择DHS模板 ===');

    // 查找DHS模板
    const dhsTemplate = page.locator('.template-card').filter({ hasText: 'DHS' }).first();
    await expect(dhsTemplate).toBeVisible();

    console.log('✓ 找到DHS模板');

    // 点击选择
    await dhsTemplate.click();
    await page.waitForTimeout(500);

    // 检查 selectedTemplate 变量
    const selectedTemplate = await page.evaluate(() => {
      return window.selectedTemplate;
    });

    console.log('selectedTemplate:', JSON.stringify(selectedTemplate, null, 2));

    expect(selectedTemplate).toBeTruthy();
    expect(selectedTemplate.strategy_type).toBe('DHS');

    // 检查是否进入步骤2
    const step2Visible = await page.locator('#step2-content').isVisible();
    console.log('步骤2可见:', step2Visible);

    await page.screenshot({
      path: 'tests/e2e/screenshots/step2_dhs_selected.png',
      fullPage: true
    });
  });

  test('步骤3: 选择路段', async () => {
    console.log('\n=== 步骤3: 选择路段 ===');

    // 点击"下一步"进入步骤2
    const nextBtn = page.locator('button:has-text("下一步")');
    await nextBtn.click();
    await page.waitForTimeout(1000);

    // 确认在步骤2
    await expect(page.locator('#step2-content')).toBeVisible();
    console.log('✓ 成功进入步骤2');

    // 选择一些路段（使用edge selector）
    // 先检查是否有路段选择器
    const edgeSelectorExists = await page.locator('#edge-selector-container').isVisible();
    console.log('路段选择器存在:', edgeSelectorExists);

    if (edgeSelectorExists) {
      // 等待路段数据加载
      await page.waitForTimeout(2000);

      // 尝试选择几个路段（假设有可选路段）
      const selectableEdges = await page.locator('input[type="checkbox"][name="edge"]').count();
      console.log(`可选路段数量: ${selectableEdges}`);

      if (selectableEdges > 0) {
        // 选择前5个路段
        const edgesToSelect = Math.min(5, selectableEdges);
        for (let i = 0; i < edgesToSelect; i++) {
          await page.locator('input[type="checkbox"][name="edge"]').nth(i).check();
        }
        console.log(`✓ 选择了 ${edgesToSelect} 个路段`);
      }
    }

    // 检查 selectedEdges 变量
    const selectedEdges = await page.evaluate(() => {
      return window.selectedEdges;
    });

    console.log('selectedEdges:', selectedEdges);
    console.log(`选中路段数量: ${selectedEdges ? selectedEdges.length : 0}`);

    await page.screenshot({
      path: 'tests/e2e/screenshots/step2_edges_selected.png',
      fullPage: true
    });
  });

  test('步骤4: 进入步骤3并检查参数表单', async () => {
    console.log('\n=== 步骤4: 进入步骤3 ===');

    // 点击"下一步"进入步骤3
    const nextBtn = page.locator('button:has-text("下一步")').last();
    await nextBtn.click();
    await page.waitForTimeout(2000);

    // 确认在步骤3
    const step3Visible = await page.locator('#step3-content').isVisible();
    console.log('步骤3可见:', step3Visible);
    expect(step3Visible).toBe(true);

    // 检查参数表单容器
    const paramsForm = page.locator('#params-form');
    const paramsFormExists = await paramsForm.count();
    console.log('参数表单存在:', paramsFormExists > 0);

    // 检查表单内容
    const formHTML = await paramsForm.innerHTML();
    console.log('表单HTML长度:', formHTML.length);
    console.log('表单HTML前500字符:', formHTML.substring(0, 500));

    // 检查是否有表单控件
    const formGroups = await paramsForm.locator('.form-group').count();
    console.log(`表单组数量: ${formGroups}`);

    // 检查 edge-display-container
    const edgeDisplayContainer = page.locator('#edge-display-container');
    const edgeDisplayExists = await edgeDisplayContainer.count();
    console.log('edge-display-container存在:', edgeDisplayExists > 0);

    const edgeDisplayHTML = await edgeDisplayContainer.innerHTML();
    console.log('edge-display-container HTML长度:', edgeDisplayHTML.length);
    console.log('edge-display-container HTML前500字符:', edgeDisplayHTML.substring(0, 500));

    // 检查 selectedTemplate.parameters_schema
    const templateSchema = await page.evaluate(() => {
      if (!window.selectedTemplate) {
        return { error: 'selectedTemplate is null' };
      }
      return {
        hasSchema: !!window.selectedTemplate.parameters_schema,
        schemaKeys: window.selectedTemplate.parameters_schema ?
          Object.keys(window.selectedTemplate.parameters_schema) : [],
        schemaPreview: window.selectedTemplate.parameters_schema ?
          JSON.stringify(window.selectedTemplate.parameters_schema).substring(0, 500) : null
      };
    });

    console.log('Template Schema 信息:', JSON.stringify(templateSchema, null, 2));

    // 检查 generateParamsForm 函数是否被调用
    const generateParamsFormCalled = await page.evaluate(() => {
      return window.generateParamsFormCalled || false;
    });
    console.log('generateParamsForm 被调用:', generateParamsFormCalled);

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/step3_params_form.png',
      fullPage: true
    });

    // 如果表单为空，输出更多诊断信息
    if (formGroups === 0) {
      console.error('\n❌ 参数表单为空！');
      console.error('可能的原因:');
      console.error('1. selectedTemplate.parameters_schema 为空');
      console.error('2. generateParamsForm() 函数未被调用');
      console.error('3. generateParamsForm() 函数执行出错');

      // 检查控制台错误
      const consoleErrors = await page.evaluate(() => {
        return window.consoleErrors || [];
      });
      console.error('控制台错误:', consoleErrors);
    }
  });

  test('步骤5: 检查JavaScript加载', async () => {
    console.log('\n=== 步骤5: 检查JavaScript加载 ===');

    // 检查关键函数是否存在
    const functionsCheck = await page.evaluate(() => {
      return {
        generateParamsForm: typeof window.generateParamsForm === 'function',
        initializeEdgeDisplay: typeof window.initializeEdgeDisplay === 'function',
        EdgeDisplayTable: typeof window.EdgeDisplayTable === 'function',
        generateSmartPlaceholder: typeof window.generateSmartPlaceholder === 'function',
        validateArrayField: typeof window.validateArrayField === 'function',
        validateNumberRange: typeof window.validateNumberRange === 'function'
      };
    });

    console.log('函数存在性检查:', JSON.stringify(functionsCheck, null, 2));

    // 检查是否所有必要函数都存在
    for (const [funcName, exists] of Object.entries(functionsCheck)) {
      if (!exists) {
        console.error(`❌ 函数 ${funcName} 不存在`);
      } else {
        console.log(`✓ 函数 ${funcName} 存在`);
      }
    }
  });

  test('步骤6: 手动调用 generateParamsForm', async () => {
    console.log('\n=== 步骤6: 手动调用 generateParamsForm ===');

    // 手动调用 generateParamsForm
    const result = await page.evaluate(() => {
      if (!window.selectedTemplate) {
        return { error: 'selectedTemplate is null' };
      }

      if (typeof window.generateParamsForm !== 'function') {
        return { error: 'generateParamsForm function not found' };
      }

      try {
        window.generateParamsForm(window.selectedTemplate);
        return { success: true };
      } catch (err) {
        return { error: err.message, stack: err.stack };
      }
    });

    console.log('手动调用结果:', JSON.stringify(result, null, 2));

    // 等待DOM更新
    await page.waitForTimeout(1000);

    // 再次检查表单
    const formGroups = await page.locator('#params-form .form-group').count();
    console.log(`手动调用后表单组数量: ${formGroups}`);

    // 截图
    await page.screenshot({
      path: 'tests/e2e/screenshots/step3_after_manual_call.png',
      fullPage: true
    });
  });
});
