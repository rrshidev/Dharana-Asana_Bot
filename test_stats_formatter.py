# -*- coding: utf-8 -*-
"""Карточка статистики /stats: только сухие числа, оба языка."""

from src.i18n import format_total_time, t_days, t_practices
from src.utils.stats_formatter import format_stats, has_practice_data


STATS = {
    "total_minutes": 324,
    "total_days": 9,
    "total_sessions": 12,
    "total_asanas_practiced": 24,
    "current_streak": 3,
    "favorite_asanas": [
        {"name": "Бакасана", "count": 4},
        {"name": "Триконасана", "count": 2},
        {"name": "Адхо мукха шванасана", "count": 2},
        {"name": "Викшасана", "count": 1},
    ],
    "by_type": {
        "asana": {"minutes": 240, "sessions": 8},
        "meditation": {"minutes": 75, "sessions": 3},
        "pranayama": {"minutes": 0, "sessions": 0},
    },
}


def test_has_practice_data():
    assert has_practice_data(STATS) is True
    assert has_practice_data({"total_sessions": 0}) is False
    assert has_practice_data({}) is False
    assert has_practice_data(None) is False


def test_empty_state_ru():
    text = format_stats('ru', {"total_sessions": 0, "by_type": {}})
    assert text == (
        '📊 **Пока нет статистики**\n\n'
        'Заверши первую практику с таймером — и здесь появятся твои минуты, '
        'дни и серии 🧘'
    )


def test_empty_state_en():
    assert 'No statistics yet' in format_stats('en', {"total_sessions": 0})


def test_ru_card_shows_key_numbers():
    text = format_stats('ru', STATS)
    assert text.startswith('📊 **Статистика практики**')
    assert '🧘 Практик: 12 практик' in text          # 12 -> практик
    assert '⏱ Всего: 5 ч 24 мин' in text
    assert '🔥 Серия: 3 дня подряд' in text
    assert '📅 Дней практики: 9 дней' in text
    assert '🌿 Асан выполнено: 24' in text
    assert '🧘 Асаны: 8 практик · 4 ч' in text
    assert '🕯 Медитации: 3 практики · 1 ч 15 мин' in text
    assert 'Пранаяма' not in text                     # 0 сессий — не показываем
    assert '📱 Графики и история — в приложении Dharana' in text


def test_ru_card_limits_favorites():
    text = format_stats('ru', STATS)
    favorites_line = next(line for line in text.splitlines() if line.startswith('❤️'))
    assert favorites_line == '❤️ Любимые асаны: Бакасана ×4, Триконасана ×2, Адхо мукха шванасана ×2'
    assert 'Викшасана' not in favorites_line          # только топ-3


def test_en_card():
    text = format_stats('en', STATS)
    assert text.startswith('📊 **Practice statistics**')
    assert '🧘 Practices: 12 practices' in text
    assert '⏱ Total: 5h 24m' in text
    assert '🔥 Streak: 3 days in a row' in text
    assert '📅 Days practised: 9 days' in text
    assert '🧘 Asanas: 8 practices · 4h' in text
    assert '🕯 Meditations: 3 practices · 1h 15m' in text
    assert 'Pranayama' not in text
    assert '📱 Charts and history — in the Dharana app' in text


def test_en_favorites_localized():
    """EN-карточка показывает асаны латиницей (API отдаёт канонические имена)."""
    mapping = {
        "Бакасана": "BAKASANA",
        "Триконасана": "TRIKONASANA",
        "Адхо мукха шванасана": "ADHO MUKHA SVANASANA",
    }
    text = format_stats('en', STATS, lambda name: mapping.get(name))
    favorites_line = next(line for line in text.splitlines() if line.startswith('❤️'))
    assert favorites_line == (
        '❤️ Favourite asanas: BAKASANA ×4, TRIKONASANA ×2, '
        'ADHO MUKHA SVANASANA ×2'
    )
    assert 'Бакасана' not in text


def test_localizer_fallbacks():
    """Нет EN-имени или локализатор упал — остаётся каноническое имя."""
    text = format_stats('en', STATS, lambda name: None)
    favorites_line = next(line for line in text.splitlines() if line.startswith('❤️'))
    assert 'BAKASANA' not in favorites_line
    assert 'Бакасана ×4' in favorites_line

    def boom(name):
        raise RuntimeError('catalog unavailable')

    text = format_stats('en', STATS, boom)
    assert 'Бакасана ×4' in text


def test_card_is_short():
    """Коротко: не больше 14 строк и без подряд идущих пустых."""
    lines = format_stats('ru', STATS).splitlines()
    assert len(lines) <= 14
    assert all(not (a == '' and b == '') for a, b in zip(lines, lines[1:]))
    assert not any(line.endswith(': ') for line in lines)


def test_singular_forms():
    assert t_practices('ru', 1) == '1 практика'
    assert t_practices('ru', 3) == '3 практики'
    assert t_practices('en', 1) == '1 practice'
    assert t_days('ru', 1) == '1 день'
    assert t_days('ru', 2) == '2 дня'
    assert t_days('ru', 5) == '5 дней'
    assert t_days('en', 1) == '1 day'


def test_single_practice_card():
    text = format_stats('ru', {
        "total_minutes": 5,
        "total_days": 1,
        "total_sessions": 1,
        "total_asanas_practiced": 0,
        "current_streak": 1,
        "favorite_asanas": [],
        "by_type": {"asana": {"minutes": 5, "sessions": 1}},
    })
    assert '🧘 Практик: 1 практика' in text
    assert '⏱ Всего: 5 мин' in text
    assert '🔥 Серия: 1 день подряд' in text
    assert '📅 Дней практики: 1 день' in text
    assert '🌿 Асан выполнено' not in text            # ноль — не показываем
    assert 'Любимые асаны' not in text


def test_missing_fields_do_not_crash():
    text = format_stats('ru', {"total_sessions": 2})
    assert '🧘 Практик: 2 практики' in text
    assert '⏱ Всего: 0 мин' in text


def test_time_format():
    assert format_total_time('ru', 0) == '0 мин'
    assert format_total_time('ru', 59) == '59 мин'
    assert format_total_time('ru', 60) == '1 ч'
    assert format_total_time('ru', 65) == '1 ч 5 мин'
    assert format_total_time('en', 0) == '0m'
    assert format_total_time('en', 324) == '5h 24m'