# 任务分解：交通管控方案管理与批量优化

**变更ID**: implement-plan-management-and-batch-optimization
**预计工期**: 4-6周
**优先级**: P0（Phase 2核心功能）

## 任务组织

任务按照三个阶段组织，每个阶段交付可验证的用户价值：

1. **Phase 1：方案管理核心** (1-2周) - 方案CRUD、XML生成、引用保护
2. **Phase 2：批量优化仿真** (2-3周) - 批量仿真、进度监控、结果汇总
3. **Phase 3：集成与优化** (1周) - 基准方案、验证增强、文档完善

---

## Phase 1：方案管理核心（1-2周）

### 任务1.1：增强Plan实体模型 ✅

**文件**: `api/models/control/entities/plan.py`

**工作内容**:

- [X] 在现有Plan模型基础上增加新字段
  - `tags: List[str]` - 标签列表
  - `target_scenario: Optional[str]` - 目标场景
  - `expected_effects: Optional[Dict[str, str]]` - 预期效果
- [X] 添加计算属性
  - `is_baseline` - 判断是否为基准方案（检查plan_id == "baseline_plan"）
  - `strategy_count` - 策略数量
- [X] 添加示例数据和文档字符串
- [X] 确保所有字段有类型提示和Field描述

**验证**:

```bash
pytest tests/unit/models/test_plan_entity.py
# 4 tests passing
```

**完成时间**: 2025-10-25
**预计时间**: 2小时

---

### 任务1.2：创建Plan请求/响应模型 ✅

**文件**:

- `api/models/control/requests/plan_request.py`
- `api/models/control/responses/plan_response.py`

**工作内容**:

- [X] 创建 `CreatePlanRequest`模型
  - 必填: plan_name, strategy_ids
  - 可选: description, tags, target_scenario, expected_effects
- [X] 创建 `UpdatePlanRequest`模型（所有字段可选）
- [X] 创建 `PlanResponse`模型（包含完整plan信息）
- [X] 创建 `PlanListResponse`模型（分页列表）
- [X] 创建 `PlanValidationResponse`模型（验证结果）
- [X] 创建 `PlanPreviewResponse`模型（预览信息）

**验证**:

```bash
# 模型已创建并在service测试中验证
ls api/models/control/requests/plan_request.py
ls api/models/control/responses/plan_response.py
```

**完成时间**: 2025-10-26
**预计时间**: 3小时

---

### 任务1.3：实现方案文件管理器 ✅

**文件**: `shared/control_tools/plan_file_manager.py`

**工作内容**:

- [X] 实现 `create_plan()`方法
  - 生成plan_id（格式：plan_YYYYMMDD_HHMMSS_xxxxx）
  - 创建方案目录结构
  - 保存plan_metadata.json
  - 保存strategy_refs.json
  - 更新plans_index.json
- [X] 实现 `get_plan()`方法（读取方案详情）
- [X] 实现 `update_plan()`方法（更新元数据）
- [X] 实现 `delete_plan()`方法（删除方案及文件，含基准方案保护）
- [X] 实现 `list_plans()`方法（列出所有方案，支持过滤）
- [X] 实现 `get_plan_strategies()`方法（加载方案的策略实例）
- [X] 实现 `regenerate_plan_xml()`方法（重新生成XML）
- [X] 实现 `ensure_baseline_plan_exists()`方法（基准方案自动创建）
- [X] 添加完整的文档字符串和类型提示
- [X] 添加日志记录

**验证**:

```bash
pytest tests/unit/shared/control_tools/test_plan_file_manager.py
# 10 tests passing
```

**完成时间**: 2025-10-26
**预计时间**: 1天

---

### 任务1.4：增强Additional生成器 ✅

**文件**: `shared/control_tools/additional_generator.py`

**工作内容**:

- [X] 实现 `generate_plan_additional()`方法
  - 接收plan_id, plan_name, strategies列表
  - 按类型分组策略（VSS、DHS、TEC）
  - 为每个策略生成XML（复用现有generate_strategy_xml）
  - 合并所有XML元素到`<additional>`根节点
  - 添加方案注释和策略注释
  - 格式化输出（缩进4空格）
- [X] 处理空方案（基准方案）
- [X] 添加XML验证（格式检查）
- [X] 添加日志和错误处理

