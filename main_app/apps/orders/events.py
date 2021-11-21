from fastapi import BackgroundTasks

from .models import BaseOrder

from apps.notifications.new_order import send_order_admin_notification

from apps.users.user import get_user_by_id

from apps.orders.orders import get_user_total_spent_by_user_id


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
            # check and spend user bonuses, if they are used
            if order.cart.bonuses_used:
                user.bonuses -= order.cart.pay_with_bonuses
                user.update_db()
        

    # send order notifications
    background_tasks.add_task(send_order_admin_notification, order)

def order_completed_event(
    background_tasks: BackgroundTasks,
    order: BaseOrder,
):
    """
        Action, that will be done when order status is completed:
        if user attaches to the order:
            TODO - Need to charge user bonuses from order, if user attached to order
            TODO - Need to check user total spent and bonuses level
        3. 
    """
    print('run order completed event')
    if not order.cart:
        return
    # check, if user applied to order
    if order.customer_id:
        current_user = get_user_by_id(order.customer_id, silent = True) 
        if current_user:
            if order.cart.bonuses_to_apply:
                current_user.bonuses += order.cart.bonuses_to_apply
            total_spent = get_user_total_spent_by_user_id(order.customer_id)
            print('current user is', current_user)
            current_user.update_db()
            print('total spent is', total_spent)


