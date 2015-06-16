__author__ = 'anderson'
from pyramid.view import view_config, forbidden_view_config
from khipu.validacao.validacao_controle import Validador, KhipuToken, KhipuAuthorization
from khipu.servicos.servico import manuseia_excecao
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
        json_credentials = None
        try:
            json_credentials = json.loads(self.request.params['q'])
            log.debug(json_credentials)
            req_validador = Validador()
            khiputoken = KhipuToken(req_validador)
            autorizador = KhipuAuthorization(req_validador)
            header, body, data = autorizador.create_token_response(json_credentials, khiputoken)
            return body
        except Exception as e:
            manuseia_excecao()
            print(e)
            return "erro"