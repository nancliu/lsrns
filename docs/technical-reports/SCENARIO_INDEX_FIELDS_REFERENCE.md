# scenario_index.json 字段参考卡片

**快速参考**: scenario_index.json中需要填写的所有字段说明

---

## scenario_index.json 完整结构

```json
{
  "generated_at": "2025-11-16 00:13:09",        // ⏰ 生成/更新时间
  "total_scenarios": 477,                        // 📊 场景总数
  "scenarios": [
    {
      // ========== 事件信息 ==========
      "event_id": "10754",                      // 🔑 事件ID
      "event_type": "交通事故",                  // 📝 事件类型（中文）

      // ========== 策略信息 ==========
      "strategy": "NO_CONTROL",                 // 🎯 管控策略

      // ========== 位置信息 ==========
      "location": {
        "road": "G5京昆高速（成雅段）",         // 🛣️ 道路名称
        "direction": "下行",                     // ↔️ 方向
        "mileage": "K1834.3+000",               // 📍 里程
        "junction_id": "-55409",                // 🔗 路口ID
        "edge_id": "-3734"                      // 🌐 边ID
      },

      // ========== 时间信息 ==========
      "time": {
        "start_time": "2025-06-10 10:43:48",   // ⏱️ 开始时间
        "end_time": "2025-06-10 11:14:50",     // ⏱️ 结束时间
        "duration_hours": 0.52                  // ⏳ 持续时长
      },

      // ========== 文件信息 ==========
      "files": {
        "scenario_dir": "scenario_10754_no_control",         // 📁 场景目录
        "add_xml": "scenario_accident_event_10754.add.xml",  // 📄 事件XML
        "event_description": "event_description.json",        // 📄 事件描述
        "traffic_config": "traffic_input_config.json",       // 📄 交通配置
        "control_config": "control_strategy_config.json"     // 📄 控制配置
      },

      // ========== 案例关联 (自动填充) ==========
      "created_cases": [
        {
          "case_id": "case_event_10754",                      // 案例ID
          "case_name": "case_10754_batch",                    // 案例名称
          "status": "created",                                // 状态
          "created_at": "2025-11-16T00:09:24.283768",       // 创建时间
          "source_scenario_id": "scenario_10754_no_control"   // 源场景
        }
      ]
    }
    // ... 更多场景
  ]
}
```

---

## 字段对应表

### 必填字段 ✅

| scenario_index.json | 数据类型 | 来源 | 说明 |
|-------------------|---------|------|------|
| `event_id` | string | scenario配置 | 事件唯一标识 |
| `event_type` | string | scenario配置 | 事件类型（中文） |
| `strategy` | string | scenario配置 | NO_CONTROL \| VSS \| TEC \| DHS |
| `location.road` | string | scenario配置 | 道路名称 |
| `location.junction_id` | string | scenario配置 | SUMO路网中的路口ID |
| `location.edge_id` | string | scenario配置 | SUMO路网中的边ID |
| `time.start_time` | string | scenario配置 | YYYY-MM-DD HH:MM:SS |
| `time.end_time` | string | scenario配置 | YYYY-MM-DD HH:MM:SS |
| `time.duration_hours` | number | 计算 | (end_time - start_time).hours |
| `files.scenario_dir` | string | scenario配置 | 场景目录名 |

### 自动填充字段 (sync_scenario_index.py) 🤖

| created_cases字段 | 数据类型 | 来源 | 说明 |
|-----------------|---------|------|------|
| `case_id` | string | metadata.json.case_id | 案例ID |
| `case_name` | string | metadata.json.case_name | 案例名称 |
| `status` | string | metadata.json.status | 案例状态 |
| `created_at` | string | metadata.json.created_at | ISO格式时间 |
| `source_scenario_id` | string | metadata.json.scenarios[i] | 源scenario_dir |

### 其他字段 📌

