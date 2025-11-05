# 两层结果分析架构 (Two-Layer Results Architecture)

**日期**: 2025-11-05
**版本**: v1.0
**状态**: ✅ 已实现

---

## 概述 (Overview)

系统采用明确的两层结果分析架构，完全分离了批次结果分析（Layer 1）和控制策略排序（Layer 2），提供清晰的用户流程和独立的功能模块。

### 架构设计目标

- ✅ **清晰分离** - 两层功能独立、页面隔离
- ✅ **单一职责** - 每层专注于特定分析任务
- ✅ **渐进式工作流** - Layer 1 → Layer 2 的自然过渡
- ✅ **独立可扩展** - 各层可独立演进而不影响对方

---

## Layer 1: 批次结果分析 (Batch Results Analysis)

### 页面位置
- **文件**: `frontend/control/simulations.html`
- **视图标签**: `results`（结果标签页）
- **容器**: `.results-container`（CSS 类）

### 功能职责

**批次监控和性能指标展示**：

1. **8 个核心指标对比**
   - 仿真统计: loaded（已加载）, inserted（已插入）, ended（已结束）, running（运行中）
   - 车辆状态: waiting（等待）, teleports（传送）, collisions（碰撞）
   - 性能指标: avgSpeed（平均速度）

2. **在网车辆峰值曲线**
   - 时间序列图表（Chart.js）
   - 所有方案对比

3. **方案对比表格**
   - 横向对比 5-10 个方案
   - 显示绝对值和改进率

### 数据来源

```
API Endpoint: GET /api/v1/batch/{batch_id}/results
Response: {
    batch_id: string,
    case_id: string,
    plan_results: [
        {
            plan_id: string,
            plan_name: string,
            loaded: number,
            inserted: number,
            ended: number,
            running: number,
            waiting: number,
            teleports: number,
            collisions: number,
            avgSpeed: number,
            improvement_vs_baseline: object
        }
    ]
}
```

### 代码位置

| 组件 | 文件 | 职责 |
|------|------|------|
| **HTML** | `simulations.html` | 定义 `.results-container` 容器 |
| **JavaScript** | `js/batch_results.js` | 加载和渲染批次结果 |
| **样式** | `css/batch-results-theme.css` | Layer 1 样式 |

### 用户交互

```
1. 用户在"批量仿真"页面创建批次
2. 批次完成后，点击"查看结果"
3. 显示批次结果分析 (Layer 1)
   ├─ 批次信息面板
   ├─ 8 个指标对比表
   ├─ 峰值车辆曲线图
   └─ 方案对比表格
4. 点击"查看详细优化分析 →"按钮
5. 导航到优化页面显示策略排序 (Layer 2)
```

---

## Layer 2: 控制策略排序 (Strategy Ranking)

### 页面位置
- **文件**: `frontend/control/optimization.html`
- **容器**: `#resultsSection`（HTML ID）
- **URL 格式**: `optimization.html?batch_id=<id>&case_id=<id>`

### 功能职责

**多准则评分和策略推荐**：

1. **策略排序摘要**
   - 首推策略 (Top 1)
   - 总体评分 (0-100)
   - 推荐等级 (强烈推荐/推荐/可选/不推荐)

2. **策略排序表**
   - 排名 1-N
   - 每个策略的:
     - 综合评分
     - 4 维度得分 (有效性、覆盖率、效率、可靠性)
     - 推荐等级
     - 改进指标

3. **首推方案详情**
   - Top 1 策略的深度分析
   - 4 维度得分对标
   - 改进数据 (vs baseline)

4. **可视化图表**
   - 雷达图: 4 维度对比
   - 柱状图: 综合评分排序
   - 对比图: 改进指标

### 数据来源

```
API Endpoint: POST /api/v1/control/batch-optimization/batch/{case_id}/{batch_id}/strategy-ranking

Request: {
    case_id: string,
    batch_id: string,
    baseline_plan_id: "baseline_plan",
    strategy_plan_ids: [...],  // 可选，自动检测
    ranking_criteria: {         // 可选，使用默认权重
        effectiveness_weight: 0.40,
        coverage_weight: 0.25,
        efficiency_weight: 0.20,
        reliability_weight: 0.15
    }
}

Response: {
    ranking_id: string,
    case_id: string,
    batch_id: string,
    ranked_strategies: [
        {
            rank: number,
            plan_id: string,
            plan_name: string,
            overall_score: number (0-100),
            recommendation: string,
            dimension_scores: {
                effectiveness: number,
                coverage: number,
                efficiency: number,
                reliability: number
            },
            improvement_vs_baseline: {
                avg_speed_increase: number,
                travel_time_reduction: number,
                affected_vehicles: number
            }
        }
    ],
    ranking_metadata: { ... },
    report_file: string,
    timestamp: string
}
```

