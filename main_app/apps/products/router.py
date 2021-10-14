from fastapi import APIRouter, Request, HTTPException, Depends
from bson.json_util import loads, dumps
import json

import datetime

from pydantic import UUID4


# models 
from .models import BaseProduct, BaseProductCreate, BaseProductUpdate
from .models import BaseCategory, BaseCategoryCreate, BaseCategoryUpdate
# product exceptions
from .product_exceptions import ProductNotExist, CategoryNotExist
# products methods
from .products import get_product_by_id, get_category_by_id, search_products_by_name

from apps.users.user import get_current_admin_user

router = APIRouter(
	prefix = "/products",
	tags = ["products"],
	# responses ? 
)

# categories
@router.get("/categories")
async def get_categories(request: Request):
	categories_dict = request.app.mongodb["categories"].find({})
	categories = [BaseCategory(**category).dict() for category in categories_dict]
	return {
		"status": "success",
		"categories": categories,
	}

@router.get("/categories/{category_id}")
async def get_category(
	request: Request,
	category_id: UUID4,
):
	category = get_category_by_id(request.app.categories_db, category_id)
	return category.dict()

@router.post("/categories")
async def create_category(
	request: Request,
	category: BaseCategoryCreate,
	admin_user = Depends(get_current_admin_user),
):
	new_category = BaseCategory(**category.dict())
	new_category.insert_db(request.app.categories_db)
	return new_category.dict()

@router.patch("/categories/{category_id}")
async def update_category(
	request: Request,
	category_id: UUID4,
	new_category: BaseCategoryUpdate,
):
	category_to_update = get_category_by_id(request.app.categories_db, category_id)
	updated_model = category_to_update.copy(update = {**new_category.dict(exclude_unset=True)})
	updated_category = updated_model.update_db(request.app.categories_db)
	return updated_category.dict()

@router.delete("/categories/{category_id}")
async def delete_category(
	request: Request,
	category_id: UUID4,
):
	category = get_category_by_id(request.app.categories_db, category_id)
	category.delete_db(request.app.categories_db)
	return {
		"status": "success"
	}

# products

@router.get("/")
async def get_products(request: Request):
	products_dict = request.app.mongodb["products"].find({})
	products = [BaseProduct(**product).dict() for product in products_dict]
	return {
		"status": "success",
		"products": products,
	}

@router.get("/search")
async def search_products(
	request: Request,
	search: str
):
	if not search:
		return []
	products = search_products_by_name(request.app.products_db, search)
	return products

@router.get("/{product_id}")
async def get_product(
	request: Request,
	product_id: UUID4,
):
	product = get_product_by_id(request.app.products_db, product_id)
	return product.dict()

@router.post("/")
async def create_product(
	request: Request,
	product: BaseProductCreate,
):
	new_product = BaseProduct(**product.dict())
	new_product.insert_db(request.app)
	return new_product.dict()

@router.patch("/{product_id}")
async def update_product(
	request: Request,
	product_id: UUID4,
	new_product: BaseProductUpdate,
):
	product_to_update = get_product_by_id(request.app.products_db, product_id)
#	print('new product is', new_product)
	updated = product_to_update.copy(update = {**new_product.dict(exclude_unset=True)})
	updated_model = BaseProduct(**updated.dict(by_alias=True))
#	print('updated model is', updated_model)
	updated_product = updated_model.update_db(request)
#	print('updated product is', updated_product)
	if updated_product:
		return updated_product.dict()
	else:
		return None

@router.delete("/{product_id}")
async def delete_product(
	request: Request,
	product_id: UUID4,
):
	product = get_product_by_id(request.app.products_db, product_id)
	product.delete_db(request.app.products_db)
	return {
		"status": "success"
	}

