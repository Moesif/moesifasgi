from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime
from moesifapi.moesif_api_client import *
from moesifapi.app_config import AppConfig
from .async_iterator_wrapper import async_iterator_wrapper
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper
from .event_logger import EventLogger
from moesifapi.update_companies import Company
from moesifapi.update_users import User
from starlette.middleware.base import _StreamingResponse
from moesifpythonrequest.start_capture.start_capture import StartCapture
from moesifapi.config_manager import ConfigUpdateManager
from moesifapi.workers import ConfigJobScheduler
from moesifapi.parse_body import ParseBody
from starlette.types import Message
from importlib.metadata import version
try:
    from packaging.version import Version as LooseVersion
except ImportError:
    try:
        from distutils.version import LooseVersion
    except ImportError as e:
        raise ImportError("Neither 'packaging' nor 'distutils' is available. ") from e
import math
import random
import logging
import json
import time
import starlette.datastructures
from .version import read_version

logger = logging.getLogger(__name__)


class MoesifMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware for recording of request-response"""
    def __init__(self, app=None, settings=None, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        if settings is None:
            raise Exception('settings is not set. Ensure MoesifMiddleware is initialized with settings')
            return

        if not isinstance(settings, dict):
            raise Exception('settings is not a dictionary. Ensure MoesifMiddleware is initialized with a settings dictionary')
            return

        if 'APPLICATION_ID' not in settings:
            raise Exception('APPLICATION_ID was not defined in settings. APPLICATION_ID is a required field')
            return

        self.settings = settings
        self.DEBUG = self.settings.get('DEBUG', False)

        self.initialize_logger()
        self.validate_settings()

        self.initialize_counter()
        self.initialize_client()
        self.initialize_config()

        if self.settings.get('CAPTURE_OUTGOING_REQUESTS', False):
            try:
                if self.DEBUG:
                    logger.info('Start capturing outgoing requests')
                # Start capturing outgoing requests
                StartCapture().start_capture_outgoing(self.settings)
            except:
                logger.warning('Error while starting to capture the outgoing events')

        self.disable_transaction_id = self.settings.get('DISABLED_TRANSACTION_ID', False)
        self.starlette_version = version('starlette')

    def initialize_logger(self):
        """Initialize logger mirroring the debug and stdout behavior of previous print statements for compatibility"""
        logging.basicConfig(
            level=logging.DEBUG if self.DEBUG else logging.INFO,
            format='%(asctime)s\t%(levelname)s\tPID: %(process)d\tThread: %(thread)d\t%(funcName)s\t%(message)s',
            handlers=[logging.StreamHandler()]
        )

    def log_checkpoint(self, request_mo_start_time, description: str):
        if self.DEBUG and request_mo_start_time is not None:
            current_time = time.perf_counter()
            elapsed_time_ms = (current_time - request_mo_start_time) * 1000
            logger.info(f"{description}: {elapsed_time_ms:.2f} milliseconds")

    def validate_settings(self):
        if self.settings is None or not self.settings.get("APPLICATION_ID", None):
            raise Exception("Moesif Application ID is required in settings")
    def initialize_counter(self):
        self.dropped_events = 0
        self.logger_helper = LoggerHelper()
        self.event_mapper = EventMapper()
        self.parse_body = ParseBody()

    def initialize_client(self):
        Configuration.BASE_URI = self.settings.get("BASE_URI", "https://api.moesif.net")
        Configuration.version = f'moesifasgi-python/{read_version()}'
        self.LOG_BODY = self.settings.get("LOG_BODY", True)
        self.api_version = self.settings.get("API_VERSION")
        self.client = MoesifAPIClient(self.settings.get("APPLICATION_ID"))
        self.api_client = self.client.api

    def schedule_config_job(self):
        try:
            ConfigJobScheduler(self.DEBUG, self.config).schedule_background_job()
            self.is_config_job_scheduled = True
        except Exception as ex:
            self.is_config_job_scheduled = False
            if self.DEBUG:
                logger.info(f'Error while starting the config scheduler job in background: {str(ex)}')

    def initialize_config(self):
        self.app_config = AppConfig()
        self.config = ConfigUpdateManager(self.api_client, self.app_config, self.DEBUG)
        self.schedule_config_job()
        self.event_logger = EventLogger(self.settings, self.config, self.api_client, self.DEBUG)

    def update_user(self, user_profile):
        User().update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        User().update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        Company().update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        Company().update_companies_batch(companies_profiles, self.api_client, self.DEBUG)

    def set_body(self, request: Request, body: bytes):
        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request._receive = receive

    def set_form_data_body(self, request: Request, form_data: starlette.datastructures.FormData):
        # Extract boundary from the Content-Type header
        content_type = request.headers.get("content-type", "")
        boundary = content_type.split("boundary=")[
            -1] if "boundary=" in content_type else "------------------------boundary_string"

        # Store the original receive function
        original_receive = request._receive

        async def receive() -> Message:
            # Create the multipart body for logging purposes
            multipart_body = []

            for key, value in form_data.items():
                multipart_body.append(f'--{boundary}')
                multipart_body.append(f'Content-Disposition: form-data; name="{key}"')

                if isinstance(value, str):
                    multipart_body.append('')
                    multipart_body.append(value)
                elif hasattr(value, 'filename'):
                    multipart_body.append(f'Content-Disposition: form-data; name="{key}"; filename="{value.filename}"')
                    multipart_body.append('Content-Type: application/octet-stream')
                    multipart_body.append('')
                    # Read the file content for logging purposes
                    file_content = await value.read()
                    multipart_body.append(file_content)
                    # Reset the file stream so it can be read again downstream
                    value.file.seek(0)

            # Add the closing boundary
            multipart_body.append(f'--{boundary}--')

            # Log the multipart body without modifying the request
            body_bytes = b'\r\n'.join(
                part.encode('utf-8') if isinstance(part, str) else part for part in multipart_body
            )
            logger.debug(f"Multipart body (for logging only): {body_bytes}")

            # Return the original request body unchanged
            return await original_receive()

        # Override the request's receive method
        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        # In higher version of Starlette(>0.27.0), we could read the body on the middleware without hanging
        # Reference: https://github.com/tiangolo/fastapi/discussions/8187#discussioncomment-7962881
        if LooseVersion(self.starlette_version) < LooseVersion("0.29.0"):
            self.set_body(request, body)
        self.log_checkpoint(request.mo_start_time, "Get Body")
        return body

    async def get_form_data(self, request: Request):
        try:
            # First, get the raw body content
            body = await request.body()

            # Create a copy of the request with the body content
            async def receive() -> Message:
                return {"type": "http.request", "body": body, "more_body": False}

            # Store the original receive function
            original_receive = request._receive

            # Set our temporary receive function to get the form data
            request._receive = receive

            # Process the form data
            form = await request.form()

            # Create JSON representation for logging
            json_data = {}
            for key, value in form.items():
                if isinstance(value, str):
                    json_data[key] = value
                elif hasattr(value, 'filename'):
                    # If the value is an UploadFile, store the filename
                    json_data[key] = value.filename

            if LooseVersion(self.starlette_version) < LooseVersion("0.29.0"):
                self.set_form_data_body(request, body)

            self.log_checkpoint(request.mo_start_time, "Get form data")
            return json.dumps(json_data).encode('utf-8')
        except Exception as e:
            logger.error(f"Error processing form data: {str(e)}")
            return None

    @classmethod
    def get_time(cls):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    # Prepare response for the governance rule
    def prepare_response_content(self, body, request_mo_start_time):
        response_content = None
        try:
            response_content = body[0]
        except Exception as ex:
            if self.DEBUG:
                logger.info(f"Error while preparing the response content: {str(ex)}")
        self.log_checkpoint(request_mo_start_time, "Prepare response content")
        return response_content

    async def dispatch(self, request, call_next):
        if self.DEBUG:
            request.mo_start_time = time.perf_counter()
        else:
            request.mo_start_time = None

        # request time
        request_time = self.get_time()
        if self.DEBUG:
            logger.info(f"event request time: {str(request_time)}")
        self.log_checkpoint(request.mo_start_time, "Request time", )

        # Request headers
        request_headers = dict(request.headers)
        self.log_checkpoint(request.mo_start_time, "Request header")

        # Check if multipart/form-data payload
        is_multi_part_request_upload = self.parse_body.is_multi_part_upload(request_headers)
        self.log_checkpoint(request.mo_start_time, "Multipart form-data Request")

        # Read Request Body
        request_body = None
        if self.LOG_BODY:
            if is_multi_part_request_upload:
                request_body = await self.get_form_data(request)
            else:
                request_body = await self.get_body(request)
        self.log_checkpoint(request.mo_start_time, "Request body")

        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(request, request_time, request_headers, request_body, self.api_version,
                                                 self.disable_transaction_id, self.DEBUG)
        self.log_checkpoint(request.mo_start_time, "Request Model")

        governed_response = {}
        if self.config.have_governance_rules():
            # we must fire these hooks early.
            user_id = await self.logger_helper.get_user_id(self.settings, request, None, request_headers, self.DEBUG)
            self.log_checkpoint(request.mo_start_time, "User Id")
            company_id = await self.logger_helper.get_company_id(self.settings, request, None, self.DEBUG)
            self.log_checkpoint(request.mo_start_time, "Company Id")
            governed_response = self.config.govern_request(event_req, user_id, company_id, event_req.body, request_headers)
            self.log_checkpoint(request.mo_start_time, "Governed response")

        blocked_by = None
        if 'blocked_by' in governed_response:
            # start response immediately, skip next step
            response_content = self.prepare_response_content(governed_response['body'], request.mo_start_time)
            blocked_by = governed_response['blocked_by']
            async def generate_data():
                yield response_content
            headers = {k: self.logger_helper.sanitize_header_value(v) for k, v in governed_response['headers'].items() }
            response = _StreamingResponse(content=generate_data(), status_code=governed_response['status'], headers=headers)
            self.log_checkpoint(request.mo_start_time, "Blocked By")
        else:
            # Call the next middleware
            response = await call_next(request)
            self.log_checkpoint(request.mo_start_time, "Next mw")

        # response time
        response_time = self.get_time()
        if self.DEBUG:
            logger.info(f"event response time: {str(response_time)}")
        self.log_checkpoint(request.mo_start_time, "Response time")

        # Check if needs to skip the event
        skip = await self.logger_helper.should_skip(self.settings, request, response, self.DEBUG)
        if skip:
            if self.DEBUG:
                logger.info("Skipped Event using should_skip configuration option")
            return response
        self.log_checkpoint(request.mo_start_time, "Skip event")

        # Response headers
        response_headers = dict(response.headers)
        self.log_checkpoint(request.mo_start_time, "Response header")

        # Check if multipart/form-data payload
        is_multi_part_response_upload = self.parse_body.is_multi_part_upload(response_headers)
        self.log_checkpoint(request.mo_start_time, "Multipart form-data Response")

        # Read Response Body
        resp_body = None

        # Prepare Event Response Model
        event_rsp = self.event_mapper.to_response(response, response_time, response_headers, resp_body)
        self.log_checkpoint(request.mo_start_time, "Response Model")

        # Add user, company, session_token, and metadata
        user_id = await self.logger_helper.get_user_id(self.settings, request, response, request_headers, self.DEBUG)
        company_id = await self.logger_helper.get_company_id(self.settings, request, response, self.DEBUG)
        session_token = await self.logger_helper.get_session_token(self.settings, request, response, self.DEBUG)
        metadata = await self.logger_helper.get_metadata(self.settings, request, response, self.DEBUG)
        self.log_checkpoint(request.mo_start_time, "Get Entity")

        # Prepare Event Model
        event_data = await self.event_mapper.to_event(event_req, event_rsp, user_id, company_id, session_token, metadata, blocked_by)
        self.log_checkpoint(request.mo_start_time, "Event model")

        # Mask Event Model
        if self.logger_helper.is_coroutine_function(self.logger_helper.mask_event):
            event_data = await self.logger_helper.mask_event(event_data, self.settings, self.DEBUG)
        else:
            event_data = self.logger_helper.mask_event(event_data, self.settings, self.DEBUG)

        # Sampling percentage
        self.sampling_percentage = self.config.get_sampling_percentage(event_data, user_id, company_id)
        if self.sampling_percentage != 100:
            random_percentage = random.random() * 100

            if random_percentage >= self.sampling_percentage:
                logger.info(f"Skipped Event due to sampling percentage: {str(self.sampling_percentage)}"
                            f" and random percentage: {str(random_percentage)}")
                return response
        else:
            self.sampling_percentage = 100

        # Add Weight to the event
        event_data.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)

        # mask_event_sampling_end = time.perf_counter()
        self.log_checkpoint(request.mo_start_time, "Mask Event and sampling")

        resp_body = None
        if self.LOG_BODY and not is_multi_part_response_upload:
            async def log_body(body_iterator):
                nonlocal resp_body, event_data
                body_chunks = []
                async for chunk in body_iterator:
                    body_chunks.append(chunk)
                    yield chunk
                resp_body = b"".join(body_chunks)
                body, transfer_encoding = self.event_mapper.parse(resp_body, response_headers)
                event_data.response.body = body
                event_data.response.transfer_encoding = transfer_encoding
                self.event_logger.log_event(event_data)

            response.body_iterator = log_body(response.body_iterator)
        else:
            self.event_logger.log_event(event_data)

        self.log_checkpoint(request.mo_start_time, "Response body and/or log event")

        self.log_checkpoint(request.mo_start_time, "Dispatch")

        return response
