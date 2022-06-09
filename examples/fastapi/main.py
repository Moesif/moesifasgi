from fastapi import FastAPI
from moesifasgi import MoesifMiddleware
from starlette.middleware import Middleware
from typing import Optional
from pydantic import BaseModel
import json
import uvicorn

# Your custom code that returns a user id string
custom_user = "12345"

async def custom_identify_user():
    return custom_user

# identify user using async mode
async def identify_user(request, response):
    user = await custom_identify_user()
    return user

# identify user not using async mode
def identify_user(request, response):
    return custom_user

# Your custom code that returns a company id string
custom_company = "67890"

async def custom_identify_company():
    return custom_company

# identify company using async mode
async def identify_company(request, response):
    company = await custom_identify_company
    return company

# identify company not using async mode
def identify_company(request, response):
    return custom_company

# If you don't want to use the standard ASGI session token,
# add your custom code that returns a string for session/API token
custom_session_token = "XXXXXXXXXXXXXX"

async def custom_get_token():
    return custom_session_token

# get session token using async mode
async def get_token(request, response):
    result = await custom_get_token()
    return result

# get session token not using async mode
def get_token(request, response):
    return custom_session_token

custom_metadata = {
    'datacenter': 'westus',
    'deployment_version': 'v1.2.3',
}

async def custom_get_metadata():
    return custom_metadata

# get metadata using async mode
async def get_metadata(request, response):
    result = await custom_get_metadata()
    return result

# get metadata not using async mode
def get_metadata(request, response):
    return custom_metadata

# Your custom code that returns true to skip logging
skip_route = "health/probe"

async def custom_should_skip(request):
    return skip_route in request.url._url

# should skip check using async mode
async def should_skip(request, response):
    result = await custom_should_skip(request)
    return result

# should skip check not using async mode
def should_skip(request, response):
    return skip_route in request.url._url

def custom_mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    if 'password' in eventmodel.response.body:
        eventmodel.response.body['password'] = None
    return eventmodel

# mask event using async mode
async def mask_event(eventmodel):
    return custom_mask_event(eventmodel)

# mask event not using async mode
def mask_event(eventmodel):
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

# in case you need run with debugger, those lines are needed
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)