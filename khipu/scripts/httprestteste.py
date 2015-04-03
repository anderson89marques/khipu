__author__ = 'anderson'
import urllib


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
        try:
            req = urllib.request.Request(url, bytedados)
            handle = opner.open('http://0.0.0.0:6544/receiver').read()
        except urllib.error.HTTPError as e:
            print("ERRO: %r" % e)

        print(handle.decode("utf8"))
