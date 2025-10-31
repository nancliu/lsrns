# E2E Test Data Setup Guide
## enhance-strategy-parameter-configuration

**Purpose**: Guide for preparing test database data to enable full E2E test execution

---

## Quick Reference - Production Edge IDs

**These edges already exist in your production database:**

| Purpose | Edge IDs | Usage |
|---------|----------|-------|
| **VSS/DHS Tests** | `-2680`, `-690`, `-5016`, `-10000` | Select 1 or more for route segment testing |
| **TEC Tests** | `-13042` | Entrance edge for TEC strategy testing |

**No data insertion needed** - Just verify these edges exist in `dim.sim_network_edges` table.

---

## Overview

The E2E tests for strategy creation workflow require specific database records to execute successfully. This document provides verification queries for existing production data.

---

## Manual Test Workflow (Reference)

Based on actual manual testing procedure:

1. **Step 1**: Select strategy template → Auto-transition to Step 2
2. **Step 2**:
   - Select route code: G4202
   - Wait for section codes to load (auto-populated based on route)
   - Set filters based on template requirements:
     - For entrances: Select entrance type
     - For DHS: Set minimum lanes ≥ 4
     - Set stake range: 33-44 km
   - Click "查询路段" button
   - Wait for query results to display
   - Select 1 or more edges from results
   - "进入配置参数" buttons appear (one above, one below results table)
3. **Step 3**: Click "进入配置参数" → Configure parameters and save

---

## Required Test Data

### 1. Edge Data for VSS/DHS Tests

**Table**: `dim.sim_network_edges`

**Requirements**:
- Route: G4202 (成都绕城高速)
- Stake range: 33-44 km
- Minimum 5 continuous edges
- Lane count: ≥ 4 (for DHS validation)
- Complete metadata

#### SQL Script - Actual Edge Data (From Production Database)

**Note**: These are actual edge IDs from your production database. Use these for E2E testing.

```sql
-- Verify these edges exist in your database
-- If they exist, E2E tests will pass immediately without additional setup

-- Sample edges for VSS/DHS tests (use 1 or more)
SELECT
    edge_id,
    route_code,
    section_code,
    CONCAT('K', start_stake::int, '+', LPAD(((start_stake % 1) * 1000)::int::text, 3, '0')) AS start_stake_formatted,
    CONCAT('K', end_stake::int, '+', LPAD(((end_stake % 1) * 1000)::int::text, 3, '0')) AS end_stake_formatted,
    length_m,
    num_lanes,
    direction,
    node_type
FROM dim.sim_network_edges
WHERE edge_id IN ('-2680', '-690', '-5016', '-10000')
ORDER BY start_stake;

-- Sample entrance edge for TEC tests
SELECT
    edge_id,
    route_code,
    section_code,
    start_stake,
    end_stake,
    length_m,
    num_lanes,
    direction,
    node_type
FROM dim.sim_network_edges
WHERE edge_id = '-13042';
```

**Verification Query**:
```sql
-- Verify edge data inserted correctly
SELECT
    edge_id,
    route_code,
    section_code,
    CONCAT('K', start_stake::int, '+', LPAD(((start_stake % 1) * 1000)::int::text, 3, '0')) AS start_stake_formatted,
    CONCAT('K', end_stake::int, '+', LPAD(((end_stake % 1) * 1000)::int::text, 3, '0')) AS end_stake_formatted,
    length_m,
    num_lanes,
    direction
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND start_stake >= 33
  AND end_stake <= 44
ORDER BY start_stake;
```

---

### 2. Entrance Edge Data for TEC Tests

**Requirements**:
- At least 1-2 entrance edges
- Associated with toll stations
- Proper edge type classification

#### Actual TEC Entrance Edge

**Production Edge ID**: `-13042`

This entrance edge is already in your database and ready for TEC strategy testing.

```sql
-- Verify the entrance edge exists and check its properties
SELECT
    edge_id,
    route_code,
    section_code,
    start_stake,
    end_stake,
    length_m,
    num_lanes,
    direction,
    node_type,
    demonstration_id
FROM dim.sim_network_edges
WHERE edge_id = '-13042';
```

**Expected Result**:
- Should return 1 row with entrance edge properties
- If no results: contact database admin to verify edge_id -13042 exists
- `node_type` should indicate this is an entrance (e.g., 'toll_entrance', 'entrance', or similar)

**Alternative Query** (if specific entrance unknown):
```sql
-- Find all available entrance edges on G4202 route
SELECT
    edge_id,
    route_code,
    section_code,
    start_stake,
    end_stake,
    num_lanes,
    direction,
    node_type
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND (node_type ILIKE '%entrance%' OR direction ILIKE '%entrance%')
ORDER BY start_stake
LIMIT 5;
```

---

## Database Schema Verification

### Check Table Structure

```sql
-- Verify dim.sim_network_edges table exists and has correct columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'dim'
  AND table_name = 'sim_network_edges'
ORDER BY ordinal_position;
```

### Expected Columns

| Column Name | Data Type | Required |
|-------------|-----------|----------|
| edge_id | varchar/text | Yes |
| route_code | varchar | Yes |
| section_code | varchar | Yes |
| start_stake | numeric/float | Yes |
| end_stake | numeric/float | Yes |
| length_m | numeric/float | Yes |
| num_lanes | integer | Yes |
| direction | varchar | Yes |
| node_type | varchar | Optional |
| demonstration_id | varchar | Optional |

---

## Test Execution with Data

### Step 1: Insert Test Data

