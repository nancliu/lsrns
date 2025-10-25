# G4202 路段查询问题诊断报告

**日期**: 2025-10-25
**问题**: G4202路线查询不返回数据
**诊断状态**: ✅ **根本原因已找到**

---

## 问题描述

在Phase 3测试中，所有E2E测试因为G4202路线查询失败而被跳过：

```
❌ 查询失败: {
  detail: {
    error: 'VALIDATION_ERROR',
    message: '1 validation error for EdgeInfoResponse\nroute_code\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]'
  }
}
```

---

## 诊断过程

### 1. 测试路线列表API ✅

```bash
GET /api/v1/control/edges/routes
```

**结果**: 成功
```json
{
  "route_code": "G4202",
  "edge_count": 1198
}
```

**结论**: G4202路线存在，数据库中有1198条边数据。

---

### 2. 测试路段查询API ❌

```bash
GET /api/v1/control/edges/query?route_code=G4202
```

**结果**: HTTP 400 Bad Request
```
Pydantic ValidationError:
  route_code: Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

**问题**: API参数名称错误！

---

## 根本原因分析

### 原因1: API参数名称不匹配 ⚠️

**测试使用的参数**:
```
?route_code=G4202&direction=0
```

**API实际接受的参数** (api/routes/control_strategy_routes.py:115-127):
```python
@router.get("/edges/query", response_model=EdgeQueryResponse)
async def query_edges(
    route_codes: str = Query(None, ...),      # ❌ 不是 route_code
    route_direction: str = Query(None, ...),  # ❌ 不是 direction
    ...
):
```

**正确的参数名**:
- `route_codes` (复数)
- `route_direction` (不是direction)

---

### 原因2: 数据库中存在route_code为NULL的记录 🔍

**代码路径**: `shared/data_access/edge_query.py:174-186`

```python
for row in rows:
    edge = EdgeInfo(
        edge_id=str(row[0]),
        route_code=row[1],      # ⚠️ 如果row[1]是NULL，route_code会是None
        section_code=row[2],
        ...
    )
```

**Pydantic模型定义** (api/models/responses/edge_query_response.py:20):
```python
route_code: str = Field(..., description="Route code (e.g., G4202)")
                  # ^^^ 必填字段，不能是None
```

**问题**:
1. 当API参数错误（如`route_code`而非`route_codes`）时，查询变成**无过滤条件**
2. SQL查询返回所有路段，包括`route_code IS NULL`的记录
3. Pydantic模型验证失败，因为`route_code`不能为None

---

## SQL查询验证

### 检查NULL记录

```sql
-- 查看route_code为NULL的记录数
SELECT COUNT(*)
FROM dim.sim_network_edges
WHERE route_code IS NULL;
```

### 验证G4202数据存在

```sql
-- 验证G4202路线数据
SELECT COUNT(*),
       MIN(start_stake),
       MAX(end_stake)
FROM dim.sim_network_edges
WHERE route_code = 'G4202';
```

**预期结果**: 1198条记录

---

## 解决方案

### 方案A: 修复测试用例 (短期) ✅ **推荐**

**修改测试**:
```javascript
// ❌ 错误
const url = `${BASE_URL}/api/v1/control/edges/query?route_code=G4202`;

// ✅ 正确
const url = `${BASE_URL}/api/v1/control/edges/query?route_codes=G4202`;
```

**优点**:
- 立即可用
- 符合API设计

**缺点**:
- 不解决NULL数据问题

---

### 方案B: 在SQL中过滤NULL (中期) ✅ **推荐**

**修改**: `shared/data_access/edge_query.py:111`

```python
WHERE 1=1
  AND e.route_code IS NOT NULL  -- 添加此行
```

**优点**:
- 防止返回无效数据
- 提高数据质量

**缺点**:
- 需要修改核心查询逻辑

---

### 方案C: 修改Pydantic模型 (不推荐) ❌

```python
route_code: Optional[str] = Field(None, ...)
```

**优点**:
- 允许NULL值通过

**缺点**:
- 降低数据质量要求
- 可能影响前端逻辑

---

### 方案D: 清理数据库NULL记录 (长期) 🔍

```sql
-- 查找并修复NULL记录
UPDATE dim.sim_network_edges
SET route_code = '<unknown>'
WHERE route_code IS NULL;

-- 或删除无效记录
DELETE FROM dim.sim_network_edges
WHERE route_code IS NULL;
```

**优点**:
- 从根本解决数据质量问题

**缺点**:
- 需要DBA权限
- 可能影响现有数据

---

## 立即行动计划

### 1. 修复测试用例 ✅

**文件**: `tests/e2e/test_g4202_database_diagnosis.spec.js`

```diff
- ?route_code=G4202&direction=0
+ ?route_codes=G4202&route_direction=clockwise
```

### 2. 在边查询中过滤NULL ✅

**文件**: `shared/data_access/edge_query.py:111`

```python
WHERE 1=1
  AND e.route_code IS NOT NULL
```

### 3. 添加日志增强 ✅

**文件**: `shared/data_access/edge_query.py:167`

```python
logger.info(f"Executing edge query with {len(params)} filters")
logger.debug(f"SQL: {sql}")
logger.debug(f"Params: {params}")
```

---

## 测试验证清单

- [ ] 修复测试用例参数名称
- [ ] 重新运行诊断测试
- [ ] 验证G4202查询返回数据
- [ ] 验证其他路线查询正常
- [ ] 检查数据库NULL记录数量
- [ ] 应用SQL过滤补丁（如果有NULL记录）
- [ ] 重新运行Phase 3完整测试套件

---

## 相关文件

### 后端文件
- `api/routes/control_strategy_routes.py:115` - API端点定义
- `shared/data_access/edge_query.py:52-199` - 查询逻辑
- `api/models/responses/edge_query_response.py:12-66` - 响应模型

### 测试文件
- `tests/e2e/test_g4202_database_diagnosis.spec.js` - 诊断测试
- `tests/e2e/test_phase3_complete_workflow.spec.js` - Phase 3测试
- `tests/e2e/test_strategy_name_auto_generation.spec.js` - 名称生成测试
- `tests/e2e/test_strategy_description_auto_generation.spec.js` - 描述生成测试

---

## 总结

### 问题根源

1. **API参数名称不匹配**: 测试使用`route_code`，但API需要`route_codes`
2. **数据库数据质量问题**: 存在`route_code IS NULL`的记录
3. **Pydantic严格验证**: 模型不允许`route_code`为None

### 关键发现

✅ G4202路线数据存在（1198条记录）
✅ 路线列表API正常工作
❌ 路段查询API因参数错误和NULL数据导致失败
❌ 所有测试因相同问题被跳过

### 下一步

1. **立即**: 修复测试参数名称
2. **短期**: 在SQL中添加`route_code IS NOT NULL`过滤
3. **中期**: 检查并清理数据库NULL记录
4. **长期**: 添加数据质量监控

---

## 附件

- ✅ `test_g4202_database_diagnosis.spec.js` - 诊断测试文件
- ✅ 测试输出日志 (见上方)
- ⏳ SQL验证脚本 (待执行)
- ⏳ 修复补丁 (待创建)
