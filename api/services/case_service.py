"""
案例管理服务 - 负责案例的CRUD操作和管理
"""

import json
import logging
import shutil
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Any as FileHandle

logger = logging.getLogger(__name__)

# Platform-specific imports for file locking
if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix/Linux
    import fcntl

from ..models import (
    CaseCreationRequest, CaseCloneRequest, CaseMetadata,
    CaseListResponse, CaseStatus, EventScenarioQuickCreateRequest
)
from .base_service import BaseService, MetadataManager, DirectoryManager
from shared.utilities.scenario_case_mapping import ScenarioCaseMapper


class CaseService(BaseService):
    """案例管理服务类"""
    
    async def create_case(self, request: CaseCreationRequest) -> Dict[str, Any]:
        """创建新案例"""
        try:
            # 生成案例ID
            case_id = self.generate_unique_id("case")
            
            # 创建案例目录结构
            case_dir = DirectoryManager.create_case_structure(case_id)
            
            # 创建标准子目录结构
            self._create_standard_directories(case_dir)
            
            # 创建元数据
            metadata = self._create_initial_metadata(case_id, request)
            
            # 保存元数据
            MetadataManager.save_case_metadata(case_dir, metadata)
            
            return {
                "case_id": case_id,
                "case_dir": str(case_dir),
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"案例创建失败: {str(e)}")
    
    def _create_standard_directories(self, case_dir: Path) -> None:
        """创建标准的案例目录结构 - 调用shared层功能"""
        from shared.utilities.file_utils import DirectoryManager
        
        # 使用shared层的标准案例结构创建功能
        DirectoryManager.create_case_structure(case_dir.name)
    
    def _create_initial_metadata(self, case_id: str, request: CaseCreationRequest) -> Dict[str, Any]:
        """创建初始元数据"""
        return {
            "case_id": case_id,
            "case_name": request.case_name or case_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "time_range": request.time_range,
            "config": request.config,
            "status": CaseStatus.CREATED.value,
            "description": request.description,
            "statistics": {},
            "files": {}
        }

    def _extract_event_id_from_scenario(self, scenario_id: str) -> str:
        """
        Extract event ID from scenario ID.

        Format: scenario_{event_id}_{strategy}
        Example: scenario_10814_vss → 10814

        Args:
            scenario_id: The scenario ID in format scenario_{event_id}_{strategy}

        Returns:
            The extracted event ID

        Raises:
            ValueError: If scenario_id format is invalid
        """
        parts = scenario_id.split('_')
        if len(parts) < 3 or parts[0] != 'scenario':
            raise ValueError(
                f"Invalid scenario_id format: {scenario_id}. "
                f"Expected format: scenario_{{event_id}}_{{strategy}}"
            )

        return parts[1]

    def _validate_case_config(self, case_path: Path) -> bool:
        """
        Validate that case has complete config files.

        Args:
            case_path: Path to case directory

        Returns:
            True if config is complete, False otherwise

        Checks:
            - config/ directory exists
            - Network file (.net.xml) exists
            - At least one OD/route file exists
        """
        config_dir = case_path / "config"

        if not config_dir.exists():
            logger.warning(f"Config directory missing: {config_dir}")
            return False

        # Check for network file
        net_files = list(config_dir.glob("*.net.xml"))
        if not net_files:
            logger.warning(f"No network file found in: {config_dir}")
            return False

        # Check for OD/route files (various patterns)
        od_files = []
        od_files.extend(list(config_dir.glob("*.rou.xml")))  # Route files
        od_files.extend(list(config_dir.glob("*.od.xml")))   # OD files
        if not od_files:
            logger.warning(f"No OD/route files found in: {config_dir}")
            return False

        logger.debug(f"✓ Config validation passed for {case_path.name}")
        logger.debug(f"  Network files: {[f.name for f in net_files]}")
        logger.debug(f"  OD/Route files: {[f.name for f in od_files]}")

        return True

    def _acquire_case_lock(self, lock_file_path: Path) -> Any:
        """
        Acquire an exclusive lock on the case lock file.

        Args:
            lock_file_path: Path to the lock file

        Returns:
            File handle (to be passed to _release_case_lock)
        """
        # Create lock file if it doesn't exist
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open lock file for writing
        lock_handle = open(lock_file_path, 'w')

        # Acquire exclusive lock (platform-specific)
        if os.name == 'nt':  # Windows
            try:
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
                logger.debug(f"✓ Lock acquired: {lock_file_path.name}")
            except IOError:
                # Lock already held, wait and retry
                logger.debug(f"⏳ Waiting for lock: {lock_file_path.name}")
                time.sleep(0.5)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
                logger.debug(f"✓ Lock acquired after waiting: {lock_file_path.name}")
        else:  # Unix/Linux
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.debug(f"✓ Lock acquired: {lock_file_path.name}")
            except IOError:
                # Lock already held, wait for exclusive access
                logger.debug(f"⏳ Waiting for lock: {lock_file_path.name}")
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                logger.debug(f"✓ Lock acquired after waiting: {lock_file_path.name}")

        return lock_handle

    def _release_case_lock(self, lock_handle: Any, lock_file_path: Path) -> None:
        """
        Release the case lock and clean up lock file.

        Args:
            lock_handle: File handle returned by _acquire_case_lock
            lock_file_path: Path to the lock file
        """
        try:
            # Release lock (platform-specific)
            if os.name == 'nt':  # Windows
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:  # Unix/Linux
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

            # Close file handle
            lock_handle.close()

            # Remove lock file
            if lock_file_path.exists():
                lock_file_path.unlink()

            logger.debug(f"✓ Lock released: {lock_file_path.name}")
        except Exception as e:
            logger.warning(f"⚠️  Error releasing lock {lock_file_path.name}: {e}")

    def _get_or_create_event_case(
        self,
        event_id: str,
        event_type: str,
        network_file: str,
        od_file: str,
        taz_file: Optional[str],
        time_range: Dict[str, str],
        description: Optional[str] = None
    ) -> Tuple[Path, bool, Dict[str, Any]]:
        """
        Get existing event case or create new one.

        This implements the core logic for event-based case reuse:
        1. Check if case_event_{event_id} exists
        2. If exists and has complete config → reuse
        3. If not exists or config incomplete → create new case with full config

        Args:
            event_id: Event identifier
            event_type: Event type folder (e.g., '01_accident')
            network_file: Network file path
            od_file: OD/routes file path
            taz_file: TAZ file path (optional)
            time_range: Event time range
            description: Case description (optional)

        Returns:
            Tuple of:
            - case_path: Path to case directory
            - is_new_case: True if newly created, False if reused
            - case_metadata: Case metadata dictionary

        Example:
            First call (scenario_10814_vss):
                returns (cases/case_event_10814, True, {...})
            Second call (scenario_10814_tec):
                returns (cases/case_event_10814, False, {...})
        """
        case_id = f"case_event_{event_id}"
        case_path = self.cases_dir / case_id
        metadata_file = case_path / "metadata.json"

        # Check if case exists with valid and complete config
        if case_path.exists() and metadata_file.exists():
            # Validate config completeness
            if self._validate_case_config(case_path):
                logger.info(f"✓ Reusing existing event case: {case_id}")
                logger.info(f"  - Config directory: {case_path / 'config'}")
                logger.info(f"  - OD data already generated")
                logger.info(f"  - Config validation: PASSED")

                # Load existing metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    case_metadata = json.load(f)

                return case_path, False, case_metadata
            else:
                logger.warning(f"⚠️  Existing case {case_id} has incomplete config, recreating...")
                # Fall through to create new case

        if True:  # Replaced else with if True to maintain structure
            logger.info(f"✓ Creating new event case: {case_id}")

            # Create case directory structure
            case_path.mkdir(parents=True, exist_ok=True)
            (case_path / "config").mkdir(exist_ok=True)
            (case_path / "simulations").mkdir(exist_ok=True)

            # Create case metadata
            case_metadata = {
                "case_id": case_id,
                "case_name": f"Event {event_id} Analysis",
                "case_type": "event_based",
                "event_id": event_id,
                "event_type": event_type,
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "version": "2.0",
                "description": description or f"Event-based case for event {event_id}",
                "files": {
                    "network_file": f"config/{Path(network_file).name}",
                    "routes_file": f"config/{Path(od_file).name}",
                    "taz_file": f"config/{Path(taz_file).name}" if taz_file else None,
                    "edgedata_template": "config/edgeData.add.xml"
                },
                "time_range": time_range,
                "scenarios": [],  # Will be populated as scenarios are added
                "simulations": {},  # Will be populated as simulations are created
                "statistics": {
                    "total_scenarios": 0,
                    "total_simulations": 0
                }
            }

            # Save metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(case_metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Event case created: {case_id}")
            logger.info(f"  - Directory: {case_path}")
            logger.info(f"  - Config directory: {case_path / 'config'}")
            logger.info(f"  - Simulations directory: {case_path / 'simulations'}")

            return case_path, True, case_metadata

    def _get_or_create_event_case_with_lock(
        self,
        event_id: str,
        event_type: str,
        network_file: str,
        od_file: str,
        taz_file: Optional[str],
        time_range: Dict[str, str],
        description: Optional[str] = None
    ) -> Tuple[Path, bool, Dict[str, Any]]:
        """
        Thread-safe wrapper for _get_or_create_event_case with file locking.

        This method prevents race conditions when multiple requests try to create
        cases for the same event simultaneously.

        Args:
            Same as _get_or_create_event_case

        Returns:
            Same as _get_or_create_event_case

        Thread Safety:
            Uses file-based locking (msvcrt on Windows, fcntl on Unix).
            Only one thread can create/access a case at a time.
        """
        lock_file_path = self.cases_dir / f".case_event_{event_id}.lock"
        lock_handle = None

        try:
            # Acquire exclusive lock
            lock_handle = self._acquire_case_lock(lock_file_path)

            # Perform case creation/retrieval with lock held
            result = self._get_or_create_event_case(
                event_id=event_id,
                event_type=event_type,
                network_file=network_file,
                od_file=od_file,
                taz_file=taz_file,
                time_range=time_range,
                description=description
            )

            return result

        finally:
            # Always release lock, even if exception occurs
            if lock_handle is not None:
                self._release_case_lock(lock_handle, lock_file_path)

    def _find_event_type_folder(self, scenario_id: str) -> Optional[str]:
        """
        Find the event type folder for a given scenario ID.

        Args:
            scenario_id: The scenario ID

        Returns:
            Event type folder name (e.g., '01_accident'), or None if not found

        Example:
            _find_event_type_folder("scenario_10814_vss")
            → "01_accident"
        """
        scenarios_base = Path("output/scenarios")
        if not scenarios_base.exists():
            logger.warning(f"Scenarios base directory not found: {scenarios_base}")
            return None

        # Search all event type folders
        for event_folder in scenarios_base.iterdir():
            if event_folder.is_dir():
                scenario_path = event_folder / scenario_id
                if scenario_path.exists():
                    return event_folder.name

        logger.warning(f"Event type folder not found for scenario: {scenario_id}")
        return None

    def _find_scenario_add_xml(self, scenario_id: str, event_type: str) -> Optional[Path]:
        """
        Find scenario-specific .add.xml file in output directory.

        Searches for the scenario .add.xml file while excluding:
        - edgeData.add.xml (template file)
        - TAZ_*.add.xml (TAZ files)

        Args:
            scenario_id: The scenario ID
            event_type: Event type folder (e.g., '01_accident')

        Returns:
            Path to scenario .add.xml file, or None if not found

        Example:
            _find_scenario_add_xml("scenario_10814_vss", "01_accident")
            → output/scenarios/01_accident/scenario_10814_vss/scenario_accident_vss_10814.add.xml
        """
        scenario_dir = Path("output/scenarios") / event_type / scenario_id

        if not scenario_dir.exists():
            logger.warning(f"Scenario directory not found: {scenario_dir}")
            return None

        # Find .add.xml files (exclude edgeData and TAZ)
        add_xml_files = [
            f for f in scenario_dir.glob("*.add.xml")
            if f.name not in ["edgeData.add.xml"]
            and not f.name.startswith("TAZ_")
        ]

        if not add_xml_files:
            logger.warning(f"No scenario .add.xml file found in {scenario_dir}")
            return None

        if len(add_xml_files) > 1:
            logger.warning(f"Multiple .add.xml files found in {scenario_dir}, using first: {add_xml_files[0].name}")

        logger.info(f"✓ Found scenario .add.xml file: {add_xml_files[0]}")
        return add_xml_files[0]

    def _create_scenario_simulation(
        self,
        case_path: Path,
        case_metadata: Dict[str, Any],
        scenario_id: str,
        event_id: str,
        event_type: str,
        strategy: str,
        simulation_params: Dict[str, Any]
    ) -> Tuple[str, Path]:
        """
        Create simulation directory for a specific scenario.

        This creates the scenario-specific simulation setup:
        1. Create simulation directory with unique ID
        2. Copy scenario .add.xml file
        3. Generate simulation.sumocfg
        4. Create output directories (edgedata/, e1/)
        5. Create simulation metadata

        Args:
            case_path: Path to case directory
            case_metadata: Case metadata dictionary
            scenario_id: The scenario ID
            event_id: The event ID
            event_type: Event type (e.g., "交通事故")
            strategy: Control strategy type (e.g., "VSS", "TEC", "DHS")
            simulation_params: Simulation parameters

        Returns:
            Tuple of (simulation_id, simulation_path)
        """
        # Generate simulation ID
        simulation_id = f"event_simulation_{scenario_id}"
        sim_dir = case_path / "simulations" / simulation_id

        # Create simulation directory
        sim_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Created simulation directory: {sim_dir}")

        # Find and copy scenario .add.xml
        # Extract event_type folder from scenario output directory structure
        # output/scenarios/01_accident/scenario_10814_vss/
        event_type_folder = None
        scenarios_base = Path("output/scenarios")
        if scenarios_base.exists():
            for event_folder in scenarios_base.iterdir():
                if event_folder.is_dir():
                    scenario_path = event_folder / scenario_id
                    if scenario_path.exists():
                        event_type_folder = event_folder.name
                        break

        scenario_add_xml_path = None
        scenario_add_file = None  # 初始化为 None
        if event_type_folder:
            scenario_add_xml_path = self._find_scenario_add_xml(scenario_id, event_type_folder)

        if scenario_add_xml_path:
            target_path = sim_dir / scenario_add_xml_path.name
            shutil.copy2(scenario_add_xml_path, target_path)
            logger.info(f"✓ Copied scenario .add.xml: {scenario_add_xml_path.name}")

            # ✓ 修复方案：在 simulation metadata 中记录当前场景的 additional_file (不添加到 case_metadata)
            # 将 .add.xml 文件名记录到 simulation_params，后续保存到 simulation metadata
            scenario_add_file = scenario_add_xml_path.name  # 仅文件名（文件已复制到仿真目录）
            logger.info(f"✓ 记录当前场景的 additional_file: {scenario_add_file}")
        else:
            logger.warning(f"⚠️ Scenario .add.xml not found for {scenario_id}")

        # Copy TAZ file to simulation directory (from case config)
        if case_metadata.get("files", {}).get("taz_file"):
            try:
                taz_filename = Path(case_metadata["files"]["taz_file"]).name
                source_taz = case_path / "config" / taz_filename
                target_taz = sim_dir / taz_filename

                if source_taz.exists():
                    shutil.copy2(source_taz, target_taz)
                    logger.info(f"✓ Copied TAZ file to simulation directory: {taz_filename}")
                else:
                    logger.warning(f"⚠️ TAZ file not found in case config: {source_taz}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to copy TAZ file to simulation directory: {e}")

        # Generate sumocfg
        from shared.utilities.sumo_utils import generate_sumocfg_for_simulation

        # 将 scenario_add_file 添加到 simulation_params 中，用于 sumocfg 生成
        if scenario_add_file:
            simulation_params["scenario_additional_file"] = scenario_add_file

        sumocfg_content = generate_sumocfg_for_simulation(
            case_metadata=case_metadata,
            simulation_type=simulation_params.get("simulation_type", "microscopic"),
            simulation_folder=sim_dir,
            case_root=case_path,
            simulation_params=simulation_params
        )

        sumocfg_file = sim_dir / "simulation.sumocfg"
        with open(sumocfg_file, 'w', encoding='utf-8') as f:
            f.write(sumocfg_content)

        logger.info(f"✓ Generated simulation.sumocfg")

        # Create output directories (edgedata and e1)
        output_dirs = ["edgedata", "e1"]
        for dir_name in output_dirs:
            output_dir = sim_dir / dir_name
            output_dir.mkdir(exist_ok=True)
            logger.info(f"✓ Created output directory: {dir_name}/")

        # Create simulation metadata (backward compatible format)
        sim_metadata = {
            "metadata_version": "2.0",
            "simulation_id": simulation_id,
            "case_id": case_metadata["case_id"],
            "status": "ready",
            "created_at": datetime.now().isoformat(),
            "source_scenario": {
                "scenario_id": scenario_id,
                "event_id": event_id,
                "event_type": event_type,
                "control_strategy_type": strategy
            },
            "simulation_params": {
                "duration_hours": simulation_params.get("duration_hours"),
                "random_seed": simulation_params.get("random_seed"),
                "simulation_type": simulation_params.get("simulation_type", "microscopic"),
                "output_config": simulation_params.get("output_config", {})
            },
            "files": {
                "scenario_additional_file": scenario_add_file if scenario_add_xml_path else None
            },
            "config_file": sumocfg_content,  # Full content for backward compatibility
            "config_file_path": "simulation.sumocfg",  # File path (new)
            "sumocfg_generated_at": datetime.now().isoformat()
        }

        sim_metadata_file = sim_dir / "simulation_metadata.json"
        with open(sim_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Simulation metadata saved")

        return simulation_id, sim_dir

    def _update_case_metadata_with_simulation(
        self,
        case_path: Path,
        scenario_id: str,
        simulation_id: str
    ) -> None:
        """
        Update case metadata with new simulation entry.

        Updates:
        1. Add scenario_id to scenarios list (if not already present)
        2. Add simulation entry to simulations dict
        3. Update modified_at timestamp

        Args:
            case_path: Path to case directory
            scenario_id: Scenario identifier
            simulation_id: Simulation identifier
        """
        metadata_file = case_path / "metadata.json"

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Add scenario to list (if not present)
        if scenario_id not in metadata.get("scenarios", []):
            metadata.setdefault("scenarios", []).append(scenario_id)
            logger.info(f"✓ Added scenario {scenario_id} to case scenarios list")

        # Add simulation entry
        metadata.setdefault("simulations", {})[simulation_id] = {
            "created_at": datetime.now().isoformat(),
            "status": "ready",
            "scenario_id": scenario_id
        }
        logger.info(f"✓ Added simulation {simulation_id} to case simulations dict")

        # Update statistics
        metadata.setdefault("statistics", {})
        metadata["statistics"]["total_scenarios"] = len(metadata.get("scenarios", []))
        metadata["statistics"]["total_simulations"] = len(metadata.get("simulations", {}))

        # Update modified timestamp
        metadata["modified_at"] = datetime.now().isoformat()

        # Save updated metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Updated case metadata with simulation {simulation_id}")

    async def _setup_case_config_files(
        self,
        case_path: Path,
        network_file: str,
        taz_file: Optional[str]
    ) -> None:
        """
        Copy network, TAZ, and edgeData template files to case config directory.

        Args:
            case_path: Path to case directory
            network_file: Path to network file
            taz_file: Path to TAZ file (optional)
        """
        config_dir = case_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Copy network file
        if network_file:
            network_source = Path(network_file)
            if network_source.exists():
                network_dest = config_dir / network_source.name
                shutil.copy2(network_source, network_dest)
                logger.info(f"✓ Network file copied: {network_source.name}")
            else:
                logger.warning(f"Network file not found: {network_source}")

        # Copy TAZ file
        if taz_file:
            taz_source = Path(taz_file)
            if taz_source.exists():
                taz_dest = config_dir / taz_source.name
                shutil.copy2(taz_source, taz_dest)
                logger.info(f"✓ TAZ file copied: {taz_source.name}")
            else:
                logger.warning(f"TAZ file not found: {taz_source}")

        # Copy edgeData template file
        try:
            edgedata_template_path = Path("templates/edge_add/edgeData.add.xml")
            if edgedata_template_path.exists():
                edgedata_dest = config_dir / "edgeData.add.xml"
                shutil.copy2(edgedata_template_path, edgedata_dest)
                logger.info(f"✓ EdgeData template file copied: edgeData.add.xml")
            else:
                logger.warning(f"EdgeData template not found: {edgedata_template_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to copy edgeData template: {e}")

    def _save_case_metadata(self, case_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Save case metadata to metadata.json file.

        Args:
            case_path: Path to case directory
            metadata: Metadata dictionary to save
        """
        metadata_file = case_path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Case metadata saved: {metadata_file}")

    def _update_scenario_index(
        self,
        scenario_id: str,
        case_id: str,
        simulation_id: str
    ) -> None:
        """
        Update scenario index with case and simulation linkage.

        Args:
            scenario_id: Scenario identifier
            case_id: Case identifier
            simulation_id: Simulation identifier
        """
        try:
            from shared.utilities.scenario_case_mapping import ScenarioCaseMapper

            mapper = ScenarioCaseMapper()
            mapper.link_scenario_to_case(
                scenario_id=scenario_id,
                case_id=case_id,
                simulation_id=simulation_id
            )
            logger.info(f"✓ Scenario index updated: {scenario_id} → {case_id}")

        except Exception as e:
            logger.warning(f"Failed to update scenario index: {e}")

    def _parse_od_file(self, od_file: str) -> Tuple[str, str]:
        """
        Parse od_file string to extract schema and table name.

        Args:
            od_file: OD file identifier (e.g., "dwd.dwd_od_weekly" or "dwd_od_weekly")

        Returns:
            Tuple of (schema_name, table_name)

        Examples:
            "dwd.dwd_od_weekly" -> ("dwd", "dwd_od_weekly")
            "dwd_od_weekly" -> ("dwd", "dwd_od_weekly")
        """
        if '.' in od_file:
            # Format: "schema.table"
            schema, table = od_file.split('.', 1)
            return schema, table
        else:
            # Format: "table" (assume dwd schema)
            return "dwd", od_file

    def _get_scenario_time_range(self, scenario_id: str) -> Dict[str, str]:
        """
        Get time range from scenario index.

        Args:
            scenario_id: Scenario identifier (e.g., "scenario_10754_tec")

        Returns:
            Dictionary with start_time and end_time

        Raises:
            Exception if scenario not found in index
        """
        try:
            scenario_index_path = Path("output/scenarios/scenario_index.json")
            if not scenario_index_path.exists():
                raise Exception("Scenario index not found")

            with open(scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Match by scenario_dir field (e.g., "scenario_10754_tec")
            for scenario in index_data.get("scenarios", []):
                scenario_dir = scenario.get("files", {}).get("scenario_dir", "")

                if scenario_dir == scenario_id:
                    # Time info is nested in "time" object
                    time_info = scenario.get("time", {})
                    return {
                        "start_time": time_info.get("start_time", ""),
                        "end_time": time_info.get("end_time", "")
                    }

            raise Exception(f"Scenario {scenario_id} not found in index")

        except Exception as e:
            logger.warning(f"Failed to get time range for {scenario_id}: {e}")
            # Return default time range
            return {
                "start_time": "",
                "end_time": ""
            }

    async def list_cases(self, page: int = 1, page_size: int = 10, 
                        status: Optional[CaseStatus] = None, 
                        search: Optional[str] = None) -> CaseListResponse:
        """列出案例"""
        try:
            if not self.cases_dir.exists():
                return CaseListResponse(cases=[], total_count=0, page=page, page_size=page_size)
            
            # 获取所有案例目录
            case_dirs = [d for d in self.cases_dir.iterdir() 
                        if d.is_dir() and d.name.startswith("case_")]
            
            # 加载并过滤案例
            filtered_cases = []
            for case_dir in case_dirs:
                try:
                    metadata = MetadataManager.load_case_metadata(case_dir)
                    
                    # 状态过滤
                    if status and metadata.get("status") != status.value:
                        continue
                    
                    # 搜索过滤
                    if search and not self._matches_search(metadata, search):
                        continue
                    
                    filtered_cases.append(metadata)
                    
                except Exception:
                    continue  # 跳过无效的案例
            
            # 排序
            filtered_cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # 分页
            total_count = len(filtered_cases)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_cases = filtered_cases[start_idx:end_idx]
            
            # 转换为CaseMetadata对象
            case_metadata_list = []
            for case_data in page_cases:
                # Phase 2: 案例来源类型映射
                # 如果metadata中有case_type字段，将其映射为source_type
                if 'case_type' in case_data and 'source_type' not in case_data:
                    case_data['source_type'] = case_data['case_type']

                case_metadata = CaseMetadata(**case_data)
                case_metadata_list.append(case_metadata)
            
            return CaseListResponse(
                cases=case_metadata_list,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            raise Exception(f"获取案例列表失败: {str(e)}")
    
    def _matches_search(self, metadata: Dict[str, Any], search: str) -> bool:
        """检查案例是否匹配搜索条件"""
        search_lower = search.lower()
        case_name = metadata.get("case_name", "").lower()
        description = metadata.get("description", "").lower()
        return search_lower in case_name or search_lower in description
    
    async def get_case(self, case_id: str) -> CaseMetadata:
        """获取案例详情"""
        try:
            case_dir = self.cases_dir / case_id
            if not case_dir.exists():
                raise Exception(f"案例 {case_id} 不存在")

            metadata = MetadataManager.load_case_metadata(case_dir)

            # Phase 2: 案例来源类型映射
            # 如果metadata中有case_type字段，将其映射为source_type
            if 'case_type' in metadata and 'source_type' not in metadata:
                metadata['source_type'] = metadata['case_type']

            return CaseMetadata(**metadata)

        except Exception as e:
            raise Exception(f"获取案例详情失败: {str(e)}")
    
    async def delete_case(self, case_id: str) -> Dict[str, Any]:
        """删除案例"""
        try:
            case_dir = self.cases_dir / case_id
            
            if not case_dir.exists():
                raise Exception(f"案例 {case_id} 不存在")
            
            # 删除案例目录
            shutil.rmtree(case_dir)
            
            return {
                "case_id": case_id,
                "deleted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"删除案例失败: {str(e)}")
    
    async def clone_case(self, case_id: str, request: CaseCloneRequest) -> Dict[str, Any]:
        """克隆案例"""
        try:
            source_case_dir = self.cases_dir / case_id
            if not source_case_dir.exists():
                raise Exception(f"源案例 {case_id} 不存在")
            
            # 生成新案例ID
            new_case_id = self.generate_unique_id("case")
            new_case_dir = self.cases_dir / new_case_id
            
            # 复制案例目录
            shutil.copytree(source_case_dir, new_case_dir)
            
            # 更新元数据
            self._update_cloned_metadata(new_case_dir, new_case_id, case_id, request)
            
            return {
                "original_case_id": case_id,
                "new_case_id": new_case_id,
                "new_case_dir": str(new_case_dir),
                "cloned_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"克隆案例失败: {str(e)}")
    
    def _update_cloned_metadata(self, new_case_dir: Path, new_case_id: str, 
                               original_case_id: str, request: CaseCloneRequest) -> None:
        """更新克隆案例的元数据"""
        try:
            metadata = MetadataManager.load_case_metadata(new_case_dir)
            
            # 获取原案例名称
            original_name = metadata.get('case_name', original_case_id)
            
            metadata.update({
                "case_id": new_case_id,
                "case_name": request.new_case_name or f"{original_name}_copy",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": request.new_description or f"克隆自 {original_case_id}",
                "status": CaseStatus.CREATED.value
            })
            
            MetadataManager.save_case_metadata(new_case_dir, metadata)
            
        except Exception as e:
            print(f"更新克隆案例元数据失败: {e}")

    async def create_case_from_scenario(self, request: EventScenarioQuickCreateRequest) -> Dict[str, Any]:
        """
        从事件场景创建案例 (Task 1.3 - Week 1 Phase 2)

        创建 v2.0 元数据案例:
        - metadata_version: "2.0"
        - source_scenario 字段
        - immutable_fields 和 overridable_fields

        Design Decision Q4: 独立端点 (不修改现有 create_case)

        Args:
            request: 事件场景快速创建请求

        Returns:
            包含新创建案例的信息

        Note: 与 quick_create_case_from_event 不同,此方法创建 v2.0 元数据
        """
        try:
            # 生成案例ID
            case_id = request.case_id or self.generate_unique_id("case")

            # 创建案例目录结构
            case_dir = DirectoryManager.create_case_structure(case_id)

            # 创建标准子目录
            self._create_standard_directories(case_dir)

            # 创建 v2.0 元数据 (事件场景案例)
            metadata = self._create_v2_metadata_from_scenario(case_id, request)

            # 保存元数据
            MetadataManager.save_case_metadata(case_dir, metadata)

            logger.info(f"创建事件场景案例: {case_id}, 场景: {request.scenario_id}")

            return {
                "case_id": case_id,
                "case_dir": str(case_dir),
                "metadata": metadata,
                "metadata_version": "2.0"
            }

        except Exception as e:
            raise Exception(f"从场景创建案例失败: {str(e)}")

    def _create_v2_metadata_from_scenario(
        self,
        case_id: str,
        request: EventScenarioQuickCreateRequest
    ) -> Dict[str, Any]:
        """
        创建 v2.0 元数据 (事件场景案例)

        Args:
            case_id: 案例ID
            request: 事件场景请求

        Returns:
            v2.0 元数据字典

        Structure (design.md):
            - metadata_version: "2.0"
            - source_scenario: {...}
            - immutable_fields: {...}
            - overridable_fields: {...}
        """
        return {
            "metadata_version": "2.0",
            "case_id": case_id,
            "case_name": request.case_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": CaseStatus.CREATED.value,

            # 源场景信息 (AD-12: 场景溯源)
            "source_scenario": {
                "scenario_id": request.scenario_id,
                "event_id": request.event_id,
                "event_type": request.event_type,
                "control_strategy_type": request.strategy,
                "description": f"事件 {request.event_id}, 策略 {request.strategy}"
            },

            # 不可变字段 (AD-8: 配置覆盖策略)
            "immutable_fields": {
                "event_id": request.event_id,
                "event_type": request.event_type,
                "control_strategy_type": request.strategy,
                # 位置和影响道路从场景元数据中提取 (TODO)
            },

            # 可覆盖字段 (AD-8)
            "overridable_fields": {
                "simulation_duration_hours": 2.5,  # 默认值
                "random_seed": None,  # 运行时分配
                "output_config": {
                    "generate_edgedata": True,
                    "generate_summary": True,
                    "generate_tripinfo": True,
                    "generate_vehroute": False
                }
            },

            # 案例配置
            "case_config": {
                "network_file": request.network_file,
                "od_file": request.od_file,
                "taz_file": request.taz_file
            },

            "description": request.description or f"从场景 {request.scenario_id} 创建",
            "statistics": {},
            "files": {}
        }

    async def quick_create_case_from_event(self, request: EventScenarioQuickCreateRequest) -> Dict[str, Any]:
        """
        从事件场景快速创建案例并生成OD文件 (Phase 5.3.3)

        工作流：
        1. 调用QuickCaseCreator创建case结构和元数据
        2. 如果OD文件是数据库表参考，立即启动OD生成（非阻塞）
        3. 更新case状态为"od_generating"
        4. 返回case信息和OD生成状态

        Args:
            request: 包含event scenario和case输入文件信息

        Returns:
            包含新创建case的信息和OD生成状态
        """
        try:
            # 动态导入QuickCaseCreator
            import sys
            from pathlib import Path
            scripts_path = Path(__file__).parent.parent.parent / "scripts"
            if str(scripts_path) not in sys.path:
                sys.path.insert(0, str(scripts_path))

            from initialize_scenario_library import QuickCaseCreator

            # 生成case_id（如果未提供）
            case_id = request.case_id or self.generate_unique_id("case_event")

            # 调用QuickCaseCreator创建case
            # project_root 默认为当前工作目录，case_dir 使用相对路径
            creator = QuickCaseCreator(
                project_root=None,  # 使用默认 Path.cwd()
                case_dir=self.cases_dir
            )

            result = creator.create_case_from_event(
                case_name=request.case_name,
                case_id=case_id,
                event_type=request.event_type,
                strategy=request.strategy,
                scenario_id=request.scenario_id,
                network_file=request.network_file,
                od_file=request.od_file,
                taz_file=request.taz_file,
                description=request.description or f"从事件场景 {request.scenario_id} 创建"
            )

            if not result.get('success'):
                raise Exception(result.get('error', '未知错误'))

            # 为事件场景案例添加源类型标记和初始状态
            import json
            case_path = Path(result.get('case_path'))
            metadata_file = case_path / "metadata.json"
            od_generation_started = False

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata['source_type'] = 'event_scenario'

                    # 如果OD文件是待生成状态，标记为od_generating
                    od_file_metadata = result.get('od_file_metadata', {})
                    if od_file_metadata.get('od_file_status') == 'pending' and \
                       od_file_metadata.get('od_file_type') == 'database':
                        metadata['status'] = 'od_generating'
                        logger.info(f"Case {case_id} marked as od_generating")

                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to update metadata source_type: {e}")

            # 如果OD文件是数据库表参考，立即启动OD生成（后台，非阻塞）
            od_file_metadata = result.get('od_file_metadata', {})
            if od_file_metadata.get('od_file_status') == 'pending' and \
               od_file_metadata.get('od_file_type') == 'database':
                # 启动OD生成任务（后台处理）
                od_generation_started = await self._start_od_generation_async(
                    case_id=case_id,
                    case_path=case_path,
                    od_file_info=od_file_metadata,
                    od_file_info_json=case_path / "config" / "od_file_info.json"
                )
                logger.info(f"OD generation task started for case {case_id}: {od_generation_started}")

            # 注册案例创建到场景元数据 (AD-12: 三层元数据追踪)
            # 在scenario_index.json中添加案例记录，建立scenario->case链接
            # Status is 'od_generating' if OD generation started, otherwise 'created'
            case_status_for_mapping = 'od_generating' if od_generation_started else 'created'
            try:
                mapper = ScenarioCaseMapper()
                mapper.register_case_creation(
                    scenario_id=request.scenario_id,  # e.g., "scenario_10754_no_control"
                    case_id=case_id,
                    case_name=request.case_name,
                    case_status=case_status_for_mapping
                )
                logger.info(f"Registered case {case_id} in scenario {request.scenario_id} with status {case_status_for_mapping}")
            except Exception as e:
                logger.warning(f"Failed to register case in scenario index: {e}")
                # 继续执行，不中断case创建流程

            # 返回成功结果，包含OD文件生成状态
            return {
                "case_id": case_id,
                "case_path": str(case_path),
                "case_name": request.case_name,
                "event_scenario": {
                    "event_type": request.event_type,
                    "strategy": request.strategy,
                    "scenario_id": request.scenario_id
                },
                "od_file_metadata": od_file_metadata,
                "od_file_status": od_file_metadata.get('od_file_status'),
                "od_file_type": od_file_metadata.get('od_file_type'),
                "od_generation_started": od_generation_started,
                "created_at": datetime.now().isoformat(),
                "source_type": "event_scenario",
                "case_status": case_status_for_mapping
            }

        except Exception as e:
            raise Exception(f"从事件场景创建案例失败: {str(e)}")

    async def _start_od_generation_async(
        self,
        case_id: str,
        case_path: Path,
        od_file_info: Dict[str, Any],
        od_file_info_json: Path
    ) -> bool:
        """
        启动异步OD文件生成任务（后台执行，不阻塞）

        Args:
            case_id: 案例ID
            case_path: 案例路径
            od_file_info: OD文件元数据
            od_file_info_json: OD文件信息JSON路径

        Returns:
            是否成功启动生成任务
        """
        try:
            # 从od_file_info.json读取时间范围
            import json
            if od_file_info_json.exists():
                with open(od_file_info_json, 'r', encoding='utf-8') as f:
                    od_info = json.load(f)
                    time_range = od_info.get('time_range', {})
            else:
                logger.warning(f"od_file_info.json not found: {od_file_info_json}")
                return False

            # 准备OD生成请求参数
            from ..models.requests.data_requests import TimeRangeRequest

            start_time = time_range.get('start_time')
            end_time = time_range.get('end_time')
            od_file_ref = od_file_info.get('od_file')

            if not (start_time and end_time and od_file_ref):
                logger.warning(f"Missing time range info for OD generation: {time_range}")
                return False

            # 解析schema.table格式（前端发送格式: dwd.dwd_od_weekly）
            if '.' in od_file_ref:
                schema_name, table_name = od_file_ref.split('.', 1)
            else:
                # 如果没有点，假设是dwd schema
                schema_name = "dwd"
                table_name = od_file_ref

            # 创建OD处理请求（为事件场景提供默认TAZ文件）
            od_request = TimeRangeRequest(
                start_time=start_time,
                end_time=end_time,
                table_name=table_name,
                schemas_name=schema_name,
                net_file=None,
                taz_file="templates/taz_files/TAZ_6.add.xml",  # 使用默认TAZ文件
                interval_minutes=5  # 使用默认5分钟间隔（而不是30分钟）
            )

            # 在后台线程启动OD生成（不阻塞）
            import threading
            od_generation_thread = threading.Thread(
                target=self._run_od_generation_in_background,
                args=(case_id, case_path, od_request, od_file_info_json),
                daemon=True
            )
            od_generation_thread.start()

            logger.info(f"OD generation thread started for case {case_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start OD generation: {e}")
            return False

    def _run_od_generation_in_background(
        self,
        case_id: str,
        case_path: Path,
        od_request,
        od_file_info_json: Path
    ) -> None:
        """
        在后台线程中运行OD生成（非阻塞）

        直接调用ODProcessor而不是data_service，以确保文件生成在正确的case文件夹中

        Args:
            case_id: 案例ID
            case_path: 案例路径
            od_request: OD处理请求
            od_file_info_json: OD文件信息JSON路径
        """
        try:
            import json
            from pathlib import Path
            from shared.data_processors.od_processor import ODProcessor
            from shared.data_access.connection import open_db_connection

            logger.info(f"Starting OD generation for case {case_id}...")

            # 复制TAZ文件到case配置目录
            if od_request.taz_file:
                try:
                    taz_source = Path(od_request.taz_file)
                    if taz_source.exists():
                        taz_dest = case_path / "config" / taz_source.name
                        # 确保目标目录存在
                        taz_dest.parent.mkdir(parents=True, exist_ok=True)
                        # 复制文件
                        import shutil
                        shutil.copy2(str(taz_source), str(taz_dest))
                        logger.info(f"✓ TAZ file copied: {taz_source.name} → {taz_dest}")
                    else:
                        logger.warning(f"TAZ file not found: {taz_source}")
                except Exception as e:
                    logger.error(f"Failed to copy TAZ file: {e}")

            # 验证车型模板
            vehicle_template_path = "templates/config_templates/vehicle_templates/vehicle_types.json"

            # 创建OD处理器
            od_processor = ODProcessor(vehicle_config_path=vehicle_template_path)

            # 构建处理参数（关键：指定output_dir为case的config目录）
            output_dir = str(case_path / "config")
            request_params = {
                "start_time": od_request.start_time,
                "end_time": od_request.end_time,
                "interval_minutes": od_request.interval_minutes,
                "taz_file": od_request.taz_file,
                "net_file": od_request.net_file,
                "schemas_name": od_request.schemas_name,
                "table_name": od_request.table_name,
                "output_dir": output_dir  # 🔑 确保文件输出到正确的case文件夹
            }

            # 获取数据库连接
            db_connection = open_db_connection()
            try:
                # 调用OD处理器处理数据
                result = od_processor.process_od_data(db_connection, request_params)

                if result.get('success'):
                    # 更新od_file_info.json状态为已生成
                    if od_file_info_json.exists():
                        with open(od_file_info_json, 'r', encoding='utf-8') as f:
                            od_info = json.load(f)

                        od_info['od_file_status'] = 'exists'
                        od_info['generated_at'] = datetime.now().isoformat()
                        od_info['od_file'] = result.get('od_file', od_info.get('od_file'))

                        with open(od_file_info_json, 'w', encoding='utf-8') as f:
                            json.dump(od_info, f, indent=2, ensure_ascii=False)

                        logger.info(f"✓ OD file generated for case {case_id}: {od_info['od_file']}")

                    # 更新case元数据状态为created（完成OD生成）
                    metadata_file = case_path / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        if metadata.get('status') == 'od_generating':
                            metadata['status'] = 'created'
                            metadata['od_generated_at'] = datetime.now().isoformat()

                            # Update routes_file with actual generated file
                            if result.get('route_file'):
                                route_file_path = Path(result.get('route_file'))
                                if route_file_path.exists():
                                    metadata.setdefault('files', {})['routes_file'] = f"config/{route_file_path.name}"
                                    logger.info(f"✓ Updated routes_file in metadata: config/{route_file_path.name}")

                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                        logger.info(f"✓ Case {case_id} status updated to created after OD generation")

                        # 生成sumocfg配置文件（OD文件已准备好）
                        # 重新生成所有 simulation 的 sumocfg（确保使用实际的 .rou.xml 文件）
                        try:
                            simulations_dir = case_path / "simulations"
                            if simulations_dir.exists():
                                simulation_dirs = [d for d in simulations_dir.iterdir() if d.is_dir()]
                                logger.info(f"重新生成 {len(simulation_dirs)} 个 simulation 的 sumocfg...")

                                for sim_dir in simulation_dirs:
                                    simulation_id = sim_dir.name
                                    try:
                                        self._generate_sumocfg_after_od_ready(case_id, simulation_id, case_path, metadata)
                                        logger.info(f"✓ sumocfg regenerated for {simulation_id}")
                                    except Exception as sim_error:
                                        logger.error(f"Failed to regenerate sumocfg for {simulation_id}: {sim_error}")
                        except Exception as sumocfg_error:
                            logger.error(f"Failed to regenerate sumocfg after OD completion: {sumocfg_error}")
                else:
                    raise Exception(result.get("error", "OD data processing failed"))

            finally:
                if db_connection:
                    db_connection.close()

        except Exception as e:
            logger.error(f"Error in OD generation thread for case {case_id}: {e}", exc_info=True)

            # 更新失败状态到metadata.json
            try:
                metadata_file = case_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    if metadata.get('status') == 'od_generating':
                        metadata['status'] = 'od_generation_failed'
                        metadata['od_generation_error'] = str(e)
                        metadata['failed_at'] = datetime.now().isoformat()

                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    logger.info(f"✓ Case {case_id} status updated to od_generation_failed after exception")
            except Exception as meta_error:
                logger.error(f"Failed to update metadata after OD generation error: {meta_error}")

    def _find_pending_simulation_id(self, case_path: Path) -> Optional[str]:
        """
        Find the simulation_id created during case creation.

        Args:
            case_path: Path to case directory

        Returns:
            simulation_id if found, None otherwise
        """
        simulations_dir = case_path / "simulations"
        if not simulations_dir.exists():
            return None

        # Find first simulation directory
        sim_dirs = [d for d in simulations_dir.iterdir() if d.is_dir() and d.name.startswith("simulation_")]
        if sim_dirs:
            return sim_dirs[0].name
        return None

    def _generate_sumocfg_after_od_ready(
        self,
        case_id: str,
        simulation_id: str,
        case_path: Path,
        case_metadata: Dict[str, Any]
    ) -> None:
        """
        Generate sumocfg file after OD files are ready.

        This is called after OD generation completes successfully.

        Args:
            case_id: Case ID
            simulation_id: Simulation ID
            case_path: Path to case directory
            case_metadata: Case metadata dictionary
        """
        from shared.utilities.sumo_utils import generate_sumocfg_for_simulation

        try:
            # Read simulation metadata
            sim_dir = case_path / "simulations" / simulation_id
            sim_metadata_file = sim_dir / "simulation_metadata.json"

            if not sim_metadata_file.exists():
                logger.warning(f"Simulation metadata not found: {sim_metadata_file}")
                return

            import json
            with open(sim_metadata_file, 'r', encoding='utf-8') as f:
                sim_metadata = json.load(f)

            # Extract simulation parameters
            sim_params = sim_metadata.get("simulation_params", {})
            output_config = sim_params.get("output_config", {})

            # Generate sumocfg content
            # 检查是否是事件场景（从 sim_metadata 中判断）
            is_event_scenario = "source_scenario" in sim_metadata and sim_metadata["source_scenario"].get("event_id")

            sumocfg_content = generate_sumocfg_for_simulation(
                case_metadata=case_metadata,
                simulation_type=sim_params.get("simulation_type", "microscopic"),
                simulation_folder=sim_dir,
                case_root=case_path,
                simulation_params={
                    "output_edgedata": output_config.get("generate_edgedata", False),
                    "output_summary": output_config.get("generate_summary", True),
                    # 事件场景强制不输出 tripinfo.xml
                    "output_tripinfo": False if is_event_scenario else output_config.get("generate_tripinfo", False),
                    "output_vehroute": output_config.get("generate_vehroute", False),
                    # 如果是事件场景，传递 scenario_additional_file
                    "scenario_additional_file": sim_metadata.get("files", {}).get("scenario_additional_file") if is_event_scenario else None
                }
            )

            # Write sumocfg content to file
            sumocfg_file_path = sim_dir / "simulation.sumocfg"
            with open(sumocfg_file_path, 'w', encoding='utf-8') as f:
                f.write(sumocfg_content)

            logger.info(f"✓ sumocfg file saved: {sumocfg_file_path}")

            # Update simulation metadata with config file content and path
            sim_metadata["config_file"] = sumocfg_content  # Keep content for backward compatibility
            sim_metadata["config_file_path"] = str(sumocfg_file_path)  # Add file path
            sim_metadata["sumocfg_generated_at"] = datetime.now().isoformat()
            sim_metadata["status"] = "ready"

            with open(sim_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ sumocfg metadata updated")

        except Exception as e:
            logger.error(f"Error generating sumocfg: {e}", exc_info=True)
            raise

    async def create_case_with_simulation(self, request: "CreateCaseWithSimulationRequest") -> Dict[str, Any]:
        """
        Create event-based case with scenario simulation.

        NEW: Event-based architecture for efficient case reuse:
        - First scenario from an event creates case_event_{event_id} with full config
        - Subsequent scenarios reuse existing case (70% faster, 65% less disk)
        - Each scenario gets its own simulation directory

        Workflow:
        1. Try to extract event_id from scenario_id (event-based architecture)
        2. Get or create event case (reuse if exists)
        3. If new case: Setup config + trigger OD generation
        4. Create scenario-specific simulation
        5. Update case metadata and scenario index
        6. Return response with is_new_case flag

        Args:
            request: CreateCaseWithSimulationRequest - 包含场景信息、案例参数和仿真配置

        Returns:
            dict with keys: case_id, simulation_id, case_type, is_new_case, od_generation_status
        """
        try:
            # Try event-based architecture first
            try:
                event_id = self._extract_event_id_from_scenario(request.scenario_id)
                logger.info(f"✓ Event-based architecture: event {event_id}, scenario {request.scenario_id}")

                # Get time range from scenario index
                time_range = self._get_scenario_time_range(request.scenario_id)

                # Get or create event case (with file locking for thread safety)
                case_path, is_new_case, case_metadata = self._get_or_create_event_case_with_lock(
                    event_id=event_id,
                    event_type=request.event_type,
                    network_file=request.network_file,
                    od_file=request.od_file,
                    taz_file=request.taz_file,
                    time_range=time_range,
                    description=request.description
                )

                case_id = case_metadata["case_id"]

                # If new case, set up config and trigger OD generation
                if is_new_case:
                    # Copy network and TAZ files to config directory
                    await self._setup_case_config_files(
                        case_path=case_path,
                        network_file=request.network_file,
                        taz_file=request.taz_file
                    )

                    # Mark case as generating OD
                    case_metadata["status"] = "od_generating"
                    self._save_case_metadata(case_path, case_metadata)

                    # Trigger async OD generation
                    # Parse schema and table name from od_file (e.g., "dwd.dwd_od_weekly")
                    schema_name, table_name = self._parse_od_file(request.od_file)

                    import threading
                    thread = threading.Thread(
                        target=self._run_od_generation_in_background,
                        args=(case_id, case_path),
                        kwargs={
                            "od_request": type('obj', (object,), {
                                'start_time': time_range.get("start_time"),
                                'end_time': time_range.get("end_time"),
                                'interval_minutes': 5,  # Default interval: 5 minutes
                                'taz_file': request.taz_file,
                                'net_file': request.network_file,
                                'schemas_name': schema_name,
                                'table_name': table_name,
                                'output_dir': str(case_path / "config")
                            })(),
                            "od_file_info_json": case_path / "od_file_info.json"
                        },
                        daemon=True
                    )
                    thread.start()
                    logger.info(f"✓ OD generation started for new event case {case_id}")
                else:
                    logger.info(f"✓ Reusing existing event case {case_id} (OD data already generated)")

                # Create scenario-specific simulation
                # Map output_config from request to format expected by sumo_utils
                output_config = request.output_config or {}
                simulation_params = {
                    "duration_hours": request.simulation_duration_hours,
                    "random_seed": request.random_seed,
                    "simulation_type": request.simulation_type,
                    "output_config": request.output_config,
                    # Map generate_* keys to output_* keys for sumo_utils
                    "output_edgedata": output_config.get("generate_edgedata", False),
                    # 事件场景强制不输出 tripinfo.xml（仅输出 edgedata）
                    "output_tripinfo": False,
                    "output_vehroute": output_config.get("generate_vehroute", False),
                    "output_netstate": output_config.get("generate_netstate", False),
                    "output_fcd": output_config.get("generate_fcd", False),
                    "output_emission": output_config.get("generate_emission", False),
                }

                simulation_id, sim_dir = self._create_scenario_simulation(
                    case_path=case_path,
                    case_metadata=case_metadata,
                    scenario_id=request.scenario_id,
                    event_id=event_id,
                    event_type=request.event_type,
                    strategy=request.strategy,
                    simulation_params=simulation_params
                )

                # Update case metadata with new simulation
                self._update_case_metadata_with_simulation(
                    case_path=case_path,
                    scenario_id=request.scenario_id,
                    simulation_id=simulation_id
                )

                # Update scenario index
                self._update_scenario_index(
                    scenario_id=request.scenario_id,
                    case_id=case_id,
                    simulation_id=simulation_id
                )

                # Return response
                return {
                    "success": True,
                    "case_id": case_id,
                    "case_type": "event_based",
                    "simulation_id": simulation_id,
                    "simulation_path": str(sim_dir),
                    "is_new_case": is_new_case,
                    "od_generation_status": "in_progress" if is_new_case else "completed",
                    "case_status": "od_generating" if is_new_case else "ready",
                    "simulation_status": "ready",
                    "message": "Case created successfully" if is_new_case else "Simulation added to existing case",
                    "files_created": {
                        "case_metadata": str(case_path / "metadata.json"),
                        "simulation_metadata": str(sim_dir / "simulation_metadata.json")
                    }
                }

            except ValueError as e:
                # Not an event-based scenario, fall back to time-based architecture
                logger.info(f"✓ Time-based architecture (non-event scenario): {e}")

                # Use existing implementation for backward compatibility
                case_id = self.generate_unique_id("case")
                simulation_id = self.generate_unique_id("simulation")
                case_name = request.case_name or f"case_{request.scenario_id}_{case_id.split('_')[-1]}"

                from ..models.requests.case_requests import EventScenarioQuickCreateRequest
                quick_create_request = EventScenarioQuickCreateRequest(
                    case_name=case_name,
                    case_id=case_id,
                    event_type=request.event_type,
                    strategy=request.strategy,
                    scenario_id=request.scenario_id,
                    event_id=request.event_id,
                    network_file=request.network_file,
                    od_file=request.od_file,
                    taz_file=request.taz_file,
                    description=request.description
                )

                result = await self.quick_create_case_from_event(quick_create_request)
                case_path = Path(result.get('case_path'))

                await self._prepare_simulation_for_case(
                    case_id=case_id,
                    simulation_id=simulation_id,
                    case_path=case_path,
                    request=request
                )

                return {
                    "success": True,
                    "case_id": case_id,
                    "case_type": "time_based",
                    "simulation_id": simulation_id,
                    "is_new_case": True,
                    "od_generation_status": "in_progress",
                    "case_status": "od_generating",
                    "simulation_status": "pending",
                    "message": "案例创建成功，OD数据生成中，完成后可开始仿真",
                    "files_created": {
                        "case_metadata": str(case_path / "metadata.json"),
                        "simulation_metadata": str(case_path / "simulations" / simulation_id / "simulation_metadata.json")
                    }
                }

        except Exception as e:
            logger.error(f"Failed to create case with simulation: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create case: {str(e)}")

    async def _prepare_simulation_for_case(self, case_id: str, simulation_id: str, case_path: Path, request: "CreateCaseWithSimulationRequest") -> None:
        """
        准备仿真：生成sumocfg和仿真元数据

        注意：此方法不生成sumocfg，因为需要等待OD文件生成完成。
        sumocfg会在start_simulation时生成。

        Args:
            case_id: 案例ID
            simulation_id: 仿真ID
            case_path: 案例目录路径
            request: CreateCaseWithSimulationRequest - 包含仿真配置
        """
        try:
            import json

            # 创建仿真目录
            sim_dir = case_path / "simulations" / simulation_id
            sim_dir.mkdir(parents=True, exist_ok=True)

            # 构建仿真参数（用于元数据，不立即生成sumocfg）
            sim_params = {
                "duration_hours": request.simulation_duration_hours,
                "random_seed": request.random_seed,
                "simulation_type": request.simulation_type,
                "output_config": request.output_config
            }

            # 创建仿真元数据
            case_metadata_file = case_path / "metadata.json"
            case_metadata = {}
            if case_metadata_file.exists():
                with open(case_metadata_file, 'r', encoding='utf-8') as f:
                    case_metadata = json.load(f)

            sim_metadata = {
                "metadata_version": "2.0",
                "simulation_id": simulation_id,
                "case_id": case_id,
                "status": "pending",
                "created_at": datetime.now().isoformat(),

                # AD-12: 三层元数据追踪 - 保持source_scenario
                "source_scenario": {
                    "scenario_id": request.scenario_id,
                    "event_id": request.event_id,
                    "event_type": request.event_type,
                    "control_strategy_type": request.strategy
                },

                "simulation_params": sim_params
            }

            # 保存仿真元数据
            sim_metadata_file = sim_dir / "simulation_metadata.json"
            with open(sim_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ Simulation metadata created: {sim_metadata_file}")

        except Exception as e:
            logger.error(f"Failed to prepare simulation: {str(e)}")
            raise

    async def create_event_case_batch(self, request) -> Dict[str, Any]:
        """
        批量创建事件案例（完整版）

        完整工作流程:
        1. 创建案例目录结构
        2. 复制网络和TAZ文件到config/目录
        3. 触发OD数据生成（后台异步）
        4. 生成统一的edgeData.add.xml（聚合事件+所有策略边缘）
        5. 为每个场景创建完整的仿真准备:
           - 创建仿真目录和输出子目录
           - 复制场景特定的控制策略.add.xml文件
           - 复制统一的edgeData.add.xml
           - 复制TAZ文件
           - 生成simulation.sumocfg配置文件
           - 创建完整的仿真元数据
        6. 更新案例元数据（记录scenarios和simulations）

        Args:
            request: CreateEventCaseBatchRequest对象

        Returns:
            批量创建结果，包含案例ID、各场景创建状态、edgeData信息
        """
        start_time = time.time()

        try:
            # 1. 生成案例ID
            case_id = self.generate_unique_id("case_event")
            case_name = f"case_{request.event_id}_batch"

            logger.info(f"开始批量创建事件案例: event_id={request.event_id}, scenarios={len(request.scenarios)}")

            # 2. 创建案例目录结构
            case_dir = DirectoryManager.create_case_structure(case_id)
            self._create_standard_directories(case_dir)

            # 3. 复制网络和TAZ文件到config/目录
            await self._setup_case_config_files(
                case_path=case_dir,
                network_file=request.network_file,
                taz_file=request.taz_file
            )
            logger.info(f"✓ 案例配置文件已复制到config/")

            # 4. 收集并复制所有场景的控制策略.add.xml文件到config/目录
            config_dir = case_dir / "config"
            all_strategies_config = []
            strategy_files_copied = []

            for scenario in request.scenarios:
                # 查找场景特定的控制策略.add.xml文件
                event_type_folder = self._find_event_type_folder(scenario.scenario_id)

                if event_type_folder:
                    scenario_add_xml_path = self._find_scenario_add_xml(scenario.scenario_id, event_type_folder)

                    if scenario_add_xml_path:
                        # 复制到config/目录
                        target_path = config_dir / scenario_add_xml_path.name
                        if not target_path.exists():  # 避免重复复制
                            shutil.copy2(scenario_add_xml_path, target_path)
                            strategy_files_copied.append(target_path.name)
                            logger.info(f"✓ 复制策略文件到config/: {scenario_add_xml_path.name}")

                # 收集策略配置（用于生成edgeData）
                if scenario.control_strategy:
                    all_strategies_config.append(scenario.control_strategy)

            logger.info(f"✓ 共复制 {len(strategy_files_copied)} 个策略文件到config/")

            # 5. 生成统一的edgeData.add.xml（聚合事件+所有策略边缘）
            edgedata_info = None
            if len(request.scenarios) > 0:
                # 使用第一个场景的事件位置信息
                event_location = request.scenarios[0].event_location

                from shared.utilities.sumo_utils import generate_edgedata_xml_for_case

                edgedata_result = generate_edgedata_xml_for_case(
                    case_root=case_dir,
                    event_location=event_location,
                    strategies_config=all_strategies_config,
                    network_file=request.network_file,
                    event_method="radius_2_hops"
                )

                edgedata_info = {
                    "file_path": edgedata_result['file_path'],
                    "edge_count": edgedata_result['edge_count'],
                    "event_edges": edgedata_result.get('event_count', 0),
                    "strategy_edges": edgedata_result.get('strategy_count', 0),
                    "source_breakdown": edgedata_result.get('source_breakdown', {}),
                    "validation_rate": edgedata_result.get('validation', {}).get('validation_rate', 1.0)
                }

                logger.info(f"✓ 统一edgeData生成成功: {edgedata_result['edge_count']} edges")

            # 6. 获取时间范围（从request或第一个scenario）
            time_range = request.time_range
            if not time_range and len(request.scenarios) > 0:
                first_scenario = request.scenarios[0]
                time_range = {
                    "start_time": first_scenario.time.get('start_time', '06:00:00'),
                    "end_time": first_scenario.time.get('end_time', '09:00:00')
                }

            # 7. 触发OD数据生成（后台异步）
            if request.od_file and '.' in request.od_file:  # 数据库表格式：schema.table
                schema_name, table_name = self._parse_od_file(request.od_file)

                import threading
                thread = threading.Thread(
                    target=self._run_od_generation_in_background,
                    args=(case_id, case_dir),
                    kwargs={
                        "od_request": type('obj', (object,), {
                            'start_time': time_range.get("start_time"),
                            'end_time': time_range.get("end_time"),
                            'interval_minutes': 5,  # 默认5分钟间隔
                            'taz_file': request.taz_file,
                            'net_file': request.network_file,
                            'schemas_name': schema_name,
                            'table_name': table_name,
                            'output_dir': str(case_dir / "config")
                        })(),
                        "od_file_info_json": case_dir / "od_file_info.json"
                    },
                    daemon=True
                )
                thread.start()
                logger.info(f"✓ OD数据生成已启动（后台处理）")

            # 8. 初始化案例元数据（用于生成sumocfg）
            case_metadata = {
                "metadata_version": "2.0",
                "case_id": case_id,
                "case_name": case_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "od_generating",
                "source_type": "event_scenario_batch",
                "event_scenario": {
                    "event_id": request.event_id,
                    "event_type": request.event_type,
                    "total_scenarios": len(request.scenarios),
                },
                "case_config": {
                    "network_file": request.network_file,
                    "od_file": request.od_file,
                    "taz_file": request.taz_file,
                    "time_range": time_range
                },
                "files": {
                    "network_file": f"config/{Path(request.network_file).name}",
                    "taz_file": f"config/{Path(request.taz_file).name}" if request.taz_file else None,
                    "routes_file": f"config/{request.od_file}",  # 占位符：OD表名，生成后会更新为实际 .rou.xml 文件名
                    "additional_files": []
                },
                "edgedata_config": edgedata_info,
                "description": f"批量创建: 事件{request.event_id}, {len(request.scenarios)}个场景",
                "scenarios": [],
                "simulations": {},
                "statistics": {}
            }

            # 9. 为每个场景创建完整的仿真准备
            scenario_results = []
            successful_count = 0
            failed_count = 0

            for scenario in request.scenarios:
                try:
                    # 生成仿真ID
                    simulation_id = f"sim_{scenario.scenario_id}"

                    # 创建仿真目录
                    sim_dir = case_dir / "simulations" / simulation_id
                    sim_dir.mkdir(parents=True, exist_ok=True)

                    # 创建输出子目录
                    for output_dir in ["edgedata", "e1"]:
                        (sim_dir / output_dir).mkdir(exist_ok=True)
                    logger.info(f"✓ 创建仿真输出目录: {simulation_id}")

                    # 从config/目录复制场景特定的控制策略.add.xml文件到仿真目录
                    # 查找对应的策略文件
                    event_type_folder = self._find_event_type_folder(scenario.scenario_id)
                    if event_type_folder:
                        scenario_add_xml_path = self._find_scenario_add_xml(scenario.scenario_id, event_type_folder)
                        if scenario_add_xml_path:
                            # 从config/复制到仿真目录
                            source_strategy_file = config_dir / scenario_add_xml_path.name
                            if source_strategy_file.exists():
                                target_path = sim_dir / scenario_add_xml_path.name
                                shutil.copy2(source_strategy_file, target_path)
                                logger.info(f"✓ 复制策略文件到仿真目录: {scenario_add_xml_path.name}")
                            else:
                                logger.warning(f"⚠️ config/中未找到策略文件: {scenario_add_xml_path.name}")

                    # 复制统一的edgeData到仿真目录
                    if edgedata_info:
                        edgedata_source = Path(edgedata_info['file_path'])
                        edgedata_dest = sim_dir / "edgeData.add.xml"
                        shutil.copy2(edgedata_source, edgedata_dest)
                        logger.info(f"✓ 复制edgeData到仿真目录: {simulation_id}")

                    # 复制TAZ文件到仿真目录
                    if request.taz_file:
                        taz_filename = Path(request.taz_file).name
                        source_taz = config_dir / taz_filename
                        if source_taz.exists():
                            target_taz = sim_dir / taz_filename
                            shutil.copy2(source_taz, target_taz)
                            logger.info(f"✓ 复制TAZ文件到仿真目录: {taz_filename}")

                    # 准备仿真参数
                    simulation_params = {
                        "duration_hours": scenario.time.get('sim_duration_hours', 2.5),
                        "random_seed": None,
                        "simulation_type": request.simulation_type,
                        "output_config": scenario.output_config
                    }

                    # 生成 simulation.sumocfg 配置文件（与表格视图创建逻辑一致）
                    # 注意：即使 OD 数据还在生成，sumocfg 也会生成（引用固定路径的 rou.xml）
                    from shared.utilities.sumo_utils import generate_sumocfg_for_simulation

                    sumocfg_content = generate_sumocfg_for_simulation(
                        case_metadata=case_metadata,
                        simulation_type=request.simulation_type,
                        simulation_folder=sim_dir,
                        case_root=case_dir,
                        simulation_params=simulation_params
                    )

                    sumocfg_file = sim_dir / "simulation.sumocfg"
                    with open(sumocfg_file, 'w', encoding='utf-8') as f:
                        f.write(sumocfg_content)
                    logger.info(f"✓ 生成 simulation.sumocfg: {simulation_id}")

                    # 创建完整的仿真元数据（与表格视图创建逻辑一致）
                    sim_metadata = {
                        "metadata_version": "2.0",
                        "simulation_id": simulation_id,
                        "case_id": case_id,
                        "created_at": datetime.now().isoformat(),
                        "status": "ready",  # 仿真已准备就绪（sumocfg已生成）
                        "source_scenario": {
                            "scenario_id": scenario.scenario_id,
                            "event_id": scenario.event_id,
                            "event_type": scenario.event_type,
                            "control_strategy_type": scenario.strategy
                        },
                        "simulation_params": {
                            "duration_hours": simulation_params["duration_hours"],
                            "random_seed": simulation_params["random_seed"],
                            "simulation_type": simulation_params["simulation_type"],
                            "output_config": simulation_params["output_config"],
                            "network_file": request.network_file,
                            "od_file": request.od_file,
                            "taz_file": request.taz_file
                        },
                        "config_file": sumocfg_content,  # 完整内容（向后兼容）
                        "config_file_path": "simulation.sumocfg",
                        "sumocfg_generated_at": datetime.now().isoformat()
                    }

                    # 保存仿真元数据
                    sim_metadata_file = sim_dir / "simulation_metadata.json"
                    with open(sim_metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

                    # 更新案例元数据（记录场景和仿真）
                    if scenario.scenario_id not in case_metadata["scenarios"]:
                        case_metadata["scenarios"].append(scenario.scenario_id)

                    case_metadata["simulations"][simulation_id] = {
                        "created_at": datetime.now().isoformat(),
                        "status": "ready",  # 仿真已准备就绪（sumocfg已生成）
                        "scenario_id": scenario.scenario_id
                    }

                    scenario_results.append({
                        "scenario_id": scenario.scenario_id,
                        "strategy": scenario.strategy,
                        "success": True,
                        "simulation_id": simulation_id,
                        "error_message": None
                    })
                    successful_count += 1

                    logger.info(f"✓ 场景仿真准备成功: {scenario.scenario_id} -> {simulation_id}")

                except Exception as e:
                    scenario_results.append({
                        "scenario_id": scenario.scenario_id,
                        "strategy": scenario.strategy,
                        "success": False,
                        "simulation_id": None,
                        "error_message": str(e)
                    })
                    failed_count += 1

                    logger.error(f"✗ 场景仿真准备失败: {scenario.scenario_id}, 错误: {str(e)}")

            # 10. 更新并保存最终案例元数据
            case_metadata["event_scenario"]["successful_scenarios"] = successful_count
            case_metadata["event_scenario"]["failed_scenarios"] = failed_count
            case_metadata["statistics"] = {
                "total_scenarios": len(case_metadata["scenarios"]),
                "total_simulations": len(case_metadata["simulations"])
            }
            # 更新additional_files列表
            case_metadata["files"]["additional_files"] = [
                f"config/{filename}" for filename in strategy_files_copied
            ]

            MetadataManager.save_case_metadata(case_dir, case_metadata)

            duration = time.time() - start_time
            logger.info(f"✓ 批量创建完成: {successful_count}/{len(request.scenarios)} 成功, 耗时 {duration:.2f}秒")

            # 11. 返回结果
            return {
                "event_id": request.event_id,
                "event_type": request.event_type,
                "case_id": case_id,
                "case_name": case_name,
                "case_dir": str(case_dir),
                "total_scenarios": len(request.scenarios),
                "successful_scenarios": successful_count,
                "failed_scenarios": failed_count,
                "scenario_results": scenario_results,
                "edgedata_info": edgedata_info,
                "created_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "od_generation_status": "in_progress",
                "simulation_status": "ready",  # 仿真已准备就绪（sumocfg已生成）
                "message": "批量创建成功！仿真已准备就绪，OD数据生成中（3-5分钟），完成后可启动仿真"
            }

        except Exception as e:
            logger.error(f"批量创建失败: {str(e)}")
            raise Exception(f"批量创建事件案例失败: {str(e)}")


# 创建服务实例
case_service = CaseService()


# 导出服务函数 (保持向后兼容)
async def create_case_service(request: CaseCreationRequest) -> Dict[str, Any]:
    """案例创建服务函数"""
    return await case_service.create_case(request)


async def list_cases_service(page: int = 1, page_size: int = 10,
                           status: Optional[CaseStatus] = None,
                           search: Optional[str] = None) -> CaseListResponse:
    """案例列表服务函数"""
    return await case_service.list_cases(page, page_size, status, search)


async def get_case_service(case_id: str) -> CaseMetadata:
    """获取案例详情服务函数"""
    return await case_service.get_case(case_id)


async def delete_case_service(case_id: str) -> Dict[str, Any]:
    """删除案例服务函数"""
    return await case_service.delete_case(case_id)


async def clone_case_service(case_id: str, request: CaseCloneRequest) -> Dict[str, Any]:
    """克隆案例服务函数"""
    return await case_service.clone_case(case_id, request)
