# strategy-configuration-ux Specification

## Purpose

Define the user experience and functional requirements for the strategy parameter configuration page (Step 3 in strategy creation workflow), ensuring users can successfully configure all parameter types, verify edge selections, and create well-named, self-documented strategy instances.

## Requirements

### ADDED Requirement: Enhanced Parameter Input Components

The system SHALL provide specialized input components for each template parameter type, with clear format guidance, examples, and real-time validation to ensure successful parameter entry.

#### Scenario: Array parameter with smart placeholder

- **WHEN** user encounters an array-type parameter (e.g., `time_intervals`, `speed_steps`, `allowed_vehicle_types`)
- **THEN** system displays textarea with:
  - Context-aware placeholder based on parameter name and type
  - Example values from template's default_value if available
  - Format hint explaining supported input formats (newline-separated, comma-separated, JSON)
  - Minimum height of 100px for visibility
  - Monospace font for structured data clarity
- **THEN** placeholder examples:
  - **For `time_intervals`**: `示例格式:\n[\n  [7, 9],\n  [17, 19]\n]\n\n每行一个时间段 [开始小时, 结束小时]`
  - **For `speed_steps`**: `限速值示例(每行一个):\n80\n60\n40\n\n或JSON格式:[80, 60, 40]`
  - **For `allowed_vehicle_types`**: `车型列表示例:\npassenger\ntruck\nbus\n\n或用逗号分隔:passenger, truck, bus`
  - **For `affected_edges`**: `路段ID列表示例:\n-5880\n-5881\n-5882\n\n或用逗号分隔:-5880, -5881, -5882`

#### Scenario: Nested array parameter (time intervals)

- **WHEN** parameter has nested array default value (e.g., `[[7, 9], [17, 19]]`)
- **THEN** system pre-fills textarea with JSON format:
  ```
  [
    [7, 9],
    [17, 19]
  ]
  ```
- **THEN** placeholder explains: `示例格式:\n[[开始小时, 结束小时], ...]\n可直接编辑JSON或每行输入一个时段`
- **THEN** user can edit JSON directly or replace with simpler format

#### Scenario: Simple array parameter (vehicle types)

- **WHEN** parameter has simple array default value (e.g., `["passenger", "truck"]`)
- **THEN** system pre-fills textarea with newline-separated format:
  ```
  passenger
  truck
  ```
- **THEN** user can add/remove lines or use comma-separated format: `passenger, truck, bus`
- **THEN** system accepts both formats on submission

#### Scenario: Array parameter without default value

- **WHEN** parameter has no default value but name suggests type (e.g., `entrance_edges`)
- **THEN** system provides smart placeholder based on naming patterns:
  - Contains "entrance": Show entrance edge ID examples
  - Contains "speed": Show speed value examples
  - Contains "time"|"interval": Show time period examples
  - Contains "vehicle": Show vehicle type examples
  - Generic fallback: Multi-line value format hint
- **THEN** placeholder is clickable to auto-fill with example

#### Scenario: Number parameter with range constraint

- **WHEN** parameter is integer/float with min/max values (e.g., `speed_limit` with min=30, max=130)
- **THEN** system displays number input with:
  - Input type="number" with appropriate step (1 for integer, 0.01 for float)
  - HTML min/max attributes set from schema
  - Unit label displayed after input (e.g., "km/h")
  - Hint text showing valid range: `范围: 30-130 | 单位: km/h`
- **THEN** on blur, validates value is within range
- **THEN** if out of range, shows inline error: `值不能小于30` or `值不能大于130`

#### Scenario: String parameter with pattern constraint

- **WHEN** parameter has regex pattern constraint (e.g., strategy name with maxLength=100)
- **THEN** system displays text input with:
  - maxLength HTML attribute
  - Pattern HTML attribute if applicable
  - Character counter if maxLength defined: `42/100 字符`
  - Hint showing format requirements
- **THEN** on blur, validates against pattern
- **THEN** if pattern mismatch, shows error: `格式不正确` with pattern description

#### Scenario: Boolean parameter

- **WHEN** parameter is boolean type
- **THEN** system displays select dropdown with:
  - Option "是" (value="true")
  - Option "否" (value="false", selected by default)
  - Default value from template pre-selected
- **THEN** clear label explaining what true/false means in context

#### Scenario: Enum parameter

- **WHEN** parameter has allowed_values constraint (e.g., `control_mode` with values ["metering", "closure"])
- **THEN** system displays select dropdown with:
  - One option per allowed value
  - Human-readable label for each value (from template metadata if available)
  - Default value pre-selected
  - Hint explaining each option's meaning
