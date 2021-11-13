# from database.main_db import db_provider

# from .bonuses_exceptions import BonusesLevelNotExist
from .models import BonusesLevel

# from functools import lru_cache

b_lvl1 = BonusesLevel(
    id = 1,
    title = "first level",
    cart_bonuses_percent = 4,
    need_to_spent = 0
)
b_lvl2 = BonusesLevel(
    id = 2,
    title = "second level",
    cart_bonuses_percent = 5,
    need_to_spent = 3000
)
b_lvl3 = BonusesLevel(
    id = 3,
    title = "third level",
    cart_bonuses_percent = 6,
    need_to_spent = 8000
)
b_lvl4 = BonusesLevel(
    id = 4,
    title = "fourth level",
    cart_bonuses_percent = 7,
    need_to_spent = 15000
)
bonuses_levels = {
    1: b_lvl1,
    2: b_lvl2,
    3: b_lvl3,
    4: b_lvl4,
}

"""
@lru_cache
def get_bonuses_levels():
    bonuses_levels_dict = db_provider.bonuses_levels_db.find({})
    bonuses_levels = [BonusesLevel(**b).dict() for b in bonuses_levels_dict]
    return bonuses_levels

bonuses_levels = get_bonuses_levels()

def get_bonuses_level_by_id(
    bonuses_level_id: int,
    silent: bool = False
):
    bonuses_level = db_provider.bonuses_levels_db.find_one(
        {"_id": bonuses_level_id}
    )
    if not bonuses_level:
        if not silent:
            raise BonusesLevelNotExist
        return None
    bonuses_level = BonusesLevel(**bonuses_level)
    return bonuses_level 
"""
