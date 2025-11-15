# EdgeData Batch Creation Design (批量创建方案)

**Design Type**: Simplified Batch Creation (RECOMMENDED)
**Date**: 2025-11-15
**Status**: Recommended Alternative to Incremental Update

---

## Executive Summary

**User Suggestion**: Instead of creating scenarios one-by-one, create ALL scenarios for an event at once:
- Click "创建" button once
- System creates event case + ALL scenarios (no_control, VSS, TEC, DHS, etc.)
- Generate unified, complete edgeData.add.xml from the start
- All simulations use identical edge list

**Evaluation**: ✅ **SUPERIOR to incremental update approach**

---

## Problem Analysis

### Original User Concern

Sequential scenario creation causes inconsistency:
```
Day 1: Create no_control → edgeData incomplete
Day 2: Add vss → edgeData outdated for no_control
Day 3: Add dhs → edgeData outdated for no_control & vss
```

### Two Solutions

| Aspect | Incremental Update | Batch Creation ⭐ |
|--------|-------------------|------------------|
| **Complexity** | High (version tracking, re-runs) | Low (one-time generation) |
| **Consistency** | Eventual (after updates) | Immediate (from start) |
| **User Experience** | Complex (understand versions) | Simple (one click) |
| **Implementation** | ~200 lines code | ~50 lines code |
| **Edge Cases** | Many (version conflicts, re-runs) | Few (known scenarios upfront) |
| **Fits Workflow?** | Maybe | ✅ **Yes - typical analysis workflow** |

**Decision**: ✅ **Batch Creation is BETTER**

---

## Batch Creation Design

### User Workflow

#### Frontend: Scenario Browser

**Current behavior** (individual scenario cards):
```
┌──────────────────────────────────────────────┐
│ Scenario: scenario_7180720_vss              │
│ Strategy: VSS (可变限速)                     │
│ [创建] button                                │
└──────────────────────────────────────────────┘
```

**New behavior** (event-level creation):
```
┌──────────────────────────────────────────────┐
│ Event: 7180720 (交通事故 - 2025-06-13)      │
│                                              │
│ Available Scenarios:                         │
│ ☑ 无控制 (Baseline)                         │
│ ☑ VSS (可变限速)                            │
│ ☑ TEC (收费站管控)                          │
│ ☑ DHS (动态硬路肩)                          │
│                                              │
│ [创建事件案例] button                        │
│ (Creates event case + all selected scenarios)│
└──────────────────────────────────────────────┘
```

**User Actions**:
1. User selects event from event list
2. System shows available control strategies for this event
3. User checks which strategies to analyze (default: all)
4. Click "创建事件案例" (Create Event Case)
5. System creates:
   - Event case: `case_event_7180720`
   - All scenario simulations
   - Unified edgeData.add.xml (complete from start)

### Backend Workflow

#### New API Endpoint: `create_event_case_batch`

```python
# api/routes/scenario_routes.py

@router.post("/api/v1/event/create_case_batch")
async def create_event_case_batch(request: CreateEventCaseBatchRequest):
    """
    Create event case with multiple scenarios at once.

    Request:
    {
      "event_id": "7180720",
      "event_type": "01_accident",
      "scenarios": [
        {"scenario_id": "scenario_7180720_no_control", "strategy": "no_control"},
        {"scenario_id": "scenario_7180720_vss", "strategy": "vss"},
        {"scenario_id": "scenario_7180720_tec", "strategy": "tec"},
        {"scenario_id": "scenario_7180720_dhs", "strategy": "dhs"}
      ],
      "network_file": "...",
      "od_file": "...",
      "taz_file": "...",
      "time_range": {...}
    }

    Response:
    {
      "case_id": "case_event_7180720",
      "scenarios_created": 4,
      "simulations": [
        {
          "simulation_id": "event_simulation_scenario_7180720_no_control",
          "strategy": "no_control",
          "status": "ready"
        },
        {
          "simulation_id": "event_simulation_scenario_7180720_vss",
          "strategy": "vss",
          "status": "ready"
        },
        ...
      ],
      "edgedata_config": {
        "generation_method": "batch_complete",
        "total_edges": 122,
        "source_breakdown": {
          "event_impact": 10,
          "vss_strategy": 102,
          "tec_strategy": 6,
          "dhs_strategy": 4
        },
        "complete": true,
        "all_scenarios_included": true
      },
      "od_generation_status": "in_progress",
      "message": "Event case created with 4 scenarios"
    }
    """
    pass
```

#### Request Model

