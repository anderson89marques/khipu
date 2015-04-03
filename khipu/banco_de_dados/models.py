from sqlalchemy import (Column, Index, Integer, Text, ForeignKey, Date)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension
from passlib.context import CryptContext
from simplecrypt import encrypt
from binascii import hexlify
import uuid

#Criação da sessão de acesso ao banco de dados e também da classe Base para a construção dos modelos.
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension(), expire_on_commit=False))
Base = declarative_base()


#usuarios e seu grupos(principals)
class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(Text, nullable=True)
    senha = Column(Text, nullable=True)
    data_criacao = Column(Date)
    principals = relationship('Principal', secondary='usuario_principal')
    projetos = relationship('Projeto', back_populates='usuario')

    def check_password(self, password):
        #Criando um objeto que usará criptografia do método shs256, rounds default de 80000
        cripto = CryptContext(schemes="sha256_crypt")
        #Comparando o valor da string com o valor criptografado
        okornot = cripto.verify(password, self.senha)
        return okornot

    def encrypt(self, password):
        #Criando um objeto que usará criptografia do método shs256, rounds default de 80000
        cripto = CryptContext(schemes="sha256_crypt")
        #Encriptografando uma string
        self.senha = cripto.encrypt(password)


class Principal(Base):
    __tablename__ = 'principal'
    id = Column(Integer, primary_key=True)
    nome = Column(Text, nullable=True)
    usuarios = relationship('Usuario', secondary='usuario_principal')


class Usuario_Principal(Base):
    __tablename__ = 'usuario_principal'
    usuario_id = Column(Integer, ForeignKey('usuario.id'), primary_key=True)
    grupo_id = Column(Integer, ForeignKey('principal.id'), primary_key=True)

#fim usuários e seus grupos


# data = datetime.strptime(b, format_data_hora).date()
# format_data = "%d%m%Y"
#início de controle de projetos
class Projeto(Base):
    __tablename__ = 'projeto'
    id = Column(Integer, primary_key=True)
    nome = Column(Text)
    chave = Column(Text)
    uuid = Column(Text)
    data_ativacao = Column(Date)
    usuario_id = Column(Integer, ForeignKey('usuario.id'))
    usuario = relationship('Usuario', back_populates='projetos')
    #0.* mensagens podem ser enviadas(N - 1)
    mensagens = relationship('Mensagem', back_populates='projeto')

    def gerar_chave_para_projeto(self, key):
        u = uuid.uuid1().hex
        self.uuid = u
        e = encrypt(key, u)
        eh = hexlify(e)         #a ideia é criar um token em hexadecimal
        self.chave = eh.decode("utf8")

    def check_chave(self, chave):
        #Criando um objeto que usará criptografia do método sha256, rounds default de 80000
        cripto = CryptContext(schemes="sha256_crypt")
        #Comparando o valor da string(uuid) com o valor criptografado(chave)
        okornot = cripto.verify(self.uuid, chave)
        return okornot
#fim de controle de projetos


class Mensagem(Base):
    __tablename__ = 'mensagem'
    id = Column(Integer, primary_key=True)
    id_on_web_app = Column(Integer)
    data_chegada = Column(Date)
    numero_tentativas_envio = Column(Integer)
    status = Column(Text) #Vai ser um Enum.
    projeto_id = Column(Integer, ForeignKey('projeto.id'))
    projeto = relationship('Projeto', back_populates='mensagens')


class GcmInformation(Base):
    __tablename__ = 'gcminformation'
    id = Column(Integer, primary_key=True)
    name = Column(Text, default="GCMCLASS")
    apikey = Column(Text, default="AIzaSyBCyTjgOMZncxzTgPxVN9yxEbaZ0Y2SvQo") #chave do servidor
    register_id = Column(Integer, ForeignKey('registers_ids.id'))
    register_ids = relationship("RegisterIds", uselist=True)


class RegisterIds(Base):
    __tablename__ = 'registers_ids'
    id = Column(Integer, primary_key=True)
    androidkey = Column(Text)


class ServerInformation(Base):
    __tablename__ = 'server_information'
    id = Column(Integer, primary_key=True)
    mensagem_id = Column(Integer)
    app_key = Column(Integer)
    data_recebimento = Column(Date)



