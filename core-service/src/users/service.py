from fastapi import Form, UploadFile, File, HTTPException, status
from typing import Optional, List
from src.users.schemas import UserProfilePatch, UserProfileUpdate
from src.users.utils import get_image_key_from_file, check_content_type_format, check_file_size, streaming_minio_data_upload
from src.common.logger import logger

async def get_image_key(key: str, file: UploadFile = File(...)) -> str:
    check_content_type_format(formats=["image/jpeg", "image/png", "image/jpg"], file=file)
    check_file_size(file=file)

    image_key = get_image_key_from_file(key=key, file=file)

    try:
        await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
        logger.success(f'Successful uploading {file.filename} with {image_key} key')
    except Exception:
        logger.error(f'Error, while trying to upload {file.filename} with {image_key} key')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error, while trying to upload {file.filename} with {image_key} key')

    return image_key

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