```bash
# Using psql command line
psql -h 10.149.235.123 -U ln -d sdzg -f test_data_insert.sql

# Or using Python
python scripts/insert_test_data.py
```

### Step 2: Run E2E Tests

```bash
# Activate environment
conda activate od_project

# Run specific test suite
npx playwright test tests/e2e/test_strategy_creation_workflow.spec.js --reporter=list

# Run in headed mode (visible browser) for debugging
npx playwright test tests/e2e/test_strategy_creation_workflow.spec.js --headed
```

### Step 3: Verify Results

Expected output with proper test data:
```
✅ VSS策略：完整工作流验证（步骤1→2→3→保存） - PASS
✅ DHS策略：完整工作流验证（包含连续性验证） - PASS
⏭️ TEC策略：完整工作流验证（流量参数） - SKIP (if no entrance data)
✅ 参数验证：数值范围验证 - PASS
✅ 用户界面：按钮功能验证（建议名称、重新生成描述） - PASS
```

---

## Troubleshooting

### Issue 1: No Query Results

**Symptom**: Test skips with "⚠️  未找到可选路段"

**Causes**:
1. No data in `dim.sim_network_edges` for G4202 route
2. Stake range 33-44 km doesn't match any records
3. Minimum lanes filter (for DHS) excludes all edges

**Solutions**:
- Run verification query to check data exists
- Adjust stake range in test script or insert more data
- Ensure at least 5 edges have `num_lanes >= 4` for DHS

### Issue 2: Section Codes Not Loading

**Symptom**: Test fails at section code selection

**Cause**: Section codes are auto-populated based on route, may require additional tables

**Solution**: Verify route-to-section mapping exists in database

### Issue 3: Query Timeout

**Symptom**: Test timeout waiting for query results

**Causes**:
1. Database query is slow (missing indexes)
2. Network latency to database
3. Test timeout too short

**Solutions**:
- Check database indexes on `route_code`, `start_stake`, `end_stake`, `num_lanes`
- Increase test timeout in playwright config
- Run query manually to measure performance

---

## Performance Optimization

### Add Indexes for Query Performance

```sql
-- Indexes for edge query performance (if not already exist)
CREATE INDEX IF NOT EXISTS idx_edges_route_stake
ON dim.sim_network_edges(route_code, start_stake, end_stake);

CREATE INDEX IF NOT EXISTS idx_edges_route_lanes
ON dim.sim_network_edges(route_code, num_lanes);

CREATE INDEX IF NOT EXISTS idx_edges_node_type
ON dim.sim_network_edges(node_type)
WHERE node_type IS NOT NULL;
```

---

## Test Data Cleanup

### Remove Test Data After Testing

```sql
-- Clean up test edge data
DELETE FROM dim.sim_network_edges
WHERE edge_id IN (
    '-8700', '-8701', '-8702', '-8703', '-8704', '-8705',
    '-8706', '-8707', '-8708', '-8709', '-8710', '-8711',
    '-9001', '-9002'
);
```

**Warning**: Only run cleanup on test/development databases, never on production!

---

## Continuous Integration Setup

### CI/CD Pipeline Steps

1. **Before Tests**:
   ```bash
   # Run database migration
   psql -f migrations/test_data_setup.sql

   # Wait for data propagation
   sleep 2
   ```

2. **Run Tests**:
   ```bash
   npx playwright test tests/e2e/test_strategy_creation_workflow.spec.js
   ```

3. **After Tests**:
   ```bash
   # Cleanup test data
   psql -f migrations/test_data_cleanup.sql
   ```

---

## Summary

### Minimum Required Data for Full Test Pass

| Test Scenario | Required Data | Count |
|---------------|---------------|-------|
| VSS Workflow | G4202 edges, stake 33-44km | 5-10 edges |
| DHS Workflow | G4202 edges, stake 33-44km, lanes≥4 | 5-10 edges |
| TEC Workflow | Entrance edges | 1-2 entrances |
| Parameter Validation | Same as VSS | 2-5 edges |
| UI Functionality | Same as VSS | 2-5 edges |

### Quick Setup Command

```sql
-- All-in-one test data insert
BEGIN;

-- VSS/DHS edges
INSERT INTO dim.sim_network_edges (edge_id, route_code, section_code, start_stake, end_stake, length_m, num_lanes, direction, node_type)
SELECT * FROM (VALUES
    ('-8700', 'G4202', '001', 33.0, 34.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8701', 'G4202', '001', 34.0, 35.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8702', 'G4202', '001', 35.0, 36.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8703', 'G4202', '001', 36.0, 37.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8704', 'G4202', '001', 37.0, 38.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8705', 'G4202', '001', 38.0, 39.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8706', 'G4202', '001', 39.0, 40.0, 1000, 5, 'counterclockwise', 'normal'),
    ('-8707', 'G4202', '001', 40.0, 41.0, 1000, 5, 'counterclockwise', 'normal'),
    ('-8708', 'G4202', '001', 41.0, 42.0, 1000, 4, 'counterclockwise', 'normal'),
    ('-8709', 'G4202', '001', 42.0, 43.0, 1000, 4, 'counterclockwise', 'normal'),
    -- TEC entrance
    ('-9001', 'G4202', '002', 10.0, 10.2, 200, 3, 'entrance', 'toll_entrance')
) AS t(edge_id, route_code, section_code, start_stake, end_stake, length_m, num_lanes, direction, node_type)
ON CONFLICT (edge_id) DO NOTHING;

COMMIT;
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
**Status**: Ready for Use
