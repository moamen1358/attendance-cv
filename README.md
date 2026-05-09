# attendance-cv

attendance-cv is a face-recognition attendance management system. It runs
real-time face detection on a webcam feed, matches faces against an
enrolled student database stored in ChromaDB, marks attendance
automatically, and exposes role-based dashboards for administrators,
teachers, and students. Originally built as my graduation project.

The system pairs InsightFace and YOLO for detection and recognition
with a Streamlit web interface, a SQLite operational database, and
Plotly-driven analytics. It can be deployed as a single Streamlit
process or as a GPU-enabled Docker container.

## Stack

- **Python 3.10+** for application logic
- **InsightFace** for face detection and embeddings
- **YOLO** for crowd-aware face counting
- **OpenCV** for camera capture and frame processing
- **ChromaDB** for vector storage and similarity search over face embeddings
- **SQLite** for operational data (users, schedules, attendance records)
- **Streamlit** for the web UI
- **Plotly** and **Pandas** for analytics and reporting

## Requirements

- Python 3.10 or newer
- A webcam (or `/dev/video0` device for Docker)
- Optional: NVIDIA GPU with CUDA 12.x for the GPU container

## Installation

```bash
git clone https://github.com/moamen1358/attendance-cv.git
cd attendance-cv

pip install -r requirements.txt
python src/db_init.py
streamlit run src/app.py
```

`db_init.py` populates the database with sample students, teachers,
subjects, schedules, enrollments, and default user accounts so the
application is usable immediately.

Open `http://localhost:8501` and sign in with one of the default
accounts below.

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

## Default credentials

| Role | Username | Password | Notes |
|---|---|---|---|
| Admin | `admin` | `admin` | Full system access |
| Teacher | `emp2024001` | `emp2024001` | Sample teacher account |
| Teacher | `emp2024002` | `emp2024002` | Sample teacher account |
| Teacher | `emp2024003` | `emp2024003` | Sample teacher account |
| Student | `2024001` | `2024001` | Fatma Khaled Ibrahim — Section B |
| Student | `2024002` | `2024002` | Ahmed Mohamed Ali — Section A |
| Student | `2024003` | `2024003` | Sara Hassan Ahmed — Section A |

All sample accounts come with pre-configured schedules and
enrollments so the dashboards are populated on first login.

## Usage by role

**Administrators** manage users, departments, subjects, and
teacher-to-subject assignments; monitor system-wide attendance
metrics; and review session logs.

**Teachers** view their assigned subjects, start attendance sessions
that activate the camera and run live recognition, and generate
per-class or per-student reports.

**Students** enroll their face profile (a one-time capture step), view
their personal attendance history, and check upcoming class schedules.

## Architecture

The application is split into a Streamlit front-end (`src/app.py`),
domain modules under `src/`, and the recognition pipeline that wraps
InsightFace embeddings into ChromaDB queries.

### Database schema (SQLite)

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

### File layout

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

### Scheduling

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

## Methodology

A longer write-up of the recognition approach, model selection, and
evaluation metrics lives in [METHODOLOGY.md](METHODOLOGY.md).

## License

MIT.
