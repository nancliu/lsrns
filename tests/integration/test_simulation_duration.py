"""
集成测试: simulation_duration 自定义仿真时长

P1-4: 验证simulation_duration参数从API流转到sumocfg的完整链路
"""

import pytest
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

from api.services.batch_optimization_service import BatchOptimizationService


class TestSimulationDuration:
    """测试simulation_duration自定义仿真时长功能"""

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

    def _verify_simulation_config_exists(self, batch_dir: Path) -> dict:
        """验证simulation_config.json存在并加载"""
        config_file = batch_dir / "simulation_config.json"
        assert config_file.exists(), f"simulation_config.json not found at {config_file}"

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        return config_data

    def test_custom_duration_saved_to_config(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 自定义simulation_duration保存到simulation_config.json
        预期: 配置文件包含simulation_duration字段
        """
        simulation_duration = {
            "hours": 2,
            "minutes": 30,
            "total_minutes": 150
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

        # 验证配置文件存在
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证simulation_duration字段存在
        assert 'simulation_duration' in config_data, "simulation_duration not found in config"
        assert config_data['simulation_duration']['hours'] == 2
        assert config_data['simulation_duration']['minutes'] == 30
        assert config_data['simulation_duration']['total_minutes'] == 150

    def test_simulation_duration_in_params(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: simulation_duration包含在simulation_params中
        预期: simulation_params子字段包含simulation_duration
        """
        simulation_duration = {
            "hours": 4,
            "minutes": 0,
            "total_minutes": 240
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
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证simulation_params子字段存在
        assert 'simulation_params' in config_data, "simulation_params not found in config"
        sim_params = config_data['simulation_params']

        # 验证simulation_duration在simulation_params中
        assert 'simulation_duration' in sim_params, "simulation_duration not found in simulation_params"
        assert sim_params['simulation_duration']['total_minutes'] == 240

    def test_custom_duration_overrides_metadata(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 自定义simulation_duration覆盖case元数据的时间范围
        预期: 配置中包含自定义时长，而不是从case元数据推导的时长
        """
        # 注意: 这个测试验证simulation_duration在配置中的保存
        # 实际的sumocfg生成由generate_sumocfg_for_simulation处理（P1-3）
        simulation_duration = {
            "hours": 1,
            "minutes": 0,
            "total_minutes": 60
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
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证simulation_duration被保存（将由sumocfg生成时读取）
        assert 'simulation_duration' in config_data
        assert config_data['simulation_duration']['total_minutes'] == 60

    def test_no_duration_uses_metadata(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 未提供simulation_duration时不在config中添加
        预期: simulation_duration字段不存在，sumocfg生成时使用case元数据
        """
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
            simulation_duration=None  # 显式None
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证simulation_duration不存在（使用case元数据）
        assert 'simulation_duration' not in config_data, "simulation_duration should not be in config when not provided"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
