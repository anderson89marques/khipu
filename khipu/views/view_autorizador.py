__author__ = 'anderson'
from pyramid.view import view_config
from khipu.servicos.exception_service import ExceptionService
from khipu.validacao.validacao_controle import AuthorizationService
import logging
import json


log = logging.getLogger(__name__)


class GeradoraAccessToken():

    """
        Controla as requisições relacionadas ao cadastro das aplicações clientes no khipu
    """

    def __init__(self, request):
        self.request = request

    @view_config(route_name="token", request_method="GET", renderer="json")
    def token(self):
        log.debug("TOKEN")
        try:
            json_credentials = json.loads(self.request.params['q'])
            log.debug(json_credentials)
            header, body, data = AuthorizationService.create_access_token(json_credentials)
            return body
        except Exception as e:
            ExceptionService.manuseia_excecao()
            print(e)
            return "erro"