| 字段 | 说明 |
|------|------|
| `generated_at` | 脚本自动更新为当前时间 |
| `total_scenarios` | 场景总数（脚本不修改） |
| `location.direction` | 方向信息（可选） |
| `location.mileage` | 里程信息（可选） |
| `files.add_xml` | 事件配置XML路径 |
| `files.event_description` | 事件描述JSON路径 |
| `files.traffic_config` | 交通配置JSON路径 |
| `files.control_config` | 控制策略配置JSON路径 |

---

## 数据流向图

### 从metadata.json到scenario_index.json

```
metadata.json (case)
    ├─ case_id ────────────→ created_cases[].case_id
    ├─ case_name ──────────→ created_cases[].case_name
    ├─ status ─────────────→ created_cases[].status
    ├─ created_at ─────────→ created_cases[].created_at
    └─ scenarios[i] ───────→ created_cases[].source_scenario_id

scenario_index.json (scenario)
    ├─ event_id ◀──── metadata.json.event_scenario.event_id (用于匹配)
    ├─ files.scenario_dir ◀──── metadata.json.scenarios[i] (用于匹配)
    └─ created_cases[] ◀──── metadata.json (填充)
```

---

## 匹配规则

### 如何找到对应的scenario

脚本使用两个关键进行匹配：

1. **event_id 匹配**
   ```python
   metadata.json.event_scenario.event_id == scenario_index.json.event_id
   ```

2. **scenario_id 匹配**
   ```python
   metadata.json.scenarios[i] == scenario_index.json.files.scenario_dir
   ```

### 匹配示例

**metadata.json**:
```json
{
  "case_id": "case_event_10754",
  "event_scenario": {"event_id": "10754"},
  "scenarios": ["scenario_10754_no_control", "scenario_10754_vss", "scenario_10754_tec"]
}
```

**scenario_index.json中找到的三个matching entries**:
```json
{
  "event_id": "10754",  // ✓ 匹配
  "files": {"scenario_dir": "scenario_10754_no_control"}  // ✓ 匹配
},
{
  "event_id": "10754",  // ✓ 匹配
  "files": {"scenario_dir": "scenario_10754_vss"}  // ✓ 匹配
},
{
  "event_id": "10754",  // ✓ 匹配
  "files": {"scenario_dir": "scenario_10754_tec"}  // ✓ 匹配
}
```

**结果**: case_event_10754被添加到这三个scenario的created_cases中

---

## 字段验证规则

### case必须满足

```python
if metadata.get('source_type') != 'event_scenario_batch':
    skip()  # 跳过

if not metadata.get('case_id'):
    skip()  # 缺少case_id

if not metadata.get('scenarios'):
    skip()  # 缺少scenarios列表

if not metadata.get('event_scenario', {}).get('event_id'):
    skip()  # 缺少event_id
```

### case_id去重

```python
created_cases = scenario_entry.get('created_cases', [])
for existing in created_cases:
    if existing['case_id'] == new_case['case_id']:
        skip()  # 避免重复
```

---

## 字段值示例

### event_type (事件类型)

```
"交通事故"           # 01_accident
"道路管制"           # 03_road_control
"交通事件"           # 02_traffic_incident
"其他"              # others
```

### strategy (管控策略)

```
"NO_CONTROL"        # 无管控
"VSS"               # 可变限速
"TEC"               # 收费站管制
"DHS"               # 动态硬路肩
```

### status (案例状态)

```
"created"           # 创建完成
"od_generating"     # OD生成中
"od_failed"         # OD生成失败
"simulating"        # 仿真运行中
"completed"         # 完成
```

### time格式

```
"2025-06-10 10:43:48"    # YYYY-MM-DD HH:MM:SS
"2025-11-16T00:09:24"    # ISO格式 (在created_at中)
```

---

## 实际使用例子

### 例1：查询某个scenario的created_cases

```python
def get_created_cases(scenario_index, event_id, scenario_dir):
    """获取scenario的created_cases"""
    for scenario in scenario_index['scenarios']:
        if (scenario['event_id'] == event_id and
            scenario['files']['scenario_dir'] == scenario_dir):
            return scenario.get('created_cases', [])
    return []

# 使用
cases = get_created_cases(index, '10754', 'scenario_10754_no_control')
# 返回: [{'case_id': 'case_event_10754', ...}]
```

