import pytest

from app.api.chats import _sse


def test_sse_event_format():
    payload = _sse("token", "hello")

    assert payload == 'event: token\ndata: "hello"\n\n'


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        ("sources", "event: sources"),
        ("done", "event: done"),
        ("error", "event: error"),
    ],
)
def test_sse_event_names(event: str, expected: str):
    assert _sse(event, {}).startswith(expected)