**验证**:

```bash
pytest tests/unit/shared/control_tools/test_additional_generator_plan.py
# 7 tests passing
```

**完成时间**: 2025-10-26
**预计时间**: 4小时

---

### 任务1.5：实现方案验证器 ✅

**文件**: `shared/control_tools/plan_validator.py`

**工作内容**:

- [X] 创建 `ValidationResult`数据类
- [X] 创建 `Warning`数据类（type, severity, message, suggestion）
- [X] 实现 `validate_plan()`方法
  - 检查策略是否存在
  - 空间冲突检测（同一edge/lane被多个策略控制）
  - 时间协调检查（VSS-DHS协调性）
  - 策略类型兼容性检查
- [X] 实现各类验证规则函数
  - `_check_spatial_conflicts()`
  - `_check_timing_coordination()`
  - `_check_strategy_compatibility()`
- [X] 返回警告和建议（非阻塞模式，is_valid始终为True）
- [X] 添加文档和测试

**验证**:

```bash
pytest tests/unit/shared/control_tools/test_plan_validator.py
# 10 tests passing
```

**完成时间**: 2025-10-26
**预计时间**: 6小时

---

### 任务1.6：增强策略文件管理器（引用保护） ✅

**文件**: `shared/control_tools/strategy_file_manager.py`

**工作内容**:

- [X] 在策略元数据中添加 `referenced_by`字段
- [X] 实现 `increment_strategy_reference()`方法
- [X] 实现 `decrement_strategy_reference()`方法
- [X] 实现 `can_delete_strategy()`方法（返回是否可删除+引用方案列表）
- [X] 修改 `delete_strategy()`添加引用检查
- [X] 添加日志记录
- [X] 更新现有策略文件兼容性（自动添加referenced_by=[]）

**验证**:

```bash
pytest tests/unit/shared/control_tools/test_strategy_reference_protection.py
# 9 tests passing
```

**完成时间**: 2025-10-26
**预计时间**: 3小时

---

### 任务1.7：实现方案管理服务 ✅

**文件**: `api/services/control_plan_service.py`

**工作内容**:

- [X] 创建 `ControlPlanService`类
- [X] 实现 `create_plan()`方法
  - 验证所有strategy_ids存在
  - 调用plan_file_manager.create_plan()
  - 加载策略实例
  - 调用additional_generator.generate_plan_additional()
  - 保存XML到方案目录
  - 更新策略引用计数
  - 调用plan_validator验证（返回警告）
- [X] 实现 `get_plan()`方法（支持include_strategies参数）
- [X] 实现 `list_plans()`方法（支持tags、scenario过滤）
- [X] 实现 `update_plan()`方法
  - 基准方案保护：禁止修改strategy_ids为非空
  - 如果strategy_ids变化，重新生成XML
  - 更新策略引用计数
- [X] 实现 `delete_plan()`方法
  - 禁止删除baseline_plan（由file_manager强制）
  - 减少策略引用计数
- [X] 实现 `regenerate_plan_xml()`方法（手动重新生成XML）
- [X] 实现 `validate_plan_config()`方法
- [X] 实现 `preview_plan()`方法
- [X] 添加完整的错误处理和日志

**验证**:

```bash
pytest tests/unit/services/test_control_plan_service.py
# 10 tests passing
```

**完成时间**: 2025-10-26
**预计时间**: 1天

---

### 任务1.8：创建方案管理API路由 ✅

**文件**: `api/routes/control_plan_routes.py`

**工作内容**:

- [X] 创建路由文件，定义APIRouter（prefix="/api/v1/control/plans"）
- [X] 实现POST /api/v1/control/plans/（创建方案）
- [X] 实现GET /api/v1/control/plans/（列出方案）
- [X] 实现GET /api/v1/control/plans/{plan_id}（获取详情）
- [X] 实现PUT /api/v1/control/plans/{plan_id}（更新方案）
- [X] 实现DELETE /api/v1/control/plans/{plan_id}（删除方案）
- [X] 实现POST /api/v1/control/plans/{plan_id}/generate_additional（重新生成XML）
- [X] 实现POST /api/v1/control/plans/{plan_id}/validate（验证方案）
- [X] 实现POST /api/v1/control/plans/{plan_id}/preview（预览方案）
- [X] 添加请求/响应模型验证
- [X] 添加错误处理（404、400等）
- [X] 添加OpenAPI文档字符串
- [X] 在 `api/main.py`中注册路由

