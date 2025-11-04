# 指标分类澄清 - 8个对比指标 + 1个验证指标

**更新日期**: 2025-11-04
**优先级**: P0 (重要澄清)
**影响范围**: 第一层结果页面的所有指标分类

---

## 🎯 核心澄清

**之前误认**: 9个指标都是"对比指标"
**现在正确**: 8个"对比指标" + 1个"验证指标"

---

## 📊 指标重新分类

### 8个对比指标 (可计算改进率)

| # | 指标名 | 英文名 | 单位 | 改进方向 | 优先级 | 用途 |
|---|--------|--------|------|---------|--------|------|
| 1 | **已完成车数** | ended | 辆 | ⬆️越高越好 | **P0** | 通行效率 |
| 2 | **等待车数** | waiting | 辆 | ⬇️越低越好 | **P0** | 拥堵程度 |
| 3 | **传送次数** | teleports | 次 | ⬇️越低越好 | **P0** | 拥堵严重程度 |
| 4 | **平均速度** | avgSpeed | m/s | ⬆️越高越好 | **P0** | 性能指标 |
| 5 | 当前运行车数 | running | 辆 | ⬇️越低越好 | P1 | 滞留车数量 |
| 6 | 已插入车数 | inserted | 辆 | ⬆️越高越好 | P2 | 插入成功率 |
| 7 | 碰撞次数 | collisions | 次 | ⬇️越低越好 | P2 | 仿真安全性 |
| 8 | 已加载车数 | loaded | 辆 | ➡️中立 | P2 | 基准流量 |

**特点**: 值随着控制策略变化而变化，能反映策略的效果

### 1个验证指标 (不计算改进率)

| # | 指标名 | 英文名 | 单位 | 用途 | 优先级 |
|---|--------|--------|------|------|--------|
| 9 | 仿真步数 | step | 秒 | 验证仿真完整性 | **P0** |

**特点**: 值恒定相同，用于检查仿真是否正常执行到预定时长

---

## ❌ 为什么 Step 不是对比指标

### 问题1: 值恒定相同

```
同一案例中所有仿真:
├─ baseline_plan:
│  ├─ sim_66: step = 3599.00 秒 ✓
│  ├─ sim_67: step = 3599.00 秒 ✓
│  └─ sim_68: step = 3599.00 秒 ✓
│
└─ test_plan:
   ├─ sim_66: step = 3599.00 秒 ✓
   ├─ sim_67: step = 3599.00 秒 ✓
   └─ sim_68: step = 3599.00 秒 ✓

所有值都是 3599.00 → 无法比较！
```

### 问题2: 改进率无意义

```
baseline_step_mean = 3599.00
test_step_mean     = 3599.00

改进率 = (3599 - 3599) / 3599 × 100% = 0%

结论: 总是0%，用户看不出任何意义
```

### 问题3: 改进方向矛盾

```
通常说"越低越好"，但如果step=0表示仿真没运行
所以其实是"相等最好"

这与"越高越好"和"越低越好"的改进方向都不符合
```

---

## ✅ Step 的正确用途

### 用途1: 验证仿真完整执行

```python
# 检查仿真是否运行到预定时长
expected_duration = 3600  # 秒
actual_duration = 3599.00

if actual_duration >= expected_duration - 1:
    status = "✅ 仿真成功完成"
else:
    status = "❌ 仿真提前中止"
```

### 用途2: 诊断仿真问题

```python
# 识别异常情况
if step < 3500:  # 远少于预期
    issue = "严重异常: 仿真早期中止，可能网络错误或配置问题"
elif step < 3599:  # 略少于预期
    issue = "轻微异常: 仿真接近完成但未完整运行"
elif step >= 3599:
    issue = "正常: 仿真完整执行"
```

---

## 📋 API响应修正

### 修正前 (9个指标，step无用)

```json
{
  "metric_config": {
    "ended": { "direction": "higher", ... },
    "waiting": { "direction": "lower", ... },
    "teleports": { "direction": "lower", ... },
    "avgSpeed": { "direction": "higher", ... },
    "running": { "direction": "lower", ... },
    "inserted": { "direction": "higher", ... },
    "collisions": { "direction": "lower", ... },
    "loaded": { "direction": "neutral", ... },
    "step": { "direction": "neutral", ... }  ❌ 误设
  }
}
```

### 修正后 (明确区分验证指标)

```json
{
  "metric_config": {
    // 8个对比指标
    "ended": {
      "direction": "higher",
      "is_comparison_metric": true,
      "label": "已完成车数",
      "unit": "辆"
    },
    "waiting": {
      "direction": "lower",
      "is_comparison_metric": true,
      "label": "等待车数",
      "unit": "辆"
    },
    // ... 其他对比指标 ...

    // 1个验证指标
    "step": {
      "direction": "verification",  ← 改为verification
      "is_comparison_metric": false,  ← 明确标记
      "label": "仿真步数",
      "unit": "秒",
      "is_verification_metric": true,
      "expected_value": 3600,
      "description": "用于验证仿真是否完整执行到预定时长"
    }
  }
}
```

---

## 🎨 前端表格显示修正

### 修正前 (step被当作普通指标)

```
┌─────────────────────────────────────────┐
│ 指标          baseline  test  改进率    │
├─────────────────────────────────────────┤
│ 已完成车数    72860     74500  +2.3%   │
│ 等待车数      7269      5800   +20.2%  │
│ 传送次数      96        25     +74.0%  │
│ 平均速度      22.07     28.50  +29.1%  │
│ ...其他指标...                          │
│ 仿真步数      3599      3599   -  ❌   │
└─────────────────────────────────────────┘
```

### 修正后 (分离验证指标)

