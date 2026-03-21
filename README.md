# MD Medical Discipline Watch

A Flask web application that scrapes, processes and serves Maryland Board of Physicians disciplinary records with AI-powered summaries and semantic similarity search.

## What It Does

The app collects disciplinary actions taken by the Maryland Board of Physicians, runs OCR on the PDF documents, generates AI summaries and makes everything searchable:

- **Browse** alerts by doctor, doctor type, year and keywords
- **Search** across document summaries, full text and extracted keywords
- **Semantic similarity search** — find documents similar to a query using vector embeddings
- **AI-generated summaries** of each disciplinary document with extracted keywords
- **Direct links** to original PDF documents from the state

## Project Structure

```
.
├── app.py                  # Flask application
├── models.py               # Peewee ORM models (shared across app + pipeline)
├── freeze.py               # Static site generator
├── templates/              # Jinja2 templates (12 pages)
├── static/                 # CSS + htmx.min.js
├── pipeline/               # Data processing scripts
│   ├── full_pipeline.sh    # 10-step orchestrator
│   ├── scrape.py           # Scrapes MD Board of Physicians website
│   ├── get_pdfs.sh         # Downloads PDF documents
│   ├── images.sh           # PDF → image conversion (for OCR)
│   ├── ocr.sh              # Tesseract OCR
│   ├── combine_text.sh     # Merges multi-page OCR output
│   ├── mod_alerts.py       # Alert data cleaning
│   ├── data_cleaning.py    # Name/type extraction
│   ├── license_mutations.py # File ID fixes
│   ├── database_creation.sh # SQLite table creation + population
│   ├── repop_db.py         # DB population helpers
│   ├── populate_json.py    # Loads JSON summaries into DB
│   ├── generate_json_from_combined.py  # AI summary generation (Ollama)
│   ├── add_embeddings.py   # Embedding generation (Ollama)
│   ├── graph_making.py     # Datawrapper chart generation
│   ├── prompt.txt          # LLM prompt for document extraction
│   └── _paths.py           # Shared path constants
├── data/                   # All generated data (gitignored)
│   ├── bad_docs.db         # SQLite database
│   ├── pdfs/               # Downloaded PDFs
│   ├── images/             # PDF page images
│   ├── text/               # Raw OCR output
│   ├── combined_text/      # Merged OCR text per document
│   └── json/               # AI-generated JSON summaries
├── .devcontainer/          # Dev container config (tesseract, poppler)
├── pyproject.toml          # Dependencies (managed with uv)
├── Procfile                # gunicorn deployment
└── .env.example            # Environment variable template
```

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — package manager
- **[Ollama](https://ollama.ai)** — local LLM runtime (for summaries + embeddings)
- **Tesseract OCR** and **Poppler** — for PDF processing (included in devcontainer)

## Setup

### 1. Install dependencies

```bash
uv sync                      # runtime deps
uv sync --extra pipeline     # + pipeline deps (pandas, pdf2image, llm-ollama)
```

### 2. Pull Ollama models

```bash
ollama pull qwen3.5:9b        # JSON summary generation
ollama pull nomic-embed-text   # embeddings for similarity search
```

### 3. Run the pipeline

```bash
bash pipeline/full_pipeline.sh          # incremental update
bash pipeline/full_pipeline.sh --full   # full rebuild from scratch
```

The pipeline is **incremental by default** — it skips already-downloaded PDFs, already-OCR'd files, existing JSON summaries and documents that already have embeddings. A full rebuild re-processes everything except embeddings (use `--full` to also regenerate those).

### 4. Start the app

```bash
uv run python app.py                              # development
uv run gunicorn app:app                            # production
```

The app runs on port 5000.

## The Pipeline

The `full_pipeline.sh` script runs 10 steps:

| Step | Script | What it does |
|------|--------|-------------|
| 1 | `scrape.py` | Scrapes alert metadata from MD Board of Physicians |
| 2 | `license_mutations.py` | Fixes file ID inconsistencies |
| 3 | `get_pdfs.sh` | Downloads PDF documents |
| 4 | `images.sh` | Converts PDFs to images for OCR |
| 5 | `ocr.sh` | Runs Tesseract OCR on images |
| 6 | `combine_text.sh` | Merges multi-page OCR output per document |
| 7 | `mod_alerts.py` + `data_cleaning.py` | Cleans and reformats alert data |
| 8 | `database_creation.sh` | Creates/populates the SQLite database |
| 9 | `generate_json_from_combined.py` | Generates AI summaries via Ollama (qwen3.5:9b) |
| 10 | `add_embeddings.py` | Generates vector embeddings via Ollama (nomic-embed-text) |

## Database

The SQLite database (`data/bad_docs.db`) has five tables:

- **doctor_info** — doctor names, types and license numbers
- **clean_alerts** — disciplinary alerts with dates, types and links to PDFs
- **all_cases** — case numbers associated with alerts
- **text** — full OCR text of each document
- **document_json** — AI-generated summaries, keywords and embedding vectors

## Dev Container

The `.devcontainer/` config provides a ready-to-go environment with Python 3.12, Tesseract, Poppler and SQLite3. Open the project in VS Code or GitHub Codespaces and dependencies install automatically via `uv sync`.

## Tech Stack

- **Flask** + **Peewee** — web framework and ORM
- **Ollama** — local LLM runtime (qwen3.5:9b for summaries, nomic-embed-text for embeddings)
- **Tesseract** — OCR
- **Poppler** (pdf2image) — PDF to image conversion
- **NumPy** — cosine similarity for semantic search
- **htmx** — lightweight frontend interactivity
- **uv** — Python package management
