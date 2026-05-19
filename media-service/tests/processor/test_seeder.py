import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch
from src.processor.seeder import seed_music
from src.models import Track

@pytest.mark.asyncio
class TestSeeder:

    def setup_method(self):
        # Мокаем сессию БД
        self.mock_session = AsyncMock()
        self.mock_session.add = MagicMock() # Синхронный по твоему стандарту
        self.mock_session.commit = AsyncMock()
        self.mock_session.execute = AsyncMock()
        
        # Мокаем фабрику сессий
        self.mock_session_maker = MagicMock()
        self.mock_session_maker.return_value.__aenter__.return_value = self.mock_session

    @patch("src.processor.seeder.s3_storage")
    @patch("src.processor.seeder.logger")
    async def test_seed_music_no_tracks(self, mock_logger, mock_s3):
        """Случай: S3 бакет пуст"""
        mock_s3_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.list_objects_v2.return_value = {} # Contents нет

        await seed_music()

        mock_logger.warning.assert_called_with(
            f'SEEDER: No tracks in {mock_s3.bucket_name} from S3 storage are found'
        )

    @patch("src.processor.seeder.MP3")
    @patch("src.processor.seeder.get_track_artist_and_album_id")
    @patch("src.processor.seeder.get_track_image_key")
    @patch("src.processor.seeder.get_track_title")
    @patch("src.processor.seeder.get_track_duration")
    @patch("src.processor.seeder.get_track_genre")
    @patch("src.processor.seeder.async_session_maker")
    @patch("src.processor.seeder.s3_storage")
    async def test_seed_music_success(
        self, mock_s3, mock_session_maker, 
        mock_genre, mock_duration, mock_title, 
        mock_img, mock_ids, mock_mp3
    ):
        """Успешный сид одного трека"""
        # 1. Настройка S3
        mock_s3_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [{'Key': 'track1.mp3'}]
        }
        
        mock_body = AsyncMock()
        mock_body.read.return_value = b"fake_mp3_data"
        mock_s3_client.get_object.return_value = {'Body': mock_body}

        # 2. Настройка БД (через сетап метода)
        mock_session_maker.return_value.__aenter__.return_value = self.mock_session
        # Имитируем, что трека еще нет в базе
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_res

        # 3. Настройка сервисов
        mock_ids.return_value = (1, 1)
        mock_title.return_value = "Seeded Track"
        
        # Запуск
        await seed_music()

        # Проверки
        self.mock_session.add.assert_called_once()
        assert self.mock_session.commit.called
        # Проверяем, что скачивали именно mp3
        mock_s3_client.get_object.assert_called_once_with(
            Bucket=mock_s3.bucket_name,
            Key='track1.mp3',
            Range='bytes=0-26214400'
        )

    @patch("src.processor.seeder.async_session_maker")
    @patch("src.processor.seeder.s3_storage")
    @patch("src.processor.seeder.logger")
    async def test_seed_music_skip_logic(self, mock_logger, mock_s3, mock_session_maker):
        """Проверка пропуска не-mp3 файлов и существующих треков"""
        mock_s3_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'manual.txt'},     # Не mp3
                {'Key': 'exists.mp3'}      # Уже в базе
            ]
        }

        mock_session_maker.return_value.__aenter__.return_value = self.mock_session
        # Для второго файла имитируем, что он найден в базе
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = MagicMock(spec=Track)
        self.mock_session.execute.return_value = mock_res

        await seed_music()

        # Проверяем логи
        log_messages = [call.args[0] for call in mock_logger.warning.call_args_list]
        assert any("skip object" in msg for msg in log_messages)
        assert any("already exist" in msg for msg in log_messages)
        # get_object не должен быть вызван ни разу
        assert not mock_s3_client.get_object.called

    @patch("src.processor.seeder.async_session_maker")
    @patch("src.processor.seeder.s3_storage")
    @patch("src.processor.seeder.logger")
    async def test_seed_music_error_handling(self, mock_logger, mock_s3, mock_session_maker):
        """Проверка, что ошибка в одном файле не прерывает весь цикл"""
        mock_s3_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [{'Key': 'error.mp3'}, {'Key': 'valid.mp3'}]
        }

        mock_session_maker.return_value.__aenter__.return_value = self.mock_session
        
        # Имитируем ошибку на первом файле (например, при проверке в БД)
        self.mock_session.execute.side_effect = [
            Exception("DB Error"), 
            MagicMock() # Для второго файла всё ок
        ]

        await seed_music()

        # Проверяем, что была ошибка в логе
        assert mock_logger.error.called
        # Проверяем, что сессия всё равно закоммитилась (для валидных файлов)
        assert self.mock_session.commit.called