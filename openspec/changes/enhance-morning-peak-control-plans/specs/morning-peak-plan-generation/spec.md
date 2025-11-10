# morning-peak-plan-generation Specification

## ADDED Requirements

### Requirement: System SHALL support comprehensive plan collection display in UI

The system SHALL provide UI components to display the morning peak control plan collection as a cohesive set with multi-selection capabilities and visual organization by strategy type and severity.

#### Scenario: Display plan collection in UI selection panel

**Given**:
- 20 morning peak plans exist with `plan_morning_peak_g4202_` prefix
- User navigates to plan selection interface
- Plans have consistent naming and metadata

**When**:
- UI loads available plans
- System filters plans by collection identifier

**Then**:
- UI displays section header "G4202早高峰综合管控方案集"
- All 20 plans appear under this collection
- Each plan shows checkbox for selection
- Plans are grouped by strategy type (VSS/TEC/DHS/Composite)
- Plans show severity badge (Mild/Moderate/Severe)
- "Select All Morning Peak" button is available
- Selected count updates dynamically: "已选择 5/20 个方案"

#### Scenario: Multi-select plans for parallel batch simulation

**Given**:
- User views morning peak plan collection
- 20 plans are displayed with checkboxes
- Batch simulation supports up to 60 parallel tasks

**When**:
- User clicks "Select All Morning Peak" button
- Or uses regex filter `plan_morning_peak_g4202_*`
- User configures 3 random seeds

**Then**:
- All 20 plans are selected automatically
- UI shows "已选择 20 个方案"
- Batch preview shows "将创建 60 个仿真任务 (20方案 × 3种子)"
- "开始批量仿真" button becomes active
- System validates resource availability for 60 tasks
- Plans maintain consistent ordering in batch

### Requirement: System SHALL generate parameterized morning peak control plans

The system SHALL provide a plan generation service that creates morning peak control plans by systematically combining spatial segments, temporal intervals, strategy types, and severity levels for the G4202 and G5 highway network.

#### Scenario: Generate a single-strategy VSS plan for G4202 eastern section

**Given**:
- Highway segment: G4202 K0-K20
- Time interval: 7:00-8:30 (early morning peak)
- Strategy type: VSS only
- Severity level: moderate

**When**:
- Plan generator is invoked with these parameters
- Network validation passes for specified segments

**Then**:
- System creates plan_id: `plan_morning_peak_g4202_vss_k0k20_moderate_v1`
- System assigns Chinese name: "G4202早高峰VSS东段中度综合管控方案V1"
- System tags plan with collection: "morning_peak_g4202"
- System generates plan metadata with all parameters
- System selects appropriate VSS strategy templates for K0-K20 segment
- System configures VSS speed limits based on moderate severity (20-30% reduction)
- System saves plan to control_data/plans/ directory
- System updates plans_index.json with new plan entry

#### Scenario: Generate a composite VSS+TEC plan for G5 interchange

**Given**:
- Highway segment: G5 interchange with G4202
- Time interval: 7:30-9:00 (core morning peak)
- Strategy types: VSS + TEC combination
- Severity level: severe

**When**:
- Plan generator is invoked with composite strategy parameters
- Conflict detection validates no overlapping control zones

**Then**:
- System creates plan_id: `plan_morning_peak_g4202_vss_tec_g5_interchange_severe_v1`
- System assigns Chinese name: "G4202早高峰VSS+TEC立交严重综合管控方案V1"
- System tags plan with collection: "morning_peak_g4202"
- System coordinates VSS zones upstream of interchange
- System positions TEC control at interchange entrance
- System applies severe parameters (VSS: 30-50% speed reduction, TEC: 40-60% flow control)
- System ensures minimum 2km spacing between TEC points
- System generates control.add.xml with both strategy types

### Requirement: System SHALL validate spatial coverage for generated plans

The system SHALL ensure generated plans cover the specified highway segments with valid network references and appropriate strategy placement based on traffic patterns and infrastructure constraints.

#### Scenario: Validate G4202 segment coverage

**Given**:
- Target segment: G4202 K20-K40
- Available edges from network file
- Existing gantry and detector locations

**When**:
- Plan generator attempts to place control strategies
- System checks edge existence in network

