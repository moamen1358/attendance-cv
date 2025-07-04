#!/usr/bin/env python3
"""
GPU Test Script for Attendance System
"""

def test_pytorch_gpu():
    print("=== PyTorch GPU Test ===")
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"🔧 CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"🚀 CUDA version: {torch.version.cuda}")
            print(f"🚀 GPU count: {torch.cuda.device_count()}")
            print(f"🚀 Current device: {torch.cuda.current_device()}")
            print(f"🚀 GPU name: {torch.cuda.get_device_name(0)}")
            print(f"🚀 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            
            # Test tensor operations on GPU
            x = torch.rand(1000, 1000).cuda()
            y = torch.rand(1000, 1000).cuda()
            z = torch.matmul(x, y)
            print(f"✅ GPU tensor operations working")
            
        else:
            print("⚠️ CUDA not available")
        
        return torch.cuda.is_available()
    except Exception as e:
        print(f"❌ PyTorch error: {e}")
        return False

def test_yolo_gpu():
    print("\n=== YOLO GPU Test ===")
    try:
        from ultralytics import YOLO
        import torch
        print("✅ YOLO imported successfully")
        
        # Load model
        model_path = "/home/invisa/Desktop/my_grad_streamlit_last /yolov11l-face.pt"
        model = YOLO(model_path)
        print(f"✅ YOLO model loaded: {model_path}")
        
        # Check device
        print(f"🔧 Model device: {model.device}")
        
        if torch.cuda.is_available():
            # Move to GPU
            model.to('cuda')
            print(f"🚀 Model moved to GPU: {model.device}")
        
        return True
    except Exception as e:
        print(f"❌ YOLO error: {e}")
        return False

def test_insightface_gpu():
    print("\n=== InsightFace GPU Test ===")
    try:
        from insightface.app import FaceAnalysis
        import torch
        print("✅ InsightFace imported successfully")
        
        # Initialize with GPU
        if torch.cuda.is_available():
            app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
            app.prepare(ctx_id=0, det_size=(640, 640))
            print("🚀 InsightFace initialized with GPU support")
        else:
            app = FaceAnalysis(providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=-1, det_size=(640, 640))
            print("⚠️ InsightFace initialized with CPU only")
        
        return True
    except Exception as e:
        print(f"❌ InsightFace error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 GPU Detection and Testing Tool")
    print("=" * 50)
    
    pytorch_ok = test_pytorch_gpu()
    yolo_ok = test_yolo_gpu()
    insightface_ok = test_insightface_gpu()
    
    print("\n=== Summary ===")
    print(f"PyTorch GPU: {'✅' if pytorch_ok else '❌'}")
    print(f"YOLO GPU: {'✅' if yolo_ok else '❌'}")
    print(f"InsightFace GPU: {'✅' if insightface_ok else '❌'}")
    
    if all([pytorch_ok, yolo_ok, insightface_ok]):
        print("\n🎉 All components ready for GPU acceleration!")
    else:
        print("\n⚠️ Some components may not use GPU properly")
