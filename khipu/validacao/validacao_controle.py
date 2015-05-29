__author__ = 'anderson'
from khipu.banco_de_dados.models import (DBSession, Projeto, KhipuException)
from oauthlib.oauth2 import RequestValidator, BearerToken, AuthorizationCodeGrant
import json
import logging
log = logging.getLogger(__name__)


class Validador(RequestValidator):
    def validate_client(self, request):
        log.debug("validate client")
        return True if DBSession.query(Projeto.client_id == request["client_id"] and
                                       Projeto.client_secret == request["client_secret"]).first() else False

    def save_bearer_token(self, token, request):
        projeto = DBSession.query(Projeto.client_id == request["client_id"] and
                                       Projeto.client_secret == request["client_secret"]).first() else False


class KhipuAuthorization(AuthorizationCodeGrant):
    def create_token_response(self, request, token_handler):
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
        }
        try:
            self.validate_token_request(request)
            log.debug('Validação ok para %r.', request)
        except Exception as e:
            log.debug('Erro no cliente durante validação de %r. %r.', request, e)
            return headers, json.dumps({"e": "erro"}), 400

        token = token_handler.create_token(request, refresh_token=True)
        return headers, json.dumps(token), 200

    def validate_token_request(self, request):
        log.debug("validate token request : request %r" % request)
        if request["grant_type"] != 'client_credentials':
            raise Exception

        if not self.request_validator.validate_client(request):
            log.debug('Autenticação do cliente falhou, %r.', request)
            raise Exception


class KhipuToken(BearerToken):
    def create_token(self, request):
        """Create a BearerToken, by default without refresh token."""

        token = {
            'access_token': self.token_generator(request),
        }

        #token = OAuth2Token(token)
        self.request_validator.save_bearer_token(token, request)
        return token