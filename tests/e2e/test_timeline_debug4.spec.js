/**
 * Debug test #4 - Full workflow with G4202 route
 */

const { test } = require('@playwright/test');

test('debug full workflow with G4202', async ({ page }) => {
  await page.goto('http://localhost:8000/control/templates.html');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Step 1: Select VSS template
  const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
  await vssCard.click();
  console.log('✓ Selected VSS template');
  await page.waitForTimeout(500);

  // Step 2: Click next
  const nextButton1 = page.locator('#floating-next-btn');
  await nextButton1.click();
  console.log('✓ Clicked next to edge selection');
  await page.waitForTimeout(2000);

  // Step 3: Select G4202 route
  const routeSelect = page.locator('#route-codes');
  await routeSelect.selectOption({ index: 0 }); // G4202
  console.log('✓ Selected G4202 route');

  // Wait for sections
  console.log('⏳ Waiting 7 seconds for sections...');
  await page.waitForTimeout(7000);

  // Step 4: Select a section
  const sectionSelect = page.locator('#section-codes');
  const sectionOptions = await sectionSelect.locator('option').count();
  console.log(`✓ Found ${sectionOptions} sections`);

  if (sectionOptions > 1) {
    await sectionSelect.selectOption({ index: 1 });
    console.log('✓ Selected section');
  }

  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'test-results/debug4-01-edges-selected.png', fullPage: true });

  // Step 5: Click next to parameters
  const nextButton2 = page.locator('#floating-next-btn');
  await nextButton2.click();
  console.log('✓ Clicked next to parameters');
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'test-results/debug4-02-parameters.png', fullPage: true });

  // Check what step we're on
  const step1Visible = await page.locator('#step1-content').isVisible();
  const step2Visible = await page.locator('#step2-content').isVisible();
  const step3Visible = await page.locator('#step3-content').isVisible();

  console.log(`\nStep visibility:`);
  console.log(`  Step 1: ${step1Visible}`);
  console.log(`  Step 2: ${step2Visible}`);
  console.log(`  Step 3: ${step3Visible}`);

  // Get content of visible step
  let visibleContent = '';
  if (step3Visible) {
    visibleContent = await page.locator('#step3-content').innerHTML();
    console.log(`\nStep 3 content length: ${visibleContent.length} bytes`);
  } else if (step2Visible) {
    visibleContent = await page.locator('#step2-content').innerHTML();
    console.log(`\nStep 2 content length: ${visibleContent.length} bytes`);
  }

  // Check for timeline elements
  const timelineCount = await page.locator('.parameter-timeline').count();
  const tableCount = await page.locator('.steps-table').count();
  const speedInputCount = await page.locator('.step-speed').count();
  const formGroupCount = await page.locator('.form-group').count();

  console.log(`\nElement counts:`);
  console.log(`  .parameter-timeline: ${timelineCount}`);
  console.log(`  .steps-table: ${tableCount}`);
  console.log(`  .step-speed: ${speedInputCount}`);
  console.log(`  .form-group: ${formGroupCount}`);

  // Check page text
  const bodyText = await page.locator('body').innerText();
  console.log(`\nPage text contains:`);
  console.log(`  "speed_steps": ${bodyText.includes('speed_steps')}`);
  console.log(`  "参数配置": ${bodyText.includes('参数配置')}`);
  console.log(`  "请先选择": ${bodyText.includes('请先选择')}`);
  console.log(`  "时间": ${bodyText.includes('时间')}`);
  console.log(`  "限速": ${bodyText.includes('限速')}`);

  // Save full HTML for inspection
  const fullHTML = await page.content();
  require('fs').writeFileSync('test-results/debug4-full-page.html', fullHTML);
  console.log('\n✓ Saved full page HTML to debug4-full-page.html');
});
