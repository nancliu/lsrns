# scenario_index.json 快速入门

**目标**: 根据metadata.json自动填充scenario_index.json的created_cases字段
**时间**: 5分钟
**工具**: Python脚本

---

## ⚡ 30秒快速开始

```bash
# 1. 进入项目目录
cd D:\\projects\\OD_SIM

# 2. 运行脚本
python sync_scenario_index.py

# 3. 完成！scenario_index.json已更新
```

---

## 📋 scenario_index.json包含什么

### 预定义场景信息

每个scenario都有：
- `event_id` - 事件ID
- `event_type` - 事件类型
- `strategy` - 管控策略（NO_CONTROL, VSS, TEC, DHS）
- `location` - 位置信息（道路、路口、边等）
- `time` - 时间信息
- `files` - 相关文件路径

### created_cases（需要填充的部分）

从该scenario创建的案例列表：

```json
"created_cases": [
  {
    "case_id": "case_event_10754",
    "case_name": "case_10754_batch",
    "status": "created",
    "created_at": "2025-11-16T00:09:24.283768",
    "source_scenario_id": "scenario_10754_no_control"
  }
]
```

---

## 🔄 数据流向

```
批量创建API调用
        ↓
生成 metadata.json
        ↓
包含:
  - case_id: "case_event_10754"
  - scenarios: ["scenario_10754_no_control", "scenario_10754_vss", "scenario_10754_tec"]
  - event_id: "10754"
        ↓
运行: python sync_scenario_index.py
        ↓
脚本匹配:
  - 找到scenario_index.json中event_id="10754"的所有scenarios
  - 找到files.scenario_dir相符的条目
  - 添加case信息到created_cases
        ↓
更新 scenario_index.json
        ↓
前端从scenario_index.json读取关联案例
        ↓
用户在UI中看到该scenario的created_cases列表
```

---

## ✅ scenario_index.json需要填写的字段

### 从metadata.json自动提取

| 字段 | 来源 |
|------|------|
| `case_id` | metadata.json.case_id |
| `case_name` | metadata.json.case_name |
| `status` | metadata.json.status |
| `created_at` | metadata.json.created_at |
| `source_scenario_id` | metadata.json.scenarios[i] |

### 自动生成的字段

| 字段 | 说明 |
|------|------|
| `generated_at` | 更新时间戳 |

### 已有的字段（不修改）

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",
  "location": { ... },
  "time": { ... },
  "files": { ... }
}
```

---

## 📊 执行结果示例

```
================================================================================
开始同步scenario_index.json...
================================================================================
✓ 加载scenario_index.json: 477 个场景
发现 12 个case的metadata.json

处理案例metadata.json:
────────────────────────────────────────────────────────────────────────────────
✓ 更新scenario: scenario_10754_no_control ← case_event_10754
✓ 更新scenario: scenario_10754_vss ← case_event_10754
✓ 更新scenario: scenario_10754_tec ← case_event_10754
✓ case case_event_10754: 更新 3 个scenario

✓ 更新scenario: scenario_10768_no_control ← case_event_10768
✓ 更新scenario: scenario_10768_tec ← case_event_10768
✓ case case_event_10768: 更新 2 个scenario

✓ 更新scenario: scenario_10807_no_control ← case_event_10807
✓ 更新scenario: scenario_10807_vss ← case_event_10807
✓ 更新scenario: scenario_10807_tec ← case_event_10807
✓ case case_event_10807: 更新 3 个scenario

✓ 更新scenario: scenario_10814_no_control ← case_event_10814
✓ 更新scenario: scenario_10814_vss ← case_event_10814
✓ 更新scenario: scenario_10814_tec ← case_event_10814
✓ case case_event_10814: 更新 3 个scenario

================================================================================
✓ scenario_index.json已保存
✓ 同步完成！
  - 更新: 11 个scenario
  - 跳过: 8 个case (非event_scenario_batch类型)
  - 错误: 0 个case
```

---

## 🔍 验证更新是否成功

### 方法1：查看logs中的"更新"信息

脚本会输出每个更新的scenario，确认是否有你要找的case。

### 方法2：查看scenario_index.json文件

```bash
# Windows: 用记事本或JSON编辑器打开
code output/scenarios/scenario_index.json

