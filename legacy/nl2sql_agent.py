"""
nl2sql_agent.py

Wraps the Groq API (free tier, no credit card required) to turn a
natural-language question + DB schema into a SQL query. Groq's endpoint
is OpenAI-compatible chat completions, so swapping providers later
(OpenAI, local Ollama, etc.) only means changing the client + model name
below - the rest of the pipeline (schema_utils, db_executor, main) is
provider-agnostic.

Get a free API key (no credit card) at https://console.groq.com/keys
"""

import os
import re

from groq import Groq

# Free-tier model on Groq's LPU hardware. Good balance of quality/speed
# for SQL generation. Swap for "llama-3.1-8b-instant" for a faster/
# lower-quality option, or "openai/gpt-oss-120b" for a stronger one -
# check console.groq.com for current free-tier limits per model.
MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """You are a careful SQL generation agent for a SQLite database.

You will be given the database schema and a user's natural-language request.
Respond with EXACTLY ONE SQL query that answers the request, and nothing else
of substance in prose. Wrap the query in a ```sql ... ``` code block.

Rules:
- Only use tables/columns that appear in the schema below. Never invent columns.
- Prefer SELECT statements. Do not write DDL/DML unless explicitly asked.
- If a previous attempt failed, you will be shown the exact database error.
  Fix the query to address that specific error - do not just resubmit the same query.
- Keep the query as simple as possible while still correctly answering the request.
"""


class NL2SQLAgent:
    def __init__(self, api_key: str | None = None, model: str = MODEL):
        self.client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))
        self.model = model
        # Groq's chat API wants the system prompt as a message, not a
        # separate top-level param (unlike Anthropic's `system=` kwarg).
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _extract_sql(self, text: str) -> str:
        match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(";")
        return text.strip().rstrip(";")

    def start_query(self, schema: str, nl_query: str) -> str:
        #First attempt: build the initial prompt from schema + user question.
        user_msg = f"""Database schema:   {schema}  User request: {nl_query}"""
        self.history.append({"role": "user", "content": user_msg})
        return self._call()

    def retry_with_error(self, failed_sql: str, db_error: str) -> str:
        #Feed the failed SQL and the exact DB error back to the model.
        followup = f"""That query failed when executed against the database. Query that failed:```sql {failed_sql}```    Database error:    {db_error}    Please provide a corrected query."""
        self.history.append({"role": "user", "content": followup})
        return self._call()

    def _call(self) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            messages=self.history,
        )
        text = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": text})
        return self._extract_sql(text)
