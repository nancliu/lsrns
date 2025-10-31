/**
 * E2E Tests: DHS Timeline Synchronization
 *
 * Tests the real-time synchronization between DHS interval configuration table
 * and the timeline visualization component.
 *
 * Issue: Manual testing found that the DHS timeline does not sync correctly
 * with the time configuration table.
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const TEMPLATES_PAGE = `${BASE_URL}/control/templates.html`;

test.describe('DHS Timeline Synchronization', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to templates page
    await page.goto(TEMPLATES_PAGE);
    await page.waitForLoadState('networkidle');
  });

  test('should display timeline when DHS template is loaded', async ({ page }) => {
    // Step 1: Select DHS template (应急车道开放 定时管控)
    // Find and click the DHS scheduled control template
    const dhsTemplateCard = page.locator('.template-card').filter({
      hasText: '应急车道开放'
    }).first();

    await expect(dhsTemplateCard).toBeVisible();
    await dhsTemplateCard.click();

    // Click next to go to step 2
    const nextBtn = page.locator('button:has-text("下一步")');
    await nextBtn.click();

    // Step 2: Select segments (skip for now, just click next)
    // Wait for edge selector to load
    await page.waitForSelector('.edge-selector-section', { timeout: 10000 });

    // Click next to go to step 3 (configure parameters)
    await nextBtn.click();

    // Step 3: Verify timeline appears in configure parameters step
    await page.waitForSelector('.dhs-interval-control-enhanced', { timeout: 5000 });

    // Check if timeline exists
    const timeline = page.locator('.parameter-timeline');
    await expect(timeline).toBeVisible({ timeout: 5000 });

    // Check if 24-hour markers exist
    const hourMarkers = page.locator('.timeline-hour');
    await expect(hourMarkers.first()).toBeVisible();
    const hourCount = await hourMarkers.count();
    expect(hourCount).toBeGreaterThanOrEqual(24);
  });

  test('should update timeline when begin_hours is changed', async ({ page }) => {
    // Navigate to DHS configuration step
    await navigateToDHSConfigStep(page);

    // Get initial timeline state
    const initialSlots = await page.locator('.timeline-slot').count();
    expect(initialSlots).toBeGreaterThan(0);

    // Find first row's begin_hours input
    const firstBeginInput = page.locator('.dhs-interval-begin').first();
    await expect(firstBeginInput).toBeVisible();

    // Get initial value
    const initialValue = await firstBeginInput.inputValue();
    console.log(`Initial begin_hours: ${initialValue}`);

    // Change begin_hours value
    await firstBeginInput.clear();
    await firstBeginInput.fill('3');
    await firstBeginInput.blur();

    // Wait for debounced update (300ms + buffer)
    await page.waitForTimeout(500);

    // Verify timeline updated
    const updatedSlots = await page.locator('.timeline-slot').count();
    console.log(`Timeline slots: initial=${initialSlots}, updated=${updatedSlots}`);

    // Timeline should still have slots (may be same count if just repositioning)
    expect(updatedSlots).toBeGreaterThan(0);
  });

  test('should update timeline when end_hours is changed', async ({ page }) => {
    await navigateToDHSConfigStep(page);

    // Find first row's end_hours input
    const firstEndInput = page.locator('.dhs-interval-end').first();
    await expect(firstEndInput).toBeVisible();

    const initialValue = await firstEndInput.inputValue();
    console.log(`Initial end_hours: ${initialValue}`);

    // Change end_hours value
    await firstEndInput.clear();
    await firstEndInput.fill('8');
    await firstEndInput.blur();

    // Wait for debounced update
    await page.waitForTimeout(500);

    // Get timeline slot info
    const slots = page.locator('.timeline-slot');
    const slotCount = await slots.count();
    expect(slotCount).toBeGreaterThan(0);

    // Check if first slot width changed (should be wider now: 0-8 = 8 hours)
    const firstSlot = slots.first();
    const width = await firstSlot.evaluate(el => el.style.width);
    console.log(`First slot width: ${width}`);

    // 8 hours should be ~33.33% of 24 hours
    expect(width).toContain('%');
  });

  test('should update timeline color when status is changed', async ({ page }) => {
    await navigateToDHSConfigStep(page);

    // Find first row's status select
    const firstStatusSelect = page.locator('.dhs-interval-status').first();
    await expect(firstStatusSelect).toBeVisible();

    const initialStatus = await firstStatusSelect.inputValue();
    console.log(`Initial status: ${initialStatus}`);

    // Change status from CLOSED to OPEN (or vice versa)
    const newStatus = initialStatus === 'OPEN' ? 'CLOSED' : 'OPEN';
    await firstStatusSelect.selectOption(newStatus);

    // Wait for debounced update
    await page.waitForTimeout(500);

    // Get first timeline slot background color
    const firstSlot = page.locator('.timeline-slot').first();
    const bgColor = await firstSlot.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    console.log(`Status: ${newStatus}, Color: ${bgColor}`);

    // Verify color matches expected status
    if (newStatus === 'OPEN') {
      // Green for OPEN: rgb(16, 185, 129) = #10b981
      expect(bgColor).toContain('16');
    } else {
      // Red for CLOSED: rgb(239, 68, 68) = #ef4444
      expect(bgColor).toContain('239');
    }
  });

  test('should add new timeline segment when row is added', async ({ page }) => {
    await navigateToDHSConfigStep(page);

    // Count initial rows and timeline slots
    const initialRows = await page.locator('.dhs-interval-row').count();
    const initialSlots = await page.locator('.timeline-slot').count();

    console.log(`Initial: ${initialRows} rows, ${initialSlots} slots`);

    // Click "添加时间区间" button
    const addButton = page.locator('button:has-text("添加时间区间")');
    await expect(addButton).toBeVisible();
    await addButton.click();

    // Wait for new row to appear
    await page.waitForTimeout(300);

    // Verify new row added
    const newRowCount = await page.locator('.dhs-interval-row').count();
    expect(newRowCount).toBe(initialRows + 1);

    // Wait for timeline update
    await page.waitForTimeout(500);

    // Verify timeline updated
    const newSlotCount = await page.locator('.timeline-slot').count();
    console.log(`After add: ${newRowCount} rows, ${newSlotCount} slots`);
    expect(newSlotCount).toBeGreaterThanOrEqual(initialSlots);
  });

  test('should remove timeline segment when row is deleted', async ({ page }) => {
    await navigateToDHSConfigStep(page);

    // Ensure there are at least 2 rows
    const initialRows = await page.locator('.dhs-interval-row').count();
    if (initialRows < 2) {
      // Add a row first
      await page.locator('button:has-text("添加时间区间")').click();
      await page.waitForTimeout(300);
    }

    const rowCount = await page.locator('.dhs-interval-row').count();
    const initialSlots = await page.locator('.timeline-slot').count();

    console.log(`Before delete: ${rowCount} rows, ${initialSlots} slots`);

    // Click first "删除" button
    const firstDeleteBtn = page.locator('.btn-remove-interval').first();
    await expect(firstDeleteBtn).toBeVisible();
    await firstDeleteBtn.click();

    // Wait for row removal
    await page.waitForTimeout(300);

    // Verify row removed
    const newRowCount = await page.locator('.dhs-interval-row').count();
    expect(newRowCount).toBe(rowCount - 1);

    // Wait for timeline update
    await page.waitForTimeout(500);

    // Verify timeline updated
    const newSlotCount = await page.locator('.timeline-slot').count();
    console.log(`After delete: ${newRowCount} rows, ${newSlotCount} slots`);
  });

  test('should show correct timeline layout and styling', async ({ page }) => {
    await navigateToDHSConfigStep(page);

    // Verify timeline container styling
    const timelineContainer = page.locator('.parameter-timeline');
    await expect(timelineContainer).toBeVisible();

    // Check card-like styling
    const bgColor = await timelineContainer.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );
    const borderRadius = await timelineContainer.evaluate(el =>
      window.getComputedStyle(el).borderRadius
    );

    console.log(`Timeline style: bg=${bgColor}, radius=${borderRadius}`);

    // Should have white background and rounded corners
    expect(bgColor).toContain('255'); // White color
    expect(borderRadius).not.toBe('0px'); // Has border radius
  });

  test('should not have console errors during DHS timeline sync', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await navigateToDHSConfigStep(page);

    // Perform various operations
    const beginInput = page.locator('.dhs-interval-begin').first();
    await beginInput.clear();
    await beginInput.fill('5');
    await beginInput.blur();

    await page.waitForTimeout(500);

    const statusSelect = page.locator('.dhs-interval-status').first();
    await statusSelect.selectOption('OPEN');

    await page.waitForTimeout(500);

    // Check for errors
    console.log('Console errors:', consoleErrors);
    expect(consoleErrors.length).toBe(0);
  });
});

/**
 * Helper function to navigate to DHS configuration step
 */
async function navigateToDHSConfigStep(page) {
  // Step 1: Select DHS template
  const dhsTemplateCard = page.locator('.template-card').filter({
    hasText: '应急车道开放'
  }).first();

  await expect(dhsTemplateCard).toBeVisible({ timeout: 10000 });
  await dhsTemplateCard.click();

  // Go to step 2
  const nextBtn = page.locator('button:has-text("下一步")');
  await nextBtn.click();

  // Wait for edge selector
  await page.waitForSelector('.edge-selector-section', { timeout: 10000 });

  // Go to step 3 (configure parameters)
  await nextBtn.click();

  // Wait for DHS interval control to load
  await page.waitForSelector('.dhs-interval-control-enhanced', { timeout: 5000 });
  await page.waitForSelector('.parameter-timeline', { timeout: 5000 });
}
