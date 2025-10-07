/**
 * 策略模板库 (Strategy Template Library)
 *
 * 基于高速公路主动交通管控(ATM)专业标准设计
 * 关联文档:
 * - REF-04-高速公路主动交通管控阶段实施参考.md
 * - expressway_ATM策略_DefaultParameters_中文.csv
 * - expressway_ATM_KPIs_中文.csv
 *
 * 提供22个ATM标准模板，支持：
 * - 阶段0: 基准场景(3个)
 * - 阶段1: VSL(7个) + DHS(5个) + 匝道控制(4个)
 * - 阶段2: 组合策略(3个)
 */

class TemplateLibrary {
    constructor() {
        this.templates = this._initializeTemplates();
        // 组合数阈值（超过则需要确认）
        this.combinationHardLimit = 500;     // 硬上限（防止极端爆炸）
        this.combinationSoftLimit = 50;      // 软阈值（弹确认）
    }

    /**
     * 初始化所有22个ATM标准模板
     */
    _initializeTemplates() {
        return [
            // ==================== 阶段0: 基准场景 (3个) ====================
            {
                id: 'tpl_baseline_default',
                name: '基准场景 - 无管控',
                type: 'baseline',
                phase: '阶段0-基准',
                category: 'baseline',
                description: '不采用任何主动管控措施的基础场景，用于对比分析',
                recommended: true,
                parameters: {},
                expected_improvements: {
                    description: '基准场景，无改进指标',
                    metrics: []
                },
                kpi_targets: {},
                ref_doc: 'REF-04 第2.1节 - 建立基线模型'
            },
            {
                id: 'tpl_baseline_peak',
                name: '基准场景 - 早高峰',
                type: 'baseline',
                phase: '阶段0-基准',
                category: 'baseline',
                description: '早高峰时段(7:00-9:00)无管控基准场景',
                parameters: {
                    time_range: '07:00-09:00'
                },
                expected_improvements: {
                    description: '基准场景，无改进指标',
                    metrics: []
                },
                kpi_targets: {},
                ref_doc: 'REF-04 第2.1节'
            },
            {
                id: 'tpl_baseline_evening_peak',
                name: '基准场景 - 晚高峰',
                type: 'baseline',
                phase: '阶段0-基准',
                category: 'baseline',
                description: '晚高峰时段(17:00-19:00)无管控基准场景',
                parameters: {
                    time_range: '17:00-19:00'
                },
                expected_improvements: {
                    description: '基准场景，无改进指标',
                    metrics: []
                },
                kpi_targets: {},
                ref_doc: 'REF-04 第2.1节'
            },

            // ==================== 阶段1 - VSL策略 (7个) ====================
            {
                id: 'tpl_vsl_standard',
                name: 'VSL标准模板',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: 'VSL标准控制策略（SUMO静态配置）',
                recommended: true,
                parameters: {
                    speed: 80,                          // 限速值(km/h) - SUMO直接支持
                    begin_time: '07:00',                // 开始时间
                    end_time: '09:00'                   // 结束时间
                },
                parameter_schema: {
                    speed: { type: 'int', unit: 'km/h', range: [40, 120], sensitivity: 'high' },
                    begin_time: { type: 'string', format: 'HH:MM', sensitivity: 'high' },
                    end_time: { type: 'string', format: 'HH:MM', sensitivity: 'high' }
                },
                expected_improvements: {
                    description: '平滑流速、抑制冲击波、提升可靠性',
                    metrics: ['平均行程时间下降8%', '行程时间95分位下降10%', '平均速度提升5%']
                },
                kpi_targets: {
                    MTT: '下降≥8%',
                    TT95: '下降≥10%',
                    MeanSpeed: '提升≥5%',
                    SpeedSD: '降低'
                },
                ref_doc: 'REF-04 第3.1节 - VSL控制逻辑（简化版，仅SUMO可用参数）'
            },
            {
                id: 'tpl_vsl_aggressive',
                name: 'VSL激进模板 - 低限速',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '更低的限速值，适合高峰严重拥堵路段',
                parameters: {
                    speed: 60,                          // 更低限速值
                    begin_time: '07:30',                // 早高峰核心时段
                    end_time: '08:30'
                },
                expected_improvements: {
                    description: '快速响应拥堵，但可能增加震荡',
                    metrics: ['冲击波抑制效果更强', '限速变化频率较高']
                },
                kpi_targets: {
                    MTT: '下降≥10%',
                    SpeedSD: '可能增加'
                },
                ref_doc: 'REF-04 第3.1节（简化版）'
            },
            {
                id: 'tpl_vsl_conservative',
                name: 'VSL保守模板 - 稳定优先',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '适中限速值，适合交通流平稳路段',
                parameters: {
                    speed: 100,                         // 适中限速值
                    begin_time: '08:00',
                    end_time: '10:00'
                },
                expected_improvements: {
                    description: '减少震荡，但响应较慢',
                    metrics: ['限速变化频率低', '驾驶员舒适性高']
                },
                kpi_targets: {
                    SpeedSD: '显著降低',
                    MTT: '下降≥5%'
                },
                ref_doc: 'REF-04 第3.1节（简化版）'
            },
            {
                id: 'tpl_vsl_sensitivity_time',
                name: 'VSL敏感性分析 - 时段分割',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'sensitivity_analysis',
                description: '用于测试不同时段分割的敏感性分析（替代control_interval）',
                sensitivity_analysis: true,
                parameter_ranges: {
                    begin_time: ['07:00', '07:30', '08:00'],    // 3种开始时间
                    end_time: ['09:00', '09:30', '10:00']       // 3种结束时间
                },
                parameters: {
                    speed: 80,                          // 基准限速
                    begin_time: '07:00',
                    end_time: '09:00'
                },
                expected_improvements: {
                    description: '识别最优时段分割（替代控制周期敏感性分析）',
                    metrics: ['生成9组策略进行对比']
                },
                ref_doc: 'REF-04 第4.2节 - 参数敏感性分析（简化版，时段分割替代控制周期）'
            },
            {
                id: 'tpl_vsl_sensitivity_speed',
                name: 'VSL敏感性分析 - 限速值',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'sensitivity_analysis',
                description: '用于测试不同限速值的敏感性分析',
                sensitivity_analysis: true,
                parameter_ranges: {
                    speed: [60, 80, 100]                // 3种限速值
                },
                parameters: {
                    speed: 80,
                    begin_time: '07:00',
                    end_time: '09:00'
                },
                expected_improvements: {
                    description: '识别最优限速值',
                    metrics: ['生成3组策略进行对比']
                },
                ref_doc: 'REF-04 第4.2节（简化版）'
            },
            {
                id: 'tpl_vsl_sensitivity_full',
                name: 'VSL全参数敏感性分析',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'sensitivity_analysis',
                description: '笛卡尔积生成27组VSL策略(3×3×3)',
                sensitivity_analysis: true,
                parameter_ranges: {
                    speed: [60, 80, 100],
                    begin_time: ['07:00', '07:30', '08:00'],
                    end_time: ['09:00', '09:30', '10:00']
                },
                parameters: {
                    speed: 80,
                    begin_time: '07:00',
                    end_time: '09:00'
                },
                expected_improvements: {
                    description: '全面识别最优参数组合',
                    metrics: ['生成27组策略进行对比']
                },
                ref_doc: 'REF-04 第4.2节（简化版，SUMO可用参数）'
            },
            {
                id: 'tpl_vsl_low_speed_limit',
                name: 'VSL低限速保护模板',
                type: 'VSL',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '较低限速，适合雨雾天气或安全要求高的路段',
                parameters: {
                    speed: 40,                          // 低限速值（安全优先）
                    begin_time: '06:00',                // 全天候适用
                    end_time: '22:00'
                },
                expected_improvements: {
                    description: '提升安全性，但可能降低通行能力',
                    metrics: ['事故风险降低', '通行能力下降5-10%']
                },
                kpi_targets: {
                    SafetyProxy: '改善',
                    Throughput: '可能下降'
                },
                ref_doc: 'REF-04 第3.1节（简化版）'
            },

            // ==================== 阶段1 - DHS策略 (5个) ====================
            {
                id: 'tpl_dhs_standard',
                name: 'DHS标准模板',
                type: 'DHS',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: 'DHS标准控制策略（SUMO静态配置）',
                recommended: true,
                parameters: {
                    shoulder_lane: 'main_road_2',       // 硬路肩车道ID
                    allow_vehicle_types: 'passenger',   // 允许车型
                    begin_time: '07:00',                // 开始时间
                    end_time: '09:00',                  // 结束时间
                    segment: 'K10-K15'                  // 路段标识（仅用于显示，不影响仿真）
                },
                parameter_schema: {
                    shoulder_lane: { type: 'string', description: '硬路肩车道ID', sensitivity: 'high' },
                    allow_vehicle_types: { type: 'string', options: ['passenger', 'bus', 'all'], sensitivity: 'high' },
                    begin_time: { type: 'string', format: 'HH:MM', sensitivity: 'high' },
                    end_time: { type: 'string', format: 'HH:MM', sensitivity: 'high' },
                    segment: { type: 'string', description: '路段标识（可选，仅用于标识）', sensitivity: 'none' }
                },
                expected_improvements: {
                    description: '高峰时开放硬路肩增加通行能力',
                    metrics: ['通行量提升5%', '路肩使用率可控']
                },
                kpi_targets: {
                    Throughput: '提升≥5%',
                    ShoulderUtil: '可控范围',
                    MTT: '下降≥5%'
                },
                ref_doc: 'REF-04 第3.2节 - DHS控制逻辑（简化版，仅SUMO可用参数）'
            },
            {
                id: 'tpl_dhs_aggressive',
                name: 'DHS激进模板 - 早开启',
                type: 'DHS',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '更长时段，更早开放硬路肩以缓解拥堵',
                parameters: {
                    shoulder_lane: 'main_road_2',
                    allow_vehicle_types: 'passenger',
                    begin_time: '06:30',                // 更早开始
                    end_time: '09:30',                  // 更晚结束（更长时段）
                    segment: 'K8-K18'                   // 可选标识
                },
                expected_improvements: {
                    description: '更早缓解拥堵，但安全风险增加',
                    metrics: ['通行量提升7-10%', '路肩使用率高']
                },
                kpi_targets: {
                    Throughput: '提升≥7%',
                    SafetyProxy: '需监控'
                },
                ref_doc: 'REF-04 第3.2节（简化版）'
            },
            {
                id: 'tpl_dhs_conservative',
                name: 'DHS保守模板 - 安全优先',
                type: 'DHS',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '较短时段，仅在高峰核心时段开放硬路肩',
                parameters: {
                    shoulder_lane: 'main_road_2',
                    allow_vehicle_types: 'passenger',
                    begin_time: '07:30',                // 高峰核心时段
                    end_time: '08:30',                  // 较短时段
                    segment: 'K12-K15'                  // 可选标识
                },
                expected_improvements: {
                    description: '安全性高，但通行能力提升有限',
                    metrics: ['通行量提升3-5%', '安全风险低']
                },
                kpi_targets: {
                    Throughput: '提升≥3%',
                    SafetyProxy: '最佳'
                },
                ref_doc: 'REF-04 第3.2节（简化版）'
            },
            {
                id: 'tpl_dhs_sensitivity_time',
                name: 'DHS敏感性分析 - 时段分析',
                type: 'DHS',
                phase: '阶段1-策略设计',
                category: 'sensitivity_analysis',
                description: '用于测试不同时段分割的敏感性分析',
                sensitivity_analysis: true,
                parameter_ranges: {
                    begin_time: ['06:30', '07:00', '07:30'],    // 3种开始时间
                    end_time: ['08:30', '09:00', '09:30']       // 3种结束时间
                },
                parameters: {
                    shoulder_lane: 'main_road_2',
                    allow_vehicle_types: 'passenger',
                    begin_time: '07:00',
                    end_time: '09:00',
                    segment: 'K10-K15'                  // 可选标识
                },
                expected_improvements: {
                    description: '识别最优时段分割',
                    metrics: ['生成9组策略进行对比']
                },
                ref_doc: 'REF-04 第4.2节（简化版）'
            },
            {
                id: 'tpl_dhs_sensitivity_full',
                name: 'DHS全参数敏感性分析',
                type: 'DHS',
                phase: '阶段1-策略设计',
                category: 'sensitivity_analysis',
                description: '笛卡尔积生成18组DHS策略(3×3×2)',
                sensitivity_analysis: true,
                parameter_ranges: {
                    begin_time: ['06:30', '07:00', '07:30'],
                    end_time: ['08:30', '09:00', '09:30'],
                    allow_vehicle_types: ['passenger', 'all']
                },
                parameters: {
                    shoulder_lane: 'main_road_2',
                    allow_vehicle_types: 'passenger',
                    begin_time: '07:00',
                    end_time: '09:00',
                    segment: 'K10-K15'
                },
                expected_improvements: {
                    description: '全面识别最优参数组合',
                    metrics: ['生成18组策略进行对比']
                },
                ref_doc: 'REF-04 第4.2节（简化版，SUMO可用参数）'
            },

            // ==================== 阶段1 - 匝道控制策略 (4个) ====================
            {
                id: 'tpl_zone_restriction_standard',
                name: '入口管控标准模板',
                type: 'zone_restriction',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '基于主线占有率触发的货车限行策略',
                recommended: true,
                parameters: {
                    trigger_occupancy: 0.88,           // 货车限行触发(主线占有率) - CSV第15行
                    ramp_queue_threshold: 30,          // 匝道排队阈值(辆) - CSV第16行
                    priority_order: '货限→限流→封匝道', // 处置优先级 - CSV第17行
                    advance_notice_time: 5,            // 预告提前时间(分钟) - CSV第18行
                    restricted_vehicle_types: ['truck']
                },
                parameter_schema: {
                    trigger_occupancy: { type: 'float', range: [0.8, 0.95], sensitivity: 'high' },
                    ramp_queue_threshold: { type: 'int', unit: '辆', range: [20, 50], sensitivity: 'high' },
                    advance_notice_time: { type: 'int', unit: '分钟', range: [3, 10], sensitivity: 'medium' },
                    restricted_vehicle_types: { type: 'array', options: ['truck', 'bus', 'passenger'] }
                },
                expected_improvements: {
                    description: '限制货车进入以减轻主线拥堵',
                    metrics: ['主线拥堵缓解', '货车分流数可控']
                },
                kpi_targets: {
                    BreakdownProb: '降低',
                    TrucksDiverted: '影响追踪',
                    MaxRampQueue: '波动≤10%'
                },
                ref_doc: 'REF-04 第3.3节 - 匝道控制逻辑; CSV第15-19行'
            },
            {
                id: 'tpl_zone_restriction_aggressive',
                name: '入口管控激进模板',
                type: 'zone_restriction',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '更低的触发阈值，早期限制货车进入',
                parameters: {
                    trigger_occupancy: 0.80,           // 更低阈值
                    ramp_queue_threshold: 25,
                    priority_order: '货限→限流→封匝道',
                    advance_notice_time: 8,            // 更长预告时间
                    restricted_vehicle_types: ['truck']
                },
                expected_improvements: {
                    description: '更早缓解主线拥堵，但货车分流数增加',
                    metrics: ['主线拥堵显著缓解', '货车分流数高']
                },
                kpi_targets: {
                    BreakdownProb: '显著降低',
                    TrucksDiverted: '增加'
                },
                ref_doc: 'REF-04 第3.3节'
            },
            {
                id: 'tpl_zone_restriction_all_vehicles',
                name: '入口管控 - 全车型限制',
                type: 'zone_restriction',
                phase: '阶段1-策略设计',
                category: 'threshold_based',
                description: '极端拥堵时限制所有车型进入(关闭匝道)',
                parameters: {
                    trigger_occupancy: 0.92,           // 更高阈值(极端情况)
                    ramp_queue_threshold: 40,
                    priority_order: '货限→限流→封匝道',
                    advance_notice_time: 10,
                    restricted_vehicle_types: ['truck', 'bus', 'passenger']  // 全车型
                },
                expected_improvements: {
                    description: '极端措施，防止路网瘫痪',
                    metrics: ['路网瘫痪风险降低', '替代路线压力增加']
                },
                kpi_targets: {
                    BreakdownProb: '最低',
                    TrucksDiverted: '最高'
                },
                ref_doc: 'REF-04 第3.3节'
            },
            {
                id: 'tpl_zone_restriction_sensitivity',
                name: '入口管控敏感性分析',
                type: 'zone_restriction',
                phase: '阶段1-策略设计',
                category: 'sensitivity_analysis',
                description: '笛卡尔积生成6组入口管控策略(3×2)',
                sensitivity_analysis: true,
                parameter_ranges: {
                    trigger_occupancy: [0.80, 0.88, 0.92],
                    ramp_queue_threshold: [25, 35]
                },
                parameters: {
                    trigger_occupancy: 0.88,
                    ramp_queue_threshold: 30,
                    priority_order: '货限→限流→封匝道',
                    advance_notice_time: 5,
                    restricted_vehicle_types: ['truck']
                },
                expected_improvements: {
                    description: '识别最优触发参数',
                    metrics: ['生成6组策略进行对比']
                },
                ref_doc: 'REF-04 第4.2节'
            },

            // ==================== 阶段2 - 组合策略 (3个) ====================
            {
                id: 'tpl_combo_vsl_dhs',
                name: '组合策略 - VSL+DHS',
                type: 'combination',
                phase: '阶段2-组合策略',
                category: 'combination',
                description: 'VSL配合DHS的协同控制策略',
                recommended: true,
                sub_strategies: ['tpl_vsl_standard', 'tpl_dhs_standard'],
                parameters: {
                    coordination_logic: 'DHS开启时，VSL限速降低10km/h'
                },
                expected_improvements: {
                    description: '综合提升通行能力和安全性',
                    metrics: ['通行量提升10-15%', '行程时间下降12%', '速度标准差降低']
                },
                kpi_targets: {
                    Throughput: '提升≥10%',
                    MTT: '下降≥12%',
                    SpeedSD: '显著降低'
                },
                ref_doc: 'REF-04 第5.1节 - 组合策略协同'
            },
            {
                id: 'tpl_combo_vsl_zone',
                name: '组合策略 - VSL+入口管控',
                type: 'combination',
                phase: '阶段2-组合策略',
                category: 'combination',
                description: 'VSL配合入口管控的协同控制策略',
                sub_strategies: ['tpl_vsl_standard', 'tpl_zone_restriction_standard'],
                parameters: {
                    coordination_logic: '入口限制货车后，VSL限速提升10km/h'
                },
                expected_improvements: {
                    description: '货车限行后主线流速恢复',
                    metrics: ['主线拥堵缓解', '货车分流有序']
                },
                kpi_targets: {
                    BreakdownProb: '显著降低',
                    MeanSpeed: '提升≥8%'
                },
                ref_doc: 'REF-04 第5.1节'
            },
            {
                id: 'tpl_combo_full',
                name: '组合策略 - VSL+DHS+入口管控',
                type: 'combination',
                phase: '阶段2-组合策略',
                category: 'combination',
                description: '三大策略的全面协同控制',
                sub_strategies: ['tpl_vsl_standard', 'tpl_dhs_standard', 'tpl_zone_restriction_standard'],
                parameters: {
                    coordination_logic: '分级触发：VSL→DHS→入口管控'
                },
                expected_improvements: {
                    description: '全面优化路网性能',
                    metrics: ['通行量提升15-20%', '行程时间下降15%', '路网韧性增强']
                },
                kpi_targets: {
                    Throughput: '提升≥15%',
                    MTT: '下降≥15%',
                    BreakdownProb: '最低',
                    SpeedSD: '显著降低'
                },
                ref_doc: 'REF-04 第5.2节 - 全面协同策略'
            }
        ];
    }