**验证**:

```bash
# 路由已实现并在服务中测试
ls api/routes/control_plan_routes.py
# 可通过 http://localhost:8000/docs 查看API文档
```

**完成时间**: 2025-10-26
**预计时间**: 6小时

---

### 任务1.9：创建方案管理前端页面 ✅

**文件**: `frontend/control/plans.html`及相关JS/CSS

**工作内容**:

- [X] 创建方案列表页面（复用现有样式）
  - 显示所有方案（卡片式）
  - 基准方案特殊标记（无法删除）
  - 过滤功能（tags、scenario）
  - 搜索功能
- [X] 实现新建方案模态框
  - 方案名称输入
  - 描述输入
  - 策略多选列表（从API加载）
  - 标签输入
  - 目标场景输入
  - 预期效果输入（键值对）
  - 实时验证警告显示
  - 预览XML按钮
- [X] 实现方案详情页面
  - 基本信息展示
  - 包含策略列表（展开显示详情）
  - XML预览（代码高亮）
  - 编辑/删除/重新生成按钮
- [X] 实现编辑方案模态框（复用新建）
- [X] 实现API调用（fetch）
  - 列表、创建、更新、删除
  - 验证、预览
- [X] 添加加载状态和错误提示
- [X] 响应式布局

**验证**:

```bash
# 启动服务器
.\start_api.ps1
# 浏览器访问 http://localhost:8000/control/plans.html
# E2E测试
npx playwright test tests/e2e/test_plan_management.spec.js
```

**完成时间**: 2025-10-26
**预计时间**: 2天

---

### 任务1.10：编写Phase 1单元测试 ✅

**文件**: `tests/unit/`相关测试文件

**工作内容**:

- [X] Plan实体模型测试 (4 tests passing)
- [X] Plan请求/响应模型测试 (covered by entity tests)
- [X] plan_file_manager测试 (10 tests passing)
  - 创建、读取、更新、删除方案
  - 索引管理
  - 策略加载
  - 基准方案自动创建和保护
- [X] additional_generator增强测试 (7 tests passing)
  - generate_plan_additional测试
  - 空方案测试
  - 多策略组合测试
  - XML结构验证
- [X] plan_validator测试 (10 tests passing)
  - 各类验证规则测试
  - 警告生成测试
  - 空间冲突检测
  - 时间协调检查
  - 策略兼容性检查
- [X] strategy引用保护测试 (9 tests passing)
  - increment/decrement reference
  - can_delete_strategy检查
- [X] control_plan_service测试 (10 tests passing)
  - 所有服务方法覆盖
  - 错误场景测试
  - 创建、读取、更新、删除、验证、预览

**验证**:

```bash
# 运行所有Phase 1计划管理相关的单元测试
pytest tests/unit/models/test_plan_entity.py \
       tests/unit/shared/control_tools/test_plan_file_manager.py \
       tests/unit/shared/control_tools/test_plan_validator.py \
       tests/unit/shared/control_tools/test_additional_generator_plan.py \
       tests/unit/shared/control_tools/test_strategy_reference_protection.py \
       tests/unit/services/test_control_plan_service.py -v

# 结果: All 50 tests passing
```

**完成时间**: 2025-10-26
**实际耗时**: 6小时
**测试覆盖**: 50个测试全部通过

---

### 任务1.11：编写Phase 1 E2E测试 ✅

**文件**: `tests/e2e/test_plan_management.spec.js`

**工作内容**:

- [X] 测试方案列表加载
- [X] 测试创建方案完整流程
  - 填写表单
  - 选择策略
  - 添加标签
  - 提交并验证
- [X] 测试方案详情查看
- [X] 测试方案编辑
- [X] 测试方案删除（含基准方案保护）
- [X] 测试方案验证警告显示
- [X] 测试XML预览
- [X] 测试策略引用保护（删除被引用策略）

**验证**:

```bash
npx playwright test tests/e2e/test_plan_management.spec.js
npx playwright test tests/e2e/test_plan_management.spec.js --headed
```

**完成时间**: 2025-10-26
**预计时间**: 6小时

