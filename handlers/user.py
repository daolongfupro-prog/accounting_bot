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
    # 1. ПРОВ
