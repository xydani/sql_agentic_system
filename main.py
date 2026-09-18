import argparse
from pathlib import Path

from legacy.nl2sql_agent import NL2SQLAgent
from sql_agent.db_executor import execute_sql
from sql_agent.graph import answer_question, build_graph
from sql_agent.llm import PROVIDERS, describe_active_llm
from sql_agent.schema_utils import get_schema_description
from sql_agent.tools import format_table

DB_PATH = "data/example.db"
LEGACY_MAX_RETRIES = 4
SESSION = "cli"


def run_legacy(question: str, db_path: str) -> tuple[str, str]:
    agent = NL2SQLAgent(model=PROVIDERS["groq"]["model"])
    sql = agent.start_query(get_schema_description(db_path), question)

    for attempt in range(LEGACY_MAX_RETRIES):
        result = execute_sql(db_path, sql)
        if result.success:
            return sql, format_table(result.columns, result.rows, result.truncated)
        if attempt == LEGACY_MAX_RETRIES - 1:
            return sql, f"FAILED: {result.error}"
        sql = agent.retry_with_error(sql, result.error)


def print_trace(graph, thread_id: str) -> None:
    messages = graph.get_state({"configurable": {"thread_id": thread_id}}).values["messages"]
    print("\n  steps taken:")
    for message in messages:
        for call in getattr(message, "tool_calls", []):
            print(f"    {call['name']}({call['args']})")


def ask(graph, question: str, show_trace: bool) -> None:
    print(f"\n{answer_question(graph, question, thread_id=SESSION)}")
    if show_trace:
        print_trace(graph, SESSION)


def compare(question: str, db_path: str) -> None:
    print(f"\nQuestion: {question}")

    print("\n--- before: fixed pipeline, retries only on SQL errors ---")
    sql, outcome = run_legacy(question, db_path)
    print(f"  {sql}\n  {outcome}")

    print("\n--- after: agent that inspects the database ---")
    graph = build_graph(db_path)
    print(f"  {answer_question(graph, question, thread_id='comparison')}")
    print_trace(graph, "comparison")


def interactive(graph, show_trace: bool) -> None:
    print(f"Ask a question, or 'exit' to quit. Model: {describe_active_llm()}")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if question.lower() in ("exit", "quit"):
            return
        if question:
            ask(graph, question, show_trace)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions about a SQL database.")
    parser.add_argument("question", nargs="*", help="question to answer; omit for interactive mode")
    parser.add_argument("--db", default=DB_PATH, help=f"database to query (default: {DB_PATH})")
    parser.add_argument("--trace", action="store_true", help="show the tools the agent called")
    parser.add_argument("--compare", action="store_true", help="answer with both the old and new system")
    parser.add_argument("--diagram", action="store_true", help="print the graph as a mermaid diagram")
    args = parser.parse_args()

    if not Path(args.db).is_file():
        parser.error(f"database not found: {args.db}")

    question = " ".join(args.question)

    if args.diagram:
        print(build_graph(args.db).get_graph().draw_mermaid())
    elif args.compare:
        if not question:
            parser.error("--compare needs a question")
        compare(question, args.db)
    elif question:
        ask(build_graph(args.db), question, args.trace)
    else:
        interactive(build_graph(args.db), args.trace)


if __name__ == "__main__":
    main()
