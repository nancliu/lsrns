"""
模板管理服务 - 负责各种模板的管理和获取
"""

import json
from typing import List

from ..models import TemplateInfo
from .base_service import BaseService


class TemplateService(BaseService):
    """模板管理服务类"""
    
    async def get_taz_templates(self) -> List[TemplateInfo]:
        """获取TAZ模板列表"""
        try:
            templates = []
            taz_dir = self.templates_dir / "taz_files"
            config_file = taz_dir / "taz_templates.json"
            
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                for template_id, template_data in config.get("taz_templates", {}).items():
                    template = TemplateInfo(
                        name=template_data["name"],
                        description=template_data["description"],
                        file_path=str(taz_dir / template_data["file_path"]),
                        version=template_data["version"],
                        created_date=template_data["created_date"],
                        status=template_data["validation_status"]
                    )
                    templates.append(template)
            
            return templates
            
        except Exception as e:
            raise Exception(f"获取TAZ模板失败: {str(e)}")
    
    async def get_network_templates(self) -> List[TemplateInfo]:
        """获取网络模板列表"""
        try:
            templates = []
            network_dir = self.templates_dir / "network_files"
            config_file = network_dir / "network_configs.json"
            
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                for template_id, template_data in config.get("network_templates", {}).items():
                    template = TemplateInfo(
                        name=template_data["name"],
                        description=template_data["description"],
                        file_path=str(network_dir / template_data["file_path"]),
                        version=template_data["version"],
                        created_date=template_data["created_date"],
                        status=template_data["status"]
                    )
                    templates.append(template)
            
            return templates
            
        except Exception as e:
            raise Exception(f"获取网络模板失败: {str(e)}")
    
    async def get_simulation_templates(self) -> List[TemplateInfo]:
        """获取仿真配置模板列表"""
        try:
            templates = []
            sim_dir = self.templates_dir / "config_templates" / "simulation_templates"
            
            template_files = {
                "microscopic.sumocfg": "微观仿真配置（默认）",
                "mesoscopic.sumocfg": "中观仿真配置"
            }
            
            for filename, description in template_files.items():
                file_path = sim_dir / filename
                if file_path.exists():
                    template = TemplateInfo(
                        name=filename,
                        description=description,
                        file_path=str(file_path),
                        version="1.0",
                        created_date="2025-01-08",
                        status="available"
                    )
                    templates.append(template)
            
            return templates
            
        except Exception as e:
            raise Exception(f"获取仿真模板失败: {str(e)}")


# 创建服务实例
template_service = TemplateService()


# 导出服务函数 (保持向后兼容)
async def get_taz_templates_service() -> List[TemplateInfo]:
    """获取TAZ模板服务函数"""
    return await template_service.get_taz_templates()


async def get_network_templates_service() -> List[TemplateInfo]:
    """获取网络模板服务函数"""
    return await template_service.get_network_templates()


async def get_simulation_templates_service() -> List[TemplateInfo]:
    """获取仿真模板服务函数"""
    return await template_service.get_simulation_templates()
