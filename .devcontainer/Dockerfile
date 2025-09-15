FROM mcr.microsoft.com/devcontainers/python:1-3.12

# keep apt lists small and install required system packages
RUN apt-get update \
        && apt-get install -y --no-install-recommends \
             poppler-utils \
             tesseract-ocr \
             libtesseract-dev \
             sqlite3 \
             libsqlite3-dev \
        && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (if provided)
COPY requirements.txt /tmp/pip-tmp/requirements.txt
RUN if [ -f /tmp/pip-tmp/requirements.txt ]; then \
            python3 -m pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt; \
        fi \
        && rm -rf /tmp/pip-tmp