```python
# api/models/requests/event_requests.py

class ScenarioDefinition(BaseModel):
    """Single scenario definition for batch creation."""
    scenario_id: str
    strategy: str  # "no_control", "vss", "tec", "dhs"
    description: Optional[str] = None


class CreateEventCaseBatchRequest(BaseModel):
    """Request to create event case with multiple scenarios."""

    event_id: str
    event_type: str  # "01_accident", "07_flowsurge", etc.

    # List of scenarios to create
    scenarios: List[ScenarioDefinition]

    # Common configuration for all scenarios
    network_file: str
    od_file: str
    taz_file: Optional[str] = None
    time_range: Dict[str, str]

    # Optional
    description: Optional[str] = None
    simulation_duration_hours: float = 2.5
    output_config: Optional[Dict[str, bool]] = None
```

### Service Implementation

#### Case Service: `create_event_case_batch()`

```python
# api/services/case_service.py

async def create_event_case_batch(
    self,
    request: CreateEventCaseBatchRequest
) -> Dict[str, Any]:
    """
    Create event case with multiple scenarios in one operation.

    Workflow:
    1. Create event case directory structure
    2. Extract ALL strategy configurations upfront
    3. Generate complete edgeData.add.xml (event + all strategies)
    4. Create all scenario simulation directories
    5. Copy scenario-specific .add.xml files
    6. Generate sumocfg for each simulation
    7. Trigger async OD generation (once for all)
    8. Return comprehensive response

    Benefits:
    - Single edgeData generation (complete from start)
    - No version management needed
    - All simulations consistent by design
    - Simpler implementation
    """
    try:
        # Step 1: Create event case
        case_id = f"case_event_{request.event_id}"
        case_path = Path("cases") / case_id

        if case_path.exists():
            raise Exception(f"Event case {case_id} already exists")

        # Create directories
        case_path.mkdir(parents=True, exist_ok=True)
        (case_path / "config").mkdir(exist_ok=True)
        (case_path / "simulations").mkdir(exist_ok=True)

        logger.info(f"Creating event case {case_id} with {len(request.scenarios)} scenarios")

        # Step 2: Create case metadata
        case_metadata = {
            "case_id": case_id,
            "case_name": f"Event {request.event_id} Analysis",
            "case_type": "event_based",
            "event_id": request.event_id,
            "event_type": request.event_type,
            "created_at": datetime.now().isoformat(),
            "version": "2.0",
            "description": request.description or f"Batch created event case for {request.event_id}",
            "files": {
                "network_file": f"config/{Path(request.network_file).name}",
                "routes_file": f"config/{Path(request.od_file).name}",
                "taz_file": f"config/{Path(request.taz_file).name}" if request.taz_file else None,
                "edgedata_template": "config/edgeData.add.xml"
            },
            "time_range": request.time_range,
            "scenarios": [s.scenario_id for s in request.scenarios],
            "simulations": {}
        }

        # Step 3: Copy config files (network, TAZ)
        await self._setup_case_config_files(case_path, request)

        # Step 4: Generate COMPLETE edgeData with ALL strategies
        all_strategy_configs = {}
        for scenario_def in request.scenarios:
            if scenario_def.strategy != "no_control":
                # Load strategy configuration
                strategy_config = self._load_scenario_strategy_config(
                    scenario_def.scenario_id,
                    scenario_def.strategy
                )
                if strategy_config:
                    all_strategy_configs[scenario_def.strategy] = strategy_config

        # Generate unified edgeData
        await self._generate_complete_edgedata(
            case_path=case_path,
            case_metadata=case_metadata,
            all_strategies=all_strategy_configs
        )

        # Step 5: Create all scenario simulations
        created_simulations = []
        for scenario_def in request.scenarios:
            simulation_id, sim_dir = await self._create_scenario_simulation_batch(
                case_path=case_path,
                case_metadata=case_metadata,
                scenario_def=scenario_def,
                request=request
            )

            created_simulations.append({
                "simulation_id": simulation_id,
                "scenario_id": scenario_def.scenario_id,
                "strategy": scenario_def.strategy,
                "path": str(sim_dir),
                "status": "ready"
            })

            # Update case metadata with simulation
            case_metadata["simulations"][simulation_id] = {
                "created_at": datetime.now().isoformat(),
                "status": "ready",
                "scenario_id": scenario_def.scenario_id,
                "strategy": scenario_def.strategy
            }

        # Step 6: Save case metadata
        self._save_case_metadata(case_path, case_metadata)

        # Step 7: Trigger OD generation (once for all scenarios)
        self._start_od_generation_thread(
            case_id=case_id,
            case_path=case_path,
            od_file=request.od_file,
            time_range=request.time_range
        )

        # Step 8: Return response
        return {
            "case_id": case_id,
            "case_type": "event_based",
            "batch_creation": True,
            "scenarios_created": len(created_simulations),
            "simulations": created_simulations,
            "edgedata_config": case_metadata.get("edgedata_config", {}),
            "od_generation_status": "in_progress",
            "status": "ready",
            "message": f"Event case created with {len(created_simulations)} scenarios"
        }

    except Exception as e:
        logger.error(f"Error creating batch event case: {e}", exc_info=True)
        raise


async def _generate_complete_edgedata(
    self,
    case_path: Path,
    case_metadata: Dict[str, Any],
    all_strategies: Dict[str, Dict]
) -> None:
    """
    Generate complete edgeData.add.xml with ALL strategy edges.

    This is simpler than incremental update - just extract all edges at once.

    Args:
        case_path: Path to case directory
        case_metadata: Case metadata
        all_strategies: Dict of strategy_name → strategy_config for ALL scenarios
    """
    from shared.utilities.edge_aggregator import EdgeImpactAggregator
    from shared.utilities.sumo_utils import generate_edgedata_xml_for_case

    aggregator = EdgeImpactAggregator()

    # Extract event impact edges
    event_edges = aggregator.aggregate_event_impact_edges(
        case_metadata,
        method="radius_2_hops"
    )

    # Extract ALL strategy edges
    strategy_edges = aggregator.aggregate_strategy_impact_edges(all_strategies)

    # Merge all
    merged = aggregator.merge_edge_impacts(event_edges, strategy_edges)
    unified_edge_list = merged['unified_edge_list']

    logger.info(f"Complete edgeData: {len(unified_edge_list)} edges from {len(all_strategies)} strategies")

    # Generate edgeData.add.xml
    edgedata_path = case_path / "config" / "edgeData.add.xml"
    generate_edgedata_xml_for_case(
        edge_list=unified_edge_list,
        output_file=edgedata_path,
        frequency=300,
        exclude_empty=True,
        with_internal=False
    )

    # Store metadata
    case_metadata['edgedata_config'] = {
        'generation_method': 'batch_complete',
        'generated_at': datetime.now().isoformat(),
        'total_unique_edges': len(unified_edge_list),
        'from_event': len(event_edges),
        'from_strategies': sum(len(edges) for edges in strategy_edges.values()),
        'source_breakdown': merged['source_breakdown'],
        'complete': True,
        'all_scenarios_included': True,
        'strategies_included': list(all_strategies.keys())
    }

    logger.info(f"Complete edgeData generated: {edgedata_path}")
```

