from django.conf import settings
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle


class ClientIPAnonRateThrottle(AnonRateThrottle):
    """Anonymous rate limit keyed on the client IP.

    DRF's default trusts X-Forwarded-For, which any client can forge to get a fresh
    counter on every request. Behind Railway (CLIENT_IP_HEADER set), use the header
    the proxy sets; anywhere else, the socket address.
    """

    def get_ident(self, request: Request) -> str:
        header = settings.CLIENT_IP_HEADER
        if header:
            client_ip = request.META.get(header, "").strip()
            if client_ip:
                return client_ip
        # No proxy header: fall back to the socket address. Behind a proxy that means one
        # shared counter, which errs on the strict side.
        return request.META.get("REMOTE_ADDR", "")
