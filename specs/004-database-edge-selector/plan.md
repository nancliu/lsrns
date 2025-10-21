# Implementation Plan: Database-Driven Edge Selector (Phase 1B)

**Branch**: `004-database-edge-selector` | **Date**: 2025-10-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-database-edge-selector/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Develop a database-driven road edge filtering system enabling traffic control engineers to select road segments through multi-dimensional queries (route, section, stake range, length, lanes, node type, gantry presence, demonstration areas). The system provides hierarchical filtering (Route → Section → Edge) to narrow down 1000+ candidates to 10-20 target segments in under 2 seconds. Implementation includes database query module (shared/data_access/edge_query.py), API endpoints (/api/v1/control/edges/*), web filtering interface, and optional network visualization. Technical approach uses PostgreSQL queries against dim schema tables with SQLAlchemy connection pooling and response caching for metadata endpoints.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, pandas, psycopg2
**Storage**: PostgreSQL 12+ (existing database at 10.149.235.123, schema: dim)
**Testing**: pytest (unit tests ≥80% coverage, API integration tests 100% pass rate)
**Target Platform**: Windows 10/11 server
**Project Type**: Web application (FastAPI backend + vanilla JavaScript frontend)
**Performance Goals**:
- Database queries <400ms execution time
- API endpoint response <2 seconds (including query + serialization)
- Support 10 concurrent users (initial), scalable to 50+ through connection pool tuning
- Metadata endpoint caching (5-minute TTL) to reduce database load

**Constraints**:
- Read-only database access (no schema modifications allowed)
- Must work with existing dim schema tables (sim_network_edges, multiscale_node_units, point_gantry, sim_network_junctions)
- No external mapping libraries for visualization (use HTML5 Canvas only)
- No authentication required (internal tool for traffic engineers)
- Result set warnings: >50 segments (suggest refinement), >100 segments (strong recommendation)
- File-based storage principle applies (not applicable to this feature - query results only)

**Scale/Scope**:
- 8+ highway routes (G4202, SA2, G5, etc.)
- ~1200 road edges total across all routes
- ~600 edges per major section
- Target filter result: 10-20 segments per query
- 4 control strategy scenarios (VSS, TEC, DHS, general filtering)

**Database Schema** (PostgreSQL dim schema):
- **sim_network_edges**: Main edge data (edge_id, route_code, section_code, start_stake, end_stake, length, num_lanes, route_direction, type, from_junction, to_junction)
- **multiscale_node_units**: Node type classifications (unit_id, junction_id, node_type: diverging/merging/entrance/exit, connected_edge_ids)
- **point_gantry**: Gantry locations (gantry_id, route_code, gantry_stake, demonstration_id)
- **sim_network_junctions**: Junction coordinates (junction_id, longitude, latitude, route_code, stake_number)
- **sim_network_lanes** (for DHS Phase 6): Lane-level configuration (edge_id, lane_index, disallow, speed, width) - used to identify emergency lanes with disallow="all"
- **taz_demonstration_mapping** (optional for TEC): TAZ to demonstration area mapping (461 records)

**Terminology**:
- **Edge** (边): The primary technical term for a directed road segment in SUMO network. Used consistently in code and APIs.
- **Road Segment** (路段): Human-readable synonym for edge, may appear in UI text and documentation. Both terms refer to the same concept.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Layered Architecture ✅ PASS

**Requirement**: API层 → Shared层单向依赖，严禁循环依赖

**Compliance**:
- New shared module: `shared/data_access/edge_query.py` (database query logic)
- New API service: `api/services/control_strategy_service.py` (calls shared/data_access/edge_query.py)
- New API routes: `api/routes/control_routes.py` (calls api/services/control_strategy_service.py)
- Dependency direction: API routes → API services → Shared data_access ✅
- No circular dependencies introduced ✅

**Status**: PASS - Maintains clear layered architecture

### Principle II: Module Isolation ✅ PASS

**Requirement**: 新功能域作为独立模块，严禁修改现有仿真分析代码

**Compliance**:

**API Layer**:
- ✅ New service file: `api/services/control_strategy_service.py` (dedicated to control domain)
- ✅ New route file: `api/routes/control_routes.py` with dedicated prefix `/api/v1/control/*`
- ✅ May call existing APIs: `/api/v1/simulation/*`, `/api/v1/case/*` (for future integration)
- ❌ No modifications to existing service/route files
- ✅ Will provide integration tests (100% pass rate)

**Shared Layer**:
- ✅ New tool: `shared/data_access/edge_query.py` (dedicated edge filtering queries)
- ✅ Extends existing connection management: reuses `shared/data_access/connection.py` without modifying it
- ❌ No modifications to existing shared tools
- ✅ Will provide unit tests (≥80% coverage)

**Status**: PASS - Complete module isolation, new control domain independent from simulation/analysis domains

### Principle III: Single Responsibility ✅ PASS

**Requirement**: 每个模块/类/函数只做一件事，Service按业务域严格分离

**Compliance**:
- `control_strategy_service.py`: Only handles control strategy domain (edge selection, control parameter management)
- `edge_query.py`: Only handles database queries for road edge filtering
- Route grouping: `/api/v1/control/*` for all control-related endpoints
- No cross-domain responsibility mixing (control logic separate from simulation/analysis/case management)

**Function responsibilities**:
- `query_edges_with_filters()`: Single purpose - filter edges by criteria
- `get_available_routes()`: Single purpose - return route metadata
- `get_available_sections()`: Single purpose - return section metadata

**Status**: PASS - Clear single responsibility boundaries

### Principle IV: Test-First ✅ COMMIT

**Requirement**: TDD流程，API测试100%，单测≥80%

**Commitment**:
- Write tests BEFORE implementation for all new endpoints
- Integration tests for all 4 API endpoints: `/query`, `/routes`, `/sections`, `/demonstrations`
- Unit tests for `edge_query.py` query functions (≥80% coverage)
- Test scenarios cover: normal queries, edge cases (empty results, invalid filters), error handling (DB failures)

**Test Development Plan**:
1. Phase 0 research: Define test structure and fixtures
2. Phase 1 design: Write failing tests for all contracts
3. Phase 2 implementation: Make tests pass

**Status**: COMMIT - Will follow TDD workflow

### Principle V: Configuration Over Code ✅ PASS

**Requirement**: 参数配置化，禁止硬编码

**Compliance**:
- Database connection via `.env` configuration (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- No hardcoded route codes, section codes, or demonstration IDs (all retrieved from database)
- Query timeout configurable via environment variable if needed
- Connection pool parameters configurable (pool_size, max_overflow)

**Status**: PASS - All configuration externalized

### Principle VI: File-Based Storage ✅ N/A

**Requirement**: 仿真结果必须文件存储，禁止数据库存储仿真输出

**Applicability**: NOT APPLICABLE - This feature queries existing road network metadata from database, does not generate or store simulation results. Feature is read-only data access for edge selection.

**Status**: N/A - Principle does not apply to metadata query features

### Development Standards ✅ COMMIT

**Compliance**:
- ✅ Use `pathlib.Path` for file operations (frontend serving static files if needed)
- ✅ Type hints + Google-style docstrings for all functions
- ✅ Use logging module (no `print()` statements)
- ✅ Function limits: ≤30 lines, ≤5 parameters, ≤3 nesting levels
- ✅ Code formatting: black with 100-character line width
- ✅ Pandas for data processing (e.g., result aggregation if needed)

**Status**: COMMIT - Will adhere to all development standards

### Overall Gate Status: ✅ PASS

**Summary**: All applicable constitution principles satisfied. Feature design follows:
- Layered architecture with clear API → Shared dependency
- Complete module isolation (new control domain, zero impact on simulation/analysis)
- Single responsibility per module/function
- TDD commitment for quality assurance
- Configuration-driven implementation
- File-based storage N/A (metadata queries only)

**Action**: Proceed to Phase 0 research

**Re-evaluation Point**: After Phase 1 design completion, verify:
1. API contracts maintain module isolation
2. Data model does not introduce cross-domain dependencies
3. Test coverage plans are comprehensive

---

### Post-Design Re-Evaluation ✅ PASS

**Date**: 2025-10-20 (After Phase 1 Design Completion)

**Re-evaluation Criteria**:

1. **API contracts maintain module isolation** ✅
   - All endpoints use `/api/v1/control/*` prefix (dedicated namespace)
   - No modifications to existing `/api/v1/simulation/*`, `/api/v1/case/*`, `/api/v1/analysis/*` endpoints
   - OpenAPI contract defines 4 independent endpoints without cross-domain dependencies
   - Request/response models are self-contained within control domain

2. **Data model does not introduce cross-domain dependencies** ✅
   - EdgeInfo dataclass remains in shared/data_access (existing, no changes)
   - New Pydantic models (EdgeQueryRequest, EdgeQueryResponse) isolated to api/models/
   - No dependencies on simulation/analysis domain models
   - Conversion pattern: EdgeInfo (shared) → EdgeInfoResponse (API) maintains clear layer boundary

3. **Test coverage plans are comprehensive** ✅
   - Unit tests defined for Pydantic model validation (tests/unit/test_edge_query_models.py)
   - Integration tests defined for all 4 API endpoints (tests/integration/test_control_api.py)
   - Edge case coverage: empty results, invalid ranges, DB failures, large result sets
   - Test fixtures planned for database connection and sample data
   - Coverage targets: Unit tests ≥80%, Integration tests 100% pass rate

**Additional Verification**:

4. **Backward Compatibility** ✅
   - No changes to existing edge_query.py functions (Phase 1A code untouched)
   - New API endpoints do not conflict with existing routes
   - Database schema read-only (no migrations required)

5. **Performance Requirements** ✅
   - API contracts specify <2 second response time requirement
   - Caching strategy documented for metadata endpoints (5-minute TTL)
   - Connection pooling design supports 10-50 concurrent users
   - Query optimization strategy researched (indexes, parameterized queries)

6. **Security Compliance** ✅
   - API contracts use parameterized query inputs (SQL injection prevention)
   - No authentication required (documented as internal tool)
   - Database credentials remain in .env (not exposed in API)
   - Error responses do not leak sensitive information

**Constitution Compliance Summary**:

| Principle | Initial Check | Post-Design Check | Status |
|-----------|---------------|-------------------|--------|
| I. Layered Architecture | ✅ PASS | ✅ PASS | Maintained |
| II. Module Isolation | ✅ PASS | ✅ PASS | Verified in contracts |
| III. Single Responsibility | ✅ PASS | ✅ PASS | Each endpoint single-purpose |
| IV. Test-First | ✅ COMMIT | ✅ COMMIT | Comprehensive test plans |
| V. Configuration Over Code | ✅ PASS | ✅ PASS | All params configurable |
| VI. File-Based Storage | ✅ N/A | ✅ N/A | Not applicable |
| Development Standards | ✅ COMMIT | ✅ COMMIT | Type hints, logging, black |

**Final Assessment**: ✅ **ALL GATES PASS** - Ready to proceed to Phase 2 (tasks.md generation)

## Project Structure

### Documentation (this feature)

```text
specs/004-database-edge-selector/
├── spec.md              # Feature specification (already exists)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - database schema analysis, query optimization
├── data-model.md        # Phase 1 output - EdgeInfo models, filter parameters
├── quickstart.md        # Phase 1 output - API usage examples, integration guide
├── contracts/           # Phase 1 output - OpenAPI specifications
│   └── edge_query_api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web application structure (FastAPI backend + vanilla JS frontend)

# Backend - API Layer
api/
├── routes/
│   └── control_routes.py           # NEW: /api/v1/control/edges/* endpoints
├── services/
│   └── control_strategy_service.py # NEW: Edge selection business logic
└── models/
    ├── requests/
    │   └── edge_query_request.py   # NEW: Filter parameter models
    └── responses/
        └── edge_query_response.py  # NEW: EdgeInfo, EdgeQueryResponse models

# Backend - Shared Layer
shared/
├── data_access/
│   ├── connection.py               # EXISTING: Reuse database connection
│   └── edge_query.py               # NEW: Database query functions
└── utilities/
    └── cache_utils.py              # NEW: Response caching for metadata endpoints

# Frontend
frontend/
└── control/                        # NEW: Control strategy pages
    ├── edge_selector.html          # NEW: Filtering interface
    └── js/
        ├── edge_filter.js          # NEW: Filter controls and API calls
        └── network_viz.js          # NEW: Canvas-based visualization (optional)

# Tests
tests/
├── integration/
│   └── test_control_api.py         # NEW: API endpoint integration tests
└── unit/
    ├── test_edge_query.py          # NEW: Database query unit tests
    └── test_control_service.py     # NEW: Service layer unit tests
```

**Structure Decision**: Web application structure selected based on:

1. **Existing OD_SIM architecture**: Feature extends existing FastAPI backend with new control domain
2. **Module isolation**: New files in dedicated control namespace (`control_routes.py`, `control_strategy_service.py`)
3. **Layered architecture**: API layer (routes/services/models) → Shared layer (data_access/utilities)
4. **Frontend integration**: New HTML/JS pages under `frontend/control/` directory
5. **No modifications**: Zero changes to existing simulation/analysis/case management modules

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations detected** - All constitution principles are satisfied. No complexity justifications required.

