import os
import sys
import json
import uuid
import logging
import asyncio
import argparse
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ============ 导入VISTA模块 ============
from vista.src.utils.HyperParameters import configure_parser
from vista.src.utils.Evaluation import evaluate_imputed_result
from vista.src.utils.utils import setup_logging, get_root_path
from vista.src.data.AISDataProcess import get_training_test_data
from vista.src.pipeline.pipeline import SDKG_Construction_Multithreading, Trajectory_Imputation_Multithreading
from vista.src.modules.M0_SDKG import SDKG
from vista.src.modules.M7_Scheduler import KnowledgeUnitManager, ImputationResultsManager

# 获取根路径
root_path = get_root_path()

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter(prefix="/vista", tags=["vista"])

# ============ 本地JSON文件存储 ============

class JSONTaskStorage:
    def __init__(self, storage_dir: str = "./task_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_task_filepath(self, task_id: str) -> Path:
        return self.storage_dir / f"{task_id}.json"
    
    def save_task(self, task_id: str, task_data: Dict):
        filepath = self._get_task_filepath(task_id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        filepath = self._get_task_filepath(task_id)
        if not filepath.exists():
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_task_progress(self, task_id: str, progress: float, status: str = "running", message: str = None):
        task = self.get_task(task_id)
        if task:
            task["progress"] = progress
            task["status"] = status
            task["updated_at"] = datetime.now().isoformat()
            if message:
                task["message"] = message
            self.save_task(task_id, task)
    
    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        tasks = []
        for filepath in self.storage_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                task = json.load(f)
            if status is None or task.get("status") == status:
                tasks.append(task)
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return tasks[:limit]

# 初始化任务存储和线程池
task_storage = JSONTaskStorage(storage_dir="/mnt/aisdata/Haoyu/CLEAR/task_storage")
executor = ThreadPoolExecutor(max_workers=4)

# ============ VISTARequest模型 ============

class VISTARequest(BaseModel):
    # 前端字段（前端form中的v-model）
    dataset: Optional[str] = None
    apikey: Optional[str] = None
    platform: Optional[str] = None
    miningModel: Optional[str] = None
    codingModel: Optional[str] = None
    imputationModel: Optional[str] = None
    
    # 前端数值参数
    topK: Optional[int] = None
    trajectoryNum: Optional[int] = None
    trajectoryLen: Optional[int] = None
    miniSegmentLen: Optional[int] = None
    missingRatio: Optional[float] = None
    minTimeInterval: Optional[int] = None
    maxTimeInterval: Optional[int] = None
    eF: Optional[float] = None  
    concurrentNum: Optional[int] = None
    maxRetries: Optional[int] = None
    retryTimes: Optional[int] = None
    
    # 后端默认值（前端不提供时使用）
    llm_api_key: str = Field(default="")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # 种子、实验名称等固定参数（前端不需要设置）
    seed: int = Field(default=40)
    exp_name: str = Field(default="Default_1")
    end_point_sdkg: int = Field(default=800)
    check_point: int = Field(default=0)
    process_length: int = Field(default=2)
    end_point: int = Field(default=200)
    pre_load: bool = Field(default=False)

# ============ 响应模型 ============

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    created_at: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    message: Optional[str] = None
    result: Optional[Dict] = None
    created_at: str
    updated_at: str

# ============ 任务管理函数 ============

def _save_task(task_id: str, task_data: Dict):
    task_storage.save_task(task_id, task_data)

def _get_task(task_id: str) -> Optional[Dict]:
    return task_storage.get_task(task_id)

def _update_task_progress(task_id: str, progress: float, status: str = "running", message: str = None):
    task_storage.update_task_progress(task_id, progress, status, message)

# ============ 参数映射函数 ============

def _create_args_namespace_from_request(request: Dict) -> argparse.Namespace:
    """从前端请求创建argparse.Namespace对象"""
    
    # 获取parser的默认值
    parser = configure_parser()
    defaults = {}
    for action in parser._actions:
        if action.dest != 'help':
            defaults[action.dest] = action.default
    
    # 参数映射
    mapping = {
        'apikey': 'llm_api_key',
        'miningModel': 'mining_llm',
        'codingModel': 'coding_llm',
        'imputationModel': 'analysis_llm',
        'topK': 'top_k',
        'trajectoryNum': 'trajectory_num',
        'trajectoryLen': 'trajectory_len',
        'miniSegmentLen': 'mini_segment_len',
        'missingRatio': 'missing_ratio',
        'retryTimes': 'retry_times',
        'eF': 'e_f',
        'concurrentNum': 'max_concurrent',
        'maxRetries': 'max_retries',
        'minTimeInterval': 'min_time_interval',
        'maxTimeInterval': 'max_time_interval',
    }
    
    # 更新映射的参数
    for frontend, backend in mapping.items():
        if frontend in request and request[frontend] is not None:
            defaults[backend] = request[frontend]
    
    # 直接参数
    if 'dataset' in request:
        defaults['dataset'] = request['dataset']
    
    # 处理platform和base_url
    platform = request.get('platform', 'alibaba').lower()
    if platform == 'openai':
        defaults['base_url'] = 'https://api.openai.com/v1'
    else:  # alibaba或其他
        defaults['base_url'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    
    # 前端可覆盖base_url
    if 'base_url' in request and request['base_url']:
        defaults['base_url'] = request['base_url']
    
    # 设置数据文件路径
    dataset = defaults.get('dataset', 'demo-dk')
    if dataset == "demo-dk":
        defaults['raw_data_file'] = f"{root_path}/data/CleanedFilteredData/aisdk-2024-03-01@31_filtered10_1000000000.csv"
    elif dataset == "demo-us":
        defaults['raw_data_file'] = f"{root_path}/data/CleanedFilteredData/AIS_2024_04_01@15_filtered360_1000000000.csv"
    else:
        defaults['raw_data_file'] = f"{root_path}/data/CleanedFilteredData/aisdk-2024-03-01@31_filtered10_1000000000.csv"
    
    if dataset == "demo-dk":
        defaults['exp_name'] = "Default"
    elif dataset == "demo-us":
        defaults['exp_name'] = "Default_us"
    # 创建Namespace
    args = argparse.Namespace()
    for key, value in defaults.items():
        setattr(args, key, value)
    
    return args

# ============ VISTA任务执行函数 ============

def _run_sdkg_build_task(task_id: str, request_data: Dict):
    """执行SD-KG构建任务"""
    try:
        _update_task_progress(task_id, 10, "running", "开始创建参数")
        
        # 创建参数
        args = _create_args_namespace_from_request(request_data)
        
        _update_task_progress(task_id, 20, "running", "设置日志")
        setup_logging(args)
        
        _update_task_progress(task_id, 30, "running", "获取训练和测试数据")
        _, (test_df, mark_missing_test) = get_training_test_data(args)
        
        _update_task_progress(task_id, 40, "running", "初始化SDKG和知识单元管理器")
        sdkg = SDKG(args)
        ku_manager = KnowledgeUnitManager(args)
        sdkg.load_SDKG(args.end_point_sdkg)
        ku_manager.load_knowledge_unit_list(args.end_point_sdkg)
        _update_task_progress(task_id, 50, "running", "开始SD-KG构建")
        if((not sdkg.SDK_graph_vs) or (not ku_manager.knowledge_unit_list)):
            logging.info("Starting SD-KG Construction...")
            sdkg, ku_manager = SDKG_Construction_Multithreading(
                args=args,
                trajectory_data=(test_df, mark_missing_test),
                ku_manager=ku_manager,
                SDKG=sdkg,
            )
        
        _update_task_progress(task_id, 90, "running", "保存构建结果")
        _update_task_progress(task_id, 100, "done", "SD-KG构建完成")
        
        # 保存任务结果
        task = _get_task(task_id)
        if task:
            task["result"] = {
                "status": "success",
                "sdkg_nodes": len(sdkg.SDK_graph_vs) if hasattr(sdkg, 'SDK_graph_vs') else 0,
                "knowledge_units": len(ku_manager.knowledge_unit_list) if ku_manager.knowledge_unit_list else 0
            }
            _save_task(task_id, task)
            
    except Exception as e:
        logging.error(f"SD-KG构建任务失败: {str(e)}")
        _update_task_progress(task_id, 0, "error", f"构建失败: {str(e)}")

def _run_imputation_task(task_id: str, request_data: Dict):
    """执行轨迹填补任务"""
    try:
        _update_task_progress(task_id, 10, "running", "开始创建参数")
        
        # 创建参数
        args = _create_args_namespace_from_request(request_data)
        
        _update_task_progress(task_id, 20, "running", "设置日志")
        setup_logging(args)
        
        _update_task_progress(task_id, 30, "running", "获取训练和测试数据")
        _, (test_df, mark_missing_test) = get_training_test_data(args)
        
        _update_task_progress(task_id, 40, "running", "初始化管理器和SDKG")
        sdkg = SDKG(args)
        ku_manager = KnowledgeUnitManager(args)
        result_manager = ImputationResultsManager(args)
        sdkg.load_SDKG(args.end_point_sdkg)
        ku_manager.load_knowledge_unit_list(args.end_point_sdkg)
        _update_task_progress(task_id, 60, "running", "开始轨迹填补")
        result_manager.load_results_list(args.end_point_sdkg,args)
        if(not result_manager.results_list):
            result_manager = Trajectory_Imputation_Multithreading(
                args=args,
                trajectory_data=(test_df, mark_missing_test),
                context_info_manager=ku_manager,
                SDKG=sdkg,
                result_manager=result_manager
            )
        
        _update_task_progress(task_id, 80, "running", "评估填补结果")
        evaluate_imputed_result(args, result_manager, test_df, mark_missing_test, sdkg)
        
        _update_task_progress(task_id, 100, "done", "轨迹填补完成")
        
        # 保存任务结果
        task = _get_task(task_id)
        if task:
            task["result"] = {
                "status": "success",
                "imputed_trajectories": len(result_manager.results_list) if result_manager.results_list else 0
            }
            _save_task(task_id, task)
            
    except Exception as e:
        logging.error(f"轨迹填补任务失败: {str(e)}")
        _update_task_progress(task_id, 0, "error", f"填补失败: {str(e)}")

# ============ API路由 ============

@router.post("/build", response_model=TaskResponse)
async def start_sdkg_build(request: VISTARequest, background_tasks: BackgroundTasks):
    """启动SD-KG构建任务"""
    task_id = str(uuid.uuid4())
    
    task_data = {
        "task_id": task_id,
        "type": "sdkg_build",
        "status": "pending",
        "progress": 0,
        "request": request.dict(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message": "SD-KG构建任务已创建"
    }
    
    _save_task(task_id, task_data)
    background_tasks.add_task(_run_sdkg_build_task, task_id, request.dict())
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="SD-KG构建任务已启动",
        created_at=task_data["created_at"]
    )

@router.post("/impute", response_model=TaskResponse)
async def start_imputation(request: VISTARequest, background_tasks: BackgroundTasks):
    """启动轨迹填补任务"""
    task_id = str(uuid.uuid4())
    
    task_data = {
        "task_id": task_id,
        "type": "imputation",
        "status": "pending",
        "progress": 0,
        "request": request.dict(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message": "轨迹填补任务已创建"
    }
    
    _save_task(task_id, task_data)
    background_tasks.add_task(_run_imputation_task, task_id, request.dict())
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="轨迹填补任务已启动",
        created_at=task_data["created_at"]
    )

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskStatusResponse(**task)

@router.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    """列出所有任务"""
    tasks = task_storage.list_tasks(status, limit)
    return {"total": len(tasks), "tasks": tasks}

@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task["status"] in ["pending", "running"]:
        task["status"] = "cancelled"
        task["message"] = "任务已取消"
        task["updated_at"] = datetime.now().isoformat()
        _save_task(task_id, task)
    
    return {"message": "任务已标记为取消", "task_id": task_id}