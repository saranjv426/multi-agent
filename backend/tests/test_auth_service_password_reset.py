import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from auth.service import AuthenticationService


def test_forgot_password_returns_deprecated_endpoint_message():
    security = MagicMock()
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)
    db = MagicMock()

    result = asyncio.run(
        service.forgot_password(db, "user@example.com", "http://localhost:3000")
    )

    assert result["success"] is True
    assert result["message"] == "Deprecated endpoint"
    db.add.assert_not_called()
    db.commit.assert_not_called()
    email_service.send_password_reset_email.assert_not_called()


def test_reset_password_requires_minimum_length():
    security = MagicMock()
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)
    db = MagicMock()

    result = asyncio.run(service.reset_password(db, "user@example.com", "short"))

    assert result["success"] is False
    assert result["error"] == "Password must be at least 8 characters long"
    db.commit.assert_not_called()


def test_reset_password_returns_user_not_found_for_unknown_email():
    security = MagicMock()
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = asyncio.run(service.reset_password(db, "missing@example.com", "ValidPass123"))

    assert result["success"] is False
    assert result["error"] == "User not found"
    db.commit.assert_not_called()


def test_reset_password_with_existing_email_updates_password():
    security = MagicMock()
    security.verify_password.return_value = False
    security.hash_password.return_value = "new-hash"
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)

    user = SimpleNamespace(email="user@example.com", password_hash="old-hash")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user

    result = asyncio.run(service.reset_password(db, "user@example.com", "ValidPass123"))

    assert result["success"] is True
    assert result["message"] == "Password reset successfully"
    assert user.password_hash == "new-hash"
    db.commit.assert_called_once()


def test_reset_password_rejects_same_as_current_password():
    security = MagicMock()
    security.verify_password.return_value = True
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)

    user = SimpleNamespace(email="user@example.com", password_hash="existing-hash")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user

    result = asyncio.run(service.reset_password(db, "user@example.com", "SamePass123"))

    assert result["success"] is False
    assert result["error"] == "New password must be different from current password"
    db.commit.assert_not_called()


def test_get_user_by_token_normalizes_uuid_subject_before_lookup():
    security = MagicMock()
    user_id = uuid4()
    security.verify_token.return_value = {"sub": str(user_id)}
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)

    user = SimpleNamespace(id=user_id, email="user@example.com", created_at=SimpleNamespace(isoformat=lambda: "2026-04-01T00:00:00"), is_active=True)
    db = MagicMock()
    filter_mock = db.query.return_value.filter
    filter_mock.return_value.first.return_value = user

    result = asyncio.run(service.get_user_by_token(db, "token"))

    assert result == {
        "id": str(user_id),
        "email": "user@example.com",
        "created_at": "2026-04-01T00:00:00",
    }
    passed_expression = filter_mock.call_args.args[0]
    assert passed_expression.right.value == user_id


def test_get_user_by_token_rejects_invalid_uuid_subject():
    security = MagicMock()
    security.verify_token.return_value = {"sub": "not-a-uuid"}
    email_service = MagicMock()
    service = AuthenticationService(security, email_service)
    db = MagicMock()

    result = asyncio.run(service.get_user_by_token(db, "token"))

    assert result is None
    db.query.assert_not_called()