- **THEN** user cannot enter custom values (dropdown only)

#### Scenario: Real-time format hint updates

- **WHEN** parameter name or default value changes during form generation
- **THEN** hint text updates to reflect current parameter context
- **THEN** placeholder adapts to show relevant examples
- **THEN** validation rules adjust to parameter constraints

### ADDED Requirement: Comprehensive Edge Selection Display

The system SHALL display selected edges in a detailed, readable table format showing all relevant attributes to enable verification before strategy creation.

#### Scenario: Display full edge information table

- **WHEN** user is on Step 3 (Configure Parameters) after selecting edges in Step 2
- **THEN** system displays "已选路段" (Selected Edges) section with table containing columns:
  | Column | Description | Example Value |
  |--------|-------------|---------------|
  | 序号 | Row number | 1, 2, 3 |
  | Edge ID | Unique edge identifier | -5880, edge_k10_001 |
  | 路线 | Route code | G4202, SA2, G5 |
  | 路段 | Section code | K10-K15 |
  | 起始桩号 | Start stake (km) | K10+200 |
  | 结束桩号 | End stake (km) | K10+800 |
  | 长度 | Edge length (m) | 600m |
  | 车道数 | Lane count | 4 |
  | 方向 | Direction | 顺时针, 上行 |
  | 节点类型 | Node type | entrance, normal, merging |
  | 操作 | Actions | [移除] button |
- **THEN** table is sortable by stake order (default sort)
- **THEN** table shows pagination if >20 edges selected

#### Scenario: Show edge count summary

- **WHEN** selected edges table is displayed
- **THEN** system shows summary above table:
  - "已选择 15 个路段" (15 edges selected)
  - "总长度: 8.5 km" (total length sum)
  - "覆盖路线: G4202, SA2" (unique routes)
  - "车道数范围: 3-5" (min-max lane count)
- **THEN** summary updates dynamically if edges are removed

#### Scenario: Inline edge removal

- **WHEN** user clicks [移除] button in edge table row
- **THEN** system removes edge from selected list
- **THEN** table row disappears with fade animation
- **THEN** edge count summary updates immediately
- **THEN** removed edge becomes re-selectable in Step 2 if user returns

#### Scenario: Edge continuity warning for DHS

- **WHEN** strategy template is DHS type AND selected edges are not continuous
- **THEN** system displays warning banner above table:
  - Icon: ⚠️ yellow warning
  - Message: `警告:所选路段不连续,DHS策略可能效果降低`
  - Details: Show gaps in stake coverage (e.g., `K10+800 到 K11+200 之间存在400m间隙`)
- **THEN** user can proceed despite warning (may be intentional for multiple DHS segments)
- **THEN** warning disappears if user removes edges to create continuity

#### Scenario: Lane count alert for DHS

- **WHEN** strategy template is DHS type AND any selected edge has lanes < 4
- **THEN** system displays error message:
  - Icon: ❌ red error
  - Message: `错误:DHS策略要求车道数≥4,以下路段不符合:`
  - List: Edge IDs with lane count < 4 (e.g., `edge_k8_001 (3车道)`)
  - Action: [移除不符合路段] button to auto-remove invalid edges
- **THEN** user cannot proceed until invalid edges removed

#### Scenario: Empty edge selection error

- **WHEN** user proceeds to save strategy with zero selected edges
- **THEN** system shows validation error: `至少需要选择一个管控路段`
- **THEN** [保存策略] button remains disabled until edges selected
- **THEN** error message includes link to return to Step 2

#### Scenario: Edge information tooltip

- **WHEN** user hovers over edge ID in table
- **THEN** system shows tooltip with additional details:
  - From/To junction IDs
  - Demonstration segment name (if applicable)
  - Gantry presence (if contains gantries)
  - Last data update timestamp
- **THEN** tooltip appears after 500ms hover delay

#### Scenario: Export edge list

- **WHEN** user wants to save edge selection for documentation
- **THEN** system provides [导出路段列表] button above table
- **THEN** click exports CSV file with all table columns
- **THEN** filename format: `strategy_{timestamp}_edges.csv`

### ADDED Requirement: Automatic Strategy Name Generation

The system SHALL generate strategy names automatically based on template type, affected locations, and key parameters, with user override capability.

#### Scenario: VSS strategy name generation

- **WHEN** user creates VSS strategy with:
  - Affected edges on route G4202, sections K10-K15
  - Speed limit: 80 km/h
  - Time intervals: [[7, 9], [17, 19]]
- **THEN** system generates name: `G4202 K10-K15 限速80km/h (早晚高峰)`
- **THEN** name pre-filled in "策略名称" field (user can edit)
- **THEN** if multiple routes selected, use first route or "多路线"

