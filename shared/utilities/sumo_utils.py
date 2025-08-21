"""
SUMO配置工具函数（shared）
"""
from pathlib import Path
from typing import Dict, Any
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
	
	# 网络文件路径：从sim_xxx目录到各文件的相对路径计算
	network_file_path = case_metadata['files']['network_file']
	if network_file_path.startswith('templates/'):
		# 从sim_xxx目录到templates目录的相对路径
		# sim_xxx -> simulations -> case_xxx -> cases -> 项目根目录 -> templates
		net_file = f"../../../../{network_file_path}"
	else:
		# 从sim_xxx目录到case/config目录的相对路径
		net_file = f"../../config/{Path(network_file_path).name}"
	
	# 路由文件路径：从sim_xxx目录到case/config目录的相对路径
	route_files = []
	if 'routes_file' in case_metadata['files'] and case_metadata['files']['routes_file']:
		# sim_xxx -> simulations -> case_xxx -> config
		route_files.append(f"../../config/{Path(case_metadata['files']['routes_file']).name}")
	
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
				# 如果复制失败，回退到原来的相对路径方式
				print(f"警告：TAZ文件复制失败，使用相对路径: {e}")
				taz_files.append(f"../../config/{taz_filename}")
		else:
			# 如果源文件不存在，使用相对路径
			print(f"警告：TAZ源文件不存在: {source_taz}")
			taz_files.append(f"../../config/{taz_filename}")
	
	# 时间计算
	time_range = case_metadata.get('time_range', {})
	if time_range.get('start') and time_range.get('end'):
		start_dt = parse_datetime(time_range['start'])
		end_dt = parse_datetime(time_range['end'])
		duration = int((end_dt - start_dt).total_seconds())
	else:
		duration = 3600
	
	# 构建input section
	route_files_str = ",".join(route_files) if route_files else ""
	
	input_lines = [
		f'        <net-file value="{net_file}"/>'
	]
	
	if route_files_str:
		input_lines.append(f'        <route-files value="{route_files_str}"/>')
	
	if taz_files:
		input_lines.append(f'        <additional-files value="{",".join(taz_files)}"/>')
	
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
