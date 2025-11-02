# ui-progress-optimization Specification

## Purpose

优化批量仿真列表卡片UI布局和进度计算逻辑，确保操作按钮在同一行显示，同时正确处理失败任务的进度统计。

## Requirements

### Requirement: 批次卡片操作按钮单行显示

操作按钮（监控进度、查看结果、删除）MUST在同一行显示，不进行换行。系统MUST：
- 限制按钮宽度，避免超出卡片宽度
- 对超长文本进行截断处理
- 保持按钮可点击状态
- 在所有分辨率下保持一致

**优先级**: P1
**状态**: 新增

#### Scenario: 批次卡片在标准分辨率下显示

**Given**:
- 批次卡片宽度为300px
- 需要显示3个操作按钮

**When**:
- 用户查看批次列表

**Then**:
- 3个按钮在同一行显示
- 按钮间距为6px
- 按钮宽度自动调整以适应卡片宽度
- 按钮文本超长时显示省略号（...）
- 按钮仍然保持可点击状态

---

#### Scenario: 不同分辨率下的响应式显示

**Given**:
- 用户在不同屏幕分辨率下查看列表

**When**:
- 用户缩放浏览器窗口

**Then**:
- 按钮始终在同一行显示
- 按钮宽度响应式调整
- 文本截断处理一致
- 无水平滚动条出现

---

### Requirement: 进度计算考虑失败任务

批次进度计算MUST将失败的任务视为\"已处理完毕\"，采用统一的进度公式。系统MUST：
- 失败任务贡献100%完成度
- 总进度 = (已完成 + 已失败 + 已取消) / 总任务数 × 100
- 失败批次的总进度显示为100%

**优先级**: P1
**状态**: 新增

#### Scenario: 批次中有失败任务的进度计算

**Given**:
- 批次包含6个任务
- 状态分布：2个completed, 2个failed, 1个running(50%), 1个pending

**When**:
- 系统计算批次总进度

**Then**:
- 系统计算：(2×100 + 2×100 + 1×50 + 1×0) / (6×100) = 66.7%
- 进度条显示66.7%
- failed任务被视为已处理，不再增加

---

#### Scenario: 批次全部失败时的进度显示

**Given**:
- 批次包含6个任务，全部失败

**When**:
- 系统计算批次总进度

**Then**:
- 系统计算：(6×100) / (6×100) = 100%
- 进度条显示100%
- 批次状态显示为\"failed\"，但进度完成

---

#### Scenario: 混合completed和failed的进度计算

**Given**:
- 批次包含4个任务
- 状态：2个completed, 2个failed

**When**:
- 系统计算批次总进度

**Then**:
- 系统计算：(2×100 + 2×100) / (4×100) = 100%
- 进度条显示100%
- 所有任务已处理完毕

---

## API Endpoints

无新增API端点。此需求涉及前端UI和现有后端服务的改进。

---

## Data Structures

### 进度计算公式更新

后端`batch_simulation_scheduler.py`中的进度计算：

```python
# 旧公式（不考虑failed任务）
total_progress = sum(
    100 if task.status in ["completed", "cancelled"] else task.progress
    for task in self.tasks
) / len(self.tasks)

# 新公式（将failed任务视为100%完成）
total_progress = sum(
    100 if task.status in ["completed", "failed", "cancelled"] else task.progress
    for task in self.tasks
) / len(self.tasks)
```

---

## CSS Changes

### 批次卡片按钮容器样式更新

```css
/* frontend/control/css/simulations.css */

.batch-card-actions {
    display: flex;
    gap: 6px;                    /* ← 从8px减少为6px */
    flex-wrap: nowrap;           /* ← 从wrap改为nowrap，防止换行 */
    overflow: hidden;            /* ← 防止溢出 */
}

.btn-small {
    padding: 6px 8px;            /* ← 从8px 10px减少为6px 8px */
    font-size: 0.8rem;           /* ← 从0.85rem减少为0.8rem */
    min-width: 0;                /* ← 允许flex item缩小到0 */
    white-space: nowrap;         /* ← 防止文本换行 */
    overflow: hidden;            /* ← 隐藏溢出文本 */
    text-overflow: ellipsis;     /* ← 显示省略号 */
}
```

### 详细说明

