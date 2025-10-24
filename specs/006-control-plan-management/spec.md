# Feature Specification: 方案管理 (Control Plan Management) - Phase 2

**Feature Branch**: `006-control-plan-management`
**Created**: 2025-10-24
**Status**: Draft
**Input**: Phase 2 方案管理 - 实现方案的组建和SUMO Additional文件生成

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 创建交通管控方案 (Priority: P1)

用户需要创建一个交通管控方案，将多个已有的管控策略组合在一起。方案是进行批量仿真对比的基础单位，每个方案可以包含多个不同类型的策略（VSS、DHS、TEC）。

**Why this priority**: 这是实现方案管理的核心功能。用户必须能够创建方案才能进行后续的仿真和优化。完成后，用户拥有"方案"概念，可以组织多个策略进行仿真。

**Independent Test**: 用户可以从现有策略库中选择多个策略，创建一个新方案，并验证方案包含正确的策略列表。

**Acceptance Scenarios**:

1. **Given** 用户已创建至少3个管控策略，**When** 用户在方案管理页面创建新方案，**Then** 系统显示可用策略列表供选择
2. **Given** 用户选择了多个策略，**When** 用户输入方案名称和描述，**Then** 系统创建方案并保存所有策略关联
3. **Given** 方案已成功创建，**When** 用户查看方案列表，**Then** 新创建的方案出现在列表中，显示包含的策略数量

---

### User Story 2 - 生成SUMO Additional配置文件 (Priority: P1)

系统需要自动生成SUMO Additional XML文件，将用户选择的管控策略转换为SUMO可以识别的控制命令。系统应支持三种策略类型的XML生成：VSS（可变限速）、DHS（动态硬路肩）、TEC（入口控制）。

**Why this priority**: 这是实现管控仿真的技术关键。没有正确生成的Additional文件，管控策略无法在SUMO中生效。这直接影响整个系统的可用性。

**Independent Test**: 用户创建包含各类型策略的方案后，系统生成Additional XML文件，该文件可被验证为有效的XML格式并包含所有策略定义。

**Acceptance Scenarios**:

1. **Given** 方案包含一个VSS策略（可变限速），**When** 系统生成Additional文件，**Then** XML包含正确的`<variableSpeedSign>`元素，指定目标路段和限速值
2. **Given** 方案包含一个DHS策略（动态硬路肩），**When** 系统生成Additional文件，**Then** XML包含`<rerouter>`和`<closingLaneReroute>`元素
3. **Given** 方案包含一个TEC策略（入口控制），**When** 系统生成Additional文件，**Then** XML包含`<calibrator>`或`<closingReroute>`元素（根据策略配置）
4. **Given** 方案包含多个策略（VSS+DHS+TEC），**When** 系统生成Additional文件，**Then** XML元素按正确顺序排列（VSS → DHS → TEC），不产生冲突

---

### User Story 3 - 浏览和编辑方案 (Priority: P2)

用户需要能够查看已创建方案的详细信息、修改方案中的策略组合、查看生成的Additional XML内容，并能删除不需要的方案。

**Why this priority**: 虽然创建是P1，但编辑和查看是完整方案管理的必要功能，使用户能够迭代和改进他们的方案设计。

**Independent Test**: 用户能够打开现有方案，修改其策略组成，查看生成的XML预览，保存或删除方案。

**Acceptance Scenarios**:

1. **Given** 用户打开现有方案，**When** 用户从方案中移除一个策略，**Then** 系统更新方案并重新生成Additional文件
2. **Given** 方案已生成Additional文件，**When** 用户查看方案详情，**Then** 系统显示生成的XML内容（代码高亮）和预览区域
3. **Given** 用户决定删除一个方案，**When** 用户点击删除按钮确认，**Then** 方案被删除，列表更新

---

### User Story 4 - 方案版本管理（支持基准方案） (Priority: P2)

系统应支持"基准方案"（无管控策略的方案），用于与有管控的方案对比分析。用户也应能够管理不同版本的方案变体。

**Why this priority**: 基准方案是进行对比分析的前提。没有基准方案作为参照，无法评估管控策略的效果。

**Independent Test**: 用户能够创建一个基准方案（空的策略列表），并将其与其他方案进行对比。

**Acceptance Scenarios**:

1. **Given** 系统初始化，**When** 用户创建新方案时留空策略选择，**Then** 系统创建基准方案并标记为"基准"
2. **Given** 基准方案和一个含策略的方案都存在，**When** 用户选择这两个方案，**Then** 系统支持对比分析（后续Phase的功能）

---

### Edge Cases

