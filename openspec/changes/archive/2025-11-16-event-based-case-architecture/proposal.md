# Event-Based Case Architecture

**Change ID**: `event-based-case-architecture`
**Status**: Draft
**Created**: 2025-11-14
**Type**: Architecture Enhancement
**Priority**: P1
**Scope**: Backend (Case Management), Frontend (Scenario Browser)

---

## Overview

### Problem Statement

Currently, each scenario (event + control strategy combination) creates a completely independent case with its own config directory, leading to:

1. **Resource Duplication**: Same OD data, network files, TAZ files generated multiple times for scenarios from the same event
2. **OD Processing Waste**: Each scenario triggers separate OD generation (database queries + XML processing), even though event location/time are identical
3. **Inconsistent Data**: Multiple copies of config files can diverge over time
4. **Poor Organization**: No clear relationship between scenarios from the same event

**Current Structure**:
```
cases/
├── case_20251114_170211/    # scenario_10814_vss
│   └── config/              # Full config set
├── case_20251114_170842/    # scenario_10814_tec
│   └── config/              # Duplicate config set
└── case_20251114_171822/    # scenario_10814_dhs
    └── config/              # Duplicate config set
```

### Proposed Solution

Implement an **event-based case architecture** where:

- **1 Event → 1 Case → Multiple Simulations**
- **Shared Config**: All scenarios from the same event share config files (OD, network, TAZ, edgeData)
- **Scenario-Specific Simulations**: Each scenario has its own simulation directory with strategy-specific .add.xml

**New Structure**:
```
cases/
└── case_event_10814/                          # One case per event
    ├── config/                                 # Shared config (all scenarios)
    │   ├── dwd_od_weekly_xxx.rou.xml          # OD generated once
    │   ├── edgeData.add.xml
    │   ├── TAZ_6.add.xml
    │   └── sichuan202508v7.net.xml
    ├── simulations/                            # Multiple scenario simulations
    │   ├── event_simulation_scenario_10814_vss/      # VSS strategy
    │   │   ├── scenario_accident_vss_10814.add.xml   # Strategy-specific
    │   │   ├── simulation.sumocfg                    # Simulation configuration
    │   │   ├── simulation_metadata.json              # Simulation metadata
    │   │   ├── edgedata/                             # EdgeData output
    │   │   └── e1/                                   # E1 detector output
    │   ├── event_simulation_scenario_10814_tec/      # TEC strategy
    │   │   ├── scenario_accident_tec_10814.add.xml
    │   │   ├── simulation.sumocfg
    │   │   ├── simulation_metadata.json
    │   │   ├── edgedata/
    │   │   └── e1/
    │   └── event_simulation_scenario_10814_dhs/      # DHS strategy
    │       ├── scenario_accident_dhs_10814.add.xml
    │       ├── simulation.sumocfg
    │       ├── simulation_metadata.json
    │       ├── edgedata/
    │       └── e1/
    └── metadata.json                           # Event-level metadata
```

---

## Goals

### Primary Goals

1. **Eliminate Config Duplication**: Generate OD data, network files, TAZ files only once per event
2. **Optimize OD Processing**: Reduce database load by generating OD data once per event (not per scenario)
3. **Maintain Scenario Isolation**: Each scenario has independent simulation directory and results
4. **Improve Organization**: Clear event → scenarios hierarchy in file system

### Secondary Goals

5. **Backward Compatibility**: Existing time-based cases continue to work
6. **Incremental Migration**: Support both architectures during transition
7. **E1 Detector Support**: Create `e1/` output directories alongside `edgedata/`

---

## Benefits

### Resource Efficiency
- **OD Generation**: 1x instead of Nx (where N = number of strategies)
- **Disk Space**: ~500MB → ~100MB per event (4 strategies)
- **Database Load**: ~70% reduction in query volume

### Operational Benefits
- **Faster Case Creation**: Subsequent scenarios reuse existing config
- **Consistency**: All scenarios use identical base data
- **Analysis**: Easy comparison between strategies for same event

### Developer Benefits
- **Clear Architecture**: Event-centric design matches domain model
- **Simpler Testing**: Test once per event, not per scenario
- **Better Debugging**: Related scenarios co-located

---

## Key Design Decisions

### 1. Case ID Format

**Decision**: Use event-based IDs for scenario-created cases

```python
# Event scenario cases
case_id = f"case_event_{event_id}"      # e.g., case_event_10814

# Regular cases (backward compatible)
case_id = f"case_{timestamp}"            # e.g., case_20251114_170211
```

### 2. Simulation ID Format

**Decision**: Include scenario ID and strategy in simulation directory name

