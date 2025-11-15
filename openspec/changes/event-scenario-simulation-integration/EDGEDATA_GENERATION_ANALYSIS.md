# EdgeData Generation Analysis - Current Implementation & Improvement Opportunities

**Date**: 2025-11-15
**Status**: 🔍 **ANALYSIS IN PROGRESS**
**Focus**: How edgeData.add.xml is generated and how to intelligently configure simulation output

---

## Executive Summary

Current edgeData generation process:
1. ✅ Extracts event edge_id from case metadata
2. ✅ Validates and creates edgeData.add.xml (smart or full-network mode)
3. ✅ Adds edgeData.add.xml to simulation's additional files
4. ⚠️ **Gap**: No explicit verification that edgedata.xml output is actually generated after validation

**Key Question**: After edge_id validation and edgeData.add.xml configuration, does the system intelligently:
- Verify that edgedata.xml was actually generated?
- Configure output capture if collection was successful?
- Handle cases where edge_id validation fails?

---

## Current Implementation Flow

### Stage 1: EdgeData Configuration Generation
**Location**: `shared/utilities/sumo_utils.py:275-350`

```python
if simulation_params.get('output_edgedata', False):
    # Step 1: Extract relevant edges from event metadata
    relevant_edges = []
    collection_mode = "full_network"  # default

    # Step 2: Check if event scenario with valid edge_id
    if 'event_scenario' in case_metadata and 'event_location' in case_metadata['event_scenario']:
        edge_id = case_metadata['event_scenario']['event_location'].get('edge_id')
        if edge_id:  # ✅ Edge ID validation happens here
            relevant_edges.append(edge_id)
            # Add reverse direction edge
            if edge_id.startswith('-'):
                relevant_edges.append(edge_id[1:])
            else:
                relevant_edges.append(f"-{edge_id}")

            collection_mode = "event_edges"  # Smart mode enabled
            print(f"✓ EdgeData 智能优化: 仅收集事件相关边 {relevant_edges}")

    # Step 3: Generate edgeData.add.xml with validated edges
    if relevant_edges:
        # Smart mode: only event edges
        template_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<additional>\n'
            '  <edgeData id="ed1"\n'
            '    freq="300"\n'
            '    file="edgedata/edgedata.xml"\n'
            f'    edges="{edges_str}"\n'  # ← Only includes validated edges
            '    excludeEmpty="true"\n'
            '    withInternal="false"/>\n'
            '</additional>'
        )
    else:
        # Fallback: full network
        template_content = (... no edges attribute ...)

    # Step 4: Save edgeData.add.xml
    config_edgedata_path = case_root / "config" / "edgeData.add.xml"
    with open(config_edgedata_path, 'w', encoding='utf-8') as f:
        f.write(template_content)

    # Step 5: Copy to simulation directory
    simulation_edgedata_path = simulation_folder / "edgeData.add.xml"
    shutil.copy2(config_edgedata_path, simulation_edgedata_path)

    # Step 6: Add to additional files list
    edgedata_files.append("edgeData.add.xml")
```

**Key Points**:
- ✅ Edge ID extraction and validation happens
- ✅ Smart vs full-network decision based on edge validity
- ✅ edgeData.add.xml created with appropriate configuration
- ⚠️ **Gap 1**: No verification that SUMO will actually generate output
- ⚠️ **Gap 2**: No explicit output configuration in sumocfg file
- ⚠️ **Gap 3**: No post-simulation verification that edgedata.xml was created

### Stage 2: SUMO Configuration Generation
**Location**: `shared/utilities/sumo_utils.py:426-451`

```python
# Output configuration in sumocfg
output_lines = [
    '        <summary-output value="summary.xml"/>'
]

# Conditional outputs based on simulation_params
if simulation_params.get('output_tripinfo', False):
    output_lines.append('        <tripinfo-output value="tripinfo.xml"/>')

if simulation_params.get('output_vehroute', False):
    output_lines.append('        <vehroute-output value="vehroute.xml"/>')

# ... other outputs ...

# ⚠️ NOTE: NO edgedata-output line!
# EdgeData output is configured through edgeData.add.xml additional file
# But there's no explicit edgedata-output entry in sumocfg
```

**Current Limitation**:
- Summary.xml explicitly configured in sumocfg
- Other outputs explicitly configured in sumocfg
- **But edgedata.xml NOT explicitly configured** - relies only on edgeData.add.xml

