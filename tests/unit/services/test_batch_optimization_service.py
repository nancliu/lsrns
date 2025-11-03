"""
批量优化仿真服务单元测试
"""

import pytest
import json
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from api.services.batch_optimization_service import BatchOptimizationService
from shared.control_tools import plan_file_manager


@pytest.fixture
def temp_test_env(tmp_path, monkeypatch):
    """创建临时测试环境"""
    # 设置临时目录
    cases_dir = tmp_path / "cases"
    plans_dir = tmp_path / "control_data" / "plans"

    cases_dir.mkdir(parents=True)
    plans_dir.mkdir(parents=True)

    # 创建测试case
    test_case = cases_dir / "test_case_001"
    test_case.mkdir()
    (test_case / "config").mkdir()
    (test_case / "simulations").mkdir()

    # 创建基准方案
    baseline_dir = plans_dir / "baseline_plan"
    baseline_dir.mkdir()

    baseline_metadata = {
        "plan_id": "baseline_plan",
        "plan_name": "基准方案（无管控）",
        "description": "无管控基准方案",
        "strategy_ids": [],
        "created_at": datetime.now().isoformat()
    }

    with open(baseline_dir / "plan_metadata.json", "w", encoding="utf-8") as f:
        json.dump(baseline_metadata, f, ensure_ascii=False, indent=2)

    with open(baseline_dir / "strategy_refs.json", "w", encoding="utf-8") as f:
        json.dump([], f)

    # 创建测试方案
    plan_001_dir = plans_dir / "plan_001"
    plan_001_dir.mkdir()

    plan_001_metadata = {
        "plan_id": "plan_001",
        "plan_name": "测试方案A",
        "description": "测试方案",
        "strategy_ids": ["strategy_001"],
        "created_at": datetime.now().isoformat()
    }

    with open(plan_001_dir / "plan_metadata.json", "w", encoding="utf-8") as f:
        json.dump(plan_001_metadata, f, ensure_ascii=False, indent=2)

    # 创建plans_index.json
    plans_index = {
        "plans": [
            {
                "plan_id": "baseline_plan",
                "plan_name": "基准方案（无管控）"
            },
            {
                "plan_id": "plan_001",
                "plan_name": "测试方案A"
            }
        ]
    }

    with open(plans_dir / "plans_index.json", "w", encoding="utf-8") as f:
        json.dump(plans_index, f, ensure_ascii=False, indent=2)

    # Monkeypatch paths (use Path objects for plan_file_manager)
    monkeypatch.setattr("api.services.batch_optimization_service.CASES_BASE_DIR", str(cases_dir))
    monkeypatch.setattr("api.services.batch_optimization_service.PLANS_BASE_DIR", str(plans_dir))
    monkeypatch.setattr("shared.control_tools.plan_file_manager.PLANS_BASE_DIR", plans_dir)

    yield {
        "cases_dir": cases_dir,
        "plans_dir": plans_dir,
        "test_case_id": "test_case_001"
    }

    # 清理
    if tmp_path.exists():
        shutil.rmtree(tmp_path)


@pytest.fixture
def service(temp_test_env):
    """创建服务实例"""
    return BatchOptimizationService()


