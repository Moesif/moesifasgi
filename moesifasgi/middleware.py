from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from moesifapi.moesif_api_client import *
from .send_batch_events import SendEventAsync
from .app_config import AppConfig
from .async_iterator_wrapper import async_iterator_wrapper
from .logger_helper import LoggerHelper
from .parse_body import ParseBody
from .event_mapper import EventMapper
from .update_companies import Company
from .update_users import User
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from moesifpythonrequest.start_capture.start_capture import StartCapture
from starlette.types import Message
import logging
import math
import random
import queue
import atexit


class MoesifMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware for recording of request-response"""
    def __init__(self, settings=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        if settings is None:
            raise Exception('Moesif Application ID is required in settings')
        self.moesif_settings = settings
       
        if self.moesif_settings.get('APPLICATION_ID', None):
            self.client = MoesifAPIClient(self.moesif_settings.get('APPLICATION_ID'))
        else:
            raise Exception('Moesif Application ID is required in settings')
        self.DEBUG = self.moesif_settings.get('DEBUG', False)
        if self.DEBUG:
            Configuration.BASE_URI = self.moesif_settings.get('BASE_URI', 'https://api.moesif.net')
        Configuration.version = 'moesifasgi-python/0.0.2'
        if self.moesif_settings.get('CAPTURE_OUTGOING_REQUESTS', False):
            try:
                if self.DEBUG:
                    print('Start capturing outgoing requests')
                # Start capturing outgoing requests
                StartCapture().start_capture_outgoing(self.moesif_settings)
            except:
                print('Error while starting to capture the outgoing events')
        self.api_client = self.client.api
        self.app_config = AppConfig()
        self.send_async_events = SendEventAsync()
        self.logger_helper = LoggerHelper()
        self.parse_body = ParseBody()
        self.event_mapper = EventMapper()
        self.sampling_percentage = 100
        self.last_updated_time = datetime.utcnow()
        self.disable_transaction_id = self.moesif_settings.get('DISABLED_TRANSACTION_ID', False)
        self.moesif_events_queue = queue.Queue()
        self.BATCH_SIZE = self.moesif_settings.get('BATCH_SIZE', 25)
        self.last_event_job_run_time = datetime(1970, 1, 1, 0, 0)  # Assuming job never ran, set it to epoch start time
        self.scheduler = None
        self.config_etag = None
        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
        self.is_event_job_scheduled = False
        self.api_version = self.moesif_settings.get('API_VERSION')
        self.LOG_BODY = self.moesif_settings.get('LOG_BODY', True)
        try:
            if self.config:
                self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                    self.config, self.DEBUG)
        except Exception as ex:
            if self.DEBUG:
                print('Error while parsing application configuration on initialization')
                print(str(ex))

    # Function to listen to the send event job response
    def moesif_event_listener(self, event):
        if event.exception:
            if self.DEBUG:
                print('Error reading response from the scheduled job')
        else:
            if event.retval:
                response_etag, self.last_event_job_run_time = event.retval
                if response_etag is not None \
                    and self.config_etag is not None \
                    and self.config_etag != response_etag \
                        and datetime.utcnow() > self.last_updated_time + timedelta(minutes=5):
                    try:
                        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
                        self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                            self.config, self.DEBUG)
                    except Exception as ex:
                        if self.DEBUG:
                            print('Error while updating the application configuration')
                            print(str(ex))

    def schedule_background_job(self):
        try:
            if not self.scheduler:
                self.scheduler = BackgroundScheduler(daemon=True)
            if not self.scheduler.get_jobs():
                self.scheduler.add_listener(self.moesif_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
                self.scheduler.start()
                self.scheduler.add_job(
                    func=lambda: self.send_async_events.batch_events(self.api_client, self.moesif_events_queue,
                                                                     self.DEBUG, self.BATCH_SIZE),
                    trigger=IntervalTrigger(seconds=2),
                    id='moesif_events_batch_job',
                    name='Schedule events batch job every 2 second',
                    replace_existing=True)

                # Avoid passing logging message to the ancestor loggers
                logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
                logging.getLogger('apscheduler.executors.default').propagate = False

                # Exit handler when exiting the app
                atexit.register(lambda: self.send_async_events.exit_handler(self.scheduler, self.DEBUG))
        except Exception as ex:
            if self.DEBUG:
                print("Error when scheduling the job")
                print(str(ex))

    def update_user(self, user_profile):
        User().update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        User().update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        Company().update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        Company().update_companies_batch(companies_profiles, self.api_client, self.DEBUG)

    async def set_body(self, request):
        receive_ = await request._receive()

        async def receive() -> Message:
            return receive_

        request._receive = receive

    async def dispatch(self, request, call_next):

        await self.set_body(request)

        # Read Request Body
        request_body = None
        if self.LOG_BODY:
            request_body = await request.body()

        # Call the next middleware
        response = await call_next(request)

        if not self.logger_helper.should_skip(self.moesif_settings, request, response, self.DEBUG):
            random_percentage = random.random() * 100

            self.sampling_percentage = self.app_config.get_sampling_percentage(self.config,
                                                                               self.logger_helper.get_user_id(self.moesif_settings, request, response, request.headers, self.DEBUG),
                                                                               self.logger_helper.get_company_id(self.moesif_settings, request, response, self.DEBUG))

            if self.sampling_percentage >= random_percentage:
                # Prepare Event Request Model
                event_req = self.event_mapper.to_request(request, request_body, self.api_version, self.disable_transaction_id)

                # Read Response Body
                resp_body = None
                if self.LOG_BODY:
                    # Consuming FastAPI response and grabbing body here
                    resp_body = [section async for section in response.__dict__['body_iterator']]
                    # Preparing FastAPI response
                    response.__setattr__('body_iterator', async_iterator_wrapper(resp_body))

                # Prepare Event Response Model
                event_rsp = self.event_mapper.to_response(response, resp_body)
                # Prepare Event Model
                event_data = self.event_mapper.to_event(request, response, event_req, event_rsp, self.moesif_settings,
                                                         self.DEBUG)

                # Mask Event Model
                event_data = self.logger_helper.mask_event(event_data, self.moesif_settings, self.DEBUG)

                if event_data:
                    # Add Weight to the event
                    event_data.weight = 1 if self.sampling_percentage == 0 else math.floor(100 / self.sampling_percentage)
                    try:
                        if not self.is_event_job_scheduled and datetime.utcnow() > self.last_event_job_run_time + timedelta(
                                minutes=5):
                            try:
                                self.schedule_background_job()
                                self.is_event_job_scheduled = True
                                self.last_event_job_run_time = datetime.utcnow()
                            except Exception as ex:
                                self.is_event_job_scheduled = False
                                if self.DEBUG:
                                    print('Error while starting the event scheduler job in background')
                                    print(str(ex))
                        # Add Event to the queue
                        if self.DEBUG:
                            print('Add Event to the queue')
                        self.moesif_events_queue.put(event_data)
                    except Exception as ex:
                        if self.DEBUG:
                            print("Error while adding event to the queue")
                            print(str(ex))
                else:
                    if self.DEBUG:
                        print('Skipped Event as the moesif event model is None')
            else:
                if self.DEBUG:
                    print("Skipped Event due to sampling percentage: " + str(self.sampling_percentage)
                          + " and random percentage: " + str(random_percentage))
        else:
            if self.DEBUG:
                print('Skipped Event using should_skip configuration option')

        return response
