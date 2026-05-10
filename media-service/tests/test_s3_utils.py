import pytest
from unittest.mock import AsyncMock, MagicMock
from src.common.s3_utils import get_image_key_from_file, streaming_minio_data_upload, default_minio_data_delete
from fastapi import UploadFile

def test_get_image_key_from_file():
    mock_file = MagicMock(spec=UploadFile)
    mock_file.content_type = "image/jpeg"
    key = get_image_key_from_file("test_id", mock_file)
    assert "test_id.jpg" in key
    assert "covers" in key

@pytest.mark.asyncio
async def test_streaming_minio_data_upload_and_default_minio_data_delete(mocker):
    mock_s3_client = AsyncMock()
    mock_storage = mocker.patch("src.common.s3_utils.s3_storage.get_client")
    mock_storage.return_value.__aenter__.return_value = mock_s3_client
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = b"fake_data"
    mock_file.filename = 'test_song.mp3'
    
    await streaming_minio_data_upload("test_key", "audio/mpeg", mock_file)
    
    mock_s3_client.put_object.assert_called_once_with(
        Bucket=mocker.ANY,
        Key="test_key",
        Body=b"fake_data",
        ContentType="audio/mpeg"
    )

    await default_minio_data_delete(key='test_key')