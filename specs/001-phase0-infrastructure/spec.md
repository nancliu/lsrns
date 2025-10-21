# Feature Specification: 交通管控仿真 - Phase 0 基础设施准备

**Feature Branch**: `001-phase0-infrastructure`
**Created**: 2025-10-19
**Status**: Draft
**Input**: User description: "实现Phase 0基础设施准备，包括：1. 数据模型定义（ControlTemplate, Strategy, Plan, BatchSimulation）2. 目录结构创建（templates/control_strategies, control_data等）3. API框架搭建（空路由，注册到main.py）4. 前端页面框架（基础布局，导航切换）5. 数据库连接测试（复用existing connection.py，确认能访问dim schema）参考：docs/design/development_roadmap.md 的 Phase 0 部分"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 开发者初始化控制策略功能模块 (Priority: P1)

作为系统开发者，我需要建立交通管控仿真功能的基础架构，包括数据模型、目录结构、API框架和前端页面骨架，以便为后续阶段（策略模板、边选择器、方案管理、批量仿真）的开发提供标准化的代码结构和数据存储位置。

**Why this priority**: 这是所有后续开发的基础，没有基础设施，无法进行任何功能开发。所有Phase 1-4的功能都依赖于此阶段定义的数据模型和目录结构。

**Independent Test**: 可以通过检查目录是否创建、API路由是否可访问、数据模型是否通过类型检查来独立验证，无需依赖任何业务逻辑实现。

**Acceptance Scenarios**:

1. **Given** 项目根目录存在，**When** 执行基础设施创建脚本，**Then** 所有必需的目录结构被正确创建（templates/control_strategies, control_data及其子目录）
2. **Given** FastAPI应用已启动，**When** 访问 `/api/v1/control/strategies/` 路由，**Then** 返回200状态码和空列表（表示路由已注册但无数据）
3. **Given** 数据模型文件已创建，**When** 运行Python类型检查工具（mypy），**Then** 所有控制相关模型通过类型验证
4. **Given** 前端服务器已启动，**When** 访问 `/control/index.html`，**Then** 页面正确加载，显示基础布局和导航菜单

---

### User Story 2 - 验证数据库连接能访问dim schema (Priority: P1)

作为系统开发者，我需要确认现有的数据库连接模块能够访问dim schema中的表（如dim.sim_network_edges, dim.multiscale_node_units），以便后续阶段的边选择器功能可以查询路段和节点数据。

**Why this priority**: Phase 1B的核心功能（数据库驱动的边选择器）依赖于访问dim schema。提前验证数据库连接可以避免后续开发中出现阻塞性问题。

**Independent Test**: 可以通过运行独立的测试脚本（查询dim schema的一张表并返回结果数量）来验证，无需等待业务功能开发。

**Acceptance Scenarios**:

1. **Given** .env文件配置了正确的数据库连接信息，**When** 运行数据库连接测试脚本，**Then** 成功连接到数据库并返回连接状态
2. **Given** 数据库连接已建立，**When** 执行查询 `SELECT COUNT(*) FROM dim.sim_network_edges`，**Then** 返回路段总数（大于0）
3. **Given** 数据库连接已建立，**When** 执行查询 `SELECT COUNT(*) FROM dim.multiscale_node_units`，**Then** 返回节点单元总数（大于0）
4. **Given** 数据库连接已建立，**When** 执行查询 `SELECT COUNT(*) FROM dim.point_gantry`，**Then** 返回门架点总数（大于0）

---

### User Story 3 - 前端页面框架提供导航切换能力 (Priority: P2)

作为系统用户（交通工程师），我需要能够在浏览器中打开管控仿真功能的前端页面，并通过导航菜单在不同功能模块之间切换（策略管理、方案管理、批量仿真、优化分析），尽管这些功能模块在Phase 0阶段还未实现具体业务逻辑。

**Why this priority**: 提供前端页面骨架可以让用户提前熟悉系统布局，也为后续各阶段的前端开发提供统一的导航结构。但相比数据模型和API框架，前端框架的优先级略低。

