from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.deep_linking import decode_payload

from database.requests import link_telegram_id, get_user_by_tg_id, update_user_language
from config import SUPERADMINS

router = Router()

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
TEXTS = {
    "ru": {
        "main_menu": "Выберите действие:",
        "balance": "📊 Мой остаток",
        "change_lang": "🌐 Сменить язык",
        "profile_head": "📋 <b>Ваши активные услуги:</b>",
        "massage": "💆‍♂️ Массаж",
        "edu": "🎓 Обучение",
        "rem": "Остаток",
        "of": "из",
        "active": "✅ Активен",
        "completed": "🏁 Завершен",
        "lang_set": "✅ Язык установлен!"
    },
    "uz": {
        "main_menu": "Harakatni tanlang:",
        "balance": "📊 Mening qoldig'im",
        "change_lang": "🌐 Tilni o'zgartirish",
        "profile_head": "📋 <b>Sizning faol xizmatlaringiz:</b>",
        "massage": "💆‍♂️ Massaj",
        "edu": "🎓 O'qitish",
        "rem": "Qoldiq",
        "of": "dan",
        "active": "✅ Faol",
        "completed": "🏁 Yakunlandi",
        "lang_set": "✅ Til o'rnatildi!"
    },
    "en": {
        "main_menu": "Choose an action:",
        "balance": "📊 My balance",
        "change_lang": "🌐 Change language",
        "profile_head": "📋 <b>Your active services:</b>",
        "massage": "💆‍♂️ Massage",
        "edu": "🎓 Education",
        "rem": "Remaining",
        "of": "of",
        "active": "✅ Active",
        "completed": "🏁 Completed",
        "lang_set": "✅ Language set!"
    }
}

def get_user_main_kb(lang="ru"):
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=TEXTS[lang]["balance"])],
        [KeyboardButton(text=TEXTS[lang]["change_lang"])]
    ], resize_keyboard=True)

def get_language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])

@router.message(CommandStart())
async def cmd_start_unified(message: Message, command: CommandObject):
    # 1. ПРОВЕРЯЕМ, ПРИШЕЛ ЛИ ПОЛЬЗОВАТЕЛЬ ПО ССЫЛКЕ (ЕСТЬ ЛИ АРГУМЕНТЫ)
    if command.args:
        try:
            # Расшифровываем токен (например, 'Mw')
            db_user_id = int(decode_payload(command.args))
            
            # Привязываем Telegram ID к карточке в БД
            user = await link_telegram_id(db_user_id, message.from_user.id)
            
            if user:
                await message.answer(
                    f"🌟 Здравствуйте, <b>{user.full_name}</b>!\nВыберите язык / Tilni tanlang / Choose language:", 
                    reply_markup=get_language_kb(), 
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Карточка клиента не найдена или ссылка уже была использована.")
            return  # Останавливаем выполнение, чтобы не пойти в обычный старт
            
        except Exception as e:
            print(f"Ошибка диплинка: {e}")  # Выведет ошибку в консоль сервера для дебага
            await message.answer("❌ Ссылка недействительна или повреждена.")
            return

    # 2. ЕСЛИ ЭТО ОБЫЧНЫЙ СТАРТ (БЕЗ ССЫЛКИ)
    # Проверка на супер-админа
    if message.from_user.id in SUPERADMINS:
        await message.answer("⚙️ Режим администратора: /admin", reply_markup=get_user_main_kb("ru"))
        return

    # Проверка обычного клиента, который уже есть в базе
    user = await get_user_by_tg_id(message.from_user.id)
    if user:
        lang = user.language if user.language in TEXTS else "ru"
        await message.answer(f"Рады видеть вас снова, {user.full_name}!", reply_markup=get_user_main_kb(lang))
    else:
        # Срабатывает ТОЛЬКО если человек пришел без ссылки и его нет в базе
        await message.answer("🔒 Доступ ограничен. Обратитесь к мастеру.")

@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    await update_user_language(callback.from_user.id, lang_code)
    
    # Сразу обновляем меню на новом языке
    await callback.message.answer(TEXTS[lang_code]["lang_set"], reply_markup=get_user_main_kb(lang_code))
    await callback.message.delete()
    await callback.answer()

@router.message(F.text.in_([TEXTS["ru"]["balance"], TEXTS["uz"]["balance"], TEXTS["en"]["balance"]]))
async def show_profile(message: Message):
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user and user.language in TEXTS else "ru"
    
    if not user or not user.packages:
        await message.answer("У вас пока нет активных услуг.")
        return

    text = f"{TEXTS[lang]['profile_head']}\n\n"
    for p in user.packages:
        name = TEXTS[lang]["massage"] if p.package_type == "massage" else TEXTS[lang]["edu"]
        rem = p.total_sessions - p.used_sessions
        status = TEXTS[lang]["active"] if p.status == "active" else TEXTS[lang]["completed"]
        text += f"{name}\n{TEXTS[lang]['rem']}: <b>{rem}</b> {TEXTS[lang]['of']} {p.total_sessions}\n{status}\n\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(F.text.in_([TEXTS["ru"]["change_lang"], TEXTS["uz"]["change_lang"], TEXTS["en"]["change_lang"]]))
async def change_lang(message: Message):
    await message.answer("Выберите язык / Tilni tanlang / Choose language:", reply_markup=get_language_kb())
