# Custom Face Analysis with YOLO Integration
# Based on face_analysis_adj.py
import sys
import os
from pathlib import Path
import numpy as np
import torch
from ultralytics import YOLO
import cv2
import glob
import os.path as osp
import onnxruntime

# Add insightface to path
insightface_path = Path(__file__).parent.parent / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

from insightface.app.common import Face
from insightface.model_zoo import model_zoo
from insightface.utils import DEFAULT_MP_NAME, ensure_available


class CustomFaceAnalysis:
    def __init__(self, name=DEFAULT_MP_NAME, root='~/.insightface', allowed_modules=None, yolo_model_path='yolov11l-face.pt', use_yolo=True, **kwargs):
        onnxruntime.set_default_logger_severity(3)
        self.models = {}
        self.use_yolo = True  # Force YOLO usage
        
        # Load YOLO model for detection (required)
        try:
            print(f"Loading YOLO model from: {yolo_model_path}")
            self.yolo_model = self.load_yolo_model(yolo_model_path)
            # Add YOLO model to models dictionary
            self.models['detection'] = 'yolo'  # Placeholder to satisfy assertion
            print("YOLO model loaded successfully for face detection")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise RuntimeError(f"Failed to load YOLO model: {e}")
        
        # Load only non-detection InsightFace models (like recognition, gender/age, etc.)
        self.model_dir = ensure_available('models', name, root=root)
        onnx_files = glob.glob(osp.join(self.model_dir, '*.onnx'))
        onnx_files = sorted(onnx_files)
        for onnx_file in onnx_files:
            model = model_zoo.get_model(onnx_file, **kwargs)
            if model is None:
                print('model not recognized:', onnx_file)
            elif model.taskname == 'detection':
                # Skip detection models since we're using YOLO
                print('skipping detection model (using YOLO):', onnx_file, model.taskname)
                del model
            elif allowed_modules is not None and model.taskname not in allowed_modules:
                print('model ignore:', onnx_file, model.taskname)
                del model
            elif model.taskname not in self.models and (allowed_modules is None or model.taskname in allowed_modules):
                print('find model:', onnx_file, model.taskname, model.input_shape, model.input_mean, model.input_std)
                self.models[model.taskname] = model
            else:
                print('duplicated model task type, ignore:', onnx_file, model.taskname)
                del model
            
        # Ensure detection is available (YOLO)
        assert 'detection' in self.models
        self.det_model = self.yolo_model
    
    def load_yolo_model(self, model_path):
        """Load YOLO model from local path"""
        try:
            # Resolve relative paths properly
            if not os.path.isabs(model_path):
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                yolo_models_dir = os.path.join(project_root, "yolo_models")
                
                # Try different model paths
                possible_paths = [
                    os.path.join(yolo_models_dir, model_path),  # yolo_models/model.pt
                    os.path.join(project_root, model_path),     # root/model.pt
                    model_path,                                 # as provided
                    os.path.join(os.getcwd(), model_path)       # current_dir/model.pt
                ]
                
                model_found = False
                for path in possible_paths:
                    if os.path.exists(path):
                        model_path = path
                        model_found = True
                        print(f"Found YOLO model at: {model_path}")
                        break
                
                if not model_found:
                    print(f"Model path not found: {model_path}")
                    print(f"Searched in: {possible_paths}")
                    raise FileNotFoundError(f"YOLO model not found: {model_path}")
            
            elif not os.path.exists(model_path):
                print(f"Absolute model path not found: {model_path}")
                raise FileNotFoundError(f"YOLO model not found: {model_path}")
            
            # Load YOLO model using ultralytics
            from ultralytics import YOLO
            model = YOLO(model_path)
            model.conf = 0.25  # Lower default confidence threshold for more detections
            model.iou = 0.5    # IoU threshold for Non-Maximum Suppression
            print(f"YOLO model loaded from: {model_path}")
            return model
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise

    def prepare(self, ctx_id, det_thresh=0.25, det_size=(640, 640)):
        self.det_thresh = det_thresh
        assert det_size is not None
        print('set det-size:', det_size)
        print(f'set detection threshold: {det_thresh}')
        self.det_size = det_size
        
        # Always configure YOLO model (since we're only using YOLO for detection)
        self.yolo_model.conf = det_thresh  # Set confidence threshold to the provided det_thresh
        if torch.cuda.is_available() and ctx_id >= 0:
            self.yolo_model.to(f'cuda:{ctx_id}')
            print(f"YOLO model moved to GPU: cuda:{ctx_id}")
        else:
            self.yolo_model.to('cpu')
            print("YOLO model using CPU")
        
        print(f"YOLO confidence threshold set to: {self.yolo_model.conf}")
        
        # Prepare other InsightFace models (recognition, gender/age, etc.)
        for taskname, model in self.models.items():
            if taskname == 'detection' or model == 'yolo':
                continue  # Skip detection since we use YOLO
            print(f"Preparing {taskname} model...")
            model.prepare(ctx_id)

    def get(self, img, max_num=0, det_metric='default'):
        # Always use YOLO model for detection
        print("Using YOLO for detection")
        
        # Run YOLO inference with explicit confidence threshold
        results = self.yolo_model(img, conf=self.det_thresh, verbose=False)
        
        # Process YOLO results
        ret = []
        
        # Get detections from YOLO results
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
                
            # Limit to max_num if specified and positive
            num_detections = len(boxes)
            if max_num > 0 and num_detections > max_num:
                # Sort by confidence and take top max_num
                confidences = boxes.conf.cpu().numpy()
                top_indices = np.argsort(confidences)[::-1][:max_num]
                boxes = [boxes[i] for i in top_indices]
            
            for box in boxes:
                # Extract bounding box in XYXY format
                bbox = box.xyxy.cpu().numpy()[0]  # [x1, y1, x2, y2]
                det_score = float(box.conf.cpu().numpy()[0])
                
                # YOLO doesn't provide keypoints by default, so set to None
                kps = None
                
                # Create Face object
                face = Face(bbox=bbox, kps=kps, det_score=det_score)
                
                # Process with other InsightFace models if available (recognition, gender/age, etc.)
                for taskname, model in self.models.items():
                    if taskname == 'detection' or model == 'yolo':
                        continue
                    try:
                        model.get(img, face)
                    except Exception as e:
                        print(f"Warning: Error processing {taskname}: {e}")
                
                ret.append(face)
        
        print(f"YOLO detected {len(ret)} faces with confidence >= {self.det_thresh}")
        return ret

    def draw_on(self, img, faces):
        import cv2
        dimg = img.copy()
        for i in range(len(faces)):
            face = faces[i]
            # Fix: Use np.int32 instead of deprecated np.int
            box = face.bbox.astype(np.int32)
            
            # Use blue color (BGR) for YOLO detections
            color = (255, 0, 0)
            
            # Draw rectangle around face
            cv2.rectangle(dimg, (box[0], box[1]), (box[2], box[3]), color, 2)
            
            # Draw confidence score
            score_text = f"{face.det_score:.2f}"
            cv2.putText(dimg, score_text, (box[0], box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw keypoints if available (usually not available with YOLO)
            if face.kps is not None:
                kps = face.kps.astype(np.int32)
                for l in range(kps.shape[0]):
                    kp_color = (0, 0, 255)
                    if l == 0 or l == 3:
                        kp_color = (0, 255, 0)
                    cv2.circle(dimg, (kps[l][0], kps[l][1]), 1, kp_color, 2)
            
            # Draw gender and age if available
            if hasattr(face, 'gender') and hasattr(face, 'age') and face.gender is not None and face.age is not None:
                gender_text = "M" if face.gender == 1 else "F"
                cv2.putText(dimg, f'{gender_text},{face.age}', (box[0]-1, box[1]-4), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0,255,0), 1)
            
        return dimg
