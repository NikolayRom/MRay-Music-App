import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile, status
from datetime import datetime
from src.artists.router import get_all_artists, get_artist, post_artist, patch_artist, put_artist, delete_artist
from src.models import Artist, Album, Track
from src.artists.schemas import ArtistPost, ArtistPatch, ArtistUpdate

@pytest.mark.asyncio
class TestArtistRouter:

    def setup_method(self):
        self.mock_session = AsyncMock()
        self.mock_session.add = MagicMock()
        self.mock_session.commit = AsyncMock()
        self.mock_session.refresh = AsyncMock()
        self.mock_session.delete = AsyncMock()

    def create_mock_artist_full(self, id: int, name: str, image_key="art.jpg", album_count=1, track_count=1):
        """Создает мока артиста с заданным количеством связанных объектов"""
        artist = MagicMock(spec=Artist)
        artist.id = id
        artist.name = name
        artist.image_key = image_key
        artist.created_at = datetime.now()

        # Создаем альбомы
        albums = []
        for i in range(album_count):
            alb = MagicMock(spec=Album)
            alb.id = i
            alb.name = f"Album {i}"
            alb.image_key = f"alb_img_{i}.jpg"
            albums.append(alb)
        
        # Создаем треки
        tracks = []
        for i in range(track_count):
            tr = MagicMock(spec=Track)
            tr.id = i
            tr.title = f"Track {i}"
            tr.s3_key = f"tr_audio_{i}.mp3" # Приватный
            tr.image_key = f"tr_img_{i}.jpg" # Публичный
            tracks.append(tr)

        artist.albums = albums
        artist.tracks = tracks
        return artist

    # --- GET /artists ---

    async def test_get_all_artists_pagination(self):
        """Проверка пагинации и структуры ответа всех артистов"""
        artist1 = self.create_mock_artist_full(1, "Artist 1")
        artist2 = self.create_mock_artist_full(2, "Artist 2")
        artist3 = self.create_mock_artist_full(3, "Artist 3")

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [artist1, artist2, artist3]
        self.mock_session.execute.return_value = mock_result

        response = await get_all_artists(
            request=MagicMock(),
            limit=2,
            session=self.mock_session
        )

        assert len(response.items) == 2
        assert response.has_more is True
        assert response.next_cursor == 2
        assert response.items[0].name == "Artist 1"
        # Проверка вложенности
        assert response.items[0].albums[0].name == "Album 0"

    async def test_get_all_artists_empty(self):
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        self.mock_session.execute.return_value = mock_result

        response = await get_all_artists(
            request=MagicMock(),
            limit=10,
            session=self.mock_session
        )
        assert response.items == []
        assert response.has_more is False

    # --- GET /artist/{id} ---

    async def test_get_artist_success(self):
        artist = self.create_mock_artist_full(1, "The Star")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artist
        self.mock_session.execute.return_value = mock_result

        result = await get_artist(request=MagicMock(), id=1, session=self.mock_session)
        assert result.id == 1
        assert result.name == "The Star"

    @patch("src.artists.router.check_object_exist")
    async def test_get_artist_not_found(self, mock_check):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result
        
        # Имитируем поведение валидатора
        mock_check.side_effect = HTTPException(status_code=404, detail="Not found")

        with pytest.raises(HTTPException) as exc:
            await get_artist(request=MagicMock(), id=99, session=self.mock_session)
        assert exc.value.status_code == 404

    # --- POST /artist ---

    @patch("src.artists.router.check_unique_artist_name")
    async def test_post_artist_success_no_file(self, mock_check_unique):
        # Имя свободно
        mock_check_unique.return_value = True
        
        artist_data = ArtistPost(name="New Legend")
        
        result = await post_artist(
            request=MagicMock(),
            artist_obj=artist_data,
            file=None,
            session=self.mock_session,
            user=MagicMock()
        )

        assert result.name == "New Legend"
        self.mock_session.add.assert_called_once()
        assert self.mock_session.commit.call_count == 1

    @patch("src.artists.router.check_unique_artist_name")
    async def test_post_artist_duplicate_name(self, mock_check_unique):
        # Имя уже занято
        mock_check_unique.return_value = False
        
        artist_data = ArtistPost(name="Existing Artist")

        with pytest.raises(HTTPException) as exc:
            await post_artist(
                request=MagicMock(),
                artist_obj=artist_data,
                session=self.mock_session,
                user=MagicMock()
            )
        
        assert exc.value.status_code == 400
        assert "already exist" in exc.value.detail

    @patch("src.artists.router.get_file_key")
    @patch("src.artists.router.get_image_key_from_file")
    @patch("src.artists.router.streaming_minio_data_upload")
    @patch("src.artists.router.check_unique_artist_name")
    async def test_post_artist_with_file_success(
        self, mock_check_unique, mock_s3_up, mock_img_key, mock_file_key
    ):
        mock_check_unique.return_value = True
        mock_file_key.return_value = "artist_uuid"
        mock_img_key.return_value = "artist_uuid.png"
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/png"
        artist_data = ArtistPost(name="Artist with Bio")

        result = await post_artist(
            request=MagicMock(),
            artist_obj=artist_data,
            file=mock_file,
            session=self.mock_session,
            user=MagicMock()
        )

        assert result.image_key == "artist_uuid.png"
        assert mock_s3_up.called
        # Один коммит после создания, второй после обновления image_key
        assert self.mock_session.commit.call_count == 2

    @patch("src.artists.router.streaming_minio_data_upload")
    @patch("src.artists.router.check_unique_artist_name")
    async def test_post_artist_upload_error(self, mock_check_unique, mock_s3_up):
        mock_check_unique.return_value = True
        mock_s3_up.side_effect = Exception("S3 error")
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = 'test name'
        artist_data = ArtistPost(name="Broken Upload")

        with pytest.raises(HTTPException) as exc:
            await post_artist(
                request=MagicMock(),
                artist_obj=artist_data,
                file=mock_file,
                session=self.mock_session,
                user=MagicMock()
            )
        
        assert exc.value.status_code == 500

    # --- Тесты PUT /artist/{id} ---

    @patch("src.artists.router.check_unique_artist_name")
    @patch("src.artists.router.default_minio_data_delete")
    @patch("src.artists.router.streaming_minio_data_upload")
    @patch("src.artists.router.check_object_exist")
    async def test_put_artist_success(self, mock_exist, mock_upload, mock_delete, mock_unique):
        artist = self.create_mock_artist_full(1, "Old Name", image_key="old.jpg")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artist
        self.mock_session.execute.return_value = mock_result
        
        mock_unique.return_value = True # Новое имя уникально
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = 'test name'
        mock_file.content_type = "image/jpeg"
        update_data = ArtistUpdate(name="New Name")

        await put_artist(
            request=MagicMock(),
            id=1,
            artist_obj=update_data,
            file=mock_file,
            session=self.mock_session,
            user=MagicMock()
        )

        assert artist.name == "New Name"
        mock_delete.assert_called_once_with(key="old.jpg", is_public=True)
        assert mock_upload.called
        assert self.mock_session.commit.called

    @patch("src.artists.router.check_unique_artist_name")
    @patch("src.artists.router.check_object_exist")
    async def test_put_artist_duplicate_name(self, mock_exist, mock_unique):
        artist = self.create_mock_artist_full(1, "Name")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artist
        self.mock_session.execute.return_value = mock_result
        
        mock_unique.return_value = False # Имя занято

        with pytest.raises(HTTPException) as exc:
            await put_artist(
                request=MagicMock(), id=1, 
                artist_obj=ArtistUpdate(name="Taken"), 
                file=MagicMock(), session=self.mock_session, user=MagicMock()
            )
        assert exc.value.status_code == 400

    # --- Тесты PATCH /artist/{id} ---

    @patch("src.artists.router.check_unique_artist_name")
    @patch("src.artists.router.check_object_exist")
    async def test_patch_artist_name_only(self, mock_exist, mock_unique):
        artist = self.create_mock_artist_full(1, "Original")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artist
        self.mock_session.execute.return_value = mock_result
        mock_unique.return_value = True

        patch_data = ArtistPatch(name="Updated")
        await patch_artist(
            request=MagicMock(), id=1, artist_obj=patch_data, 
            file=None, session=self.mock_session, user=MagicMock()
        )

        assert artist.name == "Updated"
        assert self.mock_session.commit.called

    # --- Тесты DELETE /artist/{id} ---

    @patch("src.artists.router.default_minio_data_delete")
    @patch("src.artists.router.check_object_exist")
    async def test_delete_artist_full_cleanup(self, mock_exist, mock_delete):
        # Создаем артиста с 2 альбомами и 2 треками
        # Итого ключей: 1 (арт) + 2 (альбомы) + 2*2 (треки: аудио + фото) = 7
        artist = self.create_mock_artist_full(1, "Dead Artist", album_count=2, track_count=2)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artist
        self.mock_session.execute.return_value = mock_result

        response = await delete_artist(
            request=MagicMock(),
            id=1,
            session=self.mock_session,
            user=MagicMock()
        )

        # Проверяем количество вызовов удаления из S3
        # 2 приватных (аудио треков) + 5 публичных (арт + 2 альбома + 2 фото треков)
        assert mock_delete.call_count == 7
        
        # Проверяем вызовы с разными параметрами is_public
        # 2 раза для приватных ключей (is_public по дефолту False)
        # 5 раз для публичных (is_public=True)
        
        # Проверка удаления из БД
        self.mock_session.delete.assert_called_once_with(artist)
        assert response.status_code == 204

    @patch("src.artists.router.default_minio_data_delete")
    @patch("src.artists.router.check_object_exist")
    async def test_delete_artist_s3_fail(self, mock_exist, mock_delete):
        artist = self.create_mock_artist_full(1, "Artist")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artist
        self.mock_session.execute.return_value = mock_result
        
        # Имитируем ошибку S3
        mock_delete.side_effect = Exception("Delete failed")

        with pytest.raises(HTTPException) as exc:
            await delete_artist(request=MagicMock(), id=1, session=self.mock_session, user=MagicMock())
        
        assert exc.value.status_code == 500
        assert "Error while trying to delete" in exc.value.detail