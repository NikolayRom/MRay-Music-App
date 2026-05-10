from loguru import logger
import sys
from pathlib import Path

LOGS_DIR = Path("/app/logs")
LOGS_DIR.mkdir(exist_ok=True)

if not LOGS_DIR.exists():
    LOGS_DIR = Path(__file__).parent.parent / "logs"
    LOGS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add(LOGS_DIR / "media_service.log", rotation="10 MB", retention="10 days", level="INFO", enqueue=True)

