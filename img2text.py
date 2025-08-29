from pdf2image import convert_from_path
import PyPDF2
import os
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text
        # OCR images in PDF pages
        images = convert_from_path(pdf_path)
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
        if ocr_text.strip():
            text += "\n[OCR Extracted Text from Images:]\n" + ocr_text
    except Exception as e:
        text = f"Error extracting text from PDF: {e}"
    return text

def extract_text_from_md(md_path):
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading markdown file: {e}"
import time

import requests
from PIL import Image
import pytesseract

def extract_text_from_image(image_path):
    """
    Extracts text from an image using Tesseract OCR.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The extracted text from the image.
    """
    try:
        # Open the image using Pillow
        image = Image.open(image_path)

        # Specify the path to the Tesseract executable (if not in system PATH)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
        # (Uncomment and modify if Tesseract is not in your system's PATH)

        # Extract text using pytesseract
        text = pytesseract.image_to_string(image)
        return text
    except FileNotFoundError:
        return "Error: Image file not found."
    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract OCR engine not found. Please ensure it's installed and accessible in your PATH."
    except Exception as e:
        return f"An error occurred: {e}"

import json
import re
def send_to_ollama(text, model_name):
    """Send extracted text to Ollama server and return the response, filtering out <think> tags."""
    url = "http://host.docker.internal:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": text
    }
    try:
        # Increase timeout for large file processing
        response = requests.post(url, json=payload, timeout=900, stream=True)
        response.raise_for_status()
        result = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        result += data["response"]
                except Exception:
                    continue
        # Remove <think>...</think> blocks from the result
        result = re.sub(r'<think>[\s\S]*?<\/think>', '', result, flags=re.IGNORECASE)
        return result.strip()
    except Exception as e:
        return f"Error communicating with Ollama server: {e}"



# --- Flask Web UI ---
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename

# Increase upload size limit (e.g., 100MB)
MAX_CONTENT_LENGTH = 100 * 1024 * 1024

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Optional: Enable CORS for debugging
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# Constants
DEFAULT_MODEL = 'ALIENTELLIGENCE/accountingandtaxation'

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Image2Text Ollama UI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        textarea { width: 100%; height: 300px; }
        button { padding: 10px 20px; font-size: 16px; }
        .upload-section { margin-bottom: 20px; }
        #clock { font-size: 18px; margin-bottom: 20px; color: #333; }
    </style>