    /**
     * 根据ID获取模板
     * @param {string} id - 模板ID
     * @returns {object|null} 模板对象，如果不存在返回null
     */
    getTemplateById(id) {
        return this.templates.find(t => t.id === id) || null;
    }

    /**
     * 参数校验（基于模板的 parameter_schema 可选）
     * @param {object} template 模板
     * @param {object} params   实际参数
     * @returns {{valid:boolean, errors:string[]}}
     */
    validateParameters(template, params) {
        const schema = template.parameter_schema || {};
        const errors = [];

        const isHHMM = (v) => /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/.test(String(v));

        Object.entries(schema).forEach(([key, rule]) => {
            const value = params[key];
            const type = rule.type;

            // 必填检查（如果 schema 中声明但参数缺失）
            if (value === undefined || value === null || value === '') {
                errors.push(`${key} 缺失或为空`);
                return;
            }

            // 类型检查
            if (type === 'int' && !Number.isInteger(Number(value))) {
                errors.push(`${key} 需要整数`);
            }
            if (type === 'float' && isNaN(Number(value))) {
                errors.push(`${key} 需要数值`);
            }
            if (type === 'string' && typeof value !== 'string') {
                errors.push(`${key} 需要字符串`);
            }
            if (type === 'array' && !Array.isArray(value)) {
                errors.push(`${key} 需要数组`);
            }

            // 枚举/选项检查
            if (rule.options && Array.isArray(rule.options)) {
                const candidate = Array.isArray(value) ? value : [value];
                const invalid = candidate.filter(v => !rule.options.includes(v));
                if (invalid.length > 0) {
                    errors.push(`${key} 包含非法取值: ${invalid.join(',')}`);
                }
            }

            // 范围检查
            if (rule.range && Array.isArray(rule.range) && rule.range.length === 2) {
                const [min, max] = rule.range;
                const num = Number(value);
                if (!isNaN(num) && (num < min || num > max)) {
                    errors.push(`${key} 超出范围 [${min}, ${max}]`);
                }
            }

            // 格式检查
            if (rule.format === 'HH:MM' && !isHHMM(value)) {
                errors.push(`${key} 需要 HH:MM 格式`);
            }
        });

        return { valid: errors.length === 0, errors };
    }

