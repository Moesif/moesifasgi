from moesifasgi import MoesifMiddleware
from typing import Optional
from datetime import datetime, timedelta
from typing import Union
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel


# identify user not using async mode
def identify_user(request, response):
    # Implement your custom logic which reads user id from your request context
    # For example, you can extract the claim from a JWT in the Authorization header
    return "12345"

# identify company not using async mode
def identify_company(request, response):
    # Implement your custom logic which reads company id from your request context
    # For example, you can extract the claim from a JWT in the Authorization header
    return "67890"

# get metadata not using async mode
def get_metadata(request, response):
    return {
        'datacenter': 'westus',
        'deployment_version': 'v1.2.3',
    }

# should skip check not using async mode
def should_skip(request, response):
    # Implement your custom logic to skip logging specific API calls to Moesif.
    return "health/probe" in request.url._url

# mask event not using async mode
def mask_event(eventmodel):
    # Ensure the response body exists and is a dictionary
    if eventmodel.response.body and isinstance(eventmodel.response.body, dict):
        # Mask sensitive fields, such as 'password'
        if 'password' in eventmodel.response.body:
            eventmodel.response.body['password'] = None
    return eventmodel

moesif_settings = {
    'APPLICATION_ID': 'Your Moesif Application Id',
    'LOG_BODY': True,
    'DEBUG': True,
    'IDENTIFY_USER': identify_user,
    'IDENTIFY_COMPANY': identify_company,
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

@app.get("/hello")
async def read_main():
    return {"message": "Hello World"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    return {"filename": file.filename, "content_size": len(content)}

@app.post("/submit-form/")
async def submit_form(
    username: str = Form(...),
    email: str = Form(...),
    message: str = Form(default="")
):
    return {
        "username": username,
        "email": email,
        "message": message,
        "status": "success"
    }

# in case you need run with debugger, those lines are needed
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)
