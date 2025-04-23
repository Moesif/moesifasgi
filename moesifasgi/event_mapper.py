from moesifapi.models import *
from moesifapi.parse_body import ParseBody
from .logger_helper import LoggerHelper
from .client_ip import ClientIp
import uuid


class EventMapper:
    def __init__(self):
        self.parse_body = ParseBody()
        self.logger_helper = LoggerHelper()
        self.client_ip = ClientIp()
        self.transaction_id = None

    def parse(self, body, headers): 
        if not body or not isinstance(body, bytes) :
            return None, None
        return self.parse_body.parse_bytes_body(body, None, headers)

    async def to_event(self, event_req, event_rsp, user_id, company_id, session_token, metadata, blocked_by):
        return EventModel(request=event_req,
                          response=event_rsp,
                          user_id=user_id,
                          company_id=company_id,
                          session_token=session_token,
                          metadata=metadata,
                          direction="Incoming",
                          blocked_by=blocked_by)

    def to_request(self, request, request_time, request_headers, request_body, api_version, disable_capture_transaction_id, debug=False):
        # Request URI
        request_uri = request.url._url
        # Request Verb
        request_verb = request.method
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
        request_ip_address = self.client_ip.get_client_address(request_headers, request.client.host, debug)
        # Request Body
        req_body = None
        req_transfer_encoding = None
        if request_body:
            req_body, req_transfer_encoding = self.parse_body.parse_bytes_body(request_body, None, request_headers)

        return EventRequestModel(time=request_time,
                                 uri=request_uri,
                                 verb=request_verb,
                                 api_version=api_version,
                                 ip_address=request_ip_address,
                                 headers=request_headers,
                                 body=req_body,
                                 transfer_encoding=req_transfer_encoding)

    def to_response(self, response, response_time, response_headers, response_body):
        # Response Status code
        response_status = response.status_code
        # Add transaction id to the response header
        if self.transaction_id:
            response_headers["X-Moesif-Transaction-Id"] = self.transaction_id
        # Response Body
        rsp_body, rsp_transfer_encoding = self.parse(response_body, response_headers)

        response_model = EventResponseModel(time=response_time,
                                      status=response_status,
                                      headers=response_headers,
                                      body=rsp_body,
                                      transfer_encoding=rsp_transfer_encoding)
        return response_model

