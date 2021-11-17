from fastapi import Security
from fastapi.security.api_key import APIKeyHeader
from fastapi import HTTPException

from database.main_db import db_provider

def get_api_app_client(
    api_key_header:str = Security(APIKeyHeader(name="app_token"))
):
    app_client_dict = db_provider.app_clients_db.find_one(
        {"access_token": api_key_header}
    )
    print('api key query is', api_key_header)
    print('client is', app_client_dict)

    if not app_client_dict:
        raise HTTPException(
            status_code = 400,
            detail = "Incorrect auth credentials",
        )

