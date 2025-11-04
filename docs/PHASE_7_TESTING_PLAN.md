# Phase 7: Integration & Testing - Testing Plan and Implementation Guide

**Date**: 2025-11-04
**OpenSpec Change**: batch-monitoring-hierarchy-and-results-analysis
**Phase Status**: 0% → Planning for full implementation
**Current Project Progress**: 75% (6 of 8 phases complete)

---

## Executive Summary

Phase 7 focuses on comprehensive testing to validate all implemented features across the batch monitoring hierarchy and results analysis system. This document outlines the testing strategy, test cases, and implementation guidance for:

- **T7.1**: Unit tests for BatchResultAnalyzer
- **T7.2**: Integration tests for batch operations
- **T7.3**: E2E tests for UI workflows (with chart visualization validation)
- **T7.4**: Manual UAT and verification

---

## Testing Strategy Overview

### Three-Level Testing Approach

```
┌─────────────────────────────────────────┐
│         Unit Tests (T7.1 & T7.2)        │
│  - BatchResultAnalyzer methods          │
│  - Batch service operations             │
│  - Data transformations                 │
│  Coverage: ≥90% code coverage           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Integration Tests (T7.2 continued)     │
│  - Batch creation → results workflow    │
│  - Configuration persistence            │
│  - Data aggregation and calculations    │
│  Coverage: End-to-end service flow      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   E2E Tests (T7.3) + Manual UAT (T7.4)  │
│  - Complete user workflows              │
│  - UI rendering and interactivity       │
│  - Chart visualization validation       │
│  - Cross-browser compatibility          │
└─────────────────────────────────────────┘
```

---

## T7.1: Unit Tests for BatchResultAnalyzer

### Purpose
Validate the core metrics extraction and calculation logic that powers results analysis.

### File Location
`tests/unit/test_batch_result_analyzer.py` (NEW FILE)

### Test Class Structure

```python
class TestBatchResultAnalyzer:
    """Batch result analyzer unit tests"""

    # Setup fixtures
    @pytest.fixture
    def analyzer(self):
        """Initialize BatchResultAnalyzer instance"""
        return BatchResultAnalyzer()

    @pytest.fixture
    def sample_summary_xml(self):
        """Provide sample summary.xml content"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <summary>
            <meanTravelTime value="1200.5"/>
            <waitingTime value="45.3"/>
            <ended value="1250"/>
            <maxRunningPersons value="450"/>
        </summary>"""
```

### Test Cases to Implement

#### T7.1.1: XML Parsing Tests
```python
def test_parse_summary_xml_valid_file(analyzer, sample_summary_xml):
    """Test parsing valid summary.xml file"""
    # Create temporary XML file
    # Call _parse_summary_xml()
    # Assert metrics extracted correctly
    assert result['mean_travel_time'] == 1200.5
    assert result['mean_waiting_time'] == 45.3
    assert result['total_ended'] == 1250
    assert result['max_running'] == 450

def test_parse_summary_xml_missing_file(analyzer, tmp_path):
    """Test handling of missing summary.xml"""
    # Call _parse_summary_xml() with non-existent file
    # Assert returns empty dict or raises appropriate error
    assert result == {} or raises FileNotFoundError

def test_parse_summary_xml_malformed_xml(analyzer, tmp_path):
    """Test handling of malformed XML"""
    # Create XML with syntax errors
    # Call _parse_summary_xml()
    # Assert handles gracefully (returns empty or logged error)

def test_parse_summary_xml_missing_metrics(analyzer, tmp_path):
    """Test XML with missing metric values"""
    # Create XML missing some metrics
    # Call _parse_summary_xml()
    # Assert returns available metrics with defaults for missing ones
```

#### T7.1.2: Aggregation Tests
```python
def test_aggregate_plan_results_single_seed(analyzer):
    """Test aggregation with N=1 seed (no aggregation)"""
    # Input: 1 result with metrics
    # Assert: mean, std, min, max calculated correctly
    # Expected std: 0 (single value)

def test_aggregate_plan_results_three_seeds(analyzer):
    """Test aggregation with N=3 seeds"""
    # Input: 3 results (seeds 66, 67, 68)
    # Assert: mean, std, min, max calculated correctly
    # Verify standard deviation > 0

def test_aggregate_plan_results_five_seeds(analyzer):
    """Test aggregation with N=5 seeds"""
    # Input: 5 results
    # Assert: All aggregation functions work correctly
    # Verify ranges (min ≤ mean ≤ max)

def test_aggregate_plan_results_missing_data(analyzer):
    """Test aggregation with missing seed results"""
    # Input: 3 expected seeds, only 2 results
    # Assert: Handles gracefully (aggregates available data)
```

