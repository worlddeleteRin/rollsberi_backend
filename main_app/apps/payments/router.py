from fastapi import APIRouter, Depends, Request, Body
from typing import Optional, List

from datetime import datetime, timedelta

from pymongo import ReturnDocument

import uuid

# import config (env variables)
from config import settings


# order exceptions

router = APIRouter(
	prefix = "/payments",
	tags = ["payments"],
)


