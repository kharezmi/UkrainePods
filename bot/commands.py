import config

import telebot
from telebot import types

from bot import utils
from bot.call_types import CallTypes
from bot.states import States

from backend.models import BotUser, ShopCard
from backend.templates import Messages, Keys


def start_command_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    keyboard = types.InlineKeyboardMarkup()

    ru_language_button = utils.make_inline_button(
        text=Keys.LANGUAGE.get(BotUser.Lang.RU),
        CallType=CallTypes.Language,
        lang=BotUser.Lang.RU,
    )
    ua_language_button = utils.make_inline_button(
        text=Keys.LANGUAGE.get(BotUser.Lang.UA),
        CallType=CallTypes.Language,
        lang=BotUser.Lang.UA,
    )
    keyboard.add(ru_language_button)
    keyboard.add(ua_language_button)

    text = Messages.CHOICE_LANGUAGE.text
    bot.send_message(chat_id, text,
                     reply_markup=keyboard)


def language_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    lang = call_type.lang
    chat_id = call.message.chat.id
    user, _ = BotUser.objects.get_or_create(chat_id=chat_id)
    user.lang = lang
    user.save()
    ShopCard.shop_cards.get_or_create(user=user)
    first_name = call.message.chat.first_name

    text = Messages.WELCOME.get(lang).format(first_name=first_name)
    bot.send_message(chat_id, text)

    text = Messages.INCEPTION.get(lang)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Keys.MENU.get(lang))
    bot.send_message(chat_id, text,
                     reply_markup=keyboard)


def menu_command_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    products_button = utils.make_inline_button(
        text=Keys.PRODUCTS.get(lang),
        CallType=CallTypes.Products,
    )
    shop_card_button = utils.make_inline_button(
        text=Keys.SHOP_CARD.get(lang),
        CallType=CallTypes.ShopCard,
    )
    history_orders_button = utils.make_inline_button(
        text=Keys.HISTORY_ORDERS.get(lang),
        CallType=CallTypes.HistoryOrders,
        page=1,
    )
    info_button = utils.make_inline_button(
        text=Keys.INFO.get(lang),
        CallType=CallTypes.Info,
    )

    menu_keyboard = types.InlineKeyboardMarkup()
    menu_keyboard.add(products_button)
    menu_keyboard.add(shop_card_button, history_orders_button)
    menu_keyboard.add(info_button)

    text = utils.text_to_fat(Keys.MENU.get(lang))
    if hasattr(message, 'edited') and message.content_type == 'text':
        bot.edit_message_text(
            chat_id=chat_id,
            text=text,
            message_id=message.id,
            reply_markup=menu_keyboard,
        )
    else:
        if message.content_type == 'photo':
            bot.delete_message(chat_id, message.id)

        bot.send_message(chat_id, text,
                         reply_markup=menu_keyboard)


def back_call_handler(bot: telebot.TeleBot, call):
    call.message.edited = True
    menu_command_handler(bot, call.message)


def cancel_message_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    user.orders.filter(completed=False).delete()

    bot.delete_message(chat_id, message.id)
    menu_command_handler(bot, message)
