from khipu.banco_de_dados.models import (DBSession, Mensagem, Projeto, GcmInformation, RegisterIds, Usuario)
from pyramid.security import (remember, forget, authenticated_userid, effective_principals)
from khipu.servicos.servico import (Sender, SistemaService, MensagemService, GcmService)
from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized
from pyramid.view import (view_config, forbidden_view_config)
from pyramid.response import Response
from sqlalchemy.exc import DBAPIError
from paginate import Page
import transaction
import datetime
import logging

log = logging.getLogger(__name__)


# ***** KHIPU *********
class KhipuController:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid #no template eu uso assim -> view.logged_in
        #testar isso abaixo pra usar na exibição de dados de acordo com a permissão.
        #self.principals = DBSession.query(Usuario).filter(Usuario.nome == self.logged_in).first()

    @view_config(route_name="exibeprojeto", renderer="templates/projeto/criarprojeto.jinja2", permission='comum')
    def exibirprojeto(self):
        log.debug("Exibir projeto!")
        return {'id': 'id', 'nome_projeto': 'nome projeto', 'chave': 'chave', 'data_ativacao': 'data ativação', 'ativado_por': 'nome usuario'}

    @view_config(route_name="criarprojeto", renderer="json", permission='comum')
    def criarprojeto(self):
        log.debug("informações do dialog: %r" % self.request.params)
        nome_projeto = self.request.params['nomeprojeto']

        with transaction.manager:
            projeto = DBSession.query(Projeto).filter(Projeto.nome == nome_projeto).first()
            owner = authenticated_userid(self.request) #pega o usuário logado
            print(owner)
            log.debug("Usuário Logado: %r" % owner)
            if not projeto: #não é permitido criar projetos com mesmo nome
                projeto = Projeto()
                projeto.nome = nome_projeto
                projeto.gerar_chave_para_projeto(self.request.registry.settings["token.secret"]) #passando a chave que será usando como base pra gerar o token
                projeto.data_ativacao = datetime.datetime.now().date()
                projeto.usuario = DBSession.query(Usuario).filter(Usuario.nome == owner).first()
                DBSession.add(projeto)
                log.debug("Projeto: %r %r %r" % (projeto.nome, projeto.chave, projeto.data_ativacao.strftime("%d/%m/%Y")))
            else:
                Response("Projeto já existe!", content_type='text/plain', status_int=500)

            return {'id': projeto.id, 'nome_projeto': projeto.nome, 'chave': projeto.chave,
                    'data_ativacao': projeto.data_ativacao.strftime("%d/%m/%Y"), 'ativado_por': projeto.usuario.nome}

    @view_config(route_name="showprojeto", renderer="templates/projeto/showprojeto.jinja2", permission='comum')
    def show_projeto(self):
        log.debug("PARAMETROS DO SHOW: %r" % self.request.matchdict['id']) #com o metachdict consehuir pegar o valor da paramentro da url
        id = self.request.matchdict['id']
        projeto = DBSession.query(Projeto).filter(Projeto.id == id).first()
        return {'projeto': projeto}

    @view_config(route_name="listaprojetos", renderer="templates/projeto/listaprojetos.jinja2", permission="comum")
    def listarprojetos(self):
        log.debug("Listar projetos!")
        try:
            #consulta no banco
            query = DBSession.query(Projeto).all()
            #paginação
            listprojetos = Page(query,
                                 page=int(self.request.matchdict['page']),
                                 items_per_page=10,
                                 item_count=len(query))
        except DBAPIError:
            Response("Problema na busca dos projetos", content_type='text/plain', status_int=500)
        return {'listprojetos': listprojetos}


