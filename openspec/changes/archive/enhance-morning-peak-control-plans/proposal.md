# enhance-morning-peak-control-plans Change Proposal

## Title
Create Comprehensive Morning Peak Control Plan Collection for Large-Scale Parallel Optimization

## Summary
Generate a comprehensive control plan collection (综合管控方案集合) containing 12-20 additional morning peak control plans with consistent naming conventions for G4202 and G5 highways. These plans will be directly displayable in the UI and support multi-selection for parallel simulation of up to 60 control strategies with 3-5 random seeds.

## Problem Statement

### Current Limitations
- Only 6 morning peak control plans exist currently (seen in plans_index.json)
- Limited spatial coverage: existing plans don't fully cover G4202-G5 highway network variations
- Limited temporal variations: few time interval combinations for morning peak (7:00-10:00)
- Insufficient plan diversity for large-scale parallel optimization testing (need 60+ concurrent simulations)

### Business Impact
- Cannot adequately test peak vehicle volume scenarios
- Limited optimization space for long-term traffic control planning
- Insufficient variety for machine learning-based strategy selection
- Unable to fully leverage parallel simulation capabilities (40-60 concurrent tasks)

## Proposed Solution

### Core Changes
1. **Create Comprehensive Control Plan Collection**
   - Generate 12-20 additional morning peak control plans as a unified collection
   - Use consistent naming convention with shared prefix for easy multi-selection
   - Enable direct display in UI plan selection interface
   - Support batch selection for parallel simulation
   - Focus on G4202 highway and connection points like G5

2. **Unified Naming Convention**
   - All plans use prefix: `plan_morning_peak_g4202_` for consistency
   - Encoding pattern: `plan_morning_peak_g4202_{strategy}_{location}_{severity}_{version}`
   - Chinese names use template: `G4202早高峰{策略类型}{区段}{严重程度}综合管控方案V{n}`
   - Examples:
     - `plan_morning_peak_g4202_vss_k0k20_moderate_v1`
     - `plan_morning_peak_g4202_vss_tec_k40k60_severe_v2`
     - `plan_morning_peak_g4202_full_composite_severe_v3`
   - Enables regex selection: `plan_morning_peak_g4202_*` for all morning plans

3. **Plan Generation Strategy**
   - **Spatial Variations**:
     - G4202 segments: K0-K20, K20-K40, K40-K60, K60-K85
     - G5 connection points: interchange areas
     - Different control point densities
   - **Temporal Variations**:
     - Early morning peak: 7:00-8:30
     - Core morning peak: 7:30-9:30
     - Extended morning peak: 7:00-10:00
     - Phased activation: 7:00-8:00, 8:00-9:00, 9:00-10:00
   - **Strategy Combinations**:
     - Single strategy plans: VSS-only, TEC-only, DHS-only
     - Dual combinations: VSS+TEC, VSS+DHS, TEC+DHS
     - Triple combination: VSS+TEC+DHS (full_composite)
     - Different parameter intensities (mild, moderate, severe)

4. **UI Display and Selection Integration**
   - Plans displayed as a cohesive collection in the UI
   - Support for checkbox multi-selection with "Select All Morning Peak" option
   - Visual grouping of plans by strategy type and severity
   - Preview of plan parameters on hover/selection
   - Batch operations enabled through consistent naming

5. **Integration with Existing Systems**
   - Leverage existing strategy templates in `control_data/strategies/`
   - Extend `plans_index.json` with new plan metadata and collection tags
   - Ensure compatibility with batch optimization system
   - Support control strategy ranking evaluation
   - Enable direct UI display through standardized metadata

### Technical Approach
1. Create parameterized plan generator that combines:
   - Highway segments from network data
   - Time interval templates
   - Strategy template references
2. Generate plans with systematic variations
3. Validate each plan's control.add.xml generation
4. Update plan index and metadata

## Success Criteria
- [ ] Generate 12-20 new morning peak control plans as a comprehensive collection
- [ ] All plans use consistent `plan_morning_peak_g4202_` prefix naming convention
- [ ] Plans are directly displayable in UI with multi-selection support
- [ ] All plans have valid control.add.xml files
- [ ] Plans cover diverse spatial locations on G4202 and G5
- [ ] Plans include varied time intervals within morning peak
- [ ] Plans demonstrate all strategy type combinations
- [ ] Plans successfully integrate with batch simulation system for parallel execution
- [ ] Plans can be evaluated by control strategy ranking system
- [ ] Collection supports regex-based batch selection in UI

## Risks and Mitigations

### Risk 1: Invalid Network References
- **Risk**: Generated plans may reference non-existent edges/junctions
- **Mitigation**: Validate all spatial references against network files

### Risk 2: Conflicting Control Strategies
- **Risk**: Multiple strategies on same road segment may conflict
- **Mitigation**: Implement conflict detection and resolution rules

### Risk 3: Performance Impact
- **Risk**: 60+ parallel simulations may overwhelm system resources
- **Mitigation**: Test incremental load increases, optimize resource allocation

## Dependencies
- Existing strategy templates in `control_data/strategies/`
- Network files defining G4202 and G5 highways
- Batch optimization system (already implemented)
- Control strategy ranking system (already implemented)

## Implementation Phases
1. **Phase 1**: Plan Design and Template Preparation (2 days)
2. **Phase 2**: Plan Generation Implementation (3 days)
3. **Phase 3**: Validation and Testing (2 days)
4. **Phase 4**: Integration with Batch System (1 day)
5. **Phase 5**: Documentation and Deployment (1 day)

Total estimated effort: 9 days