# Global Variable Conflicts 修复 - 2025-11-05

**问题**: JavaScript 全局变量重复声明和脚本加载顺序错误
**状态**: ✅ 已修复
**Commit**: c36e1ca

---

## 问题描述

### 错误1: SyntaxError - 变量重复声明

```
Uncaught SyntaxError: Identifier 'currentBatchId' has already been declared
```

### 错误2: ReferenceError - API_BASE 未定义

```
Uncaught ReferenceError: API_BASE is not defined
    at loadAndDisplayRanking (strategy_ranking.js:82:16)
```

---

## 根本原因

### 原因1: 变量重复声明

在 `optimization.html` 中，两个脚本都定义了相同的全局变量：

**optimization.js** (第11-14行):
```javascript
const API_BASE = '/api/v1';

let currentBatchId = null;
let batchData = null;
```

**strategy_ranking.js** (第21-22行，修复前):
```javascript
let currentBatchId = null;  // ❌ 重复声明!
let currentCaseId = null;   // ❌ 重复声明!
```

在同一个 HTML 页面中加载两个脚本时，这导致了 `SyntaxError`。

### 原因2: 脚本加载顺序错误

**optimization.html** (修复前，第390-392行):
```html
<!-- strategy_ranking.js 先加载 -->
<script src="js/strategy_ranking.js"></script>
<!-- optimization.js 后加载 -->
<script src="js/optimization.js"></script>
```

**问题**:
- `strategy_ranking.js` 尝试使用 `API_BASE` (第76行)
- 但 `API_BASE` 定义在 `optimization.js` (第11行)
- 脚本加载顺序反了，导致 `API_BASE is not defined`

---

## 解决方案

### 方案1: 共享全局变量（采用）

**设计原则**: `optimization.js` 是主模块，`strategy_ranking.js` 是辅助模块

**修改**:

1. **strategy_ranking.js**: 移除本地变量声明
   ```javascript
   // 删除这些行:
   // let currentBatchId = null;
   // let currentCaseId = null;

   // 改为注释说明:
   // 注意: currentBatchId, currentCaseId 由 optimization.js 定义和管理
   // 本模块使用 optimization.js 中定义的全局变量，避免重复声明
   ```

2. **strategy_ranking.js**: 从 URL 参数赋值给全局变量
   ```javascript
   function initializeRankingPage() {
       const batchId = params.get('batch_id');
       const caseId = params.get('case_id');

       // 赋值给 optimization.js 定义的全局变量
       currentBatchId = batchId;
       currentCaseId = caseId;
   }
   ```

3. **optimization.html**: 修复脚本加载顺序
   ```html
   <!-- optimization.js 必须先加载 -->
   <script src="js/optimization.js"></script>
   <!-- 然后再加载 strategy_ranking.js -->
   <script src="js/strategy_ranking.js"></script>
   ```

---

## 修改清单

### 文件1: `frontend/control/js/strategy_ranking.js`

**修改点1** (第18-34行): 移除本地变量声明
```diff
- let rankingResultsData = null;
- let rankingCharts = {};
- let currentBatchId = null;
- let currentCaseId = null;

+ let rankingResultsData = null;
+ let rankingCharts = {};
+
+ // 注意: currentBatchId, currentCaseId 由 optimization.js 定义和管理
+ // 本模块使用 optimization.js 中定义的全局变量，避免重复声明
+ // API_BASE 也由 optimization.js 定义和管理
```

**修改点2** (第43-50行): 使用本地变量从 URL 读取，然后赋值给全局变量
```diff
  function initializeRankingPage() {
      const params = new URLSearchParams(window.location.search);
-     currentBatchId = params.get('batch_id');
-     currentCaseId = params.get('case_id');
+     const batchId = params.get('batch_id');
+     const caseId = params.get('case_id');

      if (!batchId || !caseId) {
          // ...
      }

+     // 使用 optimization.js 中的全局变量
+     currentBatchId = batchId;
+     currentCaseId = caseId;
  }
```

### 文件2: `frontend/control/optimization.html`

**修改点**: 脚本加载顺序 (第389-392行)
```diff
  <!-- 通用提示组件 -->
  <script src="js/notification.js"></script>
- <!-- 控制策略排序逻辑 (Layer 2) -->
- <script src="js/strategy_ranking.js"></script>
- <!-- 方案优化分析逻辑 -->
- <script src="js/optimization.js"></script>

+ <!-- 方案优化分析逻辑 (必须先加载，定义 API_BASE 和全局变量) -->
+ <script src="js/optimization.js"></script>
+ <!-- 控制策略排序逻辑 (Layer 2) -->
+ <script src="js/strategy_ranking.js"></script>
```

---

## 验证修复

### 验证步骤

1. **清除浏览器缓存** (Ctrl+Shift+Delete)

2. **打开优化分析页面**
   ```
   http://localhost:8000/control/optimization.html?batch_id=batch_20251105_000102&case_id=case_20251103_141612
   ```

3. **检查浏览器控制台** (F12)
   - ❌ 不应该看到: `SyntaxError: Identifier 'currentBatchId' has already been declared`
   - ❌ 不应该看到: `ReferenceError: API_BASE is not defined`
   - ✅ 应该看到: 加载指示器显示并正常工作

4. **等待加载完成** (3-5秒)
   - ✅ 加载指示器应该消失
   - ✅ 排序结果应该显示

---

## 技术细节

### JavaScript 全局变量作用域

```javascript
// optimization.js
const API_BASE = '/api/v1';  // 全局常量
let currentBatchId = null;   // 全局变量

// strategy_ranking.js
// 可以直接访问 optimization.js 中定义的全局变量
// 因为它们在同一个 window 作用域中
console.log(API_BASE);           // '/api/v1' ✅
console.log(currentBatchId);     // null 或赋值后的值 ✅
```

### 脚本加载顺序的重要性

```html
<!-- 错误的顺序 -->
<script>console.log(API_BASE)</script>  <!-- ❌ ReferenceError -->
<script>const API_BASE = '/api/v1'</script>

<!-- 正确的顺序 -->
<script>const API_BASE = '/api/v1'</script>
<script>console.log(API_BASE)</script>  <!-- ✅ '/api/v1' -->
```

---

## 最佳实践

### ✅ 推荐做法

1. **单一数据来源**
   - 让主模块 (`optimization.js`) 定义全局变量
   - 辅助模块只读取或赋值，不重复声明

2. **清晰的脚本加载顺序**
   - 依赖库先加载
   - 定义全局变量的脚本先加载
   - 使用全局变量的脚本后加载

3. **文档化依赖关系**
   ```javascript
   // strategy_ranking.js
   // 依赖: API_BASE (来自 optimization.js)
   // 依赖: currentBatchId, currentCaseId (来自 optimization.js)
   ```

### ❌ 避免做法

1. **多处定义相同的全局变量**
2. **没有文档的全局变量使用**
3. **随意的脚本加载顺序**

---

## 相关文件

- `frontend/control/js/optimization.js` - 主模块
- `frontend/control/js/strategy_ranking.js` - Layer 2 模块
- `frontend/control/optimization.html` - HTML 页面

---

**修复完成日期**: 2025-11-05
**修复者**: Claude Code
**Commit**: c36e1ca

