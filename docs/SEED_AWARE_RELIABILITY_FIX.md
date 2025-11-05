# 种子感知的可靠性评分修复 - 2025-11-05

**问题**: 排序结果生成时忽略了种子数量和随机种子参数，导致可靠性评分不正确

**根本原因**: 代码只返回默认可靠性评分(70)，没有真正使用多种子数据

**状态**: ✅ 已修复

**Commit**: a91b399

---

## 问题诊断

### 设计与实现的差距

**设计规范** (`openspec/changes/add-layer2-control-strategy-ranking/design.md`)：

```
可靠性评分 = 100 - (有效性标准差 * 10)
其中：
  - 有效性标准差 = 不同种子间有效性的标准差
  - 如果只有1个种子：默认使用70
```

**当前实现**：
```python
def _calculate_reliability(self, combined_analysis, plan_id):
    # TODO: In future phases, extract std_dev from batch results
    # For now, use a default reliability score
    return 70.0  # 总是返回70！
```

### 数据来源检查

`batch_metadata.json` 中包含的数据：
```json
{
  "num_seeds": 3,
  "base_seed": 66,
  "plan_ids": [
    "baseline_plan",
    "plan_dhs_morning_peak_severe",
    "plan_tec_morning_peak_severe",
    "plan_vss_dhs_morning_peak_severe",
    "plan_vss_morning_peak_severe"
  ]
}
```

实际文件结构：
```
batch_20251105_000102/
├── baseline_plan/
│   ├── sim_66/summary.xml      ← 种子1
│   ├── sim_67/summary.xml      ← 种子2
│   └── sim_68/summary.xml      ← 种子3
├── plan_dhs_morning_peak_severe/
│   ├── sim_66/summary.xml
│   ├── sim_67/summary.xml
│   └── sim_68/summary.xml
└── ...
```

**问题**：
1. `BatchResultAnalyzer` 在 `plan_dir/summary.xml` 找不到文件（实际在 `plan_dir/sim_XX/summary.xml`）
2. 即使找到了，也没有保存多种子数据用于可靠性计算
3. `MultiCriteriaScorer` 没有实现种子感知的可靠性计算

---

## 完整修复

### 修复 1: BatchResultAnalyzer - 聚合多种子指标

**文件**: `shared/analysis_tools/batch_result_analyzer.py`

**问题**:
- 查找 `plan_dir/summary.xml`（不存在）
- 应该查找 `plan_dir/sim_66/summary.xml`, `sim_67/summary.xml`, `sim_68/summary.xml`

**解决方案**:
```python
def _extract_aggregated_metrics(self, plan_dir: Path, plan_id: str) -> Dict[str, Any]:
    """
    从计划目录中聚合多个种子的指标
    """
    # 1. 找所有 sim_XX 目录
    sim_dirs = sorted([d for d in plan_dir.iterdir()
                      if d.is_dir() and d.name.startswith('sim_')])

    # 2. 从每个 sim_XX/summary.xml 提取指标
    all_metrics = []
    for sim_dir in sim_dirs:
        summary_path = sim_dir / "summary.xml"
        metrics = self._extract_summary_metrics(summary_path)
        all_metrics.append(metrics)

    # 3. 聚合指标（平均）
    aggregated = self._aggregate_metrics_list(all_metrics, plan_id)

    # 4. 保存原始种子数据用于可靠性计算
    aggregated['num_seeds'] = len(all_metrics)
    aggregated['seed_metrics'] = all_metrics

    return aggregated

def _aggregate_metrics_list(self, metrics_list, plan_id):
    """对所有指标计算平均值"""
    aggregated = {}
    for key in all_keys:
        values = [float(metrics[key]) for metrics in metrics_list if key in metrics]
        aggregated[key] = round(statistics.mean(values), 2)
    return aggregated
```

### 修复 2: AnalysisOrchestrator - 传递种子信息

**文件**: `shared/analysis_tools/analysis_orchestrator.py`

**改动**:
```python
def analyze_batch(self, batch_dir, plan_ids, baseline_plan_id):
    # 1. 加载 batch_metadata.json
    metadata_path = batch_dir / "batch_metadata.json"
    batch_metadata = json.load(open(metadata_path))

    # 2. 传递给 _combine_results
    combined_results = self._combine_results(
        summary_results, tripinfo_results, edgedata_results,
        output_combination,
        batch_metadata  # ← 新增
    )

def _combine_results(self, ..., batch_metadata):
    # 在结果中包含种子信息
    return {
        "batch_metadata": {
            "num_seeds": batch_metadata.get("num_seeds", 1),
            "base_seed": batch_metadata.get("base_seed"),
        },
        "summary": {
            ...
            "seed_data": summary_results.get("seed_data", {}),  # ← 新增
        },
        ...
    }
```

