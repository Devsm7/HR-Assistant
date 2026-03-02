"""
sql_engine.py - Text-to-SQL engine for the HR Assistant.

Two-step pipeline:
  1. LLM receives the DB schema and generates a SQL SELECT query.
  2. SQLite executes the SQL locally and returns the result.

The result is then passed to the orchestrator, which calls the LLM
again to format it into a natural language answer.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

# ── Config ────────────────────────────────────────────────────────────────────
_ENV_FILE    = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_FILE)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH      = PROJECT_ROOT / "hr.db"
TABLE_NAME   = "employees"
MODEL_ID     = "meta-llama/Meta-Llama-3-8B-Instruct"

_client = InferenceClient(model=MODEL_ID, token=os.getenv("HF_TOKEN"))

# ── Schema (sent to LLM with every SQL generation request) ───────────────────
DB_SCHEMA = """
Table: employees
Columns:
  Age                        INTEGER   -- employee age
  Attrition                  TEXT      -- 'Yes' or 'No'
  BusinessTravel             TEXT      -- 'Travel_Rarely', 'Travel_Frequently', 'Non-Travel'
  DailyRate                  INTEGER
  Department                 TEXT      -- 'Sales', 'Research & Development', 'Human Resources'
  DistanceFromHome           INTEGER
  Education                  TEXT      -- 'Below College','College','Bachelor','Master','Doctor'
  EducationField             TEXT      -- 'Life Sciences','Medical','Marketing','Technical Degree','Human Resources','Other'
  EmployeeCount              INTEGER
  EmployeeNumber             INTEGER   -- unique employee ID
  EnvironmentSatisfaction    TEXT      -- 'Low','Medium','High','Very High'
  Gender                     TEXT      -- 'Male' or 'Female'
  HourlyRate                 INTEGER
  JobInvolvement             TEXT      -- 'Low','Medium','High','Very High'
  JobLevel                   INTEGER   -- 1 to 5
  JobRole                    TEXT      -- e.g. 'Sales Executive','Research Scientist','Manager', etc.
  JobSatisfaction            TEXT      -- 'Low','Medium','High','Very High'
  MaritalStatus              TEXT      -- 'Single','Married','Divorced'
  MonthlyIncome              INTEGER
  MonthlyRate                INTEGER
  NumCompaniesWorked         INTEGER
  Over18                     TEXT      -- always 'Y'
  OverTime                   TEXT      -- 'Yes' or 'No'
  PercentSalaryHike          INTEGER
  PerformanceRating          TEXT      -- 'Excellent' or 'Outstanding'
  RelationshipSatisfaction   TEXT      -- 'Low','Medium','High','Very High'
  StandardHours              INTEGER   -- always 80
  StockOptionLevel           INTEGER   -- 0 to 3
  TotalWorkingYears          INTEGER
  TrainingTimesLastYear      INTEGER
  WorkLifeBalance            TEXT      -- 'Bad','Good','Better','Best'
  YearsAtCompany             INTEGER
  YearsInCurrentRole         INTEGER
  YearsSinceLastPromotion    INTEGER
  YearsWithCurrManager       INTEGER
"""

SQL_GEN_SYSTEM = f"""You are an expert SQL assistant for an HR database.
Given a user question, write ONE valid SQLite SELECT query that answers it.

Rules:
- Use ONLY the columns listed in the schema below.
- Use SELECT statements ONLY — no INSERT, UPDATE, DELETE, DROP.
- Column string values are case-sensitive (e.g. 'Yes', 'Sales', 'Female').
- Return ONLY the SQL query, no explanation, no markdown.

Schema:
{DB_SCHEMA}
"""


def _extract_sql(text: str) -> str:
    """Extract the SQL query from the LLM output (strip markdown fences if any)."""
    # Strip ```sql ... ``` fences
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE).strip("`\n ")
    # Take only up to the first semicolon
    match = re.search(r"(SELECT\b.+?)(?:;|$)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def _is_safe(sql: str) -> bool:
    """Only allow SELECT statements."""
    stripped = sql.strip().upper()
    return stripped.startswith("SELECT") and not any(
        kw in stripped for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE")
    )


def generate_sql(question: str) -> str:
    """Ask the LLM to generate a SQL query for the given question."""
    response = _client.chat_completion(
        messages=[
            {"role": "system", "content": SQL_GEN_SYSTEM},
            {"role": "user",   "content": question},
        ],
        max_tokens=256,
        temperature=0.0,
    )
    raw = response.choices[0].message.content.strip()
    return _extract_sql(raw)


def execute_sql(sql: str) -> str:
    """
    Execute a validated SQL query on the local SQLite DB and return
    the result as a formatted string.
    """
    if not _is_safe(sql):
        return "Error: Only SELECT queries are allowed."

    if not DB_PATH.exists():
        return (
            "Error: Database not found. "
            "Please run `python -m src.sql.db_setup` first."
        )

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            return "No results found."
        # Return at most 50 rows to avoid overwhelming the LLM
        return df.head(50).to_string(index=False)
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()


def run(question: str) -> tuple[str, str]:
    """
    Full Text-to-SQL pipeline.

    Returns:
        (sql, result_str) — the generated SQL and its execution result.
    """
    sql    = generate_sql(question)
    result = execute_sql(sql)
    return sql, result
