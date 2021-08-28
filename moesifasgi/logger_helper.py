import json
import base64


class LoggerHelper:

    def __init__(self):
        pass

    @classmethod
    def transform_token(cls, token):
        if not isinstance(token, str):
            token = token.decode('utf-8')
        return token

    @classmethod
    def fetch_token(cls, token, token_type):
        return token.split(token_type, 1)[1].strip()

    @classmethod
    def split_token(cls, token):
        return token.split('.')

    def parse_authorization_header(self, token, field, debug):
        try:
            # Fix the padding issue before decoding
            token += '=' * (-len(token) % 4)
            # Decode the payload
            base64_decode = base64.b64decode(token)
            # Transform token to string to be compatible with Python 2 and 3
            base64_decode = self.transform_token(base64_decode)
            # Convert the payload to json
            json_decode = json.loads(base64_decode)
            # Convert keys to lowercase
            json_decode = {k.lower(): v for k, v in json_decode.items()}
            # Check if field is present in the body
            if field in json_decode:
                # Fetch user Id
                return str(json_decode[field])
        except Exception as e:
            if debug:
                print("Error while parsing authorization header to fetch user id.")
                print(e)
        return None

    def get_user_id(self, middleware_settings, request, response, request_headers, debug):
        user_id = None
        try:
            identify_user = middleware_settings.get('IDENTIFY_USER', None)
            if identify_user is not None:
                user_id = identify_user(request, response)
            if not user_id:
                # Transform request headers keys to lower case
                request_headers = {k.lower(): v for k, v in request_headers.items()}
                # Fetch the auth header name from the config
                auth_header_names = middleware_settings.get('AUTHORIZATION_HEADER_NAME', 'authorization').lower()
                # Split authorization header name by comma
                auth_header_names = [x.strip() for x in auth_header_names.split(',')]
                # Fetch the header name available in the request header
                token = None
                for auth_name in auth_header_names:
                    # Check if the auth header name in request headers
                    if auth_name in request_headers:
                        # Fetch the token from the request headers
                        token = request_headers[auth_name]
                        # Split the token by comma
                        token = [x.strip() for x in token.split(',')]
                        # Fetch the first available header
                        if len(token) >= 1:
                            token = token[0]
                        else:
                            token = None
                        break
                # Fetch the field from the config
                field = middleware_settings.get('AUTHORIZATION_USER_ID_FIELD', 'sub').lower()
                # Check if the auth header name in request headers
                if token:
                    # Check if token is of type Bearer
                    if 'Bearer' in token:
                        # Fetch the bearer token
                        token = self.fetch_token(token, 'Bearer')
                        # Split the bearer token by dot(.)
                        split_token = self.split_token(token)
                        # Check if payload is not None
                        if len(split_token) >= 3 and split_token[1]:
                            # Parse and set user Id
                            user_id = self.parse_authorization_header(split_token[1], field, debug)
                    # Check if token is of type Basic
                    elif 'Basic' in token:
                        # Fetch the basic token
                        token = self.fetch_token(token, 'Basic')
                        # Decode the token
                        decoded_token = base64.b64decode(token)
                        # Transform token to string to be compatible with Python 2 and 3
                        decoded_token = self.transform_token(decoded_token)
                        # Fetch and set the user Id
                        user_id = decoded_token.split(':', 1)[0].strip()
                    # Check if token is of user-defined custom type
                    else:
                        # Split the token by dot(.)
                        split_token = self.split_token(token)
                        # Check if payload is not None
                        if len(split_token) > 1 and split_token[1]:
                            # Parse and set user Id
                            user_id = self.parse_authorization_header(split_token[1], field, debug)
                        else:
                            # Parse and set user Id
                            user_id = self.parse_authorization_header(token, field, debug)
        except Exception as e:
            if debug:
                print("can not execute identify_user function, please check moesif settings.")
                print(e)
        return user_id

    @classmethod
    def get_company_id(cls, middleware_settings, request, response, debug):
        company_id = None
        try:
            identify_company = middleware_settings.get('IDENTIFY_COMPANY', None)
            if identify_company is not None:
                company_id = identify_company(request, response)
        except Exception as e:
            if debug:
                print("can not execute identify_company function, please check moesif settings.")
                print(e)
        return company_id

    @classmethod
    def get_metadata(cls, middleware_settings, request, response, debug):
        metadata = None
        try:
            get_metadata = middleware_settings.get('GET_METADATA', None)
            if get_metadata is not None:
                metadata = get_metadata(request, response)
        except Exception as e:
            if debug:
                print("can not execute get_metadata function, please check moesif settings.")
                print(e)
        return metadata

    @classmethod
    def get_session_token(cls, middleware_settings, request, response, debug):
        session_token = None
        try:
            get_session_token = middleware_settings.get('GET_SESSION_TOKEN', None)
            if get_session_token is not None:
                session_token = get_session_token(request, response)
        except Exception as e:
            if debug:
                print("Can not execute get_session_token function. Please check moesif settings.")
                print(e)
        return session_token

    @classmethod
    def should_skip(cls, middleware_settings, request, response, debug):
        try:
            skip_proc = middleware_settings.get("SKIP")
            if skip_proc is not None:
                return skip_proc(request, response)
            else:
                return False
        except Exception as e:
            if debug:
                print("error trying to execute skip function.")
            return False

    @classmethod
    def mask_event(cls, event_model, middleware_settings, debug):
        try:
            mask_event_model = middleware_settings.get("MASK_EVENT_MODEL")
            if mask_event_model is not None:
                return mask_event_model(event_model)
        except Exception as e:
            if debug:
                print("Can not execute MASK_EVENT_MODEL function. Please check moesif settings.")
        return event_model
