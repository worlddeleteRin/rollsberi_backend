from fastapi import FastAPI, Depends
from pymongo import MongoClient

from config import settings


# db_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://{}:{}@{}".format(db_username, db_password, db_host))
def setup_mongodb(app: FastAPI) -> None:
	db_client = MongoClient(settings.DB_URL)
	app.mongodb_client = db_client
	app.mongodb = db_client[settings.DB_NAME]




