# Research Report: Database-Driven Edge Selector (Phase 1B)

**Feature**: Database-Driven Edge Selector
**Date**: 2025-10-20
**Phase**: Phase 0 - Research & Analysis

---

## Executive Summary

Phase 1A of the edge selector has been completed successfully with **9 filter dimensions** implemented in `shared/data_access/edge_query.py`. Phase 1B requires building API endpoints, frontend interface, and optional enhancements (edge_types, emergency lanes, TAZ filtering). The database schema analysis shows stable dim schema tables ready for production use. Performance testing shows hierarchical filtering (Route → Section → Edge) effectively reduces results from 1000+ to 10-20 segments.

**Key Finding**: Most core functionality already exists. Phase 1B focuses on **exposing existing capabilities through REST API and building user interface**.

---

## 1. Database Schema Analysis

### 1.1 Current State Assessment

**Status**: ✅ **Production-Ready**

The dim schema tables have been analyzed and validated through Phase 1A testing:

- **dim.sim_network_edges**: 8000+ edges with complete metadata (route_code, section_code, stake numbers, length, lanes)
- **dim.multiscale_node_units**: Node type classifications (diverging, merging, entrance, exit) fully populated
- **dim.point_gantry**: Gantry location data accurately mapped to edges via stake numbers
- **dim.sim_network_junctions**: Junction coordinates available for visualization

**Data Quality Findings**:
- ✅ Route codes: 8 distinct routes (G4202, SA2, G5, G76, S81, etc.)
- ✅ Section codes: 26 sections with clear hierarchical relationship to routes
- ✅ Demonstration IDs: 9 predefined areas for quick selection
- ✅ Stake number accuracy: Tested and validated in hierarchical filtering
- ✅ TAZ mapping: 461 records in taz_demonstration_mapping table

### 1.2 Schema Stability

**Decision**: Use existing schema without modifications (read-only access pattern)

**Rationale**:
- Current schema supports all P1/P2 requirements
- Adding new filter dimensions requires no schema changes (all data already exists)
- Read-only access reduces deployment risk and follows Constitution Principle V (Configuration Over Code)

**Alternatives Considered**:
1. **Add materialized views for performance** - Rejected: Premature optimization. Current query performance <400ms meets requirements.
2. **Add has_emergency_lane computed column** - Deferred to P3: Can implement via JOIN to sim_network_lanes when needed.

---

## 2. Existing Implementation Analysis (Phase 1A)

### 2.1 Completed Modules

**File**: `shared/data_access/edge_query.py` (327 lines)

**Status**: ✅ **Fully Functional** - Tested with 9 filter dimensions

**Implemented Functions**:

1. **`query_edges_with_filters()`** - Core filtering function
   - Accepts 11 parameters (route_codes, section_codes, node_types, stake range, length range, direction, demonstration_ids, min_lanes, with_gantry)
   - Uses parameterized SQL queries (SQL injection protection ✅)
   - Returns EdgeInfo dataclass objects with 11 fields
   - Performance: <400ms for typical queries

2. **`get_available_route_codes()`** - Metadata query
   - Returns list of distinct route codes
   - Used for populating route dropdown in UI

3. **`get_available_section_codes(route_code)`** - Hierarchical metadata
   - Returns sections filtered by route (optional)
   - Includes edge_count and stake_range for each section
   - Enables hierarchical filtering UX

4. **`get_demonstration_info()`** - Demonstration area metadata
   - Returns demonstration areas with edge counts and stake ranges
   - Supports quick selection of predefined areas

### 2.2 Data Model Assessment

**Current EdgeInfo Dataclass** (shared/data_access/edge_query.py:16-49):

```python
@dataclass
class EdgeInfo:
    edge_id: str
    route_code: str
    section_code: Optional[str]
    start_stake: Optional[float]
    end_stake: Optional[float]
    length: Optional[float]
    num_lanes: Optional[int]
    route_direction: Optional[str]
    node_type: Optional[str]
    gantry_count: int = 0
    gantry_ids: List[str] = None
```

**Decision**: Keep existing EdgeInfo dataclass unchanged for Phase 1B

**Rationale**:
- Provides all required fields for P1-P3 user stories
- Tested and validated in Phase 1A
- Can be extended with EdgeInfoWithLanes subclass for DHS (P3) without breaking existing code

**Pydantic Models Needed** (for API layer):
- Create parallel Pydantic BaseModel versions for API request/response validation
- Location: `api/models/requests/edge_query_request.py` and `api/models/responses/edge_query_response.py`

---

## 3. Best Practices Research

### 3.1 SQLAlchemy Connection Pooling

**Current Implementation**: Direct psycopg2 connection via `open_db_connection()`

**Decision**: Upgrade to SQLAlchemy connection pooling with QueuePool

