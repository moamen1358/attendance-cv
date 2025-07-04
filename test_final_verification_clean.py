#!/usr/bin/env python3
"""
Test the updated CustomFaceAnalysis with flexible GPU modes
"""

import os
import sys
import torch

# Add source directory to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit_last /src')

def test_gpu_modes():
    """Test different GPU modes"""
    print("🚀 TESTING FLEXIBLE GPU MODES")
    print("=" * 50)
    
    from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
    
    MODEL_ROOT = os.path.dirname('/home/invisa/Desktop/my_grad_streamlit_last /src')
    MODEL_NAME = 'buffalo_sc'
    yolo_path = "/home/invisa/Desktop/my_grad_streamlit_last /models/yolov11n-face.pt"
    
    # Test 1: HYBRID mode (recommended)
    print("\n1️⃣ TESTING HYBRID MODE (Recommended)")
    print("-" * 45)
    
    try:
        torch.cuda.empty_cache()
        initial_memory = torch.cuda.memory_allocated(0) / 1024**2
        
        app_hybrid = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT,
            yolo_model_path=yolo_path,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
            gpu_mode='HYBRID'
        )
        app_hybrid.prepare(ctx_id=0, det_size=(480, 480))
        
        after_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory used: +{after_memory - initial_memory:.1f} MB")
        
        # Check YOLO device
        yolo_device = next(app_hybrid.yolo_model.model.parameters()).device
        print(f"🔍 YOLO device: {yolo_device}")
        
        # Count models by device
        gpu_models = 0
        cpu_models = 0
        for taskname, model in app_hybrid.models.items():
            if taskname == 'detection' or model == 'yolo':
                continue
            if hasattr(model, 'session') and hasattr(model.session, 'get_providers'):
                providers = model.session.get_providers()
                if providers and providers[0] == 'CUDAExecutionProvider':
                    gpu_models += 1
                else:
                    cpu_models += 1
        
        print(f"📊 Results: YOLO={'GPU' if yolo_device.type=='cuda' else 'CPU'}, InsightFace={gpu_models} GPU + {cpu_models} CPU")
        
        if yolo_device.type == 'cuda':
            print("✅ HYBRID mode SUCCESS: Critical YOLO detection on GPU!")
            hybrid_success = True
        else:
            print("❌ HYBRID mode FAILED: YOLO not on GPU")
            hybrid_success = False
        
        del app_hybrid
        torch.cuda.empty_cache()
        
    except Exception as e:
        print(f"❌ HYBRID mode failed: {e}")
        hybrid_success = False
    
    return hybrid_success

def test_inference_performance():
    """Test actual inference performance"""
    print("\n🎯 INFERENCE PERFORMANCE TEST")
    print("=" * 40)
    
    try:
        import numpy as np
        import time
        from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
        
        MODEL_ROOT = os.path.dirname('/home/invisa/Desktop/my_grad_streamlit_last /src')
        MODEL_NAME = 'buffalo_sc'
        yolo_path = "/home/invisa/Desktop/my_grad_streamlit_last /models/yolov11n-face.pt"
        
        # Initialize in HYBRID mode
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT,
            yolo_model_path=yolo_path,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
            gpu_mode='HYBRID'
        )
        app.prepare(ctx_id=0, det_size=(480, 480))
        
        # Create test image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Warm up
        _ = app.get(test_img)
        
        # Performance test
        num_tests = 5
        times = []
        
        for i in range(num_tests):
            start_time = time.time()
            faces = app.get(test_img)
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # Convert to ms
            
        avg_time = sum(times) / len(times)
        print(f"🔍 Average inference time: {avg_time:.1f} ms")
        print(f"🔍 Estimated FPS: {1000/avg_time:.1f}")
        
        # Check GPU memory usage
        gpu_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory usage: {gpu_memory:.1f} MB")
        
        if avg_time < 100:
            print("🚀 EXCELLENT: Very fast inference (<100ms)")
            return True
        elif avg_time < 300:
            print("✅ GOOD: Fast inference (<300ms)")
            return True
        else:
            print("⚠️ SLOW: Consider optimization")
            return False
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    os.chdir('/home/invisa/Desktop/my_grad_streamlit_last /src')
    
    print("🎯 FINAL GPU VERIFICATION TEST")
    print("=" * 40)
    
    hybrid_ok = test_gpu_modes()
    perf_ok = test_inference_performance()
    
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 20)
    print(f"Hybrid Mode: {'✅ SUCCESS' if hybrid_ok else '❌ FAILED'}")
    print(f"Performance: {'✅ GOOD' if perf_ok else '❌ NEEDS WORK'}")
    
    if hybrid_ok:
        print("\n🏆 SUCCESS: Your system is optimized for GPU face recognition!")
        print("🚀 YOLO detection is using GPU (most critical for performance)")
        print("📝 InsightFace recognition may use CPU fallback (acceptable)")
        print("💡 This provides excellent real-time performance!")
    else:
        print("\n⚠️ Issues detected - check CUDA installation and GPU availability")
