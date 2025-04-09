# Moesif Middleware for Python ASGI-based Frameworks

[![Built For][ico-built-for]][link-built-for]
[![Latest Version][ico-version]][link-package]
[![Language Versions][ico-language]][link-language]
[![Software License][ico-license]][link-license]
[![Source Code][ico-source]][link-source]

With Moesif middleware for Python ASGI-based frameworks, you can automatically log API calls 
and send them to [Moesif](https://www.moesif.com) for API analytics and monitoring.

> If you're new to Moesif, see [our Getting Started](https://www.moesif.com/docs/) resources to quickly get up and running.

## Overview

This middleware allows you to easily integrate Moesif's API analytics and 
API monetization service with APIs built on Python ASGI-based (Asynchronous Server Gateway Interface) frameworks including [FastAPI](https://fastapi.tiangolo.com/) and [Starlette](https://www.starlette.io/).

[ASGI](https://asgi.readthedocs.io/en/latest/)
is a spiritual successor to WSGI (Web Server Gateway Interface) enabling async-capable applications.

## Prerequisites
Before using this middleware, make sure you have the following:

- [An active Moesif account](https://moesif.com/wrap)
- [A Moesif Application ID](#get-your-moesif-application-id)

### Get Your Moesif Application ID
After you log into [Moesif Portal](https://www.moesif.com/wrap), you can get your Moesif Application ID during the onboarding steps. You can always access the Application ID any time by following these steps from Moesif Portal after logging in:

1. Select the account icon to bring up the settings menu.
2. Select **Installation** or **API Keys**.
3. Copy your Moesif Application ID from the **Collector Application ID** field.

<img class="lazyload blur-up" src="images/app_id.png" width="700" alt="Accessing the settings menu in Moesif Portal">

## Install the Middleware
Install with `pip` using the following command:

```shell
pip install moesifasgi
```

## Configure the Middleware
See the available [configuration options](#configuration-options) to learn how to configure the middleware for your use case. 

## How to Use

### FastAPI

Simply add `MoesifMiddleware` to a FastAPI application using the `add_middleware` method:

```python
from moesifasgi import MoesifMiddleware

moesif_settings = {
    'APPLICATION_ID': 'YOUR_APPLICATION_ID',
    'LOG_BODY': True,
    # ... For other options see below.
}

app = FastAPI()

app.add_middleware(MoesifMiddleware, settings=moesif_settings)
```

Replace *`YOUR_MOESIF_APPLICATION_ID`* with your [Moesif Application ID](#get-your-moesif-application-id).

### Other ASGI Frameworks

If you are using a framework that is built on top of ASGI, it should work just by adding the Moesif middleware.
Please read the documentation for your specific framework on how to add middlewares.

### Optional: Capturing Outgoing API Calls
In addition to your own APIs, you can also start capturing calls out to third party services through by setting the `CAPTURE_OUTGOING_REQUESTS` option:

```python
from moesifasgi import MoesifMiddleware

moesif_settings = {
    'APPLICATION_ID': 'YOUR_APPLICATION_ID',
    'LOG_BODY': True,
    'CAPTURE_OUTGOING_REQUESTS': False,
}

app = FastAPI()

app.add_middleware(MoesifMiddleware, settings=moesif_settings)
```

For configuration options specific to capturing outgoing API calls, see [Options For Outgoing API Calls](#options-for-outgoing-api-calls).

## Troubleshoot
For a general troubleshooting guide that can help you solve common problems, see [Server Troubleshooting Guide](https://www.moesif.com/docs/troubleshooting/server-troubleshooting-guide/).

Other troubleshooting supports:

- [FAQ](https://www.moesif.com/docs/faq/)
- [Moesif support email](mailto:support@moesif.com)

## Repository Structure

```
.
├── BUILDING.md
├── examples/
├── images/
├── LICENSE
├── MANIFEST.in
├── moesifasgi/
├── README.md
├── requirements.txt
├── setup.cfg
└── setup.py
```

## Configuration Options
The following sections describe the available configuration options for this middleware. You can set these options in a Python dictionary and then pass that as a parameter to `add_middleware` when you add this middleware. See [the sample FastAPI code](https://github.com/Moesif/moesifasgi/blob/1c43c02d2e90b392980371bd4382a609fbdd7f06/examples/fastapi/main.py#L218-L233) for an example.

Some configuration options use request and response as input arguments. These correspond to the [`Requests`](https://www.starlette.io/requests/) and [`Responses`](https://www.starlette.io/responses/) objects respectively.

#### `APPLICATION_ID` (Required)
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
  </tr>
  <tr>
   <td>
    String
   </td>
  </tr>
</table>

A string that [identifies your application in Moesif](#get-your-moesif-application-id).

#### `SKIP`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(request, response)</code>
   </td>
   <td>
    Boolean
   </td>
  </tr>
</table>

Optional.

A function that takes a request and a response,
and returns `True` if you want to skip this particular event.

#### `IDENTIFY_USER`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(request, response)</code>
   </td>
   <td>
    <code>String</code>
   </td>
  </tr>
</table>

Optional, but highly recommended.

A function that takes a request and a response, and returns a string that represents the user ID used by your system. 

Moesif identifies users automatically. However, due to the differences arising from different frameworks and implementations, provide this function to ensure user identification properly.

#### `IDENTIFY_COMPANY`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(request, response)</code>
   </td>
   <td>
    String
   </td>
  </tr>
</table>

Optional. 

A function that takes a request and response, and returns a string that represents the company ID for this event.

#### `GET_METADATA`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(request, response)</code>
   </td>
   <td>
    Dictionary
   </td>
  </tr>
</table>

Optional.

This function allows you
to add custom metadata that Moesif can associate with the event. The metadata must be a simple Python dictionary that can be converted to JSON. 

For example, you may want to save a virtual machine instance ID, a trace ID, or a resource ID with the request.

#### `GET_SESSION_TOKEN`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(request, response)</code>
   </td>
   <td>
    String
   </td>
  </tr>
</table>

Optional.

A function that takes a request and response, and returns a string that represents the session token for this event. 

Similar to users and companies, Moesif tries to retrieve session tokens automatically. But if it doesn't work for your service, provide this function to help identify sessions.

#### `MASK_EVENT_MODEL`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(EventModel)</code>
   </td>
   <td>
    <code>EventModel</code>
   </td>
  </tr>
</table>

Optional.

A function that takes the final Moesif event model and returns an event model with desired data removed. 

The return value must be a valid eventt model required by Moesif data ingestion API. For more information about the `EventModel` object, see the [Moesif Python API documentation](https://www.moesif.com/docs/api?python).

#### `DEBUG`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
  </tr>
  <tr>
   <td>
    Boolean
   </td>
  </tr>
</table>

Optional.

Set to `True` to print debug logs if you're having integration issues.

#### `LOG_BODY`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default
   </th>
  </tr>
  <tr>
   <td>
    Boolean
   </td>
   <td>
    <code>True</code>
   </td>
  </tr>
</table>

Optional.

Whether to log request and response body to Moesif.

#### `BATCH_SIZE`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default
   </th>
  </tr>
  <tr>
   <td>
    <code>int</code>
   </td>
   <td>
    <code>100</code>
   </td>
  </tr>
</table>

An optional field name that specifies the maximum batch size when sending to Moesif.

#### `EVENT_BATCH_TIMEOUT`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default
   </th>
  </tr>
  <tr>
   <td>
    <code>int</code>
   </td>
   <td>
    <code>1</code>
   </td>
  </tr>
</table>

Optional.

Maximum time in seconds to wait before sending a batch of events to Moesif when reading from the queue.

#### `EVENT_QUEUE_SIZE`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default
   </th>
  </tr>
  <tr>
   <td>
    <code>int</code>
   </td>
   <td>
    <code>1000000</code>
   </td>
  </tr>
</table>

Optional.

The maximum number of event objects queued in memory pending upload to Moesif. For a full queue, additional calls to `MoesifMiddleware` returns immediately without logging the event. Therefore, set this option based on the event size and memory capacity you expect.

#### `AUTHORIZATION_HEADER_NAME`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default 
   </th>
  </tr>
  <tr>
   <td>
    String
   </td>
   <td>
    <code>authorization</code>
   </td>
  </tr>
</table>

Optional.

A request header field name used to identify the User in Moesif. It also supports a comma separated string. Moesif checks headers in order like `"X-Api-Key,Authorization"`.

#### `AUTHORIZATION_USER_ID_FIELD`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default 
   </th>
  </tr>
  <tr>
   <td>
    String
   </td>
   <td>
    <code>sub</code>
   </td>
  </tr>
</table>

Optional.

A field name used to parse the user from authorization header in Moesif.

#### `BASE_URI`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
  </tr>
  <tr>
   <td>
    String
   </td>
  </tr>
</table>

Optional.

A local proxy hostname when sending traffic through secure proxy. Remember to set this field when using secure proxy. For more information, see [Secure Proxy documentation.](https://www.moesif.com/docs/platform/secure-proxy/#2-configure-moesif-sdk).

### Options For Outgoing API Calls

The following options apply to outgoing API calls. These are calls you initiate using the Python [Requests](http://docs.python-requests.org/en/master/) library to third parties like Stripe or to your own services.

Several options use request and response as input arguments. These correspond to the [Requests](http://docs.python-requests.org/en/master/api/) library's request or response objects.

If you are not using ASGI, you can import [`moesifpythonrequest`](https://github.com/Moesif/moesifpythonrequest) directly.

#### `CAPTURE_OUTGOING_REQUESTS` (Required)
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default 
   </th>
  </tr>
  <tr>
   <td>
    Boolean
   </td>
   <td>
    <code>False</code>
   </td>
  </tr>
</table>

Set to `True` to capture all outgoing API calls.

##### `GET_METADATA_OUTGOING`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(req, res)</code>
   </td>
   <td>
    Dictionary
   </td>
  </tr>
</table>

Optional.

A function that enables you to return custom metadata associated with the logged API calls.

Takes in the [Requests](http://docs.python-requests.org/en/master/api/) request and response objects as arguments. 

We recommend that you implement a function that
returns a dictionary containing your custom metadata. The dictionary must be a valid one that can be encoded into JSON. For example, you may want to save a virtual machine instance ID, a trace ID, or a resource ID with the request.

##### `SKIP_OUTGOING`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(req, res)</code>
   </td>
   <td>
    Boolean
   </td>
  </tr>
</table>

Optional.

A function that takes a [Requests](http://docs.python-requests.org/en/master/api/) request and response objects,
and returns `True` if you want to skip this particular event.

##### `IDENTIFY_USER_OUTGOING`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(req, res)</code>
   </td>
   <td>
    String
   </td>
  </tr>
</table>

Optional, but highly recommended.

A function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response objects, and returns a string that represents the user ID used by your system. 

While Moesif tries to identify users automatically, different frameworks and your implementation might vary. So we highly recommend that you accurately provide a 
user ID using this function.

##### `IDENTIFY_COMPANY_OUTGOING`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(req, res)</code>
   </td>
   <td>
    String
   </td>
  </tr>
</table>

Optional.

A function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response objects, and returns a string that represents the company ID for this event.

##### `GET_SESSION_TOKEN_OUTGOING`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Parameters
   </th>
   <th scope="col">
    Return type
   </th>
  </tr>
  <tr>
   <td>
    Function
   </td>
   <td>
    <code>(req, res)</code>
   </td>
   <td>
    String
   </td>
  </tr>
</table>

Optional.

A function that takes [Requests](http://docs.python-requests.org/en/master/api/) request and response objects, and returns a string that corresponds to the session token for this event. 

Similar to [user IDs](#identify_user_outgoing), Moesif tries to get the session token automatically. However, if you setup differs from the standard, this function can help tying up events together and help you replay the events.

##### `LOG_BODY_OUTGOING`
<table>
  <tr>
   <th scope="col">
    Data type
   </th>
   <th scope="col">
    Default
   </th>
  </tr>
  <tr>
   <td>
    Boolean
   </td>
   <td>
    <code>True</code>
   </td>
  </tr>
</table>

Optional.

Set to `False` to remove logging request and response body.

## Examples
See the example FastAPI app in the `examples/` folder of this repository that uses this middleware.

Here's another sample FastAPI app:

```python
# identify user not using async mode
def identify_user(request, response):
    return "12345"

# identify company not using async mode
def identify_company(request, response):
    return "67890"

# get metadata not using async mode
def get_metadata(request, response):
    return {
        'datacenter': 'westus',
        'deployment_version': 'v1.2.3',
    }

# should skip check not using async mode
def should_skip(request, response):
    return "health/probe" in request.url._url

# mask event not using async mode
def mask_event(eventmodel):
    # Your custom code to change or remove any sensitive fields
    if 'password' in eventmodel.response.body:
        eventmodel.response.body['password'] = None
    return eventmodel


moesif_settings = {
    'APPLICATION_ID': 'YOUR_MOESIF_APPLICATION_ID',
    'LOG_BODY': True,
    'DEBUG': False,
    'IDENTIFY_USER': identify_user,
    'IDENTIFY_COMPANY': identify_company,
    'GET_METADATA': get_metadata,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
    'CAPTURE_OUTGOING_REQUESTS': False,
}

app = FastAPI()

app.add_middleware(MoesifMiddleware, settings=moesif_settings)
```

You can use OAuth2 in your FastAPI app with this middleware. For more information, see [OAuth2 with Password (and hashing), Bearer with JWT tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).

## Tested versions

Moesif has validated this middleware against the following frameworks and framework versions:

| Framework | Version |
|---------|-------------------|
| fastapi | > 0.51.0 |
| fastapi | > 0.78.0 |
| fastapi | > 0.108.0 |
| fastapi | > 0.115.5 |

## Examples
- [View example app with FastAPI](https://github.com/Moesif/moesifasgi/tree/master/examples/fastapi).


## Explore Other Integrations

Explore other integration options from Moesif:

- [Server integration options documentation](https://www.moesif.com/docs/server-integration//)
- [Client integration options documentation](https://www.moesif.com/docs/client-integration/)

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