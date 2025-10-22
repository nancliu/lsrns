/**
 * Playwright E2E Tests for Network Visualization Performance
 *
 * Tests loading stability, performance metrics, and rendering behavior
 * for the Canvas-based network visualization component.
 */

const { test, expect } = require('@playwright/test');

// Test configuration
const BASE_URL = 'http://localhost:8000';
const VISUALIZATION_TIMEOUT = 30000; // 30 seconds max for loading

test.describe('Network Visualization Performance Tests', () => {

    test.beforeEach(async ({ page }) => {
        // Navigate to templates page
        await page.goto(`${BASE_URL}/control/templates.html`);

        // Wait for page to be fully loaded
        await page.waitForLoadState('networkidle');

        // Wait for network_viz.js to load
        await page.waitForFunction(() => typeof window.networkViz !== 'undefined', {
            timeout: 10000
        });
    });


    test('T1: Measure initial visualization load time', async ({ page }) => {
        console.log('\n=== T1: Initial Load Performance ===');

        // Navigate to step 2 (select first template)
        await page.click('button:has-text("加载网络地图")');

        // Start timing
        const startTime = Date.now();

        // Wait for API call to complete
        const apiResponsePromise = page.waitForResponse(
            response => response.url().includes('/api/v1/control/edges/network_geometry'),
            { timeout: VISUALIZATION_TIMEOUT }
        );

        // Click load button
        await page.click('button:has-text("加载网络地图")');

        // Wait for API response
        const apiResponse = await apiResponsePromise;
        const apiTime = Date.now() - startTime;

        // Get response size
        const responseData = await apiResponse.json();
        const junctionCount = responseData.junctions?.length || 0;
        const edgeCount = responseData.edges?.length || 0;

        console.log(`  API Response Time: ${apiTime}ms`);
        console.log(`  Data Size: ${junctionCount} junctions, ${edgeCount} edges`);

        // Wait for Canvas to render
        await page.waitForFunction(() => {
            const canvas = document.getElementById('network-canvas');
            if (!canvas) return false;

            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

            // Check if Canvas has any non-white pixels (network is rendered)
            for (let i = 0; i < imageData.data.length; i += 4) {
                const r = imageData.data[i];
                const g = imageData.data[i + 1];
                const b = imageData.data[i + 2];

                // Not background color (245, 247, 250)
                if (r !== 245 || g !== 247 || b !== 250) {
                    return true;
                }
            }
            return false;
        }, { timeout: 10000 });

        const totalTime = Date.now() - startTime;
        const renderTime = totalTime - apiTime;

        console.log(`  Render Time: ${renderTime}ms`);
        console.log(`  Total Load Time: ${totalTime}ms`);

        // Performance assertions
        expect(apiTime).toBeLessThan(15000); // API should respond within 15s
        expect(renderTime).toBeLessThan(5000); // Rendering should take < 5s
        expect(totalTime).toBeLessThan(20000); // Total should be < 20s

        // Verify Canvas has content
        const canvasPixels = await page.evaluate(() => {
            const canvas = document.getElementById('network-canvas');
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

            let nonBackgroundPixels = 0;
            for (let i = 0; i < imageData.data.length; i += 4) {
                const r = imageData.data[i];
                const g = imageData.data[i + 1];
                const b = imageData.data[i + 2];
                if (r !== 245 || g !== 247 || b !== 250) {
                    nonBackgroundPixels++;
                }
            }
            return nonBackgroundPixels;
        });

        console.log(`  Canvas Non-Background Pixels: ${canvasPixels}`);
        expect(canvasPixels).toBeGreaterThan(1000); // Should have significant content
    });


    test('T2: Test reload stability (5 consecutive reloads)', async ({ page }) => {
        console.log('\n=== T2: Reload Stability Test ===');

        const loadTimes = [];
        const errors = [];

        for (let i = 1; i <= 5; i++) {
            console.log(`  Reload ${i}/5...`);

            try {
                const startTime = Date.now();

                // Click reload button
                await page.click('button:has-text("重置视图")');

                // Wait a bit before clicking load again
                await page.waitForTimeout(500);

                // Click load button
                const responsePromise = page.waitForResponse(
                    response => response.url().includes('/api/v1/control/edges/network_geometry'),
                    { timeout: VISUALIZATION_TIMEOUT }
                );

                await page.click('button:has-text("加载网络地图")');
                await responsePromise;

                // Wait for rendering
                await page.waitForTimeout(1000);

                const loadTime = Date.now() - startTime;
                loadTimes.push(loadTime);

                console.log(`    Load ${i}: ${loadTime}ms`);

            } catch (error) {
                errors.push({ reload: i, error: error.message });
                console.log(`    Load ${i}: FAILED - ${error.message}`);
            }
        }

        // Calculate statistics
        const avgTime = loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length;
        const maxTime = Math.max(...loadTimes);
        const minTime = Math.min(...loadTimes);
        const variance = loadTimes.reduce((sum, t) => sum + Math.pow(t - avgTime, 2), 0) / loadTimes.length;
        const stdDev = Math.sqrt(variance);

        console.log(`\n  Statistics:`);
        console.log(`    Average: ${avgTime.toFixed(0)}ms`);
        console.log(`    Min: ${minTime}ms`);
        console.log(`    Max: ${maxTime}ms`);
        console.log(`    Std Dev: ${stdDev.toFixed(0)}ms`);
        console.log(`    Success Rate: ${loadTimes.length}/5 (${(loadTimes.length/5*100).toFixed(0)}%)`);

        // Stability assertions
        expect(errors).toHaveLength(0); // No errors
        expect(stdDev).toBeLessThan(3000); // Consistent load times (std dev < 3s)
    });


    test('T3: Test filtered vs full network load performance', async ({ page }) => {
        console.log('\n=== T3: Filtered vs Full Network Performance ===');

        // Test 1: Load full network
        console.log('  Loading FULL network...');
        let startTime = Date.now();

        await page.click('button:has-text("加载网络地图")');

        const fullNetworkResponse = await page.waitForResponse(
            response => response.url().includes('/api/v1/control/edges/network_geometry')
                     && !response.url().includes('route_codes='),
            { timeout: VISUALIZATION_TIMEOUT }
        );

        const fullData = await fullNetworkResponse.json();
        const fullLoadTime = Date.now() - startTime;

        console.log(`    Full Network: ${fullLoadTime}ms (${fullData.junctions.length} junctions, ${fullData.edges.length} edges)`);

        // Wait for rendering
        await page.waitForTimeout(2000);

        // Test 2: Load filtered network (G5 route only)
        console.log('  Loading FILTERED network (G5 only)...');

        // Clear visualization first
        await page.click('button:has-text("清除可视化选择")');
        await page.waitForTimeout(500);

        startTime = Date.now();

        // Mock selecting G5 route (need to check actual UI structure)
        await page.evaluate(() => {
            // Simulate selecting G5 route
            if (typeof window.loadVisualization === 'function') {
                window.loadVisualization(['G5']);
            }
        });

        const filteredResponse = await page.waitForResponse(
            response => response.url().includes('/api/v1/control/edges/network_geometry')
                     && response.url().includes('route_codes=G5'),
            { timeout: VISUALIZATION_TIMEOUT }
        );

        const filteredData = await filteredResponse.json();
        const filteredLoadTime = Date.now() - startTime;

        console.log(`    Filtered Network: ${filteredLoadTime}ms (${filteredData.junctions.length} junctions, ${filteredData.edges.length} edges)`);

        // Calculate performance improvement
        const speedup = ((fullLoadTime - filteredLoadTime) / fullLoadTime * 100).toFixed(1);
        const dataReduction = ((1 - filteredData.edges.length / fullData.edges.length) * 100).toFixed(1);

        console.log(`\n  Performance Improvement:`);
        console.log(`    Speed Up: ${speedup}% faster`);
        console.log(`    Data Reduction: ${dataReduction}% fewer edges`);

        // Performance assertions
        expect(filteredLoadTime).toBeLessThan(fullLoadTime); // Filtered should be faster
        expect(filteredData.edges.length).toBeLessThan(fullData.edges.length); // Filtered should have fewer edges
    });


    test('T4: Diagnose rendering bottlenecks with performance marks', async ({ page }) => {
        console.log('\n=== T4: Rendering Performance Analysis ===');

        // Inject performance measurement code
        await page.addInitScript(() => {
            window.perfMarks = {
                apiStart: 0,
                apiEnd: 0,
                renderStart: 0,
                renderEnd: 0,
                edgesRendered: 0,
                junctionsRendered: 0
            };
        });

        // Override loadNetworkGeometry to add performance marks
        await page.evaluate(() => {
            const originalLoadGeometry = window.networkViz.loadGeometry;

            window.networkViz.loadGeometry = async function(routeCodes) {
                window.perfMarks.apiStart = performance.now();

                const result = await originalLoadGeometry.call(this, routeCodes);

                window.perfMarks.apiEnd = performance.now();

                return result;
            };

            // Override renderNetwork to add timing
            const originalRender = window.networkViz.render;

            window.networkViz.render = function() {
                window.perfMarks.renderStart = performance.now();

                originalRender.call(this);

                window.perfMarks.renderEnd = performance.now();
            };
        });

        // Trigger load
        await page.click('button:has-text("加载网络地图")');

        // Wait for completion
        await page.waitForResponse(
            response => response.url().includes('/api/v1/control/edges/network_geometry'),
            { timeout: VISUALIZATION_TIMEOUT }
        );

        await page.waitForTimeout(3000); // Wait for rendering

        // Get performance metrics
        const perfData = await page.evaluate(() => window.perfMarks);

        const apiTime = perfData.apiEnd - perfData.apiStart;
        const renderTime = perfData.renderEnd - perfData.renderStart;

        console.log(`  API Fetch Time: ${apiTime.toFixed(1)}ms`);
        console.log(`  Canvas Render Time: ${renderTime.toFixed(1)}ms`);

        // Get geometry data size
        const geometryInfo = await page.evaluate(() => {
            if (!window.networkViz || !networkViz.geometry) return null;

            return {
                junctions: networkViz.geometry.junctions.length,
                edges: networkViz.geometry.edges.length
            };
        });

        console.log(`  Geometry: ${geometryInfo.junctions} junctions, ${geometryInfo.edges} edges`);

        // Calculate render efficiency
        const edgesPerMs = (geometryInfo.edges / renderTime).toFixed(1);
        console.log(`  Render Efficiency: ${edgesPerMs} edges/ms`);

        // Performance assertions
        expect(apiTime).toBeLessThan(15000); // API < 15s
        expect(renderTime).toBeLessThan(3000); // Render < 3s for full network
        expect(edgesPerMs).toBeGreaterThan(1); // Should render at least 1 edge per ms
    });


    test('T5: Test zoom and pan performance', async ({ page }) => {
        console.log('\n=== T5: Zoom/Pan Performance Test ===');

        // Load visualization first
        await page.click('button:has-text("加载网络地图")');

        await page.waitForResponse(
            response => response.url().includes('/api/v1/control/edges/network_geometry'),
            { timeout: VISUALIZATION_TIMEOUT }
        );

        await page.waitForTimeout(2000);

        const canvas = await page.locator('#network-canvas');
        const canvasBox = await canvas.boundingBox();

        // Test zoom performance
        console.log('  Testing zoom performance...');

        const zoomStartTime = Date.now();

        // Simulate 10 zoom operations
        for (let i = 0; i < 10; i++) {
            await page.mouse.move(canvasBox.x + canvasBox.width / 2, canvasBox.y + canvasBox.height / 2);
            await page.mouse.wheel(0, i % 2 === 0 ? -100 : 100); // Zoom in/out
            await page.waitForTimeout(50);
        }

        const zoomTime = Date.now() - zoomStartTime;
        const avgZoomTime = zoomTime / 10;

        console.log(`    Total Zoom Time: ${zoomTime}ms`);
        console.log(`    Avg Zoom Response: ${avgZoomTime.toFixed(1)}ms`);

        // Test pan performance
        console.log('  Testing pan performance...');

        const panStartTime = Date.now();

        // Simulate drag operations
        await page.mouse.move(canvasBox.x + 100, canvasBox.y + 100);
        await page.mouse.down();

        for (let i = 0; i < 20; i++) {
            await page.mouse.move(
                canvasBox.x + 100 + i * 5,
                canvasBox.y + 100 + i * 3
            );
            await page.waitForTimeout(20);
        }

        await page.mouse.up();

        const panTime = Date.now() - panStartTime;
        const avgPanTime = panTime / 20;

        console.log(`    Total Pan Time: ${panTime}ms`);
        console.log(`    Avg Pan Response: ${avgPanTime.toFixed(1)}ms`);

        // Interaction performance assertions
        expect(avgZoomTime).toBeLessThan(100); // Zoom should respond < 100ms
        expect(avgPanTime).toBeLessThan(50); // Pan should respond < 50ms
    });

});


