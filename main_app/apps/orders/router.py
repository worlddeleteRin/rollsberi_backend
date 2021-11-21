from fastapi import APIRouter, BackgroundTasks, Depends, Request, Body
from typing import Optional, List


from datetime import datetime, timedelta

from pymongo import ReturnDocument

import uuid

# import config (env variables)
from config import settings

# helper methods from user app 
from apps.users.user import get_current_active_user, get_current_admin_user
from apps.users.models import BaseUser

from .models import BaseOrder, BaseOrderCreate, BaseOrderUpdate, OrderStatusEnum
from .orders import get_order_by_id, new_order_object, get_orders_db

from .events import order_created_event, order_completed_event

from apps.cart.cart import delete_session_cart

# imprort send order notifications
from apps.notifications.new_order import send_order_admin_notification

from database.main_db import db_provider

import math



# order exceptions
from .order_exceptions import OrderNotEditable

router = APIRouter(
    prefix = "/orders",
    tags = ["orders"],
    # responses ? 
)


# test routes

# eof test routes
@router.get("/")
def get_orders(
    admin_user = Depends(get_current_admin_user),
    per_page: int = 8,
    page: int = 1,
):
    print('page is', page)
    orders = get_orders_db(
        per_page = per_page,
        page = page,
    )
    pages_count = int(
        math.ceil(db_provider.orders_db.count_documents({}) / per_page)
    )
    return {
        'info': {
            'count': orders.__len__(),
            'current_page': page,
            'pages_count': pages_count,
        },
        'orders': orders,
    }

# creates guest order
@router.post("/guest")
def create_guest_order(
    new_order: BaseOrderCreate,
    current_user: BaseUser = Depends(get_current_active_user)
    ):
    order: BaseOrder = new_order_object(new_order)
    if order.cart and order.cart.line_items:
        for line_item in order.cart.line_items:
            if line_item.product == None:
                order.cart.add_line_item(line_item)
    if order.cart:
        order.cart.count_amount()
        order.save_db()

    if new_order.customer_session_id:
        delete_session_cart(new_order.customer_session_id)
    return order.dict()

# creates order from admin
@router.post("/admin")
def create_admin_order(
    new_order: BaseOrderCreate,
    background_tasks: BackgroundTasks,
    admin_user: BaseUser = Depends(get_current_admin_user),
    ):
    order: BaseOrder = new_order_object(new_order)
    if new_order.customer_id:
        order.customer_id = new_order.customer_id
    # add products line_items to order
    if not order.cart:
        raise
    for line_item in order.cart.line_items:
        if line_item.product == None:
            order.cart.add_line_item(line_item)
    # count order amounts
    order.check_set_user()
    order.cart.count_amount()
    # save order to db
    order.save_db()
    # delete cart by session_id, if it is exist
    if new_order.customer_session_id:
        delete_session_cart(new_order.customer_session_id)

    # send notification about order creation
    order_created_event(background_tasks, order)
    # background_task.add_task(send_order_admin_notification, order)

    return order.dict()

# get current order
@router.get("/{order_id}")
def get_order(
    order_id: uuid.UUID
    ):
    order = get_order_by_id(order_id)
    return {
        'order': order.dict()
    }

# delete current order
# only for admin
@router.delete("/{order_id}")
def delete_order(
    order_id: uuid.UUID,
    admin_user = Depends(get_current_admin_user),
    ):
    order = get_order_by_id(order_id)
    order.delete_db()
    return {
        "status": "success",
    }

@router.patch("/{order_id}")
def update_order(
    order_id: uuid.UUID,
    update_order: BaseOrderUpdate,
    background_tasks: BackgroundTasks,
    admin_user = Depends(get_current_admin_user),
):
    order = get_order_by_id(order_id)
    can_edit = order.check_can_edit()
    print('can edit order', can_edit)
    if not can_edit:
        raise OrderNotEditable
    update_order.set_status()
    to_update = update_order.dict(exclude_unset=True)
    order = order.copy(update=to_update)
    updated_order = order.update_db()
    # run order completed event, if status is completed
    print('updated order is', updated_order)
    if updated_order.status.id == OrderStatusEnum.completed:
        order_completed_event(
            background_tasks = background_tasks,
            order = updated_order 
        )
    return updated_order.dict()

@router.post("/")
async def create_order(
    request: Request,
    new_order: BaseOrderCreate,
    # background task
    background_tasks: BackgroundTasks,
    current_user: BaseUser = Depends(get_current_active_user)
    ):
    order: BaseOrder = new_order_object(new_order)
    # add products line_items to order
    if not order.cart:
        raise
    for line_item in order.cart.line_items:
        if line_item.product == None:
            line_item.attach_product()
    # assign user to order, if user is simple user
    order.customer_id = current_user.id
    order.customer_username = current_user.username
    # add customer ip addresss to order
    order.customer_ip_address = request.client.host
    # add login to assign customer_id to passed customer_id to BaseOrderCreated, if user if admin,
    # and admin specifies the user, that need to be assigned to the order
    # count order amounts
    order.cart.count_amount()
    # save order to db
    order.save_db()

    # delete cart by session_id, if it is exist
    if new_order.customer_session_id:
        delete_session_cart(new_order.customer_session_id)
    # delet cart by session_id, if it is exist
    # delete cart by cart_id, if it is specified in request
#   if order.cart_id:
#       cart = get_cart_by_id(request, order.cart_id, silent=True)
#       if cart:
#           cart.delete_db()
    # add background task to send order notification
    order_created_event(background_tasks, order)
    # background_tasks.add_task(send_order_admin_notification, order)

    order.dict()

