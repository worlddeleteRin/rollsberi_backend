from fastapi import APIRouter, Depends, Request, Body, BackgroundTasks
from typing import Optional, List

from datetime import datetime, timedelta

from pymongo import ReturnDocument

import uuid

# import config (env variables)
from config import settings

from .models import PickupAddress, StockItem, MenuLink, MainSliderItem, RequestCall

from .delivery_pickup import get_pickup_addresses
from apps.payments.payments import get_payment_methods
from apps.delivery.delivery import get_delivery_methods

from apps.users.user import get_current_admin_user

from apps.orders.models import order_statuses

from apps.notifications.call_request import send_call_request_admin_notification

from database.main_db import db_provider
# order exceptions

router = APIRouter(
    prefix = "/site",
    tags = ["site"],
)

@router.get("/order-statusses")
def get_order_statusses(
    admin_user = Depends(get_current_admin_user)
):
    return order_statuses

@router.get("/pickup-addresses",
# response_model = List[PickupAddress]
)
def pickup_addresses(
    ):
    pickup_addresses = get_pickup_addresses()
    return pickup_addresses

@router.post("/pickup-address")
def add_pickup_address(
    pickup_address: PickupAddress,
):
    pickup_address.save_db()
    return pickup_address.dict()


@router.get("/checkout-common-info")
def get_checkout_common_info(
):
    delivery_methods = get_delivery_methods()
    payment_methods = get_payment_methods()
    pickup_addresses = get_pickup_addresses()

    return {
        "delivery_methods": delivery_methods,
        "payment_methods": payment_methods,
        "pickup_addresses": pickup_addresses,
    }

@router.get('/common-info')
def get_common_info(
):
    menu_links_cursor = db_provider.menu_links_db.find({}).sort("display_order", 1)
    menu_links = [MenuLink(**menu_link).dict() for menu_link in menu_links_cursor]
    #print('menu links are', menu_links)
    location_address = "Здесь будет адрес доставки"
    delivery_phone = "+79781111111"
    delivery_phone_display = "7 978 111 11 11"
    main_logo_link = settings.base_static_url + "logo_variant.png"
    map_delivery_location_link = "https://yandex.ru/map-widget/v1/?um=constructor%3A9b116676061cfe4fdf22efc726567c5f21c243f18367e2b8a207accdae7e4786&amp;source=constructor"
    return {
        "main_logo_link": main_logo_link,
        "menu_links": menu_links,
        "location_address": location_address,
        "delivery_phone": delivery_phone,
        "delivery_phone_display": delivery_phone_display,
        "map_delivery_location_link": map_delivery_location_link,
    }

# get main sliders
@router.get("/main-sliders")
def get_main_sliders(
):
    main_sliders_cursor = db_provider.main_sliders_db.find({})
    main_sliders = [MainSliderItem(**slider).dict() for slider in main_sliders_cursor]
    return main_sliders


# get stocks
@router.get("/stocks")
def get_stocks(
):
    stocks_dict = db_provider.stocks_db.find({})
    stocks = [StockItem(**stock).dict() for stock in stocks_dict]
    return {
        "stocks": stocks,
    }
# add stock
@router.post("/stocks")
def create_stock(
    stock: StockItem,
):
    stock.save_db()
    return stock.dict()

@router.post("/request-call")
async def request_call(
    call_object: RequestCall,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(send_call_request_admin_notification, call_object)
    return {
        "success": True,
    }

