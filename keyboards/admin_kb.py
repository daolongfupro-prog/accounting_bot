from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💆‍♀️ Управление Массажем", callback_data="admin_massage")],
        [InlineKeyboardButton(text="🎓 Управление Обучением", callback_data="admin_edu")],
        [InlineKeyboardButton(text="👥 Список Администраторов", callback_data="admin_list")]
    ])

def get_massage_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить клиента", callback_data="msg_add_client"),
            InlineKeyboardButton(text="➖ Списать сеанс", callback_data="msg_deduct")
        ],
        [InlineKeyboardButton(text="📊 Статистика и остатки", callback_data="msg_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])

def get_edu_admin_kb() -> InlineKeyboardMarkup:
    """Клавиатура для управления обучением"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить ученика", callback_data="edu_add_student"),
            InlineKeyboardButton(text="➖ Списать занятие", callback_data="edu_deduct")
        ],
        [InlineKeyboardButton(text="📅 Расписание", callback_data="edu_schedule")],
        [InlineKeyboardButton(text="📈 Статистика учеников", callback_data="edu_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
    ])