**Independent Test**: 可以通过访问前端URL并点击导航菜单项来验证，无需后端业务逻辑支持。

**Acceptance Scenarios**:

1. **Given** 前端服务器已启动，**When** 访问 `/control/index.html`，**Then** 页面显示导航菜单，包含"策略管理"、"方案管理"、"批量仿真"、"优化分析"四个选项
2. **Given** 导航菜单已显示，**When** 点击"策略管理"选项，**Then** 页面内容区域切换到策略管理视图（显示占位文本"策略管理功能开发中"）
3. **Given** 导航菜单已显示，**When** 点击"方案管理"选项，**Then** 页面内容区域切换到方案管理视图（显示占位文本"方案管理功能开发中"）
4. **Given** 任意导航菜单项被激活，**When** 页面刷新，**Then** 保持当前激活的菜单项和视图状态

---

### Edge Cases

- 如果数据库连接失败（网络不可达、凭据错误），数据库连接测试脚本应返回明确的错误信息和诊断建议，而非静默失败
- 如果目录创建过程中遇到权限问题（Windows文件系统只读），应抛出清晰的异常并指导用户解决
- 如果API路由注册到main.py时发现路径冲突（已有相同前缀的路由），应在启动时警告或报错
- 如果前端页面框架加载JavaScript文件失败（CDN不可用），应降级使用本地库或显示友好错误提示

## Requirements *(mandatory)*

### Functional Requirements

#### 数据模型定义

- **FR-001**: 系统必须定义 `ControlTemplate` 数据模型，包含字段：template_id（字符串）、template_name（字符串）、strategy_type（枚举：VSS/DHS/TEC）、parameters_schema（JSON schema字典）、description（可选字符串）
- **FR-002**: 系统必须定义 `Strategy` 数据模型，包含字段：strategy_id（字符串）、strategy_name（字符串）、template_id（字符串，关联到ControlTemplate）、parameters（参数值字典）、target_edges（路段ID列表）、created_at（时间戳）、updated_at（时间戳）
- **FR-003**: 系统必须定义 `Plan` 数据模型，包含字段：plan_id（字符串）、plan_name（字符串）、description（可选字符串）、strategy_ids（策略ID列表）、additional_file_path（生成的Additional文件路径，可选）、created_at（时间戳）、updated_at（时间戳）
- **FR-004**: 系统必须定义 `BatchSimulation` 数据模型，包含字段：batch_id（字符串）、batch_name（字符串）、case_id（字符串，关联到已有Case）、plan_ids（方案ID列表）、status（枚举：PENDING/RUNNING/COMPLETED/FAILED）、progress（进度字典，包含total/completed/failed）、simulation_ids（仿真ID列表，关联到已有Simulation）、created_at（时间戳）、updated_at（时间戳）
- **FR-005**: 所有数据模型必须使用Pydantic BaseModel实现，并提供类型注解和字段描述，符合项目现有的数据模型规范

#### 目录结构创建

- **FR-006**: 系统必须创建目录 `templates/control_strategies/`，用于存储策略模板JSON文件（Phase 1A阶段使用）
- **FR-007**: 系统必须创建目录 `control_data/strategies/`，用于存储用户创建的策略数据文件
- **FR-008**: 系统必须创建目录 `control_data/plans/`，用于存储用户创建的方案数据文件
- **FR-009**: 系统必须创建目录 `control_data/optimizations/`，用于存储优化分析结果（Phase 4阶段使用）
- **FR-010**: 系统必须创建目录 `api/routes/control/`，用于存放控制相关的路由文件（可选，根据实际需要决定是否独立子目录）
- **FR-011**: 系统必须创建目录 `api/services/control/`，用于存放控制相关的服务文件
- **FR-012**: 系统必须创建目录 `shared/control_tools/`，用于存放控制相关的共享工具模块（模板解析器、Additional生成器等）
- **FR-013**: 系统必须创建目录 `frontend/control/`，用于存放控制相关的前端页面文件

