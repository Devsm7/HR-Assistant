# HR Assistant (Text-to-SQL)

An intelligent, terminal-based HR Assistant powered by Large Language Models. Instead of traditional RAG semantic search, this project uses a powerful **Text-to-SQL architecture** to provide 100% mathematically accurate answers to complex HR analytics questions.

## How It Works

1. **User asks a question:** "How many employees are in Sales?" or "What is the average income in R&D?"
2. **SQL Generation:** The LLM receives the HR database schema and translates the natural language question into a valid `SELECT` SQLite query.
3. **Execution:** The SQL query executes locally against an embedded SQLite database (`hr.db`), safely fetching exact counts, averages, and group distributions.
4. **Answer Formatting:** The raw database results are fed back to the LLM to format into a clean, professional, and easy-to-read natural language response.

*Note: By replacing Retrieval-Augmented Generation (RAG) with Text-to-SQL for highly structured datasets, this assistant entirely eliminates "counting hallucinations" and guarantees exact figures.*

## Tech Stack
- **Python 3.10+**
- **LLM Engine:** HuggingFace Inference API (`meta-llama/Meta-Llama-3-8B-Instruct`)
- **Database:** SQLite & Pandas
- **Conversation State:** In-memory tracking for context-aware follow-up questions

---

## 🚀 Setup & Installation

### 1. Requirements
Ensure you have Conda installed. Create and activate a new environment:
```bash
conda create -n ai_base python=3.10
conda activate ai_base
pip install -r requirements.txt
```

### 2. Environment Variables
You need a free HuggingFace API token to call the LLM endpoint:
1. Get a token from [HuggingFace settings](https://huggingface.co/settings/tokens)
2. Create a `.env` file in the project directory
3. Add your token:
   ```env
   HF_TOKEN=hf_your_token_here
   ```

### 3. Database Initialization
Before running the bot, convert the downloaded HR CSV dataset into the local SQLite database. You only need to run this once:
```bash
conda run -n ai_base python -m src.sql.db_setup
```

---

## 🏃 Usage

Launch the terminal interaction loop:
```bash
conda activate ai_base
python app.py
```

### Example Questions
- **Simple Counts:** "How many employees are in the Research & Development department?"
- **Aggregations:** "What is the average monthly income for male vs female employees?"
- **Complex Filters:** "Which job role has the highest attrition rate?"
- **Conversational Queries:**
  - *You:* "How many employees left the company?"
  - *Assistant:* "Based on the records, 237 employees have left."
  - *You:* "Which department did they mostly come from?" (Memory tracks context)

## Project Structure
```text
HR-Assistant/
├── .env                  # HF API Token (not tracked in git)
├── .gitignore            # Git config
├── app.py                # Main terminal loop and entry point
├── hr.db                 # Auto-generated SQLite database
├── dataset/              # Source CSV data (hr_Employee_data_decoded.csv)
├── src/
│   ├── sql/
│   │   ├── db_setup.py   # One-time script to convert CSV -> SQLite
│   │   └── sql_engine.py # Core LLM SQL generator & local executor
│   └── rag/rag/
│       ├── memory.py     # Tracks conversation context (history)
│       ├── prompts.py    # Answer formatting instructions
│       └── orchestrator.py # Ties SQL execution, formatting, and memory together
```

## Security Notice
- The SQLite execution layer validates that ONLY `SELECT` statements are executed to prevent SQL injection or destructive LLM behaviors (`DROP`, `DELETE`, etc.).
- Your actual HR data **never leaves your local machine**. Only the Database schema (column names/types) and the SQL query results string are transmitted to the HuggingFace API for natural language formatting.
