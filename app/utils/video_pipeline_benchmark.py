"""Video processing pipeline for extracting and analyzing score tables from videos."""
import json
import math
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import torch
from torchvision import transforms
from ultralytics.utils.nms import TorchNMS

from app.services.model_loader import load_models

def sharpness(frame):
    """Calculate the sharpness of a frame using the variance of the Laplacian.
    
    Args:
        frame (np.ndarray): Input video frame.
        
    Returns:
        float: Sharpness score.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var

def select_best_frame(frames):
    """Select the sharpest frame from a list of frames.
    
    Args:
        frames (list of np.ndarray): List of video frames.

    Returns:
        np.ndarray | None: The sharpest frame or None if no valid frames are found.
    """
    if not frames:
        return None
    best_frame = max(frames, key=sharpness)
    return best_frame

import numpy as np

def crop_score_table(frame, min_area_ratio=0.05):
    """Detect and crop the score table region from a frame.
    
    Args:
        frame (np.ndarray): Input video frame.
        min_area_ratio (float): Minimum area ratio to consider a contour as table.

    Returns:
        np.ndarray | None: Cropped score table region or None if not found.
    """
    h, w = frame.shape[:2]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh,
                                   cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Use a minimum relative area to handle different video resolutions
    min_area = (h * w) * min_area_ratio

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue  # Skip small contours

        # Apply perspective correction (warping)
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = np.array(box, dtype=np.float32)

        # Sort box points to consistent order: top-left, top-right, bottom-right, bottom-left
        s = box.sum(axis=1)
        diff = np.diff(box, axis=1)
        pts = np.array([box[np.argmin(s)], box[np.argmin(diff)],
                        box[np.argmax(s)], box[np.argmax(diff)]], dtype="float32")

        (tl, tr, br, bl) = pts

        table_width = int(max(np.linalg.norm(br - bl),
                              np.linalg.norm(tr - tl)))
        table_height = int(max(np.linalg.norm(tr - br),
                               np.linalg.norm(tl - bl)))

        # Destination points for perspective transform
        dst = np.array([
            [0, 0], [table_width - 1, 0],
            [table_width - 1, table_height - 1], [0, table_height - 1]
        ], dtype="float32")

        # Perspective transform
        M = cv2.getPerspectiveTransform(pts, dst)
        table_warped = cv2.warpPerspective(frame, M, (table_width, table_height))

        # Crop the right half (score area)
        crop = table_warped[:, table_width // 2 : table_width]
        crop_h, crop_w = crop.shape[:2]
        if crop_h == 0 or crop_w == 0:
            continue  # Skip if cropped area is invalid

        return crop

    return None

def letterbox(img, new_shape=1280, color=(114,114,114)):
    """Resize and pad image to meet desired shape while maintaining aspect ratio.
    
    Args:
        img (np.ndarray): Input image.
        new_shape (int): Desired new shape (square).
        color (tuple): Padding color.
    
    Returns:
        np.ndarray: Resized and padded image.
        float: Scaling ratio.
        tuple: Padding applied (pad_x, pad_y).
    """
    h0, w0 = img.shape[:2]
    r = new_shape / max(h0, w0)
    new_unpad = (int(w0 * r), int(h0 * r))
    img_resized = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

    dw = new_shape - new_unpad[0]
    dh = new_shape - new_unpad[1]
    top, bottom = dh // 2, dh - dh // 2
    left, right = dw // 2, dw - dw // 2
    img_padded = cv2.copyMakeBorder(img_resized, top, bottom, left, right,
                                    cv2.BORDER_CONSTANT, value=color)
    return img_padded, r, (left, top)

def scale_coords(boxes, img_shape_orig, ratio, pad):
    """Scale bounding box coordinates back to original image shape.
    
    Args:
        boxes (torch.Tensor): Bounding boxes in resized image.
        img_shape_orig (tuple): Original image shape (height, width).
        ratio (float): Scaling ratio used during resizing.
        pad (tuple): Padding applied during resizing (pad_x, pad_y).
    
    Returns:
        torch.Tensor: Scaled bounding boxes in original image coordinates.
    """
    pad_x, pad_y = pad
    boxes[:, [0,2]] -= pad_x
    boxes[:, [1,3]] -= pad_y
    boxes /= ratio
    # Clamping
    boxes[:, 0].clamp_(0, img_shape_orig[1])
    boxes[:, 1].clamp_(0, img_shape_orig[0])
    boxes[:, 2].clamp_(0, img_shape_orig[1])
    boxes[:, 3].clamp_(0, img_shape_orig[0])
    return boxes

def filter_outliers(detections, img_orig, ratio, pad, device="cpu", threshold_ratio=0.8,
                    num_rows=9):
    """Filter out bounding boxes that are outside a vertical column defined by a threshold.

    Args:
        detections (torch.Tensor): Detected bounding boxes.
        img_orig (np.ndarray): Original image.
        ratio (float): Scaling ratio used during resizing.
        pad (tuple): Padding applied during resizing (pad_x, pad_y).
        device (str): Device type ('cpu' or 'cuda').
        threshold_ratio (float): Ratio to define the vertical column threshold.
    
    Returns:
        torch.Tensor: Filtered bounding boxes.
    """
    # Apply scaling to original image coordinates
    detections[:, :4] = scale_coords(detections[:, :4], img_orig.shape, ratio, pad)

    img_w = img_orig.shape[1]
    # Define threshold based on image width
    x_threshold = img_w * threshold_ratio

    img_h = img_orig.shape[0]
    y_threshold = img_h // (num_rows + 1)

    # Filter detections based on x1 coordinate
    good_detections = []
    for det in detections:
        # Use the left edge (x1) to be more certain than x_center
        if det[0] < x_threshold and det[1] > y_threshold: 
            good_detections.append(det)

    if not good_detections:
        # If all were filtered out, create an empty tensor to avoid errors
        detections = torch.empty((0, 6), device=device) 
    else:
        # 'detections' now only contains the filtered boxes
        detections = torch.stack(good_detections)

    return detections

def sanitize_score_string(s: str) -> str:
    """Sanitize a score string to keep only digits and at most one dot.
    
    Args:
        s (str): Input score string.
    
    Returns:
        str: Sanitized score string.
    """
    if not s:
        return ""

    s_out = ""
    dot_found = False

    for char in s:
        if char == '.':
            # Allow only one dot
            if not dot_found:
                s_out += char
                dot_found = True
        elif char.isdigit():
            s_out += char

    s_out_stripped = s_out.strip('.')
    return s_out_stripped

def _find_nearest_digit_slot(decimal_char: dict, main_digits: list, y_min_anchor: float,
                             slot_height_real: float, num_rows: int = 9) -> int:
    """Find the nearest main digit to a decimal character and determine its slot index.
    
    Args:
        decimal_char (dict): Detected decimal character with coordinates.
        main_digits (list): List of detected main digit characters.
        y_min_anchor (float): Minimum y_center anchor of main digits.
        slot_height_real (float): Height of each slot.
        num_rows (int): Total number of rows including total score row.
    
    Returns:
        int: Slot index for the decimal character, or -1 if no main digits exist.
    """
    if not main_digits:
        # No main digits to compare with
        return -1 

    min_dist = float('inf')
    nearest_digit_y_center = -1

    dec_x_center = (decimal_char['x1'] + decimal_char['x2']) / 2
    dec_y_center = decimal_char['y_center']

    for digit in main_digits:
        dig_x_center = (digit['x1'] + digit['x2']) / 2
        dig_y_center = digit['y_center']

        # Calculate Euclidean distance
        dist = math.sqrt((dec_x_center - dig_x_center)**2 + (dec_y_center - dig_y_center)**2)

        if dist < min_dist:
            min_dist = dist
            nearest_digit_y_center = dig_y_center

    # Determine slot index based on nearest digit's y_center
    if slot_height_real == 0:
        slot_index = 0
    else:
        relative_y = nearest_digit_y_center - y_min_anchor
        slot_index = int(round(relative_y / slot_height_real))

    return max(0, min(slot_index, num_rows - 1))

def finalize_scores_by_slotting(char_detections: list, question_amount: int,
                                num_rows: int = 9) -> dict:
    """Assemble scores by slotting detected characters into rows based on y_center"
    
    Args:
        char_detections (list): List of detected characters with their coordinates.
        question_amount (int): Number of questions (slots with scores) expected.
        num_rows (int): Total number of rows including total score row.
    
    Returns:
        dict: Final scores in JSON format.
    """
    # Separate main digits and satellite characters
    main_digits = []
    satellite_chars = []
    for char in char_detections:
        if char['char'].isdigit():
            main_digits.append(char)
        elif char['char'] == '.':
            satellite_chars.append(char)

    # Handle case with no main digits detected
    if not main_digits:
        output_json = {}
        for i in range(num_rows - 1):
            output_json[f"question_{i+1}"] = 0.0
        output_json["total_score"] = 0.0
        return output_json

    # Find stable y_centers of main digits using DBSCAN
    y_centers_digits = []
    char_heights = []
    for char in main_digits:
        y_centers_digits.append(char['y_center'])
        height = char['y2'] - char['y1']
        if height > 0:
            char_heights.append(height)

    y_min_anchor = min(y_centers_digits)
    y_max_anchor = max(y_centers_digits)

    if char_heights:
        avg_char_height = np.mean(char_heights)
        eps = avg_char_height * 0.75  # 75% of the average height of a digit

        y_centers_np = np.array(y_centers_digits).reshape(-1, 1)
        db = DBSCAN(eps=eps, min_samples=1).fit(y_centers_np)
        labels = db.labels_

        stable_row_centers = []
        for label in set(labels):
            if label == -1: continue
            points_in_cluster = y_centers_np[labels == label]
            stable_row_centers.append(np.mean(points_in_cluster))

        if stable_row_centers:
            y_min_anchor = min(stable_row_centers)
            y_max_anchor = max(stable_row_centers)

    # Calculate table height and slot height
    table_height_real = y_max_anchor - y_min_anchor

    if table_height_real == 0 or (num_rows - 1) == 0:
        slot_height_real = 0 
    else:
        slot_height_real = table_height_real / (num_rows - 1)

    # Assign characters to slots
    slots = [[] for _ in range(num_rows)]

    # Assign main digits
    for char in main_digits:
        if slot_height_real == 0:
            slot_index = 0
        else:
            relative_y = char['y_center'] - y_min_anchor
            slot_index = int(round(relative_y / slot_height_real))
        
        slot_index = max(0, min(slot_index, num_rows - 1))
        slots[slot_index].append(char)

    # Assign satellite characters (decimal separator)
    for char in satellite_chars:
        slot_index = _find_nearest_digit_slot(
            char, main_digits, y_min_anchor, slot_height_real, num_rows
        )
        if slot_index != -1:
            slots[slot_index].append(char)

    # Assemble scores for each slot
    final_scores = {}
    for i in range(num_rows):
        chars_in_this_row = slots[i]
        score_value = 0.0

        if chars_in_this_row:
            for d in chars_in_this_row:
                d['x_center'] = (d['x1'] + d['x2']) / 2
            sorted_chars = sorted(chars_in_this_row, key=lambda d: d['x_center'])
            score_str = "".join([d['char'] for d in sorted_chars])
            sanitized_str = sanitize_score_string(score_str)

            if sanitized_str:
                try:
                    score_value = float(sanitized_str)
                except ValueError:
                    score_value = 0.0

        # Handle absurd values: only the total score can be equal to 20
        if score_value >= 20.0 and i < num_rows - 1:
            score_value = score_value / pow(10, len(str(int(score_value))) - 1)
        if score_value > 20.0 and i == num_rows - 1:
            score_value = score_value / pow(10, len(str(int(score_value))) - 1)
        final_scores[i] = score_value

    output_json = {}
    for i in range(num_rows - 1):
        key_name = f"question_{i+1}"
        if i >= question_amount:
            # For non-existing questions, assign 0.0
            output_json[key_name] = 0.0
        else:
            output_json[key_name] = final_scores[i]
    output_json["total_score"] = final_scores[num_rows - 1]

    return output_json

def finalize_scores_by_slotting_old(char_detections: list, question_amount: int, num_rows=9) -> dict:
    """(DEPRECATED) Assemble scores by slotting detected characters into rows based on y_center.
    
    Args:
        char_detections (list): List of detected characters with their coordinates.
        question_amount (int): Number of questions (slots) expected.
        num_rows (int): Total number of rows including total score row.
        
    Returns:
        dict: Final scores in JSON format.
    """
    slots = [[] for _ in range(num_rows)]

    # If no characters detected, return zeros
    if not char_detections:
        output_json = {}
        for i in range(num_rows - 1):
            output_json[f"question_{i+1}"] = 0.0
        output_json["total_score"] = 0.0
        return output_json

    # Find vertical bounds of detected characters
    """all_y_centers = [char['y_center'] for char in char_detections]
    y_min_detected = min(all_y_centers)
    y_max_detected = max(all_y_centers)"""
    all_y1 = [char['y1'] for char in char_detections]
    all_y2 = [char['y2'] for char in char_detections]
    y_min_detected = min(all_y1)
    y_max_detected = max(all_y2)

    # Calculate the estimated height of the table
    table_height_real = y_max_detected - y_min_detected
    if table_height_real == 0:
        return {"error": "Table height cannot be zero."}
    elif question_amount == 0:
        return {"error": "Question amount cannot be zero."}
    else:
        # Calculate average slot height
        slot_height_real = table_height_real / (num_rows - 1)

    # Assign characters to slots based on y_center
    for char in char_detections:
        y = char['y_center']

        # Calculate relative position to the first digit
        relative_y = y - y_min_detected

        # Assign to the nearest slot
        slot_index = int(round(relative_y / slot_height_real))

        # Ensure it is within bounds
        slot_index = max(0, min(slot_index, num_rows - 1))

        slots[slot_index].append(char)

    # Assemble scores for each slot
    final_scores = {}
    for i in range(num_rows):
        chars_in_this_row = slots[i]

        score_value = 0.0  # Default value if the slot is empty

        if chars_in_this_row:
            for d in chars_in_this_row:
                d['x_center'] = (d['x1'] + d['x2']) / 2
            sorted_chars = sorted(chars_in_this_row, key=lambda d: d['x_center'])

            # Assemble score string
            score_str = "".join([d['char'] for d in sorted_chars])

            # Sanitize the score string
            sanitized_str = sanitize_score_string(score_str)

            if sanitized_str:
                try:
                    score_value = float(sanitized_str)
                except ValueError:
                    score_value = 0.0  # Fallback if conversion fails

        # Adjust score if it's unreasonably high
        if score_value >= 20.0 and i < num_rows - 1:
            score_value = score_value / pow(10, len(str(int(score_value))) - 1)
        final_scores[i] = score_value

    output_json = {}

    for i in range(num_rows - 1):
        key_name = f"question_{i+1}"

        if i >= question_amount:
            # For non-existing questions, assign 0.0
            output_json[key_name] = 0.0
        else:
            output_json[key_name] = final_scores[i]

    output_json["total_score"] = final_scores[num_rows - 1]

    return output_json

def calculate_statistics(all_booklet_scores: list, question_amount: int) -> dict:
    """Calculate statistics (mean, median, std, min, max) for total and per-question scores.
    
    Args:
        all_booklet_scores (list): List of booklet scores in JSON format.
        question_amount (int): Number of questions.
    
    Returns:
        dict: Calculated statistics.
    """
    total_scores = []
    question_scores_map = {
        f"question_{i+1}": [] for i in range(question_amount)
    }
    # Save question scores and recalculate total score
    for booklet in all_booklet_scores:
        current_booklet_sum = 0.0

        for i in range(question_amount):
            q_key = f"question_{i+1}"
            q_score = booklet.get(q_key, 0.0)
            if isinstance(q_score, (int, float)):
                question_scores_map[q_key].append(q_score)
                current_booklet_sum += q_score

        booklet["total_score"] = current_booklet_sum
        total_scores.append(current_booklet_sum)

    stats_dict = {}
    if total_scores:
        scores_array = np.array(total_scores)
        stats_dict = {
            "count": len(total_scores),
            "mean": np.mean(scores_array),
            "median": np.median(scores_array),
            "std_dev": np.std(scores_array),
            "min": np.min(scores_array),
            "max": np.max(scores_array)
        }
    else:
        stats_dict = {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "min": 0.0,
            "max": 0.0
        }

    question_stats = {}
    for q_key, scores_list in question_scores_map.items():
        if scores_list:
            scores_array = np.array(scores_list)
            question_stats[q_key] = {
                "count": len(scores_array),
                "mean": np.mean(scores_array),
                "median": np.median(scores_array),
                "std_dev": np.std(scores_array),
                "min": np.min(scores_array),
                "max": np.max(scores_array)
            }
        else:
            question_stats[q_key] = {
                "count": 0,
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "min": 0.0,
                "max": 0.0
            }

    stats_dict["question_stats"] = question_stats

    return stats_dict

def process_video_benchmarked(video_path: str, stride=10,
                              iou_threshold=0.5, question_amount=8,
                              frames_indexes: Optional[List[int]] = None)-> Tuple[Dict, Dict]:
    """Process a video to extract relevant frames, detect bounding boxes,
    and classify digits using pre-loaded machine learning models.
    
    Args:
        video_path (str): Path to the video file.
        stride (int): Process every N frames.
        iou_threshold (float): IoU threshold for NMS.
        question_amount (int): Number of questions in the assessment.
        frames_indexes (List[int], optional): Specific frame indexes to process.
    
    Returns:
        dict: Extracted scores and statistics.
    """
    total_start_time = time.perf_counter()

    t_selection = 0.0
    t_crop = 0.0
    t_detection = 0.0
    t_classification = 0.0
    t_assembly = 0.0

    # Load models
    models = load_models()
    device = models["device"]
    frames_model = models["frames"]
    recognizer_model = models["recognizer"]
    classifier_model = models["classifier"]

    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    # --------------------------------
    # Filter and crop relevant frames
    # --------------------------------

    # Read video frames
    frames_to_process = []
    selection_loop_start = time.perf_counter()
    if frames_indexes is not None and len(frames_indexes) > 0:
        # Get FPS to calculate frame time
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps is None:
            fps = 30  # Default to 30 if FPS cannot be determined

        # Convert timestamps in milliseconds to frame indexes
        target_frame_indexes = set()
        for timestamp_ms in frames_indexes:
            frame_idx = int((timestamp_ms / 1000.0) * fps)
            target_frame_indexes.add(frame_idx)

        # Iterate through video and extract specified frames
        frame_idx_counter = 0
        while True:
            ret = cap.grab()
            if not ret:
                break

            # Check if current frame index is in target indexes
            if frame_idx_counter in target_frame_indexes:
                ret, frame = cap.retrieve()
                if ret:
                    t_c_start = time.perf_counter()
                    crop = crop_score_table(frame)
                    t_crop += (time.perf_counter() - t_c_start)
                    if crop is not None:
                        frames_to_process.append(crop)

                # Remove processed index to speed up future checks
                target_frame_indexes.remove(frame_idx_counter)

                # Break early if all target frames have been processed
                if not target_frame_indexes:
                    break

            frame_idx_counter += 1
    else:
        # Preprocessing for frame relevance model
        preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                [0.229, 0.224, 0.225]) # ImageNet stats
        ])

        frame_idx = 0
        relevant_buffer = []
        while True:
            # Read next frame from video
            ret = cap.grab()

            if not ret:
                # Finish processing remaining relevant frames
                best_frame = select_best_frame(relevant_buffer)
                if best_frame is not None:
                    t_c_start = time.perf_counter()
                    crop = crop_score_table(best_frame)
                    t_crop += (time.perf_counter() - t_c_start)
                    if crop is not None:
                        frames_to_process.append(crop)
                break

            if frame_idx % stride == 0:
                # Decode the frame (one out of every 'stride' frames)
                ret, frame = cap.retrieve()
                if not ret:
                    break
                frame_tensor = preprocess(frame).unsqueeze(0).to(device)  # type: ignore
                with torch.no_grad():
                    relevance = frames_model(frame_tensor)  # Shape [1, num_classes]
                    pred_class = relevance.argmax(dim=1).item()  # Predicted class as scalar
                if pred_class == 1:  # Relevant frame
                    relevant_buffer.append(frame)
                else:
                    # If the relevant frame sequence ends, select the best frame
                    best_frame = select_best_frame(relevant_buffer)
                    if best_frame is not None:
                        t_c_start = time.perf_counter()
                        crop = crop_score_table(best_frame)
                        t_crop += (time.perf_counter() - t_c_start)
                        if crop is not None:
                            frames_to_process.append(crop)
                    relevant_buffer = []

            frame_idx += 1

    cap.release()

    total_selection_loop_time = time.perf_counter() - selection_loop_start
    t_selection = total_selection_loop_time - t_crop

    if not frames_to_process:
        return {"scores": [], "statistics": calculate_statistics([], question_amount)}, {}

    # -----------------------------------------------------
    # Detect bounding boxes on ROI for each selected frame
    # -----------------------------------------------------

    # Process each cropped frame
    final_detections = []
    det_start = time.perf_counter()
    for idx, img_orig in enumerate(frames_to_process):
        img_rgb = cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)

        crop_resized, ratio, pad = letterbox(img_rgb, new_shape=1280)
        crop_tensor = torch.from_numpy(crop_resized).permute(2, 0, 1).float()/255.0
        crop_tensor = crop_tensor.unsqueeze(0).to(device)

        with torch.no_grad():
            preds = recognizer_model(crop_tensor)[0]

        boxes = preds[:, :4]
        scores = preds[:, 4]
        # classes = preds[:, 5]

        # NMS
        keep = TorchNMS.nms(boxes, scores, iou_threshold=iou_threshold)
        detections = preds[keep]

        detections = filter_outliers(detections, img_orig, ratio, pad, device, threshold_ratio=0.8)

        final_detections.append(detections)

    t_detection = time.perf_counter() - det_start

    # -------------------------
    # Classify detected digits
    # -------------------------

    # Normalization stats for classifier obtained from original training data
    classifier_mean = [0.7138324946621879, 0.6752742936984362, 0.6944984441793525]
    classifier_std = [0.06064024192479617, 0.08277346212477447, 0.07542827455486965]

    # Preprocessing for digit classifier
    classifier_preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(classifier_mean, classifier_std)
    ])

    # Classify each detected digit and assemble scores
    #final_predictions = []
    index_to_class = {
        0: '0',
        1: '1',
        2: '.',  # The model was trained with the class 10 in the index 2 representing '.'
        3: '2',
        4: '3',
        5: '4',
        6: '5',
        7: '6',
        8: '7',
        9: '8',
        10: '9'
    }
    all_booklet_scores = []
    for detections, img_orig in zip(final_detections, frames_to_process):
        char_detections_in_frame = []
        for det in detections:
            x1f, y1f, x2f, y2f, conf, cls = det.cpu().numpy()

            # Clamping: ensure coordinates are within image bounds
            h, w = img_orig.shape[:2]
            x1 = max(0, int(np.floor(x1f)))
            y1 = max(0, int(np.floor(y1f)))
            x2 = min(w, int(np.ceil(x2f)))
            y2 = min(h, int(np.ceil(y2f)))

            # Avoid empty crops
            if x1 >= x2 or y1 >= y2:
                continue

            digit_crop = img_orig[y1:y2, x1:x2]
            if digit_crop.size == 0:
                continue  # Skip invalid crops

            t_cls_start = time.perf_counter()

            digit_crop_rgb = cv2.cvtColor(digit_crop, cv2.COLOR_BGR2RGB)
            digit_tensor = classifier_preprocess(digit_crop_rgb).unsqueeze(0).to(device)

            with torch.no_grad():
                digit_pred = classifier_model(digit_tensor)
                digit_class_idx = digit_pred.argmax(dim=1).item()

                t_classification += (time.perf_counter() - t_cls_start)

                if digit_class_idx not in index_to_class:
                    continue  # Skip unknown classes
                digit_class_name = index_to_class[digit_class_idx]
                #final_predictions.append((digit_class_name, conf))
                char_detections_in_frame.append({
                    'char': digit_class_name,
                    'x1': x1, 'x2': x2,
                    'y_center': (y1 + y2) / 2,
                    'y1': y1, 'y2': y2
                })

        t_assem_start = time.perf_counter()
        # Assemble score string from detected characters based on spatial arrangement
        frame_json_output = finalize_scores_by_slotting(
            char_detections_in_frame,
            question_amount
        )
        t_assembly += (time.perf_counter() - t_assem_start)
        all_booklet_scores.append(frame_json_output)

    stats_dict = calculate_statistics(all_booklet_scores, question_amount)

    final_output = {
        "scores": all_booklet_scores,
        "statistics": stats_dict
    }

    total_end_time = time.perf_counter()
    total_time = total_end_time - total_start_time

    measured_sum = t_selection + t_crop + t_detection + t_classification + t_assembly
    t_others = total_time - measured_sum

    timing_stats = {
        "selection": t_selection,
        "crop": t_crop,
        "detection": t_detection,
        "classification": t_classification,
        "assembly": t_assembly,
        "others": t_others,
        "total": total_time
    }

    return final_output, timing_stats

def select_timestamps_interactively(video_path: str) -> List[int]:
    """Interactively select timestamps from a video using keyboard inputs.
    
    Args:
        video_path (str): Path to the video file.
        
    Returns:
        List[int]: List of selected timestamps in milliseconds.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
    
    selected_timestamps = []
    paused = False

    print("\n--- Interactive Timestamp Selection ---")
    print("Press 'S' to select the current frame's timestamp, 'P' to pause/resume, 'Q' to quit.")
    print("-------------------------------")

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("End of video reached.")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
                continue

        # Copy frame for display
        display_frame = frame.copy()

        # Get current timestamp
        curr_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

        # Display info on the screen
        status = "PAUSED" if paused else "PLAYING"
        cv2.putText(display_frame, f"Status: {status}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Time: {int(curr_ms)} ms", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(display_frame, f"Saved: {len(selected_timestamps)}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Timestamp Selector (Use 'S' to save, 'P' to pause/resume, 'Q' to quit)", display_frame)

        # Speed control: If paused, wait indefinitely (0 ms) until a key is pressed
        # Otherwise, wait 30 ms between frames
        wait_ms = 0 if paused else 30
        key = cv2.waitKey(wait_ms) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
        elif key == ord('s'):
            ts_int = int(curr_ms)
            selected_timestamps.append(ts_int)
            print(f" [+] Timestamp saved: {ts_int} ms")
            # Small visual flash to confirm
            cv2.putText(display_frame, "SAVED!", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.imshow("Timestamp Selector (Use 'S' to save, 'Q' to quit)", display_frame)
            cv2.waitKey(200) # Brief pause to see the message

    cap.release()
    cv2.destroyAllWindows()
    
    # Return unique sorted timestamps
    return sorted(list(set(selected_timestamps)))

if __name__ == "__main__":
    video_path = "app/services/video_012.mp4"
    ITERATIONS = 10
    selected_timestamps = None

    # Select timestamps interactively (uncomment to use)
    selected_timestamps = select_timestamps_interactively(video_path)
    print(f"Selected timestamps (ms): {selected_timestamps}")
    
    print(f"Starting Benchmark ({ITERATIONS} iterations) for: {video_path}\n")
    
    # Store results of each iteration
    history = {
        "selection": [], "crop": [], "detection": [],
        "classification": [], "assembly": [], "others": [], "total": []
    }

    for i in range(ITERATIONS):
        print(f"Running iteration {i+1}/{ITERATIONS}...", end="\r", flush=True)
        
        # Benchmark call
        _, stats = process_video_benchmarked(
            video_path, stride=10, iou_threshold=0.5, question_amount=4,
            frames_indexes=selected_timestamps
        )
        
        # Save metrics
        for key in history:
            history[key].append(stats[key])

    print(f"\n{'='*60}")
    print(f"{'PHASE':<25} | {'AVG TIME (s)':<15} | {'% OF TOTAL':<10}")
    print(f"{'-'*60}")

    # Calculate averages
    avg_total = sum(history["total"]) / ITERATIONS

    phases_order = ["selection", "crop", "detection", "classification", "assembly", "others"]
    phases_es = {
        "selection": "Frame Selection",
        "crop": "Crops",
        "detection": "Detection (BBoxes)",
        "classification": "Digit Classification",
        "assembly": "Score Assembly",
        "others": "Others (Load/IO/Misc)"
    }

    for phase in phases_order:
        avg_time = sum(history[phase]) / ITERATIONS
        pct = (avg_time / avg_total) * 100
        print(f"{phases_es[phase]:<25} | {avg_time:.4f} s        | {pct:.1f}%")

    print(f"{'-'*60}")
    print(f"{'AVG TOTAL TIME':<25} | {avg_total:.4f} s")
    print(f"{'='*60}")
