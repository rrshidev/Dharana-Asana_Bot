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

_ADM_HELP = (
    "🔐 <b>Команды администратора</b>\n\n"
    "Формат: <code>Имя</code>\n\n"
    "/adm_hlp - этот список\n"
    "/adm_stats - сводная статистика (юзеры, практики, конверсия)\n"
    "/adm_users - последние пользователи\n"
    "/adm_search &lt;запрос&gt; - поиск пользователей\n"
    "/adm_make &lt;telegram_id|@username&gt; - выдать админку\n"
    "/adm_unmake &lt;telegram_id|@username&gt; - снять админку\n"
    "/adm_premium &lt;telegram_id|@username&gt; [дней] - выдать премиум (по умолч. 30)\n"
    "/adm_unpremium &lt;telegram_id|@username&gt; - снять премиум\n"
    "/adm_broadcast &lt;текст&gt; - рассылка (аудитория + каналы на выбор)\n"
    "/adm_btest &lt;текст&gt; - тестовая рассылка только админу\n"
    "/adm_addvideo &lt;free|premium&gt; &lt;название&gt; - добавить видео готового комплекса\n\n"
    "Пример: <code>/adm_make 123456789</code>, <code>/adm_premium @username 30</code>, "
    "<code>/adm_addvideo free Утренний комплекс</code>"
)


