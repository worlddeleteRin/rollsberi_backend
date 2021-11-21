from fastapi import HTTPException, status


class OrderNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Order not exist"

class OrderNotEditable(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Заказ нельзя редактировать"
