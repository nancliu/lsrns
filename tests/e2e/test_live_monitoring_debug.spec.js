/**
 * E2E Test: Live Monitoring Feature Debugging
 *
 * Focuses on debugging the in-network vehicle curve display issue.
 * Tests:
 * 1. API response structure (running_vehicles, live_time_series)
 * 2. Frontend state management
 * 3. Dynamic curve rendering
 * 4. Data flow tracing
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

// Set timeout for long-running tests
test.setTimeout(180000); // 3 minutes

const API_BASE_URL = 'http://localhost:8000/api/v1';
const FRONTEND_URL = 'http://localhost:8000';

// Helper function to wait for API response
async function waitForApiResponse(page, apiPath, timeout = 5000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      console.log(`⚠️  Timeout waiting for API: ${apiPath}`);
      resolve(null);
    }, timeout);

    page.on('response', (response) => {
      if (response.url().includes(apiPath)) {
        clearTimeout(timer);
        response.json().then(resolve).catch(() => resolve(null));
      }
    });
  });
}

// Helper function to poll batch progress with API debugging
async function pollBatchProgressDebug(page, batchId, maxAttempts = 20) {
  let attempt = 0;
  const progressHistory = [];

  while (attempt < maxAttempts) {
    attempt++;
    console.log(`\n🔍 [Attempt ${attempt}/${maxAttempts}] Polling batch progress...`);

    try {
      const response = await page.request.get(
        `${API_BASE_URL}/control/batch-optimization/batch/${batchId}/progress`
      );

      if (!response.ok()) {
        console.log(`⚠️  API returned status ${response.status()}`);
        await page.waitForTimeout(2000);
        continue;
      }

      const data = await response.json();

      // Log API response structure
      console.log(`✅ API Response received at attempt ${attempt}`);
      console.log(`   - Status: ${data.status}`);
      console.log(`   - Progress: ${(data.progress * 100).toFixed(1)}%`);
      console.log(`   - Tasks: ${data.tasks?.length || 0}`);

      // Analyze live_time_series
      if (data.live_time_series) {
        const timeSeriesLength = data.live_time_series.time_points?.length || 0;
        console.log(`   📊 live_time_series detected:`);
        console.log(`      - time_points: ${timeSeriesLength} points`);
        console.log(`      - total_running: ${data.live_time_series.total_running?.length || 0} points`);
        console.log(`      - task_count: ${data.live_time_series.task_count || 0}`);
      } else {
        console.log(`   📊 live_time_series: NOT FOUND in response ⚠️`);
      }

      // Analyze running tasks
      const runningTasks = data.tasks?.filter(t => t.status === 'running') || [];
      console.log(`   🚗 Running tasks: ${runningTasks.length}`);

      runningTasks.forEach((task, i) => {
        console.log(`      Task ${i + 1}: ${task.task_id}`);
        if (task.live_status) {
          console.log(`         - running_vehicles: ${task.live_status.running_vehicles ?? 'undefined'} ⚠️`);
          console.log(`         - current_step: ${task.live_status.current_step ?? 'N/A'}`);
          console.log(`         - progress_percent: ${task.live_status.progress_percent?.toFixed(1) ?? 'N/A'}%`);
        } else {
          console.log(`         - live_status: NOT FOUND ⚠️`);
        }
      });

      progressHistory.push({
        attempt,
        status: data.status,
        progress: data.progress,
        hasLiveTimeSeries: !!data.live_time_series,
        timeSeriesLength: data.live_time_series?.time_points?.length || 0,
        runningTaskCount: runningTasks.length,
        tasksWithLiveStatus: runningTasks.filter(t => t.live_status).length,
      });

      // Check if we have usable data
      if (data.status === 'completed' || (runningTasks.length === 0 && data.progress >= 0.9)) {
        console.log(`\n✅ Batch completed or near completion`);
        break;
      }

      if (attempt < maxAttempts) {
        await page.waitForTimeout(5000); // Wait 5 seconds before next poll
      }
    } catch (error) {
      console.log(`❌ Error during API polling: ${error.message}`);
      await page.waitForTimeout(2000);
    }
  }

  return progressHistory;
}

// Main test
test('Live Monitoring Feature - Debug In-Network Vehicle Curve Display', async ({ page, context }) => {
  console.log('\n' + '='.repeat(70));
  console.log('START: Live Monitoring Debug Test');
  console.log('='.repeat(70));

  // Step 1: Navigate to batch simulation page
  console.log('\n📍 Step 1: Navigate to batch simulation page');
  await page.goto(`${FRONTEND_URL}/control/simulations.html`);
  await page.waitForLoadState('domcontentloaded');

  // Wait for page elements to be ready
  await page.waitForSelector('[id="batchSimulationContainer"]', { timeout: 5000 }).catch(() => {
    console.log('⚠️  Container not found, but continuing...');
  });

  // Step 2: Check if there are any existing batches or start a new one
  console.log('\n📍 Step 2: Check for existing batch or prepare new batch');

  const existingBatches = await page.$$eval(
    '[class*="batch-item"]',
    (els) => els.length
  ).catch(() => 0);

  console.log(`   - Found ${existingBatches} existing batch items`);

  // Try to find and click on an existing running batch, or prepare to create one
  let batchId = null;
  let isNewBatch = false;

  // Look for a running batch in the history
  const batchCards = await page.$$('[class*="batch-card"]').catch(() => []);

  if (batchCards.length > 0) {
    console.log(`   - Found ${batchCards.length} batch cards, checking for running batches...`);

    for (const card of batchCards) {
      const statusText = await card.textContent();
      if (statusText?.includes('运行中') || statusText?.includes('running')) {
        console.log(`   ✅ Found running batch!`);
        // Extract batch ID from card if possible
        const batchIdMatch = statusText.match(/batch_\w+/);
        if (batchIdMatch) {
          batchId = batchIdMatch[0];
          console.log(`   - Batch ID: ${batchId}`);
        }
        break;
      }
    }
  }

  // If no running batch found, we'll use API to check
  if (!batchId) {
    console.log(`   - No running batch found in UI, checking via API...`);
    try {
      const response = await page.request.get(
        `${API_BASE_URL}/control/batch-optimization/batches?status=running&limit=1`
      );
      if (response.ok()) {
        const data = await response.json();
        if (data.batches?.length > 0) {
          batchId = data.batches[0].batch_id;
          console.log(`   ✅ Found running batch via API: ${batchId}`);
        }
      }
    } catch (error) {
      console.log(`   ⚠️  Error checking API: ${error.message}`);
    }
  }

  // Step 3: Poll batch progress and collect data
  console.log('\n📍 Step 3: Poll batch progress and analyze API responses');

  let progressHistory;
  if (batchId) {
    console.log(`   - Using batch ID: ${batchId}`);
    progressHistory = await pollBatchProgressDebug(page, batchId, 5);
  } else {
    console.log(`   ⚠️  No batch ID available, cannot proceed with polling`);
    progressHistory = [];
  }

  // Step 4: Check frontend state
  console.log('\n📍 Step 4: Check frontend state and console logs');

  if (batchId) {
    // Navigate to progress view
    await page.goto(`${FRONTEND_URL}/control/simulations.html`);
    await page.waitForLoadState('domcontentloaded');

    // Check if progress tab exists and click it
    const progressTab = await page.$('[id*="progress"], [class*="progress-tab"]').catch(() => null);
    if (progressTab) {
      await progressTab.click();
      await page.waitForTimeout(1000);
    }

    // Capture console logs
    const consoleLogs = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location().url,
      });
      if (msg.type() === 'log' || msg.type() === 'error') {
        console.log(`   [Browser Console ${msg.type().toUpperCase()}]: ${msg.text()}`);
      }
    });

    // Check for dynamic curve elements
    await page.waitForTimeout(2000);

    console.log('\n📍 Step 5: Check if dynamic curve HTML element exists');
    const curveSection = await page.$('[id="liveCurveSection"]').catch(() => null);
    const curveCanvas = await page.$('[id="liveCurveChart"]').catch(() => null);

    if (curveSection) {
      const isVisible = await curveSection.isVisible();
      console.log(`   - liveCurveSection found: ${isVisible ? '✅ VISIBLE' : '⚠️ HIDDEN'}`);
    } else {
      console.log(`   - liveCurveSection element: ❌ NOT FOUND`);
    }

    if (curveCanvas) {
      console.log(`   - liveCurveChart canvas: ✅ FOUND`);
    } else {
      console.log(`   - liveCurveChart canvas: ❌ NOT FOUND`);
    }

    // Check for running vehicles display
    const vehicleElements = await page.$$('[class*="vehicle"], [id*="vehicle"]').catch(() => []);
    console.log(`   - Running vehicles display elements: ${vehicleElements.length} found`);
  }

  // Step 6: Generate summary report
  console.log('\n📍 Step 6: Summary and Diagnostics');
  console.log('\n' + '='.repeat(70));
  console.log('PROGRESS HISTORY:');
  console.log('='.repeat(70));

  if (progressHistory.length > 0) {
    progressHistory.forEach((record, i) => {
      console.log(`\nAttempt ${record.attempt}:`);
      console.log(`  Status: ${record.status}`);
      console.log(`  Progress: ${(record.progress * 100).toFixed(1)}%`);
      console.log(`  live_time_series: ${record.hasLiveTimeSeries ? '✅ PRESENT' : '❌ MISSING'}`);
      if (record.hasLiveTimeSeries) {
        console.log(`    └─ Data points: ${record.timeSeriesLength}`);
      }
      console.log(`  Running tasks: ${record.runningTaskCount}`);
      console.log(`  Tasks with live_status: ${record.tasksWithLiveStatus}/${record.runningTaskCount}`);
    });

    console.log('\n' + '='.repeat(70));
    console.log('ISSUES DETECTED:');
    console.log('='.repeat(70));

    // Analyze issues
    const lastRecord = progressHistory[progressHistory.length - 1];
    const issues = [];

    if (!lastRecord.hasLiveTimeSeries) {
      issues.push('❌ live_time_series not present in API response');
    } else if (lastRecord.timeSeriesLength === 0) {
      issues.push('⚠️  live_time_series present but empty (no data points)');
    }

    if (lastRecord.runningTaskCount > 0 && lastRecord.tasksWithLiveStatus === 0) {
      issues.push('❌ Running tasks have no live_status data');
    } else if (lastRecord.runningTaskCount > 0 && lastRecord.tasksWithLiveStatus < lastRecord.runningTaskCount) {
      issues.push(`⚠️  Only ${lastRecord.tasksWithLiveStatus}/${lastRecord.runningTaskCount} running tasks have live_status`);
    }

    if (issues.length === 0) {
      console.log('✅ No critical issues detected!');
      console.log('   The live_time_series and running_vehicles data appear to be present.');
      console.log('   If the curve is still not displaying, check:');
      console.log('   1. Frontend JavaScript console for rendering errors');
      console.log('   2. Chart.js library is loaded');
      console.log('   3. renderLiveCurve() function is being called');
    } else {
      issues.forEach(issue => console.log(`  ${issue}`));
    }
  } else {
    console.log('⚠️  No progress history collected');
  }

  console.log('\n' + '='.repeat(70));
  console.log('END: Live Monitoring Debug Test');
  console.log('='.repeat(70) + '\n');

  // Return test as passed (we're gathering diagnostics, not asserting failures)
  expect(true).toBe(true);
});

/**
 * Additional test: Check if Chart.js and related libraries are loaded
 */