- **What happens when** 用户选择两个作用于同一路段但参数冲突的策略时？系统应检测冲突并提示用户（或根据优先级自动处理）
- **How does system handle** Additional文件生成失败的情况？系统应显示清晰的错误信息指出具体问题（如路段编号无效）
- **What happens when** 用户尝试删除被批量仿真任务引用的方案？系统应防止删除，提示用户该方案正在使用
- **What happens when** 方案包含过多策略导致生成的XML文件过大？系统应有合理的限制并提示用户

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统MUST能够为每个方案关联多个已创建的管控策略
- **FR-002**: 系统MUST根据方案中的策略列表生成有效的SUMO Additional XML文件
- **FR-003**: 系统MUST支持VSS策略转换为`<variableSpeedSign>`XML元素
- **FR-004**: 系统MUST支持DHS策略转换为`<rerouter>`和`<closingLaneReroute>`XML元素
- **FR-005**: 系统MUST支持TEC策略转换为`<calibrator>`或`<closingReroute>`XML元素
- **FR-006**: 系统MUST在Additional XML中按正确顺序组织元素（VSS → DHS → TEC）
- **FR-007**: 系统MUST为方案提供完整的CRUD操作（创建、读取、更新、删除）
- **FR-008**: 系统MUST支持创建基准方案（空策略列表），用于对比分析
- **FR-009**: 系统MUST验证方案中的策略不存在冲突或依赖问题
- **FR-010**: 系统MUST持久化方案数据，包括方案名称、描述、策略列表和生成的Additional内容
- **FR-011**: 系统MUST提供方案列表API，支持分页和基本筛选
- **FR-012**: 前端MUST提供直观的方案管理界面，支持策略选择和可视化编辑
- **FR-013**: 系统MUST生成的Additional文件可导出为独立的XML文件供SUMO使用
- **FR-014**: 系统MUST显示生成的Additional XML预览，并支持代码高亮

### Key Entities *(include if feature involves data)*

- **Plan（方案）**:
  - 属性：plan_id, plan_name, description, status, created_at, updated_at
  - 关系：包含多个Strategy（管控策略）
  - 行为：可生成Additional XML文件

- **Strategy（管控策略）**:
  - 属性：strategy_id, strategy_name, template_id, selected_edges, parameters
  - 关系：属于某个Plan（方案）
  - 来源：来自Phase 1C创建的策略实例

- **Additional XML**:
  - 生成的SUMO配置片段，包含VSS、DHS、TEC控制命令
  - 与Plan一对一关联
  - 可导出为独立文件

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户能在2分钟内创建包含3个策略的方案
- **SC-002**: 系统生成的Additional XML文件的验证通过率为100%（格式有效、包含所有策略定义）
- **SC-003**: 方案CRUD操作的响应时间 <500ms
- **SC-004**: 系统支持至少500个路段的管控方案，Additional文件大小 <1MB
- **SC-005**: 生成的Additional XML能被SUMO v1.18+正确识别和加载
- **SC-006**: 用户对方案管理界面的易用性评分 ≥4/5（若进行用户测试）
- **SC-007**: 系统能检测和提示95%以上的策略冲突场景

---

## Architecture & Data Model

### API 端点设计

```
POST   /api/v1/control/plans/                    # 创建方案
GET    /api/v1/control/plans/                    # 获取方案列表
GET    /api/v1/control/plans/{plan_id}           # 获取方案详情
PUT    /api/v1/control/plans/{plan_id}           # 更新方案
DELETE /api/v1/control/plans/{plan_id}           # 删除方案
POST   /api/v1/control/plans/{plan_id}/generate  # 生成Additional文件
GET    /api/v1/control/plans/{plan_id}/additional # 获取Additional XML内容
```

### 数据存储

- **方案文件**: `control_data/plans/{plan_id}.json`
- **方案索引**: `control_data/plans/plans_index.json`
- **Additional文件**: `control_data/plans/{plan_id}/additional.xml`

### 核心工具模块

- **additional_generator.py**: 生成Additional XML
  - `generate_vss_xml(strategy)` - VSS元素生成
  - `generate_dhs_xml(strategy)` - DHS元素生成
  - `generate_tec_xml(strategy)` - TEC元素生成
  - `generate_control_additional(plan, strategies)` - 完整方案转换

- **plan_manager.py**: 方案持久化和管理
  - 方案CRUD操作
  - 索引维护

---

## Assumptions

1. 策略冲突检测采用简单的"同一路段不同策略类型允许，相同类型不允许"的规则
2. Additional文件生成基于SUMO v1.18+文档标准
3. 方案和策略之间采用松散耦合设计，删除策略不自动删除包含它的方案
4. 用户有权限创建/编辑/删除他们创建的方案（暂不考虑跨用户共享）
5. Basic方案（无策略）仅用于对比分析，不会被用于实际仿真

---

## Out of Scope

- 方案版本控制（如git风格的版本历史）
- 方案权限管理和多用户协作
- 方案模板预设
- 自动优化建议
- A/B测试框架集成

这些功能可在后续迭代中添加。

---

## Dependencies & Risks

### Dependencies

- Phase 1C完成（策略实例创建和管理）
- SUMO官方文档中关于Additional文件格式的准确信息
- 数据库中关于路段有效性的验证

### Risks

- **技术风险**: Additional XML格式生成错误可能导致SUMO无法加载
  - 缓解：提前创建测试用例验证生成的XML
- **数据一致性风险**: 策略被修改或删除时，方案中的引用需要同步更新
  - 缓解：设计策略变更时的级联更新规则
- **性能风险**: 大规模方案（1000+路段）的Additional文件生成可能变慢
  - 缓解：设置限制并优化生成算法

---

## Next Steps

1. 获得用户/产品确认本规格描述准确
2. 运行 `/speckit.clarify` 澄清任何不清晰的地方
3. 运行 `/speckit.plan` 生成详细实施计划
4. 运行 `/speckit.tasks` 生成具体任务清单
5. 开始实施开发