#### Scenario: DHS strategy name generation

- **WHEN** user creates DHS strategy with:
  - Affected edges on route SA2, sections K20-K25
  - Intervals: [[7, 9], [17, 19]]
- **THEN** system generates name: `SA2 K20-K25 应急车道开放 (早晚高峰)`
- **THEN** time period description adapts:
  - `[[7, 9]]` → "早高峰"
  - `[[17, 19]]` → "晚高峰"
  - `[[7, 9], [17, 19]]` → "早晚高峰"
  - `[[0, 24]]` → "全天"
  - Custom periods → "定时管控"

#### Scenario: TEC Metering strategy name generation

- **WHEN** user creates TEC Metering strategy with:
  - Entrance edge: entrance_jinjiang (锦江收费站入口)
  - Flow intervals: peak hours with reduced flow
- **THEN** system generates name: `锦江收费站入口 计量控制 (高峰限流)`
- **THEN** name extracted from entrance edge metadata (junction name) if available
- **THEN** control type appended: "计量控制" for metering, "关闭管控" for closure

#### Scenario: TEC Closure strategy name generation

- **WHEN** user creates TEC Closure strategy with:
  - Entrance edges: entrance_chengya_001, entrance_chengya_002
  - Vehicle ban: trucks only during [[7, 9]]
- **THEN** system generates name: `成雅收费站入口 货车限行 (早高峰)`
- **THEN** if full closure (no allowed types), use "完全关闭" instead of "货车限行"

#### Scenario: Name uniqueness enforcement

- **WHEN** generated name conflicts with existing strategy name
- **THEN** system appends counter suffix: `G4202 K10-K15 限速80km/h (2)`
- **THEN** increments counter until unique name found
- **THEN** user can manually change name to remove suffix

#### Scenario: User overrides generated name

- **WHEN** user edits auto-generated name in "策略名称" field
- **THEN** system accepts custom name (no auto-regeneration)
- **THEN** still validates:
  - Not empty
  - Max length 100 characters
  - Unique (no duplicate strategy names)
- **THEN** user can click [建议名称] button to regenerate from current parameters

#### Scenario: Re-generate name after parameter changes

- **WHEN** user changes key parameters (edges, speed, time) after name was generated
- **THEN** system does NOT auto-update name (user may have customized it)
- **THEN** [建议名称] button appears next to name field
- **THEN** click button regenerates name from current parameter values
- **THEN** confirms with user before replacing custom name

### ADDED Requirement: Automatic Strategy Description Generation

The system SHALL generate comprehensive strategy descriptions from template metadata and configured parameters, with user edit capability.

#### Scenario: VSS strategy description generation

- **WHEN** user configures VSS strategy with parameters
- **THEN** system generates description:
  ```
  可变限速策略 - 中等控制

  管控位置:
  - 路线: G4202 (成都绕城高速)
  - 路段: K10-K15 (共15个edge,总长8.5km)
  - 车道数: 3-4车道

  管控参数:
  - 限速值: 80 km/h
  - 管控时段: 07:00-09:00, 17:00-19:00 (早晚高峰)
  - 适用车型: 所有车辆

  策略目的: 通过动态调整限速来管理高峰时段交通流,缓解拥堵。

  生成元素: 1个 variableSpeedSign (SUMO XML)
  ```
- **THEN** description displayed in multiline textarea (editable)
- **THEN** user can modify description before saving

#### Scenario: DHS strategy description generation

- **WHEN** user configures DHS strategy
- **THEN** system generates:
  ```
  动态硬路肩开放策略

  管控位置:
  - 路线: SA2 (成都第二绕城)
  - 路段: K20-K25 (共10个edge,总长5.2km)
  - 车道数: 4车道 (硬路肩为第3车道)

  开放时段:
  - 早高峰: 07:00-09:00
  - 晚高峰: 17:00-19:00
  - 允许车型: passenger, bus, truck

  策略目的: 在高峰时段临时开放硬路肩作为通行车道,增加道路通行能力。

  注意事项: 路段连续性已验证,车道数符合要求(≥4)。

  生成元素: 1个 rerouter,包含2个时段interval (SUMO XML)
  ```

#### Scenario: TEC strategy description generation

- **WHEN** user configures TEC strategy
- **THEN** system generates:
  ```
  收费站入口计量控制策略

  管控入口:
  - 锦江收费站入口 (entrance_jinjiang)
  - 接入路线: G4202

  限流参数:
  - 07:00-09:00: 180 veh/h (早高峰严格限流)
  - 09:00-17:00: 480 veh/h (平峰正常通行)
  - 17:00-19:00: 300 veh/h (晚高峰中度限流)
  - 目标速度: 8-15 m/s

  策略目的: 通过入口计量控制,平衡主线交通流量,防止下游拥堵传播。

  生成元素: 1个 calibrator,包含3个流量interval (SUMO XML)
  ```

