# Phase 1 Plan Management Unit Tests

## Overview

This directory contains comprehensive unit tests for Phase 1 (Plan Management Core) of the traffic control optimization system.

## Test Files

### 1. `test_plan_entity.py`
Tests for the Plan entity model (`api/models/control/entities/plan.py`)

**Coverage:**
- Basic plan creation with all fields
- Computed properties (`is_baseline`, `strategy_count`)
- Optional fields handling
- Field validation

**Key Tests:**
- `test_plan_entity_basic_creation` - Verify all fields are properly stored
- `test_plan_entity_is_baseline` - Test baseline detection logic
- `test_plan_entity_strategy_count` - Test strategy counting
- `test_plan_entity_optional_fields` - Test optional field defaults

---

### 2. `test_plan_file_manager.py`
Tests for plan file management (`shared/control_tools/plan_file_manager.py`)

**Coverage:**
- CRUD operations (create, read, update, delete)
- Plan ID generation
- Index management
- Baseline plan creation
- File system operations

**Key Tests:**
- `test_create_plan` - Plan creation and file structure
- `test_get_plan` - Plan retrieval
- `test_update_plan` - Plan updates and metadata sync
- `test_delete_plan` - Plan deletion and cleanup
- `test_delete_baseline_plan_protected` - Baseline protection
- `test_list_plans_with_filters` - Filtering logic
- `test_ensure_baseline_plan_exists` - Baseline initialization
- `test_plans_index_management` - Index consistency

---

### 3. `test_plan_validator.py`
Tests for plan validation (`shared/control_tools/plan_validator.py`)

**Coverage:**
- Spatial conflict detection
- Timing coordination checks
- Strategy compatibility analysis
- Warning generation
- Validation result structure

**Key Tests:**
- `test_validate_empty_plan` - Baseline plan validation
- `test_spatial_conflict_detection_same_edge` - Overlapping strategies
- `test_spatial_conflict_different_types` - Multi-type conflicts
- `test_timing_coordination_dhs_without_vss` - Missing advance warning
- `test_strategy_compatibility_dhs_without_vss` - Incomplete strategy sets
- `test_warning_mode_always_valid` - Non-blocking validation

---

### 4. `test_additional_generator_plan.py`
Tests for plan XML generation (`shared/control_tools/additional_generator.py`)

**Coverage:**
- Empty plan XML generation
- Single strategy XML
- Multiple strategy XML merging
- Strategy grouping by type
- XML structure and validation
- Header and comment generation

**Key Tests:**
- `test_generate_empty_plan_xml` - Baseline XML
- `test_generate_single_strategy_xml` - Single strategy
- `test_generate_multiple_strategies_xml` - Multiple strategies
- `test_xml_groups_by_strategy_type` - Proper grouping (VSS/DHS/TEC)
- `test_xml_validation_passes` - Well-formed XML
- `test_handles_strategy_without_template` - Error handling

---

### 5. `test_strategy_reference_protection.py`
Tests for strategy reference protection (`shared/control_tools/strategy_file_manager.py`)

**Coverage:**
- Reference count increment/decrement
- Delete permission checking
- Reference field initialization
- Idempotency

**Key Tests:**
- `test_increment_strategy_reference` - Adding plan reference
- `test_increment_reference_multiple_plans` - Multiple references
- `test_increment_reference_idempotent` - Duplicate handling
- `test_decrement_strategy_reference` - Removing reference
- `test_can_delete_strategy_no_references` - Unreferenced deletion allowed
- `test_can_delete_strategy_with_references` - Referenced deletion blocked
- `test_referenced_by_field_initialized` - Auto-initialization

---

### 6. `test_control_plan_service.py`
Tests for plan service layer (`api/services/control_plan_service.py`)

**Coverage:**
- Plan CRUD operations
- Strategy validation
- XML generation coordination
- Reference management
- Plan preview and validation

**Key Tests:**
- `test_create_plan_success` - Complete creation flow
- `test_create_plan_strategy_not_found` - Error handling
- `test_get_plan_with_strategies` - Detailed retrieval
- `test_update_plan_strategy_ids_changed` - Reference updates
- `test_delete_plan` - Cleanup and reference decrements
- `test_regenerate_plan_xml` - Manual XML regeneration
- `test_validate_plan_config` - Validation workflow
- `test_preview_plan` - Preview generation

---

## Running Tests

### Run All Phase 1 Tests

```bash
# Windows PowerShell
.\run_phase1_tests.ps1

# Or manually with pytest
conda activate od_project
pytest tests/unit/test_plan_*.py tests/unit/test_strategy_reference_protection.py tests/unit/test_additional_generator_plan.py tests/unit/test_control_plan_service.py -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_plan_entity.py -v
```

### Run with Coverage

```bash
pytest tests/unit/test_plan_*.py --cov=api --cov=shared --cov-report=html
```

### Run Specific Test

```bash
pytest tests/unit/test_plan_entity.py::test_plan_entity_is_baseline -v
```

## Test Coverage Goals

- **Target Coverage**: >80% for all components
- **Critical Paths**: 100% coverage for:
  - Plan CRUD operations
  - Reference protection logic
  - XML generation
  - Baseline plan handling

## Expected Coverage Areas

| Component | Target | Notes |
|-----------|--------|-------|
| `plan_file_manager.py` | >85% | Core CRUD logic |
| `plan_validator.py` | >80% | Validation rules |
| `additional_generator.py` | >75% | XML generation (plan functions) |
| `strategy_file_manager.py` | >70% | Reference protection only |
| `control_plan_service.py` | >80% | Business logic orchestration |
| `plan.py` (entity) | 100% | Simple data model |

## Test Dependencies

- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `unittest.mock` - Mocking dependencies

## Fixtures and Utilities

Common fixtures used across tests:

- `temp_plans_dir` - Temporary plans directory for file operations
- `temp_strategies_dir` - Temporary strategies directory
- `sample_plan_data` - Standard plan data for testing
- `sample_vss_strategy` - VSS strategy fixture
- `sample_dhs_strategy` - DHS strategy fixture
- `sample_tec_strategy` - TEC strategy fixture

## Known Issues / Limitations

1. Some file system operations require temporary directories (using `tmp_path` fixture)
2. Service layer tests use mocks extensively to isolate unit tests
3. XML validation tests check well-formedness but not SUMO-specific schema compliance

## Next Steps

After completing unit tests:
1. **Integration Tests** - Test component interactions
2. **E2E Tests** - Full workflow testing with Playwright
3. **Frontend Tests** - UI component tests
4. **API Tests** - REST endpoint testing

## Maintenance

When adding new features to Phase 1:
1. Add corresponding unit tests
2. Ensure >80% coverage for new code
3. Update this README with new test files
4. Run full test suite before committing
