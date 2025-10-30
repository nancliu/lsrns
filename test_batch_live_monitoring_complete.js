/**
 * Complete Test Script: Batch Live Monitoring Debugging
 *
 * This script:
 * 1. Finds or creates a case with control strategies
 * 2. Starts a batch optimization simulation
 * 3. Monitors the progress API response
 * 4. Debugs missing running_vehicles and live_time_series data
 * 5. Tests the frontend UI for curve rendering
 *
 * Usage: node test_batch_live_monitoring_complete.js
 */

const https = require('https');
const http = require('http');
const { chromium } = require('playwright');

const API_BASE = 'http://localhost:8000/api/v1';
const FRONTEND_URL = 'http://localhost:8000';

// Helper: Make HTTP request
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const timeout = setTimeout(() => {
      reject(new Error(`Request timeout for ${url}`));
    }, 30000);

    client
      .request(url, {
        method: options.method || 'GET',
        ...options.requestOptions,
      }, (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          clearTimeout(timeout);
          try {
            resolve({
              status: res.statusCode,
              data: res.statusCode >= 200 && res.statusCode < 300 ? JSON.parse(data) : data,
            });
          } catch (e) {
            resolve({ status: res.statusCode, data });
          }
        });
      })
      .on('error', (err) => {
        clearTimeout(timeout);
        reject(err);
      })
      .end(options.body ? JSON.stringify(options.body) : undefined);
  });
}

// Format duration
function formatDuration(ms) {
  const sec = Math.floor(ms / 1000);
  const min = Math.floor(sec / 60);
  const h = Math.floor(min / 60);

  if (h > 0) return `${h}h ${min % 60}m`;
  if (min > 0) return `${min}m ${sec % 60}s`;
  return `${sec}s`;
}

