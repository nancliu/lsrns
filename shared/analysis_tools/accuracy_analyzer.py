"""
精度分析器
迁移自原有的精度分析逻辑
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccuracyAnalyzer:
    """精度分析器类"""
    
    def __init__(self):
        self.analysis_results = {}
        self.charts_dir = None
        self.reports_dir = None
        
    def set_output_dirs(self, charts_dir: str, reports_dir: str):
        """
        设置输出目录
        
        Args:
            charts_dir: 图表输出目录
            reports_dir: 报告输出目录
        """
        self.charts_dir = Path(charts_dir)
        self.reports_dir = Path(reports_dir)
        
        # 创建目录
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"设置输出目录: 图表={charts_dir}, 报告={reports_dir}")
    
    def load_simulation_data(self, simulation_folder: str) -> Dict[str, pd.DataFrame]:
        """
        加载仿真数据
        
        Args:
            simulation_folder: 仿真文件夹路径
            
        Returns:
            仿真数据字典
        """
        try:
            sim_path = Path(simulation_folder)
            data = {}
            
            # 加载E1检测器数据
            e1_folder = sim_path / "e1_detectors"
            if e1_folder.exists():
                e1_files = list(e1_folder.glob("*.xml"))
                e1_data = []
                
                for e1_file in e1_files:
                    # 解析E1 XML文件
                    e1_df = self._parse_e1_xml(e1_file)
                    if not e1_df.empty:
                        e1_data.append(e1_df)
                
                if e1_data:
                    data["e1_detectors"] = pd.concat(e1_data, ignore_index=True)
                    logger.info(f"加载了 {len(e1_data)} 个E1检测器文件")
            
            # 加载门架数据
            gantry_folder = sim_path / "gantry_data"
            if gantry_folder.exists():
                gantry_files = list(gantry_folder.glob("*.csv"))
                gantry_data = []
                
                for gantry_file in gantry_files:
                    gantry_df = pd.read_csv(gantry_file)
                    gantry_data.append(gantry_df)
                
                if gantry_data:
                    data["gantry_data"] = pd.concat(gantry_data, ignore_index=True)
                    logger.info(f"加载了 {len(gantry_data)} 个门架数据文件")
            
            # 加载仿真摘要
            summary_file = sim_path / "summary.xml"
            if summary_file.exists():
                data["summary"] = self._parse_summary_xml(summary_file)
                logger.info("加载了仿真摘要数据")
            
            return data
            
        except Exception as e:
            logger.error(f"加载仿真数据失败: {e}")
            return {}
    
    def _parse_e1_xml(self, e1_file: Path) -> pd.DataFrame:
        """
        解析E1检测器XML文件
        
        Args:
            e1_file: E1检测器文件路径
            
        Returns:
            E1检测器数据DataFrame
        """
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(e1_file)
            root = tree.getroot()
            
            data = []
            for interval in root.findall(".//interval"):
                record = {
                    "detector_id": interval.get("id"),
                    "begin": float(interval.get("begin")),
                    "end": float(interval.get("end")),
                    "nVehContrib": int(interval.get("nVehContrib", 0)),
                    "flow": float(interval.get("flow", 0)),
                    "occupancy": float(interval.get("occupancy", 0)),
                    "speed": float(interval.get("speed", 0)),
                    "file": e1_file.name
                }
                data.append(record)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"解析E1文件失败 {e1_file}: {e}")
            return pd.DataFrame()
    
    def _parse_summary_xml(self, summary_file: Path) -> pd.DataFrame:
        """
        解析仿真摘要XML文件
        
        Args:
            summary_file: 仿真摘要文件路径
            
        Returns:
            仿真摘要数据DataFrame
        """
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(summary_file)
            root = tree.getroot()
            
            data = []
            for step in root.findall(".//step"):
                record = {
                    "time": float(step.get("time")),
                    "loaded": int(step.get("loaded", 0)),
                    "inserted": int(step.get("inserted", 0)),
                    "running": int(step.get("running", 0)),
                    "waiting": int(step.get("waiting", 0)),
                    "ended": int(step.get("ended", 0))
                }
                data.append(record)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"解析仿真摘要文件失败 {summary_file}: {e}")
            return pd.DataFrame()
    
    def calculate_accuracy_metrics(self, simulated_data: pd.DataFrame, 
                                 observed_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算精度指标
        
        Args:
            simulated_data: 仿真数据
            observed_data: 观测数据
            
        Returns:
            精度指标字典
        """
        try:
            metrics = {}
            
            # 确保数据对齐
            common_columns = simulated_data.columns.intersection(observed_data.columns)
            if len(common_columns) == 0:
                logger.warning("仿真数据和观测数据没有共同的列")
                return metrics
            
            # 对齐数据
            aligned_sim = simulated_data[common_columns]
            aligned_obs = observed_data[common_columns]
            
            # 计算各种精度指标
            for col in common_columns:
                sim_values = aligned_sim[col].dropna()
                obs_values = aligned_obs[col].dropna()
                
                if len(sim_values) > 0 and len(obs_values) > 0:
                    # 确保长度一致
                    min_len = min(len(sim_values), len(obs_values))
                    sim_values = sim_values.iloc[:min_len]
                    obs_values = obs_values.iloc[:min_len]
                    
                    # 计算指标
                    metrics[f"{col}_mae"] = np.mean(np.abs(sim_values - obs_values))
                    metrics[f"{col}_mse"] = np.mean((sim_values - obs_values) ** 2)
                    metrics[f"{col}_rmse"] = np.sqrt(metrics[f"{col}_mse"])
                    
                    # 计算MAPE（避免除零）
                    non_zero_obs = obs_values != 0
                    if non_zero_obs.any():
                        mape = np.mean(np.abs((sim_values[non_zero_obs] - obs_values[non_zero_obs]) / obs_values[non_zero_obs])) * 100
                        metrics[f"{col}_mape"] = mape
                    
                    # 计算相关系数
                    correlation = np.corrcoef(sim_values, obs_values)[0, 1]
                    if not np.isnan(correlation):
                        metrics[f"{col}_correlation"] = correlation
            
            logger.info(f"计算了 {len(metrics)} 个精度指标")
            return metrics
            
        except Exception as e:
            logger.error(f"计算精度指标失败: {e}")
            return {}
    
    def generate_accuracy_charts(self, simulated_data: pd.DataFrame, 
                               observed_data: pd.DataFrame, 
                               metrics: Dict[str, float]) -> List[str]:
        """
        生成精度分析图表
        
        Args:
            simulated_data: 仿真数据
            observed_data: 观测数据
            metrics: 精度指标
            
        Returns:
            生成的图表文件路径列表
        """
        try:
            if self.charts_dir is None:
                raise Exception("图表输出目录未设置")
            
            chart_files = []
            
            # 设置图表样式
            plt.style.use('default')
            sns.set_palette("husl")
            
            # 1. 时间序列对比图
            common_columns = simulated_data.columns.intersection(observed_data.columns)
            for col in common_columns[:5]:  # 限制图表数量
                plt.figure(figsize=(12, 6))
                
                sim_values = simulated_data[col].dropna()
                obs_values = observed_data[col].dropna()
                
                min_len = min(len(sim_values), len(obs_values))
                if min_len > 0:
                    plt.plot(range(min_len), sim_values.iloc[:min_len], label='仿真数据', alpha=0.7)
                    plt.plot(range(min_len), obs_values.iloc[:min_len], label='观测数据', alpha=0.7)
                    plt.title(f'{col} 时间序列对比')
                    plt.xlabel('时间步')
                    plt.ylabel(col)
                    plt.legend()
                    plt.grid(True, alpha=0.3)
                    
                    chart_file = self.charts_dir / f"timeseries_{col}.png"
                    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_files.append(str(chart_file))
            
            # 2. 散点图
            for col in common_columns[:5]:
                plt.figure(figsize=(8, 8))
                
                sim_values = simulated_data[col].dropna()
                obs_values = observed_data[col].dropna()
                
                min_len = min(len(sim_values), len(obs_values))
                if min_len > 0:
                    plt.scatter(obs_values.iloc[:min_len], sim_values.iloc[:min_len], alpha=0.6)
                    
                    # 添加对角线
                    min_val = min(sim_values.iloc[:min_len].min(), obs_values.iloc[:min_len].min())
                    max_val = max(sim_values.iloc[:min_len].max(), obs_values.iloc[:min_len].max())
                    plt.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8)
                    
                    plt.title(f'{col} 散点图')
                    plt.xlabel('观测值')
                    plt.ylabel('仿真值')
                    plt.grid(True, alpha=0.3)
                    
                    chart_file = self.charts_dir / f"scatter_{col}.png"
                    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_files.append(str(chart_file))
            
            # 3. 精度指标柱状图
            if metrics:
                plt.figure(figsize=(12, 6))
                
                metric_names = list(metrics.keys())
                metric_values = list(metrics.values())
                
                plt.bar(range(len(metric_names)), metric_values)
                plt.title('精度指标对比')
                plt.xlabel('指标')
                plt.ylabel('值')
                plt.xticks(range(len(metric_names)), metric_names, rotation=45)
                plt.grid(True, alpha=0.3)
                
                chart_file = self.charts_dir / "accuracy_metrics.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            logger.info(f"生成了 {len(chart_files)} 个图表")
            return chart_files
            
        except Exception as e:
            logger.error(f"生成精度分析图表失败: {e}")
            return []
    
    def generate_accuracy_report(self, metrics: Dict[str, float], 
                               chart_files: List[str]) -> str:
        """
        生成精度分析报告
        
        Args:
            metrics: 精度指标
            chart_files: 图表文件路径列表
            
        Returns:
            报告文件路径
        """
        try:
            if self.reports_dir is None:
                raise Exception("报告输出目录未设置")
            
            # 生成HTML报告
            report_file = self.reports_dir / "accuracy_report.html"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>精度分析报告</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .metrics {{ margin: 20px 0; }}
                    .metric {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
                    .charts {{ margin: 20px 0; }}
                    .chart {{ margin: 20px 0; text-align: center; }}
                    .chart img {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>精度分析报告</h1>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="metrics">
                    <h2>精度指标</h2>
            """
            
            # 添加指标
            for metric_name, metric_value in metrics.items():
                html_content += f"""
                    <div class="metric">
                        <strong>{metric_name}:</strong> {metric_value:.4f}
                    </div>
                """
            
            html_content += """
                </div>
                
                <div class="charts">
                    <h2>分析图表</h2>
            """
            
            # 添加图表
            for chart_file in chart_files:
                chart_name = Path(chart_file).stem
                html_content += f"""
                    <div class="chart">
                        <h3>{chart_name}</h3>
                        <img src="{chart_file}" alt="{chart_name}">
                    </div>
                """
            
            html_content += """
                </div>
            </body>
            </html>
            """
            
            # 写入文件
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"精度分析报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"生成精度分析报告失败: {e}")
            return ""
    
    def analyze_accuracy(self, simulation_folder: str, observed_data: pd.DataFrame,
                        analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        执行精度分析
        
        Args:
            simulation_folder: 仿真文件夹路径
            observed_data: 观测数据
            analysis_type: 分析类型
            
        Returns:
            分析结果
        """
        try:
            logger.info(f"开始精度分析: {simulation_folder}")
            
            # 加载仿真数据
            simulation_data = self.load_simulation_data(simulation_folder)
            
            if not simulation_data:
                raise Exception("无法加载仿真数据")
            
            # 设置输出目录
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            charts_dir = f"analysis/charts_{current_time}"
            reports_dir = f"analysis/reports_{current_time}"
            self.set_output_dirs(charts_dir, reports_dir)
            
            # 选择要分析的数据
            if "e1_detectors" in simulation_data:
                simulated_data = simulation_data["e1_detectors"]
            elif "gantry_data" in simulation_data:
                simulated_data = simulation_data["gantry_data"]
            else:
                raise Exception("没有找到可分析的仿真数据")
            
            # 计算精度指标
            metrics = self.calculate_accuracy_metrics(simulated_data, observed_data)
            
            # 生成图表
            chart_files = self.generate_accuracy_charts(simulated_data, observed_data, metrics)
            
            # 生成报告
            report_file = self.generate_accuracy_report(metrics, chart_files)
            
            # 保存结果
            results = {
                "analysis_type": analysis_type,
                "simulation_folder": simulation_folder,
                "metrics": metrics,
                "chart_files": chart_files,
                "report_file": report_file,
                "analysis_time": datetime.now().isoformat(),
                "data_summary": {
                    "simulated_records": len(simulated_data),
                    "observed_records": len(observed_data),
                    "metrics_count": len(metrics)
                }
            }
            
            # 保存结果到JSON文件
            results_file = Path(reports_dir) / "analysis_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info("精度分析完成")
            return results
            
        except Exception as e:
            logger.error(f"精度分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            } 