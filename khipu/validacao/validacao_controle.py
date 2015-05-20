__author__ = 'anderson'
from oauthlib.oauth2 import RequestValidator, BearerToken


class Validador(RequestValidator):
    def validate_client_id(self, client_id, request, *args, **kwargs):
        pass


class KhipuToken(BearerToken):
    pass