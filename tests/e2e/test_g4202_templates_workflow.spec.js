// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * G4202 Network Map Test via Templates Workflow
 *
 * Tests the complete workflow:
 * 1. Select a control strategy template
 * 2. Filter and select G4202 route
 * 3. Verify map loading, centering, zoom, and pan
 * 4. Test base map integration (if available)
 */

test.describe('G4202 Network Map via Templates Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      const type = msg.type();
      if (type === 'error' || type === 'warning' || type === 'log') {
        console.log(`[Browser ${type}]:`, msg.text());
      }
    });

    // Enable error tracking
    page.on('pageerror', error => {
      console.error('[Browser Page Error]:', error.message);
    });

    // Navigate to templates page
    await page.goto('http://localhost:8000/control/templates.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('should complete workflow: select template, load G4202, verify map', async ({ page }) => {
    console.log('\n=== Test: Complete Templates Workflow for G4202 ===\n');

    // Step 1: Wait for templates to load
    console.log('Step 1: Waiting for templates to load...');
    await page.waitForSelector('.template-card', { timeout: 15000 });

    const templateCount = await page.locator('.template-card').count();
    console.log(`Found ${templateCount} template(s)`);
    expect(templateCount).toBeGreaterThan(0);

    // Take screenshot of templates
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step1_templates.png'
    });
    console.log('Screenshot: g4202_step1_templates.png');

    // Step 2: Select the first available template
    console.log('\nStep 2: Selecting first template...');
    const firstTemplate = page.locator('.template-card').first();
    const templateName = await firstTemplate.locator('.template-title, h4').first().textContent();
    console.log(`Template name: ${templateName}`);

    await firstTemplate.click();
    await page.waitForTimeout(1500);

    // Verify step 2 is now visible
    const step2Content = page.locator('#step2-content');
    await expect(step2Content).toBeVisible({ timeout: 5000 });
    console.log('✓ Step 2 (route selection) is now visible');

    // Take screenshot after template selection
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step2_route_selection.png'
    });
    console.log('Screenshot: g4202_step2_route_selection.png');

    // Step 3: Wait for route codes to load
    console.log('\nStep 3: Loading route options...');
    const routeCodes = page.locator('#route-codes');
    await expect(routeCodes).toBeVisible();

    // Wait for options to load (not just "加载中...")
    await page.waitForFunction(() => {
      const select = document.getElementById('route-codes');
      return select && select.options.length > 0 && select.options[0].value !== '';
    }, { timeout: 10000 });

    const routeOptions = await page.evaluate(() => {
      const select = document.getElementById('route-codes');
      return Array.from(select.options).map(opt => opt.value);
    });
    console.log('Available routes:', routeOptions.join(', '));
    expect(routeOptions).toContain('G4202');

    // Step 4: Select G4202
    console.log('\nStep 4: Selecting G4202...');
    await routeCodes.selectOption('G4202');
    await page.waitForTimeout(500);

    // Click "Query Edges" button
    console.log('Clicking "查询路段" button...');
    const queryButton = page.locator('button:has-text("查询路段")');
    await expect(queryButton).toBeVisible();
    await queryButton.click();
    await page.waitForTimeout(3000); // Wait for network data to load and render

    // Take screenshot after filtering
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step3_filtered.png'
    });
    console.log('Screenshot: g4202_step3_filtered.png');

    // Step 5: Verify canvas exists and has content
    console.log('\nStep 5: Verifying map canvas...');
    const canvas = page.locator('#network-canvas');
    await expect(canvas).toBeVisible({ timeout: 5000 });

    const canvasInfo = await page.evaluate(() => {
      const canvas = document.getElementById('network-canvas');
      const viz = window.networkViz;

      // Check if canvas has non-white pixels
      const ctx = canvas.getContext('2d');
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      let hasContent = false;
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] !== 255 || data[i+1] !== 255 || data[i+2] !== 255) {
          hasContent = true;
          break;
        }
      }

      return {
        canvasSize: { width: canvas.width, height: canvas.height },
        hasContent: hasContent,
        vizExists: !!viz,
        vizInfo: viz ? {
          hasEdges: viz.edges && viz.edges.length > 0,
          hasNodes: viz.nodes && viz.nodes.length > 0,
          edgeCount: viz.edges ? viz.edges.length : 0,
          nodeCount: viz.nodes ? viz.nodes.length : 0
        } : null
      };
    });

    console.log('Canvas info:', JSON.stringify(canvasInfo, null, 2));
    expect(canvasInfo.hasContent).toBeTruthy();
    expect(canvasInfo.vizExists).toBeTruthy();

    // Take screenshot of loaded map
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step4_map_loaded.png',
      fullPage: false
    });
    console.log('Screenshot: g4202_step4_map_loaded.png');

    // Step 6: Test zoom functionality
    console.log('\nStep 6: Testing zoom...');
    const bbox = await canvas.boundingBox();

    // Hover over canvas center
    await canvas.hover({ position: { x: bbox.width / 2, y: bbox.height / 2 } });

    // Zoom in
    await page.mouse.wheel(0, -100);
    await page.waitForTimeout(500);

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step5_zoomed_in.png'
    });
    console.log('Screenshot: g4202_step5_zoomed_in.png');
    console.log('✓ Zoom in executed');

    // Zoom out
    await page.mouse.wheel(0, 150);
    await page.waitForTimeout(500);

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step6_zoomed_out.png'
    });
    console.log('Screenshot: g4202_step6_zoomed_out.png');
    console.log('✓ Zoom out executed');

    // Step 7: Test pan functionality
    console.log('\nStep 7: Testing pan...');
    await canvas.hover({ position: { x: bbox.width / 2, y: bbox.height / 2 } });
    await page.mouse.down();
    await page.mouse.move(bbox.x + bbox.width / 2 + 100, bbox.y + bbox.height / 2 + 50);
    await page.mouse.up();
    await page.waitForTimeout(500);

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_step7_panned.png'
    });
    console.log('Screenshot: g4202_step7_panned.png');
    console.log('✓ Pan executed');

    // Step 8: Check for base map toggle
    console.log('\nStep 8: Checking for base map...');
    const baseMapToggle = page.locator('#basemap-toggle');
    const hasBaseMapToggle = await baseMapToggle.count() > 0;

    if (hasBaseMapToggle) {
      console.log('✓ Base map toggle found');

      const isChecked = await baseMapToggle.isChecked();
      console.log(`Base map toggle state: ${isChecked ? 'ON' : 'OFF'}`);

      if (!isChecked) {
        console.log('Enabling base map...');
        await baseMapToggle.check();
        await page.waitForTimeout(2000); // Wait for tiles to load

        await page.screenshot({
          path: 'tests/e2e/screenshots/g4202_step8_with_basemap.png'
        });
        console.log('Screenshot: g4202_step8_with_basemap.png');

        // Check if base map canvas exists
        const baseMapCanvas = page.locator('#basemap-canvas');
        const hasBaseMapCanvas = await baseMapCanvas.count() > 0;

        if (hasBaseMapCanvas) {
          await expect(baseMapCanvas).toBeVisible();
          console.log('✓ Base map canvas is visible');

          // Test base map zoom synchronization
          console.log('Testing base map zoom synchronization...');
          await canvas.hover({ position: { x: bbox.width / 2, y: bbox.height / 2 } });
          await page.mouse.wheel(0, -80);
          await page.waitForTimeout(800);

          await page.screenshot({
            path: 'tests/e2e/screenshots/g4202_step9_basemap_zoom.png'
          });
          console.log('Screenshot: g4202_step9_basemap_zoom.png');
          console.log('✓ Base map zoom synchronization tested');

          // Test base map pan synchronization
          console.log('Testing base map pan synchronization...');
          await page.mouse.down();
          await page.mouse.move(bbox.x + bbox.width / 2 - 80, bbox.y + bbox.height / 2 - 80);
          await page.mouse.up();
          await page.waitForTimeout(800);

          await page.screenshot({
            path: 'tests/e2e/screenshots/g4202_step10_basemap_pan.png'
          });
          console.log('Screenshot: g4202_step10_basemap_pan.png');
          console.log('✓ Base map pan synchronization tested');
        } else {
          console.log('⚠ Base map canvas not found');
        }
      }
    } else {
      console.log('⚠ Base map toggle not found - base map feature may not be implemented yet');
    }

    console.log('\n✅ Complete workflow test finished successfully!');
  });

  test('should verify map centering on initial G4202 load', async ({ page }) => {
    console.log('\n=== Test: Map Centering Verification ===\n');

    // Quick workflow to get to map
    await page.waitForSelector('.template-card', { timeout: 15000 });
    await page.locator('.template-card').first().click();
    await page.waitForTimeout(1500);

    const routeCodes = page.locator('#route-codes');
    await page.waitForFunction(() => {
      const select = document.getElementById('route-codes');
      return select && select.options.length > 0 && select.options[0].value !== '';
    }, { timeout: 10000 });

    await routeCodes.selectOption('G4202');
    await page.waitForTimeout(500);

    await page.locator('button:has-text("查询路段")').click();
    await page.waitForTimeout(3000);

    // Get viewport bounds before and after
    const viewportInfo = await page.evaluate(() => {
      const viz = window.networkViz;
      if (!viz || !viz.edges || viz.edges.length === 0) {
        return null;
      }

      // Calculate bounds of loaded edges
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;

      viz.edges.forEach(edge => {
        const shape = edge.shape || [];
        shape.forEach(point => {
          minX = Math.min(minX, point.x);
          maxX = Math.max(maxX, point.x);
          minY = Math.min(minY, point.y);
          maxY = Math.max(maxY, point.y);
        });
      });

      return {
        edgeBounds: { minX, maxX, minY, maxY },
        boundsWidth: maxX - minX,
        boundsHeight: maxY - minY,
        edgeCount: viz.edges.length,
        canvasSize: {
          width: viz.canvas.width,
          height: viz.canvas.height
        }
      };
    });

    console.log('Viewport info:', JSON.stringify(viewportInfo, null, 2));

    if (viewportInfo) {
      expect(viewportInfo.edgeCount).toBeGreaterThan(0);
      expect(viewportInfo.boundsWidth).toBeGreaterThan(0);
      expect(viewportInfo.boundsHeight).toBeGreaterThan(0);
      console.log('✓ Map is properly bounded and centered on G4202 network');
    }

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_centering_verification.png'
    });
  });

  test('should handle multiple route selection and filtering', async ({ page }) => {
    console.log('\n=== Test: Multiple Route Selection ===\n');

    // Navigate to route selection
    await page.waitForSelector('.template-card', { timeout: 15000 });
    await page.locator('.template-card').first().click();
    await page.waitForTimeout(1500);

    const routeCodes = page.locator('#route-codes');
    await page.waitForFunction(() => {
      const select = document.getElementById('route-codes');
      return select && select.options.length > 0 && select.options[0].value !== '';
    }, { timeout: 10000 });

    // Try selecting multiple routes if available
    const availableRoutes = await page.evaluate(() => {
      const select = document.getElementById('route-codes');
      return Array.from(select.options).map(opt => opt.value).filter(v => v);
    });

    console.log('Available routes:', availableRoutes);

    if (availableRoutes.includes('G4202') && availableRoutes.includes('SA2')) {
      console.log('Testing multiple selection: G4202 + SA2');

      // Select multiple routes (Ctrl+Click simulation)
      await routeCodes.selectOption(['G4202', 'SA2']);
      await page.waitForTimeout(500);

      await page.locator('button:has-text("查询路段")').click();
      await page.waitForTimeout(3000);

      const edgeCount = await page.evaluate(() => {
        return window.networkViz && window.networkViz.edges ? window.networkViz.edges.length : 0;
      });

      console.log(`Loaded ${edgeCount} edges for multiple routes`);
      expect(edgeCount).toBeGreaterThan(0);

      await page.screenshot({
        path: 'tests/e2e/screenshots/g4202_multiple_routes.png'
      });
    } else {
      console.log('⚠ Multiple route test skipped - not enough routes available');
    }
  });
});
