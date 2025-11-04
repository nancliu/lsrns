# Step 指标澄清 - 从对比指标改为验证指标

**更新日期**: 2025-11-04
**优先级**: P0 (重要澄清)
**影响**: 第一层结果页面的指标分类

---

## 🔍 发现的问题

在实际验证中发现，**step** (仿真步数) 指标被误分类为"可对比指标"。

### 原误分类
```
9个对比指标 (错误):
├─ step ❌ (错误)
├─ loaded
├─ inserted
├─ ended
├─ running
├─ waiting
├─ teleports
├─ collisions
└─ avgSpeed
```

### 实际情况

**step 不是对比指标，而是验证指标！**

---

## ❌ 为什么 Step 不能作为对比指标

### 原因1: 值恒定相同

在同一个案例中，所有方案的仿真时长配置相同：

```python
# 案例级别的配置
case_metadata = {
    "case_name": "G4202绕城高速",
    "simulation_start_time": "07:00",
    "simulation_end_time": "08:00",    ← 1小时
    "total_simulation_duration": 3600  ← 固定3600秒
}

# 所有仿真都使用相同时长
baseline_plan sim_66: step = 3599.00 秒  ✓
baseline_plan sim_67: step = 3599.00 秒  ✓
baseline_plan sim_68: step = 3599.00 秒  ✓
test_plan sim_66:     step = 3599.00 秒  ✓
test_plan sim_67:     step = 3599.00 秒  ✓
test_plan sim_68:     step = 3599.00 秒  ✓
```

### 后果: 无法计算改进率

```
baseline_step_mean = 3599.00
test_step_mean     = 3599.00

改进率 = (3599 - 3599) / 3599 × 100% = 0%

结论: ➡️ 中立，无法判断好坏
```

### 计算示例 (对比真正的对比指标)

| 指标 | baseline | test | 改进率 | 含义 |
|------|----------|------|--------|------|
| **step** | 3599 | 3599 | **0%** | ❌ 无意义，两者相同 |
| ended | 72860 | 74500 | +2.3% | ✅ 有意义，体现通行效率 |
| waiting | 7269 | 5800 | +20.2% | ✅ 有意义，体现拥堵缓解 |

---

## ✅ Step 的正确用途：验证指标

### 用途1: 验证仿真是否完整执行

```python
# 检查仿真是否到达预定时长
if simulation_result.step == expected_duration:
    status = "✅ 仿真成功完成"  # 运行了完整的3600秒
else:
    status = "❌ 仿真提前中止"   # 可能因为其他原因停止
```

### 用途2: 验证仿真的一致性

在批量仿真中，检查所有仿真是否都完整执行：

```python
def verify_simulation_completeness(batch_results):
    """检查所有仿真是否都运行到预定时长"""
    expected_step = 3600  # 秒

    issues = []
    for plan_results in batch_results.plan_results:
        step = plan_results.aggregated_metrics["step"]["mean"]

        if step < expected_step - 1:  # 允许1秒误差
            issues.append({
                "plan": plan_results.plan_id,
                "step": step,
                "problem": "仿真提前结束，未完整运行"
            })

    if issues:
        print("⚠️ 发现异常:")
        for issue in issues:
            print(f"  {issue['plan']}: step={issue['step']}")
    else:
        print("✅ 所有仿真都完整运行")

# 输出示例
verify_simulation_completeness(batch_data)
# ✅ 所有仿真都完整运行
#    baseline: step = 3599.0 秒 ✓
#    test:     step = 3599.0 秒 ✓
```

### 用途3: 诊断仿真问题

```python
def diagnose_simulation_issues(plan_results):
    """诊断仿真执行状态"""
    step = plan_results.aggregated_metrics["step"]["mean"]
    expected_step = 3600

    diagnosis = {
        "step_value": step,
        "expected_step": expected_step,
        "status": None,
        "recommendation": None
    }

    if step >= expected_step:
        diagnosis["status"] = "✅ 正常完成"
        diagnosis["recommendation"] = "仿真执行正常"

    elif step >= expected_step * 0.95:  # 95%以上
        diagnosis["status"] = "⚠️ 基本完成"
        diagnosis["recommendation"] = "仿真基本完成，轻微异常"

    elif step >= expected_step * 0.80:  # 80%以上
        diagnosis["status"] = "❌ 提前中止"
        diagnosis["recommendation"] = "仿真可能遇到问题，建议检查日志"

    else:
        diagnosis["status"] = "🔴 严重异常"
        diagnosis["recommendation"] = "仿真严重异常，可能因为配置错误或网络问题"

    return diagnosis

# 输出示例
result = diagnose_simulation_issues(plan_data)
# {
#     "step_value": 3599.0,
#     "expected_step": 3600,
#     "status": "✅ 正常完成",
#     "recommendation": "仿真执行正常"
# }
```

