from fastapi import HTTPException, status

def check_object_exist(obj):
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Object not found')