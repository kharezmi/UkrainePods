import config

import telebot
from telebot import types

from django.core.paginator import Paginator

from backend.models import BotUser, Order
from backend.templates import Messages, Keys

from bot import utils
from bot.call_types import CallTypes
from bot.shopcard import get_purchases_info, ordering_start


def get_order_info(order, lang):
    purchases_info = get_purchases_info(order.purchases.all(), lang)
    order_info = Messages.ORDER.get(lang).format(
        id=order.id,
        created=utils.datetime_to_utc5_str(order.created),
        full_name=order.full_name,
        contact=order.contact,
        mail=order.mail,
        city=order.city,
        purchases_info=purchases_info,
    )
    return order_info


def history_orders_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    page_number = call_type.page

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang

    orders = user.orders.filter(completed=True).reverse()
    if not orders.exists():
        text = Messages.HISTORY_ORDERS_EMPTY.get(lang)
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=text,
            show_alert=True,
        )
        return

    order = orders[page_number-1]
    order_info = get_order_info(order, lang)
    paginator = Paginator(orders, 1)
    page = paginator.get_page(page_number)
    reorder_button = utils.make_inline_button(
        text=Keys.REORDER.get(lang),
        CallType=CallTypes.ReOrder,
        order_id=order.id,
    )
    back_button = utils.make_inline_button(
        text=Keys.BACK.get(lang),
        CallType=CallTypes.Back,
    )
    keyboard = utils.make_page_keyboard(page, CallTypes.HistoryOrders)
    keyboard.add(reorder_button)
    keyboard.add(back_button)

    text = utils.text_to_fat(Keys.HISTORY_ORDERS.get(lang))
    text += utils.text_to_double_line(order_info)
    bot.edit_message_text(
        text=text,
        chat_id=chat_id,
        message_id=call.message.id,
        reply_markup=keyboard,
    )


def reorder_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)

    call_type = CallTypes.parse_data(call.data)
    order_id = call_type.order_id
    order = Order.orders.get(id=order_id)
    purchases = order.purchases.all()

    ordering_start(bot, user, purchases)
