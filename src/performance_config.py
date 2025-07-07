INSIGHTFACE_MODEL = "buffalo_sc"  # Small model for 2GB GPU
YOLO_MODEL_SIZE = "s"  # Small model instead of large
DETECTION_SIZE = (320, 320)
CONFIDENCE_THRESHOLD = 0.3  # Lower for smaller model
MAX_FACES_PER_FRAME = 1  # Single person attendance
UI_UPDATE_INTERVAL = 5
SKIP_FRAME_INTERVAL = 2
CACHE_DURATION = 30
RECOGNITION_THRESHOLD = 0.65
AUTO_PERFORMANCE_ADJUST = False
TARGET_FPS = 5
VERBOSE_LOGGING = False
GPU_MODE = "LOW_MEMORY"
CAMERA_BUFFER_SIZE = 1
USE_RTSP = False
RTSP_URL = 0

# Force consistent dtype settings to avoid Half/Float mismatch
FORCE_FLOAT32 = True
DISABLE_MIXED_PRECISION = True
