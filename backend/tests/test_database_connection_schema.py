from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

import database.connection as connection_module
from database.connection import DatabaseManager, get_local_sqlite_url, validate_schema_name


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
        assert kwargs["connect_args"] == {"check_same_thread": False}


def test_get_local_sqlite_url_defaults_to_backend_local_db(monkeypatch):
    monkeypatch.delenv("LOCAL_DATABASE_URL", raising=False)

    sqlite_url = get_local_sqlite_url()

    assert sqlite_url.startswith("sqlite:///")
    assert sqlite_url.endswith("/backend/local_dev.db")


def test_init_database_falls_back_to_sqlite_in_development(monkeypatch):
    postgres_manager = object.__new__(DatabaseManager)
    postgres_manager._is_postgres = True
    postgres_manager.create_tables = lambda: (_ for _ in ()).throw(
        OperationalError("statement", {}, Exception("db down"))
    )

    sqlite_manager = object.__new__(DatabaseManager)
    sqlite_manager._is_postgres = False
    sqlite_manager.create_tables = lambda: None
    sqlite_manager.test_connection = lambda: True

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("ENABLE_SQLITE_FALLBACK", "true")
    monkeypatch.setattr(connection_module, "db_manager", None)

    with patch(
        "database.connection.get_database_manager",
        return_value=postgres_manager,
    ), patch(
        "database.connection.get_local_sqlite_url",
        return_value="sqlite:///tmp/test.db",
    ), patch(
        "database.connection.DatabaseManager",
        return_value=sqlite_manager,
    ) as mock_db_manager:
        assert connection_module.init_database() is True
        assert connection_module.db_manager is sqlite_manager
        mock_db_manager.assert_called_once_with("sqlite:///tmp/test.db", db_schema="public")
