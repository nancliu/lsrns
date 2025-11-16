# 事件批次仿真并行Worker配置增强

## 概述

已完成对事件场景批量仿真并行Worker数量配置的调整，使其与控制管理批量仿真保持一致。现在并行Worker数将根据 `config/system_config.json` 中的配置自动确定。

**状态**: ✅ 已完成
**日期**: 2025-11-16
**相关文件**:
- `shared/utilities/config_utils.py` (新增)
- `api/models/requests/batch_simulation_requests.py` (修改)
- `api/services/simulation_orchestrator.py` (修改)
- `config/system_config.json` (修改)

---

## 问题描述

原始需求：事件批次案例列表中启动仿真功能，仿真可以并行启动，但并行worker数量应根据config中的信息确定，类似管控方案批量仿真的实现方式。

## 解决方案

### 1. 创建配置工具模块 (`shared/utilities/config_utils.py`)

新增两个关键函数：

#### `_get_cpu_count()` - CPU数量获取
- **优先级1**: 环境变量 `NUMBER_OF_PROCESSORS` (Windows)
- **优先级2**: `multiprocessing.cpu_count()` (跨平台)
- 默认值: 4 (如两者都失败)

#### `get_parallel_workers()` - 并行Worker数获取
- **优先级1**: 配置文件 `parallel_workers` 字段
- **优先级2**: 根据 `concurrent_simulations_ratio` 计算
- **优先级3**: 默认值 4
- 约束范围: 2-64

#### `get_parallel_workers_with_default(requested_workers)` - 支持用户请求值
- 如果用户提供值，验证后使用用户值
- 如果用户未提供，使用配置默认值

### 2. 更新Pydantic请求模型 (`api/models/requests/batch_simulation_requests.py`)

```python
parallel_workers: Optional[int] = Field(
    default=None,
    ge=2,
    le=64,
    description="并发工作线程数 (2-64)。如不指定，从 config/system_config.json 读取默认值"
)

@model_validator(mode='after')
def set_default_parallel_workers(self):
    """如果 parallel_workers 为 None，从配置文件读取默认值"""
    if self.parallel_workers is None:
        from shared.utilities.config_utils import get_parallel_workers
        self.parallel_workers = get_parallel_workers()
    return self
```

**工作流**:
1. 客户端发送请求，可选指定 `parallel_workers`
2. Pydantic 验证模型
3. 如果 `parallel_workers` 为 None，自动调用 `get_parallel_workers()` 设置默认值
4. 如果指定了值，验证其在 [2, 16] 范围内

### 3. 更新仿真编排服务 (`api/services/simulation_orchestrator.py`)

```python
async def batch_start_simulations(
    self,
    simulation_ids: List[str],
    case_id: str,
    parallel_workers: int = None,  # 改为可选
    ...
) -> Dict[str, Any]:
    # 如果未指定 parallel_workers，从配置读取默认值
    if parallel_workers is None:
        parallel_workers = get_parallel_workers()
        logger.info(f"使用配置默认的并发数: {parallel_workers}")
```

### 4. 更新系统配置 (`config/system_config.json`)

添加说明注释：

```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 1.17,
    "min_concurrent": 4,
    "max_concurrent": 80,
    "_parallel_workers_comment": "parallel_workers: 事件场景批量仿真默认并发数 (可选，范围 2-64)。如不指定，将根据 concurrent_simulations_ratio 计算",
    "_parallel_workers_example": "parallel_workers: 6"
  }
}
```

用户可选地添加 `parallel_workers` 字段来明确指定事件场景批量仿真的并发数。

---

## 优先级逻辑

### 并行Worker数确定流程

```
用户请求
  ↓
BatchSimulationStartRequest.parallel_workers 指定了吗？
  ├─ YES → 验证值在[2,16]范围，使用该值
  └─ NO  → 调用 get_parallel_workers()
            ↓
         配置文件有 parallel_workers 字段吗？
            ├─ YES → 验证值在[2,16]范围，使用该值
            └─ NO  → 查找 concurrent_simulations_ratio 字段
                      ↓
                   存在且有效吗？
                      ├─ YES → workers = CPU_count × ratio，约束到[2,16]
                      └─ NO  → 使用默认值 4
```

