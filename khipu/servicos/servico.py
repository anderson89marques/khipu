__author__ = 'anderson'

from khipu.banco_de_dados.models import (DBSession, Mensagem, UsuarioAplicacaoCliente, GcmInformation, Projeto, RegisterIds, KhipuException)
from khipu.banco_de_dados.enuns import StatusMensagem
from sqlalchemy.exc import DBAPIError
from khipu.gcm_wraper.gcm import GCM
from binascii import unhexlify
from simplecrypt import decrypt
import datetime
import transaction
import logging
import json
import psutil

log = logging.getLogger(__name__)


# ***** Sender *********
class Sender(object):
    """
        Classe responsável por formatar as informações que serão enviadas para o servidor do google e posteriormente
        para o celular cadastrado, que então enviará as mensagens de texto;
    """

    def __init__(self):
        pass

    def givemeGcm(self):
        log.debug("Buscando GCM")
        return DBSession.query(GcmInformation).filter(GcmInformation.name == "GCMCLASS").first()

    def get_mensagem(self, id_msg):
        msg = DBSession.query(Mensagem).filter(Mensagem.id_on_web_app == id_msg).first()
        return msg

    def salvar_mensagem(self, id_msg, projeto):
        log.debug("Salvando Mensagem.")
        with transaction.manager:
            m = self.get_mensagem(id_msg)
            if m:
                m.status = StatusMensagem.RECEBIDA_CLIENTE.value
                m.data_ultimo_envio = datetime.datetime.now().date()
                DBSession.add(m)
                log.debug("Mensagem atualizada: %r" % m)
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

    def processador(self, dados, key):
        log.debug("Processando Mensagem Recebida")
        d = json.loads(dados)
        projeto = None
        log.debug("Dados json: %r" % d['data'])
        try:
            projeto = descriptografa_projeto(d['data']['id_projeto'], key)
            if projeto:
                self.salvar_mensagem(d['data']['id_mensagem'], projeto)
                gcminformation = self.givemeGcm()

                d['registration_ids'] = [gcminformation.register_ids[0].androidkey]
                log.debug("DADOS: %r" % d)
                gcmobj = GCM(gcminformation.apikey)
                response = gcmobj.json_request(registration_ids=d['registration_ids'], data=d['data'])
                log.debug("Resposta Google: %r" % response)
                return {'msg': "Mensagem Recebida com sucesso"}
            else:
                return {'msg': "Projeto não autorizado"}

        except Exception as e:
            manuseia_excecao()
            return {'msg': "Erro: {0}".format(e)}


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
            manuseia_excecao()
            msg['ok'] = "Erro :( %r" % e
            return msg
        return list


# ***** Mensagem *********
class MensagemService(object):
    """
        Classe que controla a busca de informações sobre as mensagens.
        O método get_messages recebe a chave para descriptografar o token identificador da aplicação
        e também os dados contendo o token e os ids das mensagens ao qual se quer obter informação.
    """

    def __init__(self):
        pass

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
            manuseia_excecao()
            return {'msg': "Erro na consulta: %r" % e}


# ***** Mensagem *********
class GcmService(object):
    def __init__(self):
        pass

    def informa_regid(self, dados, key):
        log.debug("Recebimento do RegId do android")
        log.debug("")
        projeto = None
        msg = {}
        try:
            projeto = descriptografa_projeto(dados['id_projeto'], key)

            if projeto:
                log.debug("Buscando a classe GcmInformation")
                gcmclass = DBSession.query(GcmInformation).filter(GcmInformation.name == "GCMCLASS").first()
                if not gcmclass:
                    log.debug("a classe GcmInformation")
                    regId = RegisterIds(androidkey=dados["RegId"])
                    gcmclass = GcmInformation()
                    gcmclass.register_ids.append(regId)
                    DBSession.add(gcmclass)
                msg['ok'] = 'Projeto autorizado'
            else:
                msg['ok'] = "Projeto não autorizado"

        except Exception as e:
            msg['ok'] = "Erro :( %r" % e
            manuseia_excecao()

        return msg

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
            manuseia_excecao()

        return response


# ***** Usuario Aplicação Cliente Service *********
class UsuarioAplicacaoService:

    def cadastrarUsuario(self, dados):
        try:
            usuario_cliente = DBSession.query(UsuarioAplicacaoCliente).\
                filter(UsuarioAplicacaoCliente.chave == dados["chave_registro_android"]).first()
            if not usuario_cliente:
                pass
        except Exception as e:
            manuseia_excecao()


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


def manuseia_excecao():
    """
    Função que cria e escreve no log as excessões
    :return:
    """

    with transaction.manager:
        excep = KhipuException()
        log.debug(excep)
        DBSession.add(excep)