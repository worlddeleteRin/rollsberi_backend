import uuid
from pymongo import ReturnDocument
from enum import Enum

from typing import Optional, List

from pydantic import UUID4, BaseModel, Field, validator
from datetime import datetime, date

from apps.products.models import BaseProduct
from apps.products.products import get_product_by_id

# from coupons app
from apps.coupons.models import BaseCoupon

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
	product: BaseProduct = None
	# variant_id: UUID4


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
	# sum of line-items amount, minus cart-level discounts and coupons.
	# Amount includes taxes, if needed
	total_amount: int = None # ? float?
	# list of coupons objects
	coupons: List[BaseCoupon] = None

	def count_amount(self):
		base = 0
		discount = 0
		total = 0
		# count base and discount amount
		for line_item in self.line_items:
			base += line_item.product.price * line_item.quantity
			if line_item.product.sale_price:
				discount += (line_item.product.price - line_item.product.sale_price) * line_item.quantity
		# count total amount 
		total = base - discount
		# assign to object vars
		self.base_amount = base
		self.discount_amount = discount
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
		print('updated cart is', updated_cart)

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

