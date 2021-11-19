# import time
from config import settings
###
from apps.orders.models import BaseOrder

from .models import TelegramBot


def send_order_email(msg:str):
    pass

def send_order_telegram(msg:str):
    group_id = settings.telegram_notif_group_id
    bot = TelegramBot(username=settings.telegram_bot_username, access_token=settings.telegram_bot_token)
    bot.send_msg(group_id, msg)

def send_order_admin_notification(order: BaseOrder):
    print('call send order admin notif order is', order)
    if not order:
        return
    msg = "🔥 *Новый заказ* ✨ \n"
    msg += f"{'-'*5} Информация по заказу {'-'*5} \n"
    msg += f"Дата создания: {order.date_created} \n"
    msg += f"Клиент: *{order.customer_username}* \n"

    if not order.cart:
        return None
    if order.payment_method and order.delivery_method:
        msg += f"Оплата: *{order.payment_method.name}* \n"
        msg += f"Доставка: *{order.delivery_method.name}* \n"
    if order.delivery_method.id == 'delivery':
        if order.delivery_address and order.customer_id:
            msg += f"Адрес доставки: {order.delivery_address.address_display} \n"
        else:
            msg += f"Адрес доставки: {order.guest_delivery_address} \n"
    if order.delivery_method.id == 'pickup':
        msg += f"Пункт выдачи: {order.pickup_address.name} \n"
    msg += f"Сумма без скидки: {order.cart.base_amount} \n"
    msg += f"Сумма скидки: {order.cart.discount_amount} \n"
    if order.cart.promo_discount_amount and order.cart.promo_discount_amount > 0:
        msg += f"Скидка по промокоду: {order.cart.promo_discount_amount} \n"
    if order.cart.bonuses_used and order.cart.pay_with_bonuses:
        msg += f"Оплачено бонусами: {order.cart.pay_with_bonuses} \n"
    msg += f"Сумма заказа: *{order.cart.total_amount}* \n"
    msg += f"{'-'*5} Состав заказа {'-'*5} \n"
    for index, item in enumerate(order.cart.line_items):
        msg+= f"{index + 1}. {item.product.name} - {item.quantity} шт. \n"


    # replace for telegram
    msg = msg.replace('-', '\-').replace('.', '\.').replace('=', '\=').replace('(','\(').replace(')','\)').replace('+', '\+')

    send_order_telegram(msg=msg)
#   await send_order_email(msg=msg)
