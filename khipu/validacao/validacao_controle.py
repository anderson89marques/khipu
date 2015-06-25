__author__ = 'anderson'
from khipu.banco_de_dados.models import (DBSession, Projeto)
from khipu.servicos.exception_service import (ExceptionService)
from oauthlib.oauth2 import (RequestValidator, BearerToken, AuthorizationCodeGrant)
import json
import logging
import transaction

log = logging.getLogger(__name__)


class Validador(RequestValidator):

    def validate_client(self, request):
        log.debug("validate client")
        try:
            projeto = DBSession.query(Projeto).filter(Projeto.client_id == request["client_id"] and
                                                      Projeto.client_secret == request["client_secret"]).first()
            result = {"projeto": None, "has_access_token": False, "has_project": False}
            log.debug(type(projeto))

            if projeto:
                result["projeto"] = projeto
                result["has_access_token"] = True if projeto.access_token else False
                result["has_project"] = True
            return result
        except Exception as e:
                ExceptionService.manuseia_excecao()

    def is_access_token_ok(self, access_token):
        projeto_id = DBSession.query(Projeto.id).filter(Projeto.access_token == access_token).first()
        return True if projeto_id else False

    def save_bearer_token(self, token, projeto):
        with transaction.manager:
            log.debug("save token")
            try:
                projeto.access_token = token["access_token"]
                DBSession.add(projeto)
            except Exception as e:
                ExceptionService.manuseia_excecao()


class KhipuAuthorization(AuthorizationCodeGrant):

    def create_token_response(self, request, token_handler):

        """
        :param request:
        :param token_handler:
        :return header, access_token e o código:
        """

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
            ExceptionService.manuseia_excecao()
            return headers, json.dumps({"e": "erro"}), 400

        return headers, token, 200

    def validate_token_request(self, request):
        log.debug("validate token request : request %r" % request)
        if request["grant_type"] != 'client_credentials':
            raise Exception

        return self.request_validator.validate_client(request)

    def validate_access_token(self, access_token):

        """
        :param access_token:
        :return True se o access token é válido e False se não é válido:
        """

        return self.request_validator.is_access_token_ok(access_token)


class KhipuToken(BearerToken):

    def create_token(self, request, projeto):

        """Create a BearerToken, by default without refresh token."""

        log.debug("token handler")
        token = {
            'access_token': self.token_generator(request),
        }
        log.debug("Token criado: %r" % token)
        self.request_validator.save_bearer_token(token, projeto)
        return token


class AuthorizationService:

    @classmethod
    def get_authorization_with_token(cls):
        req_validador = Validador()
        khiputoken = KhipuToken(req_validador)
        authorizator = KhipuAuthorization(req_validador)
        return (khiputoken, authorizator)

    @classmethod
    def get_authorization_without_token(cls):
        req_validador = Validador()
        return KhipuAuthorization(req_validador)

    @classmethod
    def create_access_token(cls, json_credentials):
        khiputoken, authorizator = cls.get_authorization_with_token()
        return authorizator.create_token_response(json_credentials, khiputoken)

    @classmethod
    def validate_access_token(cls, access_token):
        authorizator = cls.get_authorization_without_token()
        return authorizator.validate_access_token(access_token)