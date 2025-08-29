FROM python:3.12-slim

# Install system dependencies for Tesseract and PDF/image processing
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev poppler-utils gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose Flask port
EXPOSE 5000

# Default command: run Flask app
CMD ["python", "img2text.py"]
