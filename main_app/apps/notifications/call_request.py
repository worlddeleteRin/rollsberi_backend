# import time
from config import settings
###
from apps.site.models import RequestCall

from .models import TelegramBot


def send_call_request_telegram(msg:str):
    print('msg is', msg)
    group_id = settings.telegram_notif_group_id
    bot = TelegramBot(username=settings.telegram_bot_username, access_token=settings.telegram_bot_token)
    bot.send_msg(group_id, msg)

def send_call_request_admin_notification(call_request: RequestCall):
    print('start admin call request notif')
    msg = "🔥 *Заявка на обратный звонок* ✨ \n"

    msg += f"Имя клиента: {call_request.name} \n"
    msg += f"Телефон клиента: {call_request.phone_mask} \n"
    msg += f"Телефон клиента (чистый): {call_request.phone} \n"

    # replace for telegram
    msg = msg.replace('-', '\-').replace('.', '\.').replace('=', '\=').replace('(','\(').replace(')','\)').replace('+', '\+')

    send_call_request_telegram(msg=msg)
#   await send_order_email(msg=msg)