class AdminHandlers:
    """Обработчики админ-команд бота (только для админов)"""

    def __init__(self, bot, subscription_service=None):
        self.bot = bot
        self.subscription_service = subscription_service

    def _headers(self):
        return {"X-Bot-Key": BOT_ADMIN_KEY}

    async def _check_admin(self, telegram_id: int) -> bool:
        if not BOT_ADMIN_KEY:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/is-admin",
                    json={"telegram_id": telegram_id},
                    headers=self._headers(),
                    timeout=10,
                )
                if resp.status_code == 200:
                    return bool(resp.json().get("is_admin"))
        except Exception as e:
            logger.error(f"Error checking admin: {e}")
        return False

    async def _deny(self, message: types.Message):
        await message.reply(
            "⛔ Эта команда доступна только администраторам."
        )

    async def adm_hlp(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        await message.reply(_ADM_HELP, parse_mode=ParseMode.HTML)

    async def adm_stats(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/stats",
                    headers=self._headers(),
                    timeout=10,
                )
                if resp.status_code != 200:
                    return await message.reply(
                        f"Ошибка API ({resp.status_code}). Проверьте BOT_ADMIN_KEY."
                    )
                s = resp.json()
        except Exception as e:
            logger.error(f"adm_stats error: {e}")
            return await message.reply("Не удалось получить статистику. Внутренняя ошибка.")

        text = (
            "📊 <b>Статистика Dharana</b>\n\n"
            f"👥 Всего пользователей: <b>{s.get('total_users', 0)}</b>\n"
            f"⭐ Премиум: <b>{s.get('premium_users', 0)}</b> "
            f"({s.get('conversion_rate', 0)}%)\n"
            f"🟢 Новых за неделю: <b>{s.get('new_users_week', 0)}</b>\n"
            f"🟢 Новых за месяц: <b>{s.get('new_users_month', 0)}</b>\n\n"
            f"🧘 Всего практик: <b>{s.get('total_sessions', 0)}</b>\n"
            f"⏱ Практик за неделю: <b>{s.get('sessions_week', 0)}</b>\n"
            f"⏱ Практик за месяц: <b>{s.get('sessions_month', 0)}</b>\n"
            f"🕐 Минут практики: <b>{s.get('total_practice_minutes', 0)}</b>\n"
        )
        await message.reply(text, parse_mode=ParseMode.HTML)

    async def adm_users(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        await self._search(message, None)

    async def adm_search(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        text = (message.text or "").strip()
        parts = text.split(" ", 1)
        query = parts[1].strip() if len(parts) > 1 else None
        await self._search(message, query)

    async def _search(self, message: types.Message, query: str | None):
        try:
            params = {"limit": 10}
            if query:
                params["search"] = query
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/users",
                    params=params,
                    headers=self._headers(),
                    timeout=10,
                )
                if resp.status_code != 200:
                    return await message.reply(
                        f"Ошибка API ({resp.status_code})."
                    )
                data = resp.json()
                items = data.get("items", [])
        except Exception as e:
            logger.error(f"adm_users error: {e}")
            return await message.reply("Не удалось получить пользователей. Внутренняя ошибка.")

        if not items:
            return await message.reply("Никто не найден 🤷")

        lines = [f"Найдено: <b>{data.get('total', 0)}</b>"]
        for u in items[:10]:
            admin_badge = "👑 " if u.get("is_admin") else ""
            premium_badge = "⭐ " if u.get("is_premium") else ""
            name = u.get("name") or "—"
            ident = u.get("telegram_id")
            ident_txt = f" | id: <code>{ident}</code>" if ident else ""
            lines.append(
                f"{admin_badge}{premium_badge}<b>{name}</b>{ident_txt}\n"
                f"   🕐 {u.get('total_practice_minutes', 0)} мин · "
                f"регистрация {str(u.get('created_at'))[:10] if u.get('created_at') else '?'}"
            )
        await message.reply("\n".join(lines), parse_mode=ParseMode.HTML)

    async def _resolve_target(self, query: str) -> tuple[str | None, int | None, str]:
        """Возвращает (name, user_id, detail) для целевого пользователя."""
        query = query.strip()
        if not query:
            return None, None, "Укажите telegram_id или @username"

        # Если это число - telegram_id
        if query.isdigit():
            target_telegram_id = int(query)
            return None, None, ""  # handled by set-admin via telegram_id

        # Если @username или текст - ищем через API
        search = query[1:] if query.startswith("@") else query
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/users",
                    params={"search": search, "limit": 5},
                    headers=self._headers(),
                    timeout=10,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if len(items) == 1:
                        u = items[0]
                        return u.get("name"), u.get("id"), ""
                    elif len(items) > 1:
                        matches = "\n".join(
                            f"#{i + 1} {u.get('name')} | tg: {u.get('telegram_id')}"
                            for i, u in enumerate(items[:5])
                        )
                        return None, None, "Найдено несколько пользователей:\n" + matches
                    else:
                        return None, None, "Пользователь не найден."
        except Exception as e:
            logger.error(f"resolve target error: {e}")
            return None, None, "Ошибка поиска."
        return None, None, "Пользователь не найден."

    async def adm_make(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        await self._set_admin(message, True)

    async def adm_unmake(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        await self._set_admin(message, False)

    async def _set_admin(self, message: types.Message, make_admin: bool):
        text = (message.text or "").strip()
        parts = text.split(" ", 1)
        query = parts[1].strip() if len(parts) > 1 else ""

        if not query:
            verb = "выдать" if make_admin else "снять"
            return await message.reply(f"Укажите, кому {verb} админку. Пример: <code>{parts[0]} @username</code>",
                                       parse_mode=ParseMode.HTML)

        payload = {}
        if query.isdigit():
            payload["telegram_id"] = int(query)
        else:
            name, user_id, detail = await self._resolve_target(query)
            if user_id is None:
                return await message.reply(detail or "Пользователь не найден.")
            payload["user_id"] = user_id

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/set-admin",
                    json={**payload, "is_admin": make_admin},
                    headers=self._headers(),
                    timeout=10,
                )
                if resp.status_code == 404:
                    return await message.reply("Пользователь не найден.")
                if resp.status_code != 200:
                    return await message.reply(f"Ошибка API ({resp.status_code}).")
                data = resp.json()
        except Exception as e:
            logger.error(f"set_admin error: {e}")
            return await message.reply("Не удалось выполнить операцию. Внутренняя ошибка.")

        status = "выдана 👑" if data.get("is_admin") else "снята"
        changed = " Обновлено." if data.get("changed") else " (уже так)."
        await message.reply(f"Админка {status} для user_id {data.get('user_id')}.{changed}")

    async def adm_premium(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        await self._set_premium(message, True)

    async def adm_unpremium(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        await self._set_premium(message, False)

    async def _set_premium(self, message: types.Message, grant: bool):
        text = (message.text or "").strip()
        parts = text.split(" ", 2)
        query = parts[1].strip() if len(parts) > 1 else ""
        days_arg = parts[2].strip() if len(parts) > 2 else ""

        if not query:
            verb = "выдать премиум" if grant else "снять премиум"
            return await message.reply(
                f"Укажите, кому {verb}. Пример: <code>{parts[0]} @username 30</code>",
                parse_mode=ParseMode.HTML,
            )

        payload = {}
        if query.isdigit():
            payload["telegram_id"] = int(query)
        else:
            _, user_id, detail = await self._resolve_target(query)
            if user_id is None:
                return await message.reply(detail or "Пользователь не найден.")
            payload["user_id"] = user_id

        if grant:
            days = None
            if days_arg.isdigit():
                days = int(days_arg)
            payload["days"] = days

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/set-premium",
                    json={**payload, "is_premium": grant},
                    headers=self._headers(),
                    timeout=10,
                )
                if resp.status_code == 404:
                    return await message.reply("Пользователь не найден.")
                if resp.status_code != 200:
                    return await message.reply(f"Ошибка API ({resp.status_code}).")
                data = resp.json()
        except Exception as e:
            logger.error(f"set_premium error: {e}")
            return await message.reply("Не удалось выполнить операцию. Внутренняя ошибка.")

        if grant:
            end = str(data.get("subscription_end"))[:10]
            await message.reply(
                f"Премиум выдан 🎉 для user_id {data.get('user_id')} "
                f"на {data.get('days')} дн. (до {end})."
            )
        else:
            await message.reply(f"Премиум снят для user_id {data.get('user_id')}.")

    # ---------- Broadcast (рассылки) ----------
    _bc_state = {}

    async def adm_broadcast(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        text = (message.text or "").strip()
        parts = text.split(" ", 1)
        msg_text = parts[1].strip() if len(parts) > 1 else ""
        if not msg_text:
            return await message.reply(
                "📣 <b>Рассылка</b>\n\nУкажите текст сообщения.\n"
                "Формат: <code>/adm_broadcast Текст сообщения</code>",
                parse_mode=ParseMode.HTML,
            )
        self._bc_state[message.from_user.id] = {
            "message": msg_text,
            "audience": None,
            "channels": None,
        }
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Бесплатные", callback_data="bc_aud_free"),
                types.InlineKeyboardButton(text="Премиум", callback_data="bc_aud_premium"),
                types.InlineKeyboardButton(text="Все", callback_data="bc_aud_all"),
            ]
        ])
        await message.reply(
            "📣 Кому отправить?\n\n" + f"Текст: <i>{msg_text[:200]}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )

    async def bc_aud_callback(self, callback_query: types.CallbackQuery):
        tg = callback_query.from_user.id
        state = self._bc_state.get(tg)
        if not state:
            await self.bot.answer_callback_query(callback_query.id, text="Сессия рассылки истекла")
            return
        aud = callback_query.data.split("_", 2)[2]
        if aud == "free":
            state["audience"] = ("free", False, True)
        elif aud == "premium":
            state["audience"] = ("premium", True, False)
        else:
            state["audience"] = ("all", True, True)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Telegram", callback_data="bc_chan_tg"),
                types.InlineKeyboardButton(text="Приложение", callback_data="bc_chan_app"),
                types.InlineKeyboardButton(text="Оба", callback_data="bc_chan_both"),
            ]
        ])
        await self.bot.answer_callback_query(callback_query.id)
        try:
            await self.bot.edit_message_text(
                chat_id=tg,
                message_id=callback_query.message.message_id,
                text="📣 Куда отправить? (оба = продублировать в каждом канале)",
                reply_markup=kb,
            )
        except Exception:
            await self.bot.send_message(tg, "📣 Куда отправить?", reply_markup=kb)

    async def bc_chan_callback(self, callback_query: types.CallbackQuery):
        tg = callback_query.from_user.id
        state = self._bc_state.get(tg)
        if not state or not state["audience"]:
            await self.bot.answer_callback_query(callback_query.id, text="Сессия рассылки истекла")
            return
        ch = callback_query.data.split("_", 2)[2]
        if ch == "tg":
            state["channels"] = (True, False)
        elif ch == "app":
            state["channels"] = (False, True)
        else:
            state["channels"] = (True, True)
        aud_label = {"free": "Бесплатные", "premium": "Премиум", "all": "Все"}[state["audience"][0]]
        pair = (str(state["channels"][0]), str(state["channels"][1]))
        ch_label = {"TrueFalse": "Telegram", "FalseTrue": "Приложение", "TrueTrue": "Оба канала"}[pair[0] + pair[1]]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Разослать", callback_data="bc_send"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="bc_abort"),
            ]
        ])
        await self.bot.answer_callback_query(callback_query.id)
        try:
            await self.bot.edit_message_text(
                chat_id=tg,
                message_id=callback_query.message.message_id,
                text=(
                    "📣 <b>Подтверждение рассылки</b>\n\n"
                    "Текст: <i>" + state["message"][:200] + "</i>\n"
                    "Аудитория: <b>" + aud_label + "</b>\n"
                    "Каналы: <b>" + ch_label + "</b>\n\n"
                    "Отправить?"
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        except Exception:
            await self.bot.send_message(tg, "Отправить рассылку?", reply_markup=kb)

    async def bc_send_callback(self, callback_query: types.CallbackQuery):
        tg = callback_query.from_user.id
        state = self._bc_state.pop(tg, None)
        if not state or state["channels"] is None:
            await self.bot.answer_callback_query(callback_query.id, text="Сессия истекла")
            return
        premium = state["audience"][1]
        free = state["audience"][2]
        ch_tg, ch_app = state["channels"]
        try:
            payload = {
                "message": state["message"],
                "audience": {"free": free, "premium": premium},
                "channels": {"telegram": ch_tg, "app": ch_app},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/broadcast",
                    json=payload, headers=self._headers(), timeout=15,
                )
            if resp.status_code != 200:
                await self.bot.answer_callback_query(callback_query.id, text="Ошибка API")
                return await self.bot.send_message(
                    tg, "Ошибка создания рассылки (" + str(resp.status_code) + ").")
            data = resp.json()
        except Exception as e:
            logger.error("bc_send error: %s", e)
            await self.bot.answer_callback_query(callback_query.id, text="Сетевая ошибка")
            return
        await self.bot.answer_callback_query(callback_query.id, text="Отправлено ✅")
        await self.bot.send_message(
            tg,
            "✅ <b>Рассылка создана</b>\n"
            "Telegram: <b>" + str(data.get("count_telegram", 0)) + "</b> | "
            "Приложение: <b>" + str(data.get("count_app", 0)) + "</b>",
            parse_mode=ParseMode.HTML,
        )

    async def bc_abort_callback(self, callback_query: types.CallbackQuery):
        tg = callback_query.from_user.id
        self._bc_state.pop(tg, None)
        await self.bot.answer_callback_query(callback_query.id, text="Отменено")
        try:
            await self.bot.edit_message_text(
                chat_id=tg, message_id=callback_query.message.message_id, text="Рассылка отменена ❌")
        except Exception:
            pass

    async def adm_btest(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        text = (message.text or "").strip()
        parts = text.split(" ", 1)
        msg_text = parts[1].strip() if len(parts) > 1 else ""
        if not msg_text:
            return await message.reply(
                "🔎 <b>Тест рассылки админу</b>\n\nУкажите текст.\n"
                "Формат: <code>/adm_btest Текст</code>",
                parse_mode=ParseMode.HTML,
            )
        try:
            payload = {
                "message": msg_text,
                "audience": {"free": True, "premium": True},
                "channels": {"telegram": True, "app": True},
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/broadcast/test",
                    json=payload, headers=self._headers(), timeout=15,
                )
            if resp.status_code != 200:
                return await message.reply("Ошибка (" + str(resp.status_code) + "): " + resp.text)
            data = resp.json()
        except Exception as e:
            logger.error("adm_btest error: %s", e)
            return await message.reply("Не удалось отправить тест. Внутренняя ошибка.")
        tg_res = {"sent": "✅", "failed": "❌", "skipped": "⏭️"}.get(data.get("telegram"), str(data.get("telegram")))
        app_res = {"queued": "✅", "no_admin_user": "⚠️ админ не найден"}.get(data.get("app"), str(data.get("app")))
        await message.reply(
            "🧪 <b>Тест рассылки админу</b>\n"
            "Telegram: " + tg_res + "\nПриложение: " + app_res,
            parse_mode=ParseMode.HTML,
        )

    # ---------- Добавление видео готового комплекса ----------
    _video_state = {}

    async def adm_addvideo(self, message: types.Message):
        if not await self._check_admin(message.from_user.id):
            return await self._deny(message)
        text = (message.text or "").strip()
        parts = text.split(" ", 2)
        if len(parts) < 3:
            return await message.reply(
                "🎬 <b>Добавление видео комплекса</b>\n\n"
                "Формат: <code>/adm_addvideo &lt;free|premium&gt; Название комплекса</code>\n\n"
                "Пример: <code>/adm_addvideo free Утренний комплекс</code>\n\n"
                "После этого пришлите видеофайл (mp4, mov, avi, mkv, webm).",
                parse_mode=ParseMode.HTML,
            )
        section = parts[1].strip().lower()
        if section not in ("free", "premium"):
            return await message.reply(
                "Раздел должен быть <code>free</code> или <code>premium</code>.",
                parse_mode=ParseMode.HTML,
            )
        name = parts[2].strip()
        if not name:
            return await message.reply("Укажите название комплекса.")
        self._video_state[message.from_user.id] = {"section": section, "name": name}
        await message.reply(
            f"🎬 Отправьте видеофайл для комплекса <b>{name}</b> "
            f"(раздел: <b>{'Premium' if section == 'premium' else 'Бесплатные'}</b>).\n\n"
            "Поддерживаются: mp4, mov, avi, mkv, webm.",
            parse_mode=ParseMode.HTML,
        )

    async def handle_video_document(self, message: types.Message):
        tg_id = message.from_user.id
        state = self._video_state.get(tg_id)
        if not state:
            return

        # Telegram sends video as either message.document or message.video
        doc = message.document
        vid = message.video
        if not doc and not vid:
            await message.reply("Пришлите файл видео (не текст).")
            return

        if vid:
            file_id = vid.file_id
            file_name = vid.file_name or "video.mp4"
            mime = (vid.mime_type or "").lower()
        else:
            file_id = doc.file_id
            file_name = doc.file_name or "video.mp4"
            mime = (doc.mime_type or "").lower()

        if not (mime.startswith("video/") or file_name.lower().endswith(
                (".mp4", ".mov", ".avi", ".mkv", ".webm"))):
            await message.reply(
                "Это не похоже на видео. Поддерживаются: mp4, mov, avi, mkv, webm.")
            return

        logger.info("video receive from admin %s: name=%s mime=%s", tg_id, file_name, mime)
        reply_msg = await message.reply("⏳ Загружаю видео...")
        try:
            file = await self.bot.get_file(file_id)
            downloaded = await self.bot.download_file(file.file_path)
            data = downloaded.read() if not isinstance(downloaded, bytes) else downloaded
            logger.info("video downloaded: %d bytes", len(data))
        except Exception as e:
            logger.error("video download error: %s", e, exc_info=True)
            self._video_state.pop(tg_id, None)
            return await reply_msg.edit_text("❌ Не удалось скачать видео из Telegram.")

        try:
            files = {"file": (file_name, data, mime or "video/mp4")}
            form = {"name": state["name"], "section": state["section"]}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/api/v1/admin-bot/sequences/add-video",
                    headers=self._headers(),
                    data=form,
                    files=files,
                    timeout=300,
                )
            logger.info("video upload response: %d %s", resp.status_code, resp.text[:300])
        except Exception as e:
            logger.error("video upload error: %s", e, exc_info=True)
            self._video_state.pop(tg_id, None)
            return await reply_msg.edit_text("❌ Ошибка загрузки на сервер. Попробуйте позже.")

        self._video_state.pop(tg_id, None)

        if resp.status_code in (200, 201):
            return await reply_msg.edit_text(
                "✅ Видео добавлено в раздел "
                f"{'Premium' if state['section'] == 'premium' else 'бесплатные'}:\n"
                f"<b>{state['name']}</b>",
                parse_mode=ParseMode.HTML,
            )
        if resp.status_code == 409:
            return await reply_msg.edit_text(
                f"⚠️ Комплекс <b>{state['name']}</b> уже существует в этом разделе.\n"
                "Повторите команду с другим названием — "
                "<code>/adm_addvideo &lt;free|premium&gt; Новое название</code>",
                parse_mode=ParseMode.HTML,
            )
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            pass
        return await reply_msg.edit_text(
            f"❌ Ошибка ({resp.status_code}). {detail}")

    # ---------- Broadcast loop (доставка Telegram из очереди) ----------
    async def broadcast_loop(self):
        while True:
            try:
                await self._process_broadcast_queue()
            except Exception as e:
                logger.error("broadcast loop error: %s", e)
            await asyncio.sleep(15)

    async def _process_broadcast_queue(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/broadcast/pending",
                    headers=self._headers(), timeout=15,
                )
                if resp.status_code != 200:
                    return
                items = resp.json()
        except Exception as e:
            logger.error("fetch broadcast pending error: %s", e)
            return

        for it in items:
            delivery_id = it.get("delivery_id")
            tg_id = it.get("telegram_id")
            if not tg_id:
                continue
            try:
                text = "📣 " + (it.get("message") or "")
                media_url = it.get("media_url")
                sent = False
                if media_url:
                    try:
                        data, ext = await self._fetch_media_bytes(media_url)
                        if data:
                            filename = f"attachment_{delivery_id}{ext}"
                            await self.bot.send_photo(
                                int(tg_id),
                                photo=BufferedInputFile(data, filename=filename),
                                caption=text,
                            )
                            sent = True
                    except Exception as e:
                        logger.error("bc media send to %s error: %s", tg_id, e)
                if not sent:
                    await self.bot.send_message(int(tg_id), text)
            except Exception as e:
                logger.error("bc send to %s error: %s", tg_id, e)
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{API_URL}/api/v1/admin-bot/broadcast/{delivery_id}/failed",
                            json={"error": str(e)[:300]},
                            headers=self._headers(), timeout=10,
                        )
                except Exception as e2:
                    logger.error("bc report failed %s error: %s", delivery_id, e2)

    async def _fetch_media_bytes(self, media_url):
        """Скачать вложение (bytes + расширение) с API по внутреннему адресу."""
        if not media_url:
            return None, None
        url = media_url.replace("/uploads/", f"{API_URL}/uploads/").replace(
            "http://localhost:8000", API_URL
        )
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None, None
            ext = os.path.splitext(media_url)[1].lower() or ".jpg"
            return resp.content, ext
