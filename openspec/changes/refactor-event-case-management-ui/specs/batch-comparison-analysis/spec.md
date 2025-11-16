# 批次对比分析 (Batch Comparison Analysis)

支持多个案例的分析对比功能，包括对比标签页、案例选择器、对比表格、多案例指标卡片、快速切换器，以及URL参数和返回导航功能。

**Affected Files**:
- `frontend/scenarios/analysis_viewer.html`
- `frontend/scenarios/css/event-scenario-comparison.css`

---

## ADDED Requirements

### Requirement: 对比分析标签页 - 新增标签页支持多案例对比
The system SHALL implement this requirement.
在现有分析页面添加新的"对比分析"标签页，支持同时查看多个案例的分析结果。

#### Scenario: 打开对比分析标签页

```
Given: 用户在 analysis_viewer.html
When: 用户点击"对比分析"标签页（新增标签）
Then: 页面切换到对比分析视图
And: 显示案例选择器和对比表格容器
And: 提示"请选择至少2个案例进行对比"（初始状态）
```

---

### Requirement: 案例选择器 - 支持多选和确认
The system SHALL implement this requirement.
提供便捷的案例/仿真选择界面，支持单选和多选。

#### Scenario: 打开和使用案例选择器

```
Given: 用户在对比分析标签页
When: 用户点击"选择案例"按钮
Then: 弹出模态框或展开选择面板
And: 显示可用案例列表（当前事件批次的所有案例）
And: 每个案例显示：案例ID、案例名称、场景名称
And: 提供复选框支持多选
And: 底部显示"已选择 X 个案例"
And: "确认对比"按钮在选择 ≥2 个案例时启用，否则禁用
```

---

### Requirement: 对比表格和指标卡片 - 并排显示多案例指标
The system SHALL implement this requirement.
并排显示多个案例的关键指标，支持清晰的数值和差异对比。

#### Scenario: 显示对比结果表格

```
Given: 用户已选择 2 个或更多案例
When: 对比分析加载完成
Then: 在顶部显示多案例指标卡片（并排）
And: 显示对比表格，格式为：
  | 指标名称 | 案例A | 案例B | 差异 | 改善状态 |
  |--------|-------|-------|------|---------|
  | 总车辆数 | 1000 | 1050 | +5.0% | ✗ 恶化 |
  | 平均行程时间 | 25.3分 | 23.1分 | -8.7% | ✓ 改善 |
And: 改善/恶化用颜色表示（绿色改善、红色恶化）
And: 差异 >10% 的行应用背景高亮
```

#### Scenario: 处理缺失数据

```
Given: 某个案例的某项分析数据不可用
When: 对比表格加载时遇到缺失字段
Then: 显示"--"或"N/A"
And: 不中断对比过程，其他数据正常显示
```

---

### Requirement: 案例快速切换器 - 支持快速切换案例
The system SHALL implement this requirement.
在分析页面顶部添加案例选择器，支持快速查看不同案例的详细分析。

#### Scenario: 使用案例下拉菜单快速切换

```
Given: 用户在分析页面任意标签页
When: 页面顶栏显示"选择案例：[下拉菜单]"
Then: 下拉菜单列出当前事件批次的所有案例
And: 用户可点击选择案例
And: 页面数据和所有标签页内容自动更新
And: URL参数自动更新为：?case_id={case_id}&simulation_id={sim_id}
```

---

### Requirement: URL 参数支持 - 便于书签和分享
The system SHALL implement this requirement.
分析页面支持URL参数，便于书签和分享。

#### Scenario: 单案例URL和多案例对比URL

```
Given: 用户浏览分析页面
When: 单案例查看时
Then: URL 格式：analysis_viewer.html?case_id=case123&simulation_id=sim456
When: 多案例对比时
Then: URL 格式：analysis_viewer.html?compare=case1,case2,case3
Or: 格式：analysis_viewer.html?case_ids=case1,case2,case3&event=event_id
And: 用户可复制 URL 分享给他人
And: 他人打开 URL 时，自动加载相同的分析结果
```

---

### Requirement: 返回导航 - 支持返回案例管理和浏览器导航
The system SHALL implement this requirement.
支持从分析页面返回案例管理页面的导航。

#### Scenario: 返回案例管理和浏览器后退

```
Given: 用户从 case-simulation-center 导航到 analysis_viewer
When: 用户点击"返回案例管理"按钮
Then: 返回到 case-simulation-center.html
And: 页面状态恢复（多选状态、滚动位置等，如可能）
When: 用户点击浏览器"后退"按钮
Then: 也应正确返回到 case-simulation-center.html
```

---

## MODIFIED Requirements

### Requirement: 增强响应式设计 - 优化不同屏幕宽度下的表现
The system SHALL implement this requirement.
改进现有分析标签页在不同屏幕宽度下的表现。

#### Scenario: 移动、平板、桌面设备的响应式显示

```
Given: 用户在不同屏幕宽度查看分析结果
When: 宽度 < 768px (移动设备)
Then: 指标卡片单列显示，表格可水平滚动
And: 表格最小宽度 ≥360px，内容不截断
When: 宽度 768px-1199px (平板)
Then: 指标卡片 2 列显示，表格优化列宽
When: 宽度 ≥1200px (桌面)
Then: 指标卡片 4 列显示，充分利用屏幕空间
And: 表格无需水平滚动
```

#### Scenario: 对比表格水平滚动

```
Given: 用户进行多案例对比
When: 表格列数较多，超出屏幕宽度
Then: 表格支持水平滚动
And: 第一列（指标名称）固定不动，便于行识别
And: 用户可轻松对比不同案例的数值
```

---

### Requirement: 数据加载指示 - 显示加载进度
The system SHALL implement this requirement.
对比分析加载大量数据时，提供进度提示。

#### Scenario: 加载中的用户反馈

```
Given: 用户选择多个案例进行对比
When: 系统开始加载分析数据
Then: 显示加载中的动画或进度条
And: 显示"正在加载对比数据..."提示
And: 加载完成后，立即显示对比表格（无闪烁）
```

---

## 验收标准

- [ ] 对比分析标签页可显示，支持案例选择
- [ ] 案例选择器允许多选（2个或以上）
- [ ] 对比表格显示多案例的指标并排对比
- [ ] 差异百分比计算正确，颜色标记清晰（绿改善、红恶化）
- [ ] URL 参数支持多案例（如 ?case_ids=case1,case2,case3）
- [ ] 从 case-simulation-center 点击"查看分析"可正确导航
- [ ] 案例快速切换器功能正常，页面数据实时更新
- [ ] 返回导航正确，浏览器返回按钮有效
- [ ] 移动设备 (<768px) 下表格可水平滚动，无截断
- [ ] API 调用成功，无 404 或超时错误