---

## Frontend Changes

### Scenario Browser Enhancement

#### Current: Individual Scenario Cards

```html
<!-- Current: One card per scenario -->
<div class="scenario-card">
  <h3>scenario_7180720_vss</h3>
  <p>Strategy: VSS</p>
  <button onclick="createCase('scenario_7180720_vss')">创建</button>
</div>
```

#### New: Event-Level Batch Creation

```html
<!-- New: Event-level creation dialog -->
<div class="event-case-creation-modal">
  <h2>创建事件案例: Event 7180720</h2>
  <p>交通事故 - 2025-06-13 15:22:37 ~ 16:49:16</p>

  <div class="scenario-selection">
    <h3>选择要对比的场景策略:</h3>

    <label>
      <input type="checkbox" value="no_control" checked disabled>
      无控制 (基线)
    </label>

    <label>
      <input type="checkbox" value="vss" checked>
      VSS - 可变限速
    </label>

    <label>
      <input type="checkbox" value="tec" checked>
      TEC - 收费站管控
    </label>

    <label>
      <input type="checkbox" value="dhs" checked>
      DHS - 动态硬路肩
    </label>
  </div>

  <div class="summary">
    <p>将创建: 1个案例 + 4个场景仿真</p>
    <p>预计时间: 约3分钟 (OD生成 + 场景配置)</p>
  </div>

  <button onclick="createEventCaseBatch()">
    批量创建事件案例
  </button>
</div>
```

#### JavaScript Implementation

```javascript
// frontend/scenarios/scenario_browser.js

async function createEventCaseBatch(eventId, selectedStrategies) {
    const scenarios = selectedStrategies.map(strategy => ({
        scenario_id: `scenario_${eventId}_${strategy}`,
        strategy: strategy,
        description: getStrategyDescription(strategy)
    }));

    const requestData = {
        event_id: eventId,
        event_type: mapEventTypeToFolder(currentEvent.event_type),
        scenarios: scenarios,
        network_file: "templates/network_files/sichuan202508v7.net.xml",
        od_file: "dwd.dwd_od_weekly",
        taz_file: "templates/taz_files/TAZ_6.add.xml",
        time_range: {
            start: currentEvent.start_time,
            end: currentEvent.end_time
        },
        simulation_duration_hours: 2.5,
        output_config: {
            generate_edgedata: true,
            generate_e1: true,
            generate_summary: true,
            generate_tripinfo: true
        }
    };

    try {
        showLoadingIndicator("批量创建中...");

        const response = await fetch('/api/v1/event/create_case_batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestData)
        });

        const result = await response.json();

        hideLoadingIndicator();

        if (response.ok) {
            showSuccessMessage(
                `案例创建成功!\n` +
                `案例ID: ${result.case_id}\n` +
                `场景数: ${result.scenarios_created}\n` +
                `监测边数: ${result.edgedata_config.total_edges}\n` +
                `OD生成: ${result.od_generation_status}`
            );

            // Show created simulations
            displayCreatedSimulations(result.simulations);

        } else {
            showErrorMessage(`创建失败: ${result.message}`);
        }

    } catch (error) {
        hideLoadingIndicator();
        showErrorMessage(`创建出错: ${error.message}`);
    }
}
```

