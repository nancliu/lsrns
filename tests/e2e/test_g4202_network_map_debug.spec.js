// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * G4202 Network Map Loading Debug Test
 *
 * Tests:
 * 1. Map centering when G4202 is selected
 * 2. Pan and zoom functionality
 * 3. Base map and network overlay alignment
 * 4. Base map pan/zoom synchronization
 */

test.describe('G4202 Network Map Loading Debug', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        console.log(`[Browser ${msg.type()}]:`, msg.text());
      }
    });

    // Enable error tracking
    page.on('pageerror', error => {
      console.error('[Browser Page Error]:', error.message);
    });

    // Navigate to templates page (control module)
    await page.goto('http://localhost:8000/templates.html');
    await page.waitForLoadState('networkidle');

    // Wait for page initialization
    await page.waitForTimeout(2000);
  });

  test('should load and center map when G4202 is selected', async ({ page }) => {
    console.log('\n=== Test 1: Map Centering for G4202 ===\n');

    // Select G4202 route in the multi-select
    const routeCodes = page.locator('#route-codes');
    await expect(routeCodes).toBeVisible({ timeout: 10000 });

    // Select G4202 option
    await routeCodes.selectOption('G4202');
    await page.waitForTimeout(500);

    // Click "Apply Filter" button to trigger network loading
    const applyButton = page.locator('button:has-text("应用筛选")');
    await applyButton.click();
    await page.waitForTimeout(2000);

    // Get canvas element
    const canvas = page.locator('#network-canvas');
    await expect(canvas).toBeVisible({ timeout: 10000 });

    // Get canvas dimensions
    const canvasBBox = await canvas.boundingBox();
    console.log('Canvas dimensions:', canvasBBox);

    // Check if network is drawn (canvas should have content)
    const hasContent = await page.evaluate(() => {
      const canvas = document.getElementById('network-canvas');
      if (!canvas) return false;

      const ctx = canvas.getContext('2d');
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // Check if there are non-white pixels
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] !== 255 || data[i+1] !== 255 || data[i+2] !== 255) {
          return true;
        }
      }
      return false;
    });

    console.log('Canvas has network content:', hasContent);
    expect(hasContent).toBeTruthy();

    // Get viewport information
    const viewportInfo = await page.evaluate(() => {
      const viz = window.networkViz;
      if (!viz) return null;

      return {
        scale: viz.scale,
        offsetX: viz.offsetX,
        offsetY: viz.offsetY,
        canvasWidth: viz.canvas.width,
        canvasHeight: viz.canvas.height,
        edgeCount: viz.edges ? viz.edges.length : 0,
        nodeCount: viz.nodes ? viz.nodes.length : 0
      };
    });

    console.log('Viewport info:', viewportInfo);
    expect(viewportInfo).not.toBeNull();
    expect(viewportInfo.edgeCount).toBeGreaterThan(0);
    expect(viewportInfo.nodeCount).toBeGreaterThan(0);

    // Check if scale is reasonable (not too zoomed in or out)
    expect(viewportInfo.scale).toBeGreaterThan(0.1);
    expect(viewportInfo.scale).toBeLessThan(10);

    // Take screenshot for visual verification
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_initial_load.png',
      fullPage: false
    });
    console.log('Screenshot saved: g4202_initial_load.png');
  });

  test('should support pan and zoom operations', async ({ page }) => {
    console.log('\n=== Test 2: Pan and Zoom Functionality ===\n');

    // Select G4202 route
    const routeCodes = page.locator('#route-codes');
    await routeCodes.selectOption('G4202');
    await page.waitForTimeout(500);

    // Click "Apply Filter" button
    const applyButton = page.locator('button:has-text("应用筛选")');
    await applyButton.click();
    await page.waitForTimeout(2000);

    const canvas = page.locator('#network-canvas');
    const canvasBBox = await canvas.boundingBox();

    // Get initial viewport state
    const initialState = await page.evaluate(() => {
      const viz = window.networkViz;
      return {
        scale: viz.scale,
        offsetX: viz.offsetX,
        offsetY: viz.offsetY
      };
    });
    console.log('Initial state:', initialState);

    // Test zoom in (mouse wheel up)
    await canvas.hover({ position: { x: canvasBBox.width / 2, y: canvasBBox.height / 2 } });
    await page.mouse.wheel(0, -100); // Scroll up to zoom in
    await page.waitForTimeout(300);

    const zoomedInState = await page.evaluate(() => {
      const viz = window.networkViz;
      return {
        scale: viz.scale,
        offsetX: viz.offsetX,
        offsetY: viz.offsetY
      };
    });
    console.log('After zoom in:', zoomedInState);
    expect(zoomedInState.scale).toBeGreaterThan(initialState.scale);

    // Take screenshot after zoom in
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_zoomed_in.png',
      fullPage: false
    });

    // Test zoom out (mouse wheel down)
    await page.mouse.wheel(0, 200); // Scroll down to zoom out
    await page.waitForTimeout(300);

    const zoomedOutState = await page.evaluate(() => {
      const viz = window.networkViz;
      return {
        scale: viz.scale,
        offsetX: viz.offsetX,
        offsetY: viz.offsetY
      };
    });
    console.log('After zoom out:', zoomedOutState);
    expect(zoomedOutState.scale).toBeLessThan(zoomedInState.scale);

    // Test pan (drag)
    await canvas.hover({ position: { x: canvasBBox.width / 2, y: canvasBBox.height / 2 } });
    await page.mouse.down();
    await page.mouse.move(
      canvasBBox.x + canvasBBox.width / 2 + 100,
      canvasBBox.y + canvasBBox.height / 2 + 100
    );
    await page.mouse.up();
    await page.waitForTimeout(300);

    const pannedState = await page.evaluate(() => {
      const viz = window.networkViz;
      return {
        scale: viz.scale,
        offsetX: viz.offsetX,
        offsetY: viz.offsetY
      };
    });
    console.log('After pan:', pannedState);

    // Offset should have changed
    const offsetChanged =
      Math.abs(pannedState.offsetX - zoomedOutState.offsetX) > 10 ||
      Math.abs(pannedState.offsetY - zoomedOutState.offsetY) > 10;
    expect(offsetChanged).toBeTruthy();

    // Take screenshot after pan
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_panned.png',
      fullPage: false
    });
  });

  test('should load base map and check alignment with network', async ({ page }) => {
    console.log('\n=== Test 3: Base Map and Network Alignment ===\n');

    // Select G4202 route
    const routeCodes = page.locator('#route-codes');
    await routeCodes.selectOption('G4202');
    await page.waitForTimeout(500);

    // Click "Apply Filter" button
    const applyButton = page.locator('button:has-text("应用筛选")');
    await applyButton.click();
    await page.waitForTimeout(2000);

    // Enable base map if toggle exists
    const baseMapToggle = page.locator('#basemap-toggle');
    const toggleExists = await baseMapToggle.count() > 0;

    if (toggleExists) {
      console.log('Base map toggle found, enabling base map...');
      const isChecked = await baseMapToggle.isChecked();
      if (!isChecked) {
        await baseMapToggle.check();
        await page.waitForTimeout(1000); // Wait for base map to load
      }

      // Check if base map canvas exists
      const baseMapCanvas = page.locator('#basemap-canvas');
      const baseMapExists = await baseMapCanvas.count() > 0;
      console.log('Base map canvas exists:', baseMapExists);

      if (baseMapExists) {
        await expect(baseMapCanvas).toBeVisible();

        // Get base map info
        const baseMapInfo = await page.evaluate(() => {
          const baseMapCanvas = document.getElementById('basemap-canvas');
          const networkCanvas = document.getElementById('network-canvas');

          return {
            baseMap: {
              width: baseMapCanvas.width,
              height: baseMapCanvas.height,
              style: {
                width: baseMapCanvas.style.width,
                height: baseMapCanvas.style.height,
                position: baseMapCanvas.style.position,
                zIndex: baseMapCanvas.style.zIndex
              }
            },
            network: {
              width: networkCanvas.width,
              height: networkCanvas.height,
              style: {
                width: networkCanvas.style.width,
                height: networkCanvas.style.height,
                position: networkCanvas.style.position,
                zIndex: networkCanvas.style.zIndex
              }
            }
          };
        });

        console.log('Base map info:', JSON.stringify(baseMapInfo, null, 2));

        // Check if dimensions match
        expect(baseMapInfo.baseMap.width).toBe(baseMapInfo.network.width);
        expect(baseMapInfo.baseMap.height).toBe(baseMapInfo.network.height);

        // Take screenshot with base map
        await page.screenshot({
          path: 'tests/e2e/screenshots/g4202_with_basemap.png',
          fullPage: false
        });
        console.log('Screenshot saved: g4202_with_basemap.png');

        // Test if base map has content
        const baseMapHasContent = await page.evaluate(() => {
          const canvas = document.getElementById('basemap-canvas');
          if (!canvas) return false;

          const ctx = canvas.getContext('2d');
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;

          // Check if there are non-transparent pixels
          for (let i = 3; i < data.length; i += 4) {
            if (data[i] > 0) {
              return true;
            }
          }
          return false;
        });

        console.log('Base map has content:', baseMapHasContent);
        expect(baseMapHasContent).toBeTruthy();
      }
    } else {
      console.log('Base map toggle not found, skipping base map test');
    }
  });

  test('should synchronize base map pan and zoom with network', async ({ page }) => {
    console.log('\n=== Test 4: Base Map Pan/Zoom Synchronization ===\n');

    // Select G4202 route
    const routeCodes = page.locator('#route-codes');
    await routeCodes.selectOption('G4202');
    await page.waitForTimeout(500);

    // Click "Apply Filter" button
    const applyButton = page.locator('button:has-text("应用筛选")');
    await applyButton.click();
    await page.waitForTimeout(2000);

    // Enable base map
    const baseMapToggle = page.locator('#basemap-toggle');
    const toggleExists = await baseMapToggle.count() > 0;

    if (!toggleExists) {
      console.log('Base map toggle not found, skipping sync test');
      return;
    }

    const isChecked = await baseMapToggle.isChecked();
    if (!isChecked) {
      await baseMapToggle.check();
      await page.waitForTimeout(1000);
    }

    const canvas = page.locator('#network-canvas');
    const canvasBBox = await canvas.boundingBox();

    // Get initial state
    const initialState = await page.evaluate(() => {
      const viz = window.networkViz;
      const baseMapRenderer = window.baseMapRenderer;

      return {
        network: {
          scale: viz.scale,
          offsetX: viz.offsetX,
          offsetY: viz.offsetY
        },
        baseMap: baseMapRenderer ? {
          scale: baseMapRenderer.scale,
          offsetX: baseMapRenderer.offsetX,
          offsetY: baseMapRenderer.offsetY
        } : null
      };
    });
    console.log('Initial state:', JSON.stringify(initialState, null, 2));

    // Test zoom synchronization
    await canvas.hover({ position: { x: canvasBBox.width / 2, y: canvasBBox.height / 2 } });
    await page.mouse.wheel(0, -100);
    await page.waitForTimeout(300);

    const afterZoomState = await page.evaluate(() => {
      const viz = window.networkViz;
      const baseMapRenderer = window.baseMapRenderer;

      return {
        network: {
          scale: viz.scale,
          offsetX: viz.offsetX,
          offsetY: viz.offsetY
        },
        baseMap: baseMapRenderer ? {
          scale: baseMapRenderer.scale,
          offsetX: baseMapRenderer.offsetX,
          offsetY: baseMapRenderer.offsetY
        } : null
      };
    });
    console.log('After zoom:', JSON.stringify(afterZoomState, null, 2));

    // Check if scales are synchronized
    if (afterZoomState.baseMap) {
      const scaleRatio = afterZoomState.network.scale / afterZoomState.baseMap.scale;
      console.log('Scale ratio (network/basemap):', scaleRatio);

      // Scales should be the same or have a consistent ratio
      expect(Math.abs(scaleRatio - 1.0)).toBeLessThan(0.1); // Within 10% difference
    }

    // Take screenshot after zoom
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_basemap_zoomed.png',
      fullPage: false
    });

    // Test pan synchronization
    await canvas.hover({ position: { x: canvasBBox.width / 2, y: canvasBBox.height / 2 } });
    await page.mouse.down();
    await page.mouse.move(
      canvasBBox.x + canvasBBox.width / 2 + 100,
      canvasBBox.y + canvasBBox.height / 2 + 100
    );
    await page.mouse.up();
    await page.waitForTimeout(300);

    const afterPanState = await page.evaluate(() => {
      const viz = window.networkViz;
      const baseMapRenderer = window.baseMapRenderer;

      return {
        network: {
          scale: viz.scale,
          offsetX: viz.offsetX,
          offsetY: viz.offsetY
        },
        baseMap: baseMapRenderer ? {
          scale: baseMapRenderer.scale,
          offsetX: baseMapRenderer.offsetX,
          offsetY: baseMapRenderer.offsetY
        } : null
      };
    });
    console.log('After pan:', JSON.stringify(afterPanState, null, 2));

    // Take screenshot after pan
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_basemap_panned.png',
      fullPage: false
    });

    // Check if offsets changed together
    if (afterPanState.baseMap && initialState.baseMap) {
      const networkOffsetChange = {
        x: afterPanState.network.offsetX - initialState.network.offsetX,
        y: afterPanState.network.offsetY - initialState.network.offsetY
      };
      const baseMapOffsetChange = {
        x: afterPanState.baseMap.offsetX - initialState.baseMap.offsetX,
        y: afterPanState.baseMap.offsetY - initialState.baseMap.offsetY
      };

      console.log('Network offset change:', networkOffsetChange);
      console.log('Base map offset change:', baseMapOffsetChange);

      // Both should have changed
      const networkChanged = Math.abs(networkOffsetChange.x) > 10 || Math.abs(networkOffsetChange.y) > 10;
      const baseMapChanged = Math.abs(baseMapOffsetChange.x) > 10 || Math.abs(baseMapOffsetChange.y) > 10;

      expect(networkChanged).toBeTruthy();
      expect(baseMapChanged).toBeTruthy();
    }
  });
});
