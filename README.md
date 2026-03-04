# HR Assistant

An intelligent HR chatbot powered by Large Language Models and a **Text-to-SQL** architecture. Ask natural language questions about your employee data and get precise, data-backed answers — no guessing, no hallucinations.

![Architecture](https://img.shields.io/badge/architecture-Text--to--SQL-blue) ![Models](https://img.shields.io/badge/models-Groq%20%7C%20Local-green) ![DB](https://img.shields.io/badge/database-SQLite-orange)

---

## How It Works

```
User Question  ──▶  LLM generates SQL  ──▶  SQLite executes query  ──▶  LLM formats answer
```

1. **SQL Generation** — The LLM receives the HR database schema and translates the user's question into a valid `SELECT` query.
2. **Local Execution** — The query runs against the embedded SQLite database (`hr.db`), returning exact counts, averages, and distributions.
3. **Answer Formatting** — The raw SQL results are sent back to the LLM to produce a clean, readable natural language response.
4. **Memory** — Conversation history is tracked per session, enabling coherent multi-turn dialogue (e.g. "Which department did *they* mostly come from?").

> By using Text-to-SQL instead of RAG, the assistant eliminates counting hallucinations and guarantees mathematically exact figures.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Server** | FastAPI + Uvicorn |
| **LLM — Cloud** | Groq API (`llama-3.3-70b-versatile`) |
| **LLM — Local** | HuggingFace Transformers (`Qwen/Qwen2.5-7B-Instruct`) |
| **Database** | SQLite + Pandas |
| **Frontend** | Vanilla HTML/CSS/JS (single-page chat UI) |
| **SQL Safety** | `sqlparse` — SELECT-only validation |
| **Memory** | In-memory session store with TTL eviction |

---

## 🚀 Setup & Installation

### 1. Create Environment

```bash
conda create -n ai_base python=3.10
conda activate ai_base
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required: Groq API key (free at https://console.groq.com)
GROQ_API_KEY=gsk_your_key_here

# Required for local model: HuggingFace token (https://huggingface.co/settings/tokens)
HF_TOKEN=hf_your_token_here
```

### 3. Initialize the Database

Convert the HR CSV dataset into SQLite (run once):

```bash
python -m src.sql.db_setup
```

---

## 🏃 Running the Server

```bash
conda activate ai_base
python src/run.py
```

Then open **http://localhost:8000** in your browser.

> The server does **not** auto-reload. Restart manually after code changes.

---

## Models

### ⚡ Groq (default)
- Model: `llama-3.3-70b-versatile`
- Fast cloud inference — responses in ~2–5 seconds
- Requires `GROQ_API_KEY` in `.env`

### 🖥 Local (Qwen2.5-7B)
- Model: `Qwen/Qwen2.5-7B-Instruct` (~15 GB)
- Runs fully on-device — no data leaves your machine
- **First use:** downloads and caches the model (~45–60 min depending on connection)
- **Subsequent uses:** loads from local cache (~1–2 min)
- Toggle between models using the **Groq / Local** button in the top-right of the UI

---

## Example Questions

| Category | Example |
|---|---|
| Counts | "How many employees are there?" |
| Filters | "How many female managers are there?" |
| Aggregations | "What is the average monthly income by job role?" |
| Analytics | "Which department has the highest attrition rate?" |
| Top-N | "Show the top 5 highest paid employees" |
| Follow-up | "Which department did they mostly come from?" |

---

## Project Structure

```
HR-Assistant/
├── .env                        # API keys (not tracked in git)
├── .gitignore
├── app.py                      # Optional: terminal Q&A interface
├── hr.db                       # Auto-generated SQLite database
├── requirements.txt
├── dataset/                    # Source CSV data
├── static/
│   └── index.html              # Web chat UI
└── src/
    ├── run.py                  # FastAPI server entry point
    ├── sql/
    │   ├── db_setup.py         # One-time CSV → SQLite converter
    │   └── sql_engine.py       # SQL generation, safety check & execution
    └── chatbot/
        ├── api/
        │   ├── main.py         # FastAPI app + middleware
        │   ├── schemas.py      # Pydantic request/response models
        │   └── routes/
        │       ├── chat.py     # POST /api/chat
        │       └── health.py   # GET /api/health
        ├── llm/
        │   ├── orchestrator.py # Full Text-to-SQL pipeline
        │   ├── providers.py    # Groq & Local HuggingFace providers
        │   ├── prompts.py      # SQL generation & answer formatting prompts
        │   └── memory.py       # Session store with TTL eviction
        └── core/
            ├── config.py       # Environment-driven configuration
            └── logging.py      # Structured logging setup
```

---

## Security

- **SELECT-only enforcement** — `sqlparse` validates every generated query. `INSERT`, `UPDATE`, `DELETE`, `DROP`, and other destructive statements are blocked before execution.
- **Local data** — The actual employee records never leave your machine. Only the DB schema and query result strings are sent to the Groq API for formatting.
- **Local model option** — Switch to the Local model for a fully air-gapped setup where nothing is transmitted externally.