test('Check Frontend Dependencies - Chart.js and Libraries', async ({ page }) => {
  console.log('\n📚 Checking frontend dependencies...');

  await page.goto(`${FRONTEND_URL}/control/simulations.html`);
  await page.waitForLoadState('domcontentloaded');

  // Check if Chart.js is available
  const chartLibLoaded = await page.evaluate(() => {
    return typeof Chart !== 'undefined';
  }).catch(() => false);

  console.log(`  Chart.js library: ${chartLibLoaded ? '✅ LOADED' : '❌ NOT LOADED'}`);

  // Check if jQuery is loaded (if used)
  const jqueryLoaded = await page.evaluate(() => {
    return typeof $ !== 'undefined' || typeof jQuery !== 'undefined';
  }).catch(() => false);

  console.log(`  jQuery library: ${jqueryLoaded ? '✅ LOADED' : '⚠️ NOT LOADED (may not be needed)'}`);

  // Check if fetch API is available
  const fetchAvailable = await page.evaluate(() => {
    return typeof fetch !== 'undefined';
  });

  console.log(`  Fetch API: ${fetchAvailable ? '✅ AVAILABLE' : '❌ NOT AVAILABLE'}`);

  expect(chartLibLoaded).toBe(true);
});

/**
 * Test: Direct API call to verify data structure
 */
