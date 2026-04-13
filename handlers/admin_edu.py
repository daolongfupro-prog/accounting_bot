from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.deep_linking import create_start_link

from config import settings
from database.models import PackageStatus, PackageType
from database.requests import (
    create_client_with_package,
    deduct_sessions,
    get_active_users_by_type,
)
from handlers.admin_massage import IsAdmin
from keyboards.admin_kb import get_edu_admin_kb

logger = logging.getLogger(__name__)
router = Router()

PACKAGE_OPTIONS = [4, 8, 12]


class AddStudentForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_package = State()


def _package_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(
                    text=f"{n} занятий",
                    callback_data=f"edu_pkg_{n}",
                )]
                for n in PACKAGE_OPTIONS
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_edu")],
        ]
    )


@router.callback_query(IsAdmin(), F.data == "admin_edu")
async def edu_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🎓 <b>Управление обучением</b>",
        reply_markup=get_edu_admin_kb(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "edu_add_student")
async def add_student_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("📝 Введите ФИО ученика:")
    await state.set_state(AddStudentForm.waiting_for_name)
    await callback.answer()


@router.message(IsAdmin(), AddStudentForm.waiting_for_name)
async def add_student_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await state.update_data(student_name=name)
    await message.answer(
        f"Выберите пакет для <b>{name}</b>:",
        reply_markup=_package_kb(),
    )
    await state.set_state(AddStudentForm.waiting_for_package)


@router.callback_query(IsAdmin(), AddStudentForm.waiting_for_package, F.data.startswith("edu_pkg_"))
async def add_student_finish(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    count = int(callback.data.split("_")[2])
    data = await state.get_data()
    name = data["student_name"]

    db_id = await create_client_with_package(name, PackageType.EDUCATION, count)
    link = await create_start_link(bot, str(db_id), encode=True)

    await callback.message.edit_text(
        f"✅ Ученик <b>{name}</b> добавлен!\n"
        f"🎟 Пакет: {count} занятий\n"
        f"🔗 Ссылка:\n{link}",
    )
    await state.clear()
    logger.info("Добавлен ученик '%s' db_id=%s пакет=%s", name, db_id, count)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "edu_deduct_list")
async def edu_deduct_list(callback: CallbackQuery) -> None:
    students = await get_active_users_by_type(PackageType.EDUCATION)

    if not students:
        await callback.answer("Нет активных учеников", show_alert=True)
        return

    kb = []
    for s in students:
        pkg = next(
            (p for p in s.packages
             if p.package_type == PackageType.EDUCATION
             and p.status == PackageStatus.ACTIVE),
            None,
        )
        if not pkg:
            continue
        kb.append([InlineKeyboardButton(
            text=f"👤 {s.full_name} (остаток: {pkg.remaining_sessions})",
            callback_data=f"edu_dec_{s.id}",
        )])

    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edu")])

    await callback.message.edit_text(
        "👇 Выберите ученика для списания:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("edu_dec_"))
async def process_edu_deduction(callback: CallbackQuery) -> None:
    user_id = int(callback.data.split("_")[2])
    res = await deduct_sessions(user_id, PackageType.EDUCATION, 1)

    if res["status"] == "success":
        status = "🏁 Пакет завершён!" if res["completed"] else f"✅ Списано! Остаток: {res['remaining']}"
        await callback.answer(status, show_alert=True)
        await edu_deduct_list(callback)
    else:
        await callback.answer(f"❌ {res['message']}", show_alert=True)
        logger.warning("Ошибка списания user_id=%s: %s", user_id, res["message"])


@router.callback_query(IsAdmin(), F.data == "edu_stats")
async def show_edu_stats(callback: CallbackQuery) -> None:
    students = await get_active_users_by_type(PackageType.EDUCATION)

    if not students:
        await callback.answer("Нет активных учеников", show_alert=True)
        return

    lines = ["📊 <b>Текущие ученики:</b>\n"]
    for s in students:
        pkg = next(
            (p for p in s.packages
             if p.package_type == PackageType.EDUCATION
             and p.status == PackageStatus.ACTIVE),
            None,
        )
        if pkg:
            lines.append(
                f"👤 {s.full_name}: {pkg.used_sessions}/{pkg.total_sessions} "
                f"(остаток: {pkg.remaining_sessions})"
            )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=get_edu_admin_kb(),
    )
    await callback.answer()
