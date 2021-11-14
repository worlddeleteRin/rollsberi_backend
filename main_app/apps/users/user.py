from fastapi import Depends, Request, FastAPI
from pydantic import UUID4
from jose import JWTError, jwt


from .models import BaseUser, BaseUserDB, Token, TokenData, BaseUserCreate, BaseUserVerify, BaseUserRestore, BaseUserRestoreVerify, UserDeliveryAddress, UserDeliveryAddress
from config import settings
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .jwt import decode_token, create_access_token

from .password import verify_password, get_password_hash

from .user_exceptions import InvalidAuthenticationCredentials, IncorrectVerificationCode, InactiveUser, UserAlreadyExist, UserNotExist, UserDeliveryAddressNotExist, UserNotAdmin

from database.main_db import db_provider


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token", auto_error = False)



# authenticate user
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_user(username: str) -> BaseUserDB:
    user_dict = db_provider.users_db.find_one({"username": username})
    #print('user dict is', user_dict)
    if not user_dict:
        raise
    return BaseUserDB(**user_dict)


def get_user_by_id(
    user_id: UUID4, 
    silent: bool = False,
    ):
    user_dict = db_provider.users_db.find_one(
        {"_id": user_id}
    )
    if not user_dict:
        if silent:
            return None
        raise
    return BaseUser(**user_dict)

async def get_current_user_silent(token: str = Depends(oauth2_scheme)):
    print('get current user silent, token is', token)
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY, [settings.JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        #    raise InvalidAuthenticationCredentials
        token_data = TokenData(username = username)
    except JWTError:
        return None
        # raise InvalidAuthenticationCredentials
    except Exception as e:
        return None
    if not token_data.username:
        return None
        # raise InvalidAuthenticationCredentials
    user = get_user(username = token_data.username)
    if user is None:
        return None
        # raise InvalidAuthenticationCredentials
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY, [settings.JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise InvalidAuthenticationCredentials
        token_data = TokenData(username = username)
    except JWTError:
        raise InvalidAuthenticationCredentials
    if not token_data.username:
        raise InvalidAuthenticationCredentials
    user = get_user(username = token_data.username)
    if user is None:
        raise InvalidAuthenticationCredentials
    return user


def get_current_active_user(current_user: BaseUser = Depends(get_current_user)):
    if not current_user.is_active:
        raise InactiveUser
    return current_user

def get_current_admin_user(current_user: BaseUser = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise UserNotAdmin
    return current_user


def get_user_register(user_info: BaseUserCreate):
    user = db_provider.users_db.find_one({"username": user_info.username})
    # if user exist and verified, we raise exist exception
    if user:
        user = BaseUser(**user)
        if user.is_verified:
            raise UserAlreadyExist
        # if user exist, but not verified - we delete it,
        # to recreate in future
        else:
            #print('found user when register, but it is not verified, so, delete it')
            db_provider.users_db.delete_one({"_id": user.id})

    hashed_password = get_password_hash(user_info.password)
    user_to_register = BaseUserDB(**user_info.dict(), hashed_password = hashed_password)
    return user_to_register

def get_user_restore(user_info: BaseUserRestore) -> BaseUserDB:
    #user_info = user_info.dict()
    user = db_provider.users_db.find_one({"username": user_info.username})
    # if user not exist we raise not exist exception
    if not user:
        raise UserNotExist

    user_to_verify = BaseUserDB(**user)
    return user_to_verify

def get_user_verify(user_info: BaseUserVerify):
    #user_info = user_info.dict()
    user = db_provider.users_db.find_one({"username": user_info.username})
    if not user:
        raise UserNotExist
    user = BaseUserDB(**user)
    if not user_info.otp == user.otp:
        raise IncorrectVerificationCode
    # set user to verified
    user.is_verified = True
    user.is_active = True
    user.otp = None
    db_provider.users_db.update_one({"_id": user.id}, {"$set": user.dict(by_alias=True)})

    return BaseUser(**user.dict())
#   if user.is_verified:
#       raise UserAlreadyVerified
def get_user_restore_verify(user_info: BaseUserRestoreVerify) -> BaseUser:
    user = db_provider.users_db.find_one({"username": user_info.username})
    if not user:
        raise UserNotExist
    user = BaseUserDB(**user)
    if not user_info.otp == user.otp:
        raise IncorrectVerificationCode
    # set user otp code to None 
    user.otp = None
    db_provider.users_db.update_one({"_id": user.id}, {"$set": user.dict(by_alias=True)})
    return BaseUser(**user.dict())

def get_user_delivery_addresses(user_id: UUID4):
    addresses_dict = db_provider.users_addresses_db.find(
        {"user_id": user_id}
    )
    addresses = [UserDeliveryAddress(**address).dict() for address in addresses_dict]
    return addresses

def get_user_delivery_address_by_id(delivery_address_id) -> UserDeliveryAddress:
    address_dict = db_provider.users_addresses_db.find_one(
        { "_id": delivery_address_id }
    )
    if not address_dict:
        raise UserDeliveryAddressNotExist
    address = UserDeliveryAddress(**address_dict)
    return address

# search users by username
def search_users_by_username(search_string: str):
    users_dict = db_provider.users_db.find(
        {
            "username": {
                "$regex": search_string
            }
        }
    ).limit(10)
    users = [BaseUser(**user).dict() for user in users_dict]
    return users

