/**
 * Smart Frontend E2E Test for All 11 Strategy Templates
 *
 * 根据模板要求，智能选择指定数量的路段checkbox
 * 不选择第1个，从第2个开始，选择所需数量
 */

const { test, expect } = require('@playwright/test');

const LONG_TIMEOUT = 90000;
const WAIT_TIME = 1500;  // 1.5 seconds between operations
const BASE_URL = 'http://localhost:8000';

// 模板配置 - 包含所需边数
const TEMPLATES = [
  {
    templateId: 'vss_moderate',
    templateName: '可变限速 - 中等控制',
    strategyName: 'VSS中等控制-UI测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '33',
    maxStake: '44',
    edgeCount: 5  // 选择5条边 (从第2-6个)
  },
  {
    templateId: 'vss_strict',
    templateName: '可变限速 - 严格控制',
    strategyName: 'VSS严格控制-UI测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '20',
    maxStake: '35',
    edgeCount: 5
  },
  {
    templateId: 'vss_weather_based',
    templateName: '可变限速 - 天气应急',
    strategyName: 'VSS天气应急-UI测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '40',
    maxStake: '52',
    edgeCount: 5
  },
  {
    templateId: 'vss_upstream_warning',
    templateName: '可变限速 - 上游预警',
    strategyName: 'VSS上游预警-UI测试',
    type: 'VSS',
    route: 'G5',
    minStake: '1700',
    maxStake: '1800',
    edgeCount: 5
  },
  {
    templateId: 'vss_lane_differentiated',
    templateName: '可变限速 - 分车道控制',
    strategyName: 'VSS分车道-UI测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '10',
    maxStake: '30',
    edgeCount: 5
  },
  {
    templateId: 'dhs_peak_hours',
    templateName: '应急车道开放',
    strategyName: 'DHS高峰时段-UI测试',
    type: 'DHS',
    route: 'G4202',
    minStake: '33',
    maxStake: '44',
    edgeCount: 3  // DHS需要更少的边
  },
  {
    templateId: 'dhs_passenger_only',
    templateName: '应急车道 - 仅客车',
    strategyName: 'DHS仅客车-UI测试',
    type: 'DHS',
    route: 'G4202',
    minStake: '25',
    maxStake: '40',
    edgeCount: 3
  },
  {
    templateId: 'dhs_peak_multi_interval',
    templateName: '应急车道 - 多时段管理',
    strategyName: 'DHS多时段-UI测试',
    type: 'DHS',
    route: 'G4202',
    minStake: '45',
    maxStake: '55',
    edgeCount: 3
  },
  {
    templateId: 'tec_flow_metering',
    templateName: '收费入口 - 流量控制',
    strategyName: 'TEC流量控制-UI测试',
    type: 'TEC',
    route: 'G5',
    edgeCount: 2  // TEC只需要1-2条边
  },
  {
    templateId: 'tec_vehicle_restriction',
    templateName: '收费入口 - 车型限制',
    strategyName: 'TEC车型限制-UI测试',
    type: 'TEC',
    route: 'G5',
    edgeCount: 2
  },
  {
    templateId: 'tec_emergency_closure',
    templateName: '收费入口 - 紧急关闭',
    strategyName: 'TEC紧急关闭-UI测试',
    type: 'TEC',
    route: 'G5',
    edgeCount: 2
  }
];

