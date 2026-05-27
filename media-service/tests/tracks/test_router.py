import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from src.tracks.router import get_all_tracks, get_track, patch_track, post_track, put_track, delete_track, stream_from_minio
from src.models import Track, Artist, Album
from src.tracks.schemas import TrackPatch, TrackPost, TrackUpdate

@pytest.mark.asyncio
class TestTrackRouter:

    def setup_method(self):
        self.mock_session = AsyncMock()
        self.mock_session.add = MagicMock()
        self.mock_session.commit = AsyncMock()
        self.mock_session.refresh = AsyncMock()
        self.mock_session.get = AsyncMock()
        self.mock_session.execute = AsyncMock()
        self.mock_session.delete = AsyncMock()

    def create_mock_track(self, id: int, title: str, image_key="img.jpg"):
        track = MagicMock(spec=Track)
        track.id = id
        track.title = title
        track.image_key = image_key
        track.s3_key = f"key_{id}.mp3"
        track.genre = ["Rock"]
        track.duration = timedelta(seconds=120)
        track.created_at = datetime.now()
        
        artist = MagicMock(spec=Artist)
        artist.id = 1; artist.name = "A"; artist.image_key = "i.jpg"
        
        album = MagicMock(spec=Album)
        album.id = 1; album.name = "Al"; album.image_key = "al.jpg"
        
        track.artist = artist
        track.album = album
        album.artist = artist
        return track

    def create_valid_track_mock(self):
        
        track = MagicMock(spec=Track)
        track.id = 1
        track.title = "Test"
        track.s3_key = "uuid_file.mp3"
        track.image_key = "uuid_file.jpg"
        track.genre = ["Rock"]
        track.duration = timedelta(seconds=180)
        
        
        track.artist = MagicMock(spec=Artist)
        track.artist.name = "Artist"
        track.album = MagicMock(spec=Album)
        track.album.name = "Album"
        return track

    async def test_get_all_tracks_no_filters(self):
        track1 = self.create_mock_track(1, "Track 1")
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [track1]
        self.mock_session.execute.return_value = mock_result

        
        response = await get_all_tracks(
            request=MagicMock(),
            ids=None,
            search=None,
            genre=None,
            artist_id=None,
            album_id=None,
            limit=10,
            cursor=None,
            session=self.mock_session
        )

        assert len(response.items) == 1
        assert response.items[0].title == "Track 1"

    async def test_get_all_tracks_pagination(self):
        tracks = [self.create_mock_track(i, f"T{i}") for i in range(1, 4)]
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = tracks
        self.mock_session.execute.return_value = mock_result

        response = await get_all_tracks(
            request=MagicMock(),
            ids=None,
            search=None,
            genre=None,
            artist_id=None,
            album_id=None,
            limit=2,
            cursor=1,
            session=self.mock_session
        )

        assert len(response.items) == 2
        assert response.has_more is True
        assert response.next_cursor == 2

    async def test_get_all_tracks_filters_hit(self):
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [self.create_mock_track(1, "Filtered")]
        self.mock_session.execute.return_value = mock_result

        response = await get_all_tracks(
            request=MagicMock(),
            ids=[1],
            search="Filtered",
            genre=["Rock"],
            artist_id=10,
            album_id=20,
            limit=5,
            cursor=None,
            session=self.mock_session
        )
        assert response.items[0].title == "Filtered"

    @patch("src.tracks.router.logger")
    async def test_get_all_tracks_empty_warning(self, mock_logger):
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        self.mock_session.execute.return_value = mock_result

        await get_all_tracks(
            request=MagicMock(),
            ids=None,
            search=None,
            genre=None,
            artist_id=None,
            album_id=None,
            limit=10,
            cursor=None,
            session=self.mock_session
        )
        mock_logger.warning.assert_called_once()

    async def test_get_track_success(self):
        track = self.create_mock_track(7, "Song")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = track
        self.mock_session.execute.return_value = mock_result

        result = await get_track(request=MagicMock(), id=7, session=self.mock_session)
        assert result.id == 7

    @patch("src.tracks.router.MP3")
    @patch("src.tracks.router.get_track_artist_and_album_id")
    @patch("src.tracks.router.get_track_image_key")
    @patch("src.tracks.router.streaming_minio_data_upload")
    @patch("src.tracks.router.get_metadata_size")
    @patch("src.tracks.router.check_artist_and_album_id_for_track")
    @patch("src.tracks.router.check_file_format")
    @patch("src.tracks.router.check_file_size")
    async def test_post_track_success(
        self, mock_size, mock_fmt, mock_ids_check, mock_meta_size,
        mock_upload, mock_get_img_key, mock_get_ids, mock_mp3_class
    ):
        file_track = AsyncMock(spec=UploadFile)
        file_track.filename = "test.mp3"
        file_track.file = MagicMock()
        file_track.read.return_value = b"metadata"
        file_track.seek = AsyncMock()

        mock_meta_size.return_value = 100
        mock_get_img_key.return_value = "img.jpg"
        mock_ids_check.return_value = None
        
        mock_get_ids.return_value = (10, 20) 

        mock_audio = MagicMock()
        mock_audio.info.length = 180
        mock_mp3_class.return_value = mock_audio

        track_data = TrackPost(title="My Song", artist_id=None, album_id=None, genre=["Rock"])

        result = await post_track(
            request=MagicMock(),
            track_data=track_data,
            file_track=file_track,
            file=None, 
            session=self.mock_session,
            user=MagicMock()
        )

        assert result.artist_id == 10
        assert result.album_id == 20
        assert self.mock_session.commit.called

    @patch("src.tracks.router.get_metadata_size")
    async def test_post_track_metadata_error(self, mock_meta_size):
        mock_meta_size.side_effect = Exception("Read Error")
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.size = 5242880
        mock_file.filename = 'test_name.mp3'

        with pytest.raises(HTTPException) as exc:
            await post_track(
                request=MagicMock(),
                track_data=TrackPost(),
                file_track=mock_file,
                session=self.mock_session,
                user=MagicMock()
            )
        assert exc.value.status_code == 500
        assert "Can't read metadata" in exc.value.detail

    @patch("src.tracks.router.check_content_type_format") 
    @patch("src.tracks.router.check_file_size")           
    @patch("src.tracks.router.check_artist_and_album_id_for_track") 
    @patch("src.tracks.router.streaming_minio_data_upload")
    @patch("src.tracks.router.default_minio_data_delete")
    @patch("src.tracks.router.get_image_key_from_file")
    @patch("src.tracks.router.check_object_exist")
    async def test_put_track_success(
        self, mock_exist, mock_get_key, mock_s3_del, 
        mock_s3_up, mock_ids_check, mock_file_size, mock_content_fmt
    ):
        
        track = self.create_valid_track_mock()
        self.mock_session.get.return_value = track
        
        
        mock_ids_check.return_value = AsyncMock() 

        file = MagicMock(spec=UploadFile)
        file.size = 5242880
        file.filename = 'test_name.jpg'
        file.content_type = "image/jpeg"
        
        update_data = TrackUpdate(title="New Title", artist_id=1, album_id=1, genre=["Jazz"])

        
        result = await put_track(
            request=MagicMock(),
            track_id=1,
            track_data=update_data,
            file=file,
            session=self.mock_session,
            user=MagicMock()
        )

        assert track.title == "New Title"
        mock_ids_check.assert_called_once()
        assert mock_s3_up.called
        assert self.mock_session.commit.called

    @patch("src.tracks.router.check_artist_and_album_id_for_track")
    @patch("src.tracks.router.check_object_exist")
    async def test_patch_track_data_only(self, mock_exist, mock_ids_check):
        
        track = self.create_valid_track_mock()
        track.title = "Old"
        self.mock_session.get.return_value = track
        
        patch_data = TrackPatch(title="New", artist_id=None, album_id=None, genre=None)

        result = await patch_track(
            request=MagicMock(),
            track_id=1,
            track_data=patch_data,
            file=None,
            session=self.mock_session,
            user=MagicMock()
        )

        assert track.title == "New"
        assert self.mock_session.commit.called

    @patch("src.tracks.router.check_object_exist")
    async def test_patch_track_invalid_params_error(self, mock_exist):
        
        track = self.create_valid_track_mock()
        self.mock_session.get.return_value = track
        
        patch_data = MagicMock(spec=TrackPatch)
        patch_data.title = None; patch_data.artist_id = None; patch_data.album_id = None
        
        type(patch_data).genre = PropertyMock(side_effect=Exception("Data error"))

        with pytest.raises(HTTPException) as exc:
            await patch_track(
                request=MagicMock(), track_id=1, track_data=patch_data,
                file=None, session=self.mock_session, user=MagicMock()
            )
        assert exc.value.status_code == 400

    @patch("src.tracks.router.default_minio_data_delete")
    @patch("src.tracks.router.check_object_exist")
    async def test_delete_track_full_cleanup(self, mock_exist, mock_s3_del):
        
        track = MagicMock(spec=Track)
        track.id = 1
        track.image_key = "cover.jpg"
        track.s3_key = "audio.mp3"
        self.mock_session.get.return_value = track

        response = await delete_track(
            request=MagicMock(),
            track_id=1,
            session=self.mock_session,
            user=MagicMock()
        )

        assert mock_s3_del.call_count == 2
        self.mock_session.delete.assert_called_once_with(track)
        assert self.mock_session.commit.called
        assert response.status_code == 204

    @patch("src.tracks.router.default_minio_data_delete")
    @patch("src.tracks.router.check_object_exist")
    async def test_delete_track_no_image(self, mock_exist, mock_s3_del):
        
        track = MagicMock(spec=Track)
        track.id = 2
        track.image_key = None
        track.s3_key = "only_audio.mp3"
        self.mock_session.get.return_value = track

        await delete_track(MagicMock(), 2, self.mock_session, MagicMock())

        
        mock_s3_del.assert_called_once_with(key="only_audio.mp3")

    @patch("src.tracks.router.s3_storage")
    @patch("src.tracks.router.check_object_exist")
    async def test_stream_from_minio_200_full_file(self, mock_exist, mock_s3_storage):
        track = MagicMock(spec=Track)
        track.s3_key = "music.mp3"
        self.mock_session.get.return_value = track

        mock_s3_client = AsyncMock()
        mock_s3_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        
        mock_body = MagicMock() 
        
        mock_body.__aiter__.return_value = [b"chunk1", b"chunk2"]
        
        mock_body.close = MagicMock()
        
        mock_s3_client.get_object.return_value = {
            "Body": mock_body,
            "ContentType": "audio/mpeg",
            "ContentLength": 1000
        }

        request = MagicMock()
        request.headers = {}

        response = await stream_from_minio(request, 1, self.mock_session)

        
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        
        assert chunks == [b"chunk1", b"chunk2"]
        
        mock_body.close.assert_called_once()
        
        assert mock_s3_client.__aexit__.called

    @patch("src.tracks.router.s3_storage")
    @patch("src.tracks.router.check_object_exist")
    async def test_stream_from_minio_206_partial(self, mock_exist, mock_s3_storage):
        
        track = MagicMock(spec=Track)
        track.s3_key = "music.mp3"
        self.mock_session.get.return_value = track

        mock_s3_client = AsyncMock()
        mock_s3_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        mock_s3_client.get_object.return_value = {
            "Body": AsyncMock(),
            "ContentType": "audio/mpeg",
            "ContentLength": 500,
            "ContentRange": "bytes 0-499/1000"
        }

        request = MagicMock()
        request.headers = {"range": "bytes=0-499"}

        response = await stream_from_minio(request, 1, self.mock_session)

        assert response.status_code == 206
        assert response.headers["content-range"] == "bytes 0-499/1000"
        
        mock_s3_client.get_object.assert_called_once_with(
            Bucket=mock_s3_storage.bucket_name,
            Key="music.mp3",
            Range="bytes=0-499"
        )

    @patch("src.tracks.router.s3_storage")
    @patch("src.tracks.router.check_object_exist")
    async def test_stream_from_minio_exception(self, mock_exist, mock_s3_storage):
        
        self.mock_session.get.return_value = MagicMock(spec=Track)
        
        mock_s3_client = AsyncMock()
        mock_s3_storage.get_client.return_value.__aenter__.return_value = mock_s3_client
        
        
        mock_s3_client.get_object.side_effect = Exception("Connection lost")

        with pytest.raises(HTTPException) as exc:
            await stream_from_minio(MagicMock(), 1, self.mock_session)
        
        assert exc.value.status_code == 500
        
        assert mock_s3_client.__aexit__.called

    
    async def test_get_all_tracks_complex_filters(self):
        
        track = self.create_mock_track(1, "Title")
        mock_res = MagicMock()
        mock_res.scalars().all.return_value = [track, track] 
        self.mock_session.execute.return_value = mock_res

        response = await get_all_tracks(
            request=MagicMock(),
            ids=[1],
            search="query",
            genre=["Rock"],
            artist_id=1,
            album_id=1,
            limit=1,
            cursor=None,
            session=self.mock_session
        )
        assert response.has_more is True
        assert response.next_cursor == 1

    async def test_get_all_tracks_cursor_logic(self):
        
        mock_res = MagicMock()
        mock_res.scalars().all.return_value = []
        self.mock_session.execute.return_value = mock_res

        await get_all_tracks(
            request=MagicMock(),
            ids=None,
            search=None,
            genre=None,
            limit=10, 
            cursor=10,
            session=self.mock_session
        )
        assert self.mock_session.execute.called

    @patch("src.tracks.router.MP3")
    @patch("src.tracks.router.get_track_artist_and_album_id")
    @patch("src.tracks.router.get_track_image_key")
    @patch("src.tracks.router.streaming_minio_data_upload")
    @patch("src.tracks.router.get_metadata_size")
    @patch("src.tracks.router.check_artist_and_album_id_for_track")
    async def test_post_track_metadata_logic(self, mock_ids_chk, mock_meta, mock_up, mock_img, mock_get_ids, mock_mp3):
        file = AsyncMock(spec=UploadFile)
        file.file = MagicMock()
        file.read.return_value = b"bytes"
        file.size = 1234
        file.filename = 'track.mp3'
        
        mock_meta.return_value = 10
        mock_get_ids.return_value = (1, 1) 
        
        audio_mock = MagicMock()
        audio_mock.info.length = 120
        mock_mp3.return_value = audio_mock
        
        track_data = TrackPost(title=None, artist_id=None, album_id=None, genre=None)

        result = await post_track(
            request=MagicMock(), track_data=track_data, file_track=file,
            file=None, session=self.mock_session, user=MagicMock()
        )
        assert self.mock_session.add.called

    @patch("src.tracks.router.streaming_minio_data_upload")
    async def test_post_track_upload_error(self, mock_up):
        
        mock_up.side_effect = Exception("S3 Fail")
        file = AsyncMock(spec=UploadFile)
        file.content_type = "audio/mpeg"
        file.size = 5242880
        file.filename = 'test_name.mp3'
        
        with pytest.raises(HTTPException) as exc:
            await post_track(MagicMock(), TrackPost(), file, None, self.mock_session, MagicMock())
        assert exc.value.status_code == 500

    @patch("src.tracks.router.MP3")
    @patch("src.tracks.router.get_metadata_size")
    async def test_post_track_parse_metadata_error(self, mock_meta, mock_mp3):
        
        mock_mp3.side_effect = Exception("Corrupted file")
        file = AsyncMock(spec=UploadFile)
        file.content_type = "audio/mpeg"
        file.size = 5242880
        file.filename = 'test_name.mp3'
        
        with pytest.raises(HTTPException) as exc:
            await post_track(MagicMock(), TrackPost(), file, None, self.mock_session, MagicMock())
        assert exc.value.status_code == 500

    @patch("src.tracks.router.check_artist_and_album_id_for_track")
    @patch("src.tracks.router.streaming_minio_data_upload")
    @patch("src.tracks.router.default_minio_data_delete")
    @patch("src.tracks.router.check_object_exist")
    async def test_put_track_invalid_params_catch(self, mock_exist, mock_s3_del, mock_s3_up, mock_ids_check):
        track = self.create_mock_track(1, "Title")
        self.mock_session.get.return_value = track
        
        mock_s3_del.return_value = None
        mock_s3_up.return_value = None
        mock_ids_check.return_value = None 

        type(track).title = PropertyMock(side_effect=Exception("DB Error"))
    
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/jpeg"
        file.size = 100
        file.filename = 'test.jpg'
    
        update_data = TrackUpdate(title="X", artist_id=1, album_id=1, genre=[])

        with pytest.raises(HTTPException) as exc:
            await put_track(
                MagicMock(), 1, update_data, file, self.mock_session, MagicMock()
            )
        assert exc.value.status_code == 400

    async def test_patch_track_with_image_upload_fail(self):
        
        track = self.create_mock_track(1, "Title")
        self.mock_session.get.return_value = track
        
        with patch("src.tracks.router.streaming_minio_data_upload", side_effect=Exception()):
            file = MagicMock(spec=UploadFile)
            file.content_type = "image/jpeg"
            with pytest.raises(HTTPException) as exc:
                await patch_track(MagicMock(), 1, TrackPatch(), file, self.mock_session, MagicMock())
            assert exc.value.status_code == 500


    async def test_delete_track_no_image_branch(self):
        track = self.create_mock_track(1, "Title", image_key=None)
        self.mock_session.get.return_value = track
        
        with patch("src.tracks.router.default_minio_data_delete") as mock_del:
            await delete_track(MagicMock(), 1, self.mock_session, MagicMock())
            
            assert mock_del.call_count == 1

    @patch("src.tracks.router.s3_storage")
    async def test_stream_s3_exception_handling(self, mock_s3):
        
        track = self.create_mock_track(1, "Title")
        self.mock_session.get.return_value = track
        
        mock_client = AsyncMock()
        mock_s3.get_client.return_value.__aenter__.return_value = mock_client
        mock_client.get_object.side_effect = Exception("Network error")

        with pytest.raises(HTTPException) as exc:
            await stream_from_minio(MagicMock(), 1, self.mock_session)
        
        assert exc.value.status_code == 500
        
        assert mock_client.__aexit__.called

    async def test_body_iterator_finally_block(self):
        
        mock_body = MagicMock()
        mock_body.__aiter__.return_value = [b"data"]
        mock_body.close = MagicMock()
        
        mock_client = AsyncMock()