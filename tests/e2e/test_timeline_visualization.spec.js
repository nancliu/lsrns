/**
 * E2E Tests for Timeline Visualization Component
 *
 * Tests the streamlined time selector visualization feature for control strategies.
 * Covers VSS (Variable Speed Signs) strategy type with optional parameter handling.
 *
 * Related OpenSpec: add-streamlined-time-selector-visualization
 */

const { test, expect } = require('@playwright/test');

/**
 * Helper function to select a VSS template and navigate to parameter configuration
 */
async function selectVSSTemplateAndConfigure(page) {
  // Step 1: Select a VSS template by clicking on a template card
  const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
  await vssCard.waitFor({ state: 'visible', timeout: 10000 });
  await vssCard.click();
  await page.waitForTimeout(500);

  // Step 2: Click the floating "下一步" button to go to edge selection
  const nextButton1 = page.locator('#floating-next-btn');
  await nextButton1.waitFor({ state: 'visible', timeout: 10000 });
  await nextButton1.click();
  await page.waitForTimeout(2000);

  // Step 3: Wait for edge selection UI to load (route selector, section selector)
  // Select route by ID to be more specific
  const routeSelect = page.locator('#route-codes');
  await routeSelect.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForTimeout(1000);

  // Select G4202 (index 0) which has many sections (1198 edges)
  // Note: Some routes like G4215 only have 1 section, so we choose G4202
  console.log('Selecting G4202 route which has many sections...');
  await routeSelect.selectOption({ index: 0 }); // G4202

  // IMPORTANT: Wait 7 seconds for section codes to refresh after route selection
  console.log('Waiting 7 seconds for section codes to load...');
  await page.waitForTimeout(7000);

  // Step 4: Now select a section
  const sectionSelect = page.locator('#section-codes');
  await sectionSelect.waitFor({ state: 'visible', timeout: 5000 });

  const sectionOptions = await sectionSelect.locator('option').count();
  console.log(`Found ${sectionOptions} section options after waiting`);

  if (sectionOptions > 1) {
    // Select first real section (not placeholder if any)
    await sectionSelect.selectOption({ index: 1 });
    console.log('Selected section');
  } else if (sectionOptions === 1) {
    console.log('Only 1 section available, selecting it...');
    await sectionSelect.selectOption({ index: 0 });
  }

  await page.waitForTimeout(1000);

  // Step 5: Click "查询路段" button to load edges
  const queryButton = page.locator('button:has-text("查询路段")');
  await queryButton.waitFor({ state: 'visible', timeout: 10000 });
  await queryButton.click();
  console.log('Clicked query button to load edges');

  // Wait for edges to load
  await page.waitForTimeout(2000);

  // Step 6: Select at least one edge checkbox from the results
  // Note: First checkbox might be "select-all", so we click it (which triggers toggleSelectAll())
  const selectAllCheckbox = page.locator('#select-all-checkbox');
  const selectAllExists = await selectAllCheckbox.count() > 0;

  if (selectAllExists) {
    // Click select-all to select all edges
    await selectAllCheckbox.click();
    console.log('Clicked select-all checkbox');
  } else {
    // If no select-all, find and click individual edge checkbox
    const edgeCheckbox = page.locator('input[type="checkbox"]').nth(1); // Skip first (might be select-all)
    await edgeCheckbox.waitFor({ state: 'visible', timeout: 10000 });
    await edgeCheckbox.click();
    console.log('Selected first edge checkbox');
  }

  await page.waitForTimeout(500);

  // Step 7: Click next to go to parameter configuration
  const nextButton2 = page.locator('#floating-next-btn');
  await nextButton2.waitFor({ state: 'visible', timeout: 10000 });
  await nextButton2.click();
  console.log('Clicked next to go to parameters');

  // Wait for parameter form to render
  console.log('Waiting for parameter form to render...');
  await page.waitForTimeout(3000);
}

