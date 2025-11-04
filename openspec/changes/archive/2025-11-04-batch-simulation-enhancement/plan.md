# 批量仿真配置增强 - 实现计划

**Status**: Planning
**Version**: v1.0
**Last Updated**: 2025-11-03

---

## 1. 实现策略

### 1.1 分阶段交付策略

采用**渐进式集成**方案，优先解决用户体验最差的问题（输出配置复杂度），然后逐步增强功能：

```
Phase 1: Output Config  → User sees concrete output options (not confusing levels)
         ↓
Phase 2: Vehicle Template → Enables different parameter testing
         ↓
Phase 3: Simulation Duration → Enables flexible simulation scenarios
         ↓
Phase 4: Task Estimation  → UI cleanup
         ↓
Phase 5: Testing & Docs  → Quality assurance
```

### 1.2 向后兼容策略

**原则**: 旧的批次、API请求、配置文件应继续工作

**实现**:
1. 保留`output_level`字段在API请求中（但deprecated）
2. 支持读取旧的`simulation_config.json`格式
3. 旧批次执行时自动升级配置格式
4. 新创建的批次使用新格式

---

## 2. 代码组织结构

### 2.1 Frontend修改

```
frontend/control/
├── simulations.html              [修改] 更新表单UI结构
├── js/
│   └── batch_simulation.js        [修改] 增加新字段处理、模板加载
└── css/
    ├── simulations.css            [修改] 性能提示样式
    └── variables.css              [无修改] (如需)
```

### 2.2 Backend修改

```
api/
├── routes/
│   └── batch_optimization_routes.py  [修改] 新增template列表端点
├── models/
│   ├── control/
│   │   └── requests/
│   │       └── batch_request.py      [修改] 新增Request模型
│   └── responses/
│       └── batch_response.py         [可选] 如需增加template信息
└── services/
    ├── batch_optimization_service.py [修改] 处理新字段
    └── template_service.py           [修改或新增] 加载模板列表

shared/
├── control_tools/
│   └── batch_simulation_scheduler.py [修改] 保存新配置
└── utilities/
    └── sumo_utils.py                 [修改] 支持新参数
```

### 2.3 测试

```
tests/
├── unit/
│   ├── test_simulation_duration.py    [新增]
│   └── test_output_config.py          [新增]
├── integration/
│   └── test_batch_creation_flow.py    [修改/新增]
└── e2e/
    └── test_batch_simulation_ui.spec.js [修改/新增]
```

---

## 3. 实现细节设计

### 3.1 Frontend - HTML表单结构

#### 当前结构
```html
<form id="batchConfigForm">
  <select id="caseSelector">...</select>
  <div id="planSelector">...</div>
  <select id="outputLevel">
    <option value="minimal">minimal</option>
    <option value="standard">standard</option>
    <option value="full">full</option>
  </select>
  <input id="numSeeds" type="number" />
  <input id="baseSeed" type="number" />
  <div id="estimate">...</div>
</form>
```

