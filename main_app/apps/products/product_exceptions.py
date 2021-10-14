from fastapi import HTTPException, status


class ProductNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Product not exist"

class CategoryNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Category not exist"

class ProductAlreadyExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Product is already exist"

class CategoryAlreadyExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Category already exist"


