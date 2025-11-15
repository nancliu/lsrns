"""
SUMO配置工具函数（shared）
"""
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re
import os
import logging
import xml.etree.ElementTree as ET
from shared.utilities.time_utils import parse_datetime

logger = logging.getLogger(__name__)


def should_enable_edgedata_output(
	edge_count: int,
	validation_rate: float,
	min_edge_threshold: int = 10,
	min_validation_rate: float = 0.5
) -> tuple[bool, Dict[str, Any]]:
	"""
	智能决策：根据EdgeData聚合和验证结果，决定是否启用edgedata输出

	【P2修复 v2】简化规则：只要有验证通过的edge_id，就启用输出，保证有价值的分析结果

	原规则（v1）：同时满足数量 ≥ 10 且验证率 ≥ 50%
	新规则（v2）：只要有验证通过的边（edge_count > 0），就启用输出

	Args:
		edge_count: 聚合的边缘总数（已验证的边数）
		validation_rate: 边缘验证通过率（0-1）
		min_edge_threshold: 最小边缘数阈值（已废弃，保留向后兼容）
		min_validation_rate: 最小验证通过率阈值（已废弃，保留向后兼容）

	Returns:
		元组(should_enable, decision_info)，其中：
		- should_enable: bool，是否应启用edgedata输出
		- decision_info: dict，包含决策原因和详细信息

	示例:
		>>> should_enable, info = should_enable_edgedata_output(
		...     edge_count=2,  # 即使只有2条边
		...     validation_rate=0.5
		... )
		>>> print(info['decision_reason'])
		'Have verified edges (2), enable output for analysis'
	"""
	decision_info = {
		'edge_count': edge_count,
		'validation_rate': validation_rate,
		'min_edge_threshold': min_edge_threshold,
		'min_validation_rate': min_validation_rate,
		'checks': {},
		'decision_reason': '',
		'recommendations': []
	}

	# 新规则（P2 v2）：只检查是否有验证通过的边
	# edge_count > 0 表示有已验证的边，值得生成edgedata输出
	has_verified_edges = edge_count > 0
	decision_info['checks']['has_verified_edges'] = {
		'passed': has_verified_edges,
		'message': f'Verified edges: {edge_count} edge(s) found and validated' if has_verified_edges
			else 'No verified edges found'
	}

	# 做出决策：只要有验证通过的边就启用输出
	should_enable = has_verified_edges

	# 生成决策原因
	if should_enable:
		decision_info['decision_reason'] = f'Have verified edges ({edge_count}), enable output for analysis'
		decision_info['action'] = f'✅ 启用edgedata输出 ({edge_count}条已验证的边, 验证率{validation_rate:.1%})'
		decision_info['recommendations'].append(
			'EdgeData分析已启用，可以用于流量模式分析和优化决策'
		)
	else:
		decision_info['decision_reason'] = 'No verified edges found in network'
		decision_info['action'] = '❌ 禁用edgedata输出 (无验证通过的边，无法生成有价值的分析)'
		decision_info['recommendations'].append(
			'检查OD数据与事件标签的匹配度，或验证edge_id是否与路网一致'
		)

	logger.info(f"EdgeData决策 (P2 v2): {decision_info['decision_reason']}")
	logger.info(f"  - {decision_info['action']}")

	return should_enable, decision_info


def verify_edgedata_generation(simulation_folder: Path) -> bool:
	"""
	验证edgedata.xml是否成功生成

	Verifies that edgedata.xml was actually created after simulation completes.
	Used to detect silent collection failures.

	Args:
		simulation_folder: Path to simulation directory

	Returns:
		True if edgedata.xml exists and is valid

	Example:
		>>> verify_edgedata_generation(Path("cases/case_xxx/simulations/sim_xxx"))
		True
	"""
	edgedata_path = simulation_folder / "edgedata" / "edgedata.xml"

	if not edgedata_path.exists():
		logger.warning(f"EdgeData file not generated: {edgedata_path}")
		return False

	try:
		file_size = edgedata_path.stat().st_size
		if file_size == 0:
			logger.warning(f"EdgeData file is empty: {edgedata_path}")
			return False

		# Validate XML structure
		tree = ET.parse(edgedata_path)
		root = tree.getroot()

		# Check if root has edgeData elements
		edgedata_elements = root.findall('.//edgeData')
		if edgedata_elements:
			logger.info(f"✓ EdgeData file verified: {edgedata_path} ({file_size} bytes, {len(edgedata_elements)} edges)")
			return True
		else:
			logger.warning(f"EdgeData file has no edgeData elements: {edgedata_path}")
			return False

	except Exception as e:
		logger.warning(f"EdgeData file validation failed: {e}")
		return False


