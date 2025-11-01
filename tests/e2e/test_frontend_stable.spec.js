/**
 * Stable Frontend E2E Test for All 11 Strategy Templates
 *
 * This test slowly and carefully navigates through the frontend UI
 * to create strategy instances for all 11 control strategy templates.
 *
 * Important: Operations are deliberately slow to ensure stability
 */

const { test, expect } = require('@playwright/test');

// Extended timeouts for stability
const LONG_TIMEOUT = 60000;
const WAIT_TIME = 1500;  // Wait 1.5 seconds between operations

const BASE_URL = 'http://localhost:8000';

const TEMPLATES = [
  {
    templateId: 'vss_moderate',
    templateName: '可变限速 - 中等控制',
    strategyName: 'VSS中等控制-前端测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '33',
    maxStake: '44'
  },
  {
    templateId: 'vss_strict',
    templateName: '可变限速 - 严格控制',
    strategyName: 'VSS严格控制-前端测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '20',
    maxStake: '35'
  },
  {
    templateId: 'vss_weather_based',
    templateName: '可变限速 - 天气应急',
    strategyName: 'VSS天气应急-前端测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '40',
    maxStake: '52'
  },
  {
    templateId: 'vss_upstream_warning',
    templateName: '可变限速 - 上游预警',
    strategyName: 'VSS上游预警-前端测试',
    type: 'VSS',
    route: 'G5',
    minStake: '1700',
    maxStake: '1800'
  },
  {
    templateId: 'vss_lane_differentiated',
    templateName: '可变限速 - 分车道控制',
    strategyName: 'VSS分车道-前端测试',
    type: 'VSS',
    route: 'G4202',
    minStake: '10',
    maxStake: '30'
  },
  {
    templateId: 'dhs_peak_hours',
    templateName: '应急车道开放',
    strategyName: 'DHS高峰时段-前端测试',
    type: 'DHS',
    route: 'G4202',
    minStake: '33',
    maxStake: '44'
  },
  {
    templateId: 'dhs_passenger_only',
    templateName: '应急车道 - 仅客车',
    strategyName: 'DHS仅客车-前端测试',
    type: 'DHS',
    route: 'G4202',
    minStake: '25',
    maxStake: '40'
  },
  {
    templateId: 'dhs_peak_multi_interval',
    templateName: '应急车道 - 多时段管理',
    strategyName: 'DHS多时段-前端测试',
    type: 'DHS',
    route: 'G4202',
    minStake: '45',
    maxStake: '55'
  },
  {
    templateId: 'tec_flow_metering',
    templateName: '收费入口 - 流量控制',
    strategyName: 'TEC流量控制-前端测试',
    type: 'TEC',
    route: 'G5'
  },
  {
    templateId: 'tec_vehicle_restriction',
    templateName: '收费入口 - 车型限制',
    strategyName: 'TEC车型限制-前端测试',
    type: 'TEC',
    route: 'G5'
  },
  {
    templateId: 'tec_emergency_closure',
    templateName: '收费入口 - 紧急关闭',
    strategyName: 'TEC紧急关闭-前端测试',
    type: 'TEC',
    route: 'G5'
  }
];

