from fastapi import FastAPI
from moesifasgi import MoesifMiddleware
from starlette.middleware import Middleware
from typing import Optional
from pydantic import BaseModel
import json

async def custom_identify_user():
    # Your custom code that returns a user id string
    return "12345"

async def identify_user(request, response):
    result = await custom_identify_user()
    return result

async def async_identify_company():
    # Your custom code that returns a company id string
    return "67890"

async def identify_company(request, response):
    result = await custom_identify_company()
    return result

async def custom_get_token():
    # If you don't want to use the standard ASGI session token,
    # add your custom code that returns a string for session/API token
    return "XXXXXXXXXXXXXX"

async def get_token(request, response):
    result = await custom_get_token()
    return result

async def custom_get_metadata():
    return {
        'datacenter': 'westus',
        'deployment_version': 'v1.2.3',
    }

async def get_metadata(request, response):
    result = await custom_get_metadata()
    return result

async def custom_should_skip(request):
    # Your custom code that returns true to skip logging
    return "health/probe" in request.url._url

async def should_skip(request, response):
    result = await custom_should_skip(request)
    return result

async def custom_mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    if 'password' in eventmodel.response.body:
        eventmodel.response.body['password'] = None
    return eventmodel

async def mask_event(eventmodel):
    result = await custom_mask_event(eventmodel)
    return result

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
