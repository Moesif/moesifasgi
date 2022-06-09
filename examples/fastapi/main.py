from fastapi import FastAPI
from moesifasgi import MoesifMiddleware
from starlette.middleware import Middleware
from typing import Optional
from pydantic import BaseModel
import json

# Your custom code that returns a user id string
custom_user = "12345"

async def custom_identify_user():
    return custom_user

async def identify_user(request, response):
    user = await custom_identify_user()
    return user

def identify_user(request, response):
    return custom_user

# Your custom code that returns a company id string
custom_company = "67890"

async def custom_identify_company():
    return custom_company

async def identify_company(request, response):
    company = await custom_identify_company
    return company

def identify_company(request, response):
    return custom_company

custom_session_token = "XXXXXXXXXXXXXX"

async def custom_get_token():
    # If you don't want to use the standard ASGI session token,
    # add your custom code that returns a string for session/API token
    return custom_session_token

async def get_token(request, response):
    result = await custom_get_token()
    return result

def get_token(request, response):
    return custom_session_token

custom_metadata = {
    'datacenter': 'westus',
    'deployment_version': 'v1.2.3',
}

async def custom_get_metadata():
    return custom_metadata

async def get_metadata(request, response):
    result = await custom_get_metadata()
    return result

def get_metadata(request, response):
    return custom_metadata

skip_route = "health/probe"

async def custom_should_skip(request):
    # Your custom code that returns true to skip logging
    return skip_route in request.url._url

async def should_skip(request, response):
    result = await custom_should_skip(request)
    return result

def should_skip(request, response):
    return skip_route in request.url._url

def custom_mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    if 'password' in eventmodel.response.body:
        eventmodel.response.body['password'] = None
    return eventmodel

async def mask_event(eventmodel):
    return custom_mask_event(eventmodel)

def mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    return custom_mask_event(eventmodel)

moesif_settings = {
    'APPLICATION_ID': 'Your Moesif Application Id',
    'LOG_BODY': True,
    'DEBUG': True,
    'IDENTIFY_USER': identify_user,
    'IDENTIFY_COMPANY': identify_company,
    'GET_SESSION_TOKEN': get_token,
    'GET_METADATA': get_metadata,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
    'CAPTURE_OUTGOING_REQUESTS': False,
}

app = FastAPI()

app.add_middleware(MoesifMiddleware, settings=moesif_settings)

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


@app.post("/items")
async def create_item(item: Item):
    return item

@app.get("/v2")
async def read_main():
    return {"message": "Hello World"}
