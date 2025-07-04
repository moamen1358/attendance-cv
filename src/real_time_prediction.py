import streamlit as st
import cv2
import numpy as np
import onnxruntime as ort
import chromadb
import sqlite3
from database_utils import execute_query, execute_query_df
import json
import uuid
import os
from datetime import datetime
import time
import sys
import subprocess
from pathlib import Path

# Add camera_scripts to path for imports
camera_scripts_path = Path(__file__).parent.parent / "camera_scripts"
sys.path.append(str(camera_scripts_path))

# Add local insightface to path BEFORE importing
insightface_path = Path(__file__).parent.parent / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

# Import our custom FaceAnalysis with YOLO integration
from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis

# Import performance monitor
from performance_monitor import get_global_monitor

# Import performance configuration
try:
    from performance_config import *
except ImportError:
    # Fallback to default settings if config file doesn't exist
    DETECTION_SIZE = (480, 480)
    CONFIDENCE_THRESHOLD = 0.25
    MAX_FACES_PER_FRAME = 3
    UI_UPDATE_INTERVAL = 3
    SKIP_FRAME_INTERVAL = 1
    CACHE_DURATION = 30
    RECOGNITION_THRESHOLD = 0.6
    AUTO_PERFORMANCE_ADJUST = True
    TARGET_FPS = 15
    FPS_CHECK_INTERVAL = 60
    VERBOSE_LOGGING = False
    CACHE_LOG_INTERVAL = 20
    DETECTION_LOG_INTERVAL = 10
    PERFORMANCE_LOG_INTERVAL = 3
    GPU_MODE = "HYBRID"
    CAMERA_BUFFER_SIZE = 1
    USE_RTSP = False
    RTSP_URL = "rtsp://admin:Admin%40123@192.168.1.64:554/Streaming/Channels/102"

MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Project root directory
MODEL_NAME = 'buffalo_sc'  # Changed from buffalo_sc to buffalo_l for better recognition

# Use configuration from performance_config.py
# Settings are now imported from performance_config.py - see that file for customization

CHROMA_STORE_PATH = "./store"
DATABASE_PATH = 'attendance_system.db'

# Async processing variables
frame_count = 0
ui_update_count = 0
recognition_cache = {}      # Cache for recognition results
last_cache_clear = time.time()
is_processing = False       # Flag to track if frame processing is ongoing
last_processed_frame = None # Store last processed frame for display
processing_results = {}     # Store processing results

# Initialize face analysis model with GPU ONLY (no CPU fallback)
try:
    # Suppress PyTorch warnings and errors that don't affect functionality
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # Check if CUDA is available - REQUIRE it for GPU-only operation
    import torch
    if not torch.cuda.is_available():
        st.error("🚨 CUDA is not available! This system requires GPU for optimal performance.")
        st.error("Please ensure NVIDIA GPU drivers and CUDA are properly installed.")
        st.stop()
    
    device = "cuda"
    print(f"🔧 Using device: {device} (GPU MODE: {GPU_MODE})")
    print(f"🚀 CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"🚀 CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Force GPU-only initialization - Handle PyTorch class errors gracefully
    print(f"🚀 Initializing models in {GPU_MODE} mode...")
    yolo_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov11n-face.pt")
    
    # Suppress specific torch.classes errors that don't affect functionality
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Initialize with forced GPU context (ctx_id=0) - HYBRID mode allows CPU fallback for InsightFace
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT, 
            yolo_model_path=yolo_path,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],  # Allow CPU fallback for InsightFace
            gpu_mode=GPU_MODE  # Use configured GPU mode
        )
        app.prepare(ctx_id=0, det_size=DETECTION_SIZE, det_thresh=CONFIDENCE_THRESHOLD)  # Use configured settings
    
    print(f"✅ Face analysis with YOLO initialized in {GPU_MODE} mode")
    print(f"✅ FaceAnalysis with YOLO integration loaded")
    
except Exception as e:
    st.error(f"Failed to initialize face analysis model: {str(e)}")
    print(f"❌ Face analysis error: {e}")
    # Print more details for debugging
    import traceback
    traceback.print_exc()
    st.stop()

