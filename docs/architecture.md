# attendance-cv architecture

The application is split into a Streamlit front-end (`src/app.py`),
domain modules under `src/`, and the recognition pipeline that wraps
InsightFace embeddings into ChromaDB queries.

## Stack

- **Python 3.10+** for application logic
- **InsightFace** for face detection and embeddings
- **YOLO** for crowd-aware face counting
- **OpenCV** for camera capture and frame processing
- **ChromaDB** for vector storage and similarity search over face embeddings
- **SQLite** for operational data (users, schedules, attendance records)
- **Streamlit** for the web UI
- **Plotly** and **Pandas** for analytics and reporting

## Database schema (SQLite)

Core entities:

- `students_enhanced` — student profiles
- `teachers_enhanced` — teacher accounts
- `subjects_enhanced` — course definitions
- `departments` — academic department records
- `users_enhanced` — authentication

Relationships:

- `teacher_subjects_enhanced` — teacher-to-subject assignments
- `student_enrollments_enhanced` — student-to-section enrollments
- `class_schedules_enhanced` — daily timetables
- `sections` — section/group management

Attendance and recognition:

- `attendance_records_enhanced` — per-event attendance entries
- `attendance_sessions_enhanced` — class session tracking
- `student_profiles_enhanced` — face embedding references into ChromaDB

## File layout

```
attendance-cv/
├── src/
│   ├── app.py                          # Streamlit entry point
│   ├── db_init.py                      # Database bootstrap with sample data
│   ├── admin_dashboard.py
│   ├── student_dashboard.py
│   ├── real_time_prediction.py         # Face recognition pipeline
│   ├── registration_form.py
│   ├── login.py
│   ├── security.py                     # Password hashing, session helpers
│   └── report.py
├── data_frames/                        # Pickled DataFrames used at runtime
├── insightface_model/                  # InsightFace weights (created on first run)
├── store/                              # ChromaDB storage (created on first run)
├── migrations/                         # SQL migration scripts
├── server_api/                         # Optional REST endpoints
├── camera_scripts/                     # Camera utilities
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── run_app.sh
├── run_gpu.sh
└── METHODOLOGY.md                      # Project methodology and rationale
```

## Scheduling

Each student is assigned 2-3 subjects per day across 8:00-16:00 time
slots. Sections (A, B, C, …) are balanced across departments and
teachers; conflicts in timetables are resolved at insertion time. The
`db_init.py` script generates a representative dataset for sample
operation.

## Configuration

Create a `.env` file in the project root:

```env
DATABASE_PATH=attendance_system.db
CHROMADB_PATH=./store
MODEL_PATH=./insightface_model
```

For camera setup, ensure read access to `/dev/video0` (or the
appropriate device) and that lighting is sufficient for the
InsightFace detector.

## Docker (GPU)

Build the image first, then run:

```bash
docker build -t attendance-cv:gpu .

docker run --rm -it --name attendance_cv \
  -p 8501:8501 \
  -v "$(pwd)/store:/app/store" \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/data_frames:/app/data_frames" \
  --device /dev/video0:/dev/video0 \
  --gpus all \
  -e PYTHONUNBUFFERED=1 \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  --shm-size=4gb \
  attendance-cv:gpu /app/start_gpu.sh
```
