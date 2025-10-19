"""
控制策略服务 (Phase 0 stub)
"""

from typing import List, Dict, Any


class ControlStrategyService:
    """控制策略业务逻辑服务 (Phase 0: empty methods)"""

    async def list_templates(self) -> List[Dict[str, Any]]:
        """获取模板列表 (Phase 0: empty list)"""
        return []

    async def list_strategies(self) -> Dict[str, Any]:
        """获取策略列表 (Phase 0: empty list)"""
        return {"total": 0, "items": []}

    async def list_plans(self) -> List[Dict[str, Any]]:
        """获取方案列表 (Phase 0: empty list)"""
        return []

    async def list_batch_simulations(self) -> List[Dict[str, Any]]:
        """获取批量仿真任务列表 (Phase 0: empty list)"""
        return []
