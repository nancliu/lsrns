# Add Toll Station Mapping Data

**Status**: Proposed
**Owner**: Event Scenario System
**Created**: 2025-11-10
**Target**: Phase 3.5 - Event Scenario Enhancement

## Summary

Add comprehensive toll station mapping data to enable precise event scenario configuration with toll station control. This change creates a structured CSV mapping file that links toll station IDs to SUMO network elements (edge_id, junction_id, TAZ) to support accurate TEC (Toll Entrance Control) strategy generation.

## Context

The event scenario system needs to map toll stations referenced in events (`managed_toll_stations` field) to specific SUMO network elements for control strategy generation. Currently:

- Events reference toll stations by ID (e.g., "250,255,256")
- Database contains toll station data in `dim.point_toll_84` and `dim.point_toll_square`
- TAZ file links some toll stations to edges via `tazSource`
- No unified mapping table exists for event processing

## Goals

1. **Create toll station mapping CSV** with complete edge_id and junction_id mappings
2. **Enable precise TEC strategy generation** from event toll station references
3. **Support all routes** (G5, G4202, G76, S81) not just G5
4. **Validate mappings** against network and TAZ definitions

## Non-Goals

- Modifying existing database schema
- Real-time toll station monitoring
- Changing existing TEC control templates
- Altering event data format

## Solution Overview

Generate a comprehensive toll station mapping CSV by:

1. Query database tables (`dim.point_toll_84`, `dim.point_toll_square`, `dim.taz_demonstration_mapping`)
2. Match toll station codes with TAZ definitions in `TAZ_6.add.xml`
3. Resolve edge_id and junction_id from `dim.sim_network_edges`
4. Create reference CSV with all mapping fields
5. Integrate with scenario generator for TEC strategy creation

### Mapping Data Structure

```csv
toll_station_id,station_name,square_code,route_code,section_code,longitude,latitude,taz_id,entrance_exit,edge_id,junction_id
250,小溪坝站,SQ001,G5,K1234,104.123,30.456,TAZ_250,entrance,-1232,J_250
255,厚坝站,SQ002,G5,K1245,104.234,30.567,TAZ_255,exit,E15,J_255
```

## User Experience

**Before**: Manual lookup of toll stations, error-prone edge mapping
**After**: Automated toll station resolution from event data

Example workflow:
```python
# Event contains: managed_toll_stations = "250,255,256"
toll_mapping = load_toll_station_mapping()
edges = resolve_toll_edges(event.managed_toll_stations, toll_mapping)
# Returns: ['-1232', 'E15', '-15818'] for TEC strategy
```

## Dependencies

- Database access to `dim` schema
- TAZ file (`TAZ_6.add.xml`) parsing
- Network edge data (`sim_network_edges`)
- Existing TEC control templates

## Alternatives Considered

1. **Direct database queries**: Runtime overhead, requires DB connection
2. **Hardcoded mappings**: Maintenance burden, not scalable
3. **TAZ-only approach**: Missing non-TAZ toll stations

## Scope

**In Scope:**
- Generate toll station mapping CSV from database
- Match station_code_js suffix to event toll IDs
- Include all toll stations from dim.point_toll_84
- Validate against TAZ and network files
- Create reference documentation

**Out of Scope:**
- Modify event data structure
- Change TEC control logic
- Add real-time toll monitoring
- Create new database tables

## Success Criteria

1. **Complete mapping file** with 37+ toll stations from database
2. **100% G5 coverage** matching existing TEC strategies
3. **Edge validation** against network file
4. **TAZ correlation** for entrance toll stations
5. **Integration test** with scenario generator

## Implementation Plan

1. **Data extraction** (Day 1)
   - Query database tables
   - Export toll station data

2. **Mapping generation** (Day 2)
   - Match station codes to event IDs
   - Resolve edge_id from coordinates/TAZ
   - Validate against network

3. **Integration** (Day 3)
   - Update scenario generator
   - Add mapping loader
   - Test with real events

4. **Validation** (Day 4)
   - Verify G5 mappings
   - Test other routes
   - Documentation

## Rollout Strategy

1. Generate mapping for G5 (already validated)
2. Extend to G4202, G76, S81
3. Deploy to event scenario system
4. Monitor TEC strategy generation

## Open Questions

1. How to handle toll stations without TAZ entries?
2. Should exit toll stations be included for control?
3. Mapping priority when multiple edges match coordinates?

## References

- `docs/control_strategies/TAZ边缘映射_TEC策略配置指南.md`
- `docs/data_in_db/示范路网基础设施静态数据说明.md`
- Database tables: `dim.point_toll_84`, `dim.point_toll_square`
- TAZ file: `templates/taz_files/TAZ_6.add.xml`