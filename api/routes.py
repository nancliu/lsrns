"""
OD数据处理与仿真系统 - API路由定义
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from api.models import *
from api.services import *

# 创建路由器
router = APIRouter()

# ==================== 数据处理API ====================

@router.post("/process_od_data/", response_model=BaseResponse)
async def process_od_data(request: TimeRangeRequest):
    """
    处理OD数据
    """
    try:
        result = await process_od_data_service(request)
        return BaseResponse(
            success=True,
            message="OD数据处理成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OD数据处理失败: {str(e)}")

@router.post("/run_simulation/", response_model=BaseResponse)
async def run_simulation(request: SimulationRequest):
    """
    运行仿真
    """
    try:
        result = await run_simulation_service(request)
        return BaseResponse(
            success=True,
            message="仿真运行成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"仿真运行失败: {str(e)}")

@router.get("/simulation_progress/{case_id}")
async def get_simulation_progress(case_id: str):
    """
    获取仿真任务进度
    """
    try:
        data = await get_simulation_progress_service(case_id)
        return BaseResponse(success=True, message="获取进度成功", data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

@router.post("/analyze_accuracy/", response_model=BaseResponse)
async def analyze_accuracy(request: AccuracyAnalysisRequest):
    """
    精度分析
    """
    try:
        result = await analyze_accuracy_service(request)
        return BaseResponse(
            success=True,
            message="精度分析成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"精度分析失败: {str(e)}")

# ==================== 案例管理API ====================

@router.post("/create_case/", response_model=BaseResponse)
async def create_case(request: CaseCreationRequest):
    """
    创建新案例
    """
    try:
        result = await create_case_service(request)
        return BaseResponse(
            success=True,
            message="案例创建成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"案例创建失败: {str(e)}")

@router.get("/list_cases/", response_model=CaseListResponse)
async def list_cases(
    page: int = 1,
    page_size: int = 10,
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None
):
    """
    列出所有案例
    """
    try:
        result = await list_cases_service(page, page_size, status, search)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取案例列表失败: {str(e)}")

@router.get("/case/{case_id}", response_model=CaseMetadata)
async def get_case(case_id: str):
    """
    获取案例详情
    """
    try:
        result = await get_case_service(case_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"案例不存在: {str(e)}")

@router.delete("/case/{case_id}", response_model=BaseResponse)
async def delete_case(case_id: str):
    """
    删除案例
    """
    try:
        result = await delete_case_service(case_id)
        return BaseResponse(
            success=True,
            message="案例删除成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"案例删除失败: {str(e)}")

@router.post("/case/{case_id}/clone", response_model=BaseResponse)
async def clone_case(case_id: str, request: CaseCloneRequest):
    """
    克隆案例
    """
    try:
        result = await clone_case_service(case_id, request)
        return BaseResponse(
            success=True,
            message="案例克隆成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"案例克隆失败: {str(e)}")

# ==================== 文件管理API ====================

@router.get("/get_folders/{prefix}", response_model=List[FolderInfo])
async def get_folders(prefix: str):
    """
    获取文件夹列表
    """
    try:
        result = await get_folders_service(prefix)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件夹列表失败: {str(e)}")

@router.get("/accuracy_analysis_status/{result_folder}", response_model=AnalysisStatus)
async def get_accuracy_analysis_status(result_folder: str):
    """
    获取精度分析状态
    """
    try:
        result = await get_accuracy_analysis_status_service(result_folder)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析状态失败: {str(e)}")

# ==================== 精度结果回看API ====================

@router.get("/analysis_results/{case_id}", response_model=BaseResponse)
async def list_analysis_results(case_id: str, analysis_type: Optional[str] = "accuracy"):
    """
    按类型列出指定案例下的历史分析结果（accuracy | mechanism | performance）。
    """
    try:
        data = await list_analysis_results_service(case_id, analysis_type)
        return BaseResponse(success=True, message="获取分析结果成功", data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")

# ==================== 模板管理API ====================

@router.get("/templates/taz", response_model=List[TemplateInfo])
async def get_taz_templates():
    """
    获取TAZ模板列表
    """
    try:
        result = await get_taz_templates_service()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取TAZ模板失败: {str(e)}")

@router.get("/templates/network", response_model=List[TemplateInfo])
async def get_network_templates():
    """
    获取网络模板列表
    """
    try:
        result = await get_network_templates_service()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取网络模板失败: {str(e)}")

@router.get("/templates/simulation", response_model=List[TemplateInfo])
async def get_simulation_templates():
    """
    获取仿真配置模板列表
    """
    try:
        result = await get_simulation_templates_service()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仿真模板失败: {str(e)}")

# ==================== 工具API ====================

@router.get("/tools/taz/validate", response_model=BaseResponse)
async def validate_taz_file(file_path: str):
    """
    验证TAZ文件
    """
    try:
        result = await validate_taz_file_service(file_path)
        return BaseResponse(
            success=True,
            message="TAZ文件验证完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TAZ文件验证失败: {str(e)}")

@router.post("/tools/taz/fix", response_model=BaseResponse)
async def fix_taz_file(file_path: str):
    """
    修复TAZ文件
    """
    try:
        result = await fix_taz_file_service(file_path)
        return BaseResponse(
            success=True,
            message="TAZ文件修复完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TAZ文件修复失败: {str(e)}")

@router.post("/tools/taz/compare", response_model=BaseResponse)
async def compare_taz_files(file1: str, file2: str):
    """
    比较两个TAZ文件
    """
    try:
        result = await compare_taz_files_service(file1, file2)
        return BaseResponse(
            success=True,
            message="TAZ文件比较完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TAZ文件比较失败: {str(e)}") 