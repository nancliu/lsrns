"""
报告生成模块
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# 导入字体配置
from .font_config import setup_chinese_font, get_font_properties, chinese_font_prop

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_folder: str):
        """
        初始化报告生成器
        
        Args:
            output_folder: 输出文件夹路径
        """
        self.output_folder = output_folder
        self.charts_folder = os.path.join(output_folder, 'charts')
        os.makedirs(self.charts_folder, exist_ok=True)
        
        # 设置图表样式
        self._setup_plot_style()
    
    def _setup_plot_style(self):
        """设置图表样式"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 强制设置中文字体
        from .font_config import force_chinese_font
        self.font_prop = force_chinese_font()
        
        # 设置全局字体配置以确保一致性
        plt.rcParams['font.sans-serif'] = [self.font_prop.get_name()] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 重要：在创建任何图表之前，确保字体设置生效
        plt.rcParams['font.family'] = 'sans-serif'
        
        # 清除字体缓存以确保设置生效
        import matplotlib.font_manager as fm
        try:
            fm._rebuild()
        except AttributeError:
            # 新版本的matplotlib可能没有_rebuild方法
            pass
    
    def _apply_font_to_axes(self, ax):
        """为坐标轴应用字体属性"""
        # 设置刻度标签字体
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        
        # 强制应用字体属性到所有刻度标签
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(self.font_prop)
        
        # 确保标题和轴标签也应用了字体
        if ax.get_title():
            ax.title.set_fontproperties(self.font_prop)
        if ax.get_xlabel():
            ax.xaxis.label.set_fontproperties(self.font_prop)
        if ax.get_ylabel():
            ax.yaxis.label.set_fontproperties(self.font_prop)
    
    def _apply_font_to_colorbar(self, cbar, label_text):
        """为colorbar应用字体属性"""
        cbar.set_label(label_text, fontproperties=self.font_prop)
        cbar.ax.tick_params(labelsize=10)
        for label in cbar.ax.get_yticklabels():
            label.set_fontproperties(self.font_prop)
    
    def _ensure_font_consistency(self, fig):
        """确保整个图表的字体一致性"""
        # 确保在保存前应用字体设置
        plt.rcParams['font.sans-serif'] = [self.font_prop.get_name()] + plt.rcParams['font.sans-serif']
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False
        
        # 清除字体缓存
        import matplotlib.font_manager as fm
        try:
            fm._rebuild()
        except AttributeError:
            # 新版本的matplotlib可能没有_rebuild方法
            pass
        
        # 遍历所有子图应用字体
        if hasattr(fig, 'axes'):
            for ax in fig.axes:
                self._apply_font_to_axes(ax)
    
    def generate_all_reports(self, accuracy_summary: Dict[str, Any], 
                           detailed_results: Dict[str, Any],
                           df_merged: pd.DataFrame) -> Dict[str, str]:
        """
        生成所有类型的报告
        
        Args:
            accuracy_summary: 精度分析摘要
            detailed_results: 详细分析结果
            df_merged: 合并后的数据
            
        Returns:
            生成的报告文件路径字典
        """
        report_files = {}
        
        # 生成CSV报告
        csv_files = self.generate_csv_reports(accuracy_summary, detailed_results, df_merged)
        report_files.update(csv_files)
        
        # 生成图表
        chart_files = self.generate_charts(accuracy_summary, detailed_results, df_merged)
        report_files.update(chart_files)
        
        # 生成HTML报告
        html_file = self.generate_html_report(accuracy_summary, detailed_results, df_merged)
        report_files['html_report'] = html_file
        
        return report_files
    
    def generate_csv_reports(self, accuracy_summary: Dict[str, Any],
                           detailed_results: Dict[str, Any],
                           df_merged: pd.DataFrame) -> Dict[str, str]:
        """
        生成CSV报告
        
        Args:
            accuracy_summary: 精度分析摘要
            detailed_results: 详细分析结果
            df_merged: 合并后的数据
            
        Returns:
            CSV报告文件路径字典
        """
        csv_files = {}
        
        try:
            # 1. 总体精度结果
            overall_results = []
            overall_metrics = accuracy_summary.get('overall_metrics', {})
            
            overall_results.append({
                'metric': 'MAPE',
                'value': overall_metrics.get('mape', np.nan),
                'threshold': 15.0,
                'unit': '%',
                'level': self._get_mape_level(overall_metrics.get('mape', np.nan))
            })
            
            overall_results.append({
                'metric': 'GEH平均值',
                'value': overall_metrics.get('geh_mean', np.nan),
                'threshold': 5.0,
                'unit': '',
                'level': self._get_geh_level(overall_metrics.get('geh_pass_rate', 0))
            })
            
            overall_results.append({
                'metric': 'GEH合格率',
                'value': overall_metrics.get('geh_pass_rate', 0),
                'threshold': 75.0,
                'unit': '%',
                'level': self._get_geh_level(overall_metrics.get('geh_pass_rate', 0))
            })
            
            overall_df = pd.DataFrame(overall_results)
            overall_file = os.path.join(self.output_folder, 'accuracy_results.csv')
            overall_df.to_csv(overall_file, index=False, encoding='utf-8-sig')
            csv_files['overall_results'] = overall_file
            
            # 2. 门架级别精度分析
            if 'gantry_metrics' in detailed_results and not detailed_results['gantry_metrics'].empty:
                gantry_df = detailed_results['gantry_metrics'].copy()
                
                # 添加精度等级
                gantry_df['mape_level'] = gantry_df['mape'].apply(self._get_mape_level)
                gantry_df['geh_level'] = gantry_df['geh_pass_rate'].apply(self._get_geh_level)
                
                gantry_file = os.path.join(self.output_folder, 'gantry_accuracy_analysis.csv')
                gantry_df.to_csv(gantry_file, index=False, encoding='utf-8-sig')
                csv_files['gantry_analysis'] = gantry_file
            
            # 3. 时间间隔精度分析
            if 'time_metrics' in detailed_results and not detailed_results['time_metrics'].empty:
                time_df = detailed_results['time_metrics'].copy()
                
                # 添加时间格式化
                time_df['time_formatted'] = time_df['interval_start'].apply(
                    lambda x: f"{x//60:02d}:{x%60:02d}"
                )
                
                time_file = os.path.join(self.output_folder, 'time_accuracy_analysis.csv')
                time_df.to_csv(time_file, index=False, encoding='utf-8-sig')
                csv_files['time_analysis'] = time_file
            
            # 4. 详细记录数据
            detailed_df = df_merged.copy()
            detailed_df['time_formatted'] = detailed_df['interval_start'].apply(
                lambda x: f"{x//60:02d}:{x%60:02d}"
            )
            
            detailed_file = os.path.join(self.output_folder, 'detailed_records.csv')
            detailed_df.to_csv(detailed_file, index=False, encoding='utf-8-sig')
            csv_files['detailed_records'] = detailed_file
            
            # 5. 异常值分析
            if 'anomaly_analysis' in detailed_results:
                anomaly_stats = detailed_results['anomaly_analysis'].get('statistics', {})
                anomaly_df = pd.DataFrame(list(anomaly_stats.items()), columns=['type', 'count'])
                
                anomaly_file = os.path.join(self.output_folder, 'anomaly_analysis.csv')
                anomaly_df.to_csv(anomaly_file, index=False, encoding='utf-8-sig')
                csv_files['anomaly_analysis'] = anomaly_file
            
        except Exception as e:
            print(f"生成CSV报告时发生错误: {e}")
        
        return csv_files
    
    def generate_charts(self, accuracy_summary: Dict[str, Any],
                       detailed_results: Dict[str, Any],
                       df_merged: pd.DataFrame) -> Dict[str, str]:
        """
        生成图表
        
        Args:
            accuracy_summary: 精度分析摘要
            detailed_results: 详细分析结果
            df_merged: 合并后的数据
            
        Returns:
            图表文件路径字典
        """
        chart_files = {}
        
        try:
            # 1. MAPE分布图
            mape_chart = self._generate_mape_distribution_chart(df_merged)
            if mape_chart:
                chart_files['mape_distribution'] = mape_chart
            
            # 2. GEH分布图
            geh_chart = self._generate_geh_distribution_chart(df_merged)
            if geh_chart:
                chart_files['geh_distribution'] = geh_chart
            
            # 3. 散点图
            scatter_chart = self._generate_scatter_plot(df_merged)
            if scatter_chart:
                chart_files['scatter_plot'] = scatter_chart
            
            # 4. 门架精度对比图
            if 'gantry_metrics' in detailed_results and not detailed_results['gantry_metrics'].empty:
                gantry_chart = self._generate_gantry_comparison_chart(detailed_results['gantry_metrics'])
                if gantry_chart:
                    chart_files['gantry_comparison'] = gantry_chart
            
            # 5. 时间序列图
            if 'time_metrics' in detailed_results and not detailed_results['time_metrics'].empty:
                time_chart = self._generate_time_series_chart(detailed_results['time_metrics'])
                if time_chart:
                    chart_files['time_series'] = time_chart
            
            # 6. 精度指标雷达图
            radar_chart = self._generate_radar_chart(accuracy_summary)
            if radar_chart:
                chart_files['radar_chart'] = radar_chart
            
        except Exception as e:
            print(f"生成图表时发生错误: {e}")
        
        return chart_files
    
    def _generate_mape_distribution_chart(self, df_merged: pd.DataFrame) -> Optional[str]:
        """生成MAPE分布图"""
        try:
            plt.figure(figsize=(12, 8))
            
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. MAPE直方图
            valid_mape = df_merged['mape'].dropna()
            ax1.hist(valid_mape, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.axvline(x=15, color='red', linestyle='--', label='MAPE阈值(15%)')
            ax1.set_xlabel('MAPE (%)', fontproperties=self.font_prop)
            ax1.set_ylabel('频次', fontproperties=self.font_prop)
            ax1.set_title('MAPE分布直方图', fontproperties=self.font_prop)
            ax1.legend(prop=self.font_prop)
            ax1.grid(True, alpha=0.3)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax1)
            
            # 2. MAPE箱线图
            ax2.boxplot(valid_mape, vert=True, patch_artist=True)
            ax2.axhline(y=15, color='red', linestyle='--', label='MAPE阈值(15%)')
            ax2.set_ylabel('MAPE (%)', fontproperties=self.font_prop)
            ax2.set_title('MAPE箱线图', fontproperties=self.font_prop)
            ax2.legend(prop=self.font_prop)
            ax2.grid(True, alpha=0.3)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax2)
            
            # 3. MAPE vs 观测流量散点图
            scatter = ax3.scatter(df_merged['obs_flow'], df_merged['mape'], 
                                alpha=0.6, c=df_merged['mape'], cmap='viridis')
            ax3.axhline(y=15, color='red', linestyle='--', label='MAPE阈值(15%)')
            ax3.set_xlabel('观测流量', fontproperties=self.font_prop)
            ax3.set_ylabel('MAPE (%)', fontproperties=self.font_prop)
            ax3.set_title('MAPE vs 观测流量', fontproperties=self.font_prop)
            ax3.legend(prop=self.font_prop)
            ax3.grid(True, alpha=0.3)
            
            # 添加colorbar并设置字体
            cbar = plt.colorbar(scatter, ax=ax3)
            self._apply_font_to_colorbar(cbar, 'MAPE')
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax3)
            
            # 4. MAPE统计信息
            stats_text = f"""
            MAPE统计信息:
            平均值: {valid_mape.mean():.2f}%
            中位数: {valid_mape.median():.2f}%
            标准差: {valid_mape.std():.2f}%
            最小值: {valid_mape.min():.2f}%
            最大值: {valid_mape.max():.2f}%
            样本数: {len(valid_mape)}
            """
            ax4.text(0.1, 0.5, stats_text, transform=ax4.transAxes, fontsize=12,
                    verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"),
                    fontproperties=self.font_prop)
            ax4.set_title('MAPE统计信息', fontproperties=self.font_prop)
            ax4.axis('off')
            
            plt.tight_layout()
            
            # 确保字体一致性
            self._ensure_font_consistency(fig)
            
            chart_file = os.path.join(self.charts_folder, 'mape_distribution.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"生成MAPE分布图时发生错误: {e}")
            return None
    
    def _generate_geh_distribution_chart(self, df_merged: pd.DataFrame) -> Optional[str]:
        """生成GEH分布图"""
        try:
            plt.figure(figsize=(12, 8))
            
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. GEH直方图
            valid_geh = df_merged['geh'].dropna()
            ax1.hist(valid_geh, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
            ax1.axvline(x=5, color='red', linestyle='--', label='GEH阈值(5)')
            ax1.set_xlabel('GEH', fontproperties=self.font_prop)
            ax1.set_ylabel('频次', fontproperties=self.font_prop)
            ax1.set_title('GEH分布直方图', fontproperties=self.font_prop)
            ax1.legend(prop=self.font_prop)
            ax1.grid(True, alpha=0.3)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax1)
            
            # 2. GEH合格率饼图
            geh_pass = (valid_geh <= 5).sum()
            geh_fail = (valid_geh > 5).sum()
            sizes = [geh_pass, geh_fail]
            labels = [f'合格 ({geh_pass})', f'不合格 ({geh_fail})']
            colors = ['lightgreen', 'lightcoral']
            
            wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.set_title(f'GEH合格率 ({geh_pass/(geh_pass+geh_fail)*100:.1f}%)', fontproperties=self.font_prop)
            
            # 为饼图文本设置字体
            for text in texts + autotexts:
                text.set_fontproperties(self.font_prop)
            
            # 3. GEH vs 观测流量散点图
            scatter = ax3.scatter(df_merged['obs_flow'], df_merged['geh'], 
                                alpha=0.6, c=df_merged['geh'], cmap='plasma')
            ax3.axhline(y=5, color='red', linestyle='--', label='GEH阈值(5)')
            ax3.set_xlabel('观测流量', fontproperties=self.font_prop)
            ax3.set_ylabel('GEH', fontproperties=self.font_prop)
            ax3.set_title('GEH vs 观测流量', fontproperties=self.font_prop)
            ax3.legend(prop=self.font_prop)
            ax3.grid(True, alpha=0.3)
            
            # 添加colorbar并设置字体
            cbar = plt.colorbar(scatter, ax=ax3)
            self._apply_font_to_colorbar(cbar, 'GEH')
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax3)
            
            # 4. GEH统计信息
            stats_text = f"""
            GEH统计信息:
            平均值: {valid_geh.mean():.2f}
            中位数: {valid_geh.median():.2f}
            标准差: {valid_geh.std():.2f}
            最小值: {valid_geh.min():.2f}
            最大值: {valid_geh.max():.2f}
            合格率: {(valid_geh <= 5).mean()*100:.1f}%
            样本数: {len(valid_geh)}
            """
            ax4.text(0.1, 0.5, stats_text, transform=ax4.transAxes, fontsize=12,
                    verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"),
                    fontproperties=self.font_prop)
            ax4.set_title('GEH统计信息', fontproperties=self.font_prop)
            ax4.axis('off')
            
            plt.tight_layout()
            
            # 确保字体一致性
            self._ensure_font_consistency(fig)
            
            chart_file = os.path.join(self.charts_folder, 'geh_distribution.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"生成GEH分布图时发生错误: {e}")
            return None
    
    def _generate_scatter_plot(self, df_merged: pd.DataFrame) -> Optional[str]:
        """生成散点图"""
        try:
            plt.figure(figsize=(12, 10))
            
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 仿真流量 vs 观测流量散点图
            ax1.scatter(df_merged['obs_flow'], df_merged['sim_flow'], alpha=0.6, s=50)
            
            # 添加对角线
            min_val = min(df_merged['obs_flow'].min(), df_merged['sim_flow'].min())
            max_val = max(df_merged['obs_flow'].max(), df_merged['sim_flow'].max())
            ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8, label='理想线')
            
            # 添加拟合线
            z = np.polyfit(df_merged['obs_flow'], df_merged['sim_flow'], 1)
            p = np.poly1d(z)
            ax1.plot(df_merged['obs_flow'], p(df_merged['obs_flow']), "g--", alpha=0.8, label=f'拟合线 (y={z[0]:.2f}x+{z[1]:.2f})')
            
            ax1.set_xlabel('观测流量', fontproperties=self.font_prop)
            ax1.set_ylabel('仿真流量', fontproperties=self.font_prop)
            ax1.set_title('仿真流量 vs 观测流量', fontproperties=self.font_prop)
            ax1.legend(prop=self.font_prop)
            ax1.grid(True, alpha=0.3)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax1)
            
            # 2. 流量比例分布
            ratio = df_merged['sim_flow'] / df_merged['obs_flow']
            ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()
            ax2.hist(ratio, bins=30, alpha=0.7, color='lightblue', edgecolor='black')
            ax2.axvline(x=1, color='red', linestyle='--', label='理想比例(1.0)')
            ax2.set_xlabel('流量比例 (仿真/观测)', fontproperties=self.font_prop)
            ax2.set_ylabel('频次', fontproperties=self.font_prop)
            ax2.set_title('流量比例分布', fontproperties=self.font_prop)
            ax2.legend(prop=self.font_prop)
            ax2.grid(True, alpha=0.3)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax2)
            
            # 3. 残差图
            residuals = df_merged['sim_flow'] - df_merged['obs_flow']
            ax3.scatter(df_merged['obs_flow'], residuals, alpha=0.6, s=50)
            ax3.axhline(y=0, color='red', linestyle='--', label='零残差线')
            ax3.set_xlabel('观测流量', fontproperties=self.font_prop)
            ax3.set_ylabel('残差 (仿真-观测)', fontproperties=self.font_prop)
            ax3.set_title('残差图', fontproperties=self.font_prop)
            ax3.legend(prop=self.font_prop)
            ax3.grid(True, alpha=0.3)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax3)
            
            # 4. 相关性统计
            corr_pearson = df_merged['obs_flow'].corr(df_merged['sim_flow'])
            corr_spearman = df_merged['obs_flow'].corr(df_merged['sim_flow'], method='spearman')
            
            stats_text = f"""
            相关性分析:
            Pearson相关系数: {corr_pearson:.3f}
            Spearman相关系数: {corr_spearman:.3f}
            
            流量统计:
            总仿真流量: {df_merged['sim_flow'].sum():.0f}
            总观测流量: {df_merged['obs_flow'].sum():.0f}
            流量比例: {df_merged['sim_flow'].sum()/df_merged['obs_flow'].sum():.3f}
            """
            ax4.text(0.1, 0.5, stats_text, transform=ax4.transAxes, fontsize=12,
                    verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"),
                    fontproperties=self.font_prop)
            ax4.set_title('相关性统计', fontproperties=self.font_prop)
            ax4.axis('off')
            
            plt.tight_layout()
            
            # 确保字体一致性
            self._ensure_font_consistency(fig)
            
            chart_file = os.path.join(self.charts_folder, 'scatter_plot.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"生成散点图时发生错误: {e}")
            return None
    
    def _generate_gantry_comparison_chart(self, gantry_metrics: pd.DataFrame) -> Optional[str]:
        """生成门架对比图"""
        try:
            plt.figure(figsize=(15, 10))
            
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
            
            # 1. 门架MAPE对比
            gantry_sorted = gantry_metrics.sort_values('mape', ascending=False)
            bars1 = ax1.bar(range(len(gantry_sorted)), gantry_sorted['mape'], color='skyblue')
            ax1.axhline(y=15, color='red', linestyle='--', label='MAPE阈值(15%)')
            ax1.set_xlabel('门架', fontproperties=self.font_prop)
            ax1.set_ylabel('MAPE (%)', fontproperties=self.font_prop)
            ax1.set_title('各门架MAPE对比', fontproperties=self.font_prop)
            ax1.legend(prop=self.font_prop)
            ax1.grid(True, alpha=0.3)
            
            # 设置x轴标签
            ax1.set_xticks(range(len(gantry_sorted)))
            ax1.set_xticklabels(gantry_sorted['gantry_id'], rotation=45, ha='right', fontproperties=self.font_prop)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax1)
            
            # 2. 门架GEH合格率对比
            bars2 = ax2.bar(range(len(gantry_sorted)), gantry_sorted['geh_pass_rate'], color='lightgreen')
            ax2.axhline(y=75, color='red', linestyle='--', label='合格率阈值(75%)')
            ax2.set_xlabel('门架', fontproperties=self.font_prop)
            ax2.set_ylabel('GEH合格率 (%)', fontproperties=self.font_prop)
            ax2.set_title('各门架GEH合格率对比', fontproperties=self.font_prop)
            ax2.legend(prop=self.font_prop)
            ax2.grid(True, alpha=0.3)
            
            # 设置x轴标签
            ax2.set_xticks(range(len(gantry_sorted)))
            ax2.set_xticklabels(gantry_sorted['gantry_id'], rotation=45, ha='right', fontproperties=self.font_prop)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax2)
            
            # 3. 流量对比
            x = np.arange(len(gantry_sorted))
            width = 0.35
            
            bars3 = ax3.bar(x - width/2, gantry_sorted['total_sim_flow'], width, label='仿真流量', alpha=0.8)
            bars4 = ax3.bar(x + width/2, gantry_sorted['total_obs_flow'], width, label='观测流量', alpha=0.8)
            
            ax3.set_xlabel('门架', fontproperties=self.font_prop)
            ax3.set_ylabel('流量', fontproperties=self.font_prop)
            ax3.set_title('各门架流量对比', fontproperties=self.font_prop)
            ax3.legend(prop=self.font_prop)
            ax3.grid(True, alpha=0.3)
            
            # 设置x轴标签
            ax3.set_xticks(x)
            ax3.set_xticklabels(gantry_sorted['gantry_id'], rotation=45, ha='right', fontproperties=self.font_prop)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax3)
            
            # 4. 综合评分
            # 计算综合评分 (MAPE权重40%, GEH合格率权重60%)
            gantry_sorted['composite_score'] = (
                (100 - gantry_sorted['mape']) * 0.4 + gantry_sorted['geh_pass_rate'] * 0.6
            )
            
            bars5 = ax4.bar(range(len(gantry_sorted)), gantry_sorted['composite_score'], color='gold')
            ax4.set_xlabel('门架', fontproperties=self.font_prop)
            ax4.set_ylabel('综合评分', fontproperties=self.font_prop)
            ax4.set_title('各门架综合评分', fontproperties=self.font_prop)
            ax4.grid(True, alpha=0.3)
            
            # 设置x轴标签
            ax4.set_xticks(range(len(gantry_sorted)))
            ax4.set_xticklabels(gantry_sorted['gantry_id'], rotation=45, ha='right', fontproperties=self.font_prop)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax4)
            
            plt.tight_layout()
            
            # 确保字体一致性
            self._ensure_font_consistency(fig)
            
            chart_file = os.path.join(self.charts_folder, 'gantry_comparison.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"生成门架对比图时发生错误: {e}")
            return None
    
    def _generate_time_series_chart(self, time_metrics: pd.DataFrame) -> Optional[str]:
        """生成时间序列图"""
        try:
            plt.figure(figsize=(15, 10))
            
            # 创建子图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
            
            # 格式化时间
            time_metrics['time_formatted'] = time_metrics['interval_start'].apply(
                lambda x: f"{x//60:02d}:{x%60:02d}"
            )
            
            # 1. 流量时间序列
            ax1.plot(time_metrics['time_formatted'], time_metrics['total_sim_flow'], 
                    marker='o', label='仿真流量', linewidth=2, markersize=4)
            ax1.plot(time_metrics['time_formatted'], time_metrics['total_obs_flow'], 
                    marker='s', label='观测流量', linewidth=2, markersize=4)
            ax1.set_xlabel('时间', fontproperties=self.font_prop)
            ax1.set_ylabel('流量', fontproperties=self.font_prop)
            ax1.set_title('流量时间序列', fontproperties=self.font_prop)
            ax1.legend(prop=self.font_prop)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax1)
            
            # 2. MAPE时间序列
            ax2.plot(time_metrics['time_formatted'], time_metrics['mape_mean'], 
                    marker='o', color='red', linewidth=2, markersize=4)
            ax2.axhline(y=15, color='red', linestyle='--', label='MAPE阈值(15%)')
            ax2.set_xlabel('时间', fontproperties=self.font_prop)
            ax2.set_ylabel('MAPE (%)', fontproperties=self.font_prop)
            ax2.set_title('MAPE时间序列', fontproperties=self.font_prop)
            ax2.legend(prop=self.font_prop)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax2)
            
            # 3. GEH时间序列
            ax3.plot(time_metrics['time_formatted'], time_metrics['geh_mean'], 
                    marker='o', color='green', linewidth=2, markersize=4)
            ax3.axhline(y=5, color='red', linestyle='--', label='GEH阈值(5)')
            ax3.set_xlabel('时间', fontproperties=self.font_prop)
            ax3.set_ylabel('GEH', fontproperties=self.font_prop)
            ax3.set_title('GEH时间序列', fontproperties=self.font_prop)
            ax3.legend(prop=self.font_prop)
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax3)
            
            # 4. GEH合格率时间序列
            ax4.plot(time_metrics['time_formatted'], time_metrics['geh_pass_rate'], 
                    marker='o', color='blue', linewidth=2, markersize=4)
            ax4.axhline(y=75, color='red', linestyle='--', label='合格率阈值(75%)')
            ax4.set_xlabel('时间', fontproperties=self.font_prop)
            ax4.set_ylabel('GEH合格率 (%)', fontproperties=self.font_prop)
            ax4.set_title('GEH合格率时间序列', fontproperties=self.font_prop)
            ax4.legend(prop=self.font_prop)
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
            
            # 为坐标轴应用字体
            self._apply_font_to_axes(ax4)
            
            plt.tight_layout()
            
            # 确保字体一致性
            self._ensure_font_consistency(fig)
            
            chart_file = os.path.join(self.charts_folder, 'time_series.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"生成时间序列图时发生错误: {e}")
            return None
    
    def _generate_radar_chart(self, accuracy_summary: Dict[str, Any]) -> Optional[str]:
        """生成雷达图"""
        try:
            from matplotlib.patches import Polygon
            
            overall_metrics = accuracy_summary.get('overall_metrics', {})
            
            if not overall_metrics:
                return None
            
            # 准备雷达图数据
            categories = ['MAPE评分', 'GEH评分', '数据完整性', '样本量评分', '稳定性评分']
            
            # 计算各项评分 (0-100分)
            mape_score = max(0, 100 - overall_metrics.get('mape', 100))
            geh_score = overall_metrics.get('geh_pass_rate', 0)
            completeness_score = 100  # 假设数据完整性为100%
            sample_score = min(100, overall_metrics.get('sample_size', 0) / 10)  # 每10个样本得1分，最高100分
            stability_score = 100 - overall_metrics.get('mape', 100) * 2  # 基于MAPE的稳定性评分
            
            values = [mape_score, geh_score, completeness_score, sample_score, stability_score]
            
            # 计算角度
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]  # 闭合图形
            angles += angles[:1]  # 闭合图形
            
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            # 绘制雷达图
            ax.plot(angles, values, 'o-', linewidth=2, label='精度评分', color='blue')
            ax.fill(angles, values, alpha=0.25, color='blue')
            
            # 设置标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontproperties=self.font_prop)
            ax.set_ylim(0, 100)
            
            # 添加网格
            ax.grid(True)
            
            # 添加标题
            ax.set_title('仿真精度综合评分', size=20, color='black', y=1.1, fontproperties=self.font_prop)
            
            # 添加数值标签
            for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
                ax.text(angle, value + 5, f'{value:.1f}', ha='center', va='center', fontproperties=self.font_prop)
            
            # 为雷达图刻度标签设置字体
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(self.font_prop)
            
            # 确保字体一致性
            self._ensure_font_consistency(fig)
            
            chart_file = os.path.join(self.charts_folder, 'radar_chart.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"生成雷达图时发生错误: {e}")
            return None
    
    def generate_html_report(self, accuracy_summary: Dict[str, Any],
                           detailed_results: Dict[str, Any],
                           df_merged: pd.DataFrame) -> str:
        """
        生成HTML报告
        
        Args:
            accuracy_summary: 精度分析摘要
            detailed_results: 详细分析结果
            df_merged: 合并后的数据
            
        Returns:
            HTML报告文件路径
        """
        try:
            html_content = self._generate_html_content(accuracy_summary, detailed_results, df_merged)
            
            html_file = os.path.join(self.output_folder, 'accuracy_report.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return html_file
            
        except Exception as e:
            print(f"生成HTML报告时发生错误: {e}")
            return ""
    
    def _generate_html_content(self, accuracy_summary: Dict[str, Any],
                             detailed_results: Dict[str, Any],
                             df_merged: pd.DataFrame) -> str:
        """生成HTML内容"""
        overall_metrics = accuracy_summary.get('overall_metrics', {})
        data_stats = accuracy_summary.get('data_statistics', {})
        # 阈值说明文本
        mape_level = self._get_mape_level(overall_metrics.get('mape', 0))
        geh_level = self._get_geh_level(overall_metrics.get('geh_pass_rate', 0))
        
        # 生成图表引用
        chart_refs = []
        chart_files = [
            ('mape_distribution.png', 'MAPE分布分析'),
            ('geh_distribution.png', 'GEH分布分析'),
            ('scatter_plot.png', '流量相关性分析'),
            ('gantry_comparison.png', '门架精度对比'),
            ('time_series.png', '时间序列分析'),
            ('radar_chart.png', '综合评分雷达图')
        ]
        
        for chart_file, chart_title in chart_files:
            chart_path = os.path.join('charts', chart_file)
            if os.path.exists(os.path.join(self.charts_folder, chart_file)):
                chart_refs.append(f'''
                <div class="chart-container">
                    <h3>{chart_title}</h3>
                    <img src="{chart_path}" alt="{chart_title}" style="max-width: 100%; height: auto;">
                </div>
                ''')
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>仿真精度分析报告</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .metric-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .chart-container img {{
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .data-table th, .data-table td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                .data-table th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                }}
                .data-table tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .status-good {{ color: #27ae60; }}
                .status-warning {{ color: #f39c12; }}
                .status-bad {{ color: #e74c3c; }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>仿真精度分析报告</h1>
                
                <h2>分析概览</h2>
                <div class="summary-grid">
                    <div class="metric-card">
                        <div class="metric-label">MAPE</div>
                        <div class="metric-value">{overall_metrics.get('mape', 0):.2f}%</div>
                        <div class="metric-label">等级：{mape_level}（目标≤15%）</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">GEH平均值</div>
                        <div class="metric-value">{overall_metrics.get('geh_mean', 0):.2f}</div>
                        <div class="metric-label">目标: ≤5</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">GEH合格率</div>
                        <div class="metric-value">{overall_metrics.get('geh_pass_rate', 0):.1f}%</div>
                        <div class="metric-label">等级：{geh_level}（阈值≤5，合格率≥75%）</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">样本数量</div>
                        <div class="metric-value">{overall_metrics.get('sample_size', 0)}</div>
                        <div class="metric-label">有效记录</div>
                    </div>
                </div>
                
                <h2>数据统计</h2>
                <table class="data-table">
                    <tr>
                        <th>统计项目</th>
                        <th>数值</th>
                    </tr>
                    <tr>
                        <td>总记录数</td>
                        <td>{data_stats.get('total_records', 0)}</td>
                    </tr>
                    <tr>
                        <td>门架数量</td>
                        <td>{data_stats.get('unique_gantry_ids', 0)}</td>
                    </tr>
                    <tr>
                        <td>时间间隔数</td>
                        <td>{data_stats.get('unique_time_intervals', 0)}</td>
                    </tr>
                    <tr>
                        <td>总仿真流量</td>
                        <td>{data_stats.get('total_sim_flow', 0):.0f}</td>
                    </tr>
                    <tr>
                        <td>总观测流量</td>
                        <td>{data_stats.get('total_obs_flow', 0):.0f}</td>
                    </tr>
                    <tr>
                        <td>流量比例</td>
                        <td>{data_stats.get('total_sim_flow', 0) / max(data_stats.get('total_obs_flow', 1), 1):.3f}</td>
                    </tr>
                </table>
                
                <h2>分析图表</h2>
                {''.join(chart_refs)}
                
                <div class="footer">
                    <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>精度分析工具 v1.0</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_mape_level(self, mape: float) -> str:
        """获取MAPE等级"""
        if pd.isna(mape):
            return "无法计算"
        elif mape <= 10:
            return "优秀"
        elif mape <= 15:
            return "良好"
        elif mape <= 20:
            return "一般"
        elif mape <= 30:
            return "较差"
        else:
            return "很差"
    
    def _get_geh_level(self, geh_pass_rate: float) -> str:
        """获取GEH等级"""
        if geh_pass_rate >= 85:
            return "优秀"
        elif geh_pass_rate >= 75:
            return "良好"
        elif geh_pass_rate >= 60:
            return "一般"
        elif geh_pass_rate >= 40:
            return "较差"
        else:
            return "很差"