# Assignment Management System

This is a web application built using Flask for managing assignments, rubrics, and submissions, designed for teachers and students. The application allows users to upload, manage, and download assignments and related documents. It also integrates with OpenAI’s API, and stores user and assignment data in an SQLite database.

## Features

- **User Authentication**: Role-based access with `teacher` and `student` roles.
- **File Upload**: Teachers can upload assignments and rubrics in PDF format, and students can upload submissions.
- **File Storage**: Uploaded files are stored in designated folders for assignments, rubrics, and submissions.
- **OpenAI Integration**: Utilizes OpenAI's API for enhanced functionality (exact purpose needs clarification).
- **Database**: Uses SQLite for storing user credentials, roles, and assignment details.

## Prerequisites

- **Python** 3.7+
- **Flask** and **Flask-SQLAlchemy**
- **PyPDF2** for PDF handling
- **OpenAI API Key** (stored in `.env` file)
- **dotenv** for loading environment variables

Install all required packages:
```bash
pip install -r requirements.txt
```

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Environment Variables**:
   Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Database Setup**:
   Initialize the SQLite database:
   ```bash
   python
   >>> from app import db
   >>> db.create_all()
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   Access the application at `http://127.0.0.1:5000`.

## Folder Structure

- `uploads/assignments`: Stores uploaded assignments.
- `uploads/rubrics`: Stores uploaded rubrics.
- `uploads/submissions`: Stores student submissions.
- `uploads/feedbacks`: Stores feedback files.

## Key Endpoints

- **/register**: Register a new user (teacher or student).
- **/login**: Login to the application.
- **/upload-assignment**: Upload an assignment (teachers only).
- **/upload-submission**: Upload a submission (students only).

## Security

- The app uses `werkzeug` for password hashing and session management.
- Environment variables (like API keys) are loaded securely from `.env`.
