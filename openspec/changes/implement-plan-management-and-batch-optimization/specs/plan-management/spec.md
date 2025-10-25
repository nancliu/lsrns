# 规格：方案管理 (Plan Management)

**能力ID**: plan-management
**关联变更**: implement-plan-management-and-batch-optimization
**版本**: 1.0

---

## ADDED Requirements

### Requirement: 用户可以创建包含多个策略的管控方案

用户MUST能够选择多个已创建的策略实例（VSS/DHS/TEC），将它们组合成一个完整的管控方案。系统MUST自动生成方案ID、验证策略存在性、生成SUMO配置文件，并跟踪策略引用关系。

**优先级**: P0
**状态**: 新增

#### Scenario: 创建包含3个策略的综合管控方案

**Given**:
- 系统中已存在3个策略实例
  - strategy_001: VSS类型（K10-K15限速80km/h）
  - strategy_002: DHS类型（K15-K20应急车道开放）
  - strategy_003: TEC类型（K18入口流量控制）
- 用户已登录方案管理页面

**When**:
- 用户点击"新建方案"按钮
- 填写方案名称"早高峰综合管控方案A"
- 填写描述"缓解K10-K15路段早高峰拥堵"
- 选择strategy_001、strategy_002、strategy_003
- 添加标签"早高峰"、"综合管控"
- 填写目标场景"工作日早高峰(7:00-9:00)"
- 点击"创建方案"按钮

**Then**:
- 系统生成plan_id（格式：plan_YYYYMMDD_HHMMSS_xxxxx）
- 系统创建方案目录：control_data/plans/{plan_id}/
- 系统保存plan_metadata.json，包含所有输入信息
- 系统保存strategy_refs.json，包含["strategy_001", "strategy_002", "strategy_003"]
- 系统调用additional_generator生成control.add.xml
- control.add.xml包含3个策略的XML元素（按VSS→DHS→TEC顺序）
- 系统更新plans_index.json添加新方案
- 系统为3个策略增加引用计数（referenced_by字段）
- 返回成功响应，包含plan_id和验证警告（如有）
- 前端显示成功消息，跳转到方案详情页面

---

#### Scenario: 创建方案时引用不存在的策略

**Given**:
- 用户在方案创建页面

**When**:
- 用户填写方案信息
- 用户选择策略ID列表包含不存在的"strategy_999"
- 点击"创建方案"按钮

**Then**:
- 系统验证策略存在性失败
- 返回400错误："策略 strategy_999 不存在"
- 方案未创建
- 前端显示错误消息

---

### Requirement: 系统自动生成方案的SUMO配置文件

系统在方案创建时MUST自动调用additional_generator，将所有包含的策略合并生成一个统一的control.add.xml文件。XML元素按策略类型排序（VSS→DHS→TEC），包含完整的注释和格式化。

**优先级**: P0
**状态**: 新增

#### Scenario: 生成包含多种策略类型的control.add.xml

**Given**:
- 方案plan_001包含3个策略
  - strategy_vss_001（VSS类型）
  - strategy_dhs_002（DHS类型）
  - strategy_tec_003（TEC类型）

**When**:
- 系统创建方案plan_001
- 调用additional_generator.generate_plan_additional()

**Then**:
- 生成的XML文件包含正确的XML声明
- 包含<additional>根元素
- 包含方案注释："<!-- 方案: 早高峰综合管控方案A (plan_001) -->"
- 包含生成时间注释
- 包含3个策略组注释："<!-- ==================== VSS策略组 ==================== -->"
- 每个策略前包含单独注释："<!-- 策略: strategy_vss_001 - K10-K15限速80km/h -->"
- 策略按类型排序：VSS → DHS → TEC
- 每个策略的XML元素格式正确
- XML格式化（缩进4空格）
- 文件保存到control_data/plans/plan_001/control.add.xml

---

#### Scenario: 生成空方案（基准方案）的control.add.xml

**Given**:
- 基准方案baseline_plan
- strategy_ids为空数组[]

