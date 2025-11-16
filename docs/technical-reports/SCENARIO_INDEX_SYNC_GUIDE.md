# scenario_index.json 同步指南

**概述**: 根据cases中的metadata.json自动更新scenario_index.json中的created_cases字段
**工具**: `sync_scenario_index.py` 脚本
**日期**: 2025-11-16
**状态**: ✅ 已实现

---

## scenario_index.json 字段说明

### 顶级字段

```json
{
  "generated_at": "2025-11-15 07:00:09",      // 生成/更新时间
  "total_scenarios": 477,                      // 场景总数
  "scenarios": [ ... ]                         // 场景数组
}
```

### scenarios 数组中的单个scenario对象

```json
{
  "event_id": "10754",                        // 事件ID
  "event_type": "交通事故",                    // 事件类型（中文显示）
  "strategy": "NO_CONTROL",                   // 管控策略 (NO_CONTROL|VSS|TEC|DHS)

  "location": {                               // 事件位置信息
    "road": "G5京昆高速（成雅段）",           // 道路名称
    "direction": "下行",                       // 方向
    "mileage": "K1834.3+000",                 // 里程
    "junction_id": "-55409",                  // 路口ID
    "edge_id": "-3734"                        // 道路边编号
  },

  "time": {                                   // 时间信息
    "start_time": "2025-06-10 10:43:48",     // 开始时间
    "end_time": "2025-06-10 11:14:50",       // 结束时间
    "duration_hours": 0.52                    // 持续时长（小时）
  },

  "files": {                                  // 场景文件信息
    "scenario_dir": "scenario_10754_no_control",  // 场景目录名
    "add_xml": "scenario_accident_event_10754.add.xml",  // 事件配置XML
    "event_description": "event_description.json",      // 事件描述
    "traffic_config": "traffic_input_config.json",      // 交通配置
    "control_config": "control_strategy_config.json"    // 控制策略配置
  },

  "created_cases": [                          // ✅ 从该场景创建的案例列表
    {
      "case_id": "case_event_10754",         // 案例ID
      "case_name": "case_10754_batch",       // 案例名称
      "status": "created",                    // 案例状态
      "created_at": "2025-11-16T00:09:24.283768",  // 创建时间
      "source_scenario_id": "scenario_10754_no_control"  // 源场景ID
    },
    // ... 可能有多个created_cases
  ]
}
```

---

## metadata.json 字段映射

### 从metadata.json到scenario_index.json的字段映射

| scenario_index.json字段 | 来源 | 说明 |
|------------------------|------|------|
| `created_cases[].case_id` | `metadata.json.case_id` | 案例ID |
| `created_cases[].case_name` | `metadata.json.case_name` | 案例名称 |
| `created_cases[].status` | `metadata.json.status` | 案例状态 |
| `created_cases[].created_at` | `metadata.json.created_at` | 创建时间 |
| `created_cases[].source_scenario_id` | `metadata.json.scenarios[i]` | 源场景ID（从metadata中的scenarios数组获取） |

### 匹配键

匹配metadata.json中的case到scenario_index.json中的scenario需要：
- `metadata.json.event_scenario.event_id` **=** `scenario_index.json.event_id`
- `metadata.json.scenarios[i]` **=** `scenario_index.json.files.scenario_dir`

---

## 使用脚本自动同步

### 第1步：运行脚本

```bash
cd D:\\projects\\OD_SIM
python sync_scenario_index.py
```

### 第2步：查看输出

脚本会输出类似的日志：

```
================================================================================
开始同步scenario_index.json...
================================================================================
✓ 加载scenario_index.json: 477 个场景
发现 3 个case的metadata.json

处理案例metadata.json:
--------------------------------------------------------------------------------
✓ 更新scenario: scenario_10754_no_control ← case_event_10754
✓ 更新scenario: scenario_10754_vss ← case_event_10754
✓ 更新scenario: scenario_10754_tec ← case_event_10754
✓ case case_event_10754: 更新 3 个scenario

================================================================================
✓ 同步完成！
  - 更新: 3 个scenario
  - 跳过: 0 个case
  - 错误: 0 个case
```

