from khipu.banco_de_dados.models import (DBSession, Mensagem, Projeto, Usuario)
from khipu.banco_de_dados.enuns import StatusMensagem
from pyramid.security import (remember, forget, authenticated_userid, effective_principals)
from khipu.servicos.servico import (Sender, SistemaService, MensagemService, GcmService, manuseia_excecao)
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
        return {'projeto': None}

    @view_config(route_name="criarprojeto", renderer="templates/projeto/_tab.jinja2", permission='comum')
    def criarprojeto(self):
        log.debug("Criando projeto")
        log.debug("informações do dialog: %r" % self.request.params)
        nome_projeto = self.request.params['nomeprojeto']

        with transaction.manager:
            try:
                projeto = DBSession.query(Projeto).filter(Projeto.nome == nome_projeto).first()
                owner = authenticated_userid(self.request) #pega o usuário logado
                log.debug("Usuário logado: %r" % owner)
                if not projeto: #não é permitido criar projetos com mesmo nome
                    projeto = Projeto()
                    projeto.nome = nome_projeto
                    projeto.gerar_chaves_para_projeto()
                    projeto.data_ativacao = datetime.datetime.now().date()
                    projeto.usuario = DBSession.query(Usuario).filter(Usuario.nome == owner).first()
                    DBSession.add(projeto)
                    log.debug("Projeto Criado: %r %r %r %r" % (projeto.nome, projeto.client_id, projeto.client_secret, projeto.data_ativacao.strftime("%d/%m/%Y")))
                else:
                    return Response("Projeto já existe!", content_type='text/plain', status_int=500)
            except Exception as e:
                manuseia_excecao()
                return Response("Erro ao criar projeto", content_type='text/plain', status_int=500)

            return {'projeto': projeto}

    @view_config(route_name="showprojeto", renderer="templates/projeto/showprojeto.jinja2", permission='comum')
    def show_projeto(self):
        log.debug("Show projeto.")
        log.debug("Projeto id: %r" % self.request.matchdict['id']) #com o metachdict consegui pegar o valor da paramentro da url
        try:
            id = self.request.matchdict['id']
            projeto = DBSession.query(Projeto).filter(Projeto.id == id).first()
            log.debug("Projeto: %s" % projeto.nome)
        except Exception as e:
            manuseia_excecao()
            return Response("Erro ao exibir projeto", content_type='text/plain', status_int=500)
        return {'projeto': projeto}

    @view_config(route_name="listaprojetos", renderer="templates/projeto/listaprojetos.jinja2", permission="comum")
    def listarprojetos(self):
        log.debug("Listar projetos.")
        try:
            log.debug("Parametros do request: %r" % self.request.params)
            nome_projeto = self.request.GET.get("nome_projeto", "")
            nome_usuario = self.request.GET.get("nome_usuario", "")
            datepicker1 = self.request.GET.get("datepicker1", "")
            datepicker2 = self.request.GET.get("datepicker2", "")
            log.debug("Nome Projeto: %r" % nome_projeto)
            log.debug("Nome Usuário: %r" % nome_usuario)
            log.debug("Datepicker1: %r" % datepicker1)
            log.debug("Datepicker2: %r" % datepicker2)

            query = None
            #consultas no banco
            if nome_projeto:
                query = DBSession.query(Projeto).filter(Projeto.nome == nome_projeto).all()
            elif nome_usuario and datepicker1 and datepicker2:
                from_date = datetime.datetime.strptime(datepicker1, "%m/%d/%Y").date()
                to_date = datetime.datetime.strptime(datepicker2, "%m/%d/%Y").date()

                query = DBSession.query(Projeto).join(Usuario, Usuario.id == Projeto.usuario_id).\
                    filter(Usuario.nome == nome_usuario).\
                    filter(Projeto.data_ativacao >= from_date).\
                    filter(Projeto.data_ativacao <= to_date).all()
            elif datepicker1 and datepicker2:
                from_date = datetime.datetime.strptime(datepicker1, "%m/%d/%Y").date()
                to_date = datetime.datetime.strptime(datepicker2, "%m/%d/%Y").date()

                query = DBSession.query(Projeto).filter(Projeto.data_ativacao >= from_date).\
                                                 filter(Projeto.data_ativacao <= to_date).all()
            elif nome_usuario:
                query = DBSession.query(Projeto).join(Usuario, Usuario.id == Projeto.usuario_id).\
                    filter(Usuario.nome == nome_usuario).all()
            else:
                query = DBSession.query(Projeto).all()

            #paginação
            listprojetos = Page(query,
                                 page=int(self.request.matchdict['page']),
                                 items_per_page=10,
                                 item_count=len(query))
        except DBAPIError:
            manuseia_excecao()
            return Response("Problema na busca dos projetos", content_type='text/plain', status_int=500)

        log.debug("lista de projetos: %s" % listprojetos)
        model = {'listprojetos': listprojetos}

        if nome_projeto:
            model['nome_projeto'] = nome_projeto
        if nome_usuario:
            model['nome_usuario'] = nome_usuario
        if datepicker1 and datepicker2:
            model['datepicker1'] = datepicker1
            model['datepicker2'] = datepicker2

        return model


