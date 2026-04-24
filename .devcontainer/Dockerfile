FROM mcr.microsoft.com/devcontainers/python:1-3.12

# Remove stale Yarn repo that has an expired/missing GPG key
RUN rm -f /etc/apt/sources.list.d/yarn.list

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