**Then**:
- System validates all referenced edges exist in network
- System ensures VSS covers major flow segments
- System places TEC at natural bottlenecks (on-ramps, toll stations)
- System identifies suitable DHS segments (shoulders available)
- System reports coverage percentage of target segment
- System warns if coverage < 80% of segment length

#### Scenario: Handle invalid network references

**Given**:
- Plan references edge that doesn't exist in network
- Or junction ID is incorrect

**When**:
- Validation runs during plan generation

**Then**:
- System logs specific invalid reference
- System attempts to find nearest valid alternative
- System reports error if no alternative found
- System excludes invalid strategies from plan
- System continues generation with valid strategies only

### Requirement: System SHALL implement temporal variation patterns

The system SHALL create plans with different temporal patterns within the morning peak window (6:30-10:30), including phased activation, overlapping intervals, and adaptive duration based on expected traffic patterns.

#### Scenario: Create phased activation plan

**Given**:
- Morning peak window: 7:00-10:00
- Phased approach requested
- Three activation phases defined

**When**:
- Plan generator creates temporal pattern

**Then**:
- Phase 1 (7:00-8:00): Activate mild controls on critical segments
- Phase 2 (8:00-9:00): Escalate to moderate controls, expand coverage
- Phase 3 (9:00-10:00): Maintain or reduce based on flow
- Each phase has specific strategy parameters
- Transitions between phases are smooth (no abrupt changes)
- System generates time-based additional files for SUMO

#### Scenario: Create adaptive duration plan based on traffic patterns

**Given**:
- Historical traffic data shows peak at 8:15
- Traffic reduces after 9:30

**When**:
- Plan generator uses traffic pattern template

**Then**:
- System sets pre-activation at 7:00 (preparation)
- System sets maximum control 7:45-8:45 (peak coverage)
- System implements gradual reduction 8:45-9:30
- System includes early termination condition if flow normalizes
- Each time period has appropriate strategy intensity

### Requirement: System SHALL enforce strategy combination rules

The system SHALL validate and enforce rules for combining multiple control strategies within a single plan, preventing conflicts and ensuring traffic flow coherence.

#### Scenario: Validate VSS+TEC combination

**Given**:
- Plan includes both VSS and TEC strategies
- VSS zone: K10-K15
- TEC point: K12

**When**:
- System validates strategy combination

**Then**:
- System detects TEC point within VSS zone
- System adjusts TEC to K8 (upstream of VSS) or K17 (downstream)
- System ensures minimum 2km buffer between control types
- System logs adjustment reason
- System maintains strategy effectiveness despite adjustment

#### Scenario: Enforce maximum intervention limits

**Given**:
- Plan requests VSS+TEC+DHS triple combination
- All strategies set to severe level
- Same road segment targeted

**When**:
- System evaluates total intervention level

**Then**:
- System calculates cumulative impact on capacity
- System warns if total capacity reduction > 60%
- System suggests parameter adjustments
- System limits maximum speed reduction when DHS active
- System ensures emergency vehicle access maintained

### Requirement: System SHALL integrate generated plans with batch optimization

The system SHALL ensure all generated plans are compatible with the batch optimization system, supporting parallel simulation with multiple random seeds and strategy ranking evaluation.

#### Scenario: Prepare plan for batch simulation

**Given**:
- Newly generated plan with 3 strategies
- Batch system requests 5 random seeds
- 60 total concurrent simulations planned

**When**:
- Plan is added to batch optimization queue

**Then**:
- System generates control.add.xml for plan
- System validates XML against SUMO requirements
- System creates plan directory structure
- System initializes simulation metadata
- System confirms resource requirements (RAM, CPU)
- System adds plan to batch_metadata.json
- Plan executes successfully in parallel batch

#### Scenario: Enable plan comparison in ranking system

**Given**:
- Multiple plan variations for same segment
- Different strategy combinations and severities
- Ranking system requires comparison metrics

**When**:
- Plans complete batch simulation

**Then**:
- Each plan provides standard metrics (delay, speed, flow)
- System tags plans with comparison groups
- System enables multi-criteria scoring
- System identifies best plan for conditions
- System generates ranking report with recommendations