import uuid
from fastapi import UploadFile

def gen_uuid():
    return str(uuid.uuid4().hex)

def get_file_full(file: UploadFile):
    return f'{gen_uuid()}_{file.filename}'

def get_file_key(file: UploadFile):
    return get_file_full(file=file).rsplit('.', 1)[0]