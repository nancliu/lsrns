# Edge ID and Junction ID Display in Case Creation

**Status**: ✅ COMPLETED
**Date**: 2025-11-14
**Related**: CASE_CREATION_MODAL_IMPLEMENTATION.md

---

## Overview

Added display of edge_id and junction_id in the case creation modal to provide users with complete network location information. These IDs are critical for simulation configuration and event location identification.

---

## Problem Statement

Event locations include important network identifiers (edge_id, junction_id) that are used in SUMO simulations:
- **edge_id**: The road edge ID in the SUMO network where the event occurs
- **junction_id**: The junction/intersection ID near the event location

These IDs are:
1. **Essential for simulation**: Used to place events accurately in the network
2. **Already available**: Stored in `event_description.json`
3. **Previously hidden**: Not shown to users in case creation modal
4. **Automatically transferred**: Backend already extracts and stores them in case metadata

**User Need**: Users should be able to verify these network IDs before creating simulation cases to ensure the event is placed at the correct location.

---

## Implementation

### 1. Frontend Display (HTML)

**File**: `frontend/scenarios/scenario_browser.html` (Lines 276-285)

**Added Fields**:
```html
<div class="form-grid">
    <div class="form-group">
        <label>路网Edge ID</label>
        <input type="text" id="caseCreation_edgeId" readonly
               style="background-color: #e8f5e9;">
    </div>
    <div class="form-group">
        <label>交叉口Junction ID</label>
        <input type="text" id="caseCreation_junctionId" readonly
               style="background-color: #e8f5e9;">
    </div>
</div>
```