def aggregate_relevant_edges(case_metadata: Dict[str, Any], control_strategy_config: Dict[str, Any] = None) -> List[str]:
	"""
	从多个来源聚合相关边ID

	Aggregates edge IDs from multiple sources:
	1. Event location edge
	2. Control strategy affected edges

	Args:
		case_metadata: Case metadata (contains event_scenario)
		control_strategy_config: Control strategy configuration (optional)

	Returns:
		List of aggregated and deduplicated edge IDs

	Example:
		>>> edges = aggregate_relevant_edges(case_metadata, control_config)
		>>> # Returns: ["3026", "-3026", "3027", "-3027"]
	"""
	edges = set()

	# Source 1: Event location edge
	if 'event_scenario' in case_metadata:
		event_location = case_metadata['event_scenario'].get('event_location', {})
		event_edge = event_location.get('edge_id')
		if event_edge:
			edges.add(event_edge)
			# Add reverse direction
			if event_edge.startswith('-'):
				edges.add(event_edge[1:])
			else:
				edges.add(f"-{event_edge}")

	# Source 2: Control strategy affected edges (if provided)
	if control_strategy_config:
		try:
			strategy_edges = control_strategy_config.get('affected_edges', [])
			if strategy_edges:
				for edge in strategy_edges:
					if edge and isinstance(edge, str):
						edges.add(edge)
		except (AttributeError, TypeError) as e:
			logger.debug(f"Failed to extract edges from control strategy: {e}")

	return list(edges)


def validate_edge_ids_in_network(edge_ids: List[str], network_file: Path) -> Tuple[List[str], List[str]]:
	"""
	验证边ID是否存在于路网文件中

	Validates that edge IDs exist in the network file before configuration.
	Critical for preventing silent EdgeData collection failures.

	Args:
		edge_ids: List of edge IDs to validate (e.g., ["3026", "-3027"])
		network_file: Path to network.net.xml file

	Returns:
		Tuple of (valid_edge_ids, invalid_edge_ids)

	Example:
		>>> valid, invalid = validate_edge_ids_in_network(["3026", "-3026"], Path("network.net.xml"))
		>>> # valid = ["3026", "-3026"], invalid = []
	"""
	if not edge_ids or not network_file.exists():
		return edge_ids, []

	try:
		tree = ET.parse(network_file)
		root = tree.getroot()

		# Extract all edge IDs from network
		valid_edges = set()
		for edge in root.findall('.//edge'):
			valid_edges.add(edge.get('id'))

		# Filter input edge_ids to only valid ones
		validated_ids = [eid for eid in edge_ids if eid in valid_edges]
		invalid_ids = [eid for eid in edge_ids if eid not in valid_edges]

		# Log warnings for invalid edges
		if invalid_ids:
			logger.warning(f"Edge IDs not found in network (will be excluded from EdgeData): {invalid_ids}")

		if validated_ids:
			logger.info(f"✓ Validated {len(validated_ids)} edge IDs against network topology")

		return validated_ids, invalid_ids

	except Exception as e:
		logger.error(f"Failed to validate edge IDs against network: {e}")
		return edge_ids, []  # Fallback: assume valid if can't parse


def _duration_seconds(start_time: str, end_time: str) -> int:
	st = parse_datetime(start_time); et = parse_datetime(end_time)
	return int((et - st).total_seconds())


