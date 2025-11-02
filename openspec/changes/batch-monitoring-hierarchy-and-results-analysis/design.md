# Design: Batch Monitoring Hierarchy and Results Analysis

This document describes the technical design for organizing batch monitoring hierarchically and implementing two-layer results analysis.

---

## System Architecture Overview

### Data Structure

```
Database / File System
├── cases/
│   └── case_001/
│       ├── metadata.json (case info)
│       └── simulations/
│           ├── plan_opti/
│           │   └── batch_20251102_091500/
│           │       ├── batch_metadata.json (batch config, output_level, num_seeds)
│           │       ├── simulation_config.json (SUMO output settings, applied to all plans)
│           │       ├── baseline_plan/
│           │       │   ├── sim_66/
│           │       │   │   ├── summary.xml ← results data
│           │       │   │   ├── tripinfo.xml
│           │       │   │   └── ...
│           │       │   ├── sim_67/
│           │       │   └── sim_68/
│           │       ├── plan_001/
│           │       │   ├── sim_66/
│           │       │   ├── sim_67/
│           │       │   └── sim_68/
│           │       └── plan_002/
│           │           └── ... (same structure)
│           └── ... (other batch types)
│   └── case_002/
│       └── ... (similar structure)
```

### UI Component Hierarchy

```
Batch Monitoring View
├── Case Group A (case_001 - 案例名称)
│   ├── [+/-] toggle, batch count, latest status
│   ├── Batch Card 1
│   │   ├── batch_id, case_name, plan_count
│   │   ├── status badge, created_at
│   │   ├── "查看结果" button → Results View
│   │   └── Action buttons (delete, etc.)
│   ├── Batch Card 2
│   └── ...
└── Case Group B (case_002 - 案例名称)
    └── ...

Results View (Modal/Separate Page)
├── Batch Summary
│   ├── batch_id, case_name, plan_count, task_count
│   └── Output level, Random seed info
├── Results Table (comparison across plans)
│   ├── Plan name | Metric 1 | Improvement Rate | Metric 2 | ...
│   ├── baseline_plan | 1201.67s | - | 28666 veh | ...
│   ├── plan_001 | 1051.67s | +12.5% ↑ | 29500 veh | +2.9% ↑ | ...
│   └── ...
├── Chart Visualizations
│   ├── Bar chart (metric comparison)
│   ├── Improvement rate visualization
│   └── Optional: time series curve (peak vehicles over time)
└── Detailed Metrics Section (expandable per plan)
```

---

## Implementation Design

### 1. Backend: Batch Optimization Service Enhancement

**File**: `api/services/batch_optimization_service.py`

#### New Parameters in `create_batch()`

```python
async def create_batch(
    case_id: str,
    plan_ids: List[str],
    num_seeds: int = 3,           # NEW: 1-10 seeds per plan
    base_seed: int = 66,          # NEW: starting seed
    output_level: str = "standard" # NEW: minimal/standard/full
) -> Dict:
    """Create batch with output configuration and baseline enforcement."""

    # 1. Ensure baseline_plan included (enforcement)
    if "baseline_plan" not in plan_ids:
        plan_ids.insert(0, "baseline_plan")
        logger.info(f"Auto-included baseline_plan in batch")

    # 2. Validate output_level
    valid_levels = ["minimal", "standard", "full"]
    if output_level not in valid_levels:
        output_level = "standard"

    # 3. Validate num_seeds
    if not 1 <= num_seeds <= 10:
        raise ValueError(f"num_seeds must be 1-10, got {num_seeds}")

    # 4. Create simulation_config.json (applied to ALL plans)
    simulation_config = {
        "output_level": output_level,
        "num_seeds": num_seeds,
        "base_seed": base_seed,
        "seed_sequence": list(range(base_seed, base_seed + num_seeds)),
        # Output settings based on output_level
        "summary_xml": True,  # Always enabled
        "tripinfo_xml": output_level in ["standard", "full"],
        "edgedata_xml": output_level in ["standard", "full"],
        "e1_detectors": output_level in ["standard", "full"],
        "created_at": datetime.utcnow().isoformat()
    }

    # 5. Save configuration to batch directory
    batch_dir = Path(f"cases/{case_id}/simulations/plan_opti/{batch_id}")
    config_path = batch_dir / "simulation_config.json"
    save_json(config_path, simulation_config)

    # 6. Generate tasks with same seed sequence for all plans
    # For each plan, create tasks: plan × seed
    tasks = []
    for plan_id in plan_ids:
        for seed in simulation_config["seed_sequence"]:
            task_id = f"{plan_id}_seed{seed}"
            tasks.append({
                "task_id": task_id,
                "plan_id": plan_id,
                "seed": seed,
                "status": "pending"
            })

    # 7. Store batch metadata
    batch_metadata = {
        "batch_id": batch_id,
        "case_id": case_id,
        "plan_ids": plan_ids,
        "output_level": output_level,
        "num_seeds": num_seeds,
        "base_seed": base_seed,
        "total_tasks": len(tasks),
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    return batch_metadata
```

