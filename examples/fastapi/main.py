from fastapi import FastAPI
from moesifasgi import MoesifMiddleware
from starlette.middleware import Middleware
from typing import Optional
from pydantic import BaseModel
import json


def identify_user(request, response):
    # Your custom code that returns a user id string
    return "12345"

def identify_company(request, response):
    # Your custom code that returns a company id string
    return "67890"

def get_token(request, response):
    # If you don't want to use the standard ASGI session token,
    # add your custom code that returns a string for session/API token
    return "XXXXXXXXXXXXXX"

def get_metadata(request, response):
    return {
        'datacenter': 'westus',
        'deployment_version': 'v1.2.3',
    }

def should_skip(request, response):
    # Your custom code that returns true to skip logging
    return "health/probe" in request.url._url

def mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    if 'password' in eventmodel.response.body:
        eventmodel.response.body['password'] = None
    return eventmodel

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