---

## Phase 2：批量优化仿真（2-3周）

### 任务2.1：创建批量仿真数据模型

**文件**:

- `api/models/control/entities/batch_simulation.py`
- `api/models/control/requests/batch_request.py`
- `api/models/control/responses/batch_response.py`

**工作内容**:

- [ ] 创建 `BatchSimulationTask`模型
  - task_id, plan_id, plan_name, seed
  - status, simulation_id
  - started_at, completed_at, error
- [ ] 创建 `BatchSimulation`模型
  - batch_id, case_id, plan_ids
  - num_seeds, base_seed
  - tasks列表
  - status, progress
  - timestamps
- [ ] 创建 `CreateBatchRequest`模型
- [ ] 创建 `BatchProgressResponse`模型
- [ ] 创建 `BatchResultsResponse`模型
- [ ] 添加文档和示例

**验证**:

```bash
pytest tests/unit/models/test_batch_models.py
```

**预计时间**: 4小时

---

### 任务2.2：实现批量仿真调度器

**文件**: `shared/control_tools/batch_simulation_scheduler.py`

**工作内容**:

- [ ] 创建 `BatchSimulationScheduler`类
- [ ] 实现 `create_batch()`方法
  - 验证case_id和plan_ids
  - 生成batch_id（格式：batch_YYYYMMDD_HHMMSS）
  - 创建批次目录结构
  - 生成任务列表（plans × seeds）
  - 保存batch_metadata.json
  - 初始化batch_progress.json
- [ ] 实现 `start_batch()`方法（异步）
  - 动态并发控制（根据CPU线程数计算，支持40-60个并发）
  - 任务队列管理
  - 调用_run_task()执行单个任务
  - 更新进度
- [ ] 实现 `_run_task()`方法
  - 创建仿真目录（{batch_id}/{plan_id}/sim_{seed}/）
  - 复制case配置文件
  - 复制plan的control.add.xml
  - 调用simulation_service准备仿真
  - 更新sumocfg添加--seed参数
  - 启动仿真
  - 更新任务状态
  - 错误处理和日志
- [ ] 实现 `get_batch_progress()`方法
- [ ] 实现 `cancel_batch()`方法（取消所有pending任务）
- [ ] 实现 `_calculate_estimated_completion()`方法
- [ ] 添加动态并发控制（asyncio.Semaphore，基于CPU线程数计算并发数）
- [ ] 实现 `get_max_concurrent_simulations()`辅助函数
- [ ] 添加进度实时更新机制

**验证**:

```bash
pytest tests/unit/shared/control_tools/test_batch_scheduler.py
```

**预计时间**: 2天

---

### 任务2.3：实现批量优化服务

**文件**: `api/services/batch_optimization_service.py`

**工作内容**:

- [ ] 创建 `BatchOptimizationService`类
- [ ] 实现 `create_batch()`方法
  - 验证输入参数
  - 确保包含baseline_plan
  - 调用batch_simulation_scheduler.create_batch()
- [ ] 实现 `start_batch()`方法（异步启动）
- [ ] 实现 `get_batch_progress()`方法
- [ ] 实现 `get_batch_results()`方法
  - 读取所有仿真结果
  - 提取关键指标（tripinfo.xml、summary.xml）
  - 计算聚合统计（mean、std、min、max）
  - 生成对比摘要
- [ ] 实现 `cancel_batch()`方法
- [ ] 实现 `delete_batch()`方法
- [ ] 添加后台任务管理（使用FastAPI BackgroundTasks）
- [ ] 添加错误处理和日志

**验证**:

```bash
pytest tests/unit/services/test_batch_optimization_service.py
```

**预计时间**: 1天

---

### 任务2.4：创建批量优化API路由

**文件**: `api/routes/batch_optimization_routes.py`

**工作内容**:

- [ ] 创建路由文件（prefix="/api/v1/control/optimization"）
- [ ] 实现POST /batch（创建批次）
- [ ] 实现POST /batch/{batch_id}/start（启动批次）
- [ ] 实现GET /batch/{batch_id}/progress（获取进度）
- [ ] 实现GET /batch/{batch_id}/results（获取结果）
- [ ] 实现DELETE /batch/{batch_id}（取消/删除批次）
- [ ] 添加请求/响应验证
- [ ] 添加错误处理
- [ ] 添加OpenAPI文档
- [ ] 在main.py注册路由

