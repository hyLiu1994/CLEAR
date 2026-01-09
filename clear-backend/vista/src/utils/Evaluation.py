import numpy as np
import pandas as pd
import logging
import json
import os
import time  
import matplotlib.pyplot as plt  
import seaborn as sns  
from datetime import datetime  
from src.utils.utils import get_root_path

def get_vf_function(sdkg, function_id):
    """Get and compile function from SDKG by function ID"""
    vf_node = sdkg.SDK_graph_vf_node.get(function_id)
    if not vf_node or not vf_node.get('code'):
        logging.warning(f"Function {function_id} not found or has no code")
        return None
    
    try:
        local_ns = {}
        exec(vf_node['code'], {'np': np}, local_ns)
        return local_ns.get("spatial_function")
    except Exception as e:
        logging.warning(f"Failed to compile function {function_id}: {e}")
        return None

def execute_imputation(function, segment_data, prev_segment_data=None, next_segment_data=None):
    try:
        if prev_segment_data is not None and not prev_segment_data.empty:
            start = (float(prev_segment_data.iloc[-1]['latitude']), 
                    float(prev_segment_data.iloc[-1]['longitude']))
            base_time = pd.to_datetime(prev_segment_data.iloc[-1]['timestamp'])
        else:
            start = (float(segment_data.iloc[0]['latitude']), 
                    float(segment_data.iloc[0]['longitude']))
            base_time = pd.to_datetime(segment_data.iloc[0]['timestamp'])
            
        if next_segment_data is not None and not next_segment_data.empty:
            end = (float(next_segment_data.iloc[0]['latitude']), 
                  float(next_segment_data.iloc[0]['longitude']))
        else:
            end = (float(segment_data.iloc[-1]['latitude']), 
                  float(segment_data.iloc[-1]['longitude']))
        
        timestamps = segment_data['timestamp'].values
        T = np.array([(pd.to_datetime(ts) - base_time).total_seconds() for ts in timestamps])
        logging.info(f"T:{T}")
        trajectory = function(start, end, T)
        return np.array(trajectory, dtype=float)
    except Exception as e:
        logging.warning(f"Imputation execution failed: {e}")
        return None