# 或用命令查看
grep -A 10 "case_event_10754" output/scenarios/scenario_index.json
```

应该看到：
```json
"created_cases": [
  {
    "case_id": "case_event_10754",
    "case_name": "case_10754_batch",
    "status": "created",
    "created_at": "2025-11-16T00:09:24.283768",
    "source_scenario_id": "scenario_10754_no_control"
  }
]
```

### 方法3：在浏览器中验证

打开 http://localhost:8000/output/scenarios/scenario_index.json
搜索 "case_event" 看是否有created_cases被填充。

---

## 🎯 什么时候运行脚本

### 必须运行

✅ 创建新case后（批量创建API返回后）
✅ 添加/修改metadata.json后
✅ 定期同步（每天一次）

### 不需要运行

❌ 修改scenario_index.json的其他字段
❌ 删除case时（脚本只添加，不删除）

---

## ⚙️ 脚本特性

### ✅ 优点

- 自动化 - 一键运行
- 安全 - 检查重复，避免覆盖
- 快速 - 毫秒级执行
- 可复用 - 可以重复运行
- 详细 - 输出完整日志

### 🔄 幂等性

脚本是**幂等的**，多次运行不会产生重复数据：
- 检查case_id是否已存在
- 跳过已有的case

### 📊 不修改的字段

脚本只更新：
- ✅ `generated_at` (时间戳)
- ✅ `created_cases` (添加新case)

脚本**不修改**：
- ❌ `event_id`, `event_type`, `strategy`
- ❌ `location`, `time`, `files`
- ❌ 其他scenario的数据

---

## 常见问题

### Q1: 脚本出错了怎么办？

```
❌ scenario_index.json不存在: output/scenarios/scenario_index.json
```

**解决**: 确保 `output/scenarios/` 目录存在。

### Q2: 为什么某些case被跳过？

```
⊘ case_20251016_113040: 非event_scenario_batch类型，跳过
```

**答**: 这些case不是通过批量创建API创建的，是其他类型的case。

### Q3: 重复运行脚本安全吗？

**答**: 完全安全！脚本检查重复，避免添加相同的case。

### Q4: created_cases为什么还是空的？

**可能原因**:
1. 没有event_scenario_batch类型的case
2. case的event_id与scenario的event_id不匹配
3. case的scenarios列表中的scenario_id与scenario_index.json中的scenario_dir不匹配

**排查**:
```bash
# 查看metadata.json中的event_id和scenarios
grep -A 5 '"event_scenario"' cases/case_event_10754/metadata.json
grep -A 5 '"scenarios"' cases/case_event_10754/metadata.json

# 查看scenario_index.json中的event_id和scenario_dir
grep '"event_id": "10754"' output/scenarios/scenario_index.json
grep '"scenario_10754' output/scenarios/scenario_index.json
```

### Q5: 前端如何使用created_cases？

```javascript
// scenario_browser.js 已集成了加载逻辑
const scenarios = await fetch('/output/scenarios/scenario_index.json');
for (const scenario of scenarios) {
  const cases = scenario.created_cases;  // 自动加载！
}
```

---

## 🚀 集成到API（可选）

如果想在创建case后自动同步，可以修改批量创建endpoint：

```python
# api/routes/scenario_routes.py
@router.post("/create-case-batch")
async def create_event_case_batch(request):
    result = await case_service.create_event_case_batch(request)

    # 自动同步scenario_index.json
    from sync_scenario_index import ScenarioIndexSyncer
    syncer = ScenarioIndexSyncer()
    syncer.run()

    return result
```

---

## 📚 更多信息

| 文档 | 用途 |
|------|------|
| `SCENARIO_INDEX_SYNC_GUIDE.md` | 详细使用指南 |
| `SCENARIO_INDEX_FIELDS_REFERENCE.md` | 字段详细说明 |
| `SCENARIO_INDEX_SYNC_SUMMARY.md` | 本次执行结果 |

---

## ✨ 总结

### 做什么

根据cases目录中的metadata.json，自动填充scenario_index.json中每个scenario的created_cases字段。

### 怎么做

运行一个Python脚本，自动扫描、匹配、填充。

### 为什么

这样前端就能知道每个scenario创建了哪些case，用户能看到完整的scenario↔case关联关系。

---

## 🎬 立即开始

```bash
# 进入项目目录
cd D:\\projects\\OD_SIM

# 运行脚本（只需一行命令！）
python sync_scenario_index.py

# 完成！✅
```

---

**现在scenario_index.json已经完全填充了！** 🎉
