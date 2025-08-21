"""
机理分析模块
专门处理交通流机理分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import matplotlib.font_manager as fm
from matplotlib import rcParams

logger = logging.getLogger(__name__)


class MechanismAnalysis:
    """机理分析类"""
    
    def __init__(self):
        self.analysis_results = {}
        self.charts_dir = None
        self.reports_dir = None
        self._ensure_chinese_font()
        
    def _ensure_chinese_font(self) -> None:
        """设置支持中文的字体"""
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
                fm.findfont(name, fallback_to_default=False)
                picked = name
                break
            except Exception:
                continue
        if not picked:
            picked = "Microsoft YaHei"
        try:
            rcParams["font.sans-serif"] = [picked, "DejaVu Sans", "Arial Unicode MS"]
            rcParams["axes.unicode_minus"] = False
        except Exception:
            pass
        
    def set_output_dirs(self, charts_dir: str, reports_dir: str):
        """设置输出目录"""
        self.charts_dir = Path(charts_dir)
        self.reports_dir = Path(reports_dir)
        
        # 创建目录
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"设置输出目录: 图表={charts_dir}, 报告={reports_dir}")
    
    def analyze_mechanism(self, simulation_data: pd.DataFrame) -> Dict[str, Any]:
        """
        执行机理分析
        
        Args:
            simulation_data: 仿真数据
            
        Returns:
            分析结果字典
        """
        try:
            logger.info("开始机理分析...")
            
            if simulation_data.empty:
                raise Exception("仿真数据为空，无法进行机理分析")
            
            # 1. 流量-密度关系分析
            flow_density_analysis = self._analyze_flow_density_relationship(simulation_data)
            
            # 2. 速度-流量关系分析
            speed_flow_analysis = self._analyze_speed_flow_relationship(simulation_data)
            
            # 3. 交通流状态分析
            traffic_state_analysis = self._analyze_traffic_state(simulation_data)
            
            # 4. 流量残差时间序列分析
            residual_analysis = self._analyze_flow_residual_timeseries(simulation_data)
            
            # 5. 生成机理分析图表
            chart_files = self._generate_mechanism_charts(simulation_data, flow_density_analysis, speed_flow_analysis, traffic_state_analysis, residual_analysis)
            
            # 6. 生成分析报告
            report_file = self._generate_mechanism_report(flow_density_analysis, speed_flow_analysis, traffic_state_analysis, residual_analysis, chart_files)
            
            # 7. 导出分析结果CSV
            csv_files = self._export_analysis_csvs(simulation_data, flow_density_analysis, speed_flow_analysis, traffic_state_analysis, residual_analysis)
            
            results = {
                "flow_density_analysis": flow_density_analysis,
                "speed_flow_analysis": speed_flow_analysis,
                "traffic_state_analysis": traffic_state_analysis,
                "residual_analysis": residual_analysis,
                "chart_files": chart_files,
                "report_file": report_file,
                "csv_files": csv_files,
                "analysis_time": pd.Timestamp.now().isoformat()
            }
            
            self.analysis_results = results
            logger.info("机理分析完成")
            return results
            
        except Exception as e:
            logger.error(f"机理分析失败: {e}")
            return {}
    
    def _analyze_flow_density_relationship(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析流量-密度关系"""
        try:
            analysis = {}
            
            # 检查必要列
            if 'flow' not in data.columns or 'density' not in data.columns:
                logger.warning("缺少流量或密度列，跳过流量-密度关系分析")
                return analysis
            
            # 过滤有效数据
            valid_data = data.dropna(subset=['flow', 'density'])
            if valid_data.empty:
                return analysis
            
            # 基本统计
            analysis['total_points'] = len(valid_data)
            analysis['flow_range'] = [float(valid_data['flow'].min()), float(valid_data['flow'].max())]
            analysis['density_range'] = [float(valid_data['density'].min()), float(valid_data['density'].max())]
            
            # 相关性分析
            correlation = valid_data['flow'].corr(valid_data['density'])
            if not pd.isna(correlation):
                analysis['flow_density_correlation'] = float(correlation)
            
            # 拟合二次函数 (流量 = a * 密度^2 + b * 密度 + c)
            try:
                z = np.polyfit(valid_data['density'], valid_data['flow'], 2)
                p = np.poly1d(z)
                analysis['quadratic_fit'] = {
                    'a': float(z[0]),
                    'b': float(z[1]),
                    'c': float(z[2]),
                    'equation': f"flow = {z[0]:.4f}*density² + {z[1]:.4f}*density + {z[2]:.4f}"
                }
                
                # 计算R²
                y_pred = p(valid_data['density'])
                ss_res = np.sum((valid_data['flow'] - y_pred) ** 2)
                ss_tot = np.sum((valid_data['flow'] - valid_data['flow'].mean()) ** 2)
                r_squared = 1 - (ss_res / ss_tot)
                analysis['r_squared'] = float(r_squared)
                
            except Exception as e:
                logger.warning(f"二次函数拟合失败: {e}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"流量-密度关系分析失败: {e}")
            return {}
    
    def _analyze_speed_flow_relationship(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析速度-流量关系"""
        try:
            analysis = {}
            
            # 检查必要列
            if 'speed' not in data.columns or 'flow' not in data.columns:
                logger.warning("缺少速度或流量列，跳过速度-流量关系分析")
                return analysis
            
            # 过滤有效数据
            valid_data = data.dropna(subset=['speed', 'flow'])
            if valid_data.empty:
                return analysis
            
            # 基本统计
            analysis['total_points'] = len(valid_data)
            analysis['speed_range'] = [float(valid_data['speed'].min()), float(valid_data['speed'].max())]
            analysis['flow_range'] = [float(valid_data['flow'].min()), float(valid_data['flow'].max())]
            
            # 相关性分析
            correlation = valid_data['speed'].corr(valid_data['flow'])
            if not pd.isna(correlation):
                analysis['speed_flow_correlation'] = float(correlation)
            
            # 速度-流量关系类型判断
            if correlation < -0.5:
                analysis['relationship_type'] = "强负相关（拥堵时速度下降，流量减少）"
            elif correlation > 0.5:
                analysis['relationship_type'] = "强正相关（自由流时速度增加，流量增加）"
            else:
                analysis['relationship_type'] = "弱相关或无明确关系"
            
            return analysis
            
        except Exception as e:
            logger.error(f"速度-流量关系分析失败: {e}")
            return {}
    
    def _analyze_traffic_state(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析交通流状态"""
        try:
            analysis = {}
            
            # 检查必要列
            if 'flow' not in data.columns or 'speed' not in data.columns:
                logger.warning("缺少流量或速度列，跳过交通流状态分析")
                return analysis
            
            # 过滤有效数据
            valid_data = data.dropna(subset=['flow', 'speed'])
            if valid_data.empty:
                return analysis
            
            # 计算交通流状态指标
            total_points = len(valid_data)
            
            # 自由流状态（高速度，中等流量）
            free_flow_mask = (valid_data['speed'] > valid_data['speed'].quantile(0.7)) & \
                           (valid_data['flow'] < valid_data['flow'].quantile(0.8))
            free_flow_count = free_flow_mask.sum()
            analysis['free_flow'] = {
                'count': int(free_flow_count),
                'percentage': float(free_flow_count / total_points * 100)
            }
            
            # 稳定流状态（中等速度，高流量）
            stable_flow_mask = (valid_data['speed'] > valid_data['speed'].quantile(0.3)) & \
                             (valid_data['speed'] <= valid_data['speed'].quantile(0.7)) & \
                             (valid_data['flow'] > valid_data['flow'].quantile(0.6))
            stable_flow_count = stable_flow_mask.sum()
            analysis['stable_flow'] = {
                'count': int(stable_flow_count),
                'percentage': float(stable_flow_count / total_points * 100)
            }
            
            # 不稳定流状态（低速度，中等流量）
            unstable_flow_mask = (valid_data['speed'] <= valid_data['speed'].quantile(0.3)) & \
                               (valid_data['flow'] > valid_data['flow'].quantile(0.4))
            unstable_flow_count = unstable_flow_mask.sum()
            analysis['unstable_flow'] = {
                'count': int(unstable_flow_count),
                'percentage': float(unstable_flow_count / total_points * 100)
            }
            
            # 拥堵状态（低速度，低流量）
            congestion_mask = (valid_data['speed'] <= valid_data['speed'].quantile(0.3)) & \
                            (valid_data['flow'] <= valid_data['flow'].quantile(0.4))
            congestion_count = congestion_mask.sum()
            analysis['congestion'] = {
                'count': int(congestion_count),
                'percentage': float(congestion_count / total_points * 100)
            }
            
            # 主要交通流状态
            states = [
                ('free_flow', analysis['free_flow']['percentage']),
                ('stable_flow', analysis['stable_flow']['percentage']),
                ('unstable_flow', analysis['unstable_flow']['percentage']),
                ('congestion', analysis['congestion']['percentage'])
            ]
            main_state = max(states, key=lambda x: x[1])
            analysis['main_traffic_state'] = main_state[0]
            analysis['main_state_percentage'] = main_state[1]
            
            return analysis
            
        except Exception as e:
            logger.error(f"交通流状态分析失败: {e}")
            return {}
    
    def _analyze_flow_residual_timeseries(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析流量残差时间序列"""
        try:
            analysis = {}
            
            # 检查必要列
            if 'flow' not in data.columns:
                logger.warning("缺少流量列，跳过流量残差时间序列分析")
                return analysis
            
            # 过滤有效数据
            valid_data = data.dropna(subset=['flow'])
            if valid_data.empty:
                return analysis
            
            # 基本统计
            analysis['total_points'] = len(valid_data)
            
            # 计算流量残差（相对于均值）
            flow_mean = valid_data['flow'].mean()
            residuals = valid_data['flow'] - flow_mean
            
            analysis['residual_range'] = [float(residuals.min()), float(residuals.max())]
            analysis['residual_mean'] = float(residuals.mean())
            analysis['residual_std'] = float(residuals.std())
            
            # 生成残差时间序列图
            if self.charts_dir:
                plt.figure(figsize=(12, 6))
                
                # 如果有时间列，使用时间作为x轴
                if 'time_key' in valid_data.columns:
                    x_data = valid_data['time_key']
                    x_label = '时间'
                elif 'start_time' in valid_data.columns:
                    x_data = valid_data['start_time']
                    x_label = '时间'
                else:
                    x_data = range(len(valid_data))
                    x_label = '数据点序号'
                
                plt.plot(x_data, residuals, 'b-', linewidth=1.5, alpha=0.8, label='流量残差')
                plt.axhline(y=0, color='r', linestyle='--', linewidth=2, label='残差均值线')
                
                # 添加置信区间
                std = residuals.std()
                plt.fill_between(x_data, -2*std, 2*std, alpha=0.2, color='gray', label='±2σ置信区间')
                
                plt.xlabel(x_label, fontsize=12)
                plt.ylabel('流量残差 (veh/h)', fontsize=12)
                plt.title('流量残差时间序列分析', fontsize=14, fontweight='bold')
                plt.grid(True, alpha=0.3)
                plt.legend(fontsize=10)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "flow_residual_timeseries.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                
                analysis['residual_timeseries_chart'] = str(chart_file)
                
                logger.info(f"流量残差时间序列图已生成: {chart_file}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"流量残差时间序列分析失败: {e}")
            return {}
    
    def _generate_mechanism_charts(self, data: pd.DataFrame, 
                                 flow_density_analysis: Dict[str, Any], 
                                 speed_flow_analysis: Dict[str, Any], 
                                 traffic_state_analysis: Dict[str, Any], 
                                 residual_analysis: Dict[str, Any]) -> List[str]:
        """生成机理分析图表"""
        try:
            if self.charts_dir is None:
                logger.warning("图表目录未设置，跳过图表生成")
                return []
            
            chart_files = []
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 1. 流量-密度散点图
            if 'flow' in data.columns and 'density' in data.columns:
                plt.figure(figsize=(12, 8))
                plt.scatter(data['density'], data['flow'], alpha=0.6, s=50, c='blue', edgecolors='black', linewidth=0.5)
                
                # 添加拟合曲线
                if 'quadratic_fit' in flow_density_analysis:
                    fit = flow_density_analysis['quadratic_fit']
                    density_range = np.linspace(data['density'].min(), data['density'].max(), 100)
                    flow_fit = fit['a'] * density_range**2 + fit['b'] * density_range + fit['c']
                    plt.plot(density_range, flow_fit, 'r-', linewidth=2, 
                           label=f"二次拟合曲线 (R²={flow_density_analysis.get('r_squared', 0):.3f})")
                    plt.legend(fontsize=12)
                
                plt.xlabel('密度 (veh/km)', fontsize=14)
                plt.ylabel('流量 (veh/h)', fontsize=14)
                plt.title('流量-密度关系分析', fontsize=16, fontweight='bold')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "flow_density_relationship.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 2. 速度-流量散点图
            if 'speed' in data.columns and 'flow' in data.columns:
                plt.figure(figsize=(12, 8))
                plt.scatter(data['flow'], data['speed'], alpha=0.6, s=50, c='green', edgecolors='black', linewidth=0.5)
                plt.xlabel('流量 (veh/h)', fontsize=14)
                plt.ylabel('速度 (km/h)', fontsize=14)
                plt.title('速度-流量关系分析', fontsize=16, fontweight='bold')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "speed_flow_relationship.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 3. 交通流状态分布饼图
            if traffic_state_analysis and 'free_flow' in traffic_state_analysis:
                plt.figure(figsize=(12, 8))
                states = ['自由流', '稳定流', '不稳定流', '拥堵']
                percentages = [
                    traffic_state_analysis['free_flow']['percentage'],
                    traffic_state_analysis['stable_flow']['percentage'],
                    traffic_state_analysis['unstable_flow']['percentage'],
                    traffic_state_analysis['congestion']['percentage']
                ]
                
                # 设置颜色
                colors = ['#2E8B57', '#4169E1', '#FF8C00', '#DC143C']
                
                # 创建饼图
                wedges, texts, autotexts = plt.pie(percentages, labels=states, autopct='%1.1f%%', 
                                                  startangle=90, colors=colors, explode=(0.05, 0.05, 0.05, 0.05))
                
                # 设置文本样式
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                plt.title('交通流状态分布', fontsize=16, fontweight='bold')
                plt.axis('equal')
                plt.tight_layout()
                
                chart_file = self.charts_dir / "traffic_state_distribution.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 4. 流量残差时间序列图
            if residual_analysis and 'residual_timeseries_chart' in residual_analysis:
                residual_chart_file = residual_analysis['residual_timeseries_chart']
                if residual_chart_file:
                    chart_files.append(residual_chart_file)
            
            # 5. 流量-速度-密度三维散点图（如果数据完整）
            if all(col in data.columns for col in ['flow', 'speed', 'density']):
                fig = plt.figure(figsize=(14, 10))
                ax = fig.add_subplot(111, projection='3d')
                
                scatter = ax.scatter(data['density'], data['flow'], data['speed'], 
                                   c=data['flow'], cmap='viridis', alpha=0.7, s=30)
                
                ax.set_xlabel('密度 (veh/km)', fontsize=12)
                ax.set_ylabel('流量 (veh/h)', fontsize=12)
                ax.set_zlabel('速度 (km/h)', fontsize=12)
                ax.set_title('流量-速度-密度三维关系', fontsize=14, fontweight='bold')
                
                # 添加颜色条
                cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, aspect=20)
                cbar.set_label('流量 (veh/h)', fontsize=12)
                
                plt.tight_layout()
                
                chart_file = self.charts_dir / "flow_speed_density_3d.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 6. 交通流状态时间序列图
            if 'speed' in data.columns and 'flow' in data.columns and 'time_key' in data.columns:
                plt.figure(figsize=(14, 10))
                
                # 创建子图
                fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
                
                # 流量时间序列
                ax1.plot(data['time_key'], data['flow'], 'b-', linewidth=1.5, alpha=0.8)
                ax1.set_ylabel('流量 (veh/h)', fontsize=12)
                ax1.set_title('流量时间序列', fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3)
                
                # 速度时间序列
                ax2.plot(data['time_key'], data['speed'], 'g-', linewidth=1.5, alpha=0.8)
                ax2.set_ylabel('速度 (km/h)', fontsize=12)
                ax2.set_title('速度时间序列', fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3)
                
                # 密度时间序列（如果存在）
                if 'density' in data.columns:
                    ax3.plot(data['time_key'], data['density'], 'r-', linewidth=1.5, alpha=0.8)
                    ax3.set_ylabel('密度 (veh/km)', fontsize=12)
                    ax3.set_title('密度时间序列', fontsize=14, fontweight='bold')
                    ax3.grid(True, alpha=0.3)
                
                ax3.set_xlabel('时间', fontsize=12)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "traffic_parameters_timeseries.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            logger.info(f"生成了 {len(chart_files)} 个机理分析图表")
            return chart_files
            
        except Exception as e:
            logger.error(f"生成机理分析图表失败: {e}")
            return []
    
    def _generate_mechanism_report(self, flow_density_analysis: Dict[str, Any], 
                                 speed_flow_analysis: Dict[str, Any], 
                                 traffic_state_analysis: Dict[str, Any], 
                                 residual_analysis: Dict[str, Any], 
                                 chart_files: List[str]) -> str:
        """生成机理分析报告"""
        try:
            if self.reports_dir is None:
                logger.warning("报告目录未设置，跳过报告生成")
                return ""
            
            # 生成HTML报告
            html_content = self._generate_html_report(flow_density_analysis, speed_flow_analysis, traffic_state_analysis, residual_analysis, chart_files)
            
            report_file = self.reports_dir / "mechanism_analysis_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"机理分析报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return ""
    
    def _generate_html_report(self, flow_density_analysis: Dict[str, Any], 
                            speed_flow_analysis: Dict[str, Any], 
                            traffic_state_analysis: Dict[str, Any], 
                            residual_analysis: Dict[str, Any],
                            chart_files: List[str]) -> str:
        """生成HTML报告内容"""
        timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>交通流机理分析报告</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Microsoft YaHei', 'SimHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    min-height: 100vh; 
                }}
                .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
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
                    margin-bottom: 15px; 
                    font-size: 2.5em; 
                    font-weight: 700; 
                }}
                .header p {{ 
                    color: #7f8c8d; 
                    font-size: 1.1em; 
                    margin-bottom: 10px; 
                }}
                .section {{ 
                    background: rgba(255, 255, 255, 0.95); 
                    backdrop-filter: blur(10px); 
                    border-radius: 15px; 
                    padding: 25px; 
                    margin-bottom: 25px; 
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); 
                }}
                .section h2 {{ 
                    color: #2c3e50; 
                    margin-bottom: 20px; 
                    font-size: 1.8em; 
                    font-weight: 600; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 10px; 
                }}
                .metrics-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 20px; 
                    margin-bottom: 25px; 
                }}
                .metric-card {{ 
                    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
                    color: white; 
                    padding: 20px; 
                    border-radius: 12px; 
                    text-align: center; 
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                    transition: transform 0.3s ease; 
                }}
                .metric-card:hover {{ transform: translateY(-5px); }}
                .metric-card h3 {{ 
                    font-size: 1.2em; 
                    margin-bottom: 10px; 
                    font-weight: 600; 
                }}
                .metric-card .value {{ 
                    font-size: 2em; 
                    font-weight: 700; 
                    margin-bottom: 5px; 
                }}
                .metric-card .unit {{ 
                    font-size: 0.9em; 
                    opacity: 0.9; 
                }}
                .chart-container {{ 
                    margin: 25px 0; 
                    text-align: center; 
                }}
                .chart-container h3 {{ 
                    color: #2c3e50; 
                    margin-bottom: 15px; 
                    font-size: 1.4em; 
                    font-weight: 600; 
                }}
                .chart-container img {{ 
                    max-width: 100%; 
                    height: auto; 
                    border-radius: 10px; 
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); 
                }}
                .analysis-summary {{ 
                    background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 15px; 
                    margin: 25px 0; 
                }}
                .analysis-summary h3 {{ 
                    margin-bottom: 15px; 
                    font-size: 1.5em; 
                    font-weight: 600; 
                }}
                .analysis-summary ul {{ 
                    list-style: none; 
                    padding-left: 0; 
                }}
                .analysis-summary li {{ 
                    margin-bottom: 8px; 
                    padding-left: 20px; 
                    position: relative; 
                }}
                .analysis-summary li:before {{ 
                    content: "•"; 
                    position: absolute; 
                    left: 0; 
                    font-weight: bold; 
                }}
                .footer {{ 
                    text-align: center; 
                    margin-top: 40px; 
                    padding: 20px; 
                    color: #7f8c8d; 
                    font-size: 0.9em; 
                }}
                .status-indicator {{ 
                    display: inline-block; 
                    width: 12px; 
                    height: 12px; 
                    border-radius: 50%; 
                    margin-right: 8px; 
                }}
                .status-good {{ background-color: #27ae60; }}
                .status-warning {{ background-color: #f39c12; }}
                .status-poor {{ background-color: #e74c3c; }}
                @media (max-width: 768px) {{
                    .metrics-grid {{ grid-template-columns: 1fr; }}
                    .container {{ padding: 10px; }}
                    .header h1 {{ font-size: 2em; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 交通流机理分析报告</h1>
                    <p>基于仿真数据的交通流特性深度分析</p>
                    <p>生成时间: {timestamp}</p>
                </div>
        """
        
        # 流量-密度关系分析
        if flow_density_analysis:
            html += """
                <div class="section">
                    <h2>📊 流量-密度关系分析</h2>
                    <div class="metrics-grid">
            """
            
            if 'total_points' in flow_density_analysis:
                html += f"""
                    <div class="metric-card">
                        <h3>数据点数量</h3>
                        <div class="value">{flow_density_analysis['total_points']}</div>
                        <div class="unit">个有效数据点</div>
                    </div>
                """
            
            if 'flow_density_correlation' in flow_density_analysis:
                corr = flow_density_analysis['flow_density_correlation']
                status_class = 'status-good' if abs(corr) > 0.7 else 'status-warning' if abs(corr) > 0.4 else 'status-poor'
                html += f"""
                    <div class="metric-card">
                        <h3>流量-密度相关性</h3>
                        <div class="value">{corr:.3f}</div>
                        <div class="unit">
                            <span class="status-indicator {status_class}"></span>
                            {self._get_correlation_description(corr)}
                        </div>
                    </div>
                """
            
            if 'r_squared' in flow_density_analysis:
                r2 = flow_density_analysis['r_squared']
                status_class = 'status-good' if r2 > 0.8 else 'status-warning' if r2 > 0.6 else 'status-poor'
                html += f"""
                    <div class="metric-card">
                        <h3>拟合优度</h3>
                        <div class="value">{r2:.3f}</div>
                        <div class="unit">
                            <span class="status-indicator {status_class}"></span>
                            R²值
                        </div>
                    </div>
                """
            
            if 'quadratic_fit' in flow_density_analysis:
                fit = flow_density_analysis['quadratic_fit']
                html += f"""
                    <div class="metric-card">
                        <h3>拟合方程</h3>
                        <div class="value">二次函数</div>
                        <div class="unit">{fit['equation']}</div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        # 速度-流量关系分析
        if speed_flow_analysis:
            html += """
                <div class="section">
                    <h2>🚦 速度-流量关系分析</h2>
                    <div class="metrics-grid">
            """
            
            if 'total_points' in speed_flow_analysis:
                html += f"""
                    <div class="metric-card">
                        <h3>数据点数量</h3>
                        <div class="value">{speed_flow_analysis['total_points']}</div>
                        <div class="unit">个有效数据点</div>
                    </div>
                """
            
            if 'speed_flow_correlation' in speed_flow_analysis:
                corr = speed_flow_analysis['speed_flow_correlation']
                status_class = 'status-good' if abs(corr) > 0.7 else 'status-warning' if abs(corr) > 0.4 else 'status-poor'
                html += f"""
                    <div class="metric-card">
                        <h3>速度-流量相关性</h3>
                        <div class="value">{corr:.3f}</div>
                        <div class="unit">
                            <span class="status-indicator {status_class}"></span>
                            {self._get_correlation_description(corr)}
                        </div>
                    </div>
                """
            
            if 'relationship_type' in speed_flow_analysis:
                html += f"""
                    <div class="metric-card">
                        <h3>关系类型</h3>
                        <div class="value">{speed_flow_analysis['relationship_type']}</div>
                        <div class="unit">交通流特征</div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        # 交通流状态分析
        if traffic_state_analysis:
            html += """
                <div class="section">
                    <h2>🔄 交通流状态分析</h2>
                    <div class="metrics-grid">
            """
            
            if 'free_flow' in traffic_state_analysis:
                free_flow = traffic_state_analysis['free_flow']
                html += f"""
                    <div class="metric-card">
                        <h3>自由流状态</h3>
                        <div class="value">{free_flow['percentage']:.1f}%</div>
                        <div class="unit">{free_flow['count']} 个数据点</div>
                    </div>
                """
            
            if 'stable_flow' in traffic_state_analysis:
                stable_flow = traffic_state_analysis['stable_flow']
                html += f"""
                    <div class="metric-card">
                        <h3>稳定流状态</h3>
                        <div class="value">{stable_flow['percentage']:.1f}%</div>
                        <div class="unit">{stable_flow['count']} 个数据点</div>
                    </div>
                """
            
            if 'unstable_flow' in traffic_state_analysis:
                unstable_flow = traffic_state_analysis['unstable_flow']
                html += f"""
                    <div class="metric-card">
                        <h3>不稳定流状态</h3>
                        <div class="value">{unstable_flow['percentage']:.1f}%</div>
                        <div class="unit">{unstable_flow['count']} 个数据点</div>
                    </div>
                """
            
            if 'congestion' in traffic_state_analysis:
                congestion = traffic_state_analysis['congestion']
                html += f"""
                    <div class="metric-card">
                        <h3>拥堵状态</h3>
                        <div class="value">{congestion['percentage']:.1f}%</div>
                        <div class="unit">{congestion['count']} 个数据点</div>
                    </div>
                """
            
            if 'main_traffic_state' in traffic_state_analysis:
                main_state = traffic_state_analysis['main_traffic_state']
                main_percentage = traffic_state_analysis['main_state_percentage']
                state_names = {
                    'free_flow': '自由流',
                    'stable_flow': '稳定流',
                    'unstable_flow': '不稳定流',
                    'congestion': '拥堵'
                }
                html += f"""
                    <div class="metric-card">
                        <h3>主要交通状态</h3>
                        <div class="value">{state_names.get(main_state, main_state)}</div>
                        <div class="unit">占比 {main_percentage:.1f}%</div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        # 流量残差时间序列分析
        if residual_analysis:
            html += """
                <div class="section">
                    <h2>⏰ 流量残差时间序列分析</h2>
                    <div class="metrics-grid">
            """
            
            if 'total_points' in residual_analysis:
                html += f"""
                    <div class="metric-card">
                        <h3>数据点数量</h3>
                        <div class="value">{residual_analysis['total_points']}</div>
                        <div class="unit">个有效数据点</div>
                    </div>
                """
            
            if 'residual_mean' in residual_analysis:
                mean = residual_analysis['residual_mean']
                html += f"""
                    <div class="metric-card">
                        <h3>残差均值</h3>
                        <div class="value">{mean:.2f}</div>
                        <div class="unit">veh/h</div>
                    </div>
                """
            
            if 'residual_std' in residual_analysis:
                std = residual_analysis['residual_std']
                html += f"""
                    <div class="metric-card">
                        <h3>残差标准差</h3>
                        <div class="value">{std:.2f}</div>
                        <div class="unit">veh/h</div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        # 分析总结
        html += """
            <div class="analysis-summary">
                <h3>🔍 机理分析总结</h3>
                <ul>
        """
        
        if flow_density_analysis and 'r_squared' in flow_density_analysis:
            r2 = flow_density_analysis['r_squared']
            if r2 > 0.8:
                html += "<li>流量-密度关系拟合效果良好，符合经典交通流理论</li>"
            elif r2 > 0.6:
                html += "<li>流量-密度关系拟合效果一般，存在一定偏差</li>"
            else:
                html += "<li>流量-密度关系拟合效果较差，需要进一步分析</li>"
        
        if speed_flow_analysis and 'relationship_type' in speed_flow_analysis:
            rel_type = speed_flow_analysis['relationship_type']
            if "强负相关" in rel_type:
                html += "<li>速度-流量呈现强负相关，符合拥堵交通流特征</li>"
            elif "强正相关" in rel_type:
                html += "<li>速度-流量呈现强正相关，符合自由流特征</li>"
            else:
                html += "<li>速度-流量关系不明确，需要进一步分析</li>"
        
        if traffic_state_analysis and 'main_traffic_state' in traffic_state_analysis:
            main_state = traffic_state_analysis['main_traffic_state']
            if main_state == 'free_flow':
                html += "<li>交通流以自由流状态为主，道路通行条件良好</li>"
            elif main_state == 'congestion':
                html += "<li>交通流以拥堵状态为主，需要优化交通管理</li>"
            else:
                html += "<li>交通流状态相对稳定，处于过渡阶段</li>"
        
        html += """
                </ul>
            </div>
        """
        
        # 图表展示
        if chart_files:
            html += """
                <div class="section">
                    <h2>📈 机理分析图表</h2>
            """
            
            for chart_file in chart_files:
                chart_name = self._get_friendly_chart_name(chart_file)
                html += f"""
                    <div class="chart-container">
                        <h3>{chart_name}</h3>
                        <img src="../charts/{Path(chart_file).name}" alt="{chart_name}" />
                    </div>
                """
            
            html += "</div>"
        
        # 页脚
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
    
    def _get_correlation_description(self, correlation: float) -> str:
        """获取相关性描述"""
        abs_corr = abs(correlation)
        if abs_corr > 0.8:
            return "极强相关"
        elif abs_corr > 0.6:
            return "强相关"
        elif abs_corr > 0.4:
            return "中等相关"
        elif abs_corr > 0.2:
            return "弱相关"
        else:
            return "无相关"
    
    def _get_friendly_chart_name(self, chart_file: str) -> str:
        """获取友好的图表名称"""
        chart_name_map = {
            "flow_density_relationship.png": "流量-密度关系散点图",
            "speed_flow_relationship.png": "速度-流量关系散点图",
            "traffic_state_distribution.png": "交通流状态分布饼图",
            "flow_residual_timeseries.png": "流量残差时间序列图",
            "flow_speed_density_3d.png": "流量-速度-密度三维关系图",
            "traffic_parameters_timeseries.png": "交通参数时间序列图"
        }
        chart_name = Path(chart_file).name
        return chart_name_map.get(chart_name, chart_name)
    
    def _export_analysis_csvs(self, data: pd.DataFrame, 
                             flow_density_analysis: Dict[str, Any], 
                             speed_flow_analysis: Dict[str, Any], 
                             traffic_state_analysis: Dict[str, Any], 
                             residual_analysis: Dict[str, Any]) -> Dict[str, str]:
        """导出分析结果CSV文件"""
        try:
            if self.reports_dir is None:
                logger.warning("报告目录未设置，跳过CSV导出")
                return {}
            
            csv_files = {}
            
            # 1. 流量-密度分析结果
            if flow_density_analysis:
                fd_df = pd.DataFrame([flow_density_analysis])
                fd_file = self.reports_dir / "flow_density_analysis.csv"
                fd_df.to_csv(fd_file, index=False, encoding="utf-8-sig")
                csv_files["flow_density_analysis.csv"] = str(fd_file)
            
            # 2. 速度-流量分析结果
            if speed_flow_analysis:
                sf_df = pd.DataFrame([speed_flow_analysis])
                sf_file = self.reports_dir / "speed_flow_analysis.csv"
                sf_df.to_csv(sf_file, index=False, encoding="utf-8-sig")
                csv_files["speed_flow_analysis.csv"] = str(sf_file)
            
            # 3. 交通流状态分析结果
            if traffic_state_analysis:
                ts_df = pd.DataFrame([traffic_state_analysis])
                ts_file = self.reports_dir / "traffic_state_analysis.csv"
                ts_df.to_csv(ts_file, index=False, encoding="utf-8-sig")
                csv_files["traffic_state_analysis.csv"] = str(ts_file)
            
            # 4. 流量残差分析结果
            if residual_analysis:
                ra_df = pd.DataFrame([residual_analysis])
                ra_file = self.reports_dir / "residual_analysis.csv"
                ra_df.to_csv(ra_file, index=False, encoding="utf-8-sig")
                csv_files["residual_analysis.csv"] = str(ra_file)
            
            # 5. 原始数据
            if not data.empty:
                data_file = self.reports_dir / "mechanism_analysis_data.csv"
                data.to_csv(data_file, index=False, encoding="utf-8-sig")
                csv_files["mechanism_analysis_data.csv"] = str(data_file)
            
            logger.info(f"导出了 {len(csv_files)} 个CSV文件")
            return csv_files
            
        except Exception as e:
            logger.error(f"导出CSV文件失败: {e}")
            return {}
