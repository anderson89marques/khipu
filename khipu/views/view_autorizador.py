__author__ = 'anderson'
from pyramid.view import view_config, forbidden_view_config
from khipu.validacao.validacao_controle import Validador, KhipuToken, KhipuAuthorization
import logging
log = logging.getLogger(__name__)


class GeradoraAccessToken():
    def __init__(self, request):
        self.request = request

    @view_config(route_name="token", renderer="json")
    def token(self):
        log.debug("TOKEN")
        try:
            json_credentials = self.request.json_body
            req_validador = Validador()
            khiputoken = KhipuToken()
            autorizador = KhipuAuthorization(req_validador)
            header, body, data = autorizador.validate_authorization_request(json_credentials, khiputoken)
        except Exception as e:
            pass
        print(json_credentials)
        return body