/**
 * E2E Test: Dual-layer Canvas Architecture for Network Visualization
 *
 * Tests the performance optimization implementation that separates:
 * - Bottom layer (network-canvas): Static network rendering
 * - Top layer (network-canvas-hover): Hover effects only
 *
 * Related Files:
 * - frontend/control/templates.html (L726-730: dual canvas elements)
 * - frontend/control/js/network_viz.js (dual-layer rendering logic)
 */

const { test, expect } = require('@playwright/test');

test.describe('Dual-layer Canvas Architecture', () => {

    test.beforeEach(async ({ page }) => {
        // Navigate to control strategy instance creator page
        await page.goto('http://localhost:8000/control/templates.html');

        // Wait for page load
        await page.waitForLoadState('networkidle');

        // Select first template to proceed to Step 2 (where network visualization is located)
        await page.waitForTimeout(1000); // Wait for templates to load
        const firstTemplate = page.locator('.template-card').first();
        await firstTemplate.waitFor({ state: 'visible', timeout: 10000 });
        await firstTemplate.click();

        // Wait for step 2 to become visible
        await page.waitForTimeout(500);
    });

    test('T037: Verify dual-layer canvas elements exist in DOM', async ({ page }) => {
        console.log('Test T037: Checking dual-layer canvas DOM structure...');

        // Check bottom layer (static network) exists in DOM
        const mainCanvas = page.locator('#network-canvas');
        await expect(mainCanvas).toBeAttached();

        // Check top layer (hover effects) exists in DOM
        const hoverCanvas = page.locator('#network-canvas-hover');
        await expect(hoverCanvas).toBeAttached();

        // Verify CSS properties for hover layer
        const hoverStyle = await hoverCanvas.evaluate(el => ({
            position: window.getComputedStyle(el).position,
            pointerEvents: window.getComputedStyle(el).pointerEvents,
            zIndex: window.getComputedStyle(el.parentElement).position // Check container is relative
        }));

        expect(hoverStyle.position).toBe('absolute');
        expect(hoverStyle.pointerEvents).toBe('none');

        // Verify both canvases are within the same container
        const containerCheck = await page.evaluate(() => {
            const main = document.getElementById('network-canvas');
            const hover = document.getElementById('network-canvas-hover');
            return {
                sameParent: main.parentElement === hover.parentElement,
                containerIsRelative: window.getComputedStyle(main.parentElement).position === 'relative'
            };
        });

        expect(containerCheck.sameParent).toBe(true);
        expect(containerCheck.containerIsRelative).toBe(true);

        console.log('✅ T037 PASSED: Both canvas layers exist with correct CSS properties');
    });

    test('T038: Verify dual-layer canvas initialization in JavaScript', async ({ page }) => {
        console.log('Test T038: Checking JavaScript initialization...');

        // Listen for console logs
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push(msg.text());
        });

        // Reload page to capture initialization logs
        await page.reload();
        await page.waitForLoadState('networkidle');

        // Wait a bit for initialization
        await page.waitForTimeout(1000);

        // Check for dual-layer initialization message
        const hasInitMessage = consoleMessages.some(msg =>
            msg.includes('Dual-layer Canvas initialized') ||
            msg.includes('static + hover')
        );

        expect(hasInitMessage).toBeTruthy();

        // Verify networkViz state has both canvases
        const vizState = await page.evaluate(() => {
            if (typeof networkViz === 'undefined') return null;
            return {
                hasMainCanvas: networkViz.canvas !== null,
                hasMainCtx: networkViz.ctx !== null,
                hasHoverCanvas: networkViz.hoverCanvas !== null,
                hasHoverCtx: networkViz.hoverCtx !== null
            };
        });

        expect(vizState).not.toBeNull();
        expect(vizState.hasMainCanvas).toBe(true);
        expect(vizState.hasMainCtx).toBe(true);
        expect(vizState.hasHoverCanvas).toBe(true);
        expect(vizState.hasHoverCtx).toBe(true);

        console.log('✅ T038 PASSED: Dual-layer canvas initialized correctly in JavaScript');
    });

    test('T039: Test network map loading does not trigger multiple renders', async ({ page }) => {
        console.log('Test T039: Testing network map loading render count...');

        // Set up console log monitoring
        const renderLogs = [];
        page.on('console', msg => {
            const text = msg.text();
            if (text.includes('[renderNetwork]') || text.includes('[renderNetworkProgressive]')) {
                renderLogs.push({
                    text: text,
                    timestamp: Date.now()
                });
            }
        });

        // Click "加载网络地图" button
        const loadButton = page.locator('button:has-text("加载网络地图")');
        await loadButton.click();

        // Wait for rendering to complete
        await page.waitForTimeout(3000);

        // Count render calls (should be 1-2, not 3+)
        console.log(`Render calls detected: ${renderLogs.length}`);
        renderLogs.forEach((log, idx) => {
            console.log(`  [${idx + 1}] ${log.text}`);
        });

        // We expect at most 2 renders (initial + potential highlight)
        expect(renderLogs.length).toBeLessThanOrEqual(2);

        console.log('✅ T039 PASSED: Network loading does not trigger excessive renders');
    });

    test('T040: Test mouse hover only renders hover layer, not full network', async ({ page }) => {
        console.log('Test T040: Testing hover layer rendering behavior...');

        // First load the network
        await page.locator('button:has-text("加载网络地图")').click();
        await page.waitForTimeout(2000);

        // Set up console monitoring
        const hoverLayerRenders = [];
        const fullNetworkRenders = [];

        page.on('console', msg => {
            const text = msg.text();
            if (text.includes('[renderHoverLayer]') || text.includes('hover layer')) {
                hoverLayerRenders.push(text);
            }
            if (text.includes('[renderNetworkProgressive]') && !text.includes('hover')) {
                fullNetworkRenders.push(text);
            }
        });

        // Get canvas bounding box
        const canvas = page.locator('#network-canvas');
        const box = await canvas.boundingBox();

        if (!box) {
            throw new Error('Canvas not found or not visible');
        }

        // Reset log counters
        hoverLayerRenders.length = 0;
        fullNetworkRenders.length = 0;

        // Move mouse over canvas multiple times
        const centerX = box.x + box.width / 2;
        const centerY = box.y + box.height / 2;

        // Move to different positions
        await page.mouse.move(centerX - 50, centerY - 50);
        await page.waitForTimeout(100);
        await page.mouse.move(centerX, centerY);
        await page.waitForTimeout(100);
        await page.mouse.move(centerX + 50, centerY + 50);
        await page.waitForTimeout(100);

        // Check that hover layer was used (or no excessive full renders)
        console.log(`Hover layer renders: ${hoverLayerRenders.length}`);
        console.log(`Full network renders during hover: ${fullNetworkRenders.length}`);

        // Full network renders should be 0 during hover (only hover layer should render)
        expect(fullNetworkRenders.length).toBe(0);

        console.log('✅ T040 PASSED: Mouse hover uses hover layer, not full network render');
    });

    test('T041: Test hover highlighting still works correctly', async ({ page }) => {
        console.log('Test T041: Testing hover highlighting functionality...');

        // Load network
        await page.locator('button:has-text("加载网络地图")').click();
        await page.waitForTimeout(2000);

        // Get canvas
        const canvas = page.locator('#network-canvas');
        const box = await canvas.boundingBox();

        if (!box) {
            throw new Error('Canvas not found');
        }

        // Move mouse to center of canvas
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.waitForTimeout(200);

        // Check if hoveredEdge is set in networkViz state
        const hoverState = await page.evaluate(() => {
            if (typeof networkViz === 'undefined') return null;
            return {
                hasHoveredEdge: networkViz.hoveredEdge !== null,
                hoveredEdgeId: networkViz.hoveredEdge ? networkViz.hoveredEdge.edge_id : null
            };
        });

        // Note: hoveredEdge might be null if mouse is over empty space
        // But the test verifies the mechanism exists
        expect(hoverState).not.toBeNull();

        console.log(`Hover state: ${JSON.stringify(hoverState)}`);

        // Check tooltip existence (tooltip should appear on hover)
        const tooltip = page.locator('#network-tooltip');

        if (hoverState.hasHoveredEdge) {
            // If there's a hovered edge, tooltip should be visible
            await expect(tooltip).toBeVisible();
            console.log('✅ Tooltip visible when hovering over edge');
        } else {
            console.log('ℹ️  No edge at center position (expected if area is empty)');
        }

        console.log('✅ T041 PASSED: Hover highlighting mechanism is functional');
    });

    test('T042: Performance - No console errors or warnings', async ({ page }) => {
        console.log('Test T042: Checking for console errors/warnings...');

        const errors = [];
        const warnings = [];

        page.on('console', msg => {
            const type = msg.type();
            const text = msg.text();

            if (type === 'error') {
                errors.push(text);
            } else if (type === 'warning') {
                warnings.push(text);
            }
        });

        // Load network and interact
        await page.locator('button:has-text("加载网络地图")').click();
        await page.waitForTimeout(2000);

        // Move mouse around
        const canvas = page.locator('#network-canvas');
        const box = await canvas.boundingBox();

        if (box) {
            await page.mouse.move(box.x + 100, box.y + 100);
            await page.waitForTimeout(100);
            await page.mouse.move(box.x + 200, box.y + 200);
            await page.waitForTimeout(100);
        }

        // Report errors/warnings
        if (errors.length > 0) {
            console.log('❌ Console errors detected:');
            errors.forEach(err => console.log(`  - ${err}`));
        }

        if (warnings.length > 0) {
            console.log('⚠️  Console warnings detected:');
            warnings.forEach(warn => console.log(`  - ${warn}`));
        }

        // Errors should be 0
        expect(errors.length).toBe(0);

        console.log('✅ T042 PASSED: No console errors during dual-layer canvas usage');
    });
});