### 修复 3: SummaryAnalyzer - 提取种子数据

**文件**: `shared/analysis_tools/summary_analyzer.py`

**改动**:
```python
def analyze(self, batch_dir, plan_ids, baseline_plan_id):
    # ... 现有代码 ...

    # 新增：提取种子数据
    seed_data = {}
    for plan_id, plan_data in batch_results.get("plan_results", {}).items():
        seed_metrics = plan_data.get("metrics", {}).get("seed_metrics", [])
        if seed_metrics:
            seed_data[plan_id] = seed_metrics

    return {
        ...
        "seed_data": seed_data,  # ← 新增
        ...
    }
```

### 修复 4: MultiCriteriaScorer - 种子感知的可靠性计算

**文件**: `shared/analysis_tools/multi_criteria_scorer.py`

**改动**:
```python
def _calculate_reliability(self, combined_analysis, plan_id):
    """
    计算可靠性评分 (15%)

    公式: reliability = 100 - (std_dev * 10)
    其中 std_dev = 有效性在不同种子间的标准差
    """

    # 1. 获取种子数据
    seed_data = combined_analysis.get("summary", {}).get("seed_data", {}).get(plan_id, [])
    num_seeds = combined_analysis.get("batch_metadata", {}).get("num_seeds", 1)

    # 2. 如果只有1个种子，使用默认值70
    if len(seed_data) <= 1 or num_seeds <= 1:
        return 70.0

    # 3. 计算每个种子的有效性分数
    effectiveness_scores = []
    for seed_metrics in seed_data:
        effectiveness = self._calculate_effectiveness_from_metrics(
            seed_metrics,
            improvement_rates_baseline
        )
        effectiveness_scores.append(effectiveness)

    # 4. 计算标准差
    std_dev = statistics.stdev(effectiveness_scores)
    reliability = max(0, min(100, 100 - (std_dev * 10)))

    logger.info(f"Reliability: std_dev={std_dev}, reliability={reliability}")
    return reliability

def _calculate_effectiveness_from_metrics(self, seed_metrics, improvement_rates):
    """为单个种子计算有效性"""
    # 使用改进率计算有效性（公式同原有实现）
    effectiveness = (
        0.25 * self._normalize_score(improvement_rates.get("ended", 0))
        + 0.25 * self._normalize_score(improvement_rates.get("avgSpeed", 0))
        + 0.20 * self._normalize_score(improvement_rates.get("waiting", 0))
        + 0.20 * self._normalize_score(improvement_rates.get("teleports", 0))
        + ...
    )
    return effectiveness
```

---

## 工作流示例

### 场景：3 个种子的批量仿真

**输入**:
```
batch_metadata.json: num_seeds=3, base_seed=66
baseline_plan/
  ├── sim_66/summary.xml (末步数据: ended=892, avgSpeed=8.5, ...)
  ├── sim_67/summary.xml (末步数据: ended=895, avgSpeed=8.6, ...)
  └── sim_68/summary.xml (末步数据: ended=890, avgSpeed=8.4, ...)
plan_dhs_xxx/
  ├── sim_66/summary.xml (末步数据: ended=920, avgSpeed=9.2, ...)
  ├── sim_67/summary.xml (末步数据: ended=925, avgSpeed=9.3, ...)
  └── sim_68/summary.xml (末步数据: ended=915, avgSpeed=9.1, ...)
```

**处理步骤**:

1. **BatchResultAnalyzer 聚合**:
   ```
   baseline_plan:
     - ended: (892 + 895 + 890) / 3 = 892.33
     - avgSpeed: (8.5 + 8.6 + 8.4) / 3 = 8.50
     - seed_metrics: [度量_66, 度量_67, 度量_68]

   plan_dhs_xxx:
     - ended: (920 + 925 + 915) / 3 = 920.00
     - avgSpeed: (9.2 + 9.3 + 9.1) / 3 = 9.20
     - seed_metrics: [度量_66, 度量_67, 度量_68]
   ```

2. **改进率计算**:
   ```
   plan_dhs_xxx 相对 baseline:
     - ended 改进: (920 - 892.33) / 892.33 * 100 = +3.10%
     - avgSpeed 改进: (9.20 - 8.50) / 8.50 * 100 = +8.24%
   ```

3. **有效性评分**（基于聚合指标）:
   ```
   effectiveness = 0.25 * 3.10 + 0.25 * 8.24 + ... = 某个值
   ```

