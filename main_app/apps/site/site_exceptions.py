from fastapi import HTTPException, status


class PickupAddressNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "PickupAddress not exist"
