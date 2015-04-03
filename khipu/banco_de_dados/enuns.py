__author__ = 'anderson'
from enum import Enum


"""
    Controla o estado da mensagem
"""
class StatusMensagem(Enum):
    RECEBIDA_CLIENTE = "Recebida do Cliente"
    ENVIADA_GOOGLE = "Enviada para o google"
    CONFIRMADA = "Confirmada a chegada no android"