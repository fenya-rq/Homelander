from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class DateCallback(CallbackData, prefix='set_date'):
    date_str: str


class CancelCallback(CallbackData, prefix='cancel'):
    cancel_cmd: str


def get_week_dates_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    current_date = datetime.now() - timedelta(1)

    # Русские названия дней недели (опционально)
    days_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    months_ru = [
        'янв', 'фев', 'мар', 'апр', 'мая', 'июня',
        'июля', 'авг', 'сен', 'окт', 'ноя', 'дек'
    ]

    for i in range(7):
        date_obj = current_date - timedelta(days=i)

        # Красивое название: "Пн, 30 мар"
        day_str = days_ru[date_obj.weekday()]
        month_str = months_ru[date_obj.month-1]
        label = f'{day_str}, {date_obj.day} {month_str}'

        builder.button(
            text=label,
            callback_data=DateCallback(date_str=date_obj.strftime('%Y-%m-%d')).pack()
        )
    builder.row(
        InlineKeyboardButton(
            text='❌ Отмена',
            callback_data=CancelCallback(cancel_cmd='cancel_fsm').pack()
        )
    )

    return builder.adjust(2).as_markup()
