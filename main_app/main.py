import uvicorn
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, status, Request, Depends
from starlette.middleware.cors import CORSMiddleware
# import staticfiles
from fastapi.staticfiles import StaticFiles

# app config (env variables)
from config import settings

# import motor.motor_asyncio
from bson.objectid import ObjectId
from bson import json_util
import json

# routes importing
from apps.products import router as products_router
from apps.users import router as users_router
from apps.orders import router as orders_router
from apps.cart import router as cart_router
from apps.coupons import router as coupons_router
from apps.site import router as site_router
from apps.cart.cart import create_session_id
# eof routes importing
from dependencies import get_api_app_client

# import database
from database.main_db import setup_mongodb

# include all necessary routes
app = FastAPI(
	dependencies=[Depends(get_api_app_client)]
)
# mount static files folder
app.mount("/static", StaticFiles(directory="static"), name = "static")

app.add_middleware(
	CORSMiddleware,
	allow_origins = ['*'],
	# allow_credentials=True,
	allow_methods = ['*'],
	allow_headers = ['*'],
)

# setting up app cors


# include app routes
app.include_router(products_router.router)
app.include_router(users_router.router)
app.include_router(orders_router.router)
app.include_router(cart_router.router)
app.include_router(coupons_router.router)
app.include_router(site_router.router)

@app.on_event('startup')
async def startup_db_client():
	print('settings are', settings.dict())
	setup_mongodb(app)
	print('now app is', app)
	print('app mongo db is', app.mongodb)

	app.users_db = app.mongodb["users"]
	app.users_addresses_db = app.mongodb["users_addresses"]
	app.products_db = app.mongodb["products"]
	app.categories_db = app.mongodb["categories"]
	app.carts_db = app.mongodb["carts"]
	app.coupons_db = app.mongodb["coupons"]
	app.orders_db = app.mongodb["orders"]
	app.payment_methods_db = app.mongodb["payment_methods"]
	app.delivery_methods_db = app.mongodb["delivery_methods"]
	app.pickup_addresses_db = app.mongodb["pickup_addresses"]
	app.order_statuses_db = app.mongodb["order_statuses"]
	app.stocks_db = app.mongodb["stocks"]
	app.app_clients_db = app.mongodb["app_clients"]

@app.on_event('shutdown')
async def shutdown_db_client():
	app.mongodb_client.close()




@app.get("/status")
def get_status():
	""" Get status of server """
	return {
		"status": "running",
		"settings": settings.dict(),
		}

@app.get("/session")
def create_session():
	""" Creates session id for client """
	session_key = create_session_id()
	return {
		"session_id": session_key,
	}



if __name__ == "__main__":
	uvicorn.run(
		"main:app",
		host='0.0.0.0',
		reload=settings.DEBUG_MODE,
		port=8000,
	)
