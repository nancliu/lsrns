### 精度分析报告规范（草案）

本文件用于沉淀报告需要展示的内容与结构，供后续补充实现与前后端对齐。

#### 一、报告目标
- 面向业务与研发，清晰呈现精度评估结果与关键诊断线索
- 页面可视化 + 链接到全部产物（CSV/图表），保证可复现

#### 二、推荐结构
1. 概览卡片
   - 批次ID、开始/完成时间、耗时
   - 指标：MAPE、GEH均值、GEH合格率、样本量
2. 指标明细
   - `accuracy_metrics` 全量展示，含相关系数等
3. 数据规模与来源
   - 门架/E1/对齐 三类记录数与唯一数
   - 数据源说明、解析异常统计
4. 图表区
   - 固定顺序展示：
     - 流量散点、速度散点、误差分布、精度热力、精度等级、误差来源、数据质量
     - 条件：E1异常诊断（E1零占比>50%）
5. 结果产物
   - CSV与PNG完整清单（相对路径），用于外部访问
6. 对齐与策略
   - 公共列、MAPE零分母策略（含epsilon可选）
7. 工作流与版本
   - `analysis_tool`/`analysis_version`，工作流步骤

#### 三、后续计划（待补充）
- 指标阈值配置化（报告内标注是否达标）
- 图表交互（缩放/筛选）
- 诊断提示（如数据缺失率/异常占比）

#### 四、产物命名与顺序（已在前端与服务固定）
- CSV：gantry_data_standardized → e1_data_standardized → aligned_data_for_accuracy → alignment_metadata.json → basic_accuracy_metrics → gantry_level_metrics → time_level_metrics
- 图表：flow_scatter → speed_scatter → flow_error_distribution → accuracy_heatmap → accuracy_classification → error_source_analysis → data_quality_assessment → e1_anomaly_diagnosis（条件）