test.describe('Frontend UI Test: All 11 Templates - Smart Edge Selection', () => {

  async function testTemplate(page, template, index) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`[${index}/${TEMPLATES.length}] ${template.type}: ${template.templateName}`);
    console.log(`${'='.repeat(80)}`);

    // ===== P1任务: 网络监听设置 =====
    let apiResponses = [];
    page.on('response', async (response) => {
      if (response.url().includes('/api/v1/control/strategy-instances')) {
        const status = response.status();
        let body = '';
        try {
          body = await response.text();
        } catch (e) {
          body = 'Unable to read response body';
        }
        apiResponses.push({ status, url: response.url(), body });

        console.log(`\n[API_RESPONSE] ${status} ${response.url()}`);
        if (status >= 400) {
          console.error(`[API_ERROR] ${status}:`, body);
        }
      }
    });

    // ===== P1.5任务: 浏览器控制台日志监听 =====
    page.on('console', (msg) => {
      const text = msg.text();
      // Log all parameter-related console messages from frontend
      if (text.includes('[') && (
          text.includes('createStrategy') ||
          text.includes('collectParameterValues') ||
          text.includes('extractTableParameters') ||
          text.includes('generateParamsForm') ||
          text.includes('renderStepArrayControl') ||
          text.includes('addStepRow') ||
          text.includes('extractFormParameters'))) {
        console.log(`[BROWSER_CONSOLE] ${text}`);
      }
    });

    try {
      // ===== 步骤1: 加载页面 =====
      console.log('[步骤1] 加载策略管理页面...');
      await page.goto(`${BASE_URL}/control/templates.html`, {
        waitUntil: 'networkidle',
        timeout: LONG_TIMEOUT
      });
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(WAIT_TIME);
      console.log('✓ 页面已加载');

      // ===== 步骤2: 等待模板加载 =====
      console.log('[步骤2] 等待模板列表加载...');
      await page.waitForSelector('.template-card', { timeout: LONG_TIMEOUT });
      await page.waitForTimeout(WAIT_TIME);
      console.log('✓ 模板列表已加载');

      // ===== 步骤3: 选择模板 =====
      console.log(`[步骤3] 选择模板: ${template.templateName}`);

      const templateCards = await page.locator('.template-card').all();
      console.log(`  找到 ${templateCards.length} 个模板卡片`);

      let selected = false;
      for (let i = 0; i < templateCards.length; i++) {
        const card = templateCards[i];
        const text = await card.textContent();

        if (text.includes(template.templateName)) {
          console.log(`  ✓ 在位置 ${i} 找到模板`);
          await card.click();
          await page.waitForTimeout(WAIT_TIME);
          selected = true;
          break;
        }
      }

      if (!selected) {
        console.error(`✗ 未找到模板`);
        return false;
      }
      console.log('✓ 模板已选择 (自动进入步骤2)');

      // ===== 步骤4: 设置路段过滤条件 =====
      console.log(`[步骤4] 设置路段查询条件...`);

      // 等待输入框出现
      await page.waitForSelector('input[type="text"], input[type="number"]', { timeout: LONG_TIMEOUT });
      await page.waitForTimeout(WAIT_TIME);

      // 对于 TEC 模板，先选择节点类型 (entrance)
      if (template.type === 'TEC') {
        console.log('  ℹ 检测到 TEC 模板，尝试选择节点类型...');
        const nodeTypeDropdowns = await page.locator('select, [role="combobox"]').all();
        for (const dropdown of nodeTypeDropdowns) {
          const text = await dropdown.textContent();
          if (text && text.includes('节点') || text.includes('entrance')) {
            await dropdown.click();
            await page.waitForTimeout(500);
            const entranceOption = page.locator('option:has-text("entrance"), div:has-text("entrance")').first();
            if (await entranceOption.isVisible({ timeout: 3000 }).catch(() => false)) {
              await entranceOption.click();
              console.log(`  ✓ 已选择节点类型: entrance`);
              await page.waitForTimeout(800);
              break;
            }
          }
        }
      }

      // 填充路线
      const textInputs = await page.locator('input[type="text"]').all();
      if (textInputs.length > 0) {
        await textInputs[0].clear();
        await textInputs[0].fill(template.route);
        console.log(`  ✓ 路线: ${template.route}`);
        await page.waitForTimeout(800);
      }

      // 填充最小桩号和其他数字字段
      if (template.minStake || template.type === 'DHS') {
        const numberInputs = await page.locator('input[type="number"]').all();
        console.log(`  ℹ 找到 ${numberInputs.length} 个数字输入框`);

        if (numberInputs.length > 0) {
          // 对于DHS,第一个数字字段可能是最小车道数
          if (template.type === 'DHS') {
            const firstInputPlaceholder = await numberInputs[0].getAttribute('placeholder');
            console.log(`    输入框0 placeholder: ${firstInputPlaceholder}`);

            // 检查是否是最小车道数字段,填充4
            if (firstInputPlaceholder && firstInputPlaceholder.includes('车道')) {
              await numberInputs[0].clear();
              await numberInputs[0].fill('4');
              console.log(`  ✓ 最小车道数: 4`);
              await page.waitForTimeout(800);
            } else if (template.minStake) {
              // 否则填充最小桩号
              await numberInputs[0].clear();
              await numberInputs[0].fill(template.minStake);
              console.log(`  ✓ 最小桩号: ${template.minStake}`);
              await page.waitForTimeout(800);
            }
          } else if (template.minStake) {
            // VSS和TEC的标准流程
            await numberInputs[0].clear();
            await numberInputs[0].fill(template.minStake);
            console.log(`  ✓ 最小桩号: ${template.minStake}`);
            await page.waitForTimeout(800);
          }
        }

        // 填充最大桩号
        if (numberInputs.length > 1 && template.maxStake) {
          await numberInputs[1].clear();
          await numberInputs[1].fill(template.maxStake);
          console.log(`  ✓ 最大桩号: ${template.maxStake}`);
          await page.waitForTimeout(800);
        }
      }

      // ===== 步骤5: 查询路段 =====
      console.log('[步骤5] 查询路段...');

      const queryBtn = page.locator('button:has-text("查询路段")').first();
      if (await queryBtn.isVisible({ timeout: 10000 })) {
        await queryBtn.click();
        console.log('  ✓ 查询已启动');
        // 等待结果加载
        await page.waitForTimeout(WAIT_TIME * 2);
        console.log('  ✓ 结果已加载');
      } else {
        console.warn('⚠ 未找到查询按钮');
      }

      // ===== 步骤6: 智能选择路段 =====
      console.log(`[步骤6] 选择 ${template.edgeCount} 条路段...`);

      // 找出路段表格的checkbox (跳过表头等)
      const edgeCheckboxes = await page.locator('tbody input[type="checkbox"], table input[type="checkbox"]').all();
      console.log(`  找到 ${edgeCheckboxes.length} 条路段`);

      let selectedCount = 0;
      // 从第2个开始选择 (索引从1开始，跳过第0个)
      const startIndex = 1; // 从第2个开始
      const endIndex = Math.min(startIndex + template.edgeCount - 1, edgeCheckboxes.length - 1);

      for (let i = startIndex; i <= endIndex && selectedCount < template.edgeCount; i++) {
        try {
          const checkbox = edgeCheckboxes[i];
          const isChecked = await checkbox.isChecked();

          if (!isChecked) {
            // 先scroll到checkbox位置
            await checkbox.scrollIntoViewIfNeeded();
            await checkbox.check();
            selectedCount++;
            console.log(`  ✓ 已选择第 ${i + 1} 条路段`);
            await page.waitForTimeout(300);
          }
        } catch (e) {
          console.log(`  ⚠ 无法选择第 ${i + 1} 条路段: ${e.message}`);
        }
      }

      if (selectedCount < template.edgeCount) {
        console.warn(`⚠ 仅选择了 ${selectedCount} 条路段 (目标: ${template.edgeCount})`);
      } else {
        console.log(`✓ 已选择 ${selectedCount} 条路段`);
      }

      await page.waitForTimeout(WAIT_TIME);

      // ===== 步骤7: 进入参数配置 =====
      console.log('[步骤7] 进入参数配置步骤...');

      const proceedBtn = page.locator('button:has-text("进入配置参数")').first();
      const proceedVisible = await proceedBtn.isVisible({ timeout: 10000 }).catch(() => false);

      if (proceedVisible) {
        await proceedBtn.click();
        console.log('  ✓ 点击了"进入配置参数"按钮');
        await page.waitForTimeout(WAIT_TIME * 1.5);
        console.log('✓ 已进入参数配置步骤');

        // 验证页面已更新到第3步
        const step3Title = page.locator('h3:has-text("步骤3"), h2:has-text("步骤3")');
        const step3Visible = await step3Title.isVisible({ timeout: 5000 }).catch(() => false);
        if (step3Visible) {
          console.log('  ✓ 确认已进入步骤3：配置参数');
        } else {
          console.warn('  ⚠ 无法确认是否进入步骤3');
        }
      } else {
        console.warn('⚠ 未找到进入配置按钮，可能已自动进入参数配置');
        // 尝试等待并检查是否已进入第3步
        await page.waitForTimeout(2000);
      }

      // ===== 步骤8: 填充策略名称和其他参数 =====
      console.log('[步骤8] 填充策略名称和表单参数...');

      // 先尝试为 DHS 和 TEC 模板填充必需的时间间隔参数
      if (template.type === 'DHS') {
        console.log('  ℹ 检测到 DHS 模板，尝试填充时间间隔参数');
        // 查找时间间隔表格
        const intervalTables = await page.locator('table tbody').all();
        console.log(`    找到 ${intervalTables.length} 个表格`);

        for (const tbody of intervalTables) {
          const rows = await tbody.locator('tr').all();
          console.log(`    表格有 ${rows.length} 行`);

          // 如果表格为空，添加至少一行数据
          if (rows.length === 0) {
            const addBtn = await tbody.locator('ancestor::table').locator('button:has-text("添加"), button:has-text("Add")').first();
            if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
              await addBtn.click();
              console.log(`    ✓ 点击了添加按钮`);
              await page.waitForTimeout(500);
            }
          }
        }
      }

      // 找策略名输入框
      const inputs = await page.locator('input[type="text"]').all();
      console.log(`  ℹ 找到 ${inputs.length} 个文本输入框`);
      let nameInputFound = false;

      for (let i = 0; i < inputs.length; i++) {
        const placeholder = await inputs[i].getAttribute('placeholder');
        const label = await inputs[i].getAttribute('aria-label');
        console.log(`    输入框 ${i}: placeholder="${placeholder}", label="${label}"`);

        if (placeholder && placeholder.includes('名')) {
          await inputs[i].clear();
          await inputs[i].fill(template.strategyName);
          console.log(`  ✓ 策略名称填充成功: ${template.strategyName}`);
          nameInputFound = true;
          await page.waitForTimeout(WAIT_TIME);
          break;
        }
      }

      if (!nameInputFound) {
        // 尝试第一个文本输入框
        if (inputs.length > 0) {
          const firstInput = inputs[0];
          const value = await firstInput.inputValue();
          if (!value || value.length === 0) {
            await firstInput.fill(template.strategyName);
            console.log(`  ✓ 策略名称填充成功（备选方案）: ${template.strategyName}`);
            await page.waitForTimeout(WAIT_TIME);
          } else {
            console.warn(`  ⚠ 第一个输入框已有值: ${value}`);
          }
        } else {
          console.error(`  ✗ 未找到任何文本输入框`);
        }
      }

      // ===== 步骤9: 提交策略并验证API响应 (P1.2任务) =====
      console.log('[步骤9] 提交策略并等待API响应...');

      // 检查表单中是否有参数字段
      const paramFields = await page.locator('[class*="form-group"]').count();
      console.log(`  ℹ 页面中找到 ${paramFields} 个表单组`);

      // 找到提交按钮
      const submitBtn = page.locator('#save-strategy-btn');
      const btnVisible = await submitBtn.isVisible({ timeout: 5000 }).catch(() => false);

      if (!btnVisible) {
        console.error('✗ 提交按钮不可见');
        return false;
      }

      // 检查按钮是否被禁用
      const isDisabled = await submitBtn.isDisabled().catch(() => true);
      if (isDisabled) {
        const title = await submitBtn.getAttribute('title');
        console.error(`✗ 提交按钮被禁用: ${title || 'No title'}`);
        return false;
      }

      console.log('  ✓ 提交按钮可用');

      // P1.2关键改进: 等待API响应
      let apiSuccess = false;
      let strategyId = null;

      const apiResponsePromise = new Promise((resolve) => {
        const checkResponses = () => {
          const creationResponse = apiResponses.find(r =>
            r.url.includes('/strategy-instances/') && r.status === 201
          );
          if (creationResponse) {
            try {
              const data = JSON.parse(creationResponse.body);
              strategyId = data.strategy_id || data.id;
              apiSuccess = true;
              console.log(`  ✓ API响应: 201 Created`);
              console.log(`  ✓ 策略ID: ${strategyId}`);
              resolve(true);
            } catch (e) {
              console.error(`  ✗ 解析API响应失败: ${e.message}`);
              resolve(false);
            }
          } else {
            const errorResponse = apiResponses.find(r =>
              r.url.includes('/strategy-instances/') && r.status >= 400
            );
            if (errorResponse) {
              console.error(`  ✗ API错误: ${errorResponse.status}`);
              console.error(`  ✗ 错误详情: ${errorResponse.body}`);
              resolve(false);
            }
          }
        };

        // 立即检查一次
        checkResponses();

        // 设置定时器,每100ms检查一次(最多5秒)
        let checked = 0;
        const interval = setInterval(() => {
          checked++;
          checkResponses();
          if (apiSuccess || checked > 50) {
            clearInterval(interval);
            resolve(apiSuccess);
          }
        }, 100);
      });

      // 点击提交按钮
      await submitBtn.click();
      console.log('  ✓ 点击提交按钮');

      // 等待API响应完成 (最多8秒)
      const apiCompleted = await Promise.race([
        apiResponsePromise,
        new Promise(resolve => setTimeout(() => resolve(false), 8000))
      ]);

      if (!apiSuccess) {
        console.error('✗ 未收到成功的API响应');
        if (apiResponses.length === 0) {
          console.error('  (未捕获到任何API响应)');
        } else {
          console.error(`  捕获到${apiResponses.length}个响应:`, apiResponses.map(r => `${r.status}`).join(','));
        }
        return false;
      }

      // ===== 步骤10: 验证成功 =====
      console.log('[步骤10] 验证创建成功...');

      console.log(`✅ [${index}] 测试完成: ${template.templateName}`);
      console.log(`   策略ID: ${strategyId}`);
      console.log(`   API状态: 成功 (201)\n`);
      return true;

    } catch (error) {
      console.error(`\n❌ [${index}] 错误: ${error.message}\n`);
      return false;
    }
  }

  // ===== 各模板的测试 =====

  test('1-VSS: vss_moderate', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[0], 1);
    expect(result).toBeTruthy();
  });

  test('2-VSS: vss_strict', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[1], 2);
    expect(result).toBeTruthy();
  });

  test('3-VSS: vss_weather_based', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[2], 3);
    expect(result).toBeTruthy();
  });

  test('4-VSS: vss_upstream_warning', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[3], 4);
    expect(result).toBeTruthy();
  });

  test('5-VSS: vss_lane_differentiated', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[4], 5);
    expect(result).toBeTruthy();
  });

  test('6-DHS: dhs_peak_hours', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[5], 6);
    expect(result).toBeTruthy();
  });

  test('7-DHS: dhs_passenger_only', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[6], 7);
    expect(result).toBeTruthy();
  });

  test('8-DHS: dhs_peak_multi_interval', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[7], 8);
    expect(result).toBeTruthy();
  });

  test('9-TEC: tec_flow_metering', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[8], 9);
    expect(result).toBeTruthy();
  });

  test('10-TEC: tec_vehicle_restriction', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[9], 10);
    expect(result).toBeTruthy();
  });

  test('11-TEC: tec_emergency_closure', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplate(page, TEMPLATES[10], 11);
    expect(result).toBeTruthy();
  });
});
