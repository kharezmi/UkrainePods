import requests

import telebot
from telebot import types

from django.utils import timezone
from django.core.paginator import Page

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from bot import config
from bot.call_types import CallTypes
from backend.templates import Smiles


def seconds_to_time_str(seconds: int):
    minutes, seconds = seconds // 60, seconds % 60
    return '{:02}:{:02}'.format(minutes, seconds)


def text_to_fat(text: str) -> str:
    return f"<b>{text}</b>"


def text_to_italic(text: str) -> str:
    return f"<i>{text}</i>"


def text_to_code(text: str) -> str:
    return f"<code>{text}</code>"


def text_to_underline(text: str) -> str:
    return f"<u>{text}</u>"


def text_to_double_line(text: str) -> str:
    new_text = '\n———————————————————'
    new_text += '\n\n'
    new_text += text
    new_text += '\n———————————————————'
    new_text += '\n\n'
    return new_text


def datetime_to_utc5_str(dt) -> str:
    return (dt+timezone.timedelta(hours=5)).strftime('%d-%m-%Y, %H:%M')


def filter_tag(tag: Tag, ol_number=None):
    if isinstance(tag, NavigableString):
        text = tag
        text = text.replace('<', '&#60;')
        text = text.replace('>', '&#62;')
        return text

    html = str()
    li_number = 0
    for child_tag in tag:
        if tag.name == 'ol':
            if child_tag.name == 'li':
                li_number += 1
        else:
            li_number = None

        html += filter_tag(child_tag, li_number)

    format_tags = ['strong', 'em', 'pre', 'b', 'u', 'i', 'code']
    if tag.name in format_tags:
        return f'<{tag.name}>{html}</{tag.name}>'

    if tag.name == 'a':
        return f"""<a href="{tag.get("href")}">{tag.text}</a>"""

    if tag.name == 'li':
        if ol_number:
            return f'{ol_number}. {html}'
        return f'•  {html}'

    if tag.name == 'br':
        html += '\n'

    if tag.name == 'span':
        styles = tag.get_attribute_list('style')
        if 'text-decoration: underline;' in styles:
            return f'<u>{html}</u>'

    if tag.name == 'ol' or tag.name == 'ul':
        return '\n'.join(map(lambda row: f'   {row}', html.split('\n')))

    return html


def filter_html(html: str):
    soup = BeautifulSoup(html, 'lxml')
    return filter_tag(soup)


def get_file(file_id):
    bot = telebot.TeleBot(config.TOKEN)
    file = bot.get_file(file_id)
    file_path = file.file_path
    file_url = f'https://api.telegram.org/file/bot{config.TOKEN}/{file_path}'
    response = requests.get(file_url)
    if response.ok:
        return response.content


def get_file_text(file_id):
    bot = telebot.TeleBot(config.TOKEN)
    file = bot.get_file(file_id)
    file_path = file.file_path
    file_url = f'https://api.telegram.org/file/bot{config.TOKEN}/{file_path}'
    response = requests.get(file_url)
    if response.ok:
        return response.text


def make_page_keyboard(page: Page, CallType, **kwargs):
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    buttons = []
    if page.has_previous():
        prev_page_button = make_inline_button(
            text=f'{Smiles.PREVIOUS}',
            CallType=CallType,
            page=page.previous_page_number(),
            **kwargs,
        )
        buttons.append(prev_page_button)

    page_number_button = make_inline_button(
        text=str(page.number),
        CallType=CallTypes.Nothing,
    )
    buttons.append(page_number_button)

    if page.has_next():
        next_page_button = make_inline_button(
            text=f'{Smiles.NEXT}',
            CallType=CallType,
            page=page.next_page_number(),
            **kwargs,
        )
        buttons.append(next_page_button)

    keyboard.add(*buttons)
    return keyboard


def make_inline_button(text, CallType, **kwargs):
    call_type = CallType(**kwargs)
    call_data = CallTypes.make_data(call_type)
    button = types.InlineKeyboardButton(
        text=text,
        callback_data=call_data,
    )
    return button


def make_page_buttons(queryset, CallType):
    buttons = []
    for obj in queryset:
        class_name = obj.__class__.__name__.lower()
        kwargs = {
            f'{class_name}_id': obj.id
        }
        call_type = CallType(**kwargs)
        call_data = CallTypes.make_data(call_type)
        button = types.InlineKeyboardButton(
            text=obj.id,
            callback_data=call_data,
        )
        buttons.append(button)

    return buttons


def get_page_start_end(page: int, per_page: int):
    start = (page-1)*per_page
    end = page*per_page
    return start, end


def normalize_page(page, all):
    return (page % all + all) % all
