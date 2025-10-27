"""
控制方案管理路由

提供方案管理的HTTP API端点
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from api.services.control_plan_service import ControlPlanService
from api.models.control.requests.plan_request import CreatePlanRequest, UpdatePlanRequest
from api.models.control.responses.plan_response import (
    PlanResponse,
    PlanDetailResponse,
    PlanListResponse,
    PlanValidationResponse,
    PlanPreviewResponse,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/control/plans", tags=["Control Plans"])

# 初始化服务
plan_service = ControlPlanService()


@router.post("/", response_model=PlanResponse, status_code=201)
async def create_plan(request: CreatePlanRequest):
    """
    创建新方案

    请求体:
    - plan_name: 方案名称（必填）
    - description: 方案描述
    - strategy_ids: 策略ID列表（可为空表示基准方案）
    - tags: 标签列表
    - target_scenario: 目标场景
    - expected_effects: 预期效果（键值对）

    返回:
    - 完整的方案信息，包含验证结果
    """
    try:
        plan_data = request.model_dump(exclude_none=True)
        result = plan_service.create_plan(plan_data)
        return result

    except ValueError as e:
        logger.warning(f"Validation error creating plan: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建方案失败: {str(e)}")


@router.get("/", response_model=PlanListResponse)
async def list_plans(
    tags: Optional[str] = Query(None, description="标签过滤（逗号分隔）"),
    target_scenario: Optional[str] = Query(None, description="目标场景过滤"),
    include_baseline: bool = Query(True, description="是否包含基准方案")
):
    """
    列出所有方案

    查询参数:
    - tags: 标签过滤（逗号分隔）
    - target_scenario: 场景过滤（模糊匹配）
    - include_baseline: 是否包含基准方案（默认True）

    返回:
    - 方案列表和总数
    """
    try:
        # 构建过滤条件
        filters = {"include_baseline": include_baseline}

        if tags:
            filters["tags"] = [t.strip() for t in tags.split(",")]

        if target_scenario:
            filters["target_scenario"] = target_scenario

        result = plan_service.list_plans(filters)
        return result

    except Exception as e:
        logger.error(f"Error listing plans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取方案列表失败: {str(e)}")


@router.get("/{plan_id}", response_model=PlanDetailResponse)
async def get_plan(
    plan_id: str,
    include_strategies: bool = Query(True, description="是否包含策略详情")
):
    """
    获取方案详情

    路径参数:
    - plan_id: 方案ID

    查询参数:
    - include_strategies: 是否包含策略详情（默认True）

    返回:
    - 方案完整信息，可选包含策略详情列表
    """
    try:
        result = plan_service.get_plan(plan_id, include_strategies)
        return result

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"方案不存在: {plan_id}")
    except Exception as e:
        logger.error(f"Error getting plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取方案详情失败: {str(e)}")


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, request: UpdatePlanRequest):
    """
    更新方案

    路径参数:
    - plan_id: 方案ID

    请求体（所有字段可选）:
    - plan_name: 方案名称
    - description: 描述
    - strategy_ids: 策略ID列表
    - tags: 标签
    - target_scenario: 目标场景
    - expected_effects: 预期效果

    行为:
    - 如果strategy_ids变化，自动重新生成control.add.xml
    - 更新updated_at时间戳

    返回:
    - 更新后的方案信息
    """
    try:
        updates = request.model_dump(exclude_none=True)

        if not updates:
            raise HTTPException(status_code=400, detail="至少需要提供一个更新字段")

        result = plan_service.update_plan(plan_id, updates)
        return result

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"方案不存在: {plan_id}")
    except ValueError as e:
        logger.warning(f"Validation error updating plan {plan_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新方案失败: {str(e)}")


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str):
    """
    删除方案

    路径参数:
    - plan_id: 方案ID

    限制:
    - 不能删除baseline_plan（基准方案）
    - 删除前会检查是否被批量仿真引用（警告，但允许删除）

    返回:
    - 删除结果
    """
    try:
        result = plan_service.delete_plan(plan_id)
        return result

    except ValueError as e:
        # 尝试删除基准方案
        logger.warning(f"Attempted to delete protected plan: {plan_id}")
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"方案不存在: {plan_id}")
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除方案失败: {str(e)}")


@router.post("/{plan_id}/generate_additional")
async def regenerate_additional(plan_id: str):
    """
    手动重新生成control.add.xml

    路径参数:
    - plan_id: 方案ID

    使用场景:
    - 策略更新后手动触发重新生成
    - 修复损坏的XML文件

    返回:
    - 操作结果
    """
    try:
        result = plan_service.regenerate_plan_xml(plan_id)
        return result

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"方案不存在: {plan_id}")
    except Exception as e:
        logger.error(f"Error regenerating XML for plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新生成XML失败: {str(e)}")


@router.post("/{plan_id}/validate", response_model=PlanValidationResponse)
async def validate_plan(plan_id: str):
    """
    验证方案配置

    路径参数:
    - plan_id: 方案ID

    返回:
    - 验证结果（is_valid始终为True，仅提供警告和建议）
    - 警告列表（空间冲突、时间协调、策略兼容性）
    - 优化建议列表
    """
    try:
        result = plan_service.validate_plan_config(plan_id)
        return result

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"方案不存在: {plan_id}")
    except Exception as e:
        logger.error(f"Error validating plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证方案失败: {str(e)}")


@router.post("/{plan_id}/preview", response_model=PlanPreviewResponse)
async def preview_plan(plan_id: str):
    """
    预览方案效果

    路径参数:
    - plan_id: 方案ID

    返回:
    - 方案摘要（策略数量、类型统计、影响范围、时间范围）
    - 策略详情列表
    - XML内容预览（前500行）
    """
    try:
        result = plan_service.preview_plan(plan_id)
        return result

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"方案不存在: {plan_id}")
    except Exception as e:
        logger.error(f"Error previewing plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览方案失败: {str(e)}")
