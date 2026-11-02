import argparse
import logging
import threading
from concurrent import futures

import grpc

import const
import nomes_pb2
import nomes_pb2_grpc

OK = nomes_pb2.StatusMsg(status='OK')
NOK = nomes_pb2.StatusMsg(status='NOK')


class ServicoNomes(nomes_pb2_grpc.ServicoNomesServicer):
    def __init__(self):
        self.tabela = {}
        self.trava = threading.Lock()

    def Bind(self, request, context):
        endereco = (request.address.ipaddress, request.address.portnumber)
        with self.trava:
            if request.name in self.tabela:
                logging.info("BIND %s recusado: já registrado em %s:%s",
                             request.name, *self.tabela[request.name])
                return NOK
            self.tabela[request.name] = endereco
        logging.info("BIND %s -> %s:%s", request.name, *endereco)
        return OK

    def Lookup(self, request, context):
        with self.trava:
            endereco = self.tabela.get(request.name)
        if endereco is None:
            logging.info("LOOKUP %s -> não encontrado", request.name)
            return nomes_pb2.AddressMsg(ipaddress='', portnumber='')
        logging.info("LOOKUP %s -> %s:%s", request.name, *endereco)
        return nomes_pb2.AddressMsg(ipaddress=endereco[0], portnumber=endereco[1])

    def Rebind(self, request, context):
        endereco = (request.address.ipaddress, request.address.portnumber)
        with self.trava:
            self.tabela[request.name] = endereco
        logging.info("REBIND %s -> %s:%s", request.name, *endereco)
        return OK

    def Unbind(self, request, context):
        with self.trava:
            removido = self.tabela.pop(request.name, None)
        logging.info("UNBIND %s (%s)", request.name, "ok" if removido else "não existia")
        return OK if removido else NOK


def serve(porta):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    nomes_pb2_grpc.add_ServicoNomesServicer_to_server(ServicoNomes(), server)
    server.add_insecure_port(f'[::]:{porta}')
    server.start()
    logging.info("Serviço de Nomes ouvindo na porta %s", porta)
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [nomes] %(message)s")
    parser = argparse.ArgumentParser(description="Servidor do Serviço de Nomes")
    parser.add_argument("--porta", default=const.NS_PORT)
    args = parser.parse_args()
    serve(args.porta)
