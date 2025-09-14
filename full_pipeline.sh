#!/bin/bash
uv add csvkit
uv add pdf2image-cli
uv add datasette
uv add sqlite-utils
uv add datawrapper
uv add pandas
uv run datasette install datasette-codespaces
uv add sqlite_utils
uv add llm
uv run llm install llm-gemini
uv run llm install llm-groq
uv run llm install llm-ollama

uv run python scrape.py
uv run python license_mutations.py
bash get_pdfs.sh
bash images.sh
bash ocr.sh
bash combine_text.sh
uv run python mod_alerts.py
uv run python data_cleaning.py
bash database_creation.sh
uv run python app.py




