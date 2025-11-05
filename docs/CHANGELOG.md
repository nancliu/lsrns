# Changelog

All notable changes to the OD Simulation System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2025-11-05

### Fixed - TripInfo 指标元数据

**问题**: 批次结果对比页面中 TripInfo 指标显示英文键名而非中文标签

#### 修复详情
- **添加元数据**: `api/services/batch_optimization_service.py`
  - 为 `total_delay`（总延误时间）添加完整元数据
  - 为 `avg_travel_time`（平均行程时间）添加完整元数据
  - 包含中文标签、单位（秒）、改进方向（越低越好）
  - 说明数据来源为 tripinfo.xml

- **更新文档**: `api/models/control/responses/batch_response.py`
  - 同步更新 API 响应模型示例
  - 确保 API 文档准确反映返回数据结构

#### 影响
- ✅ 批次结果页面现在显示"总延误时间 (秒)"而非 "total_delay"
- ✅ 批次结果页面现在显示"平均行程时间 (秒)"而非 "avg_travel_time"
- ✅ 图表横轴使用中文标签
- ✅ 改进率根据指标方向正确计算

#### 设计澄清
- `loaded`（已加载车数）指标改进率显示 `-` 是**正确行为**
- `loaded` 是中立指标 (`direction: "neutral"`)，批次内所有方案使用相同输入
- 符合 [METRICS_CLARIFICATION_SUMMARY.md](../openspec/changes/archive/2025-11-04-batch-monitoring-hierarchy-and-results-analysis/METRICS_CLARIFICATION_SUMMARY.md) 设计规范

**文档**: [TRIPINFO_METRICS_FIX_SUMMARY.md](TRIPINFO_METRICS_FIX_SUMMARY.md)

---

## [v0.9.0] - 2025-11-02

### Added - SUMO XML Validation & Cascade Regeneration

**OpenSpec Change**: `validate-strategy-xml-generation`

#### XML Validation Infrastructure (Phase 1)
- **New Module**: `shared/control_tools/xml_validator.py` (600+ lines)
  - Validates SUMO control.add.xml files against v1.19+ format
  - Checks parameter constraints (time: 0-86400s, speed: 0-200 km/h, flow: 0-10000 veh/h)
  - Strategy-specific validation (VSS steps, DHS intervals, TEC flow rates)
  - Detects XML well-formedness issues
  - Warns about edge list issues (empty, duplicates)

- **New Response Models**: `api/models/responses/validation_responses.py` (300+ lines)
  - `ValidationResult`: Validation outcome with errors/warnings
  - `ValidationError`: Structured error information
  - `ValidationWarning`: Structured warning information
  - `ValidationStatusResponse`: API response model

- **Enhanced Parameter Transformation**: `shared/control_tools/additional_generator.py`
  - Time conversion with case metadata support (hours → seconds)
  - Two-layer vehicle type conversion (UI types → SUMO vClass)
  - Comprehensive assertions for parameter constraints

- **Test Suite**: 63 unit tests (100% passing)
  - 30 parameter transformation tests
  - 33 XML validator tests
  - Real strategy instance validation

#### Cascade Regeneration (Phase 2)
- **Enhanced Plan Regeneration**: `shared/control_tools/plan_file_manager.py`
  - XML validation integrated into regeneration workflow
  - Validation failures block XML save
  - Returns validation results in API response

- **Service Layer Enhancement**: `api/services/control_plan_service.py`
  - Service method returns validation results
  - Structured logging with validation metrics

- **Cascade Regeneration Logging**: `api/services/strategy_instance_service.py`
  - Comprehensive audit logging with CASCADE_* events
  - Performance tracking (duration_seconds)
  - Error categorization (validation_error vs. regeneration_error)
  - Success/failure counters

- **API Enhancement**: `POST /api/v1/control/plans/{plan_id}/generate_additional`
  - Response now includes `validation` field with validation results
  - Backward compatible (existing clients can ignore new field)