class TestBatchOptimizationServiceCreate:
    """批量仿真服务创建测试"""

    def test_create_batch_basic(self, service, temp_test_env):
        """测试基本批次创建"""
        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan", "plan_001"],
            num_seeds=3,
            base_seed=66
        )

        assert "batch_id" in result
        assert result["batch_id"].startswith("batch_")
        assert result["case_id"] == "test_case_001"
        assert result["plan_ids"] == ["baseline_plan", "plan_001"]
        assert result["total_tasks"] == 6  # 2 plans × 3 seeds
        assert result["status"] == "pending"
        assert "created_at" in result

        # 验证批次目录已创建
        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / result["batch_id"]
        assert batch_dir.exists()
        assert (batch_dir / "batch_metadata.json").exists()
        assert (batch_dir / "batch_progress.json").exists()

    def test_create_batch_auto_add_baseline(self, service, temp_test_env):
        """测试自动添加baseline_plan"""
        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["plan_001"],  # 没有baseline_plan
            num_seeds=2
        )

        # 应该自动添加baseline_plan到列表首位
        assert "baseline_plan" in result["plan_ids"]
        assert result["plan_ids"][0] == "baseline_plan"
        assert result["total_tasks"] == 4  # 2 plans × 2 seeds

    def test_create_batch_case_not_found(self, service):
        """测试案例不存在"""
        with pytest.raises(FileNotFoundError, match="案例不存在"):
            service.create_batch(
                case_id="nonexistent_case",
                plan_ids=["baseline_plan"]
            )

    def test_create_batch_plan_not_found(self, service):
        """测试方案不存在"""
        with pytest.raises(FileNotFoundError, match="方案不存在"):
            service.create_batch(
                case_id="test_case_001",
                plan_ids=["nonexistent_plan"]
            )

    def test_create_batch_with_simulation_config(self, service, temp_test_env):
        """测试包含仿真配置的批次创建"""
        simulation_config = {
            "begin": 0,
            "end": 14400,
            "step_length": 1
        }

        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            simulation_config=simulation_config
        )

        # 验证配置已保存
        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / result["batch_id"]
        config_file = batch_dir / "simulation_config.json"

        assert config_file.exists()

        with open(config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # 验证提供的simulation_config字段已保存（注: 现在还包含output参数等）
        assert saved_config.get("begin") == 0
        assert saved_config.get("end") == 14400
        assert saved_config.get("step_length") == 1

    def test_create_batch_with_tripinfo_output(self, service, temp_test_env):
        """P0-6: 测试tripinfo输出参数配置"""
        output_config = {
            'output_tripinfo': True,
            'output_vehroute': False,
            'output_netstate': False,
            'output_fcd': False,
            'output_emission': False,
            'output_edgedata': False,
        }

        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=1,
            base_seed=66,
            output_config=output_config
        )

        # 验证配置文件
        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / result["batch_id"]
        config_file = batch_dir / "simulation_config.json"

        with open(config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # 验证output_tripinfo为True
        assert saved_config.get('output_tripinfo') is True
        # 验证其他参数为False
        assert saved_config.get('output_vehroute') is False
        assert saved_config.get('output_netstate') is False

    def test_create_batch_with_vehroute_output(self, service, temp_test_env):
        """P0-6: 测试vehroute输出参数配置"""
        output_config = {
            'output_tripinfo': False,
            'output_vehroute': True,
            'output_netstate': False,
            'output_fcd': False,
            'output_emission': False,
            'output_edgedata': False,
        }

        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=1,
            base_seed=66,
            output_config=output_config
        )

        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / result["batch_id"]
        config_file = batch_dir / "simulation_config.json"

        with open(config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # 验证output_vehroute为True
        assert saved_config.get('output_vehroute') is True
        assert saved_config.get('output_tripinfo') is False

    def test_create_batch_with_mixed_outputs(self, service, temp_test_env):
        """P0-6: 测试混合输出参数配置"""
        output_config = {
            'output_tripinfo': True,
            'output_vehroute': True,
            'output_netstate': False,
            'output_fcd': True,
            'output_emission': False,
            'output_edgedata': True,
        }

        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=1,
            base_seed=66,
            output_config=output_config
        )

        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / result["batch_id"]
        config_file = batch_dir / "simulation_config.json"

        with open(config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # 验证启用的参数
        assert saved_config.get('output_tripinfo') is True
        assert saved_config.get('output_vehroute') is True
        assert saved_config.get('output_fcd') is True
        assert saved_config.get('output_edgedata') is True

        # 验证禁用的参数
        assert saved_config.get('output_netstate') is False
        assert saved_config.get('output_emission') is False

    def test_simulation_params_construction(self, service, temp_test_env):
        """P0-6: 测试simulation_params构造"""
        output_config = {
            'output_tripinfo': True,
            'output_vehroute': False,
            'output_netstate': True,
            'output_fcd': False,
            'output_emission': True,
            'output_edgedata': False,
        }

        result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=1,
            base_seed=66,
            output_config=output_config
        )

        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / result["batch_id"]
        config_file = batch_dir / "simulation_config.json"

        with open(config_file, "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        # 验证simulation_params子字段存在
        assert 'simulation_params' in saved_config
        sim_params = saved_config['simulation_params']

        # 验证所有参数都在simulation_params中
        assert sim_params.get('output_tripinfo') is True
        assert sim_params.get('output_vehroute') is False
        assert sim_params.get('output_netstate') is True
        assert sim_params.get('output_fcd') is False
        assert sim_params.get('output_emission') is True
        assert sim_params.get('output_edgedata') is False


class TestBatchOptimizationServiceProgress:
    """批量仿真服务进度查询测试"""

    def test_get_batch_progress(self, service, temp_test_env):
        """测试获取批次进度"""
        # 先创建批次
        create_result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=2
        )

        batch_id = create_result["batch_id"]

        # 获取进度
        progress = service.get_batch_progress("test_case_001", batch_id)

        assert progress["batch_id"] == batch_id
        assert progress["status"] == "pending"
        assert progress["total_tasks"] == 2
        assert progress["completed_tasks"] == 0
        assert "estimated_completion" in progress  # 服务层添加的字段
        assert isinstance(progress["tasks"], list)

    def test_get_batch_progress_not_found(self, service):
        """测试获取不存在批次的进度"""
        with pytest.raises(FileNotFoundError, match="批次不存在"):
            service.get_batch_progress("test_case_001", "nonexistent_batch")


