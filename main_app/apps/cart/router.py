from fastapi import APIRouter, Depends, Request, Response, Body
from typing import Optional, List

from datetime import datetime, timedelta

from pymongo import ReturnDocument

# import config (env variables)
from config import settings

from .models import BaseCart, LineItem, LineItemUpdate, SessionId
from .cart_exceptions import CartAlreadyExist, CartNotExist, NotValidUUID

from apps.users.user import get_current_user
from apps.users.models import BaseUser, BaseUserDB
# from coupons app
from apps.coupons.coupon import get_coupon_by_id
from apps.coupons.models import BaseCoupon, BaseCouponDB

from bson import json_util

from .cart import  get_current_cart_active_by_id, get_cart_by_session_id




import uuid


# order exceptions

router = APIRouter(
	prefix = "/carts",
	tags = ["carts"],
	# responses ? 
)


def get_or_create_session(request: Request):
	if not "session_id" in request.session:
		request.session.update(
			{"session_id": str(uuid.uuid4())}
		)

@router.get("/{session_id}")
async def get_cart(
	request: Request,
	session_id: uuid.UUID
	):
#	print('request session is', request.session)
#	get_or_create_session(request)
#	print('session UUID is', uuid.UUID(request.session.get("session_id", None)))
	cart = get_cart_by_session_id(request.app.carts_db, session_id)
	return cart.dict()

@router.delete("/{cart_id}")
async def delete_cart(
	request: Request,
	cart_id: uuid.UUID,
	):
	deleted_count = request.app.carts_db.delete_one(
		{"_id": cart_id}
	).deleted_count
	if deleted_count == 0:
		raise CartNotExist
	return {
		"status": "success"
	}

@router.post("/{session_id}")
async def create_cart(
		request: Request,
		session_id: uuid.UUID,
		line_items: List[LineItem] = Body(..., embed=True),
		token: str = None,
	):
	"""
		Create a cart for currently logged in user
		---------------
		Exceptions:
		- line_items are empty or incorrect
	"""
	# check, if cart is already exist
	cart = BaseCart()
	exist_cart = request.app.carts_db.find_one(
		{"session_id": session_id}
	)
	# if cart exist, dont create it and raise excaption
	if exist_cart:
		raise CartAlreadyExist
	# cart not exist, add session_id
	cart.session_id = session_id
	for line_item in line_items:
		cart.add_line_item(request, line_item)
	# count cart amount 
	cart.count_amount()
	# add new cart to db
	request.app.carts_db.insert_one(
		cart.dict(by_alias=True)
	)
#	if token:
#		current_user = await get_current_user(request, token)
#		if current_user.is_active:
#			cart.user_id = current_user.id
#			print('current user is', current_user)

	# add cart to database
	return cart.dict()

# add line_items to cart
@router.post("/{cart_id}/items")
def add_cart_items(
		request: Request,
		cart_id: uuid.UUID,
		line_items: List[LineItem] = Body(..., embed=True),
		cart: BaseCart = Depends(get_current_cart_active_by_id)
	):
	"""
		Add line_items to the cart
	"""
	for line_item in line_items:
		cart.add_line_item(request, line_item)
	cart.count_amount()
	cart.update_db(request.app.carts_db)
	return cart.dict()

# update line item by id in cart
@router.patch("/{cart_id}/items/{item_id}")
def update_cart_item(
		request: Request,
		cart_id: uuid.UUID,
		item_id: uuid.UUID,
		line_item: LineItemUpdate = Body(..., embed=True),
		cart: BaseCart = Depends(get_current_cart_active_by_id)
	):
	cart.update_line_item(request.app.carts_db, item_id, line_item)
	cart.count_amount()
	cart.update_db(request.app.carts_db)
	return cart.dict()

# delete line item by id in cart 
@router.delete("/{cart_id}/items/{item_id}")
def delete_cart_item(
		request: Request,
		cart_id: uuid.UUID,
		item_id: uuid.UUID,
		cart: BaseCart = Depends(get_current_cart_active_by_id)
	):
	cart.remove_line_item(request.app.carts_db, item_id)
	cart.count_amount()
	cart.update_db(request.app.carts_db)
	return cart.dict()

# cart coupons
@router.post("/{cart_id}/coupons/add") # add coupon to cart
def add_cart_coupon(
	request: Request,
	coupon_code: str = Body(..., embed = True),
	cart: BaseCart = Depends(get_current_cart_active_by_id),
	current_user: BaseUser = Depends(get_current_user),
):
	coupon = get_coupon_by_id(request, coupon_code, db_model = True)
	# check, if user can apply coupon
	# check, coupon is enable and not expired
	cart.coupons = []
	cart.coupons.append(coupon)
	cart.update_db(request.app.carts_db)
	return cart.dict()

@router.post("/{cart_id}/coupons/remove") # remove coupon from cart
def remove_cart_coupon(
	request: Request,
	cart: BaseCart = Depends(get_current_cart_active_by_id),
):
	cart.coupons = []
	cart.update_db(request.app.carts_db)
	return cart