    /**
     * 按阶段筛选模板
     * @param {string} phase - 阶段名称(阶段0-基准 | 阶段1-策略设计 | 阶段2-组合策略)
     * @returns {array} 模板数组
     */
    getTemplatesByPhase(phase) {
        return this.templates.filter(t => t.phase === phase);
    }

    /**
     * 按分类筛选模板
     * @param {string} category - 分类名称(baseline | threshold_based | sensitivity_analysis | combination)
     * @returns {array} 模板数组
     */
    getTemplatesByCategory(category) {
        return this.templates.filter(t => t.category === category);
    }

    /**
     * 按策略类型筛选模板
     * @param {string} type - 策略类型(VSL | DHS | zone_restriction | baseline | combination)
     * @returns {array} 模板数组
     */
    getTemplatesByType(type) {
        return this.templates.filter(t => t.type === type);
    }

    /**
     * 获取推荐模板
     * @returns {array} 推荐模板数组
     */
    getRecommendedTemplates() {
        return this.templates.filter(t => t.recommended === true);
    }

    /**
     * 将模板参数填充到表单
     * @param {string} templateId - 模板ID
     * @param {HTMLFormElement} formElement - 表单DOM元素
     * @returns {boolean} 是否成功填充
     */
    applyTemplateToForm(templateId, formElement) {
        const template = this.getTemplateById(templateId);
        if (!template) {
            console.error(`Template not found: ${templateId}`);
            return false;
        }

        try {
            // 填充基础信息
            const nameInput = formElement.querySelector('#strategyName');
            const typeSelect = formElement.querySelector('#strategyType');
            const descInput = formElement.querySelector('#strategyDescription');

            if (nameInput) nameInput.value = template.name;
            if (typeSelect) typeSelect.value = template.type;
            if (descInput) descInput.value = template.description;

            // 触发策略类型变化事件，显示对应参数表单
            if (typeSelect) {
                const event = new Event('change', { bubbles: true });
                typeSelect.dispatchEvent(event);
            }

            // 等待参数表单渲染后填充参数
            setTimeout(() => {
                // 参数校验（若失败则提示并不填充）
                const validation = this.validateParameters(template, template.parameters || {});
                if (!validation.valid) {
                    const msg = `模板参数不符合约束:\n- ${validation.errors.join('\n- ')}`;
                    console.error(msg);
                    if (typeof window !== 'undefined' && window.alert) {
                        window.alert(msg);
                    }
                    return;
                }
                this._fillParameters(template.type, template.parameters, formElement);
            }, 100);

            return true;
        } catch (error) {
            console.error('Error applying template to form:', error);
            return false;
        }
    }

