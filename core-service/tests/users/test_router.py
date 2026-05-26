import pytest
from fastapi import HTTPException, status, UploadFile
from unittest.mock import AsyncMock, patch, MagicMock
from src.users.router import get_profile, update_profile, patch_profile
from src.models import User
from src.common.rbac import CurrentUser
from src.users.schemas import UserProfileUpdate, UserProfilePatch

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_user():
    return User(id=1, username="testuser", email="test@test.com", hashed_password="old_hash", is_active=True)

@pytest.fixture
def mock_current_user():
    return CurrentUser(id=1, is_superuser=False)

@pytest.fixture
def mock_avatar():
    mock = MagicMock(spec=UploadFile)
    mock.filename = "avatar.png"
    return mock

@pytest.mark.asyncio
async def test_get_profile_success(mock_session, mock_current_user, mock_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await get_profile(request=MagicMock(), current_user=mock_current_user, session=mock_session)

    assert result == mock_user
    assert mock_session.execute.called

@pytest.mark.asyncio
async def test_get_profile_not_found(mock_session, mock_current_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await get_profile(request=MagicMock(), current_user=mock_current_user, session=mock_session)
    
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_profile_success(mock_session, mock_user, mock_avatar):
    user_data = UserProfileUpdate(
        new_username="newname",
        new_email="new@test.com",
        new_password="pass",
        new_password2="pass"
    )
    
    mock_user.image_key = "old_avatar_key"

    with patch("src.users.router.get_user_by_username", return_value=None), \
         patch("src.users.router.get_user_by_email", return_value=None), \
         patch("src.users.router.get_image_key", new_callable=AsyncMock) as mock_img, \
         patch("src.users.router.pwd_context.hash", return_value="new_hash"), \
         patch("src.users.router.default_minio_data_delete", new_callable=AsyncMock) as mock_s3_delete:
        
        mock_img.return_value = "new_avatar_key"
        
        result = await update_profile(
            request=MagicMock(),
            user=mock_user,
            user_data=user_data,
            avatar=mock_avatar,
            session=mock_session
        )

        assert result.image_key == "new_avatar_key"
        mock_s3_delete.assert_called_once_with(key="old_avatar_key")
        assert mock_session.commit.called

@pytest.mark.asyncio
async def test_update_profile_conflict_username(mock_session, mock_user, mock_avatar):
    user_data = UserProfileUpdate(new_username="busy", new_email="a@b.com", new_password="1", new_password2="1")
    another_user = User(id=2, username="busy")

    with patch("src.users.router.get_user_by_username", return_value=another_user):
        with pytest.raises(HTTPException) as exc:
            await update_profile(MagicMock(), mock_user, user_data, mock_avatar, mock_session)
        assert exc.value.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_update_profile_password_mismatch(mock_session, mock_user, mock_avatar):
    user_data = UserProfileUpdate(new_username="u", new_email="e", new_password="1", new_password2="2")
    
    with patch("src.users.router.get_user_by_username", return_value=None), \
         patch("src.users.router.get_user_by_email", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await update_profile(MagicMock(), mock_user, user_data, mock_avatar, mock_session)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_patch_profile_partial_success(mock_session, mock_user):
    user_data = UserProfilePatch(new_email="only_email@test.com")

    with patch("src.users.router.get_user_by_email", return_value=None):
        result = await patch_profile(
            request=MagicMock(),
            user=mock_user,
            user_data=user_data,
            avatar=None,
            session=mock_session
        )

        assert result.email == "only_email@test.com"
        assert result.username == "testuser" 
        assert mock_session.commit.called

@pytest.mark.asyncio
async def test_patch_profile_password_logic_error(mock_session, mock_user):
    user_data = UserProfilePatch(new_password="only_one_field")

    with pytest.raises(HTTPException) as exc:
        await patch_profile(MagicMock(), mock_user, user_data, None, mock_session)
    
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "2 required fields" in exc.value.detail

@pytest.mark.asyncio
async def test_patch_profile_with_avatar(mock_session, mock_user, mock_avatar):
    user_data = UserProfilePatch()
    mock_user.image_key = "current_key"

    with patch("src.users.router.get_image_key", new_callable=AsyncMock) as mock_img, \
         patch("src.users.router.default_minio_data_delete", new_callable=AsyncMock) as mock_s3_delete:
        
        mock_img.return_value = "patch_avatar_key"
        
        result = await patch_profile(
            request=MagicMock(),
            user=mock_user,
            user_data=user_data,
            avatar=mock_avatar,
            session=mock_session
        )

        assert result.image_key == "patch_avatar_key"
        mock_s3_delete.assert_called_once_with(key="current_key")


@pytest.mark.asyncio
async def test_get_profile_inactive_user(mock_session, mock_current_user):
    mock_user_inactive = User(id=1, is_active=False)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_inactive
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await get_profile(request=MagicMock(), current_user=mock_current_user, session=mock_session)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_profile_conflict_email(mock_session, mock_user, mock_avatar):
    user_data = UserProfileUpdate(new_username="ok", new_email="busy@test.com", new_password="1", new_password2="1")
    another_user = User(id=2, email="busy@test.com")

    with patch("src.users.router.get_user_by_username", return_value=None), \
         patch("src.users.router.get_user_by_email", return_value=another_user):
        
        with pytest.raises(HTTPException) as exc:
            await update_profile(MagicMock(), mock_user, user_data, mock_avatar, mock_session)
        assert exc.value.status_code == status.HTTP_409_CONFLICT
        assert "email already exists" in exc.value.detail

@pytest.mark.asyncio
async def test_update_profile_avatar_exception(mock_session, mock_user, mock_avatar):
    user_data = UserProfileUpdate(new_username="u", new_email="e", new_password="1", new_password2="1")
    
    with patch("src.users.router.get_user_by_username", return_value=None), \
         patch("src.users.router.get_user_by_email", return_value=None), \
         patch("src.users.router.get_image_key", side_effect=Exception("S3 Error")):
        
        with pytest.raises(HTTPException) as exc:
            await update_profile(MagicMock(), mock_user, user_data, mock_avatar, mock_session)
        assert exc.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

@pytest.mark.asyncio
async def test_update_profile_db_exception(mock_session, mock_user, mock_avatar):
    user_data = UserProfileUpdate(new_username="u", new_email="e", new_password="1", new_password2="1")
    mock_session.commit.side_effect = Exception("DB Crash")

    with patch("src.users.router.get_user_by_username", return_value=None), \
         patch("src.users.router.get_user_by_email", return_value=None), \
         patch("src.users.router.get_image_key", new_callable=AsyncMock), \
         patch("src.users.router.pwd_context.hash"):
        
        with pytest.raises(HTTPException) as exc:
            await update_profile(MagicMock(), mock_user, user_data, mock_avatar, mock_session)
        assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

@pytest.mark.asyncio
async def test_patch_profile_username_conflict(mock_session, mock_user):
    user_data = UserProfilePatch(new_username="taken")
    another_user = User(id=2, username="taken")

    with patch("src.users.router.get_user_by_username", return_value=another_user):
        with pytest.raises(HTTPException) as exc:
            await patch_profile(MagicMock(), mock_user, user_data, None, mock_session)
        assert exc.value.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_patch_profile_email_conflict(mock_session, mock_user):
    user_data = UserProfilePatch(new_email="taken@test.com")
    another_user = User(id=2, email="taken@test.com")

    with patch("src.users.router.get_user_by_email", return_value=another_user):
        with pytest.raises(HTTPException) as exc:
            await patch_profile(MagicMock(), mock_user, user_data, None, mock_session)
        assert exc.value.status_code == status.HTTP_409_CONFLICT

@pytest.mark.asyncio
async def test_patch_profile_password_mismatch(mock_session, mock_user):
    user_data = UserProfilePatch(new_password="123", new_password2="456")

    with pytest.raises(HTTPException) as exc:
        await patch_profile(MagicMock(), mock_user, user_data, None, mock_session)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_patch_profile_avatar_exception(mock_session, mock_user, mock_avatar):
    user_data = UserProfilePatch()
    with patch("src.users.router.get_image_key", side_effect=Exception("S3 Error")):
        with pytest.raises(HTTPException) as exc:
            await patch_profile(MagicMock(), mock_user, user_data, mock_avatar, mock_session)
        assert exc.value.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

@pytest.mark.asyncio
async def test_patch_profile_db_exception(mock_session, mock_user):
    user_data = UserProfilePatch(new_username="new")
    mock_session.commit.side_effect = Exception("DB Crash")

    with patch("src.users.router.get_user_by_username", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await patch_profile(MagicMock(), mock_user, user_data, None, mock_session)
        assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR