import os
import chromadb
import uuid
from PIL import Image
import numpy as np
from pathlib import Path
import sys

# Add local insightface and camera_scripts to path for imports
project_root = Path(__file__).parent
camera_scripts_path = project_root / "camera_scripts"
insightface_path = project_root / "insightface" / "python-package"
sys.path.append(str(camera_scripts_path))
sys.path.insert(0, str(insightface_path))

from src.custom_face_analysis import CustomFaceAnalysis as FaceAnalysis
from src.performance_config import (
    INSIGHTFACE_MODEL, YOLO_MODEL_SIZE, DETECTION_SIZE, 
    CONFIDENCE_THRESHOLD, GPU_MODE
)

# ChromaDB config
CHROMA_STORE_PATH = "./store"
COLLECTION_NAME = "face_recognition"

# Initialize ChromaDB client and collection
client = chromadb.PersistentClient(path=CHROMA_STORE_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

# Initialize face analysis model
MODEL_ROOT = str(project_root)
yolo_path = project_root / "models" / f"yolov11{YOLO_MODEL_SIZE}-face.pt"
app = FaceAnalysis(
    name=INSIGHTFACE_MODEL,
    root=MODEL_ROOT,
    yolo_model_path=str(yolo_path),
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
    gpu_mode=GPU_MODE,
    low_memory=True,
    allowed_modules=['recognition']
)
app.prepare(ctx_id=0, det_size=DETECTION_SIZE, det_thresh=CONFIDENCE_THRESHOLD)

def list_chromadb_data():
    print("Listing all stored faces in ChromaDB:")
    count = collection.count()
    print(f"Total items: {count}")
    if count > 0:
        all_data = collection.get(limit=count)
        for idx, meta in zip(all_data['ids'], all_data['metadatas']):
            print(f"ID: {idx}, Name: {meta.get('name', 'Unknown')}")

def add_images_from_folder(dataset_path):
    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if not os.path.isdir(person_folder):
            continue
        for img_file in os.listdir(person_folder):
            img_path = os.path.join(person_folder, img_file)
            try:
                img = Image.open(img_path).convert('RGB')
                img_array = np.array(img)
                faces = app.get(img_array)
                if not faces:
                    print(f"No face detected in {img_path}")
                    continue
                for face in faces:
                    embedding = face.embedding.tolist()
                    unique_id = f"{person_name}_{img_file}_{uuid.uuid4()}"
                    collection.add(
                        embeddings=[embedding],
                        ids=[unique_id],
                        metadatas=[{"name": person_name}]
                    )
                    print(f"Added {img_path} as {unique_id}")
            except Exception as e:
                print(f"Failed to process {img_path}: {e}")

if __name__ == "__main__":
    # 1. List current data
    list_chromadb_data()
    # # 2. Add new images (set your dataset path)
    # dataset_path = "/home/invisa/Desktop/working_grad/images_for_chroma"  # Folder structure: dataset/person_name/image.jpg
    # add_images_from_folder(dataset_path)
    # list_chromadb_data()