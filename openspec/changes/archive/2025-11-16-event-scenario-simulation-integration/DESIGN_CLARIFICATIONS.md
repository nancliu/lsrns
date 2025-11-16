# Design Clarifications Summary

**Date**: 2025-11-12
**Status**: Resolved
**Impact**: Non-Breaking Extension

---

## Resolved Design Issues

### ISSUE 1: Integration with Existing Workflows ✅

**Q1**: SimulationExecutionService定位
- **Decision**: 选项C - 创建编排层(SimulationOrchestrator)，根据仿真来源分发
- **Rationale**: 保持现有工作流不变，复用BatchSimulationScheduler

**Q2**: 与BatchOptimizationService的关系
- **Decision**: 复用BatchSimulationScheduler，不创建新基础设施
- **Implementation**: SimulationOrchestrator通过适配器访问BatchSimulationScheduler

**Q3**: 元数据兼容性
- **Decision**: 向后兼容，检测metadata_version字段
- **Strategy**: 旧案例(v1.0)无source_scenario字段，新案例(v2.0)有该字段

---

### ISSUE 2: Case Creation Duplication ✅

**Q4**: 端点数量
- **Decision**: 两个独立端点
  - `POST /api/v1/case/create` - OD提取案例
  - `POST /api/v1/case/create-from-scenario` - 事件场景案例
- **Rationale**: 业务语义不同，请求参数不同，向后兼容

**Q5**: 元数据Schema兼容性
- **Decision**: 使用metadata_version字段区分
  - Version 1.0: 无metadata_version字段(隐式)
  - Version 2.0: "metadata_version": "2.0"
- **Strategy**: Services检测版本并适配行为

---

### ISSUE 3: Simulation Metadata ✅

**Q6**: 旧仿真兼容性
- **Decision**: 不会失败，所有新字段可选
- **Implementation**: Services null-safe读取source_scenario字段

**Q7**: Schema迁移策略
- **Decision**: 选项A + 版本字段
- **Strategy**: 双Schema并存，Services检测版本

---

### ISSUE 4: Analysis Service Integration ✅

**Q8**: 服务接口兼容性
- **Decision**: 不复用OD分析服务(accuracy/mechanism/performance/edgedata_service)
- **Reuses**: SummaryAnalyzer + EdgeDataAnalyzer (shared layer, unchanged)
- **Rationale**: OD服务接口不兼容事件场景结构

**Q9**: 分析服务修改范围
- **Decision**: 选项A - 不修改现有服务，创建适配层
- **Implementation**: AnalysisOrchestrationService作为适配层
- **Architecture**:
  - SummaryAnalyzer (shared) ← Unchanged
  - EdgeDataAnalyzer (shared) ← Unchanged
  - AnalysisOrchestrationService (api) ← NEW adapter

---

### ISSUE 5: Relative Path Generation ✅

**Q12**: 路径存储权威性
- **Decision**: 统一使用相对路径
  - **Metadata**: 相对于项目根(source of truth)
  - **sumocfg**: 相对于sumocfg位置(从metadata生成)
- **Authority**: Metadata是权威源，sumocfg按需生成

---

### ISSUE 6: Frontend Refactoring ✅

**Q13**: 重构影响
- **Decision**: 渐进式重构，Phase 2不修改现有代码
- **Impact**:
  - script.js (index.html) ← NOT modified
  - Control plan UI ← NOT affected
  - Phase 1 scenario browser ← NOT affected
- **Strategy**: 创建新组件，不触碰现有页面

**Q14**: 组件可复用性
- **Decision**: simulation-monitor.js设计为通用组件
- **Supports**:
  - Event-scenario simulations (Phase 2 实现)
  - OD extraction simulations (未来兼容)
  - Control plan simulations (现有，考虑兼容性)

---

## Architecture Decisions Summary

| Component | Strategy | Impact on Existing |
|-----------|----------|-------------------|
| **SimulationOrchestrator** | NEW orchestration layer, delegates by source | ZERO - Delegation pattern |
| **AnalysisOrchestrationService** | NEW adapter layer, reuses batch tools | ZERO - No interface changes |
| **BatchSimulationScheduler** | Reused via adapter | ZERO - Unchanged |
| **SummaryAnalyzer/EdgeDataAnalyzer** | Reused directly | ZERO - Unchanged |
| **OD Analysis Services** | NOT used | ZERO - Unchanged |
| **Case Metadata** | Version 2.0 schema, optional fields | ZERO - V1.0 continues working |
| **Simulation Metadata** | Version 2.0 schema, optional fields | ZERO - V1.0 continues working |
| **Frontend Components** | NEW components only | ZERO - No modifications to existing |

---

## Non-Breaking Principles

### PRINCIPLE-INTEGRATION-001: Non-Breaking Extension
- New services DO NOT modify existing service interfaces
- New metadata fields are OPTIONAL for backward compatibility
- New APIs use separate endpoints (not override existing)

### PRINCIPLE-INTEGRATION-002: Workflow Isolation
- Event-scenario workflow code isolated in dedicated services
- Shared infrastructure accessed via adapters
- Existing OD/Control Plan workflows continue unchanged

### PRINCIPLE-INTEGRATION-003: Gradual Migration
- Old and new metadata schemas coexist
- Services detect schema version and adapt
- Migration tools provided but not mandatory

---

## Validation Checklist

- [x] Q1-C: SimulationOrchestrator creates orchestration layer
- [x] Q2: Reuses BatchSimulationScheduler
- [x] Q3: Backward compatible metadata detection
- [x] Q4: Two separate case creation endpoints
- [x] Q5: metadata_version field for schema versioning
- [x] Q6: Old simulations will not fail
- [x] Q7: Dual schema support with version detection
- [x] Q8: Does not use OD analysis services
- [x] Q9: Creates adapter, does not modify existing services
- [x] Q12: Unified relative path strategy
- [x] Q13: Incremental frontend refactoring
- [x] Q14: Generic simulation-monitor component

---

## Implementation Priority

1. **P0 (Week 1)**: Metadata versioning + SimulationOrchestrator
2. **P0 (Week 1)**: AnalysisOrchestrationService adapter
3. **P1 (Week 2)**: Relative path generation
4. **P1 (Week 2)**: Frontend components (generic)
5. **P2 (Week 3)**: Results visualization

---

**Status**: All design clarifications resolved. Ready for implementation.
