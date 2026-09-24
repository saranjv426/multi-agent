"""
CORS configuration helpers.
Enforces explicit origin allowlists when credentials are enabled.
"""

import re
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


def parse_allowed_origin_regex(regex_str: Optional[str]) -> Optional[str]:
    """
    Parse and validate optional ALLOWED_ORIGIN_REGEX.

    This is useful for provider preview URLs such as Vercel deployments while
    still avoiding a blanket '*' CORS policy with credentials enabled.
    """
    regex = (regex_str or "").strip()
    if not regex:
        return None
    if regex == ".*":
        raise ValueError("ALLOWED_ORIGIN_REGEX cannot allow every origin")
    re.compile(regex)
    return regex
