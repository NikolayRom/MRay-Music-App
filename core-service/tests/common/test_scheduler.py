import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from src.common.scheduler import clean_up_expired_tokens, clean_up_users_history, setup_scheduler

@pytest.fixture
def mock_settings():
    with patch("src.common.scheduler.settings") as mocked_settings:
        mocked_settings.INACTIVE_REFRESH_TOKEN_LIFETIME_DAYS = 7
        mocked_settings.USER_HISTORY_LIFETIME_DAYS = 30
        yield mocked_settings

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.__aenter__.return_value = session
    return session

@pytest.mark.asyncio
async def test_clean_up_expired_tokens_success(mock_session, mock_settings):
    with patch("src.common.scheduler.async_session_maker", return_value=mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        with patch("src.common.scheduler.logger") as mock_logger:
            await clean_up_expired_tokens()

            assert mock_session.execute.called
            assert mock_session.commit.called
            mock_logger.success.assert_called_with('Cleaned up 5 expired refresh tokens')

@pytest.mark.asyncio
async def test_clean_up_expired_tokens_no_records(mock_session, mock_settings):
    with patch("src.common.scheduler.async_session_maker", return_value=mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        with patch("src.common.scheduler.logger") as mock_logger:
            await clean_up_expired_tokens()
            
            mock_logger.info.assert_called_with('No expired refresh tokens to clean up')

@pytest.mark.asyncio
async def test_clean_up_users_history_exception(mock_session, mock_settings):
    with patch("src.common.scheduler.async_session_maker", return_value=mock_session):
        mock_session.execute.side_effect = Exception("DB Error")

        with patch("src.common.scheduler.logger") as mock_logger:
            await clean_up_users_history()

            assert mock_session.rollback.called
            assert mock_logger.error.called
            assert "Failed to clean up users history" in mock_logger.error.call_args[0][0]

def test_setup_scheduler():
    with patch("src.common.scheduler.scheduler") as mock_scheduler:
        with patch("src.common.scheduler.logger") as mock_logger:
            setup_scheduler()

            assert mock_scheduler.add_job.call_count == 2
            
            calls = [call.kwargs['id'] for call in mock_scheduler.add_job.call_args_list]
            assert 'clean_up_expired_tokens' in calls
            assert 'clean_up_users_history' in calls

            assert mock_scheduler.start.called
            assert mock_logger.info.called

@pytest.mark.asyncio
async def test_clean_up_logic_dates(mock_session, mock_settings):
    with patch("src.common.scheduler.async_session_maker", return_value=mock_session):
        fixed_now = datetime(2023, 1, 10, tzinfo=timezone.utc)
        
        with patch("src.common.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            
            await clean_up_expired_tokens()
            
            assert mock_session.execute.called