```python
simulation_id = f"event_simulation_scenario_{scenario_id}"
# e.g., event_simulation_scenario_10814_vss
```

**Rationale**:
- Easily identify scenario and strategy from directory name
- Unique across all simulations
- Clear differentiation from regular simulations

### 3. Config Sharing Strategy

**Decision**: First scenario creates config, subsequent scenarios reuse

**Detection Logic**:
```python
case_dir = Path(f"cases/case_event_{event_id}")
if case_dir.exists() and (case_dir / "config").exists():
    # Reuse existing config
    skip_od_generation = True
    skip_file_copies = True
else:
    # First scenario - create full config
    create_config_directory()
    generate_od_data()
    copy_network_taz_files()
```

### 4. Backward Compatibility

**Decision**: Detect case type by case_id pattern

```python
def is_event_based_case(case_id: str) -> bool:
    return case_id.startswith("case_event_")

def get_event_id_from_case(case_id: str) -> Optional[str]:
    if is_event_based_case(case_id):
        return case_id.replace("case_event_", "")
    return None
```

### 5. Output Directories

**Decision**: Create both `edgedata/` and `e1/` directories

```python
output_dirs = ["edgedata", "e1"]
for dir_name in output_dirs:
    (simulation_folder / dir_name).mkdir(exist_ok=True)
```

---

## Architecture Changes

### Case Service Changes

**File**: `api/services/case_service.py`

#### New Method: `_get_or_create_event_case()`

```python
def _get_or_create_event_case(
    self,
    event_id: str,
    event_type: str,
    network_file: str,
    od_file: str,
    taz_file: Optional[str],
    time_range: Dict[str, str]
) -> Tuple[Path, bool]:
    """
    Get existing event case or create new one.

    Returns:
        (case_path, is_new_case)
    """
    case_id = f"case_event_{event_id}"
    case_path = Path("cases") / case_id

    if case_path.exists() and (case_path / "config").exists():
        logger.info(f"✓ Reusing existing event case: {case_id}")
        return case_path, False
    else:
        logger.info(f"✓ Creating new event case: {case_id}")
        # Create full config
        return case_path, True
```

#### Modified Method: `create_case_with_simulation()`

```python
async def create_case_with_simulation(self, request: CreateCaseWithSimulationRequest):
    # Extract event_id from scenario_id
    event_id = request.event_id

    # Get or create event case
    case_path, is_new_case = self._get_or_create_event_case(
        event_id=event_id,
        event_type=request.event_type,
        network_file=request.network_file,
        od_file=request.od_file,
        taz_file=request.taz_file,
        time_range=request.time_range
    )

    if is_new_case:
        # First scenario - full setup
        await self._create_event_case_config(case_path, request)

    # Always create scenario-specific simulation
    simulation_id = f"event_simulation_scenario_{request.scenario_id}"
    await self._create_scenario_simulation(case_path, simulation_id, request)
```

### Simulation Directory Setup

```python
def _create_scenario_simulation(
    self,
    case_path: Path,
    simulation_id: str,
    request: CreateCaseWithSimulationRequest
):
    sim_dir = case_path / "simulations" / simulation_id
    sim_dir.mkdir(parents=True, exist_ok=True)

    # Copy scenario-specific .add.xml
    scenario_add_xml = self._find_scenario_add_xml(request.scenario_id)
    shutil.copy2(scenario_add_xml, sim_dir / f"scenario_{request.strategy}_{request.event_id}.add.xml")

    # Generate sumocfg
    sumocfg_content = generate_sumocfg_for_simulation(...)
    (sim_dir / "simulation.sumocfg").write_text(sumocfg_content)

    # Create output directories
    for output_dir in ["edgedata", "e1"]:
        (sim_dir / output_dir).mkdir(exist_ok=True)

    # Create simulation metadata
    metadata = {
        "simulation_id": simulation_id,
        "case_id": case_path.name,
        "scenario_id": request.scenario_id,
        "event_id": request.event_id,
        "strategy": request.strategy,
        ...
    }
    (sim_dir / "simulation_metadata.json").write_text(json.dumps(metadata, indent=2))
```

### Metadata Structure

#### Event Case Metadata

**File**: `cases/case_event_10814/metadata.json`