#### T7.1.3: Improvement Rate Tests
```python
def test_calculate_improvement_rate_positive(analyzer):
    """Test positive improvement (baseline 1200, test 1050)"""
    # baseline_value = 1200, test_value = 1050, metric = 'speed'
    # Call _calculate_improvement_rate()
    # Assert improvement rate ≈ +12.5%

def test_calculate_improvement_rate_negative(analyzer):
    """Test negative improvement (baseline 100, test 120)"""
    # baseline_value = 100, test_value = 120, metric = 'waiting_time'
    # Call _calculate_improvement_rate()
    # Assert improvement rate ≈ -20% (worse)

def test_calculate_improvement_rate_zero_baseline(analyzer):
    """Test division by zero handling"""
    # baseline_value = 0, test_value = 100
    # Call _calculate_improvement_rate()
    # Assert returns 0 or handles gracefully

def test_calculate_improvement_rate_directional_awareness(analyzer):
    """Test metric-specific direction awareness"""
    # For 'speed' metrics: higher is better
    # For 'waiting_time' metrics: lower is better
    # Call with different metric types
    # Assert rate calculations respect metric direction
```

#### T7.1.4: Comparison Summary Tests
```python
def test_generate_comparison_summary_single_metric(analyzer):
    """Test comparison summary generation"""
    # Input: 2 plans with aggregated metrics
    # Call _generate_comparison_summary()
    # Assert: Table-ready format
    # Verify: Plan names, metrics, improvement rates

def test_generate_comparison_summary_multiple_metrics(analyzer):
    """Test with multiple metrics"""
    # Input: 2 plans with 4+ metrics each
    # Assert: All metrics included in summary

def test_generate_comparison_summary_missing_baseline(analyzer):
    """Test handling when baseline not first plan"""
    # Input: Plans ordered differently
    # Assert: Still identifies baseline correctly
```

### Test Coverage Goals
- **Line Coverage**: ≥90%
- **Branch Coverage**: ≥85%
- **Function Coverage**: 100%

### Running T7.1 Tests
```bash
# Activate environment
conda activate od_project

# Run all BatchResultAnalyzer tests
pytest tests/unit/test_batch_result_analyzer.py -v

# Run with coverage report
pytest tests/unit/test_batch_result_analyzer.py --cov=shared.analysis_tools.batch_result_analyzer --cov-report=html
```

---

## T7.2: Integration Tests for Batch Operations

### Purpose
Validate the complete batch creation, execution, and results analysis workflow.

### File Location
`tests/unit/services/test_batch_optimization_service.py` (EXTEND EXISTING)

### Test Class Structure

```python
class TestBatchOptimizationServiceIntegration:
    """Integration tests for batch operations"""

    @pytest.fixture
    def batch_service(self, temp_test_env):
        """Initialize BatchOptimizationService"""
        return BatchOptimizationService()

    @pytest.fixture
    def setup_test_data(self, temp_test_env):
        """Create test case and plans"""
        # Setup case directory
        # Create baseline_plan
        # Create 2-3 test plans
        # Return setup context
```

### Test Cases to Implement

#### T7.2.1: Batch Creation Tests
```python
def test_create_batch_with_standard_output_level(batch_service, setup_test_data):
    """Test batch creation with standard output level"""
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        output_level="standard",
        num_seeds=3,
        base_seed=66
    )
    # Assert batch created successfully
    assert response['batch_id'] is not None
    assert response['status'] == 'pending'
    # Verify configuration persisted
    config_file = Path(response['batch_dir']) / "simulation_config.json"
    assert config_file.exists()

def test_create_batch_with_minimal_output_level(batch_service, setup_test_data):
    """Test batch creation with minimal output level"""
    # Minimal: summary.xml + e1_detector only
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        output_level="minimal"
    )
    # Assert output config reflects minimal settings

def test_create_batch_with_full_output_level(batch_service, setup_test_data):
    """Test batch creation with full output level"""
    # Full: all outputs enabled
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        output_level="full"
    )
    # Assert output config has all options enabled

def test_create_batch_auto_includes_baseline(batch_service, setup_test_data):
    """Test automatic baseline plan inclusion"""
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["plan_001"],  # NO baseline_plan specified
        num_seeds=3,
        base_seed=66
    )
    # Assert baseline_plan automatically added
    assert "baseline_plan" in response['plan_ids']
    assert response['plan_ids'][0] == "baseline_plan"
```

