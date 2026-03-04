# HR Assistant — Your HR Intelligence Partner

An intelligent HR chatbot powered by Large Language Models and a **Text-to-SQL** architecture. Ask natural language questions about your employee data and get precise, data-backed answers — no guessing, no hallucinations.

![Architecture](https://img.shields.io/badge/architecture-Text--to--SQL-blue) ![Models](https://img.shields.io/badge/models-Groq%20%7C%20Local-green) ![DB](https://img.shields.io/badge/database-SQLite-orange) ![Persona](https://img.shields.io/badge/persona-HR%20Consultant-purple)

---

## How It Works

```
User Question  ──▶  LLM generates SQL  ──▶  SQLite executes query  ──▶  LLM formats answer
```

1. **SQL Generation** — The LLM receives the HR database schema and translates the user question into a valid `SELECT` query.
2. **Local Execution** — The query runs against the embedded SQLite database (`hr.db`), returning exact counts, averages, and distributions.
3. **Answer Formatting** — The raw SQL results are sent back to the LLM to produce a professional, consultative natural language response.
4. **Memory** — Conversation history is tracked per session, enabling coherent multi-turn dialogue (e.g. "Which department did *they* mostly come from?").

> By using Text-to-SQL instead of RAG, the assistant eliminates counting hallucinations and guarantees mathematically exact figures.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Server** | FastAPI + Uvicorn |
| **LLM — Cloud** | Groq API (`llama-3.3-70b-versatile`) |
| **LLM — Local** | HuggingFace Transformers (`Qwen/Qwen2.5-Coder-7B-Instruct`) |
| **Database** | SQLite + Pandas |
| **Frontend** | Vanilla HTML/CSS/JS (single-page chat UI) |
| **SQL Safety** | `sqlparse` — SELECT-only validation |
| **Memory** | In-memory session store with TTL eviction |
| **GPU Support** | PyTorch nightly + CUDA 12.8 (Blackwell / RTX 50xx compatible) |

---

## 🚀 Setup & Installation

### 1. Create Environment

```bash
conda create -n ai_base python=3.10
conda activate ai_base
pip install -r requirements.txt
```

> **If you have an NVIDIA GPU (RTX 50xx / Blackwell):** install PyTorch nightly for best performance:
> ```bash
> pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
> ```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required: Groq API key (free at https://console.groq.com)
GROQ_API_KEY=gsk_your_key_here

# Optional: HuggingFace token (needed if model is private)
HF_TOKEN=hf_your_token_here

# Optional: path to a locally saved model folder
LOCAL_MODEL_ID=C:/path/to/qwen2.5-coder-7b-instruct
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

### 🖥 Local (Qwen2.5-Coder-7B)
- Model: `Qwen/Qwen2.5-Coder-7B-Instruct` (~15 GB)
- Runs fully on-device — no data leaves your machine
- Point to a pre-downloaded folder via `LOCAL_MODEL_ID` in `.env` to skip re-download
- **With GPU (RTX 30xx/40xx/50xx):** loads in ~1 min, responds in ~5–15 seconds
- **Without GPU (CPU only):** loads in ~5 min, responds in ~3–10 minutes
- Toggle between models using the **Groq / Local** button in the top-right of the UI

---

## ⚡ vs 🖥 Model Comparison: Groq API vs Qwen2.5-Coder-7B

| Criterion | ⚡ Groq (`llama-3.3-70b-versatile`) | 🖥 Local (`Qwen2.5-Coder-7B-Instruct`) |
|---|---|---|
| **Response speed** | ~2–5 seconds | ~5–15 sec (GPU) / ~3–10 min (CPU) |
| **SQL accuracy** | ⭐⭐⭐⭐⭐ Excellent — 70B parameter model | ⭐⭐⭐⭐ Very good — Coder model fine-tuned for SQL/code |
| **Answer quality** | ⭐⭐⭐⭐⭐ Rich, nuanced responses | ⭐⭐⭐⭐ Clear and accurate |
| **Multi-turn context** | ✅ Strong pronoun/reference resolution | ✅ Good, occasional drift on long sessions |
| **Data privacy** | ⚠️ Schema + results sent to Groq servers | ✅ Fully local — zero external transmission |
| **Internet required** | ✅ Yes | ❌ No (after initial download) |
| **Cost** | Free tier (rate-limited) | Free — runs on your hardware |
| **Best for** | Fast exploration, demos, daily use | Sensitive data, air-gapped environments |

**Summary:** Use **Groq** for speed and quality in most sessions. Switch to **Local** when data privacy is critical or you need offline capability. The Coder variant of Qwen2.5 is specifically fine-tuned for SQL and code, making it an excellent local alternative for this Text-to-SQL use case.

---

## ✨ Features

| Feature | Description |
|---|---|
| **HR Consultant Persona** | The assistant responds as *Alexandra*, a senior HR consultant — professional, consultative, insight-driven tone |
| **Natural Language Queries** | Ask any HR question in plain English |
| **Text-to-SQL Engine** | Exact answers from structured data — no hallucination |
| **Multi-turn Memory** | Follow-up questions resolve context ("how many of *them*…") |
| **Dual Model Support** | Switch between Groq cloud and local Qwen2.5-Coder-7B per request |
| **Export Transcript** | Download the full chat as a `.txt` file or **PDF** via the Export button |
| **View SQL** | Toggle the generated SQL query under each assistant response |
| **Session Management** | Clear history button resets conversation memory |

---

## Example Questions

| Category | Example |
|---|---|
| Headcount | "What is our total headcount by department?" |
| Attrition | "What is our overall attrition rate?" |
| Compensation | "What is the average salary by job level?" |
| Satisfaction | "How many employees have low job satisfaction?" |
| Overtime | "Which department has the most overtime workers?" |
| Top-N | "Show the top 5 highest paid roles" |
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
│   └── index.html              # Web chat UI (chat + export button)
└── src/
    ├── run.py                  # FastAPI server entry point
    ├── sql/
    │   ├── db_setup.py         # One-time CSV → SQLite converter
    │   └── sql_engine.py       # SQL generation, safety check & execution
    └── chatbot/
        ├── api/
        │   ├── main.py         # FastAPI app + global exception handler
        │   ├── schemas.py      # Pydantic request/response models
        │   └── routes/
        │       ├── chat.py     # POST /api/chat
        │       └── health.py   # GET /api/health
        ├── llm/
        │   ├── orchestrator.py # Full Text-to-SQL pipeline
        │   ├── providers.py    # Groq & Local HuggingFace providers
        │   ├── prompts.py      # HR Consultant persona & answer prompts
        │   └── memory.py       # Session store with TTL eviction
        └── core/
            ├── config.py       # Environment-driven configuration
            └── logging.py      # Structured logging setup
```

---

## 📓 Jupyter Notebooks

| Notebook | Description |
|---|---|
| `EDA.ipynb` | Exploratory data analysis of the 1,470-employee IBM HR dataset — data overview, column decoding, feature distributions using Pandas & Matplotlib |
| `Sentiment_Analysis.ipynb` | Employee sentiment scoring via two methods: (1) rule-based composite of `JobSatisfaction`, `EnvironmentSatisfaction` & `PerformanceRating`; (2) HuggingFace `distilbert-base-uncased-finetuned-sst-2-english` NLP classifier |

**To run:**
```bash
conda activate ai_base
jupyter notebook notebook/EDA.ipynb         # or Sentiment_Analysis.ipynb
```

---

## Security

- **SELECT-only enforcement** — `sqlparse` validates every generated query. `INSERT`, `UPDATE`, `DELETE`, `DROP`, and other destructive statements are blocked before execution.
- **Local data** — The actual employee records never leave your machine. Only the DB schema and query result strings are sent to the Groq API for formatting.
- **Local model option** — Switch to the Local model for a fully air-gapped setup where nothing is transmitted externally.
