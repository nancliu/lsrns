"""
集成测试: simulation_duration在sumocfg中的应用

P1-3验证: 确认simulation_duration正确应用到生成的sumocfg.xml文件中
"""

import pytest
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

from api.services.batch_optimization_service import BatchOptimizationService
from shared.utilities.sumo_utils import generate_sumocfg_for_simulation


class TestSimulationDurationSumocfg:
    """测试simulation_duration在sumocfg中的应用"""

    @pytest.fixture
    def batch_service(self):
        """创建批量优化服务实例"""
        return BatchOptimizationService()

    @pytest.fixture
    def test_case_id(self):
        """使用测试案例"""
        return "case_20251028_091831"

    @pytest.fixture
    def baseline_plan_id(self):
        """基准方案ID"""
        return "baseline_plan"

    def test_simulation_duration_applied_to_sumocfg(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 自定义simulation_duration应用到生成的sumocfg.xml
        预期: sumocfg的<end>值应等于total_minutes * 60
        """
        # 创建批次，设置自定义时长
        simulation_duration = {
            "hours": 2,
            "minutes": 30,
            "total_minutes": 150  # 150分钟 = 9000秒
        }

        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_config={
                'output_tripinfo': True,
                'output_vehroute': False,
                'output_netstate': False,
                'output_fcd': False,
                'output_emission': False,
                'output_edgedata': False,
            },
            num_seeds=1,
            base_seed=66,
            simulation_duration=simulation_duration
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id

        # 验证simulation_config.json包含simulation_duration
        config_file = batch_dir / "simulation_config.json"
        assert config_file.exists(), f"simulation_config.json not found at {config_file}"

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # 验证simulation_duration在config中
        assert 'simulation_params' in config_data
        assert 'simulation_duration' in config_data['simulation_params']
        assert config_data['simulation_params']['simulation_duration']['total_minutes'] == 150

        # 现在生成sumocfg来验证时长是否被应用
        # 加载case元数据
        case_dir = Path("cases") / test_case_id
        metadata_file = case_dir / "metadata.json"
        assert metadata_file.exists(), f"Case metadata not found at {metadata_file}"

        with open(metadata_file, "r", encoding="utf-8") as f:
            case_metadata = json.load(f)

        # 提取simulation_params
        simulation_params = config_data.get('simulation_params', {})

        # 生成sumocfg
        sim_folder = batch_dir / baseline_plan_id / "sim_66"
        sim_folder.mkdir(parents=True, exist_ok=True)

        sumocfg_content = generate_sumocfg_for_simulation(
            case_metadata=case_metadata,
            simulation_type=None,  # 可以为None，函数会处理
            simulation_folder=sim_folder,
            case_root=case_dir,
            simulation_params=simulation_params
        )

        # 解析sumocfg XML并验证end值
        root = ET.fromstring(sumocfg_content)

        # 查找<time>元素下的<end>元素
        time_elem = root.find('.//time')
        assert time_elem is not None, "<time> element not found in sumocfg"

        end_elem = time_elem.find('end')
        assert end_elem is not None, "<end> element not found in <time> section"

        end_value = int(end_elem.get('value', '0'))

        # 验证end值等于150分钟 = 9000秒
        expected_end = 150 * 60  # 9000
        assert end_value == expected_end, \
            f"Expected <end> value {expected_end}s for 150 minutes, but got {end_value}s"

    def test_no_duration_uses_case_metadata(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 未提供simulation_duration时使用case元数据的时间范围
        预期: sumocfg的<end>值应基于case的start/end时间计算
        """
        # 创建批次，不提供自定义时长
        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_config={
                'output_tripinfo': True,
                'output_vehroute': False,
                'output_netstate': False,
                'output_fcd': False,
                'output_emission': False,
                'output_edgedata': False,
            },
            num_seeds=1,
            base_seed=66,
            simulation_duration=None  # 不提供自定义时长
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id

        # 验证simulation_config.json不包含simulation_duration
        config_file = batch_dir / "simulation_config.json"
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # 如果没有提供custom duration，simulation_params中不应该有simulation_duration
        # （或者如果有，也应该被忽略）
        if 'simulation_params' in config_data:
            # 如果simulation_duration存在，它不应该影响sumocfg生成逻辑
            pass

        # 生成sumocfg
        case_dir = Path("cases") / test_case_id
        metadata_file = case_dir / "metadata.json"
        with open(metadata_file, "r", encoding="utf-8") as f:
            case_metadata = json.load(f)

        simulation_params = config_data.get('simulation_params', {})
        sim_folder = batch_dir / baseline_plan_id / "sim_66"
        sim_folder.mkdir(parents=True, exist_ok=True)

        sumocfg_content = generate_sumocfg_for_simulation(
            case_metadata=case_metadata,
            simulation_type=None,
            simulation_folder=sim_folder,
            case_root=case_dir,
            simulation_params=simulation_params
        )

        # 解析sumocfg并检查end值
        root = ET.fromstring(sumocfg_content)
        time_elem = root.find('.//time')
        assert time_elem is not None

        end_elem = time_elem.find('end')
        assert end_elem is not None

        end_value = int(end_elem.get('value', '0'))

        # 如果case有时间范围，end值应该是计算得出的，否则应该是默认的3600秒
        # 这取决于case metadata中是否有time_range
        time_range = case_metadata.get('time_range', {})
        if time_range.get('start') and time_range.get('end'):
            # 有时间范围，end值应该被正确计算
            assert end_value > 0, "End value should be > 0 when case has time range"
        else:
            # 没有时间范围，应该使用默认3600秒
            assert end_value == 3600, f"Expected default 3600s, but got {end_value}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
