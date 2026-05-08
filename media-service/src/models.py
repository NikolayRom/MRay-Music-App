from sqlalchemy import ForeignKey, String, ARRAY, func, Index
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from typing import Optional, List
from datetime import timedelta, datetime

class Base(DeclarativeBase):
    pass

class Track(Base):
    __tablename__ = 'tracks'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    artist_id: Mapped[Optional[int]] = mapped_column(ForeignKey('artists.id'), index=True)
    album_id: Mapped[Optional[int]] = mapped_column(ForeignKey('albums.id'), index=True)
    s3_key: Mapped[str] = mapped_column(String(500), unique=True)
    image_key: Mapped[Optional[str]] = mapped_column(String(500))
    genre: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    duration: Mapped[timedelta] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    album: Mapped['Album'] = relationship(back_populates='tracks')
    artist: Mapped['Artist'] = relationship(back_populates='tracks')

    __table_args__ = (
        Index(
            'idx_track_title_trgm', 
            'title', 
            postgresql_using='gin', 
            postgresql_ops={'title': 'gin_trgm_ops'}
        ),
    )

class Artist(Base):
    __tablename__ = 'artists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, unique=True)
    image_key: Mapped[Optional[str]] = mapped_column(String(500), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    albums: Mapped[List['Album']] = relationship(back_populates='artist', cascade='all, delete-orphan')
    tracks: Mapped[List['Track']] = relationship(back_populates='artist', cascade='all, delete-orphan')

    __table_args__ = (
        Index(
            'idx_artist_name_trgm', 
            'name', 
            postgresql_using='gin', 
            postgresql_ops={'name': 'gin_trgm_ops'}
        ),
    )

class Album(Base):
    __tablename__ = 'albums'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    image_key: Mapped[Optional[str]] = mapped_column(String(500), unique=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey('artists.id'), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    artist: Mapped['Artist'] = relationship(back_populates='albums')
    tracks: Mapped[List['Track']] = relationship(back_populates='album', cascade='all, delete-orphan')

    __table_args__ = (
        Index(
            'idx_album_name_trgm', 
            'name', 
            postgresql_using='gin', 
            postgresql_ops={'name': 'gin_trgm_ops'}
        ),
    )