#### T7.2.2: Seed Configuration Tests
```python
def test_seed_configuration_num_seeds_3(batch_service, setup_test_data):
    """Test seed generation with num_seeds=3"""
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        num_seeds=3,
        base_seed=66
    )
    # Load batch metadata
    metadata = json.load(open(Path(response['batch_dir']) / "batch_metadata.json"))
    # Assert num_seeds = 3
    assert metadata['num_seeds'] == 3

def test_seed_sequence_generation(batch_service, setup_test_data):
    """Test seed sequence generation"""
    # base_seed=66, num_seeds=3 → [66, 67, 68]
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        num_seeds=3,
        base_seed=66
    )
    config_file = Path(response['batch_dir']) / "simulation_config.json"
    config = json.load(open(config_file))
    # Assert seed_sequence correct
    assert config['seed_sequence'] == [66, 67, 68]

def test_seed_configuration_high_num_seeds(batch_service, setup_test_env):
    """Test with high num_seeds value"""
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        num_seeds=10,
        base_seed=100
    )
    # Assert total_tasks = 2 plans × 10 seeds = 20
    assert response['total_tasks'] == 20
```

#### T7.2.3: Results Retrieval and Aggregation Tests
```python
def test_get_batch_results_basic(batch_service, setup_test_data, mock_simulations):
    """Test batch results retrieval"""
    # Create batch with simulations
    # Call get_batch_results()
    # Assert results structure correct
    results = batch_service.get_batch_results("test_case_001", "batch_12345")
    assert 'plan_results' in results
    assert len(results['plan_results']) >= 1

def test_get_batch_results_plan_comparison(batch_service, setup_test_data, mock_simulations):
    """Test plan comparison in results"""
    results = batch_service.get_batch_results("test_case_001", "batch_12345")
    # Assert baseline plan present
    baseline = next((p for p in results['plan_results'] if 'baseline' in p['plan_id']), None)
    assert baseline is not None
    # Assert test plans present
    test_plans = [p for p in results['plan_results'] if 'baseline' not in p['plan_id']]
    assert len(test_plans) >= 1

def test_get_batch_results_aggregated_metrics(batch_service, setup_test_data, mock_simulations):
    """Test aggregated metrics calculation"""
    results = batch_service.get_batch_results("test_case_001", "batch_12345")
    # For each plan
    for plan in results['plan_results']:
        # Assert aggregated_metrics has mean, std, min, max
        for metric_name, metric_data in plan['aggregated_metrics'].items():
            assert 'mean' in metric_data
            assert 'std' in metric_data
            assert 'min' in metric_data
            assert 'max' in metric_data
            # Assert min ≤ mean ≤ max
            assert metric_data['min'] <= metric_data['mean'] <= metric_data['max']

def test_get_batch_results_improvement_rates(batch_service, setup_test_data, mock_simulations):
    """Test improvement rate calculation"""
    results = batch_service.get_batch_results("test_case_001", "batch_12345")
    # For test plans (non-baseline)
    test_plans = [p for p in results['plan_results'] if 'improvement_vs_baseline' in p]
    assert len(test_plans) >= 1
    # For each improvement metric
    for plan in test_plans:
        for metric, rate in plan['improvement_vs_baseline'].items():
            # Assert improvement rate is percentage
            assert isinstance(rate, (int, float))
```

#### T7.2.4: Configuration Validation Tests
```python
def test_batch_config_validation_passes(batch_service, setup_test_data):
    """Test configuration validation passes for valid config"""
    response = batch_service.create_batch(
        case_id="test_case_001",
        plan_ids=["baseline_plan", "plan_001"],
        output_level="standard",
        num_seeds=3,
        base_seed=66
    )
    # Assert validation passed (should have succeeded)
    assert response['status'] == 'pending'

def test_batch_config_validation_detects_inconsistency(batch_service, setup_test_data):
    """Test configuration validation detects inconsistencies"""
    # Manually modify simulation_config.json after creation
    # to introduce inconsistency
    # Call validation function
    # Assert detects the inconsistency
```