#### 新结构（紧凑网格布局）
```html
<form id="batchConfigForm" class="config-form-grid">

  <!-- Section 1: 案例和方案 (2列) -->
  <div class="config-row">
    <div class="form-section form-col-1">
      <label>案例选择：</label>
      <select id="caseSelector">...</select>
    </div>
    <div class="form-section form-col-2">
      <label>方案选择：</label>
      <div id="planSelector" class="plan-checkboxes">
        <!-- 动态生成 -->
      </div>
      <div class="help-text">ℹ️ 基准方案自动包含</div>
    </div>
  </div>

  <!-- Section 2: 时长配置 (2列对比) -->
  <div class="config-row">
    <div class="form-section form-col-1 duration-box default">
      <div class="radio-group">
        <input type="radio" id="durationDefault" name="durationMode" value="default" checked />
        <label for="durationDefault">使用输入数据时长</label>
      </div>
      <div id="currentDurationInfo" class="duration-info">当前: 7h30m (07:00 - 14:30)</div>
    </div>
    <div class="form-section form-col-2 duration-box custom">
      <div class="radio-group">
        <input type="radio" id="durationCustom" name="durationMode" value="custom" />
        <label for="durationCustom">自定义时长</label>
      </div>
      <div id="customDurationInputs" class="duration-inputs">
        <input type="number" id="simHours" min="0" max="24" placeholder="0" disabled />
        <span class="unit">小时</span>
        <input type="number" id="simMinutes" min="0" max="59" placeholder="0" disabled />
        <span class="unit">分钟</span>
      </div>
      <div id="durationError" class="error-text"></div>
      <div class="help-text">可设1分钟-24小时</div>
    </div>
  </div>

  <!-- Section 3: 模板和输出 (2列) -->
  <div class="config-row">
    <div class="form-section form-col-1 template-box">
      <label>车辆类型模板：</label>
      <select id="vehicleTypesTemplate">
        <option value="vehicle_types.json">vehicle_types.json (默认参数)</option>
        <!-- 动态加载 -->
      </select>
      <div class="help-text">选择不同参数配置</div>
    </div>
    <div class="form-section form-col-2 output-box">
      <label>仿真输出配置：</label>
      <div class="output-checkboxes">
        <div class="checkbox-item">
          <input type="checkbox" id="outputSummary" checked disabled />
          <label for="outputSummary">summary</label>
          <span class="status-badge checked">☑</span>
        </div>
        <div class="checkbox-item">
          <input type="checkbox" id="outputE1" checked disabled />
          <label for="outputE1">E1检测器</label>
          <span class="status-badge checked">☑</span>
        </div>
        <div class="checkbox-item">
          <input type="checkbox" id="outputEdgedata" />
          <label for="outputEdgedata">edgedata</label>
          <span class="warning-badge">+20%</span>
        </div>
        <div class="checkbox-item">
          <input type="checkbox" id="outputTripinfo" />
          <label for="outputTripinfo">tripinfo</label>
          <span class="warning-badge">+30%</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Section 4: 种子配置 (2列) -->
  <div class="config-row seed-row">
    <div class="form-inline">
      <label for="numSeeds">随机种子数:</label>
      <input type="number" id="numSeeds" min="1" max="10" value="3" />
      <span class="inline-hint">(1-10)</span>
    </div>
    <div class="form-inline">
      <label for="baseSeed">起始种子:</label>
      <input type="number" id="baseSeed" value="66" />
    </div>
  </div>

  <!-- Section 5: 任务预估 -->
  <div class="config-row estimate-row">
    <div class="estimate-box">
      <span id="estimate">3个方案 × 3个随机种子 = 9个并行仿真任务</span>
    </div>
  </div>

  <!-- 按钮 -->
  <div class="button-group">
    <button type="reset" class="btn-secondary">清除配置</button>
    <button type="submit" class="btn-primary">创建批次 →</button>
  </div>
</form>
```

### 3.2 Frontend - JavaScript逻辑变更

#### 新增函数
```javascript
// 1. 初始化vehicle types模板
async function initVehicleTypesTemplate() {
  const response = await fetch('/api/v1/template/vehicle-types/list');
  const data = await response.json();
  const select = document.getElementById('vehicleTypesTemplate');

  data.templates.forEach(template => {
    const option = document.createElement('option');
    option.value = template.filename;
    option.textContent = `${template.display_name} (${template.filename})`;
    select.appendChild(option);
  });
}

// 2. 仿真时长Radio切换
function onDurationModeChange(mode) {
  const customInputs = document.getElementById('customDurationInputs');
  const hoursInput = document.getElementById('simHours');
  const minutesInput = document.getElementById('simMinutes');

  if (mode === 'custom') {
    customInputs.style.display = 'block';
    hoursInput.disabled = false;
    minutesInput.disabled = false;
  } else {
    customInputs.style.display = 'none';
    hoursInput.disabled = true;
    minutesInput.disabled = true;
  }

  updateEstimate();
}

// 3. 仿真时长验证
function validateSimulationDuration() {
  const mode = document.querySelector('input[name="durationMode"]:checked').value;
  const errorDiv = document.getElementById('durationError');

  if (mode === 'default') {
    errorDiv.textContent = '';
    return true;
  }

  const hours = parseInt(document.getElementById('simHours').value) || 0;
  const minutes = parseInt(document.getElementById('simMinutes').value) || 0;
  const totalMinutes = hours * 60 + minutes;

  if (totalMinutes < 1) {
    errorDiv.textContent = '❌ 仿真时长至少为1分钟';
    return false;
  }
  if (totalMinutes > 1440) {
    errorDiv.textContent = '❌ 仿真时长不能超过24小时';
    return false;
  }

  errorDiv.textContent = '';
  return true;
}

// 4. 组建批次请求
function buildBatchRequest() {
  const request = {
    case_id: document.getElementById('caseSelector').value,
    plan_ids: getSelectedPlans(),
    num_seeds: parseInt(document.getElementById('numSeeds').value),
    base_seed: parseInt(document.getElementById('baseSeed').value),
  };

  // 仿真时长
  const durationMode = document.querySelector('input[name="durationMode"]:checked').value;
  if (durationMode === 'custom') {
    request.simulation_duration = {
      use_default: false,
      hours: parseInt(document.getElementById('simHours').value) || 0,
      minutes: parseInt(document.getElementById('simMinutes').value) || 0
    };
  }

  // Vehicle types模板
  request.vehicle_types_template = document.getElementById('vehicleTypesTemplate').value;

  // 输出配置
  request.output_config = {
    summary_xml: true,
    e1_detector_data: true,
    edgedata_xml: document.getElementById('outputEdgedata').checked,
    tripinfo_xml: document.getElementById('outputTripinfo').checked
  };

  return request;
}

// 5. 修改任务数量预估（移除种子序列）
function updateEstimate() {
  const numPlans = getSelectedPlans().length;
  const numSeeds = parseInt(document.getElementById('numSeeds').value) || 3;
  const totalTasks = numPlans * numSeeds;

  document.getElementById('estimate').textContent =
    `${numPlans}个方案 × ${numSeeds}个随机种子 = ${totalTasks}个并行仿真任务`;
}
```

