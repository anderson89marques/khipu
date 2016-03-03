__author__ = 'anderson'

from khipu.banco_de_dados.models import (DBSession, Mensagem, UsuarioAplicacaoCliente, GcmInformation, Projeto,
                                         RegisterIds, KhipuException, Telefone)
from khipu.banco_de_dados.enuns import StatusMensagem
from khipu.servicos.exception_service import ExceptionService
from khipu.gcm_wraper.gcm import GCM
from binascii import unhexlify
from simplecrypt import decrypt
import datetime
import transaction
import logging
import json
import psutil

log = logging.getLogger(__name__)


# ***** Sistema *********
class SistemaService(object):
    """
        Classe responsável por coletar informações do Computador como: Memória, Uso de CPU, e informações da REDE.
    """

    def __init__(self):
        pass

    def bytes2human(self, n):
        # http://code.activestate.com/recipes/578019
        # >>> bytes2human(10000)
        # '9.8K'
        # >>> bytes2human(100001221)
        # '95.4M'
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n

    def parametros_list(self, nt):
        num_fields = 0
        parametros = []
        for name in nt._fields:
            num_fields += 1
            value = getattr(nt, name)
            if name != 'percent':
                value = self.bytes2human(value)
            parametros.append('%s' % value)
            print('%-10s : %7s' % (name.capitalize(), value))
            if num_fields == 4: #é que só quero o retorno de quatro parametros
                break
        return parametros

    def get_memoria_ram_parametros(self):
        return self.parametros_list(psutil.virtual_memory())

    def get_list_parametros(self):
        memoria_ram = self.get_memoria_ram_parametros()
        print("Memoria Parametros: %r" % memoria_ram)
        cpu_times = enumerate(psutil.cpu_times(True))
        print(cpu_times)
        cpu_porcento = psutil.cpu_percent(interval=1, percpu=True)
        network_interfaces = psutil.net_io_counters(pernic=True)
        return {'cpu_times': cpu_times, 'cpu_porcento': cpu_porcento, 'memoria_ram': memoria_ram,
                'network_interfaces': network_interfaces}

    def get_list_exception(self):
        msg = {}
        try:
           list = DBSession.query(KhipuException).all()
        except Exception as e:
            ExceptionService.manuseia_excecao()
            msg['ok'] = "Erro :( %r" % e
            return msg
        return list


# ***** Mensagem *********
class MensagemService(object):
    """
        Classe responsável por formatar as informações que serão enviadas para o servidor do google e posteriormente
        para o celular cadastrado, que então enviará as mensagens de texto.
        Controla a busca de informações sobre as mensagens.
        O método get_messages recebe a chave para descriptografar o token identificador da aplicação
        e também os dados contendo o token e os ids das mensagens ao qual se quer obter informação.
    """

    def __init__(self):
        #como implementar singleton no python
        self.gcm_service = GcmService()
        self.msg_service = UsuarioAplicacaoService()

    def get_mensagem(self, id_msg):
        msg = DBSession.query(Mensagem).filter(Mensagem.id_on_web_app == id_msg).first()
        return msg

    def salvar_mensagem(self, id_msg, projeto):
        log.debug("Salvando Mensagem.")
        with transaction.manager:
            msg = self.get_mensagem(id_msg)
            if msg:
                msg.status = StatusMensagem.RECEBIDA_CLIENTE.value
                msg.data_ultimo_envio = datetime.datetime.now().date()
                DBSession.add(msg)
                log.debug("Mensagem atualizada: %r" % msg)
            else:
                msg = Mensagem()
                msg.id_on_web_app = id_msg
                msg.data_chegada = datetime.datetime.now().date()
                msg.data_ultimo_envio = datetime.datetime.now().date()
                msg.numero_tentativas_envio = 1
                msg.status = StatusMensagem.RECEBIDA_CLIENTE.value
                msg.projeto = projeto
                DBSession.add(msg)
                log.debug("Mensagem salva: %r" % msg)
        return msg

    def processador(self, dados):
        log.debug("Processando Mensagem Recebida")
        d = dados['data']
        try:
            projeto = DBSession.query(Projeto).filter(Projeto.access_token == d["access_token"]).first()
            if projeto:
                self.salvar_mensagem(d['id_mensagem'], projeto)

                gcminformation = self.gcm_service.givemeGcm()
                usr_app_client = self.msg_service.buscaUsuarioPorChave(d["chave"])
                d['registration_ids'] = [usr_app_client.register_ids[0].androidkey] #[gcminformation.register_ids[0].androidkey]

                log.debug("DADOS: %r" % d)

                gcmobj = GCM(gcminformation.apikey)
                response = gcmobj.json_request(registration_ids=d['registration_ids'], data=dados['data'])

                log.debug("Resposta Google: %r" % response)

                return {'msg': "Mensagem Recebida com sucesso"}
            else:
                return {'msg': "Projeto não autorizado"}

        except Exception as e:
            ExceptionService.manuseia_excecao()
            return {'msg': "Erro: {0}".format(e)}

    def get_messages(self, dados, key):
        log.debug("Buscando Mensagens!")
        d = json.loads(dados)
        projeto = None
        log.debug("projeto json: %r" % d)
        try:
            projeto = descriptografa_projeto(d['id_projeto'], key)
            if projeto:
                msg_ids = d['mensagem_ids']
                mensagens = [DBSession.query(Mensagem).filter(Mensagem.id_on_web_app == id).first() for id in msg_ids]
                informacoes = [{"mensagem_id": msg.id_on_web_app, "data_chegada": msg.data_chegada.strftime("%d/%m/%Y"),
                                "numero_tentativas": msg.numero_tentativas_envio, "status": msg.status}
                               for msg in mensagens if msg]
                log.debug("Informações: %r" % informacoes)
                return informacoes
            else:
                return {'msg': "Projeto não autorizado"}
        except Exception as e:
            ExceptionService.manuseia_excecao()
            return {'msg': "Erro na consulta: %r" % e}