def save_evaluation_results(args, metrics):
    """Save evaluation results to file"""
    root_path = get_root_path()
    eval_dir = os.path.join(root_path, 'results', args.exp_name, 'EVA')
    os.makedirs(eval_dir, exist_ok=True)
    
    filename = f"evaluations{args.trajectory_num}_len{args.trajectory_len}_seed{args.seed}_{args.end_point_sdkg}_{args.end_point}.json"
    file_path = os.path.join(eval_dir, filename)
    
    # Add metadata to metrics
    metrics_with_meta = {
        'evaluation_metadata': {
            'exp_name': args.exp_name,
            'trajectory_num': args.trajectory_num,
            'trajectory_len': args.trajectory_len,
            'seed': args.seed,
            'end_point_sdkg': args.end_point_sdkg,
            'end_point': args.end_point,
            'timestamp': pd.Timestamp.now().isoformat()
        },
        'metrics': metrics
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_with_meta, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Evaluation results saved to: {file_path}")
    return file_path

def save_comparison_csv(args, comparison_data):
    """Save detailed comparison between original and imputed results to CSV"""
    root_path = get_root_path()
    comp_dir = os.path.join(root_path, 'results', args.exp_name, 'COMPARISON')
    os.makedirs(comp_dir, exist_ok=True)
    
    filename = f"comparison{args.trajectory_num}_len{args.trajectory_len}_seed{args.seed}_{args.end_point_sdkg}_{args.end_point}.csv"
    file_path = os.path.join(comp_dir, filename)
    
    # Create DataFrame from comparison data
    df = pd.DataFrame(comparison_data)
    
    # Save to CSV
    df.to_csv(file_path, index=False, encoding='utf-8')
    
    logging.info(f"Comparison results saved to: {file_path}")
    return file_path

def evaluate_imputed_result(args, result_manager, test_df, mark_missing_test, sdkg):
    lat_errors, lon_errors, spherical_dists = [], [], []
    processed_segments = 0
    comparison_data = []
    
    grouped_results = {}
    for result in result_manager.results_list:
        if not result or 'method_selector' not in result:
            continue
        key = (result['sequence_id'], result['mmsi'])
        if key not in grouped_results:
            grouped_results[key] = []
        grouped_results[key].append(result)
    
    for (seq_id, mmsi), results in grouped_results.items():
        seq_data = test_df[
            (test_df['sequence_id'] == seq_id) & 
            (test_df['mmsi'] == mmsi)
        ].sort_values('timestamp')
        
        results.sort(key=lambda x: x['segment_id'])
        
        missing_segments = [r['segment_id'] for r in results]
        all_segments = seq_data['segment_id'].unique()
        
        missing_groups = []
        current_group = []
        
        for seg_id in all_segments:
            if seg_id in missing_segments:
                current_group.append(seg_id)
            else:
                if current_group:
                    missing_groups.append(current_group)
                    current_group = []
        if current_group:
            missing_groups.append(current_group)
        
        for missing_group in missing_groups:
            if not missing_group:
                continue
                
            first_missing = missing_group[0]
            last_missing = missing_group[-1]
            
            all_segments_list = list(all_segments)
            first_idx = list(all_segments_list).index(first_missing)
            last_idx = list(all_segments_list).index(last_missing)
            
            prev_segment_data = None
            if first_idx > 0:
                prev_segment_id = all_segments_list[first_idx - 1]
                prev_segment_data = seq_data[seq_data['segment_id'] == prev_segment_id]
            
            next_segment_data = None
            if last_idx < len(all_segments_list) - 1:
                next_segment_id = all_segments_list[last_idx + 1]
                next_segment_data = seq_data[seq_data['segment_id'] == next_segment_id]
            
            for segment_id in missing_group:
                result = next(r for r in results if r['segment_id'] == segment_id)
                
                try:
                    function_id = result['method_selector']['selected_function_id']
                    function = get_vf_function(sdkg, function_id)
                    if not function:
                        continue
                    
                    seg_data = seq_data[seq_data['segment_id'] == segment_id]
                    if seg_data.empty:
                        continue
                    
                    imputed_traj = execute_imputation(function, seg_data, prev_segment_data, next_segment_data)
                    if imputed_traj is None:
                        continue
                    
                    true_points = seg_data[['latitude', 'longitude']].values.astype(float)

                    for j, (true_point, imputed_point) in enumerate(zip(true_points, imputed_traj)):
                        R = 6371
                        lat1, lon1 = np.radians(true_point[0]), np.radians(true_point[1])
                        lat2, lon2 = np.radians(imputed_point[0]), np.radians(imputed_point[1])
                        dlat, dlon = lat2 - lat1, lon2 - lon1
                        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                        spherical_dist = R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                        
                        comparison_data.append({
                            'sequence_id': seq_id,
                            'mmsi': mmsi,
                            'segment_id': segment_id,
                            'point_index': j,
                            'timestamp': seg_data.iloc[j]['timestamp'],
                            'original_latitude': true_point[0],
                            'original_longitude': true_point[1],
                            'imputed_latitude': imputed_point[0],
                            'imputed_longitude': imputed_point[1],
                            'latitude_error': abs(true_point[0] - imputed_point[0]),
                            'longitude_error': abs(true_point[1] - imputed_point[1]),
                            'spherical_distance_km': spherical_dist,
                            'selected_function_id': function_id
                        })

                    lat_errors.extend(np.abs(true_points[:, 0] - imputed_traj[:, 0]))
                    lon_errors.extend(np.abs(true_points[:, 1] - imputed_traj[:, 1]))
                    
                    R = 6371
                    lat1, lon1 = np.radians(true_points[:, 0]), np.radians(true_points[:, 1])
                    lat2, lon2 = np.radians(imputed_traj[:, 0]), np.radians(imputed_traj[:, 1])
                    dlat, dlon = lat2 - lat1, lon2 - lon1
                    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                    spherical_dists.extend(R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))
                    
                    processed_segments += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to evaluate segment {segment_id}: {e}")
                    continue
    
    if not lat_errors:
        logging.error("No valid results to evaluate")
        metrics = {"error": "No valid results"}
        comparison_file = None
    else:
        lat_errors, lon_errors, spherical_dists = map(np.array, [lat_errors, lon_errors, spherical_dists])
        
        metrics = {
            'processed_segments': processed_segments,
            'processed_points': len(lat_errors),
            'latitude_mae': float(np.mean(lat_errors)),
            'longitude_mae': float(np.mean(lon_errors)),
            'latitude_rmse': float(np.sqrt(np.mean(lat_errors**2))),
            'longitude_rmse': float(np.sqrt(np.mean(lon_errors**2))),
            'mean_spherical_distance_km': float(np.mean(spherical_dists)),
            'max_spherical_distance_km': float(np.max(spherical_dists)),
            'min_spherical_distance_km': float(np.min(spherical_dists))
        }

        comparison_file = save_comparison_csv(args, comparison_data)
        metrics['comparison_file'] = comparison_file
    
    logging.info("\n" + "="*50)
    logging.info("IMPUTATION EVALUATION RESULTS")
    logging.info("="*50)
    logging.info(f"Processed segments: {metrics['processed_segments']}")
    logging.info(f"Total points evaluated: {metrics['processed_points']}")
    logging.info(f"Latitude MAE: {metrics['latitude_mae']:.6f}")
    logging.info(f"Longitude MAE: {metrics['longitude_mae']:.6f}")
    logging.info(f"Latitude RMSE: {metrics['latitude_rmse']:.6f}")
    logging.info(f"Longitude RMSE: {metrics['longitude_rmse']:.6f}")
    logging.info(f"Mean spherical distance: {metrics['mean_spherical_distance_km']:.4f} km")
    logging.info(f"Max spherical distance: {metrics['max_spherical_distance_km']:.4f} km")
    logging.info(f"Min spherical distance: {metrics['min_spherical_distance_km']:.4f} km")
    
    if comparison_file:
        logging.info(f"Detailed comparison saved to: {comparison_file}")
    
    logging.info("="*50)
    
    saved_file = save_evaluation_results(args, metrics)
    logging.info(f"Results saved to: {saved_file}")
    
    return metrics


