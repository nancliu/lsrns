# Proposal: Batch Monitoring Hierarchy Organization and Results Analysis

**Change ID**: `batch-monitoring-hierarchy-and-results-analysis`

**Status**: 📋 Proposal (Planning)

**Priority**: P1 (UX and Functionality Improvement)

**Created**: 2025-11-02

---

## Why (Problem Statement)

### Current Issues

**1. Batch List Organization Problem**

- Current batch list displays all batches flat (no hierarchy), making it hard to find batches for a specific case
- When a user has multiple cases and multiple batches per case, all batches mix together
- Missing case-level summary information (how many batches per case? what's the latest batch status?)

**2. Results Analysis Missing**

- Current system only shows simple peak value curve visualization
- No comparative analysis between plans (baseline vs. controlled)
- Users cannot quickly evaluate control strategy effectiveness (improvement rates, capacity improvements)
- No mechanism to assess impact of control strategies across time periods

**3. Output Configuration Consistency Risk**

- If different plans within the same batch have different output configurations, comparison results become invalid
- Example: baseline with full output (has tripinfo) vs. control plan with minimal output (no tripinfo) → cannot fairly compare vehicle-level metrics
- No mechanism to enforce output configuration consistency

**4. Baseline Plan Management Unclear**

- Baseline plan necessity not explicitly enforced
- Users may forget to create baseline plan, making comparisons impossible
- No system-level guarantee that each batch has a baseline

---

## What Changes

### New Capabilities

1. **Case-Grouped Batch List Display** - Hierarchical organization (Case → Batches)
   - Group batches by case_id
   - Show case-level summary info (batch count, latest status)
   - Collapsible/expandable case groups
   - Filtering and sorting within case scope

2. **Two-Layer Results Analysis System**
   - **Layer 1 (Quick Overview)**: Based on summary.xml
     - Parse final metrics from summary.xml
     - Compare across plans within a batch
     - Calculate improvement rates relative to baseline
     - Display comparison table and charts
   - **Layer 2 (Detailed Analysis)**: Deferred to future iteration
     - Based on tripinfo.xml and edgedata.xml
     - Vehicle-level histogram distributions
     - Road segment heat maps

3. **Unified Output Configuration**
   - Users select output level (minimal/standard/full) when creating batch
   - Same configuration applied to ALL plans (including baseline) in the batch
   - Configuration saved as `simulation_config.json` in batch directory
   - Validation to ensure no plan has different output settings

4. **Baseline Plan Enforcement**
   - System automatically includes baseline_plan in every batch
   - If user doesn't select baseline, system adds it automatically
   - UI marks baseline_plan as "standard plan (cannot delete)"

5. **Configurable Random Simulation Count**
   - Users can set random simulation count per plan (1-10, default 3)
   - All plans in batch use same count
   - Consistent seed sequence: if num_seeds=3, base_seed=66 → seeds [66, 67, 68]
   - Same-round different-plan same seed (enables comparison), different-round different seed (adds randomness)

### Modified Capabilities

- **batch-optimization**: Add output configuration parameters, baseline enforcement logic
- **batch-monitoring-unified**: Add case grouping, filtering/sorting within groups
- **batch-simulation-charts** (if exists): Add results comparison charts, improvement rate visualization

### Modified Components

- `api/services/batch_optimization_service.py` - Add output level parameter, baseline enforcement
- `frontend/control/js/batch_simulation.js` - Case grouping render logic, form UI enhancements
- `frontend/control/js/batch_results.js` - Results analysis rendering
- `frontend/control/simulations.html` - Case group structure, results view
- `frontend/control/css/simulations.css` - Case group styling, comparison table styling

### New Components

- `shared/control_tools/batch_result_analyzer.py` - summary.xml parsing, improvement rate calculation
- `frontend/control/js/batch_results_analyzer.js` - Results data aggregation logic

---

## Impact

### Affected Files (Backend)

- `api/services/batch_optimization_service.py` (modify `create_batch()`, add analysis methods)
- `api/models/requests/batch_requests.py` (add output_level, num_seeds fields)
- `shared/control_tools/batch_result_analyzer.py` (new file)

### Affected Files (Frontend)

- `frontend/control/js/batch_simulation.js` (case grouping, form enhancements)
- `frontend/control/js/batch_results.js` (new or enhanced)
- `frontend/control/js/batch_results_analyzer.js` (new helper)
- `frontend/control/simulations.html` (structure update)
- `frontend/control/css/simulations.css` (new styles for groups, tables)

### API Changes

**Modify**: `POST /api/v1/control/optimization/batch`

- Add optional `output_level: "minimal" | "standard" | "full"` (default: "standard")
- Add optional `num_seeds: 1-10` (default: 3)
- System automatically includes `baseline_plan` if not in plan_ids

**New Endpoint** (optional, for consistency): `GET /api/v1/control/optimization/batch/{batch_id}/results`

- Returns aggregated results (improvement rates, summary metrics)
- Queries all plans' summary.xml files, calculates statistics

### Breaking Changes

⚠️ **Non-breaking**: The change is purely additive and UI-focused.

- Output configuration is optional; if not provided, system uses default "standard" level
- Baseline auto-inclusion is transparent to users
- No existing API contracts broken

---

## Success Criteria

### Functional Acceptance

- [ ] **AC1: Case Grouping Display**
  - Batches grouped by case_id in UI
  - Case group shows batch count, latest batch info
  - Case groups collapsible/expandable
  - Filtering/sorting work within case scope

- [ ] **AC2: Results Analysis (Layer 1)**
  - summary.xml parsing works for all plans
  - Improvement rates calculated correctly (relative to baseline)
  - Comparison table displays 5+ metrics (time, capacity, wait time, vehicles, etc.)
  - Charts render correctly (bar chart, optionally radar/curve)

- [ ] **AC3: Output Configuration Consistency**
  - Batch creation form includes output_level selector
  - Configuration applied to ALL plans (including baseline)
  - Validation ensures no plan has conflicting config
  - Config saved in batch metadata

- [ ] **AC4: Baseline Plan Enforcement**
  - Batch creation auto-includes baseline_plan
  - UI marks baseline as "standard plan"
  - User cannot delete baseline from batch

- [ ] **AC5: Random Seed Configuration**
  - Form includes num_seeds selector (1-10)
  - Seed sequence generated correctly
  - Config stored and applied during task execution

### UX Acceptance

- [ ] **UX1: Hierarchy Clear**
  - Users quickly find batches for a specific case
  - Case grouping information is visually distinct

- [ ] **UX2: Results Intuitive**
  - Comparison table easy to read
  - Improvement rates clearly marked (↑ green, ↓ red)
  - Charts have good visual quality

---

## Dependencies

### Prerequisites

- ✅ `unify-batch-monitoring-and-history` (batch list UI base)
- ✅ `batch-optimization` API implemented
- ✅ `plan-management` (baseline_plan exists)

### Related Changes

- Builds on: `unify-batch-monitoring-and-history`
- Relates to: `batch-optimization`, `batch-management`, `plan-management`

---

## Open Questions

1. **Layer 2 detailed analysis scope** - To be determined after Layer 1 user feedback
2. **Case group sort order** - By latest batch time or by case_id?
3. **Improvement rate thresholds** - Significant improvement color threshold (e.g., >5%)?
4. **Summary.xml parsing robustness** - Error handling if a plan's summary.xml is missing/malformed?

---

## References

- Current batch monitoring: `frontend/control/js/batch_simulation.js`
- Batch service: `api/services/batch_optimization_service.py`
- Unified batch spec: `openspec/specs/batch-monitoring-unified/spec.md`
- Batch optimization spec: `openspec/specs/batch-optimization/spec.md`
