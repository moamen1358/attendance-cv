# Performance Configuration for Face Recognition System
# Adjust these settings to optimize performance vs accuracy
# Updated to use antelopev2 + yolov11n models with low-memory optimization

# MODEL SELECTION SETTINGS
INSIGHTFACE_MODEL = "antelopev2"     # InsightFace model: "antelopev2", "buffalo_sc", "buffalo_l", etc.
YOLO_MODEL_SIZE = "l"                # YOLO model size: "n", "s", "m", "l", "x"
                                     # n=nano (fastest, least memory), l=large (slower, more accurate)

# PROCESSING SETTINGS
DETECTION_SIZE = (480, 480)    # Detection resolution - optimized for low memory
                               # Options: (320, 320), (480, 480), (640, 640)

CONFIDENCE_THRESHOLD = 0.25    # YOLO detection confidence threshold
                               # Lower = more detections, higher = fewer false positives

MAX_FACES_PER_FRAME = 2        # Maximum faces to process per frame (reduced for memory)
                               # Lower = faster processing

# PERFORMANCE OPTIMIZATION
UI_UPDATE_INTERVAL = 3         # Update UI every N frames (higher = faster)
SKIP_FRAME_INTERVAL = 1        # Process every Nth frame (higher = faster, lower accuracy)
CACHE_DURATION = 30            # Recognition cache duration in seconds

# QUALITY SETTINGS
RECOGNITION_THRESHOLD = 0.6    # Face recognition threshold for antelopev2
                               # Higher = stricter matching, fewer false positives

# AUTO-ADJUSTMENT SETTINGS
AUTO_PERFORMANCE_ADJUST = True  # Enable automatic performance adjustment
TARGET_FPS = 15                # Target FPS for auto-adjustment
FPS_CHECK_INTERVAL = 60        # Check FPS every N frames for adjustment

# LOGGING SETTINGS  
VERBOSE_LOGGING = False        # Enable detailed logging (impacts performance)
CACHE_LOG_INTERVAL = 20        # Log cache hits every N cache accesses
DETECTION_LOG_INTERVAL = 10    # Log detections every N detection calls
PERFORMANCE_LOG_INTERVAL = 3   # Log performance adjustments every N checks

# GPU SETTINGS
GPU_MODE = "LOW_MEMORY"        # GPU mode: LOW_MEMORY, HYBRID, PREFER_GPU, STRICT_GPU_ONLY
                               # LOW_MEMORY recommended for GPUs with < 2GB memory

# CAMERA SETTINGS
CAMERA_BUFFER_SIZE = 1         # Camera buffer size (lower = less latency)
USE_RTSP = True                # Use RTSP camera vs local camera
RTSP_URL = "rtsp://admin:Admin%40123@192.168.1.64:554/Streaming/Channels/101"
# RTSP_URL = 0 # Use local camera (0 for default webcam)


# PERFORMANCE PRESETS
# Uncomment one of these presets or customize individual settings above

# # LOW MEMORY GPU (Recommended for <2GB GPU)
# DETECTION_SIZE = (320, 320)
# MAX_FACES_PER_FRAME = 1
# UI_UPDATE_INTERVAL = 5
# GPU_MODE = "LOW_MEMORY"

# # HIGH PERFORMANCE (Fastest, lower accuracy)
# DETECTION_SIZE = (320, 320)
# MAX_FACES_PER_FRAME = 2
# UI_UPDATE_INTERVAL = 5
# SKIP_FRAME_INTERVAL = 2
# RECOGNITION_THRESHOLD = 0.7

# # BALANCED (Good speed and accuracy)
# DETECTION_SIZE = (480, 480)
# MAX_FACES_PER_FRAME = 3
# UI_UPDATE_INTERVAL = 3
# SKIP_FRAME_INTERVAL = 1
# RECOGNITION_THRESHOLD = 0.6

# # HIGH ACCURACY (Slower, best accuracy)
# DETECTION_SIZE = (640, 640)
# MAX_FACES_PER_FRAME = 5
# UI_UPDATE_INTERVAL = 2
# SKIP_FRAME_INTERVAL = 1
# RECOGNITION_THRESHOLD = 0.5
