# /mnt/aisdata/Haoyu/CLEAR/clear-backend/app/api/v1/update.py
import os
import sys
import json
import uuid
import logging
import argparse
import pandas as pd
from typing import Dict, Optional, List, Any, Set, Tuple
from datetime import datetime
from pathlib import Path
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path

# 获取当前文件的目录路径
current_dir = Path(__file__).parent
# 获取项目根目录（根据你的文件结构，向上4级到clear-backend）
project_root = current_dir.parent.parent.parent

router = APIRouter(prefix="/update", tags=["update"])
process_length = 4
end_point = 4
seed=42
exp_name = "Default"

# ============ 本地JSON文件存储 ============
class UpdateTaskStorage:
    def __init__(self, storage_dir: str = "./update_task_storage"):
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
task_storage = UpdateTaskStorage(storage_dir="/mnt/aisdata/Haoyu/CLEAR/update_task_storage")
executor = ThreadPoolExecutor(max_workers=4)

# ============ 请求/响应模型 ============
class UpdateRequest(BaseModel):
    dataset: str = "demo-dk"
    sdkg_task_id: Optional[str] = None
    impute_task_id: Optional[str] = None

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

# ============ 第一步：CSV转JSON轨迹数据 ============
def _convert_csv_to_segments(task_id: str, request_data: Dict):
    """将CSV数据转换为前端地图JSON格式"""
    try:
        _update_task_progress(task_id, 5, "running", "开始转换CSV数据")
        
        # 根据数据集选择路径
        dataset = request_data.get("dataset", "demo-dk")
        trajectorylen = request_data.get("trajectoryLen", 200)
        trajectorynum = request_data.get("trajectoryNum", 10000)

        if dataset == "demo-dk":
            exp_name = "Default"
        elif dataset == "demo-us":
            exp_name = "Default_us"
            
        if dataset == "demo-dk":
            csv_path = f"{project_root}/vista/data/ProcessedData/aisdk-2024-03-01@31_filtered10_1000000000_standardized_with_SequenceId_SegementId_PointInfo_{trajectorylen}_{trajectorynum}.csv"
            ku_path = f"{project_root}/vista/results/{exp_name}/KU/knowledge_units_trajectory{trajectorynum}_len{trajectorylen}_seed{seed}_{process_length}.json"
        elif dataset == "demo-us":
            csv_path = f"{project_root}/vista/data/ProcessedData/AIS_2024_04_01@15_filtered360_1000000000_standardized_with_SequenceId_SegementId_PointInfo_{trajectorylen}_{trajectorynum}.csv"
            ku_path = f"{project_root}/vista/results/{exp_name}/KU/knowledge_units_trajectory{trajectorynum}_len{trajectorylen}_seed{seed}_{process_length}.json"
        else:
            raise ValueError(f"未知的数据集: {dataset}")
        
        output_path = f"{project_root}/data/segments.json"
        
        # 读取CSV文件
        _update_task_progress(task_id, 10, "running", "读取CSV文件")
        df = pd.read_csv(csv_path)
        
        # 如果提供了KU文件，基于KU文件内容筛选数据
        if ku_path and os.path.exists(ku_path):
            _update_task_progress(task_id, 15, "running", "读取KU文件并筛选数据")
            with open(ku_path, 'r') as f:
                ku_data = json.load(f)
            
            ku_trajectories = set()
            for ku_item in ku_data:
                if not ku_item or 'v_s' not in ku_item:
                    continue
                v_s = ku_item.get('v_s', {})
                mmsi = v_s.get('MMSI')
                seq = v_s.get('seq')
                if mmsi is not None and seq is not None:
                    try:
                        seq_int = int(seq)
                        ku_trajectories.add((mmsi, seq_int))
                    except ValueError:
                        continue
            
            if ku_trajectories:
                mask = df.apply(lambda row: (row['mmsi'], row['sequence_id']) in ku_trajectories, axis=1)
                df = df[mask]
        
        _update_task_progress(task_id, 20, "running", "处理轨迹分段")
        # 按sequence_id和segment_id分组
        segments_data = []
        grouped = df.groupby(['sequence_id', 'segment_id'])
        
        for (seq_id, seg_id), group in grouped:
            if len(group) < 2:
                continue
            
            group = group.sort_values('timestamp')
            first_row = group.iloc[0]
            mmsi = first_row['mmsi']
            ship_type = first_row.get('ship_type', 'Unknown')
            
            points = []
            for _, row in group.iterrows():
                point = {
                    "timestamp": row['timestamp'].replace(' ', 'T') + 'Z',
                    "lat": float(row['latitude']),
                    "lon": float(row['longitude']),
                    "sog": float(row['sog']) if pd.notna(row['sog']) else None,
                    "cog": float(row['cog']) if pd.notna(row['cog']) else None
                }
                points.append(point)
            
            segment = {
                "id": f"TRJ_{seq_id}_SEG_{seg_id}",
                "trajectory_id": f"TRJ_{seq_id}",
                "vessel_id": str(mmsi),
                "start_time": group.iloc[0]['timestamp'].replace(' ', 'T') + 'Z',
                "end_time": group.iloc[-1]['timestamp'].replace(' ', 'T') + 'Z',
                "short_description": f"{ship_type} vessel {mmsi} trajectory segment",
                "points": points
            }
            segments_data.append(segment)
        
        # 保存JSON文件
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments_data, f, indent=2, ensure_ascii=False)
        
        _update_task_progress(task_id, 30, "running", "CSV转换完成")
        return True, f"转换完成: {len(segments_data)}个分段"
        
    except Exception as e:
        return False, f"CSV转换失败: {str(e)}"