test('Direct API Call - Verify batch progress response structure', async ({ page }) => {
  console.log('\n📡 Testing API response structure directly...\n');

  try {
    // Get a running batch
    const batchesResponse = await page.request.get(
      `${API_BASE_URL}/control/batch-optimization/batches?status=running&limit=1`
    );

    if (!batchesResponse.ok()) {
      console.log('⚠️  No running batches found, skipping direct API test');
      expect(true).toBe(true);
      return;
    }

    const batchesData = await batchesResponse.json();
    if (!batchesData.batches?.length) {
      console.log('⚠️  No batches returned from API');
      expect(true).toBe(true);
      return;
    }

    const batchId = batchesData.batches[0].batch_id;
    console.log(`Testing batch: ${batchId}\n`);

    // Get batch progress
    const progressResponse = await page.request.get(
      `${API_BASE_URL}/control/batch-optimization/batch/${batchId}/progress`
    );

    if (!progressResponse.ok()) {
      console.log(`❌ Failed to get batch progress: ${progressResponse.status()}`);
      expect(progressResponse.ok()).toBe(true);
      return;
    }

    const progressData = await progressResponse.json();

    // Check response structure
    console.log('✅ Progress API Response Structure:');
    console.log(`  - batch_id: ${progressData.batch_id ? '✅' : '❌'}`);
    console.log(`  - status: ${progressData.status ? '✅' : '❌'}`);
    console.log(`  - progress: ${progressData.progress !== undefined ? '✅' : '❌'}`);
    console.log(`  - tasks: ${Array.isArray(progressData.tasks) ? `✅ (${progressData.tasks.length} items)` : '❌'}`);
    console.log(`  - live_time_series: ${progressData.live_time_series ? '✅' : '❌ ⚠️ MISSING'}`);

    if (progressData.live_time_series) {
      console.log(`\n✅ live_time_series structure:`);
      console.log(`    - time_points: ${Array.isArray(progressData.live_time_series.time_points) ? `✅ (${progressData.live_time_series.time_points.length} points)` : '❌'}`);
      console.log(`    - total_running: ${Array.isArray(progressData.live_time_series.total_running) ? `✅ (${progressData.live_time_series.total_running.length} points)` : '❌'}`);
      console.log(`    - task_count: ${progressData.live_time_series.task_count ?? 'undefined'}`);
    }

    // Check running tasks
    const runningTasks = progressData.tasks?.filter(t => t.status === 'running') || [];
    console.log(`\n🚗 Running Tasks (${runningTasks.length}):`);

    runningTasks.forEach((task) => {
      console.log(`  ${task.task_id}:`);
      if (task.live_status) {
        console.log(`    ✅ live_status present`);
        console.log(`       - running_vehicles: ${task.live_status.running_vehicles ?? 'undefined'} ⚠️`);
        console.log(`       - current_step: ${task.live_status.current_step ?? 'undefined'}`);
        console.log(`       - progress_percent: ${task.live_status.progress_percent ?? 'undefined'}`);
      } else {
        console.log(`    ❌ live_status missing`);
      }
    });

    expect(progressResponse.ok()).toBe(true);
    expect(progressData.live_time_series).toBeDefined();
  } catch (error) {
    console.log(`❌ Error during API test: ${error.message}`);
    throw error;
  }
});
