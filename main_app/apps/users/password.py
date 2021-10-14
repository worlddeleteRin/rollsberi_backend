#passlib package
from passlib.context import CryptContext


# passlib context and verify and hash logic
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# verify password
def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)
# create hashed_password from passed password
def get_password_hash(password):
	return pwd_context.hash(password)
