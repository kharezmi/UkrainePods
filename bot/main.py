import config

import telebot

from backend.models import BotUser
from backend.templates import Keys, Messages

from bot import commands, products, shopcard, info, orders
from bot.call_types import CallTypes
from bot.states import States


bot = telebot.TeleBot(
    token=config.TOKEN,
    num_threads=3,
    parse_mode='HTML',
)

message_handlers = {
    '/start': commands.start_command_handler,
    '/menu': commands.menu_command_handler,
}

key_handlers = {
    Keys.MENU: commands.menu_command_handler,
    Keys.CANCEL: commands.cancel_message_handler,
}


def update_full_name(chat):
    user = BotUser.objects.get(chat_id=chat.id)
    first_name = chat.first_name
    last_name = chat.last_name
    full_name = first_name
    if last_name:
        full_name += ' ' + last_name

    user.full_name = full_name
    user.save()


@bot.message_handler(content_types=['text'])
def message_handler(message):
    if message.chat.type in ['group', 'supergroup']:
        if message.text == '/update_chat_id':
            update_chat_id(message.chat.id)

        return

    chat_id = message.chat.id
    if BotUser.objects.filter(chat_id=chat_id).exists():
        update_full_name(message.chat)
        user = BotUser.objects.get(chat_id=chat_id)
        lang = user.lang
        if (state := user.bot_state):
            if state == States.ORDER_FORM_FULL_NAME:
                shopcard.order_form_full_name_message_handler(bot, message)

            if state == States.ORDER_FORM_CONTACT:
                text = Messages.PLEASE_SEND_CONTACT.get(lang)
                bot.send_message(chat_id, text)

            if state == States.ORDER_FORM_MAIL:
                shopcard.order_form_mail_message_handler(bot, message)

            if state == States.ORDER_FORM_CITY:
                shopcard.order_form_city_message_handler(bot, message)

            if state == States.WRITE_REVIEW:
                user.bot_state = None
                user.save()
                if message.text == Keys.CANCEL.get(lang):
                    commands.menu_command_handler(bot, message)
                else:
                    info.write_review_message_handler(bot, message)

            return

    for text, message_handler in message_handlers.items():
        if message.text == text:
            message_handler(bot, message)
            break

    for key, message_handler in key_handlers.items():
        if message.text in key.getall():
            message_handler(bot, message)
            break

    bot.delete_message(chat_id, message.id)


callback_query_handlers = {
    CallTypes.Nothing: lambda _, __: True,
    CallTypes.Back: commands.back_call_handler,
    CallTypes.Language: commands.language_call_handler,

    CallTypes.Products: products.products_call_handler,
    CallTypes.Category: products.category_call_handler,
    CallTypes.ProductPage: products.product_page_call_handler,
    CallTypes.AddToShopCard: products.add_to_shop_card_call_handler,

    CallTypes.ShopCard: shopcard.shop_card_call_handler,
    CallTypes.PurchasePage: shopcard.purchase_page_call_handler,
    CallTypes.PurchaseCount: shopcard.purchase_count_call_handler,
    CallTypes.PurchaseRemove: shopcard.purchase_remove_call_handler,
    CallTypes.PurchaseBuy: shopcard.purchase_buy_call_handler,
    CallTypes.PurchasesBuy: shopcard.purchases_buy_call_handler,
    CallTypes.IsYourName: shopcard.is_your_name_call_handler,

    CallTypes.Info: info.info_call_handler,
    CallTypes.ShopContacts: info.shop_contacts_call_handler,
    CallTypes.ShopReviews: info.shop_reviews_call_handler,
    CallTypes.ShopMyReview: info.shop_my_review_call_handler,
    CallTypes.ShopMyReviewChange: info.shop_my_review_change_call_handler,
    CallTypes.ShopMyReviewDelete: info.shop_my_review_delete_call_handler,
    CallTypes.ShopMyReviewRatingBall:
        info.shop_my_review_rating_ball_call_handler,
    CallTypes.WantWriteReview: info.want_write_review_call_handler,

    CallTypes.HistoryOrders: orders.history_orders_call_handler,
    CallTypes.ReOrder: orders.reorder_call_handler,
}


@bot.callback_query_handler(func=lambda _: True)
def callback_query_handler(call):
    call_type = CallTypes.parse_data(call.data)
    chat_id = call.message.chat.id
    if BotUser.objects.filter(chat_id=chat_id).exists():
        update_full_name(call.message.chat)
        user = BotUser.objects.get(chat_id=chat_id)
        if (state := user.bot_state):
            if state == States.IS_YOUR_NAME:
                shopcard.is_your_name_call_handler(bot, call)

            return

    for CallType, query_handler in callback_query_handlers.items():
        if call_type.__class__ == CallType:
            query_handler(bot, call)
            break


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    if user.bot_state == States.ORDER_FORM_CONTACT:
        shopcard.order_form_contact_message_handler(bot, message)


def update_chat_id(chat_id):
    with open('group_chat_id.txt', 'w') as file:
        file.write(str(chat_id))

    text = Messages.GROUP_CHAT_ID_UPDATED.text
    bot.send_message(chat_id, text)


if __name__ == "__main__":
    # bot.polling()
    bot.infinity_polling()