```json
{
  "case_id": "case_event_10814",
  "case_name": "Event 10814 Analysis",
  "case_type": "event_based",
  "event_id": "10814",
  "event_type": "01_accident",
  "created_at": "2025-11-14T20:53:38.761361",
  "version": "2.0",
  "files": {
    "network_file": "config/sichuan202508v7.net.xml",
    "routes_file": "config/dwd_od_weekly_20250613152237_20250613164916.rou.xml",
    "taz_file": "config/TAZ_6.add.xml",
    "edgedata_template": "config/edgeData.add.xml"
  },
  "time_range": {
    "start": "2025-06-13 15:22:37",
    "end": "2025-06-13 16:49:16"
  },
  "scenarios": [
    "scenario_10814_vss",
    "scenario_10814_tec",
    "scenario_10814_dhs",
    "scenario_10814_no_control"
  ],
  "simulations": {
    "event_simulation_scenario_10814_vss": {
      "created_at": "2025-11-14T20:53:38",
      "status": "ready"
    },
    "event_simulation_scenario_10814_tec": {
      "created_at": "2025-11-14T21:15:22",
      "status": "ready"
    }
  }
}
```

#### Simulation Metadata

**File**: `cases/case_event_10814/simulations/event_simulation_scenario_10814_vss/simulation_metadata.json`

**Note**: This format maintains 100% backward compatibility with existing simulation metadata structure.

```json
{
  "metadata_version": "2.0",
  "simulation_id": "event_simulation_scenario_10814_vss",
  "case_id": "case_event_10814",
  "status": "ready",
  "created_at": "2025-11-14T20:53:38.874134",
  "source_scenario": {
    "scenario_id": "scenario_10814_vss",
    "event_id": "10814",
    "event_type": "交通事故",
    "control_strategy_type": "VSS"
  },
  "simulation_params": {
    "duration_hours": 2.5,
    "random_seed": null,
    "simulation_type": "microscopic",
    "output_config": {
      "generate_edgedata": true,
      "generate_e1": true,
      "generate_summary": true,
      "generate_tripinfo": true,
      "generate_vehroute": false
    }
  },
  "config_file": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<configuration>\n    <input>\n        <net-file value=\"../../config/sichuan202508v7.net.xml\"/>\n        <route-files value=\"../../config/dwd_od_weekly_20250613152237_20250613164916.rou.xml\"/>\n        <additional-files value=\"TAZ_6.add.xml,edgeData.add.xml,../../config/scenario_accident_vss_10814.add.xml\"/>\n    </input>\n    <output>\n        <summary-output value=\"summary.xml\"/>\n        <tripinfo-output value=\"tripinfo.xml\"/>\n    </output>\n    <time>\n        <begin value=\"0\"/>\n        <end value=\"5199\"/>\n    </time>\n    <processing>\n        <ignore-route-errors value=\"true\"/>\n        <collision.action value=\"warn\"/>\n    </processing>\n    <report>\n        <verbose value=\"true\"/>\n        <no-step-log value=\"true\"/>\n    </report>\n</configuration>",
  "config_file_path": "simulation.sumocfg",
  "sumocfg_generated_at": "2025-11-14T20:53:54.323832"
}
```

**Backward Compatibility Notes**:
- Uses existing `source_scenario` nested structure (not flattened fields)
- Includes `config_file` with full sumocfg content (for compatibility)
- Adds `config_file_path` for file-based access (new in this change)
- Includes `random_seed` field (can be null)
- Uses existing `output_config` format
- Only difference from time-based cases: `simulation_id` naming convention

### Scenario Index Updates

**Location**: `output/scenarios/scenario_index.json`

Add `case_id` field to track which case each scenario belongs to:

```json
{
  "scenario_10814_vss": {
    "scenario_id": "scenario_10814_vss",
    "event_id": "10814",
    "event_type": "01_accident",
    "strategy": "VSS",
    "case_id": "case_event_10814",              // ✅ New field
    "simulation_id": "event_simulation_scenario_10814_vss",  // ✅ New field
    "linked_at": "2025-11-14T20:53:38",
    ...
  }
}
```

---

## Migration Strategy

### Phase 1: Parallel Support (Weeks 1-2)

1. Implement event-based architecture
2. Keep time-based case creation for regular cases
3. Detect case type by ID pattern

### Phase 2: Testing & Validation (Week 3)

1. Test scenario creation with config reuse
2. Validate simulation execution
3. Compare results between architectures

### Phase 3: User Adoption (Week 4+)

1. Document new architecture
2. Monitor usage metrics
3. Plan eventual deprecation of time-based cases (optional)

---

## Testing Strategy

### Unit Tests

```python
def test_event_case_id_generation():
    event_id = "10814"
    case_id = generate_event_case_id(event_id)
    assert case_id == "case_event_10814"

def test_simulation_id_generation():
    scenario_id = "scenario_10814_vss"
    sim_id = generate_simulation_id(scenario_id)
    assert sim_id == "event_simulation_scenario_10814_vss"

def test_case_type_detection():
    assert is_event_based_case("case_event_10814") == True
    assert is_event_based_case("case_20251114_170211") == False
```

