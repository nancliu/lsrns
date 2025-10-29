/**
 * E2E Tests for Peak Vehicle Curve Visualization (Phase 2 Task 2.9)
 * Tests the in-network vehicles peak curve feature in batch optimization results
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const SIMULATIONS_URL = `${BASE_URL}/control/simulations.html`;

test.describe('Peak Vehicle Curve E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to batch simulations page
        await page.goto(SIMULATIONS_URL);
        await page.waitForLoadState('networkidle');
    });

    test('should have peak curve chart canvas element in results view', async ({ page }) => {
        // Check that peak curve chart canvas exists
        const peakCurveCanvas = page.locator('#peakCurveChart');
        expect(await peakCurveCanvas.count()).toBe(1);

        // Canvas should exist but section may be hidden initially
        const canvasElement = await peakCurveCanvas.elementHandle();
        expect(canvasElement).not.toBeNull();
    });

    test('should have peak curve section with proper structure', async ({ page }) => {
        // Check peak curve section exists
        const peakCurveSection = page.locator('#peakCurveSection');
        expect(await peakCurveSection.count()).toBe(1);

        // Check section title
        const sectionTitle = peakCurveSection.locator('h3');
        await expect(sectionTitle).toContainText('在网车辆峰值曲线');

        // Check canvas exists within section
        const canvas = peakCurveSection.locator('#peakCurveChart');
        expect(await canvas.count()).toBe(1);

        // Check peak metrics container exists
        const peakMetrics = peakCurveSection.locator('#peakMetrics');
        expect(await peakMetrics.count()).toBe(1);
    });

    test('should hide peak curve section by default (no data)', async ({ page }) => {
        // Peak curve section should be hidden when no data is loaded
        const peakCurveSection = page.locator('#peakCurveSection');

        // Element exists in DOM
        expect(await peakCurveSection.count()).toBe(1);

        // But should not be visible (display: none)
        const isVisible = await peakCurveSection.isVisible();
        expect(isVisible).toBe(false);
    });

    test('should have Chart.js library loaded for visualization', async ({ page }) => {
        // Check if Chart.js script is loaded
        const chartJsScript = page.locator('script[src*="chart.js"]');
        const scriptCount = await chartJsScript.count();

        // Should have at least one Chart.js script tag
        expect(scriptCount).toBeGreaterThan(0);
    });

    test('should have peak metrics container for displaying statistics', async ({ page }) => {
        // Check peak metrics container exists
        const peakMetrics = page.locator('#peakMetrics');
        expect(await peakMetrics.count()).toBe(1);

        // Container should have grid layout styling
        const gridStyle = await peakMetrics.getAttribute('style');
        expect(gridStyle).toContain('grid');
    });

    test('should have results view with all necessary components', async ({ page }) => {
        // Check results view exists
        const resultsView = page.locator('#resultsView');
        expect(await resultsView.count()).toBe(1);

        // Check content header
        const resultsHeader = page.locator('#resultsView .content-header h2');
        await expect(resultsHeader).toContainText('批量仿真结果');

        // Check results container
        const resultsContainer = page.locator('.results-container');
        expect(await resultsContainer.count()).toBeGreaterThan(0);

        // Check comparison table container
        const comparisonTable = page.locator('#comparisonTable');
        expect(await comparisonTable.count()).toBe(1);

        // Check peak curve section is within results
        const peakCurveInResults = resultsView.locator('#peakCurveSection');
        expect(await peakCurveInResults.count()).toBe(1);
    });

    test('peak curve canvas should have proper styling', async ({ page }) => {
        // Check canvas styling
        const canvas = page.locator('#peakCurveChart');
        const canvasStyle = await canvas.getAttribute('style');

        // Should have max-height constraint
        expect(canvasStyle).toContain('max-height');
        expect(canvasStyle).toContain('400px');
    });

    test('peak curve section should be inside results view', async ({ page }) => {
        // Verify the peak curve section is within results view
        const peakCurveInResults = page.locator('#resultsView #peakCurveSection');
        expect(await peakCurveInResults.count()).toBe(1);
    });

    test('should have proper config section class for peak curve', async ({ page }) => {
        // Peak curve section should have config-section class for styling
        const peakCurveSection = page.locator('#peakCurveSection');
        const hasConfigClass = await peakCurveSection.evaluate(el =>
            el.classList.contains('config-section')
        );
        expect(hasConfigClass).toBe(true);
    });

    test('peak curve section title should be visible when section is shown', async ({ page }) => {
        // Get the section title
        const peakCurveSection = page.locator('#peakCurveSection');
        const sectionTitle = peakCurveSection.locator('h3');

        // Title text should be correct
        const titleText = await sectionTitle.textContent();
        expect(titleText).toContain('在网车辆峰值曲线');
    });
});
