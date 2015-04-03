__author__ = 'anderson'

from khipu.banco_de_dados.models import (DBSession, Mensagem, GcmInformation, Projeto, RegisterIds)
from khipu.banco_de_dados.enuns import StatusMensagem
from khipu.gcm_wraper.gcm import GCM
from binascii import unhexlify
from simplecrypt import decrypt
import datetime
import transaction
import json
import psutil


# ***** Sender *********
class Sender(object):
    """
        Classe responsável por formatar as informações que serão enviadas para o servidor do google e posteriormente
        para o celular cadastrado, que então enviará as mensagens de texto;
    """

    def __init__(self):
        pass

    def givemeGcm(self):
        return DBSession.query(GcmInformation).filter(GcmInformation.name == "GCMCLASS").first()

    def salvar_mensagem(self, id_msg, projeto):
        with transaction.manager:
            msg = Mensagem()
            msg.id_on_web_app = id_msg
            msg.data_chegada = datetime.datetime.now().date()
            msg.numero_tentativas_envio = 1
            msg.status = StatusMensagem.RECEBIDA_CLIENTE
            msg.projeto = projeto
            DBSession.add(msg)
        return msg

    def processador(self, dados, key):
        print("Processando Mensagem Recebida")
        d = json.loads(dados)
        projeto = None
        print("projeto json: %r" % d)
        try:
            projeto = descriptografa_projeto(dados['id_projeto'], key)
        except Exception as e:
            print("Erro na consulta: %r" % e)

        if projeto:
            self.salvar_mensagem(d['data']['id_mensagem'], projeto)
            gcminformation = self.givemeGcm()

            d['registration_ids'] = [gcminformation.register_ids[0].androidkey]
            print("DADOS: %r" % d)
            gcmobj = GCM(gcminformation.apikey)
            response = gcmobj.json_request(registration_ids=d['registration_ids'], data=d['data'])
            print("Resposta Google: %r" % response)
            return {'msg': "Mensagem Recebida com sucesso"}
        else:
            return {'msg': "Projeto não autorizado"}


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
            if num_fields == 4: #é que só quero o retorno de quantro parametros
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
        print("Buscando Mensagens!")
        d = json.loads(dados)
        projeto = None
        print("projeto json: %r" % d)
        try:
            projeto = descriptografa_projeto(dados['id_projeto'], key)
        except Exception as e:
            print("Erro na consulta: %r" % e)

        if projeto:
            msg_ids = d['mensagem_ids']
            mensagens = [DBSession.query(Mensagem).filter(Mensagem.id_on_web_app == id).first() for id in msg_ids]
            informacoes = [{"mensagem_id": msg.id, "data_chegada": msg.data_chegada.strftime("%d/%m/%Y"),
                            "numero_tentativas": msg.numero_tentativas_envio, "status": msg.status}
                           for msg in mensagens if msg]
            print("Informações: %r" % informacoes)
            return informacoes


# ***** Mensagem *********
class GcmService(object):
    def __init__(self):
        pass

    def informa_msg(self, dados, key):
        print("Recebimento da Informação da mensagem do android")
        projeto = None
        msg = {}
        try:
            projeto = descriptografa_projeto(dados['id_projeto'], key)
        except Exception as e:
            msg['ok'] = "Erro :( %r" % e
        print(msg)

        if projeto:
            gcmclass = DBSession.query(GcmInformation).filter(GcmInformation.name == "GCMCLASS").first()
            if not gcmclass:
                regId = RegisterIds(androidkey=dados["RegId"])
                gcmclass = GcmInformation()
                gcmclass.register_ids.append(regId)
                DBSession.add(gcmclass)
            msg['ok'] = 'Projeto autorizado'
        else:
            msg['ok'] = "Projeto não autorizado"

        return msg


def descriptografa_projeto(id_projeto, key):
    """
    Função utilizada por várias classes para descriptografar o token e buscar o projeto relacionado a ele.
    :param id_projeto: token de identificação do projeto
    :param key: chave usada para descriptografar
    :return: o projeto relaciona is id_projeto
    """
    #descriptografando e buscando o projeto no banco
    token_em_bytes = unhexlify(id_projeto)
    token_descripto_bytes = decrypt(key, token_em_bytes)
    projeto = DBSession.query(Projeto).filter(Projeto.uuid == token_descripto_bytes.decode("utf8")).first()
    return projeto