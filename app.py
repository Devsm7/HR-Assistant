"""
app.py - HR Assistant terminal Q&A interface with debug output.

Run with:
    conda activate ai_base
    python app.py
"""

import asyncio

from src.chatbot.llm.orchestrator import generate_response
from src.chatbot.llm.providers import ModelChoice
from src.sql.sql_engine import run as sql_run


SESSION_ID = "terminal-session"
DEBUG      = True   # set to False to hide SQL debug output


def _pick_model() -> ModelChoice:
    """Ask the user which model to use for the session."""
    print("\nSelect model:")
    print("  [g] Groq  — llama-3.3-70b-versatile (fast, cloud)")
    print("  [l] Local — Qwen/Qwen2.5-7B-Instruct (downloaded, runs on device)")
    while True:
        choice = input("Choice [g/l]: ").strip().lower()
        if choice in ("g", "groq", ""):
            return ModelChoice.GROQ
        if choice in ("l", "local"):
            return ModelChoice.LOCAL
        print("  Please enter 'g' for Groq or 'l' for Local.")


def main() -> None:
    print("\n" + "=" * 55)
    print("  HR Assistant  -  Ask me anything about employees")
    print("  Type 'exit' or 'quit' to stop")
    print("=" * 55)

    model_choice = _pick_model()
    print(f"\nUsing model: {model_choice.value}\n")

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

        try:
            answer, sql = asyncio.run(
                generate_response(user_input, session_id=SESSION_ID, model_choice=model_choice)
            )
        except Exception as exc:
            print(f"Error: {exc}")
            continue

        if DEBUG:
            print(f"\n[DEBUG] SQL: {sql}\n")

        print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    main()
