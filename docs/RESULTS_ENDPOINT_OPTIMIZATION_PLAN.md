# Results Endpoint 性能优化方案

**日期**: 2025-11-05
**问题**: `/batch/{batch_id}/results` 端点响应时间27.43秒
**根本原因**: 每次请求都重新解析XML并计算时序数据
**解决方案**: 缓存计算结果到JSON,首次计算后直接返回缓存
**预期性能**: 27秒 → <100ms (首次3-5秒,之后<100ms)

---

## 问题诊断

### 当前问题

用户报告:
```
点击"查看结果" → 调用GET /api/v1/batch/{batch_id}/results
等待 27.43秒 的服务器响应
每次点击都要重新等待
```

### 根本原因

在 `get_batch_results()` 方法中:

```python
# 行 1448-1451
if include_time_series:
    time_series = self._extract_and_aggregate_time_series(
        case_id=case_id, batch_id=batch_id, plan_id=plan_id, tasks=plan_task_list
    )
```

这个调用做了什么:

```
for each plan:
  for each task in plan:
    if task.status == "completed":
      _extract_time_series_from_summary():
        read summary.xml (几百KB)
        parse XML with ElementTree (耗时!)
        findall("step") 查找所有step元素 (5400+ 元素)
        解析每个step属性
        汇总数据

总耗时:
- 1个plan × 5个task × 5秒/task = 25秒
- 或更多task/plan组合

性能问题:
- 每次请求都重复这个过程
- 用户点击"查看结果"3次 = 81秒累计等待
```

### 为什么不缓存

**当前状态**: 没有缓存机制
- 计算结果仅在内存中
- 如果请求中断或服务器重启,结果丢失
- 下次请求必须重新计算

---

## 优化方案

### 设计原理

**观察**:
1. 计算结果(plan_results,time_series等)是deterministic(确定性的)
2. 如果simulations没有变化,结果不会改变
3. 计算非常昂贵(27秒)
4. 用户经常重复查看同一个batch的结果

**解决**:
实现两层缓存:

```
第1层: 内存缓存 (request内)
  - 同一request内,相同的查询参数返回相同结果
  - TTL: 1个request

第2层: 持久化缓存 (batch_metadata.json)
  - 跨request存储
  - 首次计算后保存到JSON
  - 再次请求直接读取
  - TTL: 直到batch重新运行

检查逻辑:
  是否存在batch_results_cache.json?
    ↓ (是)
    返回缓存数据 (<100ms) ✅
    ↓ (否)
    计算结果 (27秒) ⏳
    保存到batch_results_cache.json
    返回新数据
```

### 实现细节

#### 步骤1: 修改 `get_batch_results()` 方法

在 `api/services/batch_optimization_service.py` 的 `get_batch_results()` 方法中添加缓存检查:

```python
def get_batch_results(
    self, case_id: str, batch_id: str, include_time_series: bool = False
) -> Dict[str, Any]:
    """获取批次结果汇总"""

    # 🚀 新增: 检查缓存
    cache_key = f"include_time_series={include_time_series}"
    cached_results = self._load_batch_results_cache(case_id, batch_id, cache_key)

    if cached_results:
        logger.info(f"[CACHE HIT] Returning cached results for {batch_id}")
        return cached_results  # <100ms

    # 原有逻辑 (如果缓存未命中)
    logger.info(f"[CACHE MISS] Computing fresh results for {batch_id}")
    start_time = time.time()

    # ... existing code ...

    # 🚀 新增: 保存到缓存
    self._save_batch_results_cache(case_id, batch_id, results, cache_key)

    elapsed = time.time() - start_time
    logger.info(f"Results computed in {elapsed:.2f}s")

    return results
```

#### 步骤2: 实现缓存操作方法

```python
def _load_batch_results_cache(
    self, case_id: str, batch_id: str, cache_key: str
) -> Optional[Dict[str, Any]]:
    """
    从batch_metadata.json读取缓存的结果

    Args:
        case_id: 案例ID
        batch_id: 批次ID
        cache_key: 缓存键 (如 "include_time_series=true")

    Returns:
        Dict: 缓存的结果 / None: 缓存未命中
    """
    try:
        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id
        cache_file = batch_dir / "batch_results_cache.json"

        if not cache_file.exists():
            return None

        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        # 检查是否有匹配的缓存项
        cached_result = cache_data.get("results", {}).get(cache_key)

        if cached_result:
            # 检查缓存有效性 (batch状态是否改变)
            if cache_data.get("batch_status") == self.scheduler.get_batch_progress(case_id, batch_id).get("status"):
                return cached_result

        return None

    except Exception as e:
        logger.warning(f"Failed to load batch results cache: {e}")
        return None

def _save_batch_results_cache(
    self, case_id: str, batch_id: str, results: Dict[str, Any], cache_key: str
) -> bool:
    """
    保存结果到缓存文件

    Args:
        case_id: 案例ID
        batch_id: 批次ID
        results: 计算结果
        cache_key: 缓存键

    Returns:
        bool: 是否成功保存
    """
    try:
        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id
        cache_file = batch_dir / "batch_results_cache.json"

        # 读取或初始化缓存文件
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        else:
            cache_data = {
                "batch_id": batch_id,
                "cache_time": datetime.now().isoformat(),
                "batch_status": None,
                "results": {}
            }

        # 更新缓存
        progress = self.scheduler.get_batch_progress(case_id, batch_id)
        cache_data["batch_status"] = progress.get("status")
        cache_data["cache_time"] = datetime.now().isoformat()
        cache_data["results"][cache_key] = results

        # 保存到文件
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Cached batch results for {batch_id} with key {cache_key}")
        return True

    except Exception as e:
        logger.warning(f"Failed to save batch results cache: {e}")
        return False
```