| 属性 | 旧值 | 新值 | 原因 |
|------|------|------|------|
| `.batch-card-actions` gap | 8px | 6px | 减少按钮间距，为3个按钮留出更多空间 |
| `.batch-card-actions` flex-wrap | wrap | nowrap | 强制按钮在同一行，禁止换行 |
| `.batch-card-actions` overflow | - | hidden | 防止超出的内容溢出卡片 |
| `.btn-small` padding | 8px 10px | 6px 8px | 减少按钮内边距，缩小按钮整体尺寸 |
| `.btn-small` font-size | 0.85rem | 0.8rem | 缩小字体，为文本留出更多空间 |
| `.btn-small` min-width | - | 0 | 允许flex item在必要时缩小到0 |
| `.btn-small` white-space | - | nowrap | 防止按钮文本换行 |
| `.btn-small` overflow | - | hidden | 隐藏溢出的文本 |
| `.btn-small` text-overflow | - | ellipsis | 对超长文本显示省略号 |

---

## Implementation Details

### 前端实现 (已完成)

**文件**: `frontend/control/css/simulations.css`

1. 修改`.batch-card-actions`容器样式
   - 移除`flex-wrap: wrap`
   - 添加`flex-wrap: nowrap`
   - 减少`gap`从8px到6px

2. 修改`.btn-small`按钮样式
   - 减少`padding`从8px 10px到6px 8px
   - 减少`font-size`从0.85rem到0.8rem
   - 添加`min-width: 0`
   - 添加`white-space: nowrap`
   - 添加`overflow: hidden`
   - 添加`text-overflow: ellipsis`

### 后端实现 (已完成)

**文件**: `shared/control_tools/batch_simulation_scheduler.py`

1. 更新`_update_batch_progress()`方法（第216-231行）
   - 修改进度计算公式
   - failed任务贡献100%完成度
   - 新公式：`if task.status == "failed": total_progress += 100`

**文件**: `api/services/batch_optimization_service.py`

1. `get_batch_progress()`方法调用`_update_batch_progress()`
   - 自动应用新的进度计算逻辑
   - 无需额外修改

---

## Button Layout Calculation

### 按钮宽度计算示例

假设批次卡片宽度为300px，需要放置3个按钮：

```
总可用宽度 = 300px
间距总和 = 6px × 2 = 12px
可用于按钮的宽度 = 300px - 12px = 288px
单个按钮平均宽度 = 288px / 3 = 96px

按钮1: 96px (文本: "监控进度")
按钮2: 96px (文本: "查看结果")
按钮3: 96px (文本: "删除")
```

### 文本截断示例

| 按钮原始文本 | 显示文本 (96px宽度) | 说明 |
|-----------|-----------------|------|
| 监控进度 | 监控进度 | 完整显示 |
| 查看结果 | 查看结果 | 完整显示 |
| 删除 | 删除 | 完整显示 |
| 查看详细分析结果 | 查看详细... | 截断显示 |

---

## Testing

### UI Tests

- [ ] test_buttons_single_line - 验证3个按钮在同一行显示
- [ ] test_buttons_no_wrap - 验证flex-wrap为nowrap
- [ ] test_button_text_ellipsis - 验证超长文本显示省略号
- [ ] test_buttons_responsive - 验证不同分辨率下的显示
- [ ] test_button_clickable - 验证按钮仍然可点击

### Progress Calculation Tests

- [ ] test_progress_with_failed_tasks - 计算包含失败任务的进度
- [ ] test_progress_all_failed - 全部失败时进度为100%
- [ ] test_progress_mixed_completed_failed - 混合completed和failed的计算
- [ ] test_progress_cancelled_tasks - 已取消任务也视为100%
- [ ] test_batch_progress_display - 进度条显示正确

### E2E Tests

- [ ] test_batch_card_layout - 批次卡片完整显示
- [ ] test_progress_bar_updates - 进度条随任务状态更新
- [ ] test_failed_batch_completion - 失败批次进度显示为100%

---

## Related Specs

- [batch-cancellation](../batch-cancellation/spec.md) - 批次取消功能（使用新的进度计算）
- [simulation-cancellation](../simulation-cancellation/spec.md) - 单个仿真取消
- [batch-optimization](../batch-optimization/spec.md) - 批量仿真优化

---

## Status

- **Started**: 2025-11-02
- **Completed**: 2025-11-02
- **Version**: 1.0

---
