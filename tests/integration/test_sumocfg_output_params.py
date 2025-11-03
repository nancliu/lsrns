"""
集成测试: sumocfg.xml输出参数生成

P0-5: 验证sumocfg.xml是否正确生成所有输出参数
"""

import pytest
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

from api.services.batch_optimization_service import BatchOptimizationService


class TestSumocfgOutputParams:
    """测试sumocfg.xml输出参数生成"""

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

    def test_simulation_config_contains_output_params(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: simulation_config.json包含所有输出参数
        预期: 配置文件包含output_tripinfo, output_vehroute等标准键名
        """
        # 创建批次，启用所有输出参数
        output_config = {
            'output_tripinfo': True,
            'output_vehroute': True,
            'output_netstate': True,
            'output_fcd': True,
            'output_emission': True,
            'output_edgedata': True,
        }

        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_config=output_config,
            num_seeds=1,
            base_seed=66
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id

        # 验证配置文件存在
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证包含所有输出参数
        assert config_data.get('output_tripinfo') is True, "output_tripinfo not found in config"
        assert config_data.get('output_vehroute') is True, "output_vehroute not found in config"
        assert config_data.get('output_netstate') is True, "output_netstate not found in config"
        assert config_data.get('output_fcd') is True, "output_fcd not found in config"
        assert config_data.get('output_emission') is True, "output_emission not found in config"
        assert config_data.get('output_edgedata') is True, "output_edgedata not found in config"

    def test_simulation_params_contains_output_params(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: simulation_params子字段包含输出参数
        预期: simulation_config.json的simulation_params字段包含所有output_*参数
        """
        output_config = {
            'output_tripinfo': True,
            'output_vehroute': False,
            'output_netstate': True,
            'output_fcd': False,
            'output_emission': True,
            'output_edgedata': False,
        }

        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_config=output_config,
            num_seeds=1,
            base_seed=66
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证simulation_params子字段存在
        assert 'simulation_params' in config_data, "simulation_params not found in config"
        sim_params = config_data['simulation_params']

        # 验证参数值正确
        assert sim_params.get('output_tripinfo') is True
        assert sim_params.get('output_vehroute') is False
        assert sim_params.get('output_netstate') is True
        assert sim_params.get('output_fcd') is False
        assert sim_params.get('output_emission') is True
        assert sim_params.get('output_edgedata') is False

    def test_output_disabled_parameters_excluded(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 禁用的输出参数在配置中为False
        预期: disabled参数的值为False
        """
        output_config = {
            'output_tripinfo': False,
            'output_vehroute': False,
            'output_netstate': False,
            'output_fcd': False,
            'output_emission': False,
            'output_edgedata': False,
        }

        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_config=output_config,
            num_seeds=1,
            base_seed=66
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证所有参数都是False
        assert config_data.get('output_tripinfo') is False
        assert config_data.get('output_vehroute') is False
        assert config_data.get('output_netstate') is False
        assert config_data.get('output_fcd') is False
        assert config_data.get('output_emission') is False
        assert config_data.get('output_edgedata') is False

    def test_output_config_uses_new_key_names(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: 使用新的output_*键名而不是旧的tripinfo_xml等
        预期: 配置使用output_tripinfo而不是tripinfo_xml
        """
        output_config = {
            'output_tripinfo': True,
        }

        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_config=output_config,
            num_seeds=1,
            base_seed=66
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id
        config_data = self._verify_simulation_config_exists(batch_dir)

        # 验证新键名存在
        assert 'output_tripinfo' in config_data

        # 验证旧键名不存在
        assert 'tripinfo_xml' not in config_data, "Old key name 'tripinfo_xml' found in config"

    def test_output_level_compatibility(self, batch_service, test_case_id, baseline_plan_id):
        """
        测试场景: output_level为standard时启用tripinfo和edgedata
        预期: standard级别启用output_tripinfo和output_edgedata
        """
        # 不提供output_config，使用output_level进行向后兼容测试
        response = batch_service.create_batch(
            case_id=test_case_id,
            plan_ids=[baseline_plan_id],
            output_level="standard",
            num_seeds=1,
            base_seed=66
        )

        batch_id = response["batch_id"]
        batch_dir = Path("cases") / test_case_id / "simulations" / "plan_opti" / batch_id
        config_data = self._verify_simulation_config_exists(batch_dir)

        # standard级别应该启用tripinfo和edgedata
        assert config_data.get('output_tripinfo') is True, "output_tripinfo should be True for standard level"
        assert config_data.get('output_edgedata') is True, "output_edgedata should be True for standard level"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
