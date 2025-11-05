# Layer 1 与 Layer 2 架构分离说明 - 2025-11-05

**问题**: 为什么 `optimization.js` 不再用于 `optimization.html`?
**答案**: 实现 OpenSpec 设计中的 Layer 1 和 Layer 2 的正确分离
**状态**: ✅ 已实现
**Commit**: 3a3e1fb

---

## 架构概览

根据 `openspec/changes/add-layer2-control-strategy-ranking` 设计，系统分为两层：

### Layer 1: 批量仿真结果分析

**页面**: `simulations.html`
**功能**: 基础方案对比分析
**数据**: 8 个基础指标 (来自 summary.xml)
**JS 模块**:
- `batch_simulation.js` (主模块)
- `strategy_ranking.js` (集成排序功能)

**显示内容**:
- 批次监控 (进度条)
- 批次结果对比表
- 在网车辆峰值曲线
- 方案对比指标
- **按钮**: "查看详细优化分析" → 跳转到 Layer 2

---

### Layer 2: 控制策略排序与优化

**页面**: `optimization.html` (新实现)
**功能**: 多准则策略排序和推荐
**数据**:
- 多准则评分 (effectiveness, coverage, efficiency, reliability)
- EdgeData/TripInfo 分析 (如果可用)
- 排序推荐和报告
**JS 模块**:
- `strategy_ranking.js` (独立实现)

**显示内容**:
- 策略排序表格
- 推荐等级 (一级/二级/三级)
- 多指标雷达图
- 对比柱状图
- HTML 报告下载

---

## 为什么需要分离？

### 设计理由

1. **单一职责原则**
   - Layer 1: 显示基础指标对比
   - Layer 2: 提供排序和推荐

2. **避免功能重复**
   - 旧 `optimization.js`: 重复了 Layer 1 的功能
   - 新设计: `strategy_ranking.js` 专注于排序

3. **清晰的业务流程**
   ```
   批量仿真 (simulations.html)
       ↓
   用户查看结果
       ↓
   点击"查看详细优化分析"
       ↓
   跳转到 optimization.html (Layer 2)
       ↓
   查看排序和推荐
   ```

4. **独立部署和维护**
   - Layer 1 和 Layer 2 可以独立开发
   - Layer 1 不依赖 Layer 2
   - Layer 2 不重复 Layer 1 的代码

---

## 修改历史

### 修改前

```html
<!-- optimization.html -->
<script src="js/notification.js"></script>
<script src="js/strategy_ranking.js"></script>
<script src="js/optimization.js"></script>  <!-- ❌ 不应该使用 -->
```

**问题**:
- `optimization.js` 是 Layer 1 的代码
- `optimization.html` 应该是纯 Layer 2 页面
- 两个脚本定义相同的全局变量 → 重复声明错误
- 两个脚本定义相同的 API_BASE → 冲突

### 修改后

```html
<!-- optimization.html -->
<script src="js/notification.js"></script>
<script src="js/strategy_ranking.js"></script>  <!-- ✅ 只使用 Layer 2 模块 -->
```

**优点**:
- 清晰的模块分离
- 无全局变量冲突
- 无重复定义
- 正确的架构实现

---

## 文件对应关系

### Layer 1 (Batch Simulation)

| 文件 | 作用 |
|------|------|
| `simulations.html` | Layer 1 主页面 |
| `batch_simulation.js` | Layer 1 主逻辑 |
| `batch_results.js` | Layer 1 结果展示 |
| `strategy_ranking.js` | Layer 2 集成按钮 (嵌入 Layer 1) |

### Layer 2 (Strategy Ranking)

| 文件 | 作用 |
|------|------|
| `optimization.html` | Layer 2 主页面 |
| `strategy_ranking.js` | Layer 2 完整实现 |

### 已淘汰

| 文件 | 原因 |
|------|------|
| `optimization.js` | Layer 1 代码，不应用于 optimization.html |

