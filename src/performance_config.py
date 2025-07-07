INSIGHTFACE_MODEL = "antelopev2"  # Options: "antelopev2", "buffalo_l", "buffalo_m", "buffalo_s", "buffalo_sc" (sc=smallest)
YOLO_MODEL_SIZE = "l"  # Options: "n" (nano), "s" (small), "m" (medium), "l" (large), "x" (extra-large)
DETECTION_SIZE = (640, 640)  # Options: (320,320), (416,416), (512,512), (640,640), (736,736), (832,832)
CONFIDENCE_THRESHOLD = 0.4  # Options: 0.1-0.9 (lower=more detections, higher=fewer but confident)
MAX_FACES_PER_FRAME = 50  # Options: 1-100+ (1=single person, 10=classroom, 50+=crowd detection)
UI_UPDATE_INTERVAL = 3  # Options: 1-30 frames (1=real-time, 5=balanced, 10+=slower updates)
SKIP_FRAME_INTERVAL = 1  # Options: 0-10 (0=process all frames, 2=skip 2 process 1, 5=skip 5 process 1)
CACHE_DURATION = 30  # Options: 10-300 seconds (how long to remember faces)
RECOGNITION_THRESHOLD = 0.65  # Options: 0.3-0.9 (0.4=loose matching, 0.65=balanced, 0.8=strict)
AUTO_PERFORMANCE_ADJUST = False  # Options: True, False (auto-adjust settings based on performance)
TARGET_FPS = 12  # Options: 1-30 fps (1=slow/accurate, 5=balanced, 15=fast, 30=real-time)
VERBOSE_LOGGING = False  # Options: True, False (detailed console output for debugging)
GPU_MODE = "BALANCED"  # Options: "HIGH_PERFORMANCE", "BALANCED", "LOW_MEMORY", "ULTRA_LOW_MEMORY"
CAMERA_BUFFER_SIZE = 2  # Options: 1-10 (1=minimal latency, 5=smooth video, 10=very smooth but delayed)
USE_RTSP = False  # Options: True, False (network camera vs local camera)
RTSP_URL = 0  # Options: 0 (default camera), 1 (second camera), "rtsp://ip:port/stream" (network camera)

# Force consistent dtype settings to avoid Half/Float mismatch
FORCE_FLOAT32 = True  # Options: True, False (prevent mixed precision errors)
DISABLE_MIXED_PRECISION = True  # Options: True, False (disable automatic half-precision)

# RTX 3050 (4GB VRAM) Optimized Configuration:
# "HIGH_PERFORMANCE" = Maximum accuracy, high GPU/CPU usage, perfect for RTX 3050 8GB
# "BALANCED" = Good balance of speed/accuracy, PERFECT for RTX 3050 4GB ⭐
# "LOW_MEMORY" = Optimized for limited GPU memory, good for 2GB GPUs like MX250
# "ULTRA_LOW_MEMORY" = Minimal memory usage, may sacrifice some accuracy, for 1GB or less

# Model Size Memory Usage (approximate):
# InsightFace: antelopev2 (~800MB), buffalo_l (~600MB), buffalo_m (~400MB), buffalo_s (~200MB), buffalo_sc (~150MB)
# YOLO: x (~400MB), l (~200MB), m (~100MB), s (~50MB), n (~20MB)

# RTX 3050 4GB Total Usage: ~1000MB (antelopev2 + YOLO-L) = Good for 4GB VRAM with 3GB headroom!


