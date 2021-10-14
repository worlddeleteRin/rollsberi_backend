from fastapi import HTTPException, status


class CartNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Cart not exist"

class LineItemNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Line Item not exist"

class CartAlreadyExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Cart already exist"


class NotValidUUID(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "not valid uuid specified"
