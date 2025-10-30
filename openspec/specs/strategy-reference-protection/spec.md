# strategy-reference-protection Specification

## Purpose
TBD - created by archiving change implement-plan-management-and-batch-optimization. Update Purpose after archive.
## Requirements
### Requirement: 系统跟踪策略被哪些方案引用

系统MUST在策略元数据中维护referenced_by字段，记录所有引用该策略的方案ID列表。当方案创建或更新时，系统MUST自动增加或减少相应策略的引用计数，确保引用关系准确跟踪。

**优先级**: P0
**状态**: 新增

#### Scenario: 创建方案时增加策略引用计数

**Given**:
- 策略strategy_001存在
- 策略元数据中referenced_by为空数组[]

**When**:
- 用户创建方案plan_001，包含strategy_001
- 调用increment_strategy_reference("strategy_001", "plan_001")

**Then**:
- 系统读取strategy_001的元数据
- 在referenced_by数组中添加"plan_001"
- 保存更新后的元数据：
  ```json
  {
    "strategy_id": "strategy_001",
    ...
    "referenced_by": ["plan_001"]
  }
  ```
- 返回成功

---

#### Scenario: 多个方案引用同一策略

**Given**:
- 策略strategy_001已被plan_001引用

**When**:
- 用户创建plan_002，也包含strategy_001
- 调用increment_strategy_reference("strategy_001", "plan_002")

**Then**:
- referenced_by数组包含2个方案ID：
  ```json
  {"referenced_by": ["plan_001", "plan_002"]}
  ```

---

#### Scenario: 防止重复添加引用

**Given**:
- 策略strategy_001已被plan_001引用

**When**:
- 系统再次调用increment_strategy_reference("strategy_001", "plan_001")

**Then**:
- 系统检测到plan_001已在referenced_by中
- 跳过添加
- referenced_by保持不变：["plan_001"]

---

### Requirement: 删除方案时减少策略引用计数

当方案MUST被删除时，系统MUST自动从所有引用的策略的referenced_by列表中移除该方案ID。当策略的referenced_by变为空时，该策略可以被安全删除。

**优先级**: P0
**状态**: 新增

#### Scenario: 删除方案时移除策略引用

**Given**:
- 策略strategy_001的referenced_by为["plan_001", "plan_002"]
- 用户删除方案plan_001

**When**:
- 系统调用decrement_strategy_reference("strategy_001", "plan_001")

**Then**:
- 系统从referenced_by数组中移除"plan_001"
- 保存更新后的元数据：
  ```json
  {"referenced_by": ["plan_002"]}
  ```

---

#### Scenario: 删除最后一个引用方案

**Given**:
- 策略strategy_001仅被plan_001引用

**When**:
- 用户删除plan_001
- 调用decrement_strategy_reference("strategy_001", "plan_001")

**Then**:
- referenced_by数组变为空：[]
- 策略可以被删除

---

### Requirement: 禁止删除被引用的策略

系统MUST在删除策略前检查其referenced_by列表。如果列表非空，拒绝删除操作并返回错误，列出所有引用该策略的方案。只有当referenced_by为空时才允许删除策略。

**优先级**: P0
**状态**: 新增

#### Scenario: 尝试删除被方案引用的策略

**Given**:
- 策略strategy_001被plan_001和plan_002引用
- referenced_by为["plan_001", "plan_002"]

**When**:
- 用户发送DELETE /api/v1/control/strategies/strategy_001

**Then**:
- 系统调用can_delete_strategy("strategy_001")
- 返回(False, ["plan_001", "plan_002"])
- 系统拒绝删除
- 返回400响应：
  ```json
  {
    "error": "无法删除策略",
    "message": "策略 strategy_001 被以下方案引用: plan_001, plan_002",
    "strategy_id": "strategy_001",
    "referenced_by": ["plan_001", "plan_002"]
  }
  ```
- 策略文件保持不变

---

#### Scenario: 删除未被引用的策略

**Given**:
- 策略strategy_002的referenced_by为空数组[]

**When**:
- 用户发送DELETE /api/v1/control/strategies/strategy_002

**Then**:
- can_delete_strategy返回(True, [])
- 系统允许删除
- 删除策略文件和目录
- 返回204响应

---

### Requirement: 更新方案策略列表时调整引用计数

当方案MUST的strategy_ids更新时（添加、删除或替换策略），系统MUST自动调整所有相关策略的引用计数。新增的策略增加引用，移除的策略减少引用，确保referenced_by准确反映当前引用关系。

**优先级**: P0
**状态**: 新增

#### Scenario: 更新方案添加新策略

**Given**:
- 方案plan_001当前包含["strategy_001"]
- 策略strategy_002未被引用