### Running T7.2 Tests
```bash
# Activate environment
conda activate od_project

# Run all batch service integration tests
pytest tests/unit/services/test_batch_optimization_service.py -v

# Run specific test class
pytest tests/unit/services/test_batch_optimization_service.py::TestBatchOptimizationServiceIntegration -v
```

---

## T7.3: E2E Tests for UI Workflows

### Purpose
Validate complete user workflows through the web interface, including the new chart visualizations.

### File Location
`tests/e2e/test_batch_monitoring_hierarchy.spec.js` (CREATE/EXTEND)

### Test Suite Structure

```javascript
test.describe('Batch Monitoring Hierarchy and Results Analysis', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to simulations page
        // Ensure test data available
        // Wait for page load
    });

    // Test groups for each workflow
});
```

### Test Cases to Implement

#### T7.3.1: Case Grouping Tests
```javascript
test('Case groups display correctly with multiple cases', async ({ page }) => {
    // Navigate to batch monitoring
    // Assert case groups visible
    // Assert each case shows batch count
    // Assert batches grouped under correct case

    const caseGroups = page.locator('.case-group');
    const groupCount = await caseGroups.count();
    expect(groupCount).toBeGreaterThan(1);
});

test('Case group toggle expands and collapses', async ({ page }) => {
    // Find case group toggle button
    // Click to expand
    // Assert batches become visible
    // Click to collapse
    // Assert batches hidden

    const toggle = page.locator('.case-group-toggle').first();
    const batches = page.locator('.case-group-body').first();

    await expect(batches).toBeVisible();
    await toggle.click();
    await expect(batches).toBeHidden();
    await toggle.click();
    await expect(batches).toBeVisible();
});

test('Latest batch appears first in each case group', async ({ page }) => {
    // Get all batches in a case group
    // Assert ordered by created_at descending

    const batchCards = page.locator('.batch-card');
    const createdTimes = [];
    const count = await batchCards.count();
    for (let i = 0; i < count; i++) {
        const time = await batchCards.nth(i).getAttribute('data-created-at');
        createdTimes.push(new Date(time));
    }
    // Assert times are descending
    for (let i = 0; i < createdTimes.length - 1; i++) {
        expect(createdTimes[i].getTime()).toBeGreaterThanOrEqual(createdTimes[i+1].getTime());
    }
});
```

#### T7.3.2: Results View Tests
```javascript
test('Results view opens when "查看结果" button clicked', async ({ page }) => {
    // Click "查看结果" button on batch card
    // Assert results view opens (modal or new view)
    // Assert batch ID displayed in results

    const viewResultsBtn = page.locator('button:has-text("查看结果")').first();
    await viewResultsBtn.click();

    const resultsView = page.locator('.results-container');
    await expect(resultsView).toBeVisible();
});

test('Results summary displays batch metadata', async ({ page }) => {
    // Open results view
    // Assert batch ID visible
    // Assert case name visible
    // Assert plan count visible
    // Assert seed info visible

    const summary = page.locator('.results-summary');
    await expect(summary).toContainText(/批次ID|Batch ID/);
    await expect(summary).toContainText(/随机种子|Seeds/);
});
```

#### T7.3.3: Comparison Table Tests
```javascript
test('Comparison table displays all plans and metrics', async ({ page }) => {
    // Open results view
    // Assert table visible
    // Assert baseline plan highlighted/distinguished
    // Assert all plans listed

    const table = page.locator('.comparison-table');
    const rows = table.locator('tbody tr');
    expect(await rows.count()).toBeGreaterThan(0);

    // Check for baseline plan
    const baselineRow = table.locator('tr:has-text("基准方案")');
    await expect(baselineRow).toBeVisible();
});

test('Improvement rates displayed and color-coded', async ({ page }) => {
    // Open results view
    // Find improvement rate cells
    // Assert positive rates show green (or positive color)
    // Assert negative rates show red (or negative color)

    const positiveRates = page.locator('.improvement.positive');
    const negativeRates = page.locator('.improvement.negative');

    // Assert at least one positive (or negative) rate visible
    const positiveCount = await positiveRates.count();
    const negativeCount = await negativeRates.count();
    expect(positiveCount + negativeCount).toBeGreaterThan(0);
});

test('Table metrics match API response data', async ({ page, context }) => {
    // Intercept API call for results
    // Open results view
    // Compare displayed values with API response
    // Assert values match exactly

    const [response] = await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/batch') && response.url().includes('results')
        ),
        page.locator('button:has-text("查看结果")').first().click()
    ]);

    const data = await response.json();
    const displayedMetrics = await page.locator('.comparison-table tbody tr').count();
    expect(displayedMetrics).toBe(data.plan_results.length);
});
```

