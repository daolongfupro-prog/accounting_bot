from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import decode_payload

# Импортируем функции базы и список админов
from database.requests import link_telegram_id, get_user_by_tg_id
from config import SUPERADMINS

router = Router()

def get_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")]
    ])

@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject):
    args = command.args
    try:
        db_user_id = int(decode_payload(args))
        user = await link_telegram_id(db_user_id, message.from_user.id)
        
        if user:
            await message.answer(
                f"👋 Здравствуйте, <b>{user.full_name}</b>!\nВыберите язык / Tilni tanlang:",
                reply_markup=get_language_kb(),
                parse_mode="HTML"
            )
    except Exception:
        await message.answer("❌ Ошибка ссылки.")

@router.message(CommandStart())
async def cmd_start_normal(message: Message):
    # 1. Сначала проверяем: может это сам Босс зашел?
    if message.from_user.id in SUPERADMINS:
        await message.answer(
            "⚙️ <b>Вы зашли как администратор!</b>\n\n"
            "Чтобы управлять клиентами и обучением, используйте команду: /admin",
            parse_mode="HTML"
        )
        return

    # 2. Если не админ, ищем в базе клиентов
    user = await get_user_by_tg_id(message.from_user.id)
    
    if user:
        await message.answer(f"Приветствуем снова, <b>{user.full_name}</b>!")
    else:
        # 3. Если и в базе нет, тогда уже закрываем доступ
        await message.answer(
            "🔒 <b>Доступ ограничен</b>\n\n"
            "Этот бот предназначен только для клиентов студии и учеников.\n"
            "Для получения доступа обратитесь к вашему мастеру."
        )
