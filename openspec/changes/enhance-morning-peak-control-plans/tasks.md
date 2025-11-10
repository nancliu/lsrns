# enhance-morning-peak-control-plans Tasks

## Phase 1: Network Analysis and Segment Definition (2 days)

- [x] **Task 1.1**: Extract G4202 highway network topology
  - Load network files and identify all G4202 edges
  - Map edges to kilometer markers (K0-K85)
  - Document segment boundaries and characteristics
  - Output: `g4202_segments.json`

- [x] **Task 1.2**: Extract G5 interchange network data
  - Identify G5-G4202 interchange locations
  - Map interchange edges and ramps
  - Define 2km upstream/downstream zones
  - Output: `g5_interchange_zones.json`

- [x] **Task 1.3**: Validate network references
  - Cross-check edges against SUMO network file
  - Verify junction IDs and lane counts
  - Create validated segment database
  - Output: `validated_network_segments.json`

- [x] **Task 1.4**: Analyze traffic flow patterns
  - Extract morning peak flow data from historical records between 2025/09/01 and 2025/09/07
  - Identify bottleneck locations
  - Map high-flow segments for strategy placement
  - Output: `morning_peak_flow_analysis.json`

## Phase 2: Strategy Template Preparation (2 days)

- [x] **Task 2.1**: Create VSS parameter templates
  - Define mild (10-20% reduction) parameters
  - Define moderate (20-30% reduction) parameters
  - Define severe (30-50% reduction) parameters
  - Output: `vss_severity_templates.json`

- [x] **Task 2.2**: Create TEC parameter templates
  - Define flow control levels (10-60% reduction)
  - Set minimum spacing rules (2km)
  - Configure ramp metering parameters
  - Output: `tec_severity_templates.json`

- [x] **Task 2.3**: Create DHS parameter templates
  - Define shoulder opening schedules
  - Set vehicle type permissions
  - Configure lane change rules
  - Output: `dhs_severity_templates.json`

- [x] **Task 2.4**: Define temporal interval templates
  - Create 5 time window patterns (pre-peak to post-peak)
  - Define phased activation sequences
  - Set transition rules between phases
  - Output: `temporal_interval_templates.json`

## Phase 3: Plan Generation Implementation (3 days)

- [x] **Task 3.1**: Implement plan generator core
  - Create `PlanGenerator` class in `shared/control_tools/`
  - Implement parameter combination logic
  - Add plan ID generation with consistent `plan_morning_peak_g4202_` prefix
  - Implement Chinese name generation template
  - Add collection tagging ("morning_peak_g4202")
  - Output: `plan_generator.py`

- [x] **Task 3.2**: Implement spatial coverage algorithm
  - Develop segment selection logic
  - Implement strategy placement rules
  - Add conflict detection for overlapping zones
  - Output: Updated `plan_generator.py`

- [x] **Task 3.3**: Implement temporal pattern generator
  - Create time interval assignment logic
  - Implement phased activation patterns
  - Add smooth transition algorithms
  - Output: Integrated in `plan_generator.py`

- [x] **Task 3.4**: Implement strategy combination engine
  - Develop combination rule validator
  - Implement conflict resolution logic
  - Add parameter adjustment algorithms
  - Output: Integrated in `plan_generator.py`

- [x] **Task 3.5**: Generate first batch of plans (6 plans)
  - Generate 2 VSS-only plans (different segments)
  - Generate 2 TEC-only plans (different interchanges)
  - Generate 2 DHS-only plans (different severities)
  - Output: 6 plan directories in `control_data/plans/`

- [x] **Task 3.6**: Generate second batch of plans (7 plans)
  - Generate 3 VSS+TEC combination plans
  - Generate 2 VSS+DHS combination plans
  - Generate 2 TEC+DHS combination plans
  - Output: 7 plan directories in `control_data/plans/`

- [x] **Task 3.7**: Generate third batch of plans (7 plans)
  - Generate 3 VSS+TEC+DHS triple combination plans
  - Generate 4 plans with phased activation patterns
  - Output: 7 plan directories in `control_data/plans/`

## Phase 4: Validation and Testing (2 days)

- [x] **Task 4.1**: Validate network references
  - Run network validation on all 20 plans
  - Fix any invalid edge/junction references
  - Generate validation report
  - Output: `validation_report_network.json`

