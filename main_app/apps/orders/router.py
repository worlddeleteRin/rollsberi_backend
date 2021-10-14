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

from .models import BaseOrder, BaseOrderCreate, BaseOrderUpdate
from .orders import get_order_by_id, new_order_object, get_orders_db

from apps.cart.cart import delete_session_cart

# imprort send order notifications
from apps.notifications.new_order import send_order_admin_notification



# order exceptions

router = APIRouter(
	prefix = "/orders",
	tags = ["orders"],
	# responses ? 
)


# test routes

# eof test routes
@router.get("/")
def get_orders(
	request: Request,
	admin_user = Depends(get_current_admin_user),
	per_page: int = 8,
	page: int = 1,
):
	print('page is', page)
	orders = get_orders_db(
		request,
		per_page = per_page,
		page = page,
	)
	pages_count = int(request.app.orders_db.count_documents({}) / per_page)
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
	request: Request,
	new_order: BaseOrderCreate,
	current_user: BaseUser = Depends(get_current_active_user)
	):
	order: BaseOrder = new_order_object(request, new_order)
	for line_item in order.line_items:
		if line_item.product == None:
			order.add_line_item(request, line_item)

	order.count_amount()
	order.save_db(request.app.orders_db)

	if new_order.customer_session_id:
		delete_session_cart(request.app.carts_db, new_order.customer_session_id)
	return order.dict()

# creates order from admin
@router.post("/admin")
def create_admin_order(
	request: Request,
	new_order: BaseOrderCreate,
	background_task: BackgroundTasks,
	admin_user: BaseUser = Depends(get_current_admin_user),
	):
	print('current user is', admin_user)
	print('new order is', new_order)
	order: BaseOrder = new_order_object(request, new_order)
	print('order time is', order.date_created)
	if new_order.customer_id:
		order.customer_id = new_order.customer_id
	# add products line_items to order
	for line_item in order.line_items:
		if line_item.product == None:
			order.add_line_item(request, line_item)
	# count order amounts
	order.check_set_user(request.app)
	order.count_amount()
	# save order to db
	order.save_db(request.app.orders_db)
	# delete cart by session_id, if it is exist
	if new_order.customer_session_id:
		delete_session_cart(request.app.carts_db, new_order.customer_session_id)

	# send notification about order creation
	background_task.add_task(send_order_admin_notification, order)


	return order.dict()

# get current order
@router.get("/{order_id}")
def get_order(
	request: Request,
	order_id: uuid.UUID
	):
	order = get_order_by_id(request.app.orders_db, order_id)
	return {
		'order': order.dict()
	}

# delete current order
# only for admin
@router.delete("/{order_id}")
def delete_order(
	request: Request,
	order_id: uuid.UUID,
	admin_user = Depends(get_current_admin_user),
	):
	order = get_order_by_id(request.app.orders_db, order_id)
	order.delete_db(request.app.orders_db)
	return {
		"status": "success",
	}

@router.patch("/{order_id}")
def update_order(
	request: Request,
	order_id: uuid.UUID,
	update_order: BaseOrderUpdate,
):
	order = get_order_by_id(request.app.orders_db, order_id)
	update_order.set_status()
	to_update = update_order.dict(exclude_unset=True)
	order = order.copy(update=to_update)
	updated_order = order.update_db(request.app.orders_db)
	return updated_order.dict()

@router.post("/")
def create_order(
	request: Request,
	new_order: BaseOrderCreate,
	# background task
	background_task: BackgroundTasks,
	current_user: BaseUser = Depends(get_current_active_user)
	):
	print('current user is', current_user)
	print('new order is', new_order)
	order: BaseOrder = new_order_object(request, new_order)
	print('order time is', order.date_created)
	# add products line_items to order
	for line_item in order.line_items:
		if line_item.product == None:
			order.add_line_item(request, line_item)
	# assign user to order, if user is simple user
	order.customer_id = current_user.id
	order.customer_username = current_user.username
	# add login to assign customer_id to passed customer_id to BaseOrderCreated, if user if admin,
	# and admin specifies the user, that need to be assigned to the order
	# count order amounts
	order.count_amount()
	# save order to db
	order.save_db(request.app.orders_db)

	# delete cart by session_id, if it is exist
	if new_order.customer_session_id:
		delete_session_cart(request.app.carts_db, new_order.customer_session_id)
	# delet cart by session_id, if it is exist
	# delete cart by cart_id, if it is specified in request
#	if order.cart_id:
#		cart = get_cart_by_id(request, order.cart_id, silent=True)
#		if cart:
#			cart.delete_db()
	# add background task to send order notification
	background_task.add_task(send_order_admin_notification, order)

	return order.dict()

