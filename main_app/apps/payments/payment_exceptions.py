from fastapi import HTTPException, status


class PaymentMethodNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "PaymentMethod not exist"
