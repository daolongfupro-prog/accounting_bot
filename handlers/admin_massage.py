from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link
from database.requests import create_client_with_package, get_active_users_by_type, deduct_sessions
from keyboards.admin_kb import get_massage_admin_kb
router = Router()
class AddClientForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_package = State()
@router.callback_query(F.data == "admin_massage")
async def massage_menu(callback: CallbackQuery):
    await callback.message.edit_text("💆‍♂️ <b>Управление массажем</b>", 
                                     reply_markup=get_massage_admin_kb(), 
                                     parse_mode="HTML")
@router.callback_query(F.data == "msg_add_client")
async def add_client_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите ФИО клиента:")
    await state.set_state(AddClientForm.waiting_for_name)
@router.message(AddClientForm.waiting_for_name)
async def add_client_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 сеансов", callback_data="pkg_5")],
        [InlineKeyboardButton(text="10 сеансов", callback_data="pkg_10")],
        [InlineKeyboardButton(text="15 сеансов", callback_data="pkg_15")]
    ])
    await message.answer(f"Выберите пакет для <b>{message.text}</b>:", reply_markup=kb, parse_mode="HTML")
    await state.set_state(AddClientForm.waiting_for_package)
@router.callback_query(AddClientForm.waiting_for_package, F.data.startswith("pkg_"))
async def add_client_finish(callback: CallbackQuery, state: FSMContext, bot: Bot):
    count = int(callback.data.split("_")[1])
    data = await state.get_data()
    db_id = await create_client_with_package(data['client_name'], "massage", count)
    link = await create_start_link(bot, str(db_id), encode=True)
    
    await callback.message.edit_text(
        f"✅ Клиент: <b>{data['client_name']}</b> добавлена!\n🎟 Пакет: {count} сеансов.\n🔗 Ссылка:\n{link}",
        parse_mode="HTML"
    )
    await state.clear()
@router.callback_query(F.data == "msg_deduct")
async def show_massage_clients(callback: CallbackQuery):
    users = await get_active_users_by_type("massage")
    if not users:
        await callback.answer("Нет активных клиентов массажа", show_alert=True)
        return
    kb = []
    for u in users:
        pkg = next(p for p in u.packages if p.package_type == "massage" and p.status == "active")
        kb.append([InlineKeyboardButton(text=f"👤 {u.full_name} ({pkg.total_sessions - pkg.used_sessions})", 
                                       callback_data=f"msg_dec_{u.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_massage")])
    
    await callback.message.edit_text("👇 Выберите клиента для списания:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
@router.callback_query(F.data.startswith("msg_dec_"))
async def process_msg_deduction(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    res = await deduct_sessions(user_id, "massage", 1)
    
    if res["status"] == "success":
        await callback.answer(f"✅ Списано! Остаток: {res['remaining']}", show_alert=True)
        await show_massage_clients(callback) # Обновляем список