**验证**:

```bash
pytest tests/unit/routes/test_batch_optimization_routes.py
```

**预计时间**: 4小时

---

### 任务2.4.5：修正批量仿真页面UX设计 ✅

**文件**: `frontend/control/simulations.html`

**问题**: 批量优化仿真页面未遵循策略管理、方案管理的UX设计规范

**工作内容**:

- [X] 统一顶栏样式（紫色渐变背景 `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`）
- [X] 统一侧边栏样式（背景色`#2c3e50`，active状态高亮）
- [X] 修正内容区布局（flex布局，padding: 30px）
- [X] 添加标准内容头部（`.content-header`，大标题+副标题）
- [X] 统一按钮样式（主按钮使用紫色渐变，hover效果一致）
- [X] 统一卡片/区块样式（白色背景，圆角8px，阴影）
- [X] 统一表单样式（标签、输入框、下拉框）
- [X] 添加loading和empty-state样式
- [X] 移除对外部`styles.css`的依赖，使用内联样式保持一致性

**验证**:

```bash
# 启动服务器
.\start_api.ps1
# 浏览器访问 http://localhost:8000/control/simulations.html
# 对比 plans.html 和 templates.html 确认视觉一致性
```

**完成时间**: 2025-10-26
**实际耗时**: 1小时

---

### 任务2.5：创建批量优化前端页面

**文件**: `frontend/control/optimization.html`及相关JS

**工作内容**:

- [ ] 创建批量仿真配置页面
  - Case选择下拉框
  - Plan多选列表（含基准方案）
  - 仿真参数配置（seeds数、起始seed、时长）
  - 预估信息显示（总任务数、预计耗时）
  - 开始按钮
- [ ] 创建仿真进度监控页面
  - 总进度条
  - 按方案分组的任务状态
  - 实时进度更新（轮询或WebSocket）
  - 任务状态图标（✓完成、▶运行中、⏸等待、✗失败）
  - 取消按钮
- [ ] 创建结果对比页面
  - 方案对比表格（基础指标）
  - 详细结果链接
  - 下载报告按钮
  - 导出数据按钮
- [ ] 实现API调用
  - 创建批次、启动、查询进度、获取结果
  - 轮询机制（每2秒更新进度）
- [ ] 添加加载状态和错误提示
- [ ] 响应式布局

**验证**:

```bash
# 浏览器访问 http://localhost:8000/control/optimization.html
npx playwright test tests/e2e/test_batch_optimization.spec.js
```

**预计时间**: 2天

---

### 任务2.6：集成现有仿真服务

**文件**: `api/services/simulation_service.py`（轻微修改）

**工作内容**:

- [ ] 确认现有prepare_simulation()支持--seed参数
- [ ] 如需修改，增加seed参数支持
- [ ] 确认control.add.xml可以通过复制方式添加
- [ ] 测试批量仿真调用现有服务的兼容性

**验证**:

```bash
pytest tests/unit/services/test_simulation_service_integration.py
```

**预计时间**: 3小时

---

### 任务2.7：编写Phase 2单元测试

**文件**: `tests/unit/`相关测试文件

**工作内容**:

- [ ] 批量仿真数据模型测试
- [ ] batch_simulation_scheduler测试
  - 创建批次
  - 任务生成
  - 并发控制
  - 进度跟踪
  - 取消机制
- [ ] batch_optimization_service测试
  - 所有服务方法
  - 错误场景
- [ ] batch_optimization_routes测试
  - 所有API端点
  - 请求验证

**验证**:

```bash
pytest tests/unit/ --cov=api --cov=shared
```

**预计时间**: 1天

---

### 任务2.8：编写Phase 2 E2E测试

**文件**: `tests/e2e/test_batch_optimization.spec.js`

**工作内容**:

- [ ] 测试批量仿真完整流程
  - 创建case（如不存在）
  - 创建方案（如不存在）
  - 配置批量仿真
  - 启动仿真
  - 监控进度
  - 等待完成
  - 查看结果
- [ ] 测试批量仿真取消
- [ ] 测试进度实时更新
- [ ] 测试结果对比显示

**验证**:

