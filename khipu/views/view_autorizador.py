__author__ = 'anderson'
from pyramid.view import view_config, forbidden_view_config
from khipu.validacao.validacao_controle import Validador


class GeradoraAccessToken():
    def __init__(self, request):
        self.request = request

    @view_config(route_name="token", renderer="json")
    def token(self):
        json_credentials = self.request.json_body
        req_validador = Validador()
        print(json_credentials)
        return {"Anderson": "Lanna"}