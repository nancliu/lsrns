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
        temp_path.write_text(
            json.dumps(strategy, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

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
                "last_updated": datetime.now(timezone.utc).isoformat()
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
            "last_updated": datetime.now(timezone.utc).isoformat()
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
            json.dumps(index_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to save index: {e}", exc_info=True)
        return False


def regenerate_index(strategies_dir: str) -> int:
    """
    Regenerate strategies index by scanning all strategy files.

    Used for index recovery when index file is corrupted or missing.

    Args:
        strategies_dir: Path to strategies directory

    Returns:
        Number of strategies indexed

    Examples:
        >>> count = regenerate_index("control_data/strategies")
        >>> count >= 0
        True
    """
    try:
        strategies_path = Path(strategies_dir)
        strategies_path.mkdir(parents=True, exist_ok=True)

        strategies = []

        # Scan all strategy JSON files
        for file_path in strategies_path.glob("strat_*.json"):
            try:
                strategy = json.loads(file_path.read_text(encoding="utf-8"))

                strategies.append({
                    "strategy_id": strategy["strategy_id"],
                    "strategy_name": strategy["strategy_name"],
                    "strategy_type": strategy["strategy_type"],
                    "template_id": strategy["template_id"],
                    "template_name": strategy["template_name"],
                    "edges_count": len(strategy.get("affected_edges", [])),
                    "created_at": strategy["metadata"]["created_at"],
                    "updated_at": strategy["metadata"]["updated_at"],
                    "file_path": str(file_path.relative_to(strategies_path.parent.parent))
                })

            except Exception as e:
                logger.warning(f"Skipping corrupted strategy file {file_path.name}: {e}")
                continue

        # Sort by updated_at (most recent first)
        strategies.sort(key=lambda x: x["updated_at"], reverse=True)

        # Build index
        index = {
            "strategies": strategies,
            "total_count": len(strategies),
            "last_updated": datetime.now(timezone.utc).isoformat()
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
        index = load_index(strategies_dir)

        strategy_id = strategy["strategy_id"]

        # Check if strategy already exists in index (update scenario)
        existing_idx = next(
            (i for i, s in enumerate(index["strategies"]) if s["strategy_id"] == strategy_id),
            None
        )

        entry = {
            "strategy_id": strategy["strategy_id"],
            "strategy_name": strategy["strategy_name"],
            "strategy_type": strategy["strategy_type"],
            "template_id": strategy["template_id"],
            "template_name": strategy["template_name"],
            "edges_count": len(strategy.get("affected_edges", [])),
            "created_at": strategy["metadata"]["created_at"],
            "updated_at": strategy["metadata"]["updated_at"],
            "file_path": f"control_data/strategies/{strategy_id}.json"
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
        index["strategies"] = [
            s for s in index["strategies"]
            if s["strategy_id"] != strategy_id
        ]

        index["total_count"] = len(index["strategies"])
        index["last_updated"] = datetime.now(timezone.utc).isoformat()

        save_index(index, strategies_dir)

    except Exception as e:
        logger.error(f"Failed to update index after delete: {e}", exc_info=True)
