# 批量仿真配置增强 - OpenSpec需求规格

**Status**: ✅ Requirement Clarified (Phase 1 - Requirements)
**Version**: v1.0
**Date**: 2025-11-03
**Owner**: Traffic Simulation Team

---

## 1. 需求概述

在批量仿真配置页（`frontend/control/simulations.html`）的"仿真配置"部分增加以下功能：

### 1.1 新增功能
- ✅ **仿真时长设置** - 可超过或短于输入数据时长，默认使用输入数据时长
- ✅ **车辆类型模板选择** - 支持从templates目录选择不同vehicle_types.json文件
- ✅ **输出级别重构** - 从3级dropdown改为独立checkboxes，简化为4个具体输出项
- ✅ **批次任务预估简化** - 移除种子序列显示

### 1.2 影响范围
- **Frontend**: HTML表单、JavaScript逻辑、CSS样式
- **Backend API**: 请求模型、服务层、SUMO配置生成
- **Data Models**: `CreateBatchRequest`, `simulation_config.json`

---

## 2. 功能需求详解

### 2.1 F1: 仿真时长设置

#### 业务需求
- 用户可自定义仿真时长，突破输入数据的时间限制
- 超出输入数据时长时，已进入车辆继续运行但不再有新车辆进入
- 默认行为保持不变：使用输入数据的时间范围

#### 技术规格

| 属性 | 值 |
|------|-----|
| UI控件 | Radio (使用默认/自定义) + 输入框 (小时/分钟) |
| 字段名 | `simulation_duration` |
| 数据类型 | `{ use_default: bool, hours: int\|null, minutes: int\|null }` |
| 默认值 | `{ use_default: true, hours: null, minutes: null }` |
| 最小时长 | 1分钟 |
| 最大时长 | 24小时0分钟 |
| 验证规则 | 自定义时需指定hours/minutes；总分钟数在1-1440范围内 |
| SUMO实现 | 覆盖`--end`参数 = `begin_time + custom_duration` |

#### 用户场景
1. **快速衰退仿真** - 输入数据2小时，但网络在2.5小时时完全清空
2. **长期稳态仿真** - 输入数据3小时，运行8小时观察长期稳定状态
3. **政策验证** - 仅在特定时段运行（例如早高峰7-10点）

---

### 2.2 F2: 车辆类型模板选择

#### 业务需求
- 支持多套车辆动力学参数配置
- 不改变车型种类，仅改变参数（加速度、跟驰模型、换道参数等）
- 批量级别统一选择（整个batch的所有任务使用同一模板）

#### 技术规格

| 属性 | 值 |
|------|-----|
| UI控件 | Dropdown列表，动态从templates目录加载 |
| 字段名 | `vehicle_types_template` |
| 数据类型 | `string` (文件名) |
| 默认值 | `"vehicle_types.json"` |
| 文件位置 | `templates/config_templates/vehicle_templates/*.json` |
| 验证 | 文件必须存在且符合模板格式 |
| 新API端点 | `GET /api/v1/template/vehicle-types/list` |

#### 用户场景
1. **驾驶行为研究** - A/B对比：激进vs保守驾驶行为对流量的影响
2. **参数标定** - 不同地区/时段的车辆参数调整
3. **跨区域模型迁移** - 成都参数 vs 其他城市参数

---

### 2.3 F3: 输出配置简化

#### 业务需求
- 移除抽象的"minimal/standard/full"分级
- 直接显示实际输出文件类型（summary, tripinfo, edgedata, E1检测器）
- summary和E1检测器固定启用
- tripinfo和edgedata可选，默认不启用

#### 技术规格

| 属性 | 值 |
|------|-----|
| 固定启用 | summary.xml, E1检测器数据 |
| 可选项1 | edgedata.xml (路段流量) - 默认OFF |
| 可选项2 | tripinfo.xml (车辆行程) - 默认OFF |
| UI提示 | 显示性能影响（处理时间/文件大小） |
| 数据结构 | `output_config: { summary_xml, e1_detector_data, edgedata_xml, tripinfo_xml }` |
| 向后兼容 | 支持旧API的`output_level`字段，自动映射 |

