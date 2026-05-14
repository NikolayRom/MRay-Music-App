import asyncio
from sqlalchemy import select
from src.database import async_session_maker
from src.models import User
from src.common.logger import logger
from src.auth.utils import pwd_context
from typing import Optional

async def create_superuser(
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    permission: bool = True
):
    
    if not permission:
        print(f'Superuser auto create denied')
        return

    print('========== CREATE SUPERUSER ==========')

    if not username:
        username = input('Username: ').strip()
    if not email:
        email = input('Email: ').strip()
    if not password:
        password = input('Password: ').strip()

    if not all([username, email, password]):
        print('All fields are required!')
        return 
    
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(
            (User.username == username) | (User.email == email)
        ))

        if result.scalar_one_or_none():
            print(f'User with {username} username or {email} email already exists!')
            return
        
        user = User(
            username=username,
            email=email,
            hashed_password=pwd_context.hash(password),
            is_superuser=True
        )

        session.add(user)
        await session.commit()
        print(f'Superuser {username} created successfully!')
        logger.success(f'Superuser {username} created successfully!')

if __name__ == '__main__':
    asyncio.run(create_superuser())
