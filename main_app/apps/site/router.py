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

# order exceptions

router = APIRouter(
	prefix = "/site",
	tags = ["site"],
)

@router.get("/order-statusses")
def get_order_statusses(
	request: Request,
	admin_user = Depends(get_current_admin_user)
):
	return order_statuses

@router.get("/pickup-addresses",
# response_model = List[PickupAddress]
)
def pickup_addresses(
	request: Request,
	):
	pickup_addresses = get_pickup_addresses(request.app.pickup_addresses_db)
	return pickup_addresses

@router.post("/pickup-address")
def add_pickup_address(
	request: Request,
	pickup_address: PickupAddress,
):
	pickup_address.save_db(request.app.pickup_addresses_db)
	return pickup_address.dict()


@router.get("/checkout-common-info")
def get_checkout_common_info(
	request: Request,
):
	delivery_methods = get_delivery_methods(request.app.delivery_methods_db)
	payment_methods = get_payment_methods(request.app.payment_methods_db)
	pickup_addresses = get_pickup_addresses(request.app.pickup_addresses_db)

	return {
		"delivery_methods": delivery_methods,
		"payment_methods": payment_methods,
		"pickup_addresses": pickup_addresses,
	}

@router.get("/stocks")
def get_stocks(
	request: Request
):
	stocks_dict = request.app.stocks_db.find({})
	stocks = [StockItem(**stock).dict() for stock in stocks_dict]
	return {
		"stocks": stocks,
	}
@router.post("/stocks")
def create_stock(
	request: Request,
	stock: StockItem,
):
	stock.save_db(request.app.stocks_db)
	return stock.dict()
