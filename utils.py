import os
import json
import cv2
import numpy as np
from datetime import datetime

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_defects(image_path, json_path, output_root_dir):
    """
    Extract defects from an image based on its labelme json file.
    Saves extracted defects to output_root_dir/{label}/.
    """
    if not os.path.exists(image_path) or not os.path.exists(json_path):
        print(f"Error: Files not found: {image_path}, {json_path}")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # Read image
    # Handle chinese paths or special characters if needed, usually cv2.imread fails with unicode paths on Windows
    # So use numpy fromfile trick
    try:
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    if img is None:
        print(f"Failed to load image: {image_path}")
        return

    image_height, image_width = img.shape[:2]
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    for idx, shape in enumerate(data.get('shapes', [])):
        label = shape.get('label', 'unknown')
        points = shape.get('points', [])
        shape_type = shape.get('shape_type', 'polygon')

        if not points:
            continue

        points = np.array(points, dtype=np.int32)

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(points)
        
        # Add some padding if needed? No, user said minimum bounding rectangle.
        # Ensure within image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, image_width - x)
        h = min(h, image_height - y)

        if w <= 0 or h <= 0:
            continue

        # Crop image
        crop = img[y:y+h, x:x+w]

        # Create mask for transparency
        # Create a mask of the same size as crop
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # Shift points to crop coordinates
        shifted_points = points - [x, y]
        
        # Fill polygon on mask
        cv2.fillPoly(mask, [shifted_points], 255)

        # Create RGBA image
        b, g, r = cv2.split(crop)
        rgba = cv2.merge([b, g, r, mask])

        # Prepare output directory
        defect_dir = os.path.join(output_root_dir, label)
        ensure_dir(defect_dir)

        # Save image
        output_filename = f"{base_name}_{idx}.png"
        output_path = os.path.join(defect_dir, output_filename)
        
        # Use cv2.imencode for unicode path support
        success, encoded_img = cv2.imencode('.png', rgba)
        if success:
            encoded_img.tofile(output_path)

        # Create new labelme json for this defect
        # The points are relative to the new small image
        new_shape = shape.copy()
        new_shape['points'] = shifted_points.tolist()
        
        new_json_data = {
            "version": data.get("version", "4.5.6"),
            "flags": {},
            "shapes": [new_shape],
            "imagePath": output_filename,
            "imageData": None, # Could encode base64 if needed, but usually optional if path is correct
            "imageHeight": h,
            "imageWidth": w
        }

        json_output_path = os.path.join(defect_dir, f"{base_name}_{idx}.json")
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(new_json_data, f, ensure_ascii=False, indent=2)

    return True

def create_synthesized_json(base_image_path, output_image_path, items_data):
    """
    Create a LabelMe JSON for the synthesized image.
    items_data: List of dicts with keys: label, points (absolute coordinates in new image), shape_type
    """
    # Read base image to get dimensions
    try:
        img_array = np.fromfile(output_image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        h, w = img.shape[:2]
    except:
        h, w = 0, 0 # Should handle error

    shapes = []
    for item in items_data:
        shapes.append({
            "label": item['label'],
            "points": item['points'],
            "group_id": None,
            "shape_type": item.get('shape_type', 'polygon'),
            "flags": {}
        })

    json_data = {
        "version": "4.5.6",
        "flags": {},
        "shapes": shapes,
        "imagePath": os.path.basename(output_image_path),
        "imageData": None,
        "imageHeight": h,
        "imageWidth": w
    }

    output_json_path = os.path.splitext(output_image_path)[0] + ".json"
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

