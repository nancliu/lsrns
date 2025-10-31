/**
 * E2E Tests for TEC Vehicle Restriction Timeline Visualization
 *
 * Tests the timeline visualization for tec_interval_array parameter type.
 * This test validates the fix for the missing renderTECIntervalControl() function.
 *
 * Related OpenSpec: add-streamlined-time-selector-visualization (Phase 1.5)
 * Template: tec_vehicle_restriction.json
 */

const { test, expect } = require('@playwright/test');

/**
 * Helper function to select TEC vehicle restriction template and navigate to parameter configuration
 */
async function selectTECRestrictionTemplateAndConfigure(page) {
  // Step 1: Find and click TEC vehicle restriction template card
  // The template name is "收费入口 - 车型限制"
  const tecCard = page.locator('.template-card:has(.template-title:text-matches("车型限制", "i"))').first();
  await tecCard.waitFor({ state: 'visible', timeout: 10000 });
  await tecCard.click();
  await page.waitForTimeout(500);

  // Step 2: Click "下一步" to go to edge selection
  const nextButton1 = page.locator('#floating-next-btn');
  await nextButton1.waitFor({ state: 'visible', timeout: 10000 });
  await nextButton1.click();
  await page.waitForTimeout(2000);

  // Step 3: Select a route for edge selection
  const routeSelect = page.locator('#route-codes');
  await routeSelect.waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForTimeout(1000);

  // Select G4202 (has many sections)
  console.log('Selecting G4202 route...');
  await routeSelect.selectOption({ index: 0 }); // G4202

  // Wait for section codes to load
  console.log('Waiting 7 seconds for section codes to load...');
  await page.waitForTimeout(7000);

  // Step 4: Select a section
  const sectionSelect = page.locator('#section-codes');
  await sectionSelect.waitFor({ state: 'visible', timeout: 5000 });

  const sectionOptions = await sectionSelect.locator('option').count();
  console.log(`Found ${sectionOptions} section options`);

  if (sectionOptions > 1) {
    await sectionSelect.selectOption({ index: 1 });
    console.log('Selected section');
  } else if (sectionOptions === 1) {
    console.log('Only 1 section available, selecting it...');
    await sectionSelect.selectOption({ index: 0 });
  }

  await page.waitForTimeout(1000);

  // Step 5: Click "查询路段" to load edges
  const queryButton = page.locator('button:has-text("查询路段")');
  await queryButton.waitFor({ state: 'visible', timeout: 10000 });
  await queryButton.click();
  console.log('Clicked query button to load edges');

  await page.waitForTimeout(2000);

  // Step 6: Select edges
  const selectAllCheckbox = page.locator('#select-all-checkbox');
  const selectAllExists = await selectAllCheckbox.count() > 0;

  if (selectAllExists) {
    await selectAllCheckbox.click();
    console.log('Clicked select-all checkbox');
  } else {
    const edgeCheckbox = page.locator('input[type="checkbox"]').nth(1);
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

test.describe('TEC Restriction Timeline Visualization', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    // Wait for templates to load from API
    await page.waitForTimeout(2000);
  });

  test('should render timeline for tec_interval_array parameter', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Check if timeline element exists for restriction_intervals parameter
    const timeline = page.locator('.parameter-timeline').first();
    await expect(timeline).toBeVisible({ timeout: 5000 });

    console.log('Timeline found for restriction_intervals parameter');
  });

  test('should display 24-hour markers on TEC timeline', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Wait for timeline to load
    const timeline = page.locator('.parameter-timeline').first();
    await timeline.waitFor({ state: 'visible', timeout: 5000 });

    // Check for hour markers
    const hourMarkers = timeline.locator('.timeline-hour');
    await hourMarkers.first().waitFor({ state: 'visible', timeout: 5000 });
    const count = await hourMarkers.count();

    expect(count).toBeGreaterThanOrEqual(20); // Should have most hours displayed
    console.log(`Found ${count} hour markers`);
  });

  test('should render timeline slots with simple_interval colors', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Wait for timeline to load
    const timeline = page.locator('.parameter-timeline').first();
    await timeline.waitFor({ state: 'visible', timeout: 5000 });

    // Check for timeline slots
    const timelineSlots = timeline.locator('.timeline-slot');
    await timelineSlots.first().waitFor({ state: 'visible', timeout: 5000 });
    const slotCount = await timelineSlots.count();

    expect(slotCount).toBeGreaterThan(0); // Should have at least one slot (default: 2 intervals)
    console.log(`Found ${slotCount} timeline slots`);

    // Verify slots have blue color (simple_interval type)
    if (slotCount > 0) {
      const firstSlot = timelineSlots.first();
      const bgColor = await firstSlot.evaluate(el =>
        window.getComputedStyle(el).backgroundColor
      );

      // Should be blue-ish (rgb(59, 130, 246) = #3b82f6 with opacity)
      console.log('Timeline slot background color:', bgColor);
      expect(bgColor).not.toBe('rgba(0, 0, 0, 0)'); // Not transparent
      expect(bgColor).not.toBe(''); // Not empty
    }
  });

  test('should display time range labels on timeline slots', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Wait for timeline to load
    const timeline = page.locator('.parameter-timeline').first();
    await timeline.waitFor({ state: 'visible', timeout: 5000 });

    // Check for slot labels
    const slotLabels = timeline.locator('.timeline-slot-label');
    const labelCount = await slotLabels.count();

    if (labelCount > 0) {
      const firstLabel = await slotLabels.first().textContent();
      console.log('First timeline slot label:', firstLabel);

      // Label should contain time format like "7:00-9:00"
      expect(firstLabel).toMatch(/\d+:\d+-\d+:\d+/);
    }
  });

  test('should render TEC interval table below timeline', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Check if timeline exists
    const timeline = page.locator('.parameter-timeline').first();
    await expect(timeline).toBeVisible({ timeout: 5000 });

    // Check if table exists
    const table = page.locator('.intervals-table');
    await expect(table).toBeVisible({ timeout: 5000 });

    // Verify timeline is above table
    const timelineBox = await timeline.boundingBox();
    const tableBox = await table.boundingBox();

    expect(timelineBox).not.toBeNull();
    expect(tableBox).not.toBeNull();
    expect(timelineBox.y).toBeLessThan(tableBox.y); // Timeline above table

    console.log('Timeline is positioned above table');
  });

  test('should update timeline when interval table changes', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Wait for timeline to load
    const timeline = page.locator('.parameter-timeline').first();
    await timeline.waitFor({ state: 'visible', timeout: 5000 });

    // Get initial slot count
    const initialSlots = await timeline.locator('.timeline-slot').count();
    console.log('Initial slot count:', initialSlots);

    // Modify interval in table
    const beginInput = page.locator('.tec-interval-begin').first();
    const endInput = page.locator('.tec-interval-end').first();

    await beginInput.waitFor({ state: 'visible', timeout: 5000 });

    // Change begin time
    await beginInput.fill('');
    await beginInput.fill('8');
    await beginInput.blur();

    // Change end time
    await endInput.fill('');
    await endInput.fill('10');
    await endInput.blur();

    // Wait for debounced update (300ms + buffer)
    await page.waitForTimeout(600);

    // Verify timeline updated (check that label changed)
    const firstLabel = await timeline.locator('.timeline-slot-label').first().textContent();
    console.log('Updated first label:', firstLabel);

    // Label should reflect new time range
    expect(firstLabel).toContain('8:');
  });

  test('should add new timeline slot when adding interval row', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Wait for timeline to load
    const timeline = page.locator('.parameter-timeline').first();
    await timeline.waitFor({ state: 'visible', timeout: 5000 });

    // Get initial slot count
    const initialSlots = await timeline.locator('.timeline-slot').count();
    console.log('Initial slot count:', initialSlots);

    // Click "添加时间区间" button
    const addButton = page.locator('button:has-text("添加时间区间")');
    await addButton.waitFor({ state: 'visible', timeout: 5000 });
    await addButton.click();
    console.log('Clicked add interval button');

    // Wait for new row to be added and timeline to update
    await page.waitForTimeout(600);

    // Verify new slot added to timeline
    const updatedSlots = await timeline.locator('.timeline-slot').count();
    console.log('Updated slot count:', updatedSlots);

    expect(updatedSlots).toBeGreaterThan(initialSlots);
  });

  test('should display description and usage hints', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

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

  test('should have unified card-style layout', async ({ page }) => {
    await selectTECRestrictionTemplateAndConfigure(page);

    // Check for tec-interval-control-enhanced container
    const container = page.locator('.tec-interval-control-enhanced').first();
    await container.waitFor({ state: 'visible', timeout: 5000 });
    await expect(container).toBeVisible();

    // Verify card styling (border, background, border-radius)
    const styles = await container.evaluate(el => ({
      background: window.getComputedStyle(el).backgroundColor,
      border: window.getComputedStyle(el).border,
      borderRadius: window.getComputedStyle(el).borderRadius
    }));

    expect(styles.background).not.toBe('rgba(0, 0, 0, 0)'); // Has background
    expect(styles.borderRadius).not.toBe('0px'); // Has rounded corners
    console.log('Container styles:', styles);
  });
});

test.describe('TEC Restriction Timeline - Error Handling', () => {
  test('should not produce console errors when rendering TEC timeline', async ({ page }) => {
    const consoleErrors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Select TEC restriction template and configure
    await selectTECRestrictionTemplateAndConfigure(page);

    // Filter out known external errors
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
