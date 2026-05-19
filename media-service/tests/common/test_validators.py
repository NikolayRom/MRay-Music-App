# tests/common/test_validators.py
import pytest
from fastapi import HTTPException
from unittest.mock import patch
from src.common.validators import check_object_exist

def test_check_object_exist_success():
    """Проверка случая, когда объект существует (не должен вызывать исключений)"""
    # Проверяем на разных типах данных, которые считаются "истинными"
    try:
        check_object_exist({"id": 1})
        check_object_exist([1, 2, 3])
        check_object_exist("some string")
    except HTTPException:
        pytest.fail("check_object_exist raised HTTPException unexpectedly!")

@patch("src.common.validators.logger")
def test_check_object_exist_not_found(mock_logger):
    """Проверка случая, когда объект None или пуст"""
    # Проверяем, что выбрасывается HTTPException с кодом 404
    with pytest.raises(HTTPException) as exc_info:
        check_object_exist(None)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Object not found"
    
    # Проверяем, что логгер зафиксировал ошибку
    mock_logger.error.assert_called_once_with("Error: object doesn't exist")

@patch("src.common.validators.logger")
def test_check_object_exist_empty_list(mock_logger):
    """Проверка случая с пустым списком (тоже должен бросать 404)"""
    with pytest.raises(HTTPException):
        check_object_exist([])
    
    assert mock_logger.error.called