#### T7.3.4: Chart Visualization Tests (NEW - T6.3)
```javascript
test('Charts render below comparison table', async ({ page }) => {
    // Open results view
    // Assert chart containers visible
    // Assert canvas elements present

    const chartsContainer = page.locator('.charts-container');
    await expect(chartsContainer).toBeVisible();

    const canvases = page.locator('canvas[id^="chart-"]');
    const canvasCount = await canvases.count();
    expect(canvasCount).toBeGreaterThan(0);
});

test('Chart data matches comparison table values', async ({ page }) => {
    // Open results view
    // Extract chart data from Canvas
    // Extract table data
    // Assert they match

    // Note: Extracting data from Canvas requires accessing Chart.js instance
    // or using Playwright's screenshot comparison
    const table = page.locator('.comparison-table');
    const charts = page.locator('.charts-container');

    // Both should be visible
    await expect(table).toBeVisible();
    await expect(charts).toBeVisible();
});

test('Charts are responsive on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });

    // Open results view
    await page.locator('button:has-text("查看结果")').first().click();

    // Assert charts still visible and functional
    const chartsContainer = page.locator('.charts-container');
    await expect(chartsContainer).toBeVisible();

    // Assert no horizontal scrolling needed
    const containerWidth = await chartsContainer.boundingBox();
    const viewportWidth = page.viewportSize().width;
    expect(containerWidth.width).toBeLessThanOrEqual(viewportWidth);
});

test('Chart tooltips display on hover', async ({ page }) => {
    // Open results view
    // Hover over chart bar
    // Assert tooltip appears with formatted value

    const canvas = page.locator('canvas[id^="chart-"]').first();
    await canvas.hover();

    // Tooltip might be in Chart.js tooltip or custom element
    // Check for visible tooltip text
    const tooltip = page.locator('.chartjs-tooltip, [role="tooltip"]');
    // Tooltip may appear with data
});

test('Improvement rate chart shows percentage values', async ({ page }) => {
    // Open results view
    // Find improvement rate chart
    // Hover over bar
    // Assert tooltip shows percentage (%)

    const improvementChart = page.locator('canvas[id="improvement-rate-chart"]');
    if (await improvementChart.isVisible()) {
        await improvementChart.hover();
        // Should see percentage value in tooltip
    }
});
```

#### T7.3.5: Batch Creation Form Tests
```javascript
test('Output level selector works correctly', async ({ page }) => {
    // Navigate to batch creation
    // Select output_level "minimal"
    // Create batch
    // Verify API received correct output_level

    const outputLevelSelect = page.locator('[name="output_level"]');
    await outputLevelSelect.selectOption('minimal');

    const createBtn = page.locator('button:has-text("创建批次")');
    await createBtn.click();

    // Should see success message
    const success = page.locator('.success, [role="alert"]:has-text("成功")');
    await expect(success).toBeVisible();
});

test('Num seeds selector works correctly', async ({ page }) => {
    // Navigate to batch creation
    // Set num_seeds to 5
    // Create batch
    // Verify batch created with 5 seeds

    const numSeedsInput = page.locator('[name="num_seeds"]');
    await numSeedsInput.clear();
    await numSeedsInput.fill('5');

    // Verify input value
    expect(await numSeedsInput.inputValue()).toBe('5');

    // Create batch
    const createBtn = page.locator('button:has-text("创建批次")');
    await createBtn.click();
});

test('Baseline plan auto-included in plan list', async ({ page }) => {
    // Navigate to batch creation
    // Select only test plans (not baseline)
    // Create batch
    // Verify baseline plan added automatically

    // In results, baseline should be first plan
    const planList = page.locator('.comparison-table tbody tr').first();
    await expect(planList).toContainText('基准方案');
});
```

