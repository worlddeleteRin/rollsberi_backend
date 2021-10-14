from fastapi import HTTPException, status


class CouponNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Coupon not exist"

class CouponAlreadyExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Coupon already exist"

