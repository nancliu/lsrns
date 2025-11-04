# 第一层结果页面 - 计算逻辑详解

**文档日期**: 2025-11-04
**范围**: Layer 1 结果分析的完整计算流程
**涉及系统**: 后端聚合统计 + 前端改进率计算

---

## 📊 整体计算流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 数据采集: 解析每个仿真的summary.xml (后端)                  │
│    多个种子 (seed_66, seed_67, seed_68, ...) → 多个仿真结果    │
└─────────────────┬──────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. 指标提取: 从XML提取9个关键指标 (后端)                        │
│    loaded, inserted, ended, running, waiting, teleports,         │
│    collisions, avgSpeed, step                                    │
└─────────────────┬──────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. 聚合统计: 对多个种子的结果进行统计 (后端)                    │
│    对每个指标计算: mean, std, min, max                          │
└─────────────────┬──────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. 改进率计算: 对比baseline vs test方案 (前端)                 │
│    根据指标方向 (higher/lower) 正确计算改进率                  │
└─────────────────┬──────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. 结果呈现: 对比表格、图表、改进率摘要 (前端)                 │
│    显示中文标签、单位、改进百分比                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ 数据采集阶段 - 解析summary.xml

### 位置: `api/services/batch_optimization_service.py:1487-1555`

### 流程

```python
def _parse_summary_xml(self, file_path: Path) -> Dict[str, Any]:
    """
    解析单个仿真的summary.xml文件
    """
    # 1. 解析XML文件
    tree = ET.parse(file_path)
    root = tree.getroot()

    # 2. 获取所有<step>元素
    steps = root.findall("step")

    # 3. 取最后一步（仿真结束时的最终统计）
    last_step = steps[-1]

    # 4. 提取9个关键指标
    metrics = {
        "step": float(last_step.get("time", 0)),           # 秒
        "loaded": int(last_step.get("loaded", 0)),         # 辆
        "inserted": int(last_step.get("inserted", 0)),     # 辆
        "ended": int(last_step.get("ended", 0)),           # 辆 ⭐
        "running": int(last_step.get("running", 0)),       # 辆
        "waiting": int(last_step.get("waiting", 0)),       # 辆 ⭐
        "teleports": int(last_step.get("teleports", 0)),   # 次 ⭐
        "collisions": int(last_step.get("collisions", 0)), # 次
        "avgSpeed": float(last_step.get("meanSpeed", 0.0)) # m/s ⭐
    }

    return metrics
```

### 实际XML例子 (最后一步)

```xml
<summary>
    ...（前面是0-3598秒的数据）...
    <step time="3599.00"
          loaded="101852"
          inserted="86278"
          running="21722"
          waiting="7269"
          ended="72861"
          collisions="540"
          teleports="96"
          halting="3887"
          stopped="0"
          meanWaitingTime="36.42"
          meanTravelTime="541.17"
          meanSpeed="22.07"
          meanSpeedRelative="0.60"
          duration="408"/>
</summary>
```

### 输出结果 (单个仿真)

```python
{
    "seed": 66,
    "simulation_id": "sim_001",
    "step": 3599.0,        # 秒
    "loaded": 101852,      # 辆
    "inserted": 86278,     # 辆
    "ended": 72861,        # 辆
    "running": 21722,      # 辆
    "waiting": 7269,       # 辆
    "teleports": 96,       # 次
    "collisions": 540,     # 次
    "avgSpeed": 22.07,     # m/s
    "avg_travel_time": 541.17,  # 秒 (从tripinfo.xml)
    "total_delay": 45000.0      # 秒 (从tripinfo.xml)
}
```

---

## 2️⃣ 多仿真聚合统计阶段

### 位置: `api/services/batch_optimization_service.py:1594-1635`

### 流程

假设有3个种子 (seed_66, seed_67, seed_68)，每个产生一个仿真结果:

```python
simulations = [
    {
        "seed": 66,
        "loaded": 101852,
        "inserted": 86278,
        "ended": 72861,
        "avgSpeed": 22.07,
        ...
    },
    {
        "seed": 67,
        "loaded": 101852,
        "inserted": 86295,
        "ended": 72890,
        "avgSpeed": 22.15,
        ...
    },
    {
        "seed": 68,
        "loaded": 101852,
        "inserted": 86250,
        "ended": 72830,
        "avgSpeed": 22.00,
        ...
    }
]
```

