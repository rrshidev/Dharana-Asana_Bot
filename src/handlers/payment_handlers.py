import asyncio
import logging
import os

import httpx
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://dharana-api:8000")
BOT_ADMIN_KEY = os.getenv("BOT_ADMIN_KEY", "")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "")

# In-memory set of telegram ids that are expected to send a receipt after /pay
awaiting_receipt = set()

_pay_text = (
    "💳 <b>Оплата подписки Premium</b>\n\n"
    "Переведите сумму на одну из карт (получатель: <b>Руслан Дмитриевич С.</b>) "
    "и отправьте сюда скриншот/фото чека об оплате.\n"
    "После проверки админом Premium будет открыт.\n\n"
    "Реквизиты:\n"
    "{requisites}\n\n"
    "Отправьте фото чека 👇"
)


class PaymentHandlers:
    def __init__(self, bot, subscription_service=None):
        self.bot = bot
        self.subscription_service = subscription_service

    def _headers(self):
        return {"X-Bot-Key": BOT_ADMIN_KEY}

    async def _send_pay_requisites(self, chat_id: int, is_callback: bool = False):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/payments/requisites",
                    headers=self._headers(),
                    timeout=10,
                )
                requisites = resp.json().get("requisites", [])
        except Exception as e:
            logger.error(f"pay requisites error: {e}")
            requisites = []

        if not requisites:
            text = "Реквизиты пока недоступны. Попробуйте позже."
            if is_callback:
                return text, None
            return await self.bot.send_message(chat_id, text)

        lines = []
        for i, r in enumerate(requisites, 1):
            lines.append(f"{i}. {r.get('bank', '')} — <code>{r.get('card', '')}</code>")

        # Получатель указывается один раз в _pay_text (он уже выше списка карт)
        if is_callback:
            return _pay_text.format(requisites="\n".join(lines)), None

        awaiting_receipt.add(chat_id)
        await self.bot.send_message(
            chat_id,
            _pay_text.format(requisites="\n".join(lines)),
            parse_mode=ParseMode.HTML,
        )

    async def pay_command(self, message: types.Message):
        await self._send_pay_requisites(message.from_user.id)

    async def pay_now_callback(self, callback_query: types.CallbackQuery):
        text, _ = await self._send_pay_requisites(
            callback_query.from_user.id, is_callback=True
        )
        await self.bot.answer_callback_query(callback_query.id)
        awaiting_receipt.add(callback_query.from_user.id)
        try:
            await self.bot.edit_message_text(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await self.bot.send_message(
                callback_query.from_user.id, text, parse_mode=ParseMode.HTML
            )

    async def handle_receipt_photo(self, message: types.Message):
        tg_id = message.from_user.id
        if tg_id not in awaiting_receipt:
            await message.reply(
                "Чтобы оплатить, сначала отправьте команду /pay или нажмите «Оплатить» в меню подписки."
            )
            return

        if not message.photo:
            return

        largest = message.photo[-1]
        try:
            file = await self.bot.get_file(largest.file_id)
            downloaded = await self.bot.download_file(file.file_path)
            data = downloaded.read() if not isinstance(downloaded, bytes) else downloaded
        except Exception as e:
            logger.error(f"download receipt error: {e}")
            return await message.reply("Не удалось получить фото чека. Попробуйте ещё раз.")

        awaiting_receipt.discard(tg_id)

        try:
            files = {
                "file": ("receipt.jpg", data, "image/jpeg"),
            }
            data_form = {
                "telegram_id": str(tg_id),
                "user_name": message.from_user.full_name or "",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/payments/receipt",
                    headers=self._headers(),
                    data=data_form,
                    files=files,
                    timeout=30,
                )
                if resp.status_code == 200:
                    await message.reply(
                        "✅ Чек получен и отправлен администратору на проверку.\n"
                        "Как только оплата будет подтверждена, мы сообщим вам и откроем Premium."
                    )
                else:
                    logger.error(f"receipt post error: {resp.status_code} {resp.text}")
                    await message.reply("Не удалось отправить чек. Попробуйте ещё раз.")
        except Exception as e:
            logger.error(f"receipt upload error: {e}")
            await message.reply("Не удалось отправить чек. Попробуйте ещё раз.")

    # ---------- Подтверждения для клиента ----------
    async def confirmations_loop(self):
        while True:
            try:
                await self._process_confirmations()
            except Exception as e:
                logger.error(f"confirmations loop error: {e}")
            await asyncio.sleep(45)

    async def _process_confirmations(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/payments/confirmations",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code != 200:
                    return
                payments = resp.json()
        except Exception as e:
            logger.error(f"fetch confirmations error: {e}")
            return

        for p in payments:
            tg_id = p.get("telegram_id")
            if not tg_id:
                continue
            try:
                days = p.get("premium_days", 30)
                end = p.get("subscription_end")
                end_str = ""
                if end:
                    end_str = end[:10]
                text = (
                    "✅ <b>Оплата подтверждена!</b> 🎉\n\n"
                    f"Премиум-подписка и все функции доступны на <b>{days} дней</b>"
                    + (f" (до <b>{end_str}</b>)." if end_str else ".")
                )
                if p.get("receipt_url"):
                    try:
                        await self.bot.send_photo(
                            tg_id,
                            photo=p["receipt_url"].replace(
                                "/uploads/", f"{API_URL}/uploads/"
                            ).replace(
                                "http://localhost:8000", API_URL
                            ),
                            caption=text,
                            parse_mode=ParseMode.HTML,
                        )
                        continue
                    except Exception:
                        pass
                await self.bot.send_message(tg_id, text, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"send confirmation to {tg_id} error: {e}")

    # ---------- Отклонения заявки (сообщение клиенту) ----------
    async def rejections_loop(self):
        while True:
            try:
                await self._process_rejections()
            except Exception as e:
                logger.error(f"rejections loop error: {e}")
            await asyncio.sleep(45)

    async def _process_rejections(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/payments/rejections",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code != 200:
                    return
                payments = resp.json()
        except Exception as e:
            logger.error(f"fetch rejections error: {e}")
            return

        for p in payments:
            tg_id = p.get("telegram_id")
            if not tg_id:
                continue
            try:
                text = (
                    "❌ <b>Заявка на оплату отклонена.</b>\n\n"
                    "К сожалению, мы не смогли подтвердить ваш платёж.\n"
                    "Свяжитесь с администратором @yogaasana_bot, "
                    "если вы уверены в оплате, или попробуйте ещё раз."
                )
                await self.bot.send_message(tg_id, text, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"send rejection to {tg_id} error: {e}")

    # ---------- Показ чеков админу (фото + кнопки) ----------
    async def pending_review_loop(self):
        while True:
            try:
                await self._process_pending_reviews()
            except Exception as e:
                logger.error(f"pending review loop error: {e}")
            await asyncio.sleep(15)

    async def _fetch_receipt_bytes(self, receipt_url):
        if not receipt_url:
            return None, None
        url = receipt_url.replace("/uploads/", f"{API_URL}/uploads/").replace(
            "http://localhost:8000", API_URL
        )
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None, None
            ext = os.path.splitext(receipt_url)[1].lower() or ".jpg"
            return resp.content, ext

    async def _process_pending_reviews(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/payments/pending",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code != 200:
                    return
                payments = resp.json()
        except Exception as e:
            logger.error(f"fetch pending reviews error: {e}")
            return

        for p in payments:
            try:
                src = f"TG {p.get('telegram_id')}" if p.get('telegram_id') else 'приложение'
                caption = (
                    f"🧾 <b>Чек на оплату #{p.get('id')}</b>\n"
                    f"Пользователь: {p.get('user_name') or '-'} ({src})\n"
                    f"Метод: {p.get('payment_method') or '-'}\n"
                    f"Сумма: {p.get('amount') or '-'}"
                )
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="✅ Подтвердить",
                            callback_data=f"pay_review_confirm_{p['id']}",
                        ),
                        types.InlineKeyboardButton(
                            text="❌ Отклонить",
                            callback_data=f"pay_review_reject_{p['id']}",
                        ),
                    ]
                ])
                data, ext = await self._fetch_receipt_bytes(p.get("receipt_url"))
                if data:
                    mime = "image/png" if ext == ".png" else "image/jpeg"
                    file = BufferedInputFile(data, filename=f"receipt_{p['id']}{ext}")
                    await self.bot.send_photo(
                        ADMIN_TELEGRAM_ID,
                        photo=file,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb,
                    )
                else:
                    await self.bot.send_message(
                        ADMIN_TELEGRAM_ID,
                        caption + "\n\n(чек не удалось загрузить — см. в приложении)",
                        parse_mode=ParseMode.HTML,
                    )
            except Exception as e:
                logger.error(f"send pending review #{p.get('id')} error: {e}")

    async def review_callback(self, callback_query: types.CallbackQuery):
        try:
            _, _, action, payment_id = callback_query.data.split("_", 3)
            payment_id = int(payment_id)
        except Exception:
            await self.bot.answer_callback_query(callback_query.id, text="Ошибка заявки")
            return

        status = "confirmed" if action == "confirm" else "rejected"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/payments/{payment_id}/review",
                    headers=self._headers(),
                    json={"status": status, "premium_days": 30},
                    timeout=15,
                )
        except Exception as e:
            logger.error(f"review callback error: {e}")
            await self.bot.answer_callback_query(callback_query.id, text="Ошибка сети")
            return

        if resp.status_code != 200:
            await self.bot.answer_callback_query(
                callback_query.id, text=f"Ошибка: {resp.status_code}"
            )
            return

        data = resp.json()
        if self.subscription_service is not None:
            self.subscription_service.clear_api_cache()
        await self.bot.answer_callback_query(
            callback_query.id,
            text="Подтверждено ✅" if status == "confirmed" else "Отклонено ❌",
        )
        try:
            await self.bot.edit_message_caption(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                caption=(
                    f"📌 Заявка #{payment_id} "
                    f"{'подтверждена, Premium выдан' if status == 'confirmed' else 'отклонена'}"
                ),
            )
        except Exception:
            pass
