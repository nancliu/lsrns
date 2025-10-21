# Data Model: Database-Driven Edge Selector

**Feature**: Database-Driven Edge Selector (Phase 1B)
**Date**: 2025-10-20
**Phase**: Phase 1 - Design

---

## 1. Overview

This document defines the data models for the edge selector feature, including:
- Request models (filter parameters)
- Response models (edge information)
- Entity models (domain objects)
- Extension models for special scenarios (TEC, DHS)

**Architecture Layer**: These models exist in **both layers**:
- **Shared Layer**: EdgeInfo dataclass (existing, unchanged)
- **API Layer**: Pydantic models for request/response validation (new)

---

## 2. Shared Layer Models (Existing - No Changes)

### 2.1 EdgeInfo (Dataclass)

**Location**: `shared/data_access/edge_query.py:16-49`

**Status**: ✅ **Existing - No modifications required**

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class EdgeInfo:
    """路段信息 (Road Edge Information)"""
    edge_id: str                       # SUMO edge ID
    route_code: str                    # Route code (e.g., G4202, SA2)
    section_code: Optional[str]        # Section code (e.g., G4202001)
    start_stake: Optional[float]       # Start stake number (km)
    end_stake: Optional[float]         # End stake number (km)
    length: Optional[float]            # Length (meters)
    num_lanes: Optional[int]           # Number of lanes
    route_direction: Optional[str]     # Direction (clockwise/counterclockwise)
    node_type: Optional[str]           # Associated node type (diverging/merging/entrance/exit)
    gantry_count: int = 0              # Number of gantries on this edge
    gantry_ids: List[str] = None       # List of gantry IDs

    def __post_init__(self):
        if self.gantry_ids is None:
            self.gantry_ids = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "edge_id": self.edge_id,
            "route_code": self.route_code,
            "section_code": self.section_code,
            "start_stake": self.start_stake,
            "end_stake": self.end_stake,
            "length": self.length,
            "num_lanes": self.num_lanes,
            "route_direction": self.route_direction,
            "node_type": self.node_type,
            "gantry_count": self.gantry_count,
            "gantry_ids": self.gantry_ids
        }