**Rationale**:
- Current implementation creates new connection per request (performance bottleneck for concurrent users)
- SQLAlchemy QueuePool provides efficient connection reuse
- Configurable pool_size (initial: 10) and max_overflow (initial: 5) support scaling to 50+ users
- Follows FR-058 requirement for connection pooling

**Implementation**:
```python
# shared/data_access/connection.py (enhancement)
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    connection_string,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True  # Verify connections before use
)
```

**Alternatives Considered**:
1. **Keep psycopg2 direct connections** - Rejected: Does not scale to 50+ users
2. **Use asyncpg with connection pool** - Rejected: Requires async/await refactoring (high complexity)

### 3.2 Response Caching Strategy

**Decision**: Implement 5-minute TTL caching for metadata endpoints only

**Rationale**:
- Metadata (routes, sections, demonstrations) changes infrequently (hours/days)
- 5-minute TTL balances freshness vs. performance
- Main query endpoint (/query) has too diverse filter combinations for effective caching

**Technology Choice**: Python functools.lru_cache with TTL wrapper (cachetools library)

**Implementation**:
```python
from cachetools import TTLCache, cached

metadata_cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes

@cached(cache=metadata_cache)
def get_available_route_codes() -> List[str]:
    # ... existing implementation
```

**Alternatives Considered**:
1. **Redis caching** - Rejected: Adds external dependency, over-engineering for initial deployment
2. **No caching** - Rejected: Misses easy performance wins for frequently accessed metadata
3. **Cache /query endpoint** - Rejected: Too many unique filter combinations (low hit rate)

### 3.3 Error Handling and Retry Logic

**Decision**: Exponential backoff retry with max 2 attempts (immediate + 500ms delay)

**Rationale**:
- Handles transient connection failures (network blips, connection pool exhaustion)
- 2 attempts balance reliability vs. latency (total max: ~500ms retry overhead)
- Exponential backoff prevents thundering herd

**Implementation**:
```python
import time

def query_with_retry(query_func, max_attempts=2):
    for attempt in range(max_attempts):
        try:
            return query_func()
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            if attempt < max_attempts - 1:
                delay = 0.5 * (2 ** attempt)  # 0.5s, 1s, ...
                logger.warning(f"Retry attempt {attempt+1} after {delay}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"Query failed after {max_attempts} attempts")
                raise
```

**Alternatives Considered**:
1. **No retry logic** - Rejected: Poor user experience during transient failures
2. **Retry all exceptions** - Rejected: Non-retryable errors (auth failure, syntax error) should fail immediately
3. **More than 2 attempts** - Rejected: Exceeds 2-second response time budget

### 3.4 API Design Patterns

**Decision**: RESTful API with query parameters for filtering

**Endpoint Design**:
- `GET /api/v1/control/edges/query?route_codes=G4202&min_lanes=3` - Main query endpoint
- `GET /api/v1/control/edges/routes` - Metadata (cached)
- `GET /api/v1/control/edges/sections?route_code=G4202` - Hierarchical metadata (cached)
- `GET /api/v1/control/edges/demonstrations` - Demonstration areas (cached)

**Rationale**:
- GET requests are idempotent and cacheable
- Query parameters map naturally to filter dimensions
- Comma-separated values for arrays: `route_codes=G4202,SA2`
- Follows existing OD_SIM API conventions (FastAPI, /api/v1/ prefix)

**Alternatives Considered**:
1. **POST with JSON body** - Rejected: Query operations should use GET for cacheability
2. **GraphQL** - Rejected: Over-engineering, team unfamiliar with GraphQL
3. **gRPC** - Rejected: No requirement for binary protocol, REST is sufficient

---

## 4. Frontend Technology Stack

### 4.1 Filtering Interface

**Decision**: Vanilla JavaScript with Fetch API (no framework)

**Rationale**:
- Existing OD_SIM frontend uses vanilla JS (consistency)
- Simple CRUD operations don't require React/Vue complexity
- Faster initial load time (no framework bundle)
- Follows project constraint: no external frontend libraries

**Implementation Pattern**:
```javascript
// frontend/control/js/edge_filter.js
async function queryEdges(filters) {
    const queryString = new URLSearchParams(filters).toString();
    const response = await fetch(`/api/v1/control/edges/query?${queryString}`);
    return await response.json();
}
```

### 4.2 Network Visualization

**Decision**: HTML5 Canvas API (no mapping libraries)

**Rationale**:
- Project constraint: No external mapping libraries
- Canvas provides sufficient performance for ~1000 edges
- Junction coordinates available in database (no need for full map tiles)
- Simplified road network visualization (not general-purpose map)

**Implementation Approach**:
1. Fetch junction coordinates from database
2. Render edges as lines between from_junction and to_junction
3. Highlight filtered edges with distinctive color
4. Pan/zoom via canvas transformation matrix
5. Tooltip on hover via mousemove event + canvas hit testing

