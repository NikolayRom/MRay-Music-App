from fastapi import HTTPException, status
from src.common.logger import logger

def check_object_exist(obj):
    if not obj:
        logger.error(f'Error: object doesn\'t exist')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Object not found')