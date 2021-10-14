from fastapi import Request 
from .models import BaseCoupon
from .coupon_exceptions import CouponNotExist 

def get_coupon_by_id(
	request: Request,
	coupon_code: str,
	silent: bool = False,
):
	coupon_dict = request.app.coupons_db.find_one(
		{"code": coupon_code}
	)
	if not coupon_dict:
		if not silent:
			raise CouponNotExist
		return None
	coupon = BaseCoupon(**coupon_dict)
	return coupon
