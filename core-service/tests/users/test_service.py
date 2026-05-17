import pytest
from src.users.service import user_profile_update_form, user_profile_patch_form
from src.users.schemas import UserProfileUpdate, UserProfilePatch

def test_user_profile_update_form_mapping():
    """Проверка создания схемы для полного обновления профиля."""
    result = user_profile_update_form(
        new_username="new_name",
        new_password="pass1",
        new_password2="pass1",
        new_email="new@test.com"
    )
    
    assert isinstance(result, UserProfileUpdate)
    assert result.new_username == "new_name"
    assert result.new_email == "new@test.com"
    assert result.new_password == "pass1"

def test_user_profile_patch_form_full():
    """Проверка создания схемы для частичного обновления (все поля заполнены)."""
    result = user_profile_patch_form(
        new_username="patch_name",
        new_password="p1",
        new_password2="p1",
        new_email="p@test.com"
    )
    
    assert isinstance(result, UserProfilePatch)
    assert result.new_username == "patch_name"

def test_user_profile_patch_form_partial():
    """Проверка частичного обновления, когда часть полей None."""
    result = user_profile_patch_form(
        new_username="only_name",
        new_password=None,
        new_password2=None,
        new_email=None
    )
    
    assert isinstance(result, UserProfilePatch)
    assert result.new_username == "only_name"
    assert result.new_password is None
    assert result.new_email is None

def test_user_profile_patch_form_empty():
    """Проверка случая, когда форма пустая."""
    result = user_profile_patch_form(None, None, None, None)
    
    assert isinstance(result, UserProfilePatch)
    assert result.new_username is None
    assert result.new_email is None