**When**:
- 系统生成基准方案的XML

**Then**:
- 生成的XML仅包含<additional>根元素
- 包含注释："<!-- 基准方案：无管控 -->"
- 无任何策略元素
- 文件有效且格式正确

---

### Requirement: 用户可以查看方案列表和详情

用户MUST能够通过API获取所有方案的列表（支持按标签、场景过滤和排序），以及查看单个方案的完整详情（包含所有引用的策略信息、元数据和配置文件路径）。

**优先级**: P0
**状态**: 新增

#### Scenario: 查看所有方案列表

**Given**:
- 系统中存在3个方案
  - baseline_plan（基准方案）
  - plan_001（包含2个策略）
  - plan_002（包含1个策略）

**When**:
- 用户访问GET /api/v1/control/plans/

**Then**:
- 返回200响应
- 返回方案列表，包含3个方案
- 每个方案包含：plan_id, plan_name, is_baseline, strategy_count, tags, created_at
- baseline_plan的is_baseline为true
- plan_001的strategy_count为2
- 方案按created_at降序排列

---

#### Scenario: 按标签过滤方案列表

**Given**:
- 系统中存在多个方案，部分包含标签"早高峰"

**When**:
- 用户访问GET /api/v1/control/plans/?tags=早高峰

**Then**:
- 返回仅包含标签"早高峰"的方案
- 其他方案不包含在结果中

---

#### Scenario: 查看方案详情

**Given**:
- 方案plan_001存在，包含2个策略

**When**:
- 用户访问GET /api/v1/control/plans/plan_001

**Then**:
- 返回200响应
- 返回完整方案信息
- 包含strategy_ids数组
- 包含strategies数组，每个策略包含：strategy_id, strategy_name, strategy_type, template_id
- 包含additional_file_path
- 包含所有元数据字段

---

### Requirement: 用户可以更新和删除方案

用户MUST能够修改方案的任何属性（策略列表、标签、描述、目标场景等）。当策略列表变化时，系统自动重新生成XML并调整引用计数。用户也可以删除方案（基准方案除外），系统自动清理所有相关文件和引用。

**优先级**: P0
**状态**: 新增

#### Scenario: 更新方案的策略组合

**Given**:
- 方案plan_001当前包含策略["strategy_001", "strategy_002"]

**When**:
- 用户发送PUT /api/v1/control/plans/plan_001
- 请求体包含：strategy_ids: ["strategy_001", "strategy_003"]

**Then**:
- 系统验证strategy_003存在
- 系统更新plan_metadata.json
- 系统更新strategy_refs.json
- 系统重新生成control.add.xml（包含strategy_001和strategy_003）
- 系统减少strategy_002的引用计数
- 系统增加strategy_003的引用计数
- 更新updated_at时间戳
- 返回200响应和更新后的方案信息

---

#### Scenario: 删除方案

**Given**:
- 方案plan_001存在，包含2个策略
- 方案未被批量仿真使用

**When**:
- 用户发送DELETE /api/v1/control/plans/plan_001

**Then**:
- 系统减少所有引用策略的引用计数
- 系统删除方案目录control_data/plans/plan_001/
- 系统从plans_index.json中移除方案
- 返回204响应

---

#### Scenario: 尝试删除基准方案

**Given**:
- 基准方案baseline_plan存在

**When**:
- 用户发送DELETE /api/v1/control/plans/baseline_plan

**Then**:
- 系统拒绝删除
- 返回400错误："无法删除基准方案"
- 基准方案保持不变

---

### Requirement: 系统验证方案配置并提供警告

系统MUST在方案创建或更新时自动验证策略组合的合理性，包括空间冲突检测、时间协调检查、策略类型兼容性分析等。验证采用警告模式，返回详细的警告信息和优化建议，但不阻止方案创建。

**优先级**: P1
**状态**: 新增

#### Scenario: 验证方案的时间协调性

**Given**:
- 方案包含2个策略
  - VSS策略：time_begin=25200（7:00）
  - DHS策略：time_begin=25200（7:00，应急车道开放）

