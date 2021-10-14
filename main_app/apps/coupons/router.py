from fastapi import APIRouter, Request, Depends
from bson.json_util import loads, dumps
import json

import datetime

# from users apps
from apps.users.user import get_current_admin_user
from apps.users.models import BaseUser

# models 
from .models import BaseCoupon

router = APIRouter(
	prefix = "/coupons",
	tags = ["coupons"],
)


@router.get("/")
async def get_coupons(
	request: Request,
	admin_user: BaseUser = Depends(get_current_admin_user),
	):
	return {
		"status": "success",
	}

@router.post("/")
async def create_coupon(
	request: Request,
	coupon: BaseCoupon,
	admin_user: BaseUser = Depends(get_current_admin_user),
	):

	print('coupon is', coupon)
	# need to check, if coupon with that id exists
	# add coupon to db
	request.app.coupons_db.insert_one(
		coupon.dict(by_alias=True)
	)
	return {
		"status": "success",
	}
