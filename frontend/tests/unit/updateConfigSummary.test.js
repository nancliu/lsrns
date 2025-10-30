/**
 * 单元测试：updateConfigSummary() 及其子函数
 * Phase 1 重构验证
 *
 * 文件位置：frontend/tests/unit/updateConfigSummary.test.js
 * 运行命令：npm test -- updateConfigSummary.test.js
 */

describe('updateConfigSummary 重构测试套件', () => {

  /**
   * 测试前置处理
   * 为每个测试创建清晰的 DOM 环境和全局变量
   */
  beforeEach(() => {
    // 创建测试 DOM 环境
    document.body.innerHTML = `
      <div id="summary-template"></div>
      <div id="summary-edges"></div>
      <div id="summary-edge-list"></div>
      <div id="params-container"></div>
    `;

    // 初始化全局变量（模拟应用状态）
    window.selectedTemplate = null;
    window.selectedEdges = [];
  });

  /**
   * 测试后置处理
   * 清理 DOM 和全局变量
   */
  afterEach(() => {
    document.body.innerHTML = '';
    window.selectedTemplate = null;
    window.selectedEdges = [];
  });

  // ============================================================
  // 测试 1: updateTemplateSummary() 函数
  // ============================================================
  describe('updateTemplateSummary()', () => {

    it('应该正确更新模板摘要信息', () => {
      // Arrange：准备测试数据
      const template = {
        template_name: '测试模板 VSS-001',
        strategy_type: 'VSS'
      };

      // Act：执行函数
      updateTemplateSummary(template);

      // Assert：验证结果
      const elem = document.getElementById('summary-template');
      expect(elem).to.exist;
      expect(elem.textContent).to.include('测试模板 VSS-001');
      expect(elem.textContent).to.include('可变限速');
    });

    it('应该正确处理 DHS 策略类型', () => {
      const template = {
        template_name: 'DHS 动态硬路肩',
        strategy_type: 'DHS'
      };

      updateTemplateSummary(template);

      const elem = document.getElementById('summary-template');
      expect(elem.textContent).to.include('DHS 动态硬路肩');
      expect(elem.textContent).to.include('动态硬路肩');
    });

    it('应该正确处理 TEC 策略类型', () => {
      const template = {
        template_name: 'TEC 收费站管控',
        strategy_type: 'TEC'
      };

      updateTemplateSummary(template);

      const elem = document.getElementById('summary-template');
      expect(elem.textContent).to.include('收费站管控');
    });

    it('应该在模板为 null 时优雅处理', () => {
      // 不应该抛出错误
      expect(() => updateTemplateSummary(null)).not.to.throw();
      expect(() => updateTemplateSummary(undefined)).not.to.throw();
    });

    it('应该在元素不存在时优雅处理', () => {
      // 移除元素
      document.getElementById('summary-template').remove();

      const template = {
        template_name: '测试',
        strategy_type: 'VSS'
      };

      // 不应该抛出错误
      expect(() => updateTemplateSummary(template)).not.to.throw();
    });

    it('应该正确渲染策略徽章样式', () => {
      const template = {
        template_name: '样式测试',
        strategy_type: 'VSS'
      };

      updateTemplateSummary(template);

      const elem = document.getElementById('summary-template');
      const badge = elem.querySelector('.strategy-badge');

      expect(badge).to.exist;
      expect(badge.className).to.include('badge-VSS');
    });
  });

  // ============================================================
  // 测试 2: updateEdgeSummary() 函数
  // ============================================================
  describe('updateEdgeSummary()', () => {

    it('应该正确显示路段数量', () => {
      // Arrange：准备测试数据
      const edges = ['edge1', 'edge2', 'edge3'];

      // Act：执行函数
      updateEdgeSummary(edges);

      // Assert：验证结果
      const elem = document.getElementById('summary-edges');
      expect(elem).to.exist;
      expect(elem.textContent).to.include('3');
      expect(elem.textContent).to.include('条路段');
    });

    it('应该在路段列表为空时正确显示 0', () => {
      const edges = [];

      updateEdgeSummary(edges);

      const elem = document.getElementById('summary-edges');
      expect(elem.textContent).to.include('0');
    });

    it('应该在只有一个路段时正确显示', () => {
      const edges = ['single-edge'];

      updateEdgeSummary(edges);

      const elem = document.getElementById('summary-edges');
      expect(elem.textContent).to.include('1');
    });

    it('应该在有大量路段时正确显示', () => {
      const edges = Array.from({ length: 100 }, (_, i) => `edge${i}`);

      updateEdgeSummary(edges);

      const elem = document.getElementById('summary-edges');
      expect(elem.textContent).to.include('100');
    });

    it('应该在路段列表为 null 时优雅处理', () => {
      expect(() => updateEdgeSummary(null)).not.to.throw();
      expect(() => updateEdgeSummary(undefined)).not.to.throw();
    });

    it('应该在元素不存在时优雅处理', () => {
      document.getElementById('summary-edges').remove();

      expect(() => updateEdgeSummary(['e1', 'e2'])).not.to.throw();
    });

    it('应该使用正确的样式渲染数字', () => {
      updateEdgeSummary(['e1', 'e2']);

      const elem = document.getElementById('summary-edges');
      const strong = elem.querySelector('strong');

      expect(strong).to.exist;
      expect(strong.style.color).to.equal('rgb(52, 152, 219)'); // #3498db
      expect(strong.textContent).to.equal('2');
    });
  });

  // ============================================================
  // 测试 3: updateEdgeList() 函数
  // ============================================================
  describe('updateEdgeList()', () => {

    it('应该在有路段时正确渲染列表', () => {
      // Arrange
      const edges = ['edge-A', 'edge-B', 'edge-C'];

      // Act
      updateEdgeList(edges);

      // Assert
      const elem = document.getElementById('summary-edge-list');
      expect(elem).to.exist;
      expect(elem.textContent).to.include('edge-A');
      expect(elem.textContent).to.include('edge-B');
      expect(elem.textContent).to.include('edge-C');
    });

    it('应该在路段列表为空时显示警告', () => {
      const edges = [];

      updateEdgeList(edges);

      const elem = document.getElementById('summary-edge-list');
      expect(elem.textContent).to.include('警告');
      expect(elem.textContent).to.include('未选择任何路段');
    });

    it('应该为每条路段创建独立的 div 元素', () => {
      const edges = ['e1', 'e2', 'e3'];

      updateEdgeList(edges);

      const elem = document.getElementById('summary-edge-list');
      const divs = elem.querySelectorAll('div');

      expect(divs.length).to.equal(3);
      expect(divs[0].textContent).to.equal('e1');
      expect(divs[1].textContent).to.equal('e2');
      expect(divs[2].textContent).to.equal('e3');
    });

    it('应该在路段列表为 null 时优雅处理', () => {
      expect(() => updateEdgeList(null)).not.to.throw();
      expect(() => updateEdgeList(undefined)).not.to.throw();
    });

    it('应该在元素不存在时优雅处理', () => {
      document.getElementById('summary-edge-list').remove();

      expect(() => updateEdgeList(['e1'])).not.to.throw();
    });

    it('应该为路段项应用正确的样式', () => {
      updateEdgeList(['edge1']);

      const elem = document.getElementById('summary-edge-list');
      const div = elem.querySelector('div');

      expect(div.style.padding).to.include('3px');
      expect(div.style.borderBottom).to.include('1px solid');
    });

    it('应该在单个路段时正确渲染', () => {
      updateEdgeList(['single']);

      const elem = document.getElementById('summary-edge-list');
      expect(elem.children.length).to.equal(1);
      expect(elem.textContent).to.equal('single');
    });

    it('应该处理包含特殊字符的路段 ID', () => {
      const edges = ['edge-@#$', 'edge_special', 'edge.dot'];

      updateEdgeList(edges);

      const elem = document.getElementById('summary-edge-list');
      expect(elem.textContent).to.include('edge-@#$');
      expect(elem.textContent).to.include('edge_special');
      expect(elem.textContent).to.include('edge.dot');
    });
  });

  // ============================================================
  // 测试 4: updateConfigSummary() 协调函数
  // ============================================================
  describe('updateConfigSummary() [协调函数]', () => {

    it('应该调用所有子函数并更新 DOM', () => {
      // Arrange
      window.selectedTemplate = {
        template_name: '完整测试',
        strategy_type: 'VSS'
      };
      window.selectedEdges = ['edge1', 'edge2'];

      // Act
      updateConfigSummary();

      // Assert：检查所有摘要都被更新
      const templateElem = document.getElementById('summary-template');
      const edgesElem = document.getElementById('summary-edges');
      const edgeListElem = document.getElementById('summary-edge-list');

      expect(templateElem.textContent).to.include('完整测试');
      expect(edgesElem.textContent).to.include('2');
      expect(edgeListElem.textContent).to.include('edge1');
      expect(edgeListElem.textContent).to.include('edge2');
    });

    it('应该在没有模板时正确处理', () => {
      window.selectedTemplate = null;
      window.selectedEdges = ['e1'];

      // 应该不抛出错误
      expect(() => updateConfigSummary()).not.to.throw();

      // 路段摘要应该被更新
      const edgesElem = document.getElementById('summary-edges');
      expect(edgesElem.textContent).to.include('1');
    });

    it('应该在没有路段时正确处理', () => {
      window.selectedTemplate = { template_name: '测试', strategy_type: 'VSS' };
      window.selectedEdges = [];

      expect(() => updateConfigSummary()).not.to.throw();

      const edgesElem = document.getElementById('summary-edges');
      expect(edgesElem.textContent).to.include('0');

      const edgeListElem = document.getElementById('summary-edge-list');
      expect(edgeListElem.textContent).to.include('警告');
    });

    it('应该在全部为空时正确处理', () => {
      window.selectedTemplate = null;
      window.selectedEdges = [];

      // 应该不抛出错误
      expect(() => updateConfigSummary()).not.to.throw();
    });

    it('应该输出正确的日志信息', () => {
      const consoleLogSpy = sinon.spy(console, 'log');

      window.selectedTemplate = { template_name: '测试', strategy_type: 'VSS' };
      window.selectedEdges = [];

      updateConfigSummary();

      // 验证日志调用
      expect(consoleLogSpy.calledWith(sinon.match('[updateConfigSummary]'))).to.be.true;
      expect(consoleLogSpy.calledWith(sinon.match('[updateTemplateSummary]'))).to.be.true;
      expect(consoleLogSpy.calledWith(sinon.match('[updateEdgeSummary]'))).to.be.true;
      expect(consoleLogSpy.calledWith(sinon.match('[updateEdgeList]'))).to.be.true;

      consoleLogSpy.restore();
    });

    it('应该能够多次调用而不出现错误', () => {
      window.selectedTemplate = { template_name: '测试', strategy_type: 'VSS' };
      window.selectedEdges = ['e1', 'e2'];

      // 多次调用
      expect(() => {
        updateConfigSummary();
        updateConfigSummary();
        updateConfigSummary();
      }).not.to.throw();
    });
  });

  // ============================================================
  // 集成测试：完整的配置摘要更新流程
  // ============================================================
  describe('完整集成测试', () => {

    it('应该在更改 selectedTemplate 后更新显示', () => {
      window.selectedTemplate = { template_name: '初始', strategy_type: 'VSS' };
      window.selectedEdges = ['e1'];

      updateConfigSummary();

      let templateElem = document.getElementById('summary-template');
      expect(templateElem.textContent).to.include('初始');

      // 更改模板
      window.selectedTemplate = { template_name: '更新后', strategy_type: 'DHS' };
      updateConfigSummary();

      templateElem = document.getElementById('summary-template');
      expect(templateElem.textContent).to.include('更新后');
      expect(templateElem.textContent).to.include('动态硬路肩');
    });

    it('应该在更改 selectedEdges 后更新显示', () => {
      window.selectedTemplate = { template_name: '测试', strategy_type: 'VSS' };
      window.selectedEdges = ['e1'];

      updateConfigSummary();

      let edgesElem = document.getElementById('summary-edges');
      expect(edgesElem.textContent).to.include('1');

      // 更改路段
      window.selectedEdges = ['e1', 'e2', 'e3'];
      updateConfigSummary();

      edgesElem = document.getElementById('summary-edges');
      expect(edgesElem.textContent).to.include('3');
    });

    it('应该在各种状态组合下正确工作', () => {
      const testCases = [
        { template: null, edges: [] },
        { template: { template_name: 'A', strategy_type: 'VSS' }, edges: [] },
        { template: null, edges: ['e1'] },
        { template: { template_name: 'B', strategy_type: 'DHS' }, edges: ['e1', 'e2'] }
      ];

      testCases.forEach(testCase => {
        window.selectedTemplate = testCase.template;
        window.selectedEdges = testCase.edges;

        // 应该不抛出错误
        expect(() => updateConfigSummary()).not.to.throw();
      });
    });
  });
});

/**
 * 运行这些测试的命令：
 *
 * 1. 运行所有 updateConfigSummary 测试：
 *    npm test -- updateConfigSummary.test.js
 *
 * 2. 运行特定的测试套件：
 *    npm test -- --grep "updateTemplateSummary"
 *
 * 3. 查看覆盖率：
 *    npm test -- --coverage
 *
 * 4. 监视模式（文件改动自动运行）：
 *    npm test -- --watch
 */