    /**
     * 填充策略参数到表单
     * @private
     */
    _fillParameters(strategyType, parameters, formElement) {
        switch (strategyType) {
            case 'VSL':
                this._fillVSLParameters(parameters, formElement);
                break;
            case 'DHS':
                this._fillDHSParameters(parameters, formElement);
                break;
            case 'zone_restriction':
                this._fillZoneRestrictionParameters(parameters, formElement);
                break;
            case 'baseline':
                // 基准场景无需填充参数
                break;
            case 'combination':
                // 组合策略暂不支持单表单填充
                console.warn('Combination strategies require multiple strategy creation');
                break;
        }
    }

    /**
     * 填充VSL参数
     * @private
     */
    _fillVSLParameters(params, formElement) {
        // 新参数字段：vslSpeed, vslBeginTime, vslEndTime
        const speedInput = formElement.querySelector('#vslSpeed');
        const beginTimeInput = formElement.querySelector('#vslBeginTime');
        const endTimeInput = formElement.querySelector('#vslEndTime');

        if (speedInput && params.speed) {
            speedInput.value = params.speed;
        }
        if (beginTimeInput && params.begin_time) {
            beginTimeInput.value = params.begin_time;
        }
        if (endTimeInput && params.end_time) {
            endTimeInput.value = params.end_time;
        }
    }

