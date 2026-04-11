from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.deep_linking import decode_payload

from database.requests import link_telegram_id, get_user_by_tg_id
from config import SUPERADMINS

router = Router()

def get_user_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📊 Мой остаток")],
        [KeyboardButton(text="🌐 Сменить язык")]
    ], resize_keyboard=True)

def get_language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")]
    ])

@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject):
    try:
        db_user_id = int(decode_payload(command.args))
        user = await link_telegram_id(db_user_id, message.from_user.id)
        if user:
            await message.answer(f"🌟 Добро пожаловать, <b>{user.full_name}</b>!\nВыберите язык интерфейса:", 
                                reply_markup=get_language_kb(), parse_mode="HTML")
    except Exception:
        await message.answer("❌ Ссылка недействительна.")

@router.message(CommandStart())
async def cmd_start_normal(message: Message):
    if message.from_user.id in SUPERADMINS:
        await message.answer("⚙️ Босс, вы в режиме администратора.\nИспользуйте /admin для управления.", 
                             reply_markup=get_user_main_kb())
        return

    user = await get_user_by_tg_id(message.from_user.id)
    if user:
        await message.answer(f"Рады видеть вас снова, {user.full_name}!", reply_markup=get_user_main_kb())
    else:
        await message.answer("🔒 Доступ ограничен. Обратитесь к мастеру.")

@router.message(F.text == "📊 Мой остаток")
async def show_profile(message: Message):
    user = await get_user_by_tg_id(message.from_user.id)
    if not user or not user.packages:
        await message.answer("У вас пока нет активных услуг.")
        return

    text = "📋 <b>Ваши активные услуги:</b>\n\n"
    for p in user.packages:
        name = "💆‍♂️ Массаж" if p.package_type == "massage" else "🎓 Обучение"
        rem = p.total_sessions - p.used_sessions
        text += f"{name}\nОстаток: <b>{rem}</b> из {p.total_sessions}\nСтатус: {'✅ Активен' if p.status == 'active' else '🏁 Завершен'}\n\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🌐 Сменить язык")
async def change_lang(message: Message):
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=get_language_kb())
