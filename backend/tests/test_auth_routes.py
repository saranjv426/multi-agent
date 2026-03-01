from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.routes import router, get_auth_service
from database.connection import get_db


class StubAuthService:
    def __init__(self):
        self.forgot_calls = []
        self.reset_calls = []
        self.forgot_result = {"success": True, "message": "ok"}
        self.reset_result = {"success": True, "message": "ok"}
        self.raise_on_forgot = False

    async def forgot_password(self, db, email, frontend_url):
        self.forgot_calls.append(
            {
                "db": db,
                "email": email,
                "frontend_url": frontend_url,
            }
        )
        if self.raise_on_forgot:
            raise RuntimeError("email backend unavailable")
        return self.forgot_result

    async def reset_password(self, db, email, new_password):
        self.reset_calls.append(
            {
                "db": db,
                "email": email,
                "new_password": new_password,
            }
        )
        return self.reset_result


def create_client(stub_service: StubAuthService):
    app = FastAPI()
    app.include_router(router)

    fake_db = object()

    def override_auth_service():
        return stub_service

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_auth_service] = override_auth_service
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), fake_db


def test_forgot_password_calls_backend_and_returns_generic_success():
    stub = StubAuthService()
    client, fake_db = create_client(stub)

    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Use email and new password in reset password form",
        "error": None,
        "user": None,
        "access_token": None,
        "token_type": None,
    }
    assert len(stub.forgot_calls) == 1
    assert stub.forgot_calls[0]["email"] == "user@example.com"
    assert stub.forgot_calls[0]["frontend_url"] == ""
    assert stub.forgot_calls[0]["db"] is fake_db


def test_forgot_password_still_returns_generic_success_on_service_error():
    stub = StubAuthService()
    stub.raise_on_forgot = True
    client, _ = create_client(stub)

    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Use email and new password in reset password form"


def test_reset_password_success_returns_200():
    stub = StubAuthService()
    client, fake_db = create_client(stub)

    response = client.post(
        "/api/auth/reset-password",
        json={"email": "user@example.com", "new_password": "ValidPass123"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Password reset successfully"
    assert len(stub.reset_calls) == 1
    assert stub.reset_calls[0]["email"] == "user@example.com"
    assert stub.reset_calls[0]["new_password"] == "ValidPass123"
    assert stub.reset_calls[0]["db"] is fake_db


def test_reset_password_unknown_email_returns_400():
    stub = StubAuthService()
    stub.reset_result = {"success": False, "error": "User not found"}
    client, _ = create_client(stub)

    response = client.post(
        "/api/auth/reset-password",
        json={"email": "missing@example.com", "new_password": "ValidPass123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User not found"