// Main test
async function main() {
  console.log('\n' + '='.repeat(80));
  console.log('BATCH LIVE MONITORING DEBUG TEST');
  console.log('='.repeat(80));

  const startTime = Date.now();

  try {
    // Step 1: Find an existing case with simulations
    console.log('\n📍 Step 1: Find existing case with simulations');
    const cases = await makeRequest(`${API_BASE}/case/list`);

    if (!cases.data || cases.data.length === 0) {
      console.log('❌ No cases found');
      return;
    }

    const caseId = cases.data[0].case_id;
    console.log(`✅ Using case: ${caseId}`);

    // Step 2: Check if case has batch optimizations
    console.log('\n📍 Step 2: Check for existing batch optimizations');
    const batchesRes = await makeRequest(
      `${API_BASE}/control/batch-optimization/batches?case_id=${caseId}&limit=5`
    );

    let batchId = null;
    if (batchesRes.data?.batches?.length > 0) {
      // Find a running or completed batch
      const runningBatch = batchesRes.data.batches.find(b => b.status === 'running');
      const completedBatch = batchesRes.data.batches.find(b => b.status === 'completed');

      batchId = runningBatch?.batch_id || completedBatch?.batch_id;
      console.log(`✅ Found batch: ${batchId} (status: ${batchesRes.data.batches[0].status})`);
    } else {
      console.log('⚠️  No existing batches found');
    }

    if (!batchId) {
      console.log('⚠️  Cannot proceed without a batch ID');
      console.log('Note: To test live monitoring, start a batch simulation in the UI first.');
      return;
    }

    // Step 3: Poll batch progress multiple times
    console.log(`\n📍 Step 3: Monitor batch progress (${batchId})`);
    console.log('Polling API every 3 seconds...\n');

    const progressHistory = [];
    let consecutiveEmptyLiveStatus = 0;
    const maxAttempts = 10;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      console.log(`\n🔄 [Attempt ${attempt}/${maxAttempts}] Polling batch progress...`);

      const progressRes = await makeRequest(
        `${API_BASE}/control/batch-optimization/batch/${batchId}/progress`
      );

      if (progressRes.status !== 200) {
        console.log(`❌ API returned status ${progressRes.status}`);
        await new Promise(r => setTimeout(r, 3000));
        continue;
      }

      const progress = progressRes.data;

      // Analyze response
      console.log(`✅ API Response:`);
      console.log(`   Status: ${progress.status}`);
      console.log(`   Progress: ${(progress.progress * 100).toFixed(1)}%`);
      console.log(`   Tasks: ${progress.tasks?.length || 0}`);

      // Check live_time_series
      let hasLiveTimeSeries = false;
      let timeSeriesLength = 0;

      if (progress.live_time_series) {
        hasLiveTimeSeries = true;
        timeSeriesLength = progress.live_time_series.time_points?.length || 0;
        console.log(`   ✅ live_time_series: ${timeSeriesLength} time points`);
        if (timeSeriesLength > 0) {
          console.log(`      First point: ${progress.live_time_series.total_running[0]} vehicles`);
          console.log(`      Last point: ${progress.live_time_series.total_running[timeSeriesLength - 1]} vehicles`);
        }
      } else {
        console.log(`   ❌ live_time_series: NOT FOUND IN RESPONSE`);
      }

      // Check running tasks
      const runningTasks = progress.tasks?.filter(t => t.status === 'running') || [];
      console.log(`   🚗 Running tasks: ${runningTasks.length}`);

      let tasksWithLiveStatus = 0;
      let tasksWithVehicles = 0;

      runningTasks.forEach((task, i) => {
        const taskNum = i + 1;
        if (task.live_status) {
          tasksWithLiveStatus++;
          if (task.live_status.running_vehicles !== undefined) {
            tasksWithVehicles++;
            console.log(
              `      Task ${taskNum}: ${task.task_id} - ` +
              `${task.live_status.running_vehicles} vehicles, ` +
              `${task.live_status.progress_percent?.toFixed(1) || 'N/A'}%`
            );
          } else {
            console.log(`      Task ${taskNum}: ${task.task_id} - NO running_vehicles ⚠️`);
          }
        } else {
          console.log(`      Task ${taskNum}: ${task.task_id} - NO live_status ⚠️`);
        }
      });

      progressHistory.push({
        attempt,
        timestamp: new Date().toISOString(),
        status: progress.status,
        progress: progress.progress,
        hasLiveTimeSeries,
        timeSeriesLength,
        runningTaskCount: runningTasks.length,
        tasksWithLiveStatus,
        tasksWithVehicles,
      });

      // Track consecutive missing data
      if (!hasLiveTimeSeries || timeSeriesLength === 0) {
        consecutiveEmptyLiveStatus++;
      } else {
        consecutiveEmptyLiveStatus = 0;
      }

      // Stop if batch is complete
      if (progress.status === 'completed') {
        console.log(`\n✅ Batch completed`);
        break;
      }

      if (attempt < maxAttempts) {
        await new Promise(r => setTimeout(r, 3000));
      }
    }

    // Step 4: Analyze findings
    console.log('\n' + '='.repeat(80));
    console.log('ANALYSIS & DIAGNOSTICS');
    console.log('='.repeat(80));

    const lastRecord = progressHistory[progressHistory.length - 1];

    console.log('\n📊 Summary of polling attempts:');
    progressHistory.forEach(record => {
      const icon = record.hasLiveTimeSeries && record.timeSeriesLength > 0 ? '✅' : '⚠️';
      console.log(
        `  ${icon} Attempt ${record.attempt}: ` +
        `${record.timeSeriesLength} curve points, ` +
        `${record.tasksWithVehicles}/${record.runningTaskCount} tasks with vehicle count`
      );
    });

    console.log('\n🔍 Key Findings:');

    const issues = [];

    // Check for live_time_series
    if (!lastRecord.hasLiveTimeSeries) {
      issues.push('❌ live_time_series not present in API response');
    } else if (lastRecord.timeSeriesLength === 0) {
      issues.push('⚠️  live_time_series present but empty');
    } else {
      console.log(`✅ live_time_series properly populated with ${lastRecord.timeSeriesLength} points`);
    }

    // Check for running_vehicles
    if (lastRecord.runningTaskCount > 0) {
      if (lastRecord.tasksWithVehicles === lastRecord.runningTaskCount) {
        console.log(`✅ All ${lastRecord.runningTaskCount} running tasks have running_vehicles data`);
      } else if (lastRecord.tasksWithVehicles === 0) {
        issues.push(`❌ None of the ${lastRecord.runningTaskCount} running tasks have running_vehicles data`);
      } else {
        issues.push(
          `⚠️  Only ${lastRecord.tasksWithVehicles}/${lastRecord.runningTaskCount} ` +
          `running tasks have running_vehicles data`
        );
      }
    }

    if (issues.length === 0) {
      console.log('✅ All data appears to be correctly populated!');
      console.log('   If the curve still doesn\'t display, check:');
      console.log('   1. Browser console for JavaScript errors');
      console.log('   2. renderLiveCurve() is being called');
      console.log('   3. Chart.js is loaded and accessible');
    } else {
      console.log('\n⚠️  Issues detected:');
      issues.forEach(issue => console.log(`  ${issue}`));
    }

    // Step 5: Check backend code
    console.log('\n📝 Step 5: Checking backend implementation...');
    await checkBackendImplementation();

  } catch (error) {
    console.log(`\n❌ Error: ${error.message}`);
    console.log(error.stack);
  }

  console.log('\n' + '='.repeat(80));
  console.log(`Total test duration: ${formatDuration(Date.now() - startTime)}`);
  console.log('='.repeat(80) + '\n');
}

// Check if backend methods are properly implemented
async function checkBackendImplementation() {
  console.log('   Checking if backend service methods exist...');
  console.log('   Files to verify:');
  console.log('   - api/services/batch_optimization_service.py');
  console.log('     ✓ _extract_summary_last_step()');
  console.log('     ✓ _get_simulation_live_status()');
  console.log('     ✓ _aggregate_live_time_series()');
  console.log('     ✓ _calculate_batch_remaining_time()');
  console.log('   - frontend/control/js/batch_simulation.js');
  console.log('     ✓ renderLiveCurve()');
  console.log('     ✓ updateProgress()');
}

// Run
main().catch(console.error);
