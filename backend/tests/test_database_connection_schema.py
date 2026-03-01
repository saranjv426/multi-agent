from unittest.mock import patch

import pytest

from database.connection import DatabaseManager, validate_schema_name


def test_validate_schema_name_defaults_to_public_when_empty():
    assert validate_schema_name("") == "public"
    assert validate_schema_name("   ") == "public"


def test_validate_schema_name_rejects_invalid_identifiers():
    with pytest.raises(ValueError):
        validate_schema_name("1dev")
    with pytest.raises(ValueError):
        validate_schema_name("dev-schema")
    with pytest.raises(ValueError):
        validate_schema_name("public;drop table users")


def test_database_manager_sets_postgres_search_path_connect_arg():
    with patch("database.connection.create_engine") as mock_create_engine, patch(
        "database.connection.sessionmaker"
    ) as mock_sessionmaker:
        mock_create_engine.return_value = object()
        mock_sessionmaker.return_value = object()

        DatabaseManager("postgresql://user:pass@host:5432/db", db_schema="dev")

        assert mock_create_engine.call_count == 1
        kwargs = mock_create_engine.call_args.kwargs
        assert kwargs["connect_args"]["options"] == "-csearch_path=dev,public"


def test_database_manager_uses_empty_connect_args_for_non_postgres_url():
    with patch("database.connection.create_engine") as mock_create_engine, patch(
        "database.connection.sessionmaker"
    ) as mock_sessionmaker:
        mock_create_engine.return_value = object()
        mock_sessionmaker.return_value = object()

        DatabaseManager("sqlite:///test.db", db_schema="dev")

        kwargs = mock_create_engine.call_args.kwargs
        assert kwargs["connect_args"] == {}