def generate_sumocfg(route_file: str, net_file: str, start_time: str, end_time: str, **kwargs) -> str:
	"""生成SUMO配置文件内容"""
	duration = _duration_seconds(start_time, end_time)
	route_val = (route_file or "").replace('\\', '/')
	net_val = (net_file or "").replace('\\', '/')
	add_val = (kwargs.get("additional_file") or "").replace('\\', '/') if kwargs.get("additional_file") else None
	output_prefix_val = (kwargs.get("output_prefix") or "").replace('\\', '/') if kwargs.get("output_prefix") else None
	summary_output_val = (kwargs.get("summary_output") or "").replace('\\', '/') if kwargs.get("summary_output") else None
	tripinfo_output_val = (kwargs.get("tripinfo_output") or "").replace('\\', '/') if kwargs.get("tripinfo_output") else None
	vehroute_output_val = (kwargs.get("vehroute_output") or "").replace('\\', '/') if kwargs.get("vehroute_output") else None
	netstate_output_val = (kwargs.get("netstate_output") or "").replace('\\', '/') if kwargs.get("netstate_output") else None
	fcd_output_val = (kwargs.get("fcd_output") or "").replace('\\', '/') if kwargs.get("fcd_output") else None
	emission_output_val = (kwargs.get("emission_output") or "").replace('\\', '/') if kwargs.get("emission_output") else None

	input_additional = f"\n        <additional-files value=\"{add_val}\"/>" if add_val else ""
	output_lines = []
	if output_prefix_val:
		output_lines.append(f"        <output-prefix value=\"{output_prefix_val}\"/>")
	if summary_output_val:
		output_lines.append(f"        <summary-output value=\"{summary_output_val}\"/>")
	if tripinfo_output_val:
		output_lines.append(f"        <tripinfo-output value=\"{tripinfo_output_val}\"/>")
	if vehroute_output_val:
		output_lines.append(f"        <vehroute-output value=\"{vehroute_output_val}\"/>")
	if netstate_output_val:
		output_lines.append(f"        <netstate-dump value=\"{netstate_output_val}\"/>")
	if fcd_output_val:
		output_lines.append(f"        <fcd-output value=\"{fcd_output_val}\"/>")
	if emission_output_val:
		output_lines.append(f"        <emission-output value=\"{emission_output_val}\"/>")
	output_block = ("\n    <output>\n" + "\n".join(output_lines) + "\n    </output>") if output_lines else ""
	return f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{net_val}"/>
        <route-files value="{route_val}"/>{input_additional}
    </input>{output_block}
    
    <time>
        <begin value="0"/>
        <end value="{duration}"/>
    </time>
    
    <processing>
        <ignore-route-errors value="true"/>
        <collision.action value="warn"/>
    </processing>
    
    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>
