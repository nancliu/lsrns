/**
 * 集成测试：updateConfigSummary() 完整工作流
 * Phase 1 Day 3 - 参数收集和提交数据准备
 *
 * 文件位置：frontend/tests/unit/integrationTests.test.js
 * 运行命令：npm test -- integrationTests.test.js
 *
 * 测试覆盖：
 * - 参数表单与 updateConfigSummary() 集成
 * - 参数值收集
 * - 参数验证
 * - 策略提交数据准备
 * 总计：15 个集成测试
 */

describe('updateConfigSummary() 参数集成测试套件', () => {

  /**
   * 测试前置处理
   */
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="summary-template"></div>
      <div id="summary-edges"></div>
      <div id="summary-edge-list"></div>
      <div id="params-container"></div>
    `;

    // 初始化全局变量
    window.selectedTemplate = null;
    window.selectedEdges = [];
  });

  /**
   * 测试后置处理
   */
  afterEach(() => {
    document.body.innerHTML = '';
    window.selectedTemplate = null;
    window.selectedEdges = [];
  });

  // ============================================================
  // 测试 1: 参数表单集成 (4 个测试)
  // ============================================================
  describe('参数表单与 updateConfigSummary() 集成', () => {

    it('应该在更新配置时渲染参数表单', () => {
      const template = {
        template_id: 'tpl_vss_001',
        template_name: 'VSS 策略',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'speed_limit',
            parameter_type: 'integer',
            description: '速度限制',
            required: true,
            example: '80'
          }
        ]
      };

      const edges = ['edge1', 'edge2'];

      // 调用 updateConfigSummary
      updateConfigSummary(template, edges);

      // 验证参数表单已被渲染
      const paramsContainer = document.getElementById('params-container');
      expect(paramsContainer).to.exist;
      expect(paramsContainer.querySelector('.param-control-group')).to.exist;
      expect(paramsContainer.querySelector('input[type="number"]')).to.exist;
    });

    it('应该为没有参数的模板不渲染参数表单', () => {
      const template = {
        template_id: 'tpl_simple_001',
        template_name: '简单策略',
        strategy_type: 'DHS',
        parameters_schema: []
      };

      const edges = ['edge1'];

      updateConfigSummary(template, edges);

      const paramsContainer = document.getElementById('params-container');
      expect(paramsContainer.innerHTML).to.be.empty;
    });

    it('应该在参数为 null 时优雅处理', () => {
      const template = {
        template_id: 'tpl_001',
        template_name: '测试',
        strategy_type: 'VSS'
        // 没有 parameters_schema
      };

      expect(() => updateConfigSummary(template, [])).not.to.throw();
    });

    it('应该支持多次更新参数表单', () => {
      const template1 = {
        template_name: '模板 1',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'param1',
            parameter_type: 'string',
            description: '参数 1',
            required: false
          }
        ]
      };

      const template2 = {
        template_name: '模板 2',
        strategy_type: 'DHS',
        parameters_schema: [
          {
            parameter_name: 'param2',
            parameter_type: 'integer',
            description: '参数 2',
            required: false
          }
        ]
      };

      // 第一次更新
      updateConfigSummary(template1, []);
      let controls = document.querySelectorAll('.param-control-group');
      expect(controls.length).to.equal(1);

      // 第二次更新（应该清空旧的参数表单）
      updateConfigSummary(template2, []);
      controls = document.querySelectorAll('.param-control-group');
      expect(controls.length).to.equal(1);
    });
  });

  // ============================================================
  // 测试 2: 参数值收集 (3 个测试)
  // ============================================================
  describe('collectParameterValues() - 参数值收集', () => {

    it('应该正确收集字符串参数值', () => {
      const template = {
        template_name: '测试',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'strategy_name',
            parameter_type: 'string',
            description: '策略名称',
            required: false
          }
        ]
      };

      updateConfigSummary(template, []);

      const input = document.querySelector('input[type="text"]');
      input.value = '我的 VSS 策略';

      const values = collectParameterValues('params-container');

      expect(values).to.exist;
      expect(values.strategy_name).to.equal('我的 VSS 策略');
    });

    it('应该正确收集数字参数值', () => {
      const template = {
        template_name: '测试',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'max_speed',
            parameter_type: 'integer',
            description: '最大速度',
            required: false
          }
        ]
      };

      updateConfigSummary(template, []);

      const input = document.querySelector('input[type="number"]');
      input.value = '120';

      const values = collectParameterValues('params-container');

      expect(values.max_speed).to.equal(120);
      expect(typeof values.max_speed).to.equal('number');
    });

    it('应该处理空的参数容器', () => {
      const values = collectParameterValues('nonexistent-container');

      expect(values).to.be.an('object');
      expect(Object.keys(values).length).to.equal(0);
    });
  });

  // ============================================================
  // 测试 3: 参数验证 (3 个测试)
  // ============================================================
  describe('validateAllParameters() - 参数验证', () => {

    it('应该通过所有必填参数都已填写的验证', () => {
      const template = {
        template_name: '测试',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'required_param',
            parameter_type: 'string',
            description: '必填参数',
            required: true
          }
        ]
      };

      updateConfigSummary(template, []);

      const input = document.querySelector('input[type="text"]');
      input.value = '有值';

      const validation = validateAllParameters('params-container');

      expect(validation.valid).to.be.true;
      expect(Object.keys(validation.errors).length).to.equal(0);
    });

    it('应该在必填参数为空时失败验证', () => {
      const template = {
        template_name: '测试',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'required_param',
            parameter_type: 'string',
            description: '必填参数',
            required: true
          }
        ]
      };

      updateConfigSummary(template, []);

      const input = document.querySelector('input[type="text"]');
      input.value = '';

      const validation = validateAllParameters('params-container');

      expect(validation.valid).to.be.false;
      expect(validation.errors.required_param).to.exist;
    });

    it('应该处理不存在的容器', () => {
      const validation = validateAllParameters('nonexistent-container');

      expect(validation.valid).to.be.false;
      expect(validation.errors.container).to.exist;
    });
  });

  // ============================================================
  // 测试 4: 策略提交数据准备 (3 个测试)
  // ============================================================
  describe('prepareStrategySubmission() - 提交数据准备', () => {

    it('应该准备完整的提交数据', () => {
      const template = {
        template_id: 'vss_001',
        template_name: 'VSS 策略',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'speed_limit',
            parameter_type: 'integer',
            description: '速度限制',
            required: false
          }
        ]
      };

      const edges = ['edge1', 'edge2', 'edge3'];

      updateConfigSummary(template, edges);

      const input = document.querySelector('input[type="number"]');
      input.value = '80';

      const submission = prepareStrategySubmission(
        'vss_001',
        edges,
        'params-container'
      );

      expect(submission).to.exist;
      expect(submission.template_id).to.equal('vss_001');
      expect(submission.edges).to.deep.equal(edges);
      expect(submission.parameters.speed_limit).to.equal(80);
      expect(submission.timestamp).to.exist;
    });

    it('应该在缺少必填参数时返回 null', () => {
      const template = {
        template_id: 'vss_001',
        template_name: 'VSS 策略',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'required_speed',
            parameter_type: 'integer',
            description: '必填速度',
            required: true
          }
        ]
      };

      updateConfigSummary(template, ['edge1']);

      const input = document.querySelector('input[type="number"]');
      input.value = ''; // 空值

      const submission = prepareStrategySubmission(
        'vss_001',
        ['edge1'],
        'params-container'
      );

      expect(submission).to.be.null;
    });

    it('应该在缺少路段时返回 null', () => {
      const template = {
        template_id: 'vss_001',
        template_name: 'VSS 策略',
        strategy_type: 'VSS',
        parameters_schema: []
      };

      updateConfigSummary(template, []);

      const submission = prepareStrategySubmission(
        'vss_001',
        [], // 空的路段列表
        'params-container'
      );

      expect(submission).to.be.null;
    });
  });

  // ============================================================
  // 测试 5: 完整工作流 (2 个测试)
  // ============================================================
  describe('完整工作流集成', () => {

    it('应该支持完整的模板-边界-参数-提交工作流', () => {
      // Step 1: 选择模板
      const template = {
        template_id: 'vss_guangzhou_001',
        template_name: '广州环城高速 VSS 控制',
        strategy_type: 'VSS',
        parameters_schema: [
          {
            parameter_name: 'strategy_name',
            parameter_type: 'string',
            description: '策略名称',
            required: true,
            example: '早高峰 VSS'
          },
          {
            parameter_name: 'target_speed',
            parameter_type: 'integer',
            description: '目标速度',
            required: true,
            example: '60'
          }
        ]
      };

      // Step 2: 选择路段
      const edges = [
        'edge_g4202_k52_cw',
        'edge_g4202_k48_cw',
        'edge_g4202_k42_cw'
      ];

      // Step 3: 更新配置
      updateConfigSummary(template, edges);

      // 验证摘要已更新
      expect(document.getElementById('summary-template').textContent).to.not.be.empty;
      expect(document.getElementById('summary-edges').textContent).to.not.be.empty;

      // Step 4: 填写参数
      const inputs = document.querySelectorAll('input');
      expect(inputs.length).to.be.greaterThan(0);

      inputs[0].value = '广州环城 VSS'; // 策略名称
      inputs[1].value = '60'; // 目标速度

      // Step 5: 验证参数
      const validation = validateAllParameters('params-container');
      expect(validation.valid).to.be.true;

      // Step 6: 收集参数
      const parameters = collectParameterValues('params-container');
      expect(parameters.strategy_name).to.equal('广州环城 VSS');
      expect(parameters.target_speed).to.equal(60);

      // Step 7: 准备提交
      const submission = prepareStrategySubmission(
        'vss_guangzhou_001',
        edges,
        'params-container'
      );

      // Step 8: 验证提交数据
      expect(submission).to.exist;
      expect(submission.template_id).to.equal('vss_guangzhou_001');
      expect(submission.edges.length).to.equal(3);
      expect(submission.parameters.strategy_name).to.equal('广州环城 VSS');
      expect(submission.parameters.target_speed).to.equal(60);
      expect(submission.timestamp).to.be.a('string');
    });

    it('应该在表单验证失败时阻止提交', () => {
      const template = {
        template_id: 'dhs_001',
        template_name: 'DHS 策略',
        strategy_type: 'DHS',
        parameters_schema: [
          {
            parameter_name: 'dhs_status',
            parameter_type: 'string',
            description: 'DHS 状态',
            required: true
          }
        ]
      };

      updateConfigSummary(template, ['edge1', 'edge2']);

      // 不填写必填参数
      const input = document.querySelector('input[type="text"]');
      input.value = '';

      // 尝试准备提交
      const submission = prepareStrategySubmission(
        'dhs_001',
        ['edge1', 'edge2'],
        'params-container'
      );

      // 应该返回 null（验证失败）
      expect(submission).to.be.null;
    });
  });
});
