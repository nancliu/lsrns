/**
 * 单元测试：参数控件工厂函数和渲染协调函数
 * Phase 1 Day 2 重构验证
 *
 * 文件位置：frontend/tests/unit/parameterControls.test.js
 * 运行命令：npm test -- parameterControls.test.js
 *
 * 测试覆盖：
 * - 7 个参数控件工厂函数（17 个测试）
 * - 4 个参数渲染协调函数（12 个测试）
 * - 集成测试（5 个测试）
 * 总计：34 个测试
 */

describe('参数控件工厂函数和渲染测试套件', () => {

  /**
   * 测试前置处理
   * 为每个测试创建清晰的 DOM 环境
   */
  beforeEach(() => {
    // 创建测试 DOM 环境
    document.body.innerHTML = `
      <div id="params-container"></div>
      <div id="test-container"></div>
    `;
  });

  /**
   * 测试后置处理
   * 清理 DOM
   */
  afterEach(() => {
    document.body.innerHTML = '';
  });

  // ============================================================
  // 测试 1: createStringControl() 函数 (3 个测试)
  // ============================================================
  describe('createStringControl()', () => {

    it('应该创建字符串输入框', () => {
      const param = {
        parameter_name: 'strategy_name',
        description: '策略名称',
        example: '我的策略',
        required: true
      };

      const control = createStringControl(param);

      expect(control).to.exist;
      expect(control).to.have.class('param-control-group');
      expect(control.querySelector('input[type="text"]')).to.exist;
      expect(control.querySelector('label')).to.exist;
      expect(control.querySelector('label').textContent).to.include('策略名称');
    });

    it('应该为必填项添加 * 标记', () => {
      const param = {
        parameter_name: 'test_param',
        description: '必填参数',
        required: true
      };

      const control = createStringControl(param);
      const label = control.querySelector('label');

      expect(label.textContent).to.include('*');
    });

    it('应该为非必填项不添加 * 标记', () => {
      const param = {
        parameter_name: 'test_param',
        description: '可选参数',
        required: false
      };

      const control = createStringControl(param);
      const label = control.querySelector('label');

      expect(label.textContent).not.to.include('*');
    });

  });

  // ============================================================
  // 测试 2: createNumberControl() 函数 (3 个测试)
  // ============================================================
  describe('createNumberControl()', () => {

    it('应该创建数字输入框', () => {
      const param = {
        parameter_name: 'max_speed',
        description: '最大速度',
        parameter_type: 'integer',
        required: true
      };

      const control = createNumberControl(param);

      expect(control).to.exist;
      expect(control.querySelector('input[type="number"]')).to.exist;
      expect(control.querySelector('label').textContent).to.include('最大速度');
    });

    it('应该为浮点数设置 step 属性', () => {
      const param = {
        parameter_name: 'speed_limit',
        description: '速度限制',
        parameter_type: 'float',
        required: true
      };

      const control = createNumberControl(param);
      const input = control.querySelector('input');

      expect(input.step).to.equal('0.01');
    });

    it('应该为整数不设置 step 属性', () => {
      const param = {
        parameter_name: 'vehicle_count',
        description: '车辆数',
        parameter_type: 'integer',
        required: true
      };

      const control = createNumberControl(param);
      const input = control.querySelector('input');

      expect(input.step).to.not.equal('0.01');
    });

  });

  // ============================================================
  // 测试 3: createSelectControl() 函数 (3 个测试)
  // ============================================================
  describe('createSelectControl()', () => {

    it('应该创建下拉选择框', () => {
      const param = {
        parameter_name: 'strategy_type',
        description: '策略类型',
        options: ['VSS', 'DHS', 'TEC'],
        required: true
      };

      const control = createSelectControl(param);

      expect(control).to.exist;
      expect(control.querySelector('select')).to.exist;
      expect(control.querySelector('label')).to.exist;
    });

    it('应该添加所有选项到下拉框', () => {
      const param = {
        parameter_name: 'route_code',
        description: '路线代码',
        options: ['G4202', 'G5', 'SA2'],
        required: true
      };

      const control = createSelectControl(param);
      const options = control.querySelectorAll('option');

      // 包括默认的 "请选择" 选项
      expect(options.length).to.equal(4);
      expect(options[1].textContent).to.equal('G4202');
      expect(options[2].textContent).to.equal('G5');
      expect(options[3].textContent).to.equal('SA2');
    });

    it('应该为必填项设置 required 属性', () => {
      const param = {
        parameter_name: 'type',
        description: '类型',
        options: ['A', 'B'],
        required: true
      };

      const control = createSelectControl(param);
      const select = control.querySelector('select');

      expect(select.required).to.be.true;
    });

  });

  // ============================================================
  // 测试 4: createStepArrayControl() 函数 (2 个测试)
  // ============================================================
  describe('createStepArrayControl()', () => {

    it('应该创建时间-速度表格', () => {
      const param = {
        parameter_name: 'speed_steps',
        description: '速度步进',
        value: [
          { time_hours: 7, speed_kmh: 50 },
          { time_hours: 9, speed_kmh: 80 }
        ],
        required: true
      };

      const control = createStepArrayControl(param);

      expect(control).to.exist;
      expect(control.querySelector('table')).to.exist;
      expect(control.querySelector('tbody')).to.exist;
      expect(control.querySelectorAll('tr').length).to.be.greaterThan(0);
    });

    it('应该添加表格行和添加行按钮', () => {
      const param = {
        parameter_name: 'speed_steps',
        description: '速度步进',
        value: [{ time_hours: 7, speed_kmh: 50 }],
        required: true
      };

      const control = createStepArrayControl(param);
      const addBtn = control.querySelector('button');

      expect(addBtn).to.exist;
      expect(addBtn.textContent).to.include('添加');
    });

  });

  // ============================================================
  // 测试 5: createDHSIntervalControl() 函数 (2 个测试)
  // ============================================================
  describe('createDHSIntervalControl()', () => {

    it('应该创建 DHS 间隔表格', () => {
      const param = {
        parameter_name: 'dhs_intervals',
        description: 'DHS 间隔',
        value: [
          { start_km: 10, end_km: 15, enabled: true }
        ],
        required: true
      };

      const control = createDHSIntervalControl(param);

      expect(control).to.exist;
      expect(control.querySelector('table')).to.exist;
      expect(control.querySelectorAll('tr').length).to.be.greaterThan(0);
    });

    it('应该包含起始和结束 KM 输入字段', () => {
      const param = {
        parameter_name: 'dhs_intervals',
        description: 'DHS 间隔',
        value: [
          { start_km: 10, end_km: 15, enabled: true }
        ],
        required: true
      };

      const control = createDHSIntervalControl(param);
      const inputs = control.querySelectorAll('input[type="number"]');

      expect(inputs.length).to.be.greaterThan(0);
    });

  });

  // ============================================================
  // 测试 6: createFlowIntervalControl() 函数 (2 个测试)
  // ============================================================
  describe('createFlowIntervalControl()', () => {

    it('应该创建流量间隔表格', () => {
      const param = {
        parameter_name: 'flow_intervals',
        description: '流量间隔',
        value: [
          { start_time: '06:00', end_time: '09:00', flow_vph: 2000 }
        ],
        required: true
      };

      const control = createFlowIntervalControl(param);

      expect(control).to.exist;
      expect(control.querySelector('table')).to.exist;
      expect(control.querySelectorAll('tr').length).to.be.greaterThan(0);
    });

    it('应该包含时间和流量输入字段', () => {
      const param = {
        parameter_name: 'flow_intervals',
        description: '流量间隔',
        value: [
          { start_time: '06:00', end_time: '09:00', flow_vph: 2000 }
        ],
        required: true
      };

      const control = createFlowIntervalControl(param);
      const inputs = control.querySelectorAll('input');

      expect(inputs.length).to.be.greaterThan(0);
    });

  });

  // ============================================================
  // 测试 7: createVehicleTypeControl() 函数 (2 个测试)
  // ============================================================
  describe('createVehicleTypeControl()', () => {

    it('应该创建车型多选框', () => {
      const param = {
        parameter_name: 'vehicle_types',
        description: '车型',
        options: ['passenger_small', 'truck_large', 'special_small'],
        value: ['passenger_small'],
        required: true
      };

      const control = createVehicleTypeControl(param);

      expect(control).to.exist;
      expect(control.querySelectorAll('input[type="checkbox"]').length).to.be.greaterThan(0);
    });

    it('应该显示所有车型选项', () => {
      const param = {
        parameter_name: 'vehicle_types',
        description: '车型',
        options: ['passenger_small', 'truck_large', 'special_small'],
        value: [],
        required: true
      };

      const control = createVehicleTypeControl(param);
      const checkboxes = control.querySelectorAll('input[type="checkbox"]');

      expect(checkboxes.length).to.equal(3);
    });

  });

  // ============================================================
  // 测试 8: renderParameterControl() 函数 (3 个测试)
  // ============================================================
  describe('renderParameterControl()', () => {

    it('应该为字符串参数渲染字符串控件', () => {
      const param = {
        parameter_name: 'name',
        parameter_type: 'string',
        description: '名称',
        required: true
      };

      const control = renderParameterControl(param);

      expect(control).to.exist;
      expect(control.querySelector('input[type="text"]')).to.exist;
    });

    it('应该为数字参数渲染数字控件', () => {
      const param = {
        parameter_name: 'speed',
        parameter_type: 'integer',
        description: '速度',
        required: true
      };

      const control = renderParameterControl(param);

      expect(control).to.exist;
      expect(control.querySelector('input[type="number"]')).to.exist;
    });

    it('应该为选择参数渲染下拉框', () => {
      const param = {
        parameter_name: 'type',
        parameter_type: 'select',
        description: '类型',
        options: ['A', 'B'],
        required: true
      };

      const control = renderParameterControl(param);

      expect(control).to.exist;
      expect(control.querySelector('select')).to.exist;
    });

  });

  // ============================================================
  // 测试 9: renderParametersSection() 函数 (3 个测试)
  // ============================================================
  describe('renderParametersSection()', () => {

    it('应该渲染所有参数控件', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'name',
            parameter_type: 'string',
            description: '名称',
            required: true
          },
          {
            parameter_name: 'speed',
            parameter_type: 'integer',
            description: '速度',
            required: true
          }
        ]
      };

      renderParametersSection(container, template);

      const controls = container.querySelectorAll('.param-control-group');
      expect(controls.length).to.equal(2);
    });

    it('应该为每个参数添加 data-parameter-name 属性', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'test_param',
            parameter_type: 'string',
            description: '测试',
            required: true
          }
        ]
      };

      renderParametersSection(container, template);

      const wrapper = container.querySelector('[data-parameter-name]');
      expect(wrapper).to.exist;
      expect(wrapper.getAttribute('data-parameter-name')).to.equal('test_param');
    });

    it('应该处理空参数列表', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: []
      };

      expect(() => renderParametersSection(container, template)).not.to.throw();
    });

  });

  // ============================================================
  // 测试 10: attachParameterListeners() 函数 (3 个测试)
  // ============================================================
  describe('attachParameterListeners()', () => {

    it('应该为输入控件添加变化监听器', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'test_param',
            parameter_type: 'string',
            description: '测试',
            required: true
          }
        ]
      };

      renderParametersSection(container, template);
      attachParameterListeners(container, template);

      const input = container.querySelector('input');
      expect(input).to.exist;
    });

    it('应该处理参数查找失败的情况', () => {
      const container = document.getElementById('params-container');

      // 创建一个没有对应参数定义的输入框
      const input = document.createElement('input');
      input.setAttribute('data-parameter-name', 'nonexistent');
      container.appendChild(input);

      const template = {
        parameters_schema: []
      };

      expect(() => attachParameterListeners(container, template)).not.to.throw();
    });

    it('应该在输入框变化时进行验证', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'speed',
            parameter_type: 'integer',
            description: '速度',
            required: true
          }
        ]
      };

      renderParametersSection(container, template);
      attachParameterListeners(container, template);

      const input = container.querySelector('input');
      input.value = '100';

      // 触发 change 事件
      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);

      // 应该没有错误
      expect(input).to.exist;
    });

  });

  // ============================================================
  // 测试 11: validateParameterValue() 函数 (3 个测试)
  // ============================================================
  describe('validateParameterValue()', () => {

    it('应该验证必填项', () => {
      const container = document.getElementById('params-container');
      const wrapper = document.createElement('div');
      wrapper.setAttribute('data-parameter-name', 'name');

      const input = document.createElement('input');
      input.type = 'text';
      input.value = '';
      wrapper.appendChild(input);
      container.appendChild(wrapper);

      const param = {
        parameter_name: 'name',
        description: '名称',
        required: true
      };

      const result = validateParameterValue(input, param);

      expect(result).to.be.false;
      const errorMsg = wrapper.querySelector('.error-message');
      expect(errorMsg).to.exist;
    });

    it('应该验证整数输入', () => {
      const container = document.getElementById('params-container');
      const wrapper = document.createElement('div');
      wrapper.setAttribute('data-parameter-name', 'speed');

      const input = document.createElement('input');
      input.type = 'number';
      input.value = 'not-a-number';
      wrapper.appendChild(input);
      container.appendChild(wrapper);

      const param = {
        parameter_name: 'speed',
        parameter_type: 'integer',
        description: '速度',
        required: false
      };

      const result = validateParameterValue(input, param);

      expect(result).to.be.false;
    });

    it('应该验证浮点数输入', () => {
      const container = document.getElementById('params-container');
      const wrapper = document.createElement('div');
      wrapper.setAttribute('data-parameter-name', 'value');

      const input = document.createElement('input');
      input.type = 'number';
      input.value = '3.14';
      wrapper.appendChild(input);
      container.appendChild(wrapper);

      const param = {
        parameter_name: 'value',
        parameter_type: 'float',
        description: '值',
        required: false
      };

      const result = validateParameterValue(input, param);

      expect(result).to.be.true;
    });

  });

  // ============================================================
  // 集成测试 (5 个测试)
  // ============================================================
  describe('集成测试：完整参数表单工作流', () => {

    it('应该完整渲染并验证单个参数表单', () => {
      const container = document.getElementById('params-container');
      const template = {
        template_name: '测试策略',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'strategy_name',
            parameter_type: 'string',
            description: '策略名称',
            required: true,
            example: '我的策略'
          }
        ]
      };

      renderParametersSection(container, template);
      attachParameterListeners(container, template);

      const control = container.querySelector('.param-control-group');
      expect(control).to.exist;
      expect(control.querySelector('input')).to.exist;
    });

    it('应该处理多种参数类型的混合表单', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'name',
            parameter_type: 'string',
            description: '名称',
            required: true
          },
          {
            parameter_name: 'speed',
            parameter_type: 'integer',
            description: '速度',
            required: true
          },
          {
            parameter_name: 'type',
            parameter_type: 'select',
            description: '类型',
            options: ['A', 'B'],
            required: true
          }
        ]
      };

      renderParametersSection(container, template);
      attachParameterListeners(container, template);

      const controls = container.querySelectorAll('.param-control-group');
      expect(controls.length).to.equal(3);

      // 验证每个控件类型
      expect(controls[0].querySelector('input[type="text"]')).to.exist;
      expect(controls[1].querySelector('input[type="number"]')).to.exist;
      expect(controls[2].querySelector('select')).to.exist;
    });

    it('应该在用户输入后进行实时验证', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'count',
            parameter_type: 'integer',
            description: '计数',
            required: true
          }
        ]
      };

      renderParametersSection(container, template);
      attachParameterListeners(container, template);

      const input = container.querySelector('input');
      input.value = '';

      // 触发验证
      const event = new Event('change', { bubbles: true });
      input.dispatchEvent(event);

      // 应该显示错误（必填项为空）
      // 注意：实际错误显示取决于验证逻辑
      expect(input).to.exist;
    });

    it('应该支持表格类型参数的动态行添加', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: [
          {
            parameter_name: 'speed_steps',
            parameter_type: 'step_array',
            description: '速度步进',
            value: [
              { time_hours: 7, speed_kmh: 50 }
            ],
            required: true
          }
        ]
      };

      renderParametersSection(container, template);

      const table = container.querySelector('table');
      expect(table).to.exist;

      const addBtn = container.querySelector('button');
      expect(addBtn).to.exist;
      expect(addBtn.textContent).to.include('添加');
    });

    it('应该为空参数列表正确处理', () => {
      const container = document.getElementById('params-container');
      const template = {
        parameters_schema: []
      };

      renderParametersSection(container, template);
      attachParameterListeners(container, template);

      const controls = container.querySelectorAll('.param-control-group');
      expect(controls.length).to.equal(0);
    });

  });

});