def create_or_add_to_collection(collection_name, path_to_chroma="./store"):
    """Create a new collection or add data to an existing one in ChromaDB."""
    try:
        # Initialize the ChromaDB client with the persist directory
        client = chromadb.PersistentClient(path_to_chroma)

        # Check if the collection already exists
        try:
            # Try to get existing collection
            collection = client.get_collection(name=collection_name)
            # Delete existing collection to ensure fresh data
            client.delete_collection(name=collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, which is fine
            print(f"Collection {collection_name} doesn't exist yet - will create new one")
        
        # Create a new collection
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Retrieve data from the SQLite database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Try the enhanced schema first (new format)
        try:
            cursor.execute("""
                SELECT sp.profile_name, sp.encoding_data 
                FROM student_profiles_enhanced sp 
                WHERE sp.status = 'active' AND sp.encoding_data IS NOT NULL
            """)
            rows = cursor.fetchall()
            print(f"Found {len(rows)} profiles in student_profiles_enhanced")
        except sqlite3.OperationalError as e:
            print(f"Error reading from student_profiles_enhanced: {e}")
            # Fall back to legacy tables
            try:
                cursor.execute("SELECT name, facial_features FROM facial_recognition_data")
                rows = cursor.fetchall()
                print(f"Found {len(rows)} profiles in facial_recognition_data")
            except sqlite3.OperationalError:
                try:
                    cursor.execute("SELECT name, facial_features FROM presidents_embeds")
                    rows = cursor.fetchall()
                    print(f"Found {len(rows)} profiles in presidents_embeds")
                except sqlite3.OperationalError:
                    print("No facial recognition tables found!")
                    rows = []
            
        conn.close()

        # Add data to the collection
        for index, row in enumerate(rows):
            name, embedding_str = row
            embedding = json.loads(embedding_str)
            collection.add(
                ids=[str(uuid.uuid4())],  # Generate a unique ID for each entry
                documents=[name],
                embeddings=[embedding],
                metadatas=[{"name": name}],
            )

        print(f"Data successfully stored in ChromaDB! Added {len(rows)} profiles")
        return collection

    except Exception as e:
        st.error(f"Error creating or adding to the collection: {str(e)}")
        return None

def log_attendance(name, confidence, device_id=None):
    """Log student attendance to the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get current date and time
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Find the student_id based on the recognized name
        cursor.execute("""
            SELECT sp.student_id, s.name, s.roll_number 
            FROM student_profiles_enhanced sp
            JOIN students_enhanced s ON sp.student_id = s.student_id
            WHERE sp.profile_name = ? AND sp.status = 'active'
            LIMIT 1
        """, (name,))
        
        result = cursor.fetchone()
        if not result:
            print(f"⚠️ No student found for recognized name: {name}")
            # Try alternative lookup in case profile_name doesn't match exactly
            cursor.execute("""
                SELECT sp.student_id, s.name, s.roll_number 
                FROM student_profiles_enhanced sp
                JOIN students_enhanced s ON sp.student_id = s.student_id
                WHERE s.name LIKE ? AND sp.status = 'active'
                LIMIT 1
            """, (f"%{name}%",))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ No student found for name: {name} (exact or partial match)")
                return False
        
        student_id, student_name, roll_number = result
        print(f"🔍 Found student: {student_name} (ID: {student_id})")
        
        # Check if attendance already logged today
        cursor.execute("""
            SELECT id FROM attendance_records_enhanced 
            WHERE student_id = ? AND attendance_date = ?
        """, (student_id, current_date))
        
        existing_record = cursor.fetchone()
        if existing_record:
            print(f"ℹ️ Attendance already logged today for {student_name}")
            return True  # Already logged, but this is success
        
        # Insert attendance record
        cursor.execute("""
            INSERT INTO attendance_records_enhanced 
            (student_id, attendance_date, attendance_time, status, marked_by, notes)
            VALUES (?, ?, ?, 'present', 'face_recognition', ?)
        """, (student_id, current_date, current_time, f"Confidence: {confidence:.2f}"))
        
        conn.commit()
        print(f"✅ NEW ATTENDANCE logged for {student_name} at {current_time} (Confidence: {confidence:.2f})")
        return True
        
    except Exception as e:
        print(f"❌ Error logging attendance: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def cosine_similarity_search(query_embedding, threshold=0.6, collection=None):
    """Enhanced cosine similarity search with caching for FPS optimization"""
    global recognition_cache, last_cache_clear
    
    if collection is None:
        return "Unknown", 0.0
    
    # Handle None embedding
    if query_embedding is None:
        print("⚠️ Cannot search with None embedding")
        return "Unknown", 0.0

    # Clear cache periodically
    current_time = time.time()
    if current_time - last_cache_clear > CACHE_DURATION:
        recognition_cache.clear()
        last_cache_clear = current_time
        print("🗑️ Cleared recognition cache")

    # Create cache key from embedding (use first few values as key)
    cache_key = tuple(query_embedding[:10].round(3))  # Use first 10 values, rounded
    
    # Check cache first
    if cache_key in recognition_cache:
        cached_result = recognition_cache[cache_key]
        # Only log cache hits occasionally to reduce spam
        if not hasattr(cosine_similarity_search, '_cache_log_counter'):
            cosine_similarity_search._cache_log_counter = 0
        cosine_similarity_search._cache_log_counter += 1
        
        if cosine_similarity_search._cache_log_counter % CACHE_LOG_INTERVAL == 0:  # Use configured interval
            if VERBOSE_LOGGING:  # Only log if verbose logging is enabled
                print(f"💾 Cache hit: {cached_result[0]} (confidence: {cached_result[1]:.3f})")
        
        # Log cache hit for performance monitoring
        get_global_monitor().log_cache_hit()
        return cached_result

    try:
        # Normalize query embedding
        query_normalized = query_embedding / np.linalg.norm(query_embedding)
        
        # Get collection info
        collection_count = collection.count()
        
        results = collection.query(
            query_embeddings=[query_normalized.tolist()],
            n_results=min(3, collection_count),
            include=["distances", "metadatas"]
        )
        
        if not results['ids'][0]:
            get_global_monitor().log_cache_miss()
            return "Unknown", 0.0
        
        # Get best match
        best_name = results['metadatas'][0][0]['name']
        best_similarity = 1 - results['distances'][0][0]
        
        result = (best_name, best_similarity) if best_similarity >= threshold else ("Unknown", best_similarity)
        
        # Cache the result for future use
        recognition_cache[cache_key] = result
        
        # Log cache miss for performance monitoring
        get_global_monitor().log_cache_miss()
        
        return result
        
    except Exception as e:
        print(f"❌ Error in similarity search: {e}")
        get_global_monitor().log_cache_miss()
        return "Unknown", 0.0

def process_frame_with_attendance(frame, threshold=0.6, collection=None, attendance_logged=None):
    """Process a frame with face recognition and attendance logging - OPTIMIZED ASYNC VERSION"""
    global is_processing, last_processed_frame, processing_results, frame_count
    
    if attendance_logged is None:
        attendance_logged = {}
    
    recognized_faces = []
    
    # ASYNC Optimization: Only process if no other frame is currently being processed
    if is_processing:
        # Return the last processed frame with cached results for smooth streaming
        if last_processed_frame is not None:
            return last_processed_frame, processing_results.get('recognized_faces', [])
        else:
            return frame, recognized_faces
    
    # Skip frames for performance optimization
    if frame_count % SKIP_FRAME_INTERVAL != 0:
        # Return current frame without processing for smooth display
        return frame, recognized_faces
    
    # Mark as processing to prevent overlap
    is_processing = True
    
    try:
        faces = app.get(frame)
        
        if not faces:
            last_processed_frame = frame
            processing_results['recognized_faces'] = []
            return frame, recognized_faces
        
        # Limit max faces per frame for performance
        faces = faces[:MAX_FACES_PER_FRAME]
        
        # Only log face processing occasionally to reduce spam
        if not hasattr(process_frame_with_attendance, '_log_counter'):
            process_frame_with_attendance._log_counter = 0
        process_frame_with_attendance._log_counter += 1
        
        if process_frame_with_attendance._log_counter % (30 if VERBOSE_LOGGING else 60) == 0:  # Configurable logging
            if VERBOSE_LOGGING:
                print(f"🔍 Processing {len(faces)} faces (limited to {MAX_FACES_PER_FRAME} for performance)")
        
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            embedding = face.embedding
            
            # Check if embedding is None (no recognition model available)
            if embedding is None:
                print("⚠️ Face detected but no embedding available (no recognition model)")
                name, confidence = "Unknown", 0.0
            else:
                # Get recognition results
                name, confidence = cosine_similarity_search(embedding, threshold, collection)
            
            # Check if face was recognized and not already logged today
            if name != "Unknown":
                current_date = datetime.now().strftime('%Y-%m-%d')
                attendance_key = f"{name}_{current_date}"
                
                if attendance_key not in attendance_logged:
                    # Log attendance
                    if log_attendance(name, confidence):
                        attendance_logged[attendance_key] = {
                            'name': name,
                            'confidence': confidence,
                            'time': datetime.now().strftime('%H:%M:%S')
                        }
                        recognized_faces.append(name)
                        # Log attendance for performance monitoring
                        get_global_monitor().log_attendance_logged()
            
            # Draw results
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            label = f"{name} ({confidence:.2f})" if name != "Unknown" else "Unknown"
            
            # Check if already logged today
            current_date = datetime.now().strftime('%Y-%m-%d')
            attendance_key = f"{name}_{current_date}"
            if attendance_key in attendance_logged:
                label += " ✓"
                color = (0, 255, 255)  # Yellow for already logged
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Store processed frame and results
        last_processed_frame = frame.copy()
        processing_results['recognized_faces'] = recognized_faces
        
        # Log performance metrics
        get_global_monitor().log_frame_processed()
        get_global_monitor().log_faces_detected(len(faces))
        
        return frame, recognized_faces
    
    finally:
        # Always release the processing lock
        is_processing = False

def check_gpu_status():
    """Check and display current GPU status"""
    import torch
    try:
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            gpu_name = torch.cuda.get_device_name(current_device)
            gpu_memory_allocated = torch.cuda.memory_allocated(current_device) / 1024**3
            gpu_memory_total = torch.cuda.get_device_properties(current_device).total_memory / 1024**3
            
            return {
                "available": True,
                "name": gpu_name,
                "count": gpu_count,
                "current": current_device,
                "memory_used": gpu_memory_allocated,
                "memory_total": gpu_memory_total,
                "memory_percent": (gpu_memory_allocated / gpu_memory_total) * 100
            }
        else:
            return {"available": False}
    except Exception as e:
        print(f"Error checking GPU status: {e}")
        return {"available": False, "error": str(e)}

def adjust_performance_settings(fps, target_fps=15):
    """Dynamically adjust processing settings based on current FPS"""
    global SKIP_FRAME_INTERVAL, UI_UPDATE_INTERVAL, MAX_FACES_PER_FRAME
    
    # Prevent adjustment if FPS is 0 (initial startup)
    if fps <= 0:
        return "INITIALIZING"
    
    if fps < target_fps * 0.7:  # Performance is too low
        # Reduce processing load
        SKIP_FRAME_INTERVAL = min(3, SKIP_FRAME_INTERVAL + 1)
        UI_UPDATE_INTERVAL = min(5, UI_UPDATE_INTERVAL + 1)
        MAX_FACES_PER_FRAME = max(1, MAX_FACES_PER_FRAME - 1)
        return "REDUCED_LOAD"
    elif fps > target_fps * 1.2:  # Performance is good, can increase quality
        # Increase processing quality
        SKIP_FRAME_INTERVAL = max(1, SKIP_FRAME_INTERVAL - 1)
        UI_UPDATE_INTERVAL = max(2, UI_UPDATE_INTERVAL - 1)
        MAX_FACES_PER_FRAME = min(5, MAX_FACES_PER_FRAME + 1)
        return "INCREASED_QUALITY"
    
    return "STABLE"

def show_real_time_prediction():
    # Page styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .simple-mode {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<div class="main-header">🎓 Live Camera System</div>', unsafe_allow_html=True)
    
    # Simple mode toggle
    simple_mode = st.checkbox("📹 Simple Camera Mode (No attendance, just live stream)", value=True)
    
    if simple_mode:
        st.markdown('<div class="simple-mode">📹 <b>Simple Mode</b>: Live camera stream with face detection only</div>', unsafe_allow_html=True)
        show_simple_camera_stream()
        return
    
    # Original complex mode continues below...
    st.markdown("""
    <style>
    .status-info {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🎓 Live Attendance System</div>', unsafe_allow_html=True)
    
    # Check database for facial embeddings
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(CASE WHEN encoding_data IS NOT NULL THEN 1 END) as with_embeddings 
        FROM student_profiles_enhanced 
        WHERE status = 'active'
    """)
    with_embeddings = cursor.fetchone()[0]
    conn.close()
    
    if with_embeddings == 0:
        st.error("❌ No facial embeddings found! Please register student faces first.")
        st.info("💡 Go to the registration page to add student faces before using live attendance.")
        return
    
    # GPU Status Check
    import torch
    gpu_status = check_gpu_status()
    if gpu_status["available"]:
        gpu_info = f"🚀 GPU: {gpu_status['name']} ({gpu_status['memory_used']:.1f}/{gpu_status['memory_total']:.1f}GB)"
        st.success(f"�� **GPU Active**: {gpu_status['name']} ({gpu_status['memory_total']:.1f} GB)")
    else:
        gpu_info = "⚠️ CPU Only"
        st.warning("⚠️ **Running on CPU** - For better performance, ensure GPU is available")
    
    # Controls section
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        st.markdown('<div class="status-info">👥 Registered Students: {}</div>'.format(with_embeddings), unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="status-info">{}</div>'.format(gpu_info), unsafe_allow_html=True)
    
    with col3:
        threshold = st.slider("🎯 Recognition Threshold", 0.0, 1.0, RECOGNITION_THRESHOLD, 0.05, 
                             help="Higher values = stricter recognition")
    
    with col4:
        show_performance = st.checkbox("📊 Show Performance", value=False,
                                     help="Display real-time performance metrics")
    
    st.divider()
    
    # Load embeddings to ChromaDB
    with st.spinner("🔄 Loading facial recognition database..."):
        collection = create_or_add_to_collection("face_recognition", path_to_chroma=CHROMA_STORE_PATH)
    
    if collection is None:
        st.error("❌ Failed to load facial recognition collection")
        return
    
    st.success(f"✅ Facial recognition database loaded with {collection.count()} profiles")
    
    # Debug database structure to help with attendance logging
    if VERBOSE_LOGGING:
        debug_database_structure()
    
    # Live Stream Section
    st.subheader("📹 Live Attendance Stream")
    st.markdown("*Using InsightFace with YOLO detection for real-time face recognition and attendance logging*")
    
    # Stream controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col2:
        stop_stream = st.button("🛑 Stop Stream", type="secondary")
    with col3:
        clear_attendance = st.button("🗑️ Clear Today's Attendance", type="secondary")
    with col4:
        show_perf_summary = st.button("📊 Performance Summary", type="secondary")
    
    if show_perf_summary:
        performance_monitor = get_global_monitor()
        performance_monitor.print_summary()
        st.success("📊 Performance summary printed to console")
    
    if clear_attendance:
        if st.button("⚠️ Confirm Clear", type="secondary"):
            # Clear today's attendance (for testing)
            current_date = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance_records_enhanced WHERE attendance_date = ?", (current_date,))
            conn.commit()
            conn.close()
            st.success("✅ Today's attendance cleared!")
            st.experimental_rerun()
    
    # Live stream display
    stream_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Performance display (optional)
    if show_performance:
        performance_placeholder = st.empty()
    
    # Initialize performance monitor
    performance_monitor = get_global_monitor()
    performance_monitor.start_monitoring(interval=2.0)
    
    # Video capture
    if USE_RTSP:
        cap = cv2.VideoCapture(RTSP_URL)
    else:
        cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_BUFFER_SIZE)  # Use configured buffer size
    
    if not cap.isOpened():
        st.error("❌ Could not connect to camera stream")
        st.error(f"📡 Camera URL: {RTSP_URL}")
        # Try local camera as fallback
        st.info("🔄 Trying local camera as fallback...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ No camera available")
            return
        else:
            st.success("✅ Connected to local camera")
    
    # Initialize frame counter for performance monitoring
    frame_count = 0
    ui_update_count = 0  # Counter for UI updates
    start_time = time.time()
    last_fps_calculation = time.time()
    fps_calculation_interval = 5.0  # Calculate FPS every 5 seconds for accuracy
    recent_frame_times = []  # Track recent frame processing times
    attendance_logged = {}  # Track logged attendance to avoid duplicates
    display_frame = None   # Store frame for display
    last_fps_check = time.time()  # For dynamic performance adjustment
    performance_log_counter = 0   # Reduce performance logging
    
    # Continuous live stream with face recognition
    try:
        status_placeholder.success("🎥 Live stream active - Async processing enabled...")
        
        while not stop_stream:
            ret, frame = cap.read()
            if not ret:
                status_placeholder.error("❌ Lost connection to camera stream")
                break
            
            frame_count += 1
            current_frame_time = time.time()
            recent_frame_times.append(current_frame_time)
            
            # Keep only recent frame times (last 30 frames for rolling FPS calculation)
            if len(recent_frame_times) > 30:
                recent_frame_times = recent_frame_times[-30:]
            
            # Calculate FPS more accurately using recent frame times
            if len(recent_frame_times) >= 2:
                time_span = recent_frame_times[-1] - recent_frame_times[0]
                fps = (len(recent_frame_times) - 1) / time_span if time_span > 0 else 0
            else:
                fps = 0
            
            # Dynamic performance adjustment
            if AUTO_PERFORMANCE_ADJUST and frame_count % FPS_CHECK_INTERVAL == 0:
                adjustment = adjust_performance_settings(fps, target_fps=TARGET_FPS)
                
                performance_log_counter += 1
                if performance_log_counter % PERFORMANCE_LOG_INTERVAL == 0:  # Use configured interval
                    if VERBOSE_LOGGING:
                        print(f"📊 Performance: {fps:.1f} FPS | Adjustment: {adjustment} | Skip: {SKIP_FRAME_INTERVAL}")
            
            # ASYNC PROCESSING: Always get current frame, processing happens asynchronously
            processed_frame, recognized_faces = process_frame_with_attendance(
                frame, threshold, collection, attendance_logged
            )
            
            # Always update display_frame for smooth streaming
            display_frame = processed_frame
            
            # UI Update Throttling - only update display every UI_UPDATE_INTERVAL frames
            ui_update_count += 1
            if ui_update_count % UI_UPDATE_INTERVAL == 0:
                # Add frame info overlay
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Remove duplicate overlay text
                overlay_frame = display_frame.copy()
                cv2.putText(overlay_frame, f"Time: {current_time}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(overlay_frame, f"FPS: {fps:.1f} | Threshold: {threshold:.2f}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(overlay_frame, f"Attendance Logged: {len(attendance_logged)}", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Add processing status indicator
                processing_status = "Processing" if is_processing else "Ready"
                status_color = (0, 255, 255) if is_processing else (0, 255, 0)
                cv2.putText(overlay_frame, processing_status, (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                
                # Add frame counter for debugging
                cv2.putText(overlay_frame, f"Frame: {frame_count} | Skip: {SKIP_FRAME_INTERVAL}", (10, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                # Display the frame (only every UI_UPDATE_INTERVAL frames)
                stream_placeholder.image(overlay_frame, channels="BGR", 
                                   caption=f"🎥 Live Attendance Feed | FPS: {fps:.1f} | Processing Mode: {GPU_MODE}", 
                                   use_container_width=True)
                
                # Show performance metrics if enabled
                if show_performance:
                    perf_summary = performance_monitor.get_summary()
                    perf_text = f"""
                    **Performance Metrics:**
                    - FPS: {perf_summary['average_fps']:.1f}
                    - CPU: {perf_summary['average_cpu_percent']:.1f}%
                    - RAM: {perf_summary['average_ram_percent']:.1f}%
                    - Cache Hit Rate: {perf_summary['cache_hit_rate_percent']:.1f}%
                    - Faces Detected: {perf_summary['faces_detected']}
                    - Attendance Logged: {perf_summary['attendance_logged']}
                    """
                    if 'gpu_memory_percent' in perf_summary:
                        perf_text += f"- GPU Memory: {perf_summary['gpu_memory_percent']:.1f}%"
                    
                    performance_placeholder.info(perf_text)
            
            # Update status
            if recognized_faces:
                status_placeholder.success(f"✅ Face recognized and attendance logged for: {', '.join(recognized_faces)}")
            else:
                status_placeholder.info("🔍 Monitoring for faces...")
            
            # Adjust performance settings based on current FPS
            if PERFORMANCE_MODE == "AUTO":
                adjust_performance_settings(fps)
            
            # Minimal delay for smooth streaming
            time.sleep(0.01)  # Very small delay for smooth stream
            
            # Safety check - refresh stop button state
            if frame_count % 30 == 0:  # Check every 30 frames
                # Force a small refresh to check for button presses
                pass
            
    except KeyboardInterrupt:
        status_placeholder.info("🛑 Stream stopped by user")
    except Exception as e:
        status_placeholder.error(f"❌ Stream error: {e}")
    finally:
        cap.release()
        performance_monitor.stop_monitoring()
        performance_monitor.print_summary()
        status_placeholder.success(f"🏁 Stream ended. Processed {frame_count} frames. Attendance logged for {len(attendance_logged)} students.")

def debug_database_structure():
    """Debug function to check database structure and data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🔍 DEBUG: Checking database structure...")
        
        # Check available tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Available tables: {[table[0] for table in tables]}")
        
        # Check student_profiles_enhanced structure
        try:
            cursor.execute("PRAGMA table_info(student_profiles_enhanced);")
            columns = cursor.fetchall()
            print(f"📋 student_profiles_enhanced columns: {[col[1] for col in columns]}")
            
            # Check sample data
            cursor.execute("SELECT profile_name, student_id, status FROM student_profiles_enhanced LIMIT 5;")
            profiles = cursor.fetchall()
            print(f"👥 Sample profiles: {profiles}")
        except Exception as e:
            print(f"⚠️ Error checking student_profiles_enhanced: {e}")
        
        # Check students_enhanced structure  
        try:
            cursor.execute("PRAGMA table_info(students_enhanced);")
            columns = cursor.fetchall()
            print(f"📋 students_enhanced columns: {[col[1] for col in columns]}")
            
            cursor.execute("SELECT student_id, name FROM students_enhanced LIMIT 5;")
            students = cursor.fetchall()
            print(f"🎓 Sample students: {students}")
        except Exception as e:
            print(f"⚠️ Error checking students_enhanced: {e}")
            
    except Exception as e:
        print(f"❌ Database debug error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def show_simple_camera_stream():
    """Simple camera stream without attendance logging or complex features"""
    
    # Simple controls
    col1, col2 = st.columns([3, 1])
    with col2:
        stop_stream = st.button("🛑 Stop Stream", type="secondary")
    
    # Stream display
    stream_placeholder = st.empty()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)  # Use local camera
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        st.error("❌ Could not open camera")
        return
    
    st.info("🎥 Simple camera stream active...")
    
    # Simple streaming loop
    frame_count = 0
    start_time = time.time()
    
    try:
        while not stop_stream:
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Failed to read from camera")
                break
            
            frame_count += 1
            
            # Simple face detection (no recognition)
            try:
                faces = app.get(frame)
                
                for face in faces:
                    x1, y1, x2, y2 = face.bbox.astype(int)
                    confidence = face.det_score
                    
                    # Draw green box around detected face
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"Face {confidence:.2f}", (x1, y1-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            except:
                pass  # Continue even if face detection fails
            
            # Add simple overlay
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            cv2.putText(frame, f"Time: {current_time}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"FPS: {fps:.1f} | Frames: {frame_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, "Simple Mode - Face Detection Only", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Display frame
            stream_placeholder.image(frame, channels="BGR", 
                                   caption=f"📹 Simple Live Camera Feed | FPS: {fps:.1f}", 
                                   use_container_width=True)
            
            # Small delay for smooth streaming
            time.sleep(0.03)
            
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        st.success(f"🏁 Simple stream ended. Processed {frame_count} frames.")