#### New Method: Results Analysis

```python
async def get_batch_results(batch_id: str, case_id: str) -> Dict:
    """
    Fetch and analyze batch results from summary.xml files.

    Returns:
    {
        "batch_id": "...",
        "baseline_metrics": {...},  # Average across N seeds
        "plans": [
            {
                "plan_id": "baseline_plan",
                "is_baseline": true,
                "metrics": {...},     # Average across N seeds
                "samples": 3          # number of seeds
            },
            {
                "plan_id": "plan_001",
                "is_baseline": false,
                "metrics": {...},
                "improvement_rates": {...},  # Relative to baseline
                "samples": 3
            }
        ]
    }
    """
    batch_result_analyzer = BatchResultAnalyzer()

    # Query batch metadata
    batch_metadata_path = f"cases/{case_id}/simulations/plan_opti/{batch_id}/batch_metadata.json"
    batch_metadata = load_json(batch_metadata_path)

    plan_ids = batch_metadata["plan_ids"]

    # For each plan, collect all summary.xml files (one per seed)
    all_plans_data = {}
    baseline_metrics = None

    for plan_id in plan_ids:
        plan_results = await batch_result_analyzer.aggregate_plan_results(
            case_id=case_id,
            batch_id=batch_id,
            plan_id=plan_id,
            num_seeds=batch_metadata["num_seeds"],
            base_seed=batch_metadata["base_seed"]
        )

        all_plans_data[plan_id] = plan_results

        if plan_id == "baseline_plan":
            baseline_metrics = plan_results["metrics"]

    # Calculate improvement rates for each control plan
    result = {
        "batch_id": batch_id,
        "baseline_metrics": baseline_metrics,
        "plans": []
    }

    for plan_id, plan_data in all_plans_data.items():
        plan_info = {
            "plan_id": plan_id,
            "is_baseline": (plan_id == "baseline_plan"),
            "metrics": plan_data["metrics"],
            "samples": plan_data["sample_count"]
        }

        if plan_id != "baseline_plan" and baseline_metrics:
            # Calculate improvement rates
            plan_info["improvement_rates"] = \
                batch_result_analyzer.calculate_improvement_rates(
                    baseline_metrics,
                    plan_data["metrics"]
                )

        result["plans"].append(plan_info)

    return result
```

### 2. Backend: Results Analyzer Module

**File**: `shared/control_tools/batch_result_analyzer.py` (new)

