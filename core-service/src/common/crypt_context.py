import bcrypt
from src.common.logger import logger

class CryptContext:
    def hash(self, password: str) -> str:
        try:
            password_bytes = password.encode('utf-8')
            
            if len(password_bytes) > 72:
                import hashlib
                password_bytes = hashlib.sha256(password_bytes).digest()
            
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        except Exception as e:
            logger.critical(f'Failed to hash password: {e}')

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            plain_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            if len(plain_bytes) > 72:
                import hashlib
                plain_bytes = hashlib.sha256(plain_bytes).digest()
            
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        except Exception as e:
            logger.critical(f'Failed to verify password: {e}')

pwd_context = CryptContext()