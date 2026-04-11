from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.deep_linking import create_start_link

from database.requests import create_client_with_package, get_active_users_by_type, deduct_sessions
from keyboards.admin_kb import get_edu_admin_kb

router = Router()

class AddStudentForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_program = State()

@router.callback_query(F.data == "admin_edu")
async def edu_menu(callback: CallbackQuery):
    await callback.message.edit_text("🎓 <b>Управление обучением</b>", reply_markup=get_edu_admin_kb(), parse_mode="HTML")

@router.callback_query(F.data == "edu_add_student")
async def add_student_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите ФИО ученика:")
    await state.set_state(AddStudentForm.waiting_for_name)

@router.message(AddStudentForm.waiting_for_name)
async def add_student_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 мес (12)", callback_data="edu_12")],
        [InlineKeyboardButton(text="3 мес (37)", callback_data="edu_37")],
        [InlineKeyboardButton(text="6 мес (75)", callback_data="edu_75")]
    ])
    await message.answer(f"Программа для {message.text}:", reply_markup=kb)
    await state.set_state(AddStudentForm.waiting_for_program)

@router.callback_query(AddStudentForm.waiting_for_program, F.data.startswith("edu_"))
async def add_student_finish(callback: CallbackQuery, state: FSMContext, bot: Bot):
    count = int(callback.data.split("_")[1])
    data = await state.get_data()
    db_id = await create_client_with_package(data['name'], "education", count)
    link = await create_start_link(bot, str(db_id), encode=True)
    await callback.message.edit_text(f"✅ Ученик: {data['name']}\n🔗 Ссылка:\n{link}")
    await state.clear()

@router.callback_query(F.data == "edu_stats")
async def edu_deduct_list(callback: CallbackQuery):
    students = await get_active_users_by_type("education")
    if not students:
        await callback.answer("Нет активных учеников")
        return
    
    kb = []
    for s in students:
        pkg = next(p for p in s.packages if p.package_type == "education" and p.status == "active")
        kb.append([InlineKeyboardButton(text=f"{s.full_name} ({pkg.total_sessions - pkg.used_sessions})", 
                                       callback_data=f"edu_dec_{s.id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edu")])
    await callback.message.edit_text("👇 Списать занятие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(F.data.startswith("edu_dec_"))
async def edu_deduct_proc(callback: CallbackQuery):
    uid = int(callback.data.split("_")[2])
    res = await deduct_sessions(uid, "education", 1)
    await callback.answer(f"✅ Списано! Остаток: {res['remaining']}", show_alert=True)
    await edu_deduct_list(callback)
