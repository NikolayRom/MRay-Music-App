from sqlalchemy import ForeignKey, String, func, Boolean, DateTime, ARRAY
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from typing import Optional, List
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    image_key: Mapped[Optional[str]] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(100), index=True, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), index=True, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    likes: Mapped[List['Like']] = relationship(back_populates='user', cascade='all, delete-orphan')
    playlists: Mapped[List['Playlist']] = relationship(back_populates='user', cascade='all, delete-orphan')

class Like(Base):
    __tablename__ = 'likes'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    track_id: Mapped[int] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped['User'] = relationship(back_populates='likes')

class Playlist(Base):
    __tablename__ = 'playlists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    track_ids: Mapped[List[int]] = mapped_column(ARRAY(int), default=[])
    image_key: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    user: Mapped['User'] = relationship(back_populates='playlists')