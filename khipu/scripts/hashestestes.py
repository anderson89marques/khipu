from datetime import datetime

__author__ = 'anderson'
from passlib.context import CryptContext
import uuid
from datetime import datetime, datetime
from simplecrypt import encrypt, decrypt
from khipu.banco_de_dados.enuns import StatusMensagem

#o usuário cria um projeto e clica para gerar a chave<
#então é garado um número identificador para o projeto que salvo no banco junto com o nome do projeto
#encriptografo esse número identificador e mostro para o usuário como chave gerada
#quando a aplicação me mandar de volta eu descriptografo e comparo com o número identificador que está no banco.


#Criando um objeto que usará criptografia do método shs256, rounds default de 80000
"""cripto = CryptContext(schemes="sha256_crypt")

#Encriptografando uma string
passw = cripto.encrypt("anderson")

#Comparando o valor da string com o valor criptografado
isok = cripto.verify("anderso", passw)
print(passw)
print(isok)
print("////////////")
u = uuid.uuid1().hex
print(u)
p = cripto.encrypt(u)
print(p)
isuok = cripto.verify(u, p)
print(isuok)
"""
print("::::::::::::::::::")
#vou salvar a data normal e na hora de exibir eu edito
l = "03-29-2015"
formater_string = "%m-%d-%Y"
d = datetime.strptime(l, formater_string)
print(d)
print(type(d))
print(StatusMensagem.CONFIRMADA_SMS.name)
"""
print("::::::::::::::::::")
from binascii import hexlify, unhexlify
password = "98z"
palavra = uuid.uuid1().hex #salarei no bancouuid
print(palavra)
e = encrypt(password, palavra)
eh = hexlify(e)         #a ideia é criar um token em hexadecimal
ehd = eh.decode("utf8") #salvarei como chave
print(ehd)
eb = unhexlify(ehd) #na hora de descriptografar transformar primeiro para bytes e depois usar decrypt
print(eb)
if e == eb:
    print(True)
d = decrypt(password, eb)
print(d.decode("utf8"))
if palavra == d:
    print(True)
"""

