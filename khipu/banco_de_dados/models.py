from sqlalchemy import (Column, MetaData, Integer, Text, ForeignKey, Date, create_engine, Table)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (scoped_session, sessionmaker, relationship)
from zope.sqlalchemy import ZopeTransactionExtension
from passlib.context import CryptContext
from migrate.changeset import schema
import uuid
import sys
import os

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
    client_id = Column(Text)
    client_secret = Column(Text)
    access_token = Column(Text, nullable=True)
    grant_type = Column(Text, nullable=True)
    data_ativacao = Column(Date)
    usuario_id = Column(Integer, ForeignKey('usuario.id'))
    usuario = relationship('Usuario', back_populates='projetos')
    #0.* mensagens podem ser enviadas(N - 1)
    mensagens = relationship('Mensagem', back_populates='projeto')
    usuarios_aplicacao_cliente = relationship('UsuarioAplicacaoCliente', back_populates='projeto')

    def gerar_chaves_para_projeto(self):
        self.client_id = uuid.uuid1().hex
        self.client_secret = uuid.uuid1().hex

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
    data_ultimo_envio = Column(Date)
    numero_tentativas_envio = Column(Integer)
    status = Column(Text) #Vai ser um Enum.
    projeto_id = Column(Integer, ForeignKey('projeto.id'))
    projeto = relationship('Projeto', back_populates='mensagens')
    usuario_aplicacao_cliente_id = Column(Integer, ForeignKey('usuario_aplicacao_cliente.id'))
    usuario_aplicacao_cliente = relationship('UsuarioAplicacaoCliente', back_populates='mensagens')

    def __repr__(self):
        return "Mensagem: {0} {1} {2} {3}".format(self.id, self.id_on_web_app, self.data_chegada, self.status)


def upgrade():
    engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost/khipudb')
    meta = MetaData(bind=engine)
    msg = Table('mensagem', Base.metadata, autoload=True)
    usr = Column('usuario_aplicacao_cliente_id', Integer, ForeignKey('usuario_aplicacao_cliente.id'))
    schema.create_column(usr, msg)
    #msg.append_column(usr)
    msg.update()



class UsuarioAplicacaoCliente(Base):
    __tablename__ = 'usuario_aplicacao_cliente'

    id = Column(Integer, primary_key=True)
    nome_usuario = Column(Text)
    chave = Column(Text)
    projeto_id = Column(Integer, ForeignKey('projeto.id'))
    projeto = relationship('Projeto', back_populates='usuarios_aplicacao_cliente')
    telefones = relationship('Telefone', back_populates='usuario_aplicacao_cliente')
    mensagens = relationship('Mensagem', back_populates='usuario_aplicacao_cliente')
    register_ids = relationship("RegisterIds", back_populates='usuario_aplicacao_cliente')


class Telefone(Base):
    __tablename__ = 'telefone'

    id = Column(Integer, primary_key=True)
    numero = Column(Text)
    usuario_aplicacao_cliente_id = Column(Integer, ForeignKey('usuario_aplicacao_cliente.id'))
    usuario_aplicacao_cliente = relationship('UsuarioAplicacaoCliente', back_populates='telefones')


class GcmInformation(Base):
    __tablename__ = 'gcminformation'
    id = Column(Integer, primary_key=True)
    name = Column(Text, default="GCMCLASS")
    apikey = Column(Text, default="AIzaSyBCyTjgOMZncxzTgPxVN9yxEbaZ0Y2SvQo") #chave do servidor


class RegisterIds(Base):
    __tablename__ = 'registers_ids'
    id = Column(Integer, primary_key=True)
    androidkey = Column(Text)
    usuario_aplicacao_cliente_id = Column(Integer, ForeignKey('usuario_aplicacao_cliente.id'))
    usuario_aplicacao_cliente = relationship('UsuarioAplicacaoCliente', back_populates='register_ids')


class KhipuException(Base):
    __tablename__ = 'khipu_exception'
    id = Column(Integer, primary_key=True)
    nome_arquivo = Column(Text)
    tipo_excessao = Column(Text)
    linha = Column(Text)
    descricao = Column(Text)

    def __init__(self):
        exc_type, exc_obj, exc_tb = sys.exc_info()

        self.nome_arquivo = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        self.tipo_excessao = exc_type.__name__
        self.linha = exc_tb.tb_lineno
        self.descricao = str(exc_obj)

    def __repr__(self):
        return "Erro: nome do arquivo:{0}, tipo:{1}, linha:{2}, descrição:{3}".format(self.nome_arquivo,self.tipo_excessao,
                                                                                      self.linha, self.descricao)


class ServerInformation(Base):
    __tablename__ = 'server_information'
    id = Column(Integer, primary_key=True)
    mensagem_id = Column(Integer)
    app_key = Column(Integer)
    data_recebimento = Column(Date)




