import os
import config

import telebot
from telebot import types

from backend.models import BotUser, Category, Product
from backend.templates import Messages, Keys, Smiles

from bot import utils
from bot.call_types import CallTypes
from bot.config import APP_DIR


def make_subcategory_buttons(parent: Category, lang: str):
    if parent is None:
        categories = Category.categories.filter(parent=None)
    else:
        categories = parent.children.all()

    buttons = []
    for category in categories:
        category_button = utils.make_inline_button(
            text=category.name,
            CallType=CallTypes.Category,
            category_id=category.id,
        )
        buttons.append(category_button)

    if parent and parent.parent:
        back_button = utils.make_inline_button(
            text=parent.parent.name,
            CallType=CallTypes.Category,
            category_id=parent.parent.id
        )
    else:
        if parent:
            back_button = utils.make_inline_button(
                text=Keys.PRODUCTS.get(lang),
                CallType=CallTypes.Products,
            )
        else:
            back_button = utils.make_inline_button(
                text=Keys.BACK.get(lang),
                CallType=CallTypes.Back,
            )

    if parent is not None:
        text = parent.name+Keys.ALL_PRODUCTS.get(lang)
        all_products_button = utils.make_inline_button(
            text=text,
            CallType=CallTypes.AllProducts,
            category_id=parent.id,
        )
        buttons.append(all_products_button)

    buttons.append(back_button)
    return buttons


def get_all_child_products(category: Category):
    products = list(category.products.all())
    for sub_category in category.children.all():
        products += get_all_child_products(sub_category)

    return products


def products_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    text = Messages.CHOOSE_CATEGORY.get(lang)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = make_subcategory_buttons(None, lang)
    keyboard.add(*buttons)
    if call.message.content_type == 'photo':
        bot.send_message(chat_id, text,
                         reply_markup=keyboard)
        bot.delete_message(chat_id, call.message.id)
    else:
        bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=call.message.id,
            reply_markup=keyboard,
        )


def category_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    category_id = call_type.category_id
    category = Category.categories.get(id=category_id)

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    if category.children.exists():
        chat_id = call.message.chat.id
        user = BotUser.objects.get(chat_id=chat_id)
        lang = user.lang
        buttons = make_subcategory_buttons(category, lang)
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*buttons)

        text = utils.text_to_fat(category.get_name(lang))
        bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=call.message.id,
            reply_markup=keyboard,
        )
    else:
        products = get_all_child_products(category)
        page = 0
        product = products[page]
        product_info = get_product_info(product, lang)
        product_image_path = get_product_image_path(product)
        keyboard = make_product_keyboard(category, page, lang)
        with open(product_image_path, 'rb') as photo:
            bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=product_info,
                reply_markup=keyboard,
            )


def all_products_call_handler(bot: telebot.TeleBot, call):
    call_type = CallTypes.parse_data(call.data)
    category_id = call_type.category_id
    category = Category.categories.get(id=category_id)
    products = get_all_child_products(category)
    page = 0
    product = products[page]

    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang
    product_info = get_product_info(product, lang)
    product_image_path = get_product_image_path(product)
    keyboard = make_product_keyboard(category, page, lang)
    with open(product_image_path, 'rb') as photo:
        bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=product_info,
            reply_markup=keyboard,
        )


def add_to_shop_card_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang

    call_type = CallTypes.parse_data(call.data)
    product_id = call_type.product_id
    product = Product.products.get(id=product_id)
    purchase, _ = user.shop_card.purchases.get_or_create(product=product)
    purchase.count += 1
    purchase.save()

    text = Messages.ADDED_TO_SHOP_CARD.get(lang)
    bot.answer_callback_query(call.id, text=text, show_alert=True)


def product_page_call_handler(bot: telebot.TeleBot, call):
    chat_id = call.message.chat.id
    user = BotUser.objects.get(chat_id=chat_id)
    lang = user.lang

    call_type = CallTypes.parse_data(call.data)
    category_id = call_type.category_id
    page = call_type.page
    category = Category.categories.get(id=category_id)
    products = get_all_child_products(category)
    product = products[page]

    product_info = get_product_info(product, lang)
    product_image_path = get_product_image_path(product)
    keyboard = make_product_keyboard(category, page, lang)
    with open(product_image_path, 'rb') as photo:
        bot.edit_message_media(
            media=types.InputMedia(
                type='photo',
                media=photo,
                caption=product_info,
                parse_mode='HTML'
            ),
            chat_id=chat_id,
            message_id=call.message.id,
            reply_markup=keyboard,
        )


def get_product_info(product: Product, lang: str):
    return Messages.PRODUCT_INFO.get(lang).format(
        title=product.title,
    )


def get_product_image_path(product: Product):
    return os.path.join(APP_DIR, product.image.name)


def make_product_keyboard(category: Category, page: int, lang: str):
    products = get_all_child_products(category)
    product = products[page]
    products_count = len(products)
    page_buttons = [
        utils.make_inline_button(
            text=Smiles.PREVIOUS.text,
            CallType=CallTypes.ProductPage,
            category_id=category.id,
            page=(page-1+products_count) % products_count,
        ),
        utils.make_inline_button(
            text=str(page+1),
            CallType=CallTypes.Nothing,
        ),
        utils.make_inline_button(
            text=Smiles.NEXT.text,
            CallType=CallTypes.ProductPage,
            category_id=category.id,
            page=(page+1) % products_count,
        ),
    ]
    add_to_shop_card_button = utils.make_inline_button(
        text=Keys.ADD_TO_SHOP_CARD.get(lang),
        CallType=CallTypes.AddToShopCard,
        product_id=product.id,
    )
    shop_card_button = utils.make_inline_button(
        text=Keys.SHOP_CARD.get(lang),
        CallType=CallTypes.ShopCard,
    )
    back_button = utils.make_inline_button(
        text=Keys.BACK.get(lang),
        CallType=CallTypes.Products,
    )

    keyboard = types.InlineKeyboardMarkup(row_width=5)
    keyboard.add(*page_buttons)
    keyboard.add(add_to_shop_card_button)
    keyboard.add(shop_card_button, back_button)
    return keyboard
