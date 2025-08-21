# 标定功能 API 接口参考

## 📋 概述

本文档详细描述SUMO参数标定功能的API接口，包括请求参数、响应格式、错误码等信息。

## 🔗 基础信息

- **基础URL**: `/api/v1/calibration`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **认证方式**: 待定（根据现有系统配置）

## 📡 API 接口列表

### 1. 创建标定任务

#### 接口信息
- **URL**: `POST /api/v1/calibration/create`
- **描述**: 创建新的SUMO参数标定任务
- **请求方式**: POST

#### 请求参数

```json
{
    "case_id": "string",
    "scenario": "string",
    "network_file": "string",
    "taz_file": "string",
    "simulation_duration": "integer",
    "output_config": "object",
    "initial_samples": "integer",
    "max_generations": "integer",
    "custom_parameter_ranges": "object",
    "parallel_workers": "integer",
    "convergence_threshold": "number"
}
```

#### 参数说明

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| case_id | string | 是 | - | 案例ID |
| scenario | string | 否 | "mixed_traffic" | 交通场景类型 |
| network_file | string | 是 | - | 网络文件路径 |
| taz_file | string | 是 | - | TAZ文件路径 |
| simulation_duration | integer | 否 | 7200 | 仿真时长（秒） |
| output_config | object | 否 | 默认配置 | 输出配置 |
| initial_samples | integer | 否 | 100 | 初始采样数量 |
| max_generations | integer | 否 | 100 | 最大优化代数 |
| custom_parameter_ranges | object | 否 | null | 自定义参数范围 |
| parallel_workers | integer | 否 | 4 | 并行工作进程数 |
| convergence_threshold | number | 否 | 0.01 | 收敛阈值 |

#### 场景类型枚举

```json
{
    "scenario": {
        "high_traffic": "高流量拥堵场景",
        "low_traffic": "低流量畅通场景", 
        "mixed_traffic": "混合交通场景"
    }
}
```

#### 输出配置对象

```json
{
    "output_config": {
        "summary": true,      // 是否输出summary文件
        "tripinfo": true,     // 是否输出tripinfo文件
        "vehroute": false,    // 是否输出vehroute文件
        "queue": false        // 是否输出queue文件
    }
}
```

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/calibration/create" \
     -H "Content-Type: application/json" \
     -d '{
         "case_id": "case_001",
         "scenario": "high_traffic",
         "network_file": "templates/network_files/sichuan202503v5.net.xml",
         "taz_file": "templates/taz_files/TAZ_5_validated.add.xml",
         "simulation_duration": 7200,
         "initial_samples": 100,
         "max_generations": 100,
         "parallel_workers": 4
     }'
```

#### 响应格式

**成功响应** (200):
```json
{
    "success": true,
    "message": "标定任务创建成功",
    "data": {
        "task_id": "calibration_case_001_20241201_143022",
        "status": "running"
    }
}
```

**失败响应** (400/500):
```json
{
    "success": false,
    "message": "创建标定任务失败: 案例不存在",
    "error_code": "CASE_NOT_FOUND"
}
```

### 2. 查询标定任务状态

#### 接口信息
- **URL**: `GET /api/v1/calibration/status/{task_id}`
- **描述**: 查询指定标定任务的执行状态
- **请求方式**: GET

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| task_id | string | 是 | 标定任务ID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/calibration/status/calibration_case_001_20241201_143022"
```

#### 响应格式

**成功响应** (200):
```json
{
    "success": true,
    "data": {
        "task_id": "calibration_case_001_20241201_143022",
        "case_id": "case_001",
        "status": "running",
        "start_time": "2024-12-01T14:30:22",
        "progress": 45,
        "config": {
            "scenario": "high_traffic",
            "initial_samples": 100,
            "max_generations": 100
        }
    }
}
```

**任务状态说明**:
- `pending`: 等待执行
- `running`: 正在执行
- `completed`: 执行完成
- `failed`: 执行失败
- `cancelled`: 已取消

**失败响应** (404):
```json
{
    "success": false,
    "message": "标定任务不存在"
}
```

### 3. 获取标定结果