#### 修改现有函数
```javascript
// 修改表单提交处理
async function handleFormSubmit(e) {
  e.preventDefault();

  // 添加仿真时长验证
  if (!validateSimulationDuration()) {
    return;
  }

  const request = buildBatchRequest();

  try {
    const response = await fetch(`${API_BASE}/control/batch-optimization/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    const result = await response.json();
    if (result.success) {
      // 跳转到监控Tab
      switchTab('monitor');
    }
  } catch (error) {
    showError('批次创建失败: ' + error.message);
  }
}

// 页面初始化时加载模板列表
document.addEventListener('DOMContentLoaded', async () => {
  // ... 现有初始化代码 ...
  await initVehicleTypesTemplate();
});
```

### 3.3 Frontend - CSS样式

#### 新增CSS规则（网格布局）
```css
/* 主表单网格布局 */
.config-form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 8px;
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.form-col-1 {
  grid-column: 1;
}

.form-col-2 {
  grid-column: 2;
}

/* 特殊行布局 */
.seed-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.estimate-row {
  grid-column: 1 / -1;
}

/* 内联表单（种子配置） */
.form-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-inline label {
  white-space: nowrap;
  font-weight: 500;
}

.form-inline input {
  width: 80px;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.inline-hint {
  color: #999;
  font-size: 0.85em;
}

/* 时长配置框 */
.duration-box {
  position: relative;
  padding-bottom: 24px;
}

.duration-box.default {
  background-color: #f0f8ff;
}

.duration-box.custom {
  background-color: #fffbf0;
}

.duration-info {
  color: #666;
  font-size: 0.95em;
  margin-top: 6px;
}

.duration-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.duration-inputs input {
  width: 60px;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.duration-inputs input:disabled {
  background-color: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.unit {
  font-size: 0.9em;
  color: #666;
}

/* 输出配置框 */
.output-box {
  padding-bottom: 0;
}

.output-checkboxes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-top: 6px;
}

/* 单个输出项（网格排列） */
.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  font-size: 0.9em;
}

.checkbox-item input[type="checkbox"] {
  width: 14px;
  height: 14px;
  margin: 0;
}

.checkbox-item label {
  cursor: pointer;
  margin: 0;
  font-weight: 500;
}

/* 状态徽章（已启用） */
.status-badge {
  font-size: 0.85em;
  font-weight: 600;
  color: #4caf50;
  margin-left: 2px;
}

.status-badge.checked {
  color: #4caf50;
}

/* 性能警告徽章 */
.warning-badge {
  background-color: #ffccbc;
  color: #e64a19;
  padding: 1px 4px;
  border-radius: 2px;
  font-size: 0.7em;
  font-weight: 600;
  white-space: nowrap;
  margin-left: 2px;
}

/* 复选框样式 */
.checkbox-group input[type="checkbox"],
.radio-group input[type="radio"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  margin: 0;
}

.checkbox-group label,
.radio-group label {
  cursor: pointer;
  margin: 0;
  font-size: 0.95em;
}

/* 禁用复选框 */
input:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

input:disabled + label {
  color: #999;
  cursor: not-allowed;
}

/* 信息提示样式 */
.help-text {
  color: #666;
  font-size: 0.85em;
  margin-top: 4px;
  padding-left: 0;
  line-height: 1.3;
}

.help-text::before {
  content: "ℹ️ ";
  margin-right: 3px;
}

/* 错误信息样式 */
.error-text {
  color: #d32f2f;
  font-size: 0.85em;
  margin-top: 4px;
  display: none;
  padding-left: 0;
}

.error-text.show {
  display: block;
}

.error-text::before {
  content: "❌ ";
  margin-right: 3px;
}

/* 估算框样式 */
.estimate-box {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  padding: 14px 16px;
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  text-align: center;
}

#estimate {
  font-weight: 500;
  color: #1565c0;
  font-size: 1em;
}

