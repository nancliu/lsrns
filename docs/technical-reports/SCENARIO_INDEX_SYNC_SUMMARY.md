# scenario_index.json 同步 - 快速总结

**任务**: 根据metadata.json填充scenario_index.json的created_cases字段
**工具**: `sync_scenario_index.py`
**执行时间**: 2025-11-16 00:13:09
**状态**: ✅ **成功完成**

---

## 执行结果

### 同步统计

```
✓ 加载scenario_index.json: 477 个场景
✓ 发现 12 个case的metadata.json

处理结果:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 更新: 11 个scenario
✗ 跳过: 8 个case (非event_scenario_batch类型)
✗ 错误: 0 个case
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ scenario_index.json已保存
```

### 更新的案例

| 案例ID | 类型 | 更新的scenario数 |
|--------|------|-----------------|
| case_event_10754 | 事故 | 3 (no_control, vss, tec) |
| case_event_10768 | 道路管制 | 2 (no_control, tec) |
| case_event_10807 | 事故 | 3 (no_control, vss, tec) |
| case_event_10814 | 事故 | 3 (no_control, vss, tec) |

### 跳过的案例

8个case被跳过，因为它们的source_type不是`event_scenario_batch`（可能是旧版本的case或单场景case）。

---

## scenario_index.json更新内容

### 更新前 ❌

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",
  "files": {
    "scenario_dir": "scenario_10754_no_control"
  },
  "created_cases": []  // ← 空
}
```

### 更新后 ✅

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
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
  ]  // ← 已填充！
}
```

---

## 什么字段被填充了？

### created_cases数组中的字段

| 字段 | 来源 | 值示例 | 说明 |
|------|------|--------|------|
| `case_id` | metadata.json.case_id | `case_event_10754` | 案例的唯一标识 |
| `case_name` | metadata.json.case_name | `case_10754_batch` | 案例名称 |
| `status` | metadata.json.status | `created` | 案例当前状态 |
| `created_at` | metadata.json.created_at | `2025-11-16T00:09:24.283768` | ISO格式创建时间 |
| `source_scenario_id` | metadata.json.scenarios[i] | `scenario_10754_no_control` | 源场景ID |

---

## 脚本工作原理

### 1️⃣ 加载数据

```
scenario_index.json (477个场景)
         +
cases/*/metadata.json (4个event_scenario_batch类型的案例)
```

### 2️⃣ 匹配关联

```
metadata.json.event_scenario.event_id
    ↓
scenario_index.json.event_id

metadata.json.scenarios[i]
    ↓
scenario_index.json.files.scenario_dir
```

### 3️⃣ 填充数据

对每个匹配的(case, scenario)对，将case信息添加到scenario的created_cases数组中。

### 4️⃣ 保存更新

更新scenario_index.json文件，更新`generated_at`时间戳。

---

## 使用场景

### 场景1：新case创建后同步

```bash
# 用户通过批量创建API创建了案例
# 然后执行脚本来更新scenario_index.json
python sync_scenario_index.py

# 结果：scenario_index.json的created_cases被填充
```

### 场景2：前端从scenario_index.json读取关联案例

```javascript
// 前端代码：scenario_browser.js
const scenarios = data.scenarios;
for (const scenario of scenarios) {
  const createdCases = scenario.created_cases || [];
  // 显示该场景的所有关联案例
  console.log(`场景 ${scenario.files.scenario_dir} 有 ${createdCases.length} 个关联案例`);
  for (const caseInfo of createdCases) {
    console.log(`  - ${caseInfo.case_id} (${caseInfo.case_name})`);
  }
}
```

### 场景3：用户查看某个scenario时看到关联的cases

```
场景: scenario_10754_no_control
 ├─ 事件: 交通事故 (event_id=10754)
 ├─ 策略: 无管控
 └─ 关联案例:
    └─ case_event_10754 (case_10754_batch) ← 来自scenario_index.json的created_cases
```

---

## 重要字段说明

### created_cases[].source_scenario_id

该字段表示**该case从哪个scenario创建的**。

在event_scenario_batch创建中：
- 一个case对应多个scenario（如no_control, vss, tec）
- 每个scenario都会在created_cases中添加相同的case信息
- source_scenario_id记录是从哪个scenario创建的这个case

