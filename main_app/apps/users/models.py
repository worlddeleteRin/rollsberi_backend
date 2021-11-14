import uuid

from typing import Optional, List

from pydantic import UUID4, BaseModel, Field, validator
from datetime import datetime, date

from pymongo import ReturnDocument

from database.main_db import db_provider


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


class UserDeleteDeliveryAddress(BaseModel):
    id: UUID4

class UserDeliveryAddress(BaseModel):
    """
        Base User delivery model
    """
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    user_id: Optional[UUID4] = None
    city: Optional[str] = ""
    street: str
    house_number: str
    flat_number: Optional[str] = ""
    entrance_number: Optional[str] = ""
    floor_number: Optional[str] = ""
    address_display: Optional[str] = ""
    comment: Optional[str] = ""

    class Config:
        allow_population_by_field_name = True

    @validator("address_display", always = True)
    def default_address_display(cls, v, values):
        if v:
            return v
        address = f"г. Симферополь, ул. {values['street']}, д. {values['house_number']}"
        if values['flat_number'].__len__() > 0:
            address += f", кв. {values['flat_number']}"
        if values['entrance_number'].__len__() > 0:
            address += f", {values['entrance_number']} подъезд"
        if values['floor_number'].__len__() > 0:
            address += f", {values['floor_number']} этаж"
        return address


class BaseUser(BaseModel):
    """ Base User Model """
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    date_created: Optional[datetime] = Field(default_factory=datetime.utcnow)
    email: Optional[str] = ""
    username: str
    is_active: Optional[bool] = False
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    name: Optional[str] = ""
    bonuses: int = 0
    bonuses_rank: Optional[int] = 1

    class Config:
        allow_population_by_field_name = True

    def update_db(self):
        updated_user = db_provider.users_db.find_one_and_update(
            {"_id": self.id},
            {"$set": self.dict(by_alias=True)},
            return_document=ReturnDocument.AFTER
        )
        return updated_user 

class BaseUserCreate(BaseModel):
    username: str
    password: str

class BaseUserRestore(BaseModel):
    username: str

class BaseUserRestoreVerify(BaseModel):
    username: str
    otp: str

class BaseUserVerify(BaseModel):
    username: str
    password: str
    otp: str

class BaseUserExistVerified(BaseModel):
    username: str

class BaseUserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None

class BaseUserUpdatePassword(BaseModel):
    password: str


class BaseUserDB(BaseUser):
    hashed_password: str
    otp: Optional[str] = None