- [x] **Task 4.2**: Generate control.add.xml files
  - Create XML for each plan
  - Validate XML syntax against SUMO schema
  - Test XML loading in SUMO
  - Output: 20 `control.add.xml` files

- [x] **Task 4.3**: Test single plan simulation
  - Select one plan from each category
  - Run test simulation with baseline case
  - Verify simulation completes without errors
  - Output: `single_plan_test_results.json`
  - **Note**: 测试过程中发现status端点问题，已修复（见FIX_SUMMARY.md）

- [x] **Task 4.4**: Test batch simulation compatibility
  - Create test batch with 5 plans × 3 seeds
  - Run parallel batch simulation
  - Verify resource usage within limits
  - Output: `batch_compatibility_test.json`
  - **Note**: 已确认使用plan_opti目录结构，sumocfg路径正确

## Phase 5: Integration with Batch System and UI (1 day)

- [x] **Task 5.1**: Update plans_index.json
  - Add all 20 new plans to index with consistent naming
  - Include collection identifier for all morning peak plans
  - Add display metadata (Chinese names, descriptions)
  - Include complete metadata for each plan
  - Verify index structure compatibility
  - Output: Updated `plans_index.json`

- [x] **Task 5.1b**: Implement UI collection display
  - Add collection grouping logic in frontend
  - Implement "Select All Morning Peak" functionality
  - Add regex-based selection support
  - Create visual badges for strategy types and severity
  - Test multi-selection for batch operations
  - Output: Updated UI components
  - **Note**: 已实现集合分组显示、全选功能、正则表达式选择、策略类型和严重程度徽章

- [ ] **Task 5.2**: Create batch optimization configuration
  - Define optimization batch including new plans
  - Set random seed parameters (3-5 seeds)
  - Configure parallel execution settings
  - Output: `morning_peak_optimization_batch.json`

- [ ] **Task 5.3**: Test strategy ranking integration
  - Run small batch with ranking enabled
  - Verify ranking metrics collection
  - Test ranking report generation
  - Output: `ranking_integration_test.json`

- [ ] **Task 5.4**: Performance optimization
  - Profile resource usage for 60 parallel simulations
  - Optimize I/O operations
  - Tune parallel execution parameters
  - Output: `performance_optimization_report.json`

## Phase 6: Documentation and Deployment (1 day)

- [ ] **Task 6.1**: Document plan specifications
  - Create README for each plan category
  - Document parameter choices and rationale
  - Include usage examples
  - Output: `docs/control_plans/morning_peak/README.md`

- [ ] **Task 6.2**: Create API documentation
  - Document plan generation API endpoints
  - Include request/response examples
  - Add integration guide
  - Output: Updated API documentation

- [ ] **Task 6.3**: Create user guide
  - Write guide for using new morning peak plans
  - Include batch optimization workflow
  - Add troubleshooting section
  - Output: `docs/guides/morning_peak_plans_guide.md`

- [ ] **Task 6.4**: Deploy and verify
  - Deploy all plans to production environment
  - Run verification tests
  - Confirm batch system integration
  - Output: Deployment confirmation

## Success Validation

- [x] **Validation 1**: Confirm 20 plans generated as comprehensive collection (12 minimum, 20 target) ✓
- [x] **Validation 2**: All plans use consistent `plan_morning_peak_g4202_` prefix ✓
- [x] **Validation 3**: All plans have valid control.add.xml placeholder files ✓
- [ ] **Validation 4**: Plans display correctly in UI as unified collection
- [ ] **Validation 5**: Multi-selection works with "Select All Morning Peak" button
- [x] **Validation 6**: Plans cover G4202 and G5 highways ✓
- [x] **Validation 7**: Time intervals vary within 7:00-10:00 window ✓
- [x] **Validation 8**: All strategy combinations represented ✓
- [ ] **Validation 9**: Batch simulation runs successfully with 60 tasks in parallel
- [ ] **Validation 10**: Strategy ranking evaluates all plans correctly
- [x] **Validation 11**: Collection supports regex selection `plan_morning_peak_g4202_*` ✓

## Notes

- Tasks can be parallelized within phases
- Phase 1-2 can partially overlap
- Phase 3 tasks 3.5-3.7 can run in parallel after 3.1-3.4 complete
- Phase 4 validation should be iterative with Phase 3 generation
- Resource monitoring critical during Phase 4-5 testing