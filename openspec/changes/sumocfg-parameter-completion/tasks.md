# SUMOCFG参数完整性修复 - 任务清单

**Change ID:** `sumocfg-parameter-completion`
**Total Tasks:** 24
**Dependencies:** batch-simulation-enhancement (已完成)
**Execution Order:** Sequential with parallel opportunities

---

## 📌 优先级 P0 (Sprint 1) - 输出参数修复

### P0-1: 修改BatchOptimizationService键名映射
- [ ] 打开 `api/services/batch_optimization_service.py`
- [ ] 定位到 `create_batch()` 方法 (L71)
- [ ] 定位到 `unified_simulation_config` 构造 (L146-157)
- [ ] 修改键名:
  - [ ] tripinfo_xml → output_tripinfo
  - [ ] vehroute_xml → output_vehroute (新增)
  - [ ] netstate_xml → output_netstate (新增)
  - [ ] fcd_xml → output_fcd (新增)
  - [ ] emission_xml → output_emission (新增)
- [ ] 确保值来自正确的output_config字段
- [ ] 运行单元测试验证

**验收标准:**
- unified_simulation_config包含正确的键名
- 值正确映射自output_config

---

### P0-2: 从output_config读取output_vehroute等参数
- [ ] 打开 `api/services/batch_optimization_service.py`
- [ ] 修改L102-114的output_config处理逻辑
- [ ] 扩展output_config为dict,支持vehroute、netstate、fcd、emission字段
- [ ] 映射逻辑:
  - [ ] output_config['output_vehroute'] → unified_simulation_config['output_vehroute']
  - [ ] 其他同理

**验收标准:**
- output_config正确包含所有5个输出参数
- 映射逻辑正确传递到unified_simulation_config

---

### P0-3: 添加simulation_params构造逻辑
- [ ] 打开 `api/services/batch_optimization_service.py`
- [ ] 在 `create_batch()` 方法末尾添加simulation_params构造
- [ ] 代码片段:
  ```python
  simulation_params = {
      'output_tripinfo': unified_simulation_config.get('output_tripinfo', False),
      'output_vehroute': unified_simulation_config.get('output_vehroute', False),
      'output_netstate': unified_simulation_config.get('output_netstate', False),
      'output_fcd': unified_simulation_config.get('output_fcd', False),
      'output_emission': unified_simulation_config.get('output_emission', False),
      'output_edgedata': unified_simulation_config.get('output_edgedata', False),
  }
  ```
- [ ] 确保此dict保存到batch metadata中

**验收标准:**
- simulation_params正确构造
- 所有output_*参数包含在内

---

### P0-4: 修改SimulationService传递参数
- [ ] 打开 `api/services/simulation_service.py`
- [ ] 定位到 `prepare_simulation()` 或类似的sumocfg生成调用
- [ ] 修改调用以传递simulation_params:
  ```python
  # 从batch metadata读取simulation_params
  config_path = batch_dir / "simulation_config.json"
  with open(config_path) as f:
      simulation_config = json.load(f)

  simulation_params = {k: v for k, v in simulation_config.items() if k.startswith('output_')}

  # 传递给sumocfg生成
  sumocfg_content = generate_sumocfg_for_simulation(
      case_metadata=case_metadata,
      simulation_type=simulation_type,
      simulation_folder=sim_folder,
      case_root=case_root,
      simulation_params=simulation_params  # 添加此行
  )
  ```
- [ ] 测试参数正确传递

**验收标准:**
- simulation_params成功传递给generate_sumocfg_for_simulation()
- 参数类型和值正确

---

### P0-5: 验证sumocfg.xml正确生成
- [ ] 创建集成测试 `tests/integration/test_sumocfg_output_params.py`
- [ ] 测试场景:
  - [ ] output_tripinfo=True → sumocfg包含 `<tripinfo-output>`
  - [ ] output_tripinfo=False → sumocfg不包含 `<tripinfo-output>`
  - [ ] 其他4个参数同理
- [ ] 运行测试确保所有场景通过
- [ ] 验证sumocfg.xml与预期XML匹配

**验收标准:**
- 所有集成测试通过
- sumocfg.xml正确包含所有选中的输出元素

---

### P0-6: 更新单元测试
- [ ] 打开 `tests/unit/test_batch_optimization_service.py`
- [ ] 添加测试用例:
  - [ ] test_create_batch_with_tripinfo_output
  - [ ] test_create_batch_with_vehroute_output
  - [ ] test_create_batch_with_mixed_outputs
  - [ ] test_simulation_params_construction
- [ ] 运行所有单元测试确保通过

**验收标准:**
- 新增test用例全部通过
- 现有test未被破坏

---

### P0-7: 文档更新 (P0部分)
- [ ] 更新 `docs/api_docs/新架构API指南.md`
  - [ ] 添加output_*参数说明
  - [ ] 更新CreateBatchRequest文档
- [ ] 更新 `CLAUDE.md` 中关于output参数的说明
- [ ] 添加migration指南(if需要)

**验收标准:**
- 文档清晰说明output参数及其用法

---

## 📌 优先级 P1 (Sprint 2) - simulation_duration参数实现

### P1-1: 修改CreateBatchRequest API模型
- [ ] 打开 `api/models/control/requests/batch_request.py`
- [ ] 添加字段:
  ```python
  simulation_duration: Optional[Dict[str, int]] = None  # {hours, minutes, total_minutes}
  ```