### 代码位置

| 组件 | 文件 | 职责 |
|------|------|------|
| **HTML** | `optimization.html` | 定义 `#resultsSection` 容器，加载脚本 |
| **JavaScript** | `js/strategy_ranking.js` | 自动初始化、加载和渲染排序结果 |
| **样式** | `css/strategy_ranking.css` | Layer 2 样式 |
| **后端** | `api/services/strategy_ranking_service.py` | 排序算法和评分逻辑 |

### 自动初始化流程

```javascript
// optimization.html 页面加载时自动执行：
document.addEventListener('DOMContentLoaded', () => {
    initializeRankingPage();  // 从 URL 参数获取 batch_id & case_id
});

// initializeRankingPage() 做以下工作：
// 1. 从 URL 参数提取 batch_id 和 case_id
// 2. 调用 loadAndDisplayRanking()
// 3. 发送 POST 请求到排序 API
// 4. 渲染排序结果到 #resultsSection
```

### 用户交互

```
1. 用户在 Layer 1 (simulations.html) 查看批次结果
2. 点击"查看详细优化分析 →"按钮
3. 跳转到 optimization.html?batch_id=...&case_id=...
4. 优化页面自动加载策略排序结果
5. 显示策略排序分析 (Layer 2)
   ├─ 策略排序摘要
   ├─ 排序表格
   ├─ 首推方案详情
   └─ 可视化图表 (雷达图、柱状图)
6. 可选: 下载 HTML 报告
```

---

## 两层架构对比

| 维度 | Layer 1 (批次结果) | Layer 2 (策略排序) |
|------|-------------------|-------------------|
| **页面** | `simulations.html` | `optimization.html` |
| **容器** | `.results-container` | `#resultsSection` |
| **加载方式** | 用户手动点击"查看结果" | 自动初始化（URL 参数） |
| **分析类型** | 基础指标对比 | 多准则评分 |
| **指标数** | 8 个核心指标 | 4 维度评分 |
| **展示内容** | 数值、表格、曲线 | 排名、分数、推荐等级 |
| **决策支持** | 了解各方案表现 | 确定最优方案顺序 |
| **脚本** | `batch_results.js` | `strategy_ranking.js` |
| **样式** | `batch-results-theme.css` | `strategy_ranking.css` |

---

## 导航流程详解

### 完整用户旅程

```
[批量仿真页面]
    ↓ (点击"查看结果")
[simulations.html - 结果标签]
    ↓ (Layer 1: 批次结果分析)
    ├─ 显示 8 个指标对比
    ├─ 显示在网车辆峰值曲线
    ├─ 显示方案对比表格
    └─ [显示"查看详细优化分析"按钮]
        ↓ (点击按钮)
[optimization.html?batch_id=...&case_id=...]
    ↓ (Layer 2: 策略排序分析)
    ├─ 自动加载排序结果
    ├─ 显示策略排序摘要
    ├─ 显示排序表格
    ├─ 显示首推方案详情
    └─ 显示可视化图表
        ↓ (可选)
[下载 HTML 报告]
```

### URL 参数规范

```
optimization.html?batch_id=<batch_id>&case_id=<case_id>

示例：
optimization.html?batch_id=batch_20251105_000102&case_id=case_20251103_141612

参数说明：
- batch_id: 必需，用于查询批次数据和仿真结果
- case_id: 必需，用于 API 请求路径，获取案例元数据
```

### 错误处理

```javascript
// 在 optimization.html 中
initializeRankingPage() {
    // 检查 URL 参数
    if (!currentBatchId || !currentCaseId) {
        showError('缺少批次或案例信息，请从批量仿真页面进入');
        return;
    }

    // 加载失败时
    loadAndDisplayRanking() {
        // 捕获 API 错误
        if (!response.ok) {
            showError('生成优化方案失败: ' + error.message);
        }
    }
}
```

---

## 代码修改汇总

### 1. strategy_ranking.js 重构

**修改前**：在 `simulations.html` 中追加排序结果到 Layer 1
**修改后**：在 `optimization.html` 中独立初始化和显示

**关键函数**：
- `initializeRankingPage()` - 从 URL 参数自动初始化
- `loadAndDisplayRanking()` - 自动加载排序结果
- `renderRankingResults()` - 渲染到 `#resultsSection`

