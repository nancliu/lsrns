# 批次结果加载 API 后端修复

**Date**: 2025-11-03
**Issue**: API 返回 500 错误，响应数据验证失败
**Status**: ✅ **已修复**

---

## 🐛 问题诊断

### 症状
前端成功调用了 `/batch/{batch_id}/results` API，但收到 500 错误：

```
ResponseValidationError: 2 validation errors:
  'plan_results' - Field required
  'created_at' - Field required
```

### 根本原因

在 `api/services/batch_optimization_service.py` 中发现**重复的 `get_batch_results()` 方法定义**：

**第 1024 行（正确的实现）**：
```python
def get_batch_results(self, case_id: str, batch_id: str, include_time_series: bool = False) -> Dict:
    # 正确实现：
    # 1. 从任务列表提取指标
    # 2. 正确查找 sim_{seed} 目录
    # 3. 返回 BatchResultsResponse 格式的数据
```

**第 1785 行（不完整的实现）**：
```python
def get_batch_results(self, case_id: str, batch_id: str) -> Dict:
    # 不完整实现：
    # 1. 使用 BatchResultAnalyzer (路径查找有bug)
    # 2. 返回不兼容的数据格式
    # 3. 使用过时的设计
```

**问题**：Python 中后定义的方法会覆盖先前的定义，所以实际执行的是第二个不完整的版本。

### 返回数据格式不兼容

**API 响应模型期望** (`BatchResultsResponse`):
```python
class BatchResultsResponse(BaseModel):
    batch_id: str
    status: BatchSimulationStatus
    plan_results: List[PlanResultSummary]  # ← 必填！
    created_at: datetime  # ← 必填！
    completed_at: Optional[datetime]
```

**第二个实现返回的数据结构**：
```python
{
    "batch_id": "batch_20251103_095402",
    "case_id": "case_20251028_091831",
    "status": "completed",
    "analysis": {...},  # ← 这个字段不在模型中！
    "metadata": {  # ← 这个字段不在模型中！
        "created_at": "...",  # ← 放在嵌套的 metadata 中，不是顶级！
        ...
    }
}
```

这导致 Pydantic 验证失败，因为：
1. `plan_results` 缺失（但有 `analysis` 字段）
2. `created_at` 缺失（但在 `metadata.created_at` 中）

---

## ✅ 修复方案

### 删除重复的方法

删除第 1785-1842 行的不完整方法定义，保留第 1024 行的正确实现。

### 第一个实现的特点

```python
def get_batch_results(
    self, case_id: str, batch_id: str, include_time_series: bool = False
) -> Dict[str, Any]:
    """获取批次结果汇总"""

    # 1. 获取批次进度和任务列表
    progress_data = self.scheduler.get_batch_progress(case_id, batch_id)

    # 2. 按方案分组任务
    plan_tasks = {}
    for task in tasks:
        if task.plan_id not in plan_tasks:
            plan_tasks[task.plan_id] = []
        plan_tasks[task.plan_id].append(task)

    # 3. 为每个方案提取结果
    plan_results = []
    for plan_id, plan_task_list in plan_tasks.items():
        # 从 sim_{seed} 目录提取指标
        simulations = []
        for task in plan_task_list:
            if task.status == "completed" and task.simulation_id:
                metrics = self._extract_simulation_metrics(
                    case_id, batch_id, plan_id, task
                )
                if metrics:
                    simulations.append(metrics)

        # 计算聚合统计
        aggregated_metrics = self._calculate_aggregated_metrics(simulations)

        plan_results.append({
            "plan_id": plan_id,
            "plan_name": plan_name,
            "simulations": simulations,
            "aggregated_metrics": aggregated_metrics,
        })

    # 4. 返回 BatchResultsResponse 兼容的格式
    return {
        "batch_id": batch_id,
        "status": progress_data["status"],
        "plan_results": plan_results,  # ✓ 顶级字段
        "created_at": metadata.get("created_at"),  # ✓ 顶级字段
        "completed_at": metadata.get("completed_at"),
    }
```

### 关键改进

| 方面 | 第二个（删除的）| 第一个（保留的）| 改进 |
|------|---|---|---|
| **数据来源** | BatchResultAnalyzer | 直接从任务 | 避免路径查找bug |
| **目录结构** | `plan_id/summary.xml` | `plan_id/sim_XX/summary.xml` | 正确支持批量仿真 |
| **返回格式** | `analysis` + `metadata` | `plan_results` + `created_at` | 符合 API 模型 |
| **字段位置** | 嵌套结构 | 顶级结构 | Pydantic 验证通过 |

---

## 🧪 验证步骤

1. **重新加载页面** → F5 或 Ctrl+Shift+R
2. **进入批次监控** → 找已完成的批次
3. **点击"查看结果"** → 应该看到对比表格
4. **检查浏览器控制台** → 无错误消息

### 预期结果

**批次结果应显示**：
- ✅ 方案对比表格
- ✅ 基准方案与所有test方案的对比
- ✅ 聚合指标（均值、标准差等）
- ✅ 性能图表

### API 调用成功标志

```json
GET /api/v1/control/batch-optimization/batch/batch_20251103_095402/results?include_time_series=true

HTTP/1.1 200 OK
Content-Type: application/json

{
  "batch_id": "batch_20251103_095402",
  "status": "completed",
  "plan_results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案（无管控）",
      "simulations": [
        {
          "seed": 66,
          "simulation_id": "...",
          "avg_speed": 22.5,
          ...
        }
      ],
      "aggregated_metrics": {
        "avg_speed": {
          "mean": 22.55,
          "std": 0.15,
          "min": 22.4,
          "max": 22.7
        }
      }
    }
  ],
  "created_at": "2025-11-03T09:54:02.262840",
  "completed_at": "2025-11-03T09:55:38.724147"
}
```

---

## 📝 相关文件修改

**backend_optimization_service.py**:
- 删除行：1785-1842（重复的 `get_batch_results()`）
- 保留行：1024-1124（完整的 `get_batch_results()`）

---

## 🎓 教训

这个bug再次展示了 Python 中方法重复定义的危险性：

1. **无编译错误** - Python 是动态语言，重复定义不会报错
2. **后定义覆盖** - 后来定义的方法会无声地覆盖先前的
3. **隐蔽的bug** - 代码看起来"存在"，但实际执行的是错误的版本

**防止措施**：
- 使用 linter 检测重复定义（pylint, flake8）
- 编写单元测试验证返回格式
- 使用 Pydantic 模型做严格的类型检查
- 代码审查时特别检查长文件中是否有重复方法

---

**Commit**: `3b6295e` - "fix: 删除重复的 get_batch_results() 方法定义"
**Status**: ✅ **已修复并准备测试**
