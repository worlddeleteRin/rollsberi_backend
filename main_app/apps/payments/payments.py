from fastapi import Depends, Request
from .models import PaymentMethod
from .payment_exceptions import PaymentMethodNotExist
import uuid
from config import settings


def get_payment_methods(payments_db):
	payment_methods_dict = payments_db.find({})
	if not payment_methods_dict:
		return None
	payment_methods = [PaymentMethod(**p_method).dict() for p_method in payment_methods_dict]
	return payment_methods

def get_payment_method_by_id(payments_db, payment_method_id):
	payment_method = None
	payment_method = payments_db.find_one(
		{"_id": payment_method_id}
	)
	if not payment_method:
		raise PaymentMethodNotExist
	payment_method = PaymentMethod(**payment_method)
	return payment_method
