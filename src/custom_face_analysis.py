# Custom Face Analysis with YOLO Integration
import sys
import os
from pathlib import Path
import numpy as np
import torch
from ultralytics import YOLO
import cv2

# Add insightface to path
insightface_path = Path(__file__).parent.parent / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

from insightface.app.common import Face
from insightface.model_zoo import model_zoo
from insightface.utils import DEFAULT_MP_NAME, ensure_available
import glob
import os.path as osp
import onnxruntime


class CustomFaceAnalysis:
    def __init__(self, name=DEFAULT_MP_NAME, root='~/.insightface', yolo_model_path='yolov11l-face.pt', **kwargs):
        onnxruntime.set_default_logger_severity(3)
        self.models = {}
        
        # Load YOLO model for detection (required)
        try:
            print(f"🎯 Loading YOLO model from: {yolo_model_path}")
            self.yolo_model = self._load_yolo_model(yolo_model_path)
            print("✅ YOLO model loaded successfully for face detection")
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
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
                print(f'⏭️ Skipping detection model (using YOLO): {onnx_file}')
                del model
            elif model.taskname not in self.models:
                print(f'✅ Found model: {onnx_file} {model.taskname} {model.input_shape}')
                self.models[model.taskname] = model
            else:
                print(f'⚠️ Duplicated model task type, ignoring: {onnx_file} {model.taskname}')
                del model
        
        print(f"🎯 Using YOLO for detection, InsightFace for: {list(self.models.keys())}")
    
    def _load_yolo_model(self, model_path):
        """Load YOLO model from local path"""
        if not os.path.exists(model_path):
            print(f"❌ Model path not found: {model_path}")
            # Try to find it in the parent directory (where it actually is)
            parent_dir = Path(__file__).parent.parent
            new_path = parent_dir / model_path
            if new_path.exists():
                model_path = str(new_path)
                print(f"✅ Found model at: {model_path}")
            else:
                # Try with the space in directory name
                new_path = Path('/home/invisa/Desktop/my_grad_streamlit_last ') / 'yolov11l-face.pt'
                if new_path.exists():
                    model_path = str(new_path)
                    print(f"✅ Found model at: {model_path}")
                else:
                    raise FileNotFoundError(f"YOLO model not found: {model_path}")
        
        # Load YOLO model using ultralytics
        model = YOLO(model_path)
        model.conf = 0.25  # Default confidence threshold
        model.iou = 0.5    # IoU threshold for Non-Maximum Suppression
        print(f"✅ YOLO model loaded from: {model_path}")
        return model

    def prepare(self, ctx_id, det_thresh=0.25, det_size=(640, 640)):
        self.det_thresh = det_thresh
        self.det_size = det_size
        
        print(f'🔧 Setting detection size: {det_size}')
        print(f'🔧 Setting detection threshold: {det_thresh}')
        
        # Configure YOLO model
        self.yolo_model.conf = det_thresh
        
        # Move YOLO to GPU if available
        if torch.cuda.is_available() and ctx_id >= 0:
            try:
                device = f'cuda:{ctx_id}' if ctx_id >= 0 else 'cuda'
                self.yolo_model.to(device)
                print(f"🚀 YOLO model moved to GPU: {device}")
            except Exception as e:
                print(f"⚠️ Failed to move YOLO to GPU: {e}")
                self.yolo_model.to('cpu')
                print("🔄 YOLO using CPU fallback")
        else:
            self.yolo_model.to('cpu')
            print("🔧 YOLO using CPU")
        
        # Prepare other InsightFace models (recognition, gender/age, etc.)
        for taskname, model in self.models.items():
            try:
                print(f"🔧 Preparing {taskname} model...")
                model.prepare(ctx_id)
                print(f"✅ {taskname} model prepared")
            except Exception as e:
                print(f"⚠️ Failed to prepare {taskname} model: {e}")

    def get(self, img, max_num=0, det_metric='default'):
        """Get faces from image using YOLO detection + InsightFace recognition"""
        print(f"🎯 Using YOLO for detection (confidence >= {self.det_thresh})")
        
        # Run YOLO inference
        results = self.yolo_model(img, conf=self.det_thresh, verbose=False)
        
        # Process YOLO results
        ret = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue
                
            # Limit to max_num if specified and positive
            if max_num > 0 and len(boxes) > max_num:
                # Sort by confidence and take top max_num
                confidences = boxes.conf.cpu().numpy()
                top_indices = np.argsort(confidences)[::-1][:max_num]
                boxes = [boxes[i] for i in top_indices]
            
            for box in boxes:
                # Extract bounding box in XYXY format
                bbox = box.xyxy.cpu().numpy()[0]  # [x1, y1, x2, y2]
                det_score = float(box.conf.cpu().numpy()[0])
                
                # Create Face object
                face = Face(bbox=bbox, kps=None, det_score=det_score)
                
                # Process with other InsightFace models if available (recognition, gender/age, etc.)
                for taskname, model in self.models.items():
                    try:
                        model.get(img, face)
                    except Exception as e:
                        print(f"⚠️ Warning: Error processing {taskname}: {e}")
                
                ret.append(face)
        
        print(f"✅ YOLO detected {len(ret)} faces with confidence >= {self.det_thresh}")
        return ret

    def draw_on(self, img, faces):
        """Draw detection results on image"""
        import cv2
        dimg = img.copy()
        for i, face in enumerate(faces):
            box = face.bbox.astype(np.int32)
            color = (0, 255, 0)  # Green for YOLO detections
            
            # Draw rectangle
            cv2.rectangle(dimg, (box[0], box[1]), (box[2], box[3]), color, 2)
            
            # Draw confidence score
            score_text = f"{face.det_score:.2f}"
            cv2.putText(dimg, score_text, (box[0], box[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw other attributes if available
            if hasattr(face, 'gender') and hasattr(face, 'age') and face.gender is not None:
                gender_text = "M" if face.gender == 1 else "F"
                age_text = f'{gender_text},{int(face.age)}'
                cv2.putText(dimg, age_text, (box[0], box[1]-30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        return dimg
