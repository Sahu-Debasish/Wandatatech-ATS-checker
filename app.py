"""
WANDATA ATS Checker - Flask Backend
Run: python app.py
Then open index.html in browser
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import json

app = Flask(__name__, static_folder='static', static_url_path='/static')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.after_request
def after_request(response):
    return add_cors_headers(response)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def stylesheet():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def javascript():
    return send_from_directory('.', 'script.js')

@app.route('/options', methods=['OPTIONS'])
def handle_options():
    resp = app.make_default_options_response()
    return add_cors_headers(resp)

@app.route('/analyze/general', methods=['POST', 'OPTIONS'])
def analyze_general():
    if request.method == 'OPTIONS':
        return add_cors_headers(app.make_default_options_response())
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Upload PDF, DOC, DOCX, or TXT'}), 400
    
    # Save file
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    try:
        from ats_engine import extract_text, calculate_general_ats_score
        text = extract_text(filepath, file.filename)
        
        if not text or len(text.strip()) < 50:
            return jsonify({'error': 'Could not extract text from resume. Ensure it is not scanned image.'}), 400
        
        result = calculate_general_ats_score(text)
        result['filename'] = file.filename
        result['char_count'] = len(text)
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    finally:
        # Clean up uploaded file
        try: os.remove(filepath)
        except: pass

@app.route('/analyze/job', methods=['POST', 'OPTIONS'])
def analyze_job():
    if request.method == 'OPTIONS':
        return add_cors_headers(app.make_default_options_response())
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400
    
    file        = request.files['resume']
    job_title   = request.form.get('job_title', '').strip()
    job_desc    = request.form.get('job_description', '').strip()
    
    if not job_title:
        return jsonify({'error': 'Job title is required'}), 400
    if not job_desc or len(job_desc) < 50:
        return jsonify({'error': 'Please provide a detailed job description (at least 50 characters)'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Upload PDF, DOC, DOCX, or TXT'}), 400
    
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    try:
        from ats_engine import extract_text, calculate_job_ats_score
        text   = extract_text(filepath, file.filename)
        
        if not text or len(text.strip()) < 50:
            return jsonify({'error': 'Could not extract text from resume.'}), 400
        
        result = calculate_job_ats_score(text, job_title, job_desc)
        result['filename'] = file.filename
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    finally:
        try: os.remove(filepath)
        except: pass

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'WANDATA ATS Checker'})

if __name__ == '__main__':
    print("="*55)
    print("  WANDATA ATS Checker — Starting Server")
    print("="*55)
    print("  Open in browser: http://localhost:5000")
    print("  Press Ctrl+C to stop")
    print("="*55)
    app.run(debug=True, host='0.0.0.0', port=5000)
