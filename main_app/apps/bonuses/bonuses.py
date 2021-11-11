from database.main_db import db_provider

from .bonuses_exceptions import BonusesLevelNotExist
from .models import BonusesLevel


def get_bonuses_levels():
    bonuses_levels_dict = db_provider.bonuses_levels_db.find({})
    bonuses_levels = [BonusesLevel(**b).dict() for b in bonuses_levels_dict]
    return bonuses_levels

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

