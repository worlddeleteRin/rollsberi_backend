from fastapi import APIRouter, Request, Depends
from bson.json_util import loads, dumps
import json

import datetime

# from users apps
from apps.users.user import get_current_admin_user
from apps.users.models import BaseUser

# models 
from .models import BaseCoupon, BaseCouponCreate, BaseCouponDB

from database.main_db import db_provider

router = APIRouter(
	prefix = "/coupons",
	tags = ["coupons"],
)


@router.get("/")
async def get_coupons(
	admin_user: BaseUser = Depends(get_current_admin_user),
	):
	coupons_dict = db_provider.coupons_db.find({}) # implement pagination
	coupons = [BaseCoupon(**coupon).dict() for coupon in coupons_dict]
	return {
		"coupons": coupons
	}

@router.post("/")
async def create_coupon(
	coupon: BaseCouponCreate,
	admin_user: BaseUser = Depends(get_current_admin_user),
	):
	new_coupon = BaseCouponDB(**coupon.dict())
	print('coupon is', coupon)
	# need to check, if coupon with that id exists
	# add coupon to db
	db_provider.coupons_db.insert_one(
		new_coupon.dict(by_alias=True)
	)
	return {
		"status": "success",
	}
