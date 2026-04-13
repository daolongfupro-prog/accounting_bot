from __future__ import annotations

import io
import logging
from datetime import datetime

import openpyxl
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import settings
from database.models import PackageType
from database.requests import get_all_data_for_export
from keyboards.admin_kb import get_main_admin_kb

logger = logging.getLogger(__name__)
router = Router()


def _is_superadmin(telegram_id: int) -> bool:
    return telegram_id in settings.SUPERADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    if not _is_superadmin(message.from_user.id):
        logger.warning("Попытка входа в админку tg_id=%s", message.from_user.id)
        return
    await message.answer(
        "🌟 <b>Панель управления администратора</b>",
        reply_markup=get_main_admin_kb(),
    )


@router.callback_query(F.data == "admin_main")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🌟 <b>Панель управления администратора</b>",
        reply_markup=get_main_admin_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_backup")
async def export_excel(callback: CallbackQuery) -> None:
    await callback.answer("⏳ Генерирую файл...")

    users = await get_all_data_for_export()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Studio Backup"
    ws.append([
        "ID Юзера", "Telegram ID", "Имя Клиента",
        "Тип Услуги", "Всего", "Использовано", "Остаток", "Статус",
    ])

    for u in users:
        if not u.packages:
            ws.append([u.id, u.telegram_id, u.full_name, "Нет услуг", 0, 0, 0, "N/A"])
            continue
        for p in u.packages:
            ws.append([
                u.id,
                u.telegram_id,
                u.full_name,
                "Массаж" if p.package_type == PackageType.MASSAGE else "Обучение",
                p.total_sessions,
                p.used_sessions,
                p.remaining_sessions,
                "Активен" if p.status.value == "active" else "Завершён",
            ])

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    await callback.message.answer_document(
        BufferedInputFile(file_stream.read(), filename=filename),
        caption="📁 <b>Актуальный бэкап базы данных</b>",
    )
    logger.info("Бэкап выгружен суперадмином tg_id=%s", callback.from_user.id)
