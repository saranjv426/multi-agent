"""
OpenAI SDK compatibility helpers.

Some SDK versions accept `max_completion_tokens`, while older variants only
accept `max_tokens` for `chat.completions.create()`.
"""

from typing import Any


def chat_completions_create_compat(client: Any, **kwargs: Any) -> Any:
    """
    Create a chat completion with backwards-compatible token-limit arguments.

    If the underlying SDK rejects `max_completion_tokens`, retry with
    `max_tokens`.
    """
    try:
        return client.chat.completions.create(**kwargs)
    except TypeError as exc:
        if "max_completion_tokens" not in str(exc):
            raise

        fallback_kwargs = dict(kwargs)
        max_completion_tokens = fallback_kwargs.pop("max_completion_tokens", None)
        if max_completion_tokens is not None and "max_tokens" not in fallback_kwargs:
            fallback_kwargs["max_tokens"] = max_completion_tokens

        return client.chat.completions.create(**fallback_kwargs)

