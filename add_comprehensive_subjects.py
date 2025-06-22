#!/usr/bin/env python3
"""
Add More Subjects for Each Department and Year
This script adds a comprehensive curriculum for each department across all years.
"""

import sqlite3

DATABASE_PATH = 'attendance_system.db'

def add_comprehensive_subjects():
    """Add a full curriculum for each department and year"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("📚 Adding Comprehensive Subject Curriculum")
    print("=" * 50)
    
    # Computer Science Curriculum
    cs_subjects = {
        1: [  # Year 1
            ("Programming Fundamentals", "CS101", "Introduction to programming concepts"),
            ("Mathematics for CS", "CS102", "Mathematical foundations for computer science"),
            ("Computer Systems", "CS103", "Basic computer architecture and systems"),
            ("Data Structures", "CS104", "Basic data structures and algorithms"),
            ("Discrete Mathematics", "CS105", "Mathematical structures for computer science"),
            ("English Communication", "CS106", "Technical writing and communication")
        ],
        2: [  # Year 2
            ("Object-Oriented Programming", "CS201", "Advanced programming with OOP"),
            ("Database Systems", "CS202", "Database design and SQL"),
            ("Computer Networks", "CS203", "Network protocols and architecture"),
            ("Operating Systems", "CS204", "OS concepts and implementation"),
            ("Algorithms Analysis", "CS205", "Algorithm design and complexity"),
            ("Software Engineering", "CS206", "Software development methodologies")
        ],
        3: [  # Year 3
            ("Web Development", "CS301", "Full-stack web application development"),
            ("Mobile App Development", "CS302", "iOS and Android development"),
            ("Computer Graphics", "CS303", "2D and 3D graphics programming"),
            ("Distributed Systems", "CS304", "Distributed computing concepts"),
            ("Computer Security", "CS305", "Cybersecurity fundamentals"),
            ("Senior Project I", "CS306", "Capstone project development")
        ]
    }
    
    # Artificial Intelligence Curriculum
    ai_subjects = {
        1: [  # Year 1
            ("AI Fundamentals", "AI101", "Introduction to artificial intelligence"),
            ("Python Programming", "AI102", "Python for AI and data science"),
            ("Statistics for AI", "AI103", "Statistical methods for AI"),
            ("Linear Algebra", "AI104", "Mathematical foundations for AI"),
            ("Logic and Reasoning", "AI105", "Formal logic and AI reasoning"),
            ("Data Visualization", "AI106", "Data analysis and visualization")
        ],
        2: [  # Year 2
            ("Machine Learning", "AI201", "Supervised and unsupervised learning"),
            ("Deep Learning", "AI202", "Neural networks and deep learning"),
            ("Natural Language Processing", "AI203", "Text processing and NLP"),
            ("Computer Vision", "AI204", "Image processing and computer vision"),
            ("Data Mining", "AI205", "Knowledge discovery in databases"),
            ("AI Ethics", "AI206", "Ethical considerations in AI")
        ],
        3: [  # Year 3
            ("Advanced ML", "AI301", "Advanced machine learning techniques"),
            ("Robotics", "AI302", "AI applications in robotics"),
            ("Expert Systems", "AI303", "Knowledge-based AI systems"),
            ("AI Project Management", "AI304", "Managing AI development projects"),
            ("Research Methods", "AI305", "AI research methodology"),
            ("AI Capstone", "AI306", "Advanced AI project development")
        ]
    }
    
    # Information Systems Curriculum
    is_subjects = {
        1: [  # Year 1
            ("Business Analysis", "IS101", "Business systems analysis"),
            ("Information Systems Fundamentals", "IS102", "Introduction to IS"),
            ("Database Design", "IS103", "Database modeling and design"),
            ("Systems Analysis", "IS104", "Requirements analysis and design"),
            ("Business Process Management", "IS105", "Process modeling and optimization"),
            ("IT Project Management", "IS106", "Managing IT projects")
        ]
    }
    
    # Information Technology Curriculum
    it_subjects = {
        1: [  # Year 1
            ("IT Fundamentals", "IT101", "Introduction to information technology"),
            ("Network Administration", "IT102", "Network setup and management"),
            ("System Administration", "IT103", "Server and system management"),
            ("IT Support", "IT104", "Technical support and troubleshooting"),
            ("Cloud Computing", "IT105", "Cloud services and deployment"),
            ("IT Security", "IT106", "Information security practices")
        ]
    }
    
    # Software Engineering Curriculum
    se_subjects = {
        1: [  # Year 1
            ("Software Development", "SE101", "Software development methodologies"),
            ("Requirements Engineering", "SE102", "Software requirements analysis"),
            ("Software Design", "SE103", "Software architecture and design"),
            ("Quality Assurance", "SE104", "Software testing and QA"),
            ("Version Control", "SE105", "Git and software versioning"),
            ("Agile Development", "SE106", "Agile and Scrum methodologies")
        ]
    }
    
    # Cybersecurity Curriculum
    cy_subjects = {
        1: [  # Year 1
            ("Network Security", "CY101", "Network security fundamentals"),
            ("Ethical Hacking", "CY102", "Penetration testing basics"),
            ("Cryptography", "CY103", "Encryption and cryptographic methods"),
            ("Security Policies", "CY104", "Information security policies"),
            ("Incident Response", "CY105", "Security incident management"),
            ("Digital Forensics", "CY106", "Digital evidence and forensics")
        ]
    }
    
    # Department mapping
    curricula = {
        1: cs_subjects,  # Computer Science
        2: ai_subjects,  # Artificial Intelligence
        3: is_subjects,  # Information Systems
        4: it_subjects,  # Information Technology
        5: se_subjects,  # Software Engineering
        6: cy_subjects   # Cybersecurity
    }
    
    # Clear existing subjects (keep only the original ones as templates)
    print("Clearing existing subjects (keeping templates)...")
    cursor.execute("DELETE FROM subjects_enhanced WHERE subject_id > 10")
    conn.commit()
    
    subjects_added = 0
    
    for dept_id, dept_curriculum in curricula.items():
        # Get department name
        cursor.execute("SELECT department_name FROM departments WHERE department_id = ?", (dept_id,))
        dept_result = cursor.fetchone()
        dept_name = dept_result[0] if dept_result else f"Department {dept_id}"
        
        print(f"\n📖 Adding subjects for {dept_name}")
        
        for year, subjects in dept_curriculum.items():
            print(f"  Year {year}: {len(subjects)} subjects")
            
            for subject_name, course_code, description in subjects:
                try:
                    cursor.execute("""
                        INSERT INTO subjects_enhanced 
                        (subject_name, course_code, credit_hours, department_id, academic_year, semester, description)
                        VALUES (?, ?, 3, ?, ?, 1, ?)
                    """, (subject_name, course_code, dept_id, year, description))
                    subjects_added += 1
                except sqlite3.IntegrityError:
                    # If course_code already exists, use INSERT OR IGNORE
                    cursor.execute("""
                        INSERT OR IGNORE INTO subjects_enhanced 
                        (subject_name, course_code, credit_hours, department_id, academic_year, semester, description)
                        VALUES (?, ?, 3, ?, ?, 1, ?)
                    """, (subject_name, f"{course_code}_{dept_id}_{year}", dept_id, year, description))
                    subjects_added += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Added {subjects_added} subjects across all departments and years")
    return subjects_added

def verify_subjects():
    """Verify the subjects were added correctly"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            d.department_name,
            s.academic_year,
            COUNT(*) as subject_count
        FROM subjects_enhanced s
        JOIN departments d ON s.department_id = d.department_id
        GROUP BY d.department_name, s.academic_year
        ORDER BY d.department_name, s.academic_year
    """)
    
    results = cursor.fetchall()
    
    print("\n📊 Subject Distribution by Department & Year:")
    print("-" * 45)
    total_subjects = 0
    for dept, year, count in results:
        print(f"{dept:>20} Year {year}: {count:>2} subjects")
        total_subjects += count
    
    print("-" * 45)
    print(f"{'Total Subjects:':>20} {total_subjects:>2}")
    
    conn.close()
    return total_subjects

if __name__ == "__main__":
    # Add comprehensive subjects
    added = add_comprehensive_subjects()
    
    # Verify the additions
    total = verify_subjects()
    
    print(f"\n🎉 SUCCESS: Added {added} new subjects!")
    print(f"📚 Total subjects in curriculum: {total}")
    print("\nNow you can regenerate schedules for the complete curriculum.")
