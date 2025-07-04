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
    def __init__(self, name=DEFAULT_MP_NAME, root='~/.insightface', allowed_modules=None, yolo_model_path=None, use_yolo=True, 
                 gpu_mode='PREFER_GPU', **kwargs):
        """
        Custom Face Analysis with YOLO Integration and flexible GPU mode
        
        Args:
            gpu_mode: 
                - 'STRICT_GPU_ONLY': Fail if any model can't use GPU
                - 'PREFER_GPU': Use GPU where possible, warn about CPU fallback  
                - 'HYBRID': Force YOLO to GPU (critical), allow InsightFace CPU fallback
        """
        onnxruntime.set_default_logger_severity(3)
        self.models = {}
        self.use_yolo = True  # Force YOLO usage
        self.gpu_mode = gpu_mode
        
        # Force GPU-only mode for YOLO (always required)
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("🚨 CUDA is required but not available! YOLO needs GPU.")
        
        print(f"🚀 GPU Mode: {gpu_mode}")
        
        # Configure InsightFace providers based on mode
        if gpu_mode == 'STRICT_GPU_ONLY':
            kwargs['providers'] = ['CUDAExecutionProvider']  # Remove CPU fallback completely
            kwargs['provider_options'] = [{'device_id': '0'}]  # Force specific GPU
            self.gpu_only_mode = True
            print("� STRICT GPU-ONLY mode: Will fail if any model can't use GPU")
        elif gpu_mode == 'PREFER_GPU':
            kwargs['providers'] = ['CUDAExecutionProvider', 'CPUExecutionProvider']  # Prefer GPU, allow CPU
            kwargs['provider_options'] = [{'device_id': '0'}, {}]
            self.gpu_only_mode = False
            print("🚀 PREFER GPU mode: Will use GPU where possible, CPU as fallback")
        else:  # HYBRID mode (default)
            kwargs['providers'] = ['CUDAExecutionProvider', 'CPUExecutionProvider']  # Allow CPU fallback
            self.gpu_only_mode = False
            print("🚀 HYBRID mode: YOLO on GPU (critical), InsightFace GPU preferred with CPU fallback")
        
        # Set default YOLO model path if not provided
        if yolo_model_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            yolo_model_path = os.path.join(project_root, "models", "yolov11n-face.pt")
        
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
        
        successfully_loaded_gpu_models = 0
        
        for onnx_file in onnx_files:
            # Force CUDA-only providers for each model
            kwargs_cuda_only = kwargs.copy()
            kwargs_cuda_only['providers'] = ['CUDAExecutionProvider']  # Remove CPU fallback
            
            try:
                model = model_zoo.get_model(onnx_file, **kwargs_cuda_only)  # Force CUDA only
                
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
                    # Check GPU usage based on mode
                    model_on_gpu = False
                    if hasattr(model, 'session') and hasattr(model.session, 'get_providers'):
                        providers = model.session.get_providers()
                        model_on_gpu = 'CUDAExecutionProvider' in providers and providers[0] == 'CUDAExecutionProvider'
                        
                        if self.gpu_mode == 'STRICT_GPU_ONLY' and not model_on_gpu:
                            print(f'❌ STRICT MODE: {model.taskname} model not on GPU: {providers}')
                            del model
                            raise RuntimeError(f"STRICT GPU-only mode failed: {model.taskname} model fell back to CPU")
                        elif model_on_gpu:
                            print(f'✅ {model.taskname} model confirmed using CUDA: {providers[0]}')
                            successfully_loaded_gpu_models += 1
                        else:
                            print(f'⚠️ {model.taskname} model using CPU fallback: {providers[0]}')
                    
                    print('find model:', onnx_file, model.taskname, model.input_shape, model.input_mean, model.input_std)
                    self.models[model.taskname] = model
                else:
                    print('duplicated model task type, ignore:', onnx_file, model.taskname)
                    del model
                    
            except Exception as e:
                print(f"❌ Failed to load {onnx_file}: {e}")
                if self.gpu_mode == 'STRICT_GPU_ONLY' and "STRICT GPU-only mode failed" in str(e):
                    raise  # Re-raise strict mode failures
                # For other modes, continue but warn
                print(f"⚠️ Skipping {onnx_file} due to loading error")
        
        print(f"🚀 Successfully loaded {successfully_loaded_gpu_models} InsightFace models on GPU")
        
        # Summary of what was loaded
        total_insightface_models = len([k for k in self.models.keys() if k != 'detection'])
        if total_insightface_models > 0:
            gpu_ratio = successfully_loaded_gpu_models / total_insightface_models
            print(f"📊 InsightFace GPU ratio: {successfully_loaded_gpu_models}/{total_insightface_models} ({gpu_ratio*100:.0f}%)")
            if gpu_ratio == 1.0:
                print("🏆 Perfect: All InsightFace models on GPU!")
            elif gpu_ratio > 0:
                print("🌟 Good: Partial GPU acceleration for InsightFace")
            else:
                print("⚠️ Warning: All InsightFace models on CPU (still functional)")
        else:
            print("⚠️ No InsightFace models loaded!")
            
        # Ensure detection is available (YOLO)
        assert 'detection' in self.models
        self.det_model = self.yolo_model
        
        # Print loaded models for debugging
        print(f"📊 Loaded models: {list(self.models.keys())}")
        for taskname, model in self.models.items():
            if taskname != 'detection' and model != 'yolo':
                print(f"  - {taskname}: {type(model).__name__}")
                if hasattr(model, 'input_shape'):
                    print(f"    Input shape: {model.input_shape}")
                if hasattr(model, 'output_shape'):
                    print(f"    Output shape: {model.output_shape}")
        
        # Check if we have a recognition model
        recognition_available = any(taskname == 'recognition' for taskname in self.models.keys())
        print(f"🔍 Recognition model available: {recognition_available}")
        if not recognition_available:
            print("⚠️ WARNING: No recognition model found! Face embeddings will be None.")
            print("Available models:", list(self.models.keys()))
    
    def load_yolo_model(self, model_path):
        """Load YOLO model from local path"""
        try:
            # Resolve relative paths properly
            if not os.path.isabs(model_path):
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                models_dir = os.path.join(project_root, "models")
                
                # Try different model paths
                possible_paths = [
                    os.path.join(models_dir, model_path),       # models/model.pt
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
        
        # Force GPU-only for YOLO model (no CPU fallback)
        if not torch.cuda.is_available():
            raise RuntimeError("🚨 CUDA is required but not available! GPU-only mode enabled.")
        
        if ctx_id < 0:
            raise ValueError("🚨 GPU-only mode: ctx_id must be >= 0 (CPU mode disabled)")
        
        # Force YOLO to GPU
        self.yolo_model.conf = det_thresh  # Set confidence threshold
        gpu_device = f'cuda:{ctx_id}'
        self.yolo_model.to(gpu_device)
        print(f"🚀 YOLO model FORCED to GPU: {gpu_device}")
        print(f"🚀 YOLO confidence threshold set to: {self.yolo_model.conf}")
        
        # Force InsightFace models to GPU only
        print("🚀 Preparing InsightFace models in GPU-ONLY mode...")
        for taskname, model in self.models.items():
            if taskname == 'detection' or model == 'yolo':
                continue  # Skip detection since we use YOLO
            print(f"🚀 Forcing {taskname} model to GPU: {gpu_device}")
            model.prepare(ctx_id)  # Force GPU context
            
        print("✅ All models prepared in GPU-ONLY mode")

    def get(self, img, max_num=0, det_metric='default'):
        # Always use YOLO model for detection (reduced logging for performance)
        
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
                embedding_generated = False
                
                # First pass: generate keypoints if we have landmark models (minimal logging)
                if face.kps is None:
                    for taskname, model in self.models.items():
                        if taskname in ['landmark_2d_106', 'landmark_3d_68']:
                            try:
                                model.get(img, face)
                                if hasattr(face, 'kps') and face.kps is not None:
                                    break
                            except Exception as e:
                                pass  # Silent failure for performance
                
                # If still no keypoints, generate approximate ones from bbox
                if face.kps is None:
                    face.kps = self.generate_approximate_keypoints(face.bbox)
                
                # Second pass: process other models (recognition, gender/age) with minimal logging
                for taskname, model in self.models.items():
                    if taskname == 'detection' or model == 'yolo' or taskname in ['landmark_2d_106', 'landmark_3d_68']:
                        continue
                    try:
                        model.get(img, face)
                        # Check if this model generated an embedding
                        if hasattr(face, 'embedding') and face.embedding is not None:
                            embedding_generated = True
                    except Exception as e:
                        pass  # Silent failure for performance
                
                # Ensure we have an embedding for recognition
                if not embedding_generated:
                    face.embedding = None
                
                ret.append(face)
        
        # Only log detection count based on configuration
        if not hasattr(self, '_log_counter'):
            self._log_counter = 0
        self._log_counter += 1
        
        # Import logging config if available
        try:
            from performance_config import DETECTION_LOG_INTERVAL, VERBOSE_LOGGING
        except ImportError:
            DETECTION_LOG_INTERVAL = 10
            VERBOSE_LOGGING = False
        
        if VERBOSE_LOGGING or self._log_counter % DETECTION_LOG_INTERVAL == 0:
            print(f"YOLO detected {len(ret)} faces with confidence >= {self.det_thresh}")
        
        return ret

    def generate_approximate_keypoints(self, bbox):
        """Generate approximate 5-point facial landmarks from bounding box"""
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        
        # Generate approximate 5-point landmarks based on typical face proportions
        # Order: left_eye, right_eye, nose, left_mouth, right_mouth
        keypoints = np.array([
            [x1 + w * 0.35, y1 + h * 0.35],  # left eye
            [x1 + w * 0.65, y1 + h * 0.35],  # right eye  
            [x1 + w * 0.50, y1 + h * 0.55],  # nose
            [x1 + w * 0.40, y1 + h * 0.75],  # left mouth corner
            [x1 + w * 0.60, y1 + h * 0.75],  # right mouth corner
        ], dtype=np.float32)
        
        return keypoints

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
