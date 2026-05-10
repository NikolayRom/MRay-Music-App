import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.database import get_async_session

@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session

@pytest.fixture
def mock_s3():
    with MagicMock() as mock:
        yield mock

@pytest.fixture(scope="function")
async def ac(mock_session):
    app.dependency_overrides[get_async_session] = lambda: mock_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()