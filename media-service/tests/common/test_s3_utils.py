import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from src.common.s3_utils import (
    get_image_key_from_file,
    streaming_minio_data_upload,
    default_minio_data_delete,
    set_public_bucket_policy
)

class TestS3Utils:

    # --- Синхронные тесты (без маркера asyncio) ---

    def test_get_image_key_from_file_jpg(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = 'image/jpeg'
        
        result = get_image_key_from_file("test_key", mock_file)
        assert result == "test_key.jpg"

    def test_get_image_key_from_file_png(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = 'image/png'
        
        result = get_image_key_from_file("test_key", mock_file)
        assert result == "test_key.png"

    def test_get_image_key_from_file_default(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = 'text/plain'
        
        result = get_image_key_from_file("test_key", mock_file)
        assert result == "test_key.png"

    # --- Асинхронные тесты (с маркером asyncio) ---

    @pytest.mark.asyncio
    @patch("src.common.s3_utils.s3_storage")
    @patch("src.common.s3_utils.s3_assets_storage")
    async def test_streaming_minio_data_upload(self, mock_assets_storage, mock_storage):
        mock_storage.bucket_name = "private-bucket"
        mock_assets_storage.bucket_name = "public-bucket"
        
        mock_s3_client = AsyncMock()
        mock_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.put_object.return_value = {"ETag": "12345"}

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = MagicMock()

        result = await streaming_minio_data_upload("key1", "image/jpeg", mock_file, is_public=False)

        assert result == {"ETag": "12345"}
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.common.s3_utils.s3_storage")
    @patch("src.common.s3_utils.s3_assets_storage")
    async def test_default_minio_data_delete_public(self, mock_assets_storage, mock_storage):
        mock_assets_storage.bucket_name = "public-bucket"
        
        mock_s3_client = AsyncMock()
        mock_storage.get_client.return_value.__aenter__.return_value = mock_s3_client

        await default_minio_data_delete("key_to_delete", is_public=True)

        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="public-bucket",
            Key="key_to_delete"
        )

    @pytest.mark.asyncio
    @patch("src.common.s3_utils.s3_assets_policy")
    async def test_set_public_bucket_policy_bucket_exists(self, mock_policy_storage):
        mock_s3_client = AsyncMock()
        mock_policy_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.head_bucket.return_value = {}

        await set_public_bucket_policy("my-bucket")

        mock_s3_client.head_bucket.assert_called_once()
        mock_s3_client.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.common.s3_utils.s3_assets_policy")
    async def test_set_public_bucket_policy_bucket_not_exists(self, mock_policy_storage):
        mock_s3_client = AsyncMock()
        mock_policy_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.head_bucket.side_effect = Exception("Not Found")

        await set_public_bucket_policy("new-bucket")

        mock_s3_client.create_bucket.assert_called_once_with(Bucket="new-bucket")
        mock_s3_client.put_bucket_policy.assert_called_once()