**Why This Matters**:
- User can see in sumocfg which outputs will be generated
- Missing edgedata-output means edgedata.xml isn't listed as "expected output"
- Makes it harder to verify if EdgeData collection was supposed to happen

---

## Issues Identified

### Issue 1: No Validation of Edge IDs Against Network ❌
**Current State**: Edge IDs are extracted and included, but not validated against the actual network topology.

**Problem**: If edge_id is invalid (e.g., "边缘ID不存在于路网中: 3734"), SUMO will silently fail to collect data for that edge, and the user won't know.

**Impact**:
- EdgeData collection might produce incomplete or empty results
- User assumes data is being collected, but it's not

**Example**:
```
Edge ID 3734 configured in edgeData.add.xml
  ↓
SUMO checks network file
  ↓
Edge 3734 doesn't exist
  ↓
SUMO silently skips it
  ↓
edgedata.xml generated but with no data for edge 3734
```

### Issue 2: No Explicit Output Configuration in sumocfg ❌
**Current State**: edgedata.xml output is configured through additional file, not in sumocfg.

**Problem**:
- Other outputs (summary, tripinfo, etc.) are explicit in sumocfg
- edgedata output is implicit (only in additional file)
- Makes it harder to see all outputs at a glance

**Impact**:
- Configuration is less discoverable
- Difficult to verify what outputs are enabled
- Inconsistent with other output configuration style

### Issue 3: No Post-Generation Verification ❌
**Current State**: edgeData.add.xml is created, but no verification that SUMO will actually use it.

**Problem**:
- No check that edgedata.xml was actually created after simulation
- No validation that data collection succeeded
- Silent failures possible

**Impact**:
- User doesn't know if EdgeData was successfully collected
- Difficult to troubleshoot if collection fails

### Issue 4: No Aggregation of Multiple Edge Sources ⚠️
**Current State**: Only event edge_id is used. Control strategy edges (if any) are separate.

**Problem**:
- Event has edge_id (e.g., 3026)
- Control strategy might affect other edges (e.g., 3026, 3027, 3028)
- Only event edge is collected, other strategy edges ignored

**Impact**:
- Incomplete EdgeData collection
- Missing data for strategy-affected edges

---

## Proposed Improvements

### Improvement 1: Edge ID Validation Against Network
**Objective**: Validate edge_ids exist in network before configuring EdgeData collection.

**Implementation**:
```python
def validate_edge_ids_in_network(edge_ids: List[str], network_file: Path) -> List[str]:
    """
    Validate that edge IDs exist in the network file

    Args:
        edge_ids: List of edge IDs to validate
        network_file: Path to network.net.xml file

    Returns:
        List of valid edge IDs
    """
    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(network_file)
        root = tree.getroot()

        # Extract all edge IDs from network
        valid_edges = set()
        for edge in root.findall('.//edge'):
            valid_edges.add(edge.get('id'))

        # Filter input edge_ids to only valid ones
        validated_ids = [eid for eid in edge_ids if eid in valid_edges]

        # Log warnings for invalid edges
        invalid_ids = [eid for eid in edge_ids if eid not in valid_edges]
        if invalid_ids:
            logger.warning(f"Edge IDs not found in network: {invalid_ids}")

        return validated_ids
    except Exception as e:
        logger.error(f"Failed to validate edge IDs: {e}")
        return edge_ids  # Fallback: assume valid if can't parse
```

**Benefits**:
- ✅ Validates edges before configuration
- ✅ Catches invalid edges early
- ✅ Prevents silent collection failures

### Improvement 2: Explicit edgedata-output in sumocfg
**Objective**: Add explicit edgedata-output configuration to sumocfg when edgedata collection is enabled.

**Implementation**:
```python
# In sumocfg generation (around line 434)
if simulation_params.get('output_edgedata', False):
    output_lines.append('        <edgedata-output value="edgedata/edgedata.xml"/>')
```

**Benefits**:
- ✅ Makes EdgeData output visible in sumocfg
- ✅ Consistent with other output configuration
- ✅ Easier to understand what outputs are enabled

### Improvement 3: Post-Generation Verification
**Objective**: Verify that edgedata.xml was actually created after simulation.

