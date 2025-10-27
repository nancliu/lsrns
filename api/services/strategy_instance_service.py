"""
Strategy Instance Service

Business logic for strategy instance management (Phase 1C - CRUD operations).
Handles template loading, parameter validation, edge enrichment, and file operations.

Note: This is separate from control_strategy_service.py (Phase 1B - edge selector).
"""

import logging
import socket
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from shared.control_tools import (
    validate_strategy_parameters,
    generate_strategy_id,
    save_strategy,
    load_strategy,
    delete_strategy as file_delete_strategy,
    load_index,
    regenerate_index,
)
from api.models.requests.strategy_requests import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
)
from api.models.responses.strategy_responses import (
    StrategyCreateResponse,
    StrategyDetailResponse,
    StrategyListResponse,
    StrategyListItem,
    StrategyMetadata,
    EdgeDetail,
)

logger = logging.getLogger(__name__)


class StrategyInstanceService:
    """
    Service for managing control strategy instances (Phase 1C).

    Handles CRUD operations, template integration, parameter validation,
    and edge enrichment for strategy instances.
    """

    def __init__(self, strategies_dir: str = "control_data/strategies"):
        """
        Initialize service.

        Args:
            strategies_dir: Directory path for strategy JSON files
        """
        self.strategies_dir = strategies_dir
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensure strategies directory exists."""
        Path(self.strategies_dir).mkdir(parents=True, exist_ok=True)

    def _get_system_identifier(self) -> str:
        """
        Get system identifier for created_by field.

        Returns:
            Hostname or "system" as fallback
        """
        try:
            return socket.gethostname()
        except Exception:
            return "system"

    def _load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Load template from Phase 1A.

        Args:
            template_id: Template identifier

        Returns:
            Template data dict if found, None otherwise
        """
        try:
            # Import here to avoid circular dependency
            from shared.control_tools.template_loader import get_template_by_id
            from pathlib import Path

            # Get templates directory
            project_root = Path(__file__).parent.parent.parent
            templates_dir = project_root / "templates" / "control_strategies"

            # Load template using Phase 1A loader
            template_obj = get_template_by_id(template_id, templates_dir)

            if template_obj is None:
                logger.warning(f"Template not found: {template_id}")
                return None

            # Convert ControlTemplate object to dict for internal use
            template_dict = {
                "template_id": template_obj.template_id,
                "template_name": template_obj.template_name,
                "strategy_type": (
                    template_obj.strategy_type.value
                    if hasattr(template_obj.strategy_type, "value")
                    else template_obj.strategy_type
                ),
                "parameters_schema": [
                    {
                        "parameter_name": param.parameter_name,
                        "parameter_type": (
                            param.parameter_type
                            if isinstance(param.parameter_type, str)
                            else param.parameter_type.value
                        ),
                        "description": param.description,
                        "unit": param.unit,
                        "default_value": param.default_value,
                        "required": param.required,
                        "min_value": param.min_value,
                        "max_value": param.max_value,
                        "allowed_values": param.allowed_values,
                        "pattern": getattr(param, "pattern", None),
                        "min_items": getattr(param, "min_items", None),
                    }
                    for param in template_obj.parameters_schema
                ],
            }

            logger.info(f"Loaded template: {template_id} ({template_obj.template_name})")
            return template_dict

        except Exception as e:
            logger.error(f"Error loading template {template_id}: {e}")
            return None

    def _enrich_edges(self, edge_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Enrich edge IDs with details from database (Phase 1B integration).

        Performance optimized: Uses simplified query with connection pooling
        for ~25x faster response (~5s → ~0.2s).

        Args:
            edge_ids: List of edge identifiers

        Returns:
            List of edge detail dictionaries
        """
        if not edge_ids:
            return []

        try:
            # Import optimized edge query function (uses connection pool + simple SQL)
            from shared.data_access.edge_query import get_edges_by_ids_simple

            # Query database for edge details (optimized version)
            edge_infos = get_edges_by_ids_simple(edge_ids)

            # Convert EdgeInfo objects to dictionaries
            enriched_edges = []
            for edge_info in edge_infos:
                # Format stake range
                stake_range = None
                if edge_info.start_stake is not None and edge_info.end_stake is not None:
                    stake_range = f"K{edge_info.start_stake:.2f}-K{edge_info.end_stake:.2f}"

                enriched_edges.append(
                    {
                        "edge_id": edge_info.edge_id,
                        "route_code": edge_info.route_code,
                        "stake_range": stake_range,
                        "length": edge_info.length,
                    }
                )

            logger.info(f"Enriched {len(enriched_edges)} edges from database (optimized query)")
            return enriched_edges

        except Exception as e:
            logger.error(f"Error enriching edges: {e}. Returning minimal edge data.")
            # Fallback to minimal edge data if database query fails
            return [
                {"edge_id": edge_id, "route_code": None, "stake_range": None, "length": None}
                for edge_id in edge_ids
            ]

    def create_strategy(self, request: StrategyCreateRequest) -> StrategyCreateResponse:
        """
        Create a new strategy instance.

        Args:
            request: Strategy creation request

        Returns:
            StrategyCreateResponse with strategy_id and message

        Raises:
            ValueError: If template not found or validation fails
        """
        # Load template (Phase 1A integration)
        template = self._load_template(request.template_id)

        # Raise error if template not found
        if template is None:
            raise ValueError(f"Template not found: {request.template_id}")

        # Extract template metadata
        template_name = template.get("template_name", "Unknown Template")
        strategy_type = template.get("strategy_type", "VSS")
        parameters_schema = template.get("parameters_schema", [])

        # Validate parameters against template schema
        if parameters_schema:
            # Use the new v2.0 validator with correct parameters
            validation_result = validate_strategy_parameters(
                parameters_schema=parameters_schema,
                parameters=request.parameters,
                strategy_type=strategy_type
            )
            
            if not validation_result.valid:
                error_messages = [e["message"] for e in validation_result.errors]
                raise ValueError(f"Parameter validation failed: {'; '.join(error_messages)}")

        # Generate unique strategy ID
        strategy_id = generate_strategy_id()

        # Get system identifier
        created_by = self._get_system_identifier()
        current_time = datetime.now(timezone.utc).isoformat()

        # Build strategy data
        strategy = {
            "strategy_id": strategy_id,
            "strategy_name": request.strategy_name,
            "template_id": request.template_id,
            "template_name": template_name,
            "strategy_type": strategy_type,
            "parameters": request.parameters,
            "affected_edges": request.affected_edges,
            "metadata": {
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": created_by,
                "version": 1,
            },
        }

        # Save strategy to file
        success = save_strategy(strategy, self.strategies_dir)

        if not success:
            raise RuntimeError(f"Failed to save strategy {strategy_id}")

        # Log creation (FR-039)
        logger.info(
            f"Strategy created successfully",
            extra={
                "strategy_id": strategy_id,
                "strategy_name": request.strategy_name,
                "created_by": created_by,
                "template_id": request.template_id,
                "edges_count": len(request.affected_edges),
            },
        )

        return StrategyCreateResponse(
            strategy_id=strategy_id, message="Strategy created successfully"
        )

    def get_strategy(self, strategy_id: str) -> Optional[StrategyDetailResponse]:
        """
        Get strategy details by ID.

        Supports both schema types:
        - API-created: affected_edges, parameters, metadata at top level
        - Demo files: configured_params, created_at/updated_at at top level

        Args:
            strategy_id: Strategy identifier

        Returns:
            StrategyDetailResponse if found, None otherwise
        """
        import time

        start_time = time.time()

        # Load strategy from file
        strategy = load_strategy(strategy_id, self.strategies_dir)

        if strategy is None:
            logger.warning(f"Strategy not found: {strategy_id}")
            return None

        strategy_type = strategy.get("strategy_type", "")

        # Extract edge IDs based on schema type
        if "affected_edges" in strategy:
            # API-created schema
            edge_ids = strategy.get("affected_edges", [])
        elif "configured_params" in strategy:
            # Demo schema
            configured_params = strategy.get("configured_params", {})
            if strategy_type == "TEC":
                # TEC uses entrance_edge (single edge)
                entrance_edge = configured_params.get("entrance_edge", "")
                edge_ids = [entrance_edge] if entrance_edge else []
            else:
                # VSS/DHS use affected_edges array
                edge_ids = configured_params.get("affected_edges", [])
        else:
            edge_ids = []

        # Enrich edge data
        enriched_edges = self._enrich_edges(edge_ids)

        # Convert to EdgeDetail models
        edge_details = [
            EdgeDetail(
                edge_id=edge["edge_id"],
                route_code=edge.get("route_code"),
                stake_range=edge.get("stake_range"),
                length=edge.get("length"),
            )
            for edge in enriched_edges
        ]

        # Extract parameters based on schema type
        if "parameters" in strategy:
            # API-created schema
            parameters = strategy.get("parameters", {})
        elif "configured_params" in strategy:
            # Demo schema - use configured_params as parameters
            parameters = strategy.get("configured_params", {})
        else:
            parameters = {}

        # Extract template_name
        template_name = strategy.get("template_name", "")
        if not template_name:
            # Try to load from template
            template = self._load_template(strategy.get("template_id", ""))
            if template:
                template_name = template.get("template_name", strategy.get("template_id", ""))
            else:
                template_name = strategy.get("template_id", "")

        # Build metadata based on schema type
        if "metadata" in strategy:
            # API-created schema
            metadata_dict = strategy.get("metadata", {})
            metadata = StrategyMetadata(
                created_at=metadata_dict.get("created_at", ""),
                updated_at=metadata_dict.get("updated_at", ""),
                created_by=metadata_dict.get("created_by", ""),
                version=metadata_dict.get("version", 1),
            )
        else:
            # Demo schema
            metadata = StrategyMetadata(
                created_at=strategy.get("created_at", ""),
                updated_at=strategy.get("updated_at", ""),
                created_by=strategy.get("created_by", "system"),
                version=1,
            )

        # Performance monitoring (FR-041)
        duration = time.time() - start_time
        if duration > 2.0:  # Warn if detail load >2s
            logger.warning(
                f"Slow detail operation: {duration:.2f}s (threshold: 2.0s)",
                extra={
                    "operation": "get_strategy",
                    "strategy_id": strategy_id,
                    "duration_seconds": duration,
                    "edges_count": len(edge_ids),
                    "threshold_seconds": 2.0,
                },
            )

        logger.info(
            "Strategy detail query",
            extra={
                "strategy_id": strategy_id,
                "edges_count": len(edge_ids),
                "duration_seconds": round(duration, 3),
            },
        )

        # Build response
        return StrategyDetailResponse(
            strategy_id=strategy["strategy_id"],
            strategy_name=strategy["strategy_name"],
            template_id=strategy["template_id"],
            template_name=template_name,
            strategy_type=strategy_type,
            parameters=parameters,
            affected_edges=edge_details,
            metadata=metadata,
            is_used_in_plans=False,  # Phase 2 integration point (FR-044)
        )

    def list_strategies(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        strategy_type: Optional[str] = None,
    ) -> StrategyListResponse:
        """
        List strategies with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            search: Optional search string for strategy name
            strategy_type: Optional filter by strategy type

        Returns:
            StrategyListResponse with paginated results
        """
        import time

        start_time = time.time()

        # Load index
        index = load_index(self.strategies_dir)
        all_strategies = index.get("strategies", [])

        # Apply filters
        filtered = all_strategies

        if search:
            search_lower = search.lower()
            filtered = [s for s in filtered if search_lower in s["strategy_name"].lower()]

        if strategy_type:
            filtered = [s for s in filtered if s["strategy_type"] == strategy_type]

        total_count = len(filtered)

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = filtered[start_idx:end_idx]

        # Convert to StrategyListItem models
        items = [StrategyListItem(**item) for item in paginated]

        # Performance monitoring (FR-041)
        duration = time.time() - start_time
        if duration > 1.0:  # Warn if list load >1s
            logger.warning(
                f"Slow list operation: {duration:.2f}s (threshold: 1.0s)",
                extra={
                    "operation": "list_strategies",
                    "duration_seconds": duration,
                    "total_count": total_count,
                    "threshold_seconds": 1.0,
                },
            )

        logger.info(
            "Strategy list query",
            extra={
                "result_count": len(items),
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "search": search,
                "strategy_type": strategy_type,
                "duration_seconds": round(duration, 3),
            },
        )

        return StrategyListResponse(
            strategies=items, total_count=total_count, page=page, page_size=page_size
        )

    def update_strategy(
        self, strategy_id: str, request: StrategyUpdateRequest
    ) -> Optional[StrategyDetailResponse]:
        """
        Update an existing strategy.

        Supports both schema types:
        - API-created: affected_edges, parameters, metadata at top level
        - Demo files: configured_params, created_at/updated_at at top level

        Args:
            strategy_id: Strategy identifier
            request: Update request with optional fields

        Returns:
            Updated StrategyDetailResponse if successful, None if not found

        Raises:
            ValueError: If validation fails or concurrency conflict
        """
        # Load existing strategy
        strategy = load_strategy(strategy_id, self.strategies_dir)

        if strategy is None:
            return None

        # Determine schema type
        is_demo_schema = "configured_params" in strategy
        strategy_type = strategy.get("strategy_type", "")

        # Check optimistic concurrency control
        if "metadata" in strategy:
            current_updated_at = strategy["metadata"]["updated_at"]
        else:
            current_updated_at = strategy.get("updated_at", "")

        if current_updated_at != request.original_updated_at:
            raise ValueError(
                f"Concurrency conflict: strategy was modified. "
                f"Expected updated_at={request.original_updated_at}, "
                f"but current is {current_updated_at}"
            )

        # Update fields if provided
        if request.strategy_name is not None:
            strategy["strategy_name"] = request.strategy_name

        if request.parameters is not None:
            # TODO: Validate updated parameters against template schema
            if is_demo_schema:
                # Update configured_params for demo schema
                strategy["configured_params"] = request.parameters
            else:
                # Update parameters for API schema
                strategy["parameters"] = request.parameters

        if request.affected_edges is not None:
            if is_demo_schema:
                # For demo schema, update the appropriate field
                if strategy_type == "TEC":
                    # TEC uses entrance_edge (single edge)
                    if request.affected_edges:
                        strategy["configured_params"]["entrance_edge"] = request.affected_edges[0]
                    else:
                        strategy["configured_params"]["entrance_edge"] = ""
                else:
                    # VSS/DHS use affected_edges array
                    strategy["configured_params"]["affected_edges"] = request.affected_edges
            else:
                # API schema uses affected_edges directly
                strategy["affected_edges"] = request.affected_edges

        # Update metadata/timestamps
        current_time = datetime.now(timezone.utc).isoformat()

        if "metadata" in strategy:
            # API schema
            strategy["metadata"]["updated_at"] = current_time
            old_version = strategy["metadata"]["version"]
            strategy["metadata"]["version"] = old_version + 1
        else:
            # Demo schema
            strategy["updated_at"] = current_time
            old_version = 1  # Demo files don't have versions

        # Save updated strategy
        success = save_strategy(strategy, self.strategies_dir)

        if not success:
            raise RuntimeError(f"Failed to save updated strategy {strategy_id}")

        # Log update (FR-039)
        logger.info(
            f"Strategy updated successfully",
            extra={
                "strategy_id": strategy_id,
                "version_change": f"v{old_version}→v{old_version + 1}",
            },
        )

        # Return updated strategy details
        return self.get_strategy(strategy_id)

    def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.

        Args:
            strategy_id: Strategy identifier

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If strategy is used in plans (Phase 2 integration)
        """
        # Check if strategy exists
        strategy = load_strategy(strategy_id, self.strategies_dir)

        if strategy is None:
            return False

        # TODO: Phase 2 integration - check if used in plans (FR-018)
        # if is_used_in_plans(strategy_id):
        #     raise ValueError(f"Cannot delete strategy - used in plans")

        # Delete strategy file
        success = file_delete_strategy(strategy_id, self.strategies_dir)

        if success:
            # Log deletion (FR-020)
            logger.warning(
                f"Strategy deleted",
                extra={
                    "strategy_id": strategy_id,
                    "strategy_name": strategy.get("strategy_name", ""),
                    "deleted_by": self._get_system_identifier(),
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        return success

    def _generate_copy_id(self, source_id: str) -> str:
        """
        Generate a new strategy ID for copying with intelligent naming.

        Rules:
        - Random IDs (strat_*): Generate new random ID
        - Semantic IDs (strategy_*): Add _copy suffix with counter

        Args:
            source_id: Source strategy ID

        Returns:
            New unique strategy ID

        Examples:
            >>> _generate_copy_id("strat_20251025114442_afa65b")
            "strat_20251026150530_abc123"  # New random ID

            >>> _generate_copy_id("strategy_real_vss_g4202_001")
            "strategy_real_vss_g4202_001_copy"

            >>> _generate_copy_id("strategy_real_vss_g4202_001_copy")
            "strategy_real_vss_g4202_001_copy_2"
        """
        import re

        # Rule 1: Random ID pattern - generate new random ID
        if source_id.startswith("strat_"):
            return generate_strategy_id()

        # Rule 2: Semantic ID pattern - add _copy suffix with counter
        base_id = source_id
        counter = 1

        # Check for existing _copy suffix pattern
        match = re.match(r"(.+?)(?:_copy(?:_(\d+))?)?$", source_id)
        if match:
            base_id = match.group(1)
            if match.group(2):
                # Already has _copy_N suffix
                counter = int(match.group(2)) + 1
            elif "_copy" in source_id:
                # Has _copy but no number
                counter = 2

        # Generate new ID with counter, checking for uniqueness
        max_attempts = 100
        for _ in range(max_attempts):
            if counter == 1:
                new_id = f"{base_id}_copy"
            else:
                new_id = f"{base_id}_copy_{counter}"

            # Check if ID already exists
            if load_strategy(new_id, self.strategies_dir) is None:
                return new_id

            counter += 1

        # Fallback to random ID if unable to find unique semantic ID
        logger.warning(
            f"Unable to generate unique semantic copy ID after {max_attempts} attempts, "
            f"falling back to random ID"
        )
        return generate_strategy_id()

    def copy_strategy(self, strategy_id: str, new_name: Optional[str] = None) -> StrategyCreateResponse:
        """
        Copy an existing strategy with a new ID and name.

        Args:
            strategy_id: Strategy identifier to copy
            new_name: Optional new name (defaults to "[Copy] Original Name")

        Returns:
            StrategyCreateResponse with new strategy_id

        Raises:
            ValueError: If source strategy not found
        """
        # Load source strategy
        source_strategy = load_strategy(strategy_id, self.strategies_dir)

        if source_strategy is None:
            raise ValueError(f"Source strategy not found: {strategy_id}")

        # Determine schema type
        is_demo_schema = "configured_params" in source_strategy
        strategy_type = source_strategy.get("strategy_type", "")

        # Generate new strategy ID with intelligent naming
        new_strategy_id = self._generate_copy_id(strategy_id)

        # Determine new name
        if new_name is None:
            original_name = source_strategy.get("strategy_name", "Unnamed Strategy")
            new_name = f"[复制] {original_name}"

        # Get system identifier and current time
        created_by = self._get_system_identifier()
        current_time = datetime.now(timezone.utc).isoformat()

        # Build copied strategy
        if is_demo_schema:
            # Demo schema
            copied_strategy = {
                "strategy_id": new_strategy_id,
                "strategy_name": new_name,
                "description": source_strategy.get("description", ""),
                "template_id": source_strategy.get("template_id", ""),
                "strategy_type": strategy_type,
                "configured_params": source_strategy.get("configured_params", {}).copy(),
                "tags": source_strategy.get("tags", []).copy(),
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": created_by,
                "status": "active",
            }
        else:
            # API schema
            template_name = source_strategy.get("template_name", "")
            copied_strategy = {
                "strategy_id": new_strategy_id,
                "strategy_name": new_name,
                "template_id": source_strategy.get("template_id", ""),
                "template_name": template_name,
                "strategy_type": strategy_type,
                "parameters": source_strategy.get("parameters", {}).copy(),
                "affected_edges": source_strategy.get("affected_edges", []).copy(),
                "metadata": {
                    "created_at": current_time,
                    "updated_at": current_time,
                    "created_by": created_by,
                    "version": 1,
                },
            }

        # Save copied strategy
        success = save_strategy(copied_strategy, self.strategies_dir)

        if not success:
            raise RuntimeError(f"Failed to save copied strategy")

        # Log copy operation
        logger.info(
            f"Strategy copied successfully",
            extra={
                "source_strategy_id": strategy_id,
                "new_strategy_id": new_strategy_id,
                "new_name": new_name,
                "created_by": created_by,
            },
        )

        return StrategyCreateResponse(
            strategy_id=new_strategy_id,
            message=f"Strategy copied successfully from {strategy_id}"
        )

    def reindex_strategies(self) -> Dict[str, Any]:
        """
        Regenerate strategies index (admin operation).

        Returns:
            Dict with count and duration
        """
        import time

        start_time = time.time()
        count = regenerate_index(self.strategies_dir)
        duration = time.time() - start_time

        # Log regeneration (FR-039, FR-104)
        logger.warning(
            f"Index regenerated",
            extra={
                "event": "index_regeneration",
                "file_count": count,
                "duration_seconds": round(duration, 2),
            },
        )

        return {
            "count": count,
            "duration_seconds": round(duration, 2),
            "message": f"Index regenerated with {count} strategies",
        }
