from fastapi import Depends, Request
from .models import BaseCart, LineItem, SessionId
from .cart_exceptions import CartAlreadyExist, CartNotExist, NotValidUUID
import uuid
from config import settings

from .jwt_session import create_session_token, decode_token

from pydantic import UUID4

from database.main_db import db_provider


def create_session_id():
    session_token = uuid.uuid4()
#   session_token_expires = timedelta(minutes=settings.JWT_SESSION_TOKEN_EXPIRE_MINUTES)
#   session_token = create_session_token(
#       data = {"sub": uuid.uuid4()}, expires_delta=session_token_expires,
#       JWT_SESSION_KEY = settings.JWT_SESSION_KEY, JWT_ALGORITHM = settings.JWT_ALGORITHM
#   )
    return session_token

def get_cart_by_session_id( session_id: uuid.UUID, silent=False):
    cart = db_provider.carts_db.find_one(
        {"session_id": session_id}
    )
    if not cart:
        if not silent:
            raise CartNotExist
        return None
    cart = BaseCart(**cart)
    return cart


def get_cart_by_id(cart_id: uuid.UUID, link_products: bool = True, silent: bool = False):
#   print('cart id is', cart_id)
    cart = db_provider.carts_db.find_one(
        {"_id": cart_id}
    )
#   print('cart is', cart)
    if not cart:
        if not silent:
            raise CartNotExist
        return None
    cart = BaseCart(**cart)
    return cart


def get_current_cart_active_by_id(cart: BaseCart = Depends(get_cart_by_id)):
    return cart

def delete_session_cart(session_id: UUID4):
        cart = get_cart_by_session_id(session_id, silent=True)
        if cart:
            cart.delete_db()
