# NL → SQL agentic skeleton

Minimal skeleton for NL -> SQL agentic system:

```
NL query --> [agent: NL -> SQL] --> [executor: run SQL]
                    ^                        |
                    |____ error feedback ____|   (up to MAX_RETRIES)
```

## Files

- `schema_utils.py` — introspects the SQLite DB and turns it into a text
  block (`TABLE ... columns ... foreign keys ...`) that gets injected into
  the LLM prompt as context. This is the "context of the DB" part.
- `nl2sql_agent.py` — thin wrapper around the **Groq API** (free tier,
  no credit card, OpenAI-compatible chat endpoint, running Llama 3.3 70B
  on Groq's LPU hardware). Keeps a running message history per query so
  that when a SQL attempt fails, the error is appended as the next turn instead
  of starting from scratch — the model sees its own failed
  query + the exact DB error and self-corrects.
- `db_executor.py` — runs SQL in an isolated subprocess (so a bad/hanging
  query can't take down the loop), returns either rows or the exact
  exception text. Refuses write statements (INSERT/UPDATE/DELETE/DROP/ALTER)
  by default — flip `allow_writes=True` if you want the agent to mutate data.
- `main.py` — the retry loop: generate → execute → on failure, feed the
  error back to the agent → regenerate → repeat until success or
  `MAX_RETRIES` is hit.
- `example.db` — a tiny SQLite DB (`customers`, `orders`) so you can run
  the skeleton immediately without wiring up your own database.

## Run it

1. Get a free API key: https://console.groq.com/keys
2. Then:

```bash
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...

python main.py "Which customers have placed more than one order?"

# or interactively:
python main.py
```

## How the self-correction loop works

1. `NL2SQLAgent.start_query(schema, nl_query)` sends schema + question,
   gets back one SQL query (parsed out of a ` ```sql ` fence).
2. `execute_sql()` runs it. On a syntax/semantic error, SQLite raises an
   exception with a specific message (e.g. `no such column: custmoer_id`).
3. That exact error text — plus the failed query — is appended to the
   _same_ conversation via `agent.retry_with_error(sql, error)`. The model
   isn't starting over; it sees exactly what it tried and exactly what
   broke.
4. Loop until `execute_sql` succeeds or `MAX_RETRIES` (default 4) is hit.