# ============ 第二步：构建子图 ============
def _build_multi_level_graph(center_node_id: str, index_data: Dict, max_level: int = 3) -> Dict[str, Any]:
    """构建多级关系子图"""
    visited_nodes = set([center_node_id])
    visited_links = set()
    nodes = []
    links = []
    
    center_node_info = next((n for n in index_data["nodes"] if n["id"] == center_node_id), None)
    if center_node_info:
        nodes.append({**center_node_info, "level": 0, "isCenter": True})
    
    queue = deque([(center_node_id, 0)])
    while queue:
        current_id, level = queue.popleft()
        if level >= max_level:
            continue
        
        connected_links = [link for link in index_data["links"] 
                          if link["source"] == current_id or link["target"] == current_id]
        
        for link in connected_links:
            link_key = tuple(sorted([link["source"], link["target"]]))
            if link_key in visited_links:
                continue
                
            visited_links.add(link_key)
            links.append({**link, "level": level + 1})
            
            other_node_id = link["target"] if link["source"] == current_id else link["source"]
            if other_node_id not in visited_nodes:
                visited_nodes.add(other_node_id)
                next_level = level + 1
                
                node_info = next((n for n in index_data["nodes"] if n["id"] == other_node_id), None)
                if node_info:
                    nodes.append({**node_info, "level": next_level, "isCenter": False})
                    if next_level < max_level:
                        queue.append((other_node_id, next_level))
    
    return {
        "nodes": nodes,
        "links": links,
        "allNodeIds": list(visited_nodes),
        "centerNodeId": center_node_id,
        "maxLevel": max_level,
        "totalNodes": len(nodes),
        "totalLinks": len(links)
    }

