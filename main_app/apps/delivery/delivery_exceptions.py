from fastapi import HTTPException, status


class DeliveryMethodNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "DeliveryMethod not exist"
