from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from datetime import datetime
from moesifapi.moesif_api_client import *
from moesifapi.app_config import AppConfig
from .async_iterator_wrapper import async_iterator_wrapper
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper
from moesifapi.update_companies import Company
from moesifapi.update_users import User
from starlette.middleware.base import _StreamingResponse
from moesifpythonrequest.start_capture.start_capture import StartCapture
from moesifapi.config_manager import ConfigUpdateManager
from moesifapi.workers import BatchedWorkerPool, ConfigJobScheduler
from moesifapi.parse_body import ParseBody
from starlette.types import Message
from importlib.metadata import version
from distutils.version import LooseVersion
import math
import random
import logging
import json
import starlette.datastructures

logger = logging.getLogger(__name__)


class MoesifMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware for recording of request-response"""
    def __init__(self, settings=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        if settings is None:
            raise Exception('Moesif Application ID is required in settings')
        self.settings = settings
        self.DEBUG = self.settings.get('DEBUG', False)

        self.initialize_logger()
        self.validate_settings()

        self.initialize_counter()
        self.initialize_client()
        self.initialize_config()
        self.initialize_worker_pool()

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

    def validate_settings(self):
        if self.settings is None or not self.settings.get("APPLICATION_ID", None):
            raise Exception("Moesif Application ID is required in settings")
    def initialize_counter(self):
        self.dropped_events = 0
        self.logger_helper = LoggerHelper()
        self.event_mapper = EventMapper()
        self.parse_body = ParseBody()

    def initialize_client(self):
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
        Configuration.BASE_URI = self.settings.get("BASE_URI", "https://api.moesif.net")
        Configuration.version = 'moesifasgi-python/1.0.7'
        self.LOG_BODY = self.settings.get("LOG_BODY", True)

        self.app_config = AppConfig()
        self.config = ConfigUpdateManager(self.api_client, self.app_config, self.DEBUG)
        self.schedule_config_job()

    def initialize_worker_pool(self):
        # Create queues and threads which will batch and send events in the background
        self.worker_pool = BatchedWorkerPool(
            worker_count=self.settings.get("EVENT_WORKER_COUNT", 2),
            api_client=self.api_client,
            config=self.config,
            debug=self.DEBUG,
            max_queue_size=self.settings.get("EVENT_QUEUE_SIZE", 1000000),
            batch_size=self.settings.get("BATCH_SIZE", 100),
            timeout=self.settings.get("EVENT_BATCH_TIMEOUT", 1),
        )

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
        async def receive() -> Message:
            # Create the multipart body
            multipart_body = []

            # Iterate through the FormData and construct the multipart body
            for key, value in form_data.items():
                multipart_body.append(f'--{boundary}')
                multipart_body.append(f'Content-Disposition: form-data; name="{key}"')

                if isinstance(value, str):
                    multipart_body.append('')
                    multipart_body.append(value)
                elif hasattr(value, 'filename'):
                    multipart_body.append(f'Content-Disposition: form-data; name="{key}"; filename="{value.filename}"')
                    multipart_body.append('Content-Type: application/octet-stream')  # Set appropriate content type
                    multipart_body.append('')
                    # Read the file content as bytes
                    file_content = await value.read()
                    multipart_body.append(file_content)  # Append bytes directly

            # Add the closing boundary
            multipart_body.append(f'--{boundary}--')

            # Join the parts and encode them as bytes
            # Convert all string parts to bytes before joining
            body_bytes = b'\r\n'.join(
                part.encode('utf-8') if isinstance(part, str) else part for part in multipart_body)

            return {"type": "http.request", "body": body_bytes}

        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        # In higher version of Starlette(>0.27.0), we could read the body on the middleware without hanging
        # Reference: https://github.com/tiangolo/fastapi/discussions/8187#discussioncomment-7962881
        if LooseVersion(self.starlette_version) < LooseVersion("0.29.0"):
            self.set_body(request, body)
        return body

    async def get_form_data(self, request: Request):
        try:
            json_data = {}
            body = await request.form()

            # Iterate through the form data
            for key, value in body.items():
                if isinstance(value, str):
                    # If the value is a string, just add it to the JSON
                    json_data[key] = value
                elif hasattr(value, 'filename'):
                    # If the value is an UploadFile, store the filename
                    json_data[key] = value.filename

            if LooseVersion(self.starlette_version) < LooseVersion("0.29.0"):
                self.set_form_data_body(request, body)

            return json.dumps(json_data).encode('utf-8')
        except:
            return None

    @classmethod
    def get_time(cls):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    # Prepare response for the governance rule
    def prepare_response_content(self, body):
        response_content = None
        try:
            response_content = body[0]
        except Exception as ex:
            if self.DEBUG:
                logger.info(f"Error while preparing the response content: {str(ex)}")
        return response_content

    async def dispatch(self, request, call_next):
        # request time
        request_time = self.get_time()
        if self.DEBUG:
            logger.info(f"event request time: {str(request_time)}")

        # Request headers
        request_headers = dict(request.headers)
        # Check if multipart/form-data payload
        is_multi_part_request_upload = self.parse_body.is_multi_part_upload(request_headers)

        # Read Request Body
        request_body = None
        if self.LOG_BODY:
            if is_multi_part_request_upload:
                request_body = await self.get_form_data(request)
            else:
                request_body = await self.get_body(request)

        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(request, request_time, request_body, self.api_version,
                                                 self.disable_transaction_id, self.DEBUG)

        governed_response = {}
        if self.config.have_governance_rules():
            # we must fire these hooks early.
            user_id = await self.logger_helper.get_user_id(self.settings, request, None, dict(request.headers), self.DEBUG)
            company_id = await self.logger_helper.get_company_id(self.settings, request, None, self.DEBUG)
            governed_response = self.config.govern_request(event_req, user_id, company_id, event_req.body)

        blocked_by = None
        if 'blocked_by' in governed_response:
            # start response immediately, skip next step
            response_content = self.prepare_response_content(governed_response['body'])
            blocked_by = governed_response['blocked_by']
            async def generate_data():
                yield response_content
            headers = {k: self.logger_helper.sanitize_header_value(v) for k, v in governed_response['headers'].items() }
            response = _StreamingResponse(content=generate_data(), status_code=governed_response['status'], headers=headers)
        else:
            # Call the next middleware
            response = await call_next(request)

        # response time
        response_time = self.get_time()
        if self.DEBUG:
            logger.info(f"event response time: {str(response_time)}")

        # Check if needs to skip the event
        skip = await self.logger_helper.should_skip(self.settings, request, response, self.DEBUG)
        if skip:
            if self.DEBUG:
                logger.info("Skipped Event using should_skip configuration option")
            return response

        # Response headers
        response_headers = dict(response.headers)
        # Check if multipart/form-data payload
        is_multi_part_response_upload = self.parse_body.is_multi_part_upload(response_headers)

        # Read Response Body
        resp_body = None
        if self.LOG_BODY and not is_multi_part_response_upload:
            # Consuming FastAPI response and grabbing body here
            resp_body = [section async for section in response.__dict__['body_iterator']]
            # Preparing FastAPI response
            response.__setattr__('body_iterator', async_iterator_wrapper(resp_body))

        # Prepare Event Response Model
        event_rsp = self.event_mapper.to_response(response, response_time, resp_body)

        # Add user, company, session_token, and metadata
        user_id = await self.logger_helper.get_user_id(self.settings, request, response, dict(request.headers), self.DEBUG)
        company_id = await self.logger_helper.get_company_id(self.settings, request, response, self.DEBUG)
        session_token = await self.logger_helper.get_session_token(self.settings, request, response, self.DEBUG)
        metadata = await self.logger_helper.get_metadata(self.settings, request, response, self.DEBUG)

        # Prepare Event Model
        event_data = await self.event_mapper.to_event(event_req, event_rsp, user_id, company_id, session_token, metadata, blocked_by)

        # Mask Event Model
        if self.logger_helper.is_coroutine_function(self.logger_helper.mask_event):
            event_data = await self.logger_helper.mask_event(event_data, self.settings, self.DEBUG)
        else:
            event_data = self.logger_helper.mask_event(event_data, self.settings, self.DEBUG)

        # Sampling percentage
        random_percentage = random.random() * 100
        self.sampling_percentage = self.config.get_sampling_percentage(event_data, user_id, company_id)

        # Add Weight to the event
        event_data.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)

        if random_percentage >= self.sampling_percentage:
            logger.info(f"Skipped Event due to sampling percentage: {str(self.sampling_percentage)}"
                         f" and random percentage: {str(random_percentage)}")
            return response

        try:
            # Add Event to the queue if able and count the dropped event if at capacity
            if self.worker_pool.add_event(event_data):
                logger.debug("Add Event to the queue")
                if self.DEBUG:
                    logger.info(f"Event added to the queue: {APIHelper.json_serialize(event_data)}")
            else:
                self.dropped_events += 1
                logger.info(f"Dropped Event due to queue capacity drop_count: {str(self.dropped_events)}")
                if self.DEBUG:
                    logger.info(f"Event dropped: {APIHelper.json_serialize(event_data)}")
        # add_event does not throw exceptions so this is unexepected
        except Exception as ex:
            logger.exception(f"Error while adding event to the queue: {str(ex)}")

        return response