#### 性能影响
- tripinfo.xml: +30%仿真时间, 文件可能>200MB
- edgedata.xml: +20%仿真时间, 文件可能>50MB

---

### 2.4 F4: 批次任务预估简化

#### 业务需求
- 移除"种子序列: 66, 67, 68"显示
- 保留任务数量实时估算功能

#### 技术规格

| 属性 | 值 |
|------|-----|
| 显示格式 | "X个方案 × Y个随机种子 = Z个并行仿真任务" |
| 更新时机 | 方案数或种子数改变时实时更新 |
| 移除内容 | `<div id="seedSequencePreview">` 及相关代码 |

---

## 3. UI/UX设计

### 3.1 配置表单布局

```
┌─────────────────────────────────────────────────┐
│ 仿真配置                                       [+展开]│
├─────────────────────────────────────────────────┤
│                                                 │
│ 案例选择：                                      │
│ [▼ 选择OD案例 ________________]                 │
│                                                 │
│ 方案选择：                                      │
│ [☑ baseline_plan (基准方案)]                    │
│ [☐ plan_vss_001   (可变限速)]                   │
│ [☐ plan_tec_001   (收费管控)]                   │
│ ℹ️ 提示：基准方案将自动包含作为对比基线         │
│                                                 │
│ 仿真时长设置：                                  │
│ (◉) 使用输入数据时长                           │
│     当前数据时长：7小时30分钟 (07:00 - 14:30)  │
│ (○) 自定义仿真时长                             │
│     [____] 小时  [____] 分钟                    │
│     ℹ️ 可设置短于或长于数据时长。超出时长后，  │
│        已进入车辆继续行驶至离开路网。           │
│                                                 │
│ 车辆类型模板：                                  │
│ [▼ vehicle_types.json (默认参数) ____]         │
│ ℹ️ 提示：不同模板使用相同车型，但车辆动力学、 │
│        跟驰、换道参数不同。                     │
│                                                 │
│ 仿真输出配置：                                  │
│ [☑] summary.xml (基础统计) - 总是启用           │
│ [☑] E1检测器数据 (门架流量) - 总是启用           │
│      已在实际门架位置配置                       │
│                                                 │
│ [☐] edgedata.xml (路段流量统计)                │
│      ⚠️ 性能提示：会增加约20%仿真时间，         │
│         生成文件可能较大 (>50MB)               │
│                                                 │
│ [☐] tripinfo.xml (车辆行程信息)                │
│      ⚠️ 性能提示：会增加约30%仿真时间，         │
│         生成文件可能很大 (>200MB)              │
│                                                 │
│ 随机种子数（每个方案）：                       │
│ [____] (范围：1-10，默认：3)                   │
│                                                 │
│ 起始种子：                                      │
│ [____] (默认：66)                              │
│                                                 │
│ 批次任务数量预估：                              │
│ ┌─────────────────────────────────┐           │
│ │ 3个方案 × 3个随机种子 = 9个并行仿真任务     │
│ └─────────────────────────────────┘           │
│                                                 │
│                 [清除配置]  [创建批次 →]       │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 3.2 交互细节

| 交互场景 | 行为 |
|---------|------|
| 勾选"使用输入数据时长" | 禁用小时/分钟输入框，隐藏提示文本 |
| 取消勾选 | 启用小时/分钟输入框，显示提示文本 |
| 输入小时数 > 24 | 显示红色错误："不能超过24小时" |
| 输入小时数 + 分钟数 = 0 | 显示红色错误："仿真时长至少为1分钟" |
| 改变方案数 | 实时更新任务数量估算 |
| 改变种子数 | 实时更新任务数量估算 |
| 勾选tripinfo | 显示性能提示 |
| 勾选edgedata | 显示性能提示 |

### 3.3 改进的UI布局（紧凑设计）

采用**网格式布局**，相关参数横向排列以减少页面高度：

```
┌──────────────────────────────────────────────────────────────────┐
│ 仿真配置                                                    [+展开]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 案例和方案：                                                    │
│ ┌─案例──────────────┐  ┌─方案选择────────────────────────────┐  │
│ │ [▼案例选择]       │  │ ☑baseline ☐plan_vss ☐plan_tec ...│  │
│ └───────────────────┘  └─ ℹ️ 基准方案自动包含 ───────────────┘  │
│                                                                  │
│ 时长配置：                                                      │
│ ┌─输入数据时长──────────┐  ┌─自定义时长──────────────────────┐  │
│ │(◉) 当前: 7h30m        │  │(○) [__]小时 [__]分钟           │  │
│ │(07:00 - 14:30)       │  │   ℹ️ 可设1分钟-24小时         │  │
│ └───────────────────────┘  └─ ⚠️ 超出后车辆继续运行 ─────────┘  │
│                                                                  │
│ 模板和输出：                                                    │
│ ┌─车辆类型模板─────────┐  ┌─仿真输出配置─────────────────────┐  │
│ │ [▼vehicle_types.json]│  │ ☑summary  ☑E1检测器            │  │
│ │ (默认参数)           │  │ ☐edgedata ⚠️ +20%仿真时间      │  │
│ │ ℹ️ 选择不同参数配置  │  │ ☐tripinfo ⚠️ +30%仿真时间      │  │
│ └───────────────────────┘  └───────────────────────────────────┘  │
│                                                                  │
│ 种子配置：                                                      │
│ 随机种子数:    [__] (1-10, 默认3)                              │
│ 起始种子:      [__] (默认66)                                   │
│                                                                  │
│ ┌─批次任务数量预估────────────────────────────────────────────┐  │
│ │ 3个方案 × 3个随机种子 = 9个并行仿真任务                     │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│                    [清除配置]  [创建批次 →]                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**布局特点**:
- ✅ 上半部分（案例/方案）- 2列横向
- ✅ 时长配置 - 2列对比式（数据时长 vs 自定义时长）
- ✅ 模板和输出 - 2列（左侧模板，右侧输出复选框）
- ✅ 种子配置 - 1行2个输入框（水平排列）
- ✅ 任务预估 - 单行展示
- ✅ 减少总体页面高度约40-50%