#### 接口信息
- **URL**: `GET /api/v1/calibration/results/{case_id}`
- **描述**: 获取指定案例的标定结果
- **请求方式**: GET

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| case_id | string | 是 | 案例ID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/calibration/results/case_001"
```

#### 响应格式

**成功响应** (200):
```json
{
    "success": true,
    "data": {
        "calibration_results": {
            "initial_parameters": [...],
            "initial_results": [...],
            "optimization_result": {
                "best_individual": {...},
                "history": [...]
            },
            "best_parameters": {...}
        },
        "analysis_report": {
            "analysis_type": "calibration",
            "case_id": "case_001",
            "timestamp": "2024-12-01T15:45:30",
            "metrics": {
                "flow_error": 0.12,
                "delay_error": 0.08,
                "insertion_rate": 0.97,
                "network_utilization": 0.85
            },
            "best_parameters": {...},
            "optimization_history": [...],
            "recommendations": [
                "流量误差较大，建议调整departSpeed和departLane参数"
            ]
        },
        "best_parameters": {
            "departSpeed": 2.5,
            "departLane": "random",
            "minGap": 1.8,
            "sigma": 0.25,
            "impatience": 0.6,
            "laneChangeMode": 512,
            "maxDepartDelay": 450
        }
    }
}
```

**失败响应** (404):
```json
{
    "success": false,
    "message": "未找到标定结果"
}
```

### 4. 获取活跃标定任务列表

#### 接口信息
- **URL**: `GET /api/v1/calibration/active-tasks`
- **描述**: 获取当前系统中所有活跃的标定任务
- **请求方式**: GET

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/calibration/active-tasks"
```

#### 响应格式

**成功响应** (200):
```json
{
    "success": true,
    "data": {
        "active_tasks": [
            {
                "task_id": "calibration_case_001_20241201_143022",
                "case_id": "case_001",
                "status": "running",
                "start_time": "2024-12-01T14:30:22",
                "progress": 45
            },
            {
                "task_id": "calibration_case_002_20241201_144500",
                "case_id": "case_002",
                "status": "completed",
                "start_time": "2024-12-01T14:45:00",
                "end_time": "2024-12-01T15:30:00",
                "progress": 100
            }
        ]
    }
}
```

### 5. 取消标定任务

#### 接口信息
- **URL**: `DELETE /api/v1/calibration/cancel/{task_id}`
- **描述**: 取消正在执行的标定任务
- **请求方式**: DELETE

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| task_id | string | 是 | 标定任务ID |

#### 请求示例

```bash
curl -X DELETE "http://localhost:8000/api/v1/calibration/cancel/calibration_case_001_20241201_143022"
```

#### 响应格式

**成功响应** (200):
```json
{
    "success": true,
    "message": "标定任务已取消"
}
```

**失败响应** (400):
```json
{
    "success": false,
    "message": "只能取消正在运行的任务"
}
```

**失败响应** (404):
```json
{
    "success": false,
    "message": "标定任务不存在"
}
```

## 📊 数据模型

### 1. 标定请求模型 (CalibrationRequest)

```python
class CalibrationRequest(BaseModel):
    case_id: str
    scenario: TrafficScenario = TrafficScenario.MIXED_TRAFFIC
    network_file: str
    taz_file: str
    simulation_duration: int = 7200
    output_config: OutputConfig = OutputConfig()
    initial_samples: int = 100
    max_generations: int = 100
    custom_parameter_ranges: Optional[Dict[str, Any]] = None
    parallel_workers: int = 4
    convergence_threshold: float = 0.01
```

### 2. 输出配置模型 (OutputConfig)

```python
class OutputConfig(BaseModel):
    summary: bool = True
    tripinfo: bool = True
    vehroute: bool = False
    queue: bool = False
```

### 3. 交通场景枚举 (TrafficScenario)

```python
class TrafficScenario(str, Enum):
    HIGH_TRAFFIC = "high_traffic"
    LOW_TRAFFIC = "low_traffic"
    MIXED_TRAFFIC = "mixed_traffic"
```

### 4. 基础响应模型 (BaseResponse)

```python
class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
```

## ⚠️ 错误码说明

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| CASE_NOT_FOUND | 404 | 案例不存在 |
| TASK_NOT_FOUND | 404 | 标定任务不存在 |
| INVALID_CONFIG | 400 | 配置参数无效 |
| SIMULATION_FAILED | 500 | 仿真执行失败 |
| OPTIMIZATION_FAILED | 500 | 优化算法失败 |
| INSUFFICIENT_RESOURCES | 503 | 系统资源不足 |
| TASK_ALREADY_RUNNING | 409 | 任务已在运行中 |
| CANNOT_CANCEL_COMPLETED | 400 | 无法取消已完成的任务 |