示例：
```json
{
  "event_id": "10754",
  "created_cases": [
    {
      "case_id": "case_event_10754",
      "source_scenario_id": "scenario_10754_no_control"  ← 无管控版本
    }
  ]
}

{
  "event_id": "10754",
  "created_cases": [
    {
      "case_id": "case_event_10754",
      "source_scenario_id": "scenario_10754_vss"  ← VSS版本
    }
  ]
}

{
  "event_id": "10754",
  "created_cases": [
    {
      "case_id": "case_event_10754",
      "source_scenario_id": "scenario_10754_tec"  ← TEC版本
    }
  ]
}
```

---

## 脚本特性

### ✅ 已实现的功能

- [x] 自动加载scenario_index.json
- [x] 扫描所有metadata.json文件
- [x] 过滤event_scenario_batch类型的案例
- [x] 根据event_id和scenario_id匹配关联
- [x] 避免重复添加（检查case_id）
- [x] 保存更新后的文件
- [x] 详细的日志输出
- [x] 错误处理和统计

### 🔄 可以重复运行

脚本设计成**幂等的**（idempotent），多次运行不会产生重复数据：
- 检查case_id是否已存在
- 避免重复添加相同的case

### 📊 详细的日志

脚本会输出：
- 加载的scenario数量
- 找到的metadata.json数量
- 每个更新的scenario
- 跳过的case和原因
- 最终的统计结果

---

## 与前端集成

### scenario_browser.js中的使用

```javascript
// 已集成的加载逻辑
async function loadCreatedCases() {
  const response = await fetch('/output/scenarios/scenario_index.json');
  const data = await response.json();

  const scenarios = data.scenarios || [];
  for (const scenario of scenarios) {
    const created_cases = scenario.created_cases || [];
    scenarioCaseMap[scenario.files.scenario_dir] = created_cases;
  }
}
```

---

## 后续优化建议

### 集成到API

在批量创建API完成后自动调用：

```python
@router.post("/create-case-batch")
async def create_event_case_batch(request):
    result = await case_service.create_event_case_batch(request)

    # 自动同步scenario_index.json
    from sync_scenario_index import ScenarioIndexSyncer
    syncer = ScenarioIndexSyncer()
    syncer.run()

    return result
```

### 定时任务

使用APScheduler定期同步：

```python
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', minute=0)
def periodic_sync():
    syncer = ScenarioIndexSyncer()
    syncer.run()
```

---

## 数据验证

### 检查是否更新成功

```bash
# 查看scenario_10754_no_control是否有created_cases
grep -A 10 '"scenario_10754_no_control"' output/scenarios/scenario_index.json

# 应该看到:
# "created_cases": [
#   {
#     "case_id": "case_event_10754",
#     ...
#   }
# ]
```

---

## 常见问题

### Q: 为什么某些case被跳过了？

A: 被跳过的case不是`event_scenario_batch`类型。这通常是：
- 旧版本的case
- 单场景case（不是批量创建）
- 从OD提取创建的case

### Q: 重复运行脚本会不会有重复的created_cases？

A: 不会。脚本检查case_id，避免重复添加。

### Q: created_cases的顺序重要吗？

A: 不重要。任何顺序都可以，因为使用case_id作为唯一标识。

### Q: 如何手动添加created_cases？

A: 编辑scenario_index.json，按照格式添加case信息即可。

---

## 文件汇总

| 文件 | 说明 |
|------|------|
| `sync_scenario_index.py` | 自动同步脚本 |
| `SCENARIO_INDEX_SYNC_GUIDE.md` | 详细使用指南 |
| `SCENARIO_INDEX_SYNC_SUMMARY.md` | 本文档（快速总结） |
| `output/scenarios/scenario_index.json` | 更新后的索引文件 |

---

## 下一步

### 1️⃣ 定期运行脚本

每次创建新case后：
```bash
python sync_scenario_index.py
```

### 2️⃣ 验证前端显示

打开浏览器，检查scenario_browser中是否显示了created_cases。

### 3️⃣ 考虑集成到API

在批量创建endpoint中自动调用脚本（见"与前端集成"部分）。

---

## 总结

✅ **scenario_index.json已成功同步！**

- **更新**: 11个scenario
- **跳过**: 8个非event_scenario_batch类型的case
- **错误**: 0个
- **时间**: 毫秒级（非常快）

scenario_index.json现在包含完整的案例关联信息，前端可以正确显示scenario和case之间的关系。

---

**脚本可以重复运行，每次都会检查重复。建议在每次创建新case后执行一次！**