**When**:
- 用户创建或验证方案
- 调用plan_validator.validate_plan()

**Then**:
- 系统检测到时间协调问题
- 返回警告：
  - type: "timing_coordination"
  - severity: "medium"
  - message: "建议VSS策略提前5分钟生效，避免急刹车"
  - suggestion: "将VSS的time_begin改为24900"
- is_valid仍为true（警告模式）
- 方案可以成功创建

---

#### Scenario: 验证方案的空间冲突

**Given**:
- 方案包含2个VSS策略，都控制edge_800

**When**:
- 验证方案

**Then**:
- 系统检测到空间冲突
- 返回警告：
  - type: "spatial_conflict"
  - severity: "high"
  - message: "edge_800 被多个VSS策略控制"
  - suggestion: "检查是否需要合并策略或调整控制范围"
- is_valid仍为true

---

### Requirement: 用户可以预览方案效果

用户MUST能够在应用方案前预览其完整影响范围和配置细节，包括受影响的路段列表、时间段统计、策略类型分布、每个策略的具体配置，以及生成的SUMO XML配置预览。

**优先级**: P1
**状态**: 新增

#### Scenario: 预览方案的策略组合和影响范围

**Given**:
- 方案plan_001包含3个策略

**When**:
- 用户访问POST /api/v1/control/plans/plan_001/preview

**Then**:
- 返回预览信息：
  - total_strategies: 3
  - strategy_types: {"VSS": 1, "DHS": 1, "TEC": 1}
  - affected_edges: ["edge_800", "edge_801", ...]
  - affected_edge_count: 10
  - time_range: {earliest: 24900, latest: 32400}
- 包含每个策略的详细信息：
  - strategy_id, strategy_name, strategy_type
  - affected_objects（edge/lane列表）
  - active_periods（时间段列表）
- 包含xml_preview（前100行或完整XML）

---

### Requirement: 用户可以手动重新生成方案XML

用户MUST能够手动触发重新生成方案的control.add.xml文件，用于修复损坏或丢失的配置文件、强制同步最新的策略配置，或在策略更新后主动刷新方案配置。

**优先级**: P2
**状态**: 新增

#### Scenario: 手动重新生成损坏的XML文件

**Given**:
- 方案plan_001的control.add.xml文件损坏或丢失

**When**:
- 用户访问POST /api/v1/control/plans/plan_001/generate_additional

**Then**:
- 系统重新加载方案的所有策略
- 调用additional_generator重新生成XML
- 保存新的control.add.xml
- 返回200响应："XML重新生成成功"

---

## MODIFIED Requirements

（无，这是新增功能）

---

## REMOVED Requirements

（无，这是新增功能）

---

## 非功能性需求

### 性能要求

- 方案列表加载时间 <500ms（100个方案以内）
- 方案创建时间（含XML生成） <2s
- 方案详情加载时间 <300ms
- XML重新生成时间 <1s

### 数据完整性

- 方案ID全局唯一
- 策略引用计数准确
- plans_index.json与方案目录同步
- 事务性操作（创建失败时回滚）

### 可用性

- 所有API端点返回明确的错误消息
- 验证警告清晰易懂
- 前端加载状态和错误提示完整

### 安全性

- 输入验证：所有用户输入通过Pydantic验证
- 路径验证：防止目录遍历攻击
- 资源限制：方案数量上限（可配置）

---

## 测试策略

### 单元测试覆盖

- plan_file_manager: 所有CRUD方法
- additional_generator: generate_plan_additional方法
- plan_validator: 所有验证规则
- control_plan_service: 所有服务方法
- control_plan_routes: 所有API端点

### 集成测试

- 方案创建 → XML生成 → 策略引用计数更新
- 方案更新 → XML重新生成 → 引用计数调整
- 方案删除 → 引用计数减少 → 目录清理

### E2E测试

- 完整方案管理工作流（创建→编辑→预览→删除）
- 方案验证警告显示
- 前端与后端交互
