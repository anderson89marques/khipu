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
