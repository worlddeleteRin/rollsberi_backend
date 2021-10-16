from fastapi import FastAPI
import uuid
from pymongo import ReturnDocument
from enum import Enum

from typing import Optional, List

from pydantic import UUID4, BaseModel, Field, validator
from datetime import datetime, date

from apps.products.models import BaseProduct
from apps.products.products import get_product_by_id

# from coupons app
from apps.coupons.models import BaseCoupon, BaseCouponDB, CouponTypeEnum

from .cart_exceptions import LineItemNotExist


class SessionId(BaseModel):
	id: UUID4

class BaseCartStatusEnum(str, Enum):
	pass


class LineItemUpdate(BaseModel):
	quantity: int

class LineItem(BaseModel):
	id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
	product_id: UUID4
	quantity: int
	promo_price: int = None
	product: BaseProduct = None
	# variant_id: UUID4
	def get_price(self):
		if self.promo_price and self.promo_price > 0:
			return self.promo_price * self.quantity
		return self.product.get_price() * self.quantity
	def get_sale_price(self):
		if self.product.sale_price:
			return self.product.sale_price * self.quantity
		return 0
	def get_promo_price(self):
		if self.promo_price:
			return self.promo_price * self.quantity
		return 0


class BaseCart(BaseModel):
	""" Base Cart Model """
	id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
	user_id: UUID4 = None
	session_id: UUID4 = None
	customer_id: UUID4 = None
	date_created: Optional[datetime] = Field(default_factory=datetime.utcnow)
	date_modified: Optional[datetime] = Field(default_factory=datetime.utcnow)
	line_items: List[LineItem] = []
	# amount values
	# cost of carts content before apply discounts
	base_amount: int = None # ? or maybe float?
	# discounted amount
	discount_amount: int = None # ? float?
	# promo discount amount
	promo_discount_amount: int = None
	# sum of line-items amount, minus cart-level discounts and coupons.
	# Amount includes taxes, if needed
	total_amount: int = None # ? float?
	# list of coupons objects
	coupons: List[BaseCoupon] = []

	def delete_coupons(self):
		for line_item in self.line_items:
			line_item.promo_price = None
		self.promo_discount_amount = None
		self.coupons = []

	def apply_coupons(self, app: FastAPI):
		print('run apply coupons')
		promo_discount = 0
		coupon = self.coupons[0]
		if (coupon.type == CouponTypeEnum.per_item_discount):
			# per item discount logic 
			for line_item in self.line_items:
				if not line_item.product_id in coupon.products_ids:
					continue	
				if coupon.exclude_sale_items and line_item.product.sale_price:
					continue	
				line_item.promo_price = line_item.product.get_price() - coupon.amount
				promo_discount += coupon.amount * line_item.quantity
			self.promo_discount_amount = promo_discount
		if (coupon.type == CouponTypeEnum.per_total_discount):
			pass
			# per total discount logic
		if (coupon.type == CouponTypeEnum.percentage_discount):
			pass
			# percentage discount logic

	def count_amount(self, app: FastAPI):
		base = 0
		discount = 0
		promo_discount = 0
		total = 0
		# apply coupons, if they are exists
		if len(self.coupons) > 0:
			self.apply_coupons(app)
		# count base and discount amount
		for line_item in self.line_items:
			base += line_item.get_price()
			discount += line_item.get_sale_price()
			#promo_discount += line_item.get_promo_price()
		# count total amount 
		total = base
		# assign to object vars
		self.base_amount = base
		self.discount_amount = discount
		#self.promo_discount_amount = promo_discount
		self.total_amount = total


	def delete_db(self, carts_db):
		carts_db.delete_one(
			{"_id": self.id}
		)

	def update_db(self, carts_db):
		# maybe need improvement to recast object with updated_cart return info
		updated_cart = carts_db.find_one_and_update(
			{"_id": self.id},
			{"$set": self.dict(by_alias=True)},
			return_document=ReturnDocument.AFTER
		)

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

	def add_line_item(self, request, line_item):
		line_item_exists, exist_line_item = self.check_product_in_cart_exists(line_item)
		if line_item_exists:
			print('line item already exists, add quantity')
			# line_item already exists in cart, need to add quantity
			exist_line_item.quantity += 1
			return
		print('line item not exist, add it')
		# line item not exists in cart, need to add it
		product = get_product_by_id(request.app.products_db, line_item.product_id)
		# add product to the current line_item
		line_item.product = product
		self.line_items.append(line_item)

	def remove_line_item_quantity(self, carts_db, line_item_id):
		line_item_exists, line_item = self.check_line_item_exists(line_item_id)
		if line_item_exists:
			if line_item.quantity == 1:
				self.line_items.remove(line_item)
				return
			else:
				line_item.quantity -= 1
				return
			self.line_items.remove(line_item)
			return
		# line item not exist, raise Exception
		raise LineItemNotExist

	def remove_line_item(self, carts_db, line_item_id):
		line_item_exists, line_item = self.check_line_item_exists(line_item_id)
		if line_item_exists:
#			print('line item exist, need to delete it')
#			print('line item is', line_item)
			self.line_items.remove(line_item)
			return
		# line item not exist, raise Exception
		raise LineItemNotExist
	def update_line_item(self, carts_db, line_item_id: str, new_line_item: LineItemUpdate):
		line_item_exists, line_item = self.check_line_item_exists(line_item_id)
		if not line_item_exists:
			raise LineItemNotExist
		line_item.__dict__.update(**new_line_item.dict())
		if line_item.quantity < 1:
			self.line_items.remove(line_item)

	def set_modified(self):
		self.date_modified = datetime.utcnow()

