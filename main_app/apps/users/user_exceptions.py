from fastapi import HTTPException, status

class IncorrectUsernameOrPassword(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "incorrect username os password"

class NotSendVerificationCode(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Не уалось отправить код на данный номер"

class IncorrectVerificationCode(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Неверный код верификации"

class InactiveUser(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "Inactive user"

class InvalidAuthenticationCredentials(HTTPException):
	def __init__(self):
		self.status_code = status.HTTP_401_UNAUTHORIZED
		self.detail = "Invalid Authentication Credentials"
		headers={"WWW-Authenticate": "Bearer"},

class UserAlreadyExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "User already exist"

class UserNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "User not exist, need register first"

class UserDeliveryAddressNotExist(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "UserDeliveryAddress not exist"

class UserNotAdmin(HTTPException):
	def __init__(self):
		self.status_code = 400
		self.detail = "User is not admin user"


