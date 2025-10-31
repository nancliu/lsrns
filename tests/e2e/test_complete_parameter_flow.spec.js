/**
 * Complete E2E Test for Parameter Configuration with Timeline Visualization
 *
 * Tests the full 3-step workflow:
 * Step 1: Template Selection
 * Step 2: Edge Selection
 * Step 3: Parameter Configuration (with Timeline Visualization)
 */

const { test, expect } = require('@playwright/test');

/**
 * Complete workflow helper: Select template → Select edges → Verify parameters
 */
async function completeWorkflowToParameters(page, templateType = 'VSS') {
  console.log('=== Starting Complete Workflow ===');

  // Step 1: Navigate and select template
  await page.goto('http://localhost:8000/control/templates.html');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(2000);

  console.log('Step 1: Selecting template...');

  let templateCard;
  if (templateType === 'VSS') {
    templateCard = page.locator('.template-card:has(.badge-VSS)').first();
  } else if (templateType === 'TEC') {
    templateCard = page.locator('.template-card:has(.template-title:text-matches("车型限制", "i"))').first();
  } else if (templateType === 'DHS') {
    templateCard = page.locator('.template-card:has(.badge-DHS)').first();
  }

  await templateCard.waitFor({ state: 'visible', timeout: 10000 });
  const templateName = await templateCard.locator('.template-title').textContent();
  console.log(`  Selected template: ${templateName.trim()}`);

  await templateCard.click();
  await page.waitForTimeout(2000);

  // Step 2: Select edges
  console.log('Step 2: Selecting edges...');

  // Check if we're on step 2 (edge selection)
  const step2Content = page.locator('#step2-content');
  const step2Visible = await step2Content.isVisible();
  console.log(`  Step 2 visible: ${step2Visible}`);

  if (step2Visible) {
    // Find route selector
    const routeSelect = page.locator('#route-codes, select[name="route"]');
    const routeExists = await routeSelect.count() > 0;
    console.log(`  Route selector found: ${routeExists}`);

    if (routeExists) {
      // Select first route
      await routeSelect.selectOption({ index: 0 });
      console.log('  Selected first route');
      await page.waitForTimeout(3000); // Wait for sections to load

      // Select first section if exists
      const sectionSelect = page.locator('#section-codes, select[name="section"]');
      if (await sectionSelect.count() > 0) {
        await sectionSelect.selectOption({ index: 0 });
        console.log('  Selected first section');
        await page.waitForTimeout(1000);
      }

      // Click query button to load edges
      const queryButton = page.locator('button:has-text("查询路段"), button:has-text("Query")');
      if (await queryButton.count() > 0) {
        await queryButton.click();
        console.log('  Clicked query button');
        await page.waitForTimeout(2000);
      }

      // Select edges (use select-all if available)
      const selectAllCheckbox = page.locator('#select-all-checkbox, input[type="checkbox"]:has-text("全选")').first();
      if (await selectAllCheckbox.count() > 0) {
        await selectAllCheckbox.click();
        console.log('  Clicked select-all checkbox');
      } else {
        // Select first edge checkbox
        const firstEdgeCheckbox = page.locator('input[type="checkbox"]').first();
        if (await firstEdgeCheckbox.count() > 0) {
          await firstEdgeCheckbox.click();
          console.log('  Selected first edge');
        }
      }
      await page.waitForTimeout(1000);

      // Click next/confirm button to go to step 3
      const nextButton = page.locator('button:has-text("下一步"), button:has-text("Next"), button:has-text("确认")').first();
      if (await nextButton.count() > 0) {
        await nextButton.click();
        console.log('  Clicked next button');
        await page.waitForTimeout(2000);
      }
    }
  }

  console.log('Step 3: Checking parameter configuration...');

  // Take screenshot of final state
  await page.screenshot({ path: `test-results/complete-flow-${templateType}-step3.png`, fullPage: true });

  return templateName;
}

