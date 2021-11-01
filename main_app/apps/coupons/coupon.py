from fastapi import Request 
from .models import BaseCoupon, BaseCouponDB
from .coupon_exceptions import CouponNotExist 

from database.main_db import db_provider

def get_coupon_by_id(
	coupon_code: str,
	silent: bool = False,
	db_model: bool = False,
):
	coupon_dict = db_provider.coupons_db.find_one(
		{"code": coupon_code}
	)
	if not coupon_dict:
		if not silent:
			raise CouponNotExist
		return None
	if not db_model:
		coupon = BaseCoupon(**coupon_dict)
	else:
		coupon = BaseCouponDB(**coupon_dict)
	return coupon
