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
    `extra_body={"max_completion_tokens": ...}` first, then `max_tokens` as a
    final fallback for older non-reasoning models/providers.
    """
    try:
        return client.chat.completions.create(**kwargs)
    except TypeError as exc:
        if "max_completion_tokens" not in str(exc):
            raise

        max_completion_tokens = kwargs.get("max_completion_tokens")
        if max_completion_tokens is None:
            raise

        extra_body_kwargs = dict(kwargs)
        extra_body_kwargs.pop("max_completion_tokens", None)
        extra_body = dict(extra_body_kwargs.get("extra_body") or {})
        extra_body["max_completion_tokens"] = max_completion_tokens
        extra_body_kwargs["extra_body"] = extra_body

        try:
            return client.chat.completions.create(**extra_body_kwargs)
        except Exception as retry_exc:
            retry_message = str(retry_exc)
            if "max_completion_tokens" in retry_message or "Unsupported parameter" in retry_message:
                raise

        fallback_kwargs = dict(kwargs)
        fallback_kwargs.pop("max_completion_tokens", None)
        if "max_tokens" not in fallback_kwargs:
            fallback_kwargs["max_tokens"] = max_completion_tokens

        return client.chat.completions.create(**fallback_kwargs)