### 例2：找到case关联的所有scenarios

```python
def find_scenarios_for_case(scenario_index, case_id):
    """找到包含该case的所有scenario"""
    scenarios = []
    for scenario in scenario_index['scenarios']:
        for case_info in scenario.get('created_cases', []):
            if case_info['case_id'] == case_id:
                scenarios.append({
                    'event_id': scenario['event_id'],
                    'scenario_dir': scenario['files']['scenario_dir'],
                    'strategy': scenario['strategy']
                })
    return scenarios

# 使用
scenarios = find_scenarios_for_case(index, 'case_event_10754')
# 返回: [
#   {'event_id': '10754', 'scenario_dir': 'scenario_10754_no_control', 'strategy': 'NO_CONTROL'},
#   {'event_id': '10754', 'scenario_dir': 'scenario_10754_vss', 'strategy': 'VSS'},
#   {'event_id': '10754', 'scenario_dir': 'scenario_10754_tec', 'strategy': 'TEC'}
# ]
```

---

## 手动编辑示例

如果需要手动添加created_cases：

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",
  "location": {
    "road": "G5京昆高速（成雅段）",
    "direction": "下行",
    "mileage": "K1834.3+000",
    "junction_id": "-55409",
    "edge_id": "-3734"
  },
  "time": {
    "start_time": "2025-06-10 10:43:48",
    "end_time": "2025-06-10 11:14:50",
    "duration_hours": 0.52
  },
  "files": {
    "scenario_dir": "scenario_10754_no_control",
    "add_xml": "scenario_accident_event_10754.add.xml",
    "event_description": "event_description.json",
    "traffic_config": "traffic_input_config.json",
    "control_config": "control_strategy_config.json"
  },
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

---

## 常见错误

### ❌ 错误1：case_id重复

```json
"created_cases": [
  {"case_id": "case_event_10754", ...},
  {"case_id": "case_event_10754", ...}  // ❌ 重复！
]
```

✅ **修正**: 脚本会自动避免，手动编辑时要检查。

### ❌ 错误2：missing created_at

```json
"created_cases": [
  {"case_id": "case_event_10754"}  // ❌ 缺少created_at
]
```

✅ **修正**: 必须包含所有5个字段。

### ❌ 错误3：时间格式错误

```json
"created_at": "2025-11-16 00:09:24"  // ❌ 应该是ISO格式
```

✅ **修正**:
```json
"created_at": "2025-11-16T00:09:24.283768"  // ✓ ISO格式
```

---

## 快速检查清单

| 项目 | 检查 |
|------|------|
| ✓ event_id | 是否与scenario配置相符？ |
| ✓ scenario_dir | 是否与metadata.json的scenarios[i]相符？ |
| ✓ case_id | 是否唯一？（每个scenario中） |
| ✓ created_at | 是否为ISO格式？（YYYY-MM-DDTHH:MM:SS.sss） |
| ✓ status | 是否为有效值？（created\|od_generating等） |
| ✓ source_scenario_id | 是否与scenario_dir相同？ |

---

## 脚本使用命令

```bash
# 运行脚本
python sync_scenario_index.py

# 查看帮助（脚本有详细文档）
python sync_scenario_index.py --help

# 验证JSON格式
python -m json.tool output/scenarios/scenario_index.json > /dev/null
```

---

## 文件参考

| 文件 | 说明 |
|------|------|
| `sync_scenario_index.py` | 自动同步脚本 |
| `SCENARIO_INDEX_SYNC_GUIDE.md` | 详细使用指南 |
| `SCENARIO_INDEX_FIELDS_REFERENCE.md` | 本文档（字段参考） |
| `SCENARIO_INDEX_SYNC_SUMMARY.md` | 执行结果总结 |
| `output/scenarios/scenario_index.json` | 场景索引文件 |

---

**提示**: 建议每次创建新case后运行 `python sync_scenario_index.py` 来自动更新scenario_index.json！
