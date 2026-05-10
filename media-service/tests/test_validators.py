import pytest
from fastapi import HTTPException
from src.common.validators import check_object_exist

def test_check_object_exist_success():
    assert check_object_exist({"id": 1}) is None

def test_check_object_exist_raises():
    with pytest.raises(HTTPException) as exc:
        check_object_exist(None)
    assert exc.value.status_code == 404