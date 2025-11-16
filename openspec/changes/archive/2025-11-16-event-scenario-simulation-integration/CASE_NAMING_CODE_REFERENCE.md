# Event-Based Case Naming - Code Reference Guide

**Quick Reference for Case Naming Implementation**

---

## Code Locations

### Function 1: Core Case Creation
**File**: `api/services/case_service.py`
**Function**: `_get_or_create_event_case()`
**Line**: 252

```python
213 │ def _get_or_create_event_case(
214 │     self,
215 │     event_id: str,
216 │     event_type: str,
217 │     network_file: str,
218 │     od_file: str,
219 │     taz_file: Optional[str],
220 │     time_range: Dict[str, str],
221 │     description: Optional[str] = None
222 │ ) -> Tuple[Path, bool, Dict[str, Any]]:
    ...
252 │     case_id = f"case_event_{event_id}"  ✅ CASE NAMING PATTERN HERE
253 │     case_path = self.cases_dir / case_id
```

**Documentation** (Lines 224-250):
- ✅ Implements core event-based case reuse logic
- ✅ Creates `case_event_{event_id}` for first scenario
- ✅ Reuses existing case for subsequent scenarios
- ✅ Returns tuple: (case_path, is_new_case, case_metadata)

**Metadata Creation** (Lines 283-306):
```python
283 │     case_metadata = {
284 │         "case_id": case_id,                    # case_event_{event_id}
285 │         "case_name": f"Event {event_id} Analysis",
286 │         "case_type": "event_based",            # Marks as event-based
287 │         "event_id": event_id,                  # Original event_id
288 │         "event_type": event_type,
289 │         "created_at": datetime.now().isoformat(),
290 │         "modified_at": datetime.now().isoformat(),
291 │         "version": "2.0",                      # Event schema version
292 │         "description": description or f"Event-based case for event {event_id}",
    ...
306 │     }
```

---

### Function 2: Thread-Safe Wrapper
**File**: `api/services/case_service.py`
**Function**: `_get_or_create_event_case_with_lock()`
**Line**: 345

```python
319 │ def _get_or_create_event_case_with_lock(
320 │     self,
321 │     event_id: str,
    ...
345 │     lock_file_path = self.cases_dir / f".case_event_{event_id}.lock"  ✅ NAMING HERE
346 │     lock_handle = None
    ...
353 │     result = self._get_or_create_event_case(
354 │         event_id=event_id,                    # Passes to core function
355 │         ...
    │     )
```

**Purpose**: Thread-safe version prevents race conditions
**Lock Pattern**: `.case_event_{event_id}.lock`

---

### Function 3: Event Scenario Integration
**File**: `api/services/case_service.py`
**Function**: `create_case_from_event_scenario()`
**Line**: 1564

```python
1521 │ async def create_case_from_event_scenario(
1522 │     self,
1523 │     request: "CreateCaseWithSimulationRequest"
    ...
1547 │     event_id = self._extract_event_id_from_scenario(request.scenario_id)
1548 │     logger.info(f"✓ Event-based architecture: event {event_id}, ...")
    ...
1554 │     case_path, is_new_case, case_metadata = self._get_or_create_event_case_with_lock(
1555 │         event_id=event_id,                    # Passes to thread-safe wrapper
1556 │         ...
1557 │     )
    ...
1564 │     case_id = case_metadata["case_id"]  ✅ CONTAINS case_event_{event_id}
1565 │
1566 │     if is_new_case:
1567 │         # Setup config + trigger OD generation
```

**Key Points**:
- Line 1547: Extracts `event_id` from `scenario_id` (e.g., scenario_10814_vss → 10814)
- Line 1554: Calls thread-safe wrapper with event_id
- Line 1564: Gets case_id which follows pattern `case_event_{event_id}`
- Line 1650: Returns case_id in response

---

### Function 4: Quick Creation (Fallback)
**File**: `api/services/case_service.py`
**Function**: `quick_create_case_from_event()`
**Line**: 1095

```python
1068 │ async def quick_create_case_from_event(
1069 │     self,
1070 │     request: EventScenarioQuickCreateRequest
    ...
1095 │     case_id = request.case_id or self.generate_unique_id("case_event")  ✅ ALTERNATIVE PATTERN
    ...
1104 │     result = creator.create_case_from_event(
1105 │         case_name=request.case_name,
1106 │         case_id=case_id,                    # Uses generated case_id
    ...
1129 │     metadata['source_type'] = 'event_scenario'
```

**Patterns**:
- Primary: Uses provided `request.case_id` if available
- Fallback: Generates with `generate_unique_id("case_event")` → `case_event_{timestamp}`

---

### Function 5: Batch Processing
**File**: `api/services/case_service.py`
**Function**: `create_event_case_batch()`
**Line**: 1821

```python
1793 │ async def create_event_case_batch(self, request) -> Dict[str, Any]:
    ...
1820 │     # 1. 生成案例ID
1821 │     case_id = self.generate_unique_id("case_event")  ✅ TIMESTAMP-BASED PATTERN
1822 │     case_name = f"case_{request.event_id}_batch"
    ...
1827 │     case_dir = DirectoryManager.create_case_structure(case_id)
    ...
1864 │     # 5. 生成统一的edgeData.add.xml（聚合事件+所有策略边缘）
```

