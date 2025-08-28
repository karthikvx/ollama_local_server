FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    rm -rf /var/lib/apt/lists/* && \
    pip install Flask Pillow pytesseract requests pdf2image PyPDF2

WORKDIR /app
COPY . /app

CMD ["python", "img2text.py"]
