# 响应式布局优化 (Responsive Layout Optimization)

优化 analysis_viewer.html 和 case-simulation-center.html 的响应式设计，统一断点定义，优化在移动、平板、桌面等不同屏幕宽度下的表现。

**Affected Files**:
- `frontend/scenarios/analysis_viewer.html`
- `frontend/scenarios/case-simulation-center.html`
- `frontend/scenarios/css/event-scenario-comparison.css`

---

## ADDED Requirements

### Requirement: 标准化响应式断点 - 统一项目的媒体查询断点定义
The system SHALL implement this requirement.
定义和统一项目范围内的响应式断点，确保设计一致性。

#### Scenario: 定义三个标准断点

```
Given: 项目需要支持多种设备类型
When: 定义响应式断点时
Then: 统一使用以下断点：
  - Mobile:     max-width: 767px
  - Tablet:     768px ≤ width ≤ 1199px
  - Desktop:    min-width: 1200px
  - Ultra-wide: min-width: 1920px (可选，超大屏幕优化)
And: 所有 @media 查询使用上述标准断点
And: 在 CSS 中添加注释说明各断点的目的
```

---

### Requirement: 移动设备视图优化 - 在小屏幕上确保内容易读易操作
The system SHALL implement this requirement.
在移动设备（<768px）上优化布局，确保内容易读易操作。

#### Scenario: 移动设备的指标卡片和表格显示

```
Given: 用户在宽度 ≤767px 的移动设备上
When: 查看分析页面或监控面板
Then: 指标卡片改为单列显示（不是网格）
And: 每个卡片占满屏幕宽度，padding 10-15px
And: 内容清晰可读，字体大小 ≥12px
And: 数据表格可水平滚动（不截断列）
And: 表格最小宽度 ≥360px
```

#### Scenario: 移动设备的操作按钮

```
Given: 用户在移动设备上
When: 查看操作按钮（如"查看分析"、"批量启动"）
Then: 按钮高度 ≥44px（符合移动端可触控规范）
And: 按钮间距 ≥8px（防止误触）
And: 多个按钮若超过一行，改为竖排显示
And: 按钮宽度至少 80px 或自适应容器宽度
```

---

### Requirement: 平板设备视图优化 - 充分利用中等屏幕空间
The system SHALL implement this requirement.
在平板设备（768px-1199px）上优化布局。

#### Scenario: 平板设备的指标卡片和表格显示

```
Given: 用户在宽度 768px-1199px 的平板上
When: 查看分析页面
Then: 指标卡片显示为 2 列网格
And: 每列占 50% 宽度，间距 15-20px
And: 数据表格优化列宽，减少必须的水平滚动
And: 关键列（ID、名称、状态）保持充足宽度
And: 内容清晰可读
```

---

### Requirement: 桌面设备视图优化 - 充分利用大屏幕空间
The system SHALL implement this requirement.
在桌面设备（≥1200px）上充分利用屏幕空间。

#### Scenario: 桌面设备的最优布局

```
Given: 用户在宽度 ≥1200px 的桌面上
When: 查看分析页面或监控面板
Then: 指标卡片显示为 4 列网格
And: 每列占 25% 宽度，间距 20-30px
And: 数据表格宽度 = 容器宽度 - padding
And: 所有列都可见（无需水平滚动）
And: 文字大小 14-16px，行高 1.5-1.6，阅读舒适
```

---

### Requirement: 表格水平滚动和固定列 - 优化大表格在小屏幕的显示
The system SHALL implement this requirement.
处理表格在不同屏幕宽度下的水平滚动问题。

#### Scenario: 表格水平滚动支持

```
Given: 用户在移动或平板设备查看数据表格
When: 表格列数较多，超出屏幕宽度
Then: 表格支持水平滚动（不截断内容）
And: 滚动条样式美观，不影响阅读
And: 考虑固定第一列（关键标识符），其他列可滚动
```

---

### Requirement: 字体和间距响应式调整 - 优化可读性和美观度
The system SHALL implement this requirement.
根据屏幕大小调整字体大小和间距。

#### Scenario: 字体大小和行高响应式