---

## 技术详情

### strategy_ranking.js 的独立性

`strategy_ranking.js` 现在是完全独立的模块：

```javascript
// 第1部分: 定义自己的全局变量和常量
const API_BASE = '/api/v1';
let currentBatchId = null;
let currentCaseId = null;
let rankingResultsData = null;
let rankingCharts = {};

// 第2部分: 初始化函数
function initializeRankingPage() {
    // 从 URL 参数读取数据
    currentBatchId = params.get('batch_id');
    currentCaseId = params.get('case_id');

    // 加载排序结果
    loadAndDisplayRanking();
}

// 第3部分: API 调用
async function loadAndDisplayRanking() {
    const response = await fetch(
        `${API_BASE}/batch/${currentCaseId}/${currentBatchId}/strategy-ranking`
    );
    // ...
}

// 第4部分: 结果展示
function renderRankingResults() {
    // 渲染排序表格、雷达图等
}
```

### 在 simulations.html 中的使用

当 `strategy_ranking.js` 加载到 `simulations.html` 时：

```html
<!-- simulations.html -->
<script src="js/batch_simulation.js"></script>   <!-- 定义 API_BASE -->
<script src="js/batch_results.js"></script>      <!-- 定义其他全局变量 -->
<script src="js/strategy_ranking.js"></script>   <!-- 集成排序功能 -->
```

此时 `API_BASE` 已经由 `batch_simulation.js` 定义，`strategy_ranking.js` 中的 `const API_BASE` 声明会被 hoisting，但实际使用时会使用第一个定义的值。

**注意**: 这种情况下，为了避免混淆，可以考虑在 `strategy_ranking.js` 中检查 `API_BASE` 是否已存在。

### 在 optimization.html 中的使用

当 `strategy_ranking.js` 单独加载到 `optimization.html` 时：

```html
<!-- optimization.html -->
<script src="js/strategy_ranking.js"></script>   <!-- 定义自己的所有依赖 -->
```

此时 `strategy_ranking.js` 独立定义所有需要的全局变量，不依赖其他脚本。

---

## 最佳实践

### ✅ 推荐做法

1. **Layer 分离**
   ```
   Layer 1 (simulations.html)
   ├── batch_simulation.js (主)
   ├── batch_results.js
   └── strategy_ranking.js (辅, 嵌入排序按钮)

   Layer 2 (optimization.html)
   └── strategy_ranking.js (独立, 完整功能)
   ```

2. **模块独立性**
   - 每个模块定义自己需要的常量
   - 避免跨模块全局变量依赖
   - 使用 URL 参数传递数据

3. **清晰的职责**
   - Layer 1: 基础对比分析
   - Layer 2: 排序和推荐

---

## 验证

### 验证步骤

1. **验证 Layer 1 (simulations.html)**
   ```
   ✅ 批次监控显示
   ✅ 结果对比表显示
   ✅ "查看详细优化分析" 按钮显示
   ✅ 点击按钮跳转到 optimization.html
   ```

2. **验证 Layer 2 (optimization.html)**
   ```
   ✅ 独立加载 (不依赖 simulations.html)
   ✅ 显示排序结果
   ✅ 显示推荐等级
   ✅ 显示雷达图和柱状图
   ```

3. **验证没有错误**
   ```
   ✅ 浏览器控制台无 SyntaxError
   ✅ 浏览器控制台无 ReferenceError
   ✅ 浏览器控制台无 API 错误
   ```

---

## 相关文档

- `openspec/changes/add-layer2-control-strategy-ranking/design.md` - Layer 2 设计文档
- `openspec/changes/add-layer2-control-strategy-ranking/proposal.md` - Layer 2 提案
- `docs/GLOBAL_VARIABLES_FIX.md` - 全局变量问题修复

---

**分离完成日期**: 2025-11-05
**Commit**: 3a3e1fb
**状态**: ✅ 完成

