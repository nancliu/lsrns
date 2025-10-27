# Plan Management E2E Tests

## Overview

Comprehensive end-to-end tests for the Plan Management frontend using Playwright.

## Test File

`test_plan_management.spec.js` - Complete workflow testing for plan CRUD operations

## Test Coverage

### ✅ Page Load & Navigation (4 tests)
- `should load plans page successfully` - Page loads with all elements
- `should navigate between sidebar items` - Sidebar navigation works
- `should return to main system` - Back button navigation
- `should display baseline plan` - Baseline plan is visible

### ✅ Filtering & Search (3 tests)
- `should filter plans using search` - Search box filters plans
- `should toggle baseline plan visibility` - Baseline checkbox works
- `should handle empty state when no plans exist` - Empty state display

### ✅ Plan Creation (3 tests)
- `should open create plan modal` - Modal opens with form
- `should close create plan modal` - Modal closes correctly
- `should create a new plan` - Complete creation workflow

### ✅ Plan Viewing (2 tests)
- `should view plan details` - Detail modal displays correctly
- `should close plan detail modal` - Detail modal closes

### ✅ Plan Editing (1 test)
- `should edit and update a non-baseline plan` - Edit workflow

### ✅ Plan Deletion (2 tests)
- `should delete a non-baseline plan` - Deletion workflow
- `should not allow deleting baseline plan` - Baseline protection

### ✅ Form Validation (1 test)
- `should handle form validation` - Required field validation

**Total: 16 E2E test cases**

## Prerequisites

1. **Server Running**: API server must be running on localhost:8000
   ```bash
   conda activate od_project
   .\start_api.ps1
   ```

2. **Playwright Installed**: Ensure Playwright is set up
   ```bash
   npm install
   npx playwright install
   ```

3. **Test Data**: Baseline plan should exist (created automatically on server startup)

## Running Tests

### Run All Plan E2E Tests

```bash
# Headless mode (CI/CD)
npx playwright test tests/e2e/test_plan_management.spec.js

# Headed mode (visible browser)
npx playwright test tests/e2e/test_plan_management.spec.js --headed

# Debug mode
npx playwright test tests/e2e/test_plan_management.spec.js --debug

# Specific browser
npx playwright test tests/e2e/test_plan_management.spec.js --project=chromium
```

### Run Specific Test

```bash
npx playwright test tests/e2e/test_plan_management.spec.js -g "should create a new plan"
```

### Run with UI Mode (Interactive)

```bash
npx playwright test tests/e2e/test_plan_management.spec.js --ui
```

### Generate Test Report

```bash
npx playwright test tests/e2e/test_plan_management.spec.js --reporter=html
npx playwright show-report
```

## Test Scenarios

### Scenario 1: Basic Plan Management
1. Load page
2. View baseline plan
3. Create new plan
4. View plan details
5. Edit plan
6. Delete plan

### Scenario 2: Filtering & Search
1. Search by plan name
2. Filter by tags
3. Toggle baseline visibility
4. Verify filtered results

### Scenario 3: Baseline Plan Protection
1. Verify baseline plan exists
2. Verify baseline cannot be deleted
3. Verify baseline has no edit button

### Scenario 4: Form Validation
1. Open create modal
2. Submit without required fields
3. Verify validation errors
4. Fill required fields
5. Submit successfully

## Test Data Cleanup

Tests create plans with names starting with "E2E" for identification. To clean up test data:

```bash
# Via API (if cleanup endpoint exists)
curl -X DELETE http://localhost:8000/api/v1/control/plans/E2E*

# Or manually through the UI
# Navigate to plans page and delete plans with "E2E" in the name
```

## Common Issues & Solutions

### Issue: Tests fail with "Timeout"
**Solution**: Increase timeout in playwright.config.js or ensure server is running:
```javascript
timeout: 30000, // 30 seconds
```

### Issue: "Element not visible"
**Solution**: Add explicit wait before interaction:
```javascript
await page.waitForSelector('.plan-card', { timeout: 5000 });
```

### Issue: "Navigation timeout"
**Solution**: Check server is running and accessible:
```bash
curl http://localhost:8000/control/plans.html
```

### Issue: Dialog not handled
**Solution**: Tests handle confirmation dialogs automatically:
```javascript
page.on('dialog', dialog => dialog.accept());
```

## Debugging Tips

1. **Use Screenshots**:
   ```javascript
   await page.screenshot({ path: 'debug.png' });
   ```

2. **Use --debug Flag**:
   ```bash
   npx playwright test --debug
   ```

3. **Check Browser Console**:
   ```javascript
   page.on('console', msg => console.log(msg.text()));
   ```

4. **Slow Motion**:
   ```bash
   npx playwright test --headed --slow-mo=1000
   ```

## Test Configuration

Default Playwright configuration (from `playwright.config.js`):

```javascript
{
  testDir: './tests/e2e',
  timeout: 30000,
  expect: { timeout: 5000 },
  use: {
    baseURL: 'http://localhost:8000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
}
```

## CI/CD Integration

For automated testing in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run E2E Tests
  run: |
    npm install
    npx playwright install --with-deps
    python api/main.py & # Start server
    sleep 10 # Wait for server
    npx playwright test tests/e2e/test_plan_management.spec.js
```

## Test Maintenance

When updating the plan management feature:

1. **Add Tests**: Create new tests for new features
2. **Update Selectors**: If UI changes, update CSS selectors
3. **Update Assertions**: Ensure assertions match new behavior
4. **Run Full Suite**: Verify all tests still pass

## Expected Results

All 16 tests should pass when:
- Server is running on localhost:8000
- Baseline plan exists
- No conflicting test data exists
- Network is stable

## Screenshots & Videos

Playwright automatically captures:
- Screenshots on test failure
- Videos of failed tests (if configured)

Location: `test-results/` directory

## Performance Benchmarks

Expected test execution times:
- Full suite (16 tests): ~60-90 seconds
- Individual test: ~3-5 seconds
- Parallel execution: ~30-45 seconds (3 workers)

## Next Steps

After E2E tests pass:
1. Integrate into CI/CD pipeline
2. Add more edge case tests
3. Add visual regression tests
4. Add performance tests
5. Extend to cover Phase 2 features (batch optimization)