**Alternatives Considered**:
1. **Leaflet.js / OpenLayers** - Rejected: Violates "no external mapping libraries" constraint
2. **SVG rendering** - Rejected: Performance degrades with 1000+ elements compared to Canvas
3. **WebGL** - Rejected: Over-engineering, Canvas sufficient for initial deployment

---

## 5. Testing Strategy

### 5.1 Test Structure

**Decision**: pytest with separate test files for unit/integration tests

**Test Files to Create**:
- `tests/unit/test_edge_query.py` - Database query logic (already exists from Phase 1A)
- `tests/unit/test_control_service.py` - Service layer unit tests
- `tests/integration/test_control_api.py` - API endpoint integration tests

**Coverage Requirements**:
- Unit tests: ≥80% coverage (shared layer)
- Integration tests: 100% pass rate (all API endpoints)

### 5.2 Test Fixtures

**Decision**: Use pytest fixtures for database connection and test data

**Fixture Strategy**:
```python
@pytest.fixture
def db_connection():
    conn = open_db_connection()
    yield conn
    conn.close()

@pytest.fixture
def sample_filters():
    return {
        "route_codes": ["G4202"],
        "min_lanes": 3,
        "route_direction": "clockwise"
    }
```

### 5.3 Edge Case Testing

**Critical Edge Cases**:
1. Empty result set (no matching edges)
2. Invalid filter values (min_stake > max_stake)
3. Database connection failure
4. Large result sets (1000+ edges without filters)
5. Missing gantry/lane data (NULL handling)

---

## 6. Performance Optimization

### 6.1 Database Indexing

**Current Index Status**: Indexes exist on route_code and section_code (verified in Phase 1A testing)

**Decision**: No new indexes required for Phase 1B

**Rationale**:
- Query performance <400ms meets requirements
- Premature optimization without performance bottleneck identified
- Production monitoring (Phase 2) will identify if additional indexes needed

**Future Optimization**: Add composite index on (route_code, start_stake, end_stake) if query time exceeds 400ms threshold

### 6.2 Query Optimization

**Decision**: Keep existing query structure with LEFT JOINs

**Rationale**:
- Current query uses EXPLAIN ANALYZE to verify query plan
- LEFT JOINs necessary to handle edges without nodes/gantries
- GROUP BY with STRING_AGG efficient for gantry_ids aggregation

**Optimization Applied**: Use parameterized queries to enable query plan caching by PostgreSQL

---

## 7. Logging and Observability

### 7.1 Structured Logging

**Decision**: JSON-compatible structured logging format

**Log Fields**:
- timestamp (ISO 8601)
- log_level (INFO, WARNING, ERROR)
- filter_parameters (dict)
- result_count (int)
- query_execution_time_ms (float)
- error_type (optional)
- error_message (optional)

**Implementation**:
```python
logger.info({
    "event": "edge_query_executed",
    "filter_parameters": filters,
    "result_count": len(edges),
    "query_execution_time_ms": execution_time
})
```

**Rationale**:
- JSON format enables future integration with log aggregation tools (ELK, Splunk)
- Structured data easier to query than unstructured logs

### 7.2 Performance Monitoring

**Decision**: Log slow queries (>1500ms) as WARNING level

**Rationale**:
- 2-second timeout budget with 25% buffer = 1500ms warning threshold
- Identifies performance degradation early
- Guides index optimization decisions

---

## 8. Security Considerations

### 8.1 SQL Injection Prevention

**Current Protection**: ✅ **Adequate** - Parameterized queries via psycopg2

**Verification**: All SQL queries use `cur.execute(sql, params)` with bound parameters

**Decision**: Maintain current parameterized query approach

### 8.2 Authentication/Authorization

**Decision**: No authentication required (internal tool)

**Rationale**:
- Spec states "read-only access, no authentication required"
- Users are traffic engineers with network access to application server
- Database credentials secured in .env file (not exposed in API responses or logs)

**Future Consideration**: Add API key authentication if external access required

---

## 9. Deployment and Scalability

### 9.1 Scaling Strategy

**Decision**: Vertical scaling with connection pool tuning

**Initial Configuration**:
- pool_size: 10 connections
- max_overflow: 5 connections
- Total capacity: 15 concurrent database queries

**Scaling Path** (50+ users):
1. Increase pool_size to 20-30
2. Add query result pagination (LIMIT/OFFSET)
3. Monitor connection pool utilization via logging
4. Consider read replica if database becomes bottleneck

**Alternatives Considered**:
1. **Horizontal scaling (multiple API servers)** - Deferred: Premature for 10-50 user range
2. **Database sharding** - Rejected: Not applicable to read-only metadata queries

### 9.2 Configuration Management