</head>
<body>
    <h2>Extract Text from Images and Query Ollama</h2>
    <div id="clock"></div>
    <div id="timer" style="font-size:16px;color:#007700;"></div>
    <div class="upload-section">
        <form id="uploadForm" enctype="multipart/form-data" method="post" action="/upload">
            <label for="file">Upload screenshot/snippet (PNG/JPG, multiple allowed):</label>
            <input type="file" id="file" name="file" accept="image/png, image/jpeg,application/pdf,.md" multiple>
            <label for="model">Choose model:</label>
            <select id="model" name="model">
                <option value="ALIENTELLIGENCE/accountingandtaxation">Accountingandtaxation</option>
                <option value="llama3.2-vision:latest">llama3.2-vision</option>
                <option value="deepseek-coder:1.3b">deepseek-coder</option>
                <option value="qwen3:8b">qwen3</option>
                <option value="mistral:7b">mistral-7b</option>
                <!-- Add more models as needed -->
            </select>
            <br><label for="instruction">Additional instruction for model:</label>
            <textarea id="instruction" name="instruction" style="width: 60%; height: 80px;" placeholder="e.g. Summarize, extract numbers, etc."></textarea>
            <button type="submit" id="uploadBtn">Upload</button>
            <button type="button" id="runInstructionBtn">Run Instruction Only</button>
            <button type="button" id="cancelBtn">Cancel/Stop</button>
        </form>
        <div id="uploadMsg"></div>
    </div>
    <br>
    <label for="result">Response:</label><br>
    <textarea id="result" readonly></textarea>
    <script>
        // Clock timer
        function updateClock() {
            var now = new Date();
            var timeString = now.toLocaleTimeString();
            document.getElementById('clock').innerText = 'Current time: ' + timeString;
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Timer logic
        let timerInterval = null;
        let startTime = null;
        function startTimer() {
            startTime = Date.now();
            timerInterval = setInterval(function() {
                let elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                document.getElementById('timer').innerText = 'Elapsed: ' + elapsed + 's';
            }, 100);
        }
        function stopTimer() {
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = null;
            document.getElementById('timer').innerText = '';
        }

        // AbortController for cancel/stop
        let currentController = null;

        // Upload and process
        document.getElementById('uploadForm').onsubmit = function(e) {
            var fileInput = document.getElementById('file');
            if (!fileInput.files.length) {
                e.preventDefault();
                document.getElementById('uploadMsg').innerText = 'Please select at least one file to upload.';
                return false;
            }
            e.preventDefault();
            if (currentController) currentController.abort();
            currentController = new AbortController();
            var formData = new FormData(document.getElementById('uploadForm'));
            // Append all files
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('file', fileInput.files[i]);
            }
            document.getElementById('uploadMsg').innerText = 'Uploading and processing...';
            document.getElementById('result').value = 'Processing...';
            startTimer();
            fetch('/upload', {method: 'POST', body: formData, signal: currentController.signal})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uploadMsg').innerText = data.message;
                    if (data.result) {
                        document.getElementById('result').value = data.result;
                    } else {
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                })
                .catch(err => {
                    if (err.name === 'AbortError') {
                        document.getElementById('uploadMsg').innerText = 'Request cancelled.';
                        document.getElementById('result').value = '';
                    } else {
                        document.getElementById('uploadMsg').innerText = 'Error: ' + err;
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                });
        };
        document.getElementById('runInstructionBtn').onclick = function() {
            if (currentController) currentController.abort();
            currentController = new AbortController();
            var formData = new FormData();
            formData.append('model', document.getElementById('model').value);
            formData.append('instruction', document.getElementById('instruction').value);
            document.getElementById('uploadMsg').innerText = 'Processing instruction...';
            document.getElementById('result').value = 'Processing...';
            startTimer();
            fetch('/upload', {method: 'POST', body: formData, signal: currentController.signal})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uploadMsg').innerText = data.message;
                    if (data.result) {
                        document.getElementById('result').value = data.result;
                    } else {
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                })
                .catch(err => {
                    if (err.name === 'AbortError') {
                        document.getElementById('uploadMsg').innerText = 'Request cancelled.';
                        document.getElementById('result').value = '';
                    } else {
                        document.getElementById('uploadMsg').innerText = 'Error: ' + err;
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                });
        };
        document.getElementById('cancelBtn').onclick = function() {
            if (currentController) currentController.abort();
        };
    </script>
