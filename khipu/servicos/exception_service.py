__author__ = 'anderson'
from khipu.banco_de_dados.models import KhipuException, DBSession
import transaction
import logging

log = logging.getLogger(__name__)


class ExceptionService:

    @staticmethod
    def manuseia_excecao():

        """
        Função que cria e escreve no log as excessões
        :return:
        """

        with transaction.manager:
            excep = KhipuException()
            log.debug(excep)
            DBSession.add(excep)