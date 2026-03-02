"""
app.py - HR Assistant terminal Q&A interface with debug output.

Run with:
    conda activate ai_base
    python app.py
"""

from src.rag.rag.memory import store
from src.rag.rag.prompts import ANSWER_PROMPT
from src.sql.sql_engine import run as sql_run
from src.rag.rag.orchestrator import generate_response

SESSION_ID = "terminal-session"
DEBUG = True   # set to False to hide SQL debug output


def main():
    print("\n" + "=" * 55)
    print("  HR Assistant  -  Ask me anything about employees")
    print("  Type 'exit' or 'quit' to stop")
    print("=" * 55 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if DEBUG:
            # Show the SQL and raw result before the LLM formats it
            sql, result = sql_run(user_input)
            print(f"\n[DEBUG] SQL  : {sql}")
            print(f"[DEBUG] Result:\n{result}\n")

        print("Assistant: ", end="", flush=True)
        answer = generate_response(user_input, session_id=SESSION_ID)
        print(answer)
        print()


if __name__ == "__main__":
    main()
