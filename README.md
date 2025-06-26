# 🎓 Smart Attendance Management System

A modern, AI-powered attendance management system using face recognition technology, built with Streamlit and featuring comprehensive analytics and reporting capabilities.

## 🌟 Key Features

### 🔍 Face Recognition & AI
- **Real-time face detection** using InsightFace and YOLO models
- **ChromaDB vector database** for efficient face embedding storage and retrieval
- **High-accuracy face recognition** with confidence scoring
- **Multi-face detection** in group settings
- **Automatic attendance marking** based on face recognition

### 👨‍🏫 User Management & Roles
- **Role-based access control** (Admin, Teacher, Student)
- **Secure authentication** with password hashing
- **Session persistence** and management
- **User profile management** with face enrollment

### 📊 Comprehensive Analytics
- **Real-time attendance tracking** with live camera feed
- **Interactive dashboards** for all user roles
- **Advanced reporting** with customizable date ranges
- **Visual analytics** with charts and graphs
- **Attendance statistics** and trends analysis

### 🏫 Academic Management
- **Department management**
- **Subject and course management**
- **Class scheduling** with time slots
- **Teacher-subject assignments**
- **Student enrollment** management
- **Academic year and semester tracking**

## 🛠️ Technology Stack

### Backend
- **Python 3.10+** - Core programming language
- **SQLite** - Primary database for structured data
- **ChromaDB** - Vector database for face embeddings
- **Streamlit** - Web application framework

### AI & Computer Vision
- **InsightFace** - Face recognition and analysis
- **YOLO** - Object detection for face counting
- **OpenCV** - Computer vision operations
- **NumPy** - Numerical computing

### Frontend
- **Streamlit** - Interactive web interface
- **Plotly** - Data visualization
- **Pandas** - Data manipulation and analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Webcam/Camera access
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd my_grad_streamlit_last
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python src/db_init.py
   ```

4. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

5. **Access the application**
   - Open your browser to `http://localhost:8501`
   - Use the default credentials below to get started

### 🔐 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin` |
| Teacher | `professor` | `professor` |
| Student | `student` | `student` |

## 📋 System Architecture

### Database Schema
The system uses a normalized SQLite database with the following core tables:

#### Core Tables
- **`students_enhanced`** - Student information and profiles
- **`teachers_enhanced`** - Teacher information and credentials
- **`subjects_enhanced`** - Course and subject definitions
- **`departments`** - Academic department management
- **`users_enhanced`** - Authentication and user management

#### Relationship Tables
- **`teacher_subjects_enhanced`** - Teacher-subject assignments
- **`student_enrollments_enhanced`** - Student course enrollments
- **`class_schedules_enhanced`** - Class timing and scheduling

#### Attendance & Recognition
- **`attendance_records_enhanced`** - Attendance tracking records
- **`attendance_sessions_enhanced`** - Class session management
- **`student_profiles_enhanced`** - Face recognition profiles and embeddings

### File Structure
```
my_grad_streamlit_last/
├── src/
│   ├── app.py                          # Main application entry point
│   ├── db_init.py                      # Database initialization
│   ├── admin_dashboard.py              # Admin interface
│   ├── student_dashboard.py            # Student interface
│   ├── real_time_prediction.py         # Face recognition engine
│   ├── registration_form.py            # User registration
│   ├── login.py                        # Authentication
│   ├── security.py                     # Security utilities
│   └── report.py                       # Reporting system
├── data_frames/                        # Data storage
├── insightface_model/                  # AI models
├── store/                              # ChromaDB storage
├── migrations/                         # Database migrations
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## 🎯 Usage Guide

### For Administrators
1. **Login** with admin credentials
2. **Manage users** - Add/edit teachers and students
3. **Setup departments** and subjects
4. **Assign teachers** to subjects
5. **Monitor system** performance and attendance

### For Teachers
1. **Login** with teacher credentials
2. **View assigned subjects** and classes
3. **Start attendance sessions** with live camera
4. **Generate reports** for classes and students
5. **Manage class schedules**

### For Students
1. **Login** with student credentials
2. **Enroll face profile** for recognition
3. **View attendance** records and statistics
4. **Check class schedules**
5. **Monitor academic progress**

## 📈 Features in Detail

### Face Recognition System
- **High-accuracy detection** using InsightFace models
- **Real-time processing** with live camera feed
- **Multiple face detection** in classroom settings
- **Confidence scoring** for recognition accuracy
- **Automatic attendance marking** based on recognition

### Reporting & Analytics
- **Comprehensive reports** with filtering options
- **Attendance statistics** and trend analysis
- **Export capabilities** for data sharing
- **Visual dashboards** with interactive charts
- **Academic performance tracking**

### Security Features
- **Password hashing** with secure algorithms
- **Session management** with timeout protection
- **Role-based access control**
- **Data encryption** for sensitive information
- **Audit logging** for system activities

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_PATH=attendance_system.db
CHROMADB_PATH=./store
MODEL_PATH=./insightface_model
```

### Camera Configuration
- Ensure camera access permissions are granted
- Test camera functionality before first use
- Adjust lighting conditions for optimal face recognition

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email [your-email@example.com] or create an issue in the repository.

## 🙏 Acknowledgments

- **InsightFace** team for face recognition models
- **Streamlit** community for the amazing framework
- **ChromaDB** for vector database capabilities
- **OpenCV** for computer vision tools
