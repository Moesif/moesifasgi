import base64
import json
import gzip


class ParseBody:
    def __init__(self):
        pass

    @classmethod
    def start_with_json(cls, body):
        return body.startswith("{") or body.startswith("[")

    @classmethod
    def base64_body(cls, body):
        return base64.standard_b64encode(body).decode(encoding="UTF-8"), "base64"

    def parse_bytes_body(self, body, headers):
        try:
            if (headers is not None and "content-encoding" in headers and headers["content-encoding"] is not None
                     and "gzip" in (headers["content-encoding"]).lower()):
                parsed_body, transfer_encoding = self.base64_body(gzip.decompress(body))
            else:
                string_data = body.decode(encoding="UTF-8")
                if self.start_with_json(string_data):
                    parsed_body = json.loads(string_data)
                    transfer_encoding = 'json'
                else:
                    parsed_body, transfer_encoding = self.base64_body(body)
        except Exception as e:
            parsed_body, transfer_encoding = self.base64_body(body)
        return parsed_body, transfer_encoding