test.describe('Network Visualization Load Failures', () => {

    test('T6: Test behavior on network timeout', async ({ page }) => {
        console.log('\n=== T6: Network Timeout Handling ===');

        // Intercept API and delay response
        await page.route('**/api/v1/control/edges/network_geometry*', async route => {
            // Delay for 35 seconds (exceeds timeout)
            await page.waitForTimeout(35000);
            route.continue();
        });

        await page.goto(`${BASE_URL}/control/templates.html`);

        // Try to load visualization
        await page.click('button:has-text("加载网络地图")');

        // Wait and check error handling
        await page.waitForTimeout(5000);

        // Check if error message is displayed
        const errorVisible = await page.locator('.viz-error').isVisible();

        console.log(`  Error Message Displayed: ${errorVisible}`);

        expect(errorVisible).toBe(true); // Should show error
    });


    test('T7: Test behavior on invalid data', async ({ page }) => {
        console.log('\n=== T7: Invalid Data Handling ===');

        // Intercept API and return invalid data
        await page.route('**/api/v1/control/edges/network_geometry*', async route => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    junctions: [], // Empty data
                    edges: []
                })
            });
        });

        await page.goto(`${BASE_URL}/control/templates.html`);

        // Try to load visualization
        await page.click('button:has-text("加载网络地图")');

        await page.waitForTimeout(2000);

        // Check if empty state is displayed
        const emptyVisible = await page.locator('.viz-empty').isVisible();

        console.log(`  Empty State Displayed: ${emptyVisible}`);

        expect(emptyVisible).toBe(true); // Should show empty state
    });

});
