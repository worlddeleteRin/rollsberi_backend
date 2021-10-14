from fastapi import Depends, Request
from .models import DeliveryMethod
from .delivery_exceptions import DeliveryMethodNotExist
import uuid
from config import settings


def get_delivery_methods(delivery_db):
	delivery_methods_dict = delivery_db.find({})
	if not delivery_methods_dict:
		return None
	delivery_methods = [DeliveryMethod(**d_method).dict() for d_method in delivery_methods_dict]
	return delivery_methods

def get_delivery_method_by_id(delivery_db, delivery_method_id):
	delivery_method = delivery_db.find_one(
		{"_id": delivery_method_id}
	)
	if not delivery_method:
		raise DeliveryMethodNotExist
	delivery_method = DeliveryMethod(**delivery_method)
	return delivery_method