### Running T7.3 Tests
```bash
# Activate environment (if needed)
conda activate od_project

# Run all E2E tests
npx playwright test tests/e2e/test_batch_monitoring_hierarchy.spec.js

# Run specific test
npx playwright test tests/e2e/test_batch_monitoring_hierarchy.spec.js -g "Charts render"

# Run with UI mode (visual debugging)
npx playwright test tests/e2e/test_batch_monitoring_hierarchy.spec.js --ui

# Run in headed mode (see browser)
npx playwright test tests/e2e/test_batch_monitoring_hierarchy.spec.js --headed
```

---

## T7.4: Manual UAT and Verification

### Purpose
Comprehensive manual testing by team/stakeholders to validate user experience and business requirements.

### UAT Test Cases

#### UAT-1: Case Grouping with Multiple Cases
**Prerequisites**: 3+ cases with 2+ batches each in database

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to batch monitoring | Cases display in groups | ☐ |
| 2 | Count case groups | Number matches case count | ☐ |
| 3 | Count batches per group | Each group shows correct batch count | ☐ |
| 4 | Check sort order | Latest batches appear first | ☐ |
| 5 | Toggle case group | Batches show/hide correctly | ☐ |

#### UAT-2: Batch Creation with Different Output Levels
**Prerequisites**: None

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Create batch with "minimal" output | Batch created successfully | ☐ |
| 2 | Create batch with "standard" output | Batch created successfully | ☐ |
| 3 | Create batch with "full" output | Batch created successfully | ☐ |
| 4 | Verify config stored | Config file exists in batch dir | ☐ |
| 5 | Check output_level in metadata | Matches selected option | ☐ |

#### UAT-3: Seed Configuration
**Prerequisites**: None

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Create batch with num_seeds=1 | Batch created, 1 seed | ☐ |
| 2 | Create batch with num_seeds=3 | Batch created, 3 seeds | ☐ |
| 3 | Create batch with num_seeds=10 | Batch created, 10 seeds | ☐ |
| 4 | Set custom base_seed=100 | Seeds=[100,101,102...] | ☐ |
| 5 | Verify total_tasks | total_tasks = plans × seeds | ☐ |

#### UAT-4: Results View Display
**Prerequisites**: Completed batch with results

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Click "查看结果" button | Results view opens | ☐ |
| 2 | Check summary section | Batch ID, plan count visible | ☐ |
| 3 | Check comparison table | All plans and metrics displayed | ☐ |
| 4 | Check table formatting | Readable, professional appearance | ☐ |
| 5 | Check improvement rates | Positive values green, negative red | ☐ |

#### UAT-5: Chart Visualizations (NEW - T6.3)
**Prerequisites**: Completed batch with results

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | View results | Charts appear below table | ☐ |
| 2 | Count charts | Multiple charts for different metrics | ☐ |
| 3 | Verify chart data | Values match comparison table | ☐ |
| 4 | Hover over bars | Tooltips show formatted values | ☐ |
| 5 | Check improvement chart | Shows improvement rates with % | ☐ |
| 6 | Resize window | Charts remain responsive | ☐ |
| 7 | Test on mobile | Charts adapt to smaller screen | ☐ |

#### UAT-6: Error Handling
**Prerequisites**: Database and API running

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Try invalid batch ID | Error message displayed | ☐ |
| 2 | Try incomplete batch | Appropriate message shown | ☐ |
| 3 | Disconnect API | Graceful error handling | ☐ |
| 4 | Try missing results | Clear error message | ☐ |

#### UAT-7: Responsiveness Testing
**Prerequisites**: Results view loaded

| Device | Viewport | Test | Result |
|--------|----------|------|--------|
| Desktop | 1920x1080 | Charts render, no scroll | ☐ |
| Tablet | 768x1024 | Charts stack in grid | ☐ |
| Mobile | 375x812 | Charts single column | ☐ |
| Landscape | 812x375 | Charts adapt width | ☐ |

### Manual Testing Checklist