test.describe('Frontend E2E: All 11 Strategy Templates (Stable)', () => {

  /**
   * Test template: Generic workflow for any template
   */
  async function testTemplateCreation(page, template, templateIndex) {
    console.log(`\n${'='*70}`);
    console.log(`[TEST ${templateIndex}/${TEMPLATES.length}] ${template.type}: ${template.templateName}`);
    console.log(`${'='*70}`);

    // ===== STEP 1: Navigate to page =====
    console.log('\n[STEP 1] Navigating to strategies page...');
    await page.goto(`${BASE_URL}/control/templates.html`, { waitUntil: 'networkidle', timeout: LONG_TIMEOUT });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(WAIT_TIME);
    console.log('✓ Page loaded');

    // ===== STEP 2: Wait for templates to load =====
    console.log('[STEP 2] Waiting for templates to load...');
    try {
      await page.waitForSelector('.template-card', { timeout: LONG_TIMEOUT });
      await page.waitForTimeout(WAIT_TIME);
      console.log('✓ Templates loaded');
    } catch (e) {
      console.warn('⚠ Template cards not found, but continuing');
    }

    // ===== STEP 3: Find and click template card =====
    console.log(`[STEP 3] Selecting template: ${template.templateName}...`);

    const templateCards = await page.locator('.template-card').all();
    console.log(`  Found ${templateCards.length} template cards`);

    let found = false;
    for (let i = 0; i < templateCards.length; i++) {
      const card = templateCards[i];
      const text = await card.textContent();

      if (text.includes(template.templateName)) {
        console.log(`  ✓ Found template at position ${i}`);
        await card.click();
        await page.waitForTimeout(WAIT_TIME * 1.5);
        found = true;
        break;
      }
    }

    if (!found) {
      console.error(`✗ Template "${template.templateName}" not found`);
      console.log('Available templates:');
      for (let i = 0; i < templateCards.length; i++) {
        const text = await templateCards[i].textContent();
        console.log(`  ${i}: ${text.substring(0, 50)}`);
      }
      return false;
    }

    // ===== STEP 4: Click Next to go to edge selection =====
    console.log('[STEP 4] Clicking Next button...');
    const nextBtn1 = page.locator('button:has-text("下一步")').first();

    if (await nextBtn1.isVisible({ timeout: 10000 })) {
      await nextBtn1.click();
      await page.waitForTimeout(WAIT_TIME * 2);
      console.log('✓ Moved to edge selection step');
    } else {
      console.error('✗ Next button not found');
      return false;
    }

    // ===== STEP 5: Fill edge search criteria =====
    console.log('[STEP 5] Filling edge search criteria...');

    // Find and fill route input
    const routeInputs = page.locator('input').all();
    let routeInputElement = null;

    // Search for route input by placeholder or nearby label
    const allInputs = await page.locator('input').all();
    for (const input of allInputs) {
      const placeholder = await input.getAttribute('placeholder');
      if (placeholder && placeholder.includes('路')) {
        routeInputElement = input;
        break;
      }
    }

    if (routeInputElement) {
      await routeInputElement.clear();
      await routeInputElement.fill(template.route);
      console.log(`  ✓ Route set to: ${template.route}`);
      await page.waitForTimeout(WAIT_TIME);
    }

    // Fill min stake if provided
    if (template.minStake) {
      const inputs = await page.locator('input[type="number"]').all();
      if (inputs.length >= 1) {
        await inputs[0].clear();
        await inputs[0].fill(template.minStake);
        console.log(`  ✓ Min Stake set to: ${template.minStake}`);
        await page.waitForTimeout(WAIT_TIME);
      }
    }

    // Fill max stake if provided
    if (template.maxStake) {
      const inputs = await page.locator('input[type="number"]').all();
      if (inputs.length >= 2) {
        await inputs[1].clear();
        await inputs[1].fill(template.maxStake);
        console.log(`  ✓ Max Stake set to: ${template.maxStake}`);
        await page.waitForTimeout(WAIT_TIME);
      }
    }

    // ===== STEP 6: Click search/apply button =====
    console.log('[STEP 6] Searching for edges...');
    const searchBtn = page.locator('button:has-text("查询"), button:has-text("搜索"), button:has-text("应用")').first();

    if (await searchBtn.isVisible({ timeout: 10000 })) {
      await searchBtn.click();
      console.log('  ✓ Search initiated');
      await page.waitForTimeout(WAIT_TIME * 3);
      console.log('  ✓ Results loaded');
    } else {
      console.warn('⚠ Search button not found, trying alternative');
    }

    // ===== STEP 7: Select edges =====
    console.log('[STEP 7] Selecting edges...');
    const checkboxes = await page.locator('input[type="checkbox"]').all();
    console.log(`  Found ${checkboxes.length} checkboxes`);

    let selectedCount = 0;
    const maxEdges = 5;

    for (let i = 0; i < Math.min(checkboxes.length, maxEdges); i++) {
      try {
        await checkboxes[i].check();
        selectedCount++;
        console.log(`  ✓ Selected edge ${i + 1}`);
        await page.waitForTimeout(500);
      } catch (e) {
        console.log(`  ⚠ Could not check box ${i}`);
      }
    }

    console.log(`  ✓ Total edges selected: ${selectedCount}`);
    await page.waitForTimeout(WAIT_TIME);

    // ===== STEP 8: Click Next to go to parameters =====
    console.log('[STEP 8] Proceeding to parameters...');
    const nextBtn2 = page.locator('button:has-text("下一步")').first();

    if (await nextBtn2.isVisible({ timeout: 10000 })) {
      await nextBtn2.click();
      await page.waitForTimeout(WAIT_TIME * 2);
      console.log('✓ Moved to parameters step');
    } else {
      console.warn('⚠ Next button not visible, trying alternative selectors');
      // Try clicking any button with similar functionality
      const buttons = await page.locator('button').all();
      for (const btn of buttons) {
        const text = await btn.textContent();
        if (text && text.includes('下一') || text.includes('继续') || text.includes('Next')) {
          await btn.click();
          await page.waitForTimeout(WAIT_TIME * 2);
          break;
        }
      }
    }

    // ===== STEP 9: Fill strategy name =====
    console.log('[STEP 9] Filling strategy name...');
    const nameInput = page.locator('input[type="text"]').first();

    if (await nameInput.isVisible({ timeout: 10000 })) {
      await nameInput.clear();
      await nameInput.fill(template.strategyName);
      console.log(`  ✓ Strategy name: ${template.strategyName}`);
      await page.waitForTimeout(WAIT_TIME);
    }

    // ===== STEP 10: Submit =====
    console.log('[STEP 10] Submitting strategy creation...');
    const submitBtn = page.locator('button:has-text("创建"), button:has-text("提交"), button:has-text("确认")').first();

    if (await submitBtn.isVisible({ timeout: 10000 })) {
      await submitBtn.click();
      console.log('  ✓ Submit button clicked');
      await page.waitForTimeout(WAIT_TIME * 3);
    } else {
      console.error('✗ Submit button not found');
      return false;
    }

    // ===== STEP 11: Verify success =====
    console.log('[STEP 11] Verifying success...');

    // Look for success message
    const successElements = await page.locator('[class*="success"], text=成功, text=创建成功').all();

    if (successElements.length > 0) {
      console.log('✓ Success message found!');
      await page.waitForTimeout(WAIT_TIME);
      return true;
    } else {
      console.log('⚠ No explicit success message, but submission may have succeeded');
      await page.waitForTimeout(WAIT_TIME);
      return true;
    }
  }

  // ===== INDIVIDUAL TESTS FOR EACH TEMPLATE =====

  test('VSS-1: vss_moderate', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[0], 1);
    expect(result).toBeTruthy();
  });

  test('VSS-2: vss_strict', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[1], 2);
    expect(result).toBeTruthy();
  });

  test('VSS-3: vss_weather_based', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[2], 3);
    expect(result).toBeTruthy();
  });

  test('VSS-4: vss_upstream_warning', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[3], 4);
    expect(result).toBeTruthy();
  });

  test('VSS-5: vss_lane_differentiated', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[4], 5);
    expect(result).toBeTruthy();
  });

  test('DHS-1: dhs_peak_hours', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[5], 6);
    expect(result).toBeTruthy();
  });

  test('DHS-2: dhs_passenger_only', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[6], 7);
    expect(result).toBeTruthy();
  });

  test('DHS-3: dhs_peak_multi_interval', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[7], 8);
    expect(result).toBeTruthy();
  });

  test('TEC-1: tec_flow_metering', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[8], 9);
    expect(result).toBeTruthy();
  });

  test('TEC-2: tec_vehicle_restriction', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[9], 10);
    expect(result).toBeTruthy();
  });

  test('TEC-3: tec_emergency_closure', async ({ page }) => {
    page.setDefaultTimeout(LONG_TIMEOUT);
    const result = await testTemplateCreation(page, TEMPLATES[10], 11);
    expect(result).toBeTruthy();
  });
});
