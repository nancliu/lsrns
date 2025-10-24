# 交通管控仿真优化 - 分阶段开发路线图

**目的**：将开发工作分解为小而可管理的阶段，每个阶段独立可测试、可交付。

**最后更新**：2025-10-23

---

## 📊 当前进度总览

### ✅ 已完成阶段

- **Phase 0**: 基础设施准备 ✅ (2025-10-18)
- **Phase 1A**: 策略模板系统 ✅ (2025-10-20) - 5个策略模板
- **Phase 1B**: 数据库驱动边选择器 ✅ (2025-10-22) - 性能优化至<500ms
- **Phase 1C**: 策略配置与CRUD ✅ (2025-10-23) - 19/19 测试通过

### 🎯 第一个里程碑达成！

**成果**: 用户现在可以完整地创建和管理交通管控策略实例
- ✅ 浏览和选择策略模板
- ✅ 使用高性能边选择器选择管控路段
- ✅ 动态生成参数表单并验证
- ✅ 创建、查看、删除策略实例

---

## 🚀 下一步推荐工作

### 推荐选项1: Phase 2 - 方案管理（2周）⭐ **强烈推荐**

**理由**：
1. **自然延续**：Phase 1完成了单个策略管理，Phase 2将多个策略组合成方案
2. **核心功能**：方案是进行批量仿真对比的基础
3. **技术风险可控**：Additional文件生成是关键技术，需要尽早验证
4. **用户价值高**：完成后用户可以设计完整的管控方案
5. **技术方案已验证**：基于最新研究，VSS/DHS/TEC三类策略的SUMO实现方案已明确

**关键交付物**：
- 方案CRUD API（组合多个策略）
- SUMO Additional文件生成器（VSS/DHS/TEC）
  - VSS: 使用`<variableSpeedSign edges="...">`（SUMO v1.18+，推荐）
  - DHS: 使用`<rerouter>` + `<closingLaneReroute>`
  - TEC: 优先使用`<calibrator>`（流量控制），备选`<closingReroute>`（完全关闭）
- 方案管理页面（策略选择、XML预览）

**技术要点**：
- **策略-方案两层架构**：策略（可复用单元） + 方案（策略组合）
- **XML元素排序**：VSS → DHS → TEC（按管控链条顺序）
- **支持基准方案**：无管控方案，用于对比分析

**工作流**：
```bash
cd docs/design
/speckit.specify
# 描述：方案数据模型、策略组合逻辑、Additional生成器设计
# 参考：sumo_control_strategies_research.md
```

### 推荐选项2: Phase 1D - 边选择器增强（1周）

**理由**：
1. **优化用户体验**：当前边选择器功能完整但可以更易用
2. **工作量小**：1周即可完成，风险低
3. **可选功能**：不影响核心流程，可作为快速迭代

**关键交付物**：
- 批量导入边列表（CSV/剪贴板）
- 选择历史记录
- 路网可视化增强（颜色编码、框选）

**建议**：可以延后到Phase 2-3之后作为用户体验优化项

### 技术预研建议

在开始Phase 2之前，建议进行以下技术验证：

1. **SUMO Additional文件格式验证**
   - 研究SUMO官方文档中的variableSpeedSign、rerouter、closingLaneRerouter格式
   - 创建测试用例验证生成的XML能被SUMO正确加载

2. **策略组合逻辑设计**
   - 多个策略作用于同一路段时的冲突检测
   - 策略生效时间段的重叠处理

---

## 开发原则

1. **小步迭代**：每个阶段1-2周，独立交付
2. **垂直切片**：每个阶段包含前后端完整功能
3. **先核心后扩展**：优先实现最小可用功能，再扩展
4. **降低风险**：技术难点优先验证

---

## 阶段规划总览

```
Phase 0: 基础设施准备（1周）
  └─ 数据模型、目录结构、API框架

Phase 1A: 策略模板系统（1周）✅
  └─ 模板定义、存储、读取、展示

Phase 1B: 数据库驱动的边选择器（2周）⭐核心
  └─ 数据库查询、多维度筛选、路网可视化

Phase 1C: 策略配置与CRUD（2周）
  └─ 动态表单、参数验证、策略管理

Phase 1D: 边选择器增强（1周）
  └─ 批量导入、历史记录（可延后）

Phase 2: 方案管理（2周）
  └─ 方案组建、Additional生成

Phase 3: 并行仿真（3周）
  └─ 批量调度、进度监控

Phase 4: 方案优化（2周）
  └─ 指标计算、排序对比
```

