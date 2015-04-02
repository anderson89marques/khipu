__author__ = 'anderson'
import psutil

#CPU
for cput in psutil.cpu_times(True): #Tempo gasto pela cpu em segundos em cada modo exibido
    print(cput.user)

print(psutil.cpu_percent(interval=1, percpu=True))
print(psutil.cpu_count()) #número de CPU's lógicas
#tempo com usuário   processos importantes  número de cpus lógicas


#Memória virtual
""" psutil.virtual_memory() ->
    Retorna estatísticas sobre o uso de memória do sistema, incluindo os campos abaixo, expressados em bytes.

    total: Total de memória física disponível.
    available: A quantidade real de memória disponível que pode ser dada de imediato, aos processos que pedem
               mais memória em bytes ; este é calculado pela soma diferentes valores de memória , dependendo
               da plataforma (por exemplo, buffers + oferta + cache no Linux) e é suposto ser usado para monitorar
               o uso de memória real de uma forma multi-plataforma .
    percent : A utilização percentual calculada como (total - available) / total * 100
    used: Memória utilizada , calculado de forma diferente dependendo da plataforma e concebido apenas para fins informativos.
    active: Memória atualmente em uso ou usado muito recentemente, e por isso é de RAM.
    inactive: memóra que está marcada como não usada
    buffers: Cache para coisas como os metadados do sistema de arquivos.
    cached: Cache para várias coisas.

"""
mem = psutil.virtual_memory()
print(mem)
#memória ram
# total memorial_disponível percetual_de_utilização memória_usada

#Uso bem interessante
threashold = 100 * 1024 * 1024 #100M
if mem.available <= threashold:
    print("warning")

print("Uso do disco:")
#uso do disco
"""
    psutil.disk_usage() ->
    Retorna estatíticas do uso do disco na path passada como parâmetro.
"""
#memoria disco
#total memória_usada percetual de utilização
disk = psutil.disk_usage("/")
print(disk)
print("//////////////////////")

#Network
"""
    psutil.net_io_counters() ->
    Retorna estatíticas de entrada e saida na rede como uma namedtuple, incluindo os
    atributos abaixo.

    bytes_sent: Número de bytes enviados
    bytes_recv: Número de bytes recebidos
    packets_sent: Número de pacotes enviados
    packets_recv: Número de pacotes recebidos
    errin: Número total de erros enquanto recebe
    errout: Número total de erros enquanto envia
    dropin: Número total de pacotes de entrada que foram retiradas
    dropout: Número total de pacotes de saída que foram retiradas
"""
#network
# byes_enviados bytes_recebidos pacotes_enviados pacotes_recebidos erros_no_envio erros_no_recebimento
netio = psutil.net_io_counters()
print(netio)
netio = psutil.net_io_counters(pernic=True) #mostra os dados para cada interface de rede :D
for x in netio:
    print("X: %r, Y: %r" % (x, netio[x]))
    print("X: %r, Y: %r" % (x, netio[x][0]))
print("/////////")
netiocon = psutil.net_connections()
for n in netiocon:
    print(n)


