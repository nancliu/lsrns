# Implementation Tasks

## Phase 1: Data Extraction & Analysis (Day 1)

### 1.1 Extract toll station data from database
- [ ] Query `dim.point_toll_84` for toll station locations (WGS84)
- [ ] Query `dim.point_toll_square` for entrance/exit plazas
- [ ] Query `dim.taz_demonstration_mapping` for TAZ associations
- [ ] Export to intermediate CSV for processing

### 1.2 Analyze TAZ file structure
- [ ] Parse `templates/taz_files/TAZ_6.add.xml`
- [ ] Extract tazSource edge mappings for toll stations
- [ ] Create TAZ-to-edge lookup table
- [ ] Document unmapped TAZ entries

### 1.3 Review existing TEC strategies
- [ ] Analyze `strategy_real_tec_g5_*.json` files
- [ ] Extract verified toll-edge mappings
- [ ] Document G5 validation baseline

## Phase 2: Mapping Generation (Day 2)

### 2.1 Create toll station ID resolver
- [ ] Match `station_code_js` last 3 digits to event toll IDs
- [ ] Handle ID format variations (leading zeros, etc.)
- [ ] Create ID normalization function
- [ ] Test with `all_extracted_events.csv` toll references

### 2.2 Generate edge_id mappings
- [ ] Query `dim.sim_network_edges` with coordinates
- [ ] Match toll locations to nearest entrance edges
- [ ] Validate edge types (entrance vs normal)
- [ ] Cross-reference with TAZ edge definitions

### 2.3 Create mapping CSV
- [ ] Generate `events/reference/toll_station_mapping.csv`
- [ ] Include all required fields (see proposal structure)
- [ ] Add validation checksums/metadata
- [ ] Create backup of generated file

## Phase 3: Integration (Day 3)

### 3.1 Update scenario generator
- [ ] Modify `shared/control_tools/scenario_generator.py`
- [ ] Add toll mapping loader function
- [ ] Integrate with TEC strategy generation
- [ ] Handle missing/invalid mappings gracefully

### 3.2 Create mapping utilities
- [ ] Add `shared/utilities/toll_mapping_utils.py`
- [ ] Implement `load_toll_station_mapping()`
- [ ] Implement `resolve_toll_edges()`
- [ ] Add caching for performance

### 3.3 Update event injector
- [ ] Modify `shared/control_tools/event_injector.py`
- [ ] Use toll mappings for TEC events
- [ ] Add validation for toll station IDs
- [ ] Log mapping resolution details

## Phase 4: Validation & Testing (Day 4)

### 4.1 Validate G5 mappings
- [ ] Compare with verified edges (双流南站, 白家站, 新都站)
- [ ] Test TEC strategy generation for G5 events
- [ ] Verify edge IDs match network file
- [ ] Check lane counts and directions

### 4.2 Test other routes
- [ ] Generate mappings for G4202 toll stations
- [ ] Test G76 and S81 if data available
- [ ] Document coverage gaps
- [ ] Create route-specific validation reports

### 4.3 Integration testing
- [ ] Test with 10 sample events containing toll stations
- [ ] Verify scenario generation with toll controls
- [ ] Run SUMO simulation with generated configs
- [ ] Check additional file generation

### 4.4 Documentation
- [ ] Update `docs/control_strategies/` with mapping guide
- [ ] Add usage examples to scenario generator docs
- [ ] Document CSV format and fields
- [ ] Create troubleshooting guide

## Phase 5: Deployment (Day 5)

### 5.1 Data deployment
- [ ] Deploy mapping CSV to `events/reference/`
- [ ] Create version control entry
- [ ] Add to `.gitignore` if regeneratable
- [ ] Document generation process

### 5.2 Code deployment
- [ ] Merge scenario generator updates
- [ ] Deploy utility functions
- [ ] Update API if needed
- [ ] Run smoke tests

### 5.3 Monitoring
- [ ] Log toll mapping usage statistics
- [ ] Track resolution success rate
- [ ] Monitor TEC strategy generation
- [ ] Collect feedback from event processing

## Dependencies

- **Blocking**: Database access credentials
- **Blocking**: TAZ file read permissions
- **Parallel**: Can work on utilities while data extraction runs
- **Parallel**: Documentation can be written alongside implementation

## Validation Checklist

- [ ] All 37 toll stations from database mapped
- [ ] G5 toll stations match verified edges
- [ ] No duplicate toll_station_id entries
- [ ] All edge_id values exist in network
- [ ] TAZ associations validated where present
- [ ] Coordinates within expected bounds
- [ ] Route codes match database values
- [ ] CSV loads without errors
- [ ] Integration tests pass

## Rollback Plan

1. Keep original scenario generator code
2. Feature flag for toll mapping usage
3. Fallback to manual edge specification
4. Preserve existing TEC strategies

## Notes

- Prioritize G5 coverage (most events, validated edges)
- Handle missing data gracefully (log warnings, don't fail)
- Consider future extensibility for real-time updates
- Maintain backward compatibility with existing events