### 2. simulations.html 更新

**移除**：
- `<link rel="stylesheet" href="css/strategy_ranking.css">`
- `<script src="js/strategy_ranking.js">`

**保留**：
- "查看详细优化分析"按钮 (HTML 中已存在)

### 3. optimization.html 增强

**添加**：
```html
<script src="js/strategy_ranking.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', () => {
        initializeRankingPage();
    });
</script>
```

### 4. batch_simulation.js 改进

**更新 `viewOptimizationAnalysis()` 函数**：
- 获取 `case_id` 从 `batchResultsData`
- 传递 `batch_id` 和 `case_id` 参数到 URL
- 支持降级处理 (case_id 缺失时使用 'unknown')

---

## 集成验证清单

### 页面加载验证

- [x] `simulations.html` 加载时不包含 `strategy_ranking.js`
- [x] 移除了 Layer 2 样式和脚本从 Layer 1 页面
- [x] "查看结果"按钮仍然存在并正常工作
- [x] "查看详细优化分析"按钮正确传递参数

### 优化页面验证

- [x] `optimization.html` 加载 `strategy_ranking.js`
- [x] 页面加载时自动调用 `initializeRankingPage()`
- [x] 从 URL 参数正确提取 `batch_id` 和 `case_id`
- [x] 自动发送排序 API 请求
- [x] 结果正确渲染到 `#resultsSection`

### 导航验证

- [x] Layer 1 → Layer 2 导航链接工作正常
- [x] URL 参数正确传递
- [x] 优化页面自动加载排序结果
- [x] 错误处理正确提示用户

### 功能验证

- [x] Layer 1 独立功能完整
- [x] Layer 2 独立功能完整
- [x] 两层结果互不干扰
- [x] 页面切换后数据保持一致

---

## 运行和测试

### 手动测试步骤

```
1. 打开 http://localhost:8000/control/simulations.html
2. 创建批次或选择现有批次
3. 切换到"结果"标签页 → 显示 Layer 1
4. 点击"查看详细优化分析 →"按钮
5. 跳转到 optimization.html
6. 自动加载策略排序结果 → 显示 Layer 2
7. 验证两层结果内容和样式正确
```

### E2E 测试

```bash
# 运行现有测试
npx playwright test tests/e2e/test_real_batch_ranking.spec.js
npx playwright test tests/e2e/test_strategy_ranking_workflow.spec.js

# 测试两层分离
# - 验证 simulations.html 不包含 strategy_ranking.js
# - 验证 optimization.html 正确加载排序结果
# - 验证导航参数传递正确
```

---

## 架构优势

### 1. **清晰的单一职责**
- Layer 1: 批次监控和性能指标
- Layer 2: 策略评分和决策支持
- 各层代码、样式、脚本完全隔离

### 2. **用户友好的工作流**
- 渐进式分析：先看基础指标，再看策略排序
- 清晰的导航路径：结果 → 优化分析
- 自动初始化 Layer 2（无需额外操作）

### 3. **易于维护和扩展**
- Layer 1 升级不会影响 Layer 2
- Layer 2 可独立演进（更多维度、更复杂算法等）
- 代码复用最小化，耦合度低

### 4. **性能优化空间**
- Layer 1 和 Layer 2 资源独立加载
- 用户可自主选择是否需要 Layer 2
- 减少不必要的 API 调用

---

## 未来增强方向

### Phase 2 可选功能

1. **Layer 2 高级功能**
   - 自定义权重调整
   - 多批次排序对比
   - 历史排序趋势分析

2. **集成改进**
   - Layer 1 结果预加载 (优化 Layer 2 初始化速度)
   - 排序结果缓存 (避免重复 API 调用)
   - 批量导出 (两层结果合并报告)

3. **用户体验**
   - 添加返回按钮 (Layer 2 → Layer 1)
   - 对比工具 (并排显示两层结果)
   - 建议面板 (基于排序结果的操作建议)

---

## 总结

新的两层架构通过完全分离批次结果分析和策略排序，实现了：

✅ **架构清晰** - 两层独立、职责明确
✅ **用户友好** - 自然的工作流和导航体验
✅ **代码优质** - 低耦合、易维护、易扩展
✅ **性能高效** - 资源隔离、按需加载
✅ **可维护性** - 各层独立演进而无副作用

系统已准备好投入生产环境。

---

**文档版本**: v1.0
**最后更新**: 2025-11-05
**作者**: Claude Code
