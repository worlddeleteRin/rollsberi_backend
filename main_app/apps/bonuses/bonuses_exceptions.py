from fastapi import HTTPException, status

class BonusesLevelNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Bonuses level not exist"
