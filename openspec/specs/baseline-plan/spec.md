# baseline-plan Specification

## Purpose
TBD - created by archiving change implement-plan-management-and-batch-optimization. Update Purpose after archive.
## Requirements
### Requirement: 系统自动创建全局基准方案

系统在首次启动或检测到基准方案不存在时，MUST自动创建全局基准方案（plan_id为"baseline_plan"），包含完整的元数据、空策略列表和空XML配置文件。该操作具有幂等性，重复调用不会出错。

**优先级**: P0
**状态**: 新增

#### Scenario: 系统首次启动时创建基准方案

**Given**:
- 系统首次启动或全新安装
- control_data/plans/目录为空或不存在baseline_plan

**When**:
- FastAPI应用启动
- 触发startup事件
- 调用ensure_baseline_plan_exists()

**Then**:
- 系统创建目录：control_data/plans/baseline_plan/
- 系统创建plan_metadata.json，内容包含：
  ```json
  {
    "plan_id": "baseline_plan",
    "plan_name": "基准方案（无管控）",
    "description": "无任何管控措施的基准方案，用于对比评估管控效果",
    "strategy_ids": [],
    "tags": ["基准", "无管控"],
    "target_scenario": "所有场景",
    "expected_effects": {
      "baseline": "提供基准数据用于对比"
    },
    "additional_file_path": "control_data/plans/baseline_plan/control.add.xml",
    "created_at": "...",
    "updated_at": "..."
  }
  ```
- 系统创建strategy_refs.json，内容为空数组：[]
- 系统创建control.add.xml，内容为：
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <additional>
      <!-- 基准方案：无管控 -->
  </additional>
  ```
- 系统记录日志："全局基准方案创建成功"

---

#### Scenario: 系统重复启动时跳过创建

**Given**:
- 系统已启动过一次
- baseline_plan目录已存在

**When**:
- FastAPI应用再次启动
- 调用ensure_baseline_plan_exists()

**Then**:
- 系统检测到baseline_plan已存在
- 跳过创建逻辑
- 立即返回
- 无额外日志或操作

---

### Requirement: 基准方案作为全局单例可跨案例复用

基准方案MUST作为全局唯一的单例存在，可被所有case的批量仿真引用。不同case的批量仿真复制相同的baseline_plan配置文件到各自的仿真目录，但共享同一个方案定义。

**优先级**: P0
**状态**: 新增

#### Scenario: 在批量仿真中引用基准方案

**Given**:
- 全局基准方案baseline_plan已存在
- Case case_001和case_002都需要运行批量仿真

**When**:
- 用户为case_001创建批次，包含baseline_plan
- 用户为case_002创建批次，也包含baseline_plan

**Then**:
- 两个批次都引用相同的baseline_plan
- baseline_plan的control.add.xml被复制到：
  - cases/case_001/simulations/plan_opti/{batch_id_1}/baseline_plan/sim_66/
  - cases/case_002/simulations/plan_opti/{batch_id_2}/baseline_plan/sim_66/
- 基准方案本身不变，可跨案例复用

---

### Requirement: 基准方案受删除保护

系统MUST禁止删除基准方案，因为它是系统必需的参照标准。当用户尝试删除baseline_plan时，系统返回错误并拒绝操作，保持基准方案完整性。

**优先级**: P0
**状态**: 新增

#### Scenario: 禁止删除基准方案

**Given**:
- 基准方案baseline_plan存在

**When**:
- 用户发送DELETE /api/v1/control/plans/baseline_plan

**Then**:
- 系统检测到plan_id为"baseline_plan"
- 系统拒绝删除请求
- 返回400响应：
  ```json
  {
    "error": "无法删除基准方案",
    "message": "基准方案是系统必需的，用于对比评估管控效果",
    "plan_id": "baseline_plan"
  }
  ```
- baseline_plan目录和文件保持不变

---

### Requirement: 基准方案在方案列表中明确标识

方案列表和详情页面MUST明确标识基准方案，通过is_baseline标志、特殊图标或样式区分。前端禁用或隐藏基准方案的删除按钮，并显示"系统方案"标签。

**优先级**: P1
**状态**: 新增

#### Scenario: 方案列表中显示基准方案

**Given**:
- 系统包含基准方案和其他方案

**When**:
- 用户访问GET /api/v1/control/plans/

**Then**:
- 返回的方案列表包含baseline_plan
- baseline_plan的is_baseline字段为true
- 其他方案的is_baseline字段为false
- 前端显示时：
  - 基准方案使用特殊图标或样式
  - 删除按钮禁用或隐藏
  - 显示"系统方案"标签

---

### Requirement: 批量仿真自动包含基准方案

系统在创建批量仿真批次时，MUST自动检查并添加基准方案到方案列表中（如用户未手动选择）。这确保每次批量对比都包含无管控基准，便于量化管控措施的实际效果。

**优先级**: P1
**状态**: 新增

#### Scenario: 创建批次时自动添加基准方案

**Given**:
- 用户创建批量仿真
- 用户选择了plan_001和plan_002

**When**:
- 用户发送POST /batch请求
- plan_ids为["plan_001", "plan_002"]（未包含baseline_plan）

**Then**:
- 系统自动添加baseline_plan到plan_ids列表
- 实际批次包含：["baseline_plan", "plan_001", "plan_002"]
- 返回响应包含3个方案
- 或返回警告："已自动添加基准方案"

---

#### Scenario: 用户手动包含基准方案

**Given**:
- 用户创建批量仿真
- 用户明确选择了baseline_plan

**When**:
- 用户发送POST /batch请求
- plan_ids为["baseline_plan", "plan_001"]

**Then**:
- 系统保持plan_ids不变
- 不重复添加baseline_plan
- 批次正常创建

---

### Requirement: 基准方案不可编辑关键属性

系统MUST禁止修改基准方案的关键属性（特别是strategy_ids，必须保持为空数组）。允许更新非关键字段如描述和标签，但拒绝任何试图添加策略的更新请求，确保基准方案始终表示无管控状态。

**优先级**: P1
**状态**: 新增

#### Scenario: 禁止修改基准方案的策略列表

**Given**:
- 基准方案baseline_plan存在

**When**:
- 用户发送PUT /api/v1/control/plans/baseline_plan
- 请求体包含strategy_ids非空数组

**Then**:
- 系统拒绝更新
- 返回400响应："基准方案的strategy_ids必须为空"
- baseline_plan保持strategy_ids=[]

---

#### Scenario: 允许更新基准方案的描述和标签

**Given**:
- 基准方案存在

**When**:
- 用户发送PUT /baseline_plan
- 仅更新description或tags字段

**Then**:
- 系统允许更新非关键字段
- 更新plan_metadata.json
- strategy_ids保持为空数组
- 返回200响应

---

