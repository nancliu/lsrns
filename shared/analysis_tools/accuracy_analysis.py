"""
精度分析模块
专门处理门架数据与E1数据的精度对比分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from matplotlib import rcParams
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AccuracyAnalysis:
    """精度分析类"""

    def __init__(self):
        self.analysis_results = {}
        self.charts_dir = None
        self.reports_dir = None
        # 初始化绘图与中文字体
        self._preferred_cn_font = None
        self._setup_plot_style()

        # 定义门架顺序
        self.gantry_order = [
            'G420151002000320010',
            'G420151002000220010',
            'G420151002000120010',
            'G420151001001320010',
            'G420151001001220010',
            'G420151001001120010',
            'G420151001001020010',
            'G420151001000920010',
            'G420151001000820010',
            'G420151001000710010',
            'G420151001000620010',
            'G420151001000220010',
            'G420151001000120010',
            'G420151002001020010',
            'G420151002000920010',
            'G420151002000820010',
            'G420151002000720010',
            'G420151002000620010',
            'G420151002000520010',
            'G420151002000420010',
            'G420151002000310010',
            'G420151002000210010',
            'G420151002000110010',
            'G420151001001310010',
            'G420151001001210010',
            'G420151001001110010',
            'G420151001001010010',
            'G420151001000910010',
            'G420151001000810010',
            'G420151001000720010',
            'G420151001000610010',
            'G420151001000510010',
            'G420151001000110010',
            'G420151002001010010',
            'G420151002000910010',
            'G420151002000810010',
            'G420151002000710010',
            'G420151002000610010',
            'G420151002000510010',
            'G420151002000410010'
        ]

    def set_output_dirs(self, charts_dir: str, reports_dir: str):
        """设置输出目录"""
        self.charts_dir = Path(charts_dir)
        self.reports_dir = Path(reports_dir)

        # 创建目录
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"设置输出目录: 图表={charts_dir}, 报告={reports_dir}")

    def _setup_plot_style(self) -> None:
        """配置绘图风格与中文字体，避免中文字符缺失警告。"""
        try:
            # 基本配色
            sns.set_palette("husl")
        except Exception:
            pass
        # 配置中文字体
        self._ensure_chinese_font()

    def _ensure_chinese_font(self) -> None:
        """设置支持中文的字体到 rcParams（优先系统常见中文字体）。"""
        candidates = [
            "Microsoft YaHei",  # Windows 常见
            "SimHei",           # Windows/部分环境
            "Noto Sans CJK SC", # Noto
            "Source Han Sans CN",
            "WenQuanYi Zen Hei",
            "Arial Unicode MS",
        ]
        picked = None
        for name in candidates:
            try:
                # 若能找到该字体文件则认为可用
                fm.findfont(name, fallback_to_default=False)
                picked = name
                break
            except Exception:
                continue
        if not picked:
            picked = "Microsoft YaHei"  # 尝试指定，若无则由matplotlib回退
        self._preferred_cn_font = picked
        try:
            rcParams["font.sans-serif"] = [picked, "DejaVu Sans", "Arial Unicode MS"]
            rcParams["axes.unicode_minus"] = False
        except Exception:
            pass

        logger.info(f"设置中文字体: {picked}")

    def _ensure_font_for_plot(self) -> None:
        """确保当前绘图使用正确的中文字体"""
        try:
            # 重新应用字体设置，确保当前matplotlib实例使用正确字体
            if self._preferred_cn_font:
                rcParams["font.sans-serif"] = [self._preferred_cn_font, "DejaVu Sans", "Arial Unicode MS"]
                rcParams["axes.unicode_minus"] = False
        except Exception as e:
            logger.warning(f"重新应用字体设置失败: {e}")

    def analyze_accuracy(self, aligned_data: pd.DataFrame) -> Dict[str, Any]:
        """
        执行精度分析

        Args:
            aligned_data: 对齐后的门架-E1数据

        Returns:
            分析结果字典
        """
        try:
            logger.info("开始精度分析...")

            if aligned_data.empty:
                raise Exception("对齐数据为空，无法进行精度分析")

            # 1. 计算基础精度指标
            basic_metrics = self._calculate_basic_metrics(aligned_data)

            # 2. 计算门架级别精度指标
            gantry_metrics = self._calculate_gantry_level_metrics(aligned_data)

            # 3. 计算时间级别精度指标
            time_metrics = self._calculate_time_level_metrics(aligned_data)

            # 4. 生成精度分析图表
            chart_files = self._generate_accuracy_charts(aligned_data, basic_metrics)

            # 5. 生成分析报告
            report_file = self._generate_accuracy_report(basic_metrics, gantry_metrics, time_metrics, chart_files)

            # 6. 导出分析结果CSV
            csv_files = self._export_analysis_csvs(aligned_data, basic_metrics, gantry_metrics, time_metrics)

            results = {
                "basic_metrics": basic_metrics,
                "gantry_metrics": gantry_metrics,
                "time_metrics": time_metrics,
                "chart_files": chart_files,
                "report_file": report_file,
                "csv_files": csv_files,
                "analysis_time": pd.Timestamp.now().isoformat()
            }

            self.analysis_results = results
            logger.info("精度分析完成")
            return results

        except Exception as e:
            logger.error(f"精度分析失败: {e}")
            return {}

    def _calculate_basic_metrics(self, aligned_data: pd.DataFrame) -> Dict[str, float]:
        """计算基础精度指标"""
        try:
            metrics = {}

            # 解析时间并排序数据
            df = aligned_data.copy()
            df['time_key'] = pd.to_datetime(df['time_key'])
            df = df.sort_values(['gantry_id', 'time_key'])

            # 流量精度指标（切换为 volume）
            if 'gantry_volume' in df.columns and 'e1_volume' in df.columns:
                gantry_flow = df['gantry_volume'].dropna()
                e1_flow = df['e1_volume'].dropna()

                if len(gantry_flow) > 0 and len(e1_flow) > 0:
                    min_len = min(len(gantry_flow), len(e1_flow))
                    gantry_flow = gantry_flow.iloc[:min_len]
                    e1_flow = e1_flow.iloc[:min_len]

                    # MAE
                    metrics['flow_mae'] = float(np.mean(np.abs(gantry_flow - e1_flow)))
                    # MSE
                    metrics['flow_mse'] = float(np.mean((gantry_flow - e1_flow) ** 2))
                    # RMSE
                    metrics['flow_rmse'] = float(np.sqrt(metrics['flow_mse']))
                    # MAPE
                    non_zero_mask = e1_flow != 0
                    if non_zero_mask.any():
                        mape = np.mean(np.abs(
                            (gantry_flow[non_zero_mask] - e1_flow[non_zero_mask]) / e1_flow[non_zero_mask])) * 100
                        metrics['flow_mape'] = float(mape)
                        metrics['flow_sample_size'] = int(non_zero_mask.sum())

                    # 相关系数
                    correlation = np.corrcoef(gantry_flow, e1_flow)[0, 1]
                    if not np.isnan(correlation):
                        metrics['flow_correlation'] = float(correlation)

                    # GEH指标（修改为：5分钟聚合，每个门架取85%分位数，然后所有门架85%分位数的均值；通过率基于所有5min GEH <5比例）
                    all_gehs = []  # 新增：收集所有门架的所有5min GEH，用于全局通过率计算
                    geh_per_gantry_85th = {}  # 新增：存储每个门架的85%分位数

                    for gid, group in df.groupby('gantry_id'):
                        # Set time_key as index for resampling
                        group = group.set_index('time_key')

                        # Resample to 5-minute intervals and sum the volumes
                        resampled = group.resample('5T').agg({
                            'gantry_volume': 'sum',
                            'e1_volume': 'sum'
                        }).reset_index()

                        gehs = []

                        # Compute GEH for each 5-minute interval
                        for _, row in resampled.iterrows():
                            g_vol = row['gantry_volume']
                            e_vol = row['e1_volume']
                            geh_val = self._compute_geh(g_vol, e_vol)
                            gehs.append(geh_val)

                        if gehs:
                            # 修改：取85%分位数作为门架值（而非trimmed mean）
                            geh_85th = np.percentile([g for g in gehs if not np.isnan(g)], 85)  # 忽略NaN，只对有效值计算
                            if not np.isnan(geh_85th):
                                geh_per_gantry_85th[gid] = geh_85th
                            # 收集所有有效GEH用于全局通过率
                            valid_gehs = [g for g in gehs if not np.isnan(g)]
                            all_gehs.extend(valid_gehs)

                    # 最终GEH均值：所有门架85%分位数的平均（修改：nanmean of 85th percentiles）
                    if geh_per_gantry_85th:
                        final_geh_mean = np.nanmean(list(geh_per_gantry_85th.values()))
                        metrics['flow_geh_mean'] = float(final_geh_mean)

                    # 通过率：基于所有门架所有5min GEH中 <5 的比例（修改：全局计算，而非门架级别mean <5）
                    if all_gehs:
                        geh_pass_rate = float(sum(geh < 5 for geh in all_gehs) / len(all_gehs) * 100)
                        metrics['flow_geh_pass_rate'] = geh_pass_rate

            # 速度精度指标
            if 'gantry_speed' in df.columns and 'e1_speed' in df.columns:
                gantry_speed = df['gantry_speed'].dropna()
                e1_speed = df['e1_speed'].dropna()

                if len(gantry_speed) > 0 and len(e1_speed) > 0:
                    min_len = min(len(gantry_speed), len(e1_speed))
                    gantry_speed = gantry_speed.iloc[:min_len]
                    e1_speed = e1_speed.iloc[:min_len]

                    # MAE
                    metrics['speed_mae'] = float(np.mean(np.abs(gantry_speed - e1_speed)))
                    # MSE
                    metrics['speed_mse'] = float(np.mean((gantry_speed - e1_speed) ** 2))
                    # RMSE
                    metrics['speed_rmse'] = float(np.sqrt(metrics['speed_mse']))

                    # 相关系数
                    correlation = np.corrcoef(gantry_speed, e1_speed)[0, 1]
                    if not np.isnan(correlation):
                        metrics['speed_correlation'] = float(correlation)

            logger.info(f"计算了 {len(metrics)} 个基础精度指标")
            return metrics

        except Exception as e:
            logger.error(f"计算基础精度指标失败: {e}")
            return {}

    def _calculate_gantry_level_metrics(self, aligned_data: pd.DataFrame) -> pd.DataFrame:
        """计算门架级别精度指标"""
        try:
            if aligned_data.empty or 'gantry_id' not in aligned_data.columns:
                return pd.DataFrame()

            gantry_metrics = []

            for gantry_id in aligned_data['gantry_id'].unique():
                gantry_subset = aligned_data[aligned_data['gantry_id'] == gantry_id]

                if gantry_subset.empty:
                    continue

                metrics = {'gantry_id': gantry_id}

                # 流量精度（切换为 volume）
                if 'gantry_volume' in gantry_subset.columns and 'e1_volume' in gantry_subset.columns:
                    gantry_flow = gantry_subset['gantry_volume'].dropna()
                    e1_flow = gantry_subset['e1_volume'].dropna()

                    if len(gantry_flow) > 0 and len(e1_flow) > 0:
                        min_len = min(len(gantry_flow), len(e1_flow))
                        gantry_flow = gantry_flow.iloc[:min_len]
                        e1_flow = e1_flow.iloc[:min_len]

                        metrics['flow_mae'] = float(np.mean(np.abs(gantry_flow - e1_flow)))
                        metrics['flow_rmse'] = float(np.sqrt(np.mean((gantry_flow - e1_flow) ** 2)))

                        # MAPE
                        non_zero_mask = e1_flow != 0
                        if non_zero_mask.any():
                            mape = np.mean(np.abs((gantry_flow[non_zero_mask] - e1_flow[non_zero_mask]) / e1_flow[non_zero_mask])) * 100
                            metrics['flow_mape'] = float(mape)

                # 速度精度
                if 'gantry_speed' in gantry_subset.columns and 'e1_speed' in gantry_subset.columns:
                    gantry_speed = gantry_subset['gantry_speed'].dropna()
                    e1_speed = gantry_subset['e1_speed'].dropna()

                    if len(gantry_speed) > 0 and len(e1_speed) > 0:
                        min_len = min(len(gantry_speed), len(e1_speed))
                        gantry_speed = gantry_speed.iloc[:min_len]
                        e1_speed = e1_speed.iloc[:min_len]

                        metrics['speed_mae'] = float(np.mean(np.abs(gantry_speed - e1_speed)))
                        metrics['speed_rmse'] = float(np.sqrt(np.mean((gantry_speed - e1_speed) ** 2)))

                gantry_metrics.append(metrics)

            gantry_df = pd.DataFrame(gantry_metrics)
            logger.info(f"计算了 {len(gantry_df)} 个门架的精度指标")
            return gantry_df

        except Exception as e:
            logger.error(f"计算门架级别精度指标失败: {e}")
            return pd.DataFrame()

    def _calculate_time_level_metrics(self, aligned_data: pd.DataFrame) -> pd.DataFrame:
        """计算时间级别精度指标"""
        try:
            if aligned_data.empty or 'time_key' not in aligned_data.columns:
                return pd.DataFrame()

            time_metrics = []

            for time_key in aligned_data['time_key'].unique():
                time_subset = aligned_data[aligned_data['time_key'] == time_key]

                if time_subset.empty:
                    continue

                metrics = {'time_key': time_key}

                # 流量精度（切换为 volume）
                if 'gantry_volume' in time_subset.columns and 'e1_volume' in time_subset.columns:
                    gantry_flow = time_subset['gantry_volume'].dropna()
                    e1_flow = time_subset['e1_volume'].dropna()

                    if len(gantry_flow) > 0 and len(e1_flow) > 0:
                        min_len = min(len(gantry_flow), len(e1_flow))
                        gantry_flow = gantry_flow.iloc[:min_len]
                        e1_flow = e1_flow.iloc[:min_len]

                        metrics['flow_mae'] = float(np.mean(np.abs(gantry_flow - e1_flow)))
                        metrics['flow_rmse'] = float(np.sqrt(np.mean((gantry_flow - e1_flow) ** 2)))
                        metrics['gantry_count'] = len(time_subset)

                time_metrics.append(metrics)

            time_df = pd.DataFrame(time_metrics)
            logger.info(f"计算了 {len(time_df)} 个时间点的精度指标")
            return time_df

        except Exception as e:
            logger.error(f"计算时间级别精度指标失败: {e}")
            return pd.DataFrame()

    def _compute_geh(self, g_vol: float, e_vol: float) -> float:
        """计算单个GEH值（门架体积为observed，E1为simulated）"""
        try:
            denom = g_vol + e_vol
            if denom == 0:
                return 0.0
            return np.sqrt(2 * (g_vol - e_vol)**2 / denom)
        except Exception:
            return np.nan

    def _generate_accuracy_charts(self, aligned_data: pd.DataFrame,
                                basic_metrics: Dict[str, float]) -> List[str]:
        """生成精度分析图表"""
        try:
            if self.charts_dir is None:
                logger.warning("图表目录未设置，跳过图表生成")
                return []

            chart_files = []

            # 1. 车辆数(volume)对比散点图
            if 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                self._ensure_font_for_plot()  # 确保字体设置
                plt.figure(figsize=(10, 8))
                plt.scatter(aligned_data['e1_volume'], aligned_data['gantry_volume'], alpha=0.6)
                plt.plot([0, aligned_data['e1_volume'].max()], [0, aligned_data['gantry_volume'].max()], 'r--', label='理想线')
                plt.xlabel('E1检测器车辆数 (volume)')
                plt.ylabel('门架车辆数 (volume)')
                plt.title('门架车辆数 vs E1检测器车辆数')
                plt.legend()
                plt.grid(True, alpha=0.3)

                chart_file = self.charts_dir / "flow_scatter.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))

            # 2. 速度对比散点图
            if 'gantry_speed' in aligned_data.columns and 'e1_speed' in aligned_data.columns:
                self._ensure_font_for_plot()  # 确保字体设置
                plt.figure(figsize=(10, 8))
                plt.scatter(aligned_data['e1_speed'], aligned_data['gantry_speed'], alpha=0.6)
                plt.plot([0, aligned_data['e1_speed'].max()], [0, aligned_data['e1_speed'].max()], 'r--', label='理想线')
                plt.xlabel('E1检测器速度')
                plt.ylabel('门架速度')
                plt.title('门架速度 vs E1检测器速度')
                plt.legend()
                plt.grid(True, alpha=0.3)

                chart_file = self.charts_dir / "speed_scatter.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))

            # 3. 误差分布直方图（volume）
            if 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                flow_error = aligned_data['gantry_volume'] - aligned_data['e1_volume']
                self._ensure_font_for_plot()  # 确保字体设置
                plt.figure(figsize=(10, 6))
                plt.hist(flow_error.dropna(), bins=30, alpha=0.7, edgecolor='black')
                plt.xlabel('车辆数误差 volume (门架 - E1)')
                plt.ylabel('频次')
                plt.title('车辆数误差分布 (volume)')
                plt.grid(True, alpha=0.3)

                chart_file = self.charts_dir / "flow_error_distribution.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))

            # 4. 精度分布热力图（新增）
            if 'gantry_id' in aligned_data.columns and 'time_key' in aligned_data.columns:
                chart_file = self._generate_accuracy_heatmap(aligned_data)
                if chart_file:
                    chart_files.append(chart_file)

            # 5. 精度等级分类图（使用 volume）
            if 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                chart_file = self._generate_accuracy_classification(aligned_data)
                if chart_file:
                    chart_files.append(chart_file)

            # 6. 误差来源分析图（新增）
            chart_file = self._generate_error_source_analysis(aligned_data)
            if chart_file:
                chart_files.append(chart_file)

            # 7. 数据质量评估图（新增）
            chart_file = self._generate_data_quality_assessment(aligned_data)
            if chart_file:
                chart_files.append(chart_file)

            # 8. E1数据异常诊断图（新增）
            chart_file = self._generate_e1_anomaly_diagnosis(aligned_data)
            if chart_file:
                chart_files.append(chart_file)

            # 新增：9. GEH 24小时热力图（合并自第二个脚本）
            if 'gantry_id' in aligned_data.columns and 'time_key' in aligned_data.columns and 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                chart_file = self._generate_geh_24hour_heatmap(aligned_data)
                if chart_file:
                    chart_files.append(chart_file)

            logger.info(f"生成了 {len(chart_files)} 个图表")
            return chart_files

        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            return []

    def _generate_accuracy_heatmap(self, aligned_data: pd.DataFrame) -> Optional[str]:
        """生成精度分布热力图"""
        try:
            if 'gantry_id' not in aligned_data.columns or 'time_key' not in aligned_data.columns:
                return None

            # 计算每个门架-时间组合的精度
            heatmap_data = []
            for gantry_id in aligned_data['gantry_id'].unique():
                for time_key in aligned_data['time_key'].unique():
                    subset = aligned_data[(aligned_data['gantry_id'] == gantry_id) &
                                       (aligned_data['time_key'] == time_key)]
                    if not subset.empty and 'gantry_volume' in subset.columns and 'e1_volume' in subset.columns:
                        gantry_flow = subset['gantry_volume'].iloc[0]
                        e1_flow = subset['e1_volume'].iloc[0]

                        # 处理E1流量为0的情况
                        if e1_flow == 0:
                            if gantry_flow == 0:
                                mape = 0.0  # 两者都为0，精度完美
                            else:
                                mape = 999.9  # E1为0但门架不为0，标记为异常
                        else:
                            mape = abs((gantry_flow - e1_flow) / e1_flow) * 100

                        heatmap_data.append([gantry_id, time_key, mape])

            if not heatmap_data:
                return None

            # 转换为DataFrame并重塑为热力图格式
            heatmap_df = pd.DataFrame(heatmap_data, columns=['gantry_id', 'time_key', 'mape'])
            heatmap_pivot = heatmap_df.pivot(index='gantry_id', columns='time_key', values='mape')

            # 按自定义门架顺序排序
            heatmap_pivot.index = pd.Categorical(heatmap_pivot.index, categories=self.gantry_order, ordered=True)
            heatmap_pivot = heatmap_pivot.sort_index()

            # 字体已在初始化时设置，无需重复设置

            plt.figure(figsize=(12, 8))

            # 使用自定义颜色映射，处理异常值
            cmap = plt.cm.RdYlBu_r
            norm = plt.Normalize(0, 100)  # 正常MAPE范围0-100%

            # 创建掩码，将异常值(999.9)标记为特殊颜色
            mask = heatmap_pivot == 999.9
            heatmap_pivot_normal = heatmap_pivot.copy()
            heatmap_pivot_normal[mask] = 100  # 临时替换为100，用于正常显示

            sns.heatmap(heatmap_pivot_normal, annot=True, fmt='.1f', cmap=cmap,
                       cbar_kws={'label': 'MAPE (%)'}, norm=norm)

            # 在异常值位置添加特殊标记
            for i in range(len(heatmap_pivot.index)):
                for j in range(len(heatmap_pivot.columns)):
                    if mask.iloc[i, j]:
                        plt.text(j + 0.5, i + 0.5, 'E1=0\n异常',
                                ha='center', va='center', fontsize=8,
                                bbox=dict(boxstyle="round,pad=0.2", facecolor="red", alpha=0.7))

            plt.title('门架-时间精度分布热力图\n(红色标记表示E1检测器流量为0的异常情况)')
            plt.xlabel('时间')
            plt.ylabel('门架ID')
            plt.xticks(rotation=45)
            plt.yticks(rotation=0)

            chart_file = self.charts_dir / "accuracy_heatmap.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()

            return str(chart_file)

        except Exception as e:
            logger.error(f"生成精度热力图失败: {e}")
            return None

    def _generate_accuracy_classification(self, aligned_data: pd.DataFrame) -> Optional[str]:
        """生成精度等级分类图"""
        try:
            if 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                # 计算每个样本的MAPE，处理E1流量为0的情况
                mape_values = []
                e1_zero_count = 0
                gantry_nonzero_e1_zero_count = 0

                for _, row in aligned_data.iterrows():
                    gantry_flow = row['gantry_volume']
                    e1_flow = row['e1_volume']

                    if e1_flow == 0:
                        e1_zero_count += 1
                        if gantry_flow != 0:
                            gantry_nonzero_e1_zero_count += 1
                        # 不将E1=0的情况计入MAPE统计
                    else:
                        mape = abs((gantry_flow - e1_flow) / e1_flow) * 100
                        mape_values.append(mape)

                if not mape_values and e1_zero_count == 0:
                    return None

                # 确保字体设置
                self._ensure_font_for_plot()

                # 创建子图
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

                # 左图：精度等级分布（仅考虑E1流量非0的情况）
                if mape_values:
                    # 按精度等级分类
                    excellent = [x for x in mape_values if x <= 10]  # 优秀: ≤10%
                    good = [x for x in mape_values if 10 < x <= 20]  # 良好: 10-20%
                    fair = [x for x in mape_values if 20 < x <= 30]  # 一般: 20-30%
                    poor = [x for x in mape_values if x > 30]  # 较差: >30%

                    categories = ['优秀\n(≤10%)', '良好\n(10-20%)', '一般\n(20-30%)', '较差\n(>30%)']
                    counts = [len(excellent), len(good), len(fair), len(poor)]
                    colors = ['#2E8B57', '#90EE90', '#FFD700', '#FF6347']

                    bars = ax1.bar(categories, counts, color=colors, alpha=0.8)
                    ax1.set_title('精度等级分布\n(基于E1流量非0的样本)')
                    ax1.set_xlabel('精度等级')
                    ax1.set_ylabel('样本数量')

                    # 在柱状图上添加数值标签
                    for bar, count in zip(bars, counts):
                        height = bar.get_height()
                        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                f'{count}\n({count/len(mape_values)*100:.1f}%)',
                                ha='center', va='bottom')

                    ax1.grid(True, alpha=0.3, axis='y')
                else:
                    ax1.text(0.5, 0.5, '无有效精度数据\n(所有E1流量都为0)',
                            ha='center', va='center', fontsize=14,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.8))
                    ax1.set_title('精度等级分布')
                    ax1.axis('off')

                # 右图：数据质量分布
                quality_categories = ['E1流量=0\n门架流量=0', 'E1流量=0\n门架流量≠0', 'E1流量≠0\n正常计算']
                quality_counts = [e1_zero_count - gantry_nonzero_e1_zero_count,
                                gantry_nonzero_e1_zero_count,
                                len(mape_values)]
                quality_colors = ['#90EE90', '#FF6347', '#4ECDC4']

                bars2 = ax2.bar(quality_categories, quality_counts, color=quality_colors, alpha=0.8)
                ax2.set_title('数据质量分布')
                ax2.set_xlabel('数据质量类型')
                ax2.set_ylabel('样本数量')
                ax2.tick_params(axis='x', rotation=45)

                # 在柱状图上添加数值标签
                for bar, count in zip(bars2, quality_counts):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{count}\n({count/len(aligned_data)*100:.1f}%)',
                            ha='center', va='bottom')

                ax2.grid(True, alpha=0.3, axis='y')

                plt.tight_layout()

                chart_file = self.charts_dir / "accuracy_classification.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()

                return str(chart_file)

            return None  # If columns not present

        except Exception as e:
            logger.error(f"生成精度分类图失败: {e}")
            return None

    def _generate_error_source_analysis(self, aligned_data: pd.DataFrame) -> Optional[str]:
        """生成误差来源分析图"""
        try:
            error_sources = {}

            # 分析流量误差
            if 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                flow_error = aligned_data['gantry_volume'] - aligned_data['e1_volume']
                flow_mae = flow_error.abs().mean()
                flow_rmse = np.sqrt((flow_error ** 2).mean())
                error_sources['流量误差'] = {'MAE': flow_mae, 'RMSE': flow_rmse}

            # 分析速度误差
            if 'gantry_speed' in aligned_data.columns and 'e1_speed' in aligned_data.columns:
                speed_error = aligned_data['gantry_speed'] - aligned_data['e1_speed']
                speed_mae = speed_error.abs().mean()
                speed_rmse = np.sqrt((speed_error ** 2).mean())
                error_sources['速度误差'] = {'MAE': speed_mae, 'RMSE': speed_rmse}

            if not error_sources:
                return None

            # 确保字体设置
            self._ensure_font_for_plot()

            # 创建误差来源对比图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # MAE对比
            sources = list(error_sources.keys())
            mae_values = [error_sources[source]['MAE'] for source in sources]
            ax1.bar(sources, mae_values, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
            ax1.set_title('平均绝对误差 (MAE) 对比')
            ax1.set_ylabel('MAE值')
            ax1.grid(True, alpha=0.3)

            # RMSE对比
            rmse_values = [error_sources[source]['RMSE'] for source in sources]
            ax2.bar(sources, rmse_values, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
            ax2.set_title('均方根误差 (RMSE) 对比')
            ax2.set_ylabel('RMSE值')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            chart_file = self.charts_dir / "error_source_analysis.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()

            return str(chart_file)

        except Exception as e:
            logger.error(f"生成误差来源分析图失败: {e}")
            return None

    def _generate_data_quality_assessment(self, aligned_data: pd.DataFrame) -> Optional[str]:
        """生成数据质量评估图"""
        try:
            quality_metrics = {}

            # 数据完整性评估
            total_records = len(aligned_data)
            complete_records = aligned_data.dropna().shape[0]
            completeness_rate = complete_records / total_records * 100 if total_records > 0 else 0
            quality_metrics['数据完整性'] = completeness_rate

            # 数据一致性评估（门架数量）
            if 'gantry_id' in aligned_data.columns:
                unique_gantries = aligned_data['gantry_id'].nunique()
                quality_metrics['门架覆盖数'] = unique_gantries

            # 数据一致性评估（时间点数量）
            if 'time_key' in aligned_data.columns:
                unique_times = aligned_data['time_key'].nunique()
                quality_metrics['时间覆盖数'] = unique_times

            # 数据范围评估
            if 'gantry_volume' in aligned_data.columns and 'e1_volume' in aligned_data.columns:
                flow_range_gantry = aligned_data['gantry_volume'].max() - aligned_data['gantry_volume'].min()
                flow_range_e1 = aligned_data['e1_volume'].max() - aligned_data['e1_volume'].min()
                quality_metrics['流量范围(门架)'] = flow_range_gantry
                quality_metrics['流量范围(E1)'] = flow_range_e1

            if not quality_metrics:
                return None

            # 确保字体设置
            self._ensure_font_for_plot()

            # 创建数据质量评估图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 数据完整性饼图
            if '数据完整性' in quality_metrics:
                completeness = quality_metrics['数据完整性']
                incomplete = 100 - completeness
                ax1.pie([completeness, incomplete], labels=['完整数据', '缺失数据'],
                       autopct='%1.1f%%', colors=['#2E8B57', '#FF6347'])
                ax1.set_title('数据完整性评估')

            # 门架和时间覆盖数
            if '门架覆盖数' in quality_metrics and '时间覆盖数' in quality_metrics:
                categories = ['门架覆盖', '时间覆盖']
                values = [quality_metrics['门架覆盖数'], quality_metrics['时间覆盖数']]
                ax2.bar(categories, values, color=['#4ECDC4', '#FFD700'], alpha=0.8)
                ax2.set_title('数据覆盖范围')
                ax2.set_ylabel('数量')
                ax2.grid(True, alpha=0.3)

            # 流量范围对比
            if '流量范围(门架)' in quality_metrics and '流量范围(E1)' in quality_metrics:
                sources = ['门架数据', 'E1数据']
                ranges = [quality_metrics['流量范围(门架)'], quality_metrics['流量范围(E1)']]
                ax3.bar(sources, ranges, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
                ax3.set_title('流量数据范围对比')
                ax3.set_ylabel('流量范围')
                ax3.grid(True, alpha=0.3)

            # 数据质量评分
            quality_score = 0
            if '数据完整性' in quality_metrics:
                quality_score += quality_metrics['数据完整性'] * 0.4  # 完整性权重40%
            if '门架覆盖数' in quality_metrics and '时间覆盖数' in quality_metrics:
                coverage_score = min(quality_metrics['门架覆盖数'], quality_metrics['时间覆盖数']) / 50 * 100  # 假设50为满分
                quality_score += coverage_score * 0.6  # 覆盖度权重60%

            ax4.text(0.5, 0.5, f'综合质量评分\n{quality_score:.1f}/100',
                    ha='center', va='center', fontsize=20, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
            ax4.set_title('数据质量综合评分')
            ax4.axis('off')

            plt.tight_layout()

            chart_file = self.charts_dir / "data_quality_assessment.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()

            return str(chart_file)

        except Exception as e:
            logger.error(f"生成数据质量评估图失败: {e}")
            return None

    def _generate_e1_anomaly_diagnosis(self, aligned_data: pd.DataFrame) -> Optional[str]:
        """生成E1数据异常诊断图"""
        try:
            if 'e1_volume' not in aligned_data.columns:
                return None

            # 统计E1流量为0的记录数量
            e1_zero_count = aligned_data['e1_volume'].value_counts().get(0, 0)

            # 如果E1流量为0的记录数量超过总记录的50%，则认为存在异常
            total_records = len(aligned_data)
            if e1_zero_count > total_records * 0.5:
                self._ensure_font_for_plot()  # 确保字体设置
                plt.figure(figsize=(10, 6))
                plt.bar(['E1流量为0的记录数', '总记录数'], [e1_zero_count, total_records])
                plt.ylabel('数量')
                plt.title('E1流量异常诊断')
                plt.grid(True, alpha=0.3)

                chart_file = self.charts_dir / "e1_anomaly_diagnosis.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                return str(chart_file)
            else:
                return None

        except Exception as e:
            logger.error(f"生成E1数据异常诊断图失败: {e}")
            return None

    def _generate_geh_24hour_heatmap(self, aligned_data: pd.DataFrame) -> Optional[str]:
        """生成GEH 24小时热力图（小时聚合，GEH <5 掩码为白） - 合并自独立脚本"""
        try:
            if 'gantry_id' not in aligned_data.columns or 'time_key' not in aligned_data.columns or 'gantry_volume' not in aligned_data.columns or 'e1_volume' not in aligned_data.columns:
                logger.warning("缺少必要列，无法生成 GEH 24小时热力图")
                return None

            # 确保 time_key 是 datetime（fallback 到 gantry_time 如果存在）
            df = aligned_data.copy()
            if 'gantry_time' in df.columns and 'time_key' not in df.columns:
                df['time_key'] = pd.to_datetime(df['gantry_time'], format='%Y-%m-%d %H:%M:%S')
            else:
                df['time_key'] = pd.to_datetime(df['time_key'])

            # Set time_key as index
            df.set_index('time_key', inplace=True)

            # Group by gantry_id
            grouped = df.groupby('gantry_id')

            # Prepare a list to collect hourly GEH for each gantry
            data_list = []

            for gantry_id, group in grouped:
                # Resample to hourly and sum the volumes for each hour
                hourly_volumes = group.resample('H').agg({
                    'gantry_volume': 'sum',
                    'e1_volume': 'sum'
                }).reset_index()

                # Compute GEH for the hourly summed volumes
                hourly_volumes['geh'] = hourly_volumes.apply(
                    lambda row: self._compute_geh(row['gantry_volume'], row['e1_volume']), axis=1
                )

                hourly_volumes['gantry_id'] = gantry_id
                data_list.append(hourly_volumes)

            if not data_list:
                return None

            # Concatenate all
            all_hourly = pd.concat(data_list)

            # Filter for 24 hours (first full day in the data)
            if not all_hourly.empty:
                first_date = all_hourly['time_key'].iloc[0].date()
                # Filter for the first 24 hours of that date
                all_hourly = all_hourly[
                    (all_hourly['time_key'] >= pd.Timestamp(first_date)) &
                    (all_hourly['time_key'] < pd.Timestamp(first_date) + pd.Timedelta(days=1))
                ]

            # Extract hour from timestamp for 24-hour format
            all_hourly['hour'] = all_hourly['time_key'].dt.hour

            # Create pivot table: rows=gantry_id, columns=hour_of_day, values=geh
            pivot_df = all_hourly.pivot_table(
                index='gantry_id',
                columns='hour',
                values='geh',
                aggfunc='mean'  # In case of any duplicates, but summing volumes should yield one per hour
            )

            # Ensure we have all 24 hours (0-23)
            all_hours = list(range(24))
            for hour in all_hours:
                if hour not in pivot_df.columns:
                    pivot_df[hour] = np.nan

            # Reorder columns to have proper 24-hour sequence
            pivot_df = pivot_df.reindex(columns=all_hours)

            # 按自定义门架顺序排序
            pivot_df.index = pd.Categorical(pivot_df.index, categories=self.gantry_order, ordered=True)
            pivot_df = pivot_df.sort_index()

            # Mask values < 5 as NaN (will appear white in heatmap)
            pivot_df[pivot_df < 5] = np.nan

            # 确保字体设置
            self._ensure_font_for_plot()

            # Create the heatmap
            plt.figure(figsize=(16, 10))
            sns.heatmap(
                pivot_df,
                cmap='YlGnBu',
                annot=False,
                fmt=".2f",
                linewidths=.5,
                vmin=5,  # Start coloring from 5
                cbar_kws={'label': 'GEH Value (Hourly Summed Flows, <5 masked as white)'}
            )

            plt.title('24-Hour GEH Heatmap (5-min Flows Summed to Hourly, GEH <5 White)')
            plt.xlabel('Hour of Day')
            plt.ylabel('Gantry ID')

            # Set x-axis ticks to show all 24 hours
            plt.xticks(ticks=np.arange(24) + 0.5, labels=[f'{h:02d}:00' for h in range(24)], rotation=0)
            plt.yticks(rotation=0)

            plt.tight_layout()

            # Save the plot
            chart_file = self.charts_dir / "geh_24hour_heatmap_hourly_summed_masked.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"GEH 24小时热力图已生成: {chart_file}")
            logger.info(f"数据形状: {pivot_df.shape}, 小时: {list(pivot_df.columns)}, 门架: {list(pivot_df.index)}")

            return str(chart_file)

        except Exception as e:
            logger.error(f"生成 GEH 24小时热力图失败: {e}")
            return None

    def _generate_accuracy_report(self, basic_metrics: Dict[str, float],
                                gantry_metrics: pd.DataFrame,
                                time_metrics: pd.DataFrame,
                                chart_files: List[str]) -> str:
        """生成精度分析报告"""
        try:
            if self.reports_dir is None:
                logger.warning("报告目录未设置，跳过报告生成")
                return ""

            # 生成HTML报告
            html_content = self._generate_html_report(basic_metrics, gantry_metrics, time_metrics, chart_files)

            report_file = self.reports_dir / "accuracy_analysis_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"精度分析报告已生成: {report_file}")
            return str(report_file)

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return ""

    def _generate_html_report(self, basic_metrics: Dict[str, float],
                            gantry_metrics: pd.DataFrame,
                            time_metrics: pd.DataFrame,
                            chart_files: List[str]) -> str:
        """生成HTML报告内容"""
        timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>精度分析深度报告</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                
                .header {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    margin-bottom: 30px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    text-align: center;
                }}
                
                .header h1 {{
                    color: #2c3e50;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                
                .header p {{
                    color: #7f8c8d;
                    font-size: 1.1em;
                }}
                
                .section {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    margin: 20px 0;
                    padding: 25px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    border-left: 5px solid #667eea;
                }}
                
                .section h2 {{
                    color: #2c3e50;
                    font-size: 1.8em;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #ecf0f1;
                    position: relative;
                }}
                
                .section h2::after {{
                    content: '';
                    position: absolute;
                    bottom: -2px;
                    left: 0;
                    width: 50px;
                    height: 2px;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                }}
                
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                
                .metric-card {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                
                .metric-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
                }}
                
                .metric-card h3 {{
                    font-size: 1.2em;
                    margin-bottom: 10px;
                    opacity: 0.9;
                }}
                
                .metric-card .value {{
                    font-size: 2em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                
                .metric-card .unit {{
                    font-size: 0.9em;
                    opacity: 0.8;
                }}
                
                .chart-container {{
                    margin: 25px 0;
                    text-align: center;
                }}
                
                .chart-container h3 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                    font-size: 1.4em;
                }}
                
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 15px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                    transition: transform 0.3s ease;
                }}
                
                .chart-container img:hover {{
                    transform: scale(1.02);
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                }}
                
                th, td {{
                    padding: 15px;
                    text-align: left;
                    border-bottom: 1px solid #ecf0f1;
                }}
                
                th {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                
                tr:hover {{
                    background-color: #e3f2fd;
                }}
                
                .summary-stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                
                .stat-item {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    border-left: 4px solid #667eea;
                }}
                
                .stat-item .label {{
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }}
                
                .stat-item .value {{
                    font-size: 1.5em;
                    color: #667eea;
                    font-weight: bold;
                }}
                
                .quality-indicator {{
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: 600;
                    margin: 5px;
                }}
                
                .quality-excellent {{ background: #d4edda; color: #155724; }}
                .quality-good {{ background: #d1ecf1; color: #0c5460; }}
                .quality-fair {{ background: #fff3cd; color: #856404; }}
                .quality-poor {{ background: #f8d7da; color: #721c24; }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding: 20px;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
                
                @media (max-width: 768px) {{
                    .container {{ padding: 10px; }}
                    .header h1 {{ font-size: 2em; }}
                    .metrics-grid {{ grid-template-columns: 1fr; }}
                    .summary-stats {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 精度分析深度报告</h1>
                    <p>基于门架数据与E1检测器数据的精度对比分析</p>
                    <p>生成时间: {timestamp}</p>
                </div>
        """

        # 基础精度指标
        html += """
                <div class="section">
                    <h2>📊 基础精度指标概览</h2>
                    <div class="metrics-grid">
        """

        for metric_name, value in basic_metrics.items():
            if isinstance(value, float):
                # 根据指标类型设置不同的显示格式和单位
                if 'mape' in metric_name.lower():
                    display_value = f"{value:.2f}%"
                    unit = "%"
                    quality_class = self._get_quality_class(value, metric_type='mape')
                elif 'geh' in metric_name.lower():
                    display_value = f"{value:.2f}"
                    unit = ""
                    quality_class = self._get_quality_class(value, metric_type='geh')
                else:
                    display_value = f"{value:.2f}"
                    unit = ""
                    quality_class = ""

                html += f"""
                        <div class="metric-card">
                            <h3>{metric_name}</h3>
                            <div class="value">{display_value}</div>
                            <div class="unit">{unit}</div>
                            {quality_class}
                        </div>
                """
            else:
                html += f"""
                        <div class="metric-card">
                            <h3>{metric_name}</h3>
                            <div class="value">{value}</div>
                            <div class="unit">-</div>
                        </div>
                """

        html += """
                    </div>
                </div>
        """

        # 门架级别指标
        if not gantry_metrics.empty:
            html += """
                <div class="section">
                    <h2>🏗️ 门架级别精度指标</h2>
                    <div class="summary-stats">
            """

            # 添加门架级别的统计信息
            if 'flow_mae' in gantry_metrics.columns:
                avg_mae = gantry_metrics['flow_mae'].mean()
                html += f"""
                        <div class="stat-item">
                            <div class="label">平均MAE</div>
                            <div class="value">{avg_mae:.2f}</div>
                        </div>
                """

            if 'flow_rmse' in gantry_metrics.columns:
                avg_rmse = gantry_metrics['flow_rmse'].mean()
                html += f"""
                        <div class="stat-item">
                            <div class="label">平均RMSE</div>
                            <div class="value">{avg_rmse:.2f}</div>
                        </div>
                """

            html += f"""
                        <div class="stat-item">
                            <div class="label">门架总数</div>
                            <div class="value">{len(gantry_metrics)}</div>
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
            """

            for col in gantry_metrics.columns:
                html += f"<th>{col}</th>"

            html += "</tr></thead><tbody>"

            for _, row in gantry_metrics.iterrows():
                html += "<tr>"
                for col in gantry_metrics.columns:
                    value = row[col]
                    if isinstance(value, float):
                        html += f"<td>{value:.4f}</td>"
                    else:
                        html += f"<td>{value}</td>"
                html += "</tr>"

            html += "</tbody></table></div>"

        # 时间级别指标
        if not time_metrics.empty:
            html += """
                <div class="section">
                    <h2>⏰ 时间级别精度指标</h2>
                    <div class="summary-stats">
            """

            # 添加时间级别的统计信息
            if 'flow_mae' in time_metrics.columns:
                avg_time_mae = time_metrics['flow_mae'].mean()
                html += f"""
                        <div class="stat-item">
                            <div class="label">时间平均MAE</div>
                            <div class="value">{avg_time_mae:.2f}</div>
                        </div>
                """

            html += f"""
                        <div class="stat-item">
                            <div class="label">时间点总数</div>
                            <div class="value">{len(time_metrics)}</div>
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
            """

            for col in time_metrics.columns:
                html += f"<th>{col}</th>"

            html += "</tr></thead><tbody>"

            for _, row in time_metrics.iterrows():
                html += "<tr>"
                for col in time_metrics.columns:
                    value = row[col]
                    if isinstance(value, float):
                        html += f"<td>{value:.4f}</td>"
                    else:
                        html += f"<td>{value}</td>"
                html += "</tr>"

            html += "</tbody></table></div>"

        # 图表
        if chart_files:
            html += """
                <div class="section">
                    <h2>📈 深度分析图表</h2>
                    <p style="color: #7f8c8d; margin-bottom: 20px;">
                        以下图表展示了精度分析的详细结果，包括精度分布、误差分析、数据质量评估等
                    </p>
            """

            for chart_file in chart_files:
                chart_name = Path(chart_file).name
                # 根据文件名生成友好的图表标题
                friendly_name = self._get_friendly_chart_name(chart_name)

                # 修正：使用正确的相对路径
                # 报告文件在 analysis/accuracy/ 目录下
                # 图表文件在 analysis/accuracy/charts/ 目录下
                # 所以从报告引用图表应该使用 charts/文件名
                chart_relative_path = f"charts/{chart_name}"

                html += f"""
                    <div class="chart-container">
                        <h3>{friendly_name}</h3>
                        <img src="{chart_relative_path}" alt="{friendly_name}" loading="lazy">
                    </div>
                """

            html += "</div>"

        html += """
                <div class="footer">
                    <p>本报告由OD数据处理与仿真系统自动生成</p>
                    <p>如需技术支持，请联系系统管理员</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _get_quality_class(self, value: float, metric_type: str) -> str:
        """根据指标值获取质量等级CSS类"""
        if metric_type == 'mape':
            if value <= 10:
                return '<div class="quality-indicator quality-excellent">优秀</div>'
            elif value <= 20:
                return '<div class="quality-indicator quality-good">良好</div>'
            elif value <= 30:
                return '<div class="quality-indicator quality-fair">一般</div>'
            else:
                return '<div class="quality-indicator quality-poor">较差</div>'
        elif metric_type == 'geh':
            if value <= 5:
                return '<div class="quality-indicator quality-excellent">优秀</div>'
            elif value <= 10:
                return '<div class="quality-indicator quality-good">良好</div>'
            elif value <= 15:
                return '<div class="quality-indicator quality-fair">一般</div>'
            else:
                return '<div class="quality-indicator quality-poor">较差</div>'
        return ""

    def _get_friendly_chart_name(self, filename: str) -> str:
        """根据文件名生成友好的图表标题"""
        name_mapping = {
            'flow_scatter.png': '流量对比散点图',
            'speed_scatter.png': '速度对比散点图',
            'flow_error_distribution.png': '流量误差分布图',
            'accuracy_heatmap.png': '精度分布热力图',
            'accuracy_classification.png': '精度等级分类图',
            'error_source_analysis.png': '误差来源分析图',
            'data_quality_assessment.png': '数据质量评估图',
            'e1_anomaly_diagnosis.png': 'E1数据异常诊断图',
            # 新增：GEH 热力图友好名称
            'geh_24hour_heatmap_hourly_summed_masked.png': 'GEH 24小时热力图 (小时聚合，<5 掩码为白)'
        }
        return name_mapping.get(filename, filename.replace('.png', '').replace('_', ' ').title())

    def _export_analysis_csvs(self, aligned_data: pd.DataFrame,
                             basic_metrics: Dict[str, float],
                             gantry_metrics: pd.DataFrame,
                             time_metrics: pd.DataFrame) -> Dict[str, str]:
        """导出分析结果CSV文件"""
        try:
            if self.reports_dir is None:
                logger.warning("报告目录未设置，跳过CSV导出")
                return {}

            csv_files = {}

            # 1. 基础精度指标
            if basic_metrics:
                metrics_df = pd.DataFrame([basic_metrics])
                metrics_file = self.reports_dir / "basic_accuracy_metrics.csv"
                metrics_df.to_csv(metrics_file, index=False, encoding="utf-8-sig")
                csv_files["basic_accuracy_metrics.csv"] = str(metrics_file)

            # 2. 门架级别指标
            if not gantry_metrics.empty:
                gantry_file = self.reports_dir / "gantry_level_metrics.csv"
                gantry_metrics.to_csv(gantry_file, index=False, encoding="utf-8-sig")
                csv_files["gantry_level_metrics.csv"] = str(gantry_file)

            # 3. 时间级别指标
            if not time_metrics.empty:
                time_file = self.reports_dir / "time_level_metrics.csv"
                time_metrics.to_csv(time_file, index=False, encoding="utf-8-sig")
                csv_files["time_level_metrics.csv"] = str(time_file)

            # 4. 对齐数据 - 已由数据对齐阶段生成，此处不再重复生成
            # 使用 aligned_data_for_accuracy.csv 作为统一的对齐数据文件

            logger.info(f"导出了 {len(csv_files)} 个CSV文件")
            return csv_files

        except Exception as e:
            logger.error(f"导出CSV文件失败: {e}")
            return {}