class TestBatchOptimizationServiceResults:
    """批量仿真服务结果查询测试"""

    def _create_completed_batch(self, service, temp_test_env):
        """辅助方法：创建一个已完成的批次"""
        # 创建批次
        create_result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=2,
            base_seed=66
        )

        batch_id = create_result["batch_id"]
        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / batch_id

        # 手动标记为completed
        metadata_file = batch_dir / "batch_metadata.json"
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        metadata["status"] = "completed"
        metadata["started_at"] = datetime.now().isoformat()
        metadata["completed_at"] = datetime.now().isoformat()

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 更新progress
        progress_file = batch_dir / "batch_progress.json"
        with open(progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)

        progress["status"] = "completed"
        for task in progress["tasks"]:
            task["status"] = "completed"
            task["simulation_id"] = f"sim_{task['task_id']}"

        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

        # 创建模拟仿真结果目录和文件
        for task in progress["tasks"]:
            sim_dir = batch_dir / task["plan_id"] / f"sim_{task['seed']}"
            sim_dir.mkdir(parents=True, exist_ok=True)

            # 创建summary.xml
            summary_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<summary>
    <step time="100" loaded="1000" meanSpeed="25.5"/>
</summary>"""
            (sim_dir / "summary.xml").write_text(summary_xml, encoding="utf-8")

            # 创建tripinfo.xml
            tripinfo_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<tripinfos>
    <tripinfo id="veh_1" duration="1200.0" timeLoss="300.0"/>
    <tripinfo id="veh_2" duration="1400.0" timeLoss="400.0"/>
</tripinfos>"""
            (sim_dir / "tripinfo.xml").write_text(tripinfo_xml, encoding="utf-8")

        return batch_id

    def test_get_batch_results(self, service, temp_test_env):
        """测试获取批次结果"""
        batch_id = self._create_completed_batch(service, temp_test_env)

        # 获取结果
        results = service.get_batch_results("test_case_001", batch_id)

        assert results["batch_id"] == batch_id
        assert results["status"] == "completed"
        assert "plan_results" in results
        assert len(results["plan_results"]) == 1  # 1 plan

        # 验证方案结果
        plan_result = results["plan_results"][0]
        assert plan_result["plan_id"] == "baseline_plan"
        assert plan_result["plan_name"] == "基准方案（无管控）"
        assert "simulations" in plan_result
        assert len(plan_result["simulations"]) == 2  # 2 seeds

        # 验证聚合指标
        assert "aggregated_metrics" in plan_result
        metrics = plan_result["aggregated_metrics"]

        # 应该包含avg_speed和avg_travel_time
        if "avg_speed" in metrics:
            assert "mean" in metrics["avg_speed"]
            assert "std" in metrics["avg_speed"]
            assert "min" in metrics["avg_speed"]
            assert "max" in metrics["avg_speed"]

    def test_get_batch_results_not_completed(self, service, temp_test_env):
        """测试获取未完成批次的结果"""
        # 创建pending批次
        create_result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=2
        )

        batch_id = create_result["batch_id"]

        # 尝试获取结果应该失败
        with pytest.raises(ValueError, match="批次尚未完成"):
            service.get_batch_results("test_case_001", batch_id)


