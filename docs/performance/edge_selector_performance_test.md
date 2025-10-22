# Edge Selector Performance Test Guide

## Overview

This guide helps verify the performance improvements made on 2025-10-22 to fix the 5+ second delay when selecting routes in the control strategy edge selector.

## Performance Targets

| Operation | Before Optimization | After Optimization | Target |
|-----------|--------------------|--------------------|--------|
| Route selection → Section load | 5-10 seconds | <500ms | <1 second |
| Frontend processing | 2-4 seconds | <100ms | <200ms |
| Database query | 3-6 seconds | <400ms | <500ms |

## Test Procedure

### 1. Browser Performance Test (User-Facing)

**Steps**:
1. Open the control strategy page: `http://localhost:8000/control/templates.html`
2. Navigate to "Step 2: Select Edges" (strategy creation wizard)
3. Open browser DevTools → Network tab
4. Select a route code (e.g., `G4202`) from the dropdown
5. Measure time until section dropdown populates

**Expected Results**:
- ✅ Section dropdown populates in <500ms
- ✅ No visible lag or "加载中..." message lasting >1 second
- ✅ Only ONE API call to `/api/v1/control/edges/sections?route_code=G4202`
- ❌ NO call to `/api/v1/control/edges/query` (this was removed)

**Before vs After**:
```
BEFORE (slow):
  User clicks route → 2-4s delay → API call 1 (sections) → API call 2 (query) → 6-10s total

AFTER (fast):
  User clicks route → <100ms → API call (sections only) → <500ms total
```

### 2. API Performance Test (Backend)

**Test Section Query**:
```bash
# Time the section query API
curl -w "@curl-format.txt" "http://localhost:8000/api/v1/control/edges/sections?route_code=G4202"

# curl-format.txt content:
# time_total: %{time_total}s\n
```

**Expected**: Response time <500ms

**Verify in API logs**:
```powershell
# Check API server logs for timing information
# Look for lines like:
# [INFO] GET /api/v1/control/edges/sections - Fetching sections for route G4202
# [INFO] Successfully returned X sections (duration: XXXms)
```

### 3. Database Performance Test (Database Layer)

**Run EXPLAIN ANALYZE**:
```sql
-- Connect to database
psql -h 10.149.235.123 -U your_username -d sdzg

-- Test the exact query used by get_available_section_codes()
EXPLAIN ANALYZE
SELECT
    section_code,
    route_code,
    COUNT(*) as edge_count,
    MIN(start_stake) as min_stake,
    MAX(end_stake) as max_stake
FROM dim.sim_network_edges
WHERE section_code IS NOT NULL
  AND route_code = 'G4202'
GROUP BY section_code, route_code
ORDER BY route_code, section_code;
```

**Expected Output**:
```
Planning Time: <5ms
Execution Time: <400ms

Key indicators:
✅ "Index Scan using idx_sim_network_edges_route_section" (not Seq Scan)
✅ Rows: Should match actual section count (e.g., 50-100)
✅ Cost: Should be low (e.g., <1000)
```

**Before (slow - full table scan)**:
```
Seq Scan on sim_network_edges  (cost=0.00..15234.56 rows=10000 width=...)
Planning Time: 0.234 ms
Execution Time: 5234.567 ms
```

**After (fast - index scan)**:
```
Index Scan using idx_sim_network_edges_route_section  (cost=0.29..234.56 rows=50 width=...)
Planning Time: 0.123 ms
Execution Time: 123.456 ms
```

### 4. Verify Indexes Created

```sql
-- Check all indexes on sim_network_edges
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'sim_network_edges' AND schemaname = 'dim'
ORDER BY indexname;
```

**Expected Indexes** (should see all of these):
- `idx_sim_network_edges_route_code`
- `idx_sim_network_edges_section_code`
- `idx_sim_network_edges_route_section` ← **Most important for performance**
- `idx_sim_network_edges_demonstration_id`

```sql
-- Check indexes on JOIN tables (optional optimization)
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('multiscale_node_units', 'point_gantry')
  AND schemaname = 'dim'
ORDER BY tablename, indexname;
```

**Expected**:
- `idx_multiscale_node_units_junction_id`
- `idx_point_gantry_route_stake`

### 5. Verify Frontend Optimization

**Check that `updateDirectionOptions()` no longer calls API**:

1. Open `frontend/control/js/edge_selector_embedded.js`
2. Find `updateDirectionOptions()` function (around line 125)
3. Verify it does NOT contain `fetch()` call
4. Verify it's NOT `async` anymore

**Expected Code**:
```javascript
updateDirectionOptions(selectedRoutes) {
    const directionSelect = document.getElementById('route-direction');
    if (!directionSelect) return;

    const currentValue = directionSelect.value;

    // Always show all direction options (no database query)
    directionSelect.innerHTML = `
        <option value="">全部</option>
        <option value="upstream">上行</option>
        ...
    `;
```

**Should NOT contain**:
```javascript
// ❌ This code should be REMOVED:
const response = await fetch(`/api/v1/control/edges/query?route_codes=${routeCode}&limit=50`);
```

## Regression Testing

**Test these scenarios to ensure nothing broke**:

1. ✅ Section dropdown still shows correct sections for selected route
2. ✅ Direction dropdown still works (even though all options always visible)
3. ✅ Can still query edges with direction filter
4. ✅ Edge visualization still loads correctly
5. ✅ Strategy creation still works end-to-end

## Performance Benchmarks by Route

Test with different routes to ensure consistent performance:

| Route Code | Expected Sections | Target Time |
|------------|------------------|-------------|
| G4202 | ~50-100 | <500ms |
| SA2 | ~30-50 | <400ms |
| G4201 | ~40-80 | <450ms |

## Troubleshooting

### If performance is still slow:

1. **Check indexes exist**:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'sim_network_edges';
   ```

2. **Check if indexes are being used**:
   ```sql
   EXPLAIN (ANALYZE, BUFFERS) SELECT ... -- your query
   ```
   Look for "Index Scan" not "Seq Scan"

3. **Check database statistics are up to date**:
   ```sql
   ANALYZE dim.sim_network_edges;
   ```

4. **Check for lock contention**:
   ```sql
   SELECT * FROM pg_stat_activity WHERE datname = 'sdzg';
   ```

5. **Verify frontend optimization applied**:
   - Clear browser cache (Ctrl+Shift+R)
   - Check Network tab - should only see ONE API call per route selection
   - No call to `/api/v1/control/edges/query`

## Success Criteria

All of these must pass:

- ✅ Route selection → section load: <500ms
- ✅ No visible UI lag when selecting routes
- ✅ Only ONE API call per route selection
- ✅ Database query uses index scan (not seq scan)
- ✅ All 4+ indexes created successfully
- ✅ No regression in functionality (sections still correct)

## Rollback Plan

If optimizations cause issues:

### Rollback Frontend Changes:
```bash
git checkout HEAD~1 -- frontend/control/js/edge_selector_embedded.js
```

### Rollback Database Indexes:
```sql
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_code;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_section_code;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_route_section;
DROP INDEX IF EXISTS dim.idx_sim_network_edges_demonstration_id;
DROP INDEX IF EXISTS dim.idx_multiscale_node_units_junction_id;
DROP INDEX IF EXISTS dim.idx_point_gantry_route_stake;
```

## Date

**Optimization Applied**: 2025-10-22
**Next Review**: After production deployment
