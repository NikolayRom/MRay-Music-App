import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from src.albums.router import get_all_albums, get_album, post_album, put_album, patch_album, delete_album
from src.models import Album, Artist, Track
from src.albums.schemas import AlbumPost, AlbumPatch, AlbumUpdate
from datetime import datetime, timedelta

@pytest.mark.asyncio
class TestAlbumRouter:

    def setup_method(self):
        self.mock_session = AsyncMock()
        
        self.mock_session.add = MagicMock()
        
        self.mock_session.commit = AsyncMock()
        self.mock_session.refresh = AsyncMock()
        self.mock_session.get = AsyncMock()
        self.mock_session.delete = AsyncMock() 

    def create_mock_album(self, id: int, name: str, image_key: str = "album_image.jpg", artist_id: int = 1):
        artist = MagicMock(spec=Artist)
        artist.id = artist_id
        artist.name = "Test Artist"
        artist.image_key = "artist_image.jpg"
        artist.created_at = datetime.now()

        album = MagicMock(spec=Album)
        album.id = id
        album.name = name
        album.image_key = image_key
        album.artist_id = artist_id
        album.artist = artist
        album.created_at = datetime.now()

        track = MagicMock(spec=Track)
        track.id = 100
        track.title = "Test Track"
        track.image_key = "track_image.jpg"
        track.genre = ["Rock"]
        track.duration = timedelta(seconds=200)
        track.created_at = datetime.now()
        
        track.album = album  
        track.artist = artist 

        album.tracks = [track]
        return album

    async def test_get_all_albums_empty(self):
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result
        
        response = await get_all_albums(
            request=MagicMock(),
            limit=10,
            session=mock_session
        )
        
        assert response.items == []
        assert response.has_more is False

    async def test_get_all_albums_with_pagination(self):
        
        
        album1 = self.create_mock_album(1, "Album 1")
        album2 = self.create_mock_album(2, "Album 2")
        album3 = self.create_mock_album(3, "Album 3")
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [album1, album2, album3]
        self.mock_session.execute.return_value = mock_result
        
        response = await get_all_albums(
            request=MagicMock(),
            limit=2,
            session=self.mock_session
        )
        
        assert len(response.items) == 2
        assert response.has_more is True
        assert response.next_cursor == 2
        
        assert response.items[0].artist.name == "Test Artist"
        assert response.items[0].tracks[0].title == "Test Track"

     
    async def test_get_album_success(self):
        album = self.create_mock_album(1, "Single Album")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = album
        self.mock_session.execute.return_value = mock_result
        
        result = await get_album(request=MagicMock(), id=1, session=self.mock_session)
        assert result.name == "Single Album"

    @patch("src.albums.router.check_object_exist")
    async def test_get_album_not_found(self, mock_check):
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        mock_check.side_effect = HTTPException(status_code=404, detail="Not found")
        
        with pytest.raises(HTTPException) as exc:
            await get_album(request=MagicMock(), id=999, session=mock_session)
        assert exc.value.status_code == 404

    @patch("src.albums.router.check_object_exist")
    async def test_post_album_success_no_file(self, mock_check):
        self.mock_session.get.return_value = MagicMock(spec=Artist)
        album_data = AlbumPost(name="New", artist_id=1)
        
        result = await post_album(
            request=MagicMock(),
            album_data=album_data,
            session=self.mock_session,
            user=MagicMock(is_superuser=True)
        )
        assert result.name == "New"
        self.mock_session.add.assert_called_once()

    @patch("src.albums.router.get_file_key")
    @patch("src.albums.router.get_image_key_from_file")
    @patch("src.albums.router.streaming_minio_data_upload")
    @patch("src.albums.router.check_object_exist")
    async def test_post_album_with_file_success(
        self, mock_check, mock_upload, mock_get_img_key, mock_get_file_key
    ):
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.get.return_value = MagicMock(spec=Artist)
        
        mock_get_file_key.return_value = "uuid"
        mock_get_img_key.return_value = "uuid.jpg"
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "test.jpg"
        
        album_data = AlbumPost(name="Album with Image", artist_id=1)
        
        result = await post_album(
            request=MagicMock(),
            album_data=album_data,
            file=mock_file,
            session=mock_session,
            user=MagicMock(is_superuser=True)
        )
        
        assert result.image_key == "uuid.jpg"
        mock_upload.assert_called_once()

    @patch("src.albums.router.streaming_minio_data_upload")
    @patch("src.albums.router.check_object_exist")
    async def test_post_album_upload_error(self, mock_check, mock_upload):
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.get.return_value = MagicMock(spec=Artist)
        mock_upload.side_effect = Exception("Upload failed")
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/png"
        mock_file.filename = 'test name'
        album_data = AlbumPost(name="Fail", artist_id=1)

        with pytest.raises(HTTPException) as exc:
            await post_album(
                request=MagicMock(),
                album_data=album_data,
                file=mock_file,
                session=mock_session,
                user=MagicMock()
            )
        
        assert exc.value.status_code == 500

    
    @patch("src.albums.router.streaming_minio_data_upload")
    @patch("src.albums.router.default_minio_data_delete")
    @patch("src.albums.router.get_image_key_from_file")
    @patch("src.albums.router.get_file_key")
    @patch("src.albums.router.check_object_exist")
    async def test_put_album_success(self, mock_check, mock_file_key, mock_img_key, mock_s3_del, mock_s3_up):
        album = self.create_mock_album(id=1, name="Old", image_key="old.jpg")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = album
        self.mock_session.execute.return_value = mock_result
        self.mock_session.get.return_value = MagicMock(spec=Artist)
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        update_data = AlbumUpdate(name="New", artist_id=2)

        await put_album(
            request=MagicMock(),
            id=1,
            album_data=update_data,
            file=mock_file,
            session=self.mock_session,
            user=MagicMock(is_superuser=True)
        )

        assert album.name == "New"
        assert album.artist_id == 2
        mock_s3_del.assert_called_once_with(key="old.jpg", is_public=True)

        
    
    @patch("src.albums.router.check_object_exist")
    async def test_patch_album_name_only(self, mock_check):
        
        album = self.create_mock_album(id=1, name="Original Name", artist_id=1)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = album
        self.mock_session.execute.return_value = mock_result
    
        
        patch_data = AlbumPatch(name="Patched Name", artist_id=None)
    
        await patch_album(
            request=MagicMock(),
            id=1,
            album_data=patch_data,
            file=None,
            session=self.mock_session,
            user=MagicMock(is_superuser=True)
        )
    
        assert album.name == "Patched Name"
        assert album.artist_id == 1  
        
        self.mock_session.get.assert_not_called()

    @patch("src.albums.router.default_minio_data_delete")
    @patch("src.albums.router.streaming_minio_data_upload")
    @patch("src.albums.router.check_object_exist")
    async def test_patch_album_with_file(self, mock_check, mock_s3_up, mock_s3_del):
        
        album = self.create_mock_album(1, "Name", image_key="old.png")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = album
        self.mock_session.execute.return_value = mock_result
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = 'test name'
        patch_data = AlbumPatch(name=None, artist_id=None)

        await patch_album(
            request=MagicMock(),
            id=1,
            album_data=patch_data,
            file=mock_file,
            session=self.mock_session,
            user=MagicMock()
        )

        mock_s3_del.assert_called_with(key="old.png", is_public=True)
        assert mock_s3_up.called

    
    @patch("src.albums.router.default_minio_data_delete")
    @patch("src.albums.router.check_object_exist")
    async def test_delete_album_success(self, mock_check, mock_s3_del):
        album = self.create_mock_album(id=1, name="To Delete", image_key="album.jpg")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = album
        self.mock_session.execute.return_value = mock_result

        response = await delete_album(
            request=MagicMock(),
            id=1,
            session=self.mock_session,
            user=MagicMock(is_superuser=True)
        )

        
        assert mock_s3_del.call_count == 3
        
        
        self.mock_session.delete.assert_called_once_with(album)
        assert response.status_code == 204


    @patch("src.albums.router.default_minio_data_delete")
    @patch("src.albums.router.check_object_exist")
    async def test_delete_album_s3_error(self, mock_check, mock_s3_del):
        
        album = self.create_mock_album(1, "Fail Delete")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = album
        self.mock_session.execute.return_value = mock_result
        
        mock_s3_del.side_effect = Exception("S3 Error")

        with pytest.raises(HTTPException) as exc:
            await delete_album(request=MagicMock(), id=1, session=self.mock_session, user=MagicMock())
        
        assert exc.value.status_code == 500
        assert "Can't delete cover" in exc.value.detail