```python
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import statistics

class BatchResultAnalyzer:
    """Parses summary.xml and aggregates batch results for comparison analysis."""

    KEY_METRICS = [
        "meanTravelTime",      # Average trip time (seconds)
        "ended",               # Vehicles completed (count)
        "meanWaitingTime",     # Average waiting time (seconds)
        "maxRunningPersons",   # Peak vehicles in network (count)
    ]

    async def aggregate_plan_results(
        self,
        case_id: str,
        batch_id: str,
        plan_id: str,
        num_seeds: int,
        base_seed: int
    ) -> Dict:
        """Aggregate results from N random simulation runs."""

        all_metrics = {metric: [] for metric in self.KEY_METRICS}

        for seed in range(base_seed, base_seed + num_seeds):
            summary_xml_path = Path(
                f"cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/summary.xml"
            )

            if not summary_xml_path.exists():
                logger.warning(f"Missing summary.xml: {summary_xml_path}")
                continue

            metrics = self._parse_summary_xml(summary_xml_path)

            for metric_name, metric_value in metrics.items():
                if metric_name in self.KEY_METRICS:
                    all_metrics[metric_name].append(metric_value)

        # Calculate averages (exclude outliers using IQR method if N > 3)
        averaged_metrics = {}
        for metric_name, values in all_metrics.items():
            if values:
                # Simple: use median for robustness, or mean if preferred
                averaged_metrics[metric_name] = {
                    "value": statistics.mean(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values)
                }

        return {
            "metrics": averaged_metrics,
            "sample_count": len([m for m in all_metrics[self.KEY_METRICS[0]] if m])
        }

    def _parse_summary_xml(self, xml_path: Path) -> Dict:
        """Extract key metrics from summary.xml final step element."""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Get last step (summary data)
        last_step = None
        for step in root.findall('step'):
            last_step = step

        if last_step is None:
            return {}

        metrics = {}
        for metric in self.KEY_METRICS:
            attr_value = last_step.get(metric)
            if attr_value:
                try:
                    # Convert to appropriate type
                    if metric in ["meanTravelTime", "meanWaitingTime"]:
                        metrics[metric] = float(attr_value)
                    else:
                        metrics[metric] = int(float(attr_value))
                except (ValueError, TypeError):
                    logger.warning(f"Cannot parse {metric}={attr_value}")

        return metrics

    def calculate_improvement_rates(
        self,
        baseline_metrics: Dict,
        plan_metrics: Dict
    ) -> Dict:
        """Calculate improvement rates (positive = improvement)."""

        improvements = {}

        # Time metrics: lower is better (negative improvement = good)
        time_metrics = ["meanTravelTime", "meanWaitingTime"]

        # Count metrics: higher is better (positive improvement = good)
        count_metrics = ["ended", "maxRunningPersons"]

        for metric, baseline_value in baseline_metrics.items():
            if metric not in plan_metrics:
                continue

            plan_value = plan_metrics[metric].get("value", 0)

            if baseline_value.get("value", 0) == 0:
                continue

            baseline_val = baseline_value.get("value", 0)

            if metric in time_metrics:
                # For time: lower is better
                # improvement_rate = (baseline - plan) / baseline
                # Positive = improvement (plan is faster)
                rate = (baseline_val - plan_value) / baseline_val * 100
            else:
                # For counts: higher is better
                # improvement_rate = (plan - baseline) / baseline
                # Positive = improvement (more vehicles, better capacity)
                rate = (plan_value - baseline_val) / baseline_val * 100

            improvements[metric] = {
                "rate": round(rate, 1),
                "direction": "up" if rate > 0 else "down",
                "symbol": "↑" if rate > 0 else "↓"
            }

        return improvements
```

### 3. Frontend: Case Grouping Render Logic

**File**: `frontend/control/js/batch_simulation.js`

**Key Function**: `renderBatchListGroupedByCase(batches, caseMetadata)`

