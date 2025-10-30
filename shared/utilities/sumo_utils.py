"""
SUMO配置工具函数（shared）
"""
from pathlib import Path
from typing import Dict, Any
import re
import os
from shared.utilities.time_utils import parse_datetime


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
		route_file = str(rel_to_config / Path(case_metadata['files']['routes_file']).name).replace('\\', '/')
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
	
	# 时间计算
	time_range = case_metadata.get('time_range', {})
	if time_range.get('start') and time_range.get('end'):
		start_dt = parse_datetime(time_range['start'])
		end_dt = parse_datetime(time_range['end'])
		duration = int((end_dt - start_dt).total_seconds())
	else:
		duration = 3600
	
	# 处理 edgeData additional 文件
	edgedata_files = []
	if simulation_params.get('output_edgedata', False):
		# 创建 edgedata 子目录
		edgedata_dir = simulation_folder / "edgedata"
		edgedata_dir.mkdir(exist_ok=True)

		# 选择模板（优先自定义，其次默认）；若均不存在则使用内置默认
		template_candidates = [
			Path("templates/edge_add/edgeData_custom.add.xml"),
			Path("templates/edge_add/edgeData.add.xml"),
		]
		edgedata_target = simulation_folder / "edgeData.add.xml"
		template_path = next((p for p in template_candidates if p.exists()), None)

		try:
			if template_path:
				with open(template_path, 'r', encoding='utf-8') as f:
					template_content = f.read()
			else:
				# 内置默认：全量边，不包含 edges 属性
				template_content = (
					'<?xml version="1.0" encoding="UTF-8"?>\n'
					'<additional>\n'
					'  <edgeData id="ed1"\n'
					'    freq="300"\n'
					'    file="edgedata.xml"\n'
					'    excludeEmpty="true"\n'
					'    withInternal="false"/>\n'
					'</additional>'
				)

			# 修改输出文件路径至 edgedata 子目录（如已是目标路径则保持不变）
			modified_content = re.sub(
				r'file="edgedata(?:/edgedata)?\.xml"',
				'file="edgedata/edgedata.xml"',
				template_content
			)

			# 默认移除模板中的 edges 属性（除非显式允许保留）
			# 通过 simulation_params['edgedata_use_template_edges']=True 保留模板 edges
			if not simulation_params.get('edgedata_use_template_edges', False):
				modified_content = re.sub(r'\s+edges="[^\"]*"', '', modified_content)

			with open(edgedata_target, 'w', encoding='utf-8') as f:
				f.write(modified_content)

			edgedata_files.append("edgeData.add.xml")
			if template_path:
				print(
					f"edgeData.add.xml 已由模板复制: {template_path} -> {edgedata_target}"
				)
			else:
				print(
					f"edgeData.add.xml 使用内置默认生成: {edgedata_target}"
				)
			print(
				f"EdgeData 输出将生成在: {simulation_folder / 'edgedata' / 'edgedata.xml'}"
			)
		except Exception as e:
			print(f"警告：edgeData.add.xml 生成失败: {e}")
	
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

	# 构建 additional 文件列表（TAZ + edgeData + 管控策略）
	additional_files = taz_files + edgedata_files + control_files
	
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
