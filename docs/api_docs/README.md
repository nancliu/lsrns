# API文档

## 概述

OD数据处理与仿真系统提供RESTful API接口，支持案例管理、仿真控制、数据分析等功能。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

当前版本API无需认证，后续版本将支持JWT认证。

## 响应格式

所有API响应都遵循统一格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据
  }
}
```

## 错误处理

### HTTP状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## API端点分类

### 1. 数据处理API

- `POST /process_od_data/` - 处理OD数据
- `POST /run_simulation/` - 运行仿真
- `POST /analyze_accuracy/` - 精度分析

### 2. 案例管理API

- `POST /create_case/` - 创建案例
- `GET /list_cases/` - 获取案例列表
- `GET /case/{case_id}` - 获取案例详情
- `DELETE /case/{case_id}` - 删除案例
- `POST /case/{case_id}/clone` - 克隆案例

### 3. 文件管理API

- `GET /get_folders/{prefix}` - 获取文件夹列表

### 4. 分析结果API

- `GET /analysis_results/{case_id}` - 按类型列出案例的历史分析结果（参数：`analysis_type=accuracy|mechanism|performance`）

### 5. 模板管理API

- `GET /templates/taz` - 获取TAZ模板
- `GET /templates/network` - 获取网络模板
- `GET /templates/simulation` - 获取仿真模板

 

## 数据模型

### 请求模型

#### TimeRangeRequest
```json
{
  "start_time": "2025/07/21 08:00:00",
  "end_time": "2025/07/21 09:00:00",
  "schemas_name": "dwd",
  "interval_minutes": 5
}
```

#### SimulationRequest
```json
{
  "run_folder": "cases/case_20250108_120000/simulation",
  "gui": false,
  "simulation_type": "microscopic"
}
```

#### CaseCreationRequest
```json
{
  "time_range": {
    "start": "2025/07/21 08:00:00",
    "end": "2025/07/21 09:00:00"
  },
  "config": {},
  "case_name": "测试案例",
  "description": "这是一个测试案例"
}
```

### 响应模型

#### CaseMetadata
```json
{
  "case_id": "case_20250108_120000",
  "case_name": "测试案例",
  "created_at": "2025-01-08T12:00:00",
  "updated_at": "2025-01-08T12:30:00",
  "time_range": {
    "start": "2025/07/21 08:00:00",
    "end": "2025/07/21 09:00:00"
  },
  "config": {},
  "status": "created",
  "description": "这是一个测试案例",
  "statistics": {},
  "files": {}
}
```

## 使用示例

### 创建案例

```bash
curl -X POST "http://localhost:8000/api/v1/create_case/" \
  -H "Content-Type: application/json" \
  -d '{
    "time_range": {
      "start": "2025/07/21 08:00:00",
      "end": "2025/07/21 09:00:00"
    },
    "config": {},
    "case_name": "测试案例",
    "description": "这是一个测试案例"
  }'
```

### 获取案例列表

```bash
curl "http://localhost:8000/api/v1/list_cases/?page=1&page_size=10"
```

### 运行仿真

```bash
curl -X POST "http://localhost:8000/api/v1/run_simulation/" \
  -H "Content-Type: application/json" \
  -d '{
    "run_folder": "cases/case_20250108_120000/simulation",
    "gui": false,
    "simulation_type": "microscopic"
  }'
```

## 速率限制

当前版本无速率限制，后续版本将根据需求添加。

## 版本控制

API版本通过URL路径控制，当前版本为v1。

## 更新日志

### v1.0.0 (2025-01-08)
- 初始版本发布
- 支持案例管理
- 支持仿真控制
- 支持精度分析
- 支持模板管理
 

## 更多信息

- [数据模型详细说明](data_models.md)
- [API端点详细文档](api_endpoints.md)
- [错误处理指南](error_handling.md) 