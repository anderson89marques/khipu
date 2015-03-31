__author__ = 'anderson'
USERS = {'editor': 'editor',
         'viewer': 'viewer'}
GROUPS = {'editor': ['group:editors']}
from khipu.banco_de_dados.models import (DBSession, Usuario, Principal)
import transaction
import datetime

def groupfinder(userid, request):
    print("Request do group finder %r: userid: %r" % (request.params, userid))
    user = DBSession.query(Usuario).filter(Usuario.nome == userid).first()
    print("USER: %r" % user)
    if user:
        print("Principals %r" % user.principals)
        return [principal.nome for principal in user.principals]


#Cria, se não existirem, os usuários defaults
def init():
    user_sysdata = DBSession.query(Usuario).filter(Usuario.nome == "sysdata").first()
    user_acception = DBSession.query(Usuario).filter(Usuario.nome == "acception").first()
    with transaction.manager:
        if not user_sysdata:
            user_sysdata = Usuario(nome="sysdata")
            user_sysdata.encrypt("sysdata")
            user_sysdata.data_criacao = datetime.datetime.now().date()
            principal = Principal(nome='role_usuario')
            user_sysdata.principals.append(principal)
            DBSession.add(user_sysdata)

        if not user_acception:
            user_acception = Usuario(nome="acception")
            user_acception.encrypt("acception")
            user_acception.data_criacao = datetime.datetime.now().date()
            principal = Principal(nome='role_admin')
            user_acception.principals.append(principal)
            DBSession.add(user_acception)