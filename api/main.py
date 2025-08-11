"""
OD数据处理与仿真系统 - FastAPI主程序入口
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse  # 新增
from api.routes import router
from api.compatibility import compatibility_router

# 创建FastAPI应用实例
app = FastAPI(
    title="OD数据处理与仿真系统",
    description="基于案例管理的OD数据处理与交通仿真系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    # 改为跳转到前端首页
    return RedirectResponse(url="/index.html")

# 注册路由
app.include_router(router, prefix="/api/v1")
app.include_router(compatibility_router, prefix="/api/v1/compat")

# 挂载静态文件
# 先挂载 cases，用于访问分析报告与图表
app.mount("/cases", StaticFiles(directory="cases"), name="cases")
# 再挂载前端
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)