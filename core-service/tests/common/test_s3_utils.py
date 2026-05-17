import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.common.s3_utils import default_minio_data_delete, set_public_bucket_policy

@pytest.mark.asyncio
async def test_default_minio_data_delete_success():
    """Проверка успешного удаления объекта из S3."""
    # Создаем мок для клиента, который возвращается из контекстного менеджера
    mock_s3_client = AsyncMock()
    
    # Мокаем s3_storage.get_client() так, чтобы он работал в async with
    # Нам нужно пробросить мок через __aenter__
    with patch("src.common.s3_utils.s3_storage") as mock_storage:
        mock_storage.bucket_name = "test-bucket"
        mock_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        with patch("src.common.s3_utils.logger") as mock_logger:
            test_key = "avatars/user_1.png"
            await default_minio_data_delete(test_key)
            
            # Проверяем, что был вызван delete_object с правильными параметрами
            mock_s3_client.delete_object.assert_called_once_with(
                Bucket="test-bucket",
                Key=test_key
            )
            # Проверяем, что логи зафиксировали успех
            assert mock_logger.success.called

@pytest.mark.asyncio
async def test_set_public_bucket_policy_existing_bucket():
    """Проверка установки политики, если бакет уже существует (head_bucket ок)."""
    mock_s3_client = AsyncMock()
    # head_bucket ничего не возвращает, если бакет есть
    mock_s3_client.head_bucket.return_value = {} 
    
    with patch("src.common.s3_utils.s3_policy") as mock_policy:
        mock_policy.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        bucket_name = "public-assets"
        await set_public_bucket_policy(bucket_name)
        
        # Проверяем, что head_bucket вызывался
        mock_s3_client.head_bucket.assert_called_once_with(Bucket=bucket_name)
        # create_bucket НЕ должен быть вызван
        mock_s3_client.create_bucket.assert_not_called()
        
        # Проверяем, что политика была установлена
        assert mock_s3_client.put_bucket_policy.called
        call_args = mock_s3_client.put_bucket_policy.call_args
        assert call_args.kwargs['Bucket'] == bucket_name
        
        # Проверяем структуру JSON политики
        policy_dict = json.loads(call_args.kwargs['Policy'])
        assert policy_dict["Statement"][0]["Action"] == ["s3:GetObject"]
        assert policy_dict["Statement"][0]["Principal"] == {"AWS": ["*"]}

@pytest.mark.asyncio
async def test_set_public_bucket_policy_create_new_bucket():
    """Проверка создания бакета, если его нет (head_bucket выкидывает ошибку)."""
    mock_s3_client = AsyncMock()
    # Имитируем ошибку (бакет не найден)
    mock_s3_client.head_bucket.side_effect = Exception("Not Found")
    
    with patch("src.common.s3_utils.s3_policy") as mock_policy:
        mock_policy.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        bucket_name = "new-bucket"
        await set_public_bucket_policy(bucket_name)
        
        # Проверяем, что при ошибке head_bucket был вызван create_bucket
        mock_s3_client.create_bucket.assert_called_once_with(Bucket=bucket_name)
        # И политика всё равно была установлена
        assert mock_s3_client.put_bucket_policy.called

@pytest.mark.asyncio
async def test_default_minio_data_delete_exception():
    """Проверка поведения при ошибке S3 (необязательно, но полезно)."""
    mock_s3_client = AsyncMock()
    mock_s3_client.delete_object.side_effect = Exception("S3 Connection Error")
    
    with patch("src.common.s3_utils.s3_storage") as mock_storage:
        mock_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        # В вашем коде нет try/except вокруг delete_object, 
        # поэтому мы ожидаем, что ошибка пробросится выше
        with pytest.raises(Exception) as exc:
            await default_minio_data_delete("any-key")
        
        assert str(exc.value) == "S3 Connection Error"