from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Filter
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
from keyboards.admin_kb import get_massage_admin_kb

logger = logging.getLogger(__name__)
router = Router()

PACKAGE_OPTIONS = [5, 10, 15]


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user.id in settings.SUPERADMIN_IDS


class AddClientForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_package = State()


def _package_kb(client_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            *[
                [InlineKeyboardButton(
                    text=f"{n} сеансов",
                    callback_data=f"pkg_{n}",
                )]
                for n in PACKAGE_OPTIONS
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_massage")],
        ]
    )


@router.callback_query(IsAdmin(), F.data == "admin_massage")
async def massage_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "💆‍♂️ <b>Управление массажем</b>",
        reply_markup=get_massage_admin_kb(),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "msg_add_client")
async def add_client_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("📝 Введите ФИО клиента:")
    await state.set_state(AddClientForm.waiting_for_name)
    await callback.answer()


@router.message(IsAdmin(), AddClientForm.waiting_for_name)
async def add_client_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await state.update_data(client_name=name)
    await message.answer(
        f"Выберите пакет для <b>{name}</b>:",
        reply_markup=_package_kb(name),
    )
    await state.set_state(AddClientForm.waiting_for_package)


@router.callback_query(IsAdmin(), AddClientForm.waiting_for_package, F.data.startswith("pkg_"))
async def add_client_finish(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    count = int(callback.data.split("_")[1])
    data = await state.get_data()
    name = data["client_name"]

    db_id = await create_client_with_package(name, PackageType.MASSAGE, count)
    link = await create_start_link(bot, str(db_id), encode=True)

    await callback.message.edit_text(
        f"✅ Клиент <b>{name}</b> добавлен!\n"
        f"🎟 Пакет: {count} сеансов\n"
        f"🔗 Ссылка:\n{link}",
    )
    await state.clear()
    logger.info("Добавлен клиент массажа '%s' db_id=%s пакет=%s", name, db_id, count)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "msg_deduct")
async def show_massage_clients(callback: CallbackQuery) -> None:
    users = await get_active_users_by_type(PackageType.MASSAGE)

    if not users:
        await callback.answer("Нет активных клиентов массажа", show_alert=True)
        return

    kb = []
    for u in users:
        pkg = next(
            (p for p in u.packages
             if p.package_type == PackageType.MASSAGE
             and p.status == PackageStatus.ACTIVE),
            None,
        )
        if not pkg:
            continue
        kb.append([InlineKeyboardButton(
            text=f"👤 {u.full_name} (остаток: {pkg.remaining_sessions})",
            callback_data=f"msg_dec_{u.id}",
        )])

    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_massage")])

    await callback.message.edit_text(
        "👇 Выберите клиента для списания:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@router.callback_query(IsAdmin(), F.data.startswith("msg_dec_"))
async def process_msg_deduction(callback: CallbackQuery) -> None:
    user_id = int(callback.data.split("_")[2])
    res = await deduct_sessions(user_id, PackageType.MASSAGE, 1)

    if res["status"] == "success":
        status = "🏁 Пакет завершён!" if res["completed"] else f"✅ Списано! Остаток: {res['remaining']}"
        await callback.answer(status, show_alert=True)
        await show_massage_clients(callback)
    else:
        await callback.answer(f"❌ {res['message']}", show_alert=True)
        logger.warning("Ошибка списания user_id=%s: %s", user_id, res["message"])
