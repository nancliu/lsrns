/**
 * Debug test #2 - Check actual DOM structure
 */

const { test } = require('@playwright/test');

test('check DOM structure after clicking next', async ({ page }) => {
  await page.goto('http://localhost:8000/control/templates.html');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);

  // Select VSS template and click next
  const vssCard = page.locator('.template-card:has(.badge-VSS)').first();
  await vssCard.click();
  await page.waitForTimeout(500);

  const nextButton = page.locator('#floating-next-btn');
  await nextButton.click();
  await page.waitForTimeout(3000); // Wait longer for form to render

  // Get the HTML of step2-content
  const step2HTML = await page.locator('#step2-content').innerHTML();

  // Save to file for inspection
  const fs = require('fs');
  fs.writeFileSync('test-results/step2-content.html', step2HTML);
  console.log('Saved step2-content.html');

  // Check specific elements we're looking for
  console.log('Contains .parameter-timeline:', step2HTML.includes('parameter-timeline'));
  console.log('Contains .steps-table:', step2HTML.includes('steps-table'));
  console.log('Contains .step-array-control:', step2HTML.includes('step-array-control'));
  console.log('Contains speed_steps:', step2HTML.includes('speed_steps'));

  // Try to find any form groups
  const formGroups = await page.locator('.form-group').count();
  console.log('Form groups found:', formGroups);

  // Check if there's a "请选择管控路段" message (need to select edges first)
  const bodyText = await page.locator('body').innerText();
  console.log('Contains "选择管控路段":', bodyText.includes('选择管控路段'));
  console.log('Contains "请先选择":', bodyText.includes('请先选择'));
});
