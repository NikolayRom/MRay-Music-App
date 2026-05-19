# tests/common/test_image_utils.py
import pytest
from unittest.mock import MagicMock, patch
from src.common.image_utils import gen_uuid, get_file_full, get_file_key

def test_gen_uuid_format():
    """Проверка, что генерируется строка нужной длины (uuid4 hex)"""
    result = gen_uuid()
    assert isinstance(result, str)
    assert len(result) == 32  # hex-строка uuid4 имеет длину 32 символа

@patch("src.common.image_utils.gen_uuid")
def test_get_file_full(mock_gen_uuid):
    """Проверка формирования полного имени файла с UUID"""
    # Фиксируем UUID для теста
    mock_gen_uuid.return_value = "testuuid123"
    
    # Имитируем FastAPI UploadFile
    mock_file = MagicMock()
    mock_file.filename = "my_photo.jpg"
    
    result = get_file_full(mock_file)
    
    assert result == "testuuid123_my_photo.jpg"
    mock_gen_uuid.assert_called_once()

@patch("src.common.image_utils.get_file_full")
def test_get_file_key(mock_get_full):
    """Проверка получения ключа (имя без расширения)"""
    # Имитируем результат работы get_file_full
    mock_get_full.return_value = "uuid_name.png"
    
    mock_file = MagicMock()
    result = get_file_key(mock_file)
    
    # Должно отрезать .png
    assert result == "uuid_name"
    mock_get_full.assert_called_once_with(file=mock_file)

@patch("src.common.image_utils.get_file_full")
def test_get_file_key_multiple_dots(mock_get_full):
    """Проверка корректной работы, если в названии файла несколько точек"""
    mock_get_full.return_value = "uuid_my.archive.tar.gz"
    
    mock_file = MagicMock()
    result = get_file_key(mock_file)
    
    # Должно отрезать только последнее расширение
    assert result == "uuid_my.archive.tar"