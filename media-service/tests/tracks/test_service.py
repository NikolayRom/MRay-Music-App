import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from io import BytesIO
from src.tracks.service import (
    check_file_size,
    check_file_format,
    check_content_type_format,
    check_artist_and_album_id_for_track,
    get_metadata_size,
    default_minio_data_upload,
    get_track_image_key_from_metadata,
    get_track_image_key,
    get_track_title,
    get_track_duration,
    get_track_genre,
    get_track_artist_and_album_id,
    track_post_form,
    track_update_form,
    track_patch_form,
    get_track_artist_name,
    get_track_album_name
)
from src.models import Artist, Album
from datetime import timedelta

class TestTracksService:

    @patch("src.tracks.service.settings")
    def test_check_file_size_success(self, mock_settings):
        mock_settings.MINIO_MAX_FILE_SIZE = 100
        mock_file = MagicMock(spec=UploadFile)
        mock_file.size = 50
        mock_file.filename = "test.mp3"
        check_file_size(mock_file)

    @patch("src.tracks.service.settings")
    def test_check_file_size_too_large(self, mock_settings):
        mock_settings.MINIO_MAX_FILE_SIZE = 100
        mock_file = MagicMock(spec=UploadFile)
        mock_file.size = 150
        mock_file.filename = "large.mp3"
        with pytest.raises(HTTPException) as exc:
            check_file_size(mock_file)
        assert exc.value.status_code == 413

    def test_check_file_format_success(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "song.mp3"
        check_file_format(["mp3", "wav"], mock_file)

    def test_check_file_format_fail(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "song.exe"
        with pytest.raises(HTTPException) as exc:
            check_file_format(["mp3", "wav"], mock_file)
        assert exc.value.status_code == 415

    def test_check_content_type_format_success(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "audio/mpeg"
        check_content_type_format(["audio/mpeg"], mock_file)

    def test_get_track_image_key_from_metadata(self):
        assert get_track_image_key_from_metadata("test", "image/jpeg") == "test.jpg"
        assert get_track_image_key_from_metadata("test", "image/png") == "test.png"

    @pytest.mark.asyncio
    @patch("src.tracks.service.check_object_exist")
    async def test_check_ids_valid_artist_only(self, mock_check_exist):
        mock_session = AsyncMock()
        mock_session.get.return_value = MagicMock(spec=Artist)
        await check_artist_and_album_id_for_track(mock_session, artist_id=1)
        mock_session.get.assert_called_once_with(Artist, 1)

    @pytest.mark.asyncio
    async def test_check_ids_album_without_artist_error(self):
        mock_session = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await check_artist_and_album_id_for_track(mock_session, artist_id=None, album_id=1)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    @patch("src.tracks.service.check_object_exist")
    async def test_check_ids_artist_album_mismatch(self, mock_check_exist):
        mock_session = AsyncMock()
        mock_session.get.side_effect = [MagicMock(spec=Artist), MagicMock(spec=Album)]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        with pytest.raises(HTTPException) as exc:
            await check_artist_and_album_id_for_track(mock_session, artist_id=1, album_id=1)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    @patch("src.tracks.service.get_id3_size")
    @patch("src.tracks.service.settings")
    async def test_get_metadata_size_with_id3(self, mock_settings, mock_id3_calc):
        mock_settings.MINIO_MAX_FILE_SIZE = 1000000
        mock_id3_calc.return_value = 500
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"ID3somejunk"
        result = await get_metadata_size(mock_file)
        assert result == 500 + 102400
        mock_file.seek.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_get_metadata_size_no_id3(self):
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"NOTID3"
        result = await get_metadata_size(mock_file)
        assert result == 1024 * 128

    @pytest.mark.asyncio
    @patch("src.tracks.service.s3_storage")
    async def test_default_minio_data_upload_success(self, mock_s3):
        mock_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_client
        mock_s3.bucket_name = "private"
        await default_minio_data_upload("key", b"data", "audio/mpeg", is_public=False)
        mock_client.put_object.assert_called_once()

    

    @pytest.mark.asyncio
    @patch("src.tracks.service.streaming_minio_data_upload")
    @patch("src.tracks.service.get_image_key_from_file")
    @patch("src.tracks.service.check_file_size")
    @patch("src.tracks.service.check_content_type_format")
    async def test_get_track_image_key_from_file(self, mock_fmt, mock_size, mock_get_key, mock_upload):
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "cover.jpg"
        mock_file.content_type = "image/jpeg"
        mock_get_key.return_value = "custom_key.jpg"
        
        result = await get_track_image_key("base_key", BytesIO(), file=mock_file)
        
        assert result == "custom_key.jpg"
        mock_upload.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.tracks.service.default_minio_data_upload")
    @patch("src.tracks.service.ID3")
    async def test_get_track_image_key_from_metadata_success(self, mock_id3_class, mock_upload):
        
        
        mock_tags = MagicMock()
        mock_pic = MagicMock()
        mock_pic.mime = "image/png"
        mock_pic.data = b"fake_png_data"
        mock_tags.getall.return_value = [mock_pic]
        mock_id3_class.return_value = mock_tags

        buffer = BytesIO(b"fake_mp3_data")
        
        result = await get_track_image_key("track_uuid", buffer, file=None)
        
        assert result == "track_uuid.png"
        mock_upload.assert_called_once_with(
            key="track_uuid.png", body=b"fake_png_data", content_type="image/png", is_public=True
        )

    @pytest.mark.asyncio
    @patch("src.tracks.service.ID3")
    async def test_get_track_image_key_no_tags(self, mock_id3_class):
        
        mock_id3_class.side_effect = Exception("No ID3 tags")
        
        result = await get_track_image_key("key", BytesIO(), file=None)
        assert result is None

    

    def test_get_track_title_seeder(self):
        mock_audio = {"TIT2": "Real Title"}
        
        assert get_track_title("uuid_filename", mock_audio, is_seeder=True) == "Real Title"
        
        
        assert get_track_title("uuid_filename", {}, is_seeder=True) == "uuid_filename"

    def test_get_track_title_user(self):
        
        assert get_track_title("uuid_my_song", {}, is_seeder=False) == "my_song"

    def test_get_track_duration(self):
        mock_audio = MagicMock()
        mock_audio.info.length = 185.7
        result = get_track_duration(mock_audio)
        assert result == timedelta(seconds=185)

    def test_get_track_genre_parsing(self):
        mock_audio = {"TCON": "Rock/Metal;Alternative"}
        
        result = get_track_genre(mock_audio, separators=["/", ";"])
        assert result == ["Rock", "Metal", "Alternative"]

    def test_get_track_genre_unknown(self):
        assert get_track_genre({}, []) == ["Unknown"]

    @pytest.mark.asyncio
    @patch("src.tracks.service.get_or_create_album")
    @patch("src.tracks.service.get_or_create_artist")
    async def test_get_track_artist_and_album_id_success(self, mock_get_artist, mock_get_album):
        mock_session = AsyncMock()
        
        
        mock_artist = MagicMock(); mock_artist.id = 10
        mock_album = MagicMock(); mock_album.id = 20
        mock_get_artist.return_value = mock_artist
        mock_get_album.return_value = mock_album

        artist_id, album_id = await get_track_artist_and_album_id(
            mock_session, artist_name="Linkin Park", album_name="Meteora"
        )

        assert artist_id == 10
        assert album_id == 20
        mock_get_artist.assert_called_once()
        mock_get_album.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_track_artist_and_album_id_none(self):
        
        artist_id, album_id = await get_track_artist_and_album_id(AsyncMock(), None, None)
        assert artist_id is None
        assert album_id is None

    
    @patch("src.tracks.service.TrackPatch")
    def test_track_patch_form_parsing(self, mock_schema):
        track_patch_form(title="T", artist_id=None, album_id=None, genre="Rock, Metal")
        
        mock_schema.assert_called_once_with(
            title="T",
            artist_id=None,
            album_id=None,
            genre=["Rock", "Metal"]
        )

    @patch("src.tracks.service.TrackPatch")
    def test_track_patch_form_json_single(self, mock_schema):
        track_patch_form(title=None, artist_id=None, album_id=None, genre='"Jazz"')
        
        mock_schema.assert_called_once_with(
            title=None,
            artist_id=None,
            album_id=None,
            genre=["Jazz"]
        )
   
    @patch("src.tracks.service.settings")
    def test_check_file_size_logic(self, mock_settings):
        mock_settings.MINIO_MAX_FILE_SIZE = 100
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = 'test name'
        
        mock_file.size = 50
        check_file_size(mock_file)
        
        mock_file.size = 150
        with pytest.raises(HTTPException) as exc:
            check_file_size(mock_file)
        assert exc.value.status_code == 413

    def test_check_file_format_logic(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.mp3"
        check_file_format(["mp3"], mock_file)
        
        mock_file.filename = "test.txt"
        with pytest.raises(HTTPException) as exc:
            check_file_format(["mp3"], mock_file)
        assert exc.value.status_code == 415

    def test_check_content_type_format_logic(self):
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "audio/mpeg"
        check_content_type_format(["audio/mpeg"], mock_file)

        mock_file.content_type = "text/plain"
        with pytest.raises(HTTPException) as exc:
            check_content_type_format(["audio/mpeg"], mock_file)
        assert exc.value.status_code == 415

    @pytest.mark.asyncio
    @patch("src.tracks.service.check_object_exist")
    async def test_check_artist_and_album_id_full_success(self, mock_check):
        mock_session = AsyncMock()
        
        mock_session.get.side_effect = [MagicMock(spec=Artist), MagicMock(spec=Album)]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(spec=Album)
        mock_session.execute.return_value = mock_result

        await check_artist_and_album_id_for_track(mock_session, artist_id=1, album_id=1)
        assert mock_session.execute.called

    @pytest.mark.asyncio
    @patch("src.tracks.service.get_id3_size")
    @patch("src.tracks.service.settings")
    async def test_get_metadata_size_clamping(self, mock_settings, mock_id3):
        
        mock_settings.MINIO_MAX_FILE_SIZE = 5000
        mock_id3.return_value = 10000 
        
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.read.return_value = b"ID3"
        
        result = await get_metadata_size(mock_file)
        assert result == 5000 

    @pytest.mark.asyncio
    @patch("src.tracks.service.s3_storage")
    async def test_default_minio_data_upload_fail(self, mock_s3):
        mock_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_client
        mock_client.put_object.side_effect = Exception("S3 error")

        with pytest.raises(HTTPException) as exc:
            await default_minio_data_upload("key", b"data", "type")
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    @patch("src.tracks.service.streaming_minio_data_upload")
    @patch("src.tracks.service.get_image_key_from_file")
    async def test_get_track_image_key_file_upload_fail(self, mock_key, mock_upload):
        mock_upload.side_effect = Exception("Upload error")
        mock_file = MagicMock(spec=UploadFile)
        mock_file.size = 5242880
        mock_file.filename = 'test name'
        mock_file.content_type = "image/jpeg"
        
        with pytest.raises(HTTPException) as exc:
            await get_track_image_key("key", BytesIO(), file=mock_file)
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    @patch("src.tracks.service.ID3")
    async def test_get_track_image_key_metadata_no_pics(self, mock_id3):
        mock_tags = MagicMock()
        mock_tags.getall.return_value = [] 
        mock_id3.return_value = mock_tags
        
        result = await get_track_image_key("key", BytesIO(b"data"), file=None)
        assert result is None

    @pytest.mark.asyncio
    @patch("src.tracks.service.default_minio_data_upload")
    @patch("src.tracks.service.ID3")
    async def test_get_track_image_key_metadata_upload_fail(self, mock_id3, mock_upload):
        mock_tags = MagicMock()
        pic = MagicMock(); pic.mime = "image/jpeg"; pic.data = b"123"
        mock_tags.getall.return_value = [pic]
        mock_id3.return_value = mock_tags
        mock_upload.side_effect = Exception("S3 error")

        with pytest.raises(HTTPException) as exc:
            await get_track_image_key("key", BytesIO(b"data"), file=None)
        assert exc.value.status_code == 500

    def test_mutagen_utils(self):
        mock_audio = MagicMock()
        mock_audio.get.side_effect = lambda k: {"TPE1": "Artist Name", "TALB": "Album Name"}.get(k)
        
        assert get_track_artist_name(mock_audio) == "Artist Name"
        assert get_track_album_name(mock_audio) == "Album Name"

    @pytest.mark.asyncio
    @patch("src.tracks.service.get_or_create_artist")
    async def test_get_track_artist_and_album_id_fail(self, mock_artist):
        mock_artist.side_effect = Exception("DB error")
        with pytest.raises(HTTPException) as exc:
            await get_track_artist_and_album_id(AsyncMock(), "Artist", "Album")
        assert exc.value.status_code == 500

    @patch("src.tracks.service.TrackPost")
    def test_track_post_form(self, mock_schema):
        track_post_form(title=None, artist_id=None, album_id=None, genre=None)
        mock_schema.assert_called_once_with(title=None, artist_id=None, album_id=None, genre=None)

    @patch("src.tracks.service.TrackUpdate")
    def test_track_update_form(self, mock_schema):
        track_update_form(title="T", artist_id=1, album_id=1, genre='["Rock", "Metal"]')
        mock_schema.assert_called_once()

    @patch("src.tracks.service.TrackPatch")
    def test_track_patch_form(self, mock_schema):
        track_patch_form(title=None, artist_id=None, album_id=None, genre=None)
        mock_schema.assert_called_once_with(title=None, artist_id=None, album_id=None, genre=None)

    def test_get_track_duration_logic(self):
        mock_audio = MagicMock()
        mock_audio.info.length = 120.5
        assert get_track_duration(mock_audio) == timedelta(seconds=120)

    def test_get_track_title_logic(self):
        mock_audio = {"TIT2": "Song"}
        assert get_track_title("uuid_file.mp3", mock_audio, is_seeder=False) == "Song"
        
        assert get_track_title("uuid_file.mp3", {}, is_seeder=False) == "file.mp3"