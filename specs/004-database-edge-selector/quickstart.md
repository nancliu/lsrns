# Quick Start Guide: Edge Selector API

**Feature**: Database-Driven Edge Selector (Phase 1B)
**Audience**: Frontend developers, API integrators, traffic control engineers
**Version**: 1.0.0

---

## 1. Getting Started in 5 Minutes

### 1.1 Prerequisites

- OD_SIM API server running on `http://localhost:8000`
- Database connection configured in `.env` file
- Modern web browser (for frontend examples)

### 1.2 First API Call

**Query all edges for route G4202**:

```bash
curl "http://localhost:8000/api/v1/control/edges/query?route_codes=G4202"
```

**Response**:
```json
{
  "edges": [
    {
      "edge_id": "-5880",
      "route_code": "G4202",
      "section_code": "G4202001",
      "start_stake": 10.5,
      "end_stake": 12.3,
      "length": 1800.0,
      "num_lanes": 3,
      "route_direction": "clockwise",
      "node_type": "diverging",
      "gantry_count": 2,
      "gantry_ids": ["G001", "G002"]
    }
    // ... more edges
  ],
  "total_count": 1198,
  "warning": "Too many results (1198), please add more filters to narrow down selection."
}
```

**Key Takeaway**: Route-only query returns too many results. Add more filters!

---

## 2. Common Use Cases

### 2.1 Hierarchical Filtering (Recommended Workflow)

**Step 1: Get available routes**

```bash
curl "http://localhost:8000/api/v1/control/edges/routes"
```

Response: `["G4202", "G5", "G76", "S81", "SA2"]`

**Step 2: Get sections for selected route**

```bash
curl "http://localhost:8000/api/v1/control/edges/sections?route_code=G4202"
```

Response:
```json
[
  {
    "section_code": "G4202001",
    "route_code": "G4202",
    "edge_count": 621,
    "min_stake": 1.17,
    "max_stake": 85.68,
    "stake_range": "K1.17-K85.68"
  },
  {
    "section_code": "G4202002",
    "route_code": "G4202",
    "edge_count": 577,
    "min_stake": 85.68,
    "max_stake": 168.35,
    "stake_range": "K85.68-K168.35"
  }
]
```

**Step 3: Query edges with route + section + additional filters**

```bash
curl "http://localhost:8000/api/v1/control/edges/query?route_codes=G4202&section_codes=G4202001&min_stake=10&max_stake=50&min_length=500&max_length=2000&min_lanes=3&route_direction=clockwise&with_gantry=true"
```

**Result**: ~15 edges matching all criteria ✅

---

### 2.2 Variable Speed Sign (VSS) Scenario

**Goal**: Find mainroad segments suitable for speed control

```bash
curl "http://localhost:8000/api/v1/control/edges/query?route_codes=G4202&section_codes=G4202001&route_direction=clockwise&min_length=800&max_length=3000&min_lanes=3&with_gantry=true"
```

**Filters Explained**:
- `route_codes=G4202` → Target highway
- `section_codes=G4202001` → Specific management section
- `route_direction=clockwise` → One direction only
- `min_length=800&max_length=3000` → Long enough for speed transition, short enough for effective control
- `min_lanes=3` → Mainroad capacity
- `with_gantry=true` → Must have observation data

**Expected Result**: 10-20 candidate edges for VSS deployment

---

### 2.3 Toll Entrance Control (TEC) Scenario

**Goal**: Find entrance ramp segments for entrance flow control

```bash
curl "http://localhost:8000/api/v1/control/edges/query?route_codes=G4202&node_types=entrance"
```

**Filters Explained**:
- `route_codes=G4202` → Target highway
- `node_types=entrance` → Entrance ramps only

**Expected Result**: 15-30 entrance ramp edges

**Advanced TEC (with demonstration area)**:

```bash
# First, get demonstration areas
curl "http://localhost:8000/api/v1/control/edges/demonstrations"

# Then filter by demonstration_id + entrance nodes
curl "http://localhost:8000/api/v1/control/edges/query?demonstration_ids=5&node_types=entrance"
```

---

### 2.4 Dynamic Hard Shoulder (DHS) Scenario

**Goal**: Find mainroad segments with emergency lanes (4+ lanes)

```bash
curl "http://localhost:8000/api/v1/control/edges/query?route_codes=G4202&min_lanes=4&min_length=800"
```

**Filters Explained**:
- `route_codes=G4202` → Target highway
- `min_lanes=4` → Likely to have emergency lane (3 regular + 1 emergency or 4+ lanes total)
- `min_length=800` → Long enough for dynamic opening

