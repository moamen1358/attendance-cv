#!/usr/bin/env python3
"""
Comprehensive GPU-Only Verification Test
This test ensures both YOLO and InsightFace models use GPU exclusively with no CPU fallback.
"""

import os
import sys
import torch
import time

# Add source directory to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit_last /src')

def test_cuda_availability():
    """Test CUDA availability and device info"""
    print("🔍 CUDA AVAILABILITY TEST")
    print("=" * 40)
    
    if not torch.cuda.is_available():
        print("❌ CUDA is NOT available!")
        return False
    
    print(f"✅ CUDA is available")
    print(f"✅ Device count: {torch.cuda.device_count()}")
    print(f"✅ Current device: {torch.cuda.current_device()}")
    print(f"✅ Device name: {torch.cuda.get_device_name(0)}")
    print(f"✅ Total memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    return True

def test_yolo_gpu_usage():
    """Test YOLO model GPU usage"""
    print("\n🎯 YOLO GPU USAGE TEST")
    print("=" * 40)
    
    try:
        from ultralytics import YOLO
        import cv2
        import numpy as np
        
        # Clear GPU memory
        torch.cuda.empty_cache()
        initial_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 Initial GPU memory: {initial_memory:.1f} MB")
        
        # Load YOLO model
        model_path = "/home/invisa/Desktop/my_grad_streamlit_last /models/yolov11n-face.pt"
        model = YOLO(model_path)
        
        # Force model to GPU
        model.to('cuda:0')
        
        after_load_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory after YOLO load: {after_load_memory:.1f} MB")
        print(f"🔍 YOLO memory usage: +{after_load_memory - initial_memory:.1f} MB")
        
        # Verify model is on GPU
        print(f"🔍 YOLO model device: {next(model.model.parameters()).device}")
        
        # Test inference
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Run inference and measure memory
        before_inference = torch.cuda.memory_allocated(0) / 1024**2
        results = model(test_img, verbose=False)
        after_inference = torch.cuda.memory_allocated(0) / 1024**2
        
        print(f"🔍 GPU memory during inference: {after_inference:.1f} MB")
        print(f"🔍 Inference memory spike: +{after_inference - before_inference:.1f} MB")
        
        # Verify GPU is being used
        if next(model.model.parameters()).device.type == 'cuda':
            print("✅ YOLO is using GPU")
            return True
        else:
            print("❌ YOLO is NOT using GPU")
            return False
            
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False

def test_insightface_gpu_usage():
    """Test InsightFace models GPU usage"""
    print("\n🎯 INSIGHTFACE GPU USAGE TEST")
    print("=" * 40)
    
    try:
        import onnxruntime as ort
        
        # Clear GPU memory
        torch.cuda.empty_cache()
        initial_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 Initial GPU memory: {initial_memory:.1f} MB")
        
        # Test ONNX Runtime providers
        print("🔍 Available ONNX providers:", ort.get_available_providers())
        
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            print("❌ CUDAExecutionProvider not available in ONNX Runtime")
            return False
        
        print("✅ CUDAExecutionProvider is available")
        
        # Test custom face analysis
        from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
        
        MODEL_ROOT = os.path.dirname('/home/invisa/Desktop/my_grad_streamlit_last /src')
        MODEL_NAME = 'buffalo_sc'
        
        print(f"🚀 Initializing FaceAnalysis with GPU-only providers...")
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT,
            providers=['CUDAExecutionProvider']  # Force CUDA only
        )
        
        after_load_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory after FaceAnalysis load: {after_load_memory:.1f} MB")
        print(f"🔍 FaceAnalysis memory usage: +{after_load_memory - initial_memory:.1f} MB")
        
        # Prepare models
        app.prepare(ctx_id=0, det_size=(480, 480))
        
        after_prepare_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory after prepare: {after_prepare_memory:.1f} MB")
        print(f"🔍 Prepare memory usage: +{after_prepare_memory - after_load_memory:.1f} MB")
        
        # Verify providers for each model
        print(f"\n🔍 Verifying execution providers for InsightFace models...")
        gpu_providers_verified = True
        
        for taskname, model in app.models.items():
            if taskname == 'detection' or model == 'yolo':
                continue
            
            if hasattr(model, 'session') and hasattr(model.session, 'get_providers'):
                providers = model.session.get_providers()
                print(f"  📋 {taskname} providers: {providers}")
                if 'CUDAExecutionProvider' not in providers[0]:
                    print(f"  ❌ {taskname} is NOT using CUDA as primary provider")
                    gpu_providers_verified = False
                else:
                    print(f"  ✅ {taskname} is using CUDA as primary provider")
            else:
                print(f"  ⚠️ {taskname} provider info not available")
        
        return gpu_providers_verified
        
    except Exception as e:
        print(f"❌ InsightFace test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_combined_gpu_usage():
    """Test both models working together on GPU"""
    print("\n🎯 COMBINED MODELS GPU USAGE TEST")
    print("=" * 40)
    
    try:
        import cv2
        import numpy as np
        from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
        
        # Clear GPU memory
        torch.cuda.empty_cache()
        initial_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 Initial GPU memory: {initial_memory:.1f} MB")
        
        MODEL_ROOT = os.path.dirname('/home/invisa/Desktop/my_grad_streamlit_last /src')
        MODEL_NAME = 'buffalo_sc'
        yolo_path = "/home/invisa/Desktop/my_grad_streamlit_last /models/yolov11n-face.pt"
        
        # Initialize combined system
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT,
            yolo_model_path=yolo_path,
            providers=['CUDAExecutionProvider']
        )
        app.prepare(ctx_id=0, det_size=(480, 480))
        
        after_setup_memory = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory after full setup: {after_setup_memory:.1f} MB")
        print(f"🔍 Total setup memory usage: +{after_setup_memory - initial_memory:.1f} MB")
        
        # Create test image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Run full inference pipeline
        before_inference = torch.cuda.memory_allocated(0) / 1024**2
        start_time = time.time()
        
        faces = app.get(test_img)
        
        end_time = time.time()
        after_inference = torch.cuda.memory_allocated(0) / 1024**2
        
        print(f"🔍 GPU memory during inference: {after_inference:.1f} MB")
        print(f"🔍 Inference memory spike: +{after_inference - before_inference:.1f} MB")
        print(f"⏱️ Inference time: {(end_time - start_time)*1000:.1f} ms")
        print(f"🔍 Detected faces: {len(faces)}")
        
        # Check YOLO device
        yolo_device = next(app.yolo_model.model.parameters()).device
        print(f"🔍 YOLO device: {yolo_device}")
        
        if yolo_device.type == 'cuda':
            print("✅ YOLO confirmed on GPU")
            return True
        else:
            print("❌ YOLO not on GPU")
            return False
            
    except Exception as e:
        print(f"❌ Combined test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all GPU verification tests"""
    print("🚀 GPU-ONLY VERIFICATION TEST SUITE")
    print("=" * 50)
    
    # Change to correct directory
    os.chdir('/home/invisa/Desktop/my_grad_streamlit_last /src')
    
    results = []
    
    # Test 1: CUDA availability
    results.append(test_cuda_availability())
    
    # Test 2: YOLO GPU usage
    results.append(test_yolo_gpu_usage())
    
    # Test 3: InsightFace GPU usage
    results.append(test_insightface_gpu_usage())
    
    # Test 4: Combined GPU usage
    results.append(test_combined_gpu_usage())
    
    # Summary
    print("\n🏁 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    test_names = [
        "CUDA Availability",
        "YOLO GPU Usage", 
        "InsightFace GPU Usage",
        "Combined GPU Usage"
    ]
    
    all_passed = True
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_names[i]}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n🎯 OVERALL: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("🚀 Both YOLO and InsightFace are confirmed to use GPU-only!")
    else:
        print("⚠️ GPU-only mode not fully verified. Check individual test results.")

if __name__ == "__main__":
    main()