### 聚合计算代码

```python
def _calculate_aggregated_metrics(
    self, simulations: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """
    对多个仿真结果进行统计聚合
    """
    # 1. 提取所有指标名称 (排除seed和simulation_id)
    metric_names = set()
    for sim in simulations:
        for key in sim.keys():
            if key not in ["seed", "simulation_id"] and isinstance(sim[key], (int, float)):
                metric_names.add(key)

    # 2. 对每个指标进行统计
    aggregated = {}

    for metric_name in metric_names:
        # 2.1 提取该指标的所有值
        values = [
            sim[metric_name]
            for sim in simulations
            if metric_name in sim and sim[metric_name] is not None
        ]

        if values:
            # 2.2 计算统计值
            aggregated[metric_name] = {
                "mean": statistics.mean(values),              # 平均值
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,  # 标准差
                "min": min(values),                           # 最小值
                "max": max(values),                           # 最大值
            }

    return aggregated
```

### 聚合计算示例 (ended指标)

对于 **已完成车数 (ended)** 指标:

```
3个种子的值:
  seed_66: ended = 72861 辆
  seed_67: ended = 72890 辆
  seed_68: ended = 72830 辆

聚合统计:
  mean = (72861 + 72890 + 72830) / 3 = 72860.33 辆
  std  = √[ ((72861-72860.33)² + (72890-72860.33)² + (72830-72860.33)²) / (3-1) ]
       = √[ (0.447 + 883.11 + 900.11) / 2 ]
       = √891.835
       = 29.86 辆
  min  = min(72861, 72890, 72830) = 72830 辆
  max  = max(72861, 72890, 72830) = 72890 辆
```

### 输出结果 (某方案的所有聚合指标)

```json
{
  "aggregated_metrics": {
    "step": {
      "mean": 3599.0,
      "std": 0.0,
      "min": 3599.0,
      "max": 3599.0
    },
    "loaded": {
      "mean": 101852.0,
      "std": 0.0,
      "min": 101852,
      "max": 101852
    },
    "inserted": {
      "mean": 86274.33,
      "std": 22.25,
      "min": 86250,
      "max": 86295
    },
    "ended": {
      "mean": 72860.33,
      "std": 29.86,
      "min": 72830,
      "max": 72890
    },
    "running": {
      "mean": 21727.0,
      "std": 31.44,
      "min": 21698,
      "max": 21760
    },
    "waiting": {
      "mean": 7268.67,
      "std": 2.16,
      "min": 7267,
      "max": 7271
    },
    "teleports": {
      "mean": 96.0,
      "std": 0.0,
      "min": 96,
      "max": 96
    },
    "collisions": {
      "mean": 539.67,
      "std": 0.47,
      "min": 539,
      "max": 540
    },
    "avgSpeed": {
      "mean": 22.073,
      "std": 0.074,
      "min": 22.0,
      "max": 22.15
    }
  }
}
```

---

## 3️⃣ 改进率计算阶段 (前端)

### 位置: `frontend/control/js/batch_results.js:330-390`

### 核心公式

改进率的计算取决于**指标的改进方向** (direction):

#### 对于"越低越好"的指标 (direction = "lower")

```
原始变化 = (test_值 - baseline_值) / baseline_值 × 100%

改进率 = -原始变化   ← 注意符号翻转！

含义:
  - 如果test值更低 → 原始变化为负 → 改进率为正 ✅ (改进)
  - 如果test值更高 → 原始变化为正 → 改进率为负 ❌ (恶化)
```

**对应指标**: waiting (等待车数), teleports (传送次数), collisions (碰撞次数), running (运行车数)

#### 对于"越高越好"的指标 (direction = "higher")

```
原始变化 = (test_值 - baseline_值) / baseline_值 × 100%

改进率 = 原始变化   ← 直接使用

含义:
  - 如果test值更高 → 原始变化为正 → 改进率为正 ✅ (改进)
  - 如果test值更低 → 原始变化为负 → 改进率为负 ❌ (恶化)
```

**对应指标**: ended (完成车数), inserted (插入车数), avgSpeed (平均速度)