**Implementation**:
```python
def verify_edgedata_generation(simulation_folder: Path) -> bool:
    """
    Verify that edgedata.xml was generated

    Args:
        simulation_folder: Path to simulation directory

    Returns:
        True if edgedata.xml exists and is valid
    """
    edgedata_path = simulation_folder / "edgedata" / "edgedata.xml"

    if not edgedata_path.exists():
        logger.warning(f"EdgeData file not generated: {edgedata_path}")
        return False

    if edgedata_path.stat().st_size == 0:
        logger.warning(f"EdgeData file is empty: {edgedata_path}")
        return False

    # Optional: Validate XML structure
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(edgedata_path)
        logger.info(f"✓ EdgeData file verified: {edgedata_path}")
        return True
    except Exception as e:
        logger.warning(f"EdgeData file is invalid XML: {e}")
        return False
```

**Benefits**:
- ✅ Detects collection failures
- ✅ Provides user feedback
- ✅ Enables post-simulation error handling

### Improvement 4: Aggregate Multiple Edge Sources
**Objective**: Collect edges from both event location and control strategies.

**Implementation**:
```python
def aggregate_relevant_edges(case_metadata: Dict, control_strategy_config: Dict) -> List[str]:
    """
    Aggregate edge IDs from multiple sources:
    1. Event location edge
    2. Control strategy affected edges

    Args:
        case_metadata: Case metadata (contains event_scenario)
        control_strategy_config: Control strategy configuration

    Returns:
        List of aggregated and deduplicated edge IDs
    """
    edges = set()

    # Source 1: Event location
    if 'event_scenario' in case_metadata:
        event_location = case_metadata['event_scenario'].get('event_location', {})
        event_edge = event_location.get('edge_id')
        if event_edge:
            edges.add(event_edge)
            # Add reverse direction
            edges.add(f"-{event_edge}" if not event_edge.startswith('-') else event_edge[1:])

    # Source 2: Control strategy affected edges
    if control_strategy_config:
        strategy_edges = control_strategy_config.get('affected_edges', [])
        for edge in strategy_edges:
            edges.add(edge)

    return list(edges)
```

**Benefits**:
- ✅ Complete EdgeData collection
- ✅ Covers all affected edges
- ✅ Better analysis coverage

---

## Implementation Priority

### Phase 1: Immediate Fixes (Critical)
1. **Edge ID Validation** - Prevent silent collection failures
2. **Explicit sumocfg Output** - Make configuration discoverable

### Phase 2: Enhanced Features (Important)
3. **Post-Generation Verification** - Detect collection issues
4. **Multiple Edge Sources** - Complete data collection

---

## Current Code Quality

| Aspect | Status | Notes |
|--------|--------|-------|
| Edge ID extraction | ✅ Good | Works correctly |
| Smart vs full-network decision | ✅ Good | Intelligent fallback |
| edgeData.add.xml generation | ✅ Good | Proper XML format |
| File copying | ✅ Good | Properly integrated |
| **Edge validation** | ❌ Missing | No network check |
| **Output configuration visibility** | ❌ Missing | Not in sumocfg |
| **Post-simulation verification** | ❌ Missing | No feedback |
| **Multiple source aggregation** | ❌ Missing | Only event edges |

---

## Questions for User

To implement optimal solution, clarification needed on:

1. **Edge ID Validation**: Should invalid edges be:
   - Silently filtered out (current approach)?
   - Generate warning (proposed)?
   - Cause case creation to fail (strict mode)?

2. **Control Strategy Integration**: Should control strategy edges be:
   - Automatically included in EdgeData collection?
   - Only if explicitly configured?
   - Never (keep separate)?

3. **Post-Generation Verification**: Should the system:
   - Just verify file exists?
   - Validate XML structure?
   - Check that data was actually collected?

4. **User Feedback**: Should failures:
   - Log to console (current)?
   - Return in API response?
   - Fail the entire simulation?

---

## Summary

**Current State**: EdgeData generation works but lacks validation and verification.

**Key Gaps**:
1. No validation of edge IDs against network
2. No explicit output configuration in sumocfg
3. No post-generation verification
4. No aggregation of multiple edge sources

**Recommended Next Step**: Implement Phase 1 improvements (validation + explicit config) before proceeding to Phase 2.

---

*Analysis Complete*: Ready for implementation discussion

