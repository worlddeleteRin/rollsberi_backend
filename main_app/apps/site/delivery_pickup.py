from fastapi import Depends, Request
from .models import PickupAddress
from .site_exceptions import PickupAddressNotExist
import uuid

from database.main_db import db_provider



def get_pickup_addresses():
	pickup_addresses = []
	pickup_addresses_dict = db_provider.pickup_addresses_db.find()
	if not pickup_addresses_dict:
		return None
	pickup_addresses = [PickupAddress(**a).dict() for a in pickup_addresses_dict]
	return pickup_addresses

def get_pickup_address_by_id(pickup_address_id) -> PickupAddress:
	pickup_address = db_provider.pickup_addresses_db.find_one(
		{"_id": pickup_address_id}
	)
	if not pickup_address:
		raise PickupAddressNotExist
	pickup_address = PickupAddress(**pickup_address)
	return pickup_address
