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

MODEL_ROOT = os.path.join(os.getcwd(), "insightface_model")
MODEL_NAME = 'buffalo_sc'  # Changed from buffalo_sc to buffalo_l for better recognition

# FPS Optimization Settings - ASYNC PROCESSING
DETECTION_SIZE = (480, 480)  # Reduced from 640x640 for 30% speed boost
UI_UPDATE_INTERVAL = 3      # Update UI every 3 frames for 3x less overhead
MAX_FACES_PER_FRAME = 3     # Limit faces per frame to reduce processing time
CACHE_DURATION = 30         # Cache recognition results for 30 seconds

RTSP_URL = "rtsp://admin:Admin%40123@192.168.1.64:554/Streaming/Channels/102"
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

# Initialize face analysis model with GPU support
try:
    # Check if CUDA is available
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔧 Using device: {device}")
    
    if device == "cuda":
        print(f"🚀 CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"🚀 CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Try GPU first, fall back to CPU if needed
    try:
        # Initialize with GPU support and YOLO model path
        yolo_path = "/home/invisa/Desktop/my_grad_streamlit_last /yolo_models/yolov11n-face.pt"
        app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, yolo_model_path=yolo_path)
        app.prepare(ctx_id=0, det_size=DETECTION_SIZE)
        print(f"✅ Face analysis with YOLO initialized with GPU support")
    except Exception as gpu_error:
        print(f"⚠️ GPU initialization failed: {gpu_error}")
        print(f"🔄 Falling back to CPU...")
        # Fallback to CPU
        yolo_path = "/home/invisa/Desktop/my_grad_streamlit_last /yolo_models/yolov11n-face.pt"
        app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, yolo_model_path=yolo_path)
        app.prepare(ctx_id=-1, det_size=DETECTION_SIZE)
        print(f"✅ Face analysis with YOLO initialized with CPU fallback")
    
    print(f"✅ FaceAnalysis with YOLO integration loaded")
    
except Exception as e:
    st.error(f"Failed to initialize face analysis model: {str(e)}")
    print(f"❌ Face analysis error: {e}")
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
            print(f"No student found for recognized name: {name}")
            return False
        
        student_id, student_name, roll_number = result
        
        # Check if attendance already logged today
        cursor.execute("""
            SELECT id FROM attendance_records_enhanced 
            WHERE student_id = ? AND attendance_date = ?
        """, (student_id, current_date))
        
        if cursor.fetchone():
            print(f"Attendance already logged today for {student_name}")
            return True  # Already logged
        
        # Insert attendance record
        cursor.execute("""
            INSERT INTO attendance_records_enhanced 
            (student_id, attendance_date, attendance_time, status, marked_by, notes)
            VALUES (?, ?, ?, 'present', 'face_recognition', ?)
        """, (student_id, current_date, current_time, f"Confidence: {confidence:.2f}"))
        
        conn.commit()
        print(f"✅ Attendance logged for {student_name} at {current_time} (Confidence: {confidence:.2f})")
        return True
        
    except Exception as e:
        print(f"Error logging attendance: {e}")
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
        print(f"💾 Cache hit: {cached_result[0]} (confidence: {cached_result[1]:.3f})")
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
            return "Unknown", 0.0
        
        # Get best match
        best_name = results['metadatas'][0][0]['name']
        best_similarity = 1 - results['distances'][0][0]
        
        result = (best_name, best_similarity) if best_similarity >= threshold else ("Unknown", best_similarity)
        
        # Cache the result for future use
        recognition_cache[cache_key] = result
        
        return result
        
    except Exception as e:
        print(f"❌ Error in similarity search: {e}")
        return "Unknown", 0.0

def process_frame_with_attendance(frame, threshold=0.6, collection=None, attendance_logged=None):
    """Process a frame with face recognition and attendance logging - ASYNC VERSION"""
    global is_processing, last_processed_frame, processing_results
    
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
    .status-info {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        border-left: 4px solid #1f77b4;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        min-width: 120px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
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
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown('<div class="status-info">👥 Registered Students: {}</div>'.format(with_embeddings), unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="status-info">{}</div>'.format(gpu_info), unsafe_allow_html=True)
    
    with col3:
        threshold = st.slider("🎯 Recognition Threshold", 0.0, 1.0, 0.6, 0.05, 
                             help="Higher values = stricter recognition")
    
    st.divider()
    
    # Load embeddings to ChromaDB
    with st.spinner("🔄 Loading facial recognition database..."):
        collection = create_or_add_to_collection("face_recognition", path_to_chroma=CHROMA_STORE_PATH)
    
    if collection is None:
        st.error("❌ Failed to load facial recognition collection")
        return
    
    st.success(f"✅ Facial recognition database loaded with {collection.count()} profiles")
    
    # Live Stream Section
    st.subheader("📹 Live Attendance Stream")
    st.markdown("*Using InsightFace with YOLO detection for real-time face recognition and attendance logging*")
    
    # Stream controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        stop_stream = st.button("🛑 Stop Stream", type="secondary")
    with col3:
        clear_attendance = st.button("🗑️ Clear Today's Attendance", type="secondary")
    
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
    
    # Video capture
    # cap = cv2.VideoCapture(RTSP_URL)
    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
    
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
    attendance_logged = {}  # Track logged attendance to avoid duplicates
    display_frame = None   # Store frame for display
    
    # Continuous live stream with face recognition
    try:
        status_placeholder.success("🎥 Live stream active - Async processing enabled...")
        
        while not stop_stream:
            ret, frame = cap.read()
            if not ret:
                status_placeholder.error("❌ Lost connection to camera stream")
                break
            
            frame_count += 1
            
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
                fps = frame_count / (time.time() - start_time) if time.time() > start_time else 0
                
                # Add overlay text
                cv2.putText(processed_frame, f"Time: {current_time}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                # Add frame info overlay to display frame
                overlay_frame = display_frame.copy()
                cv2.putText(overlay_frame, f"Time: {current_time}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(overlay_frame, f"FPS: {fps:.1f} | Threshold: {threshold:.2f}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(overlay_frame, f"Attendance Logged: {len(attendance_logged)}", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Add processing status indicator
                processing_status = "🔄 Processing..." if is_processing else "✅ Ready"
                cv2.putText(overlay_frame, processing_status, (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Display the frame (only every UI_UPDATE_INTERVAL frames)
                stream_placeholder.image(overlay_frame, channels="BGR", 
                                   caption=f"🎥 Live Attendance Feed | FPS: {fps:.1f} | Async Processing", 
                                   use_container_width=True)
            
            # Update status
            if recognized_faces:
                status_placeholder.success(f"✅ Face recognized and attendance logged for: {', '.join(recognized_faces)}")
            else:
                status_placeholder.info("🔍 Monitoring for faces...")
            
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
        status_placeholder.success(f"🏁 Stream ended. Processed {frame_count} frames. Attendance logged for {len(attendance_logged)} students.")

if __name__ == "__main__":
    show_real_time_prediction()
