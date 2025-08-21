# OD数据处理与仿真系统（v0.65）

## 项目概述

OD数据处理与仿真系统是一个基于案例管理的交通仿真分析平台，采用现代化模块化架构设计。系统已完成从传统单体架构向完全模块化架构的重构，具有高可维护性、可扩展性和优秀的开发体验。

### 🎯 核心特性

- **完全模块化设计**: API层专注接口，Shared层专注核心功能
- **多类型分析支持**: 精度分析、机理分析、性能分析
- **完整分析生态**: 图表生成、报告输出、历史查看
- **现代化技术栈**: FastAPI + Pydantic + Python 3.10+
- **用户友好界面**: 一站式Web界面，操作简便

### 🔧 系统状态

- ✅ **基础功能**: 页面加载、模板管理完全正常
- ✅ **数据处理**: OD数据处理功能完整可用
- ✅ **仿真运行**: 仿真启动、监控、结果查看正常
- ✅ **分析功能**: 三种分析类型执行和历史查看正常
- ✅ **案例管理**: 案例创建、查看、管理功能完整
- ✅ **API服务**: 所有接口经过测试验证

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11

### 安装步骤

1. **克隆项目**

   ```bash
   git clone [项目地址]
   cd OD生成脚本
   ```

2. **安装依赖**（先 mamba，后 pip 补充；勿在 base 环境安装）

   ```powershell
   mamba install -y -c conda-forge --file requirements.txt
   pip install -r requirements.txt
   ```

3. **启动API服务**

   ```powershell
   # 方法1: 使用启动脚本（推荐）
   .\start_api.bat

   # 方法2: 直接运行（需已安装依赖）
   python api\main.py
   ```

4. **访问系统**

   - API服务: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 前端主页: http://localhost:8000/index.html

## 系统功能

### 核心功能

1. **OD数据处理**
   - 时间范围配置
   - TAZ和网络文件选择
   - OD数据生成和路由文件创建
   - 案例自动创建和管理

2. **仿真运行**
   - 微观/中观仿真支持
   - GUI/后台运行模式
   - 多种输出配置（summary、tripinfo、vehroute等）
   - 实时状态监控

3. **结果分析**
   - **精度分析**: 门架数据与仿真结果对比，生成精度指标
   - **机理分析**: 交通流机理特性分析，识别交通规律
   - **性能分析**: 系统性能评估，优化建议生成
   - **历史查看**: 所有分析类型的历史结果管理

4. **案例管理**
   - 案例创建、查看、克隆、删除
   - 案例状态追踪
   - 搜索和筛选功能

5. **模板管理**
   - TAZ文件模板（TAZ_5_validated.add.xml等）
   - 网络文件模板（sichuan系列）
   - 仿真配置模板（microscopic、mesoscopic）

### API接口（按业务分组）

- **数据处理**: `POST /api/v1/process_od_data/`
- **案例管理**: `GET /api/v1/list_cases/`, `POST /api/v1/create_case/`
- **仿真管理**: `POST /api/v1/run_simulation/`, `GET /api/v1/simulations/{case_id}`
- **结果分析**: 
  - 精度分析: `POST /api/v1/analyze_accuracy/`
  - 机理分析: `POST /api/v1/analyze_mechanism/`
  - 性能分析: `POST /api/v1/analyze_performance/`
  - 历史结果: `GET /api/v1/analysis/analysis_results/{case_id}?analysis_type={type}`
  - 分析历史: `GET /api/v1/analysis/analysis_history/{case_id}`
- **模板管理**: `GET /api/v1/templates/{template_type}`
- **文件管理**: `GET /api/v1/file_info/{file_path}`

## 项目结构

