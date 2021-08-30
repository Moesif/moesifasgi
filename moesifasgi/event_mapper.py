from moesifapi.models import *
from .parse_body import ParseBody
from .logger_helper import LoggerHelper
from .client_ip import ClientIp
from datetime import datetime
import uuid


class EventMapper:
    def __init__(self):
        self.parse_body = ParseBody()
        self.logger_helper = LoggerHelper()
        self.client_ip = ClientIp()
        self.transaction_id = None

    @classmethod
    def get_time(cls):
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    def to_event(self, request, response, event_req, event_rsp, moesif_settings, debug):
        return EventModel(request=event_req,
                          response=event_rsp,
                          user_id=self.logger_helper.get_user_id(moesif_settings, request, response, dict(request.headers), debug),
                          company_id=self.logger_helper.get_company_id(moesif_settings, request, response, debug),
                          session_token=self.logger_helper.get_session_token(moesif_settings, request, response, debug),
                          metadata=self.logger_helper.get_metadata(moesif_settings, request, response, debug),
                          direction="Incoming")

    def to_request(self, request, request_body, api_version, disable_capture_transaction_id):
        # Request time
        request_time = self.get_time()
        # Request URI
        request_uri = request.url._url
        # Request Verb
        request_verb = request.method
        # Request Headers
        request_headers = dict(request.headers)
        # Add Transaction Id to headers
        if not disable_capture_transaction_id:
            req_trans_id = request_headers.get("x-moesif-transaction-id")
            if req_trans_id:
                self.transaction_id = req_trans_id
                if not self.transaction_id:
                    self.transaction_id = str(uuid.uuid4())
            else:
                self.transaction_id = str(uuid.uuid4())
                # Add transaction id to the request header
                request_headers["X-Moesif-Transaction-Id"] = self.transaction_id
        # Request Ip address
        request_ip_address = self.client_ip.get_client_address(request_headers, request.client.host)
        # Request Body
        req_body = None
        req_transfer_encoding = None
        if request_body:
            req_body, req_transfer_encoding = self.parse_body.parse_bytes_body(request_body, request_headers)

        return EventRequestModel(time=request_time,
                                 uri=request_uri,
                                 verb=request_verb,
                                 api_version=api_version,
                                 ip_address=request_ip_address,
                                 headers=request_headers,
                                 body=req_body,
                                 transfer_encoding=req_transfer_encoding)

    def to_response(self, response, response_body):
        # Response time
        response_time = self.get_time()
        # Response Status code
        response_status = response.status_code
        # Response Headers
        response_headers = dict(response.headers)
        # Add transaction id to the response header
        if self.transaction_id:
            response_headers["X-Moesif-Transaction-Id"] = self.transaction_id
        # Response Body
        rsp_body = None
        rsp_transfer_encoding = None
        if response_body:
            try:
                rsp_body = response_body[0]
            except Exception as e:
                rsp_body = str(response_body)

            rsp_body, rsp_transfer_encoding = self.parse_body.parse_bytes_body(rsp_body, response_headers)

        return EventResponseModel(time=response_time,
                                  status=response_status,
                                  headers=response_headers,
                                  body=rsp_body,
                                  transfer_encoding=rsp_transfer_encoding)