---

## 详细阶段分解

### **Phase 0: 基础设施准备**（1周）

#### 目标
建立开发基础，确保后续开发顺畅

#### 交付物
- [x] 数据模型定义（Pydantic Models）
- [x] 目录结构创建
- [x] API框架搭建（空路由）
- [x] 前端页面框架（空页面）

#### spec-kit工作流
```bash
# Step 1: 创建基础设施规格
/speckit.specify
# 描述：定义数据模型、目录结构、API路由框架

# Step 2: 生成实施计划
/speckit.plan

# Step 3: 生成任务清单
/speckit.tasks

# Step 4: 执行开发
/speckit.implement

# Step 5: 验证
/speckit.checklist
```

#### 关键任务
1. **数据模型**：
   - `api/models/control/entities/template.py` - ControlTemplate
   - `api/models/control/entities/strategy.py` - Strategy
   - `api/models/control/entities/plan.py` - Plan
   - `api/models/control/entities/batch_simulation.py` - BatchSimulation

2. **目录结构**：
   ```bash
   mkdir templates/control_strategies
   mkdir control_data/{strategies,plans,optimizations}
   mkdir api/routes/control
   mkdir api/services/control
   mkdir shared/control_tools
   mkdir frontend/control
   ```

3. **API框架**：
   - `api/routes/control_strategy_routes.py` - 空路由
   - `api/services/control_strategy_service.py` - 空服务
   - 注册到 `api/main.py`

4. **前端框架**：
   - `frontend/control/index.html` - 基础布局
   - `frontend/control/styles.css` - 样式
   - `frontend/control/app.js` - 导航切换

#### 验收标准
- [ ] 所有目录创建完成
- [ ] API路由可访问（返回空数据）
- [ ] 前端页面可打开，导航可切换
- [ ] 数据模型通过类型检查

---

### **Phase 1A: 策略模板系统**（1周）✅ 已完成（2025-10-20）

#### 目标
实现策略模板的定义、存储和读取，用户可以浏览模板

#### 交付物
- [x] 3种策略类型的模板示例（VSS, DHS, TEC）
- [x] 模板解析器
- [x] 模板列表API
- [x] 前端模板展示页面

#### 实际完成情况
- ✅ Branch: `002-strategy-template-system`
- ✅ 5个模板文件（VSS x2, DHS x1, TEC x2）
- ✅ API: `control_template_routes.py`
- ✅ 服务: `control_template_service.py`
- ✅ 工具: `template_loader.py`
- ✅ 前端: `frontend/control/templates.html`

#### spec-kit工作流
```bash
/speckit.specify
# 描述：策略模板JSON Schema、模板解析器、模板列表API

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

#### 关键任务
1. **模板定义**（JSON文件）：
   ```
   templates/control_strategies/
   ├── variable_speed_sign/
   │   ├── vss_moderate.json
   │   └── vss_strict.json
   ├── dynamic_hard_shoulder/
   │   └── dhs_peak_hours.json
   ├── toll_entrance_control/
   │   ├── tec_truck_ban.json
   │   └── tec_entrance_close.json
   └── templates_index.json
   ```

2. **模板解析器**：
   - `shared/control_tools/template_parser.py`
   - 函数：`load_template()`, `list_templates()`, `validate_template()`

3. **API实现**：
   - `GET /api/v1/control/templates/` - 获取所有模板
   - `GET /api/v1/control/templates/{template_id}` - 获取模板详情

4. **前端展示**（三步工作流）：
   - 步骤1：选择策略模板（模板卡片列表，支持选中）
   - 步骤2：选择管控路段（边选择器占位，Phase 1B实现）
   - 步骤3：配置策略参数（动态生成表单）→ 生成策略实例
   - 底部：已创建的策略实例列表

#### 验收标准
- [x] 至少3种策略类型各有1个模板（VSS x2, DHS x1, TEC x2）
- [x] API返回正确的模板列表（GET /api/v1/control/templates/）
- [x] 前端能展示模板卡片（三步工作流界面）
- [x] 模板参数说明清晰（parameters_schema包含类型、范围、单位等）

---

### **Phase 1B: 数据库驱动的边选择器**（2周）✅ 已完成（2025-10-22）

#### 目标
实现基于数据库的高级边选择功能，支持多维度筛选和可视化展示

#### 交付物
- [x] 数据库查询模块（从highway schema查询edge/node/gantry）
- [x] 高级筛选API（支持多条件组合）
- [x] 前端多维度筛选界面
- [x] 路网简图可视化（基于数据库坐标）

#### 实际完成情况
- ✅ Branch: `004-database-edge-selector`
- ✅ 数据库查询: `shared/data_access/edge_query.py`（9个查询函数）
- ✅ API路由: `control_strategy_routes.py`（边查询端点）
- ✅ 数据库索引: `004_add_edge_query_indexes.sql`（7个性能索引）
- ✅ 前端界面: `frontend/control/edge_selector.html`
- ✅ 性能优化: 从5-10秒降至<500ms（静态方向分类+数据库索引）

#### spec-kit工作流
```bash
/speckit.specify
# 描述：数据库边选择器，支持从highway.baseline_edge_hourly、
# highway.baseline_node_hourly、highway.baseline_gantry_hourly
# 等表查询并筛选路段，提供多维度筛选条件

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

