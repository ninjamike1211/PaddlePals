import pytest
import requests
import json

from database import database_setup
from database import database_server
from database.database_api import restAPI

def setup_server(tmp_path, users=None, auth=True):
    db_path = tmp_path / 'pickle.db'
    database_setup.setup_db(db_path, users)
    api = restAPI(db_path, useAuth=auth)
    return database_server.PickleServer(api, 8080)


# def test_