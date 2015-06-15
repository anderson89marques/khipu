__author__ = 'anderson'
from khipu.banco_de_dados.models import (DBSession, Projeto)
from khipu.servicos.servico import manuseia_excecao
from oauthlib.oauth2 import RequestValidator, BearerToken, AuthorizationCodeGrant
import json
import logging
import transaction
log = logging.getLogger(__name__)


class Validador(RequestValidator):

    def validate_client(self, request):
        log.debug("validate client")
        projeto = DBSession.query(Projeto).filter(Projeto.client_id == request["client_id"] and
                                                  Projeto.client_secret == request["client_secret"]).first()
        result = {"projeto": None, "has_access_token": False, "has_project": False}
        log.debug(type(projeto))
        if projeto:
            result["projeto"] = projeto
            result["has_access_token"] = True if projeto.access_token else False
            result["has_project"] = True
        return result

    def save_bearer_token(self, token, projeto):
        with transaction.manager:
            log.debug("save token")
            try:
                projeto.access_token = token["access_token"]
                DBSession.add(projeto)
            except Exception as e:
                manuseia_excecao()


class KhipuAuthorization(AuthorizationCodeGrant):

    def create_token_response(self, request, token_handler):
        log.debug("create token")
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
        }
        token = None
        try:
            result = self.validate_token_request(request)
            if result["has_project"]:
                if result["has_access_token"]:
                    token = {'access_token': result["projeto"].access_token}
                else:
                    token = token_handler.create_token(request, result["projeto"])
                log.debug('Validação ok para %r.', request)
        except Exception as e:
            log.debug('Erro no cliente durante validação de %r. %r.', request, e)
            manuseia_excecao()
            return headers, json.dumps({"e": "erro"}), 400

        return headers, json.dumps(token), 200

    def validate_token_request(self, request):
        log.debug("validate token request : request %r" % request)
        if request["grant_type"] != 'client_credentials':
            raise Exception

        return self.request_validator.validate_client(request)


class KhipuToken(BearerToken):

    def create_token(self, request, projeto):
        """Create a BearerToken, by default without refresh token."""
        log.debug("token handler")
        token = {
            'access_token': self.token_generator(request),
        }
        log.debug("Token criado: %r" % token)
        #token = OAuth2Token(token)
        self.request_validator.save_bearer_token(token, projeto)
        return token