#### 关键任务

##### 1. **数据库查询模块**
`shared/data_access/edge_query.py`

```python
# 核心查询函数
def query_edges_with_filters(
    route_codes: List[str] = None,          # 路线编码（如G4202, G5, SA2）
    node_types: List[str] = None,           # 节点类型（diverging/merging/entrance/exit）
    min_stake: float = None,                # 最小桩号
    max_stake: float = None,                # 最大桩号
    min_length: float = None,               # 最小长度（米）
    max_length: float = None,               # 最大长度（米）
    route_direction: str = None,            # 方向（clockwise/counterclockwise）
    demonstration_ids: List[int] = None,    # 示范段ID列表
    min_lanes: int = None,                  # 最小车道数
    with_gantry: bool = False               # 是否仅返回有门架的路段
) -> List[EdgeInfo]

# EdgeInfo包含：
# - edge_id, route_code, section_code
# - start_stake, end_stake (桩号范围)
# - length, num_lanes, route_direction
# - node_type（关联节点类型）
# - gantry_count, gantry_ids（门架信息）
```

**数据源表**（dim schema）：
- `dim.sim_network_edges` - 路段主表（edge_id, route_code, start_stake, end_stake, length, num_lanes）
- `dim.multiscale_node_units` - 节点单元表（node_type: diverging/merging/entrance/exit）
- `dim.sim_network_junctions` - 节点表（junction坐标）
- `dim.point_gantry` - 门架点表（门架位置和桩号）

**详细设计文档**：[docs/design/edge_selector_database_design.md](edge_selector_database_design.md)

##### 2. **API实现**
`api/routes/control_strategy_routes.py`

```python
GET /api/v1/control/edges/query
# 请求参数（所有可选）：
{
  "route_codes": ["G4202"],
  "node_types": ["diverging", "merging"],
  "min_length": 500,
  "max_length": 2000,
  "flow_threshold": 1500,
  "speed_threshold": 60,
  "pattern_type": "workday",
  "hour": 8
}

# 返回：
{
  "edges": [
    {
      "edge_id": "edge_e789012",
      "from_junction": "j123456",
      "to_junction": "j123457",
      "edge_length": 1250.5,
      "route_code": "G4202",
      "avg_speed": 55.3,
      "mean_flow": 1850,
      "node_type": "diverging",
      "gantry_count": 2,
      "stake_range": "K35.500-K36.750"
    }
  ],
  "total_count": 45
}
```

##### 3. **前端高级筛选界面**

```
┌────────────────────────────────────────────┐
│ 边选择器 - 高级筛选                         │
├────────────────────────────────────────────┤
│ 路线编码:   [G4202 ▼] [G5 ▼] [+ 添加]     │
│                                            │
│ 节点类型:   ☑ 分流点  ☑ 汇流点             │
│            ☐ 入口    ☐ 出口               │
│                                            │
│ 路段长度:   [500__] 米 至 [2000__] 米     │
│                                            │
│ 流量筛选:   工作日 早8点                   │
│            平均流量 > [1500__] 辆/小时     │
│                                            │
│ 速度筛选:   平均速度 < [60__] km/h         │
│                                            │
│            [重置] [查询]                   │
├────────────────────────────────────────────┤
│ 查询结果: 45个路段                          │
│                                            │
│ ┌────────────────────────────────────┐   │
│ │ 路段可视化图（Canvas）              │   │
│ │   • 高亮显示符合条件的路段          │   │
│ │   • 点击选择/取消选择               │   │
│ │   • 显示路段信息tooltip             │   │
│ └────────────────────────────────────┘   │
│                                            │
│ 已选路段 (3):                              │
│ • edge_e789012 (G4202, K35.5-K36.7) [x]  │
│ • edge_e789013 (G4202, K36.7-K38.2) [x]  │
│ • edge_e789015 (G4202, K39.0-K40.5) [x]  │
│                                            │
│            [清空] [确认选择]               │
└────────────────────────────────────────────┘
```

