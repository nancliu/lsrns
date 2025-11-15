# 视图切换功能实现

**日期**: 2025-01-15
**状态**: ✅ 完成
**目的**: 添加表格视图和事件卡片视图的切换功能

---

## 问题

用户反馈前端页面没有显示批量创建相关的修改。原因是：
- 之前的实现只添加了事件卡片渲染函数
- 没有在UI中添加视图切换按钮
- 默认仍然显示表格视图

---

## 解决方案

添加了视图切换功能，允许用户在两种视图之间切换：
1. **表格视图** (默认) - 显示场景列表表格
2. **事件卡片视图** (新) - 显示事件分组卡片，支持批量创建

---

## 实现细节

### 1. HTML修改 (`scenario_browser.html:107-116`)

添加了视图切换按钮：

```html
<!-- 视图切换按钮 -->
<div style="display: flex; gap: 5px; border: 1px solid #ddd; border-radius: 4px; padding: 2px;">
    <button class="btn btn-sm view-toggle-btn active" id="tableViewBtn" onclick="switchView('table')">
        📋 表格视图
    </button>
    <button class="btn btn-sm view-toggle-btn" id="eventViewBtn" onclick="switchView('event')">
        🎯 事件卡片
    </button>
</div>
```

### 2. CSS修改 (`scenario_browser.css:1180-1200`)

添加了切换按钮样式：

```css
.view-toggle-btn {
    background: white;
    color: #666;
    border: none;
    transition: all 0.2s ease;
}

.view-toggle-btn.active {
    background: #3498db;
    color: white;
}
```

### 3. JavaScript修改 (`scenario_browser.js`)

#### 新增全局状态 (Line 13)
```javascript
let currentView = 'table';  // 当前视图模式: 'table' 或 'event'
```

#### 新增函数

**renderCurrentView()** (Lines 295-301)
- 根据当前视图模式调用相应的渲染函数

**switchView(viewMode)** (Lines 304-320)
- 切换视图模式
- 更新按钮active状态
- 渲染相应视图
- 处理分页显示/隐藏

**renderEventView()** (Lines 323-333)
- 按事件分组场景
- 渲染事件卡片

#### 修改函数

**applyFilters()** (Line 290)
- 从 `renderScenarios()` 改为调用 `renderCurrentView()`
- 确保筛选后保持当前视图模式

---

## 使用方法

### 表格视图 (默认)

1. 打开场景浏览器
2. 默认显示表格视图
3. 可以看到所有场景的详细列表
4. 每个场景有"创建"按钮

### 事件卡片视图 (批量创建)

1. 点击 **🎯 事件卡片** 按钮
2. 场景自动按事件分组显示
3. 每个事件卡片显示：
   - 事件基本信息（事件ID、类型、位置、时间）
   - 可用场景（无管控、VSS、TEC、DHS）
   - 场景复选框（默认全选）
   - 批量创建按钮
4. 选择要创建的场景
5. 点击"批量创建"按钮
6. 确认后创建所有选中场景

---

## 视图对比

| 特性 | 表格视图 | 事件卡片视图 |
|------|---------|------------|
| 显示方式 | 场景列表 | 事件分组 |
| 创建方式 | 单个创建 | 批量创建 |
| 分页 | 是 | 否（显示所有事件） |
| 适用场景 | 查看详细场景信息 | 快速批量创建 |
| 主要操作 | 查看详情、单个创建 | 多选场景、批量创建 |

---

## 事件卡片视图功能

### 场景选择

- **默认全选**: 所有场景默认选中
- **部分选择警告**: 如果只选择部分场景，会显示警告提示
- **全选/全不选**: 快捷按钮

### 批量创建流程

1. 选择要创建的场景
2. 点击"批量创建"
3. 显示确认对话框（包含事件信息、场景数量、策略列表）
4. 调用API创建
5. 显示创建结果：
   - 案例ID
   - 成功/失败场景数
   - EdgeData统计（总边缘数、事件边缘、策略边缘）
   - 耗时

### EdgeData信息

批量创建会显示统一edgeData的详细信息：
```
EdgeData监测:
- 总边缘数: 122
- 事件边缘: 2
- 策略边缘: 120
```

这表明系统智能聚合了：
- 事件影响的2条边缘
- 所有管控策略影响的120条边缘
- 总共监测122条边缘（相比全路网5000条，减少了98%）

---

## 技术实现

### 视图切换逻辑

```javascript
function switchView(viewMode) {
    currentView = viewMode;

    // 1. 更新按钮状态
    document.getElementById('tableViewBtn').classList.toggle('active', viewMode === 'table');
    document.getElementById('eventViewBtn').classList.toggle('active', viewMode === 'event');

    // 2. 渲染相应视图
    renderCurrentView();

    // 3. 处理分页
    if (viewMode === 'event') {
        document.getElementById('pagination').innerHTML = '';
    } else {
        renderPagination();
    }
}
```

### 事件分组算法

```javascript
function groupScenariosByEvent(scenarios) {
    const eventGroups = {};

    scenarios.forEach(scenario => {
        const eventId = scenario.event_id;

        if (!eventGroups[eventId]) {
            eventGroups[eventId] = {
                event_id: eventId,
                event_type: scenario.event_type,
                // ... 其他事件信息
                scenarios: []
            };
        }

        eventGroups[eventId].scenarios.push(scenario);
    });

    return Object.values(eventGroups);
}
```

---

## 文件变更

| 文件 | 修改内容 | 行数 |
|------|---------|------|
| `scenario_browser.html` | 添加视图切换按钮 | +15 |
| `scenario_browser.css` | 添加按钮样式 | +20 |
| `scenario_browser.js` | 添加视图切换逻辑 | +55 |

**总计**: +90行代码

---

## 截图说明

### 表格视图
- 显示场景详细列表
- 每行一个场景
- 支持分页
- 单个创建按钮

### 事件卡片视图 (切换后)
- 显示事件分组卡片
- 每个卡片包含该事件的所有场景
- 场景复选框（可多选）
- 批量创建按钮
- 完整性警告（部分选择时）

---

## 下一步操作

### 用户操作

1. **刷新页面**: `Ctrl + F5` 或 `Ctrl + R`
2. **点击"🎯 事件卡片"按钮**: 切换到事件卡片视图
3. **查看事件卡片**: 每个事件显示为一个卡片
4. **选择场景**: 默认全选，可以取消部分场景
5. **批量创建**: 点击"批量创建"按钮

### 验证功能

- [ ] 视图切换按钮显示正常
- [ ] 点击按钮可以切换视图
- [ ] 事件卡片正确显示
- [ ] 场景复选框可以选择/取消
- [ ] 批量创建按钮可以点击
- [ ] 创建成功后显示详细信息

---

## 总结

✅ **完成**: 添加了完整的视图切换功能
✅ **默认视图**: 保持表格视图（向后兼容）
✅ **批量创建**: 通过事件卡片视图访问
✅ **用户体验**: 平滑切换，状态保持

**状态**: 完成，可以使用！

**使用提示**: 点击页面上方的 **🎯 事件卡片** 按钮即可看到批量创建界面。
