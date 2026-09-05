import logging
import os
import httpx
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import Command

from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://dharana-api:8000")


class CommandHandlers:
    """Обработчики команд бота"""
    
    def __init__(self, bot):
        self.bot = bot
        self.keyboard_service = KeyboardService()
    
    async def start_command(self, message: types.Message):
        """Обработчик команды /start"""
        text = message.text or ""
        payload = text.split(" ", 1)[1] if " " in text else ""
        telegram_id = message.from_user.id
        name = message.from_user.first_name or ""
        username = message.from_user.username or ""
        display_name = name or username or ""

        # Always register/sync user in DB
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_URL}/api/v1/auth/telegram/create-code",
                    json={
                        "telegram_id": telegram_id,
                        "name": name,
                        "username": username,
                    },
                    timeout=10,
                )
        except Exception as e:
            logger.error(f"Error registering user: {e}")

        if payload == "auth":
            # Show the code for app login
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{API_URL}/api/v1/auth/telegram/create-code",
                        json={
                            "telegram_id": telegram_id,
                            "name": name,
                            "username": username,
                        },
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        code = resp.json()["code"]
                        await message.reply(
                            f"🔐 Код для входа в приложение Dharana:\n\n"
                            f"`{code}`\n\n"
                            f"Введите этот код в приложении для завершения регистрации.",
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        return
                    else:
                        logger.error(f"Failed to create telegram code: {resp.text}")
            except Exception as e:
                logger.error(f"Error creating telegram code: {e}")

            await message.reply(
                "Произошла ошибка. Попробуйте позже.",
            )
            return

        greeting = f"Намаскар, {display_name}! 🙏" if display_name else "Намаскар! 🙏"

        welcome_text = (
            f"{greeting}\n\n"
            "Добро пожаловать в **Dharana** — твой гид по йоге! 🧘\n\n"
            "Здесь ты найдёшь:\n"
            "• **Каталог** — 100+ асан с фото и подробным описанием\n"
            "• **Готовые комплексы** и **генератор практики** под твои цели\n"
            "• **Многофункциональный таймер** для медитаций и практики асан\n"
            "• **Асану дня** — чтобы оставаться в тонусе каждый день\n\n"
            "Выбери действие ниже и начнём практику!"
        )

        await message.reply(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard_service.create_start_menu(),
        )
    
    async def help_command(self, message: types.Message):
        """Обработчик команды /help"""
        help_text = (
            'Напиши название асаны и получишь её описание и фото\n\n'
            'Если не знаешь названий асан, воспользуйся удобным Каталогом асан, '
            'где все позы классифицированы по разделам. Жми на кнопку с названием '
            'и получишь полное описание и отстройку асаны. А также качественное фото с ней!\n'
            'Очисти свою карму, выполнив Асану дня!🧘🤸‍♂️🙏\n\n'
            '🕐 **НОВЫЙ: ИНТЕГРИРОВАННЫЙ ТАЙМЕР** 🕐\n\n'
            'Используй встроенный таймер для структурированной практики:\n'
            '🧘 Медитация - 1-60 минут\n'
            '🧘‍♂️ Асана - настраиваемые циклы работы/отдыха\n'
            '🌬️ Пранаяма - индивидуальное время для упражнений\n\n'
            'Список команд бота:\n\n'
            '----> /start 🚀 - Активация YogaBot\n'
            '----> /help - Помощь и информация о функциях ❓❗️\n'
            '----> /what - Что умеет бот 🤖\n'
            '----> /info - Подробная информация об асанах и таймере ❓❗️\n'
            '----> /about\\_us - об авторах и реализаторах проекта\n'
            '----> /pay 💳 - оплата Premium подписки (реквизиты + чек)'
        )
        await message.reply(help_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self.keyboard_service.create_main_menu())
    
    async def what_command(self, message: types.Message):
        """Обработчик команды /what"""
        what_text = (
            '✅Бот содержит более 100 асан йоги.\n\n'
            'Для их поиска перейди в раздел «!Каталог асан!», выбери интересующий, '
            'в котором асаны удобно классифицированы, найди в нем нужную из предложенных '
            'и нажми соответсвующую кнопку🟢\n'
            'Если знаешь название асаны, то введи его на русском языке, '
            'например: Бакасана или Адхо мукха шванасана!⌨️\n\n'
            '✅Бот содержит все основные базовые понятия йоги в разделах '
            '«Основы йоги» и «8 ступеней йоги». Выбери интересующий раздел, '
            'найди в нем нужную тему, нажми соответствующую кнопку 🟢 и получи его описание.\n\n'
            '🕐 **НОВЫЙ ТАЙМЕР ДЛЯ ПРАКТИКИ** 🕐\n\n'
            'Бот теперь включает многофункциональный таймер для йогических практик:\n\n'
            '🧘 **Медитация** - таймер для медитативных практик с выбором времени от 1 до 60 минут\n'
            '🧘‍♂️ **Асана** - таймер для практики асан с настраиваемыми циклами работы и отдыха\n'
            '🌬️ **Пранаяма** - таймер для дыхательных упражнений с индивидуальным временем для каждого упражнения\n\n'
            'Все таймеры имеют удобное управление (пауза, стоп, сброс) и автоматическое обновление прогресса!'
        )
        await message.reply(what_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self.keyboard_service.create_main_menu())
    
    async def info_command(self, message: types.Message):
        """Обработчик команды /info"""
        info_text = (
            'Асана - статичная поза, разработанная древними мудрецами таким образом, '
            'чтобы оказвать определённое воздествие на разум.\n'
            'Посредством растягивания-сжимания, скручивания физического тела, '
            'и используя метод диафрагмального дыхания во время упражнений, '
            'происходит благоприятное воздействие на эндокринную систему желез '
            'внутренней секреции человека. Что положительным образом сказывается '
            'на состоянии психики. И ментального здоровья человека в целом.\n'
            'Далее оздоровлённая психика и подготовленное тело служат инструментом '
            'для познания главного объекта в медитации.\n'
            'Духа. Высшего сознания. Истины. Бога. Творца.\n\n'
            'Таким образом, асана - не является самостоятельной дисциплиной или отдельной йогой. '
            'Асана является подготовительной практикой, призванной подготовить разум и тело к медитации.\n\n'
            '🕐 **ИНТЕГРИРОВАННЫЙ ТАЙМЕР ДЛЯ ПРАКТИКИ** 🕐\n\n'
            'YogaBot теперь включает встроенный таймер для структурированной практики:\n\n'
            '🧘 **Медитация**: Фокусированная медитативная практика с таймером от 1 до 60 минут\n'
            '🧘‍♂️ **Асана**: Практика поз с настраиваемыми циклами работы и отдыха (30с-3м работа, 10с-1м отдых, 3-20 циклов)\n'
            '🌬️ **Пранаяма**: Дыхательные упражнения с индивидуальной настройкой (1-8 упражнений, 10с-2м каждое, 5с-1м отдых)\n\n'
            'Особенности таймера:\n'
            '• Автоматическое обновление прогресса каждые 5 секунд\n'
            '• Уведомления о смене фаз (работа/отдых)\n'
            '• Полное управление (пауза, продолжить, стоп, сброс, удаление)\n'
            '• Визуальный прогресс-бар и счетчик циклов\n'
            '• Корректный подсчет циклов (увеличение после отдыха)\n\n'
            'Бот носит информативный характер. Не выполняйте асаны самостоятельно, '
            'если имеете хронические заболевания, психические отклонения. '
            'Рекомеднуется осваивать этот раздел йоги с опытным наставником. '
            'Обязательно выполняйте разминку перед началом практики.'
        )
        await message.reply(info_text, parse_mode=ParseMode.MARKDOWN, reply_markup=self.keyboard_service.create_main_menu())
    
    async def about_us_command(self, message: types.Message):
        """Обработчик команды /about_us"""
        about_text = (
            'Арунодая - старший программист(кодревью, рефакторинг, кодинг, мудрые советы). Йогин! --> @Arun0daya\n\n'
            'Олег - автор проекта online-школы йоги Dharana.ru, частью которого является этот бот'
            '(Фото, описание, идеи, маркетинг). Йогин!--> @yogaolleg\n'
            'www.instagram.com/yogaolleg/\n\n'
            'Ришидэв - автор бота, идейный вдохновитель проекта online-школы йоги Dharana.ru. '
            'Младший программист(кодинг, асаны). Йогин! --> @RrshiDev'
        )
        await message.reply(about_text, reply_markup=self.keyboard_service.create_main_menu())