- [ ] 添加Pydantic验证:
  - [ ] simulation_duration总分钟数在1-1440范围内

**验收标准:**
- API模型正确包含新字段
- 验证逻辑正确

---

### P1-2: 修改BatchOptimizationService接收simulation_duration
- [ ] 打开 `api/services/batch_optimization_service.py`
- [ ] 修改 `create_batch()` 签名添加参数:
  ```python
  def create_batch(
      self,
      # ... 现有参数 ...
      simulation_duration: Optional[Dict[str, int]] = None,
  )
  ```
- [ ] 在unified_simulation_config中保存simulation_duration参数
- [ ] 测试参数正确保存

**验收标准:**
- 参数正确接收和保存

---

### P1-3: 修改generate_sumocfg_for_simulation处理simulation_duration
- [ ] 打开 `shared/utilities/sumo_utils.py`
- [ ] 定位到时间计算部分 (L152-159)
- [ ] 修改逻辑:
  ```python
  # 优先使用自定义时长
  if simulation_params.get('simulation_duration'):
      duration = simulation_params['simulation_duration']['total_minutes'] * 60
  else:
      # 原有逻辑
      if time_range.get('start') and time_range.get('end'):
          start_dt = parse_datetime(time_range['start'])
          end_dt = parse_datetime(time_range['end'])
          duration = int((end_dt - start_dt).total_seconds())
      else:
          duration = 3600
  ```
- [ ] 测试自定义时长正确应用

**验收标准:**
- sumocfg.xml中`<end>`值正确反映自定义时长
- 未提供自定义时长时使用case元数据

---

### P1-4: 集成测试 (P1部分)
- [ ] 创建 `tests/integration/test_simulation_duration.py`
  - [ ] test_custom_duration_applied
  - [ ] test_custom_duration_overrides_metadata
  - [ ] test_invalid_duration_rejected
- [ ] 运行所有集成测试

**验收标准:**
- 所有测试通过
- 参数完整度: 55% → 65%

---

### P1-5: 文档更新 (P1部分)
- [ ] 更新API文档说明simulation_duration参数
- [ ] 添加用户指南说明如何使用simulation_duration参数
- [ ] 添加示例请求/响应

**验收标准:**
- 文档完整覆盖simulation_duration参数

---

## 📌 优先级 P2 (Sprint 3) - edgedata_use_template_edges整合

### P2-1: 添加前端支持 (可选)
- [ ] 在仿真配置页面添加checkbox (可选)
- [ ] 或通过高级选项菜单暴露此参数
- [ ] 当output_edgedata启用时显示

**验收标准:**
- 前端可收集此参数

---

### P2-2: 后端接收edgedata_use_template_edges
- [ ] 修改CreateBatchRequest添加字段
- [ ] 修改BatchOptimizationService接收并保存
- [ ] 修改SimulationService传递

**验收标准:**
- 参数完整流转

---

### P2-3: 修改edgeData.add.xml生成
- [ ] 修改generate_sumocfg_for_simulation中的edgedata处理 (L201-203)
- [ ] 支持edgedata_use_template_edges标志

**验收标准:**
- edgedata_use_template_edges为true时保留edges属性

---

## 🧪 测试与验证

### T-1: 单元测试
- [ ] 所有existing tests通过
- [ ] 新增test覆盖所有修改的函数
- [ ] 参数验证logic有test覆盖

**目标:** 100% test通过率

---

### T-2: 集成测试
- [ ] 端到端流程: 前端→API→backend→sumocfg
- [ ] 所有参数组合测试
- [ ] 边界条件测试

**目标:** 所有场景覆盖

---

### T-3: 手动测试
- [ ] 通过UI创建批次,验证sumocfg.xml
- [ ] 验证SUMO正确读取sumocfg并生成配置输出
- [ ] 验证仿真结果包含预期的输出文件

**目标:** 功能端到端验证

---

## 🔄 执行顺序与依赖

```
P0-1 (键名修改)
  ↓ depends on
P0-2 (扩展output_config读取)
  ↓ depends on
P0-3 (构造simulation_params)
  ↓ depends on
P0-4 (SimulationService传递)
  ↓ depends on
P0-5 & P0-6 (验证与测试) [可并行]
  ↓
P0-7 (文档更新)

P1-1 (修改API模型)
  ↓ depends on P0-7 (需要P0完成以确保不冲突)
  ↓
P1-2 (接收simulation_duration/vehicle_types_template)
  ↓
P1-3 & P1-4 (修改生成函数) [可并行]
  ↓
P1-5 (SimulationService传递)
  ↓
P1-6 (集成测试)
  ↓
P1-7 (文档更新)

P2-* (可在P1进行时同时进行)
```

---

## 📊 工作量估计

| 阶段 | 任务数 | 工作量 | 时间估计 |
|------|--------|--------|---------|
| P0 | 7 | 4 point | 6-8小时 |
| P1 | 7 | 5 point | 8-12小时 |
| P2 | 3 | 2 point | 2-3小时 |
| **总计** | **24** | **11 point** | **12-16小时** |

---

## ✅ 验收条件

- [x] 所有任务完成
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 手动测试通过
- [ ] 代码审查通过
- [ ] 文档已更新
- [ ] 参数完整度评分≥75%

---

**状态:** 🟡 Ready for Implementation
**下一步:** 分配开发者,创建对应issue
