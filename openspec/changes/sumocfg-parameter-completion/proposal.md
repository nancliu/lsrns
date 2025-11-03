# SUMOCFG参数完整性修复 - OpenSpec Change Proposal

**Change ID:** `sumocfg-parameter-completion`
**Status:** 🟡 Proposal (Planning Phase)
**Priority:** P0 (Critical - Blocks production use of output parameters)
**Scope:** Backend parameter handling and SUMO config generation
**Estimated Effort:** 12-16 hours
**Date:** 2025-11-03

---

## 📋 Executive Summary

当前批量仿真系统中,前端成功收集了仿真配置参数(仿真时长、车辆模板、输出选项等),但后端处理存在**4个关键问题**导致这些参数无法正确应用到SUMO配置文件生成中。

**整体参数完整度: 35%** (仅1/10参数完全实现)

此change致力于修复这些问题,使所有配置参数能够完整流转从前端→后端→sumocfg.xml。

---

## 🔴 当前问题

### 问题1: 5个输出参数的键名映射错误 (P0)

**症状:**
- 前端: output_tripinfo ✅
- 后端: 映射为 tripinfo_xml ❌
- sumocfg: 期望 output_tripinfo ❌

**影响:** tripinfo.xml、vehroute.xml等输出始终不生成

**位置:** `api/services/batch_optimization_service.py` L152-155

**代码现状:**
```python
"tripinfo_xml": output_level in ["standard", "full"],
"edgedata_xml": output_level in ["standard", "full"],
```

### 问题2: simulation_params接收链断裂 (P0)

**症状:**
- simulation_config.json生成了正确的键值
- 但从未传递给sumocfg生成函数
- sumocfg完全无法感知这些配置

**影响:** output_*参数全部失效

**位置:** `batch_optimization_service.py` L167-171 & `simulation_service.py` (调用处)

### 问题3: simulation_duration完全未实现 (P1)

**前端:** ✅ 已完成 (Revision 6 - HTML输入框+JavaScript收集)
**后端:** ❌ 0% 未实现
- CreateBatchRequest未包含此字段
- create_batch()未接收此参数
- sumocfg使用硬编码计算: `duration = (end_dt - start_dt).total_seconds()`

**影响:** 用户无法自定义仿真时长,始终使用case元数据计算的时长

### 问题4: vehicle_types_template完全未实现 (P1)

**前端:** ✅ 已完成 (Revision 2 - API加载+下拉菜单)
**后端:** ❌ 0% 未实现
- CreateBatchRequest未包含此字段
- create_batch()未接收此参数
- rou.xml生成时硬编码使用默认模板

**影响:** 用户无法使用自定义车辆参数配置,始终使用vehicle_types.json

---

## 📊 参数完整度矩阵

| 参数 | 前端支持 | API模型 | 后端处理 | simulation_params | sumocfg应用 | 完整度 | 优先级 |
|------|--------|--------|--------|-----------------|-----------|-------|-------|
| output_edgedata | ✅ | ❌ | ✅ | ✅ | ✅ | 100% | - |
| output_tripinfo | ✅ | ❌ | ⚠️ | ❌ | ✅ | 40% | P0 |
| output_vehroute | ✅ | ❌ | ⚠️ | ❌ | ✅ | 40% | P0 |
| output_netstate | ✅ | ❌ | ⚠️ | ❌ | ✅ | 40% | P0 |
| output_fcd | ✅ | ❌ | ⚠️ | ❌ | ✅ | 40% | P0 |
| output_emission | ✅ | ❌ | ⚠️ | ❌ | ✅ | 40% | P0 |
| **simulation_duration** | ✅ | ❌ | ❌ | ❌ | ❌ | 20% | P1 |
| **vehicle_types_template** | ✅ | ❌ | ❌ | ❌ | ❌ | 20% | P1 |
| edgedata_use_template_edges | ❌ | ❌ | ❌ | ❌ | ✅ | 25% | P2 |
| additional_file | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | 80% | - |

**加权完整度: 35%** (1×100% + 5×40% + 2×20% + 1×25% + 1×80%) ÷ 10 = 3.5/10

---

## 🎯 修复目标

### 短期目标 (P0 - Sprint 1)
- ✅ 修复5个output_*参数的键名映射
- ✅ 建立参数从simulation_config到sumocfg的传递链
- ✅ 验证tripinfo.xml、vehroute.xml等正确输出
- **预期完整度:** 35% → 55%

### 中期目标 (P1 - Sprint 2)
- ✅ 实现simulation_duration参数完整支持
- ✅ 实现vehicle_types_template参数完整支持
- ✅ 更新API模型和验证逻辑
- **预期完整度:** 55% → 75%

### 长期目标 (P2 - Sprint 3)
- ✅ 整合孤立的edgedata_use_template_edges参数
- ✅ 添加前端UI支持
- **预期完整度:** 75% → 85%+

---

## 📂 相关代码位置

### 核心实现文件

| 文件 | 行号 | 功能 | 问题 |
|------|------|------|------|
| `shared/utilities/sumo_utils.py` | 78-330 | generate_sumocfg_for_simulation() | 无法接收output_*和simulation_duration |
| `batch_optimization_service.py` | 71-205 | create_batch() | 键名映射错误,参数未传递 |
| `batch_optimization_service.py` | 146-157 | unified_simulation_config生成 | tripinfo_xml等键名错误 |
| `simulation_service.py` | ~ | prepare_simulation() | 未传递simulation_params |
| `api/models/.../batch_request.py` | ~ | CreateBatchRequest | 缺少simulation_duration等字段 |

