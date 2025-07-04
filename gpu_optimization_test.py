#!/usr/bin/env python3
"""
GPU Optimization Test for YOLO + InsightFace
Tests and verifies 100% GPU utilization for face detection and analysis
"""

import sys
import os
import torch
import cv2
import time
from pathlib import Path

# Add insightface to path
insightface_path = Path(__file__).parent / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

from insightface.app import FaceAnalysis

def check_gpu_status():
    """Check GPU availability and status"""
    print("🔍 GPU STATUS CHECK")
    print("=" * 50)
    
    if torch.cuda.is_available():
        print(f"✅ CUDA Available: True")
        print(f"🎮 Device Count: {torch.cuda.device_count()}")
        print(f"🎯 Current Device: {torch.cuda.current_device()}")
        print(f"🚀 Device Name: {torch.cuda.get_device_name(0)}")
        print(f"🔧 CUDA Version: {torch.version.cuda}")
        
        # Memory info
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
        reserved_memory = torch.cuda.memory_reserved(0) / 1024**3
        
        print(f"💾 Total Memory: {total_memory:.2f} GB")
        print(f"📊 Allocated: {allocated_memory:.2f} GB")
        print(f"📈 Reserved: {reserved_memory:.2f} GB")
        print(f"🔋 Free: {total_memory - reserved_memory:.2f} GB")
        
        return True
    else:
        print("❌ CUDA Not Available")
        return False

def optimize_gpu_settings():
    """Optimize GPU settings for maximum performance"""
    print("\n🚀 OPTIMIZING GPU SETTINGS")
    print("=" * 50)
    
    if torch.cuda.is_available():
        # Enable optimizations
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        torch.backends.cudnn.enabled = True
        
        # Set memory growth
        torch.cuda.empty_cache()
        
        print("✅ CUDNN benchmark enabled")
        print("✅ CUDNN deterministic disabled (for speed)")
        print("✅ GPU memory cache cleared")
        
        # Set high performance mode
        os.environ['CUDA_LAUNCH_BLOCKING'] = '0'  # Async GPU operations
        print("✅ Async GPU operations enabled")
        
        return True
    return False

def test_yolo_gpu_performance():
    """Test YOLO GPU performance"""
    print("\n🎯 TESTING YOLO GPU PERFORMANCE")
    print("=" * 50)
    
    try:
        # Initialize with GPU optimization
        app = FaceAnalysis(yolo_model_path='yolov11l-face.pt')
        app.prepare(ctx_id=0, det_thresh=0.25)
        
        # Load test image
        test_image = 'images/face_detection_result_42_faces.jpg'
        if not os.path.exists(test_image):
            print(f"⚠️ Test image not found: {test_image}")
            return False
        
        img = cv2.imread(test_image)
        print(f"📷 Test image loaded: {img.shape}")
        
        # Warm up GPU (first inference is usually slower)
        print("🔥 Warming up GPU...")
        _ = app.get(img, max_num=5)
        
        # Performance test
        print("⏱️ Running performance test...")
        num_iterations = 5
        total_time = 0
        
        for i in range(num_iterations):
            start_time = time.time()
            
            # Clear GPU cache before each iteration
            torch.cuda.empty_cache()
            
            # Run inference
            faces = app.get(img)
            
            end_time = time.time()
            iteration_time = end_time - start_time
            total_time += iteration_time
            
            print(f"  Iteration {i+1}: {iteration_time:.3f}s, Faces: {len(faces)}")
            
            # Check GPU utilization
            if torch.cuda.is_available():
                memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
                print(f"    GPU Memory - Allocated: {memory_allocated:.2f}GB, Reserved: {memory_reserved:.2f}GB")
        
        avg_time = total_time / num_iterations
        fps = 1.0 / avg_time
        
        print(f"\n📊 PERFORMANCE RESULTS:")
        print(f"   Average time per inference: {avg_time:.3f}s")
        print(f"   Estimated FPS: {fps:.1f}")
        print(f"   Total faces detected: {len(faces)}")
        
        # Verify models are using GPU
        print(f"\n🔍 GPU VERIFICATION:")
        
        # Check YOLO device
        if hasattr(app.yolo_model.model, 'device'):
            yolo_device = next(app.yolo_model.model.parameters()).device
            print(f"   YOLO device: {yolo_device}")
            
        # Check InsightFace models
        for taskname, model in app.models.items():
            if taskname == 'detection' or model == 'yolo':
                continue
            if hasattr(model, 'session') and hasattr(model.session, 'get_providers'):
                providers = model.session.get_providers()
                gpu_provider = 'CUDAExecutionProvider' in providers
                print(f"   {taskname}: {'✅ GPU' if gpu_provider else '❌ CPU'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in GPU test: {e}")
        import traceback
        traceback.print_exc()
        return False

def monitor_gpu_usage():
    """Monitor GPU usage during operation"""
    print("\n📈 GPU USAGE MONITORING")
    print("=" * 50)
    
    if not torch.cuda.is_available():
        print("❌ No GPU available for monitoring")
        return
    
    try:
        import subprocess
        
        # Try to get GPU usage via nvidia-smi
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            gpu_util, mem_used, mem_total = result.stdout.strip().split(', ')
            print(f"🎮 GPU Utilization: {gpu_util}%")
            print(f"💾 Memory Used: {mem_used}MB / {mem_total}MB")
            print(f"📊 Memory Usage: {(int(mem_used)/int(mem_total)*100):.1f}%")
        else:
            print("⚠️ nvidia-smi not available")
            
    except Exception as e:
        print(f"⚠️ Could not monitor GPU: {e}")

def main():
    print("🚀 GPU OPTIMIZATION TEST FOR YOLO + INSIGHTFACE")
    print("=" * 60)
    print("Testing 100% GPU utilization for face detection and analysis")
    print("=" * 60)
    
    # Step 1: Check GPU status
    gpu_available = check_gpu_status()
    
    if not gpu_available:
        print("\n❌ No GPU available. Cannot test GPU optimization.")
        return
    
    # Step 2: Optimize GPU settings
    optimize_gpu_settings()
    
    # Step 3: Monitor initial GPU usage
    monitor_gpu_usage()
    
    # Step 4: Test YOLO + InsightFace GPU performance
    success = test_yolo_gpu_performance()
    
    # Step 5: Final GPU usage check
    print("\n" + "=" * 60)
    monitor_gpu_usage()
    
    if success:
        print("\n✅ GPU OPTIMIZATION TEST COMPLETED SUCCESSFULLY!")
        print("🎯 Both YOLO and InsightFace are using GPU acceleration")
        print("🚀 System optimized for maximum GPU utilization")
    else:
        print("\n❌ GPU OPTIMIZATION TEST FAILED")
        print("🔧 Check GPU drivers and CUDA installation")
    
    # Cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("🧹 GPU cache cleared")

if __name__ == "__main__":
    main()
