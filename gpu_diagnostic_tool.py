#!/usr/bin/env python3
"""
GPU Diagnostic and Fix Tool
Diagnoses ONNX Runtime CUDA issues and provides solutions
"""

import os
import sys
import subprocess

def check_cuda_environment():
    """Check CUDA installation and environment"""
    print("🔍 CUDA ENVIRONMENT DIAGNOSTIC")
    print("=" * 40)
    
    # Check CUDA
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ CUDA compiler is available")
            print(result.stdout.strip())
        else:
            print("❌ CUDA compiler not found")
    except FileNotFoundError:
        print("❌ CUDA compiler not found")
    
    # Check nvidia-smi
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA driver is working")
        else:
            print("❌ NVIDIA driver issue")
    except FileNotFoundError:
        print("❌ nvidia-smi not found")

def check_onnx_runtime():
    """Check ONNX Runtime installation"""
    print("\n🔍 ONNX RUNTIME DIAGNOSTIC")
    print("=" * 40)
    
    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime version: {ort.__version__}")
        print(f"🔍 Available providers: {ort.get_available_providers()}")
        
        # Try to create a CUDA session
        try:
            # Create minimal test
            import numpy as np
            
            # Create a simple test session with CUDA provider
            providers = ['CUDAExecutionProvider']
            provider_options = [{'device_id': 0}]
            
            print("🔍 Testing CUDA provider initialization...")
            
            # This will fail with the current cuDNN issue
            session = ort.InferenceSession(
                providers=providers,
                provider_options=provider_options
            )
            print("✅ CUDA provider test successful")
            return True
            
        except Exception as e:
            print(f"❌ CUDA provider test failed: {e}")
            
            if "libcudnn_ops.so" in str(e):
                print("\n🔧 DETECTED: cuDNN library compatibility issue")
                print("This is a known issue with ONNX Runtime and newer cuDNN versions.")
                print("\nPossible solutions:")
                print("1. Reinstall onnxruntime-gpu with compatible cuDNN:")
                print("   pip uninstall onnxruntime onnxruntime-gpu")
                print("   pip install onnxruntime-gpu==1.15.1")
                print("\n2. Or use CPU fallback with warning (not recommended for GPU-only mode)")
                print("\n3. Or install compatible cuDNN version")
                
            return False
            
    except ImportError:
        print("❌ ONNX Runtime not installed")
        return False

def check_pytorch_cuda():
    """Check PyTorch CUDA availability"""
    print("\n🔍 PYTORCH CUDA DIAGNOSTIC")
    print("=" * 40)
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA version: {torch.version.cuda}")
            print(f"✅ Device count: {torch.cuda.device_count()}")
            print(f"✅ Current device: {torch.cuda.current_device()}")
            print(f"✅ Device name: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("❌ PyTorch CUDA not available")
            return False
            
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def suggest_fixes():
    """Suggest fixes based on diagnostics"""
    print("\n🔧 RECOMMENDED FIXES")
    print("=" * 40)
    
    print("For the current cuDNN compatibility issue:")
    print("1. QUICK FIX - Downgrade ONNX Runtime:")
    print("   pip uninstall onnxruntime onnxruntime-gpu")
    print("   pip install onnxruntime-gpu==1.15.1")
    
    print("\n2. ALTERNATIVE - Use PyTorch-based face recognition:")
    print("   Since YOLO (PyTorch) works perfectly on GPU,")
    print("   consider using PyTorch-based face recognition models")
    
    print("\n3. HYBRID APPROACH - GPU detection + CPU recognition:")
    print("   Use YOLO on GPU for detection (fast)")
    print("   Use InsightFace on CPU for recognition (slower but works)")
    print("   This maintains most performance benefits")

def main():
    """Run full diagnostic"""
    print("🚀 GPU DIAGNOSTIC TOOL")
    print("=" * 50)
    
    cuda_ok = check_cuda_environment()
    pytorch_ok = check_pytorch_cuda() 
    onnx_ok = check_onnx_runtime()
    
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    print(f"CUDA Environment: {'✅ OK' if cuda_ok else '❌ ISSUE'}")
    print(f"PyTorch CUDA: {'✅ OK' if pytorch_ok else '❌ ISSUE'}")
    print(f"ONNX Runtime CUDA: {'✅ OK' if onnx_ok else '❌ ISSUE'}")
    
    if not onnx_ok:
        suggest_fixes()
    
    if pytorch_ok and not onnx_ok:
        print("\n🎯 CURRENT STATUS:")
        print("✅ YOLO face detection can use GPU (PyTorch working)")
        print("❌ InsightFace recognition falling back to CPU (ONNX Runtime issue)")
        print("\nThis gives you ~80% of the performance benefits since detection is the heavy operation.")

if __name__ == "__main__":
    main()