</configuration>'''


def save_sumocfg(config_content: str, config_file: str) -> bool:
	Path(config_file).parent.mkdir(parents=True, exist_ok=True)
	with open(config_file, "w", encoding="utf-8") as f:
		f.write(config_content)
	return True


def validate_sumocfg_paths(sumocfg_path: Path) -> tuple[bool, list[str]]:
	"""
	验证 sumocfg 文件中的所有路径是否可达 (Task 2.1 - Week 2 Phase 2)

	Args:
		sumocfg_path: sumocfg 文件路径

	Returns:
		(is_valid, error_list): 验证结果和错误列表

	Design: AD-13 - 可移植配置验证
	"""
	import xml.etree.ElementTree as ET

	errors = []

	if not sumocfg_path.exists():
		return False, [f"sumocfg file not found: {sumocfg_path}"]

	try:
		tree = ET.parse(sumocfg_path)
		root = tree.getroot()

		sumocfg_dir = sumocfg_path.parent

		# 验证 net-file
		net_elem = root.find(".//net-file")
		if net_elem is not None:
			net_path = sumocfg_dir / net_elem.get("value", "")
			if not net_path.exists():
				errors.append(f"Network file not found: {net_path}")

		# 验证 route-files
		route_elem = root.find(".//route-files")
		if route_elem is not None:
			route_value = route_elem.get("value", "")
			for route_file in route_value.split(","):
				route_file = route_file.strip()
				if route_file:
					route_path = sumocfg_dir / route_file
					if not route_path.exists():
						errors.append(f"Route file not found: {route_path}")

		# 验证 additional-files
		add_elem = root.find(".//additional-files")
		if add_elem is not None:
			add_value = add_elem.get("value", "")
			for add_file in add_value.split(","):
				add_file = add_file.strip()
				if add_file:
					add_path = sumocfg_dir / add_file
					if not add_path.exists():
						errors.append(f"Additional file not found: {add_path}")

		if errors:
			return False, errors

		return True, []

	except Exception as e:
		return False, [f"Failed to parse sumocfg: {str(e)}"]


def generate_sumocfg_for_simulation(case_metadata: dict, simulation_type, simulation_folder: Path, case_root: Path, simulation_params: dict | None = None) -> str:
	"""
	为仿真运行生成sumocfg配置文件

	设计原则：
	1. sumocfg位于sim_xxx目录下
	2. 所有路径相对于sumocfg文件位置计算
	3. 不使用output-prefix，避免路径拼接混乱
	4. 确保输出结果合理且一致
	5. TAZ文件自动复制到仿真目录，简化路径管理
	"""
	simulation_params = simulation_params or {}

	# 尝试读取 simulation metadata（如果存在）
	simulation_metadata = None
	sim_metadata_file = simulation_folder / "simulation_metadata.json"
	if sim_metadata_file.exists():
		try:
			import json
			with open(sim_metadata_file, 'r', encoding='utf-8') as f:
				simulation_metadata = json.load(f)
		except Exception as e:
			print(f"⚠️ Failed to load simulation metadata: {e}")

	# 动态计算相对路径（支持plan_opti深层目录结构）
	# 获取项目根目录（cases的父目录）
	project_root = case_root.parent.parent  # case_root是cases/{case_id}，向上2级到项目根

	# 计算从simulation_folder到case_root/config的相对路径
	config_dir = case_root / "config"
	try:
		rel_to_config = Path(os.path.relpath(config_dir, simulation_folder))
	except ValueError:
		# 跨盘符时relpath会失败，回退到绝对路径
		rel_to_config = config_dir

	# 计算从simulation_folder到project_root的相对路径
	try:
		rel_to_project = Path(os.path.relpath(project_root, simulation_folder))
	except ValueError:
		rel_to_project = project_root

	# 网络文件路径：动态计算相对路径
	network_file_path = case_metadata['files']['network_file']
	if network_file_path.startswith('templates/'):
		# 从simulation_folder到templates的相对路径
		net_file = str(rel_to_project / network_file_path).replace('\\', '/')
	else:
		# 从simulation_folder到case/config的相对路径
		net_file = str(rel_to_config / Path(network_file_path).name).replace('\\', '/')

	# 路由文件路径：动态计算相对路径
	route_files = []
	if 'routes_file' in case_metadata['files'] and case_metadata['files']['routes_file']:
		routes_file_ref = case_metadata['files']['routes_file']

		# 检查是否是数据库表名（不是 .rou.xml 文件）
		# 数据库表名格式：config/dwd.dwd_od_weekly
		# 实际文件格式：dwd_od_weekly_YYYYMMDDHHMMSS_YYYYMMDDHHMMSS.rou.xml
		if not routes_file_ref.endswith('.rou.xml'):
			# 尝试在 config 目录中查找对应的 .rou.xml 文件
			config_dir = case_root / "config"
			table_name = Path(routes_file_ref).name  # 提取表名部分（如 dwd.dwd_od_weekly）

			# 查找匹配的 .rou.xml 文件（格式：{table_name}_{timestamp}_{timestamp}.rou.xml）
			rou_files = list(config_dir.glob(f"{table_name}*.rou.xml"))

			if rou_files:
				# 使用找到的第一个 .rou.xml 文件
				actual_rou_file = rou_files[0].name
				route_file = str(rel_to_config / actual_rou_file).replace('\\', '/')
				logger.info(f"✓ Route file generated: {actual_rou_file}")
			else:
				# 没有找到 .rou.xml 文件，保持原有引用（向后兼容）
				# This is expected during initial creation before OD generation completes
				route_file = str(rel_to_config / Path(routes_file_ref).name).replace('\\', '/')
				logger.debug(f"Route file not yet available, using table reference: {routes_file_ref}")
		else:
			# 已经是 .rou.xml 文件，直接使用
			route_file = str(rel_to_config / Path(routes_file_ref).name).replace('\\', '/')

		route_files.append(route_file)
	
	# TAZ文件：复制到仿真目录，使用简单路径
	taz_files = []
	if 'taz_file' in case_metadata['files'] and case_metadata['files']['taz_file']:
		# 获取TAZ文件名（无论路径是绝对还是相对）
		taz_filename = Path(case_metadata['files']['taz_file']).name
		
		# 尝试从case/config目录复制TAZ文件到仿真目录
		source_taz = case_root / "config" / taz_filename
		target_taz = simulation_folder / taz_filename
		
		if source_taz.exists():
			try:
				import shutil
				shutil.copy2(source_taz, target_taz)
				# 使用文件名，相对路径为当前目录（仿真目录）
				taz_files.append(taz_filename)
				print(f"TAZ文件已复制到仿真目录: {target_taz}")
			except Exception as e:
				# 如果复制失败，回退到相对路径方式
				print(f"警告：TAZ文件复制失败，使用相对路径: {e}")
				taz_rel_path = str(rel_to_config / taz_filename).replace('\\', '/')
				taz_files.append(taz_rel_path)
		else:
			# 如果源文件不存在，使用相对路径
			print(f"警告：TAZ源文件不存在: {source_taz}")
			taz_rel_path = str(rel_to_config / taz_filename).replace('\\', '/')
			taz_files.append(taz_rel_path)
	
	# 时间计算 - 支持多种时间来源
	# 优先级: duration_hours参数 > 时间范围推导 > 默认值
	duration = None

	# 方法1: 使用simulation_params中的duration_hours（小时制）
	if simulation_params.get('duration_hours'):
		duration = int(simulation_params['duration_hours'] * 3600)
		logger.info(f"✓ 使用simulation_params的duration_hours: {simulation_params['duration_hours']}小时 = {duration}秒")
		print(f"使用simulation参数时长: {simulation_params['duration_hours']}小时 = {duration}秒")

	# 方法2: 使用case元数据中的时间范围 (支持多个位置)
	if duration is None:
		# 尝试多个位置查找time_range (支持不同的metadata结构)
		time_range = None

		# 位置1: 顶级 time_range
		if 'time_range' in case_metadata:
			time_range = case_metadata['time_range']
		# 位置2: case_config 中的 time_range
		elif 'case_config' in case_metadata and 'time_range' in case_metadata['case_config']:
			time_range = case_metadata['case_config']['time_range']

		if time_range:
			# 支持新格式 (start_time/end_time) 和旧格式 (start/end)
			start_key = 'start_time' if 'start_time' in time_range else 'start'
			end_key = 'end_time' if 'end_time' in time_range else 'end'

			if time_range.get(start_key) and time_range.get(end_key):
				try:
					start_dt = parse_datetime(time_range[start_key])
					end_dt = parse_datetime(time_range[end_key])
					duration = int((end_dt - start_dt).total_seconds())
					logger.info(f"✓ 使用case元数据时间范围: {duration}秒")
					logger.info(f"  - {start_key}: {time_range[start_key]}")
					logger.info(f"  - {end_key}: {time_range[end_key]}")
					print(f"使用case元数据时间范围: {duration}秒")
				except Exception as e:
					logger.warning(f"⚠️ 时间范围解析失败: {e}, 使用默认值")
					duration = None

	# 方法3: 默认时长 (1小时)
	if duration is None:
		duration = 3600
		logger.warning(f"⚠️ 使用默认仿真时长: {duration}秒 (1小时)")
		print(f"使用默认仿真时长: {duration}秒")
	
	# 处理 edgeData additional 文件
	edgedata_files = []
	if simulation_params.get('output_edgedata', False):
		# 创建 edgedata 子目录
		edgedata_dir = simulation_folder / "edgedata"
		edgedata_dir.mkdir(exist_ok=True)

		try:
			# ✅ IMPORTANT: 检查是否已经存在 case 级别的 edgeData.add.xml
			# 该文件应该由 generate_edgedata_xml_for_case() 生成（事件场景情况）
			# 或在案例初始化时创建（其他情况）
			case_edgedata_path = case_root / "config" / "edgeData.add.xml"

			if case_edgedata_path.exists():
				# ✓ 使用已有的 edgeData.add.xml 配置（已聚合事件和策略的边缘）
				logger.info(f"✓ 使用 case 级别的 edgeData.add.xml")
				print(f"✓ 使用 case 级别的 edgeData.add.xml（已聚合的边缘配置）")

				# 复制到仿真目录
				simulation_edgedata_path = simulation_folder / "edgeData.add.xml"
				import shutil
				shutil.copy2(case_edgedata_path, simulation_edgedata_path)
				print(f"✓ EdgeData 配置已复制到仿真目录: {simulation_edgedata_path}")

				edgedata_files.append("edgeData.add.xml")
				print(f"✓ EdgeData 输出将生成在: {simulation_folder / 'edgedata' / 'edgedata.xml'}")

			else:
				# ⚠️  回退方案：如果 case 级别的 edgeData.add.xml 不存在，生成全路网模式的备份
				# 这应该只发生在非事件场景或旧数据的兼容情况下
				logger.warning("未找到 case 级别的 edgeData.add.xml，生成全路网备份配置")
				print(f"⚠️  未找到已聚合的 edgeData 配置，使用全路网模式")

				# 全路网模式：不指定 edges 属性，收集整个网络
				template_content = (
					'<?xml version="1.0" encoding="UTF-8"?>\n'
					'<additional>\n'
					'  <!-- EdgeData configuration - full network mode (fallback) -->\n'
					'  <edgeData id="ed1"\n'
					'    freq="300"\n'
					'    file="edgedata/edgedata.xml"\n'
					'    excludeEmpty="true"\n'
					'    withInternal="false"/>\n'
					'</additional>'
				)

				# 保存到 case 的 config 目录
				config_edgedata_path = case_root / "config" / "edgeData.add.xml"
				with open(config_edgedata_path, 'w', encoding='utf-8') as f:
					f.write(template_content)
				print(f"✓ 已生成备份 edgeData 配置: {config_edgedata_path}")

				# 复制到仿真目录
				simulation_edgedata_path = simulation_folder / "edgeData.add.xml"
				import shutil
				shutil.copy2(config_edgedata_path, simulation_edgedata_path)
				print(f"✓ EdgeData 配置已复制到仿真目录: {simulation_edgedata_path}")

				edgedata_files.append("edgeData.add.xml")
				print(f"✓ EdgeData 输出将生成在: {simulation_folder / 'edgedata' / 'edgedata.xml'}")
				logger.warning("💡 建议：使用 generate_edgedata_xml_for_case() 生成特定场景的聚合边缘配置")

		except Exception as e:
			logger.error(f"EdgeData.add.xml 处理失败: {e}")
			print(f"⚠️  EdgeData 处理失败: {e}")
	
	# 处理管控策略additional文件（如果提供）
	control_files = []
	if simulation_params.get('additional_file'):
		additional_file_path = simulation_params['additional_file']
		# additional_file路径通常是相对于项目根目录的（如control_data/plans/xxx/control.add.xml）
		# 需要计算相对于simulation_folder的路径
		if Path(additional_file_path).is_absolute():
			# 绝对路径：计算相对路径
			try:
				control_rel_path = Path(os.path.relpath(additional_file_path, simulation_folder))
				control_files.append(str(control_rel_path).replace('\\', '/'))
			except ValueError:
				# 跨盘符，使用绝对路径
				control_files.append(str(additional_file_path).replace('\\', '/'))
		else:
			# 相对路径：假设相对于项目根目录
			control_rel_path = str(rel_to_project / additional_file_path).replace('\\', '/')
			control_files.append(control_rel_path)

	# 处理场景特定的 additional file（事件场景 .add.xml 文件）
	# 优先从 simulation_params 读取（每个场景独立），避免加载所有场景的文件
	case_additional_files = []
	if 'scenario_additional_file' in simulation_params and simulation_params['scenario_additional_file']:
		# scenario_additional_file 格式: "scenario_accident_tec_10807.add.xml" (仅文件名，文件已复制到仿真目录)
		scenario_add_file = simulation_params['scenario_additional_file']
		case_additional_files.append(scenario_add_file)
		print(f"✓ Adding scenario-specific additional file: {scenario_add_file}")
	else:
		# ✓ 向后兼容：自动发现模式（用于不支持 scenario_additional_file 的旧代码）
		# Auto-discovery used when scenario_additional_file not explicitly provided
		logger.debug("Scenario additional files not specified, auto-discovering .add.xml files...")
		discovered_add_files = list(simulation_folder.glob("scenario_*.add.xml"))
		if discovered_add_files:
			for discovered_file in discovered_add_files:
				# 仅使用文件名作为相对路径（文件在仿真目录中）
				case_additional_files.append(discovered_file.name)
				logger.debug(f"Auto-discovered scenario file: {discovered_file.name}")
		else:
			logger.debug("No scenario .add.xml files found in simulation directory")

	# 构建 additional 文件列表（TAZ + edgeData + 管控策略 + 事件场景）
	additional_files_raw = taz_files + edgedata_files + control_files + case_additional_files

	# 去重：防止同一文件被多次引入（如 TAZ 文件可能在 taz_files 和 case_additional_files 中都存在）
	seen = set()
	additional_files = []
	for file_path in additional_files_raw:
		# 标准化路径用于比较（去除路径分隔符差异）
		normalized = file_path.replace('\\', '/').lower()
		file_basename = Path(normalized).name

		# 检查是否已经添加过相同的文件（通过文件名判断）
		if file_basename not in seen:
			seen.add(file_basename)
			additional_files.append(file_path)
		else:
			print(f"⚠️ 跳过重复文件: {file_path} (已通过其他路径引入)")
	
	# 构建input section
	route_files_str = ",".join(route_files) if route_files else ""
	
	input_lines = [
		f'        <net-file value="{net_file}"/>'
	]
	
	if route_files_str:
		input_lines.append(f'        <route-files value="{route_files_str}"/>')
	
	if additional_files:
		input_lines.append(f'        <additional-files value="{",".join(additional_files)}"/>')
	
	input_section = f'''    <input>
{chr(10).join(input_lines)}
    </input>'''
	
	# 输出配置：不使用output-prefix，直接指定输出文件路径
	# 所有输出文件都保存在sim_xxx目录下
	output_lines = [
		'        <summary-output value="summary.xml"/>'
	]
	
	# 根据仿真参数添加其他输出选项
	# 注意：前端传递的参数名称是output_xxx格式
	if simulation_params.get('output_tripinfo', False):
		output_lines.append('        <tripinfo-output value="tripinfo.xml"/>')
	
	if simulation_params.get('output_vehroute', False):
		output_lines.append('        <vehroute-output value="vehroute.xml"/>')
	
	if simulation_params.get('output_netstate', False):
		output_lines.append('        <netstate-dump value="netstate.xml"/>')
	
	if simulation_params.get('output_fcd', False):
		output_lines.append('        <fcd-output value="fcd.xml"/>')
	
	if simulation_params.get('output_emission', False):
		output_lines.append('        <emission-output value="emission.xml"/>')

	# ✅ PHASE 1.2: 显式配置edgeData输出（当启用edgeData集合时）
	if simulation_params.get('output_edgedata', False):
		output_lines.append('        <edgedata-output value="edgedata/edgedata.xml"/>')
	
	output_section = f'''    <output>
{chr(10).join(output_lines)}
    </output>'''
	
	# 处理配置
	processing_section = '''    <processing>
        <ignore-route-errors value="true"/>
        <collision.action value="warn"/>
    </processing>'''
	
	# 仿真类型特定配置
	mesoscopic_section = ""
	if getattr(simulation_type, 'value', '') == 'mesoscopic':
		mesoscopic_section = '''    <mesosim>
        <meso-recheck value="0.1"/>
        <meso-multi-queue value="true"/>
        <meso-junction-control value="true"/>
    </mesosim>'''
	
	routing_section = ""
	if getattr(simulation_type, 'value', '') == 'microscopic':
		routing_section = '''    <routing>
        <device.rerouting.probability value="0.1"/>
        <device.rerouting.explicit value="true"/>
    </routing>'''
	
	# 生成完整的sumocfg内容
	return f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
{input_section}
{output_section}
    
    <time>
        <begin value="0"/>
        <end value="{duration}"/>
    </time>
    
{processing_section}
    
    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>
{mesoscopic_section}
{routing_section}
</configuration>'''