### 第3步：验证结果

```bash
# 查看更新后的scenario_index.json
# 应该能看到created_cases字段被填充了

# 示例：查看case_event_10754相关的场景
grep -A 20 "scenario_10754_no_control" output/scenarios/scenario_index.json
```

---

## 脚本功能详解

### 脚本做的事

1. **加载scenario_index.json** ✓
   - 读取`output/scenarios/scenario_index.json`

2. **扫描所有metadata.json** ✓
   - 遍历`cases/*/metadata.json`

3. **过滤event_scenario_batch类型** ✓
   - 只处理`source_type == "event_scenario_batch"`的case

4. **匹配scenario** ✓
   - 根据event_id和scenario_id匹配
   - 找到scenario_index.json中对应的scenario条目

5. **添加created_cases** ✓
   - 避免重复（检查case_id是否已存在）
   - 添加case_id, case_name, status, created_at, source_scenario_id

6. **保存结果** ✓
   - 更新`generated_at`时间戳
   - 保存更新后的scenario_index.json

### 脚本不会做的事

- ❌ **删除已有的created_cases** - 只添加新的
- ❌ **修改location, time, files字段** - 只更新created_cases
- ❌ **创建新的scenario** - 只更新已有的scenario
- ❌ **修改event_type为英文** - event_type保持原样

---

## 使用场景

### 场景1：批量创建后同步

```bash
# 1. 通过批量创建API创建多个案例（如case_event_10754, case_event_10755等）
# 2. 运行脚本更新scenario_index.json
python sync_scenario_index.py

# 结果：scenario_index.json中对应的场景的created_cases被填充
```

### 场景2：定期同步

```bash
# 在自动化脚本中定期运行
# 例如：每次新case创建后自动调用

# Python代码示例
from sync_scenario_index import ScenarioIndexSyncer
syncer = ScenarioIndexSyncer()
syncer.run()
```

### 场景3：手动修复

```bash
# 如果scenario_index.json的created_cases信息缺失或错误
# 可以运行脚本重新同步（自动去重）
python sync_scenario_index.py
```

---

## 数据一致性

### 同步前后的对比

**同步前** ❌:
```json
{
  "event_id": "10754",
  "strategy": "NO_CONTROL",
  "files": {
    "scenario_dir": "scenario_10754_no_control"
  },
  "created_cases": []  // ← 空
}
```

**同步后** ✅:
```json
{
  "event_id": "10754",
  "strategy": "NO_CONTROL",
  "files": {
    "scenario_dir": "scenario_10754_no_control"
  },
  "created_cases": [
    {
      "case_id": "case_event_10754",
      "case_name": "case_10754_batch",
      "status": "created",
      "created_at": "2025-11-16T00:09:24.283768",
      "source_scenario_id": "scenario_10754_no_control"
    }
  ]  // ← 填充了
}
```

---

## 与前端的交互

### 前端如何使用scenario_index.json

1. **显示scenario信息** - location, time, strategy等
2. **显示created_cases** - 该场景已创建的案例列表
3. **链接到case详情** - 点击case_id跳转到case页面

### 前端加载逻辑（scenario_browser.js）

```javascript
// 从scenario_index.json加载created_cases
const scenarios = data.scenarios || [];
for (const scenario of scenarios) {
  const created_cases = scenario.created_cases || [];
  scenarioCaseMap[scenario.files.scenario_dir] = created_cases.map(c => ({
    case_id: c.case_id,
    case_name: c.case_name,
    status: c.status,
    created_at: c.created_at,
    source_scenario: c.source_scenario_id
  }));
}
```

---

## 常见问题

### Q1: 为什么created_cases一开始是空的？

A: scenario_index.json是从scenario配置中生成的，doesn't know about cases yet。脚本的作用就是**填充**这个字段。

### Q2: 脚本可以重复运行吗？

A: 可以！脚本会检查case_id是否已存在，避免重复添加。

