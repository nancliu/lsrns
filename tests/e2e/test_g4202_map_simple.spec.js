// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * G4202 Network Map Simple Debug Test
 *
 * Uses test_viz.html for direct network visualization testing without workflow dependencies
 */

test.describe('G4202 Network Map Simple Debug', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      console.log(`[Browser ${msg.type()}]:`, msg.text());
    });

    // Enable error tracking
    page.on('pageerror', error => {
      console.error('[Browser Page Error]:', error.message);
    });

    // Navigate to test visualization page
    await page.goto('http://localhost:8000/control/test_viz.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('should load G4202 network and center map', async ({ page }) => {
    console.log('\n=== Test: G4202 Network Loading and Centering ===\n');

    // Initialize the visualization
    await page.click('button:has-text("2. Test Init")');
    await page.waitForTimeout(1000);

    // Load geometry with G4202 filter
    await page.evaluate(async () => {
      // Direct API call to load G4202 geometry
      try {
        const response = await fetch('/api/v1/control/edges/network_geometry?route_codes=G4202');
        const data = await response.json();

        if (data && data.edges) {
          window.networkViz.loadGeometry(data);
          console.log('✓ Loaded G4202 geometry:', data.edges.length, 'edges');
        } else {
          console.error('✗ Failed to load geometry:', data);
        }
      } catch (error) {
        console.error('✗ Error loading geometry:', error);
      }
    });

    await page.waitForTimeout(2000);

    // Check if canvas has content
    const canvas = page.locator('#network-canvas');
    await expect(canvas).toBeVisible();

    const canvasInfo = await page.evaluate(() => {
      const canvas = document.getElementById('network-canvas');
      const viz = window.networkViz;

      return {
        canvasSize: { width: canvas.width, height: canvas.height },
        viewportInfo: viz ? {
          scale: viz.scale,
          offsetX: viz.offsetX,
          offsetY: viz.offsetY,
          edgeCount: viz.edges ? viz.edges.length : 0,
          nodeCount: viz.nodes ? viz.nodes.length : 0
        } : null,
        hasContent: (() => {
          const ctx = canvas.getContext('2d');
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;
          for (let i = 0; i < data.length; i += 4) {
            if (data[i] !== 255 || data[i+1] !== 255 || data[i+2] !== 255) {
              return true;
            }
          }
          return false;
        })()
      };
    });

    console.log('Canvas info:', JSON.stringify(canvasInfo, null, 2));

    expect(canvasInfo.hasContent).toBeTruthy();
    expect(canvasInfo.viewportInfo).not.toBeNull();
    expect(canvasInfo.viewportInfo.edgeCount).toBeGreaterThan(0);

    // Take screenshot
    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_simple_load.png'
    });
    console.log('Screenshot saved: g4202_simple_load.png');
  });

  test('should support zoom operations on G4202 network', async ({ page }) => {
    console.log('\n=== Test: G4202 Zoom Operations ===\n');

    // Initialize and load G4202
    await page.click('button:has-text("2. Test Init")');
    await page.waitForTimeout(500);

    await page.evaluate(async () => {
      const response = await fetch('/api/v1/control/edges/network_geometry?route_codes=G4202');
      const data = await response.json();
      if (data && data.edges) {
        window.networkViz.loadGeometry(data);
      }
    });
    await page.waitForTimeout(1500);

    const canvas = page.locator('#network-canvas');
    const bbox = await canvas.boundingBox();

    // Get initial state
    const initialScale = await page.evaluate(() => window.networkViz.scale);
    console.log('Initial scale:', initialScale);

    // Zoom in (scroll up)
    await canvas.hover({ position: { x: bbox.width / 2, y: bbox.height / 2 } });
    await page.mouse.wheel(0, -100);
    await page.waitForTimeout(300);

    const zoomedInScale = await page.evaluate(() => window.networkViz.scale);
    console.log('Zoomed in scale:', zoomedInScale);
    expect(zoomedInScale).toBeGreaterThan(initialScale);

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_zoomed_in.png'
    });

    // Zoom out (scroll down)
    await page.mouse.wheel(0, 200);
    await page.waitForTimeout(300);

    const zoomedOutScale = await page.evaluate(() => window.networkViz.scale);
    console.log('Zoomed out scale:', zoomedOutScale);
    expect(zoomedOutScale).toBeLessThan(zoomedInScale);

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_zoomed_out.png'
    });
  });

  test('should support pan operations on G4202 network', async ({ page }) => {
    console.log('\n=== Test: G4202 Pan Operations ===\n');

    // Initialize and load G4202
    await page.click('button:has-text("2. Test Init")');
    await page.waitForTimeout(500);

    await page.evaluate(async () => {
      const response = await fetch('/api/v1/control/edges/network_geometry?route_codes=G4202');
      const data = await response.json();
      if (data && data.edges) {
        window.networkViz.loadGeometry(data);
      }
    });
    await page.waitForTimeout(1500);

    const canvas = page.locator('#network-canvas');
    const bbox = await canvas.boundingBox();

    // Get initial offset
    const initialOffset = await page.evaluate(() => ({
      x: window.networkViz.offsetX,
      y: window.networkViz.offsetY
    }));
    console.log('Initial offset:', initialOffset);

    // Pan by dragging
    await canvas.hover({ position: { x: bbox.width / 2, y: bbox.height / 2 } });
    await page.mouse.down();
    await page.mouse.move(bbox.x + bbox.width / 2 + 100, bbox.y + bbox.height / 2 + 100);
    await page.mouse.up();
    await page.waitForTimeout(300);

    const pannedOffset = await page.evaluate(() => ({
      x: window.networkViz.offsetX,
      y: window.networkViz.offsetY
    }));
    console.log('Panned offset:', pannedOffset);

    const offsetChanged =
      Math.abs(pannedOffset.x - initialOffset.x) > 10 ||
      Math.abs(pannedOffset.y - initialOffset.y) > 10;
    expect(offsetChanged).toBeTruthy();

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_panned.png'
    });
  });

  test('should reset view correctly', async ({ page }) => {
    console.log('\n=== Test: G4202 Reset View ===\n');

    // Initialize and load G4202
    await page.click('button:has-text("2. Test Init")');
    await page.waitForTimeout(500);

    await page.evaluate(async () => {
      const response = await fetch('/api/v1/control/edges/network_geometry?route_codes=G4202');
      const data = await response.json();
      if (data && data.edges) {
        window.networkViz.loadGeometry(data);
      }
    });
    await page.waitForTimeout(1500);

    // Get initial viewport state (after initial load)
    const initialState = await page.evaluate(() => ({
      scale: window.networkViz.scale,
      offsetX: window.networkViz.offsetX,
      offsetY: window.networkViz.offsetY
    }));
    console.log('Initial state after load:', initialState);

    // Zoom and pan
    const canvas = page.locator('#network-canvas');
    await canvas.hover();
    await page.mouse.wheel(0, -200); // Zoom in
    await page.waitForTimeout(200);

    const bbox = await canvas.boundingBox();
    await page.mouse.down();
    await page.mouse.move(bbox.x + 150, bbox.y + 150);
    await page.mouse.up();
    await page.waitForTimeout(200);

    const modifiedState = await page.evaluate(() => ({
      scale: window.networkViz.scale,
      offsetX: window.networkViz.offsetX,
      offsetY: window.networkViz.offsetY
    }));
    console.log('Modified state:', modifiedState);

    // Reset view
    await page.click('button:has-text("4. Test Reset View")');
    await page.waitForTimeout(500);

    const resetState = await page.evaluate(() => ({
      scale: window.networkViz.scale,
      offsetX: window.networkViz.offsetX,
      offsetY: window.networkViz.offsetY
    }));
    console.log('Reset state:', resetState);

    // After reset, should be close to initial state
    expect(Math.abs(resetState.scale - initialState.scale)).toBeLessThan(0.1);

    await page.screenshot({
      path: 'tests/e2e/screenshots/g4202_reset_view.png'
    });
  });
});