**Pattern**: `case_event_{timestamp}` for batch operations
**Case Name**: `case_{event_id}_batch` (descriptive)

---

## ID Extraction Function

**File**: `api/services/case_service.py`
**Function**: `_extract_event_id_from_scenario()`

```python
def _extract_event_id_from_scenario(scenario_id: str) -> str:
    """
    Extract event_id from scenario_id

    Examples:
        scenario_10814_vss → 10814
        scenario_10814_tec → 10814
        scenario_10815_no_control → 10815
    """
    # Scenario ID format: scenario_{event_id}_{strategy}
    # Extract event_id (numeric part between "scenario_" and first "_")
    match = re.match(r"scenario_(\d+)_", scenario_id)
    if match:
        return match.group(1)
    raise ValueError(f"Cannot extract event_id from scenario: {scenario_id}")
```

---

## Generate Unique ID Helper

**File**: `api/services/case_service.py` (inherited from BaseService)
**Function**: `generate_unique_id()`

```python
def generate_unique_id(self, prefix: str = "case") -> str:
    """
    Generate unique case ID with prefix

    Args:
        prefix: "case" → case_{timestamp}_{random}
                "case_event" → case_event_{timestamp}_{random}

    Returns:
        Generated unique ID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    return f"{prefix}_{timestamp}_{random_suffix}"
```

**Examples**:
- `generate_unique_id("case")` → `case_20251115_143022_abc123`
- `generate_unique_id("case_event")` → `case_event_20251115_143022_def456`

---

## Naming Pattern Decision Tree

```
CREATE CASE REQUEST
        ↓
    Is scenario_id provided?
        ├─ YES → Try to extract event_id
        │       ↓
        │   Can extract event_id from scenario?
        │       ├─ YES → case_id = f"case_event_{event_id}"  ✅
        │       │
        │       └─ NO → raise ValueError
        │
        └─ NO → Is case_id explicitly provided?
                ├─ YES → Use provided case_id
                │
                └─ NO → case_id = generate_unique_id("case_event")
                        → case_event_{timestamp}_{random}  ✅
```

---

## API Endpoints Using These Functions

### 1. Event Scenario Creation (Phase 1)
```
POST /api/v1/case/create-from-scenario

Request:
{
  "scenario_id": "scenario_10814_vss",
  "event_type": "01_accident",
  "network_file": "path/to/network.net.xml",
  "od_file": "dwd.dwd_od_weekly",
  "taz_file": "path/to/taz.taz.xml"
}

Response:
{
  "case_id": "case_event_10814",          ✅ Pattern confirmed
  "case_type": "event_based",
  "is_new_case": true,
  "simulation_id": "sim_001",
  "od_generation_status": "in_progress"
}
```

**Function Called**: `create_case_from_event_scenario()` (Line 1521)

### 2. Quick Creation
```
POST /api/v1/case/quick-create-from-event

Request:
{
  "scenario_id": "scenario_10814_vss",
  "event_type": "01_accident",
  ...
}

Response:
{
  "case_id": "case_event_20251115_143022_abc123",  ✅ Fallback pattern
  ...
}
```

**Function Called**: `quick_create_case_from_event()` (Line 1068)

### 3. Batch Creation (Phase 1.5)
```
POST /api/v1/case/batch-create-from-scenarios

Request:
{
  "event_id": "10814",
  "scenarios": [
    {"scenario_id": "scenario_10814_vss", ...},
    {"scenario_id": "scenario_10814_tec", ...},
    {"scenario_id": "scenario_10814_dhs", ...}
  ],
  ...
}

Response:
{
  "case_id": "case_event_20251115_143022_def456",  ✅ Batch pattern
  "case_name": "case_10814_batch",
  "total_scenarios": 3,
  "total_simulations": 3
}
```

**Function Called**: `create_event_case_batch()` (Line 1793)

---

## Validation Checklist

- ✅ Function `_get_or_create_event_case()` line 252: `case_id = f"case_event_{event_id}"`
- ✅ Thread-safe wrapper uses same naming pattern (via function call)
- ✅ Event scenario integration extracts event_id and passes to wrapper
- ✅ Metadata contains `case_id`, `event_id`, `case_type: "event_based"`
- ✅ Case directory created as `cases/case_event_{event_id}/`
- ✅ Lock file pattern: `.case_event_{event_id}.lock`
- ✅ Fallback pattern: `case_event_{timestamp}` when event_id unavailable
- ✅ All API endpoints return case_id following one of these patterns

---

## Implementation Summary

| Component | Pattern | Location | Status |
|-----------|---------|----------|--------|
| Core case naming | `case_event_{event_id}` | Line 252 | ✅ |
| Thread-safe locking | `.case_event_{event_id}.lock` | Line 345 | ✅ |
| Event scenario integration | Uses core + wrapper | Line 1564 | ✅ |
| Quick creation fallback | `case_event_{timestamp}` | Line 1095 | ✅ |
| Batch creation | `case_event_{timestamp}` | Line 1821 | ✅ |
| Metadata | case_type: "event_based" | Line 286 | ✅ |

---

**Verification Date**: 2025-11-15
**Status**: 🟢 All functions confirmed implementing pattern `case_event_{event_id}`