#### Scenario: Description templates from strategy templates

- **WHEN** strategy template v2.0 includes description_template field:
  ```json
  {
    "description_template": "{strategy_type}策略\n\n管控位置:\n- 路线: {routes}\n- 路段: {sections}\n\n{parameters_summary}\n\n策略目的: {purpose}"
  }
  ```
- **THEN** system uses template with placeholder replacement:
  - `{strategy_type}` → Template display name
  - `{routes}` → Unique route codes from edges
  - `{sections}` → Section code range
  - `{parameters_summary}` → Key parameter formatted list
  - `{purpose}` → Template purpose description
- **THEN** missing placeholders are skipped (no error)

#### Scenario: User edits generated description

- **WHEN** user modifies auto-generated description in textarea
- **THEN** system saves modified description (no auto-regeneration)
- **THEN** [重新生成描述] button appears next to textarea
- **THEN** click button regenerates from current parameters
- **THEN** confirms before replacing user edits

#### Scenario: Description includes validation warnings

- **WHEN** strategy has validation warnings (e.g., DHS discontinuity)
- **THEN** description includes warnings section:
  ```
  注意事项:
  ⚠️ 所选路段不连续,存在400m间隙(K10+800 到 K11+200)
  ⚠️ 管控效果可能降低,建议检查路段选择
  ```
- **THEN** warnings are prepended to generated description
- **THEN** user can remove warnings if intentional

### ADDED Requirement: Personnel Field Removal

The system SHALL NOT include any personnel, operator, or OA-related input fields in the strategy configuration form.

#### Scenario: No personnel fields in configuration form

- **WHEN** user is on Step 3 (Configure Parameters) form
- **THEN** form does NOT contain fields for:
  - Operator name / 操作人员
  - Department / 部门
  - Contact information / 联系方式
  - Approval status / 审批状态
  - OA workflow ID / OA流程号
- **THEN** only strategy-specific technical parameters are present

#### Scenario: Metadata tracks creation automatically

- **WHEN** user saves strategy
- **THEN** backend automatically records in strategy metadata:
  - `created_at`: ISO 8601 timestamp
  - `updated_at`: ISO 8601 timestamp (same as created_at initially)
  - `version`: "2.0" (template version)
- **THEN** no user-entered personnel information stored
- **THEN** future: If OA integration needed, add separate authentication/user module

#### Scenario: Strategy list shows creation time only

- **WHEN** user views strategy list
- **THEN** each strategy shows:
  - Strategy name
  - Strategy type (VSS/DHS/TEC)
  - Creation date (e.g., "2025-10-24 14:30")
  - Last modified date (if different from creation)
- **THEN** NO "Created by" or "Operator" column displayed

### MODIFIED Requirement: Real-Time Parameter Validation (Enhanced)

The system SHALL validate parameters as user inputs them, with enhanced SUMO-specific constraint checking and actionable error messages.

*(This modifies the existing requirement in strategy-templates spec)*

#### Scenario: Array parameter format validation

- **WHEN** user enters array parameter value in textarea
- **THEN** system validates on blur:
  - If starts with `[`, attempt JSON parse
  - If JSON parse fails, show error: `JSON格式不正确: {error message}`
  - If JSON parses but not array, show error: `需要数组格式,当前为: {type}`
  - If newline/comma-separated, split and count items
  - If count < minItems, show error: `至少需要 {minItems} 个项目,当前: {count}`
- **THEN** validation error appears inline below textarea (red text)
- **THEN** [保存策略] button disabled while errors exist

#### Scenario: Nested array validation (time intervals)

- **WHEN** user enters time_intervals as `[[7, 9], [25, 19]]` (invalid end hour 25)
- **THEN** system validates each sub-array:
  - Each item must have exactly 2 elements
  - First element (start hour) must be 0-24
  - Second element (end hour) must be 0-24
  - Start < End (unless wraps midnight)
- **THEN** shows error: `时段2无效: 结束小时25超出范围(0-24)`
- **THEN** highlights specific invalid interval

#### Scenario: Cross-parameter validation (speed steps vs time intervals)

- **WHEN** user enters speed_steps and time_intervals for VSS
- **THEN** system validates cross-parameter consistency:
  - Number of speed steps should match or exceed time intervals
  - Time values in speed_steps should align with interval boundaries
  - No speed step outside defined time intervals
