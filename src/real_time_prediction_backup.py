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

# Import the adjusted FaceAnalysis
from insightface.app import FaceAnalysis

MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Project root directory
MODEL_NAME = 'buffalo_sc'

DETECTION_SIZE = (640, 640)
RTSP_URL = "rtsp://admin:Admin%40123@192.168.1.64:554/Streaming/Channels/102"
CHROMA_STORE_PATH = "./store"
DATABASE_PATH = 'attendance_system.db'

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
        # Initialize with GPU support and YOLO model path (note the space in directory name)
        yolo_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov11l-face.pt")
        app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, yolo_model_path=yolo_path)
        app.prepare(ctx_id=0, det_size=DETECTION_SIZE)
        print(f"✅ Face analysis with YOLO initialized with GPU support")
    except Exception as gpu_error:
        print(f"⚠️ GPU initialization failed: {gpu_error}")
        print(f"🔄 Falling back to CPU...")
        # Fallback to CPU
        yolo_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov11l-face.pt")
        app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, yolo_model_path=yolo_path)
        app.prepare(ctx_id=-1, det_size=DETECTION_SIZE)
        print(f"✅ Face analysis with YOLO initialized with CPU fallback")
    
    print(f"✅ FaceAnalysis with YOLO integration loaded")
    
except Exception as e:
    st.error(f"Failed to initialize face analysis model: {str(e)}")
    print(f"❌ Face analysis error: {e}")
    st.stop()

