from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import SUPERADMINS
from keyboards.admin_kb import get_main_admin_kb, get_massage_admin_kb

# Создаем роутер для админской части
router = Router()

# Простой фильтр: проверяем, есть ли ID пользователя в списке админов
# Позже мы заменим это на проверку из базы данных
def is_admin(telegram_id: int) -> bool:
    return telegram_id in SUPERADMINS

@router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return # Если не админ, бот просто игнорирует команду

    await message.answer(
        "👑 <b>Добро пожаловать в Панель Управления!</b>\n\n"
        "Здесь вы можете управлять записями на массаж и курсами обучения.\n"
        "Выберите нужный раздел ниже:",
        reply_markup=get_main_admin_kb(),
        parse_mode="HTML"
    )

# Обработка нажатия на кнопку "Управление Массажем"
@router.callback_query(F.data == "admin_massage")
async def process_massage_menu(callback: CallbackQuery):
    # Изменяем текущее сообщение (чтобы не спамить новыми)
    await callback.message.edit_text(
        "💆‍♀️ <b>Раздел: Массаж</b>\n\n"
        "Выберите действие:",
        reply_markup=get_massage_admin_kb(),
        parse_mode="HTML"
    )
    await callback.answer() # Закрываем уведомление о нажатии (часики на кнопке)

# Обработка нажатия "Назад"
@router.callback_query(F.data == "admin_main")
async def process_back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "👑 <b>Панель Управления</b>\n\n"
        "Выберите нужный раздел ниже:",
        reply_markup=get_main_admin_kb(),
        parse_mode="HTML"
    )
    await callback.answer()
