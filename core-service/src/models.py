from sqlalchemy import ForeignKey, String, func, Boolean, DateTime, ARRAY, Integer
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.timezone('UTC', func.now()), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.timezone('UTC', func.now()), onupdate=func.timezone('UTC', func.now()), nullable=False)

    likes: Mapped[List['Like']] = relationship(back_populates='user', cascade='all, delete-orphan')
    playlists: Mapped[List['Playlist']] = relationship(back_populates='user', cascade='all, delete-orphan')
    tokens: Mapped[List['RefreshToken']] = relationship(back_populates='user', cascade='all, delete-orphan')
    history: Mapped[List['UserHistory']] = relationship(back_populates='user', cascade='all, delete-orphan')

class Like(Base):
    __tablename__ = 'likes'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, nullable=False)
    track_id: Mapped[int] = mapped_column(index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.timezone('UTC', func.now()), nullable=False)

    user: Mapped['User'] = relationship(back_populates='likes')

class Playlist(Base):
    __tablename__ = 'playlists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    track_ids: Mapped[List[int]] = mapped_column(ARRAY(Integer), default=[])
    image_key: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.timezone('UTC', func.now()), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.timezone('UTC', func.now()), onupdate=func.timezone('UTC', func.now()), nullable=False)

    user: Mapped['User'] = relationship(back_populates='playlists')

class RefreshToken(Base):
    __tablename__ = 'tokens'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    hashed_token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    exp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    user: Mapped['User'] = relationship(back_populates='tokens')

class UserHistory(Base):
    __tablename__ = 'history'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    track_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.timezone('UTC', func.now()), index=True, nullable=False)

    user: Mapped['User'] = relationship(back_populates='history')