```
OD生成脚本/
├── api/                      # API接口层
│   ├── main.py              # FastAPI主程序（唯一入口）
│   ├── services/            # 业务逻辑层
│   │   ├── base_service.py     # 基础服务类
│   │   ├── data_service.py     # 数据处理服务
│   │   ├── case_service.py     # 案例管理服务
│   │   ├── simulation_service.py # 仿真服务
│   │   ├── analysis_service.py   # 分析服务
│   │   ├── template_service.py   # 模板服务
│   │   └── file_service.py       # 文件服务
│   ├── models/              # 数据模型层
│   │   ├── requests/           # 请求模型
│   │   ├── responses/          # 响应模型
│   │   ├── entities/           # 实体模型
│   │   ├── base.py            # 基础模型
│   │   └── enums.py           # 枚举定义
│   └── routes/              # API路由层
│       ├── data_routes.py      # 数据处理路由
│       ├── case_routes.py      # 案例管理路由
│       ├── simulation_routes.py # 仿真路由
│       ├── analysis_routes.py   # 分析路由
│       ├── template_routes.py   # 模板路由
│       ├── file_routes.py       # 文件路由
│       └── middleware.py        # 中间件
├── shared/                   # 共享核心功能层
│   ├── utilities/           # 通用工具函数
│   │   ├── file_utils.py       # 文件操作工具
│   │   ├── time_utils.py       # 时间处理工具
│   │   ├── sumo_utils.py       # SUMO仿真工具
│   │   ├── validation_utils.py # 验证工具
│   │   ├── taz_utils.py        # TAZ处理工具
│   │   └── data_flow_optimizer.py # 数据流优化工具
│   ├── data_access/         # 数据访问层
│   │   ├── connection.py       # 数据库连接
│   │   ├── db_config.py        # 数据库配置
│   │   ├── gantry_loader.py    # 门架数据加载
│   │   └── od_table_resolver.py # OD表解析器
│   ├── analysis_tools/      # 分析工具
│   │   ├── accuracy_analysis.py # 精度分析器
│   │   ├── mechanism_analysis.py # 机理分析器
│   │   └── performance_analysis.py # 性能分析器
│   └── data_processors/     # 数据处理器
│       ├── od_processor.py     # OD数据处理器
│       ├── e1_processor.py     # E1检测器数据处理器
│       ├── gantry_processor.py # 门架数据处理器
│       └── simulation_processor.py # 仿真数据处理器
├── cases/                    # 案例根目录
├── templates/                # 模板文件
│   ├── taz_files/           # TAZ文件模板
│   ├── network_files/       # 网络文件模板
│   └── config_templates/    # 配置模板
├── frontend/                # 前端文件
│   ├── index.html          # 主页面
│   ├── script.js           # 前端逻辑
│   └── styles.css          # 样式文件
├── docs/                    # 项目文档
│   ├── development/         # 开发相关文档
│   ├── api_docs/           # API文档
│   ├── testing/            # 测试相关文档
│   │   └── Playwright_MCP_测试任务清单.md # 自动化测试清单
│   └── DEPLOYMENT_GUIDE.md # 部署指南
├── tests/                  # 测试目录
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── e2e/               # 端到端测试
├── test_output/           # 测试输出目录
├── requirements.txt       # Python依赖
└── start_api.ps1          # 启动脚本
```

## 使用示例

### 处理OD数据

```bash
curl -X POST "http://localhost:8000/api/v1/process_od_data/" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2025-08-11T08:00",
    "end_time": "2025-08-11T08:15",
    "interval_minutes": 5,
    "taz_file": "templates/taz_files/TAZ_5_validated.add.xml",
    "network_file": "templates/network_files/sichuan202503v6.net.xml",
    "case_name": "测试案例",
    "description": "这是一个测试案例"
  }'
```

### 运行仿真

```bash
curl -X POST "http://localhost:8000/api/v1/run_simulation/" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_20250822_003318",
    "simulation_name": "测试仿真",
    "simulation_description": "自动化测试仿真运行功能",
    "gui": false,
    "simulation_type": "microscopic",
    "simulation_outputs": ["summary", "tripinfo"]
  }'
```

### 执行精度分析

```bash
curl -X POST "http://localhost:8000/api/v1/analyze_accuracy/" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_20250821_155513",
    "simulation_ids": ["sim_0821_161746_micro"]
  }'
```

### 查看分析历史

```bash
# 查看精度分析历史
curl "http://localhost:8000/api/v1/analysis/analysis_results/case_20250821_155513?analysis_type=accuracy"

# 查看所有分析类型历史
curl "http://localhost:8000/api/v1/analysis/analysis_history/case_20250821_155513"
```

## 开发指南

### 架构原则

1. **API层职责**: 
   - 处理HTTP请求/响应
   - 参数验证和序列化
   - 调用业务服务
   - 目录组织和协调

2. **Shared层职责**:
   - 核心业务逻辑和算法
   - 数据访问和处理（门架数据、E1检测器数据）
   - 分析工具（精度、机理、性能分析）
   - 数据处理器（OD、门架、仿真数据）
   - 通用工具函数

### 新功能开发流程

