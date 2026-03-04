"""
sql_engine.py - Text-to-SQL engine for the HR Assistant.

Two-step pipeline:
  1. LLM receives the DB schema (+ optional conversation history) and generates a SQL SELECT query.
  2. SQLite executes the SQL locally and returns the result.

The result is then passed to the orchestrator, which calls the LLM again
to format it into a natural language answer.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd
import sqlparse

from src.chatbot.llm.providers import BaseProvider
from src.chatbot.llm.prompts import SQL_HISTORY_PREFIX
from src.chatbot.core.config import config

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
TABLE_NAME = "employees"

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

_SQL_GEN_BASE = f"""You are an expert SQL assistant for an HR database.
Given a user question, write ONE valid SQLite SELECT query that answers it.

Rules:
- Use ONLY the columns listed in the schema below.
- Use SELECT statements ONLY — no INSERT, UPDATE, DELETE, DROP.
- Column string values are case-sensitive (e.g. 'Yes', 'Sales', 'Female').
- Return ONLY the SQL query, no explanation, no markdown.

Schema:
{DB_SCHEMA}"""


# ── SQL extraction ────────────────────────────────────────────────────────────

def _extract_sql(text: str) -> str:
    """Strip markdown fences and return just the SELECT statement."""
    text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE).strip("`\n ")
    match = re.search(r"(SELECT\b.+?)(?:;|$)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text.strip()


# ── SQL safety check ──────────────────────────────────────────────────────────

def _is_safe(sql: str) -> bool:
    """
    Accept only a single SELECT statement.
    Uses sqlparse for reliable statement-type detection.
    """
    stmts = sqlparse.parse(sql.strip())
    if not stmts or len(stmts) != 1:
        return False
    if stmts[0].get_type() != "SELECT":
        return False
    # Belt-and-suspenders: reject dangerous keywords anywhere in the text
    dangerous = (
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "EXEC", "EXECUTE",
    )
    return not any(kw in sql.upper() for kw in dangerous)


# ── SQL generation ────────────────────────────────────────────────────────────

def generate_sql(
    question: str,
    provider: BaseProvider,
    history_msgs: Optional[list[dict]] = None,
) -> str:
    """
    Ask the LLM to generate a SQL SELECT query for the given question.

    Args:
        question:     The current user question.
        provider:     LLM backend (Groq or local).
        history_msgs: Prior conversation turns as [{"role":..., "content":...}] dicts.
                      Used to resolve follow-up references ("those employees", "same dept").
    """
    system_content = _SQL_GEN_BASE

    # Inject conversation history when available (last 3 turns = 6 messages max)
    if history_msgs:
        recent = history_msgs[-6:]
        history_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in recent
        )
        system_content += SQL_HISTORY_PREFIX.format(history=history_text)

    response = provider.chat_completion(
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user",   "content": question},
        ],
        max_tokens=256,
        temperature=0.0,
    )
    sql = _extract_sql(response)
    logger.debug("Generated SQL: %s", sql)
    return sql


# ── SQL execution ─────────────────────────────────────────────────────────────

def execute_sql(sql: str) -> str:
    """
    Execute a validated SQL query on the local SQLite DB and return
    the result as a formatted string.
    """
    if not _is_safe(sql):
        logger.warning("Unsafe SQL blocked: %s", sql)
        return "Error: Only SELECT queries are allowed."

    if not config.DB_PATH.exists():
        return (
            "Error: Database not found. "
            "Please run `python -m src.sql.db_setup` first."
        )

    conn = sqlite3.connect(config.DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            return "No results found."
        return df.head(config.SQL_MAX_ROWS).to_string(index=False)
    except Exception as e:
        logger.error("SQL execution error: %s", e)
        return f"SQL Error: {e}"
    finally:
        conn.close()


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run(
    question: str,
    provider: BaseProvider,
    history_msgs: Optional[list[dict]] = None,
) -> tuple[str, str]:
    """
    Full Text-to-SQL pipeline.

    Returns:
        (sql, result_str) — the generated SQL and its execution result.
    """
    sql    = generate_sql(question, provider, history_msgs)
    result = execute_sql(sql)
    return sql, result
