import pytest
from fastapi import UploadFile, HTTPException
from src.tracks.service import check_file_format, check_file_size, get_track_genre, get_metadata_size, check_artist_and_album_id_for_track, get_track_title, get_track_duration, get_track_album_name, get_track_artist_name, check_content_type_format, default_minio_data_upload, get_track_image_key, get_track_artist_and_album_id
from unittest.mock import MagicMock, AsyncMock
from src.artists.service import check_unique_artist_name
from io import BytesIO
from mutagen.id3 import APIC

def test_check_file_format_success():
    file = MagicMock(spec=UploadFile)
    file.filename = "song.mp3"
    assert check_file_format(["mp3"], file) is None

def test_check_file_format_fail():
    file = MagicMock(spec=UploadFile)
    file.filename = "virus.exe"
    with pytest.raises(HTTPException) as exc:
        check_file_format(["mp3"], file)
    assert exc.value.status_code == 415

def test_check_content_type_format_success():
    file = MagicMock(spec=UploadFile)
    file.content_type = "test/mpeg"
    assert check_content_type_format(["test/mpeg"], file) is None

def test_check_content_type_format_fail():
    file = MagicMock(spec=UploadFile)
    file.content_type = "test_wrong/mpeg"
    with pytest.raises(HTTPException) as exc:
        check_content_type_format(["test/mpeg"], file)
    assert exc.value.status_code == 415

@pytest.mark.asyncio
async def test_check_unique_artist_name_exists(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = MagicMock()
    mock_session.execute.return_value = mock_result
    
    is_unique = await check_unique_artist_name("Nirvana", mock_session)
    assert is_unique is False

@pytest.mark.asyncio
async def test_check_unique_artist_name_exists(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    is_unique = await check_unique_artist_name("Nirvana", mock_session)
    assert is_unique is True

def test_check_file_size_large():
    mock_file = MagicMock()
    mock_file.size = 100 * 1024 * 1024
    with pytest.raises(HTTPException) as exc:
        check_file_size(mock_file)
    assert exc.value.status_code == 413

def test_get_track_genre_parsing():
    mock_audio = MagicMock()
    mock_tcon = MagicMock()
    mock_tcon.__str__.return_value = "Rock, Metal & Grunge"
    mock_audio.get.return_value = mock_tcon
    
    genres = get_track_genre(mock_audio, [",", "&"])
    assert "Rock" in genres
    assert "Metal" in genres
    assert "Grunge" in genres

@pytest.mark.asyncio
async def test_get_metadata_size_id3(mocker):
    mock_file = AsyncMock()
    mock_file.read.return_value = b"ID3\x03\x00\x00\x00\x00\x00\x00"
    
    size = await get_metadata_size(mock_file)
    assert size > 0
    mock_file.seek.assert_called_with(0)

@pytest.mark.asyncio
async def test_check_artist_and_album_id_logic(mock_session):
    with pytest.raises(HTTPException) as exc:
        await check_artist_and_album_id_for_track(mock_session, artist_id=None, album_id=1)
    assert exc.value.status_code == 400

    mock_session.get = AsyncMock(side_effect=[MagicMock(), MagicMock()]) 
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None 
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await check_artist_and_album_id_for_track(mock_session, artist_id=1, album_id=1)
    assert exc.value.status_code == 404

def test_metadata_extraction_helpers():    
    mock_audio = MagicMock()
    mock_audio.info.length = 180.5
    mock_audio.get.return_value = ["Real Title"]

    assert get_track_title("uuid_filename", mock_audio) == "['Real Title']"
    
    duration = get_track_duration(mock_audio)
    assert duration.total_seconds() == 180

def test_get_track_artist_name():
    mock_audio = MagicMock()
    mock_tpe1 = MagicMock()
    mock_tpe1.__str__.return_value = "Test Artist"
    mock_audio.get.return_value = mock_tpe1

    assert get_track_artist_name(mock_audio) == mock_tpe1

def test_get_track_album_name():
    mock_audio = MagicMock()
    mock_talb = MagicMock()
    mock_talb.__str__.return_value = "Test Album"
    mock_audio.get.return_value = mock_talb

    assert get_track_album_name(mock_audio) == mock_talb

@pytest.mark.asyncio
async def test_get_track_image_key_from_file(mocker):    
    mocker.patch("src.tracks.service.streaming_minio_data_upload", new_callable=AsyncMock)
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = 'test_file'
    mock_file.content_type = "image/jpeg"
    mock_file.size = 100
    
    key = await get_track_image_key("test_key", BytesIO(b""), file=mock_file)
    assert "test_key.jpg" in key

@pytest.mark.asyncio
async def test_default_minio_data_upload(mocker):
    mock_s3_client = AsyncMock()
    mock_storage = mocker.patch("src.common.s3_utils.s3_storage.get_client")
    mock_storage.return_value.__aenter__.return_value = mock_s3_client
    
    mock_body = b'fake_data'
    
    await default_minio_data_upload(key="test_key", content_type="audio/mpeg", body=mock_body)
    
    mock_s3_client.put_object.assert_called_once_with(
        Bucket=mocker.ANY,
        Key="test_key",
        Body=b"fake_data",
        ContentType="audio/mpeg"
    )

@pytest.mark.asyncio
async def test_get_track_image_key_from_metadata(mocker):    
    mock_id3 = MagicMock()
    mock_pic = MagicMock(spec=APIC)
    mock_pic.mime = "image/jpeg"
    mock_pic.data = b"fake_image_data"
    mock_id3.getall.return_value = [mock_pic]
    mocker.patch("src.tracks.service.ID3", return_value=mock_id3)
    
    mock_upload = mocker.patch("src.tracks.service.default_minio_data_upload", new_callable=AsyncMock)
    
    buffer = BytesIO(b"fake_mp3_data")
    key = await get_track_image_key("test_key", buffer, file=None)
    
    assert "test_key.jpg" in key
    mock_upload.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_track_artist_and_album_id_full(mock_session, mocker):    
    mock_artist = MagicMock(id=10)
    mock_album = MagicMock(id=20)
    
    mocker.patch("src.tracks.service.get_or_create_artist", return_value=mock_artist)
    mocker.patch("src.tracks.service.get_or_create_album", return_value=mock_album)
    
    art_id, alb_id = await get_track_artist_and_album_id(
        mock_session, artist_name="Nirvana", album_name="Nevermind"
    )
    
    assert art_id == 10
    assert alb_id == 20