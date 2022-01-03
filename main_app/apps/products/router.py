from fastapi import APIRouter, Request, HTTPException, Depends
from bson.json_util import loads, dumps
import json

import datetime

from typing import List

from pydantic import UUID4


# models 
from .models import BaseProduct, BaseProductCreate, BaseProductUpdate
from .models import BaseCategory, BaseCategoryCreate, BaseCategoryUpdate
# product exceptions
from .product_exceptions import ProductNotExist, CategoryNotExist
# products methods
from .products import get_product_by_id, get_category_by_id, get_category_products_by_id, search_products_by_name

from apps.users.user import get_current_admin_user

from database.main_db import db_provider

router = APIRouter(
    prefix = "/products",
    tags = ["products"],
    # responses ? 
)

# categories
@router.get("/categories")
async def get_categories(request: Request):
    categories_dict = db_provider.categories_db.find({})
    categories = [BaseCategory(**category).dict() for category in categories_dict]
    return {
        "status": "success",
        "categories": categories,
    }

@router.get("/categories/{category_id}")
async def get_category(
    category_id: UUID4,
):
    category = get_category_by_id(category_id)
    if category:
        return category.dict()

@router.get("/categories/{category_id}/products")
async def get_category_products(
    category_id: UUID4,
):
    """
        get products for category with [category_id]
    """
    category_products = get_category_products_by_id(category_id)    
    return category_products;


@router.post("/categories")
async def create_category(
    request: Request,
    category: BaseCategoryCreate,
    admin_user = Depends(get_current_admin_user),
):
    new_category = BaseCategory(**category.dict())
    new_category.insert_db()
    return new_category.dict()

@router.patch("/categories/{category_id}")
async def update_category(
    request: Request,
    category_id: UUID4,
    new_category: BaseCategoryUpdate,
):
    category_to_update = get_category_by_id(category_id)
    updated_model = category_to_update.copy(update = {**new_category.dict(exclude_unset=True)})
    updated_category = updated_model.update_db()
    return updated_category.dict()

@router.delete("/categories/{category_id}")
async def delete_category(
    request: Request,
    category_id: UUID4,
):
    category = get_category_by_id(category_id)
    if not category:
        return {
            "status": "failure",
            "msg": "category not exists"
        }
    category.delete_db()
    return {
        "status": "success"
    }

# products
@router.get("/")
async def get_products():
    products_dict = db_provider.products_db.find({})
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
    products = search_products_by_name(search)
    return products

@router.get("/{product_id}")
async def get_product(
    product_id: UUID4,
):
    product = get_product_by_id(product_id)
    if product:
        return product.dict()

@router.post("/")
async def create_product(
    product: BaseProductCreate,
):
    new_product = BaseProduct(**product.dict())
    new_product.insert_db()
    return new_product.dict()

@router.patch("/{product_id}")
async def update_product(
    request: Request,
    product_id: UUID4,
    new_product: BaseProductUpdate,
):
    product_to_update = get_product_by_id(product_id)
#   print('new product is', new_p:roduct)
    updated = product_to_update.copy(update = {**new_product.dict(exclude_unset=True)})
    updated_model = BaseProduct(**updated.dict(by_alias=True))
#   print('updated model is', updated_model)
    updated_product = updated_model.update_db(request)
#   print('updated product is', updated_product)
    if updated_product:
        return updated_product.dict()
    else:
        return None

@router.delete("/{product_id}")
async def delete_product(
    request: Request,
    product_id: UUID4,
):
    product = get_product_by_id(product_id)
    product.delete_db()
    return {
        "status": "success"
    }