---

## 4. API规格

### 4.1 新增端点：GET /api/v1/template/vehicle-types/list

**目的**: 获取可用的vehicle types模板列表

**请求**:
```http
GET /api/v1/template/vehicle-types/list
```

**响应** (200 OK):
```json
{
  "success": true,
  "templates": [
    {
      "filename": "vehicle_types.json",
      "display_name": "默认参数",
      "description": "系统默认车辆参数配置（IDM跟驰模型）",
      "file_size_kb": 5.2,
      "modified_at": "2024-10-15T10:30:00Z",
      "is_default": true
    },
    {
      "filename": "vehicle_types_tj1.json",
      "display_name": "激进驾驶参数",
      "description": "更高加速度、更小安全距离、激进换道",
      "file_size_kb": 5.3,
      "modified_at": "2024-11-01T14:22:00Z",
      "is_default": false
    }
  ]
}
```

**错误** (500 Internal Server Error):
```json
{
  "success": false,
  "error": "无法扫描模板目录",
  "details": "..."
}
```

---

### 4.2 修改端点：POST /api/v1/control/batch-optimization/batch

**变更前**:
```json
{
  "case_id": "case_20251025_001",
  "plan_ids": ["baseline_plan", "plan_vss_001"],
  "num_seeds": 3,
  "base_seed": 66,
  "output_level": "standard"
}
```