- [ ] **Setup**
  - [ ] API server running
  - [ ] Database with test data
  - [ ] Browser console clear (no errors)
  - [ ] Network tab clean (no failed requests)

- [ ] **Visual Quality**
  - [ ] Colors match design
  - [ ] Fonts readable
  - [ ] Spacing consistent
  - [ ] Alignment proper
  - [ ] Icons visible

- [ ] **Functionality**
  - [ ] All buttons clickable
  - [ ] Forms validate input
  - [ ] Dropdowns work
  - [ ] Pagination works
  - [ ] Sorting works

- [ ] **Performance**
  - [ ] Page loads < 3 seconds
  - [ ] Charts render < 2 seconds
  - [ ] No lag on hover
  - [ ] Smooth scrolling
  - [ ] No memory leaks (check Dev Tools)

- [ ] **Accessibility**
  - [ ] Tab navigation works
  - [ ] Focus visible
  - [ ] Color contrast adequate
  - [ ] Keyboard shortcuts work
  - [ ] Screen reader compatible

- [ ] **Cross-Browser**
  - [ ] Chrome: ✓
  - [ ] Firefox: ✓
  - [ ] Safari: ✓
  - [ ] Edge: ✓

---

## Test Environment Setup

### Prerequisites
```bash
# Activate Python environment
conda activate od_project

# Install test dependencies (if needed)
pip install pytest pytest-cov pytest-asyncio
npm install @playwright/test
```

### Running All Tests
```bash
# Run unit and integration tests
pytest tests/unit/ -v --cov=api --cov=shared

# Run E2E tests
npx playwright test tests/e2e/test_batch_monitoring_hierarchy.spec.js

# Generate coverage report
pytest tests/unit/ --cov=api --cov=shared --cov-report=html
```

### Test Data Setup
Create test cases and batches in the database with:
- 3+ cases
- 2+ batches per case
- Completed batches with results
- Various output levels and seed counts

---

## Success Criteria for Phase 7

| Criterion | Status | Notes |
|-----------|--------|-------|
| T7.1: Unit tests written | ☐ | BatchResultAnalyzer tests, ≥90% coverage |
| T7.2: Integration tests written | ☐ | Batch service tests, full workflow coverage |
| T7.3: E2E tests written | ☐ | UI workflow tests including charts (T6.3) |
| T7.3: E2E tests passing | ☐ | All tests pass without flakiness |
| T7.4: UAT completed | ☐ | Manual tests documented and passing |
| Code coverage | ☐ | ≥85% for critical paths |
| Documentation | ☐ | Test cases documented |
| Sign-off | ☐ | Team approval on test results |

---

## Timeline Estimate

- **T7.1**: 3-4 hours (unit tests with fixtures and mocks)
- **T7.2**: 2-3 hours (extend existing integration tests)
- **T7.3**: 4-5 hours (comprehensive E2E scenarios including charts)
- **T7.4**: 2-3 hours (manual UAT execution)
- **Total**: 11-15 hours

---

## Known Issues and Mitigations

| Issue | Mitigation |
|-------|-----------|
| Canvas element testing is difficult | Use screenshots or Chart.js API access |
| Flaky E2E tests with timing | Use explicit waits, state detection |
| Test data dependencies | Use fixtures and factories for setup |
| Environment differences | Document setup requirements clearly |

---

## Rollout Plan

1. **Phase 7.1-7.2**: Write and run unit/integration tests
2. **Phase 7.3**: Write and run E2E tests, fix failures
3. **Phase 7.4**: Execute manual UAT, document results
4. **Sign-off**: Team review and approval
5. **Phase 8**: Documentation and cleanup

---

## Sign-Off Template

| Item | Completed | By | Date |
|------|-----------|----|----|
| T7.1 Unit tests complete | ☐ | | |
| T7.2 Integration tests complete | ☐ | | |
| T7.3 E2E tests complete | ☐ | | |
| T7.4 Manual UAT complete | ☐ | | |
| All tests passing | ☐ | | |
| Code coverage ≥85% | ☐ | | |
| Documentation complete | ☐ | | |
| Phase 7 approved | ☐ | | |

---

**Prepared by**: Claude Code
**Date**: 2025-11-04
**Related**: OpenSpec change `batch-monitoring-hierarchy-and-results-analysis`
**Next Phase**: Phase 8 - Documentation and Cleanup