    /**
     * 填充DHS参数
     * @private
     */
    _fillDHSParameters(params, formElement) {
        // 当前表单字段：dhsTimeSlot, dhsSegment
        const timeSlotInput = formElement.querySelector('#dhsTimeSlot');
        const segmentInput = formElement.querySelector('#dhsSegment');

        // 如果模板有time_slot参数，填充时段
        if (timeSlotInput && params.time_slot) {
            timeSlotInput.value = params.time_slot;
        }

        // 如果模板有segment参数，填充路段
        if (segmentInput && params.segment) {
            segmentInput.value = params.segment;
        }

        // 注意：完整ATM参数(open_threshold_occupancy等)当前表单不支持
        console.log('DHS template parameters:', params);
    }

    /**
     * 填充入口管控参数
     * @private
     */
    _fillZoneRestrictionParameters(params, formElement) {
        // 当前表单字段：restrictionZone, vehicleTypes, restrictionTimeSlot
        const zoneInput = formElement.querySelector('#restrictionZone');
        const vehicleTypesInput = formElement.querySelector('#vehicleTypes');
        const timeSlotInput = formElement.querySelector('#restrictionTimeSlot');

        // 填充限行区域
        if (zoneInput && params.restriction_zone) {
            zoneInput.value = params.restriction_zone;
        }

        // 填充车辆类型
        if (vehicleTypesInput) {
            if (params.restricted_vehicle_types && Array.isArray(params.restricted_vehicle_types)) {
                vehicleTypesInput.value = params.restricted_vehicle_types.join(', ');
            } else if (params.vehicle_types) {
                vehicleTypesInput.value = params.vehicle_types;
            }
        }

        // 填充时段
        if (timeSlotInput && params.time_slot) {
            timeSlotInput.value = params.time_slot;
        }

        // 注意：完整ATM参数(trigger_occupancy等)当前表单不支持
        console.log('Zone restriction template parameters:', params);
    }