**变更后**:
```json
{
  "case_id": "case_20251025_001",
  "plan_ids": ["baseline_plan", "plan_vss_001"],
  "num_seeds": 3,
  "base_seed": 66,

  "simulation_duration": {
    "use_default": false,
    "hours": 8,
    "minutes": 30
  },

  "vehicle_types_template": "vehicle_types_tj1.json",

  "output_config": {
    "summary_xml": true,
    "e1_detector_data": true,
    "edgedata_xml": true,
    "tripinfo_xml": false
  },

  "output_level": null  // 废弃但保留向后兼容
}
```

**请求验证规则**:
- `simulation_duration` (Optional)
  - 若`use_default=false`, 则hours和minutes必须有效
  - hours ∈ [0, 24], minutes ∈ [0, 59]
  - 总分钟数 ∈ [1, 1440]
- `vehicle_types_template` (Optional, default: "vehicle_types.json")
  - 必须是`templates/config_templates/vehicle_templates/`下的有效JSON文件
- `output_config` (Optional)
  - `summary_xml`和`e1_detector_data`若存在必须为true
  - `edgedata_xml`和`tripinfo_xml`为boolean

**响应** (200 OK):
```json
{
  "success": true,
  "batch_id": "batch_20251103_150022",
  "batch_dir": "cases/case_20251025_001/simulations/plan_opti/batch_20251103_150022",
  "num_tasks": 6,
  "message": "批次创建成功"
}
```

---

## 5. 数据模型

### 5.1 Pydantic Request Model (新增和修改)

**模型**: `SimulationDuration`
```python
class SimulationDuration(BaseModel):
    use_default: bool = Field(True)
    hours: Optional[int] = Field(None, ge=0, le=24)
    minutes: Optional[int] = Field(None, ge=0, le=59)

    def get_total_minutes(self) -> Optional[int]:
        """返回总分钟数，或None（表示使用默认）"""
        if self.use_default:
            return None
        total = (self.hours or 0) * 60 + (self.minutes or 0)
        if total < 1 or total > 1440:
            raise ValueError("仿真时长必须在1分钟-24小时之间")
        return total
```

**模型**: `OutputConfig`
```python
class OutputConfig(BaseModel):
    summary_xml: bool = Field(True)
    e1_detector_data: bool = Field(True)
    edgedata_xml: bool = Field(False)
    tripinfo_xml: bool = Field(False)
```

**模型**: `CreateBatchRequest` (修改)
```python
class CreateBatchRequest(BaseModel):
    case_id: str
    plan_ids: List[str]
    num_seeds: int = Field(3, ge=1, le=10)
    base_seed: int = Field(66, ge=0)

    # 新增字段
    simulation_duration: Optional[SimulationDuration] = None
    vehicle_types_template: str = Field("vehicle_types.json")
    output_config: Optional[OutputConfig] = Field(default_factory=OutputConfig)

    # 废弃但保留向后兼容
    output_level: Optional[Literal["minimal", "standard", "full"]] = None
```

---

### 5.2 simulation_config.json格式变更

**当前格式** (v0.x):
```json
{
  "output_level": "standard",
  "num_seeds": 3,
  "base_seed": 66,
  "seed_sequence": [66, 67, 68],
  "summary_xml": true,
  "e1_detector_data": true,
  "tripinfo_xml": true,
  "edgedata_xml": true,
  "created_at": "2025-11-03T14:30:22Z"
}
```

**新格式** (v1.0):
```json
{
  "num_seeds": 3,
  "base_seed": 66,

  "simulation_duration": {
    "use_default": false,
    "hours": 8,
    "minutes": 30,
    "total_minutes": 510
  },

  "vehicle_types_template": "vehicle_types_tj1.json",

  "output_config": {
    "summary_xml": true,
    "e1_detector_data": true,
    "edgedata_xml": true,
    "tripinfo_xml": false
  },

  "created_at": "2025-11-03T14:30:22Z"
}
```

