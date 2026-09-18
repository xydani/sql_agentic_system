"""
llm.py

Builds the chat model used by the agent. Which provider is used is a
configuration choice, not a code change: set LLM_PROVIDER to "groq" or
"gemini". Both have a free tier; Gemini's token-per-minute allowance is
far larger, which matters when the agent makes several calls per question.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

PROVIDERS = {
    "groq": {
        "backend": "groq",
        "model": "openai/gpt-oss-120b",
        "key": "GROQ_API_KEY",
        "console": "https://console.groq.com/keys",
    },
    "gemini": {
        "backend": "google_genai",
        "model": "gemini-3.8-flash",
        "key": "GOOGLE_API_KEY",
        "console": "https://aistudio.google.com/apikey",
    },
}

DEFAULT_PROVIDER = "groq"


def get_llm(provider: str | None = None, model: str | None = None, temperature: float = 0.0):
    name = (provider or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()

    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER {name!r}. Available: {', '.join(sorted(PROVIDERS))}."
        )

    config = PROVIDERS[name]
    if not os.environ.get(config["key"]):
        raise RuntimeError(
            f"{config['key']} is not set, so provider {name!r} cannot be used. "
            f"Get a free key at {config['console']} and put it in your .env file."
        )

    return init_chat_model(
        model or os.environ.get("LLM_MODEL") or config["model"],
        model_provider=config["backend"],
        temperature=temperature,
    )


def describe_active_llm() -> str:
    name = (os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    config = PROVIDERS.get(name)
    if config is None:
        return f"unknown provider {name!r}"
    return f"{name} / {os.environ.get('LLM_MODEL') or config['model']}"


if __name__ == "__main__":
    print(f"Provider: {describe_active_llm()}")
    print(get_llm().invoke("Reply with exactly: ok").text)