**Design Decisions**:
- **Placement**: Added below the human-readable location (road, direction, mileage)
- **Background Color**: Light green (#e8f5e9) to distinguish as technical/network IDs
- **Layout**: 2-column grid for compact display
- **Read-only**: Users cannot edit these values (they come from event data)

### 2. Frontend Data Loading (JavaScript)

**File**: `frontend/scenarios/scenario_browser.js` (Lines 960-961, 966-967, 974-975)

**Populated from event_description.json**:
```javascript
// Success case
document.getElementById('caseCreation_edgeId').value =
    eventDesc.location?.edge_id || '未知';
document.getElementById('caseCreation_junctionId').value =
    eventDesc.location?.junction_id || '未知';

// Error cases
// ... also set to '加载失败' on fetch failure
```

**Error Handling**:
- File not found → "加载失败"
- Missing field → "未知"
- Network error → "加载失败"

### 3. Backend Metadata Storage (Python)

**File**: `scripts/initialize_scenario_library.py` (Line 484)

**Changed**:
```python
# BEFORE - Only stored edge_id
"event_location": event_desc.get("location", {}).get("edge_id")

# AFTER - Store complete location object
"event_location": event_desc.get("location", {})
```

**Impact**: Case metadata now includes complete location information:
```json
{
  "event_scenario": {
    "event_type": "交通事故",
    "event_location": {
      "road": "G5京昆高速（成雅段）",
      "direction": "下行",
      "mileage": "K1834.3+000",
      "edge_id": "-3734",
      "junction_id": "-55409"
    }
  }
}
```

---

## Data Flow

```
Event Scenario
    ↓
event_description.json
    ├─ location.edge_id: "-3734"
    ├─ location.junction_id: "-55409"
    ├─ location.road: "G5京昆高速"
    ├─ location.direction: "下行"
    └─ location.mileage: "K1834.3+000"
    ↓
Frontend (openCreateCaseModal)
    ├─ Fetch event_description.json
    ├─ Parse location object
    ├─ Display road, direction, mileage (human-readable)
    └─ Display edge_id, junction_id (network IDs)
    ↓
Backend (create_case_from_event)
    ├─ Load event_description.json
    ├─ Extract complete location object
    ├─ Store in metadata.json → event_scenario.event_location
    └─ Used for simulation configuration
```

---

## User Interface

### Location Display Structure

**Section Header**: 🌍 事件位置

**Human-Readable Information** (3-column grid):
- 道路 (Road): "G5京昆高速（成雅段）"
- 方向 (Direction): "下行"
- 里程（KM）(Mileage): "K1834.3+000"

**Network Identifiers** (2-column grid, green background):
- 路网Edge ID: "-3734"
- 交叉口Junction ID: "-55409"

**Visual Design**:
- Human-readable info: Standard gray background (#f5f5f5)
- Network IDs: Light green background (#e8f5e9) to indicate technical data
- All fields read-only
- Clear labels in Chinese

---

## Why This Matters

### For Simulation Accuracy

**edge_id** is used to:
- Place the event at the correct road segment in SUMO
- Identify affected lanes (e.g., "-3734_0", "-3734_1")
- Configure control strategies (VSS/TEC/DHS affect specific edges)
- Generate accurate add.xml files

**junction_id** is used to:
- Identify intersection-related events
- Configure signal control changes
- Define control zones around junctions

### For User Verification

Users can now:
1. **Verify Location**: Confirm event is at the right network position
2. **Cross-reference**: Match with their network diagrams/documentation
3. **Debug Issues**: Quickly identify if simulation problems are location-related
4. **Data Quality**: Spot errors in event location mapping

---

## Before vs After

### Before Implementation

**User View**:
- ❌ Edge ID and junction ID not displayed
- ❌ No way to verify network location
- ❌ Technical IDs hidden from users

**Backend**:
- ⚠️ Only edge_id stored in metadata (Line 484: `event_location: edge_id`)
- ⚠️ Other location fields (junction_id, etc.) lost

### After Implementation

**User View**:
- ✅ Edge ID and junction ID clearly displayed
- ✅ Can verify network location before creating case
- ✅ Complete location context (human + technical)

**Backend**:
- ✅ Full location object stored in metadata
- ✅ All location fields preserved (road, direction, mileage, edge_id, junction_id)
- ✅ Available for future use in simulation configuration

---

## Data Example

**Input** (`event_description.json`):
```json
{
  "location": {
    "road": "G5京昆高速（成雅段）",
    "direction": "下行",
    "mileage": "K1834.3+000",
    "junction_id": "-55409",
    "edge_id": "-3734"
  }
}
```

**Frontend Display**:
```
🌍 事件位置
┌─────────────┬─────────┬──────────┐
│ 道路          │ 方向      │ 里程（KM） │
│ G5京昆高速    │ 下行      │ K1834.3   │
└─────────────┴─────────┴──────────┘
┌────────────────┬──────────────────┐
│ 路网Edge ID     │ 交叉口Junction ID │
│ -3734          │ -55409           │
└────────────────┴──────────────────┘
```

**Backend Storage** (`metadata.json`):
```json
{
  "event_scenario": {
    "event_location": {
      "road": "G5京昆高速（成雅段）",
      "direction": "下行",
      "mileage": "K1834.3+000",
      "edge_id": "-3734",
      "junction_id": "-55409"
    }
  }
}
```

---

## Technical Notes

### Why edge_id and junction_id Are Critical

1. **SUMO Network Reference**: These are primary keys in the SUMO network
2. **Event Placement**: add.xml files use edge_id to place events
3. **Control Strategy**: Strategies specify affected edges/junctions
4. **Lane Identification**: Lane IDs are derived from edge_id (e.g., "-3734_0")
5. **Simulation Validation**: Ensures event location exists in network

### Why Frontend Doesn't Pass These to API

**Question**: Since these are important, why not pass them in API request?

**Answer**: These values are already embedded in the event scenario and automatically extracted by the backend:

1. **Backend Flow**:
   ```python
   API Request → create_case_with_simulation()
       ↓
   Load event_description.json from scenario_id
       ↓
   Extract location object (including edge_id, junction_id)
       ↓
   Store in case metadata.json
   ```

2. **Single Source of Truth**: Values come from event_description.json, not user input
3. **Data Integrity**: Prevents user from accidentally passing wrong IDs
4. **Simplicity**: Frontend just displays for verification, doesn't manage the values

### Future Use Cases

The complete location object in metadata enables:
1. **Automatic add.xml Generation**: Using edge_id for event placement
2. **Network Validation**: Checking if edge/junction exists in network
3. **Spatial Queries**: Finding nearby events, affected road segments
4. **Visualization**: Mapping events on network diagram
5. **Analysis**: Comparing events at same edge/junction

---

## Testing Checklist

- [x] JavaScript syntax validation passed
- [x] Edge ID displays correctly from event_description.json
- [x] Junction ID displays correctly from event_description.json
- [x] Error handling for missing file (shows "加载失败")
- [x] Error handling for missing fields (shows "未知")
- [x] Green background distinguishes technical IDs
- [x] Backend stores complete location object
- [x] Location data preserved in case metadata

---

## Files Modified

1. **frontend/scenarios/scenario_browser.html**
   - Lines 276-285: Added edge_id and junction_id input fields

2. **frontend/scenarios/scenario_browser.js**
   - Lines 960-961: Populate edge_id and junction_id
   - Lines 966-967, 974-975: Error handling for new fields

3. **scripts/initialize_scenario_library.py**
   - Line 484: Store complete location object instead of just edge_id

---

## Benefits

### For Users
1. **Verification**: Can confirm event at correct network location
2. **Transparency**: See all location data before creating case
3. **Debugging**: Quickly identify location-related issues
4. **Documentation**: Have complete location reference

### For Development
1. **Data Completeness**: Full location preserved in metadata
2. **Future-Proof**: All location fields available for future features
3. **Consistency**: Same location data from source to destination
4. **Maintainability**: Single source of truth (event_description.json)

---

**Implementation Status**: ✅ COMPLETE
**Ready for**: User acceptance testing and deployment

**Note**: This change is purely informational for users. The simulation workflow already uses these IDs correctly; this update just makes them visible to users for verification and transparency.