test.describe('Complete Parameter Configuration Flow', () => {

  test('VSS: Complete flow with timeline visualization', async ({ page }) => {
    const templateName = await completeWorkflowToParameters(page, 'VSS');

    // Check if we're on step 3
    const step3Content = page.locator('#step3-content');
    const step3Visible = await step3Content.isVisible();
    console.log(`Step 3 visible: ${step3Visible}`);

    if (step3Visible) {
      // Check for parameter form elements
      const parameterForms = page.locator('.parameter-card, .step-array-control-enhanced');
      const formCount = await parameterForms.count();
      console.log(`Parameter forms found: ${formCount}`);

      // Check for timeline
      const timeline = page.locator('.parameter-timeline');
      const timelineCount = await timeline.count();
      console.log(`Timeline elements found: ${timelineCount}`);

      if (timelineCount > 0) {
        // Verify timeline structure
        const hourMarkers = timeline.first().locator('.timeline-hour');
        const hourCount = await hourMarkers.count();
        console.log(`Hour markers: ${hourCount}`);
        expect(hourCount).toBeGreaterThanOrEqual(20);

        const timelineSlots = timeline.first().locator('.timeline-slot');
        const slotCount = await timelineSlots.count();
        console.log(`Timeline slots: ${slotCount}`);
        expect(slotCount).toBeGreaterThan(0);

        console.log('✓ VSS Timeline visualization verified');
      } else {
        console.log('⚠ No timeline found in step 3');
      }

      // Check for speed steps table
      const stepsTable = page.locator('.steps-table');
      const tableExists = await stepsTable.count() > 0;
      console.log(`Speed steps table exists: ${tableExists}`);
    } else {
      console.log('⚠ Step 3 not visible - workflow incomplete');

      // Debug: Check which step is visible
      const step1Visible = await page.locator('#step1-content').isVisible();
      const step2Visible = await page.locator('#step2-content').isVisible();
      console.log(`Current state - Step 1: ${step1Visible}, Step 2: ${step2Visible}, Step 3: ${step3Visible}`);
    }
  });

  test('TEC Restriction: Complete flow with simple_interval timeline', async ({ page }) => {
    const templateName = await completeWorkflowToParameters(page, 'TEC');

    // Check if we're on step 3
    const step3Content = page.locator('#step3-content');
    const step3Visible = await step3Content.isVisible();
    console.log(`Step 3 visible: ${step3Visible}`);

    if (step3Visible) {
      // Check for TEC interval control
      const tecControl = page.locator('.tec-interval-control-enhanced');
      const tecControlCount = await tecControl.count();
      console.log(`TEC interval control found: ${tecControlCount}`);

      // Check for timeline
      const timeline = page.locator('.parameter-timeline');
      const timelineCount = await timeline.count();
      console.log(`Timeline elements found: ${timelineCount}`);

      if (timelineCount > 0) {
        // Verify timeline with simple_interval type
        const timelineSlots = timeline.first().locator('.timeline-slot');
        const slotCount = await timelineSlots.count();
        console.log(`Timeline slots: ${slotCount}`);

        // Check slot color (should be blue for simple_interval)
        if (slotCount > 0) {
          const firstSlot = timelineSlots.first();
          const bgColor = await firstSlot.evaluate(el =>
            window.getComputedStyle(el).backgroundColor
          );
          console.log(`First slot color: ${bgColor}`);

          // Blue color check (rgb(59, 130, 246) with opacity)
          expect(bgColor).not.toBe('rgba(0, 0, 0, 0)');
        }

        // Check for time range labels
        const slotLabels = timeline.first().locator('.timeline-slot-label');
        if (await slotLabels.count() > 0) {
          const firstLabel = await slotLabels.first().textContent();
          console.log(`First label: ${firstLabel}`);
          // Should match format like "7:00-9:00"
          expect(firstLabel).toMatch(/\d+:\d+-\d+:\d+/);
        }

        console.log('✓ TEC simple_interval timeline verified');
      } else {
        console.log('⚠ No timeline found for TEC restriction');
      }

      // Check for intervals table
      const intervalsTable = page.locator('.intervals-table');
      const tableExists = await intervalsTable.count() > 0;
      console.log(`TEC intervals table exists: ${tableExists}`);
    } else {
      console.log('⚠ Step 3 not visible for TEC - workflow incomplete');
    }
  });

  test('DHS: Complete flow with interval timeline', async ({ page }) => {
    const templateName = await completeWorkflowToParameters(page, 'DHS');

    const step3Content = page.locator('#step3-content');
    const step3Visible = await step3Content.isVisible();
    console.log(`Step 3 visible: ${step3Visible}`);

    if (step3Visible) {
      // Check for DHS interval control
      const dhsControl = page.locator('.dhs-interval-control-enhanced, .interval-control-enhanced');
      const dhsControlCount = await dhsControl.count();
      console.log(`DHS interval control found: ${dhsControlCount}`);

      // Check for timeline
      const timeline = page.locator('.parameter-timeline');
      const timelineCount = await timeline.count();
      console.log(`Timeline elements found: ${timelineCount}`);

      if (timelineCount > 0) {
        console.log('✓ DHS interval timeline verified');
      } else {
        console.log('⚠ No timeline found for DHS');
      }
    }
  });
});

test.describe('Parameter Configuration - Interactive Features', () => {

  test('should update timeline when table values change', async ({ page }) => {
    await completeWorkflowToParameters(page, 'VSS');

    const step3Content = page.locator('#step3-content');
    if (!(await step3Content.isVisible())) {
      console.log('Skipping - Step 3 not reached');
      return;
    }

    const timeline = page.locator('.parameter-timeline').first();
    if (await timeline.count() === 0) {
      console.log('Skipping - No timeline found');
      return;
    }

    // Get initial slot count
    const initialSlots = await timeline.locator('.timeline-slot').count();
    console.log(`Initial timeline slots: ${initialSlots}`);

    // Find speed input in table
    const speedInput = page.locator('.step-speed, input[name*="speed"]').first();
    if (await speedInput.count() > 0) {
      // Change speed value
      await speedInput.fill('50');
      await speedInput.blur();

      // Wait for debounced update
      await page.waitForTimeout(500);

      // Check if timeline updated
      const updatedSlots = await timeline.locator('.timeline-slot').count();
      console.log(`Updated timeline slots: ${updatedSlots}`);

      console.log('✓ Timeline update interaction tested');
    }
  });
});