def evaluate_imputed_result_per_segment(args, result_manager, test_df, mark_missing_test, sdkg):
    lat_errors, lon_errors, spherical_dists = [], [], []
    processed_segments = 0
    comparison_data = []
    
    # Record detailed information for each imputation
    imputation_records = []
    
    grouped_results = {}
    for result in result_manager.results_list:
        if not result or 'method_selector' not in result:
            continue
        key = (result['sequence_id'], result['mmsi'])
        if key not in grouped_results:
            grouped_results[key] = []
        grouped_results[key].append(result)
    
    for (seq_id, mmsi), results in grouped_results.items():
        seq_data = test_df[
            (test_df['sequence_id'] == seq_id) & 
            (test_df['mmsi'] == mmsi)
        ].sort_values('timestamp')
        
        results.sort(key=lambda x: x['segment_id'])
        
        missing_segments = [r['segment_id'] for r in results]
        all_segments = seq_data['segment_id'].unique()
        
        missing_groups = []
        current_group = []
        
        for seg_id in all_segments:
            if seg_id in missing_segments:
                current_group.append(seg_id)
            else:
                if current_group:
                    missing_groups.append(current_group)
                    current_group = []
        if current_group:
            missing_groups.append(current_group)
        
        for missing_group in missing_groups:
            if not missing_group:
                continue
                
            first_missing = missing_group[0]
            last_missing = missing_group[-1]
            
            all_segments_list = list(all_segments)
            first_idx = list(all_segments_list).index(first_missing)
            last_idx = list(all_segments_list).index(last_missing)
            
            prev_segment_data = None
            if first_idx > 0:
                prev_segment_id = all_segments_list[first_idx - 1]
                prev_segment_data = seq_data[seq_data['segment_id'] == prev_segment_id]
            
            next_segment_data = None
            if last_idx < len(all_segments_list) - 1:
                next_segment_id = all_segments_list[last_idx + 1]
                next_segment_data = seq_data[seq_data['segment_id'] == next_segment_id]
            
            for segment_id in missing_group:
                result = next(r for r in results if r['segment_id'] == segment_id)
                
                try:
                    function_id = result['method_selector']['selected_function_id']
                    function = get_vf_function(sdkg, function_id)
                    if not function:
                        continue
                    
                    seg_data = seq_data[seq_data['segment_id'] == segment_id]
                    if seg_data.empty:
                        continue
                    
                    imputed_traj = execute_imputation(function, seg_data, prev_segment_data, next_segment_data)
                    if imputed_traj is None:
                        continue
                    
                    true_points = seg_data[['latitude', 'longitude']].values.astype(float)

                    # Calculate errors for current segment
                    lat_errors_segment = np.abs(true_points[:, 0] - imputed_traj[:, 0])
                    lon_errors_segment = np.abs(true_points[:, 1] - imputed_traj[:, 1])
                    
                    # Calculate spherical distances
                    R = 6371
                    lat1, lon1 = np.radians(true_points[:, 0]), np.radians(true_points[:, 1])
                    lat2, lon2 = np.radians(imputed_traj[:, 0]), np.radians(imputed_traj[:, 1])
                    dlat, dlon = lat2 - lat1, lon2 - lon1
                    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                    spherical_dists_segment = R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                    
                    # Calculate actual time intervals (time gaps between points in the segment)
                    timestamps = pd.to_datetime(seg_data['timestamp']).sort_values()
                    if len(timestamps) > 1:
                        time_diffs = [(timestamps.iloc[i] - timestamps.iloc[i-1]).total_seconds() 
                                    for i in range(1, len(timestamps))]
                        mean_time_interval = np.mean(time_diffs) if time_diffs else 0
                        max_time_interval = np.max(time_diffs) if time_diffs else 0
                        min_time_interval = np.min(time_diffs) if time_diffs else 0
                    else:
                        mean_time_interval = max_time_interval = min_time_interval = 0
                    
                    # Calculate segment duration
                    segment_duration = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds() if len(timestamps) > 1 else 0
                    
                    # Record detailed information for current segment
                    segment_record = {
                        'sequence_id': seq_id,
                        'mmsi': mmsi,
                        'segment_id': segment_id,
                        'function_id': function_id,
                        'num_points': len(seg_data),
                        'segment_duration_seconds': segment_duration,
                        'mean_time_interval_seconds': mean_time_interval,
                        'max_time_interval_seconds': max_time_interval,
                        'min_time_interval_seconds': min_time_interval,
                        'latitude_mae': float(np.mean(lat_errors_segment)),
                        'longitude_mae': float(np.mean(lon_errors_segment)),
                        'latitude_rmse': float(np.sqrt(np.mean(lat_errors_segment**2))),
                        'longitude_rmse': float(np.sqrt(np.mean(lon_errors_segment**2))),
                        'mean_spherical_distance_km': float(np.mean(spherical_dists_segment)),
                        'max_spherical_distance_km': float(np.max(spherical_dists_segment)),
                        'min_spherical_distance_km': float(np.min(spherical_dists_segment)),
                        'timestamp': datetime.now().isoformat()
                    }
                    imputation_records.append(segment_record)
                    
                    for j, (true_point, imputed_point) in enumerate(zip(true_points, imputed_traj)):
                        spherical_dist = spherical_dists_segment[j]
                        point_time_interval = 0
                        if j > 0:
                            current_time = pd.to_datetime(seg_data.iloc[j]['timestamp'])
                            prev_time = pd.to_datetime(seg_data.iloc[j-1]['timestamp'])
                            point_time_interval = (current_time - prev_time).total_seconds()
                        
                        comparison_data.append({
                            'sequence_id': seq_id,
                            'mmsi': mmsi,
                            'segment_id': segment_id,
                            'point_index': j,
                            'timestamp': seg_data.iloc[j]['timestamp'],
                            'original_latitude': true_point[0],
                            'original_longitude': true_point[1],
                            'imputed_latitude': imputed_point[0],
                            'imputed_longitude': imputed_point[1],
                            'latitude_error': abs(true_point[0] - imputed_point[0]),
                            'longitude_error': abs(true_point[1] - imputed_point[1]),
                            'spherical_distance_km': spherical_dist,
                            'selected_function_id': function_id,
                            'time_interval_seconds': point_time_interval
                        })

                    lat_errors.extend(lat_errors_segment)
                    lon_errors.extend(lon_errors_segment)
                    spherical_dists.extend(spherical_dists_segment)
                    
                    processed_segments += 1
                    
                except Exception as e:
                    logging.warning(f"Failed to evaluate segment {segment_id}: {e}")
                    continue
    
    if not lat_errors:
        logging.error("No valid results to evaluate")
        metrics = {"error": "No valid results"}
        comparison_file = None
    else:
        lat_errors, lon_errors, spherical_dists = map(np.array, [lat_errors, lon_errors, spherical_dists])
        
        # Calculate time interval statistics from records
        time_intervals = [record['mean_time_interval_seconds'] for record in imputation_records if record['mean_time_interval_seconds'] > 0]
        segment_durations = [record['segment_duration_seconds'] for record in imputation_records if record['segment_duration_seconds'] > 0]
        
        metrics = {
            'processed_segments': processed_segments,
            'processed_points': len(lat_errors),
            'latitude_mae': float(np.mean(lat_errors)),
            'longitude_mae': float(np.mean(lon_errors)),
            'latitude_rmse': float(np.sqrt(np.mean(lat_errors**2))),
            'longitude_rmse': float(np.sqrt(np.mean(lon_errors**2))),
            'mean_spherical_distance_km': float(np.mean(spherical_dists)),
            'max_spherical_distance_km': float(np.max(spherical_dists)),
            'min_spherical_distance_km': float(np.min(spherical_dists)),
            # Time statistics
            'mean_time_interval': float(np.mean(time_intervals)) if time_intervals else 0,
            'max_time_interval': float(np.max(time_intervals)) if time_intervals else 0,
            'min_time_interval': float(np.min(time_intervals)) if time_intervals else 0,
            'mean_segment_duration': float(np.mean(segment_durations)) if segment_durations else 0
        }

        comparison_file = save_comparison_csv(args, comparison_data)
        metrics['comparison_file'] = comparison_file
        
        # Save detailed imputation records (single CSV file)
        save_imputation_records(args, imputation_records)
        
        # Generate simplified visualization
        generate_simplified_visualization(args, imputation_records)
    
    logging.info("\n" + "="*50)
    logging.info("IMPUTATION EVALUATION RESULTS")
    logging.info("="*50)
    logging.info(f"Processed segments: {metrics['processed_segments']}")
    logging.info(f"Total points evaluated: {metrics['processed_points']}")
    logging.info(f"Latitude MAE: {metrics['latitude_mae']:.6f}")
    logging.info(f"Longitude MAE: {metrics['longitude_mae']:.6f}")
    logging.info(f"Latitude RMSE: {metrics['latitude_rmse']:.6f}")
    logging.info(f"Longitude RMSE: {metrics['longitude_rmse']:.6f}")
    logging.info(f"Mean spherical distance: {metrics['mean_spherical_distance_km']:.4f} km")
    logging.info(f"Max spherical distance: {metrics['max_spherical_distance_km']:.4f} km")
    logging.info(f"Min spherical distance: {metrics['min_spherical_distance_km']:.4f} km")
    logging.info(f"Mean time interval: {metrics['mean_time_interval']:.2f} s")
    logging.info(f"Mean segment duration: {metrics['mean_segment_duration']:.2f} s")
    
    if comparison_file:
        logging.info(f"Detailed comparison saved to: {comparison_file}")
    
    logging.info("="*50)
    
    saved_file = save_evaluation_results(args, metrics)
    logging.info(f"Results saved to: {saved_file}")
    
    return metrics