```

**Validation Rules**:
- edge_id: Required, non-empty string
- route_code: Required, non-empty string
- section_code: Optional (some edges may not have section assignment)
- start_stake, end_stake: Optional floats, start_stake ≤ end_stake when both present
- length: Optional float, must be > 0 when present
- num_lanes: Optional int, must be ≥ 1 when present
- route_direction: Optional, values: "clockwise", "counterclockwise", or null
- node_type: Optional, values: "diverging", "merging", "entrance", "exit", or null
- gantry_count: Non-negative integer (0 means no gantries)
- gantry_ids: List of strings (empty list when gantry_count = 0)

**State Transitions**: N/A (immutable data object)

**Relationships**:
- EdgeInfo → Route (many-to-one via route_code)
- EdgeInfo → Section (many-to-one via section_code)
- EdgeInfo → NodeUnit (many-to-one via node_type from from_junction)
- EdgeInfo → Gantry (one-to-many via gantry_ids)

---

## 3. API Layer Models (New - Pydantic)

### 3.1 EdgeQueryRequest (Request Model)

**Location**: `api/models/requests/edge_query_request.py` (NEW FILE)

**Purpose**: Validate and parse query parameters for edge filtering API

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class EdgeQueryRequest(BaseModel):
    """
    Edge filtering request parameters

    All fields are optional - empty request returns all edges
    """
    route_codes: Optional[str] = Field(
        None,
        description="Comma-separated route codes (e.g., 'G4202,SA2')"
    )
    section_codes: Optional[str] = Field(
        None,
        description="Comma-separated section codes (e.g., 'G4202001,G4202002')"
    )
    node_types: Optional[str] = Field(
        None,
        description="Comma-separated node types (diverging,merging,entrance,exit)"
    )
    min_stake: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum stake number in kilometers (≥0)"
    )
    max_stake: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum stake number in kilometers (≥0)"
    )
    min_length: Optional[float] = Field(
        None,
        gt=0,
        description="Minimum edge length in meters (>0)"
    )
    max_length: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum edge length in meters (>0)"
    )
    route_direction: Optional[str] = Field(
        None,
        description="Route direction: 'clockwise' or 'counterclockwise'"
    )
    demonstration_ids: Optional[str] = Field(
        None,
        description="Comma-separated demonstration IDs (e.g., '5,7')"
    )
    min_lanes: Optional[int] = Field(
        None,
        ge=1,
        description="Minimum number of lanes (≥1)"
    )
    with_gantry: bool = Field(
        False,
        description="If true, return only edges with at least one gantry"
    )

    @validator('max_stake')
    def validate_stake_range(cls, v, values):
        """Ensure max_stake >= min_stake when both are provided"""
        if v is not None and 'min_stake' in values and values['min_stake'] is not None:
            if v < values['min_stake']:
                raise ValueError('max_stake must be >= min_stake')
        return v

    @validator('max_length')
    def validate_length_range(cls, v, values):
        """Ensure max_length >= min_length when both are provided"""
        if v is not None and 'min_length' in values and values['min_length'] is not None:
            if v < values['min_length']:
                raise ValueError('max_length must be >= min_length')
        return v

    @validator('route_direction')
    def validate_direction(cls, v):
        """Validate route direction values"""
        if v is not None and v not in ['clockwise', 'counterclockwise']:
            raise ValueError('route_direction must be "clockwise" or "counterclockwise"')
        return v

    @validator('node_types')
    def validate_node_types(cls, v):
        """Validate node type values"""
        if v is not None:
            valid_types = {'diverging', 'merging', 'entrance', 'exit'}
            types = [t.strip() for t in v.split(',')]
            invalid = [t for t in types if t not in valid_types]
            if invalid:
                raise ValueError(f'Invalid node types: {invalid}. Must be one of: {valid_types}')
        return v

    def to_query_params(self) -> dict:
        """
        Convert request model to query function parameters

        Splits comma-separated strings into lists
        """
        return {
            'route_codes': self.route_codes.split(',') if self.route_codes else None,
            'section_codes': self.section_codes.split(',') if self.section_codes else None,
            'node_types': self.node_types.split(',') if self.node_types else None,
            'min_stake': self.min_stake,
            'max_stake': self.max_stake,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'route_direction': self.route_direction,
            'demonstration_ids': [int(d) for d in self.demonstration_ids.split(',')] if self.demonstration_ids else None,
            'min_lanes': self.min_lanes,
            'with_gantry': self.with_gantry
        }

    class Config:
        schema_extra = {
            "example": {
                "route_codes": "G4202",
                "section_codes": "G4202001",
                "min_stake": 10.0,
                "max_stake": 50.0,
                "min_length": 500,
                "max_length": 2000,
                "min_lanes": 3,
                "route_direction": "clockwise",
                "with_gantry": True
            }
        }
```

**Validation Rules**:
- Comma-separated strings validated and split into lists
- Numeric ranges validated (min ≤ max)
- Enum values validated (route_direction, node_types)
- Non-negative constraints on stake numbers
- Positive constraints on length values

### 3.2 EdgeInfoResponse (Response Model)

**Location**: `api/models/responses/edge_query_response.py` (NEW FILE)

