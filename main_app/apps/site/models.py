import uuid
from typing import Optional, List

from pydantic import UUID4, BaseModel, Field

from database.main_db import db_provider


class PickupAddress(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    info: Optional[str]

    def save_db(self):
        db_provider.pickup_addresses_db.insert_one(
            self.dict(by_alias=True)
        )

class StockItem(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    title: str
    description: Optional[str]
    imgsrc: List[str] = []

    def save_db(self):
        db_provider.stocks_db.insert_one(
            self.dict(by_alias=True)
        )

class MenuLink(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    link_name: Optional[str]
    link_path: Optional[str] 
    display_order: Optional[int] = 0


class MainSliderItem(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
    link_path: Optional[str] 
    display_order: Optional[int] = 0
    imgsrc: str

class RequestCall(BaseModel):
    name: str = ""
    phone: str = ""
    phone_mask: str = ""