##### 4. **路网简图可视化**（Canvas）

**数据源**：
- 从数据库查询junction坐标（如果有）
- 或从net.xml解析节点位置
- 绘制edge连线

**功能**：
- 绘制路网结构
- 高亮筛选结果
- 点击选择/取消选择
- Tooltip显示详情
- 缩放、平移

#### 数据库Schema参考

基于dim schema实际表结构：

**dim.sim_network_edges** (路段主表):
- edge_id, from_junction, to_junction
- route_code, section_code, demonstration_id
- start_stake, end_stake (桩号范围)
- length (路段长度米), num_lanes (车道数)
- route_direction (clockwise/counterclockwise)
- function, type (道路类型)

**dim.multiscale_node_units** (节点单元):
- unit_id, unit_name, junction_id
- node_type (diverging, merging, entrance, exit等)
- route_code, section_code, demonstration_id
- stake_number (桩号)
- in_edge_count, out_edge_count
- connected_edge_ids (关联路段列表)

**dim.point_gantry** (门架点):
- gantry_id, gantry_name
- route_code, section_code
- gantry_stake (门架桩号)
- demonstration_id
- lng_84, lat_84 (坐标)

#### 验收标准
- [ ] 数据库查询模块能正确从dim schema查询路段
- [ ] 支持至少6种筛选条件（路线编码、节点类型、桩号、长度、方向、示范段）
- [ ] API返回正确的筛选结果（包含门架信息）
- [ ] 前端筛选界面功能完整（多维度筛选）
- [ ] 路网简图能正确显示（基于junction坐标）
- [ ] 选择的路段能正确传递给策略配置模块

---

### **Phase 1C: 策略配置与CRUD**（2周）✅ 已完成（2025-10-23）

#### 目标
实现策略的创建、编辑、删除功能，完成策略管理闭环

#### 交付物
- [x] 动态参数表单生成器
- [x] 策略CRUD API
- [x] 策略管理完整页面

#### 实际完成情况
- ✅ Branch: `005-control-instance-creator`
- ✅ 策略实例管理: `control_strategy_instance_routes.py`
- ✅ 服务层: `control_strategy_service.py`
- ✅ 文件管理: `shared/control_tools/strategy_file_manager.py`
- ✅ 参数验证: `shared/control_tools/parameter_validator.py`
- ✅ 实体定义: `shared/control_tools/entities.py`
- ✅ 前端集成: `frontend/control/templates.html`（三步工作流）
- ✅ 测试通过: US2 集成测试 19/19 通过，US4 删除工作流完整实现

#### spec-kit工作流
```bash
/speckit.specify
# 描述：策略CRUD API、动态表单生成、参数验证、策略存储

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

#### 关键任务
1. **动态表单生成**（前端）：
   - 根据模板的`parameters_schema`生成表单
   - 类型映射：`integer` → `<input type="number">`
   - 验证：必填项、范围检查

2. **策略存储**：
   - 文件路径：`control_data/strategies/{strategy_id}.json`
   - 索引文件：`control_data/strategies/strategies_index.json`

3. **API实现**：
   - `POST /api/v1/control/strategies/` - 创建策略
   - `GET /api/v1/control/strategies/` - 列表（支持分页、搜索）
   - `GET /api/v1/control/strategies/{id}` - 详情
   - `PUT /api/v1/control/strategies/{id}` - 更新
   - `DELETE /api/v1/control/strategies/{id}` - 删除

4. **参数验证**：
   - `shared/control_tools/parameter_validator.py`
   - 验证规则：必填、类型、范围、edge_id有效性

5. **前端完整流程**：
   ```
   选择模板 → 动态生成表单 → 选择边（Phase 1B组件）
            → 填写参数 → 提交创建 → 显示在策略列表
   ```

#### 验收标准
- [ ] 能基于模板创建策略
- [ ] 参数验证正常（前后端）
- [ ] 策略列表正常展示
- [ ] 可编辑、删除策略
- [ ] 数据持久化正常

---

### **Phase 1D: 边选择器增强**（1周，可选/延后）

#### 目标
增强边选择器的交互体验和性能（可放在Phase 4之后作为优化项）

#### 交付物
- [x] 批量导入边列表（从文件/剪贴板）
- [x] 选择历史记录
- [x] 路网图性能优化（大规模路网支持）
- [x] 高级可视化（颜色编码、图例）

#### spec-kit工作流
```bash
/speckit.specify
# 描述：边选择器增强功能，包括批量导入、历史记录、性能优化

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