#### 对于"中立"的指标 (direction = "neutral")

```
改进率 = null   ← 不计算改进率，显示 "-"
```

**对应指标**: step (仿真步数), loaded (加载车数)

### 前端实现代码

```javascript
function renderNewBatchResults(planResults) {
    // ... 获取baseline和test方案 ...
    const baselinePlan = planResults[0];  // 基准方案
    const testPlans = planResults.slice(1);  // 测试方案

    const metricConfig = batchResultsData.metric_config || {};

    // 获取所有指标
    const metricKeys = baselinePlan.aggregated_metrics
        ? Object.keys(baselinePlan.aggregated_metrics)
        : [];

    metricKeys.forEach(metricKey => {
        const baselineMetrics = baselinePlan.aggregated_metrics[metricKey] || {};

        // 从API获取元数据
        const config = metricConfig[metricKey] || {};
        const metricLabel = config.label || metricKey;
        const unit = config.unit || '';
        const direction = config.direction || 'neutral';

        testPlans.forEach(testPlan => {
            const testMetrics = testPlan.aggregated_metrics[metricKey] || {};
            const testMean = testMetrics.mean || 0;
            const baselineMean = baselineMetrics.mean || 0;

            // === 改进率计算核心逻辑 ===
            let improvementRate = 0;

            if (baselineMean !== 0) {
                // 1. 计算原始变化百分比
                const rawChange = ((testMean - baselineMean) / baselineMean) * 100;

                // 2. 根据方向调整改进率
                if (direction === 'lower') {
                    // 越低越好：减少是改进
                    improvementRate = -rawChange;
                } else if (direction === 'higher') {
                    // 越高越好：增加是改进
                    improvementRate = rawChange;
                } else {
                    // 中立：不计算
                    improvementRate = null;
                }
            }

            // 3. 显示改进率
            if (improvementRate !== null) {
                const improveClass = improvementRate > 0 ? 'positive' : 'negative';
                const sign = improvementRate > 0 ? '+' : '';
                displayImprovementRate(`${sign}${improvementRate.toFixed(1)}%`, improveClass);
            } else {
                displayImprovementRate('-', 'neutral');
            }
        });
    });
}
```

### 改进率计算示例

#### 示例1: 已完成车数 (ended) - 越高越好

```
baseline: mean = 72860.33 辆
test:     mean = 74500.00 辆

direction = "higher" (越高越好)

原始变化 = (74500 - 72860.33) / 72860.33 × 100
        = 1639.67 / 72860.33 × 100
        = 2.25%

改进率 = 原始变化 = +2.25% ✅
→ 显示: "+2.3%" (绿色，表示改进)
```

#### 示例2: 等待车数 (waiting) - 越低越好

```
baseline: mean = 7268.67 辆
test:     mean = 5800.00 辆

direction = "lower" (越低越好)

原始变化 = (5800 - 7268.67) / 7268.67 × 100
        = -1468.67 / 7268.67 × 100
        = -20.21%

改进率 = -原始变化 = -(-20.21%) = +20.21% ✅
→ 显示: "+20.2%" (绿色，表示改进)
```

#### 示例3: 传送次数 (teleports) - 越低越好

```
baseline: mean = 96.0 次
test:     mean = 25.0 次

direction = "lower" (越低越好)

原始变化 = (25 - 96) / 96 × 100
        = -71 / 96 × 100
        = -73.96%

改进率 = -原始变化 = +73.96% ✅✅✅
→ 显示: "+74.0%" (绿色，非常显著改进)
```

#### 示例4: 平均速度 (avgSpeed) - 越高越好

```
baseline: mean = 22.073 m/s
test:     mean = 28.500 m/s

direction = "higher" (越高越好)

原始变化 = (28.5 - 22.073) / 22.073 × 100
        = 6.427 / 22.073 × 100
        = 29.09%

改进率 = 原始变化 = +29.09% ✅✅
→ 显示: "+29.1%" (绿色，显著改进)
```

#### 示例5: 仿真步数 (step) - 中立

```
baseline: mean = 3599.0 秒
test:     mean = 3599.0 秒

direction = "neutral" (中立)

改进率 = null

→ 显示: "-" (灰色，无法计算)
```