#### Frontend Validation Button (Phase 3.4)
- **JavaScript Modules** (357 lines total):
  - `frontend/control/js/ui-utils.js`: Toast notifications, Modal dialogs, XSS protection
  - `frontend/control/js/plan-validation-ui.js`: Validation status display updates
  - `frontend/control/js/plan-validation.js`: Validation business logic and API orchestration

- **CSS Stylesheets** (310 lines total):
  - `frontend/control/css/plan-validation.css`: Validation feature styles
  - `frontend/control/css/ui-utils.css`: Reusable UI component styles
  - Responsive design (mobile/tablet/desktop)
  - Optional dark theme support

- **Code Quality**:
  - HTML/CSS/JS three-layer separation (0 inline styles/events)
  - Single responsibility principle (functions ≤30 lines, parameters ≤5)
  - XSS protection via `escapeHTML()` function
  - Event delegation for scalability

#### Documentation & Migration (Phase 3)
- **Migration Guide**: `docs/migration/validate-strategy-xml-generation.md`
  - Comprehensive migration instructions
  - Backward compatibility analysis
  - Validation rules reference
  - Troubleshooting guide
  - Deployment checklist

- **Validation Script**: `scripts/validate_existing_plans.py`
  - Scans existing plans for validation issues
  - Reports invalid plans with detailed errors
  - JSON report export option

- **CLAUDE.md Updates**: Added "Plan XML Validation (v0.9.0+)" section
  - Backend validation documentation
  - Frontend integration guide
  - API reference
  - Code quality standards

### Changed
- **Plan XML Generation**: Now includes validation step before saving
- **Strategy Updates**: Trigger automatic cascade regeneration of referencing plans
- **API Response Format**: `/plans/{plan_id}/generate_additional` endpoint enhanced with `validation` field

### Fixed
- **Bug**: Prevented invalid SUMO XML generation that could cause simulation failures
- **Issue**: Plans with out-of-range parameters (speed >200 km/h, time >24h) now rejected during creation

### Technical Details
- **Lines of Code Added**: ~2000 lines (backend + frontend + tests)
- **Test Coverage**: >95% on validation modules
- **Performance Impact**: ~10-20ms validation overhead per plan (negligible)
- **Backward Compatibility**: ✅ Fully backward compatible

### Migration Notes
- **Action Required**: Run `python scripts/validate_existing_plans.py` to check existing plans
- **Deployment**: See `docs/migration/validate-strategy-xml-generation.md` for full guide
- **Rollback**: Documented in migration guide (comment out validation check if needed)

### References
- **OpenSpec Proposal**: `openspec/changes/validate-strategy-xml-generation/proposal.md`
- **Phase 1 Report**: `openspec/changes/validate-strategy-xml-generation/PHASE1_FINAL_REPORT.md`
- **Phase 2 Report**: `openspec/changes/validate-strategy-xml-generation/PHASE2_COMPLETION_REPORT.md`
- **Phase 3 Summary**: `openspec/changes/validate-strategy-xml-generation/SESSION_CONTINUATION_SUMMARY.md`

---

## [v0.8.0] - 2024-11

### Added
- EdgeData analysis integration
- Complete analysis toolchain (accuracy, mechanism, performance, EdgeData)

### Changed
- Analysis workflow improvements

---

## [v0.7.0] - 2024-10

### Added
- Vehicle template configuration system
- Default template updates
- Frontend optimization

### Changed
- Migrated from hardcoded vehicle types to JSON templates

---

## [v0.65] - 2024-09

### Added
- Three analysis types: accuracy, mechanism, performance
- Automated testing validation

### Changed
- Architecture refactoring (two-layer modular architecture)

---

## Format Guidelines

Each entry should include:
- **Version number** and **release date**
- **Added/Changed/Deprecated/Removed/Fixed/Security** sections
- **OpenSpec change ID** (if applicable)
- **Brief description** of changes
- **Technical details** (lines of code, test coverage, performance impact)
- **Migration notes** (if breaking changes)
- **References** to detailed documentation

---

**Note**: This CHANGELOG was created in v0.9.0. Previous version entries are backfilled based on project history. Future releases will update this file following the format above.
