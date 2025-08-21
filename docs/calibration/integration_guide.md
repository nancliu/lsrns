# 标定功能集成指南

## 📋 概述

本文档说明如何将SUMO参数标定功能集成到现有OD数据处理与仿真系统架构中。标定功能将作为第四种分析类型，与现有的精度分析、机理分析、性能分析并列。

## 🏗️ 集成架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    OD数据处理与仿真系统                      │
├─────────────────────────────────────────────────────────────┤
│  API层 (FastAPI)                                           │
│  ├── 案例管理接口                                          │
│  ├── 仿真管理接口                                          │
│  ├── 分析接口                                              │
│  │   ├── 精度分析 (accuracy_analysis)                     │
│  │   ├── 机理分析 (mechanism_analysis)                     │
│  │   ├── 性能分析 (performance_analysis)                   │
│  │   └── 🆕 参数标定 (calibration_analysis)               │
│  └── 模板管理接口                                          │
├─────────────────────────────────────────────────────────────┤
│  Services层 (业务逻辑)                                     │
│  ├── 案例服务 (case_service)                               │
│  ├── 仿真服务 (simulation_service)                         │
│  ├── 分析服务                                              │
│  │   ├── accuracy_service                                  │
│  │   ├── mechanism_service                                 │
│  │   ├── performance_service                               │
│  │   └── 🆕 calibration_service                            │
│  └── 模板服务 (template_service)                           │
├─────────────────────────────────────────────────────────────┤
│  Shared层 (核心功能)                                       │
│  ├── analysis_tools/                                       │
│  │   ├── accuracy_analysis.py                              │
│  │   ├── mechanism_analysis.py                             │
│  │   ├── performance_analysis.py                           │
│  │   └── 🆕 calibration_analysis.py                        │
│  ├── calibration_tools/                                    │
│  │   ├── ga_xgboost_optimizer.py                           │
│  │   ├── sumo_runner.py                                    │
│  │   ├── parameter_generator.py                            │
│  │   └── fitness_calculator.py                             │
│  ├── data_access/                                          │
│  ├── data_processors/                                      │
│  └── utilities/                                            │
└─────────────────────────────────────────────────────────────┘
```

### 模块职责

#### API层 (Routes)
- **calibration_routes.py**: 处理标定相关的HTTP请求
- 提供标定任务创建、监控、结果获取等接口
- 复用现有的中间件和错误处理机制

#### Services层
- **calibration_service.py**: 实现标定业务逻辑
- 管理标定任务的生命周期
- 协调各个分析工具的执行

#### Shared层
- **calibration_analysis.py**: 标定分析主模块，集成到analysis_tools
- **calibration_tools/**: 标定算法和工具集合
- 复用现有的数据访问和工具函数

## 🔧 具体集成步骤

### 步骤1: 创建标定分析模块

在`shared/analysis_tools/`下创建`calibration_analysis.py`：

```python
# shared/analysis_tools/calibration_analysis.py
"""
SUMO参数标定分析模块
集成到现有分析框架中，作为第四种分析类型
"""

from typing import Dict, List, Any
from pathlib import Path
import json
import logging

