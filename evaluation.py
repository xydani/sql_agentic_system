import argparse
import re
import time

from main import run_legacy
from sql_agent.graph import answer_question, build_graph

DB_PATH = "data/shop.db"
REPETITIONS = 3
PAUSE_SECONDS = 2

QUESTIONS = [
    ("Quanti clienti italiani ci sono?", 40),
    ("Quanti ordini sono stati annullati?", 36),
    ("Quanti clienti non hanno un indirizzo email?", 20),
    ("Quanti clienti tedeschi ci sono?", 24),
    ("Qual e il fatturato totale escludendo gli ordini annullati?", 741458.03),
]

NUMBER = re.compile(r"\d[\d.,]*")


def numbers_in(text: str) -> set[float]:
    found = set()
    for match in NUMBER.finditer(text):
        token = match.group().rstrip(".,")
        if "," in token and "." in token:
            if token.rfind(",") > token.rfind("."):
                token = token.replace(".", "").replace(",", ".")
            else:
                token = token.replace(",", "")
        elif "," in token:
            head, _, tail = token.rpartition(",")
            token = f"{head.replace(',', '')}.{tail}" if len(tail) != 3 else token.replace(",", "")
        elif "." in token:
            head, _, tail = token.rpartition(".")
            if len(tail) == 3:
                token = token.replace(".", "")
        try:
            found.add(round(float(token), 2))
        except ValueError:
            pass
    return found


def is_correct(answer: str, expected: float) -> bool:
    return round(float(expected), 2) in numbers_in(answer)


def run_agent_once(question: str, run_id: str) -> str:
    graph = build_graph(DB_PATH)
    return answer_question(graph, question, thread_id=run_id)


def run_legacy_once(question: str, run_id: str) -> str:
    sql, outcome = run_legacy(question, DB_PATH)
    return outcome


SYSTEMS = {"agentico": run_agent_once, "di partenza": run_legacy_once}


def evaluate(repetitions: int) -> dict:
    results = {name: {q: 0 for q, _ in QUESTIONS} for name in SYSTEMS}
    for name, runner in SYSTEMS.items():
        for question, expected in QUESTIONS:
            for attempt in range(repetitions):
                try:
                    answer = runner(question, f"{name}-{attempt}-{hash(question)}")
                    ok = is_correct(answer, expected)
                except Exception as error:
                    answer, ok = f"{type(error).__name__}: {error}", False
                results[name][question] += int(ok)
                print(f"  [{name:11s}] {'ok ' if ok else 'NO '} {answer.strip()[:70]}")
                time.sleep(PAUSE_SECONDS)
            print()
    return results


def print_table(results: dict, repetitions: int) -> None:
    width = max(len(q) for q, _ in QUESTIONS)
    print(f"\n{'Domanda':{width}}  {'atteso':>10}  {'agentico':>9}  {'partenza':>9}")
    for question, expected in QUESTIONS:
        agent = results["agentico"][question]
        legacy = results["di partenza"][question]
        print(f"{question:{width}}  {expected:>10}  {agent:>6}/{repetitions}  {legacy:>6}/{repetitions}")

    total = len(QUESTIONS) * repetitions
    agent_total = sum(results["agentico"].values())
    legacy_total = sum(results["di partenza"].values())
    print(f"\n{'TOTALE':{width}}  {'':>10}  {agent_total:>6}/{total}  {legacy_total:>6}/{total}")
    print(f"{'':{width}}  {'':>10}  {agent_total / total:>8.0%}  {legacy_total / total:>8.0%}")


def print_typst(results: dict, repetitions: int) -> None:
    print("\n--- tabella per la relazione ---\n")
    for question, expected in QUESTIONS:
        agent = results["agentico"][question]
        legacy = results["di partenza"][question]
        print(f"    [{question}], [{expected}], [{agent}/{repetitions}], [{legacy}/{repetitions}],")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure how often each system answers correctly.")
    parser.add_argument("--repetitions", type=int, default=REPETITIONS)
    parser.add_argument("--typst", action="store_true", help="also print the table as typst rows")
    args = parser.parse_args()

    print(f"{len(QUESTIONS)} domande x {args.repetitions} ripetizioni x {len(SYSTEMS)} sistemi\n")
    results = evaluate(args.repetitions)
    print_table(results, args.repetitions)
    if args.typst:
        print_typst(results, args.repetitions)


if __name__ == "__main__":
    main()
