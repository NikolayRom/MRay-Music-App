from datetime import timedelta, datetime
from src.tracks.schemas import TrackRead
from src.artists.schemas import ArtistRead
from src.albums.schemas import AlbumRead
from src.models import Track, Album, Artist
from unittest.mock import MagicMock

def test_track_read_computed_duration():
    fake_track = MagicMock(spec=Track)
    fake_track.id = 1
    fake_track.title = "Song"
    fake_track.duration = timedelta(minutes=3, seconds=30)
    fake_track.genre = ["Rock"]
    fake_track.created_at = datetime.now()

    fake_track.image_key = None
    fake_track.artist = None
    fake_track.album = None

    schema = TrackRead.model_validate(fake_track)
    
    assert schema.duration_seconds == 210

def test_artist_read():
    fake_artist = MagicMock(spec=Artist)
    fake_artist.id = 1
    fake_artist.name = "Fake Artist"
    fake_artist.created_at = datetime.now()

    fake_artist.image_key = None
    fake_artist.tracks = None
    fake_artist.albums = None

    schema = ArtistRead.model_validate(fake_artist)
    
def test_album_read():
    fake_album = MagicMock(spec=Album)
    fake_album.id = 1
    fake_album.name = "Fake Album"
    fake_album.created_at = datetime.now()

    fake_album.image_key = None
    fake_album.tracks = None
    fake_album.artist = None

    schema = AlbumRead.model_validate(fake_album)