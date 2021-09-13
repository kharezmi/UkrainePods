from .models import Template


keys = Template.keys.all()
messages = Template.messages.all()
smiles = Template.smiles.all()


class Keys():
    LANGUAGE = keys[0]
    PRODUCTS = keys[1]
    SHOP_CARD = keys[2]
    INFO = keys[3]
    MENU = keys[4]
    BACK = keys[5]
    ADD_TO_SHOP_CARD = keys[6]
    VIEW_PURCHASES = keys[7]
    CANCEL = keys[8]
    SHOP_CONTACTS = keys[9]
    SHOP_REVIEWS = keys[10]
    MY_REVIEW = keys[11]
    CHANGE_REVIEW = keys[12]
    WRITE_REVIEW = keys[13]
    DELETE_REVIEW = keys[14]
    YES = keys[15]
    NO = keys[16]
    SEND_CONTACT = keys[17]
    HISTORY_ORDERS = keys[18]
    REORDER = keys[19]


class Messages():
    WELCOME = messages[0]
    CHOICE_LANGUAGE = messages[1]
    INCEPTION = messages[2]
    CHOOSE_CATEGORY = messages[3]
    PRODUCT_INFO = messages[4]
    ADDED_TO_SHOP_CARD = messages[5]
    PURCHASE_INFO = messages[6]
    PURCHASES_INFO = messages[7]
    EMPTY_SHOP_CARD = messages[8]
    BUY_ALL = messages[9]
    BUY_ONE = messages[10]
    SHOP_INFO = messages[11]
    SHOP_CONTACTS = messages[12]
    REVIEW = messages[13]
    RATING_EVALUATION = messages[14]
    OPINION_MESSAGE = messages[15]
    SAVE_OPINION = messages[16]
    NO_REVIEW = messages[17]
    SHOP_MY_REVIEW_DELETED = messages[18]
    WANT_WRITE_REVIEW = messages[19]
    ORDERING_START = messages[20]
    ORDER_FORM_FULL_NAME = messages[21]
    IS_YOUR_NAME = messages[22]
    ORDER_FORM_CONTACT = messages[23]
    PLEASE_SEND_CONTACT = messages[24]
    ORDER_FORM_MAIL = messages[25]
    ORDER_FORM_CITY = messages[26]
    ORDERING_FINISH = messages[27]
    HISTORY_ORDERS_EMPTY = messages[28]
    ORDER = messages[29]
    NEW_ORDER = messages[30]
    GROUP_CHAT_ID_UPDATED = messages[31]


class Smiles():
    PREVIOUS = smiles[0]
    NEXT = smiles[1]
    REMOVE = smiles[2]
    SUBTRACT = smiles[3]
    ADD = smiles[4]
    STAR = smiles[5]