---

## 4️⃣ 元数据配置 (API)

### 位置: `api/services/batch_optimization_service.py:1343-1435`

### 元数据结构

后端在 `get_batch_results()` 中返回 `metric_config`，指导前端如何显示每个指标:

```python
response = {
    "batch_id": "batch_001",
    "plan_results": [...],
    "metric_config": {
        "ended": {
            "label": "已完成车数",
            "unit": "辆",
            "direction": "higher",
            "description": "完成行程、离开网络的车数（通行效率）"
        },
        "waiting": {
            "label": "等待车数",
            "unit": "辆",
            "direction": "lower",
            "description": "因拥堵停止等待的车数"
        },
        "teleports": {
            "label": "传送次数",
            "unit": "次",
            "direction": "lower",
            "description": "SUMO进行的传送操作次数（拥堵严重程度）"
        },
        "avgSpeed": {
            "label": "平均速度",
            "unit": "m/s",
            "direction": "higher",
            "description": "所有已完成车的平均行驶速度"
        },
        "running": {
            "label": "当前运行车数",
            "unit": "辆",
            "direction": "lower",
            "description": "仿真结束时仍在网络中的车数"
        },
        "collisions": {
            "label": "碰撞次数",
            "unit": "次",
            "direction": "lower",
            "description": "仿真中发生的碰撞事件数"
        },
        "loaded": {
            "label": "已加载车数",
            "unit": "辆",
            "direction": "neutral",
            "description": "被加载到网络中的总车数"
        },
        "inserted": {
            "label": "已插入车数",
            "unit": "辆",
            "direction": "higher",
            "description": "成功插入到网络的车数"
        },
        "step": {
            "label": "仿真步数",
            "unit": "秒",
            "direction": "neutral",
            "description": "整个仿真运行的总时长"
        }
    }
}
```

---

## 5️⃣ 完整表格呈现示例

### 表格结构 (HTML)

```html
<table class="comparison-table">
  <thead>
    <tr>
      <th>指标</th>
      <th colspan="2">基准方案</th>
      <th colspan="2">测试方案</th>
      <th>改进率</th>
    </tr>
    <tr>
      <th></th>
      <th>mean</th>
      <th>std</th>
      <th>mean</th>
      <th>std</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>已完成车数</strong> <span>(辆)</span></td>
      <td>72860.33</td>
      <td>29.86</td>
      <td>74500.00</td>
      <td>35.20</td>
      <td><span class="improvement positive">+2.3%</span></td>
    </tr>
    <tr>
      <td><strong>等待车数</strong> <span>(辆)</span></td>
      <td>7268.67</td>
      <td>2.16</td>
      <td>5800.00</td>
      <td>5.50</td>
      <td><span class="improvement positive">+20.2%</span></td>
    </tr>
    <tr>
      <td><strong>传送次数</strong> <span>(次)</span></td>
      <td>96.00</td>
      <td>0.00</td>
      <td>25.00</td>
      <td>2.50</td>
      <td><span class="improvement positive">+74.0%</span></td>
    </tr>
    <tr>
      <td><strong>平均速度</strong> <span>(m/s)</span></td>
      <td>22.07</td>
      <td>0.07</td>
      <td>28.50</td>
      <td>0.10</td>
      <td><span class="improvement positive">+29.1%</span></td>
    </tr>
    <tr>
      <td><strong>当前运行车数</strong> <span>(辆)</span></td>
      <td>21727.00</td>
      <td>31.44</td>
      <td>19800.00</td>
      <td>45.80</td>
      <td><span class="improvement positive">+8.8%</span></td>
    </tr>
    <tr>
      <td><strong>碰撞次数</strong> <span>(次)</span></td>
      <td>539.67</td>
      <td>0.47</td>
      <td>510.00</td>
      <td>3.20</td>
      <td><span class="improvement positive">+5.5%</span></td>
    </tr>
    <tr>
      <td><strong>仿真步数</strong> <span>(秒)</span></td>
      <td>3599.00</td>
      <td>0.00</td>
      <td>3599.00</td>
      <td>0.00</td>
      <td><span style="color: #999;">-</span></td>
    </tr>
  </tbody>
</table>
```

### 表格显示效果