/* 按钮组 */
.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.btn-primary, .btn-secondary {
  padding: 10px 20px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: #2196f3;
  color: white;
}

.btn-primary:hover {
  background-color: #1976d2;
}

.btn-secondary {
  background-color: #ccc;
  color: #333;
}

.btn-secondary:hover {
  background-color: #bbb;
}

/* 响应式设计 (小屏幕) */
@media (max-width: 1024px) {
  .config-row {
    grid-template-columns: 1fr;
  }

  .form-col-1,
  .form-col-2 {
    grid-column: 1;
  }

  .estimate-row {
    grid-column: 1;
  }

  .output-checkboxes {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .config-form-grid {
    padding: 12px;
    gap: 12px;
  }

  .form-section {
    padding: 10px;
  }

  .duration-inputs input {
    width: 50px;
  }

  .form-inline {
    flex-direction: column;
    align-items: flex-start;
  }

  .button-group {
    flex-direction: column-reverse;
  }

  .btn-primary, .btn-secondary {
    width: 100%;
  }
}
```

---

### 3.4 Backend - API路由修改

#### 新增：Template列表端点
```python
# api/routes/batch_optimization_routes.py

@router.get("/template/vehicle-types/list")
async def list_vehicle_templates():
    """列出可用的vehicle types模板"""
    try:
        template_dir = Path("templates/config_templates/vehicle_templates")
        templates = []

        for file in sorted(template_dir.glob("*.json")):
            try:
                # 验证JSON格式
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查必要字段
                if 'vehicle_types' not in data:
                    continue

                stat = file.stat()
                templates.append({
                    'filename': file.name,
                    'display_name': file.stem.replace('vehicle_types_', '').replace('_', ' ').title(),
                    'description': f"车辆参数配置 ({file.name})",
                    'file_size_kb': round(stat.st_size / 1024, 1),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat() + 'Z',
                    'is_default': file.name == 'vehicle_types.json'
                })
            except (json.JSONDecodeError, KeyError):
                # 跳过无效的模板文件
                continue

        return {
            'success': True,
            'templates': templates
        }
    except Exception as e:
        logger.error(f"Failed to list vehicle templates: {e}")
        return {
            'success': False,
            'error': '无法扫描模板目录',
            'details': str(e)
        }, 500
```

#### 修改：Batch创建端点
```python
# api/routes/batch_optimization_routes.py

@router.post("/batch")
async def create_batch(request: CreateBatchRequest):
    """创建批次仿真"""
    try:
        # 验证vehicle types模板
        template_path = Path("templates/config_templates/vehicle_templates") / request.vehicle_types_template
        if not template_path.exists():
            raise ValueError(f"模板文件不存在: {request.vehicle_types_template}")

        # 验证仿真时长
        if request.simulation_duration and not request.simulation_duration.use_default:
            total_minutes = request.simulation_duration.get_total_minutes()
            if not (1 <= total_minutes <= 1440):
                raise ValueError("仿真时长必须在1分钟-24小时之间")

        # 调用服务层
        result = batch_service.create_batch(
            case_id=request.case_id,
            plan_ids=request.plan_ids,
            num_seeds=request.num_seeds,
            base_seed=request.base_seed,
            simulation_duration=request.simulation_duration,
            vehicle_types_template=request.vehicle_types_template,
            output_config=request.output_config,
            # 向后兼容
            output_level=request.output_level
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create batch: {e}")
        raise HTTPException(status_code=500, detail="批次创建失败")
```

---

### 3.5 Backend - 服务层修改

#### 修改：batch_optimization_service.py
```python
class BatchOptimizationService:
    def create_batch(self,
                     case_id: str,
                     plan_ids: List[str],
                     num_seeds: int,
                     base_seed: int,
                     simulation_duration: Optional[SimulationDuration] = None,
                     vehicle_types_template: str = "vehicle_types.json",
                     output_config: Optional[OutputConfig] = None,
                     output_level: Optional[str] = None) -> dict:
        """创建批次仿真"""

        # 处理输出配置（向后兼容）
        if output_level:
            # 将旧的output_level映射到output_config
            if output_level == "minimal":
                output_config = OutputConfig(edgedata_xml=False, tripinfo_xml=False)
            elif output_level in ["standard", "full"]:
                output_config = OutputConfig(edgedata_xml=True, tripinfo_xml=True)

        if not output_config:
            output_config = OutputConfig()

        # 调用scheduler创建批次
        batch_id, batch_dir = self.scheduler.create_batch(
            case_id=case_id,
            plan_ids=plan_ids,
            num_seeds=num_seeds,
            base_seed=base_seed
        )

        # 构建simulation_config.json
        simulation_config = {
            'num_seeds': num_seeds,
            'base_seed': base_seed,
            'vehicle_types_template': vehicle_types_template,
            'output_config': output_config.model_dump(),
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }

        # 添加仿真时长配置
        if simulation_duration:
            simulation_config['simulation_duration'] = {
                'use_default': simulation_duration.use_default,
                'hours': simulation_duration.hours,
                'minutes': simulation_duration.minutes,
            }
            if not simulation_duration.use_default:
                total_minutes = simulation_duration.get_total_minutes()
                simulation_config['simulation_duration']['total_minutes'] = total_minutes

        # 保存配置文件
        config_file = Path(batch_dir) / 'simulation_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(simulation_config, f, indent=2, ensure_ascii=False)

        logger.info(f"Batch created: {batch_id} with config: {simulation_config}")

        return {
            'success': True,
            'batch_id': batch_id,
            'batch_dir': str(batch_dir),
            'num_tasks': len(plan_ids) * num_seeds,
            'message': '批次创建成功'
        }
```

---

### 3.6 Shared层 - SUMO配置生成修改

#### 修改：sumo_utils.py
```python
def generate_sumocfg_for_simulation(
    case_id: str,
    simulation_id: str,
    base_dir: str,
    case_begin_time: float,
    case_end_time: float,
    simulation_duration: Optional[Dict] = None,
    vehicle_types_template: str = "vehicle_types.json",
    output_config: Optional[Dict] = None,
    simulation_params: Optional[Dict] = None
) -> str:
    """
    生成SUMO配置文件

    Args:
        case_id: 案例ID
        simulation_id: 仿真ID
        base_dir: 基础目录
        case_begin_time: 案例开始时间（秒）
        case_end_time: 案例结束时间（秒）
        simulation_duration: 自定义仿真时长 {'hours': int, 'minutes': int}
        vehicle_types_template: vehicle types模板文件名
        output_config: 输出配置 {'edgedata_xml': bool, 'tripinfo_xml': bool, ...}
        simulation_params: 其他仿真参数

    Returns:
        配置文件路径
    """

    # 计算仿真结束时间
    if simulation_duration and not simulation_duration.get('use_default', True):
        custom_minutes = simulation_duration.get('hours', 0) * 60 + simulation_duration.get('minutes', 0)
        end_time = case_begin_time + custom_minutes * 60  # 转换为秒
    else:
        end_time = case_end_time

    # 处理输出配置
    if not output_config:
        output_config = {
            'summary_xml': True,
            'e1_detector_data': True,
            'edgedata_xml': False,
            'tripinfo_xml': False
        }

    # 加载vehicle types模板
    template_path = Path(f"templates/config_templates/vehicle_templates/{vehicle_types_template}")
    with open(template_path, 'r', encoding='utf-8') as f:
        vehicle_types_data = json.load(f)

    # ... 现有配置生成代码 ...

    # 生成vType定义（基于加载的模板）
    vtypes_xml = generate_vtypes(vehicle_types_data)

    # 配置输出设置
    output_xml = '''  <output>
    <summary value="summary.xml"/>'''

    if output_config.get('tripinfo_xml', False):
        output_xml += '\n    <tripinfo value="tripinfo.xml"/>'

    if output_config.get('edgedata_xml', False):
        output_xml += '\n    <edgedata value="edgedata.xml"/>'

    output_xml += '\n  </output>'

    # 生成完整的SUMO配置XML
    sumocfg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <input>
    <net value="{net_file}"/>
    <route value="{route_file}"/>
    <additional value="{additional_file}"/>
  </input>

  <time>
    <begin value="{int(case_begin_time)}"/>
    <end value="{int(end_time)}"/>
    <step-length value="1.0"/>
  </time>

  <processing>
    <collision.action value="remove"/>
    <ignore-route-errors value="true"/>
  </processing>

{output_xml}

{vtypes_xml}
</configuration>'''

    # 保存配置文件
    config_path = Path(base_dir) / f"{simulation_id}.sumocfg"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(sumocfg_content)

    return str(config_path)
```

---

## 4. 数据库/文件系统变更

### 4.1 无数据库变更

此变更不涉及数据库结构修改，仅修改配置文件格式。

### 4.2 文件系统变更

```
cases/{case_id}/simulations/plan_opti/{batch_id}/
├── batch_metadata.json              [无变更]
├── simulation_config.json            [新格式]
│   ├── vehicle_types_template        [新字段]
│   ├── simulation_duration           [新字段]
│   └── output_config                 [新字段]
├── {sim_id_1}/
│   ├── simulation.sumocfg            [可能使用新vehicle types模板]
│   └── ...
└── {sim_id_N}/
    └── ...
```

---

## 5. 性能影响分析

| 操作 | 当前耗时 | 预期变化 | 影响 |
|------|--------|--------|------|
| 批次创建 | ~100ms | +50ms (模板验证+API调用) | 可接受 |
| SUMO配置生成 | ~200ms | +100ms (额外的车辆参数处理) | 可接受 |
| 仿真执行 | 根据场景 | 如选tripinfo +30% | 用户知情选择 |
| 磁盘写入 | 根据输出 | 如选edgedata +50% | 用户知情选择 |

---

## 6. 测试策略

### 6.1 单元测试覆盖范围

**优先级P0** (必须):
- [ ] `SimulationDuration` 数据验证
- [ ] `OutputConfig` 默认值和序列化
- [ ] 时长计算（1分钟、24小时、边界值）
- [ ] Vehicle template路径验证

**优先级P1** (应该):
- [ ] 向后兼容映射（output_level → output_config）
- [ ] SUMO配置生成（--end参数）
- [ ] 多个vehicle types模板的正确加载

### 6.2 集成测试

**优先级P0**:
- [ ] API创建batch → 验证simulation_config.json格式
- [ ] 读取旧的simulation_config.json → 仍可正常工作
- [ ] SUMO配置生成 → 验证vehicle types正确加载

### 6.3 E2E测试（Playwright）

**优先级P0**:
- [ ] 使用默认配置创建batch
- [ ] 自定义仿真时长：8小时30分钟
- [ ] 选择非默认vehicle template
- [ ] 勾选edgedata或tripinfo
- [ ] 验证估算任务数实时更新

**优先级P1**:
- [ ] 输入非法时长显示错误
- [ ] 禁用自定义输入框当"使用默认"被选中
- [ ] 性能提示正确显示

---

## 7. 发布准备

### 7.1 发布清单

- [ ] 所有代码评审通过
- [ ] 单元测试覆盖率 ≥90%
- [ ] 集成测试全部通过
- [ ] E2E测试全部通过
- [ ] 向后兼容性验证完成
- [ ] API文档更新完成
- [ ] 用户指南/Release Notes准备
- [ ] 性能基准测试完成（无回归）

### 7.2 灰度发布

1. **阶段1** (Day 1-2): 内部测试用户
   - 验证核心功能
   - 收集反馈

2. **阶段2** (Day 3-4): 50% 正式用户
   - 监控错误率
   - 验证性能

3. **阶段3** (Day 5+): 100% 正式用户发布
   - 全量发布
   - 继续监控

---

## 8. 回滚计划

如果发现严重问题（数据损坏、性能严重下降等）：

1. **立即回滚** → 使用上一个稳定版本
2. **数据恢复** → 旧batch仍可正常读取（向后兼容）
3. **根因分析** → 修复后重新测试
4. **更新发布** → 修复版本重新发布

---

## 9. 相关文档索引

- 需求规格: `spec.md` ✓
- 实现计划: `plan.md` (本文件)
- 任务清单: `tasks.md` (待创建)
- API文档: [新架构API指南](../../docs/api_docs/新架构API指南.md)
- 项目规范: [CLAUDE.md](../../CLAUDE.md)

---

**Status**: ✅ Ready for Implementation
**Next**: Create tasks.md and begin Phase 1
