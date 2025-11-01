/**
 * Playwright E2E Test: Create strategy instances for all 11 templates
 *
 * This test validates that the frontend can successfully create strategy instances
 * for all available control strategy templates:
 * - 5 VSS templates (Variable Speed Signs)
 * - 3 DHS templates (Dynamic Hard Shoulder)
 * - 3 TEC templates (Toll Entrance Control)
 *
 * Tests both simple and complex parameter configurations
 */

const { test, expect } = require('@playwright/test');

// Test data for each template
const templateTestData = {
  vss_moderate: {
    name: 'VSS中等控制 测试策略',
    templateId: 'vss_moderate',
    description: '可变限速 - 中等控制',
    routeFilter: 'G4202',
    stakeRange: { min: 33, max: 44 },
    parameters: {
      speed_steps: [
        { time_hours: 0, speed_kmh: 100 },
        { time_hours: 7, speed_kmh: 60 },
        { time_hours: 10, speed_kmh: 80 },
        { time_hours: 24, speed_kmh: 100 }
      ]
    },
    expectedEdgeCount: { min: 3, max: 20 }
  },
  vss_strict: {
    name: 'VSS严格控制 测试策略',
    templateId: 'vss_strict',
    description: '可变限速 - 严格控制',
    routeFilter: 'G4202',
    stakeRange: { min: 20, max: 30 },
    parameters: {
      speed_steps: [
        { time_hours: 0, speed_kmh: 80 },
        { time_hours: 6, speed_kmh: 50 },
        { time_hours: 10, speed_kmh: 70 },
        { time_hours: 24, speed_kmh: 80 }
      ]
    },
    expectedEdgeCount: { min: 2, max: 20 }
  },
  vss_weather_based: {
    name: 'VSS天气应急 测试策略',
    templateId: 'vss_weather_based',
    description: '可变限速 - 天气应急',
    routeFilter: 'G4202',
    stakeRange: { min: 40, max: 50 },
    parameters: {
      speed_steps: [
        { time_hours: 0, speed_kmh: 100 },
        { time_hours: 6, speed_kmh: 80 },
        { time_hours: 7, speed_kmh: 70 },
        { time_hours: 8, speed_kmh: 60 },
        { time_hours: 9, speed_kmh: 50 },
        { time_hours: 10, speed_kmh: 40 },
        { time_hours: 24, speed_kmh: 100 }
      ]
    },
    expectedEdgeCount: { min: 3, max: 25 }
  },
  vss_upstream_warning: {
    name: 'VSS上游预警 测试策略',
    templateId: 'vss_upstream_warning',
    description: '可变限速 - 上游预警',
    routeFilter: 'G5',
    stakeRange: { min: 1700, max: 1800 },
    parameters: {
      speed_steps: [
        { time_hours: 0, speed_kmh: 120 },
        { time_hours: 7, speed_kmh: 100 },
        { time_hours: 10, speed_kmh: 80 },
        { time_hours: 24, speed_kmh: 120 }
      ]
    },
    expectedEdgeCount: { min: 3, max: 25 }
  },
  vss_lane_differentiated: {
    name: 'VSS分车道控制 测试策略',
    templateId: 'vss_lane_differentiated',
    description: '可变限速 - 分车道控制',
    routeFilter: 'G4202',
    stakeRange: { min: 15, max: 25 },
    parameters: {
      speed_steps: [
        { time_hours: 0, speed_kmh: 100 },
        { time_hours: 7, speed_kmh: 70 },
        { time_hours: 10, speed_kmh: 90 },
        { time_hours: 24, speed_kmh: 100 }
      ]
    },
    expectedEdgeCount: { min: 2, max: 20 }
  },
  dhs_peak_hours: {
    name: 'DHS高峰时段 测试策略',
    templateId: 'dhs_peak_hours',
    description: '应急车道开放',
    routeFilter: 'G4202',
    stakeRange: { min: 33, max: 44 },
    minLanes: 4,
    routeDirection: 'counterclockwise',
    parameters: {
      hard_shoulder_lane_index: 0,
      intervals: [
        { begin_hours: 0, end_hours: 7, status: 'CLOSED', allowed_vehicle_types: [] },
        { begin_hours: 7, end_hours: 10, status: 'OPEN', allowed_vehicle_types: ['passenger', 'truck'] },
        { begin_hours: 10, end_hours: 16, status: 'CLOSED', allowed_vehicle_types: [] },
        { begin_hours: 16, end_hours: 19, status: 'OPEN', allowed_vehicle_types: ['passenger', 'truck'] },
        { begin_hours: 19, end_hours: 24, status: 'CLOSED', allowed_vehicle_types: [] }
      ]
    },
    expectedEdgeCount: { min: 2, max: 10 }
  },
  dhs_passenger_only: {
    name: 'DHS仅客车 测试策略',
    templateId: 'dhs_passenger_only',
    description: '应急车道 - 仅客车',
    routeFilter: 'G4202',
    stakeRange: { min: 25, max: 35 },
    minLanes: 4,
    parameters: {
      hard_shoulder_lane_index: 0,
      intervals: [
        { begin_hours: 0, end_hours: 8, status: 'CLOSED', allowed_vehicle_types: [] },
        { begin_hours: 8, end_hours: 11, status: 'OPEN', allowed_vehicle_types: ['passenger'] },
        { begin_hours: 11, end_hours: 15, status: 'CLOSED', allowed_vehicle_types: [] },
        { begin_hours: 15, end_hours: 18, status: 'OPEN', allowed_vehicle_types: ['passenger'] },
        { begin_hours: 18, end_hours: 24, status: 'CLOSED', allowed_vehicle_types: [] }
      ]
    },
    expectedEdgeCount: { min: 2, max: 10 }
  },
  dhs_peak_multi_interval: {
    name: 'DHS多时段管理 测试策略',
    templateId: 'dhs_peak_multi_interval',
    description: '应急车道 - 多时段管理',
    routeFilter: 'G4202',
    stakeRange: { min: 40, max: 50 },
    minLanes: 4,
    parameters: {
      hard_shoulder_lane_index: 0,
      intervals: [
        { begin_hours: 0, end_hours: 6, status: 'CLOSED', allowed_vehicle_types: [] },
        { begin_hours: 6, end_hours: 8, status: 'OPEN', allowed_vehicle_types: ['passenger', 'truck'] },
        { begin_hours: 8, end_hours: 11, status: 'OPEN', allowed_vehicle_types: ['passenger'] },
        { begin_hours: 11, end_hours: 14, status: 'CLOSED', allowed_vehicle_types: [] },
        { begin_hours: 14, end_hours: 18, status: 'OPEN', allowed_vehicle_types: ['passenger', 'truck'] },
        { begin_hours: 18, end_hours: 24, status: 'CLOSED', allowed_vehicle_types: [] }
      ]
    },
    expectedEdgeCount: { min: 2, max: 10 }
  },
  tec_flow_metering: {
    name: 'TEC流量控制 测试策略',
    templateId: 'tec_flow_metering',
    description: '收费入口 - 流量控制',
    routeFilter: 'G5',
    nodeTypes: 'entrance',
    parameters: {
      position: 0,
      flow_intervals: [
        { begin_hours: 0, end_hours: 6, vehsPerHour: 300, target_speed: 15 },
        { begin_hours: 6, end_hours: 10, vehsPerHour: 150, target_speed: 8 },
        { begin_hours: 10, end_hours: 16, vehsPerHour: 250, target_speed: 12 },
        { begin_hours: 16, end_hours: 20, vehsPerHour: 160, target_speed: 8 },
        { begin_hours: 20, end_hours: 24, vehsPerHour: 300, target_speed: 15 }
      ]
    },
    expectedEdgeCount: { min: 1, max: 5 }
  },
  tec_vehicle_restriction: {
    name: 'TEC车型限制 测试策略',
    templateId: 'tec_vehicle_restriction',
    description: '收费入口 - 车型限制',
    routeFilter: 'G5',
    nodeTypes: 'entrance',
    parameters: {
      disallow_vehicle_types: ['truck']
    },
    expectedEdgeCount: { min: 1, max: 5 }
  },
  tec_emergency_closure: {
    name: 'TEC紧急关闭 测试策略',
    templateId: 'tec_emergency_closure',
    description: '收费入口 - 紧急关闭',
    routeFilter: 'G5',
    nodeTypes: 'entrance',
    parameters: {
      closure_duration_hours: 4
    },
    expectedEdgeCount: { min: 1, max: 5 }
  }
};

