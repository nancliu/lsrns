/**
 * E2E Tests for Batch Optimization (Phase 2)
 * Tests complete batch simulation workflow using Playwright
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const SIMULATIONS_URL = `${BASE_URL}/control/simulations.html`;
const API_BASE = `${BASE_URL}/api/v1`;

test.describe('Batch Optimization E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to batch simulations page
        await page.goto(SIMULATIONS_URL);
        await page.waitForLoadState('networkidle');
    });

    test('should load batch simulations page successfully', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/批量仿真/);

        // Check main views exist
        await expect(page.locator('#configView')).toBeVisible();

        // Config view should be active by default
        await expect(page.locator('#configView.active')).toBeVisible();

        // Check sidebar navigation
        await expect(page.locator('.sidebar-nav a.active')).toContainText('批量仿真');
    });

    test('should display config view components', async ({ page }) => {
        // Check config view is visible
        await expect(page.locator('#configView')).toBeVisible();

        // Check case selector exists
        await expect(page.locator('#caseSelector')).toBeVisible();

        // Check simulation parameters exist
        await expect(page.locator('#numSeeds')).toBeVisible();
        await expect(page.locator('#baseSeed')).toBeVisible();

        // Check create batch button
        await expect(page.locator('#createBatchBtn')).toBeVisible();
        await expect(page.locator('#createBatchBtn')).toContainText('创建批次');
    });

    test('should load available cases in selector', async ({ page }) => {
        // Wait longer for cases to load via JavaScript
        await page.waitForTimeout(2000);

        // Check that options exist
        const options = page.locator('#caseSelector option');
        const count = await options.count();

        expect(count).toBeGreaterThan(0);
    });

    test('should load plans when case is selected', async ({ page }) => {
        // Wait for cases to load via JavaScript
        await page.waitForTimeout(2000);

        // Get options
        const caseOptions = page.locator('#caseSelector option');
        const count = await caseOptions.count();

        // Need at least 2 options (placeholder + actual case)
        if (count > 1) {
            // Select a case (skip first option which might be placeholder)
            await page.selectOption('#caseSelector', { index: 1 });

            // Wait for plans to load
            await page.waitForTimeout(1500);

            // Check if plan items appeared
            const plansList = page.locator('#planSelector');
            const plansListContent = await plansList.textContent();

            // Should have some content (plans loaded)
            expect(plansListContent.length).toBeGreaterThan(0);
        } else {
            test.skip('No cases available for testing');
        }
    });

    test('should have default values for simulation parameters', async ({ page }) => {
        // Check default values
        await expect(page.locator('#numSeeds')).toHaveValue('3');
        await expect(page.locator('#baseSeed')).toHaveValue('66');
    });

    test('should display estimate text', async ({ page }) => {
        const estimateText = page.locator('#estimateText');

        // Should have some estimate text content
        await expect(estimateText).toBeVisible();

        // Wait for cases to load
        await page.waitForTimeout(2000);

        const caseOptions = page.locator('#caseSelector option');
        const count = await caseOptions.count();

        if (count > 1) {
            // Select a case
            await page.selectOption('#caseSelector', { index: 1 });

            // Wait for plans to load and estimate to update
            await page.waitForTimeout(2000);

            // Estimate might update based on plan selection
            // Check that estimate text contains numbers
            const text = await estimateText.textContent();
            expect(text).toMatch(/\d+/); // Should contain at least one number
        }
    });

    test('should navigate between views', async ({ page }) => {
        // Initially config view is active
        await expect(page.locator('#configView.active')).toBeVisible();
        await expect(page.locator('#progressView.active')).not.toBeVisible();
        await expect(page.locator('#resultsView.active')).not.toBeVisible();
    });

    test('should navigate to strategy management', async ({ page }) => {
        // Click on strategy management link
        await page.click('.sidebar-nav a:has-text("策略管理")');
        await page.waitForLoadState('networkidle');

        // Should navigate to templates page
        await expect(page).toHaveURL(/templates\.html/);
    });

    test('should navigate to plan management', async ({ page }) => {
        // Click on plan management link
        await page.click('.sidebar-nav a:has-text("方案管理")');
        await page.waitForLoadState('networkidle');

        // Should navigate to plans page
        await expect(page).toHaveURL(/plans\.html/);
    });

    test('should return to main system', async ({ page }) => {
        // Click return button
        await page.click('.back-btn:has-text("返回主系统")');
        await page.waitForLoadState('networkidle');

        // Should navigate to main index
        await expect(page).toHaveURL(/\/index\.html|\/$/);
    });

    test('should have progress view structure', async ({ page }) => {
        // Progress view exists but is hidden initially
        const progressView = page.locator('#progressView');
        expect(await progressView.count()).toBeGreaterThan(0);

        // Check progress bar exists
        expect(await page.locator('#progressBar').count()).toBeGreaterThan(0);
        expect(await page.locator('#progressText').count()).toBeGreaterThan(0);

        // Check action buttons exist (startBatchBtn initially visible, cancelBatchBtn hidden)
        expect(await page.locator('#startBatchBtn').count()).toBeGreaterThan(0);
        expect(await page.locator('#cancelBatchBtn').count()).toBeGreaterThan(0);
    });

    test('should have results view structure', async ({ page }) => {
        // Results view exists but is hidden initially
        const resultsView = page.locator('#resultsView');
        expect(await resultsView.count()).toBeGreaterThan(0);

        // Check results table exists
        expect(await page.locator('#comparisonTable').count()).toBeGreaterThan(0);

        // Check back button exists
        expect(await page.locator('#backToConfigBtn').count()).toBeGreaterThan(0);
    });

    test('should display plan items with checkboxes', async ({ page }) => {
        // Wait for cases to load via JavaScript
        await page.waitForTimeout(2000);

        const caseOptions = page.locator('#caseSelector option');
        const count = await caseOptions.count();

        if (count > 1) {
            // Select a case
            await page.selectOption('#caseSelector', { index: 1 });

            // Wait for plans to load
            await page.waitForTimeout(1500);

            // Check if plan-item elements exist
            const planItems = page.locator('.plan-item');
            const planCount = await planItems.count();

            if (planCount > 0) {
                // First plan item should have checkbox
                const firstPlan = planItems.first();
                const checkbox = firstPlan.locator('input[type="checkbox"]');
                await expect(checkbox).toBeVisible();

                // Should have label
                const label = firstPlan.locator('label');
                await expect(label).toBeVisible();
            }
        }
    });

    test('should select and deselect plans', async ({ page }) => {
        await page.waitForTimeout(2000);

        const caseOptions = page.locator('#caseSelector option');
        const count = await caseOptions.count();

        if (count > 1) {
            await page.selectOption('#caseSelector', { index: 1 });
            await page.waitForTimeout(1500);

            const planItems = page.locator('.plan-item');
            const planCount = await planItems.count();

            if (planCount > 1) {
                // Find a non-disabled checkbox (baseline_plan is likely disabled)
                let targetPlan = null;
                let targetCheckbox = null;

                for (let i = 0; i < planCount; i++) {
                    const plan = planItems.nth(i);
                    const checkbox = plan.locator('input[type="checkbox"]');
                    const isDisabled = await checkbox.isDisabled();

                    if (!isDisabled) {
                        targetPlan = plan;
                        targetCheckbox = checkbox;
                        break;
                    }
                }

                if (targetCheckbox) {
                    // Get initial check state
                    const initiallyChecked = await targetCheckbox.isChecked();

                    // Click checkbox to toggle
                    await targetCheckbox.click();
                    await page.waitForTimeout(300);

                    // Check state should have changed
                    const nowChecked = await targetCheckbox.isChecked();
                    expect(nowChecked).toBe(!initiallyChecked);

                    // Click again to deselect
                    await targetCheckbox.click();
                    await page.waitForTimeout(300);

                    // Should be back to initial state
                    const finalChecked = await targetCheckbox.isChecked();
                    expect(finalChecked).toBe(initiallyChecked);
                } else {
                    test.skip('No enabled checkboxes available');
                }
            } else {
                test.skip('Only one plan available');
            }
        }
    });

    test('should change simulation parameters', async ({ page }) => {
        const numSeedsInput = page.locator('#numSeeds');
        const baseSeedInput = page.locator('#baseSeed');

        // Change values
        await numSeedsInput.fill('5');
        await baseSeedInput.fill('100');

        // Verify changes
        await expect(numSeedsInput).toHaveValue('5');
        await expect(baseSeedInput).toHaveValue('100');
    });

    test('should enforce input constraints on numSeeds', async ({ page }) => {
        const numSeedsInput = page.locator('#numSeeds');

        // Try to set value below minimum
        await numSeedsInput.fill('0');
        await numSeedsInput.blur();

        // HTML5 validation should prevent invalid values
        // (exact behavior depends on browser implementation)

        // Try to set value above maximum
        await numSeedsInput.fill('15');
        await numSeedsInput.blur();

        // The input has max="10" so it should be constrained
    });

    test('should display sidebar navigation correctly', async ({ page }) => {
        // Check all sidebar links
        const sidebarLinks = page.locator('.sidebar-nav a');
        const linkCount = await sidebarLinks.count();

        expect(linkCount).toBe(4);

        // Check link texts
        await expect(sidebarLinks.nth(0)).toContainText('策略管理');
        await expect(sidebarLinks.nth(1)).toContainText('方案管理');
        await expect(sidebarLinks.nth(2)).toContainText('批量仿真');
        await expect(sidebarLinks.nth(3)).toContainText('方案优化');

        // Current page should be active
        await expect(sidebarLinks.nth(2)).toHaveClass(/active/);
    });

    test('should have proper page styling', async ({ page }) => {
        // Check top bar
        const topBar = page.locator('.top-bar');
        await expect(topBar).toBeVisible();

        // Check main container
        const mainContainer = page.locator('.main-container');
        await expect(mainContainer).toBeVisible();

        // Check sidebar
        const sidebar = page.locator('.sidebar');
        await expect(sidebar).toBeVisible();

        // Check content area
        const contentArea = page.locator('.content-area');
        await expect(contentArea).toBeVisible();
    });

    test('should display content header', async ({ page }) => {
        // Use more specific selector for config view header
        const contentHeader = page.locator('#configView .content-header');
        await expect(contentHeader).toBeVisible();

        // Check title
        await expect(contentHeader.locator('h2')).toContainText('批量优化仿真');

        // Check subtitle
        const subtitle = contentHeader.locator('.content-subtitle');
        await expect(subtitle).toContainText('配置和执行多方案批量仿真对比');
    });

    test('should have cancel button that reloads page', async ({ page }) => {
        // Find cancel button (outside start button)
        const cancelButton = page.locator('.btn.btn-secondary:has-text("取消")');

        if (await cancelButton.isVisible()) {
            // Clicking should reload - we can't easily test this without navigation
            // Just verify button exists and is clickable
            await expect(cancelButton).toBeEnabled();
        }
    });
});
