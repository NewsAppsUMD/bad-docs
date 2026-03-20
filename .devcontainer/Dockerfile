FROM mcr.microsoft.com/devcontainers/python:1-3.12

# System packages for PDF processing and OCR
RUN apt-get update \
        && apt-get install -y --no-install-recommends \
             poppler-utils \
             tesseract-ocr \
             libtesseract-dev \
             sqlite3 \
             libsqlite3-dev \
        && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv
