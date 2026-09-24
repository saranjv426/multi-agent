from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from cors_config import parse_allowed_origin_regex, parse_allowed_origins


def test_parse_allowed_origins_accepts_explicit_allowlist():
    origins = parse_allowed_origins("http://localhost:3000,https://app.example.com")
    assert origins == ["http://localhost:3000", "https://app.example.com"]


def test_parse_allowed_origins_uses_safe_defaults_when_empty():
    origins = parse_allowed_origins("")
    assert origins == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_parse_allowed_origins_rejects_wildcard_entries():
    try:
        parse_allowed_origins("http://localhost:3000,*")
        assert False, "Expected ValueError for wildcard origin"
    except ValueError as exc:
        assert "cannot contain wildcard entries" in str(exc)


def test_parse_allowed_origins_rejects_wildcard_like_patterns():
    try:
        parse_allowed_origins("https://*.vercel.app")
        assert False, "Expected ValueError for wildcard-like origin"
    except ValueError as exc:
        assert "cannot contain wildcard entries" in str(exc)


def test_parse_allowed_origin_regex_accepts_preview_pattern():
    regex = parse_allowed_origin_regex(r"https://multi-agent-system-[a-z0-9-]+-nnawaris-projects\.vercel\.app")

    assert regex == r"https://multi-agent-system-[a-z0-9-]+-nnawaris-projects\.vercel\.app"


def test_parse_allowed_origin_regex_rejects_allow_all_pattern():
    try:
        parse_allowed_origin_regex(".*")
        assert False, "Expected ValueError for allow-all regex"
    except ValueError as exc:
        assert "cannot allow every origin" in str(exc)


def _build_test_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    return app


def test_cors_preflight_allows_only_approved_origins():
    client = TestClient(_build_test_app())

    allowed = client.options(
        "/ping",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert allowed.headers.get("access-control-allow-credentials") == "true"

    denied = client.options(
        "/ping",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert denied.status_code in (200, 400)
    assert denied.headers.get("access-control-allow-origin") != "https://evil.example.com"