#### API框架搭建

- **FR-014**: 系统必须创建API路由文件 `api/routes/control_strategy_routes.py`，定义空路由但路径已规划（如 `/api/v1/control/strategies/`, `/api/v1/control/plans/`, `/api/v1/control/batch_simulations/`）
- **FR-015**: 系统必须创建API服务文件 `api/services/control/control_strategy_service.py`，定义空服务类但方法签名已规划（如 `list_strategies()`, `create_strategy()`, `delete_strategy()`）
- **FR-016**: 系统必须在 `api/routes/__init__.py` 中注册 `control_strategy_routes.py` 的路由，使用前缀 `/control`，标签为 `["交通管控"]`
- **FR-017**: 空路由在被访问时必须返回200状态码和空数据结构（如空列表`[]`或空字典`{}`），而非404或500错误
- **FR-018**: API路由文件必须包含类型注解和文档字符串，符合项目现有的API开发规范

#### 前端页面框架

- **FR-019**: 系统必须创建前端入口文件 `frontend/control/index.html`，包含基础HTML结构（header、nav、main、footer）
- **FR-020**: 系统必须创建样式文件 `frontend/control/styles.css`，定义基础布局样式（导航菜单、内容区域、响应式布局）
- **FR-021**: 系统必须创建JavaScript文件 `frontend/control/app.js`，实现导航菜单的点击事件处理和视图切换逻辑
- **FR-022**: 导航菜单必须包含四个主要功能模块入口：策略管理（Strategy Management）、方案管理（Plan Management）、批量仿真（Batch Simulation）、优化分析（Optimization Analysis）
- **FR-023**: 前端页面必须在服务器启动后可通过 `/control/index.html` 访问，无需额外配置

#### 数据库连接测试

- **FR-024**: 系统必须提供数据库连接测试脚本 `shared/data_access/test_dim_schema.py`（或类似名称），用于验证数据库连接和dim schema访问权限
- **FR-025**: 数据库连接测试脚本必须复用现有的 `shared/data_access/connection.py` 模块，不重复实现连接逻辑
- **FR-026**: 数据库连接测试脚本必须查询以下三张表并输出记录数：`dim.sim_network_edges`, `dim.multiscale_node_units`, `dim.point_gantry`
- **FR-027**: 数据库连接测试脚本必须在连接失败时输出清晰的错误信息（包括数据库地址、端口、数据库名、schema名），以便排查问题

### Key Entities

- **ControlTemplate**: 管控策略模板实体，定义了某种管控类型（如可变限速VSS）的参数结构和默认值。属性包括模板ID、名称、策略类型（枚举）、参数schema（JSON schema格式）、描述。
- **Strategy**: 管控策略实体，基于某个模板创建的具体策略实例，包含用户填写的参数值和目标路段。属性包括策略ID、名称、关联的模板ID、参数值（字典）、目标路段列表、创建/更新时间。
- **Plan**: 管控方案实体，包含多个策略的组合，用于生成SUMO Additional文件。属性包括方案ID、名称、描述、包含的策略ID列表、生成的Additional文件路径、创建/更新时间。
- **BatchSimulation**: 批量仿真任务实体，针对某个案例（Case）和多个方案（Plans）执行并行仿真。属性包括批次ID、名称、关联的案例ID、方案ID列表、状态（枚举）、进度信息、生成的仿真ID列表、创建/更新时间。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 开发者执行目录创建脚本后，所有7个必需目录（templates/control_strategies, control_data/strategies, control_data/plans, control_data/optimizations, api/services/control, shared/control_tools, frontend/control）必须全部创建成功，文件系统检查通过率100%
- **SC-002**: 开发者启动FastAPI服务器后，访问 `/api/v1/control/strategies/` 路由必须在500毫秒内返回200状态码和空列表，响应时间不超过1秒
- **SC-003**: 开发者运行mypy或pylance类型检查工具时，所有4个控制相关数据模型（ControlTemplate, Strategy, Plan, BatchSimulation）必须通过类型检查，错误数为0
- **SC-004**: 开发者运行数据库连接测试脚本后，必须成功连接数据库并查询到dim schema中至少3张表的记录数（sim_network_edges、multiscale_node_units、point_gantry），且每张表记录数大于0，查询成功率100%
- **SC-005**: 用户在浏览器中访问 `/control/index.html` 后，页面必须在2秒内完全加载并显示导航菜单，点击导航菜单项后视图切换必须在100毫秒内完成，无JavaScript错误
- **SC-006**: 开发团队完成Phase 0后，后续阶段（Phase 1A-4）的开发可以直接使用已定义的数据模型和目录结构，无需重构基础架构，基础设施变更次数为0

