__author__ = 'anderson'
from enum import Enum


"""
    Controla o estado da mensagem
"""
class StatusMensagem(Enum):
    RECEBIDA_CLIENTE = "Recebida Cliente"
    ENVIADA_GOOGLE = "Enviada google"
    CONFIRMADO_RECEBIMENTO_GOOGLE = "Confirmado o recebimento google"
    CONFIRMADO_RECEBIMENTO_ANDROID = "Confirmado o recebimento android"
    CONFIRMADA_SMS = "Confirmada sms"

    def __getitem__(self, item):
        return self.__dict__[item]