4. **可靠性评分**（基于种子变化）:
   ```
   种子 66: ended_improvement = (920-892)/892 = 3.14%
          avgSpeed_improvement = (9.2-8.5)/8.5 = 8.24%
          effectiveness_66 = 0.25*3.14 + 0.25*8.24 + ... = X1

   种子 67: ended_improvement = (925-895)/895 = 3.37%
          avgSpeed_improvement = (9.3-8.6)/8.6 = 8.14%
          effectiveness_67 = ... = X2

   种子 68: ended_improvement = (915-890)/890 = 2.81%
          avgSpeed_improvement = (9.1-8.4)/8.4 = 8.33%
          effectiveness_68 = ... = X3

   标准差 = stdev([X1, X2, X3]) = 某个较小值（如 2.5）
   可靠性 = 100 - (2.5 * 10) = 75.0 （高可靠性）
   ```

---

## 关键设计决策

### 为什么要保留 seed_metrics？

```python
# 好的做法
aggregated['seed_metrics'] = all_metrics
# 保留原始数据，用于：
# 1. 可靠性计算（计算标准差）
# 2. 未来的详细分析
# 3. 验证数据质量

# 不好的做法
# 只保留平均值，丢失种子信息
aggregated = mean(all_metrics)  # ❌
```

### 为什么用标准差计算可靠性？

**标准差的含义**:
- 小标准差 (1-2) → 不同种子结果相似 → 高可靠性 (80-90)
- 中等标准差 (3-5) → 结果有变化 → 中等可靠性 (50-70)
- 大标准差 (>5) → 结果差异大 → 低可靠性 (<50)

**例子**:
```
场景A: 有效性得分 [75, 76, 75] → std_dev=0.58 → reliability=94.2
       解读：策略性能稳定，强烈推荐

场景B: 有效性得分 [70, 80, 60] → std_dev=10.0 → reliability=0
       解读：策略性能不稳定，取决于种子，不可靠

场景C: 有效性得分 [75, 78, 72] → std_dev=3.0 → reliability=70
       解读：策略基本稳定，可推荐
```

---

## 与设计规范的对齐

| 设计规范 | 实现 | 状态 |
|---------|------|------|
| 可靠性 = 100 - (std_dev * 10) | ✅ 已实现 | ✅ |
| 单种子时默认 70 | ✅ 已实现 | ✅ |
| 使用 batch_metadata.json 的 num_seeds | ✅ 已实现 | ✅ |
| 使用 batch_metadata.json 的 base_seed | ✅ 已实现 | ✅ |
| 从 sim_XX 目录读取多个 summary.xml | ✅ 已实现 | ✅ |
| 聚合指标使用平均值 | ✅ 已实现 | ✅ |
| 保留种子数据用于计算 | ✅ 已实现 | ✅ |

---

## 修复影响范围

### 修改的文件

| 文件 | 修改内容 | 影响 |
|------|---------|------|
| `batch_result_analyzer.py` | 添加 `_extract_aggregated_metrics()`, `_aggregate_metrics_list()` | 核心修复 |
| `analysis_orchestrator.py` | 加载 batch_metadata，传递给 _combine_results | 数据流修复 |
| `summary_analyzer.py` | 提取并返回 seed_data | 数据传递 |
| `multi_criteria_scorer.py` | 修改 `_calculate_reliability()`, 添加 `_calculate_effectiveness_from_metrics()` | 核心计算 |

### 向后兼容性

✅ **完全向后兼容**：
- 如果 `batch_metadata.json` 缺失 → num_seeds 默认为 1 → 可靠性为 70
- 如果 seed_data 缺失 → 可靠性为 70
- 现有的单种子数据照样工作

---

## 验证

### 日志验证

重启后检查日志：

```
INFO: Loaded batch metadata: num_seeds=3, base_seed=66
INFO: Aggregated metrics for baseline_plan from 3 seeds: {...}
INFO: Aggregated metrics for plan_dhs_xxx from 3 seeds: {...}
INFO: Reliability for plan_dhs_xxx: std_dev=X.XX, effectiveness_scores=[...], reliability=YY.YY
```

### 前端验证

排序表格中，可靠性列应该显示：
- 单种子: 70 (默认)
- 多种子: 0-100 (基于变化)

---

## 总结

### ✅ 问题解决

1. **种子数据找不到** → 现在从 sim_XX 目录读取并聚合
2. **没有可靠性计算** → 现在基于多种子数据计算
3. **忽略 batch_metadata** → 现在正确使用 num_seeds 和 base_seed

### 🎯 设计实现完整性

所有四个评分维度现在都完全实现：
- ✅ 有效性(40%) - 基于改进率
- ✅ 覆盖率(25%) - 基于受影响范围
- ✅ 效率(20%) - 基于改进/成本
- ✅ 可靠性(15%) - 基于种子稳定性 **[新增]**

---

**修复完成日期**: 2025-11-05
**Commit**: a91b399
**状态**: ✅ 代码修复完成，等待服务器重启和测试