    /**
     * 通用输入填充方法
     * @private
     */
    _fillInputs(params, mapping, formElement) {
        for (const [paramKey, selector] of Object.entries(mapping)) {
            if (params.hasOwnProperty(paramKey)) {
                const input = formElement.querySelector(selector);
                if (input) {
                    input.value = params[paramKey];
                }
            }
        }
    }

    /**
     * 生成敏感性分析批次
     * @param {string} templateId - 敏感性分析模板ID
     * @returns {array} 参数组合数组
     */
    generateSensitivityBatch(templateId) {
        const template = this.getTemplateById(templateId);
        if (!template || !template.sensitivity_analysis) {
            console.error(`Not a sensitivity analysis template: ${templateId}`);
            return [];
        }

        const baseParams = { ...template.parameters };
        const ranges = template.parameter_ranges;

        // 预估组合数并进行阈值确认
        const estimate = this.estimateCombinationCount(ranges);
        if (estimate > this.combinationHardLimit) {
            const msg = `组合数(${estimate})超过硬上限(${this.combinationHardLimit})，已阻止生成。请缩小参数范围。`;
            console.error(msg);
            if (typeof window !== 'undefined' && window.alert) window.alert(msg);
            return [];
        }
        if (estimate > this.combinationSoftLimit) {
            const confirmMsg = `将生成 ${estimate} 组策略，是否继续？`;
            let ok = true;
            if (typeof window !== 'undefined' && window.confirm) {
                ok = window.confirm(confirmMsg);
            }
            if (!ok) return [];
        }

        // 生成笛卡尔积
        const combinations = this._cartesianProduct(ranges);

        // 将每个组合与基础参数合并
        return combinations.map((combo, index) => ({
            name: `${template.name}_${index + 1}`,
            type: template.type,
            description: `${template.description} - 组合${index + 1}`,
            parameters: { ...baseParams, ...combo }
        }));
    }

