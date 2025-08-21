"""
OD项目测试配置文件
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def sample_od_data():
    """提供示例OD数据用于测试"""
    return {
        "origin": "TAZ_001",
        "destination": "TAZ_002", 
        "volume": 100,
        "time_period": "AM_PEAK"
    }

@pytest.fixture
def sample_simulation_config():
    """提供示例仿真配置用于测试"""
    return {
        "network_file": "sichuan202503v5.net.xml",
        "taz_file": "TAZ_4.add.xml",
        "simulation_type": "mesoscopic",
        "duration": 3600
    }

@pytest.fixture
def test_data_dir():
    """提供测试数据目录路径"""
    return project_root / "tests" / "test_data"
