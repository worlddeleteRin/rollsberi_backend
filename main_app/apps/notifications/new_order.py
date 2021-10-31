import time
from config import settings
from pydantic import BaseModel
import httpx
###
from apps.orders.models import BaseOrder

class TelegramBot(BaseModel):
	api_url: str = "https://api.telegram.org/bot"
	username: str
	access_token: str

	def send_msg(self, chat_id: str, msg: str):
		req_url = self.api_url + self.access_token + "/sendMessage"
		print('request url is', req_url)
		data = {
			"chat_id": chat_id,
			"text": msg,
			"parse_mode": "MarkdownV2",
		}
		resp = httpx.post(req_url, data = data)
		print('resp is', resp.json())

async def send_order_email(msg:str):
	pass

async def send_order_telegram(msg:str):
	group_id = settings.telegram_notif_group_id
	bot = TelegramBot(username=settings.telegram_bot_username, access_token=settings.telegram_bot_token)
	bot.send_msg(group_id, msg)

async def send_order_admin_notification(order: BaseOrder):
	print('send admin notification run')
	msg = "🔥 *Новый заказ* ✨ \n"
	msg += f"{'-'*5} Информация по заказу {'-'*5} \n"
	msg += f"Дата создания: {order.date_created} \n"
	msg += f"Клиент: *{order.customer_username}* \n"
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
	msg += f"Скидка по промокоду: {order.cart.promo_discount_amount} \n"
	msg += f"Сумма заказа: *{order.cart.total_amount}* \n"
	msg += f"{'-'*5} Состав заказа {'-'*5} \n"
	for index, item in enumerate(order.cart.line_items):
		msg+= f"{index + 1}. {item.product.name} - {item.quantity} шт. \n"


	# replace for telegram
	msg = msg.replace('-', '\-').replace('.', '\.').replace('=', '\=').replace('(','\(').replace(')','\)')

	await send_order_telegram(msg=msg)
#	await send_order_email(msg=msg)
