# OD数据仿真进度监测修复

## 问题描述

**前端使用通用仿真进度监测API时，无法正确读取批次仿真的进度信息**

- 前端调用：`GET /api/v1/simulation_progress/{case_id}` （正确的API）
- 后端调用：`batch-optimization` API （错误的API）

根本原因：`get_simulation_progress()` 方法在查找进度文件时，使用了错误的目录路径构造逻辑，导致无法定位批次仿真中的 `progress.json` 文件。

## 技术分析

### 仿真目录结构差异

#### 普通仿真（OD数据仿真）
```
cases/{case_id}/simulations/
├── sim_1116_224602643_micro/
│   ├── simulation_metadata.json
│   ├── progress.json          ← 进度文件
│   └── ...
```

#### 批次仿真（批量优化仿真）
```
cases/{case_id}/simulations/
├── plan_opti/
│   ├── batch_20251111_072133/
│   │   ├── baseline_plan/
│   │   │   ├── sim_66/
│   │   │   │   ├── simulation_metadata.json
│   │   │   │   ├── progress.json  ← 进度文件
│   │   │   │   └── ...
```

### 旧代码的问题

```python
# 旧代码：假设所有仿真在 simulations/{sim_id}/ 下
sim_folder = simulations_dir / sim_id  # 错误！对于批次仿真无效
progress_file = sim_folder / "progress.json"
```

这导致对于批次仿真（如 `sim_66`），代码查找：
```
cases/case_id/simulations/sim_66/progress.json  ✗ 不存在
```

而实际位置是：
```
cases/case_id/simulations/plan_opti/batch_20251111_072133/baseline_plan/sim_66/progress.json  ✓ 存在
```

## 修复方案

### 利用元数据中的 `result_folder` 字段

所有仿真元数据都包含 `result_folder` 字段，记录了完整的仿真目录路径：

```json
{
  "simulation_id": "batch_batch_20251111_072133_baseline_plan_seed66_micro",
  "result_folder": "cases\\case_20251110_130339\\simulations\\plan_opti\\batch_20251111_072133\\baseline_plan\\sim_66",
  ...
}
```

### 实现方式

**文件**：`api/services/simulation_service.py:729-768`

```python
for sim in simulations:
    sim_id = sim.get("simulation_id")

    # 新：从元数据获取仿真文件夹
    result_folder_str = sim.get("result_folder")
    if result_folder_str:
        sim_folder = Path(result_folder_str)  # 使用元数据中的路径
    else:
        sim_folder = simulations_dir / sim_id  # 回退到旧方式

    # 使用正确的路径读取进度文件
    progress_file = sim_folder / "progress.json"
```

**优势**：
1. ✅ 支持两种目录结构（普通仿真 + 批次仿真）
2. ✅ 完全向后兼容（旧元数据可能没有 `result_folder`，会回退）
3. ✅ 无需修改仿真目录结构
4. ✅ 充分利用现有元数据

## 修复内容详解

### 改进1：使用元数据路径

| 场景 | 旧代码 | 新代码 | 结果 |
|------|--------|--------|------|
| 普通仿真 | `simulations_dir / sim_id` | `result_folder` 或 fallback | ✓ 正确 |
| 批次仿真 | ✗ 无法找到 | `result_folder` | ✓ 正确 |

### 改进2：更好的错误处理

```python
except Exception as e:
    logger.warning(f"读取进度文件失败 {progress_file}: {str(e)}")
    sim["progress"] = 100 if sim.get("status") == "completed" else 0
```

- 使用 `logger` 记录错误（而非 `except:` 吞掉异常）
- 进度文件不存在时，使用元数据中的状态作为备选

### 改进3：处理文件不存在的情况

```python
else:
    # 进度文件不存在，使用元数据中的状态
    sim["progress"] = 100 if sim.get("status") == "completed" else 0
```

对于 `pending` 状态的仿真，进度文件可能还不存在，需要妥善处理。

## 测试结果

### 测试案例1：混合结构（批次+普通）
```
案例：case_20251110_130339
✓ 成功加载 15 个仿真
  - 普通仿真：3 个
  - 批次仿真：12 个

✓ 进度文件路径验证：13 个✓，2 个✗（pending或no progress.json）
✓ 进度统计：
  - 已完成：13 个
  - 运行中：0 个
  - 失败：1 个
  - 总体进度：86%
```

### 测试案例2：普通仿真
```
案例：case_20251116_224458
✓ 成功加载 2 个仿真
✓ 进度文件路径验证：1 个✓，1 个✗（pending）
✓ 进度统计：
  - 已完成：0 个
  - 运行中：1 个
  - 失败：0 个
  - 总体进度：0%
```

## 关键特性

### 1. 向后兼容性
- ✅ 旧格式仿真（没有 `result_folder`）继续工作
- ✅ 新格式仿真（有 `result_folder`）正确加载
- ✅ 混合结构项目完全支持

### 2. 错误恢复
- ✅ 进度文件不存在不会中断整个流程
- ✅ 文件读取失败有适当的日志记录
- ✅ 使用元数据状态作为备选

### 3. 性能
- ✅ 无额外的目录遍历
- ✅ 直接使用元数据路径（O(1) 查找）
- ✅ 批量仿真不会多次遍历

## API行为

### 前端调用
```javascript
// OD数据仿真进度查询（正确的API）
GET /api/v1/simulation_progress/{case_id}

// 返回：
{
  "case_id": "case_20251110_130339",
  "simulations": [
    {
      "simulation_id": "...",
      "status": "completed",
      "progress": 100,        ← 从 progress.json 读取
      "result_folder": "...",
      ...
    }
  ],
  "stats": {
    "total": 15,
    "completed": 13,
    "in_progress": 0,
    "failed": 1
  },
  "progress_percentage": 86
}
```

### 前端不应该调用
```javascript
// ✗ 批次优化API（用于批量优化仿真）
GET /api/v1/control/batch-optimization/batch/{batch_id}/progress

// 这是用于控制优化（批量策略评估）的API，与OD仿真进度无关
```

## 代码质量

| 指标 | 改进 |
|------|------|
| 目录查找 | 从硬编码拼接改为使用元数据路径 |
| 错误处理 | 从 `except:` 改为 `except Exception as e` + logging |
| 日志记录 | 添加详细的warning日志用于调试 |
| 兼容性 | 支持旧格式（fallback）和新格式（元数据路径） |
| 可读性 | 添加详细注释说明两种目录结构 |

## 验证步骤

1. **编译检查**
   ```bash
   python -m py_compile api/services/simulation_service.py
   ```

2. **功能测试**
   ```python
   # 前端API调用（不是batch-optimization）
   GET /api/v1/simulation_progress/{case_id}
   ```

3. **覆盖范围**
   - ✅ 普通仿真（直接结构）
   - ✅ 批次仿真（嵌套结构）
   - ✅ 混合项目（两种都有）
   - ✅ 进度文件存在/不存在
   - ✅ 状态为 pending/running/completed/failed

## 总结

此修复完全解决了OD数据仿真进度监测的问题：
- ✅ 前端通过正确的API `/api/v1/simulation_progress/{case_id}` 获取进度
- ✅ 后端正确定位并读取所有仿真的进度文件（包括批次仿真）
- ✅ 支持混合结构项目（既有普通仿真又有批次仿真）
- ✅ 完全向后兼容，无需迁移现有数据
