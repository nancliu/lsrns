# 变更提案：增强批量仿真监控与管理

**变更ID**: enhance-batch-simulation-monitoring
**创建日期**: 2025-10-29
**状态**: 提案中
**优先级**: P1

---

## 为什么 (Why)

当前批量仿真功能已实现基础的任务进度监控，但缺少**细粒度的仿真运行状态监测**和**批次管理**能力。用户无法：

1. **实时监测仿真内部状态**：无法查看当前在网车辆数、已完成车辆数等关键指标，无法基于summary.xml估算剩余时间
2. **管理历史批次**：无法查看已完成的批次列表，无法快速定位特定批次的结果
3. **明确结果页面位置**：批量仿真页面和方案优化页面的职责边界不清晰

这导致：

- 用户必须等待整个批次完成才能看到任何结果，缺少过程透明度
- 无法评估仿真是否正常运行（例如：车辆数是否异常、是否卡死）
- 历史批次数据难以追溯和复用
- 用户体验不连贯，不知道在哪里查看结果

## 什么 (What)

本变更增强批量仿真监控与管理能力，包括：

### 1. **细粒度仿真状态监控** (P0)

- 从running仿真的summary.xml实时提取在网车辆数、已完成车辆数
- 基于已完成的step数和总step数估算单个仿真的剩余时间
- 基于所有任务的平均时长和剩余任务数估算批次总剩余时间
- 在进度视图中显示每个运行中任务的实时状态（简化版，不含平均速度）

### 2. **批次管理功能** (P1)

- 提供批次列表API，支持按状态（running/completed/cancelled）和时间范围筛选
- 在批量仿真页面添加"批次历史"视图（第4个Tab）
- 支持查看历史批次的详细信息和结果
- 支持删除/归档历史批次

### 3. **明确结果页面职责** (P0)

- **批量仿真页面 - 结果视图**：基于summary.xml的基础对比
  - 方案对比表（关键指标：行程时间、平均速度、车辆数等）
  - 在网车辆峰值曲线
  - 峰值指标卡片
  - 提供"查看详细优化分析"按钮跳转到方案优化页面
- **方案优化页面**：深度分析和决策支持
  - 详细方案对比表（更多指标）
  - 多指标雷达图（归一化对比）
  - 导出详细报告（PDF/Excel）

### 4. **架构优化** (P1)

- 重构进度查询逻辑，减少对文件系统的频繁访问
- 引入缓存机制，提升进度查询性能（2秒轮询场景）
- 优化summary.xml解析，支持增量读取（避免重复解析整个文件）

## 如何 (How)

### 技术方案

#### 0. 轮询频率优化

**Frontend轮询调整**:

- 进度监控轮询间隔：**10秒**（从2秒调整为10秒）
- Backend缓存TTL：**5秒**（保持不变，每2次轮询刷新一次数据）
- 理由：summary.xml每秒更新，10秒轮询足够平衡实时性和性能

#### 1. 仿真状态监控实现

**Backend (api/services/batch_optimization_service.py)**:

```python
def get_batch_progress_with_live_monitoring(
    self, case_id: str, batch_id: str
) -> Dict[str, Any]:
    """
    获取批次进度，包含运行中任务的实时状态监控

    对每个running任务：
    1. 读取对应的summary.xml（如果存在）
    2. 解析最新的<step>数据
    3. 提取running, loaded, ended, meanSpeed
    4. 计算仿真进度百分比：current_step / total_steps
    5. 估算剩余时间：avg_step_duration * remaining_steps
    """
    # 伪代码
    progress_data = self._load_batch_progress(batch_id)

    for task in progress_data['tasks']:
        if task['status'] == 'running':
            sim_status = self._get_simulation_live_status(
                case_id, batch_id, task
            )
            task['live_status'] = sim_status
            # {
            #   'current_step': 1500,
            #   'total_steps': 14400,
            #   'progress_percent': 10.4,
            #   'running_vehicles': 320,
            #   'ended_vehicles': 150,
            #   'mean_speed': 25.3,
            #   'estimated_remaining_seconds': 450
            # }

    # 计算批次总剩余时间
    progress_data['estimated_completion'] = self._estimate_batch_completion(
        progress_data['tasks']
    )

    return progress_data
```

**Frontend (batch_simulation.js)**:

- 进度视图表格增加"实时状态"列
- 显示在网车辆数、进度百分比（**不显示平均速度**，简化进度视图）
- 显示预计剩余时间（倒计时）
- **动态在网车辆曲线**（新增）：
  - 汇总所有运行中任务的在网车辆数，实时绘制曲线
  - 简单折线图（无放大、导出等复杂功能）
  - 当前无运行批次时自动隐藏

#### 2. 批次管理实现

**Backend API**:

```
GET /api/v1/control/batch-optimization/batches?status=completed&limit=20
→ 返回批次列表（分页）

GET /api/v1/control/batch-optimization/batches/{batch_id}/summary
→ 返回批次摘要（不含完整time_series，减少数据量）

DELETE /api/v1/control/batch-optimization/batches/{batch_id}?archive=true
→ 归档或删除批次
```

**Frontend**:

- 批量仿真页面添加第4个Tab："批次历史"
- 显示历史批次卡片（batch_id, 时间, 方案数, 状态）
- 点击卡片→加载该批次的结果视图

#### 3. 结果页面职责划分

**批量仿真页面 - 结果视图 (simulations.html)**:

