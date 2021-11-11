from pydantic import BaseModel
from config import settings


class BonusesLevel(BaseModel):
    id: int = 1
    title: str
    cart_bonuses_percent: int = settings.default_bonuses_percent
    need_to_spent: int