#### 关键任务
1. **批量导入功能**：
   - 从CSV/Excel导入edge_id列表
   - 从剪贴板粘贴（多行edge_id）
   - 智能识别edge_id格式

2. **选择历史**：
   - 记录最近10次选择
   - 快速恢复之前的选择
   - 命名和保存常用选择集

3. **可视化增强**：
   - 颜色编码（按流量/速度/拥堵等级）
   - 图例显示
   - 框选功能（鼠标拖拽选择多个边）
   - 更流畅的缩放平移

4. **性能优化**：
   - Canvas分层渲染（背景层+高亮层）
   - 视口裁剪（只渲染可见区域）
   - 节流/防抖优化

#### 建议
**可以延后到Phase 4之后作为优化项**，Phase 1B的基础功能已满足核心需求。

---

### **Phase 2: 方案管理**（2周）

#### 目标
实现方案的组建和SUMO Additional文件生成

#### 交付物
- [x] 方案CRUD API
- [x] Additional文件生成器（3种策略类型）
- [x] 方案管理页面

#### spec-kit工作流
```bash
/speckit.specify
# 描述：方案数据模型、Additional生成器、方案CRUD API、前端方案管理

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

#### 关键任务
1. **Additional生成器**：
   - `shared/control_tools/additional_generator.py`
   - `generate_vss_xml(strategy)` - 可变限速
   - `generate_dhs_xml(strategy)` - 动态硬路肩
   - `generate_tec_xml(strategy)` - 入口控制
   - `generate_control_additional(plan, strategies)` - 合并生成

2. **方案API**：
   - `POST /api/v1/control/plans/` - 创建方案
   - `GET /api/v1/control/plans/` - 列表
   - `GET /api/v1/control/plans/{id}` - 详情
   - `PUT /api/v1/control/plans/{id}` - 更新
   - `DELETE /api/v1/control/plans/{id}` - 删除
   - `POST /api/v1/control/plans/{id}/generate` - 生成additional

3. **前端方案管理**：
   - 左侧：方案列表
   - 右侧：方案编辑
     - 基本信息
     - 策略选择器（从策略库多选）
     - 已选策略列表（可排序、移除）
     - Additional预览（XML高亮）
     - 保存/删除按钮

#### 验收标准
- [ ] 能创建方案并选择策略
- [ ] Additional文件生成正确（XML格式验证）
- [ ] 前端能预览生成的XML
- [ ] 可编辑、删除方案

---

### **Phase 3: 并行仿真**（3周）

#### 目标
实现批量仿真调度、进度监控

#### 细分子阶段

#### **Phase 3A: 单方案仿真集成**（1周）
```bash
/speckit.specify
# 描述：扩展现有simulation_service，支持管控仿真（单方案）

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

**任务**：
- 修改`simulation_service`支持additional参数
- 创建测试：案例 + 方案 → 运行仿真
- 验证：生成的tripinfo.xml正确

#### **Phase 3B: 批量调度器**（1周）
```bash
/speckit.specify
# 描述：批量仿真调度器、并发控制、进度跟踪

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

**任务**：
- `control_batch_sim_service.py`
- 并发控制（最多4个并行）
- 进度更新机制
- 状态管理（PENDING/RUNNING/COMPLETED/FAILED）

#### **Phase 3C: 前端监控界面**（1周）
```bash
/speckit.specify
# 描述：批量仿真前端、进度监控、结果展示

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

**任务**：
- 任务配置区（案例选择、方案多选）
- 进度监控面板（进度条、状态）
- 轮询更新（每2秒）
- 历史批次列表

#### 验收标准
- [ ] 能同时运行多个方案仿真
- [ ] 进度实时更新
- [ ] 仿真结果正确存储
- [ ] 错误处理完善

