# Phase 2 实现验证清单

**用途**: 在实现过程中逐项验证前后端的正确集成
**检查频率**: 完成每个模块后立即检查
**责任**: 前端开发 + 后端开发 + QA

---

## 一、API 端点验证

### 1.1 进度监控端点

#### `/api/v1/simulation/simulation_progress/{case_id}` (GET)

**后端验证**:
- [ ] 端点存在且可调用
- [ ] 响应状态码为 200
- [ ] 响应时间 < 2 秒
- [ ] 返回字段完整：
  - [ ] case_id (string)
  - [ ] total_simulations (int)
  - [ ] completed (int)
  - [ ] running (int)
  - [ ] failed (int)
  - [ ] created (int)
  - [ ] progress_percentage (float, 0-100)
  - [ ] simulations (array)
    - [ ] simulation_id
    - [ ] status (completed|running|failed|created)
    - [ ] progress (int, 0-100)
    - [ ] started_at (ISO 8601)
    - [ ] completed_at (ISO 8601)
    - [ ] duration (string)

**前端验证**:
- [ ] 能正确解析响应 JSON
- [ ] 每 10 秒刷新一次（展开状态）
- [ ] 每 30 秒刷新一次（折叠状态）
- [ ] 进度条宽度 = progress_percentage
- [ ] 统计卡片数字正确：
  - [ ] 总数 = completed + running + failed + created
  - [ ] 完成数 = completed
  - [ ] 运行中 = running
  - [ ] 失败 = failed

**测试 curl**:
```bash
curl -X GET "http://localhost:8000/api/v1/simulation/simulation_progress/case_20251112_001" \
  -H "Content-Type: application/json"
```

---

#### `/api/v1/simulation/simulations/{case_id}` (GET)

**后端验证**:
- [ ] 端点存在且可调用
- [ ] 返回 simulations 数组
- [ ] 每个仿真包含：
  - [ ] simulation_id
  - [ ] case_id
  - [ ] status
  - [ ] scenario_name
  - [ ] control_strategy
  - [ ] created_at
  - [ ] updated_at

**前端验证**:
- [ ] 页面初始化时调用
- [ ] 表格正确显示仿真列表
- [ ] 状态值正确显示颜色

---

### 1.2 对比分析端点

#### `/api/v1/analysis/results/{batch_id}` (GET)

**后端验证**:
- [ ] 端点存在且可调用
- [ ] 支持 ?case_id 查询参数
- [ ] 返回聚合的指标数据：
  - [ ] summary (对象)
  - [ ] metrics (数组，每个包含 metric_name, values, average, min, max)
  - [ ] edgedata_metrics (数组)

**前端验证**:
- [ ] 对比分析标签页能加载数据
- [ ] 指标卡片正确显示

**测试 curl**:
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/results/batch_20251112_100000?case_id=case_20251112_001"
```

---

#### `/api/v1/analysis/comparison/{batch_id}` (GET)

**后端验证**:
- [ ] 端点存在且可调用
- [ ] 支持 ?case_id 查询参数
- [ ] 返回对比表格：
  - [ ] comparison_table (数组)
    - [ ] metric_name
    - [ ] case_a_value
    - [ ] case_b_value
    - [ ] difference (数值)
    - [ ] difference_percentage (浮点数)
    - [ ] improvement (positive|negative|neutral)
  - [ ] ranking (数组)

**前端验证**:
- [ ] 对比表格正确渲染
- [ ] 差异百分比显示正确
- [ ] 改善/恶化标签颜色正确：
  - [ ] 绿色 = positive (改善)
  - [ ] 红色 = negative (恶化)
  - [ ] 灰色 = neutral (无显著变化)
- [ ] 差异 > 10% 的行高亮显示

**测试 curl**:
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/comparison/batch_20251112_100000?case_id=case_20251112_001"
```

---

#### `/api/v1/simulation/batch-start` (POST)

**后端验证**:
- [ ] 端点存在且可调用
- [ ] 接收请求体：
  - [ ] simulation_ids (数组)
  - [ ] case_id (字符串)
  - [ ] parallel_workers (整数, 可选)
  - [ ] auto_run_analysis (布尔, 可选)
  - [ ] analysis_types (数组, 可选)
- [ ] 返回：
  - [ ] batch_id
  - [ ] total_simulations
  - [ ] status
  - [ ] started_at

**前端验证**:
- [ ] 批量启动确认对话框显示正确
- [ ] 点击启动后调用此 API
- [ ] 接收返回的 batch_id 并保存

**测试 curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/simulation/batch-start" \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_ids": ["sim_001", "sim_002"],
    "case_id": "case_20251112_001",
    "parallel_workers": 4,
    "auto_run_analysis": true
  }'