# ***** GCMService *********
class GcmService(object):

    def __init__(self):
        pass

    def givemeGcm(self):
        log.debug("Buscando GCM")
        gcminformation = DBSession.query(GcmInformation).filter(GcmInformation.name == "GCMCLASS").first()
        if not gcminformation:
            gcminformation = GcmInformation()

        return gcminformation

    def definir_regid(self, dados_android):
        log.debug("Recebimento do RegId do android")
        with transaction.manager:
            try:
                usuario_aplicao_cliente = DBSession.query(UsuarioAplicacaoCliente).\
                                          filter(UsuarioAplicacaoCliente.chave == dados_android["senha_registro"]).first()
                log.debug("usuario aplicação cliente: %r" % usuario_aplicao_cliente)
                if usuario_aplicao_cliente:
                    #É preciso ainda tratar quando fizer uma nova requisição e o RegID já existe.
                    regId = RegisterIds(android_key=dados_android["RegId"])
                    usuario_aplicao_cliente.register_ids.append(regId)
                    DBSession.add(usuario_aplicao_cliente)
                    return True
                else:
                    return False
            except Exception as e:
                ExceptionService.manuseia_excecao()

    def informacao_sobre_msg(self, dados, key):
        log.debug("Recebimento da Informação da mensagem do android")
        log.debug("Dados: %r" % dados)
        projeto = None
        response = {}
        try:
            log.debug("Verificando permissão do projeto.")
            projeto = descriptografa_projeto(dados['id_projeto'], key)

            if projeto:
                men = json.loads(dados["mensagem"].replace('\'', '\"'))
                log.debug("mensage json; %r" % men)
                #for men in d:
                #   print(men)
                with transaction.manager:
                    #Quando existir mais de um projeto vai ser necessário usar o identificar do projeto que enviou a mensagem
                    #além do id do projeto android.
                    log.debug("Buscando mensagem.")
                    msg_obj = DBSession.query(Mensagem).filter(Mensagem.id_on_web_app == men["id_mensagem"]).first()
                    log.debug("alterando status da mensagem")
                    msg_obj.status = StatusMensagem[men['status']].value
                    DBSession.add(msg_obj)
                response['ok'] = 'Projeto autorizado'
            else:
                response['ok'] = "Projeto não autorizado"
        except Exception as e:
            response['ok'] = "Erro :( %r" % e
            ExceptionService.manuseia_excecao()

        return response


# ***** Usuario Aplicação Cliente Service *********
class UsuarioAplicacaoService:

    def cadastrarUsuario(self, dados):
        with transaction.manager:
            try:
                usr_cli = DBSession.query(UsuarioAplicacaoCliente).\
                    filter(UsuarioAplicacaoCliente.chave == dados["usuario"]["chave_registro_android"]).first()
                if not usr_cli:
                    log.debug("Novo Usuário cliente")
                    projeto = DBSession.query(Projeto).filter(Projeto.access_token == dados["access_token"]).first()
                    usr_cli = UsuarioAplicacaoCliente()
                    usr_cli.nome_usuario, usr_cli.chave, usr_cli.projeto = dados["usuario"]["nome_usuario"],\
                                                                           dados["usuario"]["chave_registro_android"],\
                                                                           projeto

                    usr_cli.telefones = [Telefone(numero=tel, usuario_aplicacao_cliente=usr_cli) for tel in dados["usuario"]["telefones"]]
                    log.debug("Salvando novo usuário cliente %r" % usr_cli)
                    DBSession.add(usr_cli)
            except Exception as e:
                ExceptionService.manuseia_excecao()

    def buscaUsuarioPorChave(self, chave):
        try:
            return DBSession.query(UsuarioAplicacaoCliente).filter(UsuarioAplicacaoCliente.chave == chave).first()
        except Exception as e:
            ExceptionService.manuseia_excecao()



def descriptografa_projeto(id_projeto, key):
    """
    Função utilizada por várias classes para descriptografar o token e buscar o projeto relacionado a ele.
    :param id_projeto: token de identificação do projeto
    :param key: chave usada para descriptografar
    :return: o projeto relaciona is id_projeto
    """

    #descriptografando e buscando o projeto no banco
    log.debug("Descriptografando id_projeto!")
    token_em_bytes = unhexlify(id_projeto)
    log.debug("unhexlify")
    token_descripto_bytes = decrypt(key, token_em_bytes)
    log.debug("decript")
    projeto = DBSession.query(Projeto).filter(Projeto.uuid == token_descripto_bytes.decode("utf8")).first()
    log.debug("projeto:D")

    return projeto


