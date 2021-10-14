from typing import Optional, List

from pydantic import UUID4, BaseModel, Field


class PaymentMethod(BaseModel):
	id: str = Field(alias="_id")
	name: str