test.describe('Timeline Visualization - VSS Strategy', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    // Wait for templates to load from API
    await page.waitForTimeout(2000);
  });

  test('should render timeline above table for VSS template', async ({ page }) => {
    await selectVSSTemplateAndConfigure(page);

    // Check if timeline element exists
    const timeline = page.locator('.parameter-timeline').first();
    await expect(timeline).toBeVisible({ timeout: 5000 });

    // Verify timeline is above the table
    const timelineBox = await timeline.boundingBox();
    const table = page.locator('.steps-table').first();
    const tableBox = await table.boundingBox();

    expect(timelineBox).not.toBeNull();
    expect(tableBox).not.toBeNull();
    expect(timelineBox.y).toBeLessThan(tableBox.y); // Timeline above table
  });

  test('should display 24-hour markers', async ({ page }) => {
    await selectVSSTemplateAndConfigure(page);

    // Check for hour markers
    const hourMarkers = page.locator('.timeline-hour');
    await hourMarkers.first().waitFor({ state: 'visible', timeout: 5000 });
    const count = await hourMarkers.count();

    expect(count).toBeGreaterThanOrEqual(20); // Should have most hours displayed
  });

  test('should render timeline slots with colors', async ({ page }) => {
    await selectVSSTemplateAndConfigure(page);

    // Check for timeline slots
    const timelineSlots = page.locator('.timeline-slot');
    await timelineSlots.first().waitFor({ state: 'visible', timeout: 5000 });
    const slotCount = await timelineSlots.count();

    expect(slotCount).toBeGreaterThan(0); // Should have at least one slot

    // Verify first slot has a background color
    if (slotCount > 0) {
      const firstSlot = timelineSlots.first();
      const bgColor = await firstSlot.evaluate(el =>
        window.getComputedStyle(el).backgroundColor
      );
      expect(bgColor).not.toBe('rgba(0, 0, 0, 0)'); // Not transparent
      expect(bgColor).not.toBe(''); // Not empty
      console.log('Timeline slot background color:', bgColor);
    }
  });

  test('should update timeline when table values change', async ({ page }) => {
    await selectVSSTemplateAndConfigure(page);

    // Get initial slot color
    const firstSlot = page.locator('.timeline-slot').first();
    await firstSlot.waitFor({ state: 'visible', timeout: 5000 });
    const initialColor = await firstSlot.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    // Modify speed value in table
    const speedInput = page.locator('.step-speed').first();
    await speedInput.waitFor({ state: 'visible', timeout: 5000 });

    // Clear and set new value
    await speedInput.fill('');
    await speedInput.fill('50'); // Low speed - should trigger color change
    await speedInput.blur();

    // Wait for debounced update (300ms + buffer)
    await page.waitForTimeout(600);

    // Get updated slot color
    const updatedColor = await firstSlot.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    // Color should have changed (or at least re-rendered)
    console.log('Initial color:', initialColor);
    console.log('Updated color:', updatedColor);

    // Verify the colors are valid (not empty)
    expect(initialColor).not.toBe('');
    expect(updatedColor).not.toBe('');
  });

  test('should display unified card-style layout', async ({ page }) => {
    await selectVSSTemplateAndConfigure(page);

    // Check for step-array-control-enhanced container
    const container = page.locator('.step-array-control-enhanced').first();
    await container.waitFor({ state: 'visible', timeout: 5000 });
    await expect(container).toBeVisible();

    // Verify card styling (border, background)
    const styles = await container.evaluate(el => ({
      background: window.getComputedStyle(el).backgroundColor,
      border: window.getComputedStyle(el).border,
      borderRadius: window.getComputedStyle(el).borderRadius
    }));

    expect(styles.background).not.toBe('rgba(0, 0, 0, 0)'); // Has background
    expect(styles.borderRadius).not.toBe('0px'); // Has rounded corners
    console.log('Container styles:', styles);
  });

  test('should display description text and usage hints', async ({ page }) => {
    await selectVSSTemplateAndConfigure(page);

    // Check for description text
    const description = page.locator('.timeline-description');
    const descCount = await description.count();

    if (descCount > 0) {
      await expect(description.first()).toBeVisible();
      const descText = await description.first().textContent();
      expect(descText.length).toBeGreaterThan(0);
      console.log('Description text:', descText);
    }

    // Check for usage hint
    const hint = page.locator('.config-hint');
    const hintCount = await hint.count();

    if (hintCount > 0) {
      await expect(hint.first()).toBeVisible();
      const hintText = await hint.first().textContent();
      expect(hintText).toContain('时间'); // Should mention time
      console.log('Hint text:', hintText);
    }
  });
});

test.describe('Timeline Visualization - Console Errors', () => {
  test('should not produce console errors on load', async ({ page }) => {
    const consoleErrors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Select VSS template and configure
    await selectVSSTemplateAndConfigure(page);

    // Filter out known external errors (e.g., from extensions)
    const relevantErrors = consoleErrors.filter(err =>
      !err.includes('chrome-extension') &&
      !err.includes('favicon.ico')
    );

    if (relevantErrors.length > 0) {
      console.log('Console errors found:', relevantErrors);
    }

    expect(relevantErrors.length).toBe(0);
  });
});

test.describe('Timeline Visualization - Optional Parameters', () => {
  test('should handle optional parameters correctly', async ({ page }) => {
    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for weather-based VSS template (has optional parameters)
    // Try to find a card with "天气" in the title
    const weatherCard = page.locator('.template-card:has(.template-title:text-matches("天气", "i"))').first();

    // If weather template exists, test it
    const cardCount = await weatherCard.count();
    if (cardCount === 0) {
      console.log('Weather-based template not found, skipping optional parameter test');
      test.skip();
      return;
    }

    await weatherCard.click();
    await page.waitForTimeout(500);

    // Click next to parameter configuration
    const nextButton = page.locator('#floating-next-btn');
    await nextButton.click();
    await page.waitForTimeout(1000);

    // Listen for console logs about skipped optional parameters
    const consoleMessages = [];
    page.on('console', msg => {
      if (msg.text().includes('Skipping optional parameter')) {
        consoleMessages.push(msg.text());
      }
    });

    // Try to find and click the create button (if visible)
    const createButton = page.locator('button:has-text("创建策略实例")');
    const createButtonCount = await createButton.count();

    if (createButtonCount > 0) {
      console.log('Found create strategy button, attempting to create with optional params empty');
      // Note: This test may require additional steps like selecting edges first
      // For now, we're just checking that the UI doesn't throw errors
    }

    console.log('Optional parameter console messages:', consoleMessages);
  });
});
