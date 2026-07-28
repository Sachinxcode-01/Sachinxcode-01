# Walkthrough - Mobile Face Upload & AI Training Feature

We have implemented a fully functional feature that allows class teachers to capture or upload student face photos directly from the mobile app, automatically organize them in the server's training dataset, and trigger the AI model training process in the background.

## System Workflow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Teacher as Class Teacher (Mobile App)
    participant API as FastAPI Backend (main.py)
    participant Storage as File Storage (data/dataset/)
    participant AI as ArcFace Training (train_faces.py)
    actor Student as Student
    participant Camera as Attendance System Camera Feed

    Note over Teacher, API: 1. Student Onboarding & Upload
    Teacher->>API: GET /auth/students (fetch student list)
    API-->>Teacher: Return students (name, email, ID)
    Teacher->>Teacher: Capture or pick student photo
    Teacher->>API: POST /auth/upload-student-face (image, student_email)
    API->>API: Retrieve student details from Database
    API->>Storage: Save image to data/dataset/<Name>_<Roll>/
    API-->>Teacher: Upload success response

    Note over Teacher, AI: 2. AI Model Re-Training
    Teacher->>API: POST /auth/train-faces
    API->>API: Spawn background task run_training()
    API-->>Teacher: Immediate success response (non-blocking)
    loop ArcFace Vector Extraction
        API->>AI: Extract facial embeddings for all folders
        AI->>AI: Recompile embeddings & labels
        AI->>Storage: Save updated face_encodings_arcface.pkl
    end

    Note over Student, Camera: 3. Real-Time Verification
    Student->>Camera: Stand in front of scanning camera
    Camera->>Camera: Detect face & extract vector
    Camera->>Storage: Load face_encodings_arcface.pkl (dynamic detection)
    Camera->>Camera: Compute cosine similarity
    alt Recognition Match >= Threshold (0.6)
        Camera->>API: POST /attendance/mark/face (student_email, confidence)
        API->>API: Mark student present in DB & Google Sheets
        Camera->>Camera: Greet student audibly ("Welcome Alice!")
    else Unrecognized Individual
        Camera->>Camera: Trigger local alarm beeps
        Camera->>API: POST /security/intruder-alert (image, location)
        API->>API: Save security log & notify admin (Email & push notification)
    end
```

## Changes Made

### 1. Refactored Face Training Script (`core/train_faces.py`)
- Wrapped the ArcFace training loop into a programmatically callable function: `def run_training() -> bool`.
- Kept the command-line execution (`python core/train_faces.py`) fully working via `if __name__ == "__main__":` for backwards compatibility.

### 2. Implemented Backend Endpoints (`smartface_pro_api/main.py`)
- **`GET /auth/students`**: Retrieves a list of all registered student names, emails, and student IDs for search dropdown options.
- **`POST /auth/upload-student-face`**:
  - Validates if the student exists in the database.
  - Generates the standardized dataset directory structure: `data/dataset/<Name>_<Roll>/`.
  - Validates and saves the uploaded image.
- **`POST /auth/train-faces`**: Triggers the refactored `run_training()` function inside a FastAPI `BackgroundTasks` thread, ensuring the server handles training concurrently without blocking routes.

### 3. Integrated Mobile API Calls (`smartface_mobile/lib/services/api_service.dart`)
- Added `getStudents(token)` helper to retrieve the list of students.
- Added `uploadStudentFace(email, imageFile, token)` using multipart request payload.
- Added `triggerTrainFaces(token)` helper.

### 4. Created Mobile Face Training Screen (`smartface_mobile/lib/screens/teacher/train_faces_screen.dart`)
- **Student Picker**: Search autocomplete input that searches student names and IDs in real-time.
- **Camera/Gallery picker**: Custom image capture zone with preview frame supporting snapshots or photo selection.
- **Trigger Actions**:
  - Tap **UPLOAD FACE PHOTO** to save the image to the student's dataset.
  - Tap **RE-TRAIN NEURAL ENGINE** to trigger programmatic ArcFace vector training.
- Matches the premium dark navy and gold glassmorphic theme.

### 5. Registered Routing & Dashboard Tiles
- Registered the new screen route `'/train-faces'` in `main.dart`.
- Added the **Train AI Faces** grid tile on the `TeacherDashboard` linking to the screen.

## Verification Results

### Backend
- All endpoints compile and execute cleanly with no syntax errors.

### Mobile Client
- Flutter build/analysis validated cleanly. All modifications compile without compile errors.
