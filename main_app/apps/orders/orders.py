from fastapi import Depends, Request
from .models import BaseOrder, BaseOrderCreate
from .order_exceptions import OrderNotExist
import uuid
from config import settings
from pydantic import UUID4
import pymongo


# from apps.users.models import UserDeliveryAddress
from apps.payments.payments import get_payment_method_by_id
from apps.delivery.delivery import get_delivery_method_by_id
from apps.site.delivery_pickup import get_pickup_address_by_id
from apps.users.user import get_user_delivery_address_by_id
from apps.cart.cart import get_cart_by_id, get_cart_by_session_id
from apps.cart.models import BaseCart

from database.main_db import db_provider



def get_order_by_id(order_id: uuid.UUID, link_products: bool = True) -> BaseOrder:
    order = db_provider.orders_db.find_one(
        {"_id": order_id}
    )
    if not order:
        raise OrderNotExist
    order = BaseOrder(**order)
    return order

def new_order_object(new_order: BaseOrderCreate):
    exclude_fields = {"delivery_method", "payment_method", "delivery_address", "pickup_address"}
    order = BaseOrder(**new_order.dict(exclude=exclude_fields))
    order.payment_method = get_payment_method_by_id(new_order.payment_method)
    order.delivery_method = get_delivery_method_by_id(new_order.delivery_method)
    if new_order.cart_id:
        cart = get_cart_by_id(new_order.cart_id)
        order.cart = cart
    elif new_order.customer_session_id:
        cart = get_cart_by_session_id(new_order.customer_session_id)
        if cart:
            order.cart = cart
    elif new_order.line_items:
        cart = BaseCart()
        cart.line_items = new_order.line_items
        order.cart = cart
    if new_order.delivery_address:
        order.delivery_address = get_user_delivery_address_by_id(new_order.delivery_address)
    if new_order.pickup_address:
        order.pickup_address = get_pickup_address_by_id(new_order.pickup_address)
    return order

def get_orders_by_user_id(user_id: UUID4):
    user_orders_dict = db_provider.orders_db.find(
        {"customer_id": user_id}
    ).sort("date_created", -1)
    if user_orders_dict.count() == 0:
        return []
    user_orders = [BaseOrder(**order).dict() for order in user_orders_dict]
    return user_orders

def get_user_total_spent_by_user_id(user_id: UUID4):
    aggregate_query = [{
        "$group": {
            "_id": None,
            "total_spent": {
                "$sum": "$cart.total_amount"
            }
        }
    }]
    query_dict = list(db_provider.orders_db.aggregate(
        aggregate_query
    ))[0]
    return query_dict["total_spent"]

def get_orders_db(
    per_page: int = 10,
    page: int = 1,
    include_user: bool = True,
):
    join_customer = {"$lookup": {
            "from": "users",
            "localField": "customer_id",
            "foreignField": "_id",
            "as": "customer"
        }}
#   limit_orders = { "$limit": 1}
#   skip_orders = {"$skip": (page-1) * per_page}

    print('per page is', per_page)

    orders_dict = db_provider.orders_db.find(
    {}
    ).sort("date_created", -1).skip((page-1) * per_page).limit(per_page)

    orders = [BaseOrder(**order).dict() for order in orders_dict]
    return orders

