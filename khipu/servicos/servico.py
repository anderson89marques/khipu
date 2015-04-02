__author__ = 'anderson'
import json

from khipu.banco_de_dados.models import (
    DBSession, Mensagem, GcmInformation, Projeto
)
from khipu.gcm_wraper.gcm import GCM
from binascii import hexlify, unhexlify
from simplecrypt import encrypt, decrypt
import datetime
import urllib.request
import urllib.parse
import transaction
import json
import psutil

class Sender(object):
    """
        classe responsável por formatar as informações que serão enviadas para o servidor do google e posteriormente
        para o celular cadastrado, que então enviará as mensagens de texto;
    """

    def __init__(self):
        pass

    def testerest(self, mapadados):
        url = "http://0.0.0.0:6544/"
        username = "anderson"
        password = "anderson"

        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        opner = urllib.request.build_opener(authhandler)
        # use the opener to fetch a URL

        urllib.request.install_opener(opner)

        print(mapadados)
        dados = urllib.parse.urlencode(mapadados)
        bytedados = dados.encode("utf8")
        pagehandle = None
        try:
            #pagehandle = urllib.request.urlopen(url, bytedados).read()
            req = urllib.request.Request(url, bytedados)
            handle = opner.open('http://0.0.0.0:6544/receiver').read()
        except urllib.error.HTTPError as e:
            print("ERRO: %r" % e)

        print(handle.decode("utf8"))

    def givemeGcm(self):
        return DBSession.query(GcmInformation).filter(GcmInformation.name == "GCMCLASS").first()

    def salvar_mensagem(self, id_msg, projeto):
        with transaction.manager:
            msg = Mensagem()
            msg.id_on_web_app = id_msg
            msg.data_chegada = datetime.datetime.now().date()
            msg.numero_tentativas_envio = 1
            msg.status = "Recebido."
            msg.projeto = projeto
            DBSession.add(msg)
        return msg

    def processador(self, dados, key):
        print("Entrou no processador!")
        d = json.loads(dados)
        projeto = None
        print("projeto json: %r" % d)
        print("id projeto : %r" % d['data']['id_projeto'])
        try:
            #descriptografando e buscando o projeto no banco
            token_em_bytes = unhexlify(d['data']['id_projeto'])
            token_descripto_bytes = decrypt(key, token_em_bytes)
            projeto = DBSession.query(Projeto).filter(Projeto.uuid == token_descripto_bytes.decode("utf8")).first()
        except Exception as e:
            print("Erro na consulta: %r" % e)

        if projeto:
            self.salvar_mensagem(d['data']['id_mensagem'], projeto)
            gcminformation = self.givemeGcm()

            d['registration_ids'] = [gcminformation.register_ids[0].androidkey]
            print("DADOS: %r" % d)
            gcmobj = GCM(gcminformation.apikey)
            response = gcmobj.json_request(registration_ids=d['registration_ids'], data=d['data'])
            print(response)
            return {'msg': "Mensagem Recebida com sucesso"}
        else:
            return {'msg': "Projeto não autorizado"}


class SistemaService(object):
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


class MensagemService(object):
    def __init__(self):
        pass

    def get_messages(self, dados, key):
        print("Entrou no processador!")
        d = json.loads(dados)
        projeto = None
        print("projeto json: %r" % d)
        print("id projeto : %r" % d['id_projeto'])
        try:
            #descriptografando e buscando o projeto no banco
            token_em_bytes = unhexlify(d['id_projeto'])
            token_descripto_bytes = decrypt(key, token_em_bytes)
            projeto = DBSession.query(Projeto).filter(Projeto.uuid == token_descripto_bytes.decode("utf8")).first()
        except Exception as e:
            print("Erro na consulta: %r" % e)

        if projeto:
            msg_ids = d['mensagem_ids']
            mensagens = [DBSession.query(Mensagem).filter(Mensagem.id_on_web_app == id).first() for id in msg_ids]
            informacoes = [{"data_chegada": msg.data_chega, "numero_tentativas": msg.numero_tentativas_envio,
                            "status": msg.status} for msg in mensagens]
            print("Informações: %r" % informacoes)
            return informacoes