# ***** USUARIO *********
class UsuarioController:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='listausuarios', renderer='templates/usuario/listausuarios.jinja2', permission="admin")
    def lista_usuarios(self):
        log.debug("Listar usuários")
        log.debug("Efetive principals: %r" % effective_principals(self.request))
        try:
            #consulta no banco
            query = DBSession.query(Usuario).all()

            #paginação
            listusuarios = Page(query, page=int(self.request.matchdict['page']), items_per_page=10, item_count=len(query))
        except DBAPIError:
            manuseia_excecao()
            Response("Problema na busca de pessoas", content_type='text/plain', status_int=500)
            log.debug("Lista de usuários: %r" % listusuarios)
        return {'listusuarios': listusuarios}

    @view_config(route_name='home', renderer='templates/home.jinja2', permission="view")
    def home(self):
        log.debug("Home")
        return {"nome": "Anderson"}


    @forbidden_view_config()
    def sem_auth_control(self):
        """
        Se o usuário está logado e veio parar aqui quer dizer que ele não tem autorização para acessar
        alguma view. então devo retornar uma mensagem dizendo que ele não tem permissão, ou uma página de não permissão.
        Se o usuário não estiver logado ele vai para a tela de login
        :return:
        """
        log.debug("Sem auth control")
        if 'system.Authenticated' in effective_principals(self.request):
            log.debug("Usuário sem permissão: %r" % self.logged_in)
            return HTTPUnauthorized() #mudar para HTTPFound e criar uma tela de não permissão.
        else:
            log.debug("Usuário não logado. redirecionando para login")
            return HTTPFound(location=self.request.application_url + '/login') #redirecionado pra tela de login

    @view_config(route_name="login", renderer='templates/login.jinja2')
    def login(self):
        log.debug("Login.")
        login_url = self.request.route_url('login')
        referrer = self.request.url
        log.debug("login url:%r, refferer:%r" % (login_url, referrer))

        if referrer == login_url:
            referrer = '/khipu'  # never use login form itself as came_from

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
            message = "Login Falhou. usuário e/ou senha invalido(s)"
        if message:
            log.debug(message)
            return Response(message, content_type='text/plain', status_int=500)
        return {"ok": "ok"}


    @view_config(route_name="logout")
    def logout(self):
        log.debug("Logout!")
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
        log.debug("Criar objeto gcm")
        with transaction.manager:
            log.debug("Parametros vindos do android: %r" % self.request.params)
            mensagem = self.gcmservice.informa_regid(self.request.params, self.request.registry.settings["token.secret"])

        return mensagem

    @view_config(route_name="androidmessages", renderer="json")
    def android_messages_information(self):
        log.debug("Informação vinda do android")
        mensagens = self.gcmservice.informacao_sobre_msg(self.request.params,
                                                         self.request.registry.settings["token.secret"])
        return mensagens


