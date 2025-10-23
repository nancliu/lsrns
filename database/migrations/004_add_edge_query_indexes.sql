-- Migration: Add Indexes for Edge Query Performance
-- Created: 2025-10-22
-- Purpose: Optimize /api/v1/control/edges/sections query performance (reduce 5s+ to <500ms)
-- Related Issue: Section dropdown slow when selecting route codes
--
-- Expected Performance Improvement:
-- - Before: 5-10 seconds (full table scan)
-- - After: <500ms (index seek)

-- ============================================================================
-- 1. Add index on route_code (most selective filter)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_route_code
ON dim.sim_network_edges(route_code);

-- ============================================================================
-- 2. Add index on section_code (used in WHERE and GROUP BY)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_section_code
ON dim.sim_network_edges(section_code);

-- ============================================================================
-- 3. Add composite index for common query pattern (route_code + section_code)
-- ============================================================================
-- This index covers the exact query pattern used by get_available_section_codes()
-- which groups by (section_code, route_code) with WHERE route_code = X
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_route_section
ON dim.sim_network_edges(route_code, section_code);

-- ============================================================================
-- 4. Add index on demonstration_id (used in some queries)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_sim_network_edges_demonstration_id
ON dim.sim_network_edges(demonstration_id)
WHERE demonstration_id IS NOT NULL;  -- Partial index for non-NULL values only

-- ============================================================================
-- 5. Add indexes on related tables for JOIN optimization (optional)
-- ============================================================================
-- These indexes optimize the complex query_edges_with_filters() JOIN queries
-- Used by: GET /api/v1/control/edges/query (if needed in the future)

-- Index on multiscale_node_units.junction_id for faster JOIN
CREATE INDEX IF NOT EXISTS idx_multiscale_node_units_junction_id
ON dim.multiscale_node_units(junction_id);

-- Index on point_gantry for route_code filtering and stake range queries
CREATE INDEX IF NOT EXISTS idx_point_gantry_route_stake
ON dim.point_gantry(route_code, gantry_stake);

-- ============================================================================
-- 6. Analyze tables to update statistics (helps query planner)
-- ============================================================================
ANALYZE dim.sim_network_edges;
ANALYZE dim.multiscale_node_units;
ANALYZE dim.point_gantry;

-- ============================================================================
-- Verification Queries (run after migration)
-- ============================================================================

-- Check if indexes were created:
-- SELECT schemaname, tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'sim_network_edges' AND schemaname = 'dim'
-- ORDER BY indexname;

-- Test query performance (should use idx_sim_network_edges_route_section):
-- EXPLAIN ANALYZE
-- SELECT
--     section_code,
--     route_code,
--     COUNT(*) as edge_count,
--     MIN(start_stake) as min_stake,
--     MAX(end_stake) as max_stake
-- FROM dim.sim_network_edges
-- WHERE section_code IS NOT NULL
--   AND route_code = 'G4202'
-- GROUP BY section_code, route_code
-- ORDER BY route_code, section_code;

-- Expected EXPLAIN output should show:
-- -> Index Scan using idx_sim_network_edges_route_section
-- Execution time: < 500ms (down from 5000ms+)