**Purpose**: Serialize EdgeInfo dataclass to JSON with validation

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class EdgeInfoResponse(BaseModel):
    """
    Single edge information (response format)

    Corresponds to shared.data_access.edge_query.EdgeInfo dataclass
    """
    edge_id: str = Field(..., description="SUMO edge ID")
    route_code: str = Field(..., description="Route code (e.g., G4202)")
    section_code: Optional[str] = Field(None, description="Section code (e.g., G4202001)")
    start_stake: Optional[float] = Field(None, description="Start stake (km)")
    end_stake: Optional[float] = Field(None, description="End stake (km)")
    length: Optional[float] = Field(None, description="Length (meters)")
    num_lanes: Optional[int] = Field(None, description="Number of lanes")
    route_direction: Optional[str] = Field(None, description="Direction (clockwise/counterclockwise)")
    node_type: Optional[str] = Field(None, description="Node type (diverging/merging/entrance/exit)")
    gantry_count: int = Field(0, description="Number of gantries")
    gantry_ids: List[str] = Field(default_factory=list, description="List of gantry IDs")

    @classmethod
    def from_edge_info(cls, edge_info) -> "EdgeInfoResponse":
        """Create from EdgeInfo dataclass"""
        return cls(
            edge_id=edge_info.edge_id,
            route_code=edge_info.route_code,
            section_code=edge_info.section_code,
            start_stake=edge_info.start_stake,
            end_stake=edge_info.end_stake,
            length=edge_info.length,
            num_lanes=edge_info.num_lanes,
            route_direction=edge_info.route_direction,
            node_type=edge_info.node_type,
            gantry_count=edge_info.gantry_count,
            gantry_ids=edge_info.gantry_ids
        )

    class Config:
        schema_extra = {
            "example": {
                "edge_id": "-5880",
                "route_code": "SA2",
                "section_code": "SA002002",
                "start_stake": 139.2,
                "end_stake": 140.6,
                "length": 1328.0,
                "num_lanes": 3,
                "route_direction": "counterclockwise",
                "node_type": "diverging",
                "gantry_count": 3,
                "gantry_ids": ["G001", "G002", "G003"]
            }
        }
```

### 3.3 EdgeQueryResponse (Collection Response)

**Location**: `api/models/responses/edge_query_response.py` (NEW FILE)

**Purpose**: Wrap list of edges with metadata (total count, warnings)

```python
class EdgeQueryResponse(BaseModel):
    """
    Edge query response with metadata
    """
    edges: List[EdgeInfoResponse] = Field(..., description="List of edges matching filters")
    total_count: int = Field(..., description="Total number of edges found")
    warning: Optional[str] = Field(
        None,
        description="Warning message (e.g., too many results, suggest refinement)"
    )

    @classmethod
    def from_edge_infos(cls, edge_infos: List) -> "EdgeQueryResponse":
        """
        Create response from list of EdgeInfo dataclasses

        Automatically adds warnings based on result count
        """
        total_count = len(edge_infos)
        edges = [EdgeInfoResponse.from_edge_info(e) for e in edge_infos]

        warning = None
        if total_count > 100:
            warning = f"Too many results ({total_count}), please add more filters to narrow down selection."
        elif total_count > 50:
            warning = f"Large result set ({total_count}), consider adding more filters for better precision."

        return cls(
            edges=edges,
            total_count=total_count,
            warning=warning
        )

    class Config:
        schema_extra = {
            "example": {
                "edges": [
                    {
                        "edge_id": "-5880",
                        "route_code": "SA2",
                        "section_code": "SA002002",
                        "start_stake": 139.2,
                        "end_stake": 140.6,
                        "length": 1328.0,
                        "num_lanes": 3,
                        "route_direction": "counterclockwise",
                        "node_type": "diverging",
                        "gantry_count": 3,
                        "gantry_ids": ["G001", "G002", "G003"]
                    }
                ],
                "total_count": 1,
                "warning": null
            }
        }
```

### 3.4 Metadata Response Models

**Location**: `api/models/responses/edge_query_response.py` (NEW FILE)

```python
class RouteInfo(BaseModel):
    """Route metadata"""
    route_code: str = Field(..., description="Route code")
    edge_count: int = Field(..., description="Number of edges on this route")

