# attendance-cv

attendance-cv is a face-recognition attendance system. A webcam feed
runs through InsightFace + YOLO, faces are matched against a ChromaDB
of enrolled students, and attendance is marked automatically. The
Streamlit UI exposes role-based dashboards for admins, teachers, and
students.

Originally built as my graduation project. Runs as a single Streamlit
process on CPU, or as a GPU-enabled Docker container.

## Install

```bash
git clone https://github.com/moamen1358/attendance-cv.git
cd attendance-cv

pip install -r requirements.txt
python src/db_init.py
streamlit run src/app.py
```

`db_init.py` seeds the database with sample students, teachers,
subjects, and schedules so the dashboards work on first login. Open
`http://localhost:8501`.

For the GPU Docker setup, see
[docs/architecture.md](docs/architecture.md#docker-gpu).

## Default credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin` |
| Teacher | `emp2024001` | `emp2024001` |
| Student | `2024001` | `2024001` |

Two more sample teachers (`emp2024002`, `emp2024003`) and students
(`2024002`, `2024003`) are seeded with the same pattern.

## What each role can do

- **Admins** manage users, departments, subjects, and teacher-to-subject
  assignments; review system-wide attendance and session logs.
- **Teachers** view assigned subjects, run live attendance sessions
  (camera + recognition), and generate per-class or per-student reports.
- **Students** enroll their face once, then check personal attendance
  history and upcoming class schedules.

## Deeper reference

- [docs/architecture.md](docs/architecture.md) — stack, database
  schema, file layout, scheduling logic, configuration, GPU Docker
- [METHODOLOGY.md](METHODOLOGY.md) — recognition approach, model
  selection, evaluation metrics

## License

MIT.
