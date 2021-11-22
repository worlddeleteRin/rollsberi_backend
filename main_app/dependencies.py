from fastapi import Security
from fastapi.security.api_key import APIKeyHeader
from fastapi import HTTPException

from database.main_db import db_provider

import sys

def get_api_app_client(
    api_key_header:str = Security(APIKeyHeader(name="App-Token", auto_error=False))
    # api_key_header: str = "another_access_token_here"
):
    sys.stdout.flush()
    app_client_dict = db_provider.app_clients_db.find_one(
        {"access_token": api_key_header}
    )
    sys.stdout.flush()

    if not app_client_dict:
        raise HTTPException(
            status_code = 400,
            detail = "Incorrect auth credentials",
        )

