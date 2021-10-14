import uuid
from pymongo import ReturnDocument
from enum import Enum

from typing import Optional, List

from pydantic import UUID4, BaseModel, Field, validator
from datetime import datetime, date

from apps.products.models import BaseProduct
from apps.products.products import get_product_by_id

from .order_exceptions import OrderNotExist

# import line items from cart app
from apps.cart.models import LineItem, LineItemUpdate
# import UserDeliveryAddress from users app
from apps.users.models import UserDeliveryAddress
from apps.users.user import get_user_by_id

from apps.payments.models import PaymentMethod
from apps.delivery.models import DeliveryMethod
from apps.site.models import PickupAddress


class OrderStatus(BaseModel):
	id: str
	name: str
	name_display: str
	color: str = "black"

awaiting_confirmation = OrderStatus(
	id = "awaiting_confirmation",
	name = "На подтверждении",
	name_display = "На подтверждении",
	color = "orange",
)
awaiting_cooking = OrderStatus(
	id = "awaiting_cooking",
	name = "Заказ готовится",
	name_display = "Заказ готовится",
	color="blue"
)
awaiting_payment = OrderStatus(
	id = "awaiting_payment",
	name = "Ожидание оплаты",
	name_display = "Ожидание оплаты",
)
awaiting_shipment = OrderStatus(
	id = "awaiting_shipment",
	name = "Ожидание доставки",
	name_display = "Ожидание доставки",
)
in_progress = OrderStatus(
	id = "in_progress",
	name = "В процессе",
	name_display = "В процессе",
)
completed = OrderStatus(
	id = "completed",
	name = "Завершен",
	name_display = "Завершен",
	color = "green"
)
cancelled = OrderStatus(
	id = "cancelled",
	name = "Отменен",
	name_display = "Отменен",
	color="red"
)

order_statuses = {
	"awaiting_confirmation": awaiting_confirmation,
	"awaiting_cooking": awaiting_cooking,
	"awaiting_payment": awaiting_payment,
	"awaiting_shipment": awaiting_shipment,
	"in_progress": in_progress,
	"completed": completed,
	"cancelled": cancelled,
}

class OrderStatusEnum(str, Enum):
	awaiting_confirmation = "awaiting_confirmation"
	awaiting_cooking = "awaiting_cooking"
	awaiting_payment = "awaiting_payment"
	awaiting_shipment = "awaiting_shipment"
	in_progress = "in_progress"
	incomplete = "incomplete"
	completed = "completed"
	cancelled = "cancelled"

class BaseOrderCreate(BaseModel):
	line_items: List[LineItem]
	customer_id: UUID4 = None
	customer_ip_address: str = None
	# associated session_id
	customer_session_id: UUID4 = None
	# associated cart_id
	cart_id: UUID4 = None
	# payment method id 
	payment_method: str = None
	# delivery_method id
	delivery_method: str = None
	# user_delivery_address id, if delivery method is 'delivery'
	delivery_address: UUID4 = None
	# guest delivery address
	guest_delivery_address: str = None
	# guest phone number
	guest_phone_number: str = None
	# pickup_address id, if delivery_method is 'pickup'
	pickup_address: UUID4 = None
	# list of coupons objects
	coupons: List[str] = None
	# custom customer message, provided for order
	custom_message: str = None

class BaseOrderUpdate(BaseModel):
	status_id: OrderStatusEnum
	status: OrderStatus = None

	def set_status(self):
		self.status = order_statuses[self.status_id]

class BaseOrder(BaseModel):
	""" Base Order Model """
	id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
	# id of cart, that was converted to order
	cart_id: UUID4 = None
	# id of the customer, that makes order, or, that is assigned to the order by admin
	customer_id: UUID4 = None
	# customer username
	customer_username: str = None
	customer_ip_address: str = None

	status: OrderStatus = order_statuses["awaiting_confirmation"]
#	status: OrderStatusEnum = OrderStatusEnum.awaiting_confirmation

	date_created: Optional[datetime] = Field(default_factory=datetime.utcnow)
	date_modified: Optional[datetime] = Field(default_factory=datetime.utcnow)
	line_items: List[LineItem]
	# amount values
	# cost of orders content before apply discounts
	base_amount: int = None # ? or maybe float?
	# discounted amount
	discount_amount: int = None # ? float?
	# sum of line-items amount, minus cart-level discounts and coupons.
	# Amount includes taxes, if needed
	total_amount: int = None # ? float?

	# payment method id 
	payment_method: PaymentMethod = None
	# delivery_method id
	delivery_method: DeliveryMethod = None

	# user_delivery_address object, if delivery method is 'delivery'
	delivery_address: UserDeliveryAddress = None
	# guest delivery adderss
	guest_delivery_address: str = None
	# guest phone number
	guest_phone_number: str = None
	# pickup_address id, if delivery_method is 'pickup'
	pickup_address: PickupAddress = None
	# list of coupons objects
	coupons: List[str] = None
	# custom customer message, provided for order
	custom_message: str = None

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

	def check_set_user(self, app):
		if not self.customer_id:
			return
		user = get_user_by_id(app.users_db, self.customer_id)
		if not user:
			return
		self.customer_username = user.username

	def save_db(self, orders_db):
		saved = orders_db.insert_one(
			self.dict(by_alias=True)
		)
	def delete_db(self, orders_db):
		orders_db.delete_one(
			{"_id": self.id}
		)
	def update_db(self, orders_db):
		# maybe need improvement to recast object with updated_order return info
		updated_order_dict = orders_db.find_one_and_update(
			{"_id": self.id},
			{"$set": self.dict(by_alias=True)},
			return_document=ReturnDocument.AFTER
		)
		updated_order = BaseOrder(**updated_order_dict)
		print('updated order is', updated_order)
		return updated_order

	def check_line_item_exists(self, line_item_id):
		for line_item in self.line_items:
			if line_item.id == line_item_id:
				return True, line_item
		return False, None
	def check_product_in_order_exists(self, new_line_item):
		for line_item in self.line_items:
			if (line_item.product_id == new_line_item.product_id) and (line_item.product != None):
				return True, line_item
		return False, None

	def add_line_item(self, request, line_item):
		line_item_exists, exist_line_item = self.check_product_in_order_exists(line_item)
		if line_item_exists:
			print('line item already exists, add quantity')
			# line_item already exists in order, need to add quantity
			exist_line_item.quantity += 1
			return
		print('line item not exist, add it')
		# line item not exists in order, need to add it
		product = get_product_by_id(request.app.products_db, line_item.product_id)
		# add product to the current line_item
		line_item.product = product
#		self.line_items.append(line_item)

	def remove_line_item_quantity(self, orders_db, line_item_id):
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

	def remove_line_item(self, orders_db, line_item_id):
		line_item_exists, line_item = self.check_line_item_exists(line_item_id)
		if line_item_exists:
			self.line_items.remove(line_item)
			return
		# line item not exist, raise Exception
		raise LineItemNotExist
	def update_line_item(self, orders_db, line_item_id: str, new_line_item: LineItemUpdate):
		line_item_exists, line_item = self.check_line_item_exists(line_item_id)
		if not line_item_exists:
			raise LineItemNotExist
		line_item.__dict__.update(**new_line_item.dict())
		if line_item.quantity < 1:
			self.line_items.remove(line_item)

	def set_modified(self):
		self.date_modified = datetime.utcnow()

