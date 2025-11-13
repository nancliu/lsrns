# Phase 2 User Guide: Event Scenario Simulation and Analysis

**Version**: 1.0
**Date**: 2025-11-12
**Target Audience**: End users, traffic analysts, system operators

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Workflow Overview](#workflow-overview)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Monitoring Progress](#monitoring-progress)
6. [Viewing Analysis Results](#viewing-analysis-results)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)

---

## Introduction

Phase 2 enables you to:
- ✅ Create simulation cases directly from event scenarios
- ✅ Run multiple simulations concurrently (batch execution)
- ✅ Monitor real-time progress of simulations and analyses
- ✅ Automatically analyze simulation results
- ✅ View comprehensive analysis dashboards

### Key Features

- **449 Pre-built Scenarios**: Accident, congestion, and construction scenarios with control strategies (VSS, TEC, DHS)
- **Batch Execution**: Run up to 50 simulations concurrently
- **Automatic Analysis**: EdgeData, TripInfo, and Performance analysis run automatically after simulation
- **Real-time Monitoring**: Track progress with 10-second updates
- **Full Traceability**: Complete metadata chain from scenario → case → simulation → analysis

---

## Quick Start

### Prerequisites

1. **System Running**: Ensure OD_SIM system is running (`start_api.ps1`)
2. **Scenarios Available**: 449 scenarios should be in `output/scenarios/`
3. **Network Access**: Can access http://localhost:8000

### 5-Minute Quickstart

```bash
# 1. Navigate to scenario browser
http://localhost:8000/frontend/scenarios/scenario_browser.html

# 2. Select a scenario (e.g., "scenario_10754_vss")

# 3. Click "Create Case from Scenario"

# 4. Click "Start Simulation"

# 5. Monitor progress in real-time

# 6. View analysis results when complete
```

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2 WORKFLOW                              │
└─────────────────────────────────────────────────────────────────┘

Step 1: Browse Scenarios
   ↓
   449 scenarios organized by event type:
   • 01_accident (事故)
   • 02_congestion (拥堵)
   • 03_construction (施工)

   Each scenario has 4 variants:
   • baseline (无管控)
   • VSS (可变限速)
   • TEC (收费站管控)
   • DHS (动态硬路肩)

Step 2: Create Case from Scenario
   ↓
   System automatically:
   • Creates case directory
   • Copies scenario configuration
   • Generates metadata (v2.0)
   • Links scenario → case

Step 3: Prepare Simulation
   ↓
   System generates:
   • SUMO configuration files
   • Vehicle routing files
   • Control strategy files
   • Output specifications

Step 4: Run Simulation (Batch)
   ↓
   Options:
   • Single simulation: 1-2 hours
   • Batch (10 sims): 2-4 hours with 4 workers
   • Batch (50 sims): 10-15 hours with 8 workers

   Real-time monitoring:
   • Progress percentage
   • Vehicles completed
   • ETA remaining
   • Log viewer

Step 5: Analysis (Automatic)
   ↓
   Four analysis types:
   • Summary: Vehicle counts, speeds, delays
   • EdgeData: Road segment congestion analysis
   • TripInfo: Trip completion, travel times
   • Performance: System metrics

   Concurrent execution:
   • 4-8 parallel workers
   • Progress tracking
   • ETA calculation

Step 6: View Results
   ↓
   Dashboards show:
   • Heat maps (congestion levels)
   • Statistical comparisons
   • Baseline vs control effectiveness
   • Downloadable reports
```

---

## Step-by-Step Guide

### 1. Browse Available Scenarios

**Navigate to Scenario Browser:**
```
http://localhost:8000/frontend/scenarios/scenario_browser.html
```

**Filter Scenarios:**
- **By Event Type**: Select "01_accident", "02_congestion", or "03_construction"
- **By Control Strategy**: Filter by "baseline", "VSS", "TEC", or "DHS"
- **By Event ID**: Search for specific event (e.g., "12547")

**View Scenario Details:**
- Click on any scenario row to expand details
- View event description, location, affected edges
- See control strategy configuration

### 2. Create Case from Scenario

**Method 1: Via Scenario Browser (Recommended)**
1. Select scenario in table
2. Click "Create Case from Scenario" button
3. System creates case automatically
4. Redirects to case details page

**Method 2: Via API (Advanced)**
```python
POST /api/v1/case/create-from-scenario
{
  "scenario_id": "scenario_10754_vss",
  "event_id": "10754",
  "event_type": "01_accident",
  "control_strategy_type": "VSS",
  "simulation_duration_hours": 2.0,
  "random_seed": 42
}
```

**What Happens:**
- ✅ Case directory created: `cases/case_YYYYMMDD_HHMMSS/`
- ✅ Metadata v2.0 generated with scenario linkage
- ✅ Configuration files copied from scenario
- ✅ Immutable fields locked (event details, location)
- ✅ Overridable fields available (duration, seed)

### 3. Prepare Simulation

**Automatic Preparation:**
- After case creation, simulation is auto-prepared
- Or manually trigger via API:

```python
POST /api/v1/simulation/prepare
{
  "case_id": "case_20251112_120000"
}
```

**Generated Files:**
```
cases/case_id/simulations/sim_id/
├── simulation.sumocfg        # SUMO configuration (portable)
├── scenario.add.xml           # Control strategy
├── simulation_metadata.json   # Simulation metadata v2.0
└── outputs/                   # Output directory (created on run)
```

**Key Feature: Portable Paths**
- All paths in `simulation.sumocfg` are **relative**
- Cases can be moved between machines
- No path remapping needed

### 4. Start Simulation (Single or Batch)

#### Single Simulation

**Via UI:**
1. Navigate to case details page
2. Click "Start Simulation" on simulation row
3. Monitor progress in real-time

**Via API:**
```python
POST /api/v1/simulation/start
{
  "simulation_id": "sim_20251112_120530"
}
```

#### Batch Simulation (Multiple at Once)

**Via UI:**
1. Select multiple simulations (checkboxes)
2. Click "Batch Start" button
3. Monitor batch progress

**Via API:**
```python
POST /api/v1/simulation/batch-start
{
  "simulation_ids": [
    "sim_20251112_120530",
    "sim_20251112_120545",
    "sim_20251112_120600"
  ],
  "parallel_workers": 4,
  "auto_run_analysis": true
}
```

**Response:**
```json
{
  "batch_id": "batch_20251112_121000",
  "simulation_ids": [...],
  "total": 3,
  "created_at": "2025-11-12T12:10:00"
}
```

### 5. Monitor Simulation Progress

#### Real-Time Monitoring UI

**Navigate to:**
```
http://localhost:8000/frontend/pages/simulations.html?batch_id=<batch_id>
```

**Dashboard Shows:**
```
┌─ Batch Overview ──────────────────────────────────────┐
│ Total: 10 | Completed: 4 | Failed: 0 | Running: 2    │
│ Queued: 4                                             │
│ ETA: 2025-11-12 18:45:00                             │
└───────────────────────────────────────────────────────┘

┌─ Simulation List ─────────────────────────────────────┐
│ ID            │ Status  │ Progress │ ETA    │ Actions │
├───────────────┼─────────┼──────────┼────────┼─────────┤
│ sim_123       │ Running │ 45% ▓▓▓  │ 00:23  │ [Logs]  │
│ sim_456       │ Done    │ 100% ▓▓▓ │ --     │ [View]  │
│ sim_789       │ Pending │ 0%       │ Queued │ --      │
└───────────────┴─────────┴──────────┴────────┴─────────┘
```

**Features:**
- Updates every 5-10 seconds
- Progress bars with percentage
- Elapsed time and ETA
- Expandable log viewer
- Error messages (if any)

#### API Monitoring

```python
GET /api/v1/simulation/batch-status/{batch_id}
```

**Response:**
```json
{
  "batch_id": "batch_20251112_121000",
  "total": 10,
  "completed": 4,
  "failed": 0,
  "in_progress": 2,
  "queued": 4,
  "estimated_completion": "2025-11-12T18:45:00",
  "simulations": [
    {
      "simulation_id": "sim_123",
      "status": "running",
      "progress_percent": 45,
      "vehicles_completed": 5234,
      "elapsed_time": "00:45:30",
      "eta": "01:05:15"
    },
    ...
  ]
}
```

### 6. Run Analysis (Automatic or Manual)

#### Automatic Analysis

If `auto_run_analysis: true` in batch start request, analysis runs automatically after all simulations complete.

#### Manual Analysis

**Via API:**
```python
POST /api/v1/analysis/run-batch
{
  "simulation_ids": ["sim_123", "sim_456", "sim_789"],
  "case_id": "case_20251112_120000",
  "baseline_scenario_id": "scenario_10754_none",
  "analysis_focus": ["summary", "edgedata"],
  "parallel_workers": 4
}
```

**Monitor Progress:**
```python
GET /api/v1/analysis/batch-progress/{batch_id}
```

**Response:**
```json
{
  "batch_id": "analysis_batch_20251112_140000",
  "total_tasks": 8,
  "completed": 3,
  "failed": 0,
  "in_progress": 2,
  "queued": 3,
  "estimated_completion": "2025-11-12T16:30:00",
  "current_tasks": [
    {
      "task_id": "task_001",
      "simulation_id": "sim_123",
      "analysis_type": "edgedata",
      "status": "running",
      "progress": 65,
      "message": "Processing 2847 edges..."
    },
    ...
  ]
}
```

### 7. View Analysis Results

**Navigate to Results Dashboard:**
```
http://localhost:8000/frontend/pages/analysis.html?batch_id=<analysis_batch_id>
```

**Dashboard Components:**

#### EdgeData Heat Map
- Visual representation of road segment congestion
- Color coding: Green (free flow) → Red (congested)
- Click on road segments for details

#### Statistics Summary
```
┌─ Key Metrics ─────────────────────────────────┐
│ Total Vehicles:      8,934                     │
│ Avg Trip Time:       245.6 minutes             │
│ Completion Rate:     98.7%                     │
│ Avg Speed:           52.3 km/h                 │
│ Most Congested Edge: Edge_247 (avg 25 km/h)   │
└────────────────────────────────────────────────┘
```

#### Comparison Report
```
┌─ Baseline vs VSS Control ─────────────────────┐
│ Metric          │ Baseline │ With VSS │ Change │
├─────────────────┼──────────┼──────────┼────────┤
│ Avg Speed       │  45 km/h │  52 km/h │  +16%  │
│ Trip Time       │  200 min │  185 min │  -8%   │
│ Congestion      │  Medium  │  Low     │  -35%  │
│ Completion Rate │  95.2%   │  98.7%   │  +3.5% │
└─────────────────┴──────────┴──────────┴────────┘
```

**Download Reports:**
- Click "Download PDF" for full report
- Click "Export JSON" for raw data
- Reports include charts, statistics, and metadata

---

## Troubleshooting

### Common Issues

#### Issue: Simulation Stuck at 0% Progress

**Symptoms:**
- Simulation status "running" but progress stays at 0%
- No vehicles completed

**Possible Causes:**
1. SUMO process not started
2. Invalid SUMO configuration
3. Missing input files

**Solutions:**
```bash
# 1. Check SUMO logs
cat cases/case_id/simulations/sim_id/sumo_logs/sumo_*.log

# 2. Verify SUMO paths
# All paths in simulation.sumocfg should be relative and reachable

# 3. Manually test SUMO configuration
cd cases/case_id/simulations/sim_id
sumo -c simulation.sumocfg --verbose

# 4. Check for error messages in API logs
```

#### Issue: Analysis Not Starting

**Symptoms:**
- Simulation completed but analysis not triggered
- Analysis batch stuck at "queued"

**Possible Causes:**
1. `auto_run_analysis` was false
2. Missing simulation output files
3. Analysis service not running

**Solutions:**
```python
# 1. Manually trigger analysis
POST /api/v1/analysis/run-batch
{
  "simulation_ids": ["sim_123"],
  "case_id": "case_id",
  "baseline_scenario_id": "scenario_10754_none"
}

# 2. Verify simulation outputs exist
ls cases/case_id/simulations/sim_id/outputs/
# Should contain: summary.xml, edgedata.xml, tripinfo.xml

# 3. Check analysis service logs
# Look for errors in API logs
```

#### Issue: Batch Taking Too Long

**Symptoms:**
- Batch ETA keeps increasing
- Many simulations stuck in "queued"

**Possible Causes:**
1. Too many simulations for available workers
2. System resource constraints (CPU, memory, disk)
3. Individual simulations taking longer than expected

**Solutions:**
```python
# 1. Check system resources
# Ensure CPU usage < 80%, memory available > 4GB

# 2. Reduce parallel workers
POST /api/v1/simulation/batch-start
{
  "simulation_ids": [...],
  "parallel_workers": 2  # Reduced from 4
}

# 3. Cancel and restart with smaller batch
POST /api/v1/simulation/batch-cancel
{
  "batch_id": "batch_id"
}

# 4. Split into smaller batches (10-20 sims each)
```

#### Issue: Analysis Results Empty

**Symptoms:**
- Analysis shows "completed" but no results visible
- Dashboard shows no data

**Possible Causes:**
1. Analysis failed but status not updated
2. Result files not generated
3. Metadata linkage broken

**Solutions:**
```bash
# 1. Check analysis directory
ls cases/case_id/analysis/batch_id/
# Should contain subdirectories: edgedata/, tripinfo/, summary/

# 2. Verify analysis metadata
cat cases/case_id/analysis/batch_id/analysis_metadata.json
# Check "status" fields for each analysis type

# 3. Re-run analysis
POST /api/v1/analysis/run-batch
{
  "simulation_ids": ["sim_123"],
  "case_id": "case_id",
  "baseline_scenario_id": "scenario_10754_none"
}
```

### Error Messages and Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Scenario not found" | Invalid scenario_id | Check scenario exists in `output/scenarios/` |
| "SUMO configuration invalid" | Missing/incorrect paths | Regenerate simulation with `prepare_simulation` |
| "Analysis requires edgedata output" | Simulation didn't generate edgedata.xml | Re-run simulation with `generate_edgedata: true` |
| "Batch execution timeout" | Simulation taking too long | Increase timeout or reduce simulation duration |
| "Memory allocation failed" | System out of memory | Reduce parallel workers or restart services |

---

## Best Practices

### 1. Batch Size

- **Small batches (1-10 sims)**: Fast results, good for testing
- **Medium batches (10-30 sims)**: Balanced throughput
- **Large batches (30-50 sims)**: Maximum efficiency but longer wait

### 2. Parallel Workers

- **2 workers**: Low resource usage, slower
- **4 workers**: Recommended default
- **8 workers**: Maximum performance (requires 16+ GB RAM)

### 3. Simulation Duration

- **Test runs**: 0.5-1.0 hours (quick verification)
- **Production runs**: 2.0-4.0 hours (comprehensive analysis)
- **Full scenarios**: 6.0-24.0 hours (detailed investigation)

### 4. Analysis Focus

- **Minimal**: `["summary"]` - Quick overview
- **Standard**: `["summary", "edgedata"]` - Most use cases
- **Comprehensive**: `["summary", "edgedata", "tripinfo", "performance"]` - Full analysis

### 5. Resource Management

- Monitor system resources during batch execution
- Avoid running multiple large batches simultaneously
- Schedule long-running batches during off-peak hours

---

## FAQ

### Q: Can I run simulations from different event types in the same batch?

**A:** Yes, batch execution supports mixed event types. However, analysis comparisons work best when comparing scenarios of the same event (e.g., baseline vs VSS for event 10754).

### Q: How long does a typical simulation take?

**A:** Depends on duration and network complexity:
- 0.5 hours simulation time: ~30-60 minutes
- 2.0 hours simulation time: ~1-2 hours
- 24.0 hours simulation time: ~10-15 hours

### Q: Can I modify scenario parameters after case creation?

**A:** Only **overridable fields** can be modified (duration, seed, output config). **Immutable fields** (event details, location, control strategy) cannot be changed.

### Q: What if a simulation fails?

**A:** Failed simulations are marked as "failed" in batch status. Analysis will skip failed simulations and continue with successful ones. Check SUMO logs for error details.

### Q: Can I rerun a simulation?

**A:** Yes, but you must create a new simulation from the same case. The old simulation result will be preserved for comparison.

### Q: How do I compare different control strategies?

**A:** Create cases for the same event with different control strategies:
1. `scenario_10754_none` (baseline)
2. `scenario_10754_vss` (VSS control)
3. `scenario_10754_tec` (TEC control)

Run simulations for all, then use analysis comparison to view differences.

### Q: Where are results stored?

**A:**
```
cases/
└── case_id/
    ├── simulations/
    │   └── sim_id/
    │       └── outputs/          # Simulation results
    └── analysis/
        └── batch_id/
            ├── summary/           # Summary analysis
            ├── edgedata/          # EdgeData analysis
            ├── tripinfo/          # TripInfo analysis
            └── performance/       # Performance analysis
```

### Q: Can I export results for external analysis?

**A:** Yes, all results are JSON/XML format. Click "Export JSON" in dashboard or directly access files in analysis directories.

---

## Additional Resources

- **API Reference**: See `docs/PHASE_2_API_REFERENCE.md`
- **Developer Guide**: See `docs/PHASE_2_DEVELOPER_GUIDE.md`
- **Architecture Documentation**: See `CLAUDE.md`
- **Scenario Browser Guide**: See Phase 1 documentation

---

**Last Updated**: 2025-11-12
**Version**: 1.0
**Feedback**: Report issues via GitHub or contact system administrator
