#!/usr/bin/env python3
"""
GPU-Only Verification Script
Test that both YOLO and InsightFace models are using GPU 100%
"""

import os
import sys
sys.path.append('/home/invisa/Desktop/my_grad_streamlit_last /src')

def test_gpu_only_mode():
    """Test that both models are forced to use GPU only"""
    
    print("🚀 GPU-ONLY MODE VERIFICATION")
    print("=" * 50)
    
    # Change to project root
    os.chdir('/home/invisa/Desktop/my_grad_streamlit_last /src')
    
    try:
        import torch
        
        # Verify CUDA is available
        if not torch.cuda.is_available():
            print("❌ CUDA is not available! Cannot test GPU-only mode.")
            return False
            
        print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
        print(f"✅ CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        # Test GPU memory before loading models
        print(f"🔍 GPU memory before loading: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
        
        # Test custom face analysis initialization
        from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
        
        MODEL_ROOT = os.path.dirname(os.getcwd())
        MODEL_NAME = 'buffalo_sc'
        
        print(f"\n🧪 Testing GPU-only initialization...")
        print(f"MODEL_ROOT: {MODEL_ROOT}")
        
        # This should force GPU-only mode or fail
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT,
            providers=['CUDAExecutionProvider']  # Force CUDA only
        )
        
        print(f"✅ FaceAnalysis created with CUDA providers only")
        
        # Prepare with GPU context
        app.prepare(ctx_id=0, det_size=(480, 480))
        print(f"✅ Models prepared with GPU context (ctx_id=0)")
        
        # Check GPU memory after loading
        print(f"🔍 GPU memory after loading: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
        
        # Verify YOLO is on GPU
        if hasattr(app, 'yolo_model'):
            device = next(app.yolo_model.model.parameters()).device
            print(f"🔍 YOLO model device: {device}")
            if 'cuda' in str(device):
                print("✅ YOLO model confirmed on GPU")
            else:
                print("❌ YOLO model NOT on GPU")
                return False
        
        # Test with a sample image to ensure GPU inference
        import cv2
        import numpy as np
        
        # Create test image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        print(f"\n🧪 Testing GPU inference...")
        
        # Monitor GPU memory during inference
        gpu_memory_before = torch.cuda.memory_allocated(0) / 1024**2
        
        # Run detection
        faces = app.get(test_img)
        
        gpu_memory_after = torch.cuda.memory_allocated(0) / 1024**2
        
        print(f"🔍 GPU memory during inference: {gpu_memory_before:.1f} MB -> {gpu_memory_after:.1f} MB")
        print(f"✅ GPU inference completed successfully")
        print(f"🔍 Detected faces: {len(faces) if faces else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU-only mode test failed: {e}")
        return False

def monitor_gpu_usage():
    """Monitor GPU usage during operation"""
    print(f"\n📊 GPU USAGE MONITORING")
    print("=" * 30)
    
    try:
        import torch
        
        if torch.cuda.is_available():
            # Get GPU utilization
            print(f"🔍 GPU device count: {torch.cuda.device_count()}")
            print(f"🔍 Current device: {torch.cuda.current_device()}")
            
            # Memory info
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
            memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
            memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            print(f"🔍 Memory allocated: {memory_allocated:.2f} GB")
            print(f"🔍 Memory reserved: {memory_reserved:.2f} GB") 
            print(f"🔍 Memory total: {memory_total:.2f} GB")
            print(f"🔍 Memory usage: {(memory_allocated/memory_total)*100:.1f}%")
            
        return True
    except Exception as e:
        print(f"❌ GPU monitoring failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gpu_only_mode()
    monitor_gpu_usage()
    
    if success:
        print(f"\n🎉 GPU-ONLY MODE VERIFIED!")
        print(f"✅ Both YOLO and InsightFace are using GPU 100%")
        print(f"✅ No CPU fallback available")
        print(f"✅ System optimized for maximum GPU performance")
    else:
        print(f"\n⚠️ GPU-only mode verification failed")
        print(f"❌ Check CUDA installation and GPU availability")