- **定位**：快速查看本次批次的基础对比（基于summary.xml数据）
- **内容**：
  - 方案对比表（关键指标 + 改善百分比）
    - 数据来源：summary.xml中的meanTravelTime、meanSpeed、ended等指标
    - 显示：平均行程时间、平均速度、总车辆数、相比基准的改善率
  - 在网车辆峰值曲线（折线图）
    - 数据来源：summary.xml的时序数据
  - 峰值指标卡片（最大车辆数、峰值时刻、平均车辆数）
  - "查看详细优化分析"按钮 → 跳转到optimization.html?batch_id=xxx

**方案优化页面 (optimization.html)**:

- **定位**：深度分析和决策支持（进一步分析）
- **内容**：
  - 批次信息卡片
  - 详细方案对比表（更多指标）
    - 除summary.xml数据外，可能包含tripinfo.xml等更详细的分析
  - 在网车辆峰值曲线（支持缩放、导出）
  - **多指标雷达图**（归一化对比）
  - **导出详细报告**（PDF/Excel）
  - "返回批量仿真"按钮

**导航流程**:

```
批量仿真页面（配置视图）
  → 启动仿真
  → 切换到进度视图（实时监控）
  → 批次完成后自动切换到结果视图（基础对比）
  → 点击"查看详细优化分析"
  → 跳转到方案优化页面（深度分析）
```

#### 4. 性能优化

**进度缓存机制**:

```python
# 使用内存缓存（TTL=5秒）
from cachetools import TTLCache

progress_cache = TTLCache(maxsize=100, ttl=5)

def get_batch_progress_cached(batch_id: str):
    if batch_id in progress_cache:
        return progress_cache[batch_id]

    progress = self._load_batch_progress_from_disk(batch_id)
    progress_cache[batch_id] = progress
    return progress
```

**增量解析summary.xml**:

```python
def _parse_summary_last_step(summary_file: Path) -> Dict:
    """
    只解析summary.xml的最后一行（最新<step>），避免重复解析整个文件

    策略：
    1. 从文件末尾向前读取最后4KB数据
    2. 正则提取最后一个<step>元素
    3. 解析属性：time, running, loaded, ended, meanSpeed

    性能：<10ms/文件（vs 全文解析50ms+）
    """
    # 实现细节见design.md
    pass
```

## 影响范围

### 新增文件

- `openspec/changes/enhance-batch-simulation-monitoring/specs/live-monitoring/spec.md`
- `openspec/changes/enhance-batch-simulation-monitoring/specs/batch-management/spec.md`
- `openspec/changes/enhance-batch-simulation-monitoring/specs/result-page-separation/spec.md`

### 修改文件

- `api/services/batch_optimization_service.py` - 添加实时监控方法
- `api/routes/batch_optimization_routes.py` - 添加批次管理API
- `frontend/control/js/batch_simulation.js` - 增强进度显示
- `frontend/control/simulations.html` - 添加批次历史Tab
- `frontend/control/optimization.html` - 增强结果分析功能

### API变更

- **新增**: `GET /api/v1/control/batch-optimization/batches` - 批次列表
- **新增**: `GET /api/v1/control/batch-optimization/batches/{batch_id}/summary` - 批次摘要
- **新增**: `DELETE /api/v1/control/batch-optimization/batches/{batch_id}` - 删除批次
- **增强**: `GET /api/v1/control/batch-optimization/batch/{batch_id}/progress` - 添加live_status字段
- **向后兼容**: 现有API保持不变

## 风险与缓解

| 风险                        | 影响 | 缓解措施                                       |
| --------------------------- | ---- | ---------------------------------------------- |
| 频繁读取summary.xml影响性能 | 中   | 使用缓存（TTL=5秒）+ 增量解析                  |
| 大量批次导致列表查询慢      | 低   | 分页 + 索引（batch_metadata.json包含关键字段） |
| 实时监控数据不准确          | 低   | 明确标注"实时估算值"，避免用户误解             |
| 长时仿真（6-24小时）导致用户等待焦虑 | 中   | 显示预计完成时间和剩余时间倒计时，动态曲线提供视觉反馈 |

**注**：仿真时长取决于管控复杂度和策略配置，范围为1-24小时（通常1-6小时）。

## 验收标准

- [ ] **进度视图**显示运行中任务的在网车辆数、进度百分比（**不显示平均速度**）
- [ ] **进度视图**显示预计剩余时间（批次级和任务级）
- [ ] **进度视图**显示动态在网车辆曲线，汇总所有运行中任务，每10秒更新
- [ ] **动态曲线**在无运行批次时自动隐藏
- [ ] **结果视图**基于summary.xml展示方案对比表（行程时间、速度、车辆数等）
- [ ] **结果视图**显示在网车辆峰值曲线和峰值指标卡片
- [ ] **结果视图**提供"查看详细优化分析"按钮，跳转到optimization.html
- [ ] 批量仿真页面提供"批次历史"视图，显示历史批次列表
- [ ] 批次历史支持按状态筛选（running/completed/cancelled）
- [ ] **方案优化页面**支持通过URL参数（batch_id）加载结果，进行深度分析
- [ ] 进度查询API响应时间 <200ms（60任务场景）
- [ ] **前端轮询间隔为10秒**（从2秒调整）
- [ ] E2E测试覆盖完整导航流程（配置→进度→结果→优化分析）

## 参考资料

- 设计文档: `docs/design/traffic_control_optimization_overview.md` (第5.5节 - 用户工作流程与页面导航)
- 现有实现: `api/services/batch_optimization_service.py` (get_batch_progress方法)
- SUMO文档: summary.xml格式说明
