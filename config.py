import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Прописываем ID прямо здесь. Теперь это наш "белый список"
ADMIN_IDS = [2103579364, 146156901]

# Магия для SQLAlchemy (оставляем, чтобы база работала)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