```javascript
/**
 * Group batches by case and render hierarchical list.
 * @param {Array} batches - All batches from API
 * @param {Object} caseMetadata - Map of case_id → case info
 */
function renderBatchListGroupedByCase(batches, caseMetadata) {
  const container = document.getElementById('batch-list-container');
  container.innerHTML = '';

  // Group batches by case_id
  const groupedByCase = {};
  batches.forEach(batch => {
    if (!groupedByCase[batch.case_id]) {
      groupedByCase[batch.case_id] = [];
    }
    groupedByCase[batch.case_id].push(batch);
  });

  // Sort cases by latest batch time (newest first)
  const sortedCases = Object.entries(groupedByCase)
    .sort((a, b) => {
      const latestA = Math.max(...a[1].map(b => new Date(b.created_at)));
      const latestB = Math.max(...b[1].map(b => new Date(b.created_at)));
      return latestB - latestA;
    });

  // Render each case group
  sortedCases.forEach(([caseId, caseBatches]) => {
    const caseInfo = caseMetadata[caseId] || { case_name: caseId };
    const caseGroup = createCaseGroup(caseId, caseInfo, caseBatches);
    container.appendChild(caseGroup);
  });
}

function createCaseGroup(caseId, caseInfo, caseBatches) {
  const groupEl = document.createElement('div');
  groupEl.className = 'case-group';
  groupEl.id = `case-group-${caseId}`;

  // Header: Case name, batch count, latest status
  const headerEl = document.createElement('div');
  headerEl.className = 'case-group-header';

  const toggleBtn = document.createElement('button');
  toggleBtn.className = 'case-group-toggle';
  toggleBtn.textContent = '[-]'; // Expanded by default
  toggleBtn.onclick = () => toggleCaseGroup(caseId);

  const titleEl = document.createElement('div');
  titleEl.className = 'case-group-title';
  titleEl.innerHTML = `
    <span class="case-id">${caseId}</span>
    <span class="case-name">${caseInfo.case_name || '未命名案例'}</span>
    <span class="batch-count">${caseBatches.length}个批次</span>
  `;

  const latestBatch = caseBatches.sort((a, b) =>
    new Date(b.created_at) - new Date(a.created_at)
  )[0];

  const latestStatusEl = document.createElement('span');
  latestStatusEl.className = `status-badge status-${latestBatch.status}`;
  latestStatusEl.textContent = getStatusLabel(latestBatch.status);

  headerEl.appendChild(toggleBtn);
  headerEl.appendChild(titleEl);
  headerEl.appendChild(latestStatusEl);

  // Body: Batch cards
  const bodyEl = document.createElement('div');
  bodyEl.className = 'case-group-body';
  bodyEl.id = `case-group-body-${caseId}`;

  caseBatches
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .forEach(batch => {
      const batchCard = createBatchCard(batch);
      bodyEl.appendChild(batchCard);
    });

  groupEl.appendChild(headerEl);
  groupEl.appendChild(bodyEl);

  return groupEl;
}

function toggleCaseGroup(caseId) {
  const body = document.getElementById(`case-group-body-${caseId}`);
  const toggle = document.querySelector(`#case-group-${caseId} .case-group-toggle`);

  body.classList.toggle('hidden');
  toggle.textContent = body.classList.contains('hidden') ? '[+]' : '[-]';
}
```

### 4. Frontend: Results Analysis Rendering

**File**: `frontend/control/js/batch_results.js` (new or enhanced)

```javascript
/**
 * Fetch and render batch results (Layer 1: summary.xml comparison).
 */
async function loadAndDisplayBatchResults(batchId, caseId) {
  try {
    // Fetch aggregated results from backend
    const response = await fetch(
      `/api/v1/control/optimization/batch/${batchId}/results`
    );

    if (!response.ok) {
      showError('Failed to load batch results');
      return;
    }

    const resultsData = await response.json();

    // Render results view
    const resultsContainer = document.getElementById('batch-results-container');
    resultsContainer.innerHTML = '';

    // 1. Batch summary
    renderBatchSummary(resultsContainer, resultsData);

    // 2. Comparison table
    renderComparisonTable(resultsContainer, resultsData);

    // 3. Visualizations
    renderCharts(resultsContainer, resultsData);

  } catch (error) {
    console.error('Error loading results:', error);
    showError('Error loading batch results');
  }
}