def generate_edgedata_xml_for_case(
	case_root: Path,
	event_location: Dict[str, Any],
	strategies_config: list,
	network_file: str,
	event_method: str = "radius_2_hops"
) -> Dict[str, Any]:
	"""
	为案例生成统一的edgeData.add.xml配置文件

	此函数聚合事件和所有管控策略的影响边缘，生成一个完整的edgeData配置，
	在该案例的所有仿真场景中共用。

	Args:
		case_root: 案例根目录路径
		event_location: 事件位置信息字典，包含edge_id, junction_id等
		strategies_config: 策略配置列表，每个策略包含strategy_type和parameters
		network_file: SUMO路网文件路径（用于验证）
		event_method: 事件边缘提取方法 (primary_only, radius_1_hop, radius_2_hops, full_junction)

	Returns:
		生成结果字典，包含:
		- file_path: 生成的文件路径
		- edge_count: 边缘总数
		- source_breakdown: 来源分解统计
		- validation: 验证结果

	使用示例:
		>>> result = generate_edgedata_xml_for_case(
		...     case_root=Path("cases/case_20250115_001"),
		...     event_location={"edge_id": "3026", "junction_id": "J1"},
		...     strategies_config=[
		...         {"strategy_type": "VSS", "parameters": {"edge_range": ["3000", "3050"]}},
		...         {"strategy_type": "TEC", "parameters": {"entrance_edges": ["3100"]}}
		...     ],
		...     network_file="templates/network_files/highway.net.xml"
		... )
		>>> print(result['edge_count'])
		122
	"""
	from shared.utilities.edge_aggregator import aggregate_edgedata_edges

	# 1. 聚合边缘
	aggregation_result = aggregate_edgedata_edges(
		event_location=event_location,
		strategies_config=strategies_config,
		network_file=network_file,
		event_method=event_method
	)

	merged_edges = aggregation_result.get('merged_edges', [])
	source_breakdown = aggregation_result.get('source_breakdown', {})
	validation = aggregation_result.get('validation', {})

	# 2. 生成 edgeData.add.xml 内容
	# ✅ 使用验证通过的边（仅包含路网中实际存在的边）
	valid_edges = validation.get('valid_edges', merged_edges)
	invalid_edges = validation.get('invalid_edges', [])

	if valid_edges:
		# 使用验证后的有效边缘列表
		edges_str = " ".join(valid_edges)
		template_content = (
			'<?xml version="1.0" encoding="UTF-8"?>\n'
			'<additional>\n'
			'  <!-- EdgeData configuration for event case -->\n'
			f'  <!-- Total edges (validated): {len(valid_edges)} -->\n'
			f'  <!-- Event edges: {aggregation_result.get("event_count", 0)} -->\n'
			f'  <!-- Strategy edges: {aggregation_result.get("strategy_count", 0)} -->\n'
			f'  <!-- Invalid edges excluded: {len(invalid_edges)} -->\n'
			'  <edgeData id="ed1"\n'
			'    freq="300"\n'
			'    file="edgedata/edgedata.xml"\n'
			f'    edges="{edges_str}"\n'
			'    excludeEmpty="true"\n'
			'    withInternal="false"/>\n'
			'</additional>'
		)
		print(f"✓ EdgeData 配置生成: 聚合了 {len(valid_edges)} 条有效边（验证通过）")
		print(f"  - 事件边缘: {aggregation_result.get('event_count', 0)} 条")
		print(f"  - 策略边缘: {aggregation_result.get('strategy_count', 0)} 条")
		print(f"  - 路网验证: {len(valid_edges)} 有效 / {len(invalid_edges)} 无效")
		print(f"  - 来源分解: {source_breakdown}")
		if invalid_edges:
			print(f"  ⚠️ 排除的无效边: {invalid_edges}")
	else:
		# 回退：收集全路网（如果无法提取任何边缘）
		template_content = (
			'<?xml version="1.0" encoding="UTF-8"?>\n'
			'<additional>\n'
			'  <!-- EdgeData configuration - full network mode -->\n'
			'  <edgeData id="ed1"\n'
			'    freq="300"\n'
			'    file="edgedata/edgedata.xml"\n'
			'    excludeEmpty="true"\n'
			'    withInternal="false"/>\n'
			'</additional>'
		)
		print(f"⚠️ EdgeData 配置: 未提取到任何边缘，使用全路网模式")

	# 3. 保存到 case 的 config 目录
	config_dir = case_root / "config"
	config_dir.mkdir(exist_ok=True)

	config_edgedata_path = config_dir / "edgeData.add.xml"
	with open(config_edgedata_path, 'w', encoding='utf-8') as f:
		f.write(template_content)

	print(f"✓ EdgeData 配置文件已保存: {config_edgedata_path}")

	# 4. 智能决策：根据验证结果决定是否启用edgedata输出
	validation_rate = validation.get('validation_rate', 0.0)
	should_enable, decision_info = should_enable_edgedata_output(
		edge_count=len(merged_edges),
		validation_rate=validation_rate,
		min_edge_threshold=10,  # 至少10条有效边
		min_validation_rate=0.5   # 验证通过率至少50%
	)

	# 5. 返回结果（包含智能决策信息）
	return {
		'file_path': str(config_edgedata_path),
		'edge_count': len(merged_edges),
		'source_breakdown': source_breakdown,
		'validation': validation,
		'aggregation_result': aggregation_result,
		'edgedata_decision': {
			'should_enable': should_enable,
			'reason': decision_info['decision_reason'],
			'action': decision_info['action'],
			'details': decision_info
		}
	}