```

---

## 二、前端功能验证

### 2.1 进度监控面板

#### 展开/折叠功能
- [ ] 默认折叠状态
- [ ] 点击按钮展开（动画平滑，约 300ms）
- [ ] 点击按钮折叠（动画平滑，约 300ms）
- [ ] 展开/折叠时无页面抖动或闪烁
- [ ] 状态保存到 localStorage（可选）

#### 统计卡片
- [ ] 显示 4 个卡片：总计、已完成、运行中、失败
- [ ] 数字实时更新
- [ ] 颜色正确：
  - [ ] 已完成 = 绿色
  - [ ] 运行中 = 蓝色
  - [ ] 失败 = 红色

#### 进度条
- [ ] 显示百分比（0-100%）
- [ ] 宽度随百分比变化（平滑）
- [ ] 文字显示正确（如 "45% 完成"）

#### 详细表格（展开状态）
- [ ] 显示所有列：仿真ID、案例、状态、进度、时间、操作
- [ ] 可按列排序（点击表头）
- [ ] 可按状态筛选（下拉菜单）
- [ ] 可搜索仿真 ID（搜索框）
- [ ] 每行有"查看分析"按钮
  - [ ] 仿真完成时按钮启用
  - [ ] 仿真未完成时按钮禁用（灰显）
  - [ ] 点击时跳转到 analysis_viewer.html?case_id=...&simulation_id=...

#### 刷新频率
- [ ] 展开时：5-10 秒刷新一次
- [ ] 折叠时：30 秒刷新一次
- [ ] 切换展开/折叠时立即调整刷新频率
- [ ] 所有仿真完成时停止刷新

---

### 2.2 对比分析标签页

#### 标签页加载
- [ ] "对比分析" 标签页存在
- [ ] 点击可切换到对比分析视图
- [ ] 初始状态显示"请选择至少 2 个案例进行对比"

#### 案例选择器
- [ ] 存在"选择案例"按钮
- [ ] 点击弹出模态框
- [ ] 显示所有可用案例列表
- [ ] 每个案例显示：ID、名称、场景
- [ ] 支持多选（复选框）
- [ ] 底部显示"已选择 X 个案例"
- [ ] "确认对比"按钮：
  - [ ] 选中 < 2 个时禁用
  - [ ] 选中 ≥ 2 个时启用
  - [ ] 点击时加载对比数据

#### 对比表格
- [ ] 显示多案例指标卡片（顶部）
- [ ] 显示对比表格：指标名称 | 案例A | 案例B | 差异 | 改善
- [ ] 差异百分比计算正确：`(B-A)/A*100`
- [ ] 颜色标记：
  - [ ] 绿色 = improvement: "positive"
  - [ ] 红色 = improvement: "negative"
  - [ ] 灰色 = improvement: "neutral"
- [ ] 差异 > 10% 的行高亮显示
- [ ] 表格可水平滚动（移动设备）

#### URL 参数支持
- [ ] URL 格式：`?case_ids=case1,case2,case3`
- [ ] 用户可复制 URL 分享
- [ ] 他人打开 URL 时自动加载对比结果

---

### 2.3 响应式设计

#### 移动设备 (<768px)
- [ ] 指标卡片单列显示
- [ ] 表格可水平滚动
- [ ] 表格不截断内容
- [ ] 按钮高度 ≥ 44px
- [ ] 按钮间距 ≥ 8px
- [ ] 字体大小 ≥ 12px

#### 平板设备 (768-1199px)
- [ ] 指标卡片 2 列显示
- [ ] 表格列宽优化，减少滚动
- [ ] 内容清晰可读

#### 桌面设备 (≥1200px)
- [ ] 指标卡片 4 列显示
- [ ] 表格充分显示，无需滚动
- [ ] 字体大小 14-16px
- [ ] 行高 1.5-1.6

#### 响应式断点
- [ ] 所有 @media 查询使用标准断点：
  - [ ] Mobile: max-width 767px
  - [ ] Tablet: 768px-1199px
  - [ ] Desktop: min-width 1200px
- [ ] 在各断点切换时无布局抖动

---

## 三、批次 ID 正确性验证

### 3.1 事件批次工作流

- [ ] 使用 `/api/batch/create-from-event` 创建批次
- [ ] 返回的 batch_id 格式：`batch_event_XXXXXXX_...`
- [ ] 保存 batch_id 和 case_ids
- [ ] 使用 `/api/batch/start-batch` 启动（仅传递 batch_id）
- [ ] 进度查询用 case_id：`/api/v1/simulation/simulation_progress/{case_id}`
- [ ] 对比分析用 batch_id：`/api/v1/analysis/comparison/{batch_id}`

### 3.2 优化批次工作流

- [ ] 使用 `/api/v1/simulation/batch-start` 启动（传递 simulation_ids）
- [ ] 返回的 batch_id 格式：`batch_YYYYMMDD_...`
- [ ] 进度查询用 case_id（不用 batch_id）
- [ ] 对比分析用 batch_id

### 3.3 避免错误

- [ ] ❌ 不混淆 simulation_ids 和 batch_id
- [ ] ❌ 不在事件批次启动时传递 simulation_ids
- [ ] ❌ 不用 batch_id 替代 case_id 查询进度
- [ ] ❌ 不用 simulation_ids 列表查询对比分析

---

## 四、数据准确性验证

### 4.1 进度计算

测试数据：
```
总仿真: 10
已完成: 3
运行中: 2
失败: 0
已创建: 5
```

验证：
- [ ] total_simulations = 3 + 2 + 0 + 5 = 10 ✓
- [ ] progress_percentage = (3 + 0) / 10 * 100 = 30% ✓
- [ ] 或 progress_percentage = (3 + 2*0.5) / 10 * 100 = 35% (如果计算中包括运行中) ✓

### 4.2 差异计算

测试数据：
```
指标: 平均行程时间
案例A值: 25.3 分钟
案例B值: 23.1 分钟
```

验证：
- [ ] difference = 23.1 - 25.3 = -2.2
- [ ] difference_percentage = (-2.2 / 25.3) * 100 = -8.7%
- [ ] improvement = "positive" (因为时间减少是改善) ✓

### 4.3 改善趋势判断

根据指标定义：
- [ ] 时间类：越少越好 (negative percentage = positive)
- [ ] 速度类：越快越好 (positive percentage = positive)
- [ ] 流量类：可能需要具体定义
- [ ] 拥堵类：越少越好

验证：
- [ ] 改善/恶化标签与指标定义一致

---

## 五、性能验证

### 5.1 API 响应时间

| 端点 | 目标 | 实际 | 是否合格 |
|------|------|------|---------|
| `/api/v1/simulation/simulation_progress/{case_id}` | <2s | ___ms | [ ] |
| `/api/v1/analysis/comparison/{batch_id}` | <2s | ___ms | [ ] |
| `/api/v1/analysis/results/{batch_id}` | <2s | ___ms | [ ] |

### 5.2 前端性能

- [ ] 展开/折叠动画无卡顿（60fps）
- [ ] 表格排序/筛选响应速度 < 500ms
- [ ] 页面初始加载时间 < 3s

### 5.3 内存泄漏检查

- [ ] 浏览器控制台无内存持续增长
- [ ] 长时间运行（30分钟以上）无崩溃
- [ ] setInterval 定时器在页面卸载时清除

---

## 六、浏览器兼容性验证

- [ ] Chrome (最新版)
- [ ] Firefox (最新版)
- [ ] Edge (最新版)
- [ ] Safari (最新版，如可用)

验证项：
- [ ] 界面显示正常
- [ ] 功能正常工作
- [ ] 无 JavaScript 错误
- [ ] CSS 样式正确

---

## 七、集成测试场景

### 场景 1：完整的批次仿真流程

```
1. 打开 case-simulation-center.html
   [ ] 页面加载成功
   [ ] 仿真列表显示

