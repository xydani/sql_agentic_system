import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from sql_agent.graph import answer_question, build_graph, parse_verification, render_transcript

EXAMPLE_DB = "data/example.db"


class ScriptedRunnable:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def invoke(self, messages, *args, **kwargs):
        self.calls += 1
        return self.replies.pop(0) if self.replies else self.replies_exhausted()

    def replies_exhausted(self):
        raise AssertionError("the graph asked for more replies than the test scripted")


class ScriptedModel:
    def __init__(self, agent_replies, verdicts):
        self.agent = ScriptedRunnable(agent_replies)
        self.verifier = ScriptedRunnable(verdicts)

    def bind_tools(self, tools):
        return self.agent

    def invoke(self, messages, *args, **kwargs):
        return self.verifier.invoke(messages)


def approved():
    return AIMessage("APPROVED")


def rejected(problem="The query counted orders, not customers."):
    return AIMessage(f"REJECTED: {problem}")


def test_approved_answer_is_returned_without_revision():
    model = ScriptedModel([AIMessage("There are 3 customers.")], [approved()])
    graph = build_graph(EXAMPLE_DB, model=model)

    assert answer_question(graph, "How many customers?") == "There are 3 customers."
    assert model.agent.calls == 1


def test_rejected_answer_sends_the_agent_back_with_the_reason():
    model = ScriptedModel(
        [AIMessage("There are 4 customers."), AIMessage("There are 3 customers.")],
        [rejected(), approved()],
    )
    graph = build_graph(EXAMPLE_DB, model=model)

    assert answer_question(graph, "How many customers?") == "There are 3 customers."
    assert model.agent.calls == 2


def test_revision_reason_reaches_the_agent():
    model = ScriptedModel(
        [AIMessage("wrong"), AIMessage("right")],
        [rejected("You counted orders, not customers."), approved()],
    )
    graph = build_graph(EXAMPLE_DB, model=model)
    answer_question(graph, "How many customers?", thread_id="reason")

    history = graph.get_state({"configurable": {"thread_id": "reason"}}).values["messages"]
    assert any("You counted orders, not customers." in m.text for m in history)


def test_revisions_are_capped():
    model = ScriptedModel(
        [AIMessage("a"), AIMessage("b"), AIMessage("c"), AIMessage("d")],
        [rejected(), rejected(), rejected(), rejected()],
    )
    graph = build_graph(EXAMPLE_DB, model=model, max_revisions=2)
    answer_question(graph, "How many customers?", thread_id="capped")

    state = graph.get_state({"configurable": {"thread_id": "capped"}}).values
    assert state["approved"] is False
    assert model.agent.calls == 3


def test_tool_calls_are_executed_before_verification():
    model = ScriptedModel(
        [
            AIMessage("", tool_calls=[{"name": "list_tables", "args": {}, "id": "t1"}]),
            AIMessage("The tables are customers and orders."),
        ],
        [approved()],
    )
    graph = build_graph(EXAMPLE_DB, model=model)
    answer_question(graph, "Which tables exist?", thread_id="tools")

    history = graph.get_state({"configurable": {"thread_id": "tools"}}).values["messages"]
    assert any(getattr(m, "name", None) == "list_tables" for m in history)
    assert any("customers\norders" == m.content for m in history)


def test_memory_is_kept_per_thread():
    model = ScriptedModel([AIMessage("first"), AIMessage("second")], [approved(), approved()])
    graph = build_graph(EXAMPLE_DB, model=model)

    answer_question(graph, "question one", thread_id="shared")
    answer_question(graph, "question two", thread_id="shared")

    history = graph.get_state({"configurable": {"thread_id": "shared"}}).values["messages"]
    assert [m.text for m in history if m.type == "human"] == ["question one", "question two"]


def test_separate_threads_do_not_share_history():
    model = ScriptedModel([AIMessage("first"), AIMessage("second")], [approved(), approved()])
    graph = build_graph(EXAMPLE_DB, model=model)

    answer_question(graph, "question one", thread_id="a")
    answer_question(graph, "question two", thread_id="b")

    history = graph.get_state({"configurable": {"thread_id": "b"}}).values["messages"]
    assert [m.text for m in history if m.type == "human"] == ["question two"]


def test_graph_shape():
    graph = build_graph(EXAMPLE_DB, model=ScriptedModel([], []))
    diagram = graph.get_graph().draw_mermaid()

    for node in ("agent", "tools", "verify"):
        assert node in diagram
    assert "tools --> agent" in diagram


@pytest.mark.parametrize("verdict", ["APPROVED", "approved", "  APPROVED  "])
def test_approval_is_parsed(verdict):
    assert parse_verification(verdict).answers_the_question


@pytest.mark.parametrize("verdict", [
    "REJECTED: you counted orders",
    "rejected - you counted orders",
    "The answer is wrong because you counted orders",
    "",
])
def test_anything_that_is_not_approval_is_a_rejection(verdict):
    assert not parse_verification(verdict).answers_the_question


def test_rejection_keeps_the_reason():
    assert parse_verification("REJECTED: you counted orders").problem == "you counted orders"


def test_transcript_shows_question_steps_and_answer():
    transcript = render_transcript([
        HumanMessage("How many customers?"),
        AIMessage("", tool_calls=[{"name": "run_select", "args": {"sql": "SELECT 1"}, "id": "x"}]),
        ToolMessage(content="1\n(1 rows)", tool_call_id="x"),
        AIMessage("There is 1."),
    ])
    assert "QUESTION: How many customers?" in transcript
    assert "called run_select" in transcript
    assert "returned: 1\n(1 rows)" in transcript
    assert "PROPOSED ANSWER: There is 1." in transcript


def test_sql_error_is_fed_back_to_the_agent():
    broken = AIMessage("", tool_calls=[
        {"name": "run_select", "args": {"sql": "SELECT * FROM custmoer"}, "id": "bad"}])
    fixed = AIMessage("", tool_calls=[
        {"name": "run_select", "args": {"sql": "SELECT name FROM customers"}, "id": "good"}])
    model = ScriptedModel([broken, fixed, AIMessage("Alice, Bob and Chen.")], [approved()])

    graph = build_graph(EXAMPLE_DB, model=model)
    answer_question(graph, "Who are the customers?", thread_id="selfcorrect")

    history = graph.get_state({"configurable": {"thread_id": "selfcorrect"}}).values["messages"]
    errors = [m.content for m in history if m.type == "tool" and "failed" in m.content]
    assert errors and "no such table: custmoer" in errors[0]
    assert any(m.type == "tool" and "Alice Rossi" in m.content for m in history)
    assert model.agent.calls == 3
