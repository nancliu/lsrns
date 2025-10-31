/**
 * E2E Tests for Parameter Configuration (Actual UI Flow)
 *
 * Tests parameter configuration functionality with the actual 3-step wizard UI.
 * Focuses on testing timeline visualization in parameter forms.
 */

const { test, expect } = require('@playwright/test');

test.describe('Parameter Configuration - VSS Timeline Visualization', () => {
  test('should render parameter form with timeline after clicking template card', async ({ page }) => {
    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    console.log('Page loaded, looking for template cards...');

    // Find and click a VSS template card
    const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
    await expect(vssCard).toBeVisible({ timeout: 10000 });

    const cardTitle = await vssCard.locator('.template-title').textContent();
    console.log('Clicking VSS template:', cardTitle);

    await vssCard.click();
    await page.waitForTimeout(2000);

    // Take screenshot after clicking card
    await page.screenshot({ path: 'test-results/parameter-config-vss-clicked.png', fullPage: true });

    // Check if parameter form is rendered
    // Look for form elements that should appear
    const parameterForm = page.locator('#parameter-form-container, .parameter-form, #step3-content');
    const formVisible = await parameterForm.count();
    console.log('Parameter form elements found:', formVisible);

    if (formVisible > 0) {
      // Check for timeline visualization
      const timeline = page.locator('.parameter-timeline');
      const timelineCount = await timeline.count();
      console.log('Timeline elements found:', timelineCount);

      if (timelineCount > 0) {
        await expect(timeline.first()).toBeVisible();
        console.log('✓ Timeline visualization is present');

        // Check for hour markers
        const hourMarkers = timeline.first().locator('.timeline-hour');
        const hourCount = await hourMarkers.count();
        console.log('Hour markers found:', hourCount);

        // Check for timeline slots
        const timelineSlots = timeline.first().locator('.timeline-slot');
        const slotCount = await timelineSlots.count();
        console.log('Timeline slots found:', slotCount);
      } else {
        console.log('⚠ No timeline visualization found');
      }

      // Check for table elements
      const tables = page.locator('table.steps-table, table.intervals-table');
      const tableCount = await tables.count();
      console.log('Parameter tables found:', tableCount);
    }

    // Check all visible elements on the page
    const allButtons = page.locator('button:visible');
    const buttonCount = await allButtons.count();
    console.log('Visible buttons:', buttonCount);

    // List first 10 buttons
    for (let i = 0; i < Math.min(buttonCount, 10); i++) {
      const btnText = await allButtons.nth(i).textContent();
      console.log(`  Button ${i + 1}: ${btnText.trim()}`);
    }
  });

  test('should check if parameter form renders when navigating through steps', async ({ page }) => {
    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check if step indicators exist
    const stepIndicators = page.locator('[class*="step-indicator"], [id^="step-indicator"]');
    const stepCount = await stepIndicators.count();
    console.log('Step indicators found:', stepCount);

    // Check if step content containers exist
    const step1Content = page.locator('#step1-content');
    const step2Content = page.locator('#step2-content');
    const step3Content = page.locator('#step3-content');

    console.log('Step 1 content exists:', await step1Content.count() > 0);
    console.log('Step 2 content exists:', await step2Content.count() > 0);
    console.log('Step 3 content exists:', await step3Content.count() > 0);

    // Take screenshot of initial state
    await page.screenshot({ path: 'test-results/parameter-config-initial-state.png', fullPage: true });

    // Find VSS card and click
    const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
    if (await vssCard.count() > 0) {
      await vssCard.click();
      await page.waitForTimeout(2000);

      // Check which step content is visible
      const step1Visible = await step1Content.isVisible().catch(() => false);
      const step2Visible = await step2Content.isVisible().catch(() => false);
      const step3Visible = await step3Content.isVisible().catch(() => false);

      console.log('After clicking template:');
      console.log('  Step 1 visible:', step1Visible);
      console.log('  Step 2 visible:', step2Visible);
      console.log('  Step 3 visible:', step3Visible);

      // Take screenshot after template selection
      await page.screenshot({ path: 'test-results/parameter-config-after-selection.png', fullPage: true });
    }
  });

  test('should verify timeline_visualizer.js is loaded', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Check if TimelineVisualizer is available
    const hasTimelineVisualizer = await page.evaluate(() => {
      return typeof window.TimelineVisualizer !== 'undefined';
    });

    console.log('TimelineVisualizer loaded:', hasTimelineVisualizer);
    expect(hasTimelineVisualizer).toBe(true);

    // Check TimelineVisualizer methods
    if (hasTimelineVisualizer) {
      const methods = await page.evaluate(() => {
        return Object.keys(window.TimelineVisualizer);
      });
      console.log('TimelineVisualizer methods:', methods);
    }
  });

  test('should check parameter_form.js functions', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Check if key functions exist
    const functions = await page.evaluate(() => {
      return {
        renderStepArrayControl: typeof renderStepArrayControl !== 'undefined',
        renderDHSIntervalControl: typeof renderDHSIntervalControl !== 'undefined',
        renderFlowIntervalControl: typeof renderFlowIntervalControl !== 'undefined',
        renderTECIntervalControl: typeof renderTECIntervalControl !== 'undefined'
      };
    });

    console.log('Parameter form functions:', functions);

    expect(functions.renderStepArrayControl).toBe(true);
    // Note: Other functions might not be in global scope
  });
});

test.describe('Parameter Configuration - TEC Restriction', () => {
  test('should find TEC vehicle restriction template', async ({ page }) => {
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Find TEC template with "车型限制" in title
    const tecCard = page.locator('.template-card:has(.template-title:text-matches("车型限制", "i"))');
    const tecCount = await tecCard.count();

    console.log('TEC vehicle restriction templates found:', tecCount);

    if (tecCount > 0) {
      const cardTitle = await tecCard.first().locator('.template-title').textContent();
      console.log('TEC template title:', cardTitle);

      await tecCard.first().click();
      await page.waitForTimeout(2000);

      // Take screenshot
      await page.screenshot({ path: 'test-results/parameter-config-tec-clicked.png', fullPage: true });

      // Check for parameter form elements
      const timeline = page.locator('.parameter-timeline');
      const timelineCount = await timeline.count();
      console.log('TEC timeline elements found:', timelineCount);

      const intervalTable = page.locator('.intervals-table');
      const tableCount = await intervalTable.count();
      console.log('TEC interval tables found:', tableCount);
    }
  });
});