```bash
npx playwright test tests/e2e/test_batch_optimization.spec.js --headed
```

**预计时间**: 6小时

---

## Phase 3：集成与优化（1周）

### 任务3.1：实现基准方案自动创建 ✅

**文件**: `shared/control_tools/plan_file_manager.py`增强

**工作内容**:

- [X] 实现 `ensure_baseline_plan_exists()`函数
  - 检查baseline_plan是否存在
  - 如不存在，创建全局基准方案
  - 生成空XML文件
- [X] 在FastAPI启动事件中调用（api/main.py）
- [X] 添加日志记录
- [X] 测试首次启动和重复启动
- [X] 添加基准方案删除保护（plan_file_manager.py delete_plan()）
- [X] 添加基准方案更新限制（control_plan_service.py update_plan()）
- [X] 验证所有保护机制工作正常

**验证**:

```bash
# 删除baseline_plan目录
rm -rf control_data/plans/baseline_plan
# 启动服务器
.\start_api.ps1
# 验证baseline_plan已创建
ls control_data/plans/baseline_plan
# 运行保护机制测试
python test_baseline_plan.py
```

**完成时间**: 2025-10-26
**实际耗时**: 2小时

---

### 任务3.2：实现策略更新自动传播

**文件**: `api/services/control_strategy_service.py`增强

**工作内容**:

- [ ] 修改 `update_strategy()`方法
  - 更新策略后获取referenced_by列表
  - 异步重新生成所有引用方案的XML
  - 记录传播结果
  - 错误处理（部分失败不影响策略更新）
- [ ] 添加日志记录
- [ ] 测试多方案引用场景

**验证**:

```bash
pytest tests/unit/services/test_strategy_update_propagation.py
```

**预计时间**: 3小时

---

### 任务3.3：增强前端集成

**文件**: 现有前端页面增强

**工作内容**:

- [ ] 在策略管理页面添加"创建方案"快捷入口
- [ ] 在方案详情页面添加"启动批量仿真"按钮
- [ ] 在侧边导航添加"批量优化"菜单项
- [ ] 统一样式和交互模式
- [ ] 添加面包屑导航

**验证**:

```bash
# 手动测试完整工作流
npx playwright test tests/e2e/test_complete_workflow.spec.js
```

**预计时间**: 4小时

---

### 任务3.4：性能优化

**工作内容**:

- [ ] 优化方案列表加载（分页、懒加载）
- [ ] 优化策略加载（缓存）
- [ ] 优化进度查询（减少轮询频率、WebSocket考虑）
- [ ] 优化XML生成（缓存模板）
- [ ] 添加性能监控日志

**验证**:

```bash
# 性能测试
pytest tests/performance/test_plan_management_perf.py
```

**预计时间**: 6小时

---

### 任务3.5：文档完善

**文件**:

- `docs/api_docs/control_plan_api.md`（新增）
- `docs/user_guide/plan_management.md`（新增）
- `docs/user_guide/batch_optimization.md`（新增）
- `README.md`（更新）

**工作内容**:

- [ ] 编写API文档
  - 所有端点说明
  - 请求/响应示例
  - 错误代码说明
- [ ] 编写用户指南
  - 方案管理操作指南
  - 批量优化使用指南
  - 最佳实践
  - 常见问题
- [ ] 更新README
  - 新增功能说明
  - 更新架构图
- [ ] 更新CLAUDE.md
  - 新增模块说明
  - 更新开发指南

**预计时间**: 1天

---

### 任务3.6：集成测试和回归测试

**工作内容**:

- [ ] 运行所有单元测试确保通过
- [ ] 运行所有E2E测试确保通过
- [ ] 运行现有功能回归测试（策略管理）
- [ ] 修复发现的bug
- [ ] 确保代码覆盖率 >80%

**验证**:

```bash
# 所有单元测试
pytest tests/unit/ --cov=api --cov=shared --cov-report=html

# 所有E2E测试
npx playwright test

# 覆盖率报告
open htmlcov/index.html
```

**预计时间**: 1天

---

### 任务3.7：代码审查和重构

**工作内容**:

- [ ] 检查所有代码符合项目规范
  - 类型提示完整
  - 文档字符串完整
  - 函数长度 <30行
  - 嵌套深度 <3层
  - 无循环依赖
