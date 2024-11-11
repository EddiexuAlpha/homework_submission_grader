# app.py

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import PyPDF2
import openai
from functools import wraps
import secrets
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv


app = Flask(__name__)

# Use a secure, random secret key and keep it safe
app.secret_key = secrets.token_urlsafe(16)

# Configure upload folder and allowed file extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'rubrics'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'submissions'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'feedbacks'), exist_ok=True)

# Configure OpenAI API key
load_dotenv()
client = openai.Client(api_key='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')

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homework_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)  # Hashed password
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    assignment_filename = db.Column(db.String(200), nullable=False)
    rubric_filename = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    teacher = db.relationship('User', backref=db.backref('assignments', lazy=True))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_filename = db.Column(db.String(200), nullable=False)
    submit_date = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    feedback = db.Column(db.Text)
    score = db.Column(db.Float)

    student = db.relationship('User', backref=db.backref('submissions', lazy=True))
    assignment = db.relationship('Assignment', backref=db.backref('submissions', lazy=True))



# Simulated user database (for demonstration purposes; use a real database in production)
users = {
    'teacher': {'password': 'teacherpass', 'role': 'teacher'},
    'student': {'password': 'studentpass', 'role': 'student'}
}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(role=None):
    """Login decorator to check if the user is logged in and has the correct role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            elif role and session.get('role') != role:
                return "Access denied", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = user.username
            session['role'] = user.role
            session['user_id'] = user.id
            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if not username or not password or not role:
            error = 'Please fill out all fields.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists.'
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/teacher/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    """Teacher dashboard."""
    assignments = Assignment.query.filter_by(teacher_id=session['user_id']).all()
    return render_template('teacher_dashboard.html', username=session['username'], assignments=assignments)


@app.route('/teacher/upload', methods=['GET', 'POST'])
@login_required(role='teacher')
def upload_assignment():
    """Teacher uploads assignment and rubric."""
    if request.method == 'POST':
        title = request.form['title']
        assignment = request.files.get('assignment')
        rubric = request.files.get('rubric')
        if not title or not assignment or not rubric:
            return 'Please provide all required fields.'
        if assignment.filename == '' or rubric.filename == '':
            return 'No selected file.'
        if allowed_file(assignment.filename) and allowed_file(rubric.filename):
            assignment_filename = secure_filename(assignment.filename)
            rubric_filename = secure_filename(rubric.filename)
            assignment.save(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', assignment_filename))
            rubric.save(os.path.join(app.config['UPLOAD_FOLDER'], 'rubrics', rubric_filename))
            # Save assignment info to database
            new_assignment = Assignment(
                title=title,
                assignment_filename=assignment_filename,
                rubric_filename=rubric_filename,
                teacher_id=session['user_id']
            )
            db.session.add(new_assignment)
            db.session.commit()
            return 'Assignment uploaded successfully.'
        else:
            return 'Unsupported file type.'
    return render_template('teacher_upload.html')


@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    """Student dashboard showing assignments and feedback."""
    assignments = Assignment.query.all()
    submissions = Submission.query.filter_by(student_id=session['user_id']).all()
    feedbacks = {sub.assignment_id: sub.feedback for sub in submissions}
    return render_template('student_dashboard.html', username=session['username'], assignments=assignments, feedbacks=feedbacks)

@app.route('/student/upload/<int:assignment_id>', methods=['GET', 'POST'])
@login_required(role='student')
def upload_submission(assignment_id):
    """Student uploads assignment submission."""
    assignment = Assignment.query.get_or_404(assignment_id)
    if request.method == 'POST':
        submission = request.files.get('submission')
        if not submission or submission.filename == '':
            return 'No selected file.'
        if allowed_file(submission.filename):
            submission_filename = secure_filename(f"{session['username']}_{assignment_id}_{submission.filename}")
            submission.save(os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', submission_filename))
            # Save submission info to database
            new_submission = Submission(
                submission_filename=submission_filename,
                student_id=session['user_id'],
                assignment_id=assignment_id
            )
            db.session.add(new_submission)
            db.session.commit()
            # Call the grading function
            result = grade_and_provide_feedback(new_submission.id)
            if result != 'success':
                return result
            return redirect(url_for('student_dashboard'))
        else:
            return 'Unsupported file type.'
    return render_template('student_upload.html', assignment=assignment)

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ''
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def generate_model_answers(assignment_text, rubric_text):
    """Generate model answers using OpenAI's ChatCompletion."""
    prompt = f"Based on the following assignment instructions and grading rubric, generate detailed model answers.\n\nAssignment Instructions:\n{assignment_text}\n\nGrading Rubric:\n{rubric_text}"
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',  # or 'gpt-4' if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates model answers for assignments."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        print(f"An error occurred during model answer generation: {e}")
        return None




def grade_and_provide_feedback(submission_id):
    """Grade the submission and provide feedback."""
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment

    # Extract student's submission text
    submission_path = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', submission.submission_filename)
    submission_text = extract_text_from_pdf(submission_path)

    # Extract assignment and rubric text
    assignment_path = os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', assignment.assignment_filename)
    rubric_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rubrics', assignment.rubric_filename)
    assignment_text = extract_text_from_pdf(assignment_path)
    rubric_text = extract_text_from_pdf(rubric_path)

    # Generate model answers
    model_answers = generate_model_answers(assignment_text, rubric_text)
    if not model_answers:
        return 'Failed to generate model answers.'

    # Prepare prompt for grading
    prompt = f"""Using the following model answers and grading rubric, grade the student's assignment and provide detailed scoring and feedback.

Student's Assignment:
{submission_text}

Model Answers:
{model_answers}

Grading Rubric:
{rubric_text}

Please provide a score and detailed feedback."""

    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',  # or 'gpt-4' if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant that grades assignments based on model answers and grading rubrics."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        feedback = response.choices[0].message.content.strip()
        # Extract score from feedback
        lines = feedback.splitlines()
        score_line = next((line for line in lines if 'Score:' in line or 'score:' in line), None)
        if score_line:
            score_text = score_line.split('Score:')[-1].split('/')[0].strip()
            try:
                score = float(score_text)
            except ValueError:
                score = None
        else:
            score = None
        # Update submission with feedback and score
        submission.feedback = feedback
        submission.score = score
        db.session.commit()
        return 'success'
    except openai.OpenAIError as e:
        return f'An error occurred during grading: {e}'





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
