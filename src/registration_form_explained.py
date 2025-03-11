"""
This file explains the student registration process step by step.
It's a documentation file, not meant to be executed.
"""

'''
STEP 1: STUDENT INFORMATION COLLECTION
---------------------------------------
In the show_registration_form() function, we collect:
- Student name
- Section (though currently not explicitly collected in the UI)
- Face images (via camera or upload)
'''

def show_registration_form():
    st.header("Registration Form")
    name = st.text_input("Name", key="reg_name")  # Get student name
    
    # Collect face images (via upload or camera)
    # ...

'''
STEP 2: FACE EXTRACTION AND EMBEDDING GENERATION
-----------------------------------------------
When registering a face image through register_face_from_image():
1. The InsightFace model analyzes the image to detect faces
2. If a face is found, its embedding (facial features) is extracted
3. This embedding is a numerical representation of facial features
4. The embedding is normalized and converted to JSON for storage
'''

def register_face_from_image(image, name):
    """Register face from a given image"""
    try:
        faces = app.get(image)  # Face detection with InsightFace
        if not faces:
            return False
            
        # Extract facial embedding features
        embedding = faces[0].embedding
        normalized_embedding = embedding / np.linalg.norm(embedding)
        embedding_str = json.dumps(normalized_embedding.tolist())
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # STORE EMBEDDING: Into facial_recognition_data table
        cursor.execute('''
            INSERT INTO facial_recognition_data (name, facial_features)
            VALUES (?, ?)
        ''', (name, embedding_str))

        # STORE STUDENT: Check if student exists and add if not
        existing_name = cursor.execute('''
            SELECT name FROM student_profiles WHERE name = ?
        ''', (name,)).fetchone()
        
        if existing_name is None:
            cursor.execute('''
                INSERT INTO student_profiles (name)
                VALUES (?)
            ''', (name,))
        
        conn.commit()
        return True
    except Exception as e:
        # Error handling
        return False
    finally:
        if 'conn' in locals():
            conn.close()

'''
STEP 3: USER ACCOUNT CREATION
----------------------------
The register_student() function:
1. Adds the student to the student_profiles table with section info
2. Creates a user account in the user_accounts table
3. Generates a password in the format name_sec#
4. Saves the password as an MD5 hash for security
'''

def register_student(name, image, section=None):
    # Save to database
    try:
        # Add student information
        cursor.execute(
            "INSERT INTO student_profiles (name, section) VALUES (?, ?)",
            (name, section)
        )
        
        # Create user account
        default_password = generate_default_password(name, section)
        hashed_password = hashlib.md5(default_password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, 'student')",
            (name, hashed_password)
        )
        
        # ...rest of function...
    except Exception as e:
        # Error handling
        pass

'''
STEP 4: REAL-TIME RECOGNITION INTEGRATION
----------------------------------------
Later, when using facial recognition:
1. The system loads embeddings from the facial_recognition_data table
2. These are compared with faces detected by the camera
3. The matching name is used to log attendance
'''

# This happens in real_time_prediction.py:
def create_or_add_to_collection(collection_name, path_to_chroma="./store"):
    # ...
    # Retrieve data from the SQLite database
    cursor.execute("SELECT name, facial_features FROM facial_recognition_data")
    rows = cursor.fetchall()
    
    # Add data to the collection for facial recognition
    for index, row in enumerate(rows):
        name, embedding_str = row
        embedding = json.loads(embedding_str)
        collection.add(
            ids=[str(uuid.uuid4())],  # Generate a unique ID for each entry
            documents=[name],
            embeddings=[embedding],
            metadatas=[{"name": name}],
        )
