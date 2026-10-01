# -*- coding: utf-8 -*-
"""Сборка компактной карточки статистики (/stats) из ответа API.

Формат — только «сухие числа»: сколько практик, минут, дней, серия,
разбивка по типам практик и топ-асаны. Ничего не додумывается на стороне
бота: числа приходят из dharana-api (тот же агрегатор, что у профиля в
приложении и на сайте).
"""

from src.i18n import (
    format_total_time,
    t,
    t_days,
    t_practices,
)

PRACTICE_TYPES = ("asana", "meditation", "pranayama")

# Сколько топ-асан показываем — карточка должна оставаться короткой.
TOP_ASANAS_LIMIT = 3


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def has_practice_data(stats: dict) -> bool:
    """Есть ли что показывать (пустую карточку не рисуем)."""
    return bool(stats) and _int(stats.get("total_sessions")) > 0


def format_stats(lang: str, stats: dict) -> str:
    """Карточка статистики на языке бота. Markdown (для aiogram ParseMode.MARKDOWN)."""
    if not has_practice_data(stats):
        return t(lang, 'stats_empty')

    lines = [t(lang, 'stats_title'), '']

    sessions = _int(stats.get("total_sessions"))
    lines.append(t(lang, 'stats_sessions', sessions=t_practices(lang, sessions)))
    lines.append(t(lang, 'stats_total_time', time=format_total_time(lang, _int(stats.get("total_minutes")))))

    streak = _int(stats.get("current_streak"))
    if streak > 0:
        streak_text = t(lang, 'stats_streak_in_row', days=t_days(lang, streak))
        lines.append(t(lang, 'stats_streak', streak=streak_text))

    lines.append(t(lang, 'stats_days', days=t_days(lang, _int(stats.get("total_days")))))

    total_asanas = _int(stats.get("total_asanas_practiced"))
    if total_asanas > 0:
        lines.append(t(lang, 'stats_asanas', asanas=total_asanas))

    by_type = stats.get("by_type") or {}
    breakdown = []
    for practice_type in PRACTICE_TYPES:
        row = by_type.get(practice_type) or {}
        type_sessions = _int(row.get("sessions"))
        if type_sessions <= 0:
            continue
        breakdown.append(t(
            lang,
            'stats_breakdown',
            emoji=t(lang, f'type_{practice_type}'),
            label=t(lang, f'stats_type_{practice_type}'),
            sessions=t_practices(lang, type_sessions),
            time=format_total_time(lang, _int(row.get("minutes"))),
        ))
    if breakdown:
        lines.append('')
        lines.extend(breakdown)

    favorites = [
        item for item in (stats.get("favorite_asanas") or [])
        if isinstance(item, dict) and item.get("name")
    ][:TOP_ASANAS_LIMIT]
    if favorites:
        names = ', '.join(f"{item['name']} ×{_int(item.get('count'), 1)}" for item in favorites)
        lines.append('')
        lines.append(t(lang, 'stats_favorites', asanas=names))

    lines.append('')
    lines.append(t(lang, 'stats_app_hint'))
    return "\n".join(lines)