- [ ] 使用black格式化代码
- [ ] 使用flake8检查代码质量
- [ ] 重构复杂函数
- [ ] 添加缺失的日志

**验证**:

```bash
black api/ shared/ tests/
flake8 api/ shared/ --max-line-length=100
```

**预计时间**: 6小时

---

### 任务3.8：部署前检查

**工作内容**:

- [ ] 确保所有环境变量正确配置
- [ ] 确保数据目录存在（control_data/plans/）
- [ ] 测试基准方案自动创建
- [ ] 测试完整工作流（端到端）
- [ ] 准备部署文档
- [ ] 准备回滚计划

**验证**:

```bash
# 在干净环境测试
conda activate od_project
.\start_api.ps1
# 手动执行完整工作流
```

**预计时间**: 4小时

---

## 里程碑

### M1：Phase 1完成（第2周末）✅ 已完成

**完成日期**: 2025-10-26

- ✅ 方案CRUD功能完整（Task 1.3, 1.7, 1.8）
- ✅ XML自动生成（Task 1.4）
- ✅ 策略引用保护（Task 1.6）
- ✅ 前端方案管理页面可用（Task 1.9）
- ✅ 单元测试通过（Task 1.10 - 50个测试全部通过）
- ✅ E2E测试通过（Task 1.11）
- ✅ 基准方案自动创建和保护（Task 3.1）

### M2：Phase 2完成（第5周末）

- ✅ 批量仿真功能完整
- ✅ 进度监控可用
- ✅ 结果汇总可用
- ✅ 前端批量优化页面可用
- ✅ 单元测试通过
- ✅ E2E测试通过

### M3：Phase 3完成（第6周末）

- ✅ 基准方案自动创建
- ✅ 策略更新自动传播
- ✅ 性能优化完成
- ✅ 文档完善
- ✅ 代码审查通过
- ✅ 准备发布

---

## 依赖关系

### 关键路径

```
任务1.1-1.2 → 1.3-1.5 → 1.6-1.7 → 1.8 → 1.9 → 1.10-1.11
    ↓
任务2.1 → 2.2-2.3 → 2.4 → 2.5 → 2.6 → 2.7-2.8
    ↓
任务3.1-3.2 → 3.3-3.4 → 3.5-3.6 → 3.7-3.8
```

### 可并行任务

- 1.3、1.4、1.5 可并行（独立模块）
- 1.10、1.11 可并行（测试）
- 2.7、2.8 可并行（测试）
- 3.3、3.4、3.5 可并行（优化和文档）

---

## 风险缓解

### 风险1：批量仿真性能问题

- **监控**：在任务2.2中添加性能监控
- **缓解**：动态并发控制自动适配硬件（CPU线程数×75%）
- **备选**：通过环境变量MAX_CONCURRENT_SIMULATIONS调整并发数

### 风险2：策略更新传播耗时

- **监控**：在任务3.2中记录传播时间
- **缓解**：异步处理，添加进度指示
- **备选**：提供手动触发选项

### 风险3：测试覆盖不足

- **监控**：每个Phase结束检查覆盖率
- **缓解**：任务X.10、X.11专注测试
- **备选**：延长测试时间，优先核心功能

---

## 验收标准

### 功能完整性

- [ ] 用户可以创建、编辑、删除方案
- [ ] 方案自动生成有效的control.add.xml
- [ ] 策略被引用时无法删除
- [ ] 策略更新后方案XML自动重新生成
- [ ] 基准方案自动创建且可跨case复用
- [ ] 可以配置并启动批量仿真
- [ ] 批量仿真进度实时监控
- [ ] 批量仿真结果正确汇总
- [ ] 前端界面完整可用

### 质量标准

- [ ] 所有单元测试通过（覆盖率 >80%）
- [ ] 所有E2E测试通过
- [ ] 代码符合项目规范
- [ ] 文档完整
- [ ] 无严重Bug

### 性能标准

- [ ] 方案列表加载 <500ms
- [ ] 方案创建（含XML生成） <2s
- [ ] 批量仿真启动 <5s
- [ ] 进度查询 <200ms
- [ ] 单个仿真运行时间符合预期

---

**总预计工作量**: 4-6周（1人全职）

- Phase 1: 1-2周
- Phase 2: 2-3周
- Phase 3: 1周