## Assumptions

- 假设开发环境已正确配置Python 3.10+、FastAPI、Pydantic等依赖，无需在Phase 0中安装额外的第三方库
- 假设`.env`文件已包含正确的数据库连接信息（DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD），且数据库服务器可访问
- 假设dim schema中的表（sim_network_edges, multiscale_node_units, point_gantry）已存在并包含数据，无需在Phase 0中创建或迁移数据库schema
- 假设前端页面框架采用原生HTML/CSS/JavaScript开发（与现有frontend目录风格一致），不引入React/Vue等前端框架
- 假设目录创建操作由开发者手动执行（或通过简单的Python/PowerShell脚本），不需要实现自动化的安装程序或数据库迁移工具
- 假设API路由文件遵循现有的项目结构（api/routes/），服务文件遵循现有的项目结构（api/services/），与现有模块（data_routes.py, case_routes.py等）的组织方式保持一致
- 假设前端静态文件服务已在main.py中配置（`app.mount("/", StaticFiles(directory="frontend"))`），无需额外配置Web服务器

## Out of Scope

- 策略模板的具体内容定义（如VSS模板的参数schema）属于Phase 1A范围
- 边选择器的数据库查询逻辑和前端界面属于Phase 1B范围
- 策略CRUD的业务逻辑实现（创建、更新、删除、列表）属于Phase 1C范围
- Additional文件生成器的具体实现属于Phase 2范围
- 批量仿真调度器的并发控制和进度监控属于Phase 3范围
- 优化分析的指标计算和排序算法属于Phase 4范围
- 单元测试和集成测试的编写（虽然建议编写，但Phase 0重点是建立基础结构，测试可在后续阶段补充）
- 数据库schema设计和表创建（假设dim schema已存在）
- 前端页面的详细UI设计和交互优化（Phase 0仅提供基础布局和导航切换，详细设计在各功能阶段完成）

## Dependencies

- 依赖现有的 `shared/data_access/connection.py` 模块提供数据库连接功能
- 依赖现有的 `api/routes/__init__.py` 路由注册机制
- 依赖现有的 `api/main.py` FastAPI应用实例和静态文件挂载配置
- 依赖现有的Pydantic数据模型规范（参考 `api/models/entities/case.py` 等现有实体定义）
- 依赖现有的目录结构约定（templates/, cases/, api/, shared/, frontend/）
- 依赖Python标准库（pathlib, json, datetime等）和项目已安装的第三方库（FastAPI, Pydantic, psycopg2等）

## Related Documentation

- [docs/design/development_roadmap.md](../../docs/design/development_roadmap.md) - 分阶段开发路线图，详细描述了Phase 0-4的目标和任务
- [CLAUDE.md](../../CLAUDE.md) - 项目架构指南，定义了API层和Shared层的职责划分
- [docs/api_docs/新架构API指南.md](../../docs/api_docs/新架构API指南.md) - API开发规范
- [api/models/entities/case.py](../../api/models/entities/case.py) - 现有数据模型示例（参考CaseMetadata的定义方式）
- [api/routes/__init__.py](../../api/routes/__init__.py) - 路由注册示例（参考如何注册新的子路由）
