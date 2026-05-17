import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.processor.create_superuser import create_superuser
from src.models import User

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session

# 1. Тест отказа в доступе (флаг permission)
@pytest.mark.asyncio
async def test_create_superuser_denied(capsys):
    await create_superuser(permission=False)
    
    captured = capsys.readouterr()
    assert "Superuser auto create denied" in captured.out

# 2. Тест отсутствия обязательных полей (через input)
@pytest.mark.asyncio
async def test_create_superuser_missing_fields(capsys):
    # Имитируем, что пользователь ввел пустые строки
    with patch("builtins.input", side_effect=["", " ", ""]):
        await create_superuser(permission=True)
        
        captured = capsys.readouterr()
        assert "All fields are required!" in captured.out

# 3. Тест случая, когда пользователь уже существует
@pytest.mark.asyncio
async def test_create_superuser_already_exists(mock_session, capsys):
    # Настраиваем мок сессии
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User(id=1, username="admin")
    mock_session.execute.return_value = mock_result

    # Мокаем фабрику сессий
    with patch("src.processor.create_superuser.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.return_value = mock_session
        
        await create_superuser(
            username="admin", 
            email="admin@test.com", 
            password="password123", 
            permission=True
        )

        captured = capsys.readouterr()
        assert "already exists!" in captured.out
        # Убеждаемся, что новый пользователь не создавался
        assert not mock_session.add.called

# 4. Успешное создание суперпользователя (через аргументы)
@pytest.mark.asyncio
async def test_create_superuser_success_args(mock_session, capsys):
    # Имитируем, что пользователя нет в базе
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("src.processor.create_superuser.async_session_maker") as mock_maker, \
         patch("src.processor.create_superuser.pwd_context.hash", return_value="hashed_pass"), \
         patch("src.processor.create_superuser.logger") as mock_logger:
        
        mock_maker.return_value.__aenter__.return_value = mock_session
        
        await create_superuser(
            username="superadmin", 
            email="super@test.com", 
            password="secretpassword", 
            permission=True
        )

        # Проверяем вывод в консоль
        captured = capsys.readouterr()
        assert "created successfully!" in captured.out
        
        # Проверяем работу с БД
        assert mock_session.add.called
        assert mock_session.commit.called
        
        # Проверяем, что созданный объект — действительно суперпользователь
        args, _ = mock_session.add.call_args
        created_user = args[0]
        assert created_user.username == "superadmin"
        assert created_user.is_superuser is True
        assert created_user.hashed_password == "hashed_pass"
        
        # Проверяем логгер
        assert mock_logger.success.called

# 5. Успешное создание через интерактивный ввод (input)
@pytest.mark.asyncio
async def test_create_superuser_success_input(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("src.processor.create_superuser.async_session_maker") as mock_maker, \
         patch("src.processor.create_superuser.pwd_context.hash"), \
         patch("builtins.input", side_effect=["testuser", "test@mail.com", "pass123"]):
        
        mock_maker.return_value.__aenter__.return_value = mock_session
        
        await create_superuser(permission=True)
        
        # Проверяем, что данные из input попали в модель
        args, _ = mock_session.add.call_args
        user = args[0]
        assert user.username == "testuser"
        assert user.email == "test@mail.com"