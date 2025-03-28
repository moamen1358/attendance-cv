# Attendance Management System

A streamlined system for tracking and managing student attendance with face recognition capabilities and comprehensive reporting.

## Features

- **Real-time attendance tracking** with webcam integration
- **Comprehensive reporting** for professors and administrators
- **Student dashboard** showing personal attendance statistics
- **Course management** for professors and administrators
- **User management** with role-based access control
- **Data visualization** with interactive charts and graphs

## Getting Started

### Prerequisites

- Python 3.8+
- Streamlit
- SQLite3
- Required Python packages (see requirements.txt)

### Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run src/app.py
   ```

### Default Credentials

- Admin: username `admin`, password `admin`
- Demo Professor: username `professor`, password `professor`
- Demo Student: username `student`, password `student`

## Architecture

The application follows a modular architecture with these key components:

- `src/app.py`: Main application entry point
- `src/database_maintenance.py`: Database schema and data maintenance
- `src/database_utils.py`: Core database operations
- `src/security.py`: Authentication and authorization
- `src/db_pool.py`: Database connection pooling
- `src/student_visualization.py`: Data visualization components
- `migrations/`: Database schema migration scripts

## License

This project is licensed under the MIT License - see the LICENSE file for details.