| 指标 | baseline(mean) | baseline(std) | test(mean) | test(std) | 改进率 |
|------|--------|--------|--------|---------|--------|
| **已完成车数** (辆) | 72860.33 | 29.86 | 74500.00 | 35.20 | **+2.3%** ✅ |
| **等待车数** (辆) | 7268.67 | 2.16 | 5800.00 | 5.50 | **+20.2%** ✅ |
| **传送次数** (次) | 96.00 | 0.00 | 25.00 | 2.50 | **+74.0%** ✅ |
| **平均速度** (m/s) | 22.07 | 0.07 | 28.50 | 0.10 | **+29.1%** ✅ |
| **当前运行车数** (辆) | 21727.00 | 31.44 | 19800.00 | 45.80 | **+8.8%** ✅ |
| **碰撞次数** (次) | 539.67 | 0.47 | 510.00 | 3.20 | **+5.5%** ✅ |
| **仿真步数** (秒) | 3599.00 | 0.00 | 3599.00 | 0.00 | **-** |

---

## 6️⃣ 关键计算规则总结

### 方向识别规则

| 指标 | 中文名 | direction | 规则 |
|------|--------|-----------|------|
| ended | 已完成车数 | higher | test > baseline → 改进 ✅ |
| waiting | 等待车数 | lower | test < baseline → 改进 ✅ |
| teleports | 传送次数 | lower | test < baseline → 改进 ✅ |
| avgSpeed | 平均速度 | higher | test > baseline → 改进 ✅ |
| running | 当前运行车数 | lower | test < baseline → 改进 ✅ |
| collisions | 碰撞次数 | lower | test < baseline → 改进 ✅ |
| inserted | 已插入车数 | higher | test > baseline → 改进 ✅ |
| loaded | 已加载车数 | neutral | 不计算改进率 |
| step | 仿真步数 | neutral | 不计算改进率 |

### 改进率公式速查表

```
越高越好 (higher):    改进率 = (test - baseline) / baseline × 100%
越低越好 (lower):     改进率 = -(test - baseline) / baseline × 100%
中立 (neutral):       改进率 = null (显示 "-")
```

### 颜色编码

| 颜色 | 含义 | CSS类 |
|------|------|-------|
| 🟢 绿色 | 改进 (正改进率) | `.improvement.positive` |
| 🔴 红色 | 恶化 (负改进率) | `.improvement.negative` |
| ⚫ 灰色 | 无法计算 | `.neutral` |

---

## 7️⃣ 异常处理

### 边界情况

1. **baseline_mean = 0**
   ```javascript
   if (baselineMean !== 0) {
       // 正常计算
   } else {
       // 跳过计算，显示 "-"
   }
   ```

2. **只有1个仿真 (std = 0)**
   ```python
   "std": statistics.stdev(values) if len(values) > 1 else 0.0
   ```

3. **没有该指标的数据**
   ```python
   values = [
       sim[metric_name]
       for sim in simulations
       if metric_name in sim and sim[metric_name] is not None
   ]
   if values:
       # 有数据，继续处理
   else:
       # 无数据，跳过
   ```

---

## 📈 计算性能特性

| 阶段 | 时间复杂度 | 说明 |
|------|-----------|------|
| XML解析 | O(n) | n = XML中的step数量 (~3600) |
| 指标提取 | O(m) | m = 每个仿真的指标数 (9个) |
| 聚合统计 | O(k×m) | k = 仿真数 (3-10个) × m = 指标数 |
| 改进率计算 | O(m×k) | 前端计算，k = 方案数 (2-5个) |
| **总计** | **O(n + k×m)** | n远大于k×m，XML解析占主要时间 |

### 实际性能

- 单个XML解析: ~50ms
- 多仿真聚合: ~10ms
- 改进率计算: ~5ms (前端)
- **总耗时**: ~100-200ms (包括网络往返)

---

## 参考文档

1. **TRAFFIC_METRICS_SPECIFICATION.md** - 9个指标的详细定义
2. **XML_PARSING_FIX_REPORT.md** - XML解析修复详情
3. **FINAL_METRICS_ANALYSIS_SUMMARY.md** - 整体分析和建议

---

**最后更新**: 2025-11-04
**版本**: 1.0 (初始版本)
