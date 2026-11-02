import logging
import threading
from concurrent import futures

import grpc

import dicionario_pb2
import dicionario_pb2_grpc
from registro import argumentos_servidor, executar_registrado

NOME_SERVICO = 'Dicionario'


class Dicionario(dicionario_pb2_grpc.DicionarioServicer):
    def __init__(self):
        self.trava = threading.Lock()
        self.verbetes = {
            "rpc": "Chamada de procedimento remoto: invocar uma função em outro processo como se fosse local.",
            "grpc": "Framework de RPC do Google que usa HTTP/2 e Protocol Buffers.",
            "middleware": "Camada de software entre o sistema operacional e a aplicação distribuída.",
            "stub": "Código que representa o objeto remoto localmente e faz a serialização das chamadas.",
        }

    def Buscar(self, request, context):
        palavra = request.palavra.strip().lower()
        with self.trava:
            definicao = self.verbetes.get(palavra)
        logging.info("Buscar '%s' -> %s", palavra, "encontrada" if definicao else "não encontrada")
        if definicao is None:
            return dicionario_pb2.Definicao(encontrada=False)
        return dicionario_pb2.Definicao(encontrada=True, definicao=definicao)

    def Adicionar(self, request, context):
        palavra = request.palavra.strip().lower()
        if not palavra or not request.definicao:
            return dicionario_pb2.Status(sucesso=False, mensagem="palavra e definição são obrigatórias")
        with self.trava:
            if palavra in self.verbetes:
                return dicionario_pb2.Status(sucesso=False, mensagem=f"'{palavra}' já existe")
            self.verbetes[palavra] = request.definicao
        logging.info("Adicionar '%s'", palavra)
        return dicionario_pb2.Status(sucesso=True, mensagem=f"'{palavra}' adicionada")

    def ListarPalavras(self, request, context):
        logging.info("ListarPalavras")
        with self.trava:
            return dicionario_pb2.ListaPalavras(palavras=sorted(self.verbetes))


def serve(args):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dicionario_pb2_grpc.add_DicionarioServicer_to_server(Dicionario(), server)
    porta = str(server.add_insecure_port(f'[::]:{args.porta}'))
    server.start()
    logging.info("Dicionário ouvindo na porta %s", porta)
    executar_registrado(server, args.ns, NOME_SERVICO, args.ip, porta)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [dicionario] %(message)s")
    serve(argumentos_servidor("Servidor do Dicionário"))
