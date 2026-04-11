from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link

router = Router()

# 1. Создаем "состояния" (шаги), которые бот будет запоминать
class AddClientForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_package = State()

# 2. Ловим нажатие на кнопку "➕ Добавить клиента" из админки
@router.callback_query(F.data == "msg_add_client")
async def start_adding_client(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 <b>Добавление нового VIP-клиента</b>\n\n"
        "Введите Имя и Фамилию клиента:",
        parse_mode="HTML"
    )
    # Включаем состояние "Жду имя"
    await state.set_state(AddClientForm.waiting_for_name)
    await callback.answer()

# 3. Ловим текст (Имя), пока бот находится в состоянии waiting_for_name
@router.message(AddClientForm.waiting_for_name)
async def process_client_name(message: Message, state: FSMContext):
    # Сохраняем имя в оперативную память бота
    await state.update_data(client_name=message.text)
    
    # Клавиатура для выбора пакета
    packages_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 сеансов", callback_data="pkg_5")],
        [InlineKeyboardButton(text="10 сеансов", callback_data="pkg_10")],
        [InlineKeyboardButton(text="15 сеансов (VIP)", callback_data="pkg_15")]
    ])
    
    await message.answer(
        f"Имя <b>{message.text}</b> сохранено.\n"
        f"Выберите пакет сеансов массажа:",
        reply_markup=packages_kb,
        parse_mode="HTML"
    )
    # Переключаем на следующий шаг
    await state.set_state(AddClientForm.waiting_for_package)

# 4. Ловим выбор пакета (кнопки, начинающиеся на "pkg_")
@router.callback_query(AddClientForm.waiting_for_package, F.data.startswith("pkg_"))
async def process_client_package(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Достаем количество сеансов из callback_data (например, из "pkg_15" достаем 15)
    sessions_count = int(callback.data.split("_")[1])
    
    # Достаем сохраненное имя из памяти
    data = await state.get_data()
    client_name = data['client_name']
    
    # ==========================================
    # ЗДЕСЬ БУДЕТ ЗАПИСЬ В БАЗУ ДАННЫХ (PostgreSQL)
    # 1. Создаем пользователя (client_name)
    # 2. Создаем ему пакет (sessions_count)
    # 3. Получаем его уникальный ID из базы (допустим, ID = 105)
    db_user_id = 105 # Пока имитируем ID из базы
    # ==========================================
    
    # Генерируем ту самую умную ссылку (Deep Link) для этого ID
    # encode=True сделает ссылку зашифрованной, чтобы ID не читался явно
    link = await create_start_link(bot, str(db_user_id), encode=True)
    
    await callback.message.edit_text(
        f"✅ <b>Карточка клиента успешно создана!</b>\n\n"
        f"👤 Клиент: <b>{client_name}</b>\n"
        f"🎟 Пакет: <b>{sessions_count} сеансов</b>\n\n"
        f"🔗 <b>Ссылка для клиента:</b>\n{link}\n\n"
        f"<i>Отправьте эту ссылку клиенту. Когда он перейдет по ней, бот автоматически его узнает.</i>",
        parse_mode="HTML"
    )
    
    # Очищаем состояния, процесс завершен
    await state.clear()
    await callback.answer()