---

### **Phase 4: 方案优化**（2周）

#### 目标
实现评估指标计算和方案排序

#### spec-kit工作流
```bash
/speckit.specify
# 描述：评估指标计算器、多目标排序、优化分析API、可视化对比

/speckit.plan
/speckit.tasks
/speckit.implement
/speckit.checklist
```

#### 关键任务
1. **评估指标计算器**：
   - `shared/control_tools/evaluation_calculator.py`
   - `extract_metrics_from_tripinfo()` - 提取平均通行时间、总延误
   - `extract_metrics_from_summary()` - 提取平均速度、通过量
   - `calculate_composite_score()` - 加权求和

2. **排序算法**：
   - 归一化（Min-Max）
   - 加权求和
   - 排序返回Top-N

3. **优化API**：
   - `POST /api/v1/control/optimizations/` - 创建优化分析
   - `GET /api/v1/control/optimizations/{id}/ranking` - 获取排名
   - `GET /api/v1/control/optimizations/{id}/comparison` - 对比数据

4. **前端可视化**：
   - 雷达图对比（Chart.js）
   - 柱状图对比
   - 排名表格

#### 验收标准
- [ ] 指标提取正确
- [ ] 排序算法合理
- [ ] 前端图表展示清晰
- [ ] 可导出报告

---

## 推荐执行顺序

### ✅ **第一轮迭代**（完成基础功能）- 已完成

```
Phase 0 → Phase 1A → Phase 1B → Phase 1C ✅
        (基础)  (模板)  (边选择)  (策略管理)
                                    ↓
                            【第一个里程碑】✅
                      ✓ 用户可以创建和管理策略
```

**完成时间**: 2025-10-18 至 2025-10-23（5天）
**成果**: 策略模板系统、高性能边选择器、完整CRUD功能

---

### ⏭️ **第二轮迭代**（完成方案和仿真）- 当前推荐

```
Phase 2 → Phase 3A → Phase 3B → Phase 3C
(方案管理) (单仿真)  (批量调度)  (监控界面) 👈 下一步
    ↓
【第二个里程碑】
✓ 用户可以运行批量仿真对比方案
```

**预计工作量**: 6周
**关键产出**: Additional文件生成、批量仿真调度、进度监控

---

### **第三轮迭代**（完成优化分析）

```
Phase 4 → Phase 1D (可选)
(优化分析) (可视化选择器)
    ↓
【第三个里程碑】
✓ 完整的管控优化闭环
```

**预计工作量**: 3周
**关键产出**: 评估指标计算、多目标排序、可视化对比

---

## 每个阶段的spec-kit使用建议

### 标准流程
```bash
# 1. 明确需求
/speckit.specify
# 输入：功能描述、数据模型、API定义、验收标准

# 2. 生成计划
/speckit.plan
# 输出：详细实施计划、技术方案、风险点

# 3. 分解任务
/speckit.tasks
# 输出：具体任务清单、依赖关系、工作量估算

# 4. 执行开发
/speckit.implement
# 执行任务、编写代码、测试

# 5. 一致性检查（可选）
/speckit.analyze
# 检查跨模块一致性

# 6. 验收检查
/speckit.checklist
# 生成测试检查清单、验证交付物
```

### 注意事项
1. **每次只specify一个阶段**，避免范围过大
2. **先完成一个阶段再开始下一个**，确保质量
3. **每个阶段结束后进行测试和review**
4. **遇到问题及时调整计划**，不要硬推

---

## 风险控制

### 高风险项（优先验证）
1. **Additional文件生成正确性** → Phase 2创建测试用例验证
2. **并发仿真稳定性** → Phase 3A先单个测试，再批量
3. **指标计算准确性** → Phase 4创建标准测试数据

### 降低风险策略
1. **技术预研**：Phase 0期间验证关键技术（如路网解析）
2. **单元测试覆盖**：每个工具函数都要有测试
3. **集成测试**：每个阶段结束后做端到端测试
4. **用户反馈**：每个里程碑后邀请用户试用

---

## 总结

**推荐首次使用spec-kit的阶段**：**Phase 0 基础设施准备**

原因：
- 范围小，复杂度低
- 熟悉spec-kit工作流
- 为后续阶段打好基础

**开始命令**：
```bash
cd docs/design
/speckit.specify
# 描述Phase 0的需求（参考本文档的Phase 0部分）
```

祝开发顺利！🚀
