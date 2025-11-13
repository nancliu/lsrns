# simulation-orchestration Specification

## Purpose

Provide unified batch simulation execution interface that detects simulation source and delegates to appropriate services without breaking existing workflows.

**Design Decision**: Q1-C - Orchestration layer with automatic source detection (Q3 backward compatibility)

---

## ADDED Requirements

### Requirement: Automatic Simulation Source Detection

The system SHALL automatically detect simulation source from metadata and delegate to appropriate service.

**Rationale**: Support multiple simulation workflows (event-scenario, OD extraction, control plan) without breaking existing code.

#### Scenario: Detect event-scenario simulation

- **GIVEN** simulation metadata with "metadata_version": "2.0" and "source_scenario" field
- **WHEN** `SimulationOrchestrator.batch_start_simulations()` is called
- **THEN** detects source as "event-scenario"
- **AND** delegates to BatchSimulationScheduler (reused, Q2)
- **AND** existing OD/control-plan workflows continue unchanged

#### Scenario: Detect OD extraction simulation (backward compatibility)

- **GIVEN** simulation metadata WITHOUT "metadata_version" field
- **AND** metadata does NOT have "source_scenario" or "plan_id" fields
- **WHEN** `SimulationOrchestrator.batch_start_simulations()` is called
- **THEN** detects source as "od-extraction"
- **AND** delegates to SimulationService (unchanged)
- **AND** preserves existing behavior

#### Scenario: Detect control-plan simulation (backward compatibility)

- **GIVEN** simulation metadata with "plan_id" or "control_plan" field
- **WHEN** `SimulationOrchestrator.batch_start_simulations()` is called
- **THEN** detects source as "control-plan"
- **AND** delegates to BatchOptimizationService (unchanged)
- **AND** preserves existing behavior

---

### Requirement: Unified Batch Execution Interface

The system SHALL provide unified batch execution interface for all simulation types.

**Rationale**: Simplify client code with single entry point regardless of simulation source.

#### Scenario: Batch start event-scenario simulations

- **GIVEN** 10 event-scenario simulations with status="pending"
- **AND** simulations have "metadata_version": "2.0"
- **WHEN** `SimulationOrchestrator.batch_start_simulations(simulation_ids, parallel_workers=4)` is called
- **THEN** returns BatchExecutionResponse with batch_id
- **AND** reuses BatchSimulationScheduler for parallel execution (Q2)
- **AND** starts 4 concurrent simulations
- **AND** queues remaining simulations

#### Scenario: Preserve existing OD workflow

- **GIVEN** existing OD extraction case created via `/api/v1/case/create`
- **AND** simulation created via `/api/v1/simulation/prepare`
- **WHEN** simulation is started via existing `/api/v1/simulation/start` endpoint
- **THEN** workflow continues unchanged
- **AND** SimulationOrchestrator is NOT involved
- **AND** zero impact on existing code

---

### Requirement: Non-Breaking Integration

The system SHALL NOT modify existing service interfaces when adding orchestration layer.

**Rationale**: PRINCIPLE-INTEGRATION-001 - New services must not break existing workflows.

#### Scenario: Existing SimulationService unchanged

- **GIVEN** existing OD extraction code calls `SimulationService.prepare_simulation()` and `SimulationService.start_simulation()`
- **WHEN** Phase 2 is deployed
- **THEN** SimulationService interface is unchanged
- **AND** OD extraction workflow continues working
- **AND** no code changes required in existing clients

#### Scenario: Existing BatchOptimizationService unchanged

- **GIVEN** existing control plan optimization code calls `BatchOptimizationService.start_batch_service()`
- **WHEN** Phase 2 is deployed
- **THEN** BatchOptimizationService interface is unchanged
- **AND** control plan workflow continues working
- **AND** BatchSimulationScheduler is reused via adapter (Q2)

---

### Requirement: Metadata Version Compatibility

The system SHALL support both version 1.0 and 2.0 metadata schemas simultaneously.

**Rationale**: Q3, Q6, Q7 - Backward compatibility for existing cases and simulations.

#### Scenario: Read version 1.0 case metadata

- **GIVEN** existing case metadata WITHOUT "metadata_version" field
- **WHEN** `CaseService.get_case(case_id)` is called
- **THEN** detects version as "1.0" (implicit)
- **AND** reads metadata successfully
- **AND** handles missing "source_scenario" field gracefully (null)

#### Scenario: Read version 2.0 case metadata

- **GIVEN** new event-scenario case with "metadata_version": "2.0"
- **AND** has "source_scenario" field
- **WHEN** `CaseService.get_case(case_id)` is called
- **THEN** detects version as "2.0"
- **AND** reads "source_scenario" field
- **AND** enables scenario lineage tracking

#### Scenario: Mixed versions in same system

- **GIVEN** 50 existing OD cases (version 1.0)
- **AND** 10 new event-scenario cases (version 2.0)
- **WHEN** system lists all cases
- **THEN** both versions are displayed correctly
- **AND** no errors or warnings
- **AND** old cases continue functioning

---

## Design Constraints

1. **MUST NOT** modify SimulationService interface
2. **MUST NOT** modify BatchOptimizationService interface
3. **MUST** reuse BatchSimulationScheduler (Q2)
4. **MUST** support metadata version 1.0 and 2.0 (Q3, Q6, Q7)
5. **MUST** delegate based on source detection, not hardcode workflows

---

## Success Criteria

- [ ] Event-scenario simulations can be batch-started via orchestrator
- [ ] Existing OD extraction workflow continues unchanged
- [ ] Existing control plan workflow continues unchanged
- [ ] Metadata version 1.0 and 2.0 coexist without errors
- [ ] Source detection is automatic and reliable
- [ ] Zero breaking changes to existing code
