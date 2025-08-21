# SUMO 参数标定方案

本目录包含SUMO仿真参数标定的完整方案和实现代码。

## 🏗️ 架构集成方案

### 采用现有项目架构集成（推荐方案）

标定功能将作为**第四种分析类型**集成到现有的模块化架构中，保持系统的一致性和完整性。

#### 集成架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    OD数据处理与仿真系统                      │
├─────────────────────────────────────────────────────────────┤
│  API层 (FastAPI)                                           │
│  ├── 案例管理接口                                          │
│  ├── 仿真管理接口                                          │
│  ├── 分析接口                                              │
│  │   ├── 精度分析 (accuracy_analysis)                     │
│  │   ├── 机理分析 (mechanism_analysis)                     │
│  │   ├── 性能分析 (performance_analysis)                   │
│  │   └── 🆕 参数标定 (calibration_analysis)               │
│  └── 模板管理接口                                          │
├─────────────────────────────────────────────────────────────┤
│  Services层 (业务逻辑)                                     │
│  ├── 案例服务 (case_service)                               │
│  ├── 仿真服务 (simulation_service)                         │
│  ├── 分析服务                                              │
│  │   ├── accuracy_service                                  │
│  │   ├── mechanism_service                                 │
│  │   ├── performance_service                               │
│  │   └── 🆕 calibration_service                            │
│  └── 模板服务 (template_service)                           │
├─────────────────────────────────────────────────────────────┤
│  Shared层 (核心功能)                                       │
│  ├── analysis_tools/                                       │
│  │   ├── accuracy_analysis.py                              │
│  │   ├── mechanism_analysis.py                             │
│  │   ├── performance_analysis.py                           │
│  │   └── 🆕 calibration_analysis.py                        │
│  ├── calibration_tools/                                    │
│  │   ├── ga_xgboost_optimizer.py                           │
│  │   ├── sumo_runner.py                                    │
│  │   ├── parameter_generator.py                            │
│  │   └── fitness_calculator.py                             │
│  ├── data_access/                                          │
│  ├── data_processors/                                      │
│  └── utilities/                                            │
└─────────────────────────────────────────────────────────────┘
```

#### 集成优势
- **架构一致性**: 遵循现有的分层架构原则
- **功能完整性**: 标定作为仿真分析的自然延伸
- **维护效率**: 避免多项目维护的复杂性
- **用户体验**: 在同一系统中完成所有相关操作
- **技术复用**: 充分利用现有的基础设施和工具

## 📁 目录结构

```
docs/calibration/
├── README.md                    # 本文件，标定方案总览
├── design/                      # 方案设计文档
│   ├── calibration_strategy.md  # 标定策略详细设计
│   ├── parameter_analysis.md    # 参数影响分析
│   └── evaluation_metrics.md    # 评估指标定义
├── integration_guide.md         # 集成指南
├── api_reference.md             # API接口参考
└── user_manual.md               # 用户使用手册
```

### 🗂️ 配置文件位置建议


#### 推荐方案：项目级配置管理
```
项目根目录/
├── configs/
│   ├── calibration/                # 标定配置文件
│   │   ├── parameter_ranges.json
│   │   ├── ga_config.yaml
│   │   └── xgboost_config.yaml
│   ├── simulation/                 # 仿真配置
│   └── analysis/                   # 分析配置
```

### 🎯 标定模板文件位置

标定相关的SUMO配置模板建议放在现有的`templates/`目录下：
```
templates/
├── network_files/                  # 网络文件
├── taz_files/                      # TAZ文件
├── simulation_templates/            # 仿真配置模板
├── vehicle_templates/               # 车辆配置模板
└── calibration_templates/           # 🆕 标定配置模板
    ├── calibration_templates.json   # 不同场景的标定模板
    └── sumo_config_templates/      # SUMO配置模板
```

### 🏗️ 实际集成位置

根据架构集成方案，标定功能将集成到现有项目结构中：

```
项目根目录/
├── shared/
│   ├── analysis_tools/
│   │   ├── accuracy_analysis.py
│   │   ├── mechanism_analysis.py
│   │   ├── performance_analysis.py
│   │   └── 🆕 calibration_analysis.py    # 标定分析主模块
│   └── calibration_tools/                 # 新增标定工具目录
│       ├── ga_xgboost_optimizer.py        # GA+XGBoost混合优化器
│       ├── sumo_runner.py                 # SUMO仿真运行器
│       ├── parameter_generator.py         # 参数生成器
│       └── fitness_calculator.py          # 适应度计算器
├── api/
│   ├── services/
│   │   └── 🆕 calibration_service.py      # 标定服务
│   ├── routes/
│   │   └── 🆕 calibration_routes.py       # 标定路由
│   └── models/
│       └── requests/
│           └── 🆕 calibration_requests.py  # 标定请求模型
└── docs/calibration/                       # 标定相关文档
```

## 🚀 快速开始

### 1. 查看设计文档
- [标定策略设计](./design/calibration_strategy.md) - 了解整体方案
- [参数影响分析](./design/parameter_analysis.md) - 理解参数作用
- [评估指标定义](./design/evaluation_metrics.md) - 了解评估体系

### 2. 配置参数范围
- 编辑参数范围配置（根据选择的配置位置）
  - 方案: `configs/calibration/parameter_ranges.json`
- 选择适合的交通场景（高流量/低流量/混合交通）

### 3. 运行标定程序
```bash
# 通过API接口启动标定
POST /api/v1/calibration/create