### Integration Tests

```python
def test_event_case_config_reuse():
    """Test that second scenario reuses existing config"""
    # Create first scenario
    response1 = create_case_with_simulation(
        scenario_id="scenario_10814_vss",
        event_id="10814"
    )
    case_id_1 = response1["case_id"]

    # Create second scenario
    response2 = create_case_with_simulation(
        scenario_id="scenario_10814_tec",
        event_id="10814"  # Same event
    )
    case_id_2 = response2["case_id"]

    # Verify same case used
    assert case_id_1 == case_id_2 == "case_event_10814"

    # Verify different simulation IDs
    assert response1["simulation_id"] != response2["simulation_id"]

    # Verify config files identical
    config_1 = Path(f"cases/{case_id_1}/config")
    config_2 = Path(f"cases/{case_id_2}/config")
    assert config_1 == config_2  # Same directory

def test_output_directories_created():
    """Test that both edgedata/ and e1/ directories are created"""
    response = create_case_with_simulation(
        scenario_id="scenario_10814_vss",
        event_id="10814"
    )

    sim_dir = Path(f"cases/{response['case_id']}/simulations/{response['simulation_id']}")
    assert (sim_dir / "edgedata").exists()
    assert (sim_dir / "e1").exists()
```

### E2E Tests

```python
def test_scenario_browser_workflow():
    """Test complete workflow from scenario browser"""
    # User clicks "创建" for scenario_10814_vss
    response1 = POST("/api/v1/scenario/create_case_with_simulation", {
        "scenario_id": "scenario_10814_vss",
        "event_id": "10814",
        ...
    })

    # Verify OD generation triggered
    assert response1["od_generation_status"] == "in_progress"

    # Wait for OD completion
    wait_for_od_completion(response1["case_id"])

    # User clicks "创建" for scenario_10814_tec (same event)
    response2 = POST("/api/v1/scenario/create_case_with_simulation", {
        "scenario_id": "scenario_10814_tec",
        "event_id": "10814",
        ...
    })

    # Verify OD generation NOT triggered (reused)
    assert response2["od_generation_status"] == "completed"
    assert response2["od_reused"] == True
```

---

## Risks & Mitigation

### Risk 1: Config Corruption

**Risk**: If shared config is corrupted, all scenarios affected

**Mitigation**:
- Config files are read-only after creation
- Simulations copy files they need (TAZ, edgeData)
- Config validation on case creation

### Risk 2: Concurrent Creation

**Risk**: Two scenarios from same event created simultaneously

**Mitigation**:
- File system locking during case creation
- Check-and-create atomic operation
- Retry logic for race conditions

### Risk 3: Migration Complexity

**Risk**: Users have existing time-based cases

**Mitigation**:
- Both architectures supported indefinitely
- Clear documentation on differences
- No forced migration required

---

## Success Metrics

### Performance Metrics

- **OD Generation Time**: Measure total time for creating 4 scenarios from same event
  - Before: 4x OD generation = ~8 minutes
  - After: 1x OD generation = ~2 minutes
  - **Target**: 75% reduction

- **Disk Usage**: Measure storage for event with 4 scenarios
  - Before: ~2GB (4 × 500MB)
  - After: ~600MB (1 × 500MB + 4 × 25MB)
  - **Target**: 70% reduction

### Quality Metrics

- **Config Consistency**: 100% of scenarios from same event use identical config
- **Simulation Success Rate**: Maintain >95% success rate
- **Test Coverage**: >90% for new code

---

## Related Documents

- **Architecture Design**: `design.md`
- **Implementation Tasks**: `tasks.md`
- **Current Issues**:
  - Route files fix: `ROUTE_FILES_AND_SUMOCFG_FIX.md`
  - TAZ duplication: `DUPLICATE_TAZ_FIX.md`
  - Phase 3 fixes: `PHASE3_CRITICAL_FIXES_SUMMARY.md`

---

## Open Questions

1. **Q**: Should we support case deletion?
   **A**: TBD - Need to handle cascade (delete all simulations when case deleted)

2. **Q**: How to handle event data updates?
   **A**: Config is immutable once created. New event data = new case.

3. **Q**: Should regular (non-event) cases also support multiple simulations?
   **A**: Future enhancement - out of scope for this change

---

**Status**: Draft - Awaiting Review
**Next Steps**:
1. Review and approve proposal
2. Create design.md with detailed architecture
3. Create tasks.md with implementation plan
4. Begin Phase 1 implementation
