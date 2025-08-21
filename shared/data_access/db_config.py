import os
from typing import Dict, Any


def get_db_config() -> Dict[str, Any]:
    """从环境变量获取数据库配置。"""
    return {
        "host": os.getenv("DB_HOST", "10.149.235.123"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "sdzg"),
        "user": os.getenv("DB_USER", "ln"),
        "password": os.getenv("DB_PASSWORD", "caneln"),
    }

