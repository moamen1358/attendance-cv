#!/usr/bin/env python3
"""
Test script to verify GPU usage across all components
"""

import torch
import sys
from pathlib import Path

# Add camera_scripts to path
camera_scripts_path = Path(__file__).parent / "camera_scripts"
sys.path.append(str(camera_scripts_path))

def test_pytorch_gpu():
    """Test PyTorch GPU availability"""
    print("=" * 50)
    print("🔍 Testing PyTorch GPU Support")
    print("=" * 50)
    
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Device memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        # Test tensor operations on GPU
        print("\n🚀 Testing GPU tensor operations...")
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.mm(x, y)
        print(f"✅ GPU tensor operation successful. Result device: {z.device}")
        
        # Check memory usage
        print(f"GPU memory allocated: {torch.cuda.memory_allocated(0) / 1024**3:.3f} GB")
        print(f"GPU memory cached: {torch.cuda.memory_reserved(0) / 1024**3:.3f} GB")
    else:
        print("❌ CUDA not available")
    
    return torch.cuda.is_available()

def test_yolo_gpu():
    """Test YOLO model GPU usage"""
    print("\n" + "=" * 50)
    print("🎯 Testing YOLO GPU Support")
    print("=" * 50)
    
    try:
        from ultralytics import YOLO
        
        # Load model
        model = YOLO("yolov11l-face.pt")
        print(f"✅ YOLO model loaded")
        
        # Check device before moving to GPU
        device_before = next(model.model.parameters()).device
        print(f"Model device before: {device_before}")
        
        # Move to GPU
        if torch.cuda.is_available():
            model.model.to('cuda')
            device_after = next(model.model.parameters()).device
            print(f"Model device after: {device_after}")
            
            # Test inference on a dummy image
            import cv2
            import numpy as np
            dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            results = model(dummy_image, verbose=False)
            print(f"✅ YOLO GPU inference successful")
            
            # Check GPU memory usage
            print(f"GPU memory after YOLO: {torch.cuda.memory_allocated(0) / 1024**3:.3f} GB")
        else:
            print("❌ CUDA not available for YOLO")
            
        return True
        
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False

def test_insightface_gpu():
    """Test InsightFace GPU usage"""
    print("\n" + "=" * 50)
    print("👤 Testing InsightFace GPU Support")
    print("=" * 50)
    
    try:
        import onnxruntime as ort
        from insightface.app import FaceAnalysis
        
        # Check ONNX Runtime providers
        available_providers = ort.get_available_providers()
        print(f"ONNX Runtime providers: {available_providers}")
        
        if 'CUDAExecutionProvider' in available_providers:
            print("✅ CUDA provider available for ONNX Runtime")
            
            # Initialize InsightFace with GPU
            app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
            app.prepare(ctx_id=0, det_size=(640, 640))
            print("✅ InsightFace initialized with GPU support")
            
            # Test with dummy image
            import cv2
            import numpy as np
            dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            faces = app.get(dummy_image)
            print(f"✅ InsightFace GPU inference successful (detected {len(faces)} faces)")
            
            # Check GPU memory usage
            print(f"GPU memory after InsightFace: {torch.cuda.memory_allocated(0) / 1024**3:.3f} GB")
            
            return True
        else:
            print("❌ CUDA provider not available for ONNX Runtime")
            return False
            
    except Exception as e:
        print(f"❌ InsightFace test failed: {e}")
        return False

def main():
    """Run all GPU tests"""
    print("🚀 GPU Usage Test Suite")
    print("=" * 70)
    
    results = {}
    results['pytorch'] = test_pytorch_gpu()
    results['yolo'] = test_yolo_gpu()
    results['insightface'] = test_insightface_gpu()
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{component.upper()}: {status}")
    
    if all(results.values()):
        print("\n🎉 ALL COMPONENTS USING GPU SUCCESSFULLY!")
    else:
        print("\n⚠️ SOME COMPONENTS NOT USING GPU")
        
    print("\n💡 If any component failed:")
    print("1. Check NVIDIA drivers: nvidia-smi")
    print("2. Check CUDA installation: nvcc --version")
    print("3. Reinstall PyTorch with CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("4. Check ONNX Runtime GPU: pip install onnxruntime-gpu")

if __name__ == "__main__":
    main()