- **THEN** if mismatch, shows warning (not error): `警告: speed_steps有3个时段,但time_intervals只定义了2个`
- **THEN** allows save (warning only, not blocking)

#### Scenario: Edge existence validation

- **WHEN** user enters edge IDs in array parameter
- **THEN** system validates against edge database:
  - Call `/api/v1/control/edges/validate` endpoint
  - Pass edge ID list for existence check
  - Receive response with valid/invalid edges
- **THEN** if invalid edges found, shows error: `以下edge不存在: edge_invalid1, edge_invalid2`
- **THEN** provides [打开路段选择器] link to browse valid edges

### MODIFIED Requirement: Dynamic Parameter Form Generation (Enhanced)

The system SHALL generate HTML forms with improved visual hierarchy, grouping, and helper elements.

*(This enhances the existing requirement in strategy-templates spec)*

#### Scenario: Parameter grouping by category

- **WHEN** template parameters include multiple types (location, time, control)
- **THEN** form groups parameters into sections:
  - **管控位置** (Location): affected_edges, affected_segments, entrance_edges
  - **时间配置** (Time): time_intervals, intervals, flow_intervals
  - **管控参数** (Control): speed_steps, allowed_vehicle_types, flow_rate
  - **其他** (Other): Any parameters not in above categories
- **THEN** each section has collapsible header
- **THEN** sections render in logical order: Location → Time → Control → Other

#### Scenario: Inline help icons

- **WHEN** parameter has complex description or SUMO constraints
- **THEN** system displays small (?) icon next to field label
- **THEN** hover/(click on mobile) shows tooltip with:
  - Parameter purpose
  - SUMO element it maps to
  - Valid value range
  - Example value
  - Common mistakes to avoid
- **THEN** tooltip remains visible until user clicks outside or hovers away

#### Scenario: Field dependency indicators

- **WHEN** parameter depends on another parameter (e.g., hard_shoulder_lane_index depends on affected_segments)
- **THEN** dependent field shows note: `📌 依赖于: affected_segments`
- **THEN** dependent field disabled until dependency field filled
- **THEN** enabling happens automatically when dependency satisfied

#### Scenario: Form field icons for visual clarity

- **WHEN** rendering form fields
- **THEN** each field type has icon prefix:
  - Location parameters: 📍
  - Time parameters: ⏰
  - Speed parameters: 🚗
  - Vehicle type parameters: 🚙
  - Flow rate parameters: 📊
  - Boolean parameters: ☑️
- **THEN** icons provide quick visual scanning of form structure

### ADDED Requirement: Enhanced XML Preview

The system SHALL provide real-time SUMO XML preview that updates as parameters change, with syntax highlighting and copy functionality.

#### Scenario: Live XML preview panel

- **WHEN** user is on Step 3 (Configure Parameters)
- **THEN** system displays collapsible XML preview panel:
  - Position: Right side panel (30% width) or bottom panel (collapsible)
  - Header: "SUMO XML 预览" with [复制XML] button
  - Content: Syntax-highlighted XML code
  - Auto-scroll to changed elements on parameter update
- **THEN** preview updates within 500ms of parameter blur event

#### Scenario: Syntax highlighting in preview

- **WHEN** XML preview is displayed
- **THEN** system applies syntax highlighting:
  - Tag names: Blue (#3498db)
  - Attribute names: Green (#27ae60)
  - Attribute values: Orange (#e67e22)
  - Comments: Gray (#95a5a6)
  - Invalid XML: Red background
- **THEN** uses `<pre><code>` with CSS classes for coloring

#### Scenario: XML validation in preview

- **WHEN** generated XML has syntax errors (unclosed tags, invalid attributes)
- **THEN** preview shows error indicator:
  - Red border around preview panel
  - Error icon in header
  - Error message below XML: `XML格式错误: {validation error}`
- **THEN** [保存策略] button disabled until XML valid

#### Scenario: Copy XML to clipboard

- **WHEN** user clicks [复制XML] button
- **THEN** system copies current XML to clipboard
- **THEN** shows toast notification: `XML已复制到剪贴板` (2 second duration)
- **THEN** button text briefly changes to `✓ 已复制` then reverts

#### Scenario: Toggle XML preview visibility

- **WHEN** user clicks preview panel header/collapse icon
- **THEN** panel collapses to header bar only (or expands if collapsed)
- **THEN** main form area expands to use freed space
- **THEN** user preference saved to localStorage

## Related Specifications

- `strategy-templates` - Provides template schemas and parameter definitions
- `database-edge-selector` (future spec) - Defines edge query and display requirements
