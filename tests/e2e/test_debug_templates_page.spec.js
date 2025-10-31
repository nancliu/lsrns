/**
 * Debug test to inspect templates page state
 */

const { test, expect } = require('@playwright/test');

test.describe('Templates Page Debug', () => {
  test('should inspect page state after loading', async ({ page }) => {
    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/templates-page-loaded.png', fullPage: true });

    // Check what's on the page
    const title = await page.title();
    console.log('Page title:', title);

    // Check for template cards
    const cards = page.locator('.template-card');
    const cardCount = await cards.count();
    console.log('Template cards found:', cardCount);

    // Check for VSS cards
    const vssCards = page.locator('.template-card:has(.badge-VSS)');
    const vssCount = await vssCards.count();
    console.log('VSS template cards found:', vssCount);

    // Try to find the first VSS card and log its text
    if (vssCount > 0) {
      const firstVSSCard = vssCards.first();
      const cardText = await firstVSSCard.textContent();
      console.log('First VSS card text:', cardText);

      // Click the card
      await firstVSSCard.click();
      await page.waitForTimeout(2000);

      // Take screenshot after click
      await page.screenshot({ path: 'test-results/after-card-click.png', fullPage: true });

      // Check what happened after click
      const nextButton = page.locator('#floating-next-btn');
      const nextButtonExists = await nextButton.count();
      console.log('Next button found:', nextButtonExists);

      if (nextButtonExists === 0) {
        // Check for any visible buttons
        const allButtons = page.locator('button:visible');
        const buttonCount = await allButtons.count();
        console.log('All visible buttons:', buttonCount);

        for (let i = 0; i < Math.min(buttonCount, 5); i++) {
          const btnText = await allButtons.nth(i).textContent();
          const btnClass = await allButtons.nth(i).getAttribute('class');
          const btnId = await allButtons.nth(i).getAttribute('id');
          console.log(`Button ${i}:`, { text: btnText, class: btnClass, id: btnId });
        }
      }
    }

    // Check for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    }
  });

  test('should check if templates API is working', async ({ page }) => {
    // Check templates API endpoint
    const response = await page.goto('http://localhost:8000/api/v1/control/strategies/templates');
    const status = response.status();
    console.log('Templates API status:', status);

    if (status === 200) {
      const data = await response.json();
      console.log('Templates API response:', JSON.stringify(data, null, 2).substring(0, 500));
    }
  });
});
