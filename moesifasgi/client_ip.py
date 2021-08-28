import re


class ClientIp:

    def __init__(self):
        pass

    @classmethod
    def is_ip(cls, value):
        if not value is None:
            ipv4 = r"^(?:(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])$"
            ipv6 = r"^((?=.*::)(?!.*::.+::)(::)?([\dA-F]{1,4}:(:|\b)|){5}|([\dA-F]{1,4}:){6})((([\dA-F]{1,4}((?!\3)::|:\b|$))|(?!\2\3)){2}|(((2[0-4]|1\d|[1-9])?\d|25[0-5])\.?\b){4})$/i"
            return re.match(ipv4, value) or re.match(ipv6, value)

    def getClientIpFromXForwardedFor(self, value):
        try:

            if not value or value is None:
                return None

            if not isinstance(value, str):
                print("Expected a string, got -" + str(type(value)))
            else:
                # x-forwarded-for may return multiple IP addresses in the format:
                # "client IP, proxy 1 IP, proxy 2 IP"
                # Therefore, the right-most IP address is the IP address of the most recent proxy
                # and the left-most IP address is the IP address of the originating client.
                # source: http://docs.aws.amazon.com/elasticloadbalancing/latest/classic/x-forwarded-headers.html
                # Azure Web App's also adds a port for some reason, so we'll only use the first part (the IP)
                forwardedIps = []

                for e in value.split(','):
                    ip = e.strip()
                    if ':' in ip:
                        splitted = ip.split(':')
                        if (len(splitted) == 2):
                            forwardedIps.append(splitted[0])
                    forwardedIps.append(ip)

                # Sometimes IP addresses in this header can be 'unknown' (http://stackoverflow.com/a/11285650).
                # Therefore taking the left-most IP address that is not unknown
                # A Squid configuration directive can also set the value to "unknown" (http://www.squid-cache.org/Doc/config/forwarded_for/)
                return next(item for item in forwardedIps if self.is_ip(item))
        except StopIteration:
            return value.encode('utf-8')

    def get_client_address(self, request_headers, default_host):
        try:
            # Standard headers used by Amazon EC2, Heroku, and others.
            if 'x-client-ip' in request_headers:
                if self.is_ip(request_headers['x-client-ip']):
                    return request_headers['x-client-ip']

            # Load-balancers (AWS ELB) or proxies.
            if 'x-forwarded-for' in request_headers:
                xForwardedFor = self.getClientIpFromXForwardedFor(request_headers['x-forwarded-for'])
                if self.is_ip(xForwardedFor):
                    return xForwardedFor

            # Cloudflare.
            # @see https://support.cloudflare.com/hc/en-us/articles/200170986-How-does-Cloudflare-handle-HTTP-Request-headers-
            # CF-Connecting-IP - applied to every request to the origin.
            if 'cf-connecting-ip' in request_headers:
                if self.is_ip(request_headers['cf-connecting-ip']):
                    return request_headers['cf-connecting-ip']

            # Akamai and Cloudflare: True-Client-IP.
            if 'true-client-ip' in request_headers:
                if self.is_ip(request_headers['true-client-ip']):
                    return request_headers['true-client-ip']

            # Default nginx proxy/fcgi; alternative to x-forwarded-for, used by some proxies.
            if 'x-real-ip' in request_headers:
                if self.is_ip(request_headers['x-real-ip']):
                    return request_headers['x-real-ip']

            # (Rackspace LB and Riverbed's Stingray)
            # http://www.rackspace.com/knowledge_center/article/controlling-access-to-linux-cloud-sites-based-on-the-client-ip-address
            # https://splash.riverbed.com/docs/DOC-1926
            if 'x-cluster-client-ip' in request_headers:
                if self.is_ip(request_headers['x-cluster-client-ip']):
                    return request_headers['x-cluster-client-ip']

            if 'x-forwarded' in request_headers:
                if self.is_ip(request_headers['x-forwarded']):
                    return request_headers['x-forwarded']

            if 'forwarded-for' in request_headers:
                if self.is_ip(request_headers['forwarded-for']):
                    return request_headers['forwarded-for']

            if 'forwarded' in request_headers:
                if self.is_ip(request_headers['forwarded']):
                    return request_headers['forwarded']

            return default_host
        except KeyError:
            return default_host
