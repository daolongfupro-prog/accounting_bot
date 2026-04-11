from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import decode_payload

router = Router()

# 1. Клавиатура выбора языка
def get_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])

# 2. Ловим старт по "Умной ссылке"
@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject):
    # command.args содержит наш зашифрованный ID из ссылки
    args = command.args
    
    try:
        # Расшифровываем ID клиента (например, получим "105")
        db_user_id = int(decode_payload(args))
        
        # ==========================================
        # ЗДЕСЬ БУДЕТ РАБОТА С БАЗОЙ ДАННЫХ:
        # 1. Ищем карточку клиента по ID = db_user_id
        # 2. Обновляем в ней telegram_id = message.from_user.id
        #    (Теперь бот навсегда запомнил, чей это аккаунт)
        # 3. Достаем Имя из базы
        client_name = "Иван" # Временная заглушка
        # ==========================================
        
        await message.answer(
            f"👋 Добро пожаловать, <b>{client_name}</b>!\n\n"
            "Пожалуйста, выберите язык интерфейса\n"
            "Iltimos, tilni tanlang\n"
            "Please choose a language:",
            reply_markup=get_language_kb(),
            parse_mode="HTML"
        )
    except Exception:
        # Если ссылка битая или ID не расшифровался
        await message.answer("❌ Ошибка: неверная или устаревшая ссылка.")

# 3. Ловим обычный старт (без ссылки)
@router.message(CommandStart())
async def cmd_start_normal(message: Message):
    # Если случайный человек нашел бота в поиске Телеграма
    # Здесь мы будем проверять, есть ли его telegram_id в нашей БД
    
    # Заглушка для неавторизованных:
    await message.answer(
        "🔒 Здравствуйте! Этот бот работает только по персональным приглашениям.\n"
        "Пожалуйста, обратитесь к администратору для получения доступа."
    )

# 4. Обработка выбора языка
@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery):
    # Достаем код языка из кнопки (ru, uz, en)
    lang_code = callback.data.split("_")[1] 
    
    # ==========================================
    # ЗДЕСЬ БУДЕТ РАБОТА С БАЗОЙ ДАННЫХ:
    # Сохраняем выбранный язык (lang_code) в профиль пользователя
    # ==========================================
    
    # Временная логика ответов (позже это будет работать через файлы локализации)
    if lang_code == "ru":
        text = "✅ Язык успешно установлен!\n\n<i>Здесь будет отображаться ваш остаток сеансов и дата оплаты...</i>"
    elif lang_code == "uz":
        text = "✅ Til muvaffaqiyatli o'rnatildi!\n\n<i>Bu yerda seanslaringiz qoldig'i va to'lov sanasi ko'rsatiladi...</i>"
    else:
        text = "✅ Language successfully set!\n\n<i>Your remaining sessions and payment date will be displayed here...</i>"
        
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
