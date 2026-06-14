import pytest

from taskflow.api.deps import build_services
from taskflow.utils.validation import ValidationError


def test_register_and_authenticate():
    auth = build_services().auth
    user = auth.register("user@example.com", "User", "secret123")
    assert user.id is not None
    assert auth.authenticate("user@example.com", "secret123") is not None
    assert auth.authenticate("user@example.com", "wrong") is None


def test_register_rejects_bad_email():
    auth = build_services().auth
    with pytest.raises(ValidationError):
        auth.register("not-an-email", "User", "secret123")


def test_old_token_hash_is_stable():
    auth = build_services().auth
    assert auth.old_token_hash("x") == auth.old_token_hash("x")
    assert auth.old_token_hash("x") != auth.hash_password("x")