class TestBatchOptimizationServiceXMLParsing:
    """XML解析方法测试"""

    def test_parse_summary_xml(self, service, tmp_path):
        """测试解析summary.xml"""
        summary_xml = """<?xml version="1.0" encoding="UTF-8"?>
<summary>
    <step time="100" loaded="5000" meanSpeed="28.5"/>
</summary>"""

        xml_file = tmp_path / "summary.xml"
        xml_file.write_text(summary_xml, encoding="utf-8")

        metrics = service._parse_summary_xml(xml_file)

        assert metrics["total_vehicles"] == 5000
        assert metrics["avg_speed"] == 28.5

    def test_parse_tripinfo_xml(self, service, tmp_path):
        """测试解析tripinfo.xml"""
        tripinfo_xml = """<?xml version="1.0" encoding="UTF-8"?>
<tripinfos>
    <tripinfo id="veh_1" duration="1000.0" timeLoss="200.0"/>
    <tripinfo id="veh_2" duration="1200.0" timeLoss="300.0"/>
    <tripinfo id="veh_3" duration="1100.0" timeLoss="250.0"/>
</tripinfos>"""

        xml_file = tmp_path / "tripinfo.xml"
        xml_file.write_text(tripinfo_xml, encoding="utf-8")

        metrics = service._parse_tripinfo_xml(xml_file)

        # 平均行程时间: (1000 + 1200 + 1100) / 3 = 1100
        assert metrics["avg_travel_time"] == pytest.approx(1100.0)
        # 总延误: 200 + 300 + 250 = 750
        assert metrics["total_delay"] == 750.0

    def test_calculate_aggregated_metrics(self, service):
        """测试聚合统计计算"""
        simulations = [
            {"seed": 66, "avg_speed": 25.0, "total_vehicles": 1000},
            {"seed": 67, "avg_speed": 27.0, "total_vehicles": 1100},
            {"seed": 68, "avg_speed": 26.0, "total_vehicles": 1050},
        ]

        aggregated = service._calculate_aggregated_metrics(simulations)

        # avg_speed聚合
        assert "avg_speed" in aggregated
        assert aggregated["avg_speed"]["mean"] == pytest.approx(26.0)
        assert aggregated["avg_speed"]["min"] == 25.0
        assert aggregated["avg_speed"]["max"] == 27.0

        # total_vehicles聚合
        assert "total_vehicles" in aggregated
        assert aggregated["total_vehicles"]["mean"] == pytest.approx(1050.0)


class TestBatchOptimizationServiceCancelDelete:
    """批量仿真服务取消和删除测试"""

    def test_cancel_batch(self, service, temp_test_env):
        """测试取消批次"""
        # 创建批次
        create_result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=2
        )

        batch_id = create_result["batch_id"]

        # 取消批次
        cancel_result = service.cancel_batch("test_case_001", batch_id)

        assert cancel_result["batch_id"] == batch_id
        assert cancel_result["status"] == "cancelled"
        assert "cancelled_at" in cancel_result

    def test_delete_batch(self, service, temp_test_env):
        """测试删除批次"""
        # 创建批次
        create_result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=2
        )

        batch_id = create_result["batch_id"]
        batch_dir = temp_test_env["cases_dir"] / "test_case_001" / "simulations" / "plan_opti" / batch_id

        # 验证批次目录存在
        assert batch_dir.exists()

        # 删除批次
        delete_result = service.delete_batch("test_case_001", batch_id)

        assert delete_result["batch_id"] == batch_id
        assert delete_result["deleted"] is True
        assert "deleted_at" in delete_result

        # 验证批次目录已删除
        assert not batch_dir.exists()

    def test_delete_batch_not_found(self, service):
        """测试删除不存在的批次"""
        with pytest.raises(FileNotFoundError, match="批次不存在"):
            service.delete_batch("test_case_001", "nonexistent_batch")


