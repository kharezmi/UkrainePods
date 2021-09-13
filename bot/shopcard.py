import os
import config

import telebot
from telebot import TeleBot, types

from backend.models import BotUser, Product, Order
from backend.templates import Messages, Smiles, Keys

from bot import utils, commands
from bot.call_types import CallTypes
from bot.states import States


def get_purchases_info(purchases, lang):
    all_purchases_info = str()
    purchases_price = 0
    for purchase in purchases:
        purchase_info = Messages.PURCHASE_INFO.get(lang).format(
            product_title=purchase.product.title,
            count=purchase.count,
            price=purchase.price,
        )
        purchases_price += purchase.price
        all_purchases_info += purchase_info + '\n'

    purchases_info = Messages.PURCHASES_INFO.get(lang).format(
        all_purchases_info=all_purchases_info,
        purchases_price=purchases_price,
    )
    return purchases_info


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


def get_group_chat_id():
    with open('group_chat_id.txt', 'r') as file:
        chat_id = file.read()

    return chat_id


def shop_card_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    purchases_count = purchases.count()
    if purchases_count == 0:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=Messages.EMPTY_SHOP_CARD.get(lang),
            show_alert=True,
        )
        return

    text = get_purchases_info(purchases, lang)
    view_purchases_button = utils.make_inline_button(
        text=Keys.VIEW_PURCHASES.get(lang),
        CallType=CallTypes.PurchasePage,
        page=0,
    )
    price_all = shop_card.price
    buy_all_button = utils.make_inline_button(
        text=Messages.BUY_ALL.get(lang).format(price_all=price_all),
        CallType=CallTypes.PurchasesBuy,
    )
    back_button = utils.make_inline_button(
        text=Keys.BACK.get(lang),
        CallType=CallTypes.Back,
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(view_purchases_button)
    keyboard.add(buy_all_button)
    keyboard.add(back_button)
    if call.message.content_type == 'photo':
        bot.send_message(chat_id, text,
                         reply_markup=keyboard)
    else:
        bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=call.message.id,
            reply_markup=keyboard,
        )


def get_product_info(product: Product, lang: str):
    return Messages.PRODUCT_INFO.get(lang).format(
        title=product.title,
    )


def get_product_image_path(product: Product):
    return os.path.join(config.APP_DIR, product.image.name)


def make_purchase_keyboard(user: BotUser, page):
    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    purchases_count = purchases.count()
    purchase = purchases[page]
    lang = user.lang
    page_buttons = [
        utils.make_inline_button(
            text=Smiles.PREVIOUS.text,
            CallType=CallTypes.PurchasePage,
            page=utils.normalize_page(page-1, purchases_count),
        ),
        utils.make_inline_button(
            text=str(page+1),
            CallType=CallTypes.Nothing,
        ),
        utils.make_inline_button(
            text=Smiles.NEXT.text,
            CallType=CallTypes.PurchasePage,
            page=utils.normalize_page(page+1, purchases_count),
        ),
    ]
    plus_minus_buttons = [
        utils.make_inline_button(
            text=Smiles.SUBTRACT.text,
            CallType=CallTypes.PurchaseCount,
            page=page,
            count=purchase.count-1,
        ),
        utils.make_inline_button(
            text=str(purchase.count),
            CallType=CallTypes.Nothing,
        ),
        utils.make_inline_button(
            text=Smiles.ADD.text,
            CallType=CallTypes.PurchaseCount,
            page=page,
            count=purchase.count+1,
        ),
    ]

    remove_button = utils.make_inline_button(
        text=Smiles.REMOVE.text,
        CallType=CallTypes.PurchaseRemove,
        page=page,
    )

    price_one = purchase.price
    buy_one_button = utils.make_inline_button(
        text=Messages.BUY_ONE.get(lang).format(price_one=price_one),
        CallType=CallTypes.PurchaseBuy,
        page=page,
    )

    price_all = shop_card.price
    buy_all_button = utils.make_inline_button(
        text=Messages.BUY_ALL.get(lang).format(price_all=price_all),
        CallType=CallTypes.PurchasesBuy,
    )

    keyboard = types.InlineKeyboardMarkup(row_width=5)
    keyboard.add(*page_buttons)
    keyboard.add(*plus_minus_buttons)
    keyboard.add(remove_button)
    keyboard.add(buy_one_button)
    keyboard.add(buy_all_button)
    return keyboard


def purchase_page_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    page = call_type.page

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang

    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    try:
        purchase = purchases[page]
    except IndexError:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text=Messages.EMPTY_SHOP_CARD.get(lang),
            show_alert=True,
        )
        return

    product = purchase.product

    product_info = get_product_info(product, lang)
    image_path = get_product_image_path(product)
    keyboard = make_purchase_keyboard(user, page)

    with open(image_path, 'rb') as photo:
        if call.message.content_type == 'photo':
            bot.edit_message_media(
                media=types.InputMedia(
                    type='photo',
                    media=photo,
                    caption=product_info,
                    parse_mode='HTML',
                ),
                chat_id=chat_id,
                message_id=call.message.id,
                reply_markup=keyboard,
            )
        else:
            bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=product_info,
                reply_markup=keyboard,
            )


