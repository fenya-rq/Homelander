import io
import json
import re

import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile

from src.tg.dto import FeedDTO


def _extract_balanced_json(text: str) -> str | None:
    """Извлекает первый корректный JSON-объект по балансу скобок.

    Args:
        text: Исходная строка для поиска.

    Returns:
        Строка с JSON-объектом или None, если объект не найден.
    """
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    for i, ch in enumerate(text[start:], start=start):

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1

            if depth == 0:
                return text[start:i + 1]

    return None


def clean_and_parse_json(text: str) -> dict | None:
    """Парсит JSON из текста, очищая его от Markdown-разметки.

    Args:
        text: Текст, содержащий JSON (возможно в блоках ```json).

    Returns:
        Словарь с данными или None при ошибке парсинга.
    """
    if text.startswith('{') and text.endswith('}'):
        return json.loads(text)

    code_match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
    if code_match:
        text = code_match.group(1)

    json_str = _extract_balanced_json(text)
    if not json_str:
        return None

    return json.loads(json_str.strip())


def generate_weekly_chart(data: list[FeedDTO]) -> BufferedInputFile:
    """Визуализирует недельную статистику калорий в виде столбчатой
    диаграммы.

    Args:
        data: Список объектов FeedDTO с данными о питании.

    Returns:
        Изображение графика в формате BufferedInputFile для Telegram.
    """
    # Подготавливаем данные для осей
    days = [d.created_at.strftime('%d.%m') for d in data]
    # Форматируем дату как DD.MM
    calories = [d.energy for d in data]

    # Настраиваем стиль
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))

    # Рисуем столбчатую диаграмму
    bars = ax.bar(days, calories, color='#82aaff', edgecolor='white', alpha=0.8)

    # Добавляем значения над столбцами
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,f'{int(height)}',
            ha='center', va='bottom',
            fontsize=10,
            color='white'
        )

    # Настройка осей и заголовка
    ax.set_title('Потребление калорий за последние 7 дней', fontsize=16, pad=20)
    ax.set_ylabel('ккал', fontsize=12)
    ax.set_xlabel('Дата', fontsize=12)

    # Сетка
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    # Убираем рамки
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Сохраняем график в буфер
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buffer.seek(0)

    return BufferedInputFile(buffer.getvalue(), filename='weekly_stats.png')
