__author__ = 'anderson'
import urllib
import json
import logging
GCM_URL = 'https://android.googleapis.com/gcm/send'
log = logging.getLogger(__name__)


class GCM(object):
    def __init__(self, apikey, url=GCM_URL):
        self.apikey = apikey
        self.url = url

    def construir_dados(self, registration_ids, data=None, collapse_key=None, delay_while_idle=False,
                        time_to_live=0, is_json=True, dry_run=False):
        log.debug("Contruindo dados para enviar o google gcm server")
        if is_json:
            dados = {'registration_ids': registration_ids, 'data': data}

        if collapse_key:
            dados['collapse_key'] = collapse_key

        if delay_while_idle:
            dados['delay_while_idle'] = delay_while_idle

        if time_to_live > 0:
            dados['time_to_live'] = time_to_live

        if dry_run:
            dados['dry_run'] = True

        if is_json:
            dados = json.dumps(dados)

        log.debug("Dados: %r" % dados)
        return dados

    def fazer_requisicao(self, dados, is_json=True):
        """
        Faz requisição HTTP para os servidores GCM.

        :param dados:
        :param is_json:
        :return:
        """
        log.debug("Fazendo a requisição para o google gcm server")
        #adicionando a chave do servidor no head da requisição.
        headers = {
            'Authorization': 'key=%s' % self.apikey
        }

        log.debug("Header: %r" % headers)
        log.debug("Conteúdo: %r" % dados)
        #Default não é json é application/x-www-form-urlencoded;charset=UTF-8
        if is_json:
            headers['Content-Type'] = 'application/json'

        #Transformando os dados para bytes para evitar erro no envio.
        binary_data = dados.encode('utf8')
        req = urllib.request.Request(self.url, binary_data, headers)

        response = None
        try:
            response = urllib.request.urlopen(req).read()
        except urllib.error.HTTPError as e:
            if e.code == 400:
                log.debug("Fazendo a requisição para o google gcm server")("Error code: %d\nRequisição não pôde ser passado como JSON." % e.code)
                raise Exception("Error code: %d\nRequisição não pôde ser passado como JSON." % e.code)
            if e.code == 401:
                log.debug("Fazendo a requisição para o google gcm server")("Error code: %d\nErro de autenticação." % e.code)
                raise Exception("Error code: %d\nErro de autenticação." % e.code)
            if e.code == 503:
                log.debug("Fazendo a requisição para o google gcm server")("Error code: %d\nServiço GCM está indisponível." % e.code)
                raise Exception("Error code: %d\nServiço GCM está indisponível." % e.code)
        except urllib.error.URLError as e:
            log.debug("Fazendo a requisição para o google gcm server")("Error code: %d\nErro interno no servidor GCM enquanto estava tentandoa requisição." % e.code)
            raise Exception(("Error code: %d\nErro interno no servidor GCM enquanto estava tentandoa requisição." % e.code))

        #decodificando
        response = response.decode("utf8")
        if is_json:
            resp = json.loads(response)
        return response

    def json_request(self, registration_ids, data=None, collapse_key=None, delay_while_idle=False,
                     time_to_live=None, retries=5, dry_run=False):
        """
        Faz a requisição JSON para os servidores GCM.

        :param registration_ids: lista de ids registrados
        :param data: dados
        :param collapse_key:
        :param delay_while_idle:
        :param time_to_live:
        :param retries:
        :param dry_run:
        :return:
        """

        if not registration_ids:
            raise Exception("Faltando Registration ids")
        if not data:
            raise Exception("Faltando Dados(data):")
        if len(registration_ids) > 1000:
            raise Exception("Excedeu o limite máximo de registration ids")

        dados = self.construir_dados(registration_ids, data)
        response = self.fazer_requisicao(dados, is_json=True)
        return response