def purchase_count_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    page = call_type.page
    count = call_type.count
    if count == 0:
        call_type = CallTypes.PurchaseRemove(page=page)
        call.data = CallTypes.make_data(call_type)
        purchase_remove_call_handler(bot, call)
        return

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)

    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    purchase = purchases[page]
    purchase.count = count
    purchase.save()

    call_type = CallTypes.PurchasePage(page=page)
    call.data = CallTypes.make_data(call_type)
    purchase_page_call_handler(bot, call)


def purchase_remove_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    page = call_type.page

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)

    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    purchase = purchases[page]
    purchase.delete()

    call_type = CallTypes.PurchasePage(page=page)
    call.data = CallTypes.make_data(call_type)
    purchase_page_call_handler(bot, call)


def purchase_buy_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    page = call_type.page

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)

    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    purchase = purchases[page]
    purchases = shop_card.purchases.filter(id=purchase.id)
    ordering_start(bot, user, purchases)


def purchases_buy_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)

    shop_card = user.shop_card
    purchases = shop_card.purchases.all()
    ordering_start(bot, user, purchases)


def ordering_start(bot: telebot.TeleBot, user, purchases):
    chat_id = user.chat_id
    lang = user.lang
    user.bot_state = States.IS_YOUR_NAME
    user.save()
    order = Order.orders.create(user=user)
    order.purchases.set(purchases)

    text = Messages.ORDERING_START.get(lang)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Keys.CANCEL.get(lang))
    bot.send_message(chat_id, text,
                     reply_markup=keyboard)

    text = Messages.IS_YOUR_NAME.get(lang).format(
        full_name=user.full_name,
    )
    yes_button = utils.make_inline_button(
        text=Keys.YES.get(lang),
        CallType=CallTypes.IsYourName,
        flag=True,
    )
    no_button = utils.make_inline_button(
        text=Keys.NO.get(lang),
        CallType=CallTypes.IsYourName,
        flag=False,
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(yes_button, no_button)

    bot.send_message(chat_id, text,
                     reply_markup=keyboard)


def is_your_name_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    order = user.orders.filter(completed=False).first()

    call_type = CallTypes.parse_data(call.data)
    flag = call_type.flag
    if flag:
        order.full_name = user.full_name
        order.save()
        order_form_contact(bot, user)
    else:
        text = Messages.ORDER_FORM_FULL_NAME.get(lang)
        bot.send_message(chat_id, text)
        user.bot_state = States.ORDER_FORM_FULL_NAME
        user.save()


def order_form_full_name_message_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    order = user.orders.filter(completed=False).first()
    order.full_name = message.text
    order.save()
    order_form_contact(bot, user)


def order_form_contact(bot: telebot.TeleBot, user):
    chat_id = user.chat_id
    lang = user.lang
    order = user.orders.filter(completed=False).first()
    completed_order = user.orders.filter(completed=True).first()
    if completed_order:
        order.contact = completed_order.contact
        order.save()
        order_form_mail(bot, user)
    else:
        user.bot_state = States.ORDER_FORM_CONTACT
        user.save()
        contact_button = types.KeyboardButton(
            text=Keys.SEND_CONTACT.get(lang),
            request_contact=True,
        )
        cancel_button = Keys.CANCEL.get(lang)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(contact_button)
        keyboard.add(cancel_button)
        text = Messages.ORDER_FORM_CONTACT.get(lang)
        bot.send_message(chat_id, text,
                         reply_markup=keyboard)


def order_form_contact_message_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    order = user.orders.filter(completed=False).first()
    order.contact = message.contact.phone_number
    order.save()
    order_form_mail(bot, user)


def order_form_mail(bot: telebot.TeleBot, user):
    chat_id = user.chat_id
    lang = user.lang
    text = Messages.ORDER_FORM_MAIL.get(lang)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Keys.CANCEL.get(lang))
    bot.send_message(chat_id, text,
                     reply_markup=keyboard)
    user.bot_state = States.ORDER_FORM_MAIL
    user.save()


def order_form_mail_message_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    order = user.orders.filter(completed=False).first()
    order.mail = message.text
    order.save()
    order_form_city(bot, user)


def order_form_city(bot: telebot.TeleBot, user):
    chat_id = user.chat_id
    lang = user.lang
    text = Messages.ORDER_FORM_CITY.get(lang)
    bot.send_message(chat_id, text)
    user.bot_state = States.ORDER_FORM_CITY
    user.save()


def order_form_city_message_handler(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    order = user.orders.filter(completed=False).first()
    order.city = message.text
    order.save()
    ordering_finish(bot, message)


def ordering_finish(bot: telebot.TeleBot, message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    user.bot_state = None
    user.save()

    order = user.orders.filter(completed=False).first()
    order.completed = True
    order.save()

    for purchase in order.purchases.all():
        user.shop_card.purchases.remove(purchase)

    text = Messages.ORDERING_FINISH.get(lang)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Keys.MENU.get(lang))
    bot.send_message(chat_id, text,
                     reply_markup=keyboard)
    commands.menu_command_handler(bot, message)

    group_chat_id = get_group_chat_id()
    text = Messages.NEW_ORDER.text
    bot.send_message(group_chat_id, text)
    order_info = get_order_info(order, lang)
    bot.send_message(group_chat_id, order_info)
