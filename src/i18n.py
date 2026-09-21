# -*- coding: utf-8 -*-
"""Централизованная локализация бота (ru/en).

Все строки UI сосредоточены здесь. t(lang, key, **kw) возвращает перевод;
`ru` — исходный (и полный) набор строк, `en` — перевод.
"""

LANGUAGES = ('ru', 'en')


def normalize_lang(lang) -> str:
    """Приводит значение к 'ru'|'en' (все не-'en' считаются 'ru')."""
    if lang and str(lang).lower().startswith('en'):
        return 'en'
    return 'ru'


def lang_from_telegram(language_code) -> str:
    """Язык по умолчанию из Telegram language_code (например 'en'/'en-US')."""
    if not language_code:
        return 'ru'
    code = str(language_code).lower()
    if code.startswith('en'):
        return 'en'
    return 'ru'


def t(lang, key: str, **kwargs) -> str:
    """Перевод строки. Неизвестные ключи -> 'ru' -> сам ключ."""
    lang = normalize_lang(lang)
    text = TRANSLATIONS.get(lang, {}).get(key)
    if text is None:
        text = TRANSLATIONS['ru'].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def format_duration(lang, seconds: int) -> str:
    """'60с'/'1м' для RU, '60s'/'1m' для EN."""
    if seconds < 60:
        return f"{seconds}{t(lang, 'sec_unit')}"
    return f"{seconds // 60}{t(lang, 'min_unit')}"


def format_mm_ss(lang, seconds: int) -> str:
    """'01:30' — универсальный формат времени."""
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


def format_progress(lang, elapsed: int, total: int) -> str:
    """'18м 30с / 20м 0с' (RU) или '18m 30s / 20m 0s' (EN)."""
    mu = t(lang, 'min_unit')
    su = t(lang, 'sec_unit')

    def _part(sec):
        m = sec // 60
        s = sec % 60
        return f"{m}{mu} {s}{su}"

    return f"{_part(elapsed)} / {_part(total)}"


def t_minutes(lang, n: int) -> str:
    """'1 минута'/'5 минут' или '1 minute'/'5 minutes'."""
    if n == 1:
        return f"{n} {t(lang, 'minute_one')}"
    return f"{n} {t(lang, 'minutes_many')}"


def t_exercises(lang, n: int) -> str:
    """'1 упражнение'/'3 упражнения'/'5 упражнений' или '1 exercise'/'2 exercises'."""
    lang = normalize_lang(lang)
    if lang == 'en':
        return f"{n} exercise" if n == 1 else f"{n} exercises"
    if n == 1:
        return f"{n} упражнение"
    if n in (2, 3, 4):
        return f"{n} упражнения"
    return f"{n} упражнений"


