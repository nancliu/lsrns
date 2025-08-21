"""
OD数据处理与仿真系统 - 服务层模块

这个模块将原有的services.py按业务领域重构为多个专门的服务文件:
- data_service.py: OD数据处理服务 
- simulation_service.py: 仿真运行服务
- accuracy_service.py: 精度分析服务
- mechanism_service.py: 机理分析服务  
- performance_service.py: 性能分析服务
- base_metadata_service.py: 基础元数据管理服务
- case_service.py: 案例管理服务
- template_service.py: 模板管理服务
- file_service.py: 文件管理服务
"""

# 为了保持向后兼容性，从各个服务模块导入函数
from .data_service import (
    process_od_data_service,
)

from .simulation_service import (
    run_simulation_service,
    get_simulation_progress_service,
    get_case_simulations_service,
    get_simulation_detail_service,
    delete_simulation_service,
)

# 分析服务现在通过独立的服务类提供，不再从旧的analysis_service导入
# 这些函数现在直接在路由中使用各自的服务类

from .case_service import (
    create_case_service,
    list_cases_service,
    get_case_service,
    delete_case_service,
    clone_case_service,
)

from .template_service import (
    get_taz_templates_service,
    get_network_templates_service,
    get_simulation_templates_service,
)

from .file_service import (
    get_folders_service,
)

# 导出所有服务函数，保持原有导入方式不变
__all__ = [
    # 数据处理服务
    "process_od_data_service",
    
    # 仿真服务
    "run_simulation_service",
    "get_simulation_progress_service", 
    "get_case_simulations_service",
    "get_simulation_detail_service",
    "delete_simulation_service",
    
    # 分析服务（现在通过独立的服务类在路由中直接使用）
    
    # 案例管理服务
    "create_case_service",
    "list_cases_service",
    "get_case_service", 
    "delete_case_service",
    "clone_case_service",
    
    # 模板服务
    "get_taz_templates_service",
    "get_network_templates_service",
    "get_simulation_templates_service",
    
    # 文件服务
    "get_folders_service",
]