class SectionInfo(BaseModel):
    """Section metadata"""
    section_code: str = Field(..., description="Section code")
    route_code: str = Field(..., description="Parent route code")
    edge_count: int = Field(..., description="Number of edges in this section")
    min_stake: Optional[float] = Field(None, description="Minimum stake (km)")
    max_stake: Optional[float] = Field(None, description="Maximum stake (km)")
    stake_range: str = Field(..., description="Stake range display (e.g., 'K10.0-K50.0')")

class DemonstrationInfo(BaseModel):
    """Demonstration area metadata"""
    demonstration_id: int = Field(..., description="Demonstration area ID")
    route_code: str = Field(..., description="Route code")
    edge_count: int = Field(..., description="Number of edges in demonstration area")
    stake_range: str = Field(..., description="Stake range display (e.g., '1.17-85.68km')")
```

---

## 4. Extension Models (Phase 1B - Optional Scenarios)

### 4.1 EdgeInfoWithLanes (DHS Scenario - P3)

**Location**: `shared/data_access/edge_query.py` (Extension - NOT in Phase 1B scope)

**Purpose**: Extended edge information including emergency lane data for DHS

**Status**: 📋 **Future enhancement** (Phase 1B P3 - optional)

```python
@dataclass
class EdgeInfoWithLanes(EdgeInfo):
    """
    Extended edge information with lane-level details

    Used for DHS (Dynamic Hard Shoulder) scenarios
    """
    emergency_lane_count: int = 0                   # Number of emergency lanes
    emergency_lane_indexes: List[int] = None        # Lane indexes with disallow="all"
    total_lanes: int = 0                            # Total lanes including emergency

    def __post_init__(self):
        super().__post_init__()
        if self.emergency_lane_indexes is None:
            self.emergency_lane_indexes = []

    def has_emergency_lane(self) -> bool:
        """Check if edge has at least one emergency lane"""
        return self.emergency_lane_count > 0
```

**Validation Rules**:
- Inherits all EdgeInfo validation rules
- emergency_lane_count: Non-negative integer, ≤ total_lanes
- emergency_lane_indexes: List of non-negative integers, length must equal emergency_lane_count
- total_lanes: Positive integer when present, ≥ num_lanes (num_lanes is regular lanes only)

---

## 5. Data Flow Diagram

```
┌─────────────────┐
│  Frontend UI    │
│ (JavaScript)    │
└────────┬────────┘
         │ HTTP GET /api/v1/control/edges/query?route_codes=G4202&min_lanes=3
         ↓
┌─────────────────────────────────────────────────────────┐
│ API Layer: control_routes.py                           │
│                                                         │
│ 1. Parse query string → EdgeQueryRequest (Pydantic)    │
│ 2. Validate parameters → Return 400 if invalid         │
│ 3. Convert to query params → to_query_params()         │
└────────┬────────────────────────────────────────────────┘
         │ route_codes=['G4202'], min_lanes=3
         ↓
┌─────────────────────────────────────────────────────────┐
│ API Layer: control_strategy_service.py                 │
│                                                         │
│ 1. Call shared layer query function                    │
│ 2. Handle errors + retry logic                         │
│ 3. Log performance metrics                             │
└────────┬────────────────────────────────────────────────┘
         │ query_edges_with_filters(route_codes=['G4202'], min_lanes=3)
         ↓
┌─────────────────────────────────────────────────────────┐
│ Shared Layer: edge_query.py                            │
│                                                         │
│ 1. Build SQL query with WHERE clauses                  │
│ 2. Execute parameterized query                         │
│ 3. Fetch results from PostgreSQL                       │
│ 4. Convert rows → EdgeInfo dataclass objects           │
└────────┬────────────────────────────────────────────────┘
         │ [EdgeInfo, EdgeInfo, ...]
         ↓
┌─────────────────────────────────────────────────────────┐
│ API Layer: control_routes.py                           │
│                                                         │
│ 1. Convert EdgeInfo → EdgeInfoResponse (Pydantic)      │
│ 2. Wrap in EdgeQueryResponse                           │
│ 3. Add warnings if total_count > 50                    │
│ 4. Return JSON response                                │
└────────┬────────────────────────────────────────────────┘
         │ EdgeQueryResponse JSON
         ↓