class CalibrationAnalysis:
    """SUMO参数标定分析类"""
    
    def __init__(self, case_id: str, config: Dict[str, Any]):
        self.case_id = case_id
        self.config = config
        self.analysis_type = "calibration"
        self.logger = logging.getLogger(__name__)
        
    def run_analysis(self) -> Dict[str, Any]:
        """执行标定分析"""
        try:
            # 1. 参数验证
            self._validate_config()
            
            # 2. 初始化标定环境
            self._setup_calibration_environment()
            
            # 3. 执行标定优化
            calibration_result = self._run_calibration_optimization()
            
            # 4. 生成分析报告
            report = self._generate_analysis_report(calibration_result)
            
            # 5. 保存结果
            self._save_results(calibration_result, report)
            
            return {
                "status": "success",
                "analysis_type": self.analysis_type,
                "result": calibration_result,
                "report": report
            }
            
        except Exception as e:
            self.logger.error(f"标定分析失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _validate_config(self):
        """验证标定配置"""
        required_fields = ["parameter_ranges", "optimization_config", "simulation_config"]
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"缺少必需的配置字段: {field}")
    
    def _setup_calibration_environment(self):
        """设置标定环境"""
        # 创建标定工作目录
        self.calibration_dir = Path(f"cases/{self.case_id}/results/calibration")
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化标定工具
        from ..calibration_tools.parameter_generator import ParameterGenerator
        from ..calibration_tools.ga_xgboost_optimizer import GAXGBoostOptimizer
        
        self.parameter_generator = ParameterGenerator(self.config["parameter_ranges"])
        self.optimizer = GAXGBoostOptimizer(self.config["optimization_config"])
    
    def _run_calibration_optimization(self) -> Dict[str, Any]:
        """执行标定优化"""
        # 1. 生成初始参数组合
        initial_parameters = self.parameter_generator.generate_latin_hypercube_samples(
            n_samples=self.config.get("initial_samples", 100)
        )
        
        # 2. 执行初始仿真
        initial_results = self._run_initial_simulations(initial_parameters)
        
        # 3. 训练代理模型
        self.optimizer.train_surrogate_model(initial_parameters, initial_results)
        
        # 4. 执行混合优化
        optimization_result = self.optimizer.run_optimization(
            max_generations=self.config.get("max_generations", 100)
        )
        
        return {
            "initial_parameters": initial_parameters,
            "initial_results": initial_results,
            "optimization_result": optimization_result,
            "best_parameters": optimization_result["best_individual"]
        }
    
    def _run_initial_simulations(self, parameters: List[Dict]) -> List[Dict]:
        """运行初始仿真"""
        from ..calibration_tools.sumo_runner import SUMORunner
        
        sumo_runner = SUMORunner(self.config["simulation_config"])
        results = []
        
        for i, param_set in enumerate(parameters):
            self.logger.info(f"运行初始仿真 {i+1}/{len(parameters)}")
            result = sumo_runner.run_simulation(param_set, self.case_id)
            results.append(result)
        
        return results
    
    def _generate_analysis_report(self, calibration_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析报告"""
        from ..calibration_tools.fitness_calculator import FitnessCalculator
        
        fitness_calculator = FitnessCalculator()
        
        # 计算各项指标
        metrics = fitness_calculator.calculate_all_metrics(calibration_result)
        
        # 生成报告
        report = {
            "analysis_type": "calibration",
            "case_id": self.case_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "best_parameters": calibration_result["best_parameters"],
            "optimization_history": calibration_result["optimization_result"]["history"],
            "recommendations": self._generate_recommendations(metrics)
        }
        
        return report
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if metrics.get("flow_error", 1.0) > 0.15:
            recommendations.append("流量误差较大，建议调整departSpeed和departLane参数")
        
        if metrics.get("insertion_rate", 0.0) < 0.95:
            recommendations.append("插入成功率较低，建议优化minGap和maxDepartDelay参数")
        
        if metrics.get("network_utilization", 0.0) < 0.8:
            recommendations.append("路网利用率不足，建议调整sigma和laneChangeMode参数")
        
        return recommendations
    
    def _save_results(self, calibration_result: Dict[str, Any], report: Dict[str, Any]):
        """保存分析结果"""
        # 保存标定结果
        result_file = self.calibration_dir / "calibration_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(calibration_result, f, ensure_ascii=False, indent=2)
        
        # 保存分析报告
        report_file = self.calibration_dir / "analysis_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存最优参数
        best_params_file = self.calibration_dir / "best_parameters.json"
        with open(best_params_file, 'w', encoding='utf-8') as f:
            json.dump(calibration_result["best_parameters"], f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"标定结果已保存到: {self.calibration_dir}")
```

### 步骤2: 创建标定服务

在`api/services/`下创建`calibration_service.py`：

```python
# api/services/calibration_service.py
"""
标定服务模块
实现标定相关的业务逻辑
"""

from typing import Dict, List, Any
from pathlib import Path
import logging
import asyncio
from datetime import datetime

from ..models.requests.calibration_requests import CalibrationRequest
from ..models.responses.base_response import BaseResponse
from ...shared.analysis_tools.calibration_analysis import CalibrationAnalysis

class CalibrationService:
    """标定服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_calibrations: Dict[str, Dict[str, Any]] = {}
    
    async def create_calibration_task(self, request: CalibrationRequest) -> BaseResponse:
        """创建标定任务"""
        try:
            # 1. 验证案例
            case = await self._validate_case(request.case_id)
            
            # 2. 创建标定配置
            config = self._create_calibration_config(request)
            
            # 3. 创建标定分析实例
            calibration_analysis = CalibrationAnalysis(request.case_id, config)
            
            # 4. 异步执行标定
            task_id = f"calibration_{request.case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 启动后台任务
            asyncio.create_task(self._run_calibration_background(
                task_id, calibration_analysis, request
            ))
            
            # 记录任务信息
            self.active_calibrations[task_id] = {
                "case_id": request.case_id,
                "status": "running",
                "start_time": datetime.now(),
                "config": config,
                "progress": 0
            }
            
            return BaseResponse(
                success=True,
                message="标定任务创建成功",
                data={
                    "task_id": task_id,
                    "status": "running"
                }
            )
            
        except Exception as e:
            self.logger.error(f"创建标定任务失败: {str(e)}")
            return BaseResponse(
                success=False,
                message=f"创建标定任务失败: {str(e)}"
            )
    
    async def get_calibration_status(self, task_id: str) -> BaseResponse:
        """获取标定任务状态"""
        if task_id not in self.active_calibrations:
            return BaseResponse(
                success=False,
                message="标定任务不存在"
            )
        
        task_info = self.active_calibrations[task_id]
        return BaseResponse(
            success=True,
            data=task_info
        )
    
    async def get_calibration_results(self, case_id: str) -> BaseResponse:
        """获取标定结果"""
        try:
            # 查找标定结果文件
            results_dir = Path(f"cases/{case_id}/results/calibration")
            
            if not results_dir.exists():
                return BaseResponse(
                    success=False,
                    message="未找到标定结果"
                )
            
            # 读取结果文件
            results = {}
            for file_path in results_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    import json
                    results[file_path.stem] = json.load(f)
            
            return BaseResponse(
                success=True,
                data=results
            )
            
        except Exception as e:
            self.logger.error(f"获取标定结果失败: {str(e)}")
            return BaseResponse(
                success=False,
                message=f"获取标定结果失败: {str(e)}"
            )
    
    async def _validate_case(self, case_id: str):
        """验证案例是否存在"""
        # 这里应该调用现有的案例服务进行验证
        # 暂时返回模拟数据
        return {"id": case_id, "name": f"案例_{case_id}"}
    
    def _create_calibration_config(self, request: CalibrationRequest) -> Dict[str, Any]:
        """创建标定配置"""
        # 加载默认配置
        from ...calibration_tools.configs.parameter_ranges import load_parameter_config
        from ...calibration_tools2.configs.ga_config import load2_ga_config
        from ...calibration_tools.configs.xgboost_config import load_xgboost_config
        
        config = {
            "parameter_ranges": load_parameter_config(request.scenario),
            "optimization_config": load2_ga_config(),
            "xgboost_config": load_xgboost_config(),
            "simulation_config": {
                "network_file": request.network_file,
                "taz_file": request.taz_file,
                "duration": request.simulation_duration,
                "output_config": request.output_config
            },
            "initial_samples": request.initial_samples,
            "max_generations": request.max_generations
        }
        
        return config
    
    async def _run_calibration_background(self, task_id: str, 
                                        calibration_analysis: CalibrationAnalysis,
                                        request: CalibrationRequest):
        """后台运行标定任务"""
        try:
            self.logger.info(f"开始执行标定任务: {task_id}")
            
            # 更新任务状态
            self.active_calibrations[task_id]["status"] = "running"
            
            # 执行标定分析
            result = calibration_analysis.run_analysis()
            
            if result["status"] == "success":
                # 更新任务状态
                self.active_calibrations[task_id].update({
                    "status": "completed",
                    "end_time": datetime.now(),
                    "progress": 100,
                    "result": result
                })
                
                self.logger.info(f"标定任务完成: {task_id}")
            else:
                # 更新任务状态
                self.active_calibrations[task_id].update({
                    "status": "failed",
                    "end_time": datetime.now(),
                    "error": result.get("error", "未知错误")
                })
                
                self.logger.error(f"标定任务失败: {task_id}")
                
        except Exception as e:
            self.logger.error(f"标定任务执行异常: {task_id}, 错误: {str(e)}")
            
            # 更新任务状态
            self.active_calibrations[task_id].update({
                "status": "failed",
                "end_time": datetime.now(),
                "error": str(e)
            })
```

### 步骤3: 创建标定路由

在`api/routes/`下创建`calibration_routes.py`：

```python
# api/routes/calibration_routes.py
"""
标定相关API路由
"""

from fastapi import APIRouter
from typing import List

from ..models.requests.calibration_requests import CalibrationRequest
from ..models.responses.base_response import BaseResponse
from ..services.calibration_service import CalibrationService

router = APIRouter(prefix="/api/v1/calibration", tags=["标定管理"])
calibration_service = CalibrationService()

@router.post("/create", response_model=BaseResponse)
async def create_calibration_task(request: CalibrationRequest):
    """创建标定任务"""
    return await calibration_service.create_calibration_task(request)

@router.get("/status/{task_id}", response_model=BaseResponse)
async def get_calibration_status(task_id: str):
    """获取标定任务状态"""
    return await calibration_service.get_calibration_status(task_id)

@router.get("/results/{case_id}", response_model=BaseResponse)
async def get_calibration_results(case_id: str):
    """获取标定结果"""
    return await calibration_service.get_calibration_results(case_id)

@router.get("/active-tasks", response_model=BaseResponse)
async def get_active_calibration_tasks():
    """获取活跃的标定任务列表"""
    active_tasks = [
        {"task_id": task_id, **task_info}
        for task_id, task_info in calibration_service.active_calibrations.items()
    ]
    
    return BaseResponse(
        success=True,
        data={"active_tasks": active_tasks}
    )

@router.delete("/cancel/{task_id}", response_model=BaseResponse)
async def cancel_calibration_task(task_id: str):
    """取消标定任务"""
    if task_id in calibration_service.active_calibrations:
        task_info = calibration_service.active_calibrations[task_id]
        if task_info["status"] == "running":
            # 这里应该实现任务取消逻辑
            task_info["status"] = "cancelled"
            return BaseResponse(
                success=True,
                message="标定任务已取消"
            )
        else:
            return BaseResponse(
                success=False,
                message="只能取消正在运行的任务"
            )
    else:
        return BaseResponse(
            success=False,
            message="标定任务不存在"
        )
```

### 步骤4: 更新主路由文件

更新`api/routes/__init__.py`：

```python
# api/routes/__init__.py
"""
路由模块统一导出
"""

from .case_routes import router as case_router
from .simulation_routes import router as simulation_router
from .analysis_routes import router as analysis_router
from .template_routes import router as template_router
from .calibration_routes import router as calibration_router  # 🆕 新增

# 注册所有路由
routers = [
    case_router,
    simulation_router,
    analysis_router,
    template_router,
    calibration_router  # 🆕 新增
]
```

### 步骤5: 创建标定请求模型

在`api/models/requests/`下创建`calibration_requests.py`：

```python
# api/models/requests/calibration_requests.py
"""
标定相关请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class TrafficScenario(str, Enum):
    """交通场景枚举"""
    HIGH_TRAFFIC = "high_traffic"      # 高流量拥堵场景
    LOW_TRAFFIC = "low_traffic"        # 低流量畅通场景
    MIXED_TRAFFIC = "mixed_traffic"    # 混合交通场景

class OutputConfig(BaseModel):
    """输出配置"""
    summary: bool = Field(default=True, description="是否输出summary文件")
    tripinfo: bool = Field(default=True, description="是否输出tripinfo文件")
    vehroute: bool = Field(default=False, description="是否输出vehroute文件")
    queue: bool = Field(default=False, description="是否输出queue文件")

class CalibrationRequest(BaseModel):
    """标定请求模型"""
    case_id: str = Field(..., description="案例ID")
    scenario: TrafficScenario = Field(default=TrafficScenario.MIXED_TRAFFIC, 
                                    description="交通场景")
    
    # 仿真配置
    network_file: str = Field(..., description="网络文件路径")
    taz_file: str = Field(..., description="TAZ文件路径")
    simulation_duration: int = Field(default=7200, description="仿真时长（秒）")
    output_config: OutputConfig = Field(default=OutputConfig(), description="输出配置")
    
    # 标定配置
    initial_samples: int = Field(default=100, description="初始采样数量")
    max_generations: int = Field(default=100, description="最大优化代数")
    
    # 自定义参数范围（可选）
    custom_parameter_ranges: Optional[Dict[str, Any]] = Field(
        default=None, description="自定义参数范围"
    )
    
    # 高级配置（可选）
    parallel_workers: int = Field(default=4, description="并行工作进程数")
    convergence_threshold: float = Field(default=0.01, description="收敛阈值")
    
    class Config:
        schema_extra = {
            "example": {
                "case_id": "case_001",
                "scenario": "mixed_traffic",
                "network_file": "templates/network_files/sichuan202503v5.net.xml",
                "taz_file": "templates/taz_files/TAZ_5_validated.add.xml",
                "simulation_duration": 7200,
                "initial_samples": 100,
                "max_generations": 100,
                "parallel_workers": 4
            }
        }
```

## 🔄 集成后的使用流程

### 1. 用户操作流程

```
1. 创建案例 → 2. 配置仿真参数 → 3. 运行仿真 → 4. 选择分析类型
                                                           ↓
5. 精度分析 ← 6. 机理分析 ← 7. 性能分析 ← 8. 🆕 参数标定
```

### 2. API调用示例

#### 2.1 创建标定任务

```bash
POST /api/v1/calibration/create
Content-Type: application/json

{
    "case_id": "case_001",
    "scenario": "high_traffic",
    "network_file": "templates/network_files/sichuan202503v5.net.xml",
    "taz_file": "templates/taz_files/TAZ_5_validated.add.xml",
    "simulation_duration": 7200,
    "initial_samples": 100,
    "max_generations": 100
}
```

#### 2.2 查询任务状态

```bash
GET /api/v1/calibration/status/calibration_case_001_20241201_143022
```

#### 2.3 获取标定结果

```bash
GET /api/v1/calibration/results/case_001
```

### 3. 前端集成

#### 3.1 在分析类型选择中添加标定选项

```javascript
// 分析类型配置
const analysisTypes = [
    { id: 'accuracy', name: '精度分析', icon: 'chart-line' },
    { id: 'mechanism', name: '机理分析', icon: 'cogs' },
    { id: 'performance', name: '性能分析', icon: 'tachometer-alt' },
    { id: 'calibration', name: '参数标定', icon: 'sliders-h' }  // 🆕 新增
];
```

#### 3.2 标定配置界面

```javascript
// 标定配置组件
const CalibrationConfig = ({ caseId, onStart }) => {
    const [config, setConfig] = useState({
        scenario: 'mixed_traffic',
        initial_samples: 100,
        max_generations: 100,
        parallel_workers: 4
    });
    
    const handleStart = async () => {
        const response = await fetch('/api/v1/calibration/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: caseId, ...config })
        });
        
        const result = await response.json();
        if (result.success) {
            onStart(result.data.task_id);
        }
    };
    
    return (
        <div className="calibration-config">
            <h3>参数标定配置</h3>
            {/* 配置表单 */}
            <button onClick={handleStart}>开始标定</button>
        </div>
    );
};
```

## 🧪 测试策略

### 1. 单元测试

```python
# tests/test_calibration_analysis.py
import pytest
from shared.analysis_tools.calibration_analysis import CalibrationAnalysis

def test_calibration_analysis_initialization():
    """测试标定分析模块初始化"""
    config = {
        "parameter_ranges": {...},
        "optimization_config": {...},
        "simulation_config": {...}
    }
    
    analysis = CalibrationAnalysis("test_case", config)
    assert analysis.analysis_type == "calibration"
    assert analysis.case_id == "test_case"

def test_calibration_config_validation():
    """测试配置验证"""
    config = {"missing_field": "value"}
    
    with pytest.raises(ValueError, match="缺少必需的配置字段"):
        analysis = CalibrationAnalysis("test_case", config)
        analysis._validate_config()
```

### 2. 集成测试

```python
# tests/integration/test_calibration_integration.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_calibration_api_integration():
    """测试标定API集成"""
    # 1. 创建标定任务
    response = client.post("/api/v1/calibration/create", json={
        "case_id": "test_case",
        "scenario": "mixed_traffic",
        "network_file": "test.net.xml",
        "taz_file": "test.add.xml"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "task_id" in data["data"]
    
    # 2. 查询任务状态
    task_id = data["data"]["task_id"]
    response = client.get(f"/api/v1/calibration/status/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["status"] in ["running", "completed", "failed"]
```

## 📊 性能监控

### 1. 关键指标

- **标定任务执行时间**: 从创建到完成的耗时
- **仿真成功率**: 成功执行的仿真数量占比
- **优化收敛速度**: 达到收敛条件所需的代数
- **资源利用率**: CPU和内存使用情况

### 2. 监控实现

```python
# 在calibration_service中添加性能监控
import time
import psutil

class CalibrationService:
    def __init__(self):
        self.performance_metrics = {}
    
    async def _run_calibration_background(self, task_id: str, ...):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            # 执行标定...
            
            # 记录性能指标
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            self.performance_metrics[task_id] = {
                "execution_time": end_time - start_time,
                "memory_usage": end_memory - start_memory,
                "cpu_usage": psutil.cpu_percent(interval=1)
            }
            
        except Exception as e:
            # 记录失败指标...
```

## 🚀 部署注意事项

### 1. 依赖管理

确保在`requirements.txt`中添加标定功能所需的依赖：

```txt
# 标定功能依赖
xgboost>=1.7.0
scikit-learn>=1.1.0
numpy>=1.21.0
pandas>=1.3.0
```

### 2. 配置管理

- 标定配置文件放在`templates/calibration/`目录下
- 通过环境变量控制标定功能的开关
- 支持不同环境的配置参数

### 3. 资源管理

- 设置并行仿真数量的上限
- 监控系统资源使用情况
- 实现任务队列和优先级管理

## 📋 集成检查清单

- [ ] 标定分析模块集成到`shared/analysis_tools/`
- [ ] 标定服务创建并集成到`api/services/`
- [ ] 标定路由创建并注册到主应用
- [ ] 请求和响应模型定义完成
- [ ] 前端界面集成标定功能
- [ ] 单元测试和集成测试完成
- [ ] 性能监控和日志记录实现
- [ ] 文档更新完成
- [ ] 代码审查通过
- [ ] 部署到测试环境验证

通过以上集成步骤，标定功能将完美地融入到现有的系统架构中，为用户提供完整的仿真分析解决方案。