# ***** Mensagem *********
class MensagemController:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.sender = Sender()
        self.mensagem_service = MensagemService()

    @view_config(route_name='listamensagens', renderer='templates/mensagem/listamensagens.jinja2', permission="comum")
    def lista_mensagens(self):
        log.debug("Listar mensagens!")
        try:
            log.debug("Parametros do request: %r" % self.request.params)
            nome_projeto = self.request.GET.get("nome_projeto", "")
            status = self.request.GET.get("status", "")
            datepicker1 = self.request.GET.get("datepicker1", "")
            datepicker2 = self.request.GET.get("datepicker2", "")
            log.debug("Nome Projeto: %r" % nome_projeto)
            log.debug("Estado: %r" % status)
            log.debug("Datepicker1: %r" % datepicker1)
            log.debug("Datepicker2: %r" % datepicker2)

            query = None
            #consultas no banco
            if nome_projeto:
                query = DBSession.query(Mensagem).join(Projeto, Projeto.id == Mensagem.projeto_id).\
                    filter(Projeto.nome == nome_projeto).all()
            elif status and datepicker1 and datepicker2:
                from_date = datetime.datetime.strptime(datepicker1, "%m/%d/%Y").date()
                to_date = datetime.datetime.strptime(datepicker2, "%m/%d/%Y").date()

                query = DBSession.query(Mensagem).filter(Mensagem.status == status).\
                    filter(Mensagem.data_chegada >= from_date).\
                    filter(Mensagem.data_chegada <= to_date).all()
            elif datepicker1 and datepicker2:
                from_date = datetime.datetime.strptime(datepicker1, "%m/%d/%Y").date()
                to_date = datetime.datetime.strptime(datepicker2, "%m/%d/%Y").date()

                query = DBSession.query(Mensagem).filter(Mensagem.data_chegada >= from_date).\
                                                 filter(Mensagem.data_chegada <= to_date).all()
            elif status:
                query = DBSession.query(Mensagem).filter(Mensagem.status == StatusMensagem[status].value).all()
            else:
                query = DBSession.query(Mensagem).all()
            listmensagens = Page(query, page=int(self.request.matchdict['page']),
                                 items_per_page=10, item_count=len(query))
        except Exception as e:
            manuseia_excecao()
            return Response("Problema na busca das mensagens", content_type='text/plain', status_int=500)
        log.debug("lista de mensagens: %r" % listmensagens)
        model = {'listmensagens': listmensagens}

        if nome_projeto:
            model['nome_projeto'] = nome_projeto
        if status:
            model['status'] = status
        if datepicker1 and datepicker2:
            model['datepicker1'] = datepicker1
            model['datepicker2'] = datepicker2

        return model

    @view_config(route_name="receiver", renderer="json")
    def receiver_data(self):
        log.debug("Recebendo mensagem %r" % self.request.params)
        mensagem = self.sender.processador(self.request.params['q'], self.request.registry.settings["token.secret"])
        return mensagem

    @view_config(route_name="busca_informacao", renderer="json")
    def busca_informacao_mensagem(self):
        log.debug("Recebendo informação sobre o sms")
        log.debug(self.request.params)
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
        log.debug("lista de parametros do sistema")
        list_par = self.sistema.get_list_parametros()
        log.debug("lista: %r" % list_par)
        return list_par

    @view_config(route_name="listparametrosbody",  renderer="templates/sistema/_body_list.jinja2", permission="admin")
    def list_parametros_body(self):
        log.debug("parametros ajax")
        import time
        time.sleep(6)
        list_par = self.sistema.get_list_parametros()
        return list_par

    @view_config(route_name="listaexcecoes",  renderer="templates/sistema/listaexcecoes.jinja2", permission="admin")
    def lista_excessoes(self):
        list = self.sistema.get_list_exception()
        list_exception = Page(list, page=int(self.request.matchdict['page']),
                                 items_per_page=10, item_count=len(list))
        if type(list_exception) is dict:
            return Response(list_exception, content_type='text/plain', status_int=500)
        return {'list_exception': list_exception}