**Decision**: Environment variables for all tunable parameters

**Configurable Parameters**:
- DB_POOL_SIZE (default: 10)
- DB_MAX_OVERFLOW (default: 5)
- CACHE_TTL_SECONDS (default: 300)
- QUERY_TIMEOUT_MS (default: 2000)

**Rationale**: Follows Constitution Principle V (Configuration Over Code)

---

## 10. Phase 1B Implementation Scope

### 10.1 Priority P1 Features (Must-Have)

**Backend**:
1. ✅ Database query module - Already exists (edge_query.py)
2. 🔨 API service layer - Create control_strategy_service.py
3. 🔨 API routes - Create control_routes.py with 4 endpoints
4. 🔨 Pydantic models - Create request/response models
5. 🔨 Connection pooling - Upgrade from psycopg2 to SQLAlchemy pooling
6. 🔨 Response caching - Implement for metadata endpoints
7. 🔨 Retry logic - Add exponential backoff for transient errors

**Frontend**:
1. 🔨 Filtering interface - Create edge_selector.html
2. 🔨 Filter controls - Implement 9 filter dimension controls
3. 🔨 Results table - Display filtered edges with selection
4. 🔨 Hierarchical dropdowns - Route → Section cascading selection

**Testing**:
1. 🔨 Integration tests - Test all 4 API endpoints
2. 🔨 Unit tests - Test service layer and query functions
3. 🔨 Edge case tests - Validate error handling

### 10.2 Priority P2-P4 Features (Optional)

**P2 - TEC Support**:
- ✅ Node type filtering - Already supported (node_types=["entrance"])
- 📋 edge_types parameter - Extension for highway.motorway_link filtering

**P3 - DHS Support**:
- 📋 query_edges_with_emergency_lanes() - New function with lane table JOIN
- 📋 EdgeInfoWithLanes model - Extended model with emergency lane fields

**P4 - Visualization**:
- 📋 Network visualization - Canvas-based map with junction coordinates
- 📋 Interactive selection - Click to toggle selection state
- 📋 Pan/zoom controls - Canvas transformation matrix

---

## 11. Risk Assessment

### 11.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database performance degradation with 50+ users | Medium | High | Implement connection pooling + monitoring |
| Frontend Canvas performance issues with 1000+ edges | Low | Medium | Defer visualization to P4, implement incrementally |
| Missing indexes cause slow queries | Low | High | Monitor query performance, add indexes as needed |
| Connection pool exhaustion under load | Medium | High | Configure pool_size + max_overflow conservatively |

### 11.2 Integration Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing simulation/analysis modules | Low | Critical | Module isolation + comprehensive integration tests |
| API contract changes during development | Low | Medium | Lock API contracts in Phase 1 design |
| Frontend-backend API mismatch | Medium | Medium | Contract testing + OpenAPI schema validation |

---

## 12. Unknowns Resolved

All Technical Context "NEEDS CLARIFICATION" items have been resolved:

1. ✅ **Observability level**: Application-level structured logging (JSON format)
2. ✅ **Retry strategy**: 2 attempts with exponential backoff (immediate, +500ms)
3. ✅ **Authentication**: No authentication required (read-only, internal tool)
4. ✅ **Scaling strategy**: Vertical scaling with connection pool tuning
5. ✅ **Response caching**: 5-minute TTL for metadata endpoints

---

## 13. Key Decisions Summary

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| **Database Access** | Read-only, no schema changes | Existing schema sufficient, reduces deployment risk |
| **Connection Management** | SQLAlchemy QueuePool (pool_size=10) | Scalable, efficient connection reuse |
| **Caching** | 5-min TTL for metadata only | Balances freshness vs. performance |
| **API Design** | RESTful GET endpoints | Idempotent, cacheable, follows conventions |
| **Frontend** | Vanilla JS + Canvas | No external dependencies, consistency with existing code |
| **Error Handling** | Exponential backoff, 2 attempts | Handles transient failures gracefully |
| **Testing** | pytest, TDD workflow | Constitution requirement, ensures quality |
| **Logging** | JSON-structured logs | Future log aggregation readiness |
| **Scaling** | Vertical scaling | Appropriate for 10-50 user range |

---

## 14. Next Steps (Phase 1 Design)

1. ✅ Research complete - All unknowns resolved
2. 🔜 Generate data-model.md - Define Pydantic models for API layer
3. 🔜 Generate API contracts - OpenAPI specification for 4 endpoints
4. 🔜 Generate quickstart.md - API usage examples and integration guide
5. 🔜 Update agent context - Add edge selector technology to CLAUDE.md

---

**Research Status**: ✅ **COMPLETE**

**Action**: Proceed to Phase 1 Design

**Re-evaluation**: After Phase 1 design, verify Constitution Check compliance for API contracts and data models