</body>
</html>
'''
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename

# Helper functions must be defined before use in upload_image

def process_uploaded_files(files, instruction):
    filenames = []
    all_text = []
    for file in files:
        filename = secure_filename(file.filename)
        filenames.append(filename)
        images_dir = "images"
        os.makedirs(images_dir, exist_ok=True)
        save_path = os.path.join(images_dir, filename)
        file.save(save_path)
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            extracted_text = extract_text_from_pdf(save_path)
        elif ext == '.md':
            extracted_text = extract_text_from_md(save_path)
        else:
            extracted_text = extract_text_from_image(save_path)
            # Remove the file if it is a PNG after processing
            if filename.lower().endswith('.png'):
                try:
                    os.remove(save_path)
                except Exception:
                    pass
        all_text.append(f"[File: {filename}]\n{extracted_text}")
    prompt = build_prompt(instruction, '\n\n'.join(all_text))
    return filenames, prompt

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text
        # OCR images in PDF pages
        images = convert_from_path(pdf_path)
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
        if ocr_text.strip():
            text += "\n[OCR Extracted Text from Images:]\n" + ocr_text
    except Exception as e:
        text = f"Error extracting text from PDF: {e}"
    return text

def extract_text_from_md(md_path):
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading markdown file: {e}"
import time

import requests
from PIL import Image
import pytesseract

def extract_text_from_image(image_path):
    """
    Extracts text from an image using Tesseract OCR.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The extracted text from the image.
    """
    try:
        # Open the image using Pillow
        image = Image.open(image_path)

        # Specify the path to the Tesseract executable (if not in system PATH)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
        # (Uncomment and modify if Tesseract is not in your system's PATH)

        # Extract text using pytesseract
        text = pytesseract.image_to_string(image)
        return text
    except FileNotFoundError:
        return "Error: Image file not found."
    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract OCR engine not found. Please ensure it's installed and accessible in your PATH."
    except Exception as e:
        return f"An error occurred: {e}"

import json
import re
def send_to_ollama(text, model_name):
    """Send extracted text to Ollama server and return the response, filtering out <think> tags."""
    url = "http://host.docker.internal:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": text
    }
    try:
        # Increase timeout for large file processing
        response = requests.post(url, json=payload, timeout=900, stream=True)
        response.raise_for_status()
        result = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        result += data["response"]
                except Exception:
                    continue
        # Remove <think>...</think> blocks from the result
        result = re.sub(r'<think>[\s\S]*?<\/think>', '', result, flags=re.IGNORECASE)
        return result.strip()
    except Exception as e:
        return f"Error communicating with Ollama server: {e}"



# --- Flask Web UI ---
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename

# Increase upload size limit (e.g., 100MB)
MAX_CONTENT_LENGTH = 100 * 1024 * 1024

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Optional: Enable CORS for debugging
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# Constants
DEFAULT_MODEL = 'ALIENTELLIGENCE/accountingandtaxation'

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Image2Text Ollama UI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        textarea { width: 100%; height: 300px; }
        button { padding: 10px 20px; font-size: 16px; }
        .upload-section { margin-bottom: 20px; }
        #clock { font-size: 18px; margin-bottom: 20px; color: #333; }
    </style>
</head>
<body>
    <h2>Extract Text from Images and Query Ollama</h2>
    <div id="clock"></div>
    <div id="timer" style="font-size:16px;color:#007700;"></div>
    <div class="upload-section">
        <form id="uploadForm" enctype="multipart/form-data" method="post" action="/upload">
            <label for="file">Upload screenshot/snippet (PNG/JPG, multiple allowed):</label>
            <input type="file" id="file" name="file" accept="image/png, image/jpeg,application/pdf,.md" multiple>
            <label for="model">Choose model:</label>
            <select id="model" name="model">
                <option value="ALIENTELLIGENCE/accountingandtaxation">Accountingandtaxation</option>
                <option value="llama3.2-vision:latest">llama3.2-vision</option>
                <option value="deepseek-coder:1.3b">deepseek-coder</option>
                <option value="qwen3:8b">qwen3</option>
                <option value="mistral:7b">mistral-7b</option>
                <!-- Add more models as needed -->
            </select>
            <br><label for="instruction">Additional instruction for model:</label>
            <textarea id="instruction" name="instruction" style="width: 60%; height: 80px;" placeholder="e.g. Summarize, extract numbers, etc."></textarea>
            <button type="submit" id="uploadBtn">Upload</button>
            <button type="button" id="runInstructionBtn">Run Instruction Only</button>
            <button type="button" id="cancelBtn">Cancel/Stop</button>
        </form>
        <div id="uploadMsg"></div>
    </div>
    <br>
    <label for="result">Response:</label><br>
    <textarea id="result" readonly></textarea>
    <script>
        // Clock timer
        function updateClock() {
            var now = new Date();
            var timeString = now.toLocaleTimeString();
            document.getElementById('clock').innerText = 'Current time: ' + timeString;
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Timer logic
        let timerInterval = null;
        let startTime = null;
        function startTimer() {
            startTime = Date.now();
            timerInterval = setInterval(function() {
                let elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                document.getElementById('timer').innerText = 'Elapsed: ' + elapsed + 's';
            }, 100);
        }
        function stopTimer() {
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = null;
            document.getElementById('timer').innerText = '';
        }

        // AbortController for cancel/stop
        let currentController = null;

        // Upload and process
        document.getElementById('uploadForm').onsubmit = function(e) {
            var fileInput = document.getElementById('file');
            if (!fileInput.files.length) {
                e.preventDefault();
                document.getElementById('uploadMsg').innerText = 'Please select at least one file to upload.';
                return false;
            }
            e.preventDefault();
            if (currentController) currentController.abort();
            currentController = new AbortController();
            var formData = new FormData(document.getElementById('uploadForm'));
            // Append all files
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('file', fileInput.files[i]);
            }
            document.getElementById('uploadMsg').innerText = 'Uploading and processing...';
            document.getElementById('result').value = 'Processing...';
            startTimer();
            fetch('/upload', {method: 'POST', body: formData, signal: currentController.signal})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uploadMsg').innerText = data.message;
                    if (data.result) {
                        document.getElementById('result').value = data.result;
                    } else {
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                })
                .catch(err => {
                    if (err.name === 'AbortError') {
                        document.getElementById('uploadMsg').innerText = 'Request cancelled.';
                        document.getElementById('result').value = '';
                    } else {
                        document.getElementById('uploadMsg').innerText = 'Error: ' + err;
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                });
        };
        document.getElementById('runInstructionBtn').onclick = function() {
            if (currentController) currentController.abort();
            currentController = new AbortController();
            var formData = new FormData();
            formData.append('model', document.getElementById('model').value);
            formData.append('instruction', document.getElementById('instruction').value);
            document.getElementById('uploadMsg').innerText = 'Processing instruction...';
            document.getElementById('result').value = 'Processing...';
            startTimer();
            fetch('/upload', {method: 'POST', body: formData, signal: currentController.signal})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('uploadMsg').innerText = data.message;
                    if (data.result) {
                        document.getElementById('result').value = data.result;
                    } else {
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                })
                .catch(err => {
                    if (err.name === 'AbortError') {
                        document.getElementById('uploadMsg').innerText = 'Request cancelled.';
                        document.getElementById('result').value = '';
                    } else {
                        document.getElementById('uploadMsg').innerText = 'Error: ' + err;
                        document.getElementById('result').value = '';
                    }
                    stopTimer();
                });
        };
        document.getElementById('cancelBtn').onclick = function() {
            if (currentController) currentController.abort();
        };
    </script>
</body>
</html>
'''
from flask import Flask, render_template_string, request, jsonify
from werkzeug.utils import secure_filename

