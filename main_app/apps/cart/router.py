from fastapi import APIRouter, Depends, Request, Response, Body, HTTPException
from typing import Optional, List

from datetime import datetime, timedelta

from pymongo import ReturnDocument

# import config (env variables)
from config import settings

from .models import BaseCart, LineItem, LineItemUpdate, SessionId
from .cart_exceptions import CartAlreadyExist, CartNotExist, NotValidUUID

from apps.users.user import get_current_user, get_current_user_silent
from apps.users.models import BaseUser, BaseUserDB
# from coupons app
from apps.coupons.coupon import get_coupon_by_id
from apps.coupons.models import BaseCoupon, BaseCouponDB

from bson import json_util

from .cart import  get_current_cart_active_by_id, get_cart_by_session_id

from database.main_db import db_provider



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
    session_id: uuid.UUID
    ):
#   print('request session is', request.session)
#   get_or_create_session(request)
#   print('session UUID is', uuid.UUID(request.session.get("session_id", None)))
    cart = get_cart_by_session_id(session_id)
    if cart:
        return cart.dict()

@router.delete("/{cart_id}")
async def delete_cart(
    cart_id: uuid.UUID,
    ):
    deleted_count = db_provider.carts_db.delete_one(
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
        # token: str = None,
        current_user = Depends(get_current_user_silent)
    ):
    """
        Create a cart for currently logged in user
        ---------------
        Exceptions:
        - line_items are empty or incorrect
    """
    """
    try to get current user, if user looged in and pass credentials
    in headers
    """
    # check, if cart is already exist
    cart = BaseCart()
    exist_cart_dict = db_provider.carts_db.find_one(
        {"session_id": session_id}
    )
    # if cart exist, dont create it and raise excaption
    if exist_cart_dict:
        # exist_cart = BaseCart(**exist_cart_dict)
        # exist_cart.delete_db()
        # cart = BaseCart()
        raise CartAlreadyExist
    # cart not exist, add session_id
    cart.session_id = session_id
    for line_item in line_items:
        cart.add_line_item(line_item)
    # count cart amount 
    cart.count_amount(current_user = current_user)
    # add new cart to db
    db_provider.carts_db.insert_one(
        cart.dict(by_alias=True)
    )
#   if token:
#       current_user = await get_current_user(request, token)
#       if current_user.is_active:
#           cart.user_id = current_user.id
#           print('current user is', current_user)

    # add cart to database
    return cart.dict()

# add line_items to cart
@router.post("/{cart_id}/items")
async def add_cart_items(
        cart_id: uuid.UUID,
        line_items: List[LineItem] = Body(..., embed=True),
        cart: BaseCart = Depends(get_current_cart_active_by_id),
        current_user = Depends(get_current_user_silent),
    ):
    """
        Add line_items to the cart
    """

    for line_item in line_items:
        cart.add_line_item(line_item)
    cart.count_amount(current_user = current_user)
    cart.update_db()
    return cart.dict()

# update line item by id in cart
@router.patch("/{cart_id}/items/{item_id}")
async def update_cart_item(
        request: Request,
        cart_id: uuid.UUID,
        item_id: uuid.UUID,
        line_item: LineItemUpdate = Body(..., embed=True),
        cart: BaseCart = Depends(get_current_cart_active_by_id),
        current_user = Depends(get_current_user_silent),
    ):
    print('run update cart item, current user is', current_user)

    cart.update_line_item(item_id, line_item)
    cart.count_amount(current_user = current_user)
    cart.update_db()
    return cart.dict()

# delete line item by id in cart 
@router.delete("/{cart_id}/items/{item_id}")
async def delete_cart_item(
        cart_id: uuid.UUID,
        item_id: uuid.UUID,
        cart: BaseCart = Depends(get_current_cart_active_by_id),
        current_user = Depends(get_current_user_silent)
    ):
    cart.remove_line_item(item_id)
    cart.count_amount(current_user = current_user)
    cart.update_db()
    return cart.dict()

# cart coupons
@router.post("/{cart_id}/coupons/add") # add coupon to cart
def add_cart_coupon(
    coupon_code: str = Body(..., embed = True),
    cart: BaseCart = Depends(get_current_cart_active_by_id),
    current_user: BaseUser = Depends(get_current_user),
):
    coupon = get_coupon_by_id(coupon_code = coupon_code, db_model = True)
    if not coupon:
        return None
    # check, if user can apply coupon
    # check, coupon is enable and not expired
    is_active: bool = coupon.check_active() 
    if not is_active:
        return {
            "is_success": False,
            "msg": "Промокод не активный",
        }
    cart.coupons = []
    cart_coupon: BaseCoupon = BaseCoupon(**coupon.dict())
    # add coupon to current cart
    cart.coupons.append(cart_coupon)
    # check, if coupon can be applied
    can_apply, msg = cart.check_can_apply_coupons()
    if not can_apply:
        return {
            "is_success": False,
            "msg": msg,
        }
    # count cart amount to apply coupon
    cart.count_amount(current_user = current_user)

    cart.update_db()
    return {
        "is_success": True,
        "msg": "Промокод успешно применен",
        "cart": cart.dict(),
    }

@router.post("/{cart_id}/coupons/remove") # remove coupon from cart
async def remove_cart_coupon(
    cart: BaseCart = Depends(get_current_cart_active_by_id),
    current_user = Depends(get_current_user_silent),
):

    cart.delete_coupons()
    cart.count_amount(current_user = current_user)
    cart.update_db()
    return cart.dict()

# pay with bonuses logic
@router.post("/{cart_id}/pay-bonuses")
async def add_pay_bonuses(
    cart: BaseCart = Depends(get_current_cart_active_by_id),
    current_user = Depends(get_current_user),
    pay_with_bonuses: int = Body(..., embed = True),
):
    if cart.bonuses_used:
        cart.bonuses_used = False
        cart.pay_with_bonuses = 0
        cart.count_amount()

    cart.pay_with_bonuses = pay_with_bonuses
    cart.bonuses_used = True
    can_pay, msg = cart.check_can_pay_with_bonuses()
    if not can_pay:
        raise HTTPException(status_code = 400, detail=msg)

    cart.count_amount(current_user = current_user)
    cart.update_db()

    print(pay_with_bonuses)
    return cart.dict()

@router.delete("/{cart_id}/pay-bonuses")
async def add_pay_bonuses(
    cart: BaseCart = Depends(get_current_cart_active_by_id),
    current_user = Depends(get_current_user),
):
    cart.bonuses_used = False
    cart.pay_with_bonuses = 0
    cart.count_amount()
    cart.update_db()

    return cart.dict()
