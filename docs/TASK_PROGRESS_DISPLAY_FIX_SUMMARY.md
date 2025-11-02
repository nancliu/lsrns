# 任务进度显示百分比计算错误修复总结

**日期**: 2025-11-02
**问题**: 任务进度详情显示的百分比计算仍然错误
**根本原因**: 前端使用了硬编码的除数 144，假设所有仿真都是 14400 秒

---

## 问题诊断

### 错误的代码位置
**文件**: `frontend/control/js/batch_simulation.js`
**函数**: `renderTaskList()` (line 591-592)

**错误代码**:
```javascript
if (progressValue > 100) {
    // Assume it's in simulation steps (0-14400), convert to percentage
    progressPct = Math.min((progressValue / 144), 100);  // ❌ 硬编码除数！
}
```

### 为什么错误

1. **硬编码除数 144** 基于错误的假设：所有仿真都是 14400 秒
   - 14400 / 100 = 144（除数）

2. **实际情况**：仿真时长是可变的（例如 600 秒、3600 秒等）
   - 600 秒仿真的正确除数应该是：600 / 100 = 6
   - 14400 秒仿真的正确除数应该是：14400 / 100 = 144

3. **后端没有传递 `end_time`**
   - 前端无法计算正确的除数
   - 导致所有非 14400 秒的仿真显示错误的百分比

### 具体错误示例

**600 秒仿真，当前时间 300 秒**：
- ❌ 错误计算：`300 / 144 = 2.08%`（显示为几乎刚开始）
- ✅ 正确计算：`300 / (600/100) = 300 / 6 = 50.00%`（正确显示为一半）

---

## 修复方案

### 修复 1: 后端添加 `end_time` 字段

**文件**: `api/services/batch_optimization_service.py`
**行号**: 481-490

**修改内容**:
```python
result = {
    'current_step': current_step,
    'total_steps': total_steps,
    'end_time': total_steps,  # 新增：明确标识这是仿真结束时间（秒）
    'current_time': current_step,  # 新增：明确标识这是当前仿真时间（秒）
    'progress_percent': round(progress_percent, 2),
    'running_vehicles': summary.get('running_vehicles', 0),
    ...
}
```

**为什么需要**:
- 前端需要知道 `end_time` 来计算正确的除数
- 变量名称更清晰（`end_time` 比 `total_steps` 更明确）

### 修复 2: 前端动态计算除数

**文件**: `frontend/control/js/batch_simulation.js`
**函数**: `renderTaskList()` (line 588-605)

**修改内容**:
```javascript
if (progressValue > 100) {
    // Backend 返回的是原始仿真时间（秒），需要转换为百分比
    const endTime = liveStatus.end_time || 600;  // 从后端获取实际的仿真结束时间

    // 正确的除数：基于实际的仿真时长
    const divisor = endTime / 100;  // 动态计算，而不是硬编码 144
    progressPct = Math.min((progressValue / divisor), 100);
}
```

**为什么这样修复**:
- 使用后端传来的 `end_time` 计算正确的除数
- 支持任意长度的仿真
- 公式清晰：`(current_time / end_time) × 100`

---

## 验证修复

### 修复前（错误）
| 仿真时长 | 当前时间 | 后端返回 | 前端计算 | 正确值 | 是否正确 |
|---------|---------|---------|---------|-------|--------|
| 600秒   | 300秒   | 300     | 300/144=2% | 50% | ❌ |
| 14400秒 | 7200秒  | 7200    | 7200/144=50% | 50% | ✅ |

### 修复后（正确）
| 仿真时长 | 当前时间 | 后端返回 | end_time | divisor | 前端计算 | 正确值 | 是否正确 |
|---------|---------|---------|---------|---------|---------|-------|--------|
| 600秒   | 300秒   | 300     | 600     | 6       | 300/6=50% | 50% | ✅ |
| 14400秒 | 7200秒  | 7200    | 14400   | 144     | 7200/144=50% | 50% | ✅ |

---

## 关键点总结

1. **分子不是"步数"，是仿真时间（秒）**
   - 来自 summary.xml 的 `<step time="...">` 属性
   - 单位：秒，范围：0 到 end_time

2. **分母必须是实际配置的仿真结束时间**
   - 不能硬编码为 14400
   - 必须从后端动态获取

3. **前端无法自己知道正确的除数**
   - 必须依赖后端在 API 响应中包含 `end_time`
   - 然后动态计算：`divisor = end_time / 100`

4. **该修复前后兼容**
   - 如果后端没有提供 `end_time`，使用默认值 600
   - 逐步过渡到新的数据格式

---

## 修改的文件

### 1. `api/services/batch_optimization_service.py`
- 行 484-485：添加 `end_time` 和 `current_time` 字段
- 作用：后端明确返回仿真时长信息

### 2. `frontend/control/js/batch_simulation.js`
- 行 588-605：修复进度百分比计算逻辑
- 作用：前端使用动态除数而不是硬编码值

---

## 后续工作

### Priority 1 - 立即执行
✅ 已完成：修复前端计算逻辑（动态除数）
✅ 已完成：后端添加 `end_time` 字段

### Priority 2 - 必须修复
⏳ 待完成：后端改用动态 `total_steps`（当前仍硬编码为 14400）
- 需要从 summary.xml 配置中提取 `<time><end value="..."/>`
- 详见 `docs/PROGRESS_CALCULATION_FORMULA.md`

### Priority 3 - 优化
⏳ 可选：添加日志验证进度计算
⏳ 可选：单元测试覆盖各种仿真时长

---

## 相关文档

- `docs/PROGRESS_CALCULATION_FORMULA.md` - 完整的公式说明和后端修复指南
- `openspec/changes/unify-batch-monitoring-and-history/IMPLEMENTATION_SUMMARY.md` - Phase 1.9 实现细节
