from fastapi import BackgroundTasks

from .models import BaseOrder

from apps.notifications.new_order import send_order_admin_notification

from apps.users.user import get_user_by_id


def order_created_event(
    background_tasks: BackgroundTasks,
    order: BaseOrder,
):
    # user actions after order created
    if not order.cart:
        return
    if order.customer_id:
        user = get_user_by_id(user_id = order.customer_id, silent = True)
        print('user is', user)
        if user:
            if order.cart.bonuses_used:
                user.bonuses -= order.cart.pay_with_bonuses
                user.update_db()
    # need to check and spend user bonuses, if they are used
        

    # send order notifications
    background_tasks.add_task(send_order_admin_notification, order)
