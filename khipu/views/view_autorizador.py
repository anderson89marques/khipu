__author__ = 'anderson'
from pyramid.view import view_config, forbidden_view_config


class GeradoraAccessToken():
    def __init__(self, request):
        self.request = request

    @view_config(route_name="token", renderer="json")
    def token(self):
        return {"Anderson": "Lanna"}