```
┌─────────────────────────────────────────┐
│    🎯 交通性能对比指标 (8个)            │
├─────────────────────────────────────────┤
│ 指标          baseline  test  改进率    │
├─────────────────────────────────────────┤
│ 已完成车数    72860     74500  +2.3%   │
│ 等待车数      7269      5800   +20.2%  │
│ 传送次数      96        25     +74.0%  │
│ 平均速度      22.07     28.50  +29.1%  │
│ ...其他指标...                          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      🔍 仿真验证指标 (1个)              │
├─────────────────────────────────────────┤
│ baseline: step = 3599.00 秒             │
│ test:     step = 3599.00 秒             │
│ 状态: ✅ 仿真完整执行                 │
└─────────────────────────────────────────┘
```

---

## 🔧 前端改进率计算修正

### 修正前

```javascript
// 对所有9个指标计算改进率，包括step
metricKeys.forEach(metricKey => {
    const config = metricConfig[metricKey];
    const direction = config.direction;

    if (direction === 'higher') {
        improvementRate = rawChange;
    } else if (direction === 'lower') {
        improvementRate = -rawChange;
    } else {
        improvementRate = null;  // step被当作中立指标
    }
});
```

### 修正后

```javascript
// 区分对比指标和验证指标
metricKeys.forEach(metricKey => {
    const config = metricConfig[metricKey];
    const direction = config.direction;

    // 验证指标：跳过改进率计算
    if (direction === 'verification' || !config.is_comparison_metric) {
        renderVerificationStatus(metricKey, values);  // 显示验证状态
        return;
    }

    // 对比指标：计算改进率
    if (direction === 'higher') {
        improvementRate = rawChange;
    } else if (direction === 'lower') {
        improvementRate = -rawChange;
    } else if (direction === 'neutral') {
        improvementRate = null;
    }

    renderImprovementRate(metricKey, improvementRate);  // 显示改进率
});
```

---

## 📊 对比指标 vs 验证指标

| 特征 | 对比指标 | 验证指标 |
|------|---------|---------|
| **数量** | 8个 | 1个 |
| **值是否相同** | 不同 (随策略变化) | 相同 (恒定) |
| **改进率** | 可计算 | 无意义 |
| **表格显示** | 在对比表中 | 在验证区块中 |
| **用户关注** | 主要关注 | 次要关注 (验证用) |
| **例子** | ended, waiting | step |

---

## 📝 修改清单

### 后端修改
- [ ] 更新 `metric_config` 中 step 的 `direction` 为 "verification"
- [ ] 添加 `is_comparison_metric: false` 标记
- [ ] 添加 `is_verification_metric: true` 标记
- [ ] 更新对应的单元测试

### 前端修改
- [ ] 修改 `renderNewBatchResults()` 区分指标类型
- [ ] 添加对验证指标的特殊处理 (不显示改进率)
- [ ] 创建验证指标显示区块
- [ ] 更新表格样式 (可选：为验证区块设置不同背景)

### 文档修改
- [ ] 更新 `LAYER1_CALCULATION_LOGIC.md` 关于step的部分
- [ ] 更新 `TRAFFIC_METRICS_SPECIFICATION.md` 明确step的验证角色
- [ ] 创建 `STEP_METRIC_CLARIFICATION.md` 详细说明 ✅ (已完成)

### 测试修改
- [ ] 验证修改后的改进率计算 (step应跳过)
- [ ] 测试验证指标显示 (step应显示在验证区块)
- [ ] 集成测试确保表格显示正确

---

## 🎯 修改的好处

### 用户体验改进
- ✅ 对比表格更清晰，只显示有意义的8个指标
- ✅ 避免用户困惑为什么 step 的改进率总是 "-"
- ✅ 验证区块明确告诉用户仿真是否成功

### 逻辑清晰性
- ✅ 明确区分"对比指标"和"验证指标"
- ✅ API响应中明确标记指标类型
- ✅ 前端代码逻辑清晰，易于维护

### 诊断效率
- ✅ 快速识别仿真异常 (从step值判断)
- ✅ 支持快速故障排查

---

## 📊 修改前后对比

| 方面 | 修改前 | 修改后 | 改进 |
|------|--------|--------|------|
| 对比指标数 | 9个(有1个无用) | 8个(全部有用) | ✅ |
| 表格行数 | 9行(1行无意义) | 8行(全部有意义) | ✅ |
| 用户困惑 | 为什么step总是"-"? | 清楚了解step的用途 | ✅ |
| 代码清晰度 | 混在一起(一般) | 明确区分(好) | ✅ |
| 可维护性 | 中等 | 高 | ✅ |

---

## ✅ 验证清单

在合并这些修改前，请确保:

- [ ] 后端API返回正确的 metric_config (step标记为verification)
- [ ] 前端跳过step的改进率计算
- [ ] 前端验证区块正确显示step的状态
- [ ] 所有单元测试通过 (包括修改后的测试)
- [ ] 集成测试验证完整流程
- [ ] 文档已更新 (明确说明8个对比指标+1个验证指标)

---

## 📚 相关文档

- `STEP_METRIC_CLARIFICATION.md` - step指标的详细澄清
- `LAYER1_CALCULATION_LOGIC.md` - 计算逻辑详解 (需要更新step部分)
- `TRAFFIC_METRICS_SPECIFICATION.md` - 指标规范 (需要更新step部分)
- `CALCULATION_WORKFLOW_DIAGRAM.md` - 工作流程图 (需要更新)

---

**总结**: 通过将 step 从对比指标改为验证指标，使第一层结果页面更清晰、更有用，
让用户能够快速了解控制策略的效果，同时可以验证仿真是否正常执行。

---

**更新日期**: 2025-11-04
**版本**: 1.0 (初始版本)
**优先级**: P0 (需要立即实施)