┌─────────────────┐
│  Frontend UI    │
│  Display table  │
└─────────────────┘
```

---

## 6. Error States and Validation

### 6.1 Input Validation Errors (400 Bad Request)

| Error Scenario | Validation | Response Message |
|----------------|------------|------------------|
| max_stake < min_stake | Pydantic validator | "max_stake must be >= min_stake" |
| max_length < min_length | Pydantic validator | "max_length must be >= min_length" |
| Invalid route_direction | Pydantic validator | 'route_direction must be "clockwise" or "counterclockwise"' |
| Invalid node_type | Pydantic validator | "Invalid node types: [X]. Must be one of: {diverging, merging, entrance, exit}" |
| min_stake < 0 | Pydantic Field(ge=0) | "ensure this value is greater than or equal to 0" |
| min_length ≤ 0 | Pydantic Field(gt=0) | "ensure this value is greater than 0" |
| min_lanes < 1 | Pydantic Field(ge=1) | "ensure this value is greater than or equal to 1" |

### 6.2 Database Query Errors (500 Internal Server Error)

| Error Scenario | Handling | Response |
|----------------|----------|----------|
| Connection timeout | Retry with exponential backoff | Retry once after 500ms, then 503 Service Unavailable |
| Connection refused | Retry with exponential backoff | Retry once after 500ms, then 503 Service Unavailable |
| Authentication failure | No retry | 500 Internal Server Error (logged, not retried) |
| SQL syntax error | No retry | 500 Internal Server Error (logged, not retried) |
| Unexpected exception | No retry | 500 Internal Server Error (logged) |

### 6.3 Business Logic Warnings (200 OK with warning field)

| Scenario | Condition | Warning Message |
|----------|-----------|-----------------|
| Too many results | total_count > 100 | "Too many results (X), please add more filters to narrow down selection." |
| Large result set | total_count > 50 | "Large result set (X), consider adding more filters for better precision." |
| No results | total_count == 0 | null (no warning, empty results are valid) |

---

## 7. Model Summary Table

| Model Name | Layer | Type | Location | Status | Purpose |
|------------|-------|------|----------|--------|---------|
| EdgeInfo | Shared | Dataclass | shared/data_access/edge_query.py | ✅ Existing | Core edge data (from database) |
| EdgeQueryRequest | API | Pydantic | api/models/requests/edge_query_request.py | 🔨 New | Validate query parameters |
| EdgeInfoResponse | API | Pydantic | api/models/responses/edge_query_response.py | 🔨 New | Serialize single edge to JSON |
| EdgeQueryResponse | API | Pydantic | api/models/responses/edge_query_response.py | 🔨 New | Wrap edge list with metadata |
| RouteInfo | API | Pydantic | api/models/responses/edge_query_response.py | 🔨 New | Route metadata response |
| SectionInfo | API | Pydantic | api/models/responses/edge_query_response.py | 🔨 New | Section metadata response |
| DemonstrationInfo | API | Pydantic | api/models/responses/edge_query_response.py | 🔨 New | Demonstration metadata response |
| EdgeInfoWithLanes | Shared | Dataclass | shared/data_access/edge_query.py | 📋 Future | Extended edge data for DHS (P3) |

---

## 8. Schema Evolution Strategy

### 8.1 Backward Compatibility

**Principle**: Never remove or rename existing fields in response models

**Adding New Fields**:
1. Add as optional fields with default values
2. Update OpenAPI schema documentation
3. Increment API version if breaking change required (e.g., /api/v2/)

**Example - Adding emergency lane support**:
```python
# Backward-compatible addition to EdgeInfoResponse
class EdgeInfoResponse(BaseModel):
    # ... existing fields ...
    emergency_lane_count: Optional[int] = Field(None, description="Emergency lane count (DHS)")
    emergency_lane_indexes: Optional[List[int]] = Field(None, description="Emergency lane indexes")
