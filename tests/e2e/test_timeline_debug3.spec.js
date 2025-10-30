/**
 * Debug test #3 - Check edge selection workflow with screenshots
 */

const { test } = require('@playwright/test');

test('debug edge selection workflow', async ({ page }) => {
  await page.goto('http://localhost:8000/control/templates.html');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Select VSS template
  const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
  await vssCard.click();
  await page.waitForTimeout(500);

  // Click next
  const nextButton1 = page.locator('#floating-next-btn');
  await nextButton1.click();
  await page.waitForTimeout(2000);

  // Take screenshot of step 2
  await page.screenshot({ path: 'test-results/debug3-01-step2.png', fullPage: true });

  // Get all select elements
  const allSelects = await page.locator('select').count();
  console.log(`Total select elements: ${allSelects}`);

  // Check each select element
  for (let i = 0; i < allSelects; i++) {
    const select = page.locator('select').nth(i);
    const id = await select.getAttribute('id').catch(() => 'no-id');
    const name = await select.getAttribute('name').catch(() => 'no-name');
    const optionCount = await select.locator('option').count();
    console.log(`Select ${i}: id="${id}", name="${name}", options=${optionCount}`);

    if (optionCount > 0) {
      const firstOptionText = await select.locator('option').first().innerText();
      console.log(`  First option: "${firstOptionText}"`);
    }
  }

  // Try to find route select
  const routeSelect = page.locator('select').first();
  const routeOptions = await routeSelect.locator('option').count();
  console.log(`\nRoute select has ${routeOptions} options`);

  if (routeOptions > 1) {
    // Get all option texts
    for (let i = 0; i < Math.min(routeOptions, 5); i++) {
      const optionText = await routeSelect.locator('option').nth(i).innerText();
      console.log(`  Option ${i}: "${optionText}"`);
    }

    // Select second option (first real route)
    await routeSelect.selectOption({ index: 1 });
    console.log('\nSelected route option 1');

    // Take screenshot after route selection
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/debug3-02-route-selected.png', fullPage: true });

    // Wait for sections to load (6-7 seconds as user mentioned)
    console.log('Waiting 7 seconds for sections to load...');
    await page.waitForTimeout(7000);

    // Check section select again
    const sectionSelect = page.locator('select').nth(1);
    const sectionOptions = await sectionSelect.locator('option').count();
    console.log(`\nAfter waiting, section select has ${sectionOptions} options`);

    if (sectionOptions > 0) {
      for (let i = 0; i < Math.min(sectionOptions, 5); i++) {
        const optionText = await sectionSelect.locator('option').nth(i).innerText();
        console.log(`  Section option ${i}: "${optionText}"`);
      }
    }

    // Take screenshot after waiting
    await page.screenshot({ path: 'test-results/debug3-03-sections-loaded.png', fullPage: true });

    // Try selecting a section if available
    if (sectionOptions > 1) {
      await sectionSelect.selectOption({ index: 1 });
      console.log('\nSelected section option 1');
      await page.waitForTimeout(1000);

      // Take screenshot after section selection
      await page.screenshot({ path: 'test-results/debug3-04-section-selected.png', fullPage: true });

      // Click next to go to parameters
      const nextButton2 = page.locator('#floating-next-btn');
      await nextButton2.click();
      console.log('Clicked next button to go to parameters');
      await page.waitForTimeout(3000);

      // Take screenshot of parameter form
      await page.screenshot({ path: 'test-results/debug3-05-parameters.png', fullPage: true });

      // Check for timeline and form elements
      const timelineCount = await page.locator('.parameter-timeline').count();
      const tableCount = await page.locator('.steps-table').count();
      const controlCount = await page.locator('.step-array-control-enhanced').count();

      console.log(`\nParameter form elements:`);
      console.log(`  Timelines: ${timelineCount}`);
      console.log(`  Tables: ${tableCount}`);
      console.log(`  Controls: ${controlCount}`);

      // Get step3 content if exists
      const step3Content = await page.locator('#step3-content').innerHTML().catch(() => 'Not found');
      console.log(`\nStep3 content length: ${step3Content.length} bytes`);

      // Check for specific text in the page
      const bodyText = await page.locator('body').innerText();
      console.log(`\nPage contains:`);
      console.log(`  "speed_steps": ${bodyText.includes('speed_steps')}`);
      console.log(`  "参数配置": ${bodyText.includes('参数配置')}`);
      console.log(`  "请先选择": ${bodyText.includes('请先选择')}`);
    } else {
      console.log('\nNo sections loaded after 7 seconds wait');
    }
  } else {
    console.log('\nNo routes available to select');
  }
});