def _generate_subgraphs(task_id: str, request_data: Dict):
    """为所有节点生成子图"""
    try:
        _update_task_progress(task_id, 75, "running", "开始生成子图")
        
        dataset = request_data.get("dataset", "demo-dk")
        
        if dataset == "demo-dk":
            input_file = f"{project_root}/data/sdkg_index.json"
        elif dataset == "demo-us":
            input_file = f"{project_root}/data/sdkg_index_us.json"
        else:
            input_file = f"{project_root}/data/sdkg_index.json"

        output_base_dir = f"{project_root}/data"
        max_level = 1
        
        # 读取索引文件
        if not os.path.exists(input_file):
            return False, f"SDKG索引文件不存在: {input_file}"
        
        with open(input_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # 创建子图目录
        subgraph_dir = os.path.join(output_base_dir, "subgraph")
        os.makedirs(subgraph_dir, exist_ok=True)
        
        # 检查点文件
        checkpoint_file = os.path.join(output_base_dir, "subgraph_checkpoint.json")
        
        # 加载检查点
        processed_nodes = set()
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                processed_nodes = set(checkpoint_data.get("processed_nodes", []))
            except:
                pass
        
        # 获取所有节点
        all_nodes = index_data["nodes"]
        remaining_nodes = [node for node in all_nodes if node["id"] not in processed_nodes]
        
        _update_task_progress(task_id, 80, "running", f"处理{len(remaining_nodes)}个节点")
        
        # 处理节点
        successful_nodes = []
        failed_nodes = []
        total_remaining = len(remaining_nodes)
        
        for i, node in enumerate(remaining_nodes, 1):
            node_id = node["id"]
            
            try:
                subgraph_data = _build_multi_level_graph(node_id, index_data, max_level)
                output_file = os.path.join(subgraph_dir, f"{node_id}.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(subgraph_data, f, ensure_ascii=False, indent=2)
                
                successful_nodes.append(node_id)
            except Exception as e:
                failed_nodes.append((node_id, str(e)))
            
            # 更新进度
            if total_remaining > 0:
                progress = 40 + (i / total_remaining * 20)  # 占20%的进度
                _update_task_progress(task_id, min(60, progress), "running", 
                                     f"生成子图: {i}/{total_remaining}")
        
        # 保存检查点
        all_processed = list(processed_nodes) + successful_nodes
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "processed_nodes": all_processed,
            "failed_nodes": [{"node_id": node_id, "error": error} for node_id, error in failed_nodes],
            "total_processed": len(all_processed) + len(failed_nodes)
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        # 生成子图索引
        _update_task_progress(task_id,85, "running", "生成子图索引")
        subgraph_index_data = {
            "generatedAt": datetime.now().isoformat(),
            "totalNodes": len(all_nodes),
            "subgraphs": []
        }
        
        for node in all_nodes:
            node_id = node["id"]
            subgraph_file = f"{node_id}.json"
            file_path = os.path.join(subgraph_dir, subgraph_file)
            
            if os.path.exists(file_path):
                subgraph_index_data["subgraphs"].append({
                    "nodeId": node_id,
                    "nodeLabel": node.get("label", ""),
                    "nodeType": node.get("type", ""),
                    "filePath": f"subgraph/{subgraph_file}"
                })
        
        index_file = os.path.join(output_base_dir, "subgraphs_index.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(subgraph_index_data, f, ensure_ascii=False, indent=2)
        
        _update_task_progress(task_id, 100, "done", "子图生成完成")
        return True, f"子图生成完成: {len(successful_nodes)}成功, {len(failed_nodes)}失败"
        
    except Exception as e:
        return False, f"子图生成失败: {str(e)}"

# ============ 第三步：转换SDKG为知识图谱 ============
def _extract_main_description(text):
    """从文本中提取括号前的主要内容"""
    if not isinstance(text, str):
        return str(text)
    bracket_pos = text.find('(')
    if bracket_pos != -1:
        return text[:bracket_pos].strip()
    return text.strip()

def _convert_sdkg_to_kg(task_id: str, request_data: Dict):
    """转换SDKG文件为知识图谱"""
    try:
        _update_task_progress(task_id, 35, "running", "开始转换SDKG为知识图谱")
        
        dataset = request_data.get("dataset", "demo-dk")
        trajectorylen = request_data.get("trajectoryLen", 200)
        trajectorynum = request_data.get("trajectoryNum", 10000)
        if dataset == "demo-dk":
            exp_name = "Default"
        elif dataset == "demo-us":
            exp_name = "Default_us"
            
        if dataset == "demo-dk":
            vb_graph_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vb_{process_length}.json"
            vb_node_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vb_node_{process_length}.json"
            vf_graph_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vf_{process_length}.json"
            vf_node_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vf_node_{process_length}.json"
            vs_graph_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vs_{process_length}.json"
            ku_path = f"{project_root}/vista/results/{exp_name}/KU/knowledge_units_trajectory{trajectorynum}_len{trajectorylen}_seed{seed}_{process_length}.json"
            imputation_path = f"{project_root}/vista/results/{exp_name}/ImputationResults/imputation_results_trajectory{trajectorynum}_len{trajectorylen}_seed{seed}_{process_length}_{process_length}.json"
            csv_path = f"{project_root}/vista/data/ProcessedData/aisdk-2024-03-01@31_filtered10_1000000000_standardized_with_SequenceId_SegementId_PointInfo_{trajectorylen}_{trajectorynum}.csv"
        elif dataset == "demo-us":
            vb_graph_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vb_{process_length}.json"
            vb_node_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vb_node_{process_length}.json"
            vf_graph_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vf_{process_length}.json"
            vf_node_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vf_node_{process_length}.json"
            vs_graph_path = f"{project_root}/vista/results/{exp_name}/SDKG/SDK_graph_vs_{process_length}.json"
            ku_path = f"{project_root}/vista/results/{exp_name}/KU/knowledge_units_trajectory{trajectorynum}_len{trajectorylen}_seed{seed}_{process_length}.json"
            imputation_path = f"{project_root}/vista/results/{exp_name}/ImputationResults/imputation_results_trajectory{trajectorynum}_len{trajectorylen}_seed{seed}_{process_length}_{process_length}.json"
            csv_path = f"{project_root}/vista/data/ProcessedData/AIS_2024_04_01@15_filtered360_1000000000_standardized_with_SequenceId_SegementId_PointInfo_{trajectorylen}_{trajectorynum}.csv"
        else:
            raise ValueError(f"未知的数据集: {dataset}")
        
        output_dir = "/mnt/aisdata/Haoyu/CLEAR/clear-backend/data"
        
        # 加载文件
        _update_task_progress(task_id,40, "running", "加载SDKG文件")
        print(f"Loading VB graph from: {vb_graph_path}")
        with open(vb_graph_path, 'r') as f:
            vb_graph = json.load(f)["SDK_graph_vb"]
        
        with open(vb_node_path, 'r') as f:
            vb_nodes = json.load(f)["SDK_graph_vb_node"]
        
        with open(vf_graph_path, 'r') as f:
            vf_graph = json.load(f)["SDK_graph_vf"]
        
        with open(vf_node_path, 'r') as f:
            vf_nodes = json.load(f)["SDK_graph_vf_node"]
        
        with open(vs_graph_path, 'r') as f:
            vs_graph = json.load(f)["SDK_graph_vs"]
        
        print(f"Loading KU file from: {ku_path}")
        with open(ku_path, 'r') as f:
            ku_data = json.load(f)
        
        print(f"Loading imputation results from: {imputation_path}")
        with open(imputation_path, 'r') as f:
            imputation_data = json.load(f)
        
        # 创建imputation数据映射
        _update_task_progress(task_id, 42, "running", "创建数据映射")
        imputation_data_map = {}
        for imputation_item in imputation_data:
            if not imputation_item:
                continue
            sequence_id = imputation_item.get('sequence_id')
            segment_id = imputation_item.get('segment_id')
            mmsi = imputation_item.get('mmsi')
            if sequence_id is not None and segment_id is not None and mmsi is not None:
                key = (mmsi, sequence_id, segment_id)
                imputation_data_map[key] = imputation_item
        
        print(f"Found {len(imputation_data_map)} imputation records")
        
        # 从KU文件中提取轨迹和段信息
        print("Extracting trajectory and segment information from KU file...")
        ku_trajectory_segments = set()
        ku_mmsi_set = set()
        ku_trajectories = set()
        ku_data_map = {}
        
        for ku_item in ku_data:
            if not ku_item or 'v_s' not in ku_item:
                continue
            v_s = ku_item.get('v_s', {})
            mmsi = v_s.get('MMSI')
            seq = v_s.get('seq')
            block = v_s.get('block')
            
            if mmsi is not None and seq is not None and block is not None:
                try:
                    seq_int = int(seq)
                    block_int = int(block)
                    ku_trajectory_segments.add((mmsi, seq_int, block_int))
                    ku_trajectories.add((mmsi, seq_int))
                    ku_mmsi_set.add(mmsi)
                    key = (mmsi, seq_int, block_int)
                    ku_data_map[key] = ku_item
                except ValueError:
                    continue
        
        print(f"Found {len(ku_trajectory_segments)} unique (MMSI, sequence_id, segment_id) combinations in KU file")
        
        # 读取CSV文件
        _update_task_progress(task_id,45, "running", "读取CSV数据")
        print(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # 根据KU文件中的信息筛选CSV数据
        filtered_dfs = []
        for mmsi, seq_id in ku_trajectories:
            mask = (df['mmsi'] == mmsi) & (df['sequence_id'] == seq_id)
            matching_rows = df[mask]
            if not matching_rows.empty:
                filtered_dfs.append(matching_rows)
        
        if filtered_dfs:
            df = pd.concat(filtered_dfs, ignore_index=True)
            print(f"Filtered CSV data: {len(df)} rows, {df['sequence_id'].nunique()} trajectories, {df['segment_id'].nunique()} segments")
        else:
            raise ValueError("No matching data found in CSV for the KU file entries")
        
        # 创建输出目录
        output_path = Path(output_dir)
        nodes_dir = output_path / "nodes"
        nodes_dir.mkdir(parents=True, exist_ok=True)
        
        # 开始构建知识图谱
        _update_task_progress(task_id, 47, "running", "构建知识图谱节点")
        print("Building knowledge graph...")
        
        # Store all nodes and relationships
        all_nodes = {}
        all_links = []
        
        # Create mappings for trajectory and segment IDs to nodes
        traj_to_node = {}
        seg_to_node = {}
        
        # 创建 Behavior 模式到节点ID的映射
        behavior_pattern_map = {}
        
        # 1. Create Behavior nodes (vb)
        _update_task_progress(task_id, 48, "running", "创建Behavior节点")
        for vb_id, vb_info in vb_nodes.items():
            node_id = f"B_{vb_id}"
            
            pattern_key = (
                _extract_main_description(vb_info.get('speed_profile', '')),
                _extract_main_description(vb_info.get('course_change', '')),
                _extract_main_description(vb_info.get('heading_fluctuation', '')),
                _extract_main_description(vb_info.get('intent', '')),
                _extract_main_description(vb_info.get('duration', ''))
            )
            
            behavior_pattern_map[pattern_key] = node_id
            
            all_nodes[node_id] = {
                "id": node_id,
                "type": "behavior",
                "label": f"Behavior {vb_id[-8:]}",
                "summary": f"Vessel behavior pattern: {vb_info.get('intent', 'Unknown intent')}",
                "description": [
                    f"Speed profile: {vb_info.get('speed_profile', 'Unknown')}",
                    f"Course change: {vb_info.get('course_change', 'Unknown')}",
                    f"Heading fluctuation: {vb_info.get('heading_fluctuation', 'Unknown')}",
                    f"Behavior intent: {vb_info.get('intent', 'Unknown')}",
                    f"Duration: {vb_info.get('duration', 'Unknown')}"
                ],
                "metadata": {
                    "original_id": vb_id,
                    "duration": vb_info.get('duration'),
                    "support": len(vb_graph.get(vb_id, {})) if vb_id in vb_graph else 0,
                    "pattern_key": pattern_key
                },
                "related": []
            }
        
        # 2. Create Function nodes (vf)
        _update_task_progress(task_id, 49, "running", "创建Function节点")
        function_code_map = {}
        for vf_id, vf_info in vf_nodes.items():
            node_id = f"F_{vf_id}"
            code = vf_info.get('code', '')
            
            if code:
                function_code_map[code] = node_id
            
            all_nodes[node_id] = {
                "id": node_id,
                "type": "function",
                "label": f"Function {vf_id[-8:]}",
                "summary": vf_info.get('description', '')[:100] + "...",
                "description": [
                    f"Function description: {vf_info.get('description', 'No description')}",
                    f"Code implementation: {code}"
                ],
                "metadata": {
                    "original_id": vf_id,
                    "code": code
                },
                "related": []
            }
        
        # 3. Create Attribute nodes (vs)
        _update_task_progress(task_id, 50, "running", "创建Attribute节点")
        attribute_count = 0
        attribute_mapping = {}
        
        for category, attributes in vs_graph.items():
            for attr_name, connected_vbs in attributes.items():
                attribute_count += 1
                node_id = f"A_{attribute_count:03d}"
                attribute_key = f"vs_{category}_{attr_name}"
                attribute_mapping[attribute_key] = node_id
                
                all_nodes[node_id] = {
                    "id": node_id,
                    "type": "attribute",
                    "label": f"{category}: {attr_name}",
                    "summary": f"{category} attribute: {attr_name}",
                    "description": [f"This attribute is associated with {len(connected_vbs)} behavior patterns"],
                    "metadata": {
                        "category": category,
                        "attribute_name": attr_name,
                        "support": len(connected_vbs)
                    },
                    "related": []
                }
        
        # 4. Create Trajectory and Segment nodes
        _update_task_progress(task_id, 51, "running", "创建Trajectory和Segment节点")
        traj_groups = df.groupby('sequence_id')
        print(f"Processing {len(traj_groups)} trajectory groups...")
        
        for seq_id, traj_group in traj_groups:
            traj_node_id = f"T_{seq_id}"
            mmsi = traj_group['mmsi'].iloc[0] if 'mmsi' in traj_group.columns else 'Unknown'
            
            all_nodes[traj_node_id] = {
                "id": traj_node_id,
                "type": "trajectory",
                "label": f"Trajectory {mmsi}",
                "summary": f"Complete trajectory of vessel {mmsi}",
                "description": [
                    f"MMSI: {mmsi}",
                    f"Contains {traj_group['segment_id'].nunique()} segments",
                    f"Total data points: {len(traj_group)}"
                ],
                "metadata": {
                    "mmsi": str(mmsi),
                    "num_segments": traj_group['segment_id'].nunique(),
                    "num_points": len(traj_group)
                },
                "related": []
            }
            traj_to_node[str(seq_id)] = traj_node_id
            
            # Create segment nodes
            seg_groups = traj_group.groupby('segment_id')
            for seg_id, seg_group in seg_groups:
                seg_node_id = f"TRJ_{seq_id}_SEG_{seg_id}"
                ship_type = seg_group['ship_type'].iloc[0] if 'ship_type' in seg_group.columns else 'Unknown'
                
                # 获取当前segment的KU数据
                current_ku = ku_data_map.get((mmsi, seq_id, seg_id), {})
                v_s = current_ku.get('v_s', {})
                v_b = current_ku.get('v_b', {})
                
                # 构建Static Attributes
                static_attributes = []
                for key, value in v_s.items():
                    if key not in ['MMSI', 'seq', 'block'] and value:
                        friendly_key = key.replace('_', ' ').title()
                        static_attributes.append(f"{friendly_key}: {value}")
                
                # 构建Context
                context = {}
                
                # Current Behavior
                current_behavior = {}
                if v_b:
                    for key, value in v_b.items():
                        if key != 'llm_output' and value:
                            current_behavior[key] = value
                context['current_behavior'] = current_behavior
                
                # Previous Behavior
                prev_seg_id = seg_id - 1
                prev_ku = ku_data_map.get((mmsi, seq_id, prev_seg_id), {})
                prev_v_b = prev_ku.get('v_b', {})
                previous_behavior = {}
                if prev_v_b:
                    for key, value in prev_v_b.items():
                        if key != 'llm_output' and value:
                            previous_behavior[key] = value
                context['previous_behavior'] = previous_behavior
                
                # Next Behavior
                next_seg_id = seg_id + 1
                next_ku = ku_data_map.get((mmsi, seq_id, next_seg_id), {})
                next_v_b = next_ku.get('v_b', {})
                next_behavior = {}
                if next_v_b:
                    for key, value in next_v_b.items():
                        if key != 'llm_output' and value:
                            next_behavior[key] = value
                context['next_behavior'] = next_behavior
                
                # 获取imputation数据
                imputation_item = imputation_data_map.get((mmsi, seq_id, seg_id), {})
                
                # 构建behavior_estimator
                behavior_estimator = {}
                if imputation_item.get('behavior_estimator'):
                    behavior_estimator_data = imputation_item['behavior_estimator']
                    behavior_estimator = {
                        "graph_support": behavior_estimator_data.get('graph_support', ''),
                        "contextual_justification": behavior_estimator_data.get('contextual_justification', '')
                    }
                
                # 构建method_selector
                method_selector = {}
                if imputation_item.get('method_selector'):
                    method_selector_data = imputation_item['method_selector']
                    method_selector = {
                        "statistical_support": method_selector_data.get('statistical_support', '')
                    }
                
                # 构建explanation_composer
                explanation_composer = {}
                if imputation_item.get('explanation_composer'):
                    explanation_composer_data = imputation_item['explanation_composer']
                    explanation_composer = {
                        "regulatory_rule_cue": explanation_composer_data.get('regulatory_rule_cue', ''),
                        "operational_protocol_rationale": explanation_composer_data.get('operational_protocol_rationale', '')
                    }
                
                all_nodes[seg_node_id] = {
                    "id": seg_node_id,
                    "type": "segment",
                    "label": f"Segment TRJ_{seq_id}_SEG_{seg_id}",
                    "summary": f"Segment {seg_id} of trajectory {seq_id}",
                    "description": [
                        f"MMSI: {mmsi}",
                        f"Ship Type: {ship_type}",
                        f"Number of data points: {len(seg_group)}",
                        f"Start time: {seg_group['timestamp'].iloc[0]}",
                        f"End time: {seg_group['timestamp'].iloc[-1]}"
                    ],
                    "metadata": {
                        "trajectory_id": str(seq_id),
                        "vessel_id": str(mmsi),
                        "vessel_type": str(ship_type),
                        "num_points": len(seg_group),
                        "start_time": seg_group['timestamp'].iloc[0],
                        "end_time": seg_group['timestamp'].iloc[-1]
                    },
                    "static_attributes": static_attributes,
                    "context": context,
                    "behavior_estimator": behavior_estimator,
                    "method_selector": method_selector,
                    "explanation_composer": explanation_composer,
                    "related": []
                }
                seg_to_node[f"{seq_id}_{seg_id}"] = seg_node_id
                
                # Add segment to trajectory relationship
                all_links.append({
                    "source": seg_node_id,
                    "target": traj_node_id,
                    "relation": "part_of"
                })
        
        # 5. Build relationships from KU data
        _update_task_progress(task_id, 53, "running", "建立节点关系")
        segments_with_behavior = set()
        segments_with_attribute = set()
        segments_with_function = set()
        
        for ku_item in ku_data:
            if not ku_item or 'v_s' not in ku_item:
                continue
            
            v_s = ku_item.get('v_s', {})
            v_b = ku_item.get('v_b', {})
            v_f = ku_item.get('v_f', {})
            
            seq = v_s.get('seq')
            block = v_s.get('block')
            
            if seq is not None and block is not None:
                seg_key = f"{seq}_{block}"
                seg_node_id = seg_to_node.get(seg_key)
                
                if seg_node_id:
                    # 建立 Segment 与 Behavior 的直接链接
                    if v_b:
                        seg_pattern_key = (
                            _extract_main_description(v_b.get('speed_profile', '')),
                            _extract_main_description(v_b.get('course_change', '')),
                            _extract_main_description(v_b.get('heading_fluctuation', '')),
                            _extract_main_description(v_b.get('intent', '')),
                            _extract_main_description(v_b.get('duration', ''))
                        )
                        
                        matching_behavior_id = behavior_pattern_map.get(seg_pattern_key)
                        if matching_behavior_id:
                            all_links.append({
                                "source": seg_node_id,
                                "target": matching_behavior_id,
                                "relation": "exhibits_behavior"
                            })
                            segments_with_behavior.add(seg_key)
                    
                    # Establish segment to attribute relationships
                    for attr_key, attr_value in v_s.items():
                        if attr_key not in ['seq', 'block', 'MMSI']:
                            vs_key = f"vs_{attr_key}_{attr_value}"
                            attr_node_id = attribute_mapping.get(vs_key)
                            
                            if attr_node_id:
                                all_links.append({
                                    "source": seg_node_id,
                                    "target": attr_node_id,
                                    "relation": "has_attribute"
                                })
                                segments_with_attribute.add(seg_key)
                    
                    # 建立 Segment 与 Function 的链接
                    if v_f and 'spatial_function' in v_f:
                        spatial_function_code = v_f.get('spatial_function', '')
                        if spatial_function_code:
                            matching_function_id = function_code_map.get(spatial_function_code)
                            if matching_function_id:
                                all_links.append({
                                    "source": seg_node_id,
                                    "target": matching_function_id,
                                    "relation": "uses_function"
                                })
                                segments_with_function.add(seg_key)
        
        # 6. Build vb - vf relationships
        for vf_id, connected_vbs in vf_graph.items():
            vf_node_id = f"F_{vf_id}"
            for vb_id, weight in connected_vbs.items():
                if weight > 0:
                    vb_node_id = f"B_{vb_id}"
                    if vb_node_id in all_nodes and vf_node_id in all_nodes:
                        all_links.append({
                            "source": vf_node_id,
                            "target": vb_node_id,
                            "relation": "implements"
                        })
        
        # 7. Build vb - vs relationships
        for vb_id, connected_attrs in vb_graph.items():
            vb_node_id = f"B_{vb_id}"
            for attr_key, weight in connected_attrs.items():
                if weight > 0:
                    attr_node_id = attribute_mapping.get(attr_key)
                    if attr_node_id and vb_node_id in all_nodes:
                        all_links.append({
                            "source": vb_node_id,
                            "target": attr_node_id,
                            "relation": "has_attribute"
                        })
        
        # 8. Save node files
        _update_task_progress(task_id, 55, "running", "保存节点文件")
        print("Saving node files...")
        for node_id, node_info in all_nodes.items():
            node_file = nodes_dir / f"{node_id}.json"
            with open(node_file, 'w', encoding='utf-8') as f:
                json.dump(node_info, f, indent=2, ensure_ascii=False)
        
        # 9. Create index file
        _update_task_progress(task_id, 57, "running", "创建索引文件")
        print("Creating index file...")
        index_data = {
            "nodes": [
                {
                    "id": node_info["id"],
                    "type": node_info["type"],
                    "label": node_info["label"]
                }
                for node_info in all_nodes.values()
            ],
            "links": all_links
        }
        
        index_file = output_path / "sdkg_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        # 10. Output statistics
        node_types = defaultdict(int)
        for node in all_nodes.values():
            node_types[node['type']] += 1
        
        link_relations = defaultdict(int)
        for link in all_links:
            link_relations[link['relation']] += 1
        
        print(f"\nConversion completed!")
        print(f"Node type statistics:")
        for node_type, count in node_types.items():
            print(f"  {node_type}: {count}")
        print(f"Relationship statistics:")
        for relation, count in link_relations.items():
            print(f"  {relation}: {count}")
        print(f"Total relationships: {len(all_links)}")
        print(f"Index file: {index_file}")
        
        _update_task_progress(task_id, 75, "running", "知识图谱转换完成")
        return True, f"SDKG转换完成: {len(all_nodes)}节点, {len(all_links)}关系"
        
    except Exception as e:
        import traceback
        print(f"Error in SDKG conversion: {str(e)}")
        traceback.print_exc()
        return False, f"SDKG转换失败: {str(e)}"

# ============ 主任务执行函数 ============
def _run_update_task(task_id: str, request_data: Dict):
    """执行更新任务（三合一流水线）"""
    try:
        _update_task_progress(task_id, 0, "running", "开始更新CLEAR内容")
        
        # 步骤1: CSV转JSON
        success1, message1 = _convert_csv_to_segments(task_id, request_data)
        if not success1:
            _update_task_progress(task_id, 0, "error", message1)
            return
        
        # 步骤3: SDKG转知识图谱（先执行这个！）
        success3, message3 = _convert_sdkg_to_kg(task_id, request_data)
        if not success3:
            _update_task_progress(task_id, 0, "error", message3)
            return
        
        # 步骤2: 生成子图（需要sdkg_index.json，所以放最后）
        success2, message2 = _generate_subgraphs(task_id, request_data)
        if not success2:
            _update_task_progress(task_id, 0, "error", message2)
            return
        
        # 保存任务结果
        task = _get_task(task_id)
        if task:
            task["result"] = {
                "status": "success",
                "message": "CLEAR内容更新完成",
                "output_files": [
                    f"{project_root}/data/segments.json",
                    f"{project_root}/data/subgraph/",
                    f"{project_root}/data/sdkg_index.json",
                    f"{project_root}/data/nodes/"
                ]
            }
            _save_task(task_id, task)
            
    except Exception as e:
        logging.error(f"CLEAR内容更新失败: {str(e)}")
        _update_task_progress(task_id, 0, "error", f"更新失败: {str(e)}")

# ============ API路由 ============
@router.post("", response_model=TaskResponse)
async def start_update_task(request: UpdateRequest, background_tasks: BackgroundTasks):
    """启动CLEAR内容更新任务"""
    task_id = str(uuid.uuid4())
    
    task_data = {
        "task_id": task_id,
        "type": "update_content",
        "status": "pending",
        "progress": 0,
        "request": request.dict(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message": "CLEAR内容更新任务已创建"
    }
    
    _save_task(task_id, task_data)
    background_tasks.add_task(_run_update_task, task_id, request.dict())
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="CLEAR内容更新任务已启动",
        created_at=task_data["created_at"]
    )

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_update_task_status(task_id: str):
    """获取更新任务状态"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskStatusResponse(**task)

@router.get("/tasks")
async def list_update_tasks(status: Optional[str] = None, limit: int = 50):
    """列出所有更新任务"""
    tasks = task_storage.list_tasks(status, limit)
    return {"total": len(tasks), "tasks": tasks}

@router.delete("/task/{task_id}")
async def cancel_update_task(task_id: str):
    """取消更新任务"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task["status"] in ["pending", "running"]:
        task["status"] = "cancelled"
        task["message"] = "任务已取消"
        task["updated_at"] = datetime.now().isoformat()
        _save_task(task_id, task)
    
    return {"message": "任务已标记为取消", "task_id": task_id}

@router.get("/health")
async def update_health_check():
    """健康检查"""
    return {"status": "healthy", "service": "update", "timestamp": datetime.now().isoformat()}