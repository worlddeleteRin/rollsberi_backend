from fastapi import APIRouter, Depends, Request, Body
from typing import Optional, List

from datetime import datetime, timedelta

from pymongo import ReturnDocument

import uuid

# import config (env variables)
from config import settings

from .models import PickupAddress, StockItem

from .delivery_pickup import get_pickup_addresses
from apps.payments.payments import get_payment_methods
from apps.delivery.delivery import get_delivery_methods

from apps.users.user import get_current_admin_user

from apps.orders.models import order_statuses

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

@router.get("/stocks")
def get_stocks(
):
	stocks_dict = db_provider.stocks_db.find({})
	stocks = [StockItem(**stock).dict() for stock in stocks_dict]
	return {
		"stocks": stocks,
	}
@router.post("/stocks")
def create_stock(
	stock: StockItem,
):
	stock.save_db()
	return stock.dict()
