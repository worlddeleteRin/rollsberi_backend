from pydantic import BaseSettings
from functools import lru_cache

import os
import sys

class Settings(BaseSettings):
    app_name: str = "Some app name"
    JWT_SECRET_KEY: str = ''
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1
    JWT_SESSION_KEY: str = ''
    JWT_SESSION_TOKEN_EXPIRE_MINUTES: int = 1
    JWT_ALGORITHM: str = "HS256"
    DB_URL: str = ''
    DB_NAME: str = ''
    DEBUG_MODE: bool = True
    send_order_notifications: bool = False
    # telegram section
    telegram_notif_group_id: str = ""
    telegram_bot_username: str = ""
    telegram_bot_token: str = ""
    # smsc section
    smsc_login: str = ""
    smsc_password: str = ""
    # base static url
    base_static_url: str = ""

    default_bonuses_percent: int = 3


    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    env_mode = os.getenv("env_mode") or 'dev'
    print('env mode is', env_mode)
    if env_mode == 'prod':
        env_file = '.env.prod'
    elif env_mode == 'dev':
        env_file = '.env.dev'
    env_file = '.env.dev'
    #print('settings are', Settings())
    env_location = f'{env_file}'
    print('env location is', env_location)
    return Settings(_env_file = env_location)

settings = get_settings()
