from fastapi import FastAPI
import uuid
from pymongo import ReturnDocument
from enum import Enum

from typing import Optional, List

from pydantic import UUID4, BaseModel, Field
from datetime import datetime

from apps.products.models import BaseProduct
from apps.products.products import get_product_by_id

from apps.site.utils import get_time_now
# from coupons app
from apps.coupons.models import BaseCoupon, CouponTypeEnum

from apps.bonuses.bonuses import bonuses_levels

from .cart_exceptions import LineItemNotExist

from database.main_db import db_provider

from config import settings



class SessionId(BaseModel):
    id: UUID4

class BaseCartStatusEnum(str, Enum):
    pass


class LineItemUpdate(BaseModel):
    quantity: int

class LineItem(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    product_id: UUID4
    quantity: int = 1
    promo_price: Optional[int]
    product: Optional[BaseProduct]
    # variant_id: UUID4
    def get_base_price(self):
        if self.product:
            return self.product.price * self.quantity
    def get_price(self):
        if self.promo_price and self.promo_price > 0:
            return self.promo_price * self.quantity
        if self.product:
            return self.product.get_price() * self.quantity
        return 0
    def get_sale_discount(self):
        if self.product:
            if self.product.sale_price:
                return (self.product.price - self.product.sale_price) * self.quantity
        return 0
    def get_promo_discount(self):
        if self.product:
            if self.promo_price:
                return int(self.product.get_price() - self.promo_price) * self.quantity
        return 0
    def attach_product(self):
        product = get_product_by_id(self.product_id) 
        if product:
            self.product = product



class BaseCart(BaseModel):
    """ Base Cart Model """

    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    user_id: Optional[UUID4] = None
    session_id: Optional[UUID4] = None
    customer_id: Optional[UUID4] = None
    date_created: Optional[datetime] = Field(default_factory=get_time_now)
    date_modified: Optional[datetime] = Field(default_factory=get_time_now)
    line_items: List[LineItem] = []
    # if bonuses was used in cart
    bonuses_used: bool = False
    # pay with bonuses amount
    pay_with_bonuses: int = 0
    # amount values
    promo_amount: Optional[int] = None
    # cost of carts content before apply discounts
    base_amount: Optional[int] = None # ? or maybe float?
    # discounted amount (sum of products sale price)
    discount_amount: Optional[int] = None # ? float?
    # promo discount amount (coupons applied discount amount)
    promo_discount_amount: Optional[int] = None
    # sum of line-items amount, minus cart-level discounts and coupons.
    # Amount includes taxes, if needed
    total_amount: Optional[int] = None # ? float?
    # list of coupons objects
    coupons: List[BaseCoupon] = []
    # gift products
    coupon_gifts: List[BaseProduct] = []
    # bonuses to apply to the user
    bonuses_to_apply: Optional[int] = None

    def delete_coupons(self):
        for line_item in self.line_items:
            line_item.promo_price = None
        self.promo_discount_amount = None
        self.promo_amount = None
        self.coupons = []
        self.coupon_gifts = []

    def check_can_apply_coupons(self):
        cart_amount = 0
        coupon = self.coupons[0]
        can_use, msg = coupon.can_use()
        if not can_use:
            return can_use, msg
        # check cart amount, if can apply
        for line_item in self.line_items:
            cart_amount += line_item.get_price()
        if coupon.min_purchase > cart_amount:
            return False, "Промокод действует при заказе от "+ str(coupon.min_purchase) + " руб."
        if coupon.type in [CouponTypeEnum.per_item_discount, CouponTypeEnum.percentage_discount]:
            no_apply_msg = "В коризне нет товаров, к которым применим данный промокод"
            can_apply = 0
            for line_item in self.line_items:   
                if not line_item.product:
                    continue
                if not line_item.product_id in coupon.products_ids:
                    continue    
                if coupon.exclude_sale_items and line_item.product.sale_price:
                    continue    
                can_apply += 1
            if can_apply == 0:
                return False, no_apply_msg

        return True, ""

    def check_item_can_apply_coupon(self, item, coupon):
        if not item.product_id in coupon.products_ids:
            return False
        if coupon.exclude_sale_items and item.product.sale_price:
            return False
        return True

    def apply_coupons(self):
        can_apply, msg = self.check_can_apply_coupons()
        if not can_apply:
            self.delete_coupons()
            return False, msg
        promo_discount = 0
        coupon = self.coupons[0]
        # per item discount logic 
        if (coupon.type == CouponTypeEnum.per_item_discount):
            for line_item in self.line_items:
                item_can_apply = self.check_item_can_apply_coupon(line_item, coupon)
                if not item_can_apply:
                    continue
                if not line_item.product:
                    continue
                line_item.promo_price = line_item.product.get_price() - coupon.amount
                promo_discount += coupon.amount * line_item.quantity
            self.promo_discount_amount = promo_discount
        # per total discount logic
        if (coupon.type == CouponTypeEnum.per_total_discount):
            self.promo_amount = coupon.amount   
            self.promo_discount_amount = coupon.amount
        # percentage discount logic
        if (coupon.type == CouponTypeEnum.percentage_discount):
            for line_item in self.line_items:
                item_can_apply = self.check_item_can_apply_coupon(line_item, coupon)
                if not item_can_apply:
                    continue    
                if not line_item.product:
                    continue
                line_item.promo_price = line_item.product.get_price() - int((line_item.product.get_price() * coupon.amount) / 100 )
                promo_discount += int((line_item.product.get_price() * coupon.amount) / 100) * line_item.quantity
            self.promo_discount_amount = promo_discount
        # gift discount 
        if (coupon.type == CouponTypeEnum.gift):
            gift_products_dict = db_provider.products_db.find(
                {"_id": {"$in": coupon.products_ids}}
            )
            gift_products: List[BaseProduct] = [BaseProduct(**product) for product in gift_products_dict]
            self.coupon_gifts.clear()
            self.coupon_gifts += gift_products

    def count_bonuses_to_apply(
            self, 
            current_user = None
        ):
        if not self.total_amount or self.total_amount == 0:
            self.bonuses_to_apply = None
            return
        print('current user is', current_user)
        if current_user and current_user.bonuses_rank and current_user.bonuses_rank in bonuses_levels:
            current_bonuses_lvl = bonuses_levels[current_user.bonuses_rank]
            print('current user is here, bonuses lvl object is', current_bonuses_lvl)
            bonuses_percent = current_bonuses_lvl.cart_bonuses_percent
        else:
            bonuses_percent = settings.default_bonuses_percent
        self.bonuses_to_apply = int((self.total_amount * bonuses_percent) / 100)

    def count_amount(
            self,
            current_user = None,
        ):
        base = 0
        discount = 0
        promo_discount = 0
        total = 0
        # apply coupons, if they are exists

        if self.bonuses_used:
            self.check_can_pay_with_bonuses()
        if len(self.coupons) > 0:
            self.apply_coupons()
        # count base and discount amount
        for line_item in self.line_items:
            base += line_item.get_base_price()
            discount += line_item.get_sale_discount()
            promo_discount += line_item.get_promo_discount()
        # count total amount 
        total = base - discount - promo_discount
        if self.bonuses_used and self.pay_with_bonuses:
            total -= self.pay_with_bonuses
        if self.promo_amount and self.promo_amount > 0:
            total -= self.promo_amount
        # assign to object vars
        self.base_amount = base
        self.discount_amount = discount
        #self.promo_discount_amount = promo_discount
        self.total_amount = total
        # count bonuses to apply
        self.count_bonuses_to_apply(current_user = current_user)


    def delete_db(self):
        db_provider.carts_db.delete_one(
            {"_id": self.id}
        )

    def update_db(self):
        # maybe need improvement to recast object with updated_cart return info
        updated_cart = db_provider.carts_db.find_one_and_update(
            {"_id": self.id},
            {"$set": self.dict(by_alias=True)},
            return_document=ReturnDocument.AFTER
        )
        return updated_cart

    def check_line_item_exists(self, line_item_id):
        for line_item in self.line_items:
            if line_item.id == line_item_id:
                return True, line_item
        return False, None
    def check_product_in_cart_exists(self, new_line_item):
        for line_item in self.line_items:
            if line_item.product_id == new_line_item.product_id:
                return True, line_item
        return False, None

    def check_can_pay_with_bonuses(self):
        if not self.pay_with_bonuses or self.pay_with_bonuses == 0 or not self.total_amount:
            self.pay_with_bonuses = 0
            self.bonuses_used = False
            return False, "Неверное значение бонусов"
        if self.pay_with_bonuses > int(self.total_amount * 0.5):
            self.pay_with_bonuses = 0
            self.bonuses_used = False
            return False, "Бонусами можно оплатить до 50% стоимости заказа"
        return True, ""

    def add_line_item(self, line_item):
        line_item_exists, exist_line_item = self.check_product_in_cart_exists(line_item)
        if line_item_exists and exist_line_item:
            # line_item already exists in cart, need to add quantity
            exist_line_item.quantity += 1
            return
        # line item not exists in cart, need to add it
        product = get_product_by_id(line_item.product_id)
        # add product to the current line_item
        line_item.product = product
        self.line_items.append(line_item)

    def remove_line_item_quantity(self, line_item_id):
        line_item_exists, line_item = self.check_line_item_exists(line_item_id)
        if line_item_exists and line_item:
            if line_item.quantity == 1:
                self.line_items.remove(line_item)
                return
            else:
                line_item.quantity -= 1
                return
        # line item not exist, raise Exception
        raise LineItemNotExist

    def remove_line_item(self, line_item_id):
        line_item_exists, line_item = self.check_line_item_exists(line_item_id)
        if line_item_exists and line_item:
            self.line_items.remove(line_item)
            return
        # line item not exist, raise Exception
        raise LineItemNotExist
    def update_line_item(self, line_item_id: UUID4, new_line_item: LineItemUpdate):
        line_item_exists, line_item = self.check_line_item_exists(line_item_id)
        if not line_item_exists:
            raise LineItemNotExist
        if line_item:
            line_item.__dict__.update(**new_line_item.dict())
            if line_item.quantity < 1:
                self.line_items.remove(line_item)

    def set_modified(self):
        self.date_modified = get_time_now()