---

## 📊 正确的对比指标分类

### 第一层结果页面应该显示的指标

#### **8个对比指标** (可计算改进率)

| # | 指标名 | 英文名 | 单位 | 改进方向 | 优先级 | 说明 |
|---|--------|--------|------|---------|--------|------|
| 1 | 已完成车数 | ended | 辆 | ⬆️高 | **P0** | 通行效率 |
| 2 | 等待车数 | waiting | 辆 | ⬇️低 | **P0** | 拥堵程度 |
| 3 | 传送次数 | teleports | 次 | ⬇️低 | **P0** | 拥堵严重程度 |
| 4 | 平均速度 | avgSpeed | m/s | ⬆️高 | **P0** | 性能指标 |
| 5 | 当前运行车数 | running | 辆 | ⬇️低 | P1 | 滞留车数量 |
| 6 | 已插入车数 | inserted | 辆 | ⬆️高 | P2 | 插入成功率 |
| 7 | 碰撞次数 | collisions | 次 | ⬇️低 | P2 | 仿真安全性 |
| 8 | 已加载车数 | loaded | 辆 | ➡️中 | P2 | 基准流量 |

#### **1个验证指标** (不计算改进率，用于验证)

| # | 指标名 | 英文名 | 单位 | 用途 | 优先级 |
|---|--------|--------|------|------|--------|
| 9 | 仿真步数 | step | 秒 | 验证仿真完整性 | **P0** |

---

## 🔄 改进率计算的修正规则

### 修正前 (错误)

```javascript
// 对所有9个指标都计算改进率，包括step
if (direction === 'neutral') {
    improvementRate = null;  // ❌ step被误设为中立
}
```

### 修正后 (正确)

```javascript
function calculateImprovementRate(metricKey, baselineValue, testValue, config) {
    // 特殊处理: step 不计算改进率
    if (metricKey === 'step') {
        return {
            rate: null,
            display: '-',
            reason: 'step是验证指标，不用于改进率计算'
        };
    }

    // 其他指标正常计算
    const direction = config.direction;

    if (baselineValue === 0) {
        return { rate: null, display: '-' };
    }

    const rawChange = ((testValue - baselineValue) / baselineValue) * 100;

    let improvementRate;
    if (direction === 'higher') {
        improvementRate = rawChange;
    } else if (direction === 'lower') {
        improvementRate = -rawChange;
    } else {
        improvementRate = null;
    }

    return {
        rate: improvementRate,
        display: improvementRate === null ? '-' : `${improvementRate.toFixed(1)}%`
    };
}
```

---

## 📋 对比表格的显示调整

### 修正前 (错误的step行)

```html
<tr>
  <td><strong>仿真步数</strong> <span>(秒)</span></td>
  <td>3599.00</td>
  <td>0.00</td>
  <td>3599.00</td>
  <td>0.00</td>
  <td><span style="color: #999;">-</span></td>  <!-- 无意义 -->
</tr>
```

### 修正后 (正确的step行)

```html
<!-- 选项1: 在主表中显示但清楚标注为验证指标 -->
<tr style="background-color: #f5f5f5; font-size: 0.9em;">
  <td>
    <strong>仿真步数</strong> <span>(秒)</span>
    <span style="color: #666; margin-left: 5px;">🔍 验证指标</span>
  </td>
  <td>3599.00</td>
  <td>0.00</td>
  <td>3599.00</td>
  <td>0.00</td>
  <td><span title="验证指标，无改进率">验证 ✓</span></td>
</tr>

<!-- 选项2: 单独显示在验证区块 -->
<div class="verification-section">
  <h4>仿真验证</h4>
  <p>✅ baseline: step = 3599.00 秒 (完整执行)</p>
  <p>✅ test: step = 3599.00 秒 (完整执行)</p>
</div>
```

---

## 🎯 Metric Config 的修正

### 修正前 (错误)

```json
{
  "step": {
    "label": "仿真步数",
    "unit": "秒",
    "direction": "neutral",  ❌ 误设为中立
    "description": "整个仿真运行的总时长"
  }
}
```

### 修正后 (正确)

```json
{
  "step": {
    "label": "仿真步数",
    "unit": "秒",
    "direction": "verification",  ✅ 明确设为验证指标
    "description": "整个仿真运行的总时长 - 用于验证仿真是否完整执行",
    "is_comparison_metric": false,
    "min_value": 0,
    "max_value": 86400,
    "expected_value": 3600
  }
}
```