    /**
     * 笛卡尔积算法
     * @private
     */
    _cartesianProduct(ranges) {
        const keys = Object.keys(ranges);
        if (keys.length === 0) return [];

        const values = keys.map(k => ranges[k]);

        function product(arrays) {
            if (arrays.length === 0) return [[]];
            const [first, ...rest] = arrays;
            const restProduct = product(rest);
            return first.flatMap(value =>
                restProduct.map(combination => [value, ...combination])
            );
        }

        const combos = product(values);
        return combos.map(combo => {
            const obj = {};
            keys.forEach((key, i) => {
                obj[key] = combo[i];
            });
            return obj;
        });
    }

    /**
     * 估算组合数
     * @param {object} ranges parameter_ranges
     * @returns {number}
     */
    estimateCombinationCount(ranges) {
        if (!ranges || Object.keys(ranges).length === 0) return 0;
        return Object.values(ranges).reduce((acc, arr) => acc * (Array.isArray(arr) ? arr.length : 1), 1);
    }

    /**
     * 获取模板统计信息
     * @returns {object} 统计信息
     */
    getStatistics() {
        return {
            total: this.templates.length,
            byPhase: {
                '阶段0-基准': this.getTemplatesByPhase('阶段0-基准').length,
                '阶段1-策略设计': this.getTemplatesByPhase('阶段1-策略设计').length,
                '阶段2-组合策略': this.getTemplatesByPhase('阶段2-组合策略').length
            },
            byType: {
                'baseline': this.getTemplatesByType('baseline').length,
                'VSL': this.getTemplatesByType('VSL').length,
                'DHS': this.getTemplatesByType('DHS').length,
                'zone_restriction': this.getTemplatesByType('zone_restriction').length,
                'combination': this.getTemplatesByType('combination').length
            },
            recommended: this.getRecommendedTemplates().length,
            sensitivityAnalysis: this.templates.filter(t => t.sensitivity_analysis).length
        };
    }
}

// 导出为全局变量(浏览器环境)
if (typeof window !== 'undefined') {
    window.TemplateLibrary = TemplateLibrary;
}

// 支持模块化导出(如果需要)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplateLibrary;
}
