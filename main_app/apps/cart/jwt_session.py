from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta


# create access token
def create_session_token(
	data: dict,
	JWT_SESSION_KEY: str,
	JWT_ALGORITHM: str,
	expires_delta: Optional[timedelta] = None,
	):
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes = 100)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
	return encoded_jwt

def decode_token(token, JWT_SECRET_KEY, algorithms: list):
	return jwt.decode(token, JWT_SECRET_KEY, algorithms = algorithms)
