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
from pathlib import Path

# Add camera_scripts to path for imports
camera_scripts_path = Path(__file__).parent.parent / "camera_scripts"
sys.path.append(str(camera_scripts_path))

# Add local insightface to path BEFORE importing
insightface_path = Path(__file__).parent.parent / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

# Import our custom FaceAnalysis with YOLO integration
from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis

MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Project root directory
MODEL_NAME = 'buffalo_sc'

DETECTION_SIZE = (640, 640)
RTSP_URL = "rtsp://admin:Admin%40123@192.168.1.64:554/Streaming/Channels/101"
CHROMA_STORE_PATH = "./store"
DATABASE_PATH = 'attendance_system.db'

# Initialize face analysis model
try:
    yolo_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov11n-face.pt")
    app = FaceAnalysis(
        name=MODEL_NAME, 
        root=MODEL_ROOT, 
        yolo_model_path=yolo_path,
        providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
        gpu_mode='HYBRID'
    )
    app.prepare(ctx_id=0, det_size=DETECTION_SIZE)
except Exception as e:
    st.error(f"Failed to initialize face analysis model: {str(e)}")
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

def show_real_time_prediction():
    st.header("Real-Time Face Recognition")
    
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
        st.error("❌ No facial embeddings found! Please register some faces first.")
        return
    
    # Load embeddings to ChromaDB
    collection = create_or_add_to_collection("face_recognition", path_to_chroma=CHROMA_STORE_PATH)
    
    if collection is None:
        st.error("❌ Failed to load facial recognition collection")
        return
    
    # Check collection contents
    try:
        collection_count = collection.count()
        # Silently count faces without displaying message
    except Exception as e:
        st.error(f"❌ Error checking collection: {e}")
        return
    
    threshold = st.slider("Recognition Threshold", 0.0, 1.0, 0.6)
    st.info(f"🎯 Recognition threshold set to: {threshold}")
    
    # Video capture with hic camera
    # cap = cv2.VideoCapture(RTSP_URL)
    # laptop camera
    cap = cv2.VideoCapture(0)
    # video_path = '/home/invisa/Desktop/my_grad_streamlit/sisi.mp4'
    # cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    if not cap.isOpened():
        st.error("Error: Could not open video stream. Please check the camera connection.")
        return  # Exit the function if the camera connection fails

    stframe = st.empty()
    
    # Add recognition stats
    recognition_stats = st.empty()
    
    frame_count = 0
    recognition_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Error: Could not read frame from stream. Please check the camera connection.")
            break
        
        try:
            frame_count += 1
            # time.sleep(5)
            processed_frame, recognized = process_frame(frame, threshold, collection)
            if recognized:
                recognition_count += 1
            
            stframe.image(processed_frame, channels="BGR", use_container_width=True)
            
            # Update stats every 30 frames
            if frame_count % 30 == 0:
                recognition_stats.info(f"📊 Frames processed: {frame_count} | Recognitions: {recognition_count}")
            
        except Exception as e:
            st.error(f"Error processing frame: {str(e)}")
            break

    cap.release()


if __name__ == "__main__":
    show_real_time_prediction()
