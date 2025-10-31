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
    创建批量仿真批次

    请求体:
    - case_id: 案例ID（必填）
    - plan_ids: 方案ID列表（必填，系统会自动添加baseline_plan如果缺失）
    - num_seeds: 每个方案的随机种子数量（默认3）
    - base_seed: 起始随机种子值（默认66）
    - simulation_config: 仿真配置参数（可选）

    返回:
    - 批次创建信息，包含batch_id和总任务数
    """
    try:
        result = batch_service.create_batch(
            case_id=request.case_id,
            plan_ids=request.plan_ids,
            num_seeds=request.num_seeds,
            base_seed=request.base_seed,
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
            batch_id,
            include_time_series=include_time_series
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


@router.delete("/batch/{batch_id}")
async def delete_batch(batch_id: str):
    """
    取消或删除批量仿真

    路径参数:
    - batch_id: 批次ID

    返回:
    - 删除确认信息

    说明:
    - 如果批次正在运行，将取消所有pending任务
    - 删除批次目录和所有相关文件
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
        except:
            pass  # 如果取消失败（可能已完成），继续删除

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
