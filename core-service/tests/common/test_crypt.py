import pytest
from unittest.mock import patch
from src.common.crypt_context import CryptContext 

@pytest.fixture
def pwd_context():
    return CryptContext()

def test_hash_password_success(pwd_context):
    password = "my_secret_password"
    hashed = pwd_context.hash(password)
    
    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

def test_verify_password_success(pwd_context):
    password = "secure_password123"
    hashed = pwd_context.hash(password)
    
    assert pwd_context.verify(password, hashed) is True

def test_verify_password_failure(pwd_context):
    password = "correct_password"
    wrong_password = "wrong_password"
    hashed = pwd_context.hash(password)
    
    assert pwd_context.verify(wrong_password, hashed) is False

def test_long_password_handling(pwd_context):
    long_password = "a" * 100
    hashed = pwd_context.hash(long_password)
    
    assert hashed is not None
    assert pwd_context.verify(long_password, hashed) is True
    
    modified_long_password = "a" * 72 + "b" + "a" * 27
    assert pwd_context.verify(modified_long_password, hashed) is False

@patch("src.common.logger.logger.critical")
def test_hash_exception_handling(mock_logger, pwd_context):
    result = pwd_context.hash(None) 
    
    assert result is None
    assert mock_logger.called

@patch("src.common.logger.logger.critical")
def test_verify_exception_handling(mock_logger, pwd_context):
    result = pwd_context.verify("password", "not_a_bcrypt_hash")
    
    assert result is None
    assert mock_logger.called

@pytest.mark.parametrize("password", [
    "",
    " ",
    "12345",
    "special_!@#$%^&*()",
    "кириллица_тест"
])
def test_various_password_types(pwd_context, password):
    hashed = pwd_context.hash(password)
    assert pwd_context.verify(password, hashed) is True