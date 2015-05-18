from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from sqlalchemy import engine_from_config
from khipu.banco_de_dados.models import (DBSession, Base, Usuario, Principal)
from khipu.seguranca.security import groupfinder, init
from khipu.servicos.servico import manuseia_excecao
import logging
log = logging.getLogger(__name__)

"""
    KHIPU ou QUIPO,
    era um instrumento utilizado para COMUNICAÇÃO,
    mas também como registro contábil e como registros mnemotécnicos entre os INCAS.
"""


def main(global_config, **settings):
    """
        This function returns a Pyramid WSGI application.
        Esta função retorna uma aplicação Pyramid WSGI
    """

    #Configuração para criação do banco de dados
    log.debug("Inicializando a base de dados!")

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    #criando os usuários defaults
    init()

    #configuração principal
    log.debug("Configurando o pyramid")
    config = Configurator(settings=settings, root_factory='khipu.seguranca.resources.Root')
    #incluindo jinja2 como template engine
    config.include('pyramid_jinja2')

    #Politica de segurança
    log.debug("Configurando a Autenicação e configuração ")
    autenticacao_po = AuthTktAuthenticationPolicy(settings['tutorial.secret'], callback=groupfinder, hashalg='sha512')
    autorizacao_po = ACLAuthorizationPolicy()
    config.set_authentication_policy(autenticacao_po)
    config.set_authorization_policy(autorizacao_po)

    #criando rotas com suas urls
    log.debug("Adicionando as rotas!")
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('criargcm', '/gcm/criarGcm')
    config.add_route('receiver', '/receiver')
    config.add_route('exibeprojeto', '/projeto')
    config.add_route('criarprojeto', '/criarprojeto')
    config.add_route('listaprojetos', '/projetos/{page}')
    config.add_route('listausuarios', '/usuarios/{page}')
    config.add_route('listamensagens', '/mensagens/{page}')
    config.add_route('showprojeto', '/showprojeto/{id}')
    config.add_route('listparametros', '/parametros')
    config.add_route('listparametrosbody', '/parametros/body')
    config.add_route('busca_informacao', '/informacao')
    config.add_route('androidmessages', '/inforandroid')
    config.add_route('listaexcecoes', '/excecoes/{page}')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('my_view', 'myview')
    log.debug("Rotas Adicionadas.")
    config.scan(".views")

    return config.make_wsgi_app()