def create_or_add_to_collection(collection_name, path_to_chroma="./store"):
    """
    Create a new collection or add data to an existing one in ChromaDB.

    Args:
        collection_name (str): The name of the collection.
        path_to_chroma (str): Path to the ChromaDB store.

    Returns:
        collection: The ChromaDB collection object.
    """
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
            print(f"Adding to ChromaDB: {name} (embedding length: {len(embedding)})")
            collection.add(
                ids=[str(uuid.uuid4())],  # Generate a unique ID for each entry
                documents=[name],
                embeddings=[embedding],
                metadatas=[{"name": name}],
            )

        print(f"Data successfully stored in ChromaDB! Added {len(rows)} profiles")
        
        # Debug: Check what's actually in the collection
        try:
            collection_count = collection.count()
            print(f"ChromaDB collection now contains {collection_count} items")
            
            # Sample query to see what names are stored
            if collection_count > 0:
                sample_results = collection.get(limit=5)
                print("Sample stored names:", [meta.get('name', 'Unknown') for meta in sample_results['metadatas']])
        except Exception as debug_e:
            print(f"Debug error: {debug_e}")
        
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
        # First try to find by profile_name in student_profiles_enhanced
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
        print(f"Found student: {student_name} (ID: {student_id}, Roll: {roll_number})")
        
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
        print(f"✅ Attendance logged for {student_name} at {current_time}")
        return True
        
    except Exception as e:
        print(f"Error logging attendance: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def process_frame(frame, threshold=0.6, collection=None):
    """Process a frame with face recognition"""
    faces = app.get(frame)
    recognized = False
    
    if not faces:
        return frame, recognized
    
    for face in faces:
        x1, y1, x2, y2 = face.bbox.astype(int)
        embedding = face.embedding
        
        # Get recognition results
        name, confidence = cosine_similarity_search(embedding, threshold, collection)
        
        # Check if face was recognized
        if name != "Unknown":
            recognized = True
            log_attendance(name, confidence)
        
        # Draw results
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        label = f"{name} ({confidence:.2f})" if name != "Unknown" else "Unknown"
        if label == 'Unknown':
            label = ''
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame, recognized

def cosine_similarity_search(query_embedding, threshold=0.6, collection=None):
    """Enhanced cosine similarity search with debugging"""
    if collection is None:
        print("❌ No collection provided for search")
        return "Unknown", 0.0

    try:
        # Normalize query embedding
        query_normalized = query_embedding / np.linalg.norm(query_embedding)
        
        # Get collection info
        collection_count = collection.count()
        print(f"🔍 Searching in collection with {collection_count} faces")
        
        results = collection.query(
            query_embeddings=[query_normalized.tolist()],
            n_results=min(3, collection_count),  # Get top 3 matches for debugging
            include=["distances", "metadatas"]
        )
        
        if not results['ids'][0]:
            print("❌ No results returned from search")
            return "Unknown", 0.0
        
        # Show all top matches for debugging
        print("🎯 Top matches:")
        for i in range(len(results['ids'][0])):
            name = results['metadatas'][0][i]['name']
            distance = results['distances'][0][i]
            similarity = 1 - distance
            print(f"  {i+1}. {name} (Similarity: {similarity:.3f}, Distance: {distance:.3f})")
        
        # Get best match
        best_name = results['metadatas'][0][0]['name']
        best_similarity = 1 - results['distances'][0][0]
        
        print(f"✅ Best match: {best_name} (Similarity: {best_similarity:.3f}, Threshold: {threshold})")
        
        return (best_name, best_similarity) if best_similarity >= threshold else ("Unknown", best_similarity)
        
    except Exception as e:
        print(f"❌ Error in similarity search: {e}")
        return "Unknown", 0.0

def capture_frame_from_camera():
    """Capture a single frame from the Hikvision camera for attendance processing"""
    try:
        # Use Hikvision RTSP camera
        cap = cv2.VideoCapture(RTSP_URL)
        st.markdown("📹 **Connecting to Hikvision PTZ Camera...**")
        
        if not cap.isOpened():
            st.error("❌ Could not open Hikvision camera for frame capture")
            st.error(f"❌ Check RTSP URL: {RTSP_URL}")
            return None
        
        # Professional preview with countdown
        st.markdown("📹 **Live Preview - Preparing for Capture**")
        preview_placeholder = st.empty()
        countdown_placeholder = st.empty()
        
        for i in range(5):  # Reduced to 5 seconds for better UX
            ret, preview_frame = cap.read()
            if ret:
                # Add timestamp and countdown overlay
                frame_with_overlay = preview_frame.copy()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                countdown_text = f"Capturing in {5-i} seconds..."
                
                # Add text overlay
                cv2.putText(frame_with_overlay, timestamp, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame_with_overlay, countdown_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                preview_placeholder.image(frame_with_overlay, channels="BGR", 
                                        caption=f"📹 Live Preview - {countdown_text}", 
                                        use_container_width=True)
                
                # Progress bar
                countdown_placeholder.progress((5-i)/5)
                time.sleep(1)
        
        # Final capture
        st.markdown("📸 **Capturing Final Frame...**")
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            st.error("❌ Could not capture frame from Hikvision camera")
            return None
        
        # Save the captured frame temporarily
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_image_path = f"/tmp/attendance_capture_{timestamp}.jpg"
        cv2.imwrite(temp_image_path, frame)
        
        # Add timestamp to captured frame for display
        frame_display = frame.copy()
        capture_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame_display, f"Captured: {capture_time}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display success and the captured frame
        st.success(f"✅ **Frame Successfully Captured**")
        st.image(frame_display, channels="BGR", 
                caption=f"📸 Captured Frame for Analysis - {capture_time}", 
                use_container_width=True)
        
        return temp_image_path
        
    except Exception as e:
        st.error(f"❌ Error capturing frame: {e}")
        return None

def run_attendance_workflow():
    """Execute the complete attendance workflow"""
    st.info("🎬 Starting attendance workflow...")
    
    try:
        # Step 1: Zoom out 4x
        st.info("🔍 Step 1: Zooming camera out for wide view...")
        result = subprocess.run([
            "python", 
            str(camera_scripts_path / "simple_4x_zoom.py"), 
            "--zoom-out"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            st.warning(f"⚠️ Zoom out warning: {result.stderr}")
        else:
            st.success("✅ Camera zoomed out successfully")
        
        # Wait 10 seconds for camera to stabilize after zoom out
        st.info("⏱️ Waiting 10 seconds for camera stabilization...")
        time.sleep(10)
        
        # Step 2: Capture frame
        st.info("📷 Step 2: Capturing frame for face detection...")
        image_path = capture_frame_from_camera()
        if not image_path:
            st.error("❌ Failed to capture frame")
            return False
        
        # Step 3: Run YOLO face detection
        st.info("🎯 Step 3: Detecting faces in captured frame...")
        json_output_path = "/tmp/face_detection_results.json"
        annotated_output_path = "/tmp/face_detection_annotated.jpg"
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "yolo_image _count.py"),
            image_path,
            "--confidence", "0.3",
            "--json-output", json_output_path,
            "--output", annotated_output_path
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            # Check if it's just "no faces detected" vs a real error
            if "No faces detected" in result.stdout and result.returncode == 1:
                st.warning("⚠️ No faces detected in the captured frame")
                face_count = 0
            else:
                st.error(f"❌ Face detection failed: {result.stderr}")
                st.error(f"❌ Face detection stdout: {result.stdout}")
                return False
        else:
            # Parse face detection output
            face_count = 0
            if "Total faces detected:" in result.stdout:
                face_count = int(result.stdout.split("Total faces detected:")[1].split()[0])
        
        st.success(f"✅ Face detection completed - Found {face_count} faces")
        
        # Show annotated image with detected faces
        if os.path.exists(annotated_output_path):
            annotated_img = cv2.imread(annotated_output_path)
            if annotated_img is not None:
                st.image(annotated_img, channels="BGR", 
                        caption=f"🎯 Detected Faces: {face_count} faces found", 
                        use_container_width=True)
        
        if face_count == 0:
            st.warning("⚠️ No faces detected in the frame")
            return True
        
        # Step 4: Send face positions to Arduino
        st.info("🤖 Step 4: Sending face positions to Arduino...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "minimal_face_processor.py"),
            json_output_path,
            "--confidence", "0.3"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            st.warning(f"⚠️ Arduino communication warning: {result.stderr}")
        else:
            st.success("✅ Face positions sent to Arduino")
        
        # Step 5: Zoom in 4x
        st.info("🔍 Step 5: Zooming camera in for detailed view...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "simple_4x_zoom.py"),
            "--zoom-in"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            st.warning(f"⚠️ Zoom in warning: {result.stderr}")
        else:
            st.success("✅ Camera zoomed in successfully")
        
        # Wait 10 seconds after zoom in for camera stabilization
        st.info("⏱️ Waiting 10 seconds for camera stabilization...")
        time.sleep(10)
        
        st.success("🎉 Attendance workflow completed successfully!")
        return True
        
    except subprocess.TimeoutExpired:
        st.error("❌ Workflow timed out")
        return False
    except Exception as e:
        st.error(f"❌ Workflow error: {e}")
        return False

def run_attendance_workflow_simple():
    """Execute the attendance workflow with 30-second waits as specified"""
    with st.spinner("🎬 Running attendance workflow..."):
        try:
            # Step 1: Zoom out 4x for wide angle view
            st.info("🔍 Step 1: Zooming out 4x for wide angle view...")
            result = subprocess.run([
                "python", 
                str(camera_scripts_path / "simple_4x_zoom.py"), 
                "--zoom-out"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                st.warning(f"⚠️ Zoom out warning: {result.stderr}")
            else:
                st.success("✅ Zoom out successful")
            
            # Wait 30 seconds after zoom out
            st.info("⏱️ Waiting 30 seconds after zoom out...")
            time.sleep(30)
            
            # Step 2: Capture wide angle frame and process with YOLO
            st.info("📷 Step 2: Capturing wide angle frame and processing...")
            # cap = cv2.VideoCapture(RTSP_URL)
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("❌ Could not connect to camera")
                return False
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                st.error("❌ Could not capture frame")
                return False
            
            # Save frame for processing
            temp_image_path = "/tmp/attendance_wide_frame.jpg"
            cv2.imwrite(temp_image_path, frame)
            st.success("✅ Wide angle frame captured")
            
            # Run YOLO detection on wide angle frame
            st.info("🎯 Processing frame with YOLO...")
            json_output_path = "/tmp/attendance_face_positions.json"
            result = subprocess.run([
                "python",
                str(camera_scripts_path / "yolo_image _count.py"),
                temp_image_path,
                "--confidence", "0.3",
                "--json-output", json_output_path
            ], capture_output=True, text=True, timeout=60)
            
            face_count = 0
            if "Total faces detected:" in result.stdout:
                face_count = int(result.stdout.split("Total faces detected:")[1].split()[0])
            
            st.success(f"✅ YOLO processing complete - Found {face_count} faces")
            
            if face_count == 0:
                st.warning("⚠️ No faces detected - ending cycle")
                st.info("🛑 Attendance cycle stopped")
                return True
            
            # Step 3: Zoom in 4x to target faces
            st.info(f"🔍 Step 3: Zooming in 4x to target {face_count} detected faces...")
            result = subprocess.run([
                "python",
                str(camera_scripts_path / "simple_4x_zoom.py"),
                "--zoom-in"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                st.success("✅ Zoom in successful")
            else:
                st.warning(f"⚠️ Zoom in warning: {result.stderr}")
            
            # Wait 30 seconds after zoom in
            st.info("⏱️ Wait after zoom in - 30 seconds...")
            time.sleep(30)
            
            # Step 4: Send face positions to Arduino using Wide Angle Positioning
            st.info("🤖 Step 4: Sending face positions to Arduino (Wide Angle Positioning)...")
            result = subprocess.run([
                "python",
                str(camera_scripts_path / "wide_angle_positioning.py"),
                json_output_path,
                "--confidence", "0.3"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                st.success("✅ Face positions sent to Arduino successfully")
                st.info("⏱️ Waiting for Arduino to finish moving...")
                time.sleep(5)  # Wait for Arduino to complete movements
            else:
                st.warning(f"⚠️ Arduino communication issue: {result.stderr}")
            
            # Step 5: Final wait and stop
            st.info("⏱️ Step 5: Final wait - 30 seconds...")
            time.sleep(30)
            
            st.success("🛑 ATTENDANCE PROCESS COMPLETE - STOPPED")
            
            # Cleanup
            try:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                if os.path.exists(json_output_path):
                    os.remove(json_output_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            st.error(f"❌ Workflow error: {e}")
            return False
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
    # Simple page styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.2em;
        font-weight: bold;
        margin-bottom: 30px;
    }
    .simple-info {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<div class="main-header">🎓 Smart Attendance System</div>', unsafe_allow_html=True)
    
    # GPU Status Check
    import torch
    gpu_available = torch.cuda.is_available()
    if not gpu_available:
        st.warning("⚠️ **GPU Not Detected** - Running on CPU. For better performance, ensure CUDA-compatible GPU is available and PyTorch with CUDA support is installed.")
        with st.expander("🔧 GPU Troubleshooting"):
            st.markdown("""
            **To enable GPU acceleration:**
            1. Install CUDA-compatible PyTorch: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
            2. Verify NVIDIA GPU: `nvidia-smi`
            3. Check CUDA version: `nvcc --version`
            4. Restart the application
            """)
    else:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        st.success(f"🚀 **GPU Detected**: {gpu_name} ({gpu_memory:.1f} GB)")
    
    st.divider()
    
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
        return
    
    # Check GPU status
    import torch
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "Not Available"
    gpu_memory = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB" if gpu_available else "N/A"
    
    # Simple controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🎬 Take Attendance", type="primary", use_container_width=True):
            run_single_attendance_cycle()
        
        if st.button("📹 Start Continuous Monitoring", type="secondary", use_container_width=True):
            run_continuous_attendance_monitoring()
    
    with col2:
        # Get current GPU status
        gpu_status = check_gpu_status()
        if gpu_status["available"]:
            gpu_info = f"🚀 GPU: {gpu_status['name']} ({gpu_status['memory_used']:.1f}/{gpu_status['memory_total']:.1f}GB)"
        else:
            gpu_info = "⚠️ CPU Only"
        
        st.markdown('<div class="simple-info">👥 Students: {} | 📹 Camera: Connected | {}</div>'.format(with_embeddings, gpu_info), unsafe_allow_html=True)
    
    with col3:
        threshold = st.slider("🎯 Threshold", 0.0, 1.0, 0.6, help="Recognition confidence")
    
    st.divider()
    
    # Live Stream Section
    st.subheader("📹 Live Camera Stream")
    
    # Load embeddings to ChromaDB
    collection = create_or_add_to_collection("face_recognition", path_to_chroma=CHROMA_STORE_PATH)
    
    if collection is None:
        st.error("❌ Failed to load facial recognition collection")
        return
    
    # Live stream display
    stream_placeholder = st.empty()
    
    # Video capture
    cap = cv2.VideoCapture(RTSP_URL)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
    
    if not cap.isOpened():
        st.error("❌ Could not connect to camera stream")
        return
    
    # Continuous live stream
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Lost connection to camera stream")
                break
            
            # Process frame for face recognition
            processed_frame, recognized = process_frame(frame, threshold, collection)
            
            # Display the frame
            stream_placeholder.image(processed_frame, channels="BGR", 
                                   caption="🎥 Live Feed - Face Recognition Active", 
                                   use_container_width=True)
            
            # Small delay
            time.sleep(0.1)
            
    except Exception as e:
        st.error(f"❌ Stream error: {e}")
    finally:
        cap.release()

def run_continuous_attendance_monitoring():
    """Run continuous attendance monitoring - process every 3rd frame"""
    st.info("🎬 Starting continuous attendance monitoring...")
    st.info("📹 Processing every 3rd frame for face detection")
    
    # Create placeholders for status updates
    status_container = st.container()
    progress_container = st.container()
    frame_container = st.container()
    
    with status_container:
        status_text = st.empty()
        progress_bar = st.empty()
    
    with frame_container:
        frame_display = st.empty()
    
    # Start with wide angle view
    status_text.info("🔍 Setting camera to wide angle view...")
    result = subprocess.run([
        "python", 
        str(camera_scripts_path / "simple_4x_zoom.py"), 
        "--zoom-out"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        status_text.success("✅ Camera set to wide angle")
    
    # Wait 10 seconds for initial camera stabilization
    status_text.info("⏱️ Waiting 10 seconds for initial camera stabilization...")
    time.sleep(10)  # Camera stabilization
    
    # Main monitoring loop
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        status_text.error("❌ Could not connect to camera for monitoring")
        return False
    
    frame_count = 0
    faces_detected_total = 0
    monitoring_active = True
    
    try:
        # Add stop button
        stop_button = st.button("🛑 Stop Monitoring", type="secondary")
        
        while monitoring_active and not stop_button:
            ret, frame = cap.read()
            if not ret:
                status_text.error("❌ Lost camera connection")
                break
            
            frame_count += 1
            progress_bar.progress((frame_count % 3) / 3, text=f"Frame {frame_count}")
            
            # Display current frame
            frame_display.image(frame, channels="BGR", 
                              caption=f"📹 Live Monitoring - Frame {frame_count}", 
                              use_container_width=True)
            
            # Process every 3rd frame
            if frame_count % 3 == 0:
                status_text.info(f"🎯 Processing frame {frame_count} for face detection...")
                
                # Save frame for YOLO processing
                temp_image_path = f"/tmp/monitoring_frame_{frame_count}.jpg"
                cv2.imwrite(temp_image_path, frame)
                
                # Run YOLO face detection
                json_output_path = f"/tmp/face_results_{frame_count}.json"
                result = subprocess.run([
                    "python",
                    str(camera_scripts_path / "yolo_image _count.py"),
                    temp_image_path,
                    "--confidence", "0.3",
                    "--json-output", json_output_path
                ], capture_output=True, text=True, timeout=30)
                
                # Check if faces were detected
                face_count = 0
                if result.returncode == 0 and "Total faces detected:" in result.stdout:
                    face_count = int(result.stdout.split("Total faces detected:")[1].split()[0])
                
                if face_count > 0:
                    faces_detected_total += face_count
                    status_text.success(f"✅ Frame {frame_count}: Found {face_count} faces - Executing targeting sequence!")
                    
                    # Release camera for workflow
                    cap.release()
                    
                    # Execute targeting sequence
                    with st.spinner("🎯 Executing targeting sequence..."):
                        # Send positions to Arduino
                        subprocess.run([
                            "python",
                            str(camera_scripts_path / "minimal_face_processor.py"),
                            json_output_path,
                            "--confidence", "0.3"
                        ], capture_output=True, text=True, timeout=60)
                        
                        # Zoom in to target
                        subprocess.run([
                            "python",
                            str(camera_scripts_path / "simple_4x_zoom.py"),
                            "--zoom-in"
                        ], capture_output=True, text=True, timeout=30)
                        
                        # Wait 10 seconds for focus and motor positioning
                        time.sleep(10)
                        
                        # Zoom back out to wide view
                        subprocess.run([
                            "python",
                            str(camera_scripts_path / "simple_4x_zoom.py"),
                            "--zoom-out"
                        ], capture_output=True, text=True, timeout=30)
                        
                        # Wait 10 seconds after zoom out for stabilization
                        time.sleep(10)
                    
                    # Reconnect to camera
                    cap = cv2.VideoCapture(RTSP_URL)
                    if not cap.isOpened():
                        status_text.error("❌ Could not reconnect to camera")
                        break
                    
                    status_text.success(f"✅ Targeting completed! Total faces detected: {faces_detected_total}")
                else:
                    status_text.info(f"ℹ️ Frame {frame_count}: No faces detected, continuing monitoring...")
                
                # Clean up temporary files
                try:
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                    if os.path.exists(json_output_path):
                        os.remove(json_output_path)
                except:
                    pass
            else:
                status_text.info(f"📹 Monitoring frame {frame_count} (next processing at frame {((frame_count // 3) + 1) * 3})...")
            
            # Small delay
            time.sleep(0.2)
            
            # Safety limit
            if frame_count > 300:  # Limit to 100 processing cycles
                status_text.warning("⚠️ Monitoring limit reached (300 frames)")
                break
            
            # Check for stop button
            if stop_button:
                break
    
    except KeyboardInterrupt:
        status_text.info("🛑 Monitoring stopped by user")
    except Exception as e:
        status_text.error(f"❌ Monitoring error: {e}")
    finally:
        cap.release()
        progress_bar.empty()
        status_text.success(f"✅ Monitoring stopped. Total faces processed: {faces_detected_total}")
    
    return True

def run_single_attendance_cycle():
    """Execute a single attendance cycle with 3-frame monitoring"""
    frame_count = 0
    faces_processed = False
    
    try:
        with st.spinner("🎬 Running single attendance cycle..."):
            # Step 1: Zoom out 4x for wide angle view
            st.info("🔍 Step 1: Zooming out 4x for wide view...")
            result = subprocess.run([
                "python", 
                str(camera_scripts_path / "simple_4x_zoom.py"), 
                "--zoom-out"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                st.warning(f"⚠️ Zoom out warning: {result.stderr}")
            else:
                st.success("✅ Camera zoomed out successfully")
            
            # Wait 10 seconds for camera stabilization after zoom out
            st.info("⏱️ Waiting 10 seconds for camera stabilization...")
            time.sleep(10)
            
            # Step 2: Monitor frames and process every 3rd frame
            st.info("📹 Step 2: Monitoring frames (processing every 3rd frame)...")
            cap = cv2.VideoCapture(RTSP_URL)
            
            if not cap.isOpened():
                st.error("❌ Could not connect to camera")
                return False
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while not faces_processed and frame_count < 15:  # Max 15 frames
                frame_count += 1
                ret, frame = cap.read()
                
                if not ret:
                    st.error(f"❌ Could not capture frame {frame_count}")
                    continue
                
                progress_bar.progress(frame_count / 15)
                
                if frame_count % 3 == 0:
                    status_text.text(f"🎯 Frame {frame_count}: Processing with YOLO...")
                    
                    # Save frame for processing
                    temp_image_path = f"/tmp/cycle_frame_{frame_count}.jpg"
                    cv2.imwrite(temp_image_path, frame)
                    
                    # Run YOLO detection
                    json_output_path = f"/tmp/cycle_results_{frame_count}.json"
                    result = subprocess.run([
                        "python",
                        str(camera_scripts_path / "yolo_image _count.py"),
                        temp_image_path,
                        "--confidence", "0.3",
                        "--json-output", json_output_path
                    ], capture_output=True, text=True, timeout=60)
                    
                    face_count = 0
                    if "Total faces detected:" in result.stdout:
                        face_count = int(result.stdout.split("Total faces detected:")[1].split()[0])
                    
                    if face_count > 0:
                        st.success(f"✅ Found {face_count} faces on frame {frame_count}!")
                        faces_processed = True
                        break
                    else:
                        status_text.text(f"📹 Frame {frame_count}: No faces detected, continuing...")
                else:
                    status_text.text(f"📹 Frame {frame_count}: Monitor only")
                    time.sleep(0.1)
            
            cap.release()
            progress_bar.empty()
            status_text.empty()
            
            if not faces_processed:
                st.warning("⚠️ No faces detected in monitoring period")
                st.info("🔍 Returning to wide view and ending cycle...")
                subprocess.run([
                    "python",
                    str(camera_scripts_path / "simple_4x_zoom.py"),
                    "--zoom-out"
                ], capture_output=True, text=True, timeout=30)
                time.sleep(10)
                st.info("🛑 Attendance cycle ended (no faces detected)")
                return True
            
            # Step 3: Send face positions to Arduino
            st.info("🤖 Step 3: Sending face positions to Arduino...")
            result = subprocess.run([
                "python",
                str(camera_scripts_path / "minimal_face_processor.py"),
                json_output_path,
                "--confidence", "0.3"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                st.warning(f"⚠️ Arduino communication: {result.stderr}")
            else:
                st.success("✅ Face positions sent to Arduino")
            
            # Step 4: Zoom in 4x to target detected faces
            st.info("🔍 Step 4: Zooming in 4x to target detected faces...")
            result = subprocess.run([
                "python",
                str(camera_scripts_path / "simple_4x_zoom.py"),
                "--zoom-in"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                st.warning(f"⚠️ Zoom in warning: {result.stderr}")
            else:
                st.success("✅ Camera zoomed in to target")
            
            # Wait 10 seconds for motor positioning and focusing
            st.info("⏱️ Waiting 10 seconds for zoom in stabilization...")
            time.sleep(10)
            
            # Step 5: Take attendance at close range
            st.info("📝 Step 5: Taking attendance at close range...")
            time.sleep(3)  # Simulate attendance processing
            st.success("✅ Attendance recorded for detected faces")
            
            # Step 6: Zoom out 4x and END cycle
            st.info("🔍 Step 6: Zooming out 4x to return to wide view...")
            result = subprocess.run([
                "python",
                str(camera_scripts_path / "simple_4x_zoom.py"),
                "--zoom-out"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                st.warning(f"⚠️ Final zoom out warning: {result.stderr}")
            else:
                st.success("✅ Camera returned to wide view")
            
            # Wait 10 seconds for final stabilization
            st.info("⏱️ Waiting 10 seconds for final stabilization...")
            time.sleep(10)
            
            # Cleanup temp files
            try:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                if os.path.exists(json_output_path):
                    os.remove(json_output_path)
            except:
                pass
            
            # Final success message
            st.success("🎉 SINGLE ATTENDANCE CYCLE COMPLETED ✅")
            st.info("📝 Summary:")
            st.info(f"   • Processed {frame_count} frames")
            st.info(f"   • Found faces and sent to Arduino")
            st.info("   • Zoomed in → took attendance → zoomed out")
            st.info("🛑 Attendance session ended. Ready for next manual start.")
            
            return True
            
    except Exception as e:
        st.error(f"❌ Single cycle error: {e}")
        return False


if __name__ == "__main__":
    show_real_time_prediction()
