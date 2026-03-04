from agents.openai_compat import chat_completions_create_compat


class _DummyCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if "max_completion_tokens" in kwargs:
            raise TypeError("got an unexpected keyword argument 'max_completion_tokens'")
        return {"ok": True, "kwargs": kwargs}


class _DummyChat:
    def __init__(self):
        self.completions = _DummyCompletions()


class _DummyClient:
    def __init__(self):
        self.chat = _DummyChat()


def test_chat_completions_create_compat_falls_back_to_max_tokens():
    client = _DummyClient()

    result = chat_completions_create_compat(
        client,
        model="gpt-test",
        max_completion_tokens=123,
        messages=[{"role": "user", "content": "hello"}],
    )

    assert result["ok"] is True
    assert len(client.chat.completions.calls) == 2
    assert "max_completion_tokens" in client.chat.completions.calls[0]
    assert client.chat.completions.calls[1]["max_tokens"] == 123
