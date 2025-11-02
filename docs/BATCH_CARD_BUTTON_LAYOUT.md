# 批次卡片按钮布局速查表

## 快速参考

| 批次状态 | 按钮数量 | 按钮列表 | 宽度分配 | 每按钮宽度 |
|---------|---------|---------|---------|----------|
| 🔄 运行中 (running) | 2 | [监控进度] [取消] | 50% | 50% - 4px |
| ⏸️ 已取消 (cancelled) | 3 | [启动仿真] [查看结果] [删除] | 33.333% | ~33% - 5.33px |
| ✅ 已完成 (completed) | 3 | [查看进度] [查看结果] [删除] | 33.333% | ~33% - 5.33px |
| ❌ 失败 (failed) | 3 | [重新启动] [查看结果] [删除] | 33.333% | ~33% - 5.33px |
| ⏳ 待运行 (pending) | 1 | [启动仿真] | 自动 | 自动宽度 |

---

## 按钮功能映射

### 监控/查看类按钮
| 按钮名称 | 调用函数 | API 端点 | 适用状态 |
|---------|--------|---------|---------|
| [监控进度] | `loadBatchProgressAndSwitch()` | GET `/batch/{id}/progress` | running |
| [查看进度] | `loadBatchProgressAndSwitch()` | GET `/batch/{id}/progress` | completed |
| [查看结果] | `loadBatchResultsAndSwitch()` | GET `/batch/{id}/results` | cancelled, completed, failed |

### 操作类按钮
| 按钮名称 | 调用函数 | API 端点 | 适用状态 |
|---------|--------|---------|---------|
| [启动仿真] | `startBatchById()` | POST `/batch/{id}/start` | pending |
| [重新启动] | `startBatchById()` | POST `/batch/{id}/start` | failed, cancelled |
| [取消] | `cancelBatchById()` | POST `/batch/{id}/cancel` | running |
| [删除] | `deleteBatchHistory()` | DELETE `/batch/{id}` | cancelled, completed, failed |

---

## 样式快速参考

### 按钮 CSS 类
```css
/* 主色按钮 - 启动/重新启动操作 */
.btn-small.btn-primary

/* 默认按钮 - 查看/监控操作 */
.btn-small (无额外类)

/* 危险按钮 - 取消/删除操作 */
.btn-small.btn-danger
```

### 状态徽章 CSS 类
```css
.batch-status.pending      /* 黄色背景 */
.batch-status.running      /* 蓝色背景 */
.batch-status.completed    /* 绿色背景 */
.batch-status.cancelled    /* 红色背景 */
.batch-status.failed       /* 红色背景 */
```

---

## 按钮宽度分配公式

### CSS Flexbox 计算

```css
/* 基础（4个按钮情况） */
flex-basis: calc(25% - 6px);
max-width: 140px;

/* 2个按钮情况 */
.batch-card-actions:has(.btn-small:nth-child(1)):has(.btn-small:nth-child(2)):not(:has(.btn-small:nth-child(3))) .btn-small {
    flex-basis: calc(50% - 4px);
}

/* 3个按钮情况 */
.batch-card-actions:has(.btn-small:nth-child(1)):has(.btn-small:nth-child(2)):has(.btn-small:nth-child(3)):not(:has(.btn-small:nth-child(4))) .btn-small {
    flex-basis: calc(33.333% - 5.33px);
}
```

### 实际宽度示例（卡片宽度 300px，间距 8px）

#### 2个按钮（运行中）
```
[    监控进度 (145px)    ] [8px] [    取消 (147px)    ]
```

#### 3个按钮（已取消/已完成/失败）
```
[启动仿真(95px)] [8px] [查看结果(95px)] [8px] [删除(97px)]
```

#### 1个按钮（待运行）
```
[         启动仿真 (自动宽度)          ]
```

---

## 响应式设计

### 桌面版 (≥768px)
- 按钮高度: 28px
- 按钮内边距: 6px 12px
- 字体大小: 0.75rem
- 间距: 8px

### 平板/移动版 (<768px)
- 按钮高度: 26px
- 按钮内边距: 5px 8px
- 字体大小: 0.7rem
- 间距: 6px

---

## 关键实现文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `frontend/control/js/batch_simulation.js` | 1441-1464 | 按钮生成逻辑 |
| `frontend/control/css/simulations.css` | 617-802 | 按钮和卡片样式 |
| `api/models/enums.py` | 39-45 | BatchSimulationStatus 枚举 |
| `docs/BATCH_CARD_UI_DESIGN.md` | - | 完整 UI 设计文档 |

---

## 开发检查清单

按钮功能实现时：
- [ ] 确认按钮在正确的状态下显示
- [ ] 验证按钮调用的 API 端点正确
- [ ] 检查按钮样式（primary/info/danger）符合设计
- [ ] 确保按钮文字简洁（≤4 汉字）
- [ ] 测试按钮在各种屏幕宽度下的显示效果
- [ ] 确认按钮不会换行（flex-wrap: nowrap）

---

## 常见问题

### Q: 为什么按钮有时会缩小或显示省略号？
A: 这是正常的响应式行为。当屏幕宽度小于卡片宽度时，按钮会自动缩小。如果文字过长，会显示省略号（text-overflow: ellipsis）。

### Q: 如何添加新的按钮？
A:
1. 在 JavaScript 中的对应状态条件下添加新 `<button>` 元素
2. 给按钮添加适当的 CSS 类（`.btn-small`, `.btn-primary`, `.btn-danger`）
3. 设置 `onclick` 事件处理函数
4. 更新 CSS 的 `:has()` 选择器来匹配新的按钮数量（如需要）

### Q: 为什么我的按钮看不清文字？
A: 检查：
1. 按钮宽度是否过窄（考虑增加卡片宽度或减少按钮数量）
2. 文字是否超过按钮容量（简化按钮标签）
3. 屏幕分辨率是否太低（响应式设计在小屏幕上会缩小）

---

## 版本历史

| 版本 | 日期 | 更改 |
|------|------|------|
| v1.0 | 2025-01-15 | 初版：5个状态，按钮宽度百分比分配，速查表 |

---

*最后更新: 2025-01-15*
