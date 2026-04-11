from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import DATABASE_URL
from database.models import Base

# Создаем асинхронный движок подключения к БД
engine = create_async_engine(DATABASE_URL, echo=False)

# Создаем "фабрику" сессий. Сессия — это один канал связи с базой для выполнения запроса
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Эта функция запускается при старте бота и создает все таблицы, если их еще нет"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