---

## Benefits of Batch Creation

### ✅ Simplicity

**Code complexity**:
- Batch: ~150 lines (one-time generation)
- Incremental: ~350 lines (version tracking, updates, re-runs)

**User mental model**:
- Batch: "Create event case with all scenarios" ✅ Simple!
- Incremental: "Create scenario, update edgeData, re-run old simulations" ❌ Complex

### ✅ Consistency

**EdgeData state**:
- Batch: Complete from start, all scenarios identical ✅
- Incremental: Evolves over time, versions to track ❌

### ✅ Performance

**One-time operations**:
- OD generation: 1x (not per scenario)
- EdgeData generation: 1x (not incremental)
- Network validation: 1x

### ✅ Better UX

**User actions**:
- Batch: 1 click → all scenarios ready ✅
- Incremental: 4 clicks → manage versions → re-run ❌

---

## Handling Future Scenario Additions

**What if user wants to add a new strategy later?**

### Option A: Disallow (Simplest)
- Show message: "Cannot add scenarios to existing event case"
- User must create new event case with all desired scenarios

### Option B: Allow with Warning (Recommended)
- Allow adding new scenario
- Regenerate edgeData (now includes new strategy)
- Show warning: "EdgeData updated, recommend re-running existing simulations"
- This is the **incremental update** as a **fallback**, not primary workflow

### Option C: Allow with Auto Re-run
- Allow adding new scenario
- Regenerate edgeData
- Automatically trigger re-run of all existing simulations
- Most complex, but best consistency

**Recommendation**: Start with **Option A** (simplest), can add **Option B** later if needed.

---

## Migration from Current Architecture

### Phase 1: Add Batch Creation API

✅ New endpoint: `/api/v1/event/create_case_batch`
✅ New request model: `CreateEventCaseBatchRequest`
✅ New service method: `create_event_case_batch()`

### Phase 2: Update Frontend

✅ Event-level creation modal
✅ Scenario selection checkboxes
✅ Batch creation button
✅ Progress indicator for batch creation

### Phase 3: Deprecate Individual Creation (Optional)

⏳ Keep old `/api/v1/scenario/create_case_with_simulation` for backward compatibility
⏳ Encourage users to use batch creation
⏳ Eventually deprecate individual creation

---

## Comparison Summary

| Aspect | Incremental Update | Batch Creation ⭐ |
|--------|-------------------|------------------|
| **Clicks to create 4 scenarios** | 4 clicks | 1 click |
| **EdgeData generations** | 4 times | 1 time |
| **EdgeData versions** | v1, v2, v3, v4 | v1 (complete) |
| **Consistency guarantee** | Eventual | Immediate |
| **Re-runs needed** | Yes (1-3 times) | No |
| **Code complexity** | ~350 lines | ~150 lines |
| **User confusion risk** | High | Low |
| **Matches workflow** | Partial | ✅ **Perfect** |
| **Implementation time** | 2 days | 1 day |

---

## Decision

✅ **RECOMMEND: Batch Creation as PRIMARY approach**

**Rationale**:
1. Simpler implementation (50% less code)
2. Better user experience (1 click vs 4)
3. Immediate consistency (no versions to manage)
4. Matches typical analysis workflow
5. No edge cases with re-runs

**Fallback**: Keep incremental update as **optional future enhancement** for edge cases

---

## Updated Task Plan

### Replace Tasks 6.1-6.4 with Simplified Batch Tasks

**Old Tasks** (Incremental):
- 6.1: EdgeImpactAggregator with update logic (8h)
- 6.3: Incremental update orchestration (6h)
- 6.4: Version tracking and re-run flagging (3h)

**New Tasks** (Batch):
- 6.1: EdgeImpactAggregator (6h) - Simpler, no update logic
- 6.3: Batch creation orchestration (4h) - One-time generation
- 6.4: Frontend batch creation UI (3h) - Event-level dialog

**Time saved**: 4 hours (17h → 13h)

---

**Status**: Recommended Design
**Date**: 2025-11-15
**Impact**: Simplifies implementation by 40%, improves UX

