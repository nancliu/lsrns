"""
批量重新生成所有方案的control.add.xml文件

使用方法:
    python scripts/regenerate_all_plan_xmls.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import logging
from shared.control_tools import plan_file_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PLANS_BASE_DIR = "control_data/plans"


def main():
    """批量重新生成所有方案的XML文件"""

    # 读取方案索引
    index_file = Path(PLANS_BASE_DIR) / "plans_index.json"
    if not index_file.exists():
        logger.error(f"方案索引文件不存在: {index_file}")
        return

    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    plans = index_data.get("plans", [])
    total = len(plans)

    logger.info(f"找到 {total} 个方案，开始重新生成XML...")

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for i, plan_info in enumerate(plans, 1):
        plan_id = plan_info.get("plan_id")
        plan_name = plan_info.get("plan_name", "未命名")

        logger.info(f"\n[{i}/{total}] 处理方案: {plan_id} ({plan_name})")

        try:
            # 重新生成XML
            result = plan_file_manager.regenerate_plan_xml(plan_id)

            validation = result.get("validation", {})
            is_valid = validation.get("is_valid", False)
            warnings = validation.get("warnings", [])

            if is_valid:
                logger.info(f"✅ 成功: {plan_id}")
                if warnings:
                    logger.warning(f"   警告数量: {len(warnings)}")
                    for warning_msg in warnings[:3]:  # 只显示前3个警告
                        logger.warning(f"   - {warning_msg}")
                success_count += 1
            else:
                logger.error(f"❌ 验证失败: {plan_id}")
                for warning_msg in warnings:
                    logger.error(f"   - {warning_msg}")
                fail_count += 1

        except Exception as e:
            logger.error(f"❌ 失败: {plan_id} - {e}")
            fail_count += 1

    # 输出统计
    logger.info(f"\n{'='*60}")
    logger.info(f"批量重新生成完成:")
    logger.info(f"  总数: {total}")
    logger.info(f"  成功: {success_count}")
    logger.info(f"  失败: {fail_count}")
    logger.info(f"  跳过: {skipped_count}")
    logger.info(f"{'='*60}")

    if fail_count > 0:
        logger.warning(f"\n⚠️ 有 {fail_count} 个方案生成失败，请检查日志")
        sys.exit(1)
    else:
        logger.info(f"\n✅ 所有方案XML生成成功！")
        sys.exit(0)


if __name__ == "__main__":
    main()