### 相关API端点

| 端点 | 文件 | 功能 | 状态 |
|------|------|------|------|
| POST /api/v1/control/batch-optimization/batch | batch_optimization_routes.py | 创建批次 | ✅ 已实现,但参数处理不完 |
| GET /api/v1/control/batch-optimization/cases/{case_id}/duration | batch_optimization_routes.py | 获取案例时长 | ✅ 已实现 |
| GET /api/v1/control/batch-optimization/templates/vehicle-types | batch_optimization_routes.py | 获取车辆模板列表 | ✅ 已实现 |

---

## 🔧 技术方案概述

### 方案1: P0修复 (output_*参数)

**步骤1: 修复键名**
```python
# 修改 batch_optimization_service.py L152-157
unified_simulation_config = {
    "summary_xml": True,
    "e1_detector_data": True,
    "output_tripinfo": output_config.get('tripinfo_xml', False),  # 修复
    "output_vehroute": output_config.get('vehroute_xml', False),  # 新增
    "output_netstate": output_config.get('netstate_xml', False),  # 新增
    "output_fcd": output_config.get('fcd_xml', False),             # 新增
    "output_emission": output_config.get('emission_xml', False),   # 新增
    "output_edgedata": output_config.get('edgedata_xml', False),
}
```

**步骤2: 传递simulation_params**
```python
# 在 simulation_service.py中构建simulation_params
simulation_params = {
    'output_tripinfo': simulation_config.get('output_tripinfo', False),
    'output_vehroute': simulation_config.get('output_vehroute', False),
    # ... 其他参数
}
# 传递给 generate_sumocfg_for_simulation()
```

### 方案2: P1修复 (simulation_duration)

**步骤1: 修改API模型**
```python
class CreateBatchRequest(BaseModel):
    # ... 现有字段 ...
    simulation_duration: Optional[Dict[str, int]] = None  # {hours, minutes, total_minutes}
```

**步骤2: 修改sumocfg生成**
```python
# 在 generate_sumocfg_for_simulation() 中
if simulation_params.get('simulation_duration'):
    duration = simulation_params['simulation_duration']['total_minutes'] * 60
else:
    # 原有逻辑
    duration = int((end_dt - start_dt).total_seconds())
```

### 方案3: P1修复 (vehicle_types_template)

**步骤1: 修改API模型**
```python
class CreateBatchRequest(BaseModel):
    # ... 现有字段 ...
    vehicle_types_template: Optional[str] = "vehicle_types.json"
```

**步骤2: 修改rou.xml生成**
- 需要在data_service或新增service中支持动态模板加载
- 从 `templates/config_templates/vehicle_templates/{template_name}` 读取
- 在生成rou.xml时应用此模板

---

## 📝 验收标准

### P0修复验收标准
- [ ] 修改后tripinfo.xml输出可正常启用/禁用
- [ ] vehroute.xml、netstate.xml等输出正常工作
- [ ] sumocfg.xml中包含所有选中的输出元素
- [ ] 集成测试通过
- [ ] 参数完整度: 35% → 55%

### P1修复验收标准
- [ ] 用户可自定义仿真时长
- [ ] 用户可选择不同车辆模板
- [ ] rou.xml正确应用选中的模板
- [ ] sumocfg.xml使用自定义时长而非硬编码
- [ ] 参数完整度: 55% → 75%

### P2修复验收标准
- [ ] edgedata_use_template_edges参数可通过前端控制
- [ ] 参数完整度: 75% → 85%+

---

## ⚠️ 风险与缓解

### 风险1: 向后兼容性
**风险:** 修改参数键名可能影响既有批次
**缓解:**
- 使用migration脚本更新existing simulation_config.json
- 添加兼容性检查

### 风险2: 参数验证
**风险:** 无效参数导致sumocfg生成失败
**缓解:**
- 添加全面的参数验证
- 编写单元测试覆盖所有参数组合

### 风险3: 性能影响
**风险:** 新增参数处理可能增加处理时间
**缓解:**
- 参数处理都是简单的字典操作,性能影响微乎其微
- 添加性能基准测试

---

## 📚 相关文档

- ✅ 详细分析报告: `docs/SUMOCFG_PARAMETER_ANALYSIS.md` (255行)
- ✅ 批量仿真OpenSpec: `openspec/changes/batch-simulation-enhancement/spec.md`
- ✅ sumocfg生成代码: `shared/utilities/sumo_utils.py`

---

## 🤝 所有者与利益相关者

| 角色 | 所有者 |
|------|--------|
| 提案人 | 技术团队 |
| 审核人 | 项目经理 |
| 实现人 | 后端开发 |
| QA负责人 | QA团队 |

---

## ✅ 检查清单

- [x] 问题已充分分析和文档化
- [x] 参数完整度矩阵已建立
- [x] 修复优先级已确定
- [x] 技术方案已概述
- [ ] 详细的spec.md已编写 (待下一步)
- [ ] tasks.md已编写 (待下一步)
- [ ] design.md已编写 (待下一步)

---

**提案状态:** 🟡 Ready for Review (等待design.md和tasks.md)
**下一步:** 使用 `/openspec:apply` 创建完整的change定义
