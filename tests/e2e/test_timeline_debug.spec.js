/**
 * Debug test for timeline visualization
 */

const { test, expect } = require('@playwright/test');

test('debug timeline rendering', async ({ page }) => {
  // Navigate to templates page
  await page.goto('http://localhost:8000/control/templates.html');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Take screenshot of template list
  await page.screenshot({ path: 'test-results/01-template-list.png', fullPage: true });

  // Select a VSS template
  const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
  await vssCard.waitFor({ state: 'visible', timeout: 10000 });
  console.log('Found VSS template card');
  await vssCard.click();
  await page.waitForTimeout(500);

  // Take screenshot after selection
  await page.screenshot({ path: 'test-results/02-template-selected.png', fullPage: true });

  // Click next button
  const nextButton = page.locator('#floating-next-btn');
  await nextButton.waitFor({ state: 'visible', timeout: 5000 });
  console.log('Found next button');
  await nextButton.click();
  await page.waitForTimeout(2000);

  // Take screenshot of parameter form
  await page.screenshot({ path: 'test-results/03-parameter-form.png', fullPage: true });

  // Check what elements exist on the page
  const formContent = await page.locator('#step2-content').innerHTML().catch(() => 'Not found');
  console.log('Step2 content length:', formContent.length);

  // Check for various elements
  const timelineCount = await page.locator('.parameter-timeline').count();
  const tableCount = await page.locator('.steps-table').count();
  const controlCount = await page.locator('.step-array-control-enhanced').count();
  const speedInputCount = await page.locator('.step-speed').count();

  console.log('Timeline elements:', timelineCount);
  console.log('Table elements:', tableCount);
  console.log('Control containers:', controlCount);
  console.log('Speed inputs:', speedInputCount);

  // Get all visible text
  const bodyText = await page.locator('body').innerText();
  const hasParamForm = bodyText.includes('speed_steps') || bodyText.includes('限速') || bodyText.includes('参数');
  console.log('Has parameter form text:', hasParamForm);

  // Log any console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser console error:', msg.text());
    }
  });

  // Wait a bit more to see if anything loads
  await page.waitForTimeout(2000);

  // Final screenshot
  await page.screenshot({ path: 'test-results/04-final-state.png', fullPage: true });

  // Basic check
  expect(vssCard).toBeTruthy();
});