## 🔄 状态流转图

```
创建任务 → 等待执行 → 正在执行 → 执行完成
    ↓           ↓         ↓         ↓
  成功        pending   running   completed
    ↓           ↓         ↓         ↓
  失败        failed    failed    failed
    ↓           ↓         ↓         ↓
  取消        cancelled cancelled cancelled
```

## 📈 性能指标

### 1. 响应时间要求

- **创建任务**: < 1秒
- **查询状态**: < 100ms
- **获取结果**: < 500ms
- **任务列表**: < 200ms

### 2. 并发处理能力

- **最大并发任务数**: 10个
- **单任务最大执行时间**: 24小时
- **任务队列容量**: 100个

### 3. 资源限制

- **单任务最大内存使用**: 8GB
- **单任务最大CPU使用**: 4核
- **磁盘空间要求**: 每个任务预留2GB

## 🔐 安全考虑

### 1. 访问控制

- 所有接口需要用户认证
- 用户只能访问自己创建的案例
- 管理员可以访问所有案例

### 2. 输入验证

- 所有输入参数进行类型和范围验证
- 文件路径进行安全检查，防止路径遍历攻击
- 参数值进行合理性检查

### 3. 资源限制

- 限制单个用户的并发任务数
- 限制任务的最大执行时间
- 监控系统资源使用情况

## 📝 使用示例

### 1. Python客户端示例

```python
import requests
import json

class CalibrationClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_calibration_task(self, case_id: str, **kwargs):
        """创建标定任务"""
        url = f"{self.base_url}/api/v1/calibration/create"
        
        data = {
            "case_id": case_id,
            **kwargs
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_task_status(self, task_id: str):
        """获取任务状态"""
        url = f"{self.base_url}/api/v1/calibration/status/{task_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_results(self, case_id: str):
        """获取标定结果"""
        url = f"{self.base_url}/api/v1/calibration/results/{case_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()

# 使用示例
client = CalibrationClient("http://localhost:8000")

# 创建标定任务
task = client.create_calibration_task(
    case_id="case_001",
    scenario="high_traffic",
    network_file="network.net.xml",
    taz_file="taz.add.xml"
)

task_id = task["data"]["task_id"]

# 轮询任务状态
while True:
    status = client.get_task_status(task_id)
    if status["data"]["status"] in ["completed", "failed"]:
        break
    time.sleep(10)

# 获取结果
if status["data"]["status"] == "completed":
    results = client.get_results("case_001")
    print("标定完成:", results["data"]["best_parameters"])
```

### 2. JavaScript客户端示例

```javascript
class CalibrationClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async createCalibrationTask(caseId, options = {}) {
        const url = `${this.baseUrl}/api/v1/calibration/create`;
        
        const data = {
            case_id: caseId,
            ...options
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getTaskStatus(taskId) {
        const url = `${this.baseUrl}/api/v1/calibration/status/${taskId}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getResults(caseId) {
        const url = `${this.baseUrl}/api/v1/calibration/results/${caseId}`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
}

// 使用示例
const client = new CalibrationClient('http://localhost:8000');

async function runCalibration() {
    try {
        // 创建标定任务
        const task = await client.createCalibrationTask('case_001', {
            scenario: 'high_traffic',
            network_file: 'network.net.xml',
            taz_file: 'taz.add.xml'
        });
        
        const taskId = task.data.task_id;
        console.log('任务创建成功:', taskId);
        
        // 轮询任务状态
        const checkStatus = async () => {
            const status = await client.getTaskStatus(taskId);
            console.log('任务状态:', status.data.status, '进度:', status.data.progress);
            
            if (status.data.status === 'completed') {
                const results = await client.getResults('case_001');
                console.log('标定完成:', results.data.best_parameters);
            } else if (status.data.status === 'failed') {
                console.error('标定失败:', status.data.error);
            } else {
                setTimeout(checkStatus, 10000); // 10秒后再次检查
            }
        };
        
        checkStatus();
        
    } catch (error) {
        console.error('标定执行失败:', error);
    }
}

runCalibration();
```

## 📚 相关文档

- [标定功能集成指南](./integration_guide.md)
- [标定策略设计](../design/calibration_strategy.md)
- [参数影响分析](../design/parameter_analysis.md)
- [评估指标定义](../design/evaluation_metrics.md)
- [项目架构文档](../../development/新架构开发指南.md)