TRANSLATIONS = {
    'ru': {
        # --- Кнопки ---
        'btn_home': '🏠 Главное меню',
        'btn_timer': '🕐 Таймер',
        'btn_random_asana': '🎲 Случайная асана',
        'btn_premium': '💎 Премиум-подписка',
        'btn_catalog': '📚 Каталог асан',
        'btn_ready_sequences': '🎬 Готовые комплексы',
        'btn_basics': '🧘 Основы йоги',
        'btn_steps': '📈 8 ступеней йоги',
        'btn_daily_asana': '🌅 Асана дня',
        'btn_generator': '🏋️‍♂️ Генератор практики',
        'btn_filters': '🔍 Фильтры асан',
        'btn_start_screen': '🏠 На главный экран',
        'btn_about': 'ℹ️ О боте',
        'btn_back': '🔙 Назад',
        'btn_back_catalog': '🔙 Назад в каталог',
        'btn_back_filters': '🔙 Назад к фильтрам',
        'btn_back_main': '🔙 В главное меню',
        'btn_language': '🌐 Язык',
        'lang_ru': '🇷🇺 Русский',
        'lang_en': '🇬🇧 English',

        # --- Экран и меню ---
        'start_screen_title': "🏠 **Главный экран**\n\nБыстрые действия — в один клик:",
        'main_menu_title': "🧘‍♂️ **Каталог и разделы**\n\nЗдесь всё, что поможет в практике. Выбери раздел:",
        'lang_menu_title': '🌐 Выбери язык бота:',
        'lang_changed': 'Язык: {lang}',

        # --- Каталог ---
        'categories_title': 'Разделы асан:',
        'category_intro': '{desc} приведен ниже.\n'
                          'Нажми кнопку с искомой асаной\n'
                          'Получишь её фото и описание!',
        'back_to_catalog_prompt': '🔙 Вернуться к выбору раздела:',
        'category_not_found': 'Категория не найдена',
        'asana_not_found': 'Асана не найдена',
        'asana_load_error': 'Не удалось загрузить асану',
        'asana_error': 'Ошибка при загрузке асаны: {err}',
        'yoga_pose': 'Йогическая поза: {name}',
        'catalog_outro': 'Каталог',
        'choose_section': 'Выберите раздел:',

        # --- Основы и ступени ---
        'basics_menu_title': 'Основные понятия и термины йоги:',
        'basics_not_found': 'Основы не найдены',
        'basic_not_found': 'Содержимое не найдено для: {name}',
        'basics_section_title': 'Раздел йоги:',
        'steps_menu_title': '8 ступеней йоги:',
        'step_not_found': 'Ступень не найдена',
        'step_content_not_found': 'Содержимое не найдено для: {name}',
        'step_section_title': 'Ступень йоги:',

        # --- Карточка асаны / премиум ---
        'video_available': '🎥 **Видео-инструкция доступна**',
        'video_premium_only': '🎥 **Видео-инструкция доступна в премиум-версии**',
        'premium_offer': (
            "🎯 **Хотите видео-инструкцию?**\n\n"
            "В премиум-версии вы получите:\n"
            "• 🎥 Детальные видео для 50+ асан\n"
            "• 📊 Анализ техники и исправление ошибок\n"
            "• 🎵 Аудио-сопровождение практик\n"
            "• 🔄 Безлимитные генерации комплексов\n\n"
            "Попробуйте 7 дней бесплатно!"
        ),
        'btn_trial': '🚀 7 дней бесплатно',
        'btn_plans': '💳 Узнать о тарифах',

        # --- Поиск ---
        'not_found_prompt': 'Проверь название или воспользуйся каталогом асан!',

        # --- О боте ---
        'about_text': (
            '🧘‍♂️ Йога Асана Бот\n\n'
            'Этот бот поможет тебе изучить асаны йоги, их описание и правильное выполнение.\n\n'
            'Доступные разделы:\n'
            '📚 Каталог асан - полный список поз с фотографиями\n'
            '🧘 Основы йоги - базовые понятия и термины\n'
            '📈 Ступени йоги - 8 уровней практики\n'
            '🎲 Случайная асана - случайная поза для практики\n'
            '🔍 Фильтры асан - подбор по сложности и эффектам\n'
            '🕐 Таймер - многофункциональный таймер для практики:\n'
            '   • 🧘 Медитация - 1-60 минут\n'
            '   • 🧘‍♂️ Асана - настраиваемые циклы работы/отдыха\n'
            '   • 🌬️ Пранаяма - индивидуальное время упражнений\n\n'
            'Создан с любовью к йоге 🙏'
        ),

        # --- Команды ---
        'auth_code_text': (
            "🔐 Код для входа в приложение Dharana:\n\n"
            "`{code}`\n\n"
            "Введите этот код в приложении для завершения регистрации."
        ),
        'auth_error': 'Произошла ошибка. Попробуйте позже.',
        'start_greeting': 'Намаскар! 🙏',
        'start_greeting_named': 'Намаскар, {name}! 🙏',
        'start_welcome': (
            "Добро пожаловать в **Dharana** — твой гид по йоге! 🧘\n\n"
            "Здесь ты найдёшь:\n"
            "• **Каталог** — 100+ асан с фото и подробным описанием\n"
            "• **Готовые комплексы** и **генератор практики** под твои цели\n"
            "• **Многофункциональный таймер** для медитаций и практики асан\n"
            "• **Асану дня** — чтобы оставаться в тонусе каждый день\n\n"
            "Выбери действие ниже и начнём практику!"
        ),
        'help_text': (
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
        ),
        'what_text': (
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
        ),
        'info_text': (
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
        ),
        'about_us_text': (
            "🙏 **О проекте и его авторах**\n\n"
            "Меня зовут **Руслан** — я автор и разработчик бота Dharana. "
            "Проект родился из давней любви к йоге и желания сделать практику "
            "доступной каждому: я занимаюсь разработкой, администрированием серверов "
            "и всем, что помогает боту расти.\n\n"
            "Немного о пути: раньше я практиковал и преподавал йогу, а в некоторых "
            "публичных медиа с асанами бота — мои фотографии. То есть этот бот делали "
            "люди, для которых йога — не просто слова.\n\n"
            "**Олег** — мой друг и партнёр, йогин. Он создаёт медиа-контент: сейчас "
            "готовит видео с асанами и готовыми комплексами, а дальше займётся "
            "развитием, рекламой и продвижением проекта.\n\n"
            "Два человека. Йога. Немного кода. И желание, чтобы ваша практика была "
            "регулярной и приносила радость.\n\n"
            "Хорошей практики! 🙏\n\n"
            "Связаться с нами:\n"
            "@RrshiDev · @yogaolleg\n"
            "instagram.com/yogaolleg/"
        ),

        # --- Категории каталога ---
        'cat_name_sit_lie+': 'Асаны сидя и лёжа',
        'cat_desc_sit_lie+': 'Список асан сидя и лёжа',
        'cat_name_stay+': 'Асаны стоя',
        'cat_desc_stay+': 'Список асан стоя',
        'cat_name_hand+': 'Балансы на руках',
        'cat_desc_hand+': 'Список балансов на руках',
        'cat_name_coup+': 'Перевёрнутые асаны',
        'cat_desc_coup+': 'Список перевернутых асан',
        'cat_name_sag+': 'Прогибы',
        'cat_desc_sag+': 'Список асан с прогибами',
        'cat_name_power+': 'Силовые асаны',
        'cat_desc_power+': 'Список силовых асан',

        # --- Таймер ---
        'timer_main_title': (
            "🕐 **Таймер для практики**\n\n"
            "Выбери тип практики:\n"
            "🧘 Медитация - простая практика осознанности\n"
            "🧘‍♂️ Асана - практика поз с чередованием работы/отдыха\n"
            "🌬️ Пранаяма - дыхательные упражнения"
        ),
        'btn_meditation': '🧘 Медитация',
        'btn_asana': '🧘‍♂️ Асана',
        'btn_pranayama': '🌬️ Пранаяма',
        'btn_timer_exit': '🔙 Выйти из таймера',
        'btn_custom': '⌨️ Ввести время вручную',
        'btn_work_time': '⏱️ Время работы',
        'btn_rest_time': '⏸️ Время отдыха',
        'btn_cycles': '🔄 Количество циклов',
        'btn_start': '▶️ Начать',
        'btn_exercises': '📊 Количество упражнений',
        'btn_exercise_time': '⏱️ Время упражнения',
        'meditation_title': "🧘 **Медитация**\n\nВыбери длительность практики:",
        'meditation_custom_title': (
            "⌨️ **Ввод времени медитации**\n\n"
            "Напиши количество минут (от 1 до 120):\n"
            "Например: 7 или 15 или 45\n\n"
            "Используй обычное сообщение, а не кнопку."
        ),
        'meditation_invalid': '⚠️ Время должно быть от 1 до 120 минут. Попробуй еще раз.',
        'meditation_started': (
            "🧘 Медитация на {minutes} минут начата!\n\n"
            "Сконцентрируйся на дыхании и будь настоящем моменте. 🙏\n\n"
            "Используй кнопки управления ниже:"
        ),
        'meditation_started_notif': (
            "🔔 **Медитация началась!**\n\n"
            "Длительность: {minutes} минут\n"
            "Сосредоточься на дыхании... 🧘"
        ),
        'minutes_many': 'минут',
        'minute_one': 'минута',
        'cycles_count': '{n} циклов',
        'select_work': '⏱️ **Выбери время работы:**',
        'select_rest': '⏸️ **Выбери время отдыха:**',
        'select_cycles': '🔄 **Выбери количество циклов:**',
        'select_exercises': '📊 **Выбери количество упражнений:**',
        'select_exercise_time': '⏱️ **Выбери время упражнения:**',
        'select_rest_time': '⏸️ **Выбери время отдыха:**',
        'asana_timer_title': '🧘‍♂️ **Таймер асан**',
        'asana_timer_title_named': '🧘‍♂️ **Таймер асан: {name}**',
        'asana_config_body': (
            "{title}\n\n"
            "{work}\n"
            "{rest}\n"
            "{cycles}\n\n"
            "Настрой параметры или начни практику:"
        ),
        'work_setting': '⏱️ Работа: {value}',
        'rest_setting': '⏸️ Отдых: {value}',
        'cycles_setting': '🔄 Циклы: {value}',
        'pranayama_title': '🌬️ **Пранаяма**',
        'pranayama_config_body': (
            "{title}\n\n"
            "📊 Упражнений: {exercises}\n"
            "⏱️ Время упражнения: {exercise_time}\n"
            "⏸️ Время отдыха: {rest_time}\n\n"
            "Настрой параметры или начни практику:"
        ),
        'asana_started_title': '🧘‍♂️ **Практика: {name}**',
        'asana_started_generic': '🧘‍♂️ **Практика асан начата!**',
        'asana_started_body': (
            "{title}\n\n"
            "{work}\n"
            "{rest}\n"
            "{cycles}\n\n"
            "Начинаем с первого подхода! 💪"
        ),
        'pranayama_started_title': '🌬️ **Практика пранаямы начата!**',
        'pranayama_started_body': (
            "🌬️ **Практика пранаямы начата!**\n\n"
            "📊 Упражнений: {exercises}\n"
            "⏱️ Время упражнения: {exercise_time}\n"
            "⏸️ Время отдыха: {rest_time}\n\n"
            "Начинаем с первого упражнения! 🧘‍♂️"
        ),
        'btn_pause': '⏸️ Пауза',
        'btn_stop': '⏹️ Стоп',
        'btn_resume': '▶️ Продолжить',
        'btn_reset': '🔄 Сброс',
        'btn_delete': '🗑️ Удалить',
        'btn_timer_start': '▶️ Начать',
        'timer_stopped': (
            "⏹️ **Таймер остановлен**\n\n"
            "Практика завершена. Хорошая работа! 🙏\n\n"
            "Хочешь начать новую практику?"
        ),
        'timer_deleted': "🗑️ Таймер удален\n\nХочешь начать новую практику?",
        'timer_back_text': '🔙 **Возвращаю в главное меню таймера...**',
        'timer_exit_text': '🔙 **Выход из таймера...**',
        'practice_completed_notif': '🎉 **Практика завершена!**\n\nОтличная работа! 🙏',
        'meditation_completed': (
            "🧘 **Медитация завершена!**\n\n"
            "Отличная практика! Надеюсь, ты чувствуешь себя спокойно и гармонично. 🙏\n\n"
            "Хочешь начать новую медитацию?"
        ),
        'meditation_status': (
            "{emoji} **Медитация**\n\n"
            "Осталось времени: {remaining}\n"
            "{bar}\n\n"
            "Прогресс: {progress}"
        ),
        'asana_completed': (
            "{timer_name} **— практика завершена!**\n\n"
            "Отличная работа! Все циклы выполнены. 💪\n\n"
            "Ты молодец! Хочешь начать новую практику?"
        ),
        'asana_status': (
            "{emoji} **{timer_name}**\n\n"
            "Фаза: {phase}\n"
            "Осталось: {remaining}\n"
            "{bar}\n\n"
            "Цикл: {cycle}/{cycles}\n"
            "Общее время: {total}"
        ),
        'phase_work': 'Работа',
        'phase_rest': 'Отдых',
        'work_finish_notif': (
            "🔔 **Время работы завершено!**\n\n"
            "Отдыхай! Восстанови дыхание и подготовься к следующему подходу. 🛏️\n\n"
            "Отдых: {seconds} секунд"
        ),
        'rest_finish_notif': (
            "🔔 **Отдых завершен!**\n\n"
            "Приготовься! Начинаем следующий подход. 💪\n\n"
            "Работа: {seconds} секунд"
        ),
        'sec_unit': 'с',
        'min_unit': 'м',
        'timer_asana_name': '🧘 **Асана**',
        'timer_pranayama_name': '🌬️ **Пранаяма**',
        'cmd_start': 'Запустить бота и открыть меню',
        'cmd_help': 'Помощь и список возможностей',
        'cmd_what': 'Что такое Dharana — о проекте',
        'cmd_info': 'Информация о боте и подписке',
        'cmd_about_us': 'Наша команда',
        'cmd_language': 'Сменить язык бота (Русский / English)',
        'cmd_asana_day': 'Асана дня — получить и настроить',
        'cmd_pay': 'Оформить Premium-подписку',
    },

    'en': {
        # --- Buttons ---
        'btn_home': '🏠 Main menu',
        'btn_timer': '🕐 Timer',
        'btn_random_asana': '🎲 Random asana',
        'btn_premium': '💎 Premium subscription',
        'btn_catalog': '📚 Asana catalog',
        'btn_ready_sequences': '🎬 Ready sequences',
        'btn_basics': '🧘 Yoga basics',
        'btn_steps': '📈 8 limbs of yoga',
        'btn_daily_asana': '🌅 Asana of the day',
        'btn_generator': '🏋️‍♂️ Practice generator',
        'btn_filters': '🔍 Asana filters',
        'btn_start_screen': '🏠 Go to home screen',
        'btn_about': 'ℹ️ About the bot',
        'btn_back': '🔙 Back',
        'btn_back_catalog': '🔙 Back to catalog',
        'btn_back_filters': '🔙 Back to filters',
        'btn_back_main': '🔙 Back to main menu',
        'btn_language': '🌐 Language',
        'lang_ru': '🇷🇺 Русский',
        'lang_en': '🇬🇧 English',

        'start_screen_title': "🏠 **Home screen**\n\nQuick actions — one tap:",
        'main_menu_title': "🧘‍♂️ **Catalog & sections**\n\nEverything to support your practice. Choose a section:",
        'lang_menu_title': '🌐 Choose your language:',
        'lang_changed': 'Language: {lang}',

        'categories_title': 'Asana categories:',
        'category_intro': ('{desc}\n'
                          'Tap the button with the asana you need\n'
                          'and get its photo and description!'),
        'back_to_catalog_prompt': '🔙 Back to category selection:',
        'category_not_found': 'Category not found',
        'asana_not_found': 'Asana not found',
        'asana_load_error': 'Failed to load asana',
        'asana_error': 'Error loading asana: {err}',
        'yoga_pose': 'Yoga pose: {name}',
        'catalog_outro': 'Catalog',
        'choose_section': 'Choose a section:',

        'basics_menu_title': 'Basic yoga concepts and terms:',
        'basics_not_found': 'Basics not found',
        'basic_not_found': 'Content not found for: {name}',
        'basics_section_title': 'Yoga section:',
        'steps_menu_title': '8 limbs of yoga:',
        'step_not_found': 'Step not found',
        'step_content_not_found': 'Content not found for: {name}',
        'step_section_title': 'Yoga step:',

        'video_available': '🎥 **Video instruction available**',
        'video_premium_only': '🎥 **Video instruction available in the premium version**',
        'premium_offer': (
            "🎯 **Want a video instruction?**\n\n"
            "In the premium version you get:\n"
            "• 🎥 Detailed videos for 50+ asanas\n"
            "• 📊 Technique analysis and error correction\n"
            "• 🎵 Audio guidance for practices\n"
            "• 🔄 Unlimited sequence generation\n\n"
            "Try 7 days for free!"
        ),
        'btn_trial': '🚀 7 days free trial',
        'btn_plans': '💳 See plans',

        'not_found_prompt': 'Check the name or use the asana catalog!',

        'about_text': (
            '🧘‍♂️ Yoga Asana Bot\n\n'
            'This bot helps you learn yoga asanas, their descriptions and correct execution.\n\n'
            'Available sections:\n'
            '📚 Asana catalog - full list of poses with photos\n'
            '🧘 Yoga basics - core concepts and terms\n'
            '📈 8 limbs of yoga - 8 levels of practice\n'
            '🎲 Random asana - a random pose for practice\n'
            '🔍 Asana filters - search by difficulty and effects\n'
            '🕐 Timer - a multifunctional timer for practice:\n'
            '   • 🧘 Meditation - 1-60 minutes\n'
            '   • 🧘‍♂️ Asana - configurable work/rest cycles\n'
            '   • 🌬️ Pranayama - individual exercise times\n\n'
            'Made with love for yoga 🙏'
        ),

        'auth_code_text': (
            "🔐 Code to enter the Dharana app:\n\n"
            "`{code}`\n\n"
            "Enter this code in the app to finish registration."
        ),
        'auth_error': 'Something went wrong. Please try again later.',
        'start_greeting': 'Namaskar! 🙏',
        'start_greeting_named': 'Namaskar, {name}! 🙏',
        'start_welcome': (
            "Welcome to **Dharana** — your yoga guide! 🧘\n\n"
            "Here you will find:\n"
            "• **Catalog** — 100+ asanas with photos and detailed descriptions\n"
            "• **Ready sequences** and a **practice generator** for your goals\n"
            "• **Multifunctional timer** for meditation and asana practice\n"
            "• **Asana of the day** — to keep you in shape every day\n\n"
            "Choose an action below and let's start practicing!"
        ),
        'help_text': (
            'Type the name of an asana and get its description and photo\n\n'
            'If you do not know the asana names, use the handy Asana catalog '
            'where all poses are categorized. Tap the button with the name '
            'to get the full description and alignment of the asana, plus a great photo!\n'
            'Clear your karma by doing the Asana of the day!🧘🤸‍♂️🙏\n\n'
            '🕐 **NEW: INTEGRATED TIMER** 🕐\n\n'
            'Use the built-in timer for a structured practice:\n'
            '🧘 Meditation - 1-60 minutes\n'
            '🧘‍♂️ Asana - configurable work/rest cycles\n'
            '🌬️ Pranayama - individual exercise times\n\n'
            'List of bot commands:\n\n'
            '----> /start 🚀 - Activate YogaBot\n'
            '----> /help - Help and info about features ❓❗️\n'
            '----> /what - What the bot can do 🤖\n'
            '----> /info - Detailed info about asanas and the timer ❓❗️\n'
            '----> /about\\_us - about the authors of the project\n'
            '----> /pay 💳 - pay for the Premium subscription (details + receipt)'
        ),
        'what_text': (
            '✅The bot contains more than 100 yoga asanas.\n\n'
            'To find them go to the "Asana catalog" section and choose the one you want; '
            'asanas are nicely categorized. Find the asana you need among the suggestions '
            'and tap the button🟢\n'
            'If you know the asana name, just type it, for example: Bakasana or Adho Mukha Shvanasana!⌨️\n\n'
            '✅The bot contains all the core yoga concepts in the '
            '"Yoga basics" and "8 limbs of yoga" sections. Choose a section, '
            'pick the topic, tap the button 🟢 and get its description.\n\n'
            '🕐 **NEW PRACTICE TIMER** 🕐\n\n'
            'The bot now includes a multifunctional timer for yoga practices:\n\n'
            '🧘 **Meditation** - a timer for meditation with a choice from 1 to 60 minutes\n'
            '🧘‍♂️ **Asana** - an asana practice timer with configurable work and rest cycles\n'
            '🌬️ **Pranayama** - a breathing exercise timer with individual time for each exercise\n\n'
            'All timers have convenient controls (pause, stop, reset) and automatic progress updates!'
        ),
        'info_text': (
            'An asana is a static posture developed by ancient sages in such a way '
            'as to produce a specific effect on the mind.\n'
            'By stretching and compressing, twisting the physical body, '
            'and using diaphragmatic breathing during the exercises, '
            'a beneficial effect occurs on the endocrine gland system '
            'of the human body. This positively affects the psyche '
            'and the mental health of a person in general.\n'
            'A healed psyche and a prepared body then serve as an instrument '
            'for knowing the main object of meditation.\n'
            'Spirit. Higher consciousness. Truth. God. Creator.\n\n'
            'Thus, an asana is not an independent discipline or a separate yoga. '
            'An asana is a preparatory practice designed to prepare the mind and body for meditation.\n\n'
            '🕐 **INTEGRATED PRACTICE TIMER** 🕐\n\n'
            'YogaBot now includes a built-in timer for structured practice:\n\n'
            '🧘 **Meditation**: A focused meditative practice with a timer from 1 to 60 minutes\n'
            '🧘‍♂️ **Asana**: Pose practice with configurable work and rest cycles (30s-3m work, 10s-1m rest, 3-20 cycles)\n'
            '🌬️ **Pranayama**: Breathing exercises with individual settings (1-8 exercises, 10s-2m each, 5s-1m rest)\n\n'
            'Timer features:\n'
            '• Automatic progress updates every 5 seconds\n'
            '• Phase change notifications (work/rest)\n'
            '• Full control (pause, resume, stop, reset, delete)\n'
            '• Visual progress bar and cycle counter\n'
            '• Correct cycle counting (increments after rest)\n\n'
            'The bot is informational. Do not perform asanas on your own '
            'if you have chronic diseases or mental conditions. '
            'It is recommended to learn this part of yoga with an experienced instructor. '
            'Always warm up before practice.'
        ),
        'about_us_text': (
            "🙏 **About the project and its authors**\n\n"
            "My name is **Ruslan** — I am the author and developer of the Dharana bot. "
            "The project was born from a long-standing love of yoga and the wish to make practice "
            "available to everyone: I handle development, server administration "
            "and everything that helps the bot grow.\n\n"
            "A bit about the journey: I used to practice and teach yoga, and in some "
            "public media with the bot's asanas you will find my photos. In other words, "
            "this bot was made by people for whom yoga is not just words.\n\n"
            "**Oleg** — my friend and partner, a yogi. He creates media content: right now "
            "he is preparing videos with asanas and ready sequences, and later he will work on "
            "development, advertising and promotion of the project.\n\n"
            "Two people. Yoga. A bit of code. And the wish that your practice "
            "be regular and joyful.\n\n"
            "Have a great practice! 🙏\n\n"
            "Contact us:\n"
            "@RrshiDev · @yogaolleg\n"
            "instagram.com/yogaolleg/"
        ),

        'cat_name_sit_lie+': 'Seated & lying asanas',
        'cat_desc_sit_lie+': 'A list of seated and lying down asanas',
        'cat_name_stay+': 'Standing asanas',
        'cat_desc_stay+': 'A list of standing asanas',
        'cat_name_hand+': 'Arm balances',
        'cat_desc_hand+': 'A list of arm balancing asanas',
        'cat_name_coup+': 'Inverted asanas',
        'cat_desc_coup+': 'A list of inverted asanas',
        'cat_name_sag+': 'Backbends',
        'cat_desc_sag+': 'A list of backbending asanas',
        'cat_name_power+': 'Strength asanas',
        'cat_desc_power+': 'A list of strength asanas',

        'timer_main_title': (
            "🕐 **Practice timer**\n\n"
            "Choose the type of practice:\n"
            "🧘 Meditation - a simple mindfulness practice\n"
            "🧘‍♂️ Asana - pose practice alternating work/rest\n"
            "🌬️ Pranayama - breathing exercises"
        ),
        'btn_meditation': '🧘 Meditation',
        'btn_asana': '🧘‍♂️ Asana',
        'btn_pranayama': '🌬️ Pranayama',
        'btn_timer_exit': '🔙 Exit timer',
        'btn_custom': '⌨️ Enter time manually',
        'btn_work_time': '⏱️ Work time',
        'btn_rest_time': '⏸️ Rest time',
        'btn_cycles': '🔄 Number of cycles',
        'btn_start': '▶️ Start',
        'btn_exercises': '📊 Number of exercises',
        'btn_exercise_time': '⏱️ Exercise time',
        'meditation_title': "🧘 **Meditation**\n\nChoose the practice duration:",
        'meditation_custom_title': (
            "⌨️ **Meditation time input**\n\n"
            "Type the number of minutes (from 1 to 120):\n"
            "For example: 7 or 15 or 45\n\n"
            "Use a regular message, not a button."
        ),
        'meditation_invalid': '⚠️ Time must be between 1 and 120 minutes. Try again.',
        'meditation_started': (
            "🧘 Meditation for {minutes} minutes started!\n\n"
            "Focus on your breath and stay in the present moment. 🙏\n\n"
            "Use the control buttons below:"
        ),
        'meditation_started_notif': (
            "🔔 **Meditation started!**\n\n"
            "Duration: {minutes} minutes\n"
            "Focus on your breath... 🧘"
        ),
        'minutes_many': 'minutes',
        'minute_one': 'minute',
        'cycles_count': '{n} cycles',
        'select_work': '⏱️ **Choose work time:**',
        'select_rest': '⏸️ **Choose rest time:**',
        'select_cycles': '🔄 **Choose number of cycles:**',
        'select_exercises': '📊 **Choose number of exercises:**',
        'select_exercise_time': '⏱️ **Choose exercise time:**',
        'select_rest_time': '⏸️ **Choose rest time:**',
        'asana_timer_title': '🧘‍♂️ **Asana timer**',
        'asana_timer_title_named': '🧘‍♂️ **Asana timer: {name}**',
        'asana_config_body': (
            "{title}\n\n"
            "{work}\n"
            "{rest}\n"
            "{cycles}\n\n"
            "Configure parameters or start the practice:"
        ),
        'work_setting': '⏱️ Work: {value}',
        'rest_setting': '⏸️ Rest: {value}',
        'cycles_setting': '🔄 Cycles: {value}',
        'pranayama_title': '🌬️ **Pranayama**',
        'pranayama_config_body': (
            "{title}\n\n"
            "📊 Exercises: {exercises}\n"
            "⏱️ Exercise time: {exercise_time}\n"
            "⏸️ Rest time: {rest_time}\n\n"
            "Configure parameters or start the practice:"
        ),
        'asana_started_title': '🧘‍♂️ **Practice: {name}**',
        'asana_started_generic': '🧘‍♂️ **Asana practice started!**',
        'asana_started_body': (
            "{title}\n\n"
            "{work}\n"
            "{rest}\n"
            "{cycles}\n\n"
            "Starting with the first round! 💪"
        ),
        'pranayama_started_title': '🌬️ **Pranayama practice started!**',
        'pranayama_started_body': (
            "🌬️ **Pranayama practice started!**\n\n"
            "📊 Exercises: {exercises}\n"
            "⏱️ Exercise time: {exercise_time}\n"
            "⏸️ Rest time: {rest_time}\n\n"
            "Starting with the first exercise! 🧘‍♂️"
        ),
        'btn_pause': '⏸️ Pause',
        'btn_stop': '⏹️ Stop',
        'btn_resume': '▶️ Resume',
        'btn_reset': '🔄 Reset',
        'btn_delete': '🗑️ Delete',
        'btn_timer_start': '▶️ Start',
        'timer_stopped': (
            "⏹️ **Timer stopped**\n\n"
            "Practice complete. Great job! 🙏\n\n"
            "Want to start a new practice?"
        ),
        'timer_deleted': "🗑️ Timer deleted\n\nWant to start a new practice?",
        'timer_back_text': '🔙 **Returning to the timer menu...**',
        'timer_exit_text': '🔙 **Exiting the timer...**',
        'practice_completed_notif': '🎉 **Practice complete!**\n\nGreat job! 🙏',
        'meditation_completed': (
            "🧘 **Meditation complete!**\n\n"
            "Great practice! I hope you feel calm and harmonious. 🙏\n\n"
            "Want to start a new meditation?"
        ),
        'meditation_status': (
            "{emoji} **Meditation**\n\n"
            "Time left: {remaining}\n"
            "{bar}\n\n"
            "Progress: {progress}"
        ),
        'asana_completed': (
            "{timer_name} **— practice complete!**\n\n"
            "Great job! All cycles finished. 💪\n\n"
            "You did great! Want to start a new practice?"
        ),
        'asana_status': (
            "{emoji} **{timer_name}**\n\n"
            "Phase: {phase}\n"
            "Remaining: {remaining}\n"
            "{bar}\n\n"
            "Cycle: {cycle}/{cycles}\n"
            "Total time: {total}"
        ),
        'phase_work': 'Work',
        'phase_rest': 'Rest',
        'work_finish_notif': (
            "🔔 **Work time finished!**\n\n"
            "Rest now! Restore your breath and get ready for the next round. 🛏️\n\n"
            "Rest: {seconds} seconds"
        ),
        'rest_finish_notif': (
            "🔔 **Rest finished!**\n\n"
            "Get ready! Starting the next round. 💪\n\n"
            "Work: {seconds} seconds"
        ),
        'sec_unit': 's',
        'min_unit': 'm',
        'timer_asana_name': '🧘 **Asana**',
        'timer_pranayama_name': '🌬️ **Pranayama**',
        'cmd_start': 'Start the bot and open the menu',
        'cmd_help': 'Help and list of features',
        'cmd_what': 'What is Dharana — about the project',
        'cmd_info': 'About the bot and subscription',
        'cmd_about_us': 'Our team',
        'cmd_language': 'Change bot language (English / Русский)',
        'cmd_asana_day': 'Asana of the day — get and configure',
        'cmd_pay': 'Get Premium subscription',
    },
}