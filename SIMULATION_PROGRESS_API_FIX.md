# OD仿真进度监测API修复

## 问题诊断

**前端无法正确监测仿真进度的根本原因**：

前端 `script.js` 使用了**错误的API返回格式**：

```javascript
// ❌ 错误的用法
const p = await apiFetch(`${API_BASE_URL}/simulation_progress/${caseId}`);
const pct = data.percent;      // API 没有这个字段！
const msg = data.message;      // API 没有这个字段！
const status = data.status;    // API 返回的是数组形式
```

**API 返回的实际格式**（案例级汇总）：
```json
{
  "case_id": "case_20251116_224458",
  "simulations": [         // ← 是数组，不是单个对象！
    {
      "simulation_id": "sim_xxx",
      "status": "running",
      "progress": 45,
      ...
    }
  ],
  "stats": {
    "total": 2,
    "completed": 0,
    "in_progress": 1,
    "failed": 0
  }
}
```

**问题**：API 返回的是**案例下所有仿真的汇总**，但前端期望的是**单个仿真的详细进度**。

## 解决方案

### 1. 后端：添加单个仿真详细进度API

**新API端点**：`GET /api/v1/simulation_progress/{case_id}/{simulation_id}`

**返回格式**（前端期望的格式）：
```json
{
  "simulation_id": "sim_1116_232054382_micro",
  "case_id": "case_20251116_224458",
  "status": "running",
  "percent": 45,
  "message": "t=1628s/3600s",
  "progress": 45,
  "created_at": "2025-11-16T23:20:54.389302",
  "started_at": "2025-11-16T23:20:54.443469",
  "completed_at": null,
  "result_folder": "cases\\case_20251116_224458\\simulations\\sim_1116_232054382_micro"
}
```

### 2. 后端实现细节

**文件**：`api/services/simulation_service.py:950-1025`

新增方法 `get_simulation_progress_detail(case_id, simulation_id)`：

```python
async def get_simulation_progress_detail(self, case_id: str, simulation_id: str) -> Dict[str, Any]:
    """获取单个仿真的详细进度信息（用于前端实时监控）"""
    # 1. 从 get_case_simulations() 获取仿真元数据
    # 2. 使用 result_folder 找到进度文件位置
    # 3. 读取 progress.json 获取实时数据
    # 4. 返回前端期望的格式
```

**关键设计**：
- ✅ 充分利用元数据中的 `result_folder` 字段
- ✅ 支持普通仿真和批次仿真（自动查找进度文件）
- ✅ 进度文件不存在时使用元数据中的状态作为备选
- ✅ 返回前端期望的确切字段

### 3. 路由注册

**文件**：`api/routes/simulation_routes.py:74-94`

```python
@router.get("/simulation_progress/{case_id}/{simulation_id}")
async def get_simulation_progress_detail(case_id: str, simulation_id: str):
    """获取单个仿真的详细进度"""
    data = await get_simulation_progress_detail_service(case_id, simulation_id)
    return create_success_response("获取仿真进度详情成功", data)
```

### 4. 前端：修复轮询逻辑

**文件**：`frontend/script.js:447-491`

#### 修复前：
```javascript
// ❌ 错误：使用汇总API，期望单个仿真字段
const p = await apiFetch(`${API_BASE_URL}/simulation_progress/${caseId}`);
const pct = data.percent;  // 不存在！
```

#### 修复后：
```javascript
// ✓ 正确：使用新的单个仿真API
const p = await apiFetch(`${API_BASE_URL}/simulation_progress/${caseId}/${currentSim.simulationId}`);
const pct = data.percent;  // ✓ 存在
const msg = data.message;  // ✓ 存在
```

#### 存储仿真ID：
```javascript
// 启动仿真后保存仿真ID
const payload = result.data || result;
currentSim.simulationId = payload.simulation_id;  // 新增
currentSim.caseId = caseId;
```

## API对比

### 旧API（汇总）- 用于监控面板
```
GET /api/v1/simulation_progress/{case_id}
```

返回：
- ✓ 案例下所有仿真列表
- ✓ 统计信息（total, completed, in_progress等）
- ✓ 总体进度百分比
- 用于：多仿真列表显示

### 新API（详细）- 用于实时监控
```
GET /api/v1/simulation_progress/{case_id}/{simulation_id}
```

返回：
- ✓ 单个仿真的详细进度
- ✓ 实时状态和百分比
- ✓ 进度消息和时间戳
- 用于：单仿真进度条显示

## 代码修改统计

### 后端
| 文件 | 修改 |
|------|------|
| `api/services/simulation_service.py` | +76 行（新方法） |
| `api/services/__init__.py` | +2 行（导出新函数） |
| `api/routes/simulation_routes.py` | +23 行（新路由） |

### 前端
| 文件 | 修改 |
|------|------|
| `frontend/script.js` | ~45 行（修复轮询逻辑 + 错误处理） |

## 向后兼容性

✅ **完全向后兼容**
- 旧的汇总API保持不变
- 新的详细API是新增功能
- 前端修改不影响其他功能

## 测试验证

**测试结果**：
```
✓ 新API能正确返回单个仿真详细进度
✓ 支持普通仿真和批次仿真
✓ 进度文件不存在时能正确回退
✓ 所有必要字段都存在
```

**测试用例**：
```python
# 前提：仿真已启动
case_id = "case_20251116_224458"
simulation_id = "batch_batch_20251116_232836_plan_morning_peak_..."

# 调用新API
progress = await service.get_simulation_progress_detail(case_id, simulation_id)

# 验证
assert progress['status'] == 'running'
assert 'percent' in progress
assert 'message' in progress
assert progress['case_id'] == case_id
```

## 用户体验改进

| 场景 | 改进 |
|------|------|
| 仿真启动 | ✓ 前端正确保存仿真ID |
| 进度显示 | ✓ 进度条实时更新显示百分比 |
| 状态更新 | ✓ 实时获取状态变化 |
| 完成/失败 | ✓ 正确检测并显示完成/失败信息 |
| 错误处理 | ✓ 进度查询失败有日志记录 |

## 关键改进

### 1. API职责分离
- **汇总API**：监控多个仿真的总体进度
- **详细API**：单个仿真的实时进度监控

### 2. 前端数据流

```
启动仿真
  ↓
获取仿真ID (simulation_id)
  ↓
保存到 currentSim.simulationId
  ↓
轮询查询 /simulation_progress/{case_id}/{simulation_id}
  ↓
更新进度条
```

### 3. 错误恢复

前端轮询异常时：
```javascript
catch (e) {
    console.error('轮询仿真进度失败:', e);
    // 不中断，继续轮询
}
```

后端进度文件不存在时：
```python
if progress_file.exists():
    # 读取progress.json
else:
    # 使用元数据中的状态
    sim["percent"] = 100 if sim.get("status") == "completed" else 0
```

## 部署步骤

1. **后端**
   ```bash
   # 修改已完成，只需重启API服务
   python api/main.py
   ```

2. **前端**
   ```bash
   # 前端代码已修改，页面刷新后自动生效
   # 无需额外部署
   ```

## 总结

此修复完全解决了OD仿真进度无法正确显示的问题：

- ✅ 前端使用正确的API获取单个仿真详细进度
- ✅ API返回的格式与前端期望完全匹配
- ✅ 支持普通仿真和批次仿真
- ✅ 进度条能正确实时显示百分比
- ✅ 完全向后兼容，无需迁移
- ✅ 充分的错误处理和日志记录
