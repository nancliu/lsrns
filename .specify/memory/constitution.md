<!--
Sync Impact Report:
- Version change: 1.2.1 → 1.3.0 (MINOR - added File-Based Storage principle)
- Added principles:
  * VI. File-Based Storage (NON-NEGOTIABLE) - 仿真结果必须文件存储，支持大规模并行仿真
  * 并行仿真每个实例独立目录（{sim_id}_parallel_{index}/）
  * 禁止将仿真原始输出存入数据库
  * 例外：观测数据、分析聚合指标可用数据库
- Modified principles (v1.2.1): Enhanced Module Isolation with symmetrical API/Shared layer rules:
  API Layer:
  * ✅ ALLOWED: Add new service/route files (e.g., api/services/control_strategy_service.py)
  * ✅ ALLOWED: Add new API endpoints (prefix: /api/v1/control/*)
  * ✅ ALLOWED: Call existing APIs
  * ❌ FORBIDDEN: Modify existing service/route files (except backward-compatible extensions)
  * Require integration tests (100% pass rate)
  Shared Layer:
  * ✅ ALLOWED: Add new tools (e.g., shared/analysis_tools/control_optimizer.py)
  * ✅ ALLOWED: Extend existing tools (add functions, preserve signatures)
  * ❌ FORBIDDEN: Modify existing function signatures or behavior
  * Require unit tests (≥80% coverage)
- Added principles (v1.2.0):
  * III. Single Responsibility (单一职责原则) - Service按业务域分离
  * IV. Test-First (NON-NEGOTIABLE) - TDD强制要求，API测试100%，单测≥80%
- Core principles: 6 total (Layered Architecture, Module Isolation, Single Responsibility, Test-First, Configuration Over Code, File-Based Storage)
- Templates requiring updates:
  ✅ All templates remain compatible
- Follow-up TODOs: None
-->

# OD数据处理与仿真系统 Constitution

## Core Principles

### I. Layered Architecture (NON-NEGOTIABLE)

API层 (`api/`) 负责接口，Shared层 (`shared/`) 负责核心逻辑。依赖关系单向：API → Shared，严禁循环依赖。

**目的**：保持架构清晰，支持并行开发和独立测试。

### II. Module Isolation (NON-NEGOTIABLE)

新功能域（管控优化功能域，含多个页面）MUST作为独立模块开发，严禁修改现有仿真分析代码。

**API层要求**：

- ✅ **允许新增**专用文件（如`api/services/control_strategy_service.py`、`api/routes/control_routes.py`）
- ✅ **允许新增**API端点（独立前缀：`/api/v1/control/*`）
- ✅ **允许调用**已有API接口（如`/api/v1/simulation/*`、`/api/v1/case/*`等）
- ❌ **禁止修改**现有service/route文件（除非向后兼容扩展）
- ❌ **禁止修改**现有API行为（除非向后兼容扩展）
- 新增API端点必须有集成测试（通过率100%）

**Shared层要求**：

- ✅ **允许新增**专用工具（如`shared/analysis_tools/control_optimizer.py`）
- ✅ **允许扩展**现有工具（通过新增函数，不改已有函数签名）
- ❌ **禁止修改**现有工具的函数签名或行为（避免破坏仿真分析功能）
- 新增Shared功能必须有单元测试（覆盖率≥80%）

**目的**：保护已完成的仿真分析功能，新旧功能域互不干扰，降低回归风险。

### III. Single Responsibility (单一职责原则)

每个模块、类、函数只做一件事。Service按业务域严格分离，禁止跨域职责混合。

**具体要求**：

- 每个Service文件对应一个业务域（如`simulation_service.py`只管仿真，不管案例）
- 函数职责单一：数据处理与业务逻辑分离
- API路由按功能域分组：`/simulation/*`、`/case/*`、`/analysis/*`、`/control/*`
- Shared层工具函数保持通用性，不耦合特定业务

**目的**：降低耦合，提高可维护性，支持功能域独立演进。

### IV. Test-First (NON-NEGOTIABLE)

测试先写，功能后实现。测试是质量门禁，不是事后补充。

**具体要求**：

- API测试通过率 = 100%（所有公开API必须有集成测试）
- 单测覆盖率 ≥ 80%（Shared层核心工具）
- 关键路径必须有E2E测试覆盖（Playwright MCP）
- 新功能开发流程：编写测试 → 测试失败 → 实现功能 → 测试通过 (TDD)
- 测试必须可独立运行，不依赖外部状态

**目的**：政府研究项目要求高可靠性，测试优先确保代码质量和回归保护。

### V. Configuration Over Code

车型、网络、TAZ等参数必须配置化（`templates/`目录），禁止硬编码。模板只读，运行时复制使用。

**目的**：支持领域专家独立调整参数，无需修改代码。

### VI. File-Based Storage (NON-NEGOTIABLE)

仿真结果（包括并行仿真）MUST以文件方式存储在标准路径，禁止使用数据库存储仿真输出。

**具体要求**：

- 所有仿真结果存储在 `cases/{case_id}/simulations/{sim_id}/` 目录
- 并行仿真每个实例独立目录：`{sim_id}_parallel_{index}/` 或 `{sim_id}/run_{index}/`
- SUMO输出文件保持原始格式（XML）：`summary.xml`、`tripinfo.xml`、`edgedata.xml`等
- 分析结果存储在 `cases/{case_id}/analysis/{type}/` 目录
- 元数据使用JSON文件：`metadata.json`、`simulations_index.json`
- **禁止**将仿真结果（summary、tripinfo、edgedata等）存入数据库

**并行仿真路径示例**：

```text
cases/case_001/simulations/
├── sim_001_parallel_0/        # 并行实例0
│   ├── simulation.sumocfg
│   ├── summary.xml
│   └── tripinfo.xml
├── sim_001_parallel_1/        # 并行实例1
│   ├── simulation.sumocfg
│   ├── summary.xml
│   └── tripinfo.xml
└── sim_001_parallel_2/        # 并行实例2
    ├── simulation.sumocfg
    ├── summary.xml
    └── tripinfo.xml
```

**目的**：

- 支持海量并行仿真（数千个实例）无数据库性能瓶颈
- 简化仿真结果管理和迁移（直接复制目录）
- 保持SUMO工具链兼容性（直接读取XML文件）
- 避免大文件数据库存储开销

**例外**：

- ✅ 观测数据（门架流量、OD数据）可存储在PostgreSQL（HOMDS数据源）
- ✅ 分析聚合指标可存储在数据库（如精度统计、性能摘要）
- ❌ 仿真原始输出文件必须保持文件存储

## Development Standards

**必须遵守**：

- 使用`pathlib.Path`处理文件路径
- 类型注解 + Google风格文档字符串
- 禁用`print()`，使用logging
- 函数≤30行，参数≤5个，嵌套≤3层
- 代码格式化：black (100字符行宽)

**数据处理**：优先pandas向量化操作，避免Python循环

**依赖管理**：优先mamba安装，禁止在conda base环境安装

## Governance

**新功能开发**：

- 管控优化功能必须遵守Module Isolation原则
- 架构违规需在PR中明确说明理由

**宪法修订**：

- MAJOR：不兼容变更（需迁移计划）
- MINOR：新增原则（需评审批准）
- PATCH：澄清说明（可快速通过）

**Version**: 1.3.0 | **Ratified**: 2025-10-17 | **Last Amended**: 2025-10-17
