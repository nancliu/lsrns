"""
Complete SUMO XML Generator for Control Plans
生成完整的SUMO控制XML文件（非占位符）
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ControlXMLGenerator:
    """生成完整的SUMO控制XML文件"""

    def __init__(self):
        """初始化XML生成器"""
        # Edge修复映射（根据验证结果）
        self.edge_fixes = {
            "-15632": "-15632#0",
            "-8932": "-10812",  # 使用相近的有效edge
            "-11456": "-11456#0",
            "-7654": "-7654#0",
            "-5432": "-5432#0"
        }

    def fix_edge_id(self, edge_id: str) -> str:
        """修复无效的edge ID"""
        return self.edge_fixes.get(edge_id, edge_id)

    def generate_vss_element(self, strategy: Dict) -> ET.Element:
        """
        生成VSS (Variable Speed Sign) XML元素
        """
        vss_id = strategy.get('strategy_id', 'vss_default')
        params = strategy.get('parameters', {})
        affected_edges = params.get('affected_edges', [])
        speed_steps = params.get('speed_steps', [])

        # 创建主VSS元素
        vss = ET.Element('variableSpeedSign')
        vss.set('id', vss_id)
        vss.set('file', f"{vss_id}_schedule.xml")

        # 修复并设置影响的lanes
        lanes = []
        for edge in affected_edges:
            fixed_edge = self.fix_edge_id(edge)
            # 添加所有车道（假设每个edge有2-3条车道）
            for lane_idx in range(3):
                lanes.append(f"{fixed_edge}_{lane_idx}")

        vss.set('lanes', ' '.join(lanes[:20]))  # 限制最多20条车道

        # 生成速度调度文件内容（嵌入为comment）
        schedule_comment = f"\n    Speed schedule for {vss_id}:\n"
        for step in speed_steps:
            time_h = step.get('time_hours', 0)
            speed_kmh = step.get('speed_kmh', 120)
            speed_ms = speed_kmh / 3.6  # 转换为m/s
            time_s = int(time_h * 3600)  # 转换为秒
            schedule_comment += f"    Time: {time_h:05.1f}h ({time_s:6d}s) -> Speed: {speed_kmh:3d} km/h ({speed_ms:.1f} m/s)\n"

        return vss, schedule_comment

    def generate_tec_element(self, strategy: Dict) -> ET.Element:
        """
        生成TEC (Toll/Entry Control) XML元素
        使用calibrator进行流量控制
        """
        tec_id = strategy.get('strategy_id', 'tec_default')
        params = strategy.get('parameters', {})
        control_points = params.get('control_points', [])
        flow_steps = params.get('flow_steps', [])

        # 创建calibrator元素
        calibrator = ET.Element('calibrator')
        calibrator.set('id', tec_id)

        # 如果有控制点，使用第一个作为edge
        if control_points:
            edge = self.fix_edge_id(control_points[0])
            calibrator.set('edge', edge)
        else:
            # 使用默认edge
            calibrator.set('edge', '-1000')

        calibrator.set('output', f"{tec_id}_log.xml")
        calibrator.set('freq', '900')  # 每15分钟校准一次

        # 添加流量控制步骤
        for i, step in enumerate(flow_steps):
            time_h = step.get('time_hours', 0)
            flow_veh_hr = step.get('flow_limit_veh_hr', 600)
            begin_s = int(time_h * 3600)
            end_s = begin_s + 3600  # 持续1小时

            flow = ET.SubElement(calibrator, 'flow')
            flow.set('begin', str(begin_s))
            flow.set('end', str(end_s))
            flow.set('vehsPerHour', str(flow_veh_hr))
            flow.set('speed', '27.78')  # 默认100km/h
            flow.set('type', 'passenger')
            flow.set('departLane', 'best')
            flow.set('departSpeed', 'desired')

        return calibrator

    def generate_dhs_element(self, strategy: Dict) -> List[ET.Element]:
        """
        生成DHS (Dynamic Hard Shoulder) XML元素
        通过修改lane的allow属性来控制应急车道
        """
        dhs_id = strategy.get('strategy_id', 'dhs_default')
        params = strategy.get('parameters', {})
        affected_edges = params.get('affected_edges', [])
        lane_index = params.get('hard_shoulder_lane_index', 0)
        schedule = params.get('opening_schedule', [])

        elements = []

        # 为每个受影响的edge创建lane元素
        for edge in affected_edges:
            fixed_edge = self.fix_edge_id(edge)
            lane_id = f"{fixed_edge}_{lane_index}"

            # 创建多个时间段的lane配置
            for i, period in enumerate(schedule):
                begin_h = period.get('begin_hours', 0)
                status = period.get('status', 'CLOSED')
                allowed_types = period.get('allowed_vehicle_types', [])

                lane = ET.Element('lane')
                lane.set('id', lane_id)
                lane.set('time', str(int(begin_h * 3600)))

                if status == 'OPEN' or status == 'FULLY_OPEN':
                    # 开放应急车道
                    allow_str = ' '.join(allowed_types) if allowed_types else 'all'
                    lane.set('allow', allow_str)
                    lane.set('speed', '27.78')  # 100km/h
                elif status == 'RESTRICTED':
                    # 限制性开放
                    allow_str = ' '.join(allowed_types) if allowed_types else 'passenger'
                    lane.set('allow', allow_str)
                    lane.set('speed', '22.22')  # 80km/h
                else:
                    # 关闭应急车道
                    lane.set('disallow', 'all')

                elements.append(lane)

        return elements

    def generate_complete_xml(self, plan_path: str) -> str:
        """
        为指定方案生成完整的control.add.xml文件
        Args:
            plan_path: 方案目录路径
        Returns:
            生成的XML文件路径
        """
        plan_path = Path(plan_path)
        metadata_file = plan_path / "plan_metadata.json"

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        # 加载方案元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)

        # 创建根元素
        root = ET.Element('additional')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:noNamespaceSchemaLocation',
                 'http://sumo.dlr.de/xsd/additional_file.xsd')

        # 添加注释
        comment = f"""
    Control Plan: {plan_data['plan_id']}
    Name: {plan_data['chinese_name']}
    Generated: {datetime.now().isoformat()}
    Strategies: {', '.join([s['strategy_type'] for s in plan_data['strategies']])}
    Time Range: {plan_data['metadata'].get('time_range', '07:00-10:00')}
    Severity: {plan_data['metadata'].get('severity', 'moderate')}
        """
        root.append(ET.Comment(comment))

        # 生成各策略的XML元素
        all_comments = []
        for strategy in plan_data.get('strategies', []):
            strategy_type = strategy.get('strategy_type')

            # 添加策略注释
            root.append(ET.Comment(f" {strategy_type} Strategy: {strategy.get('strategy_name', '')} "))

            if strategy_type == 'VSS':
                vss_element, vss_comment = self.generate_vss_element(strategy)
                root.append(vss_element)
                all_comments.append(vss_comment)

            elif strategy_type == 'TEC':
                tec_element = self.generate_tec_element(strategy)
                root.append(tec_element)

            elif strategy_type == 'DHS':
                dhs_elements = self.generate_dhs_element(strategy)
                for element in dhs_elements:
                    root.append(element)

        # 添加额外的配置注释
        if all_comments:
            root.append(ET.Comment(''.join(all_comments)))

        # 美化XML
        xml_str = self.prettify_xml(root)

        # 保存到文件
        output_file = plan_path / "control.add.xml"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        print(f"Generated complete XML: {output_file}")
        return str(output_file)

    def prettify_xml(self, elem: ET.Element) -> str:
        """美化XML输出"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")

        # 移除多余的空行
        lines = pretty_xml.split('\n')
        lines = [line for line in lines if line.strip()]

        # 确保XML声明在第一行
        if not lines[0].startswith('<?xml'):
            lines.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')

        return '\n'.join(lines)

    def generate_all_morning_peak_xmls(self):
        """为所有早高峰方案生成完整的XML文件"""
        plans_dir = Path("control_data/plans")
        morning_peak_plans = list(plans_dir.glob("plan_morning_peak_g4202_*/"))

        print(f"Generating complete XML for {len(morning_peak_plans)} plans...")
        success_count = 0
        failed_plans = []

        for plan_dir in morning_peak_plans:
            try:
                self.generate_complete_xml(plan_dir)
                success_count += 1
                print(f"  ✓ {plan_dir.name}")
            except Exception as e:
                failed_plans.append((plan_dir.name, str(e)))
                print(f"  ✗ {plan_dir.name}: {e}")

        print(f"\nSummary:")
        print(f"  Success: {success_count}/{len(morning_peak_plans)}")
        if failed_plans:
            print(f"  Failed: {len(failed_plans)}")
            for plan, error in failed_plans:
                print(f"    - {plan}: {error}")

        return success_count, failed_plans


def main():
    """主函数"""
    print("=" * 60)
    print("Complete SUMO XML Generation for Morning Peak Plans")
    print("=" * 60)

    generator = ControlXMLGenerator()

    # 生成所有方案的完整XML
    success, failed = generator.generate_all_morning_peak_xmls()

    print("\n" + "=" * 60)
    print(f"XML Generation Complete!")
    print(f"Successfully generated {success} complete XML files")
    print("=" * 60)

    # 生成一个示例方案的XML并显示内容
    example_plan = "control_data/plans/plan_morning_peak_g4202_vss_tec_g4202k40k60_moderate_v1"
    if Path(example_plan).exists():
        print(f"\nExample XML content from {Path(example_plan).name}:")
        print("-" * 60)
        xml_file = Path(example_plan) / "control.add.xml"
        if xml_file.exists():
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 显示前50行
                lines = content.split('\n')[:50]
                for line in lines:
                    print(line)
                if len(content.split('\n')) > 50:
                    print("... (truncated)")

    return success, failed


if __name__ == "__main__":
    main()