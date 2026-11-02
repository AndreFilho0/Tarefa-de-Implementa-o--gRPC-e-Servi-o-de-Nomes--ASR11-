import logging
import threading
from concurrent import futures

import grpc

import biblioteca_pb2
import biblioteca_pb2_grpc
from registro import argumentos_servidor, executar_registrado

NOME_SERVICO = 'Biblioteca'


class Biblioteca(biblioteca_pb2_grpc.BibliotecaServicer):
    def __init__(self):
        self.livros = {}
        self.proximo_id = 1
        self.trava = threading.Lock()
        self._cadastrar("Sistemas Distribuídos: Princípios e Paradigmas", "Tanenbaum e Van Steen")
        self._cadastrar("Sistemas Distribuídos: Conceitos e Projeto", "Coulouris et al.")
        self._cadastrar("Dom Casmurro", "Machado de Assis")

    def _cadastrar(self, titulo, autor):
        with self.trava:
            livro = biblioteca_pb2.Livro(id=self.proximo_id, titulo=titulo, autor=autor, disponivel=True)
            self.livros[livro.id] = livro
            self.proximo_id += 1
        return livro

    def CadastrarLivro(self, request, context):
        livro = self._cadastrar(request.titulo, request.autor)
        logging.info("CadastrarLivro #%d '%s'", livro.id, livro.titulo)
        return livro

    def ListarLivros(self, request, context):
        logging.info("ListarLivros")
        with self.trava:
            return biblioteca_pb2.ListaLivros(livros=list(self.livros.values()))

    def Emprestar(self, request, context):
        with self.trava:
            livro = self.livros.get(request.id)
            if livro is None:
                status = biblioteca_pb2.Status(sucesso=False, mensagem="livro não existe")
            elif not livro.disponivel:
                status = biblioteca_pb2.Status(sucesso=False, mensagem=f"'{livro.titulo}' já está emprestado")
            else:
                livro.disponivel = False
                status = biblioteca_pb2.Status(sucesso=True, mensagem=f"'{livro.titulo}' emprestado")
        logging.info("Emprestar #%d: %s", request.id, status.mensagem)
        return status

    def Devolver(self, request, context):
        with self.trava:
            livro = self.livros.get(request.id)
            if livro is None:
                status = biblioteca_pb2.Status(sucesso=False, mensagem="livro não existe")
            elif livro.disponivel:
                status = biblioteca_pb2.Status(sucesso=False, mensagem=f"'{livro.titulo}' não estava emprestado")
            else:
                livro.disponivel = True
                status = biblioteca_pb2.Status(sucesso=True, mensagem=f"'{livro.titulo}' devolvido")
        logging.info("Devolver #%d: %s", request.id, status.mensagem)
        return status


def serve(args):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    biblioteca_pb2_grpc.add_BibliotecaServicer_to_server(Biblioteca(), server)
    porta = str(server.add_insecure_port(f'[::]:{args.porta}'))
    server.start()
    logging.info("Biblioteca ouvindo na porta %s", porta)
    executar_registrado(server, args.ns, NOME_SERVICO, args.ip, porta)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [biblioteca] %(message)s")
    serve(argumentos_servidor("Servidor da Biblioteca"))