```
Given: 用户在不同屏幕宽度
When: 页面渲染文字时
Then: 根据设备类型调整：
  Mobile:  font-size 12-14px,  line-height 1.4
  Tablet:  font-size 13-15px,  line-height 1.5
  Desktop: font-size 14-16px,  line-height 1.6
And: 所有文字可读（最小 11px）
```

#### Scenario: 间距响应式

```
Given: 用户在不同屏幕宽度
When: 页面渲染时
Then: 根据设备类型调整间距：
  Mobile:  padding 10-15px, margin 10-15px, gap 8-10px
  Tablet:  padding 15-20px, margin 15-20px, gap 12-15px
  Desktop: padding 20-30px, margin 20-30px, gap 15-20px
And: 布局不拥挤，视觉平衡
```

---

### Requirement: 侧栏和顶栏响应式 - 优化导航在小屏幕上的显示
The system SHALL implement this requirement.
侧栏和顶栏应在不同屏幕宽度下优雅地调整。

#### Scenario: 侧栏和顶栏的屏幕宽度适配

```
Given: 用户在不同设备使用分析页面
When: 宽度 < 768px (移动)
Then: 侧栏隐藏或改为汉堡菜单式（点击展开）
And: 内容区域占满屏幕宽度
When: 宽度 ≥ 768px
Then: 侧栏正常显示（或保持固定宽度）
And: 内容区域自适应剩余宽度
```

---

### Requirement: 图表响应式处理 - 优化分析图表在不同屏幕的显示
The system SHALL implement this requirement.
分析页面中的图表应响应式显示。

#### Scenario: 图表大小响应式

```
Given: 用户在不同屏幕宽度查看分析图表
When: 图表加载时
Then: 图表宽度 = 容器宽度（100%）
And: 图表高度根据屏幕大小调整：
  Mobile:   min-height 200px
  Tablet:   min-height 300px
  Desktop:  min-height 400px
And: 内容清晰，无过度缩放导致的模糊
```

---

### Requirement: 展开/折叠面板响应式 - 监控面板在小屏幕上的优化
The system SHALL implement this requirement.
监控面板的展开/折叠式在各屏幕宽度下正常工作。

#### Scenario: 监控面板在移动设备上的显示

```
Given: 用户在移动设备上，监控面板展开
When: 展开式监控显示详细表格
Then: 表格改为卡片式显示（Mobile Table View）
Or: 表格可水平滚动，关键列固定
And: 用户可轻松操作，无需过度滚动
```

---

## MODIFIED Requirements

### Requirement: 统一现有媒体查询 - 审查和更新项目中的所有 @media 查询
The system SHALL implement this requirement.
项目中的现有 @media 查询应统一到标准断点定义。

#### Scenario: 审查和更新现有断点

```
Given: 项目中存在各种 @media 查询断点（可能是 1024px, 1366px 等）
When: 进行响应式优化时
Then: 审查所有现有断点
And: 将非标准断点（如 1024px）更新为标准断点
And: 确保层级关系清晰：
  - 基础样式（Mobile first）
  - @media (min-width: 768px) { ... }  /* Tablet */
  - @media (min-width: 1200px) { ... } /* Desktop */
  - @media (min-width: 1920px) { ... } /* Ultra-wide */
And: 移除重复的媒体查询
```

---

## 验收标准

- [ ] 所有 @media 查询使用统一的断点（768px, 1200px, 1920px）
- [ ] 移动设备 (<768px)：指标单列、表格可滚动、按钮可触及
- [ ] 平板设备 (768-1199px)：指标双列、表格优化
- [ ] 桌面设备 (≥1200px)：指标四列、充分利用空间
- [ ] 字体大小在所有设备上可读（最小 11px）
- [ ] 按钮高度在移动设备上 ≥44px
- [ ] 无横向滚动导致的内容截断（除可控的表格滚动外）
- [ ] 在断点切换时无布局抖动或闪烁
- [ ] 在 Chrome DevTools 各设备模拟中正常显示
- [ ] 在实际设备（iPhone、iPad、Android）上正常显示
