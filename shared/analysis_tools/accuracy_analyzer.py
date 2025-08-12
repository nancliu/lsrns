"""
精度分析器
迁移自原有的精度分析逻辑
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from matplotlib import rcParams
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
        # 初始化绘图与中文字体
        self._preferred_cn_font = None
        self._setup_plot_style()
        # MAPE 分母为0处理策略：'filter' 过滤，或 'epsilon' 使用极小值
        self.mape_zero_policy: str = "filter"
        self.mape_epsilon: float = 1e-6
        # 解析统计
        self._e1_total_files: int = 0
        self._e1_valid_tables: int = 0
        self._e1_parse_failures: int = 0

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
            
            # 加载E1检测器数据（兼容 e1_detectors / e1 以及 e1* 目录，递归 *.xml）
            e1_dirs: list[Path] = []
            for cand in [sim_path / "e1_detectors", sim_path / "e1"]:
                if cand.exists() and cand.is_dir():
                    e1_dirs.append(cand)
            # 额外扫描以 e1 开头的目录
            try:
                e1_dirs.extend([p for p in sim_path.iterdir() if p.is_dir() and p.name.lower().startswith("e1") and p not in e1_dirs])
            except Exception:
                pass
            if e1_dirs:
                frames: list[pd.DataFrame] = []
                total_files = 0
                for e1_folder in e1_dirs:
                    for e1_file in e1_folder.rglob("*.xml"):
                        total_files += 1
                        df = self._parse_e1_xml(e1_file)
                        if not df.empty:
                            frames.append(df)
                # 记录统计
                self._e1_total_files = total_files
                self._e1_valid_tables = len(frames)
                if frames:
                    data["e1_detectors"] = pd.concat(frames, ignore_index=True)
                    logger.info(f"加载E1检测器XML：{total_files}，有效表格：{len(frames)}，解析失败：{self._e1_parse_failures}")
            
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
            try:
                self._e1_parse_failures += 1
            except Exception:
                pass
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
            metrics: Dict[str, Any] = {}
            
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
                    
                    # 计算MAPE（分母为0的策略）
                    obs_for_mape = obs_values.copy()
                    if self.mape_zero_policy == "epsilon":
                        obs_for_mape = obs_for_mape.replace(0, self.mape_epsilon)
                        mape_mask = ~np.isnan(obs_for_mape)
                    else:  # filter
                        mape_mask = obs_for_mape != 0
                    if mape_mask.any():
                        mape = np.mean(np.abs((sim_values[mape_mask] - obs_for_mape[mape_mask]) / obs_for_mape[mape_mask])) * 100
                        metrics[f"{col}_mape"] = mape
                        metrics[f"{col}_sample_size"] = int(mape_mask.sum())
                    
                    # 计算相关系数
                    correlation = np.corrcoef(sim_values, obs_values)[0, 1]
                    if not np.isnan(correlation):
                        metrics[f"{col}_correlation"] = correlation

                    # GEH 指标（flow 专用）
                    if col.lower() == "flow":
                        geh_vals = self._compute_geh(sim_values.to_numpy(dtype=float), obs_values.to_numpy(dtype=float))
                        if geh_vals.size > 0:
                            geh_mean = float(np.nanmean(geh_vals))
                            geh_pass = float(np.mean(geh_vals <= 5) * 100)
                            metrics["flow_geh_mean"] = geh_mean
                            metrics["flow_geh_pass_rate"] = geh_pass
            
            logger.info(f"计算了 {len(metrics)} 个精度指标")
            return metrics
        except Exception as e:
            logger.error(f"计算精度指标失败: {e}")
            return {}

    @staticmethod
    def _compute_geh(simulated: np.ndarray, observed: np.ndarray) -> np.ndarray:
        try:
            den = (simulated + observed) / 2.0
            mask = den != 0
            vals = np.full_like(simulated, np.nan, dtype=float)
            if mask.any():
                vals[mask] = np.sqrt(((simulated[mask] - observed[mask]) ** 2) / den[mask])
            return vals
        except Exception:
            return np.array([], dtype=float)
    
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
            try:
                plt.style.use('default')
            except Exception:
                pass
            # 再次确保中文字体生效（防止样式覆盖）
            self._ensure_chinese_font()
            
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
            
            # 3. 直方图对比（重叠）
            for col in common_columns[:5]:
                plt.figure(figsize=(10, 6))
                sim_values = simulated_data[col].dropna()
                obs_values = observed_data[col].dropna()
                min_len = min(len(sim_values), len(obs_values))
                if min_len > 0:
                    plt.hist(obs_values.iloc[:min_len], bins=30, alpha=0.5, label='观测', color='#4CAF50')
                    plt.hist(sim_values.iloc[:min_len], bins=30, alpha=0.5, label='仿真', color='#2196F3')
                    plt.title(f'{col} 分布对比')
                    plt.xlabel(col)
                    plt.ylabel('频次')
                    plt.legend()
                    plt.grid(True, alpha=0.3)
                    chart_file = self.charts_dir / f"hist_{col}.png"
                    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_files.append(str(chart_file))

            # 4. 残差直方图（仅 flow 存在时）
            if 'flow' in common_columns:
                plt.figure(figsize=(10, 6))
                sim_values = simulated_data['flow'].dropna()
                obs_values = observed_data['flow'].dropna()
                min_len = min(len(sim_values), len(obs_values))
                if min_len > 0:
                    residual = (sim_values.iloc[:min_len] - obs_values.iloc[:min_len]).to_numpy()
                    plt.hist(residual, bins=40, alpha=0.8, color='#FF9800')
                    plt.title('flow 残差分布 (仿真-观测)')
                    plt.xlabel('残差')
                    plt.ylabel('频次')
                    plt.grid(True, alpha=0.3)
                    chart_file = self.charts_dir / "residual_flow.png"
                    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_files.append(str(chart_file))

                # 5. GEH/MAPE 分布（flow）
                if min_len > 0:
                    sim_arr = sim_values.iloc[:min_len].to_numpy(dtype=float)
                    obs_arr = obs_values.iloc[:min_len].to_numpy(dtype=float)
                    # GEH 直方图
                    geh_vals = self._compute_geh(sim_arr, obs_arr)
                    if geh_vals.size > 0 and np.isfinite(geh_vals).any():
                        plt.figure(figsize=(10, 6))
                        plt.hist(geh_vals[~np.isnan(geh_vals)], bins=30, alpha=0.8, color='#9CCC65')
                        plt.axvline(5, color='red', linestyle='--', label='GEH=5')
                        plt.title('flow GEH 分布')
                        plt.xlabel('GEH')
                        plt.ylabel('频次')
                        plt.legend()
                        plt.grid(True, alpha=0.3)
                        chart_file = self.charts_dir / "geh_distribution.png"
                        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                        plt.close()
                        chart_files.append(str(chart_file))

                    # MAPE 直方图（按当前策略）
                    obs_for_mape = obs_arr.copy()
                    if self.mape_zero_policy == 'epsilon':
                        obs_for_mape[obs_for_mape == 0] = self.mape_epsilon
                        mask = ~np.isnan(obs_for_mape)
                    else:
                        mask = obs_for_mape != 0
                    if mask.any():
                        mape_vals = np.abs((sim_arr[mask] - obs_for_mape[mask]) / obs_for_mape[mask]) * 100.0
                        if mape_vals.size > 0:
                            plt.figure(figsize=(10, 6))
                            plt.hist(mape_vals, bins=30, alpha=0.8, color='#64B5F6')
                            plt.axvline(15, color='red', linestyle='--', label='MAPE=15%')
                            plt.title('flow MAPE 分布')
                            plt.xlabel('MAPE (%)')
                            plt.ylabel('频次')
                            plt.legend()
                            plt.grid(True, alpha=0.3)
                            chart_file = self.charts_dir / "mape_distribution.png"
                            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                            plt.close()
                            chart_files.append(str(chart_file))

            # 5. 精度指标柱状图
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
            
            # 添加图表（使用相对路径 ../charts/xxx.png 方便通过 /cases 静态访问）
            for chart_file in chart_files:
                chart_name = Path(chart_file).stem
                chart_rel = f"../charts/{Path(chart_file).name}"
                html_content += f"""
                    <div class="chart">
                        <h3>{chart_name}</h3>
                        <img src="{chart_rel}" alt="{chart_name}">
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
            _t0 = datetime.now()
            
            # 加载仿真数据
            simulation_data = self.load_simulation_data(simulation_folder)
            
            if not simulation_data:
                raise Exception("无法加载仿真数据")
            
            # 若未预先设置输出目录，则回退到案例标准目录
            if self.charts_dir is None or self.reports_dir is None:
                sim_path = Path(simulation_folder)
                case_root = sim_path.parent if sim_path.name == 'simulation' else sim_path
                charts_dir = (case_root / "analysis" / "accuracy" / "charts").as_posix()
                reports_dir = (case_root / "analysis" / "accuracy" / "reports").as_posix()
                self.set_output_dirs(charts_dir, reports_dir)
            
            # 选择要分析的数据（仅 E1 或门架数据）
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
            _t1 = datetime.now()
            duration_sec = (_t1 - _t0).total_seconds()

            # 对齐信息
            try:
                common_columns = simulated_data.columns.intersection(observed_data.columns)
            except Exception:
                common_columns = []

            # 产物规模/大小
            chart_count = len(chart_files)
            charts_total_bytes = 0
            for p in chart_files:
                try:
                    charts_total_bytes += os.path.getsize(p)
                except Exception:
                    pass
            report_bytes = 0
            try:
                report_bytes = os.path.getsize(report_file) if report_file else 0
            except Exception:
                pass

            # 仿真摘要统计（如有）
            summary_stats: Dict[str, Any] = {}
            try:
                if isinstance(simulation_data.get("summary"), pd.DataFrame) and not simulation_data["summary"].empty:
                    sm = simulation_data["summary"]
                    summary_stats = {
                        "steps": int(len(sm)),
                        "loaded_total": int(sm["loaded"].sum()) if "loaded" in sm.columns else None,
                        "inserted_total": int(sm["inserted"].sum()) if "inserted" in sm.columns else None,
                        "running_max": int(sm["running"].max()) if "running" in sm.columns else None,
                        "waiting_max": int(sm["waiting"].max()) if "waiting" in sm.columns else None,
                        "ended_total": int(sm["ended"].sum()) if "ended" in sm.columns else None,
                    }
            except Exception:
                summary_stats = {}

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
                },
                "source_stats": {
                    "data_source_used": "e1_detectors" if "e1_detectors" in simulation_data else ("gantry_data" if "gantry_data" in simulation_data else None),
                    "e1_total_files": self._e1_total_files,
                    "e1_valid_tables": self._e1_valid_tables,
                    "e1_parse_failures": self._e1_parse_failures
                },
                "alignment": {
                    "common_columns": list(common_columns) if hasattr(common_columns, "tolist") else list(common_columns),
                    "mape_zero_policy": self.mape_zero_policy,
                    "mape_epsilon": self.mape_epsilon
                },
                "efficiency": {
                    "duration_sec": duration_sec,
                    "chart_count": chart_count,
                    "charts_total_bytes": charts_total_bytes,
                    "report_bytes": report_bytes,
                    "summary_stats": summary_stats
                }
            }
            
            # 保存结果到JSON文件
            results_file = self.reports_dir / "analysis_results.json"
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