**When**:
- 用户更新plan_001的strategy_ids为["strategy_001", "strategy_002"]

**Then**:
- 系统调用increment_strategy_reference("strategy_002", "plan_001")
- strategy_002的referenced_by包含"plan_001"
- strategy_001的referenced_by保持不变

---

#### Scenario: 更新方案移除策略

**Given**:
- 方案plan_001当前包含["strategy_001", "strategy_002"]

**When**:
- 用户更新plan_001的strategy_ids为["strategy_001"]

**Then**:
- 系统调用decrement_strategy_reference("strategy_002", "plan_001")
- strategy_002的referenced_by中移除"plan_001"
- strategy_001的referenced_by保持不变

---

#### Scenario: 更新方案完全替换策略列表

**Given**:
- 方案plan_001当前包含["strategy_001", "strategy_002"]

**When**:
- 用户更新plan_001的strategy_ids为["strategy_003", "strategy_004"]

**Then**:
- 系统减少strategy_001和strategy_002的引用
- 系统增加strategy_003和strategy_004的引用
- 引用计数正确更新

---

### Requirement: 策略更新时自动重新生成引用方案的XML

当策略配置更新时，系统MUST读取该策略的referenced_by列表，异步地为所有引用方案重新生成control.add.xml文件。即使部分方案重新生成失败，策略更新本身仍应成功，并记录详细的传播日志。

**优先级**: P0
**状态**: 新增

#### Scenario: 更新策略后传播到所有引用方案

**Given**:
- 策略strategy_001被plan_001和plan_002引用
- strategy_001的referenced_by为["plan_001", "plan_002"]

**When**:
- 用户发送PUT /api/v1/control/strategies/strategy_001
- 更新策略参数（如修改限速值）

**Then**:
- 系统更新strategy_001的配置
- 系统读取referenced_by列表：["plan_001", "plan_002"]
- 系统异步重新生成plan_001的control.add.xml
- 系统异步重新生成plan_002的control.add.xml
- 返回响应包含传播信息：
  ```json
  {
    "updated": true,
    "strategy_id": "strategy_001",
    "propagated_to_plans": ["plan_001", "plan_002"],
    "propagation_count": 2
  }
  ```
- 记录日志："重新生成方案 plan_001 的XML"
- 记录日志："重新生成方案 plan_002 的XML"

---

#### Scenario: 重新生成失败不影响策略更新

**Given**:
- 策略strategy_001被plan_001和plan_002引用
- plan_002的某个策略文件损坏

**When**:
- 用户更新strategy_001
- plan_002的XML重新生成失败

**Then**:
- strategy_001成功更新
- plan_001的XML成功重新生成
- plan_002的XML重新生成失败，记录错误日志
- 返回响应仍显示成功：
  ```json
  {
    "updated": true,
    "propagation_count": 2,
    "errors": [
      {
        "plan_id": "plan_002",
        "error": "重新生成失败: 策略文件损坏"
      }
    ]
  }
  ```

---

### Requirement: 兼容现有策略文件

系统MUST兼容旧版策略文件（元数据中没有referenced_by字段）。读取旧版文件时自动添加referenced_by=[]字段，可选择性地持久化更新或仅在内存中添加，确保向后兼容性。

**优先级**: P1
**状态**: 新增

#### Scenario: 读取旧版策略文件自动添加referenced_by字段

**Given**:
- 存在旧版策略文件，元数据中没有referenced_by字段

**When**:
- 系统读取该策略的元数据
- 调用load_strategy_metadata()

**Then**:
- 系统检测到缺少referenced_by字段
- 自动添加referenced_by=[]
- 更新元数据文件（可选，或仅在内存中）
- 返回包含referenced_by的完整元数据

---

### Requirement: 前端显示策略引用状态

前端策略列表和详情页面MUST显示策略的引用状态，包括引用计数徽章、引用方案列表（可点击跳转）。被引用的策略MUST禁用或变灰删除按钮，并提供明确的提示信息。

**优先级**: P2
**状态**: 新增

#### Scenario: 策略列表显示引用计数

**Given**:
- 策略strategy_001被2个方案引用

**When**:
- 用户访问策略管理页面

**Then**:
- 策略列表显示strategy_001
- 显示"被2个方案引用"徽章或提示
- 删除按钮禁用或变灰
- 鼠标悬停显示引用方案列表

---

#### Scenario: 策略详情页显示引用方案

**Given**:
- 策略strategy_001被plan_001和plan_002引用

**When**:
- 用户查看strategy_001详情

**Then**:
- 详情页显示"引用此策略的方案"部分
- 列出plan_001和plan_002（可点击跳转）
- 提示："删除此策略前需先从所有方案中移除"

---

