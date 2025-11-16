# Event-Based Case Architecture - Detailed Design

**Change ID**: `event-based-case-architecture`
**Version**: 1.0
**Last Updated**: 2025-11-14

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [API Changes](#api-changes)
5. [Database Schema](#database-schema)
6. [File System Layout](#file-system-layout)
7. [Backward Compatibility](#backward-compatibility)
8. [Error Handling](#error-handling)

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     Scenario Browser (Frontend)              │
│                                                              │
│  User clicks "创建" → scenario_10814_vss                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Case Service (api/services/case_service.py)     │
│                                                              │
│  1. Extract event_id from scenario_id                       │
│  2. Check if case_event_{event_id} exists                   │
│  3. If new: Create config + Generate OD                     │
│  4. If exists: Reuse config                                 │
│  5. Create simulation directory                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      File System                             │
│                                                              │
│  cases/                                                      │
│  └── case_event_10814/                                      │
│      ├── config/         (shared)                           │
│      └── simulations/                                        │
│          ├── event_simulation_scenario_10814_vss/           │
│          └── event_simulation_scenario_10814_tec/           │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **Case Service** | Case creation & management | `api/services/case_service.py` |
| **Scenario Index Updater** | Update scenario → case links | `shared/utilities/scenario_index_updater.py` |
| **SUMO Utils** | Generate sumocfg, edgeData | `shared/utilities/sumo_utils.py` |
| **OD Processor** | Generate OD data | `shared/data_processors/od_processor.py` |
| **Metadata Manager** | Manage metadata files | `api/services/metadata_manager.py` |

---

## Component Design

### 1. Case Service Enhancements

#### New Helper Methods

**Location**: `api/services/case_service.py`

##### `_extract_event_id_from_scenario(scenario_id: str) -> str`

```python
def _extract_event_id_from_scenario(self, scenario_id: str) -> str:
    """
    Extract event ID from scenario ID.

    Format: scenario_{event_id}_{strategy}
    Example: scenario_10814_vss → 10814

    Args:
        scenario_id: Scenario identifier (e.g., 'scenario_10814_vss')

    Returns:
        Event ID (e.g., '10814')

    Raises:
        ValueError: If scenario_id format is invalid
    """
    parts = scenario_id.split('_')
    if len(parts) < 3 or parts[0] != 'scenario':
        raise ValueError(f"Invalid scenario_id format: {scenario_id}")

    return parts[1]  # Event ID
```

##### `_get_or_create_event_case() -> Tuple[Path, bool, Dict]`

```python
def _get_or_create_event_case(
    self,
    event_id: str,
    event_type: str,
    network_file: str,
    od_file: str,
    taz_file: Optional[str],
    time_range: Dict[str, str],
    description: Optional[str] = None
) -> Tuple[Path, bool, Dict[str, Any]]:
    """
    Get existing event case or create new one.

    This implements the core logic for event-based case reuse:
    1. Check if case_event_{event_id} exists
    2. If exists and has config → reuse
    3. If not exists → create new case with full config

    Args:
        event_id: Event identifier
        event_type: Event type folder (e.g., '01_accident')
        network_file: Network file path
        od_file: OD/routes file path
        taz_file: TAZ file path (optional)
        time_range: Event time range
        description: Case description (optional)

    Returns:
        Tuple of:
        - case_path: Path to case directory
        - is_new_case: True if newly created, False if reused
        - case_metadata: Case metadata dictionary

    Example:
        First call (scenario_10814_vss):
            returns (cases/case_event_10814, True, {...})
        Second call (scenario_10814_tec):
            returns (cases/case_event_10814, False, {...})
    """
    case_id = f"case_event_{event_id}"
    case_path = Path("cases") / case_id
    metadata_file = case_path / "metadata.json"

    # Check if case exists with valid config
    if case_path.exists() and (case_path / "config").exists() and metadata_file.exists():
        logger.info(f"✓ Reusing existing event case: {case_id}")
        logger.info(f"  - Config directory: {case_path / 'config'}")
        logger.info(f"  - OD data already generated")

        # Load existing metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            case_metadata = json.load(f)

        return case_path, False, case_metadata

    else:
        logger.info(f"✓ Creating new event case: {case_id}")

        # Create case directory structure
        case_path.mkdir(parents=True, exist_ok=True)
        (case_path / "config").mkdir(exist_ok=True)
        (case_path / "simulations").mkdir(exist_ok=True)

        # Create case metadata
        case_metadata = {
            "case_id": case_id,
            "case_name": f"Event {event_id} Analysis",
            "case_type": "event_based",
            "event_id": event_id,
            "event_type": event_type,
            "created_at": datetime.now().isoformat(),
            "version": "2.0",
            "description": description or f"Event-based case for event {event_id}",
            "files": {
                "network_file": f"config/{Path(network_file).name}",
                "routes_file": f"config/{Path(od_file).name}",
                "taz_file": f"config/{Path(taz_file).name}" if taz_file else None,
                "edgedata_template": "config/edgeData.add.xml"
            },
            "time_range": time_range,
            "scenarios": [],  # Will be populated as scenarios are added
            "simulations": {}  # Will be populated as simulations are created
        }

        # Save metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(case_metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"  - Created case directory: {case_path}")
        logger.info(f"  - Case metadata saved")

        return case_path, True, case_metadata
```

##### `_create_scenario_simulation()`

```python
def _create_scenario_simulation(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any],
    request: CreateCaseWithSimulationRequest
) -> Tuple[str, Path]:
    """
    Create simulation directory for a specific scenario.

    This creates the scenario-specific simulation setup:
    1. Create simulation directory with unique ID
    2. Copy scenario .add.xml file
    3. Generate simulation.sumocfg
    4. Create output directories (edgedata/, e1/)
    5. Create simulation metadata

    Args:
        case_path: Path to case directory
        case_metadata: Case metadata dictionary
        request: Simulation creation request

    Returns:
        Tuple of (simulation_id, simulation_path)
    """
    # Generate simulation ID
    simulation_id = f"event_simulation_scenario_{request.scenario_id}"
    sim_dir = case_path / "simulations" / simulation_id

    # Create simulation directory
    sim_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Created simulation directory: {sim_dir}")

    # Find and copy scenario .add.xml
    scenario_add_xml_path = self._find_scenario_add_xml(
        request.scenario_id,
        request.event_type
    )

    if scenario_add_xml_path:
        target_filename = f"scenario_{request.strategy}_{request.event_id}.add.xml"
        target_path = sim_dir / target_filename

        shutil.copy2(scenario_add_xml_path, target_path)
        logger.info(f"✓ Copied scenario .add.xml: {target_filename}")
    else:
        logger.warning(f"⚠️ Scenario .add.xml not found for {request.scenario_id}")

    # Generate sumocfg
    from shared.utilities.sumo_utils import generate_sumocfg_for_simulation

    sumocfg_content = generate_sumocfg_for_simulation(
        case_metadata=case_metadata,
        simulation_type=request.simulation_type,
        simulation_folder=sim_dir,
        case_root=case_path,
        simulation_params=request.simulation_params or {}
    )

    sumocfg_file = sim_dir / "simulation.sumocfg"
    with open(sumocfg_file, 'w', encoding='utf-8') as f:
        f.write(sumocfg_content)

    logger.info(f"✓ Generated simulation.sumocfg")

    # Create output directories
    output_dirs = ["edgedata", "e1"]
    for dir_name in output_dirs:
        output_dir = sim_dir / dir_name
        output_dir.mkdir(exist_ok=True)
        logger.info(f"✓ Created output directory: {dir_name}/")

    # Create simulation metadata
    sim_metadata = {
        "metadata_version": "2.0",
        "simulation_id": simulation_id,
        "case_id": case_metadata["case_id"],
        "scenario_id": request.scenario_id,
        "event_id": request.event_id,
        "strategy": request.strategy,
        "created_at": datetime.now().isoformat(),
        "status": "ready",
        "config_file_path": str(sumocfg_file.relative_to(sim_dir)),
        "simulation_params": {
            "duration_hours": request.simulation_duration_hours,
            "simulation_type": request.simulation_type.value,
            "output_config": request.output_config
        },
        "output_directories": {
            "edgedata": "edgedata/",
            "e1": "e1/"
        }
    }

    sim_metadata_file = sim_dir / "simulation_metadata.json"
    with open(sim_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Simulation metadata saved")

    return simulation_id, sim_dir
```

##### `_find_scenario_add_xml()`

```python
def _find_scenario_add_xml(
    self,
    scenario_id: str,
    event_type: str
) -> Optional[Path]:
    """
    Find scenario .add.xml file in output directory.

    Search path: output/scenarios/{event_type}/{scenario_id}/

    Args:
        scenario_id: Scenario identifier
        event_type: Event type folder (e.g., '01_accident')

    Returns:
        Path to .add.xml file, or None if not found
    """
    scenario_dir = Path("output") / "scenarios" / event_type / scenario_id

    if not scenario_dir.exists():
        logger.warning(f"Scenario directory not found: {scenario_dir}")
        return None

    # Find .add.xml files (excluding edgeData and TAZ)
    add_xml_files = [
        f for f in scenario_dir.glob("*.add.xml")
        if f.name not in ["edgeData.add.xml", "TAZ_6.add.xml"]
        and not f.name.startswith("TAZ_")
    ]

    if not add_xml_files:
        logger.warning(f"No scenario .add.xml found in {scenario_dir}")
        return None

    # Return first match (should only be one)
    return add_xml_files[0]
```

##### `_update_case_metadata_with_simulation()`

```python
def _update_case_metadata_with_simulation(
    self,
    case_path: Path,
    scenario_id: str,
    simulation_id: str
) -> None:
    """
    Update case metadata with new simulation entry.

    Updates:
    1. Add scenario_id to scenarios list (if not already present)
    2. Add simulation entry to simulations dict

    Args:
        case_path: Path to case directory
        scenario_id: Scenario identifier
        simulation_id: Simulation identifier
    """
    metadata_file = case_path / "metadata.json"

    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Add scenario to list
    if scenario_id not in metadata.get("scenarios", []):
        metadata.setdefault("scenarios", []).append(scenario_id)

    # Add simulation entry
    metadata.setdefault("simulations", {})[simulation_id] = {
        "created_at": datetime.now().isoformat(),
        "status": "ready",
        "scenario_id": scenario_id
    }

    # Update modified timestamp
    metadata["modified_at"] = datetime.now().isoformat()

    # Save updated metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Updated case metadata with simulation {simulation_id}")
```

#### Modified Method: `create_case_with_simulation()`

```python
async def create_case_with_simulation(
    self,
    request: CreateCaseWithSimulationRequest
) -> Dict[str, Any]:
    """
    Create event-based case with scenario simulation.

    Workflow:
    1. Extract event_id from scenario_id
    2. Get or create event case (reuse if exists)
    3. If new case: Generate OD data (async)
    4. Create scenario-specific simulation
    5. Update scenario index
    6. Return response

    Args:
        request: Case creation request

    Returns:
        Response with case_id, simulation_id, status
    """
    try:
        # Step 1: Extract event_id
        event_id = self._extract_event_id_from_scenario(request.scenario_id)
        logger.info(f"Creating case for event {event_id}, scenario {request.scenario_id}")

        # Step 2: Get or create event case
        case_path, is_new_case, case_metadata = self._get_or_create_event_case(
            event_id=event_id,
            event_type=request.event_type,
            network_file=request.network_file,
            od_file=request.od_file,
            taz_file=request.taz_file,
            time_range=request.time_range,
            description=request.description
        )

        case_id = case_metadata["case_id"]

        # Step 3: If new case, set up config
        if is_new_case:
            # Copy network and TAZ files
            await self._setup_case_config_files(case_path, request)

            # Mark case as pending OD generation
            case_metadata["status"] = "od_generating"
            self._save_case_metadata(case_path, case_metadata)

            # Trigger async OD generation
            self._start_od_generation_thread(
                case_id=case_id,
                case_path=case_path,
                od_file=request.od_file,
                time_range=request.time_range
            )

            logger.info(f"✓ OD generation started for new event case")
        else:
            logger.info(f"✓ Reusing existing config (OD data already generated)")

        # Step 4: Create scenario-specific simulation
        simulation_id, sim_dir = self._create_scenario_simulation(
            case_path=case_path,
            case_metadata=case_metadata,
            request=request
        )

        # Step 5: Update case metadata
        self._update_case_metadata_with_simulation(
            case_path=case_path,
            scenario_id=request.scenario_id,
            simulation_id=simulation_id
        )

        # Step 6: Update scenario index
        self._update_scenario_index(
            scenario_id=request.scenario_id,
            case_id=case_id,
            simulation_id=simulation_id
        )

        # Step 7: Return response
        return {
            "case_id": case_id,
            "case_type": "event_based",
            "simulation_id": simulation_id,
            "simulation_path": str(sim_dir),
            "is_new_case": is_new_case,
            "od_generation_status": "in_progress" if is_new_case else "completed",
            "status": "ready",
            "message": "Case created successfully" if is_new_case else "Simulation added to existing case"
        }

    except Exception as e:
        logger.error(f"Error creating event case: {e}", exc_info=True)
        raise Exception(f"Failed to create case: {str(e)}")
```

---

### 2. Scenario Index Updater

**Location**: `shared/utilities/scenario_index_updater.py`

#### New Method: `link_scenario_to_case()`

```python
def link_scenario_to_case(
    self,
    scenario_id: str,
    case_id: str,
    simulation_id: str
) -> None:
    """
    Link scenario to case in scenario index.

    Updates scenario_index.json with case_id and simulation_id.

    Args:
        scenario_id: Scenario identifier
        case_id: Case identifier
        simulation_id: Simulation identifier
    """
    index_file = Path("output/scenarios/scenario_index.json")

    if not index_file.exists():
        logger.warning(f"Scenario index not found: {index_file}")
        return

    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    if scenario_id not in index_data:
        logger.warning(f"Scenario {scenario_id} not found in index")
        return

    # Update scenario entry
    index_data[scenario_id].update({
        "case_id": case_id,
        "simulation_id": simulation_id,
        "linked_at": datetime.now().isoformat()
    })

    # Save updated index
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Linked scenario {scenario_id} to case {case_id}")
```

---

### 3. Case Type Detection

**Location**: `api/services/case_service.py` or `shared/utilities/case_utils.py`

```python
def is_event_based_case(case_id: str) -> bool:
    """
    Check if case is event-based.

    Args:
        case_id: Case identifier

    Returns:
        True if event-based case, False otherwise

    Examples:
        >>> is_event_based_case("case_event_10814")
        True
        >>> is_event_based_case("case_20251114_170211")
        False
    """
    return case_id.startswith("case_event_")


def get_event_id_from_case(case_id: str) -> Optional[str]:
    """
    Extract event ID from event-based case ID.

    Args:
        case_id: Case identifier

    Returns:
        Event ID if event-based case, None otherwise

    Examples:
        >>> get_event_id_from_case("case_event_10814")
        '10814'
        >>> get_event_id_from_case("case_20251114_170211")
        None
    """
    if is_event_based_case(case_id):
        return case_id.replace("case_event_", "")
    return None


def get_case_type(case_id: str) -> str:
    """
    Get case type from case ID.

    Args:
        case_id: Case identifier

    Returns:
        Case type: "event_based" or "time_based"
    """
    return "event_based" if is_event_based_case(case_id) else "time_based"
```

---

## Data Flow

### Scenario 1: First Scenario from Event

```
User Action: Click "创建" for scenario_10814_vss

Frontend → Backend:
  POST /api/v1/scenario/create_case_with_simulation
  {
    "scenario_id": "scenario_10814_vss",
    "event_id": "10814",
    "event_type": "01_accident",
    ...
  }

Backend Processing:
  1. Extract event_id = "10814"
  2. case_id = "case_event_10814"
  3. Check if cases/case_event_10814/ exists → NO
  4. Create case directory structure:
     - cases/case_event_10814/
     - cases/case_event_10814/config/
     - cases/case_event_10814/simulations/
  5. Copy files to config/:
     - sichuan202508v7.net.xml
     - TAZ_6.add.xml
  6. Start OD generation (async):
     - Query database
     - Generate .rou.xml and .od.xml
     - Save to config/
  7. Create simulation directory:
     - simulations/event_simulation_scenario_10814_vss/
  8. Copy scenario .add.xml
  9. Generate simulation.sumocfg
  10. Create output directories (edgedata/, e1/)
  11. Update scenario_index.json

Backend → Frontend:
  {
    "case_id": "case_event_10814",
    "simulation_id": "event_simulation_scenario_10814_vss",
    "is_new_case": true,
    "od_generation_status": "in_progress"
  }
```

### Scenario 2: Subsequent Scenario from Same Event

```
User Action: Click "创建" for scenario_10814_tec

Frontend → Backend:
  POST /api/v1/scenario/create_case_with_simulation
  {
    "scenario_id": "scenario_10814_tec",
    "event_id": "10814",
    "event_type": "01_accident",
    ...
  }

Backend Processing:
  1. Extract event_id = "10814"
  2. case_id = "case_event_10814"
  3. Check if cases/case_event_10814/ exists → YES
  4. Check if config/ exists → YES
  5. Load existing case metadata
  6. ✅ Skip OD generation (reuse existing)
  7. ✅ Skip file copies (reuse existing)
  8. Create simulation directory:
     - simulations/event_simulation_scenario_10814_tec/
  9. Copy scenario .add.xml (TEC-specific)
  10. Generate simulation.sumocfg (references shared config)
  11. Create output directories (edgedata/, e1/)
  12. Update case metadata (add simulation entry)
  13. Update scenario_index.json

Backend → Frontend:
  {
    "case_id": "case_event_10814",
    "simulation_id": "event_simulation_scenario_10814_tec",
    "is_new_case": false,
    "od_generation_status": "completed"
  }
```

---

## API Changes

### Modified Endpoints

#### POST `/api/v1/scenario/create_case_with_simulation`

**Request** (unchanged):
```json
{
  "scenario_id": "scenario_10814_vss",
  "event_id": "10814",
  "event_type": "01_accident",
  "strategy": "vss",
  "case_name": null,
  "description": null,
  "network_file": "templates/network_files/sichuan202508v7.net.xml",
  "od_file": "dwd.dwd_od_weekly",
  "taz_file": "templates/taz_files/TAZ_6.add.xml",
  "time_range": {
    "start": "2025-06-13 15:22:37",
    "end": "2025-06-13 16:49:16"
  },
  "simulation_duration_hours": 2.5,
  "output_config": {
    "generate_edgedata": true,
    "generate_e1": true,
    "generate_summary": true,
    "generate_tripinfo": true
  }
}
```

**Response** (enhanced):
```json
{
  "case_id": "case_event_10814",
  "case_type": "event_based",
  "simulation_id": "event_simulation_scenario_10814_vss",
  "simulation_path": "cases/case_event_10814/simulations/event_simulation_scenario_10814_vss",
  "is_new_case": true,
  "od_generation_status": "in_progress",
  "status": "ready",
  "message": "Case created successfully"
}
```

**New Fields**:
- `case_type`: "event_based" or "time_based"
- `is_new_case`: Boolean indicating if case was newly created
- `od_generation_status`: "in_progress", "completed", or "failed"

---

## Database Schema

No database schema changes required. All data stored in JSON files.

---

## File System Layout

### Event-Based Case Structure

```
cases/
└── case_event_10814/                               # Event case
    ├── metadata.json                                # Event-level metadata
    ├── config/                                      # Shared config (all scenarios)
    │   ├── dwd_od_weekly_20250613152237_20250613164916.rou.xml
    │   ├── dwd_od_weekly_20250613152237_20250613164916.od.xml
    │   ├── edgeData.add.xml
    │   ├── sichuan202508v7.net.xml
    │   ├── TAZ_6.add.xml
    │   └── od_file_info.json
    └── simulations/                                 # Scenario simulations
        ├── event_simulation_scenario_10814_vss/     # VSS scenario
        │   ├── scenario_accident_vss_10814.add.xml
        │   ├── simulation.sumocfg
        │   ├── simulation_metadata.json
        │   ├── edgedata/
        │   │   └── edgedata.xml (after simulation)
        │   └── e1/
        │       └── e1_*.xml (after simulation)
        ├── event_simulation_scenario_10814_tec/     # TEC scenario
        │   ├── scenario_accident_tec_10814.add.xml
        │   ├── simulation.sumocfg
        │   ├── simulation_metadata.json
        │   ├── edgedata/
        │   └── e1/
        ├── event_simulation_scenario_10814_dhs/     # DHS scenario
        │   └── ...
        └── event_simulation_scenario_10814_no_control/  # No control baseline
            └── ...
```

### Time-Based Case Structure (Backward Compatible)

```
cases/
└── case_20251114_170211/                           # Regular case
    ├── metadata.json
    ├── config/
    │   ├── dwd_od_weekly_xxx.rou.xml
    │   ├── sichuan202508v7.net.xml
    │   └── TAZ_6.add.xml
    └── simulations/
        └── simulation_20251114_170211/
            ├── simulation.sumocfg
            ├── simulation_metadata.json
            ├── edgedata/
            └── e1/
```

---

## Backward Compatibility

### Case Type Detection

All existing code that works with cases must detect case type:

```python
def get_case_config_dir(case_id: str) -> Path:
    """Get config directory for any case type."""
    case_path = Path("cases") / case_id
    config_dir = case_path / "config"

    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    return config_dir


def list_case_simulations(case_id: str) -> List[str]:
    """List all simulations for a case (works for both types)."""
    sim_dir = Path("cases") / case_id / "simulations"

    if not sim_dir.exists():
        return []

    return [d.name for d in sim_dir.iterdir() if d.is_dir()]
```

### API Compatibility

All existing API endpoints continue to work:
- GET `/api/v1/case/{case_id}` - Works for both case types
- GET `/api/v1/case/{case_id}/simulations` - Lists all simulations
- DELETE `/api/v1/case/{case_id}` - Deletes case (all simulations)

### Frontend Compatibility

Frontend should handle both case types:

```javascript
function displayCaseInfo(caseData) {
    const caseType = caseData.case_type || 'time_based';

    if (caseType === 'event_based') {
        // Show event-specific info
        displayEventInfo(caseData.event_id);
        displayScenarioList(caseData.scenarios);
    } else {
        // Show regular case info
        displayRegularCaseInfo(caseData);
    }
}
```

---

## Error Handling

### Common Error Scenarios

#### 1. Invalid Scenario ID Format

```python
try:
    event_id = _extract_event_id_from_scenario(scenario_id)
except ValueError as e:
    return {
        "error": "INVALID_SCENARIO_ID",
        "message": f"Invalid scenario ID format: {scenario_id}",
        "details": str(e)
    }
```

#### 2. Config Directory Corruption

```python
if case_path.exists() and not (case_path / "config").exists():
    logger.error(f"Case exists but config missing: {case_id}")
    # Treat as new case and recreate config
    is_new_case = True
```

#### 3. OD Generation Failure

```python
try:
    generate_od_data(...)
except Exception as e:
    # Mark case as failed
    case_metadata["status"] = "od_generation_failed"
    case_metadata["error"] = str(e)
    save_case_metadata(case_path, case_metadata)

    # Return error to user
    return {
        "error": "OD_GENERATION_FAILED",
        "message": "Failed to generate OD data",
        "case_id": case_id,
        "details": str(e)
    }
```

#### 4. Concurrent Case Creation

```python
import fcntl  # Unix
# or
import msvcrt  # Windows

def _get_or_create_event_case_with_lock(self, event_id: str, ...):
    """Thread-safe case creation."""
    lock_file = Path("cases") / f".case_event_{event_id}.lock"

    with open(lock_file, 'w') as f:
        try:
            # Acquire exclusive lock
            if os.name == 'nt':  # Windows
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # Unix
                fcntl.flock(f, fcntl.LOCK_EX)

            # Perform case creation/retrieval
            result = self._get_or_create_event_case(event_id, ...)

            return result

        finally:
            # Release lock
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)

            # Clean up lock file
            if lock_file.exists():
                lock_file.unlink()
```

---

## Performance Considerations

### OD Generation Optimization

**Before** (4 scenarios from same event):
```
scenario_10814_vss:  OD generation (2 min) + simulation setup (10 sec)
scenario_10814_tec:  OD generation (2 min) + simulation setup (10 sec)
scenario_10814_dhs:  OD generation (2 min) + simulation setup (10 sec)
scenario_10814_no_control: OD generation (2 min) + simulation setup (10 sec)

Total: 8 minutes 40 seconds
```

**After** (4 scenarios from same event):
```
scenario_10814_vss:  OD generation (2 min) + simulation setup (10 sec)
scenario_10814_tec:  Reuse config (0 sec) + simulation setup (10 sec)
scenario_10814_dhs:  Reuse config (0 sec) + simulation setup (10 sec)
scenario_10814_no_control: Reuse config (0 sec) + simulation setup (10 sec)

Total: 2 minutes 30 seconds (71% faster)
```

### Disk Usage Optimization

**Before**:
```
case_20251114_170211/config/    500 MB
case_20251114_170842/config/    500 MB
case_20251114_171822/config/    500 MB
case_20251114_172156/config/    500 MB

Total: 2000 MB
```

**After**:
```
case_event_10814/config/                                500 MB
case_event_10814/simulations/event_simulation_scenario_10814_vss/     25 MB
case_event_10814/simulations/event_simulation_scenario_10814_tec/     25 MB
case_event_10814/simulations/event_simulation_scenario_10814_dhs/     25 MB
case_event_10814/simulations/event_simulation_scenario_10814_no_control/ 25 MB

Total: 600 MB (70% reduction)
```

---

## Security Considerations

### Path Traversal Prevention

```python
def _validate_case_id(case_id: str) -> bool:
    """Validate case ID to prevent path traversal."""
    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', case_id):
        raise ValueError(f"Invalid case_id: {case_id}")

    # Prevent path traversal
    if '..' in case_id or '/' in case_id or '\\' in case_id:
        raise ValueError(f"Invalid case_id (path traversal): {case_id}")

    return True
```

### File Permission Management

```python
def _create_case_directory(case_path: Path) -> None:
    """Create case directory with proper permissions."""
    case_path.mkdir(parents=True, exist_ok=True)

    # Set permissions (Unix-like systems)
    if os.name != 'nt':  # Not Windows
        os.chmod(case_path, 0o755)  # rwxr-xr-x
```

---

## Testing Strategy

### Unit Tests

See `proposal.md` for unit test examples.

### Integration Tests

See `proposal.md` for integration test examples.

### Performance Tests

```python
@pytest.mark.performance
def test_multiple_scenario_creation_performance():
    """Test performance improvement with event-based architecture."""
    event_id = "10814"
    scenarios = [
        "scenario_10814_vss",
        "scenario_10814_tec",
        "scenario_10814_dhs",
        "scenario_10814_no_control"
    ]

    start_time = time.time()

    for scenario_id in scenarios:
        response = create_case_with_simulation(
            scenario_id=scenario_id,
            event_id=event_id,
            ...
        )

        # Wait for OD completion only for first scenario
        if response["is_new_case"]:
            wait_for_od_completion(response["case_id"])

    total_time = time.time() - start_time

    # Assert significant improvement
    assert total_time < 180  # Should complete in < 3 minutes
    # (vs 8+ minutes with old architecture)
```

---

## Rollout Plan

### Phase 1: Implementation (Week 1-2)
- Implement event-based case logic
- Add case type detection
- Update API responses

### Phase 2: Testing (Week 3)
- Unit tests
- Integration tests
- Performance tests

### Phase 3: Deployment (Week 4)
- Deploy to staging
- User acceptance testing
- Production deployment

### Phase 4: Monitoring (Week 5+)
- Monitor performance metrics
- Track error rates
- Collect user feedback

---

**Document Status**: Complete
**Review Status**: Pending
**Implementation Status**: Not Started
