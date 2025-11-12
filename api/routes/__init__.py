"""
OD数据处理与仿真系统 - API路由模块

按业务领域重构的路由结构:
- data_routes.py: 数据处理相关路由
- simulation_routes.py: 仿真管理相关路由
- case_routes.py: 案例管理相关路由
- analysis_routes.py: 分析相关路由
- template_routes.py: 模板管理相关路由
- middleware.py: 公共中间件和异常处理
"""

from fastapi import APIRouter
from .data_routes import router as data_router
from .simulation_routes import router as simulation_router
from .case_routes import router as case_router
from .analysis_routes import router as analysis_router
from .template_routes import router as template_router
from .file_routes import router as file_router
from .control_strategy_routes import router as control_router
from .control_strategy_instance_routes import router as control_instance_router
from .control_plan_routes import router as control_plan_router
from .batch_optimization_routes import router as batch_optimization_router
from .scenario_routes import router as scenario_router

# 创建主路由器
router = APIRouter()

# 注册各个子路由
router.include_router(data_router, prefix="/data", tags=["数据处理"])
router.include_router(simulation_router, prefix="/simulation", tags=["仿真管理"])
router.include_router(case_router, prefix="/case", tags=["案例管理"])
router.include_router(scenario_router, tags=["场景管理"])  # 场景路由已包含/scenario前缀
router.include_router(analysis_router, prefix="/analysis", tags=["结果分析"])
router.include_router(template_router, prefix="/template", tags=["模板管理"])
router.include_router(file_router, prefix="/file", tags=["文件管理"])
router.include_router(control_router, prefix="/control", tags=["交通管控"])
router.include_router(control_instance_router, tags=["策略实例管理"])
router.include_router(control_plan_router, tags=["方案管理"])
router.include_router(batch_optimization_router, tags=["批量优化仿真"])

# 为了保持向后兼容，同时注册到根路径
# 数据处理API
router.include_router(data_router, tags=["数据处理 (兼容)"])
# 仿真API
router.include_router(simulation_router, tags=["仿真管理 (兼容)"])
# 案例管理API
router.include_router(case_router, tags=["案例管理 (兼容)"])
# 分析API
router.include_router(analysis_router, tags=["结果分析 (兼容)"])
# 模板API
router.include_router(template_router, tags=["模板管理 (兼容)"])
# 文件API
router.include_router(file_router, tags=["文件管理 (兼容)"])

# 健康检查（API作用域）
@router.get("/health", tags=["系统"])
async def api_health_check():
    return {"status": "healthy", "scope": "api"}