@pytest.mark.asyncio
class TestBatchOptimizationServiceAsync:
    """批量仿真服务异步方法测试"""

    async def test_start_batch(self, service, temp_test_env):
        """测试启动批次"""
        # 创建批次
        create_result = service.create_batch(
            case_id="test_case_001",
            plan_ids=["baseline_plan"],
            num_seeds=2
        )

        batch_id = create_result["batch_id"]

        # Mock simulation_service
        class MockSimulationService:
            pass

        mock_service = MockSimulationService()

        # 启动批次（异步）
        start_result = await service.start_batch(
            case_id="test_case_001",
            batch_id=batch_id,
            simulation_service=mock_service
        )

        assert start_result["batch_id"] == batch_id
        assert start_result["status"] == "running"
        assert "started_at" in start_result

        # 短暂等待让后台任务启动
        await asyncio.sleep(0.5)

    async def test_start_batch_not_found(self, service):
        """测试启动不存在的批次"""
        class MockSimulationService:
            pass

        mock_service = MockSimulationService()

        with pytest.raises(FileNotFoundError, match="批次不存在"):
            await service.start_batch(
                case_id="test_case_001",
                batch_id="nonexistent_batch",
                simulation_service=mock_service
            )


class TestTimeSeriesExtraction:
    """时序数据提取功能测试"""

    @pytest.fixture
    def service_with_summary(self, temp_test_env, monkeypatch):
        """创建包含summary.xml文件的测试环境"""
        cases_dir = temp_test_env["cases_dir"]
        plans_dir = temp_test_env["plans_dir"]

        # Monkeypatch路径
        monkeypatch.setattr("api.services.batch_optimization_service.CASES_BASE_DIR", str(cases_dir))
        monkeypatch.setattr("api.services.batch_optimization_service.PLANS_BASE_DIR", str(plans_dir))
        monkeypatch.setattr("shared.control_tools.plan_file_manager.PLANS_BASE_DIR", str(plans_dir))

        # 创建批次目录
        batch_dir = cases_dir / "test_case_001" / "simulations" / "plan_opti" / "batch_test_001"
        batch_dir.mkdir(parents=True)

        # 创建批次元数据
        batch_metadata = {
            "batch_id": "batch_test_001",
            "case_id": "test_case_001",
            "plan_ids": ["baseline_plan", "plan_001"],
            "num_seeds": 2,
            "base_seed": 66,
            "created_at": datetime.now().isoformat()
        }

        with open(batch_dir / "batch_metadata.json", "w", encoding="utf-8") as f:
            json.dump(batch_metadata, f, ensure_ascii=False, indent=2)

        # 为每个方案创建仿真目录和summary.xml
        for plan_id in ["baseline_plan", "plan_001"]:
            plan_dir = batch_dir / plan_id
            plan_dir.mkdir()

            for seed in [66, 67]:
                sim_dir = plan_dir / f"sim_{seed}"
                sim_dir.mkdir()

                # 创建模拟的summary.xml
                summary_xml = self._create_mock_summary_xml(seed)
                with open(sim_dir / "summary.xml", "w", encoding="utf-8") as f:
                    f.write(summary_xml)

        service = BatchOptimizationService()
        yield service, cases_dir, plans_dir

    def _create_mock_summary_xml(self, seed):
        """创建模拟的summary.xml文件"""
        # 根据seed创建略有不同的数据以测试聚合
        base_running = 100 if seed == 66 else 105

        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<summary>\n'

        # 创建10个时间步的数据
        for i in range(10):
            time = i * 100  # 0, 100, 200, ..., 900
            running = base_running + i * 10  # 递增的在网车辆数
            loaded = (i + 1) * 20
            ended = i * 15
            mean_speed = 25.0 + i * 0.5

            xml_content += (
                f'    <step time="{time}" '
                f'running="{running}" '
                f'loaded="{loaded}" '
                f'ended="{ended}" '
                f'meanSpeed="{mean_speed}"/>\n'
            )

        xml_content += '</summary>'
        return xml_content

    def test_extract_time_series_from_summary_success(self, service_with_summary):
        """测试从summary.xml成功提取时序数据"""
        service, cases_dir, _ = service_with_summary

        result = service._extract_time_series_from_summary(
            case_id="test_case_001",
            batch_id="batch_test_001",
            plan_id="baseline_plan",
            seed=66
        )

        assert result is not None
        assert "time" in result
        assert "running" in result
        assert "loaded" in result
        assert "ended" in result
        assert "mean_speed" in result

        # 验证数据长度
        assert len(result["time"]) == 10
        assert len(result["running"]) == 10

        # 验证数据值
        assert result["time"][0] == 0.0
        assert result["time"][1] == 100.0
        assert result["running"][0] == 100
        assert result["loaded"][0] == 20
        assert result["ended"][0] == 0
        assert result["mean_speed"][0] == 25.0

    def test_extract_time_series_file_not_found(self, service_with_summary):
        """测试summary.xml文件不存在的情况"""
        service, _, _ = service_with_summary

        result = service._extract_time_series_from_summary(
            case_id="test_case_001",
            batch_id="batch_test_001",
            plan_id="baseline_plan",
            seed=999  # 不存在的seed
        )

        assert result is None

    def test_aggregate_time_series_success(self, service_with_summary):
        """测试时序数据聚合"""
        service, _, _ = service_with_summary

        # 模拟两次仿真的时序数据
        ts1 = {
            "time": [0, 100, 200],
            "running": [100, 110, 120],
            "loaded": [20, 40, 60],
            "ended": [0, 15, 30],
            "mean_speed": [25.0, 25.5, 26.0]
        }

        ts2 = {
            "time": [0, 100, 200],
            "running": [105, 115, 125],
            "loaded": [20, 40, 60],
            "ended": [0, 15, 30],
            "mean_speed": [25.0, 25.5, 26.0]
        }

        result = service._aggregate_time_series([ts1, ts2])

        assert result is not None
        assert "time_points" in result
        assert result["time_points"] == [0, 100, 200]

        # 验证running指标的聚合
        assert "running" in result
        assert "mean" in result["running"]
        assert "std" in result["running"]
        assert "min" in result["running"]
        assert "max" in result["running"]

        # 验证均值计算正确
        assert result["running"]["mean"][0] == 102.5  # (100 + 105) / 2
        assert result["running"]["mean"][1] == 112.5  # (110 + 115) / 2
        assert result["running"]["min"][0] == 100
        assert result["running"]["max"][0] == 105

    def test_aggregate_time_series_single_simulation(self, service_with_summary):
        """测试单次仿真的聚合（std应为0）"""
        service, _, _ = service_with_summary

        ts1 = {
            "time": [0, 100],
            "running": [100, 110],
            "loaded": [20, 40],
            "ended": [0, 15],
            "mean_speed": [25.0, 25.5]
        }

        result = service._aggregate_time_series([ts1])

        assert result is not None
        assert result["running"]["mean"][0] == 100
        assert result["running"]["std"][0] == 0.0  # 单次仿真标准差为0

    def test_aggregate_time_series_empty_list(self, service_with_summary):
        """测试空列表聚合"""
        service, _, _ = service_with_summary

        result = service._aggregate_time_series([])

        assert result == {}

    def test_extract_and_aggregate_time_series_success(self, service_with_summary):
        """测试端到端提取和聚合"""
        service, _, _ = service_with_summary

        # 创建模拟的任务列表
        from shared.control_tools.batch_simulation_scheduler import BatchTask

        tasks = [
            BatchTask(
                task_id="task_001",
                plan_id="baseline_plan",
                plan_name="基准方案",
                seed=66,
                status="completed",
                simulation_id="sim_001"
            ),
            BatchTask(
                task_id="task_002",
                plan_id="baseline_plan",
                plan_name="基准方案",
                seed=67,
                status="completed",
                simulation_id="sim_002"
            )
        ]

        result = service._extract_and_aggregate_time_series(
            case_id="test_case_001",
            batch_id="batch_test_001",
            plan_id="baseline_plan",
            tasks=tasks
        )

        assert result is not None
        assert "time_points" in result
        assert len(result["time_points"]) == 10  # 我们创建了10个时间步

        # 验证聚合了两次仿真
        assert "running" in result
        assert "mean" in result["running"]
        assert len(result["running"]["mean"]) == 10

        # 第一个时间点的均值应该是 (100 + 105) / 2 = 102.5
        assert result["running"]["mean"][0] == 102.5

    def test_extract_and_aggregate_no_completed_tasks(self, service_with_summary):
        """测试没有完成的任务时的聚合"""
        service, _, _ = service_with_summary

        from shared.control_tools.batch_simulation_scheduler import BatchTask

        tasks = [
            BatchTask(
                task_id="task_001",
                plan_id="baseline_plan",
                plan_name="基准方案",
                seed=66,
                status="pending",  # 未完成
                simulation_id=None
            )
        ]

        result = service._extract_and_aggregate_time_series(
            case_id="test_case_001",
            batch_id="batch_test_001",
            plan_id="baseline_plan",
            tasks=tasks
        )

        assert result is None

    def test_get_batch_results_with_time_series(self, service_with_summary):
        """测试get_batch_results包含时序数据"""
        service, cases_dir, _ = service_with_summary

        # 创建完整的批次进度数据
        batch_dir = cases_dir / "test_case_001" / "simulations" / "plan_opti" / "batch_test_001"

        progress_data = {
            "batch_id": "batch_test_001",
            "status": "completed",
            "progress": 1.0,
            "tasks": [
                {
                    "task_id": "task_001",
                    "plan_id": "baseline_plan",
                    "plan_name": "基准方案",
                    "seed": 66,
                    "status": "completed",
                    "simulation_id": "sim_001"
                },
                {
                    "task_id": "task_002",
                    "plan_id": "baseline_plan",
                    "plan_name": "基准方案",
                    "seed": 67,
                    "status": "completed",
                    "simulation_id": "sim_002"
                },
                {
                    "task_id": "task_003",
                    "plan_id": "plan_001",
                    "plan_name": "测试方案A",
                    "seed": 66,
                    "status": "completed",
                    "simulation_id": "sim_003"
                },
                {
                    "task_id": "task_004",
                    "plan_id": "plan_001",
                    "plan_name": "测试方案A",
                    "seed": 67,
                    "status": "completed",
                    "simulation_id": "sim_004"
                }
            ]
        }

        with open(batch_dir / "batch_progress.json", "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

        # 测试不包含时序数据
        result_without_ts = service.get_batch_results(
            case_id="test_case_001",
            batch_id="batch_test_001",
            include_time_series=False
        )

        assert "plan_results" in result_without_ts
        assert len(result_without_ts["plan_results"]) == 2  # 两个方案

        # 验证不包含时序数据
        for plan_result in result_without_ts["plan_results"]:
            assert "time_series" not in plan_result

        # 测试包含时序数据
        result_with_ts = service.get_batch_results(
            case_id="test_case_001",
            batch_id="batch_test_001",
            include_time_series=True
        )

        assert "plan_results" in result_with_ts

        # 验证包含时序数据
        for plan_result in result_with_ts["plan_results"]:
            assert "time_series" in plan_result
            ts = plan_result["time_series"]
            assert "time_points" in ts
            assert "running" in ts
            assert "mean" in ts["running"]
            assert len(ts["running"]["mean"]) == 10  # 10个时间步


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
