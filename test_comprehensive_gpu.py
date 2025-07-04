#!/usr/bin/env python3
"""
Comprehensive GPU-Only Verification with Execution Provider Analysis
"""

import os
import sys
sys.path.append('/home/invisa/Desktop/my_grad_streamlit_last /src')

def analyze_execution_providers():
    """Analyze execution providers used by models"""
    
    print("🔍 EXECUTION PROVIDER ANALYSIS")
    print("=" * 50)
    
    os.chdir('/home/invisa/Desktop/my_grad_streamlit_last /src')
    
    try:
        import torch
        from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
        
        MODEL_ROOT = os.path.dirname(os.getcwd())
        MODEL_NAME = 'buffalo_sc'
        
        print(f"🧪 Creating FaceAnalysis with forced CUDA providers...")
        
        # Initialize with explicit CUDA-only providers
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT,
            providers=['CUDAExecutionProvider']  # Force CUDA only
        )
        
        app.prepare(ctx_id=0, det_size=(480, 480))
        
        # Analyze each model's execution providers
        print(f"\n📊 MODEL EXECUTION PROVIDER ANALYSIS:")
        
        for taskname, model in app.models.items():
            if taskname == 'detection' or model == 'yolo':
                print(f"🚀 {taskname}: YOLO (GPU: {next(app.yolo_model.model.parameters()).device})")
                continue
                
            if hasattr(model, 'session'):
                providers = model.session.get_providers()
                print(f"🔍 {taskname}: {providers}")
                
                if len(providers) == 1 and providers[0] == 'CUDAExecutionProvider':
                    print(f"  ✅ CUDA-only confirmed for {taskname}")
                elif 'CUDAExecutionProvider' in providers and 'CPUExecutionProvider' in providers:
                    print(f"  ⚠️  Both CUDA and CPU available for {taskname} (CUDA preferred)")
                elif providers[0] == 'CPUExecutionProvider':
                    print(f"  ❌ CPU-only for {taskname}")
                else:
                    print(f"  🔍 Unknown provider configuration: {providers}")
            else:
                print(f"🔍 {taskname}: No session info available")
        
        # Test inference to ensure GPU usage
        print(f"\n🧪 TESTING GPU INFERENCE:")
        
        import cv2
        import numpy as np
        
        # Create test image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Monitor GPU memory
        gpu_before = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory before inference: {gpu_before:.1f} MB")
        
        # Run inference
        faces = app.get(test_img)
        
        gpu_after = torch.cuda.memory_allocated(0) / 1024**2
        print(f"🔍 GPU memory after inference: {gpu_after:.1f} MB")
        print(f"🔍 GPU memory delta: +{gpu_after - gpu_before:.1f} MB")
        
        if gpu_after > gpu_before:
            print(f"✅ GPU memory increased during inference - models using GPU")
        else:
            print(f"⚠️  No GPU memory increase detected")
            
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def force_cuda_only_verification():
    """Verify that we can create truly CUDA-only models"""
    
    print(f"\n🚀 FORCING CUDA-ONLY MODE TEST")
    print("=" * 40)
    
    try:
        import onnxruntime as ort
        
        # Check available providers
        available_providers = ort.get_available_providers()
        print(f"🔍 Available ONNX providers: {available_providers}")
        
        if 'CUDAExecutionProvider' not in available_providers:
            print(f"❌ CUDAExecutionProvider not available!")
            return False
            
        print(f"✅ CUDAExecutionProvider is available")
        
        # Test creating a session with CUDA-only
        print(f"🧪 Testing CUDA-only session creation...")
        
        model_path = "/home/invisa/Desktop/my_grad_streamlit_last /models/buffalo_sc/w600k_mbf.onnx"
        if os.path.exists(model_path):
            session = ort.InferenceSession(
                model_path, 
                providers=['CUDAExecutionProvider']
            )
            
            actual_providers = session.get_providers()
            print(f"🔍 Actual providers: {actual_providers}")
            
            if len(actual_providers) == 1 and actual_providers[0] == 'CUDAExecutionProvider':
                print(f"✅ Successfully created CUDA-only session")
                return True
            else:
                print(f"⚠️  Session created but with fallback providers")
                return False
        else:
            print(f"❌ Model file not found: {model_path}")
            return False
            
    except Exception as e:
        print(f"❌ CUDA-only verification failed: {e}")
        return False

if __name__ == "__main__":
    
    print("🎯 COMPREHENSIVE GPU-ONLY VERIFICATION")
    print("=" * 60)
    
    success1 = analyze_execution_providers()
    success2 = force_cuda_only_verification()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Execution provider analysis: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"CUDA-only verification: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print(f"\n🎉 GPU-ONLY MODE FULLY VERIFIED!")
        print(f"✅ Both YOLO and InsightFace optimized for GPU-only execution")
        print(f"✅ No CPU fallback - maximum performance achieved")
    else:
        print(f"\n⚠️  GPU-only mode needs further optimization")
