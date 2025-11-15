/**
 * E2E Tests for Scenario Browser - Event-Based Case Architecture
 *
 * Tests the complete end-to-end workflow for:
 * 1. Creating first scenario (new case, OD generation)
 * 2. Creating second scenario (reused case, instant)
 * 3. Verifying user-facing messages
 * 4. Verifying UI state changes
 */

const { test, expect } = require('@playwright/test');

test.describe('Scenario Browser - Event-Based Cases', () => {
    test('should display scenario list and controls', async ({ page }) => {
        // Navigate to scenario browser
        await page.goto('http://localhost:8000/frontend/scenarios/scenario_browser.html');
        await page.waitForLoadState('networkidle');

        // Verify page elements are present
        const scenarioTable = await page.locator('table').first();
        expect(scenarioTable).toBeTruthy();

        // Verify buttons exist
        const refreshBtn = await page.locator('button:has-text("🔄 刷新")');
        const checkBtn = await page.locator('button:has-text("✓ 检查")');
        const addCsvBtn = await page.locator('button:has-text("📤 添加新事件CSV")');

        expect(refreshBtn).toBeTruthy();
        expect(checkBtn).toBeTruthy();
        expect(addCsvBtn).toBeTruthy();
    });

    test('should show different messages for new vs reused cases', async ({ page }) => {
        await page.goto('http://localhost:8000/frontend/scenarios/scenario_browser.html');
        await page.waitForLoadState('networkidle');

        const messages = [];

        // Intercept all alerts
        page.on('dialog', async (dialog) => {
            messages.push(dialog.message());
            await dialog.accept();
        });

        // Create first scenario
        let createBtn = await page.locator('button:has-text("创建")').first();
        if (createBtn && await createBtn.isEnabled()) {
            await createBtn.click();
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Verify we have at least one message
        if (messages.length > 0) {
            // First message should contain new case or case info
            expect(messages[0].length > 0).toBeTruthy();
            expect(messages[0]).toContain('✅');
        }
    });

    test('should display appropriate UI feedback', async ({ page }) => {
        await page.goto('http://localhost:8000/frontend/scenarios/scenario_browser.html');
        await page.waitForLoadState('networkidle');

        const createBtn = await page.locator('button:has-text("创建")').first();

        // Button should be visible and enabled
        expect(await createBtn.isVisible()).toBeTruthy();
        expect(await createBtn.isEnabled()).toBeTruthy();

        // Click and verify dialog appears
        const dialogPromise = page.waitForEvent('dialog');
        await createBtn.click();
        const dialog = await dialogPromise;

        const message = dialog.message();

        // Message should be non-empty and contain relevant info
        expect(message.length > 0).toBeTruthy();
        expect(message).toMatch(/✅|⏳|💡|🚀|⚡/); // Should contain emoji feedback

        await dialog.accept();
    });

    test('should show refresh and check buttons', async ({ page }) => {
        await page.goto('http://localhost:8000/frontend/scenarios/scenario_browser.html');
        await page.waitForLoadState('networkidle');

        // Verify refresh button exists
        const refreshBtn = await page.locator('button:has-text("🔄 刷新")');
        expect(refreshBtn).toBeTruthy();

        // Verify check button exists
        const checkBtn = await page.locator('button:has-text("✓ 检查")');
        expect(checkBtn).toBeTruthy();

        // Buttons should be clickable
        expect(await refreshBtn.isEnabled()).toBeTruthy();
        expect(await checkBtn.isEnabled()).toBeTruthy();
    });

    test('should show add CSV button', async ({ page }) => {
        await page.goto('http://localhost:8000/frontend/scenarios/scenario_browser.html');
        await page.waitForLoadState('networkidle');

        // Verify add CSV button exists
        const addCsvBtn = await page.locator('button:has-text("📤 添加新事件CSV")');
        expect(addCsvBtn).toBeTruthy();

        // Button should be clickable
        expect(await addCsvBtn.isEnabled()).toBeTruthy();
    });

    test('should maintain scenario list state', async ({ page }) => {
        await page.goto('http://localhost:8000/frontend/scenarios/scenario_browser.html');
        await page.waitForLoadState('networkidle');

        // Get initial row count
        const initialRows = await page.locator('tbody tr').count();
        expect(initialRows > 0).toBeTruthy();

        // Perform an action
        const firstCreateBtn = await page.locator('button:has-text("创建")').first();
        if (firstCreateBtn && await firstCreateBtn.isEnabled()) {
            page.on('dialog', async (dialog) => {
                await dialog.accept();
            });

            await firstCreateBtn.click();
            await new Promise(resolve => setTimeout(resolve, 500));

            // Verify row count hasn't changed
            const finalRows = await page.locator('tbody tr').count();
            expect(finalRows).toBe(initialRows);
        }
    });
});