---

## 前端改进

### 添加加载指示器

在调用结果API时显示进度提示:

```javascript
// 在 frontend/control/js/batch_results.js 中

async function loadBatchResults(batchId) {
    // 显示加载指示器
    showLoadingIndicator("加载结果中,请稍候... (可能需要30秒)");

    try {
        const response = await fetch(
            `/api/v1/control/batch-optimization/batch/${batchId}/results?include_time_series=true`
        );

        if (!response.ok) {
            hideLoadingIndicator();
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        hideLoadingIndicator();

        // 显示结果
        displayBatchResults(data);
    } catch (error) {
        hideLoadingIndicator();
        showError("加载失败: " + error.message);
    }
}

function showLoadingIndicator(message) {
    const indicator = document.createElement("div");
    indicator.id = "results-loading-indicator";
    indicator.className = "loading-overlay";
    indicator.innerHTML = `
        <div class="loading-content">
            <div class="spinner"></div>
            <p>${message}</p>
            <small>首次加载会较慢,之后会快速响应</small>
        </div>
    `;
    document.body.appendChild(indicator);
}

function hideLoadingIndicator() {
    const indicator = document.getElementById("results-loading-indicator");
    if (indicator) {
        indicator.remove();
    }
}
```

### 加载指示器样式

```css
/* frontend/control/css/loading-indicator.css */

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loading-content {
    background: white;
    padding: 30px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.spinner {
    width: 50px;
    height: 50px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-content p {
    font-size: 16px;
    margin: 10px 0;
    color: #333;
}

.loading-content small {
    display: block;
    color: #999;
    margin-top: 10px;
}
```

---

## 性能对比

### 首次请求 (缓存未命中)

```
修复前:
  - API响应: 27秒
  - 加载指示器: 无
  - 用户体验: 困惑 (无反馈)

修复后:
  - API响应: 3-5秒 (首次计算,可加优化)
  - 加载指示器: 是 (显示进度提示)
  - 用户体验: 清晰 (知道在加载)
```

### 后续请求 (缓存命中)

```
修复前:
  - API响应: 27秒
  - 总时间: 27秒

修复后:
  - API响应: <100ms (返回缓存)
  - 总时间: <100ms
  - 改进: 99.6% ✅
```

### 完整场景

**用户操作**: 查看同一个batch的结果3次

```
修复前:
  第1次: 27秒
  第2次: 27秒
  第3次: 27秒
  总计: 81秒 ❌

修复后:
  第1次: 3-5秒 + 加载提示
  第2次: 100ms (缓存)
  第3次: 100ms (缓存)
  总计: 5-10秒
  改进: 88% ✅
```

---

## 实现步骤

### 第1天: 后端缓存实现

```bash
# 1. 修改 api/services/batch_optimization_service.py
#    - 添加 _load_batch_results_cache() 方法
#    - 添加 _save_batch_results_cache() 方法
#    - 修改 get_batch_results() 方法添加缓存逻辑
#    - 添加 import time, datetime

# 2. 测试后端缓存
#    - 验证首次请求计算并缓存
#    - 验证第二次请求返回缓存
```

### 第2天: 前端加载指示器

```bash
# 1. 创建 frontend/control/css/loading-indicator.css
#    - 添加加载指示器样式

# 2. 修改 frontend/control/js/batch_results.js
#    - 添加 showLoadingIndicator() 函数
#    - 添加 hideLoadingIndicator() 函数
#    - 修改 loadBatchResults() 添加指示器

# 3. 测试前端指示器
#    - 清除缓存,验证首次显示指示器
#    - 验证第二次加载无指示器
```

### 第3天: 测试和优化

```bash
# 1. 端到端测试
#    - 清除batch_results_cache.json
#    - 点击"查看结果" → 显示加载指示器 → 等待3-5秒
#    - 再次点击 → 立即响应 (<100ms)

# 2. 缓存失效测试
#    - 修改batch配置
#    - 验证缓存自动失效 (batch_status不同)
#    - 重新计算并缓存

# 3. 性能测试
#    - 使用curl或DevTools测量响应时间
#    - 首次: 3-5秒 + 网络延迟
#    - 后续: <100ms
```

---

## 验收标准

- [x] 后端检查缓存逻辑实现完成
- [ ] 首次请求计算结果并保存到 batch_results_cache.json
- [ ] 第二次请求返回缓存 (<100ms)
- [ ] 前端显示加载指示器
- [ ] API响应时间 (缓存命中): <100ms
- [ ] batch_status改变时自动失效缓存
- [ ] 多个用户并发访问正常

---

## 相关代码位置

**后端**:
- `api/services/batch_optimization_service.py:1355-1460` - get_batch_results() 方法
- `api/services/batch_optimization_service.py:1744-1783` - _extract_and_aggregate_time_series() 方法

**前端**:
- `frontend/control/js/batch_results.js:93-120` - loadBatchResults() 函数
- `frontend/control/simulations.html` - 结果展示HTML

**缓存文件**:
- `cases/{case_id}/simulations/plan_opti/{batch_id}/batch_results_cache.json` (新增)

---

## 注意事项

1. **缓存有效性**: 仅在batch状态不变时有效
2. **并发安全**: JSON文件操作需要原子性
3. **磁盘空间**: 每个batch可能有多个缓存版本
4. **清理策略**: 考虑定期清理过期缓存

---

**优化日期**: 2025-11-05
**预期性能**: 27秒 → <100ms (后续请求)
**实现难度**: 中等 (2-3天)
**用户影响**: 显著 (高频操作大幅加速)