**Note**: This is inference-based. For precise emergency lane identification, use future `query_edges_with_emergency_lanes()` function (Phase 1B P3).

---

## 3. JavaScript Frontend Integration

### 3.1 Basic Query Function

```javascript
// frontend/control/js/edge_filter.js

/**
 * Query edges with filters
 * @param {Object} filters - Filter object with optional fields
 * @returns {Promise<Object>} Query response
 */
async function queryEdges(filters) {
    // Convert filter object to query string
    const params = new URLSearchParams();

    if (filters.route_codes) params.append('route_codes', filters.route_codes.join(','));
    if (filters.section_codes) params.append('section_codes', filters.section_codes.join(','));
    if (filters.node_types) params.append('node_types', filters.node_types.join(','));
    if (filters.min_stake != null) params.append('min_stake', filters.min_stake);
    if (filters.max_stake != null) params.append('max_stake', filters.max_stake);
    if (filters.min_length != null) params.append('min_length', filters.min_length);
    if (filters.max_length != null) params.append('max_length', filters.max_length);
    if (filters.route_direction) params.append('route_direction', filters.route_direction);
    if (filters.demonstration_ids) params.append('demonstration_ids', filters.demonstration_ids.join(','));
    if (filters.min_lanes != null) params.append('min_lanes', filters.min_lanes);
    if (filters.with_gantry) params.append('with_gantry', 'true');

    const response = await fetch(`/api/v1/control/edges/query?${params.toString()}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Query failed');
    }

    return await response.json();
}

// Example usage
const filters = {
    route_codes: ['G4202'],
    section_codes: ['G4202001'],
    min_stake: 10.0,
    max_stake: 50.0,
    min_lanes: 3,
    with_gantry: true
};

try {
    const result = await queryEdges(filters);
    console.log(`Found ${result.total_count} edges`);
    if (result.warning) {
        console.warn(result.warning);
    }
    displayEdges(result.edges);
} catch (error) {
    console.error('Query error:', error.message);
    alert(`Failed to query edges: ${error.message}`);
}
```

### 3.2 Load Metadata for Dropdowns

```javascript
/**
 * Load route codes for dropdown
 * @returns {Promise<Array<string>>} Route codes
 */
async function loadRoutes() {
    const response = await fetch('/api/v1/control/edges/routes');
    return await response.json();
}

/**
 * Load sections for selected route
 * @param {string} routeCode - Route code filter (optional)
 * @returns {Promise<Array<Object>>} Section information
 */
async function loadSections(routeCode = null) {
    const url = routeCode
        ? `/api/v1/control/edges/sections?route_code=${routeCode}`
        : '/api/v1/control/edges/sections';
    const response = await fetch(url);
    return await response.json();
}

/**
 * Load demonstration areas
 * @returns {Promise<Array<Object>>} Demonstration information
 */
async function loadDemonstrations() {
    const response = await fetch('/api/v1/control/edges/demonstrations');
    return await response.json();
}

// Example: Populate route dropdown
async function initializeFilters() {
    const routes = await loadRoutes();
    const routeSelect = document.getElementById('route-select');

    routes.forEach(routeCode => {
        const option = document.createElement('option');
        option.value = routeCode;
        option.textContent = routeCode;
        routeSelect.appendChild(option);
    });

    // When route changes, update section dropdown
    routeSelect.addEventListener('change', async (e) => {
        const sections = await loadSections(e.target.value);
        updateSectionDropdown(sections);
    });
}
```

### 3.3 Display Results Table

```javascript
/**
 * Display edges in results table
 * @param {Array<Object>} edges - Edge information array
 */
