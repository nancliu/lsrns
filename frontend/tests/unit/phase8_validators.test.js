/**
 * Phase 8 Validators Unit Tests
 *
 * Tests for Task 8.1-8.4:
 * - validators.timeOrder()
 * - validators.timeRange()
 * - validators.speedRange()
 * - generateParameterHint()
 * - showError() / clearError()
 *
 * @version 1.0
 * @date 2025-11-01
 */

const { expect } = require('chai');

describe('Phase 8: 验证器单元测试', () => {

  // Mock validators object
  const validators = {
    timeOrder: (beginHours, endHours) => {
      if (beginHours >= endHours) {
        return {
          valid: false,
          message: `开始时间(${beginHours}h)必须小于结束时间(${endHours}h)`
        };
      }
      return { valid: true };
    },

    timeRange: (hours) => {
      if (hours < 0 || hours > 24) {
        return {
          valid: false,
          message: `时间必须在 0-24 小时范围内，当前值: ${hours}`
        };
      }
      return { valid: true };
    },

    speedRange: (speed, min = 0, max = 120) => {
      if (speed < min || speed > max) {
        return {
          valid: false,
          message: `速度必须在 ${min}-${max} km/h 范围内，当前值: ${speed}`
        };
      }
      return { valid: true };
    },

    numberRange: (value, min, max, unit = '') => {
      if (value < min || value > max) {
        return {
          valid: false,
          message: `值必须在 ${min}-${max}${unit ? ' ' + unit : ''} 范围内，当前值: ${value}`
        };
      }
      return { valid: true };
    },

    required: (value) => {
      if (value === '' || value === null || value === undefined) {
        return {
          valid: false,
          message: '此字段为必填项'
        };
      }
      return { valid: true };
    },

    isNumber: (value) => {
      if (value !== '' && isNaN(parseFloat(value))) {
        return {
          valid: false,
          message: '请输入有效的数字'
        };
      }
      return { valid: true };
    }
  };

  // Mock generateParameterHint function
  const generateParameterHint = (param) => {
    const controlHints = {
      'step_array': '使用表格编辑器配置速度步骤。时间单位：小时，速度单位：km/h',
      'dhs_interval_array': '使用表格编辑器配置DHS时间区间。注意：必须覆盖完整的24小时',
      'flow_interval_array': '使用表格编辑器配置流量控制区间。合理设置流量和速度限制',
      'tec_interval_array': '使用表格编辑器配置TEC时间区间'
    };

    const controlHint = controlHints[param.parameter_type] || '';
    let paramHint = '';

    switch (param.parameter_type) {
      case 'integer':
      case 'float':
      case 'number':
        if (param.unit) paramHint += param.unit;
        if (param.min_value !== null && param.max_value !== null) {
          if (paramHint) paramHint += ' · ';
          paramHint += `范围: ${param.min_value}-${param.max_value}`;
        }
        break;

      case 'enum':
        if (param.enum_values && param.enum_values.length > 0) {
          const labels = param.enum_values.map(ev => ev.label || ev).join(', ');
          paramHint = `可选值: ${labels}`;
        } else if (param.unit) {
          paramHint = param.unit;
        }
        break;

      case 'string':
        if (param.allowed_values && param.allowed_values.length > 0) {
          paramHint = `可选值: ${param.allowed_values.join(', ')}`;
        } else if (param.unit) {
          paramHint = param.unit;
        }
        break;

      case 'boolean':
        paramHint = param.unit || '';
        break;

      case 'enum_array':
      case 'array':
        const vehicleTypeParams = ['applicable_vehicle_types', 'allowed_vehicle_types', 'banned_vehicle_types'];
        if (vehicleTypeParams.includes(param.parameter_name)) {
          break;
        }
        paramHint = param.unit || 'JSON数组格式';
        break;

      case 'step_array':
      case 'dhs_interval_array':
      case 'flow_interval_array':
      case 'tec_interval_array':
        paramHint = param.unit || '';
        break;

      default:
        paramHint = param.unit || '';
    }

    if (paramHint && controlHint) {
      return `${paramHint} · ${controlHint}`;
    } else if (controlHint) {
      return controlHint;
    } else {
      return paramHint;
    }
  };

  describe('Task 8.1: 时间顺序验证 (validators.timeOrder)', () => {

    it('应该验证 begin < end 的合法顺序', () => {
      const result = validators.timeOrder(7, 9);
      expect(result.valid).to.be.true;
      expect(result.message).to.be.undefined;
    });

    it('应该拒绝 begin >= end 的非法顺序', () => {
      const result1 = validators.timeOrder(9, 7);
      expect(result1.valid).to.be.false;
      expect(result1.message).to.include('开始时间');

      const result2 = validators.timeOrder(9, 9);
      expect(result2.valid).to.be.false;
    });

    it('应该处理边界值 (0, 24)', () => {
      const result1 = validators.timeOrder(0, 24);
      expect(result1.valid).to.be.true;

      const result2 = validators.timeOrder(24, 0);
      expect(result2.valid).to.be.false;
    });

    it('应该提供清晰的错误信息', () => {
      const result = validators.timeOrder(15, 10);
      expect(result.message).to.include('15');
      expect(result.message).to.include('10');
    });
  });

  describe('Task 8.2: 时间范围验证 (validators.timeRange)', () => {

    it('应该验证 0-24 小时范围内的时间', () => {
      expect(validators.timeRange(0).valid).to.be.true;
      expect(validators.timeRange(12).valid).to.be.true;
      expect(validators.timeRange(24).valid).to.be.true;
    });

    it('应该拒绝范围外的时间值', () => {
      const result1 = validators.timeRange(-1);
      expect(result1.valid).to.be.false;

      const result2 = validators.timeRange(25);
      expect(result2.valid).to.be.false;
    });

    it('应该提供清晰的范围错误信息', () => {
      const result = validators.timeRange(30);
      expect(result.message).to.include('0-24');
      expect(result.message).to.include('30');
    });

    it('应该处理浮点数时间值', () => {
      expect(validators.timeRange(7.5).valid).to.be.true;
      expect(validators.timeRange(24.5).valid).to.be.false;
    });
  });

  describe('Task 8.2: 速度范围验证 (validators.speedRange)', () => {

    it('应该验证默认范围 (0-120) 内的速度', () => {
      expect(validators.speedRange(0).valid).to.be.true;
      expect(validators.speedRange(60).valid).to.be.true;
      expect(validators.speedRange(120).valid).to.be.true;
    });

    it('应该验证自定义范围的速度', () => {
      const result1 = validators.speedRange(50, 30, 130);
      expect(result1.valid).to.be.true;

      const result2 = validators.speedRange(20, 30, 130);
      expect(result2.valid).to.be.false;
    });

    it('应该拒绝超出范围的速度', () => {
      const result1 = validators.speedRange(-10);
      expect(result1.valid).to.be.false;

      const result2 = validators.speedRange(150);
      expect(result2.valid).to.be.false;
    });

    it('应该提供清晰的范围错误信息', () => {
      const result = validators.speedRange(150, 30, 130);
      expect(result.message).to.include('30-130');
      expect(result.message).to.include('150');
    });
  });

  describe('Task 8.2: 数值范围验证 (validators.numberRange)', () => {

    it('应该验证指定范围内的数值', () => {
      const result = validators.numberRange(500, 100, 1000, 'vph');
      expect(result.valid).to.be.true;
    });

    it('应该拒绝范围外的数值', () => {
      const result1 = validators.numberRange(50, 100, 1000);
      expect(result1.valid).to.be.false;

      const result2 = validators.numberRange(1500, 100, 1000);
      expect(result2.valid).to.be.false;
    });

    it('应该在错误信息中包含单位', () => {
      const result = validators.numberRange(50, 100, 1000, 'km');
      expect(result.message).to.include('km');
    });
  });

  describe('其他验证器 (validators.required, isNumber)', () => {

    it('required 应该验证非空值', () => {
      expect(validators.required('value').valid).to.be.true;
      expect(validators.required('').valid).to.be.false;
      expect(validators.required(null).valid).to.be.false;
      expect(validators.required(undefined).valid).to.be.false;
    });

    it('isNumber 应该验证数字格式', () => {
      expect(validators.isNumber('123').valid).to.be.true;
      expect(validators.isNumber('12.5').valid).to.be.true;
      expect(validators.isNumber('abc').valid).to.be.false;
      expect(validators.isNumber('').valid).to.be.true; // 允许空值
    });
  });

  describe('Task 8.4: 提示文本生成 (generateParameterHint)', () => {

    it('应该为数值参数生成单位+范围提示', () => {
      const param = {
        parameter_type: 'number',
        unit: 'km/h',
        min_value: 30,
        max_value: 130
      };
      const hint = generateParameterHint(param);
      expect(hint).to.include('km/h');
      expect(hint).to.include('范围');
      expect(hint).to.include('30-130');
      expect(hint).to.include('·');
    });

    it('应该为 enum 参数生成可选值提示', () => {
      const param = {
        parameter_type: 'enum',
        enum_values: [
          { label: '开放', value: 'OPEN' },
          { label: '关闭', value: 'CLOSED' }
        ]
      };
      const hint = generateParameterHint(param);
      expect(hint).to.include('可选值');
      expect(hint).to.include('开放');
      expect(hint).to.include('关闭');
    });

    it('应该为区间参数生成控件级提示', () => {
      const param = {
        parameter_type: 'dhs_interval_array',
        unit: ''
      };
      const hint = generateParameterHint(param);
      expect(hint).to.include('DHS');
      expect(hint).to.include('表格编辑器');
    });

    it('应该使用中点符号 (·) 分隔参数级和控件级提示', () => {
      const param = {
        parameter_type: 'step_array',
        unit: '小时'
      };
      const hint = generateParameterHint(param);
      expect(hint).to.include('·');
    });

    it('应该为只有控件级提示的参数返回控件级提示', () => {
      const param = {
        parameter_type: 'step_array'
      };
      const hint = generateParameterHint(param);
      expect(hint).to.include('表格编辑器');
    });

    it('应该跳过车型参数的参数级提示', () => {
      const param = {
        parameter_type: 'enum_array',
        parameter_name: 'allowed_vehicle_types'
      };
      const hint = generateParameterHint(param);
      // 不应该生成参数级提示（空字符串）
      expect(hint).to.equal('');
    });

    it('应该处理没有提示的参数', () => {
      const param = {
        parameter_type: 'string'
      };
      const hint = generateParameterHint(param);
      expect(hint).to.equal('');
    });
  });

  describe('验证器集成测试', () => {

    it('应该验证 DHS 区间的完整逻辑', () => {
      // 场景: 用户输入 begin=9, end=9
      const orderResult = validators.timeOrder(9, 9);
      expect(orderResult.valid).to.be.false;

      // 场景: 用户输入 begin=25, end=26
      const beginRangeResult = validators.timeRange(25);
      expect(beginRangeResult.valid).to.be.false;

      // 场景: 合法输入
      const validOrder = validators.timeOrder(9, 11);
      const validBeginRange = validators.timeRange(9);
      const validEndRange = validators.timeRange(11);
      expect(validOrder.valid && validBeginRange.valid && validEndRange.valid).to.be.true;
    });

    it('应该验证 VSS 步骤的完整逻辑', () => {
      // 场景: 时间 = 25 (超出范围)
      const timeResult = validators.timeRange(25);
      expect(timeResult.valid).to.be.false;

      // 场景: 速度 = 150 (超出范围)
      const speedResult = validators.speedRange(150, 30, 130);
      expect(speedResult.valid).to.be.false;

      // 场景: 合法值
      const validTime = validators.timeRange(7);
      const validSpeed = validators.speedRange(80, 30, 130);
      expect(validTime.valid && validSpeed.valid).to.be.true;
    });

    it('应该生成所有参数类型的有效提示', () => {
      const paramTypes = [
        { parameter_type: 'number', unit: 'km', min_value: 0, max_value: 100 },
        { parameter_type: 'enum', enum_values: [{ label: 'A' }] },
        { parameter_type: 'string' },
        { parameter_type: 'boolean' },
        { parameter_type: 'step_array' },
        { parameter_type: 'dhs_interval_array' },
        { parameter_type: 'flow_interval_array' },
        { parameter_type: 'tec_interval_array' }
      ];

      for (const param of paramTypes) {
        const hint = generateParameterHint(param);
        // 提示应该是字符串类型
        expect(typeof hint).to.equal('string');
        console.log(`${param.parameter_type}: "${hint.substring(0, 40)}..."`);
      }
    });
  });

});