# ***** USUARIO *********
class UsuarioController:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='listausuarios', renderer='templates/usuario/listausuarios.jinja2', permission="admin")
    def lista_usuarios(self):
        print("Aqui porra")
        log.info("listar usuários")
        log.info("Efetive principals: %r" % effective_principals(self.request))
        try:
            #consulta no banco
            query = DBSession.query(Usuario).all()

            #paginação
            listusuarios = Page(query, page=int(self.request.matchdict['page']), items_per_page=10, item_count=len(query))
        except DBAPIError:
            Response("Problema na busca de pessoas", content_type='text/plain', status_int=500)
        return {'listusuarios': listusuarios}

    @view_config(route_name='home', renderer='templates/home.jinja2', permission="view")
    def home(self):
        log.debug("Efetive principals: %r" % effective_principals(self.request))
        log.debug("Buscando o arquivo de sentings: %r" % self.request.registry.settings["tutorial.secret"])
        return {"nome": "Anderson"}


    @forbidden_view_config()
    def sem_auth_control(self):
        """
        Se o usuário está logado e veio parar aqui quer dizer que ele não tem autorização para acessar
        alguma view. então devo retornar uma mensagem dizendo que ele não tem permissão, ou uma página de não permissão.
        Se o usuário não estiver logado e vai para a tela de login
        :return:
        """
        if 'system.Authenticated' in effective_principals(self.request):
            return HTTPUnauthorized() #mudar para HTTPFound e criar uma tela de não permissão.
        else:
            return HTTPFound(location=self.request.application_url + '/login') #redirecionado pra tela de login

    @view_config(route_name="login", renderer='templates/login.jinja2')
    def login(self):
        log.debug("Logando...")
        login_url = self.request.route_url('login')
        referrer = self.request.url
        log.debug("login url:%r, refferer:%r" % (login_url, referrer))

        if referrer == login_url:
            referrer = '/'  # never use login form itself as came_from

        came_from = self.request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''

        if 'form.submitted' in self.request.params:
            login = self.request.params['login']
            password = self.request.params['password']
            user = DBSession.query(Usuario).filter(Usuario.nome == login).first()
            if user.check_password(password):
                headers = remember(self.request, login)
                return HTTPFound(location=came_from, headers=headers)
            message = "Login Falhou"

        return dict(name="Login", message=message, url=self.request.application_url + '/login',
                    came_from=came_from, login=login, password=password)

    @view_config(route_name="logout")
    def logout(self):
        log.debug("Logout")
        request = self.request
        headers = forget(request)
        url = request.route_url('home')

        return HTTPFound(location=url, headers=headers)


# ***** GCM *********
class GcmController:
    """
    Classe responsável pela comunicação com o Android.
    """

    def __init__(self, request):
        self.request = request
        self.gcmservice = GcmService()

    @view_config(route_name='criargcm', renderer='json')
    def criarGcm(self):
        with transaction.manager:
            log.debug("Entrou no criar gcm: %r" % self.request.params)
            mensagem = self.gcmservice.informa_msg(self.request.params, self.request.registry.settings["token.secret"])

        return mensagem

    def android_messages_information(self):
        pass


# ***** Mensagem *********
class MensagemController:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.sender = Sender()
        self.mensagem_service = MensagemService()

    @view_config(route_name='listamensagens', renderer='templates/mensagem/listamensagens.jinja2', permission="comum")
    def lista_mensagens(self):
        try:
            #consulta no banco
            query = DBSession.query(Mensagem).all()
            listmensagens = Page(query, page=int(self.request.matchdict['page']),
                                 items_per_page=10, item_count=len(query))
        except DBAPIError:
            Response("Problema na busca das mensagens", content_type='text/plain', status_int=500)

        return {'listmensagens': listmensagens}

    @view_config(route_name="receiver", renderer="json")
    def receiver_data(self):
        log.debug("receiver %r" % self.request.params)
        mensagem = self.sender.processador(self.request.params['q'], self.request.registry.settings["token.secret"])
        return {"msg": mensagem}

    @view_config(route_name="busca_informacao", renderer="json")
    def busca_informacao_mensagem(self):
        mensagens = self.mensagem_service.get_messages(self.request.params['q'],
                                                       self.request.registry.settings["token.secret"])
        return mensagens


# ***** Sistema *********
class SistemaController:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.sistema = SistemaService()

    @view_config(route_name="listparametros", renderer="templates/sistema/listparametros.jinja2", permission="admin")
    def list_parametros(self):
        log.debug("Listar parametros")
        list_par = self.sistema.get_list_parametros()
        log.debug("Parametros Encontrados %r" % list_par)
        return list_par

    @view_config(route_name="listparametrosbody",  renderer="templates/sistema/_body_list.jinja2", permission="admin")
    def list_parametros_body(self):
        log.debug("BODY LIST :D")
        import time
        time.sleep(6)
        list_par = self.sistema.get_list_parametros()
        return list_par