1. **确定功能归属**
   - 数据处理 → `api/services/data_service.py`
   - 案例管理 → `api/services/case_service.py`
   - 仿真控制 → `api/services/simulation_service.py`
   - 精度分析 → `api/services/accuracy_service.py`
   - 机理分析 → `api/services/mechanism_service.py`
   - 性能分析 → `api/services/performance_service.py`
   - 模板管理 → `api/services/template_service.py`

2. **模块化开发**
   - 请求模型 → `api/models/requests/`
   - 响应模型 → `api/models/responses/`
   - 业务逻辑 → `api/services/`
   - API端点 → `api/routes/`
   - 核心功能 → `shared/utilities/` 或 `shared/data_access/`

3. **代码规范**
   - 遵循PEP 8代码风格
   - 所有函数必须有文档字符串
   - 使用类型注解
   - 统一的错误处理机制

## 测试

系统包含完整的测试覆盖，使用Playwright MCP进行自动化测试：

### 测试范围
- **基础功能测试**: 页面加载、导航、模板管理
- **OD数据处理测试**: 时间配置、文件选择、数据生成
- **仿真运行测试**: 仿真启动、参数配置、状态监控
- **结果分析测试**: 三种分析类型执行和历史查看
- **案例管理测试**: 案例列表、详情、操作功能
- **API接口测试**: 所有核心API端点验证

### 测试执行
```bash
# 启动API服务（必需）
.\start_api.ps1

# 查看测试清单
cat docs/testing/Playwright_MCP_测试任务清单.md

# 使用Playwright MCP执行自动化测试
# （具体执行方式参考测试清单文档）
```

### 测试状态（v0.65）
- ✅ 基础功能：100%通过
- ✅ OD数据处理：完全正常
- ✅ 仿真运行：启动和监控正常
- ✅ 结果分析：所有类型分析和历史查看正常
- ✅ 案例管理：完整功能验证通过
- ✅ API接口：所有端点测试通过

## 故障排除

### 常见问题

1. **API服务启动失败**
   - 检查端口8000是否被占用
   - 确认依赖包已正确安装
   - 检查.env配置文件

2. **模块导入错误**
   - 确保从项目根目录运行
   - 检查Python路径设置
   - 验证shared模块路径

3. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证.env中的数据库配置
   - 确认网络连接

### 性能指标（v0.65验证）

- **页面加载时间**: < 3秒 ✅
- **表单提交响应**: < 2秒 ✅
- **仿真启动响应**: < 5秒 ✅
- **API响应时间**: < 1秒 ✅
- **分析执行**: 精度分析完整执行正常 ✅

### 已知问题

1. **中文字体警告**: 图表生成时出现中文字体缺失警告，但不影响功能
2. **仿真长时间运行**: 大规模仿真可能需要较长时间完成

## 版本信息

- **当前版本**: v0.65 🚀
- **架构状态**: ✅ 完全模块化
- **核心功能**: ✅ 完全可用
- **测试状态**: ✅ 全面验证通过
- **Python版本**: 3.10+

## 重要变更

### v0.65 (2025-08-22) - 版本更新和功能优化

- ✅ 完善三类分析功能（精度、机理、性能）
- ✅ 修复"查看历史结果"功能重要问题
- ✅ 完整的Playwright MCP自动化测试验证
- ✅ 所有核心功能端到端测试通过
- ✅ API接口全面测试验证
- ✅ 用户界面响应性能优化

### 测试验证成果

- **功能完整性**: 所有主要功能模块验证通过
- **API稳定性**: 所有分析相关API正常响应
- **用户体验**: 界面操作流畅，响应迅速
- **数据完整性**: 分析结果包含丰富图表和报告

## 文档资源

- [新架构开发指南](docs/development/新架构开发指南.md)
- [新架构API指南](docs/api_docs/新架构API指南.md)
- [Playwright MCP测试任务清单](docs/testing/Playwright_MCP_测试任务清单.md)
- [部署指南](docs/DEPLOYMENT_GUIDE.md)
- [架构重构完成报告](docs/development/架构重构完成报告.md)

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目负责人: [姓名]
- 技术支持: [邮箱]
- 问题反馈: [GitHub Issues]

---

**文档版本**: v0.65  
**最后更新**: 2025-08-22  
**系统状态**: ✅ 核心功能完全可用  
**测试状态**: ✅ 全面验证通过  
**维护者**: 开发团队