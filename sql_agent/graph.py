from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from sql_agent.llm import get_llm
from sql_agent.tools import build_tools

MAX_REVISIONS = 2

AGENT_PROMPT = (
    "You answer questions about a SQL database by inspecting it with the tools provided.\n"
    "Work in this order:\n"
    "1. Find out which tables exist and what columns they have.\n"
    "2. Look at real rows before filtering on a column, so that you filter on values "
    "that exist in the data rather than on values you assumed.\n"
    "3. Run the query.\n"
    "4. State the figures you found, answering in the language of the question.\n"
    "Give the final answer once, as a single short sentence.\n"
    "If a query fails, read the database error and correct the query. "
    "Never invent table names, column names or column values."
)

VERIFIER_PROMPT = (
    "You audit answers taken from a SQL database. You are given a question, the steps "
    "an assistant took, and the answer it proposes. Decide whether that answer can be "
    "trusted on the evidence shown.\n"
    "Reject it if any of the following holds:\n"
    "- the SQL answers a different question from the one that was asked\n"
    "- the result is empty and was reported as a finding instead of being investigated\n"
    "- a count or a total was taken from rows marked as a truncated sample\n"
    "- the answer states something the returned rows do not show\n"
    "- no query was run at all\n"
    "Reply with exactly one line. Either:\n"
    "APPROVED\n"
    "or:\n"
    "REJECTED: <what is wrong and what to do instead>"
)

REVISION_REQUEST = (
    "A reviewer rejected that answer for the following reason:\n{problem}\n"
    "Investigate with the tools and answer again."
)


@dataclass
class Verification:
    answers_the_question: bool
    problem: str


def parse_verification(verdict: str) -> Verification:
    text = verdict.strip()
    if text.upper().startswith("APPROVED"):
        return Verification(True, "")
    return Verification(False, text.removeprefix("REJECTED").lstrip(": \n") or text)


def render_transcript(messages: list) -> str:
    lines = []
    for message in messages:
        if message.type == "human":
            lines.append(f"QUESTION: {message.text}")
        elif message.type == "tool":
            lines.append(f"  returned: {message.content}")
        elif message.type == "ai":
            for call in message.tool_calls:
                lines.append(f"  called {call['name']}({call['args']})")
            if message.text:
                lines.append(f"PROPOSED ANSWER: {message.text}")
    return "\n".join(lines)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    revisions: int
    approved: bool


def build_graph(db_path: str, model=None, max_revisions: int = MAX_REVISIONS):
    tools = build_tools(db_path)

    def chat_model():
        nonlocal model
        if model is None:
            model = get_llm()
        return model

    def run_agent(state: AgentState) -> dict:
        reply = chat_model().bind_tools(tools).invoke(
            [SystemMessage(AGENT_PROMPT)] + state["messages"]
        )
        return {"messages": [reply]}

    def verify_answer(state: AgentState) -> dict:
        review = chat_model().invoke(
            [SystemMessage(VERIFIER_PROMPT), HumanMessage(render_transcript(state["messages"]))]
        )
        verification = parse_verification(review.text)
        if verification.answers_the_question:
            return {"approved": True}
        return {
            "approved": False,
            "revisions": state["revisions"] + 1,
            "messages": [HumanMessage(REVISION_REQUEST.format(problem=verification.problem))],
        }

    def route_after_agent(state: AgentState) -> str:
        return "tools" if state["messages"][-1].tool_calls else "verify"

    def route_after_verification(state: AgentState) -> str:
        if state["approved"] or state["revisions"] > max_revisions:
            return END
        return "agent"

    builder = StateGraph(AgentState)
    builder.add_node("agent", run_agent)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("verify", verify_answer)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, ["tools", "verify"])
    builder.add_edge("tools", "agent")
    builder.add_conditional_edges("verify", route_after_verification, ["agent", END])

    return builder.compile(checkpointer=InMemorySaver())


def answer_question(graph, question: str, thread_id: str = "default") -> str:
    final_state = graph.invoke(
        {"messages": [HumanMessage(question)], "revisions": 0, "approved": False},
        config={"configurable": {"thread_id": thread_id}},
    )
    answers = [m for m in final_state["messages"] if isinstance(m, AIMessage) and m.text]
    return answers[-1].text if answers else "No answer was produced."


if __name__ == "__main__":
    print(build_graph("data/example.db").get_graph().draw_mermaid())