function renderBatchSummary(container, resultsData) {
  const summaryEl = document.createElement('div');
  summaryEl.className = 'results-summary';

  const baselinePlan = resultsData.plans.find(p => p.is_baseline);
  const controlPlans = resultsData.plans.filter(p => !p.is_baseline);

  summaryEl.innerHTML = `
    <div class="summary-info">
      <h3>批次结果总览</h3>
      <p><strong>基准方案:</strong> ${baselinePlan.plan_id}</p>
      <p><strong>管控方案:</strong> ${controlPlans.map(p => p.plan_id).join(', ')}</p>
      <p><strong>仿真次数:</strong> ${baselinePlan.samples}次 (种子: 66-${66 + baselinePlan.samples - 1})</p>
      <p><strong>输出级别:</strong> standard (完整输出)</p>
    </div>
  `;

  container.appendChild(summaryEl);
}

function renderComparisonTable(container, resultsData) {
  const tableEl = document.createElement('div');
  tableEl.className = 'comparison-table-container';

  // Build table header
  const metrics = ['meanTravelTime', 'ended', 'meanWaitingTime', 'maxRunningPersons'];
  const metricLabels = {
    'meanTravelTime': '平均旅行时间 (秒)',
    'ended': '完成车辆数 (辆)',
    'meanWaitingTime': '平均等待时间 (秒)',
    'maxRunningPersons': '最高在网车辆 (辆)'
  };

  let html = `<table class="comparison-table">
    <thead>
      <tr>
        <th>方案</th>
        ${metrics.map(m => `
          <th>${metricLabels[m]}</th>
          <th>改善率</th>
        `).join('')}
      </tr>
    </thead>
    <tbody>
  `;

  // Render baseline first
  const baselinePlan = resultsData.plans.find(p => p.is_baseline);
  html += renderTableRow(baselinePlan, metrics);

  // Then render control plans
  const controlPlans = resultsData.plans.filter(p => !p.is_baseline);
  controlPlans.forEach(plan => {
    html += renderTableRow(plan, metrics);
  });

  html += `</tbody></table>`;

  tableEl.innerHTML = html;
  container.appendChild(tableEl);
}

function renderTableRow(plan, metrics) {
  let html = `<tr class="plan-row ${plan.is_baseline ? 'baseline' : 'control'}">
    <td><strong>${plan.plan_id}${plan.is_baseline ? ' (基准)' : ''}</strong></td>
  `;

  metrics.forEach(metric => {
    const metricData = plan.metrics[metric];
    if (!metricData) return;

    const value = formatMetricValue(metric, metricData.value);
    let improvementCell = '<td>-</td>';

    if (plan.improvement_rates && plan.improvement_rates[metric]) {
      const improvement = plan.improvement_rates[metric];
      const cssClass = improvement.direction === 'up' ? 'positive' : 'negative';
      improvementCell = `
        <td class="improvement ${cssClass}">
          ${improvement.rate > 0 ? '+' : ''}${improvement.rate}% ${improvement.symbol}
        </td>
      `;
    }

    html += `<td>${value}</td>${improvementCell}`;
  });

  html += '</tr>';
  return html;
}

function formatMetricValue(metric, value) {
  if (metric === 'meanTravelTime' || metric === 'meanWaitingTime') {
    return value.toFixed(2) + 's';
  }
  return Math.round(value).toLocaleString();
}

