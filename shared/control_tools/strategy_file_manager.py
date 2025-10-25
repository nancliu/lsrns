"""
Strategy File Manager

Handles file I/O operations for strategy instances including:
- Strategy ID generation
- File save/load operations with atomic writes
- Index management for fast queries
- Index regeneration for recovery
"""

import json
import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def generate_strategy_id() -> str:
    """
    Generate unique strategy ID with format: strat_{timestamp}_{random}.

    Returns:
        Strategy ID string (e.g., "strat_20251021143025_a3f7b9")

    Examples:
        >>> strategy_id = generate_strategy_id()
        >>> strategy_id.startswith("strat_")
        True
        >>> len(strategy_id.split("_"))
        3
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3)  # 6 hex characters
    return f"strat_{timestamp}_{random_suffix}"


def save_strategy(strategy: Dict[str, Any], strategies_dir: str) -> bool:
    """
    Save strategy to JSON file with atomic write operation.

    Uses temp file + rename pattern for atomic writes.
    Updates strategies index after successful save.

    Args:
        strategy: Strategy data dictionary
        strategies_dir: Path to strategies directory

    Returns:
        True if save successful, False otherwise

    Examples:
        >>> strategy = {"strategy_id": "strat_20251021143025_a3f7b9", ...}
        >>> save_strategy(strategy, "control_data/strategies")
        True
    """
    try:
        strategies_path = Path(strategies_dir)
        strategies_path.mkdir(parents=True, exist_ok=True)

        strategy_id = strategy["strategy_id"]
        final_path = strategies_path / f"{strategy_id}.json"
        temp_path = strategies_path / f"{strategy_id}.tmp"

        # Write to temp file first
        temp_path.write_text(json.dumps(strategy, ensure_ascii=False, indent=2), encoding="utf-8")

        # Atomic rename
        temp_path.replace(final_path)

        # Update index
        _update_index_after_save(strategy, strategies_dir)

        logger.info(f"Strategy saved successfully: {strategy_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to save strategy: {e}", exc_info=True)
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        return False


def load_strategy(strategy_id: str, strategies_dir: str) -> Optional[Dict[str, Any]]:
    """
    Load strategy from JSON file.

    Args:
        strategy_id: Strategy ID to load
        strategies_dir: Path to strategies directory

    Returns:
        Strategy data dictionary if found and valid, None otherwise

    Examples:
        >>> strategy = load_strategy("strat_20251021143025_a3f7b9", "control_data/strategies")
        >>> strategy["strategy_id"] if strategy else None
        'strat_20251021143025_a3f7b9'
    """
    try:
        strategies_path = Path(strategies_dir)
        file_path = strategies_path / f"{strategy_id}.json"

        if not file_path.exists():
            logger.warning(f"Strategy file not found: {strategy_id}")
            return None

        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Corrupted JSON file for strategy {strategy_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load strategy {strategy_id}: {e}", exc_info=True)
        return None


def delete_strategy(strategy_id: str, strategies_dir: str) -> bool:
    """
    Delete strategy file and update index.

    Args:
        strategy_id: Strategy ID to delete
        strategies_dir: Path to strategies directory

    Returns:
        True if deletion successful, False if strategy not found

    Examples:
        >>> delete_strategy("strat_20251021143025_a3f7b9", "control_data/strategies")
        True
    """
    try:
        strategies_path = Path(strategies_dir)
        file_path = strategies_path / f"{strategy_id}.json"

        if not file_path.exists():
            logger.warning(f"Strategy file not found for deletion: {strategy_id}")
            return False

        # Delete file
        file_path.unlink()

        # Update index
        _update_index_after_delete(strategy_id, strategies_dir)

        logger.info(f"Strategy deleted successfully: {strategy_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete strategy {strategy_id}: {e}", exc_info=True)
        return False


def load_index(strategies_dir: str) -> Dict[str, Any]:
    """
    Load strategies index from JSON file.

    Creates empty index if file doesn't exist.

    Args:
        strategies_dir: Path to strategies directory

    Returns:
        Index data dictionary with structure:
            {
                "strategies": List[Dict],
                "total_count": int,
                "last_updated": str (ISO8601)
            }

    Examples:
        >>> index = load_index("control_data/strategies")
        >>> "strategies" in index
        True
        >>> "total_count" in index
        True
    """
    try:
        strategies_path = Path(strategies_dir)
        strategies_path.mkdir(parents=True, exist_ok=True)

        index_path = strategies_path / "strategies_index.json"

        if not index_path.exists():
            # Create empty index
            empty_index = {
                "strategies": [],
                "total_count": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            save_index(empty_index, strategies_dir)
            return empty_index

        data = json.loads(index_path.read_text(encoding="utf-8"))
        return data

    except Exception as e:
        logger.error(f"Failed to load index: {e}", exc_info=True)
        # Return empty index on error
        return {
            "strategies": [],
            "total_count": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


def save_index(index_data: Dict[str, Any], strategies_dir: str) -> bool:
    """
    Save strategies index to JSON file.

    Args:
        index_data: Index data dictionary
        strategies_dir: Path to strategies directory

    Returns:
        True if save successful, False otherwise

    Examples:
        >>> index = {"strategies": [], "total_count": 0, "last_updated": "..."}
        >>> save_index(index, "control_data/strategies")
        True
    """
    try:
        strategies_path = Path(strategies_dir)
        strategies_path.mkdir(parents=True, exist_ok=True)

        index_path = strategies_path / "strategies_index.json"

        index_path.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to save index: {e}", exc_info=True)
        return False


def regenerate_index(strategies_dir: str, templates_dir: Optional[str] = None) -> int:
    """
    Regenerate strategies index by scanning all strategy files.

    Used for index recovery when index file is corrupted or missing.

    Args:
        strategies_dir: Path to strategies directory
        templates_dir: Optional path to templates directory for template name lookup

    Returns:
        Number of strategies indexed

    Examples:
        >>> count = regenerate_index("control_data/strategies")
        >>> count >= 0
        True
    """
    try:
        from shared.control_tools.template_loader import get_template_by_id

        strategies_path = Path(strategies_dir)
        strategies_path.mkdir(parents=True, exist_ok=True)

        # Determine templates directory
        if templates_dir is None:
            # Default to control_data/templates relative to strategies_dir
            templates_path = strategies_path.parent / "templates"
        else:
            templates_path = Path(templates_dir)

        strategies = []

        # Scan all strategy JSON files (both strat_* and strategy_* patterns)
        pattern_files = list(strategies_path.glob("strat_*.json")) + list(
            strategies_path.glob("strategy_*.json")
        )

        for file_path in pattern_files:
            try:
                strategy = json.loads(file_path.read_text(encoding="utf-8"))

                # Look up template name
                template_id = strategy.get("template_id", "")
                template_name = ""
                if template_id and templates_path.exists():
                    try:
                        template = get_template_by_id(template_id, templates_path)
                        template_name = template.template_name if template else template_id
                    except Exception:
                        template_name = template_id
                else:
                    template_name = template_id

                # Calculate edges count based on strategy type
                configured_params = strategy.get("configured_params", {})
                strategy_type = strategy.get("strategy_type", "")

                if strategy_type == "TEC":
                    # TEC uses entrance_edge (single edge)
                    entrance_edge = configured_params.get("entrance_edge", "")
                    edges_count = 1 if entrance_edge else 0
                else:
                    # VSS and DHS use affected_edges (array)
                    affected_edges = configured_params.get("affected_edges", [])
                    edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0

                strategies.append(
                    {
                        "strategy_id": strategy["strategy_id"],
                        "strategy_name": strategy["strategy_name"],
                        "strategy_type": strategy["strategy_type"],
                        "template_id": template_id,
                        "template_name": template_name,
                        "edges_count": edges_count,
                        "created_at": strategy.get("created_at", ""),
                        "updated_at": strategy.get("updated_at", ""),
                        "file_path": str(file_path.relative_to(strategies_path.parent.parent)),
                    }
                )

            except Exception as e:
                logger.warning(f"Skipping corrupted strategy file {file_path.name}: {e}")
                continue

        # Sort by updated_at (most recent first)
        strategies.sort(key=lambda x: x["updated_at"], reverse=True)

        # Build index
        index = {
            "strategies": strategies,
            "total_count": len(strategies),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        save_index(index, strategies_dir)

        logger.info(f"Index regenerated with {len(strategies)} strategies")
        return len(strategies)

    except Exception as e:
        logger.error(f"Failed to regenerate index: {e}", exc_info=True)
        return 0


def _update_index_after_save(strategy: Dict[str, Any], strategies_dir: str) -> None:
    """
    Update index after saving a strategy (create or update).

    Internal helper function.
    """
    try:
        from shared.control_tools.template_loader import get_template_by_id
        from pathlib import Path

        index = load_index(strategies_dir)

        strategy_id = strategy["strategy_id"]
        strategy_type = strategy.get("strategy_type", "")

        # Check if strategy already exists in index (update scenario)
        existing_idx = next(
            (i for i, s in enumerate(index["strategies"]) if s["strategy_id"] == strategy_id), None
        )

        # Look up template name
        template_id = strategy.get("template_id", "")
        template_name = strategy.get("template_name", "")
        if not template_name and template_id:
            # Try to load from template files
            strategies_path = Path(strategies_dir)
            templates_path = strategies_path.parent / "templates"
            if not templates_path.exists():
                templates_path = Path(__file__).parent.parent.parent / "templates" / "control_strategies"
            try:
                template = get_template_by_id(template_id, templates_path)
                template_name = template.template_name if template else template_id
            except Exception:
                template_name = template_id

        # Calculate edges count based on strategy structure
        # Support both schemas: API-created (affected_edges) and demo (configured_params)
        edges_count = 0
        if "affected_edges" in strategy:
            # API-created strategy schema
            affected_edges = strategy.get("affected_edges", [])
            edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0
        elif "configured_params" in strategy:
            # Demo strategy schema
            configured_params = strategy.get("configured_params", {})
            if strategy_type == "TEC":
                entrance_edge = configured_params.get("entrance_edge", "")
                edges_count = 1 if entrance_edge else 0
            else:
                affected_edges = configured_params.get("affected_edges", [])
                edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0

        # Handle both metadata schemas
        if "metadata" in strategy:
            # API-created strategy schema
            created_at = strategy["metadata"]["created_at"]
            updated_at = strategy["metadata"]["updated_at"]
        else:
            # Demo strategy schema
            created_at = strategy.get("created_at", "")
            updated_at = strategy.get("updated_at", "")

        entry = {
            "strategy_id": strategy["strategy_id"],
            "strategy_name": strategy["strategy_name"],
            "strategy_type": strategy_type,
            "template_id": template_id,
            "template_name": template_name,
            "edges_count": edges_count,
            "created_at": created_at,
            "updated_at": updated_at,
            "file_path": f"control_data/strategies/{strategy_id}.json",
        }

        if existing_idx is not None:
            # Update existing entry
            index["strategies"][existing_idx] = entry
        else:
            # Add new entry
            index["strategies"].append(entry)
            index["total_count"] += 1

        # Re-sort by updated_at
        index["strategies"].sort(key=lambda x: x["updated_at"], reverse=True)

        index["last_updated"] = datetime.now(timezone.utc).isoformat()

        save_index(index, strategies_dir)

    except Exception as e:
        logger.error(f"Failed to update index after save: {e}", exc_info=True)


def _update_index_after_delete(strategy_id: str, strategies_dir: str) -> None:
    """
    Update index after deleting a strategy.

    Internal helper function.
    """
    try:
        index = load_index(strategies_dir)

        # Remove strategy from index
        index["strategies"] = [s for s in index["strategies"] if s["strategy_id"] != strategy_id]

        index["total_count"] = len(index["strategies"])
        index["last_updated"] = datetime.now(timezone.utc).isoformat()

        save_index(index, strategies_dir)

    except Exception as e:
        logger.error(f"Failed to update index after delete: {e}", exc_info=True)
