import pytest
from fastapi import HTTPException, status, UploadFile
from unittest.mock import AsyncMock, patch, MagicMock
from src.common.image_utils import gen_uuid, get_image_key, get_image_key_from_file, check_content_type_format, streaming_minio_data_upload, check_file_size
import uuid

# 1. Тест генерации UUID
def test_gen_uuid():
    res = gen_uuid()
    assert isinstance(res, str)
    assert len(res) == 32  # hex-представление uuid4 имеет длину 32 символа
    # Проверяем, что это валидный hex
    int(res, 16) 

# 2. Тест определения расширения
@pytest.mark.parametrize("content_type, expected_ext", [
    ("image/jpeg", "jpg"),
    ("image/png", "png"),
    ("image/jpg", "png"), # В вашей логике: если не jpeg, то png
])
def test_get_image_key_from_file(content_type, expected_ext):
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = content_type
    
    res = get_image_key_from_file("test-uuid", mock_file)
    assert res == f"test-uuid.{expected_ext}"

# 3. Тесты валидации формата
def test_check_content_type_format_success():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/png"
    # Не должно вызывать исключений
    check_content_type_format(["image/png", "image/jpeg"], mock_file)

def test_check_content_type_format_error():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "application/pdf"
    
    with pytest.raises(HTTPException) as exc:
        check_content_type_format(["image/png"], mock_file)
    assert exc.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

# 4. Тесты валидации размера
@patch("src.common.image_utils.settings")
def test_check_file_size_success(mock_settings):
    mock_settings.MINIO_MAX_FILE_SIZE = 100
    mock_file = MagicMock(spec=UploadFile)
    mock_file.size = 50
    # Ок
    check_file_size(mock_file)

@patch("src.common.image_utils.settings")
def test_check_file_size_error(mock_settings):
    mock_settings.MINIO_MAX_FILE_SIZE = 100
    mock_file = MagicMock(spec=UploadFile)
    mock_file.size = 150
    mock_file.filename = "large.png"
    
    with pytest.raises(HTTPException) as exc:
        check_file_size(mock_file)
    assert exc.value.status_code == status.HTTP_413_CONTENT_TOO_LARGE

# 5. Тест загрузки (streaming_minio_data_upload)
@pytest.mark.asyncio
async def test_streaming_minio_data_upload():
    mock_s3_client = AsyncMock()
    mock_s3_client.put_object.return_value = {"ETag": "some-etag"}
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = MagicMock() # имитация файлового объекта
    mock_file.filename = "test.png"

    with patch("src.common.image_utils.s3_storage") as mock_storage:
        mock_storage.bucket_name = "test-bucket"
        mock_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        res = await streaming_minio_data_upload("key.png", "image/png", mock_file)
        
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="key.png",
            Body=mock_file.file,
            ContentType="image/png"
        )
        assert res == {"ETag": "some-etag"}

# 6. Интеграционный тест главной функции get_image_key
@pytest.mark.asyncio
async def test_get_image_key_main_flow_success():
    # Нам нужно замокать все внутренние вызовы, чтобы проверить флоу
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "avatar.jpg"
    mock_file.size = 1000

    with patch("src.common.image_utils.check_content_type_format") as mock_check_fmt, \
         patch("src.common.image_utils.check_file_size") as mock_check_size, \
         patch("src.common.image_utils.streaming_minio_data_upload", new_callable=AsyncMock) as mock_upload, \
         patch("src.common.image_utils.settings") as mock_settings:
        
        mock_settings.MINIO_MAX_FILE_SIZE = 5000
        
        key = "unique-uuid"
        result_key = await get_image_key(key, mock_file)
        
        assert result_key == "unique-uuid.jpg"
        mock_check_fmt.assert_called_once()
        mock_check_size.assert_called_once()
        mock_upload.assert_called_once()

@pytest.mark.asyncio
async def test_get_image_key_upload_failure():
    """Тест сценария, когда загрузка в S3 упала."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/png"
    mock_file.filename = 'filename'
    
    with patch("src.common.image_utils.streaming_minio_data_upload", side_effect=Exception("S3 Down")), \
         patch("src.common.image_utils.check_content_type_format"), \
         patch("src.common.image_utils.check_file_size"):
        
        with pytest.raises(HTTPException) as exc:
            await get_image_key("key", mock_file)
        
        assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error, while trying to upload" in exc.value.detail