function renderCharts(container, resultsData) {
  const chartsEl = document.createElement('div');
  chartsEl.className = 'results-charts';

  // Bar chart: metric comparison
  const barChartEl = createBarChart(resultsData);
  chartsEl.appendChild(barChartEl);

  container.appendChild(chartsEl);
}
```

### 5. Frontend: Styling

**File**: `frontend/control/css/simulations.css` (additions)

```css
/* Case Group Styles */
.case-group {
  margin-bottom: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.case-group-header {
  padding: 1rem;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  user-select: none;
}

.case-group-header:hover {
  background: #e8e8e8;
}

.case-group-toggle {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  font-weight: bold;
  min-width: 2rem;
}

.case-group-title {
  flex: 1;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.case-id {
  font-weight: 600;
  color: #333;
}

.case-name {
  color: #666;
  font-size: 0.9rem;
}

.batch-count {
  font-size: 0.85rem;
  color: #999;
  margin-left: auto;
}

.case-group-body {
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.case-group-body.hidden {
  display: none;
}

/* Comparison Table Styles */
.comparison-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  background: white;
  font-size: 0.9rem;
}

.comparison-table thead {
  background: #4CAF50;
  color: white;
}

.comparison-table th,
.comparison-table td {
  padding: 0.75rem 1rem;
  text-align: right;
  border-bottom: 1px solid #ddd;
}

.comparison-table th:first-child,
.comparison-table td:first-child {
  text-align: left;
  font-weight: 600;
}

.comparison-table .plan-row.baseline {
  background: #f5f5f5;
  font-weight: 600;
}

.comparison-table .improvement {
  font-weight: 600;
}

.comparison-table .improvement.positive {
  color: #28a745;
}

.comparison-table .improvement.negative {
  color: #dc3545;
}
```

---

## Execution Sequence

1. **Phase 1** (6-8h): Frontend case grouping
   - Modify batch_simulation.js to group by case_id
   - Add case group toggle/collapse UI
   - Update simulations.html structure

2. **Phase 2** (8-10h): Backend results analysis
   - Implement BatchResultAnalyzer (summary.xml parsing)
   - Add results endpoint to batch_optimization_service
   - Modify batch API request model to include output_level

3. **Phase 3** (4-6h): Batch configuration consistency
   - Update batch creation form (output level selector)
   - Implement output configuration validation
   - Save simulation_config.json to batch directory

4. **Phase 4** (2-4h): Baseline enforcement
   - Auto-include baseline_plan in batch creation
   - UI mark baseline as "standard plan"

5. **Phase 5** (2-3h): Seed configuration
   - Add num_seeds selector to batch creation form
   - Implement seed sequence generation
   - Store config in batch metadata

6. **Phase 6** (4-6h): Results visualization
   - Implement comparison table rendering
   - Add chart visualizations
   - Wire up results view modal/page

---

## Testing Strategy

### Unit Tests

- BatchResultAnalyzer: Test summary.xml parsing, improvement rate calculation
- Seed sequence generation: Test edge cases (num_seeds=1, 10, boundary values)
- Output level validation: Test invalid inputs, default fallback

### Integration Tests

- Batch creation with output_level parameter
- Baseline auto-inclusion verification
- Results data aggregation across multiple plans and seeds

### E2E Tests

- Create batch with case grouping visible
- Verify batches grouped correctly
- Click batch → view results
- Verify comparison table displays correctly
- Verify improvement rates calculated correctly

---

## Error Handling

### Missing summary.xml

- Log warning: "Missing summary.xml: <path>"
- Skip that seed's results
- Continue with remaining seeds
- If all seeds missing: show error "No result data available for plan"

### Invalid XML format

- Catch ET.ParseError, log and skip
- Return partial results with available plans

### Output configuration mismatch

- Validate during batch creation
- Return 400 error if conflicting configs detected
- Message: "All plans must use same output configuration"

---

## Future Enhancements (Not in Scope)

1. **Layer 2 Results**: Detailed analysis using tripinfo.xml and edgedata.xml
2. **Results Export**: Download results as CSV/PDF
3. **Historical Comparison**: Compare batch results across multiple batches
4. **Statistical Significance**: Add significance tests for improvement rates