# 或直接运行标定分析模块
python -m shared.analysis_tools.calibration_analysis
```

### 4. 查看结果
- 标定结果: `cases/{case_id}/results/calibration/calibration_results.json`
- 最优参数: `cases/{case_id}/results/calibration/best_parameters.json`
- 分析报告: `cases/{case_id}/results/calibration/analysis_report.json`

## 🔧 核心特性

- **混合优化**: GA + XGBoost 代理模型加速
- **参数标定**: 7个关键SUMO参数自动优化
- **并行仿真**: 支持多SUMO实例并行运行
- **增量学习**: 代理模型持续更新优化
- **综合评估**: 多指标加权适应度函数
- **架构集成**: 无缝集成到现有分析框架

## 🏗️ 技术架构

- **优化算法**: 遗传算法 (Genetic Algorithm)
- **代理模型**: XGBoost 回归器
- **仿真引擎**: SUMO (Simulation of Urban MObility)
- **数据处理**: Python + Pandas + NumPy
- **并行计算**: Multiprocessing + Threading
- **API框架**: FastAPI + Pydantic（复用现有框架）

## 📊 预期效果

- **仿真精度提升**: 流量误差降低30-50%
- **车辆容量增加**: 路网利用率提升20-40%
- **计算效率提升**: 通过代理模型加速，总体计算时间减少60-80%
- **系统完整性**: 标定功能与现有分析功能完美融合

## 🔄 Git管理建议

### 推荐方案：创建功能分支开发

#### 1. 分支策略
```bash
# 从main分支创建标定功能分支
git checkout -b feature/calibration-integration

# 开发过程中定期同步main分支的更新
git fetch origin
git rebase origin/main
```

#### 2. 开发流程
```bash
# 1. 创建功能分支
git checkout -b feature/calibration-integration

# 2. 开发标定功能
# ... 编写代码 ...

# 3. 提交代码（使用清晰的提交信息）
git add .
git commit -m "feat: 集成参数标定分析模块

- 新增calibration_analysis.py到analysis_tools
- 实现GA+XGBoost混合优化器
- 添加标定配置管理
- 集成到现有分析框架"

# 4. 推送到远程分支
git push origin feature/calibration-integration

# 5. 创建Pull Request
# 在GitHub/GitLab上创建PR，请求合并到main分支
```

#### 3. 为什么选择分支开发？

**优势**:
- **代码隔离**: 标定功能开发不影响main分支的稳定性
- **并行开发**: 其他开发者可以继续在main分支上工作
- **代码审查**: 通过PR进行代码审查，确保代码质量
- **回滚安全**: 如果出现问题，可以轻松回滚到main分支
- **版本管理**: 标定功能可以作为独立版本发布

**风险控制**:
- **定期同步**: 每周同步main分支的更新，避免冲突
- **小步提交**: 频繁提交小功能，便于问题定位
- **测试覆盖**: 确保标定功能有足够的测试覆盖
- **文档同步**: 及时更新相关文档

#### 4. 合并时机

**合并条件**:
- [ ] 标定功能开发完成并通过测试
- [ ] 代码审查通过
- [ ] 集成测试通过
- [ ] 文档更新完成
- [ ] 性能测试达标

**合并策略**:
- 使用Squash Merge，保持提交历史清晰
- 合并后删除功能分支
- 在main分支上打标签，标记标定功能版本

#### 5. 发布计划

```bash
# 合并到main后，创建版本标签
git tag -a v0.70.0 -m "Release: 集成SUMO参数标定功能"
git push origin v0.70.0

# 更新CHANGELOG.md
# 发布说明文档
```

## 📋 下一步计划

1. **立即开始**: 创建功能分支，开始标定功能开发
2. **第一周**: 完成基础框架和核心算法实现
3. **第二周**: 集成到现有分析框架，完成API接口
4. **第三周**: 测试和优化，准备代码审查
5. **第四周**: 代码审查、文档完善、合并到main分支

通过这种集成方案和分支管理策略，我们可以在保持项目架构清晰的同时，高效地开发标定功能，最终为用户提供完整的仿真分析解决方案。
