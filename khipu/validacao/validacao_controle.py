__author__ = 'anderson'
from oauthlib.oauth2 import RequestValidator, BearerToken, WebApplicationServer


class Validador(RequestValidator):
    def validate_client(self):
        pass

    def validate_client_id(self, client_id, request, *args, **kwargs):
        pass

    def validate_client_secret(self):
        pass


class KhipuToken(BearerToken):
    pass