**兼容性说明**:
- 旧格式batch仍可正常运行，无需升级
- 新创建的batch使用v1.0格式
- 负责解析config的代码需支持两种格式

---

## 6. 实现清单

| 模块 | 文件 | 类型 | 优先级 |
|------|------|------|--------|
| Frontend | `frontend/control/simulations.html` | HTML修改 | P0 |
| Frontend | `frontend/control/js/batch_simulation.js` | JS逻辑 | P0 |
| Frontend | `frontend/control/css/simulations.css` | CSS样式 | P1 |
| Backend API | `api/routes/batch_optimization_routes.py` | 新增端点 | P0 |
| Backend API | `api/models/control/requests/batch_request.py` | 模型修改 | P0 |
| Service | `api/services/batch_optimization_service.py` | 业务逻辑 | P0 |
| Service | `api/services/template_service.py` | 模板加载 | P1 |
| Shared | `shared/control_tools/batch_simulation_scheduler.py` | 批次调度 | P0 |
| Shared | `shared/utilities/sumo_utils.py` | SUMO配置 | P0 |

---

## 7. 测试要求

### 7.1 单元测试

- [ ] `SimulationDuration.get_total_minutes()` - 所有边界值
- [ ] `OutputConfig` - 默认值验证
- [ ] 仿真时长验证 - 1分钟、24小时、超出范围
- [ ] Vehicle template文件验证 - 有效/无效文件

### 7.2 集成测试

- [ ] 创建batch → 验证simulation_config.json格式
- [ ] SUMO配置生成 → 验证`--end`参数正确设置
- [ ] Vehicle template加载 → 验证车辆类型配置正确

### 7.3 E2E测试 (Playwright)

- [ ] 使用默认配置创建batch
- [ ] 自定义仿真时长（8小时30分钟）
- [ ] 选择非默认vehicle template
- [ ] 仅启用edgedata.xml输出
- [ ] 所有checkbox全选
- [ ] 任务数量预估实时更新
- [ ] 输入非法时长时显示错误提示

### 7.4 向后兼容性测试

- [ ] 旧API格式（使用`output_level`）仍能正常工作
- [ ] 旧批次的结果仍可正常读取和展示

---

## 8. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 用户误解仿真时长超限行为 | 中 | 中 | 清晰的UI提示 |
| Vehicle template格式错误导致仿真失败 | 中 | 高 | API端点验证 + 前端过滤 |
| 性能下降（tripinfo导致I/O瓶颈） | 低 | 中 | 默认不启用 + UI提示 |
| 旧客户端使用新API失败 | 低 | 中 | 向后兼容实现 |

---

## 9. 验收标准

- ✅ 所有4项功能正常工作
- ✅ UI/UX符合设计规格
- ✅ 所有单元/集成/E2E测试通过
- ✅ 向后兼容性验证完成
- ✅ API文档和用户指南更新
- ✅ 无性能回归（batch创建<500ms）

---

## 10. 时间表

| 阶段 | 工作内容 | 工作量 | 预计时间 |
|------|--------|--------|---------|
| Phase 1 | 输出配置简化 | 6h | 1天 |
| Phase 2 | Vehicle模板选择 | 4h | 0.5天 |
| Phase 3 | 仿真时长设置 | 5h | 1天 |
| Phase 4 | 任务预估简化 | 0.5h | < 1h |
| Phase 5 | E2E测试 + 文档 | 3h | 0.5天 |
| **总计** | | **18.5h** | **3天** |

---

## 11. 相关文档

- [CLAUDE.md - 项目规范](../../CLAUDE.md)
- [架构设计说明 - ADR-001](../../docs/development/架构重构完成报告.md)
- [API文档](../../docs/api_docs/新架构API指南.md)
- [现有批量仿真实现](../../frontend/control/js/batch_simulation.js)

---

**Review Status**: ✅ Approved
**Next Step**: Implementation (Phase 1 - Output Configuration Refactor)
