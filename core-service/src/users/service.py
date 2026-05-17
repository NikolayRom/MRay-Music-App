from fastapi import Form
from typing import Optional
from src.users.schemas import UserProfilePatch, UserProfileUpdate

def user_profile_update_form(
    new_username: str = Form(...),
    new_password: str = Form(...),
    new_password2: str = Form(...),
    new_email: str = Form(...)
) -> UserProfileUpdate:
    return UserProfileUpdate(new_username=new_username, new_email=new_email, new_password=new_password, new_password2=new_password2)

def user_profile_patch_form(
    new_username: Optional[str] = Form(None),
    new_password: Optional[str] = Form(None),
    new_password2: Optional[str] = Form(None),
    new_email: Optional[str] = Form(None)  
) -> UserProfilePatch:
    return UserProfilePatch(new_username=new_username, new_email=new_email, new_password=new_password, new_password2=new_password2)