# Helper functions must be defined before use in upload_image

def process_uploaded_files(files, instruction):
    filenames = []
    all_text = []
    for file in files:
        filename = secure_filename(file.filename)
        filenames.append(filename)
        images_dir = "images"
        os.makedirs(images_dir, exist_ok=True)
        save_path = os.path.join(images_dir, filename)
        file.save(save_path)
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            extracted_text = extract_text_from_pdf(save_path)
        elif ext == '.md':
            extracted_text = extract_text_from_md(save_path)
        else:
            extracted_text = extract_text_from_image(save_path)
            # Remove the file if it is a PNG after processing
            if filename.lower().endswith('.png'):
                try:
                    os.remove(save_path)
                except Exception:
                    pass
        all_text.append(f"[File: {filename}]\n{extracted_text}")
    prompt = build_prompt(instruction, '\n\n'.join(all_text))
    return filenames, prompt

def build_prompt(instruction, extracted_text):
    if instruction and extracted_text:
        return f"{instruction}\n\n{extracted_text}"
    elif instruction:
        return instruction
    else:
        return extracted_text

@app.route("/upload", methods=["POST"])
def upload_image():
    start_time = time.time()
    model_name = request.form.get('model', DEFAULT_MODEL)
    instruction = request.form.get('instruction', '').strip()
    files = request.files.getlist('file')
    filenames = []
    if files and any(f.filename for f in files):
        filenames, prompt = process_uploaded_files(files, instruction)
        result_text = send_to_ollama(prompt, model_name)
    elif not instruction:
        return jsonify(message="No file or instruction provided."), 400
    else:
        prompt = build_prompt(instruction, None)
        result_text = send_to_ollama(prompt, model_name)
    total_time = time.time() - start_time
    msg = f"Processed with model '{model_name}'."
    if filenames:
        msg = f"Files {filenames} uploaded and {msg}"
    # Write response to log file
    log_dir = os.path.join(os.path.dirname(__file__), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'img2text.log')
    with open(log_path, 'a', encoding='utf-8') as logf:
        logf.write(f"---\n{msg}\n{result_text}\nTotal time taken: {total_time:.2f} seconds\n")
    return jsonify(message=msg, result=result_text + f"\n\nTotal time taken: {total_time:.2f} seconds")

@app.route("/")
def index():
    return render_template_string(HTML)

## /run endpoint is now unused and can be removed or left for batch processing if needed

@app.errorhandler(Exception)
def handle_exception(e):
    from flask import jsonify
    import traceback
    response = {
        "message": f"Server error: {str(e)}",
        "result": "",
        "trace": traceback.format_exc()
    }
    return jsonify(response), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)