function displayEdges(edges) {
    const tbody = document.getElementById('results-tbody');
    tbody.innerHTML = ''; // Clear existing rows

    edges.forEach(edge => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <input type="checkbox" class="edge-checkbox" value="${edge.edge_id}" />
            </td>
            <td>${edge.edge_id}</td>
            <td>${edge.route_code}</td>
            <td>${edge.section_code || 'N/A'}</td>
            <td>K${edge.start_stake?.toFixed(1) || '?'} - K${edge.end_stake?.toFixed(1) || '?'}</td>
            <td>${edge.length?.toFixed(0) || 'N/A'} m</td>
            <td>${edge.num_lanes || 'N/A'}</td>
            <td>${edge.node_type || '-'}</td>
            <td>${edge.gantry_count}</td>
        `;
        tbody.appendChild(row);
    });

    // Update result count
    document.getElementById('result-count').textContent = `Query result: ${edges.length} segments`;
}
```

---

## 4. Error Handling Best Practices

### 4.1 Client-Side Validation

```javascript
/**
 * Validate filter inputs before sending to API
 * @param {Object} filters - Filter object
 * @returns {Object} Validation result {valid: boolean, errors: Array<string>}
 */
function validateFilters(filters) {
    const errors = [];

    // Validate stake range
    if (filters.min_stake != null && filters.max_stake != null) {
        if (filters.max_stake < filters.min_stake) {
            errors.push('Maximum stake must be >= minimum stake');
        }
    }

    // Validate length range
    if (filters.min_length != null && filters.max_length != null) {
        if (filters.max_length < filters.min_length) {
            errors.push('Maximum length must be >= minimum length');
        }
    }

    // Validate route direction
    if (filters.route_direction && !['clockwise', 'counterclockwise'].includes(filters.route_direction)) {
        errors.push('Route direction must be "clockwise" or "counterclockwise"');
    }

    // Validate node types
    const validNodeTypes = ['diverging', 'merging', 'entrance', 'exit'];
    if (filters.node_types) {
        const invalid = filters.node_types.filter(t => !validNodeTypes.includes(t));
        if (invalid.length > 0) {
            errors.push(`Invalid node types: ${invalid.join(', ')}`);
        }
    }

    return {
        valid: errors.length === 0,
        errors: errors
    };
}

// Usage
const validation = validateFilters(filters);
if (!validation.valid) {
    alert('Validation errors:\n' + validation.errors.join('\n'));
    return;
}
```

### 4.2 Handle API Errors

```javascript
async function queryEdgesWithErrorHandling(filters) {
    try {
        const result = await queryEdges(filters);

        // Handle warnings
        if (result.warning) {
            showWarning(result.warning);
        }

        return result;

    } catch (error) {
        // Handle different error types
        if (error.message.includes('max_stake')) {
            showError('Invalid stake range: Maximum stake must be greater than or equal to minimum stake');
        } else if (error.message.includes('Unable to retrieve')) {
            showError('Database connection failed. Please try again in a moment.');
        } else {
            showError(`Query failed: ${error.message}`);
        }

        return null;
    }
}

function showWarning(message) {
    const warningDiv = document.getElementById('warning-message');
    warningDiv.textContent = message;
    warningDiv.style.display = 'block';
    warningDiv.className = 'alert alert-warning';
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.className = 'alert alert-danger';
}
```

---

## 5. Performance Optimization Tips

### 5.1 Debounce User Input

```javascript
/**
 * Debounce function to avoid excessive API calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Usage: Debounce stake input changes
const debouncedQuery = debounce(() => {
    const filters = collectFiltersFromUI();
    queryEdges(filters);
}, 500); // Wait 500ms after user stops typing

document.getElementById('min-stake').addEventListener('input', debouncedQuery);
document.getElementById('max-stake').addEventListener('input', debouncedQuery);
```

### 5.2 Cache Metadata Locally

```javascript
// Simple client-side cache for metadata
const metadataCache = {
    routes: null,
    sections: {},
    demonstrations: null
};

async function loadRoutesWithCache() {
    if (!metadataCache.routes) {
        metadataCache.routes = await loadRoutes();
    }
    return metadataCache.routes;
}

async function loadSectionsWithCache(routeCode = null) {
    const cacheKey = routeCode || 'all';
    if (!metadataCache.sections[cacheKey]) {
        metadataCache.sections[cacheKey] = await loadSections(routeCode);
    }
    return metadataCache.sections[cacheKey];
}
```

---

## 6. Testing Your Integration

### 6.1 Manual Testing Checklist

- [ ] Query with route only → Returns 1000+ edges with warning
- [ ] Query with route + section → Returns ~600 edges
- [ ] Query with route + section + stake range → Returns 10-20 edges
- [ ] Query with invalid parameters (max_stake < min_stake) → Returns 400 error
- [ ] Load routes metadata → Returns 8+ routes in <100ms (cached)
- [ ] Load sections for specific route → Returns 2+ sections
- [ ] Query with `with_gantry=true` → Only returns edges with gantry_count > 0
- [ ] Query with node_types=entrance → Only returns entrance ramps

### 6.2 Automated Testing (pytest examples)

```python
# tests/integration/test_control_api.py

def test_query_edges_basic(client):
    """Test basic edge query"""
    response = client.get("/api/v1/control/edges/query?route_codes=G4202")
    assert response.status_code == 200
    data = response.json()
    assert "edges" in data
    assert "total_count" in data
    assert data["total_count"] > 0

def test_query_edges_with_filters(client):
    """Test edge query with multiple filters"""
    response = client.get(
        "/api/v1/control/edges/query"
        "?route_codes=G4202"
        "&section_codes=G4202001"
        "&min_stake=10"
        "&max_stake=50"
        "&min_lanes=3"
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all returned edges match filters
    for edge in data["edges"]:
        assert edge["route_code"] == "G4202"
        assert edge["section_code"] == "G4202001"
        assert edge["start_stake"] >= 10
        assert edge["end_stake"] <= 50
        assert edge["num_lanes"] >= 3

def test_query_edges_invalid_stake_range(client):
    """Test API rejects invalid stake range"""
    response = client.get(
        "/api/v1/control/edges/query?min_stake=50&max_stake=10"
    )
    assert response.status_code == 400
    assert "max_stake must be >= min_stake" in response.json()["detail"]

def test_metadata_routes(client):
    """Test routes metadata endpoint"""
    response = client.get("/api/v1/control/edges/routes")
    assert response.status_code == 200
    routes = response.json()
    assert isinstance(routes, list)
    assert len(routes) >= 8
    assert "G4202" in routes
```

---

## 7. Troubleshooting

### Common Issues

**Issue 1: "Too many results" warning**
- **Cause**: Query is too broad (e.g., route-only filter)
- **Solution**: Add more filters (section, stake range, length, lanes)

**Issue 2: "Unable to retrieve segment data" error (503)**
- **Cause**: Database connection failure
- **Solution**: Check database connectivity, retry after delay

**Issue 3: Empty result set (total_count = 0)**
- **Cause**: Filters too restrictive, no matching edges
- **Solution**: Relax some filter criteria (e.g., widen stake range)

**Issue 4: "max_stake must be >= min_stake" error (400)**
- **Cause**: Invalid filter combination
- **Solution**: Validate inputs before sending to API

**Issue 5: Metadata endpoints slow (>1 second)**
- **Cause**: Cache expired or first load
- **Solution**: Wait for cache to populate (subsequent calls will be fast)

### Debug Mode

```javascript
// Enable debug logging
const DEBUG = true;

async function queryEdgesDebug(filters) {
    if (DEBUG) {
        console.log('Query filters:', filters);
    }

    const startTime = performance.now();
    const result = await queryEdges(filters);
    const duration = performance.now() - startTime;

    if (DEBUG) {
        console.log(`Query completed in ${duration.toFixed(0)}ms`);
        console.log(`Result count: ${result.total_count}`);
        console.log('Sample edge:', result.edges[0]);
    }

    return result;
}
```

---

## 8. Next Steps

### Phase 1B Implementation

1. **Backend Development**:
   - Implement `control_strategy_service.py` service layer
   - Implement `control_routes.py` API endpoints
   - Add connection pooling and caching
   - Write unit and integration tests

2. **Frontend Development**:
   - Create `edge_selector.html` filtering interface
   - Implement `edge_filter.js` with API integration
   - Add result table and selection management
   - Optional: Network visualization with Canvas

3. **Testing & Validation**:
   - Run integration tests (100% pass rate)
   - Perform manual testing with all scenarios
   - Validate performance (<2 second response time)

### Future Enhancements (Phase 1B P2-P4)

- **P2**: Add `edge_types` parameter for TEC/DHS scenarios
- **P3**: Implement `query_edges_with_emergency_lanes()` for precise DHS
- **P4**: Add Canvas-based network visualization

---

## 9. Resources

### API Documentation

- OpenAPI Specification: [contracts/edge_query_api.yaml](./contracts/edge_query_api.yaml)
- Data Model: [data-model.md](./data-model.md)
- Research Report: [research.md](./research.md)

### Code Examples

- Backend: `api/services/control_strategy_service.py` (to be created)
- Backend: `api/routes/control_routes.py` (to be created)
- Frontend: `frontend/control/edge_selector.html` (to be created)
- Frontend: `frontend/control/js/edge_filter.js` (to be created)

### Database Schema

- Design Document: `docs/design/edge_selector_database_design.md`
- Test Report: `docs/design/edge_selector_test_report.md`
- Existing Implementation: `shared/data_access/edge_query.py`

---

**Quick Start Guide Version**: 1.0.0
**Last Updated**: 2025-10-20
**Maintained By**: OD_SIM Development Team
