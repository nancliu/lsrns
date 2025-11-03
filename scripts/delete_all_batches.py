"""
删除所有批量仿真批次

功能：
- 遍历所有case目录，查找batches_index.json
- 读取所有批次记录
- 对于运行中的批次，先尝试取消
- 删除所有批次目录
- 清空索引文件中的批次记录
"""

import json
import logging
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CASES_BASE_DIR = Path("cases")
MAX_DELETE_RETRIES = 3
RETRY_DELAY = 0.5


def load_batches_index(case_id: str) -> Dict[str, Any]:
    """加载批次索引文件"""
    index_path = CASES_BASE_DIR / case_id / "simulations" / "plan_opti" / "batches_index.json"
    
    if not index_path.exists():
        logger.debug(f"索引文件不存在: {index_path}")
        return {"batches": [], "last_updated": None}
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载索引文件失败 {index_path}: {e}")
        return {"batches": [], "last_updated": None}


def save_batches_index(case_id: str, index: Dict[str, Any]) -> None:
    """保存批次索引文件（清空批次记录）"""
    index_path = CASES_BASE_DIR / case_id / "simulations" / "plan_opti" / "batches_index.json"
    
    if not index_path.exists():
        logger.debug(f"索引文件不存在，无需清空: {index_path}")
        return
    
    # 清空批次记录
    index["batches"] = []
    index["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        logger.info(f"已清空索引文件: {index_path}")
    except Exception as e:
        logger.error(f"保存索引文件失败 {index_path}: {e}")
        raise


def cancel_running_batch(case_id: str, batch_id: str) -> bool:
    """尝试取消运行中的批次"""
    try:
        # 尝试导入batch_optimization_service
        import sys
        from pathlib import Path
        
        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from api.services.batch_optimization_service import batch_optimization_service
        
        logger.info(f"尝试取消批次: {batch_id}")
        batch_optimization_service.cancel_batch(case_id, batch_id)
        
        # 等待一下让进程完全关闭
        time.sleep(1)
        logger.info(f"批次已取消: {batch_id}")
        return True
    except ImportError as e:
        logger.warning(f"无法导入服务模块，跳过取消操作: {batch_id}, 错误: {e}")
        return False
    except Exception as e:
        logger.warning(f"取消批次失败（可能已完成或不存在）: {batch_id}, 错误: {e}")
        return False


def delete_batch_directory(case_id: str, batch_id: str) -> bool:
    """删除批次目录，带重试机制"""
    batch_dir = CASES_BASE_DIR / case_id / "simulations" / "plan_opti" / batch_id
    
    if not batch_dir.exists():
        logger.debug(f"批次目录不存在: {batch_dir}")
        return True
    
    # 重试删除
    for attempt in range(MAX_DELETE_RETRIES):
        try:
            shutil.rmtree(batch_dir)
            logger.info(f"已删除批次目录: {batch_id} (尝试 {attempt + 1}/{MAX_DELETE_RETRIES})")
            return True
        except PermissionError as e:
            if attempt < MAX_DELETE_RETRIES - 1:
                logger.warning(f"删除批次目录失败（权限问题），重试中: {batch_id}, 尝试 {attempt + 1}/{MAX_DELETE_RETRIES}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"删除批次目录失败（权限问题）: {batch_id}, 错误: {e}")
                return False
        except Exception as e:
            logger.error(f"删除批次目录失败: {batch_id}, 错误: {e}")
            return False
    
    return False


def delete_all_batches_for_case(case_id: str) -> Dict[str, Any]:
    """删除某个case下的所有批次"""
    logger.info(f"开始处理case: {case_id}")
    
    # 加载索引文件
    index = load_batches_index(case_id)
    batches = index.get("batches", [])
    
    if not batches:
        logger.info(f"case {case_id} 没有批次记录")
        return {
            "case_id": case_id,
            "total_batches": 0,
            "deleted": 0,
            "failed": 0,
            "skipped": 0
        }
    
    logger.info(f"找到 {len(batches)} 个批次记录")
    
    deleted_count = 0
    failed_count = 0
    skipped_count = 0
    
    # 遍历所有批次
    for batch in batches:
        batch_id = batch.get("batch_id")
        status = batch.get("status", "unknown")
        
        if not batch_id:
            logger.warning(f"批次记录缺少batch_id，跳过")
            skipped_count += 1
            continue
        
        logger.info(f"处理批次: {batch_id} (状态: {status})")
        
        # 如果是运行中的批次，先尝试取消
        if status == "running":
            cancel_running_batch(case_id, batch_id)
        
        # 删除批次目录
        if delete_batch_directory(case_id, batch_id):
            deleted_count += 1
        else:
            failed_count += 1
    
    # 清空索引文件
    try:
        save_batches_index(case_id, index)
    except Exception as e:
        logger.error(f"清空索引文件失败: {case_id}, 错误: {e}")
    
    result = {
        "case_id": case_id,
        "total_batches": len(batches),
        "deleted": deleted_count,
        "failed": failed_count,
        "skipped": skipped_count
    }
    
    logger.info(f"case {case_id} 处理完成: {result}")
    return result


def delete_all_batches() -> Dict[str, Any]:
    """删除所有case下的所有批次"""
    logger.info("=" * 60)
    logger.info("开始删除所有批量仿真批次")
    logger.info("=" * 60)
    
    if not CASES_BASE_DIR.exists():
        logger.warning(f"cases目录不存在: {CASES_BASE_DIR}")
        return {"error": "cases目录不存在"}
    
    case_results = []
    total_batches = 0
    total_deleted = 0
    total_failed = 0
    total_skipped = 0
    
    # 遍历所有case目录
    for case_dir in CASES_BASE_DIR.iterdir():
        if not case_dir.is_dir():
            continue
        
        case_id = case_dir.name
        
        # 检查是否有plan_opti目录和索引文件
        index_path = case_dir / "simulations" / "plan_opti" / "batches_index.json"
        if not index_path.exists():
            logger.debug(f"case {case_id} 没有批次索引文件，跳过")
            continue
        
        # 处理该case下的所有批次
        result = delete_all_batches_for_case(case_id)
        case_results.append(result)
        
        total_batches += result["total_batches"]
        total_deleted += result["deleted"]
        total_failed += result["failed"]
        total_skipped += result["skipped"]
    
    summary = {
        "total_cases": len(case_results),
        "total_batches": total_batches,
        "total_deleted": total_deleted,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "case_results": case_results
    }
    
    logger.info("=" * 60)
    logger.info("删除完成")
    logger.info(f"处理case数: {summary['total_cases']}")
    logger.info(f"总批次数: {summary['total_batches']}")
    logger.info(f"成功删除: {summary['total_deleted']}")
    logger.info(f"删除失败: {summary['total_failed']}")
    logger.info(f"跳过: {summary['total_skipped']}")
    logger.info("=" * 60)
    
    return summary


if __name__ == "__main__":
    try:
        result = delete_all_batches()
        
        # 打印JSON格式的结果（便于查看）
        print("\n" + "=" * 60)
        print("删除结果摘要（JSON格式）:")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"删除过程中发生错误: {e}", exc_info=True)
        exit(1)

