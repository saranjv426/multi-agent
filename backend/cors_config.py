"""
CORS configuration helpers.
Enforces explicit origin allowlists when credentials are enabled.
"""

from typing import List, Optional


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def parse_allowed_origins(origins_str: Optional[str]) -> List[str]:
    """
    Parse and validate ALLOWED_ORIGINS.

    Credentials are enabled for CORS in this app, so wildcard origins are not allowed.
    """
    if origins_str:
        origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    else:
        origins = DEFAULT_ALLOWED_ORIGINS.copy()

    if not origins:
        raise ValueError("ALLOWED_ORIGINS must contain at least one explicit origin")

    invalid = [origin for origin in origins if "*" in origin]
    if invalid:
        raise ValueError(
            "ALLOWED_ORIGINS cannot contain wildcard entries when allow_credentials=True. "
            f"Invalid values: {invalid}"
        )

    return origins
