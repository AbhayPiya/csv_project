from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import os
import csv
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'csv'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_unique_https_urls(file1, col1, file2, col2):
    """Simple CSV processing without pandas"""
    urls1 = set()
    urls2 = set()
    
    # Read first file
    with open(file1, 'r', encoding='latin1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if col1 in row and row[col1]:
                url = row[col1].strip()
                if url.startswith("https://"):
                    urls1.add(url)
    
    # Read second file
    with open(file2, 'r', encoding='latin1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if col2 in row and row[col2]:
                url = row[col2].strip()
                if url.startswith("https://"):
                    urls2.add(url)
    
    # Find unique URLs
    unique_to_file1 = urls1 - urls2
    unique_to_file2 = urls2 - urls1
    unique_urls = unique_to_file1.union(unique_to_file2)
    
    return unique_urls

def get_csv_columns(file_path):
    """Get column names from a CSV file"""
    try:
        with open(file_path, 'r', encoding='latin1') as f:
            reader = csv.reader(f)
            headers = next(reader)
            return headers
    except Exception as e:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        flash('Both files are required!')
        return redirect(request.url)
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        flash('Both files must be selected!')
        return redirect(request.url)
    
    if file1 and file2 and allowed_file(file1.filename) and allowed_file(file2.filename):
        filename1 = secure_filename(file1.filename)
        filename2 = secure_filename(file2.filename)
        
        filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
        filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
        
        file1.save(filepath1)
        file2.save(filepath2)
        
        columns1 = get_csv_columns(filepath1)
        columns2 = get_csv_columns(filepath2)
        
        return render_template('select_columns.html', 
                             filename1=filename1, 
                             filename2=filename2,
                             columns1=columns1,
                             columns2=columns2)
    
    flash('Invalid file type! Only CSV files are allowed.')
    return redirect(request.url)

@app.route('/process', methods=['POST'])
def process_files():
    filename1 = request.form['filename1']
    filename2 = request.form['filename2']
    col1 = request.form['col1']
    col2 = request.form['col2']
    
    filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
    filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
    
    try:
        unique_urls = get_unique_https_urls(filepath1, col1, filepath2, col2)
        
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], 'unique_https_urls.csv')
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Unique HTTPS URLs'])
            for url in unique_urls:
                writer.writerow([url])
        
        return render_template('results.html', 
                             unique_urls=list(unique_urls),
                             count=len(unique_urls),
                             output_file='unique_https_urls.csv')
    
    except Exception as e:
        flash(f'Error processing files: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run() 