```

### 8.2 Deprecation Strategy

**If Field Must Be Removed**:
1. Mark as deprecated in OpenAPI schema
2. Provide 6-month deprecation notice in API documentation
3. Return field with null value during deprecation period
4. Remove in next major version (v2)

---

## 9. Validation Rules Summary

### Required vs. Optional Fields

**Request Model (EdgeQueryRequest)**:
- All filters are **optional** (empty query returns all edges)
- with_gantry defaults to False (boolean, never null)

**Response Model (EdgeInfoResponse)**:
- edge_id: **Required** (always present in database)
- route_code: **Required** (always present in database)
- All other fields: **Optional** (may be null in database)

### Cross-Field Validations

1. **Stake Range**: max_stake ≥ min_stake when both provided
2. **Length Range**: max_length ≥ min_length when both provided
3. **Gantry Consistency**: len(gantry_ids) == gantry_count (enforced by database query)
4. **Emergency Lane Consistency** (future): emergency_lane_count == len(emergency_lane_indexes)

---

## 10. Performance Considerations

### 10.1 Serialization Performance

**EdgeInfo → EdgeInfoResponse Conversion**:
- Use `from_edge_info()` class method for batch conversion
- Avoid repeated field access (use local variables in loops)
- Estimated overhead: ~10μs per edge (negligible for <1000 edges)

### 10.2 Memory Footprint

**Per-Edge Memory Usage**:
- EdgeInfo dataclass: ~300 bytes (11 fields + overhead)
- EdgeInfoResponse Pydantic: ~400 bytes (validation + metadata)
- 1000 edges = ~700 KB total memory

**Optimization**: For very large result sets (>5000 edges), consider streaming JSON response instead of loading all into memory

---

## 11. Testing Strategy for Models

### 11.1 Unit Tests (Pydantic Validation)

**Test File**: `tests/unit/test_edge_query_models.py`

```python
def test_edge_query_request_valid_input():
    """Test valid input passes validation"""
    request = EdgeQueryRequest(
        route_codes="G4202,SA2",
        min_stake=10.0,
        max_stake=50.0,
        min_lanes=3
    )
    assert request.route_codes == "G4202,SA2"
    params = request.to_query_params()
    assert params['route_codes'] == ['G4202', 'SA2']

def test_edge_query_request_invalid_stake_range():
    """Test max_stake < min_stake raises validation error"""
    with pytest.raises(ValueError, match="max_stake must be >= min_stake"):
        EdgeQueryRequest(min_stake=50.0, max_stake=10.0)

def test_edge_query_response_warning_large_result():
    """Test warning added for large result sets"""
    edges = [EdgeInfo(...) for _ in range(60)]
    response = EdgeQueryResponse.from_edge_infos(edges)
    assert response.total_count == 60
    assert "Large result set" in response.warning
```

### 11.2 Integration Tests (End-to-End)

**Test File**: `tests/integration/test_control_api.py`

```python
def test_edge_query_api_valid_request(client):
    """Test API endpoint with valid query parameters"""
    response = client.get("/api/v1/control/edges/query?route_codes=G4202&min_lanes=3")
    assert response.status_code == 200
    data = response.json()
    assert "edges" in data
    assert "total_count" in data
    assert data["total_count"] > 0

def test_edge_query_api_invalid_request(client):
    """Test API endpoint rejects invalid parameters"""
    response = client.get("/api/v1/control/edges/query?min_stake=50&max_stake=10")
    assert response.status_code == 400
    assert "max_stake must be >= min_stake" in response.json()["detail"]
```

---

**Data Model Status**: ✅ **COMPLETE**

**Next Steps**:
1. Generate API contracts (OpenAPI specification)
2. Implement Pydantic models in code
3. Write unit tests for model validation