2. 选择多个仿真 + 批量启动
   [ ] 确认对话框显示
   [ ] 点击启动
   [ ] 接收 batch_id
   [ ] 监控面板自动展开

3. 监控面板实时刷新
   [ ] 统计卡片更新
   [ ] 进度条增长
   [ ] 表格行更新

4. 仿真完成，点击"查看分析"
   [ ] 跳转到 analysis_viewer.html
   [ ] URL 包含 case_id 和 simulation_id
   [ ] 分析页面加载数据

5. 在分析页面选择对比分析
   [ ] 选择多个案例
   [ ] 显示对比表格
   [ ] 差异颜色正确
```

### 场景 2：从事件创建批次

```
1. 使用 /api/batch/create-from-event 创建批次
   [ ] 返回 batch_id 和 case_ids

2. 使用 /api/batch/start-batch 启动
   [ ] 仅传递 batch_id（不传 simulation_ids）

3. 查询进度
   [ ] 用 case_id 查询进度

4. 查询对比
   [ ] 用 batch_id 查询对比报告
```

---

## 八、问题记录表

| 日期 | 模块 | 问题 | 状态 | 处理 |
|------|------|------|------|------|
| 2025-11-17 | 进度监控 | 刷新频率不对 | 待修复 | 检查 setInterval |
| 2025-11-17 | 对比分析 | 差异计算错误 | 待修复 | 检查后端公式 |
| | | | | |

---

## 九、最终签核

| 角色 | 姓名 | 日期 | 签名 |
|------|------|------|------|
| 前端开发 | | | |
| 后端开发 | | | |
| QA | | | |
| PM | | | |

---

**打印版本**: 建议打印此清单并在办公室显眼位置贴放
**更新频率**: 每周一次
**最后更新**: 2025-11-16
