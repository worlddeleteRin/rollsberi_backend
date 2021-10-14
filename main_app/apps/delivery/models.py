from typing import Optional, List

from pydantic import UUID4, BaseModel, Field


class DeliveryMethod(BaseModel):
	id: str = Field(alias="_id")
	name: str