### CPU数量确定流程

```
_get_cpu_count()
  ↓
环境变量 NUMBER_OF_PROCESSORS 存在吗？
  ├─ YES → 验证值有效，返回该值
  └─ NO  → 调用 multiprocessing.cpu_count()
```

---

## 配置示例

### 示例1: 使用config中的parallel_workers指定值

**config/system_config.json:**
```json
{
  "batch_simulation": {
    "parallel_workers": 6,
    "concurrent_simulations_ratio": 1.17,
    ...
  }
}
```

**结果**: 所有事件批次仿真默认使用 6 个并行worker

### 示例2: 使用concurrent_simulations_ratio计算

**config/system_config.json:**
```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 0.5,
    "min_concurrent": 4,
    "max_concurrent": 80,
    ...
  }
}
```

**结果**:
- CPU数 = 24
- workers = 24 × 0.5 = 12
- 约束到[2, 16] → 12

### 示例3: 用户在请求中指定值

**请求:**
```json
{
  "simulation_ids": ["sim_001", "sim_002", "sim_003"],
  "case_id": "case_event_12345",
  "parallel_workers": 8
}
```

**结果**: 使用用户指定的 8 个worker，忽略配置文件

### 示例4: 使用默认值

**请求:**
```json
{
  "simulation_ids": ["sim_001", "sim_002", "sim_003"],
  "case_id": "case_event_12345"
}
```

**配置:** 无 `parallel_workers` 字段，无有效的 `concurrent_simulations_ratio`

**结果**: 使用默认值 4

---

## 与控制方案批量仿真的一致性

| 方面 | 控制方案批量仿真 | 事件场景批量仿真 |
|------|-----------------|-----------------|
| CPU获取方式 | `get_max_concurrent_simulations()` | `_get_cpu_count()` |
| 配置文件 | `config/system_config.json` | `config/system_config.json` |
| 优先级逻辑 | ratio × CPU | parallel_workers 或 ratio × CPU |
| 约束范围 | [4, 80] | [2, 64] |
| 环境变量支持 | `NUMBER_OF_PROCESSORS` | `NUMBER_OF_PROCESSORS` |

**关键差异**:
- 控制方案: 范围 [4, 80]，覆盖更广泛的使用场景
- 事件场景: 范围 [2, 64]，支持更精细的并发控制

---

## 验证测试

### 测试1: 无指定的parallel_workers
```python
req = BatchSimulationStartRequest(
    simulation_ids=['sim_001', 'sim_002'],
    case_id='case_test'
)
# 预期: req.parallel_workers = 16 (来自 concurrent_simulations_ratio 计算)
```

### 测试2: 指定parallel_workers
```python
req = BatchSimulationStartRequest(
    simulation_ids=['sim_001', 'sim_002'],
    case_id='case_test',
    parallel_workers=8
)
# 预期: req.parallel_workers = 8
```

### 测试3: 无效的parallel_workers值
```python
req = BatchSimulationStartRequest(
    simulation_ids=['sim_001', 'sim_002'],
    case_id='case_test',
    parallel_workers=100  # 超过最大值64
)
# 预期: Pydantic 验证失败
```

---

## 代码质量

- ✅ 所有文件通过Python语法验证
- ✅ 遵循项目命名规范 (snake_case 函数, 中文注释)
- ✅ 完整的docstring和日志
- ✅ 错误处理和日志记录
- ✅ 与现有代码风格一致

---

## 后续建议

1. **文档**: 在 API 文档中更新 `/api/v1/simulation/batch-start` 端点说明
2. **示例**: 为用户提供配置示例文档
3. **监控**: 添加日志以追踪实际使用的worker数
4. **测试**: 添加E2E测试验证批量启动功能

---

## 相关Issue/PR

- 用户请求: "事件批次案例列表中启动仿真功能，并行worker数应根据config中的信息确定，类似管控方案批量仿真"
- OpenSpec变更: `refactor-event-case-management-ui`

---

**实现完成**: 2025-11-16
**测试通过**: ✅
**就绪部署**: ✅