def generate_simplified_visualization(args, imputation_records):
    """Generate simplified visualization focusing on segment duration vs metrics"""
    root_path = get_root_path()
    viz_dir = os.path.join(root_path, 'results', args.exp_name, 'VISUALIZATIONS')
    os.makedirs(viz_dir, exist_ok=True)
    
    base_filename = f"{args.trajectory_num}_len{args.trajectory_len}_seed{args.seed}_{args.end_point_sdkg}_{args.end_point}"
    
    try:
        # Create 2x2 subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Define outlier thresholds - updated for segment duration
        OUTLIER_THRESHOLDS = {
            'mean_spherical_distance_km': 10.0,    # Remove distances > 10km
            'latitude_mae': 0.1,                   # Remove latitude MAE > 0.1 degrees
            'longitude_mae': 0.1,                  # Remove longitude MAE > 0.1 degrees
            'latitude_rmse': 0.1,                  # Remove latitude RMSE > 0.1 degrees
            'longitude_rmse': 0.1,                 # Remove longitude RMSE > 0.1 degrees
            'segment_duration_seconds': 10000       # Remove segment durations > 2 hours
        }
        
        # Configuration options
        BIN_SIZE = 300  # Segment duration bin size in seconds (5 minutes)
        AGGREGATION_METHOD = 'median'  # Options: 'median', 'mean', 'mode'
        MIN_SEGMENTS_PER_BIN = 1  # Minimum number of segments per bin
        
        # Extract data and filter out zero durations, zero metrics, and outliers
        valid_records = [
            record for record in imputation_records 
            if (record.get('segment_duration_seconds', 0) > 0 and 
                record.get('segment_duration_seconds', 0) <= OUTLIER_THRESHOLDS['segment_duration_seconds'] and
                record['mean_spherical_distance_km'] > 0 and
                record['mean_spherical_distance_km'] <= OUTLIER_THRESHOLDS['mean_spherical_distance_km'] and
                record['latitude_mae'] > 0 and 
                record['latitude_mae'] <= OUTLIER_THRESHOLDS['latitude_mae'] and
                record['longitude_mae'] > 0 and 
                record['longitude_mae'] <= OUTLIER_THRESHOLDS['longitude_mae'] and
                record['latitude_rmse'] > 0 and 
                record['latitude_rmse'] <= OUTLIER_THRESHOLDS['latitude_rmse'] and
                record['longitude_rmse'] > 0 and 
                record['longitude_rmse'] <= OUTLIER_THRESHOLDS['longitude_rmse'])
        ]
        
        # Count outliers for logging
        outlier_count = len(imputation_records) - len(valid_records)
        outlier_details = {
            'segment_duration': len([r for r in imputation_records if r.get('segment_duration_seconds', 0) > OUTLIER_THRESHOLDS['segment_duration_seconds']]),
            'spherical_distance': len([r for r in imputation_records if r['mean_spherical_distance_km'] > OUTLIER_THRESHOLDS['mean_spherical_distance_km']]),
            'lat_mae': len([r for r in imputation_records if r['latitude_mae'] > OUTLIER_THRESHOLDS['latitude_mae']]),
            'lon_mae': len([r for r in imputation_records if r['longitude_mae'] > OUTLIER_THRESHOLDS['longitude_mae']]),
            'lat_rmse': len([r for r in imputation_records if r['latitude_rmse'] > OUTLIER_THRESHOLDS['latitude_rmse']]),
            'lon_rmse': len([r for r in imputation_records if r['longitude_rmse'] > OUTLIER_THRESHOLDS['longitude_rmse']])
        }
        
        if not valid_records:
            logging.warning("No valid records with non-zero segment durations and metrics for visualization")
            return
        
        # Helper function for aggregation
        def aggregate_data(values, method):
            """Aggregate data using specified method"""
            if not values:
                return 0
            if method == 'median':
                return np.median(values)
            elif method == 'mean':
                return np.mean(values)
            elif method == 'mode':
                # For mode, use the most frequent value in binned data
                if len(values) > 1:
                    hist, bin_edges = np.histogram(values, bins=min(10, len(values)))
                    mode_index = np.argmax(hist)
                    return (bin_edges[mode_index] + bin_edges[mode_index + 1]) / 2
                else:
                    return values[0]
            else:
                return np.median(values)  # Default to median
        
        # Group by segment durations and calculate aggregates
        duration_bins = {}
        
        for record in valid_records:
            segment_duration = record.get('segment_duration_seconds', 0)
            bin_key = int(segment_duration // BIN_SIZE) * BIN_SIZE
            
            if bin_key not in duration_bins:
                duration_bins[bin_key] = {
                    'count': 0,
                    'durations': [],
                    'mean_distances': [],
                    'lat_mae': [],
                    'lon_mae': [],
                    'lat_rmse': [],
                    'lon_rmse': []
                }
            
            duration_bins[bin_key]['count'] += 1
            duration_bins[bin_key]['durations'].append(segment_duration)
            duration_bins[bin_key]['mean_distances'].append(record['mean_spherical_distance_km'])
            duration_bins[bin_key]['lat_mae'].append(record['latitude_mae'])
            duration_bins[bin_key]['lon_mae'].append(record['longitude_mae'])
            duration_bins[bin_key]['lat_rmse'].append(record['latitude_rmse'])
            duration_bins[bin_key]['lon_rmse'].append(record['longitude_rmse'])
        
        # Filter out bins with too few data points
        duration_bins = {k: v for k, v in duration_bins.items() if v['count'] >= MIN_SEGMENTS_PER_BIN}
        
        if not duration_bins:
            logging.warning("No bins with sufficient data points after filtering")
            return
        
        # Calculate aggregates for each duration bin
        bin_centers = []
        agg_durations = []
        agg_mean_distances = []
        agg_lat_mae = []
        agg_lon_mae = []
        agg_lat_rmse = []
        agg_lon_rmse = []
        bin_counts = []
        
        for bin_key, bin_data in sorted(duration_bins.items()):
            bin_center = bin_key + BIN_SIZE / 2
            bin_centers.append(bin_center)
            agg_durations.append(aggregate_data(bin_data['durations'], AGGREGATION_METHOD))
            agg_mean_distances.append(aggregate_data(bin_data['mean_distances'], AGGREGATION_METHOD))
            agg_lat_mae.append(aggregate_data(bin_data['lat_mae'], AGGREGATION_METHOD))
            agg_lon_mae.append(aggregate_data(bin_data['lon_mae'], AGGREGATION_METHOD))
            agg_lat_rmse.append(aggregate_data(bin_data['lat_rmse'], AGGREGATION_METHOD))
            agg_lon_rmse.append(aggregate_data(bin_data['lon_rmse'], AGGREGATION_METHOD))
            bin_counts.append(bin_data['count'])
        
        # 1. Segment duration vs Mean spherical distance
        scatter1 = axes[0, 0].scatter(bin_centers, agg_mean_distances, alpha=0.8, color='blue', 
                                     s=50, label=f'{AGGREGATION_METHOD.title()} Spherical Distance')
        # Connect points with lines to show trend
        axes[0, 0].plot(bin_centers, agg_mean_distances, 'b-', alpha=0.5, linewidth=1)
        axes[0, 0].set_xlabel('Segment Duration (s)')
        axes[0, 0].set_ylabel('Spherical Distance (km)')
        axes[0, 0].set_title(f'Segment Duration vs Spherical Distance\n({BIN_SIZE}s bins, {AGGREGATION_METHOD})')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Segment duration vs Latitude MAE and RMSE
        scatter2a = axes[0, 1].scatter(bin_centers, agg_lat_mae, alpha=0.8, color='red', 
                                      s=50, label='Latitude MAE')
        scatter2b = axes[0, 1].scatter(bin_centers, agg_lat_rmse, alpha=0.8, color='darkred', 
                                      s=50, label='Latitude RMSE', marker='s')
        # Connect points with lines
        axes[0, 1].plot(bin_centers, agg_lat_mae, 'r-', alpha=0.5, linewidth=1)
        axes[0, 1].plot(bin_centers, agg_lat_rmse, 'r--', alpha=0.5, linewidth=1)
        axes[0, 1].set_xlabel('Segment Duration (s)')
        axes[0, 1].set_ylabel('Latitude Error')
        axes[0, 1].set_title(f'Segment Duration vs Latitude Errors\n({BIN_SIZE}s bins, {AGGREGATION_METHOD})')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Segment duration vs Longitude MAE and RMSE
        scatter3a = axes[1, 0].scatter(bin_centers, agg_lon_mae, alpha=0.8, color='green', 
                                      s=50, label='Longitude MAE')
        scatter3b = axes[1, 0].scatter(bin_centers, agg_lon_rmse, alpha=0.8, color='darkgreen', 
                                      s=50, label='Longitude RMSE', marker='s')
        # Connect points with lines
        axes[1, 0].plot(bin_centers, agg_lon_mae, 'g-', alpha=0.5, linewidth=1)
        axes[1, 0].plot(bin_centers, agg_lon_rmse, 'g--', alpha=0.5, linewidth=1)
        axes[1, 0].set_xlabel('Segment Duration (s)')
        axes[1, 0].set_ylabel('Longitude Error')
        axes[1, 0].set_title(f'Segment Duration vs Longitude Errors\n({BIN_SIZE}s bins, {AGGREGATION_METHOD})')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Segment duration distribution (show bin distribution)
        bin_edges = [bin_key for bin_key in sorted(duration_bins.keys())] + [max(bin_centers) + BIN_SIZE/2]
        axes[1, 1].hist(bin_centers, bins=bin_edges, alpha=0.7, color='orange', 
                       weights=bin_counts, edgecolor='black')
        axes[1, 1].set_xlabel('Segment Duration (s)')
        axes[1, 1].set_ylabel('Number of Segments')
        axes[1, 1].set_title(f'Distribution of Segment Durations\n({BIN_SIZE}s bins)')
        axes[1, 1].grid(True, alpha=0.3)
        
        # Add text annotation with summary statistics
        '''
        fig.text(0.02, 0.02, 
                f'Bin size: {BIN_SIZE}s\n'
                f'Aggregation: {AGGREGATION_METHOD}\n'
                f'Total segments: {len(valid_records)}\n'
                f'Total bins: {len(bin_centers)}\n'
                f'Duration range: {min(agg_durations):.1f}s - {max(agg_durations):.1f}s\n'
                f'Filtered: non-zero metrics & outliers removed\n'
                f'Outlier thresholds:\n'
                f'  Distance: {OUTLIER_THRESHOLDS["mean_spherical_distance_km"]}km\n'
                f'  Lat/Lon errors: {OUTLIER_THRESHOLDS["latitude_mae"]}°\n'
                f'  Duration: {OUTLIER_THRESHOLDS["segment_duration_seconds"]}s',
                fontsize=7, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        '''
        # Add point size indicating number of segments in each bin
        for ax in [axes[0, 0], axes[0, 1], axes[1, 0]]:
            for i, count in enumerate(bin_counts):
                if count > np.mean(bin_counts) * 1.5:  # Highlight bins with many segments
                    ax.annotate(f'n={count}', (bin_centers[i], agg_mean_distances[i]), 
                               xytext=(5, 5), textcoords='offset points', fontsize=6, alpha=0.7)
        
        plt.tight_layout()
        plot_filename = os.path.join(viz_dir, f"segment_duration_analysis_{AGGREGATION_METHOD}_{base_filename}.png")
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Segment duration visualization saved to: {plot_filename}")
        logging.info(f"Processed {len(valid_records)} valid segments into {len(bin_centers)} {BIN_SIZE}s bins")
        logging.info(f"Aggregation method: {AGGREGATION_METHOD}")
        logging.info(f"Filtered out {outlier_count} outlier records")
        logging.info(f"Outlier details: {outlier_details}")
        
        # Print bin information for debugging
        logging.info("Bin summary:")
        for i, bin_center in enumerate(bin_centers):
            logging.info(f"Bin {i+1}: {bin_center-BIN_SIZE/2:.0f}-{bin_center+BIN_SIZE/2:.0f}s, "
                        f"segments: {bin_counts[i]}, {AGGREGATION_METHOD}_distance: {agg_mean_distances[i]:.4f}km")
        
    except Exception as e:
        logging.warning(f"Failed to generate visualization: {e}")

def save_imputation_records(args, imputation_records):
    """Save imputation records to a single CSV file"""
    root_path = get_root_path()
    records_dir = os.path.join(root_path, 'results', args.exp_name, 'RECORDS')
    os.makedirs(records_dir, exist_ok=True)
    
    # Save all records in one CSV file
    filename = f"imputation_records{args.trajectory_num}_len{args.trajectory_len}_seed{args.seed}_{args.end_point_sdkg}_{args.end_point}.csv"
    file_path = os.path.join(records_dir, filename)
    
    records_df = pd.DataFrame(imputation_records)
    records_df.to_csv(file_path, index=False, encoding='utf-8')
    logging.info(f"Imputation records saved to: {file_path}")
    
    return file_path
