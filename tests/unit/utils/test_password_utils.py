import pytest
import hmac

from app.utils.password import hash_password, verify_password

@pytest.mark.unit
def test_hash_password_return_different_password_from_plain_password() -> None:
    pwd = 'TestPassword123'
    hashed_pwd = hash_password(pwd)

    assert hashed_pwd != pwd
    assert isinstance(hashed_pwd, str)

@pytest.mark.unit
def test_verify_password_returns_true_for_correct_password() -> None:
    pwd = 'TestPassword123'
    hashed_pwd = hash_password(pwd)

    assert verify_password(pwd, hashed_pwd)

@pytest.mark.unit
def test_verify_password_returns_false_for_incorrect_password() -> None:
    hashed_pwd = hash_password('TestPassword123')

    assert not verify_password('TestIncorrectPassword', hashed_pwd)

@pytest.mark.unit
def test_hash_password_generates_different_hash_for_one_password() -> None:
    pwd = 'TestPassword123'
    hashed_pwd1 = hash_password(pwd)
    hashed_pwd2 = hash_password(pwd)

    assert not hmac.compare_digest(hashed_pwd1, hashed_pwd2)
    assert verify_password(pwd, hashed_pwd1)
    assert verify_password(pwd, hashed_pwd2)
