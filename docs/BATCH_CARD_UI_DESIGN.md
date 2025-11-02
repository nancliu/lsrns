# 批次卡片 UI 设计文档

## 概述

批次卡片是批量仿真监控页面的核心 UI 组件，根据批次状态动态显示不同的按钮组合。所有按钮在卡片内一行显示，通过百分比宽度自动分配。

---

## 批次卡片状态与按钮行为

### 1️⃣ 运行中 (Running)
**状态徽章颜色**: 蓝色背景 (#d1ecf1)

```
┌─────────────────────────────────────────┐
│ batch_001_2025-01-15_10_30  [运行中]     │
│ 方案数: 5          总任务: 50            │
│ 创建时间: 2025-01-15 10:30:00           │
│ 耗时: 计算中...     成功率: 48%          │
├─────────────────────────────────────────┤
│ [监控进度]              [取消]           │
└─────────────────────────────────────────┘
```

**按钮配置**:
| 按钮 | 功能 | 样式 |
|------|------|------|
| [监控进度] | 查看实时进度 | 默认样式 (info 蓝色) |
| [取消] | POST /cancel - 保留目录，允许重启 | 危险样式 (danger 红色) |

**按钮宽度**: 每个按钮 50% (2个按钮均分)

---

### 2️⃣ 已取消 (Cancelled)
**状态徽章颜色**: 红色背景 (error-bg)

```
┌─────────────────────────────────────────┐
│ batch_002_2025-01-15_10_25  [已取消]     │
│ 方案数: 3          总任务: 30            │
│ 创建时间: 2025-01-15 10:25:00           │
│ 耗时: 3 分钟       成功率: 33%          │
├─────────────────────────────────────────┤
│ [启动仿真] [查看结果]  [删除]            │
└─────────────────────────────────────────┘
```

**按钮配置**:
| 按钮 | 功能 | 样式 |
|------|------|------|
| [启动仿真] | 重新启动仿真（支持） | 主色样式 (primary 蓝色) |
| [查看结果] | 查看之前的结果 | 默认样式 (info 蓝色) |
| [删除] | DELETE /batch/{id} - 完全删除目录 | 危险样式 (danger 红色) |

**按钮宽度**: 每个按钮 33.333% (3个按钮均分)

---

### 3️⃣ 已完成 (Completed)
**状态徽章颜色**: 绿色背景 (#d4edda)

```
┌─────────────────────────────────────────┐
│ batch_001_2025-01-15_09_30  [已完成]     │
│ 方案数: 5          总任务: 50            │
│ 创建时间: 2025-01-15 09:30:00           │
│ 耗时: 8 分钟 25 秒   成功率: 96%        │
├─────────────────────────────────────────┤
│ [查看进度] [查看结果]  [删除]            │
└─────────────────────────────────────────┘
```

**按钮配置**:
| 按钮 | 功能 | 样式 |
|------|------|------|
| [查看进度] | 查看进度最终情况（历史回顾） | 默认样式 (info 蓝色) |
| [查看结果] | 查看仿真结果 | 默认样式 (info 蓝色) |
| [删除] | DELETE /batch/{id} - 完全删除目录 | 危险样式 (danger 红色) |

**按钮宽度**: 每个按钮 33.333% (3个按钮均分)

---

### 4️⃣ 待运行 (Pending)
**状态徽章颜色**: 黄色背景 (alert-bg)

```
┌─────────────────────────────────────────┐
│ batch_003_2025-01-15_10_45  [待运行]     │
│ 方案数: 2          总任务: 20            │
│ 创建时间: 2025-01-15 10:45:00           │
│ 耗时: -              成功率: -           │
├─────────────────────────────────────────┤
│        [启动仿真]                        │
└─────────────────────────────────────────┘
```

**按钮配置**:
| 按钮 | 功能 | 样式 |
|------|------|------|
| [启动仿真] | 启动仿真 | 主色样式 (primary 蓝色) |

**按钮宽度**: 单个按钮占据适当宽度

---

### 5️⃣ 失败 (Failed)
**状态徽章颜色**: 红色背景 (error-bg)

```
┌─────────────────────────────────────────┐
│ batch_004_2025-01-15_10_20  [失败]      │
│ 方案数: 4          总任务: 40            │
│ 创建时间: 2025-01-15 10:20:00           │
│ 耗时: 5 分钟       成功率: 50%          │
├─────────────────────────────────────────┤
│ [重新启动] [查看结果]  [删除]            │
└─────────────────────────────────────────┘
```

**按钮配置**:
| 按钮 | 功能 | 样式 |
|------|------|------|
| [重新启动] | 重新启动失败的批次 | 主色样式 (primary 蓝色) |
| [查看结果] | 查看部分完成的结果 | 默认样式 (info 蓝色) |
| [删除] | DELETE /batch/{id} - 完全删除目录 | 危险样式 (danger 红色) |

**按钮宽度**: 每个按钮 33.333% (3个按钮均分)

---

## 按钮宽度分配规则

批次卡片中的按钮宽度通过 CSS `flex-basis` 自动计算，根据按钮数量动态分配：

### 宽度计算公式

| 按钮数量 | 宽度计算公式 | 每个按钮宽度 | 使用场景 |
|---------|-------------|------------|---------|
| 1 个 | - | 自动宽度 | 待运行状态 |
| 2 个 | `calc(50% - 4px)` | ~50% | 运行中状态 |
| 3 个 | `calc(33.333% - 5.33px)` | ~33.333% | 已取消、已完成状态 |

### CSS 实现

```css
/* 基础：4个按钮情况 */
.batch-card-actions .btn-small {
    flex: 1 1 auto;
    flex-basis: calc(25% - 6px);
}

/* 2个按钮情况 */
.batch-card-actions:has(.btn-small:nth-child(1)):has(.btn-small:nth-child(2)):not(:has(.btn-small:nth-child(3))) .btn-small {
    flex-basis: calc(50% - 4px);
}

/* 3个按钮情况 */
.batch-card-actions:has(.btn-small:nth-child(1)):has(.btn-small:nth-child(2)):has(.btn-small:nth-child(3)):not(:has(.btn-small:nth-child(4))) .btn-small {
    flex-basis: calc(33.333% - 5.33px);
}
```

**优点**:
- ✅ 自动适应按钮数量
- ✅ 所有按钮在一行显示（不换行）
- ✅ 按钮间距均匀（8px gap）
- ✅ 响应式设计（小屏幕自动调整）

---

## 按钮样式

### 主色按钮 (Primary) - 蓝色
- **CSS 类**: `.btn-small.btn-primary`
- **用途**: 主要操作（启动仿真）
- **默认样式**: 蓝色背景 (#005a9c) + 白色文字
- **Hover 效果**: 渐变背景 + 阴影提升

```css
.btn-small.btn-primary {
    background: var(--color-primary);  /* #005a9c */
    color: white;
    font-weight: 600;
}

.btn-small.btn-primary:hover {
    background: linear-gradient(135deg, #005a9c 0%, #1a5fa0 100%);
    box-shadow: 0 2px 8px rgba(0, 90, 156, 0.3);
}
```

### 默认按钮 (Info) - 蓝色边框
- **CSS 类**: `.btn-small` (无额外类名)
- **用途**: 次级操作（查看进度、查看结果）
- **默认样式**: 白色背景 + 蓝色边框
- **Hover 效果**: 蓝色背景 + 白色文字

```css
.btn-small {
    background: white;
    color: var(--color-info);  /* 蓝色 */
    border: 1px solid var(--color-border);
}

.btn-small:hover {
    background: var(--color-info);
    color: white;
    transform: translateY(-1px);
}
```

### 危险按钮 (Danger) - 红色
- **CSS 类**: `.btn-small.btn-danger`
- **用途**: 危险操作（取消、删除）
- **默认样式**: 白色背景 + 红色边框
- **Hover 效果**: 红色背景 + 白色文字

```css
.btn-small.btn-danger {
    color: var(--color-danger);  /* 红色 */
    border-color: var(--color-danger);
}

.btn-small.btn-danger:hover {
    background: var(--color-danger);
    color: white;
    box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}
```

---

## 卡片结构与布局

### HTML 结构

```html
<div class="batch-history-card">
    <!-- 卡片头部：标题和状态徽章 -->
    <div class="batch-card-header">
        <h4>batch_001_2025-01-15_10_30</h4>
        <span class="batch-status running">运行中</span>
    </div>

    <!-- 卡片信息：统计和时间数据 -->
    <div class="batch-card-info">
        <p><strong>方案数:</strong> 5</p>
        <p><strong>总任务:</strong> 50</p>
        <p><strong>创建时间:</strong> 2025-01-15 10:30:00</p>
        <p><strong>耗时:</strong> 2 分钟 30 秒</p>
        <p><strong>成功率:</strong> 48%</p>
    </div>

    <!-- 卡片操作：按钮行 -->
    <div class="batch-card-actions">
        <button class="btn btn-small" onclick="loadBatchProgressAndSwitch('...')">监控进度</button>
        <button class="btn btn-small btn-danger" onclick="cancelBatchById('...')">取消</button>
    </div>
</div>
```

### CSS 布局

```css
.batch-history-card {
    display: flex;
    flex-direction: column;
    padding: 12px 14px;  /* 紧凑间距 */
}

.batch-card-header {
    margin-bottom: 8px;
    display: flex;
    gap: 8px;
}

.batch-card-info {
    margin-bottom: 8px;
    flex: 1;  /* 自动占用空间 */
}

.batch-card-actions {
    display: flex;
    gap: 8px;
    flex-wrap: nowrap;  /* 禁止换行 */
}
```

---

## API 端点映射

| 按钮 | API 端点 | 方法 | 说明 |
|------|---------|------|------|
| [监控进度] | `/api/v1/control/batch-optimization/batch/{batch_id}/progress` | GET | 获取实时进度数据 |
| [取消] | `/api/v1/control/batch-optimization/batch/{batch_id}/cancel` | POST | 取消运行中的批次 |
| [启动仿真] | `/api/v1/control/batch-optimization/batch/{batch_id}/start` | POST | 启动待运行或已取消的批次 |
| [查看结果] | `/api/v1/control/batch-optimization/batch/{batch_id}/results` | GET | 获取仿真结果 |
| [删除] | `/api/v1/control/batch-optimization/batch/{batch_id}` | DELETE | 删除批次及其目录 |
| [查看进度] | `/api/v1/control/batch-optimization/batch/{batch_id}/progress` | GET | 查看已完成批次的进度历史 |

---

## 响应式设计

### 桌面版 (≥768px)
- 按钮高度: 28px (padding: 6px 12px)
- 字体大小: 0.75rem
- 间距: 8px
- 状态徽章: 完整显示

### 平板/移动版 (<768px)
- 按钮高度: 26px (padding: 5px 8px)
- 字体大小: 0.7rem
- 间距: 6px
- 按钮文字可能缩写或省略号截断

```css
@media (max-width: 768px) {
    .btn-small {
        padding: 5px 8px;
        font-size: 0.7rem;
    }

    .batch-card-actions {
        gap: 6px;
    }
}
```

---

## JavaScript 按钮生成逻辑

```javascript
// 文件: frontend/control/js/batch_simulation.js
// 行数: 1441-1464

<div class="batch-card-actions">
    // 运行中状态：[监控进度] [取消]
    ${batch.status === 'running' ? `
        <button class="btn btn-small" onclick="loadBatchProgressAndSwitch('${batch.batch_id}')">监控进度</button>
        <button class="btn btn-small btn-danger" onclick="cancelBatchById('${batch.batch_id}')">取消</button>
    ` : ''}

    // 已取消状态：[启动仿真] [查看结果] [删除]
    ${batch.status === 'cancelled' ? `
        <button class="btn btn-small btn-primary" onclick="startBatchById('${batch.batch_id}')">启动仿真</button>
        <button class="btn btn-small" onclick="loadBatchResultsAndSwitch('${batch.batch_id}')">查看结果</button>
        <button class="btn btn-small btn-danger" onclick="deleteBatchHistory('${batch.batch_id}')">删除</button>
    ` : ''}

    // 已完成状态：[查看进度] [查看结果] [删除]
    ${batch.status === 'completed' ? `
        <button class="btn btn-small" onclick="loadBatchProgressAndSwitch('${batch.batch_id}')">查看进度</button>
        <button class="btn btn-small" onclick="loadBatchResultsAndSwitch('${batch.batch_id}')">查看结果</button>
        <button class="btn btn-small btn-danger" onclick="deleteBatchHistory('${batch.batch_id}')">删除</button>
    ` : ''}

    // 失败状态：[重新启动] [查看结果] [删除]
    ${batch.status === 'failed' ? `
        <button class="btn btn-small btn-primary" onclick="startBatchById('${batch.batch_id}')">重新启动</button>
        <button class="btn btn-small" onclick="loadBatchResultsAndSwitch('${batch.batch_id}')">查看结果</button>
        <button class="btn btn-small btn-danger" onclick="deleteBatchHistory('${batch.batch_id}')">删除</button>
    ` : ''}

    // 待运行状态：[启动仿真]
    ${batch.status === 'pending' ? `
        <button class="btn btn-small btn-primary" onclick="startBatchById('${batch.batch_id}')">启动仿真</button>
    ` : ''}
</div>
```

---

## 总结表

### 状态与按钮映射表

| 批次状态 | 徽章颜色 | 按钮配置 | 功能说明 |
|---------|---------|---------|---------|
| **运行中** (running) | 蓝色 (#d1ecf1) | [监控进度] [取消] | 实时监控 + 取消选项 |
| **已取消** (cancelled) | 红色 (error-bg) | [启动仿真] [查看结果] [删除] | 允许重启 + 查看结果 + 清理 |
| **已完成** (completed) | 绿色 (#d4edda) | [查看进度] [查看结果] [删除] | 历史回顾 + 结果查看 + 清理 |
| **失败** (failed) | 红色 (error-bg) | [重新启动] [查看结果] [删除] | 允许重试 + 查看部分结果 + 清理 |
| **待运行** (pending) | 黄色 (alert-bg) | [启动仿真] | 单一启动操作 |

---

## 最佳实践

### 设计原则
✅ **一行显示** - 所有按钮在卡片内一行显示，不换行
✅ **自适应宽度** - 根据按钮数量自动调整百分比宽度
✅ **明确的视觉层级** - 主操作(Primary) > 次操作(Info) > 危险操作(Danger)
✅ **响应式** - 在小屏幕上自动缩小按钮和文字

### 按钮命名
✅ **动词开头** - [监控进度] [取消] [查看结果]（清晰的操作意图）
✅ **简洁** - 避免超过3个汉字的按钮名称
✅ **一致性** - 相同功能使用相同按钮名（如"查看"系列）

### 文件位置
- **HTML**: `frontend/control/simulations.html` (第89-193行)
- **CSS**: `frontend/control/css/simulations.css` (第617-802行)
- **JavaScript**: `frontend/control/js/batch_simulation.js` (第1428-1462行)

---

## 版本历史

| 版本 | 日期 | 更改 |
|------|------|------|
| v1.0 | 2025-01-15 | 初版：4个状态，按钮宽度百分比分配，响应式设计 |

---

*文档最后更新: 2025-01-15*
