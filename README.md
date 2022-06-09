# Moesif Middleware for Python ASGI based Frameworks

[![Built For][ico-built-for]][link-built-for]
[![Latest Version][ico-version]][link-package]
[![Language Versions][ico-language]][link-language]
[![Software License][ico-license]][link-license]
[![Source Code][ico-source]][link-source]

ASGI middleware that automatically logs _incoming_ or _outgoing_ API calls and sends to [Moesif](https://www.moesif.com) for API analytics and monitoring.
Supports Python Frameworks built on ASGI such as FastAPI and more.

[Source Code on GitHub](https://github.com/moesif/moesifasgi)

[ASGI (Asynchronous Server Gateway Interface)](https://asgi.readthedocs.io/en/latest/)
is a spiritual successor to WSGI, intended to provide a standard interface between async-capable Python web servers, frameworks, and applications. Many Python Frameworks
are build on top of ASGI, such as [FastAPI](https://fastapi.tiangolo.com/), etc.
Moesif ASGI Middleware help APIs that are build on top of these Frameworks to
easily integrate with [Moesif](https://www.moesif.com).

## How to install

```shell
pip install moesifasgi
```

## How to use

### FastAPI

Add Moesif middleware to fastAPI app.

```python
from moesifasgi import MoesifMiddleware

moesif_settings = {
    'APPLICATION_ID': 'Your Moesif Application id',
    'LOG_BODY': True,
    # ... For other options see below.
}

app = FastAPI()

app.add_middleware(MoesifMiddleware, settings=moesif_settings)

```

Your Moesif Application Id can be found in the [_Moesif Portal_](https://www.moesif.com/).
After signing up for a Moesif account, your Moesif Application Id will be displayed during the onboarding steps. 

You can always find your Moesif Application Id at any time by logging 
into the [_Moesif Portal_](https://www.moesif.com/), click on the top right menu,
and then clicking _API Keys_.

For an example with Flask, see example in the `/examples/flask` folder of this repo.

### Other ASGI frameworks

If you are using a framework that is built on top of ASGI, it should work just by adding the Moesif middleware.
Please read the documentation for your specific framework on how to add middleware.

## Configuration options

#### __`APPLICATION_ID`__
(__required__), _string_, is obtained via your Moesif Account, this is required.

For options that use the request and response as input arguments, these use the [Requests](https://www.starlette.io/requests/) and [Responses](https://www.starlette.io/responses/) objects respectively.

#### __`SKIP`__
(optional) _(request, response) => boolean_, a function that takes a request and a response,
and returns true if you want to skip this particular event.

#### __`IDENTIFY_USER`__
(optional, but highly recommended) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the user id used by your system. While Moesif tries to identify users automatically,
but different frameworks and your implementation might be very different, it would be helpful and much more accurate to provide this function.

#### __`IDENTIFY_COMPANY`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the company id for this event.

#### __`GET_METADATA`__
(optional) _(request, response) => dictionary_, a function that takes a request and a response, and
returns a dictionary (must be able to be encoded into JSON). This allows your
to associate this event with custom metadata. For example, you may want to save a VM instance_id, a trace_id, or a tenant_id with the request.

#### __`GET_SESSION_TOKEN`__
(optional) _(request, response) => string_, a function that takes a request and a response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.

#### __`MASK_EVENT_MODEL`__
(optional) _(EventModel) => EventModel_, a function that takes an EventModel and returns an EventModel with desired data removed. The return value must be a valid EventModel required by Moesif data ingestion API. For details regarding EventModel please see the [Moesif Python API Documentation](https://www.moesif.com/docs/api?python).

#### __`DEBUG`__
(optional) _boolean_, a flag to see debugging messages.

#### __`LOG_BODY`__
(optional) _boolean_, default True, Set to False to remove logging request and response body.

#### __`BATCH_SIZE`__
(optional) __int__, default 25, Maximum batch size when sending events to Moesif.

#### __`AUTHORIZATION_HEADER_NAME`__
(optional) _string_, A request header field name used to identify the User in Moesif. Default value is `authorization`. Also, supports a comma separated string. We will check headers in order like `"X-Api-Key,Authorization"`.

#### __`AUTHORIZATION_USER_ID_FIELD`__
(optional) _string_, A field name used to parse the User from authorization header in Moesif. Default value is `sub`.

#### __`BASE_URI`__
(optional) _string_, A local proxy hostname when sending traffic via secure proxy. Please set this field when using secure proxy. For more details, refer [secure proxy documentation.](https://www.moesif.com/docs/platform/secure-proxy/#2-configure-moesif-sdk)

### Options specific to outgoing API calls 

The options below are applicable to outgoing API calls (calls you initiate using the Python [Requests](http://docs.python-requests.org/en/master/) lib to third parties like Stripe or to your own services).

For options that use the request and response as input arguments, these use the [Requests](http://docs.python-requests.org/en/master/api/) lib's request or response objects.

If you are not using ASGI, you can import the [moesifpythonrequest](https://github.com/Moesif/moesifpythonrequest) directly.

#### __`CAPTURE_OUTGOING_REQUESTS`__
_boolean_, Default False. Set to True to capture all outgoing API calls. False will disable this functionality. 

##### __`GET_METADATA_OUTGOING`__
(optional) _(req, res) => dictionary_, a function that enables you to return custom metadata associated with the logged API calls. 
Takes in the [Requests](http://docs.python-requests.org/en/master/api/) request and response object as arguments. You should implement a function that 
returns a dictionary containing your custom metadata. (must be able to be encoded into JSON). For example, you may want to save a VM instance_id, a trace_id, or a resource_id with the request.

##### __`SKIP_OUTGOING`__
(optional) _(req, res) => boolean_, a function that takes a [Requests](http://docs.python-requests.org/en/master/api/) request and response,
and returns true if you want to skip this particular event.

##### __`IDENTIFY_USER_OUTGOING`__
(optional, but highly recommended) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the user id used by your system. While Moesif tries to identify users automatically,
but different frameworks and your implementation might be very different, it would be helpful and much more accurate to provide this function.

##### __`IDENTIFY_COMPANY_OUTGOING`__
(optional) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the company id for this event.

##### __`GET_SESSION_TOKEN_OUTGOING`__
(optional) _(req, res) => string_, a function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very help for tying events together, and help you replay the events.

##### __`LOG_BODY_OUTGOING`__
(optional) _boolean_, default True, Set to False to remove logging request and response body.

### Example:

```python
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

custom_session_token = "XXXXXXXXXXXXXX"

async def custom_get_token():
    # If you don't want to use the standard ASGI session token,
    # add your custom code that returns a string for session/API token
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

skip_route = "health/probe"

async def custom_should_skip(request):
    # Your custom code that returns true to skip logging
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
    'DEBUG': False,
    'LOG_BODY': True,
    'IDENTIFY_USER': identify_user,
    'IDENTIFY_COMPANY': identify_company,
    'GET_SESSION_TOKEN': get_token,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
    'GET_METADATA': get_metadata,
    'CAPTURE_OUTGOING_REQUESTS': False
}

app = FastAPI()

app.add_middleware(MoesifMiddleware, settings=moesif_settings)

```

## Other integrations

To view more documentation on integration options, please visit __[the Integration Options Documentation](https://www.moesif.com/docs/getting-started/integration-options/).__

[ico-built-for]: https://img.shields.io/badge/built%20for-python%20asgi-blue.svg
[ico-version]: https://img.shields.io/pypi/v/moesifasgi.svg
[ico-language]: https://img.shields.io/pypi/pyversions/moesifasgi.svg
[ico-license]: https://img.shields.io/badge/License-Apache%202.0-green.svg
[ico-source]: https://img.shields.io/github/last-commit/moesif/moesifasgi.svg?style=social

[link-built-for]: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
[link-package]: https://pypi.python.org/pypi/moesifasgi
[link-language]: https://pypi.python.org/pypi/moesifasgi
[link-license]: https://raw.githubusercontent.com/Moesif/moesifasgi/master/LICENSE
[link-source]: https://github.com/Moesif/moesifasgi