### Q3: 如果metadata.json中的scenarios列表有多个scenario呢？

A: 脚本会为每个scenario都添加同一个case信息到created_cases。例如case_event_10754会同时出现在scenario_10754_no_control, scenario_10754_vss, scenario_10754_tec的created_cases中。

### Q4: 为什么要保存source_scenario_id？

A: 用于追踪该case是从哪个scenario创建的。有助于数据溯源和管理。

### Q5: 脚本需要手动运行吗？

A: 目前是的。可以考虑在批量创建API完成后自动调用。

---

## 集成建议

### 集成点1：API响应后自动同步

在`api/routes/scenario_routes.py`的批量创建endpoint中：

```python
@router.post("/create-case-batch", response_model=EventCaseBatchCreationResponse)
async def create_event_case_batch(request: CreateEventCaseBatchRequest):
    result = await case_service.create_event_case_batch(request)

    # ✅ 添加：同步scenario_index.json
    from sync_scenario_index import ScenarioIndexSyncer
    syncer = ScenarioIndexSyncer()
    syncer.run()

    return EventCaseBatchCreationResponse(**result)
```

### 集成点2：定时任务

使用APScheduler定期同步：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from sync_scenario_index import ScenarioIndexSyncer

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', minute=0)  # 每小时运行一次
def sync_scenario_index():
    syncer = ScenarioIndexSyncer()
    syncer.run()

scheduler.start()
```

---

## 故障排除

### 脚本运行出错

```
❌ scenario_index.json不存在: output/scenarios/scenario_index.json
```

**解决**: 确保`output/scenarios/`目录存在且包含`scenario_index.json`

### 没有更新任何scenario

```
⚠️ case case_event_10754: 没有更新任何scenario
```

**可能原因**:
1. metadata.json中的scenario_id与scenario_index.json中的scenario_dir不匹配
2. event_id不匹配
3. case已经存在（避免重复）

**排查方法**:
```bash
# 检查metadata.json中的scenarios
grep -A 5 '"scenarios"' cases/case_event_10754/metadata.json

# 检查scenario_index.json中的scenario_dir
grep '"scenario_dir"' output/scenarios/scenario_index.json | head -10
```

### created_cases仍然为空

运行脚本后仍然为空，可能是：
1. 没有找到匹配的case
2. source_type不是event_scenario_batch
3. metadata.json格式不正确

---

## 手动编辑scenario_index.json

如果需要手动修改created_cases：

```json
{
  "event_id": "10754",
  "strategy": "NO_CONTROL",
  "created_cases": [
    {
      "case_id": "case_event_10754",
      "case_name": "case_10754_batch",
      "status": "created",
      "created_at": "2025-11-16T00:09:24.283768",
      "source_scenario_id": "scenario_10754_no_control"
    }
  ]
}
```

**必填字段**:
- ✅ `case_id` - 案例ID
- ✅ `case_name` - 案例名称
- ✅ `status` - 案例状态 (created|od_generating|od_failed等)
- ✅ `created_at` - ISO格式时间
- ✅ `source_scenario_id` - 源场景ID

---

## 总结

### 什么是scenario_index.json

它是场景元数据的**索引文件**，包含所有预定义场景的信息。

### created_cases字段的作用

记录从该场景创建的所有案例，形成**scenario ↔ case的关联关系**。

### sync_scenario_index.py脚本的作用

**自动填充**created_cases字段，**保证索引信息同步**。

---

## 使用流程总结

```
1. 通过API批量创建事件案例
   ↓
2. 运行: python sync_scenario_index.py
   ↓
3. scenario_index.json自动更新
   ↓
4. 前端从scenario_index.json读取created_cases
   ↓
5. 用户在UI中看到该场景的所有关联案例
```

---

**相关文件**:
- `sync_scenario_index.py` - 自动同步脚本
- `output/scenarios/scenario_index.json` - 场景索引文件
- `cases/*/metadata.json` - 案例元数据

**下一步**: 执行脚本同步已有的所有案例！

```bash
python sync_scenario_index.py
```
