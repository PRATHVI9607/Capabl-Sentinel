"""LLM access with a two-provider fallback.

Routing follows the PRD: Gemini 2.0 Flash for reasoning and structured
extraction, Groq llama-3.1-8b for the short, frequent calls. If the preferred
provider errors (rate limit, outage) the other one is tried before giving up.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from functools import lru_cache
from typing import Any, TypeVar

from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)

Messages = Sequence[tuple[str, str]]


class LLMUnavailable(RuntimeError):
    """No configured provider could answer."""


@lru_cache(maxsize=1)
def _gemini() -> Any | None:
    if not settings.gemini_api_key:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        logger.error("GEMINI_API_KEY is set but langchain-google-genai is not installed.")
        return None

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.0,
    )


@lru_cache(maxsize=1)
def _groq() -> Any | None:
    if not settings.groq_api_key:
        return None
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        logger.error("GROQ_API_KEY is set but langchain-groq is not installed.")
        return None

    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.0,
    )


def _providers(*, fast: bool) -> list[tuple[str, Any]]:
    """Providers to try, in order, for this call.

    Groq leads both paths. The PRD put Gemini first for reasoning, but its free
    tier allows 20 generate_content requests per day on current flash models --
    four or five analyses before everything 429s. Groq's free allowance is
    orders of magnitude larger, so it carries the demo and Gemini is the
    fallback rather than the other way round. Set PREFER_GEMINI=true on a paid
    Gemini key to restore the original ordering.
    """
    order = [("gemini", _gemini), ("groq", _groq)]
    # Groq leads unless Gemini is explicitly preferred, and short classification
    # calls go to Groq either way -- they are the frequent ones, and spending a
    # 20/day quota on them is what exhausts it before the reasoning calls run.
    if fast or not settings.prefer_gemini:
        order.reverse()
    return [(name, llm) for name, factory in order if (llm := factory()) is not None]


def any_provider_configured() -> bool:
    return bool(_providers(fast=False))


async def complete_structured(messages: Messages, schema: type[TModel], *, fast: bool = False) -> TModel:
    """Return `schema` parsed from the model, trying each configured provider in turn."""
    return await _attempt(messages, fast=fast, bind=lambda llm: llm.with_structured_output(schema))


async def complete_text(messages: Messages, *, fast: bool = False) -> str:
    result = await _attempt(messages, fast=fast, bind=lambda llm: llm)
    return getattr(result, "content", str(result))


async def _attempt(messages: Messages, *, fast: bool, bind) -> Any:
    providers = _providers(fast=fast)
    if not providers:
        raise LLMUnavailable("No LLM configured. Set GEMINI_API_KEY or GROQ_API_KEY.")

    last_error: Exception | None = None
    for name, llm in providers:
        try:
            return await bind(llm).ainvoke(list(messages))
        except Exception as exc:  # noqa: BLE001 - any provider error is a reason to fall back
            logger.warning("LLM provider %s failed: %s", name, exc)
            last_error = exc
    raise LLMUnavailable("Every configured LLM provider failed") from last_error