test.describe('All Templates Strategy Creation - Frontend E2E Tests', () => {
  test.beforeEach(async ({ page, context }) => {
    // Set a longer timeout for page loads
    page.setDefaultTimeout(30000);
    context.clearCookies();
  });

  /**
   * Helper function to navigate to the control strategies page
   */
  async function navigateToStrategiesPage(page) {
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });

    // Look for control strategies link or navigate directly
    const strategiesLink = page.locator('a:has-text("控制策略"), a[href*="control"]');
    if (await strategiesLink.isVisible()) {
      await strategiesLink.click();
    } else {
      // Direct navigation
      await page.goto('http://localhost:8000/index.html?tab=control', { waitUntil: 'networkidle' });
    }

    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  }

  /**
   * Helper function to select edge filter and get edges
   */
  async function selectEdges(page, testData) {
    // Click on edge selector
    const edgeSelectorBtn = page.locator('button:has-text("选择路段"), button:has-text("受影响路段")').first();
    if (await edgeSelectorBtn.isVisible()) {
      await edgeSelectorBtn.click();
      await page.waitForTimeout(500);
    }

    // Apply filters if provided
    if (testData.routeFilter) {
      const routeInput = page.locator('input[placeholder*="路线"], input[name*="route"]').first();
      if (await routeInput.isVisible()) {
        await routeInput.fill(testData.routeFilter);
      }
    }

    if (testData.stakeRange) {
      const minStakeInput = page.locator('input[placeholder*="最小"], input[name*="min"]').first();
      const maxStakeInput = page.locator('input[placeholder*="最大"], input[name*="max"]').first();

      if (await minStakeInput.isVisible()) {
        await minStakeInput.fill(testData.stakeRange.min.toString());
      }
      if (await maxStakeInput.isVisible()) {
        await maxStakeInput.fill(testData.stakeRange.max.toString());
      }
    }

    if (testData.minLanes) {
      const lanesInput = page.locator('input[placeholder*="车道"], input[name*="lanes"]').first();
      if (await lanesInput.isVisible()) {
        await lanesInput.fill(testData.minLanes.toString());
      }
    }

    if (testData.routeDirection) {
      const directionSelect = page.locator('select[name*="direction"], button:has-text("逆时针")').first();
      if (await directionSelect.isVisible()) {
        await directionSelect.selectOption(testData.routeDirection);
      }
    }

    // Search/Apply filters
    const searchBtn = page.locator('button:has-text("查询"), button:has-text("搜索"), button:has-text("应用")').first();
    if (await searchBtn.isVisible()) {
      await searchBtn.click();
      await page.waitForTimeout(2000);
    }

    // Select edges (click checkboxes or the "select all" checkbox)
    const edgeCheckboxes = page.locator('input[type="checkbox"][name*="edge"], td > input[type="checkbox"]');
    const checkboxCount = await edgeCheckboxes.count();

    if (checkboxCount > 0) {
      // Select the appropriate number of edges based on template type
      const edgesToSelect = Math.min(checkboxCount, testData.expectedEdgeCount?.max || 5);
      for (let i = 0; i < edgesToSelect && i < 5; i++) {
        await edgeCheckboxes.nth(i).check();
      }
      console.log(`Selected ${edgesToSelect} edges`);
    }

    // Confirm selection
    const confirmBtn = page.locator('button:has-text("确认"), button:has-text("完成")').first();
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click();
      await page.waitForTimeout(500);
    }
  }

  /**
   * Helper function to fill in strategy parameters
   */
  async function fillParameters(page, templateId, parameters) {
    // VSS templates - fill speed steps
    if (templateId.startsWith('vss')) {
      const speedStepsTable = page.locator('table:has-text("时间"), tbody');
      if (await speedStepsTable.isVisible()) {
        const rows = page.locator('tr');
        for (let i = 0; i < Math.min(parameters.speed_steps.length, 10); i++) {
          const step = parameters.speed_steps[i];

          const timeInput = rows.nth(i).locator('input[placeholder*="时间"], input:first-of-type');
          const speedInput = rows.nth(i).locator('input[placeholder*="速度"], input:last-of-type');

          if (await timeInput.isVisible()) {
            await timeInput.fill(step.time_hours.toString());
          }
          if (await speedInput.isVisible()) {
            await speedInput.fill(step.speed_kmh.toString());
          }
        }
      }
    }

    // DHS templates - fill intervals
    if (templateId.startsWith('dhs')) {
      // Set hard shoulder lane index
      if (parameters.hard_shoulder_lane_index !== undefined) {
        const laneInput = page.locator('input[name*="lane"], input[placeholder*="车道"]').first();
        if (await laneInput.isVisible()) {
          await laneInput.fill(parameters.hard_shoulder_lane_index.toString());
        }
      }

      // Fill intervals
      const intervalRows = page.locator('tbody tr');
      for (let i = 0; i < Math.min(parameters.intervals.length, 10); i++) {
        const interval = parameters.intervals[i];
        const row = intervalRows.nth(i);

        // Fill begin hours
        const beginInput = row.locator('input[type="number"]').nth(0);
        // Fill end hours
        const endInput = row.locator('input[type="number"]').nth(1);
        // Select status
        const statusSelect = row.locator('select').first();

        if (await beginInput.isVisible()) {
          await beginInput.fill(interval.begin_hours.toString());
        }
        if (await endInput.isVisible()) {
          await endInput.fill(interval.end_hours.toString());
        }
        if (await statusSelect.isVisible()) {
          await statusSelect.selectOption(interval.status);
        }

        // Check vehicle type checkboxes
        if (interval.allowed_vehicle_types && interval.allowed_vehicle_types.length > 0) {
          for (const vehicleType of interval.allowed_vehicle_types) {
            const checkbox = row.locator(`input[value="${vehicleType}"]`);
            if (await checkbox.isVisible()) {
              await checkbox.check();
            }
          }
        }
      }
    }

    // TEC templates - fill flow intervals
    if (templateId.startsWith('tec')) {
      // Fill flow intervals if present
      if (parameters.flow_intervals) {
        const intervalRows = page.locator('tbody tr');
        for (let i = 0; i < Math.min(parameters.flow_intervals.length, 10); i++) {
          const interval = parameters.flow_intervals[i];
          const row = intervalRows.nth(i);

          const inputs = row.locator('input[type="number"]');
          // begin_hours
          if ((await inputs.count()) > 0) await inputs.nth(0).fill(interval.begin_hours.toString());
          // end_hours
          if ((await inputs.count()) > 1) await inputs.nth(1).fill(interval.end_hours.toString());
          // vehsPerHour
          if ((await inputs.count()) > 2) await inputs.nth(2).fill(interval.vehsPerHour.toString());
          // target_speed
          if ((await inputs.count()) > 3) await inputs.nth(3).fill(interval.target_speed.toString());
        }
      }

      // Handle vehicle restrictions
      if (parameters.disallow_vehicle_types) {
        for (const vehicleType of parameters.disallow_vehicle_types) {
          const checkbox = page.locator(`input[value="${vehicleType}"]`);
          if (await checkbox.isVisible()) {
            await checkbox.check();
          }
        }
      }
    }
  }

  /**
   * Helper function to submit strategy creation form
   */
  async function submitStrategy(page, strategyName) {
    // Fill strategy name if there's an input
    const nameInput = page.locator('input[placeholder*="策略名称"], input[name*="name"], input#strategy-name').first();
    if (await nameInput.isVisible()) {
      await nameInput.clear();
      await nameInput.fill(strategyName);
    }

    // Submit the form
    const submitBtn = page.locator('button:has-text("创建"), button:has-text("提交"), button:has-text("确认")').first();
    expect(await submitBtn.isVisible()).toBeTruthy();
    await submitBtn.click();

    // Wait for success message
    const successMsg = page.locator('text=创建成功, text=成功, .success, .alert-success').first();
    await expect(successMsg).toBeVisible({ timeout: 10000 });

    console.log(`✅ Strategy "${strategyName}" created successfully`);
  }

  // Test: VSS Moderate
  test('Template: VSS Moderate - 可变限速 (中等控制)', async ({ page }) => {
    const testData = templateTestData.vss_moderate;

    await navigateToStrategiesPage(page);

    // Select template
    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('vss_moderate');
    } else {
      const templateBtn = page.locator('button:has-text("vss_moderate"), button:has-text("中等控制")').first();
      await templateBtn.click();
    }

    await page.waitForTimeout(500);

    // Select edges
    await selectEdges(page, testData);

    // Fill parameters
    await fillParameters(page, 'vss_moderate', testData.parameters);

    // Submit
    await submitStrategy(page, testData.name);
  });

  // Test: VSS Strict
  test('Template: VSS Strict - 可变限速 (严格控制)', async ({ page }) => {
    const testData = templateTestData.vss_strict;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('vss_strict');
    } else {
      const templateBtn = page.locator('button:has-text("vss_strict"), button:has-text("严格控制")').first();
      await templateBtn.click();
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'vss_strict', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: VSS Weather Based
  test('Template: VSS Weather Based - 可变限速 (天气应急)', async ({ page }) => {
    const testData = templateTestData.vss_weather_based;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('vss_weather_based');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'vss_weather_based', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: VSS Upstream Warning
  test('Template: VSS Upstream Warning - 可变限速 (上游预警)', async ({ page }) => {
    const testData = templateTestData.vss_upstream_warning;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('vss_upstream_warning');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'vss_upstream_warning', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: VSS Lane Differentiated
  test('Template: VSS Lane Differentiated - 可变限速 (分车道控制)', async ({ page }) => {
    const testData = templateTestData.vss_lane_differentiated;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('vss_lane_differentiated');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'vss_lane_differentiated', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: DHS Peak Hours
  test('Template: DHS Peak Hours - 应急车道 (高峰时段)', async ({ page }) => {
    const testData = templateTestData.dhs_peak_hours;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('dhs_peak_hours');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'dhs_peak_hours', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: DHS Passenger Only
  test('Template: DHS Passenger Only - 应急车道 (仅客车)', async ({ page }) => {
    const testData = templateTestData.dhs_passenger_only;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('dhs_passenger_only');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'dhs_passenger_only', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: DHS Peak Multi Interval
  test('Template: DHS Peak Multi Interval - 应急车道 (多时段管理)', async ({ page }) => {
    const testData = templateTestData.dhs_peak_multi_interval;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('dhs_peak_multi_interval');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'dhs_peak_multi_interval', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: TEC Flow Metering
  test('Template: TEC Flow Metering - 收费入口 (流量控制)', async ({ page }) => {
    const testData = templateTestData.tec_flow_metering;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('tec_flow_metering');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'tec_flow_metering', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: TEC Vehicle Restriction
  test('Template: TEC Vehicle Restriction - 收费入口 (车型限制)', async ({ page }) => {
    const testData = templateTestData.tec_vehicle_restriction;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('tec_vehicle_restriction');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'tec_vehicle_restriction', testData.parameters);
    await submitStrategy(page, testData.name);
  });

  // Test: TEC Emergency Closure
  test('Template: TEC Emergency Closure - 收费入口 (紧急关闭)', async ({ page }) => {
    const testData = templateTestData.tec_emergency_closure;

    await navigateToStrategiesPage(page);

    const templateSelect = page.locator('select[name*="template"]').first();
    if (await templateSelect.isVisible()) {
      await templateSelect.selectOption('tec_emergency_closure');
    }

    await page.waitForTimeout(500);
    await selectEdges(page, testData);
    await fillParameters(page, 'tec_emergency_closure', testData.parameters);
    await submitStrategy(page, testData.name);
  });
});
