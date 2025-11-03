"""
批量优化仿真路由

提供批量仿真的HTTP API端点
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from api.services.batch_optimization_service import BatchOptimizationService
from api.services.simulation_service import simulation_service
from api.models.control.requests.batch_request import CreateBatchRequest
from api.models.control.responses.batch_response import (
    BatchCreatedResponse,
    BatchProgressResponse,
    BatchResultsResponse,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/control/batch-optimization", tags=["Batch Optimization"])

# 初始化服务
batch_service = BatchOptimizationService()


@router.post("/batch", response_model=BatchCreatedResponse, status_code=201)
async def create_batch(request: CreateBatchRequest):
    """
    创建批量仿真批次 (Phase 1: 支持output_config)

    请求体:
    - case_id: 案例ID（必填）
    - plan_ids: 方案ID列表（必填，系统会自动添加baseline_plan如果缺失）
    - num_seeds: 每个方案的随机种子数量（默认3，范围1-10）
    - base_seed: 起始随机种子值（默认66）
    - output_config: 仿真输出配置（Phase 1新增）
    - output_level: 仿真输出级别（已弃用，保留向后兼容）
    - simulation_config: 仿真配置参数（可选）

    返回:
    - 批次创建信息，包含batch_id、总任务数和output_config

    说明:
    - baseline_plan如果缺失会自动添加
    - 优先使用output_config，如果仅提供output_level则自动映射
    """
    try:
        result = batch_service.create_batch(
            case_id=request.case_id,
            plan_ids=request.plan_ids,
            num_seeds=request.num_seeds,
            base_seed=request.base_seed,
            output_config=request.output_config,
            output_level=request.output_level,
            simulation_config=request.simulation_config
        )
        return result

    except FileNotFoundError as e:
        logger.warning(f"Resource not found creating batch: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"Validation error creating batch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建批次失败: {str(e)}")


@router.post("/batch/{batch_id}/start")
async def start_batch(batch_id: str, background_tasks: BackgroundTasks):
    """
    启动批量仿真

    路径参数:
    - batch_id: 批次ID

    返回:
    - 批次启动确认信息

    说明:
    - 批次将在后台异步执行
    - 使用GET /batch/{batch_id}/progress查询进度
    """
    try:
        # 从batch_id中提取case_id
        # batch_id格式: batch_YYYYMMDD_HHMMSS
        # 需要从batch元数据中读取case_id
        import json
        from pathlib import Path

        # 查找批次目录
        cases_dir = Path("cases")
        batch_metadata_path = None

        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
                if possible_path.exists():
                    batch_metadata_path = possible_path
                    case_id = case_dir.name
                    break

        if not batch_metadata_path:
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 启动批量仿真
        result = await batch_service.start_batch(
            case_id=case_id,
            batch_id=batch_id,
            simulation_service=simulation_service
        )

        return result

    except FileNotFoundError as e:
        logger.warning(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动批次失败: {str(e)}")


@router.get("/batch/{batch_id}/progress", response_model=BatchProgressResponse)
async def get_batch_progress(batch_id: str):
    """
    获取批量仿真进度

    路径参数:
    - batch_id: 批次ID

    返回:
    - 批次进度信息，包含所有任务的状态和预计完成时间
    """
    try:
        # 从batch_id查找case_id（同start_batch）
        import json
        from pathlib import Path

        cases_dir = Path("cases")
        case_id = None

        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
                if possible_path.exists():
                    case_id = case_dir.name
                    break

        if not case_id:
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        result = batch_service.get_batch_progress(case_id, batch_id)
        return result

    except FileNotFoundError as e:
        logger.warning(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting batch progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取批次进度失败: {str(e)}")


@router.get("/batch/{batch_id}/results", response_model=BatchResultsResponse)
async def get_batch_results(
    batch_id: str,
    include_time_series: bool = False
):
    """
    获取批量仿真结果

    路径参数:
    - batch_id: 批次ID

    查询参数:
    - include_time_series: 是否包含时序数据（在网车辆峰值曲线等），默认False

    返回:
    - 批次结果汇总，包含所有方案的仿真指标和聚合统计
    - 如果include_time_series=true，还包含时序数据用于可视化

    说明:
    - 只能查询已完成的批次
    - 返回每个方案的多次随机仿真结果和统计分析
    - 时序数据包含running_vehicles等指标的均值、标准差、最大值、最小值
    """
    try:
        # 从batch_id查找case_id
        import json
        from pathlib import Path

        cases_dir = Path("cases")
        case_id = None

        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
                if possible_path.exists():
                    case_id = case_dir.name
                    break

        if not case_id:
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        result = batch_service.get_batch_results(
            case_id,
            batch_id
        )
        return result

    except FileNotFoundError as e:
        logger.warning(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"Batch not completed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting batch results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取批次结果失败: {str(e)}")


@router.post("/batch/{batch_id}/cancel")
async def cancel_batch(batch_id: str):
    """
    取消运行中的批量仿真

    路径参数:
    - batch_id: 批次ID

    返回:
    - 取消确认信息

    说明:
    - 取消所有pending和running任务
    - 杀死运行中的SUMO进程
    - 保留仿真目录，之后可以重新启动
    """
    try:
        # 从batch_id查找case_id
        import json
        from pathlib import Path

        cases_dir = Path("cases")
        case_id = None

        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
                if possible_path.exists():
                    case_id = case_dir.name
                    break

        if not case_id:
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 取消批次
        result = batch_service.cancel_batch(case_id, batch_id)
        return result

    except FileNotFoundError as e:
        logger.warning(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"Cannot cancel batch {batch_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取消批次失败: {str(e)}")


@router.delete("/batch/{batch_id}")
async def delete_batch(batch_id: str):
    """
    删除批量仿真批次

    路径参数:
    - batch_id: 批次ID

    返回:
    - 删除确认信息

    说明:
    - 删除批次目录和所有相关文件
    - 如果批次正在运行，会先进行取消
    """
    try:
        # 从batch_id查找case_id
        import json
        from pathlib import Path

        cases_dir = Path("cases")
        case_id = None

        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
                if possible_path.exists():
                    case_id = case_dir.name
                    break

        if not case_id:
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 先取消批次（如果正在运行）
        try:
            batch_service.cancel_batch(case_id, batch_id)
        except (ValueError, FileNotFoundError) as e:
            # 如果批次已完成或不存在，继续删除
            logger.info(f"Cannot cancel batch {batch_id}: {str(e)}")
        except Exception as e:
            # 其他错误也继续删除
            logger.warning(f"Error cancelling batch {batch_id}: {str(e)}", exc_info=True)

        # 删除批次
        result = batch_service.delete_batch(case_id, batch_id)
        return result

    except FileNotFoundError as e:
        logger.warning(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除批次失败: {str(e)}")


@router.get("/batches")
async def list_batches(
    case_id: str,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """
    列表查询批次

    查询参数:
    - case_id: 案例ID（必填）
    - status: 筛选状态（可选，支持: pending, running, completed, cancelled, failed, archived）
    - page: 页码（默认1）
    - limit: 每页数量（默认20）

    返回:
    - 批次列表和分页信息
    """
    try:
        result = batch_service.list_batches(case_id, status, page, limit)
        return result
    except Exception as e:
        logger.error(f"Error listing batches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取批次列表失败: {str(e)}")


@router.get("/cases/{case_id}/duration", tags=["Configuration"])
async def get_case_duration(case_id: str):
    """
    获取案例仿真时长 (Revision 3: 新增)

    从case元数据中读取time_range，计算实际仿真时长

    路径参数:
    - case_id: 案例ID

    返回:
    - use_default: 是否使用默认时长（总是True）
    - start_time: 开始时间
    - end_time: 结束时间
    - duration_hours: 小时数
    - duration_minutes: 分钟数
    - total_minutes: 总分钟数
    - display_text: 格式化的显示文本 (例如: "1小时30分钟 (08:00 - 09:30)")

    说明:
    - 前端在case选择时调用此端点获取案例时长
    - 时长为只读，基于case元数据的time_range计算得出
    """
    try:
        result = batch_service.get_case_duration(case_id)
        return result
    except FileNotFoundError as e:
        logger.warning(f"Case not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning(f"Invalid case duration data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting case duration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取案例时长失败: {str(e)}")


@router.get("/templates/vehicle-types", tags=["Configuration"])
async def list_vehicle_templates():
    """
    获取可用的车辆模板列表 (Revision 2: 新增)

    返回:
    - templates: 可用模板列表，包含filename、display_name和path
    - total: 总模板数

    说明:
    - 动态扫描templates/config_templates/vehicle_templates/目录
    - 查找所有vehicle_types*.json文件
    - 前端可用此列表动态填充车辆模板下拉菜单
    """
    try:
        result = batch_service.list_vehicle_templates()
        return result
    except Exception as e:
        logger.error(f"Error listing vehicle templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取车辆模板列表失败: {str(e)}")


@router.get("/batches/{batch_id}/detail")
async def get_batch_detail(batch_id: str):
    """
    获取批次详细信息

    路径参数:
    - batch_id: 批次ID

    返回:
    - 批次详细信息，包含所有任务和统计摘要
    """
    try:
        # 从batch_id查找case_id
        from pathlib import Path

        cases_dir = Path("cases")
        case_id = None

        for case_dir in cases_dir.iterdir():
            if case_dir.is_dir():
                possible_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
                if possible_path.exists():
                    case_id = case_dir.name
                    break

        if not case_id:
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        result = batch_service.get_batch_detail(case_id, batch_id)
        return result

    except FileNotFoundError as e:
        logger.warning(f"Batch not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting batch detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取批次详情失败: {str(e)}")