---

## 📊 实际表格显示效果

### 修正前 (显示8+1个指标，但step无用)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 指标(单位)           baseline(mean) test(mean) 改进率              │
├─────────────────────────────────────────────────────────────────────┤
│ 已完成车数(辆)       72860.33      74500.00   🟢 +2.3%            │
│ 等待车数(辆)         7268.67       5800.00    🟢 +20.2%           │
│ 传送次数(次)         96.00         25.00      🟢 +74.0%           │
│ 平均速度(m/s)        22.07         28.50      🟢 +29.1%           │
│ 当前运行车数(辆)     21727.00      19800.00   🟢 +8.8%            │
│ 碰撞次数(次)         539.67        510.00     🟢 +5.5%            │
│ 已插入车数(辆)       86274.33      86750.00   🟢 +0.5%            │
│ 已加载车数(辆)       101852.00     101852.00  ⚫ -                 │
│ 仿真步数(秒)         3599.00       3599.00    ⚫ -      ❌ 无用   │
└─────────────────────────────────────────────────────────────────────┘
```

### 修正后 (8个对比指标 + 验证区块)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     🎯 交通性能对比指标 (8个)                       │
├─────────────────────────────────────────────────────────────────────┤
│ 指标(单位)           baseline(mean) test(mean) 改进率              │
├─────────────────────────────────────────────────────────────────────┤
│ 已完成车数(辆)       72860.33      74500.00   🟢 +2.3%            │
│ 等待车数(辆)         7268.67       5800.00    🟢 +20.2%           │
│ 传送次数(次)         96.00         25.00      🟢 +74.0%           │
│ 平均速度(m/s)        22.07         28.50      🟢 +29.1%           │
│ 当前运行车数(辆)     21727.00      19800.00   🟢 +8.8%            │
│ 碰撞次数(次)         539.67        510.00     🟢 +5.5%            │
│ 已插入车数(辆)       86274.33      86750.00   🟢 +0.5%            │
│ 已加载车数(辆)       101852.00     101852.00  ⚫ 基准              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     🔍 仿真验证指标 (1个)                           │
├─────────────────────────────────────────────────────────────────────┤
│ baseline: step = 3599.00 秒 ✅ 完整执行                           │
│ test:     step = 3599.00 秒 ✅ 完整执行                           │
│                                                                      │
│ 说明: step 仅用于验证仿真是否运行到预定时长，不用于改进率计算     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 代码修改建议

### 后端修改 (API响应)

```python
# api/services/batch_optimization_service.py

# 修改 metric_config 定义
metric_config = {
    # ... 其他8个对比指标 ...

    "step": {
        "label": "仿真步数",
        "unit": "秒",
        "direction": "verification",  ← 改为 verification
        "description": "整个仿真运行的总时长 - 用于验证仿真是否完整执行",
        "is_comparison_metric": False,  ← 新增字段标记
    }
}
```

### 前端修改 (改进率计算)

```javascript
// frontend/control/js/batch_results.js

function renderNewBatchResults(planResults) {
    // ...

    metricKeys.forEach(metricKey => {
        const config = metricConfig[metricKey] || {};
        const direction = config.direction;

        // 特殊处理验证指标
        if (direction === 'verification') {
            // 不计算改进率，只显示验证结果
            displayVerificationStatus(metricKey, values);
            return;  // 跳过改进率计算
        }

        // 其他指标正常计算改进率
        // ... 现有逻辑 ...
    });
}
```

---

## ✅ 修正清单

- [ ] 更新 metric_config，将 step 的 direction 改为 "verification"
- [ ] 修改前端 renderNewBatchResults()，跳过验证指标的改进率计算
- [ ] 更新表格显示，将 step 从对比指标区块移出
- [ ] 添加验证指标区块，显示 step 的验证状态
- [ ] 更新文档，说明 step 是验证指标而非对比指标
- [ ] 测试修改后的显示效果
- [ ] 更新单元测试的期望值 (从9个对比指标改为8个)

---

## 📝 总结

**改变**:
- ❌ step 不是第8个对比指标
- ✅ step 是验证指标，用于检查仿真是否完整执行

**影响**:
- 第一层结果页面显示 **8个对比指标** (可计算改进率)
- 添加 **1个验证区块** (显示仿真执行状态)
- 改进率计算更加清晰准确

**用户体验**:
- 对比表格更简洁，只显示有意义的改进率
- 验证区块清楚地告诉用户仿真是否完整执行
- 避免用户困惑为什么 step 的改进率总是 0%

---

**更新日期**: 2025-11-04
**版本**: 1.1 (修正版)
**责任**: 澄清 step 指标的真实角色
