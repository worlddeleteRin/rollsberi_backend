import uuid
from typing import Optional, List

from pydantic import UUID4, BaseModel, Field


class PickupAddress(BaseModel):
	id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
	name: str
	info: str = None

	def save_db(self, pickup_addresses_db):
		pickup_addresses_db.insert_one(
			self.dict(by_alias=True)
		)

class StockItem(BaseModel):
	id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
	title: str
	description: str = None
	imgsrc: List[str] = []

	def save_db(self, stocks_db):
		stocks_db.insert_one(
			self.dict(by_alias=True)
		)
