# 导航和页面位置澄清

**日期**: 2025-10-26
**变更**: 优化前端导航命名和页面职责划分

---

## 调整内容

### 1. 侧边导航命名优化

**调整前**:
```
- 策略
- 方案 ✓
- 优化
```

**调整后**:
```
- 策略管理
- 方案管理 ✓
- 并行仿真
- 方案优化  (Phase 4)
```

**理由**:
- 更明确的功能描述，避免歧义
- 区分"并行仿真"（执行）和"方案优化"（评估分析）
- 与 `traffic_control_optimization_overview.md` 保持一致

---

### 2. 页面职责明确划分

| 页面 | 文件名 | 主要功能 | 与 case 关系 | Phase |
|------|--------|---------|-------------|-------|
| **策略管理** | `templates.html` | 创建/编辑策略实例 | 无关（全局资源） | Phase 1 |
| **方案管理** | `plans.html` | 组合策略、生成 XML | 无关（全局资源） | Phase 1 |
| **并行仿真** | `simulations.html` | 选择 case、运行仿真、监控进度、基础对比 | **强关联**（案例级操作） | Phase 2-3 |
| **方案优化** | `optimization.html` | 多目标评估、高级对比、排序推荐 | 基于批次结果 | Phase 4 |

---

### 3. 按钮文字优化

#### 方案详情页面底部按钮

**调整前**:
```
[删除方案]  [重新生成XML]  [用于批量仿真]
```

**调整后**:
```
[删除方案]  [重新生成XML]  [应用到仿真]
```

**交互逻辑**:
- 点击"应用到仿真"按钮
- 跳转到并行仿真页面（`simulations.html`）
- 自动预选当前方案
- 用户继续选择 case 和其他方案
- 启动批量仿真

---

## Case 引用时机澄清

### 结论：在并行仿真阶段引入 case ✅

**设计依据**:

1. **方案管理阶段**（Phase 1）:
   - 职责：策略组合、XML 生成
   - 数据性质：全局资源
   - 存储位置：`control_data/plans/`
   - **不涉及 case**

2. **并行仿真阶段**（Phase 2-3）:
   - 职责：在特定 case 上测试方案效果
   - 数据性质：案例级操作
   - 存储位置：`cases/{case_id}/simulations/plan_opti/`
   - **引入 case**

**API 证据**:
```json
// POST /api/v1/control/optimization/batch
{
  "case_id": "case_001",  // ← 这里引入 case
  "plan_ids": ["baseline_plan", "plan_001", "plan_002"],
  "num_seeds": 3,
  "base_seed": 66
}
```

**优势**:
- 一个方案可以在多个 case 上测试
- 一个 case 可以测试多个方案
- 方案和 case 解耦，复用性高

---

## 用户工作流

### 完整流程

```
1. 策略管理页面
   └─> 创建策略实例（如"K10-K15 限速 80km/h"）

2. 方案管理页面
   └─> 选择策略组合
   └─> 创建方案（如"早高峰综合管控方案A"）
   └─> 生成 control.add.xml
   └─> [可选] 点击"应用到仿真"

3. 并行仿真页面 ← 引入 case
   └─> 选择 case（如"case_20251025_001"）
   └─> 选择方案（基准 + 方案A + 方案B）
   └─> 配置仿真参数（种子数、并发数）
   └─> 启动批量仿真
   └─> 监控进度（实时更新）
   └─> 查看基础对比结果

4. 方案优化页面 (Phase 4)
   └─> 多目标评估
   └─> 高级对比分析
   └─> 智能排序推荐
```

---

## 目录结构映射

### 全局资源（不涉及 case）
```
control_data/
├── strategies/              # 策略实例
│   └── {strategy_id}.json
└── plans/                   # 方案
    └── {plan_id}/
        ├── plan_metadata.json
        ├── strategy_refs.json
        └── control.add.xml
```

### 案例级资源（关联 case）
```
cases/{case_id}/
└── simulations/
    └── plan_opti/           # 批量优化仿真
        └── {batch_id}/
            ├── batch_metadata.json
            ├── baseline_plan/
            │   ├── sim_66/
            │   ├── sim_67/
            │   └── sim_68/
            ├── plan_001/
            │   ├── sim_66/
            │   ├── sim_67/
            │   └── sim_68/
            └── plan_002/
                ├── sim_66/
                ├── sim_67/
                └── sim_68/
```

---

## 前端文件对应

```
frontend/control/
├── templates.html       # 策略管理（Phase 1A）
├── plans.html          # 方案管理（Phase 1B）
├── simulations.html    # 并行仿真（Phase 2-3）← 本次新增
└── optimization.html   # 方案优化（Phase 4）
```

---

## 前端访问URL路径

**重要**: 所有管控优化相关页面必须使用 `/control/` 前缀访问

| 功能模块 | 页面文件 | 访问URL | Phase | 状态 |
|---------|---------|---------|-------|------|
| **策略管理** | `templates.html` | `http://localhost:8000/control/templates.html` | Phase 1A | ✅ 已实现 |
| **方案管理** | `plans.html` | `http://localhost:8000/control/plans.html` | Phase 1B | ✅ 已实现 |
| **并行仿真** | `simulations.html` | `http://localhost:8000/control/simulations.html` | Phase 2-3 | ✅ 已实现 |
| **方案优化** | `optimization.html` | `http://localhost:8000/control/optimization.html` | Phase 4 | 🔜 待实现 |

### URL路径设计原则

1. **统一前缀**: 所有管控优化页面使用 `/control/` 前缀，与其他模块（如数据处理、案例管理）区分
2. **语义化命名**: URL直接反映功能模块名称（templates/plans/simulations/optimization）
3. **RESTful风格**: 与后端API路径 `/api/v1/control/` 保持一致的命名规范
4. **静态文件服务**: 由FastAPI的`StaticFiles`中间件处理，映射到`frontend/control/`目录

### 后端静态文件配置

```python
# api/main.py
from fastapi.staticfiles import StaticFiles

# 挂载整个frontend目录到根路径
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

**路径映射说明**:
- 物理文件位置: `frontend/control/templates.html`
- 访问URL: `http://localhost:8000/control/templates.html`
- 浏览器请求 `/control/templates.html` → FastAPI 查找 `frontend/control/templates.html` → 返回文件

**原理**: 由于`frontend`目录挂载到根路径`/`，所有`frontend/control/`下的文件自动映射到`/control/`URL路径

---

## 总结

✅ **侧边导航命名**：策略管理 → 方案管理 → 并行仿真 → 方案优化

✅ **Case 引用时机**：并行仿真阶段引入，方案管理阶段不涉及

✅ **页面职责清晰**：方案管理（全局资源）vs 并行仿真（案例级操作）

✅ **按钮文字优化**："用于批量仿真" → "应用到仿真"（跳转+预选）

✅ **设计一致性**：OpenSpec 与 overview.md 完全一致

---

**相关文档**:
- `docs/design/traffic_control_optimization_overview.md` - 总体设计
- `openspec/changes/implement-plan-management-and-batch-optimization/design.md` - 详细设计
- `openspec/changes/implement-plan-management-and-batch-optimization/specs/batch-optimization/spec.md` - 批量仿真规格
