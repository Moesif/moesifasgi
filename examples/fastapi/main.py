from moesifasgi import MoesifMiddleware
from typing import Optional
import uvicorn

from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# hash password
def get_password_hash(password):
    hashed = pwd_context.hash(password)
    return hashed


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# Create a random secret key that will be used to sign the JWT tokens
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": get_password_hash("johndoe_password"),
        "disabled": False,
    }
}


# Decode the received token, verify it, and return the current user
# If the token is invalid, return an HTTP error right away.
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    # current_user = 1    # TRY 2
    return current_user


custom_user_id = "12345"


async def custom_identify_user_id():
    return custom_user_id


# identify user using async mode
async def identify_user(request, response):
    user_id = await custom_identify_user_id()
    return user_id


# identify user not using async mode
def identify_user(request, response):
    return custom_user_id


# Your custom code that returns a company id string
custom_company_id = "67890"

async def custom_identify_company_id():
    return custom_company_id

# identify company using async mode
async def identify_company(request, response):
    company = await custom_identify_company_id()
    return company

# identify company not using async mode
def identify_company(request, response):
    return custom_company_id

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

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]

# in case you need run with debugger, those lines are needed
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)